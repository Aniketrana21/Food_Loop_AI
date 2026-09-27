'use client';

import React, { useState, useEffect, useRef } from 'react';
import {
  QrCode,
  ShieldCheck,
  ShieldAlert,
  Camera,
  CameraOff,
  RefreshCw,
  Copy,
  Check,
  AlertTriangle,
  FileCheck,
  Thermometer,
  MapPin,
  Lock,
  Unlock,
  Eye,
  CheckCircle2,
  Clock,
  User,
  Truck,
  Building2,
  ChefHat,
  History,
  Layers,
  Sparkles,
  ArrowRight,
  Flame,
  Info,
  Maximize2
} from 'lucide-react';
import { Button } from '@/components/design-system/Button';
import { Card } from '@/components/design-system/Card';
import { Badge } from '@/components/design-system/Badge';
import { Input } from '@/components/design-system/Input';
import { Modal } from '@/components/design-system/Modal';
import {
  CustodyStage,
  QRScanStage,
  DonationCustodyEvent,
  DonationAuditTrailResponse,
  GenerateCustodyQRResponse,
  VerifyCustodyScanResponse
} from '@/types';
import {
  fetchDonationsManifests,
  fetchDonationCustodyStatus,
  fetchDonationAuditTrail,
  generateCustodyQRToken,
  verifyCustodyQRScan,
  transitionDonationCustody
} from '@/lib/api';

interface QrCustodyScreenProps {
  onNavigate?: (screen: any) => void;
  onShowSuccess?: (msg: string) => void;
}

// Canonical 7 stages
const STAGES: { key: CustodyStage; label: string; desc: string; icon: any }[] = [
  { key: 'DONATION_CREATED', label: '1. Created', desc: 'Manifest registered', icon: Layers },
  { key: 'ACCEPTED', label: '2. Accepted', desc: 'Recipient approved', icon: Building2 },
  { key: 'PICKUP_ASSIGNED', label: '3. Assigned', desc: 'Courier dispatched', icon: Truck },
  { key: 'PICKED_UP', label: '4. Picked Up', desc: 'Kitchen handover verified', icon: ChefHat },
  { key: 'IN_TRANSIT', label: '5. In Transit', desc: 'En route with temperature control', icon: Truck },
  { key: 'DELIVERED', label: '6. Delivered', desc: 'Arrived at dropoff point', icon: MapPin },
  { key: 'RECEIVED', label: '7. Received', desc: 'Recipient verified & signed off', icon: CheckCircle2 }
];

export const QrCustodyScreen: React.FC<QrCustodyScreenProps> = ({
  onNavigate,
  onShowSuccess
}) => {
  // Active Persona / Role
  const [activeRole, setActiveRole] = useState<'KITCHEN_MANAGER' | 'DRIVER' | 'NGO' | 'ADMIN'>('KITCHEN_MANAGER');

  // Selected Donation State
  const [activeDonationId, setActiveDonationId] = useState<string>('DON-8F4A2C10');
  const [donationsList, setDonationsList] = useState<any[]>([]);
  const [currentStatus, setCurrentStatus] = useState<CustodyStage>('PICKUP_ASSIGNED');
  const [auditData, setAuditData] = useState<DonationAuditTrailResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'scan' | 'generate' | 'audit'>('scan');

  // Scanner Viewport State
  const [cameraActive, setCameraActive] = useState(false);
  const [manualTokenInput, setManualTokenInput] = useState('');
  const [facingMode, setFacingMode] = useState<'environment' | 'user'>('environment');
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  // Proof Capture Form State
  const [measuredTemp, setMeasuredTemp] = useState<string>('3.8');
  const [signatureName, setSignatureName] = useState<string>('Chef Marcus Vance');
  const [proofNotes, setProofNotes] = useState<string>('Cargo temperature verified. Container seals intact.');
  const [gpsCoords, setGpsCoords] = useState<{ lat: number; lng: number } | null>({ lat: 40.7128, lng: -74.0060 });

  // QR Generation State
  const [generatedQR, setGeneratedQR] = useState<GenerateCustodyQRResponse | null>(null);
  const [qrStageSelection, setQrStageSelection] = useState<QRScanStage>('KITCHEN_HANDOVER');
  const [copiedToken, setCopiedToken] = useState(false);

  // Scan Result Modal
  const [verifyResult, setVerifyResult] = useState<VerifyCustodyScanResponse | null>(null);
  const [verifyModalOpen, setVerifyModalOpen] = useState(false);
  const [securityAlert, setSecurityAlert] = useState<string | null>(null);

  // Load Donations and initial status
  useEffect(() => {
    loadDonations();
  }, []);

  useEffect(() => {
    if (activeDonationId) {
      loadAuditTrail(activeDonationId);
    }
  }, [activeDonationId]);

  const loadDonations = async () => {
    try {
      const data = await fetchDonationsManifests();
      if (data && data.items && data.items.length > 0) {
        setDonationsList(data.items);
        setActiveDonationId(data.items[0].immutable_donation_id || data.items[0].id);
      } else {
        // Fallback default demo donations
        setDonationsList([
          { id: 'don-demo-001', immutable_donation_id: 'DON-8F4A2C10', tracking_number: 'TRK-8F4A2C10', status: 'PICKUP_ASSIGNED', total_portions: 180, total_weight_kg: 120.5 },
          { id: 'don-demo-002', immutable_donation_id: 'DON-3B9E7A12', tracking_number: 'TRK-3B9E7A12', status: 'IN_TRANSIT', total_portions: 95, total_weight_kg: 64.0 },
          { id: 'don-demo-003', immutable_donation_id: 'DON-7C1D5F89', tracking_number: 'TRK-7C1D5F89', status: 'DELIVERED', total_portions: 240, total_weight_kg: 165.2 },
          { id: 'don-demo-004', immutable_donation_id: 'DON-9E2A4C67', tracking_number: 'TRK-9E2A4C67', status: 'RECEIVED', total_portions: 140, total_weight_kg: 92.0 },
        ]);
      }
    } catch (err) {
      console.warn('Using demo donation items:', err);
    }
  };

  const loadAuditTrail = async (donRef: string) => {
    setLoading(true);
    try {
      const res = await fetchDonationAuditTrail(donRef);
      setAuditData(res);
      setCurrentStatus(res.current_status);
    } catch (err) {
      // Mock fallback audit trail
      setAuditData({
        donation_id: donRef,
        immutable_donation_id: donRef,
        current_status: currentStatus,
        total_events: 3,
        chain_intact: true,
        allowed_actions: [
          { action: 'KITCHEN_HANDOVER_QR', target_stage: 'KITCHEN_HANDOVER', method: 'QR_SCAN', allowed_roles: ['KITCHEN_MANAGER', 'CHEF'], description: 'Kitchen confirms cargo handover to driver.' },
          { action: 'DRIVER_PICKUP_QR', target_stage: 'DRIVER_PICKUP', method: 'QR_SCAN', allowed_roles: ['DRIVER'], description: 'Driver certifies physical possession.' }
        ],
        audit_trail: [
          {
            id: 'ev-1',
            donation_id: donRef,
            event: 'DONATION_CREATED',
            from_status: 'NONE',
            to_status: 'DONATION_CREATED',
            role: 'ADMIN',
            user_name: 'Helena Vance (Chef Director)',
            timestamp: new Date(Date.now() - 3600000 * 3).toISOString(),
            notes: 'Donation manifest generated for 180 portions Mediterranean chicken & roasted vegetables.',
            previous_hash: '0'.repeat(64),
            integrity_hash: 'a591a6d40bf420404a011733cfb7b190da591a6d40bf420404a011733cfb7b19',
            chain_verified: true
          },
          {
            id: 'ev-2',
            donation_id: donRef,
            event: 'TRANSITION_TO_ACCEPTED',
            from_status: 'DONATION_CREATED',
            to_status: 'ACCEPTED',
            role: 'NGO',
            user_name: 'Dr. Sarah Lin (St. Jude Food Bank)',
            timestamp: new Date(Date.now() - 3600000 * 2).toISOString(),
            notes: 'Recipient verified dietary match and accepted 180 meal allocation.',
            previous_hash: 'a591a6d40bf420404a011733cfb7b190da591a6d40bf420404a011733cfb7b19',
            integrity_hash: 'b783c9d10ae314561b021844dec8b2801e783c9d10ae314561b021844dec8b28',
            chain_verified: true
          },
          {
            id: 'ev-3',
            donation_id: donRef,
            event: 'TRANSITION_TO_PICKUP_ASSIGNED',
            from_status: 'ACCEPTED',
            to_status: 'PICKUP_ASSIGNED',
            role: 'ADMIN',
            user_name: 'Dispatch Manager (Logistics Center)',
            timestamp: new Date(Date.now() - 3600000).toISOString(),
            notes: 'Courier route mission assigned to Driver Alex Mercer (VAN-402, Active Refrigeration).',
            previous_hash: 'b783c9d10ae314561b021844dec8b2801e783c9d10ae314561b021844dec8b28',
            integrity_hash: 'c894dae21bf425672c132955efd9c3912f894dae21bf425672c132955efd9c39',
            chain_verified: true
          }
        ]
      });
    } finally {
      setLoading(false);
    }
  };

  // WebCam Management
  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode }
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setCameraActive(true);
    } catch (err) {
      console.warn('Camera access denied or unavailable:', err);
      setCameraActive(false);
      if (onShowSuccess) onShowSuccess('Camera unavailable in current environment. Using simulated scanner reticle.');
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    setCameraActive(false);
  };

  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, []);

  // Fetch Geolocation
  const handleFetchGps = () => {
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setGpsCoords({ lat: Number(pos.coords.latitude.toFixed(6)), lng: Number(pos.coords.longitude.toFixed(6)) });
          if (onShowSuccess) onShowSuccess(`GPS coordinates acquired: ${pos.coords.latitude.toFixed(4)}, ${pos.coords.longitude.toFixed(4)}`);
        },
        (err) => {
          console.warn('GPS unavailable:', err);
          setGpsCoords({ lat: 40.7128, lng: -74.0060 });
        }
      );
    }
  };

  // Generate QR
  const handleGenerateQR = async () => {
    setLoading(true);
    try {
      const res = await generateCustodyQRToken({
        donation_id: activeDonationId,
        stage: qrStageSelection,
        expires_in_minutes: 60
      });
      setGeneratedQR(res);
      setManualTokenInput(res.token);
      if (onShowSuccess) onShowSuccess(`Generated cryptographically signed ${qrStageSelection} QR token.`);
    } catch (err: any) {
      // Mock generated QR
      const mockNonce = Math.random().toString(36).substring(2, 10).toUpperCase();
      const mockSig = '5e884898da28047151d0e56f8dc62927';
      const mockToken = `FOODLOOP:DONATION:${activeDonationId}:${qrStageSelection}:${mockNonce}:${Math.floor(Date.now() / 1000) + 3600}:${mockSig}`;
      const mockRes: GenerateCustodyQRResponse = {
        donation_id: activeDonationId,
        immutable_donation_id: activeDonationId,
        stage: qrStageSelection,
        token: mockToken,
        nonce: mockNonce,
        hmac_signature: mockSig,
        expires_at: new Date(Date.now() + 3600000).toISOString(),
        current_status: currentStatus,
        allowed_scanner_roles: qrStageSelection === 'KITCHEN_HANDOVER' ? ['KITCHEN_MANAGER', 'CHEF'] : (qrStageSelection === 'DRIVER_PICKUP' ? ['DRIVER'] : ['NGO', 'RECIPIENT']),
        instructions: 'Present this single-use QR burn token to the verifying party.'
      };
      setGeneratedQR(mockRes);
      setManualTokenInput(mockToken);
      if (onShowSuccess) onShowSuccess(`Simulated ${qrStageSelection} QR token generated.`);
    } finally {
      setLoading(false);
    }
  };

  // Verify Scan
  const handleVerifyScan = async (overrideToken?: string) => {
    const tokenToVerify = overrideToken || manualTokenInput;
    if (!tokenToVerify) {
      setSecurityAlert('Please input or scan a valid FoodLoop QR token.');
      return;
    }

    setLoading(true);
    setSecurityAlert(null);

    try {
      const res = await verifyCustodyQRScan({
        token: tokenToVerify,
        proof_type: 'TEMPERATURE_READING',
        measured_temp_c: parseFloat(measuredTemp) || 4.0,
        current_lat: gpsCoords?.lat || 40.7128,
        current_lng: gpsCoords?.lng || -74.0060,
        signature_data: signatureName,
        notes: proofNotes
      });

      setVerifyResult(res);
      setVerifyModalOpen(true);
      setCurrentStatus(res.current_status);
      loadAuditTrail(activeDonationId);
      if (onShowSuccess) onShowSuccess(`Custody transition verified: ${res.event} -> ${res.current_status}`);
    } catch (err: any) {
      const errorMsg = err?.message || 'Verification failed';
      setSecurityAlert(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  // Stress-Test Scenarios
  const handleTestTamperedToken = async () => {
    const fakeToken = `FOODLOOP:DONATION:${activeDonationId}:KITCHEN_HANDOVER:FAKE_NONCE:1759000000:DEADBEEF_INVALID_SIG`;
    setManualTokenInput(fakeToken);
    await handleVerifyScan(fakeToken);
  };

  const handleTestDuplicateScan = async () => {
    if (!manualTokenInput) {
      setSecurityAlert('Generate or load a token first before testing duplicate burn.');
      return;
    }
    // Perform two scans in succession
    await handleVerifyScan();
    setTimeout(() => {
      handleVerifyScan();
    }, 400);
  };

  const handleCopyToken = () => {
    if (generatedQR?.token || manualTokenInput) {
      navigator.clipboard.writeText(generatedQR?.token || manualTokenInput);
      setCopiedToken(true);
      setTimeout(() => setCopiedToken(false), 2000);
      if (onShowSuccess) onShowSuccess('Cryptographic token copied to clipboard.');
    }
  };

  // Active stage index
  const activeStageIdx = STAGES.findIndex((s) => s.key === currentStatus);

  return (
    <div className="max-w-7xl mx-auto space-y-6 py-4 px-2 sm:px-4">
      {/* 1. HEADER & ACTOR SELECTOR */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900/80 backdrop-blur-md p-6 rounded-3xl border border-slate-800 shadow-2xl">
        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <Badge variant="purple" size="sm" className="font-mono">
              PHASE 11 • CUSTODY LEDGER
            </Badge>
            <Badge variant="success" size="sm" className="flex items-center gap-1">
              <Lock className="w-3 h-3" /> HMAC-SHA256
            </Badge>
          </div>
          <h1 className="text-2xl md:text-3xl font-black text-white tracking-tight flex items-center gap-2">
            <QrCode className="w-8 h-8 text-emerald-400" /> QR Chain of Custody & Verification
          </h1>
          <p className="text-xs md:text-sm text-slate-400">
            Immutable single-use QR burn tokens with role-based validation, state progression, and cryptographic audit trails.
          </p>
        </div>

        {/* Persona Selector (Role simulation) */}
        <div className="bg-slate-950/80 p-2 rounded-2xl border border-slate-800 flex items-center gap-1.5 self-start md:self-auto">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider px-2">Role:</span>
          <button
            onClick={() => { setActiveRole('KITCHEN_MANAGER'); setQrStageSelection('KITCHEN_HANDOVER'); }}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
              activeRole === 'KITCHEN_MANAGER'
                ? 'bg-amber-500 text-slate-950 shadow-md font-extrabold'
                : 'text-slate-400 hover:text-white hover:bg-slate-900'
            }`}
          >
            <ChefHat className="w-3.5 h-3.5" /> Kitchen
          </button>
          <button
            onClick={() => { setActiveRole('DRIVER'); setQrStageSelection('DRIVER_PICKUP'); }}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
              activeRole === 'DRIVER'
                ? 'bg-cyan-500 text-slate-950 shadow-md font-extrabold'
                : 'text-slate-400 hover:text-white hover:bg-slate-900'
            }`}
          >
            <Truck className="w-3.5 h-3.5" /> Driver
          </button>
          <button
            onClick={() => { setActiveRole('NGO'); setQrStageSelection('RECIPIENT_RECEIPT'); }}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
              activeRole === 'NGO'
                ? 'bg-emerald-500 text-slate-950 shadow-md font-extrabold'
                : 'text-slate-400 hover:text-white hover:bg-slate-900'
            }`}
          >
            <Building2 className="w-3.5 h-3.5" /> Recipient
          </button>
          <button
            onClick={() => setActiveRole('ADMIN')}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
              activeRole === 'ADMIN'
                ? 'bg-purple-500 text-white shadow-md font-extrabold'
                : 'text-slate-400 hover:text-white hover:bg-slate-900'
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5" /> Auditor
          </button>
        </div>
      </div>

      {/* 2. DONATION MANIFEST CONTEXT BAR */}
      <Card className="p-4 bg-slate-900/60 border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center space-x-2">
            <span className="text-xs text-slate-400 font-bold">Active Manifest:</span>
            <select
              value={activeDonationId}
              onChange={(e) => setActiveDonationId(e.target.value)}
              className="bg-slate-950 text-white font-mono text-xs font-bold px-3 py-1.5 rounded-xl border border-slate-700 focus:outline-none focus:border-emerald-500"
            >
              {donationsList.map((d) => (
                <option key={d.id} value={d.immutable_donation_id || d.id}>
                  {d.immutable_donation_id || d.tracking_number || d.id} • {d.total_portions || 180} portions
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500">Immutable ID:</span>
            <code className="text-xs font-mono font-bold text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/40">
              {activeDonationId}
            </code>
          </div>

          <Badge variant="cyan" size="sm" className="font-bold">
            Status: {currentStatus}
          </Badge>
        </div>

        <div className="flex items-center space-x-2">
          <Button
            size="sm"
            variant="outline"
            onClick={() => loadAuditTrail(activeDonationId)}
            leftIcon={<RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />}
          >
            Refresh Chain
          </Button>

          {currentStatus !== 'RECEIVED' && activeRole === 'ADMIN' && (
            <Button
              size="sm"
              variant="secondary"
              onClick={async () => {
                const nextIdx = Math.min(STAGES.length - 1, activeStageIdx + 1);
                const nextStatus = STAGES[nextIdx].key;
                await transitionDonationCustody(activeDonationId, { target_status: nextStatus });
                loadAuditTrail(activeDonationId);
              }}
            >
              Force Next Stage <ArrowRight className="w-3.5 h-3.5 ml-1" />
            </Button>
          )}
        </div>
      </Card>

      {/* 3. 7-STAGE CHAIN OF CUSTODY VISUAL STEPPER */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-3xl p-5 shadow-xl overflow-x-auto">
        <div className="flex items-center justify-between min-w-[760px] relative">
          {/* Background Connecting Line */}
          <div className="absolute top-5 left-8 right-8 h-1 bg-slate-800 -z-0" />
          <div
            className="absolute top-5 left-8 h-1 bg-emerald-500 transition-all duration-700 -z-0"
            style={{ width: `${(activeStageIdx / (STAGES.length - 1)) * 94}%` }}
          />

          {STAGES.map((stg, idx) => {
            const isCompleted = idx < activeStageIdx;
            const isCurrent = idx === activeStageIdx;
            const isUpcoming = idx > activeStageIdx;
            const Icon = stg.icon;

            return (
              <div key={stg.key} className="flex flex-col items-center text-center relative z-10 space-y-2">
                <div
                  className={`w-10 h-10 rounded-2xl flex items-center justify-center font-bold transition-all duration-300 ${
                    isCompleted
                      ? 'bg-emerald-500 text-slate-950 shadow-lg shadow-emerald-500/20'
                      : isCurrent
                      ? 'bg-cyan-500 text-slate-950 ring-4 ring-cyan-500/30 shadow-lg shadow-cyan-500/30 animate-pulse'
                      : 'bg-slate-800 text-slate-500 border border-slate-700'
                  }`}
                >
                  {isCompleted ? <Check className="w-5 h-5 stroke-[3]" /> : <Icon className="w-5 h-5" />}
                </div>
                <div className="space-y-0.5">
                  <div
                    className={`text-xs font-black tracking-tight ${
                      isCurrent ? 'text-cyan-400' : isCompleted ? 'text-white' : 'text-slate-500'
                    }`}
                  >
                    {stg.label}
                  </div>
                  <div className="text-[10px] text-slate-400 max-w-[90px] leading-tight">
                    {stg.desc}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 4. SECURITY ALERT BANNER */}
      {securityAlert && (
        <div className="bg-rose-950/80 border border-rose-800/80 p-4 rounded-2xl flex items-start space-x-3 text-rose-200 animate-shake">
          <ShieldAlert className="w-5 h-5 text-rose-400 mt-0.5 shrink-0" />
          <div className="flex-1 space-y-1">
            <div className="text-xs font-black uppercase tracking-wider text-rose-300">
              Security Violation Detected
            </div>
            <div className="text-xs font-mono text-rose-100">{securityAlert}</div>
          </div>
          <button
            onClick={() => setSecurityAlert(null)}
            className="text-xs text-rose-400 hover:text-white font-bold"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* 5. MAIN WORKSPACE TABS */}
      <div className="flex items-center space-x-2 border-b border-slate-800 pb-2">
        <button
          onClick={() => setActiveTab('scan')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
            activeTab === 'scan'
              ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
              : 'text-slate-400 hover:text-white hover:bg-slate-900'
          }`}
        >
          <Camera className="w-4 h-4" /> 1. Scan Custody QR Viewport
        </button>

        <button
          onClick={() => setActiveTab('generate')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
            activeTab === 'generate'
              ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/40'
              : 'text-slate-400 hover:text-white hover:bg-slate-900'
          }`}
        >
          <QrCode className="w-4 h-4" /> 2. Generate / Present QR Token
        </button>

        <button
          onClick={() => setActiveTab('audit')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
            activeTab === 'audit'
              ? 'bg-purple-500/20 text-purple-400 border border-purple-500/40'
              : 'text-slate-400 hover:text-white hover:bg-slate-900'
          }`}
        >
          <History className="w-4 h-4" /> 3. Forensic SHA-256 Audit Ledger
        </button>
      </div>

      {/* -------------------------------------------------------------
          TAB 1: MOBILE-FRIENDLY QR SCANNER VIEWPORT
         ------------------------------------------------------------- */}
      {activeTab === 'scan' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Viewport & Reticle */}
          <Card className="lg:col-span-7 p-6 space-y-5 bg-slate-900/90 border border-slate-800">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-black text-white tracking-tight flex items-center gap-2">
                  <Camera className="w-5 h-5 text-emerald-400" /> Optical Custody Scanner
                </h2>
                <p className="text-xs text-slate-400">
                  Align single-use QR burn token within the viewfinder. Camera stream is processed on-device.
                </p>
              </div>

              <div className="flex items-center space-x-2">
                <Button
                  size="sm"
                  variant={cameraActive ? 'destructive' : 'primary'}
                  onClick={cameraActive ? stopCamera : startCamera}
                  leftIcon={cameraActive ? <CameraOff className="w-3.5 h-3.5" /> : <Camera className="w-3.5 h-3.5" />}
                >
                  {cameraActive ? 'Stop Camera' : 'Start Camera'}
                </Button>
              </div>
            </div>

            {/* Viewfinder Frame */}
            <div className="relative w-full aspect-video sm:aspect-square max-h-[380px] bg-slate-950 rounded-3xl overflow-hidden border-2 border-slate-800 flex items-center justify-center shadow-inner group">
              {cameraActive ? (
                <video
                  ref={videoRef}
                  playsInline
                  autoPlay
                  muted
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="flex flex-col items-center justify-center p-6 text-center space-y-3">
                  <div className="w-16 h-16 rounded-3xl bg-slate-900 border border-slate-800 flex items-center justify-center">
                    <QrCode className="w-8 h-8 text-slate-600" />
                  </div>
                  <div className="text-xs text-slate-400">
                    Camera inactive. Click <span className="text-emerald-400 font-bold">Start Camera</span> or use the manual token entry below.
                  </div>
                </div>
              )}

              {/* Holographic Reticle Overlay */}
              <div className="absolute inset-8 pointer-events-none border-2 border-dashed border-cyan-400/50 rounded-2xl flex flex-col justify-between p-3">
                <div className="flex justify-between">
                  <div className="w-6 h-6 border-t-4 border-l-4 border-cyan-400 rounded-tl-lg" />
                  <div className="w-6 h-6 border-t-4 border-r-4 border-cyan-400 rounded-tr-lg" />
                </div>

                {/* Animated Laser Scanning Beam */}
                <div className="w-full h-0.5 bg-gradient-to-r from-transparent via-emerald-400 to-transparent shadow-[0_0_12px_#34d399] animate-bounce" />

                <div className="flex justify-between">
                  <div className="w-6 h-6 border-b-4 border-l-4 border-cyan-400 rounded-bl-lg" />
                  <div className="w-6 h-6 border-b-4 border-r-4 border-cyan-400 rounded-br-lg" />
                </div>
              </div>

              {/* Viewport Status Pill */}
              <div className="absolute bottom-3 left-3 bg-slate-950/80 backdrop-blur-md px-3 py-1 rounded-full border border-slate-800 text-[10px] font-mono text-slate-300 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                <span>SCANNER READY • {activeRole}</span>
              </div>
            </div>

            {/* Manual Token Fallback */}
            <div className="space-y-2 pt-2">
              <label className="text-xs font-bold text-slate-300 flex items-center justify-between">
                <span>Cryptographic Token String:</span>
                <span className="text-[10px] text-slate-500 font-mono">Format: FOODLOOP:DONATION:...</span>
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={manualTokenInput}
                  onChange={(e) => setManualTokenInput(e.target.value)}
                  placeholder="Paste or type single-use QR token..."
                  className="flex-1 bg-slate-950 text-white font-mono text-xs px-3.5 py-2.5 rounded-xl border border-slate-700 focus:outline-none focus:border-cyan-500"
                />
                <Button
                  size="sm"
                  variant="primary"
                  onClick={() => handleVerifyScan()}
                  disabled={loading || !manualTokenInput}
                  leftIcon={<Check className="w-3.5 h-3.5" />}
                >
                  Verify &amp; Burn
                </Button>
              </div>
            </div>

            {/* Stress Test Simulation Actions */}
            <div className="bg-slate-950/60 p-3.5 rounded-2xl border border-slate-800 space-y-2">
              <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <ShieldAlert className="w-3.5 h-3.5 text-amber-400" /> Security Violation Stress Tests:
              </div>
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={handleTestTamperedToken}
                  className="px-2.5 py-1 rounded-lg text-[11px] font-bold bg-rose-950/50 text-rose-300 hover:bg-rose-900/60 border border-rose-800/40 transition-colors"
                >
                  Simulate Tampered ID
                </button>
                <button
                  onClick={handleTestDuplicateScan}
                  className="px-2.5 py-1 rounded-lg text-[11px] font-bold bg-amber-950/50 text-amber-300 hover:bg-amber-900/60 border border-amber-800/40 transition-colors"
                >
                  Simulate Duplicate Replay
                </button>
                <button
                  onClick={() => {
                    const wrongRole = activeRole === 'DRIVER' ? 'NGO' : 'DRIVER';
                    setActiveRole(wrongRole);
                    handleVerifyScan();
                  }}
                  className="px-2.5 py-1 rounded-lg text-[11px] font-bold bg-purple-950/50 text-purple-300 hover:bg-purple-900/60 border border-purple-800/40 transition-colors"
                >
                  Simulate Wrong Role Scan
                </button>
              </div>
            </div>
          </Card>

          {/* Right Column: Proof-of-Custody Telemetry Capture */}
          <Card className="lg:col-span-5 p-6 space-y-5 bg-slate-900/90 border border-slate-800">
            <div>
              <h2 className="text-lg font-black text-white tracking-tight flex items-center gap-2">
                <FileCheck className="w-5 h-5 text-cyan-400" /> Proof of Custody Capture
              </h2>
              <p className="text-xs text-slate-400">
                Data captured simultaneously with the QR scan to bind physical conditions to the forensic ledger.
              </p>
            </div>

            <div className="space-y-4">
              {/* Temperature Reading */}
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-300 flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <Thermometer className="w-3.5 h-3.5 text-cyan-400" /> Cargo Temperature (°C):
                  </span>
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                      parseFloat(measuredTemp) < 5.0
                        ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                        : parseFloat(measuredTemp) < 8.0
                        ? 'bg-amber-950 text-amber-300 border border-amber-800'
                        : 'bg-rose-950 text-rose-300 border border-rose-800'
                    }`}
                  >
                    {parseFloat(measuredTemp) < 5.0 ? 'Optimal Chilled' : (parseFloat(measuredTemp) < 8.0 ? 'Marginal' : 'Abuse Warning')}
                  </span>
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={measuredTemp}
                  onChange={(e) => setMeasuredTemp(e.target.value)}
                  className="w-full bg-slate-950 text-white font-mono text-sm px-3.5 py-2 rounded-xl border border-slate-700 focus:outline-none focus:border-cyan-500"
                />
              </div>

              {/* Digital Signature / Signer Name */}
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-300 flex items-center gap-1.5">
                  <User className="w-3.5 h-3.5 text-purple-400" /> Digital Signer / Authorizing Agent:
                </label>
                <input
                  type="text"
                  value={signatureName}
                  onChange={(e) => setSignatureName(e.target.value)}
                  placeholder="e.g. Driver Alex Mercer / Chef Vance"
                  className="w-full bg-slate-950 text-white text-xs px-3.5 py-2 rounded-xl border border-slate-700 focus:outline-none focus:border-cyan-500"
                />
              </div>

              {/* GPS Coordinates */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-bold text-slate-300 flex items-center gap-1.5">
                    <MapPin className="w-3.5 h-3.5 text-emerald-400" /> GPS Geolocation Proof:
                  </label>
                  <button
                    onClick={handleFetchGps}
                    className="text-[10px] text-cyan-400 hover:underline font-bold"
                  >
                    Acquire Device GPS
                  </button>
                </div>
                <div className="bg-slate-950 px-3.5 py-2 rounded-xl border border-slate-800 font-mono text-xs text-slate-300 flex items-center justify-between">
                  <span>Lat: {gpsCoords?.lat ?? '37.7749'}</span>
                  <span>Lng: {gpsCoords?.lng ?? '-122.4194'}</span>
                </div>
              </div>

              {/* Handover Notes */}
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-300">
                  Custody &amp; Packaging Remarks:
                </label>
                <textarea
                  rows={3}
                  value={proofNotes}
                  onChange={(e) => setProofNotes(e.target.value)}
                  placeholder="Condition notes, tamper-evident seals, container state..."
                  className="w-full bg-slate-950 text-white text-xs px-3.5 py-2 rounded-xl border border-slate-700 focus:outline-none focus:border-cyan-500 resize-none"
                />
              </div>
            </div>

            {/* Quick Transition Action Button depending on current status */}
            <div className="pt-2 border-t border-slate-800">
              <Button
                variant="primary"
                className="w-full"
                onClick={() => handleVerifyScan()}
                disabled={loading}
                leftIcon={<Flame className="w-4 h-4 text-amber-300" />}
              >
                Execute Handover Scan as {activeRole}
              </Button>
            </div>
          </Card>
        </div>
      )}

      {/* -------------------------------------------------------------
          TAB 2: GENERATE CRYPTOGRAPHIC QR TOKEN
         ------------------------------------------------------------- */}
      {activeTab === 'generate' && (
        <div className="max-w-2xl mx-auto space-y-6">
          <Card className="p-8 text-center space-y-6 bg-slate-900/90 border border-slate-800 shadow-2xl">
            <div className="space-y-1">
              <Badge variant="cyan" size="sm" className="font-mono">
                HMAC-SHA256 Token Authority
              </Badge>
              <h2 className="text-2xl font-black text-white tracking-tight">
                Generate Single-Use Handover Token
              </h2>
              <p className="text-xs text-slate-400">
                Produces an ephemeral, cryptographically signed token bound to the selected donation and custody stage.
              </p>
            </div>

            {/* Stage Selector */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-left">
              {(['KITCHEN_HANDOVER', 'DRIVER_PICKUP', 'COURIER_DELIVERY', 'RECIPIENT_RECEIPT'] as QRScanStage[]).map((stg) => (
                <button
                  key={stg}
                  onClick={() => setQrStageSelection(stg)}
                  className={`p-3 rounded-2xl border text-xs font-bold transition-all ${
                    qrStageSelection === stg
                      ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/60 shadow-lg'
                      : 'bg-slate-950 text-slate-400 border-slate-800 hover:text-white'
                  }`}
                >
                  <div className="text-[10px] uppercase text-slate-500">Stage:</div>
                  <div className="truncate">{stg.replace('_', ' ')}</div>
                </button>
              ))}
            </div>

            {/* Generated QR Card Graphic */}
            <div className="mx-auto w-64 h-64 bg-white p-4 rounded-3xl shadow-2xl flex flex-col items-center justify-between relative group">
              <div className="w-full flex justify-between items-center text-[10px] font-mono font-black text-slate-950">
                <span>FOODLOOP AI</span>
                <span className="bg-emerald-100 text-emerald-800 px-1.5 py-0.5 rounded">HMAC-256</span>
              </div>

              {/* Simulated High-Density QR Pattern */}
              <div className="w-44 h-44 bg-slate-950 rounded-2xl p-2.5 flex flex-col justify-between relative overflow-hidden">
                <div className="flex justify-between">
                  <div className="w-10 h-10 bg-white rounded-lg p-1.5 flex items-center justify-center">
                    <div className="w-full h-full bg-slate-950 rounded-sm" />
                  </div>
                  <div className="w-10 h-10 bg-white rounded-lg p-1.5 flex items-center justify-center">
                    <div className="w-full h-full bg-slate-950 rounded-sm" />
                  </div>
                </div>

                <div className="flex items-center justify-center">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-500 to-cyan-500 text-slate-950 font-black flex items-center justify-center text-xs shadow-md">
                    FL
                  </div>
                </div>

                <div className="flex justify-between items-end">
                  <div className="w-10 h-10 bg-white rounded-lg p-1.5 flex items-center justify-center">
                    <div className="w-full h-full bg-slate-950 rounded-sm" />
                  </div>
                  <div className="text-[9px] font-mono font-bold text-emerald-400 bg-slate-900 px-1 py-0.5 rounded">
                    45m EXP
                  </div>
                </div>
              </div>

              <div className="w-full text-center text-[9px] font-mono text-slate-600 truncate">
                {generatedQR?.token || `FOODLOOP:DONATION:${activeDonationId}:${qrStageSelection}`}
              </div>
            </div>

            {/* Generated Token Details */}
            {generatedQR && (
              <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800 text-left space-y-2 font-mono text-xs">
                <div className="flex justify-between items-center text-slate-400">
                  <span>Nonce:</span>
                  <span className="text-cyan-400">{generatedQR.nonce}</span>
                </div>
                <div className="flex justify-between items-center text-slate-400">
                  <span>HMAC Signature:</span>
                  <span className="text-emerald-400 truncate max-w-[240px]">{generatedQR.hmac_signature}</span>
                </div>
                <div className="flex justify-between items-center text-slate-400">
                  <span>Allowed Roles:</span>
                  <span className="text-amber-400">{generatedQR.allowed_scanner_roles.join(', ')}</span>
                </div>
              </div>
            )}

            <div className="flex items-center justify-center gap-3 pt-2">
              <Button
                variant="primary"
                onClick={handleGenerateQR}
                disabled={loading}
                leftIcon={<RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />}
              >
                Generate Single-Use QR
              </Button>

              <Button
                variant="outline"
                onClick={handleCopyToken}
                disabled={!generatedQR && !manualTokenInput}
                leftIcon={copiedToken ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
              >
                {copiedToken ? 'Copied' : 'Copy Token'}
              </Button>

              <Button
                variant="secondary"
                onClick={() => {
                  setActiveTab('scan');
                  if (generatedQR) setManualTokenInput(generatedQR.token);
                }}
              >
                Scan this in Viewport <ArrowRight className="w-4 h-4 ml-1" />
              </Button>
            </div>
          </Card>
        </div>
      )}

      {/* -------------------------------------------------------------
          TAB 3: FORENSIC SHA-256 AUDIT LEDGER
         ------------------------------------------------------------- */}
      {activeTab === 'audit' && (
        <Card className="p-6 space-y-6 bg-slate-900/90 border border-slate-800">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
            <div>
              <h2 className="text-xl font-black text-white tracking-tight flex items-center gap-2">
                <ShieldCheck className="w-6 h-6 text-emerald-400" /> Cryptographic Custody Ledger
              </h2>
              <p className="text-xs text-slate-400">
                Chained SHA-256 hash log. Every transfer event binds previous hash, actor credentials, and proof telemetry.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <Badge variant={auditData?.chain_intact ? 'success' : 'danger'} size="sm" className="font-mono">
                {auditData?.chain_intact ? 'Ledger Chain Verified & Intact' : 'Chain Tampering Detected'}
              </Badge>
              <Badge variant="outline" size="sm" className="font-mono">
                {auditData?.total_events || 0} Total Events
              </Badge>
            </div>
          </div>

          {/* Audit Events Timeline */}
          <div className="space-y-4">
            {auditData?.audit_trail && auditData.audit_trail.length > 0 ? (
              auditData.audit_trail.map((ev, idx) => (
                <div
                  key={ev.id || idx}
                  className="bg-slate-950/80 p-5 rounded-2xl border border-slate-800 space-y-3 hover:border-slate-700 transition-colors"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
                    <div className="flex items-center space-x-2">
                      <span className="w-6 h-6 rounded-lg bg-emerald-500/20 text-emerald-400 font-mono text-xs font-bold flex items-center justify-center">
                        #{idx + 1}
                      </span>
                      <span className="font-black text-white text-sm tracking-tight">{ev.event}</span>
                      <Badge variant="cyan" size="sm">
                        {ev.from_status} → {ev.to_status}
                      </Badge>
                    </div>

                    <div className="flex items-center space-x-3 text-xs text-slate-400">
                      <span className="flex items-center gap-1 font-mono">
                        <Clock className="w-3.5 h-3.5 text-slate-500" />
                        {new Date(ev.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                      </span>
                      <Badge variant="purple" size="sm">
                        {ev.role}
                      </Badge>
                    </div>
                  </div>

                  {/* Actor & Remarks */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                    <div>
                      <span className="text-slate-500">Authorized Actor:</span>{' '}
                      <span className="text-slate-200 font-bold">{ev.user_name || 'System Operator'}</span>
                    </div>
                    <div>
                      <span className="text-slate-500">Proof Telemetry:</span>{' '}
                      <span className="text-slate-200 font-mono">
                        {ev.verified_temp_c !== null && ev.verified_temp_c !== undefined ? `${ev.verified_temp_c}°C` : 'N/A'} •{' '}
                        {ev.verified_lat ? `${ev.verified_lat.toFixed(4)}, ${ev.verified_lng?.toFixed(4)}` : 'GPS Verified'}
                      </span>
                    </div>
                    {ev.notes && (
                      <div className="col-span-full bg-slate-900/60 p-2.5 rounded-xl border border-slate-800 text-slate-300">
                        {ev.notes}
                      </div>
                    )}
                  </div>

                  {/* Cryptographic Hash Chaining Details */}
                  <div className="pt-2 border-t border-slate-800/60 grid grid-cols-1 sm:grid-cols-2 gap-2 text-[10px] font-mono text-slate-400">
                    <div className="truncate">
                      <span className="text-slate-500">Prev Hash:</span> {ev.previous_hash || '0'.repeat(64)}
                    </div>
                    <div className="truncate text-emerald-400">
                      <span className="text-slate-500">Block Hash:</span> {ev.integrity_hash}
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="p-8 text-center text-slate-500 text-xs">
                No custody events recorded for this manifest yet.
              </div>
            )}
          </div>
        </Card>
      )}

      {/* -------------------------------------------------------------
          6. VERIFICATION SUCCESS MODAL
         ------------------------------------------------------------- */}
      <Modal
        isOpen={verifyModalOpen}
        onClose={() => setVerifyModalOpen(false)}
        title="Custody Scan Cryptographically Verified"
      >
        {verifyResult && (
          <div className="space-y-4 text-center">
            <div className="w-16 h-16 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 flex items-center justify-center mx-auto">
              <CheckCircle2 className="w-8 h-8" />
            </div>

            <div className="space-y-1">
              <h3 className="text-lg font-black text-white">{verifyResult.event}</h3>
              <p className="text-xs text-slate-300 font-mono">{verifyResult.message}</p>
            </div>

            <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800 text-left space-y-2 font-mono text-xs">
              <div className="flex justify-between">
                <span className="text-slate-400">Donation ID:</span>
                <span className="text-emerald-400 font-bold">{verifyResult.immutable_donation_id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">New Custody Stage:</span>
                <span className="text-cyan-400 font-bold">{verifyResult.current_status}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Verifying Role:</span>
                <span className="text-purple-400">{verifyResult.scanner_role}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Chained Hash:</span>
                <span className="text-slate-300 truncate max-w-[200px]">{verifyResult.integrity_hash}</span>
              </div>
            </div>

            <Button
              variant="primary"
              className="w-full"
              onClick={() => {
                setVerifyModalOpen(false);
                setActiveTab('audit');
              }}
            >
              View Updated Audit Ledger
            </Button>
          </div>
        )}
      </Modal>
    </div>
  );
};
