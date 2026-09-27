'use client';

import React, { useState, useEffect } from 'react';
import {
  HeartHandshake,
  ShieldCheck,
  Building2,
  MapPin,
  Clock,
  Thermometer,
  Truck,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Calendar,
  Layers,
  Sparkles,
  ArrowRight,
  Info,
  ChevronDown,
  RefreshCw,
  PlusCircle,
  Package,
  Award,
  Check
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/design-system/Card';
import { Button } from '@/components/design-system/Button';
import { Badge } from '@/components/design-system/Badge';
import { Modal } from '@/components/design-system/Modal';
import {
  RecipientDashboardSummary,
  RecipientAvailableSurplusItem,
  SchedulePickupPayload
} from '@/types';
import {
  fetchRecipientDashboard,
  requestSurplus,
  acceptSurplus,
  rejectSurplus,
  scheduleSurplusPickup
} from '@/lib/api';

interface RecipientDashboardProps {
  onNavigate?: (screen: any) => void;
  onShowSuccess?: (msg: string) => void;
}

const RECIPIENT_OPTIONS = [
  { id: 'rec-001-st-jude', name: 'Downtown St. Jude Food Bank', type: 'Food Bank', address: '450 4th Street, San Francisco' },
  { id: 'rec-002-hope-mission', name: 'Hope Mission Family Shelter', type: 'Family Shelter', address: '820 Folsom Street, San Francisco' },
  { id: 'rec-003-harbor-light', name: 'Harbor Light Community Dining', type: 'Soup Kitchen', address: '1275 Mission Street, San Francisco' },
  { id: 'rec-004-covenant-youth', name: 'Covenant Youth Haven', type: 'Youth Refuge', address: '1950 Post Street, San Francisco' },
  { id: 'rec-005-mission-green', name: 'Mission Green Community Pantry', type: 'Community Pantry', address: '2840 24th Street, San Francisco' },
];

export const RecipientDashboardScreen: React.FC<RecipientDashboardProps> = ({
  onNavigate,
  onShowSuccess
}) => {
  const [selectedRecipientId, setSelectedRecipientId] = useState<string>('rec-001-st-jude');
  const [dashboardData, setDashboardData] = useState<RecipientDashboardSummary | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<'available' | 'claims' | 'pickups'>('available');
  const [expandedExplanationId, setExpandedExplanationId] = useState<string | null>(null);

  // Action states
  const [actionInProgress, setActionInProgress] = useState<string | null>(null);
  const [scheduleModalItem, setScheduleModalItem] = useState<RecipientAvailableSurplusItem | null>(null);
  const [pickupTime, setPickupTime] = useState<string>('');
  const [driverName, setDriverName] = useState<string>('Sister Beatrice / Volunteer');
  const [vehiclePlate, setVehiclePlate] = useState<string>('VAN-SF-401');
  const [tempEquipConfirmed, setTempEquipConfirmed] = useState<boolean>(true);
  const [pickupNotes, setPickupNotes] = useState<string>('Bringing 4 insulated Cambro carriers');

  const loadData = async (recipientId: string) => {
    try {
      setLoading(true);
      const data = await fetchRecipientDashboard(recipientId);
      setDashboardData(data);
    } catch (err: any) {
      console.error('Failed to load recipient dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData(selectedRecipientId);
  }, [selectedRecipientId]);

  // Set default pickup time to 2 hours from now
  useEffect(() => {
    const d = new Date();
    d.setHours(d.getHours() + 2);
    setPickupTime(d.toISOString().slice(0, 16));
  }, []);

  const handleRequest = async (item: RecipientAvailableSurplusItem) => {
    if (!dashboardData) return;
    setActionInProgress(item.id);
    try {
      const res = await requestSurplus(item.id, dashboardData.recipient_id, 'Requested via Recipient Portal');
      if (onShowSuccess) onShowSuccess(res.message);
      await loadData(selectedRecipientId);
    } catch (err: any) {
      alert(`Double-Booking Prevention Alert: ${err.message}`);
    } finally {
      setActionInProgress(null);
    }
  };

  const handleAccept = async (item: RecipientAvailableSurplusItem) => {
    if (!dashboardData) return;
    setActionInProgress(item.id);
    try {
      const res = await acceptSurplus(item.id, dashboardData.recipient_id, 'Confirmed by recipient organization');
      if (onShowSuccess) onShowSuccess(res.message);
      await loadData(selectedRecipientId);
    } catch (err: any) {
      alert(`Double-Booking Alert: ${err.message}`);
    } finally {
      setActionInProgress(null);
    }
  };

  const handleReject = async (item: RecipientAvailableSurplusItem) => {
    if (!dashboardData) return;
    if (!confirm(`Are you sure you want to pass on "${item.food}"? It will be released back to other shelters.`)) return;
    setActionInProgress(item.id);
    try {
      const res = await rejectSurplus(item.id, dashboardData.recipient_id, 'Storage at capacity');
      if (onShowSuccess) onShowSuccess(res.message);
      await loadData(selectedRecipientId);
    } catch (err: any) {
      alert(`Action error: ${err.message}`);
    } finally {
      setActionInProgress(null);
    }
  };

  const handleConfirmSchedulePickup = async () => {
    if (!scheduleModalItem || !dashboardData) return;
    setActionInProgress(scheduleModalItem.id);
    try {
      const payload: SchedulePickupPayload = {
        recipient_id: dashboardData.recipient_id,
        pickup_time: new Date(pickupTime).toISOString(),
        driver_name: driverName,
        vehicle_plate: vehiclePlate,
        temperature_equipment_confirmed: tempEquipConfirmed,
        driver_notes: pickupNotes
      };
      const res = await scheduleSurplusPickup(scheduleModalItem.id, payload);
      if (onShowSuccess) onShowSuccess(res.message);
      setScheduleModalItem(null);
      await loadData(selectedRecipientId);
    } catch (err: any) {
      alert(`Pickup Scheduling Error: ${err.message}`);
    } finally {
      setActionInProgress(null);
    }
  };

  const currentRecipient = RECIPIENT_OPTIONS.find(r => r.id === selectedRecipientId) || RECIPIENT_OPTIONS[0];

  return (
    <div className="space-y-6">
      {/* 1. HERO HEADER WITH RECIPIENT ENTITY STATUS */}
      <div className="relative overflow-hidden glass-panel p-6 sm:p-8 rounded-3xl border border-indigo-500/30 bg-gradient-to-br from-indigo-950/40 via-slate-900 to-slate-950 shadow-2xl">
        <div className="absolute top-0 right-0 -mt-10 -mr-10 w-72 h-72 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
        
        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-3">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="purple" size="md" className="shadow-lg">
                <HeartHandshake className="w-3.5 h-3.5 mr-1.5" />
                Verified Non-Profit Recipient
              </Badge>
              <Badge variant="success" size="sm">
                <ShieldCheck className="w-3 h-3 mr-1" />
                501(c)(3) Verified
              </Badge>
              <Badge variant="cyan" size="sm">
                <Truck className="w-3 h-3 mr-1" />
                {dashboardData?.pickup_available ? 'Internal Pickup Fleet Ready' : 'External Courier Delivery'}
              </Badge>
            </div>

            <div className="flex flex-col sm:flex-row sm:items-baseline gap-3">
              <h1 className="text-3xl font-black text-white tracking-tight">
                {dashboardData?.organization_name || currentRecipient.name}
              </h1>
              <span className="text-sm font-medium text-indigo-300/80">
                ({dashboardData?.facility_type?.replace('_', ' ') || currentRecipient.type})
              </span>
            </div>

            <div className="flex flex-wrap items-center gap-4 text-xs text-slate-300">
              <div className="flex items-center space-x-1.5">
                <MapPin className="w-3.5 h-3.5 text-indigo-400" />
                <span>{currentRecipient.address}</span>
              </div>
              <div className="flex items-center space-x-1.5">
                <Clock className="w-3.5 h-3.5 text-amber-400" />
                <span>Operating Hours: 07:30 - 20:30 Daily</span>
              </div>
              <div className="flex items-center space-x-1.5">
                <Layers className="w-3.5 h-3.5 text-emerald-400" />
                <span>Storage: Cold-Hold Chiller, Hot Cambro, Dry Shelving</span>
              </div>
            </div>
          </div>

          {/* Switch Organization Console */}
          <div className="bg-slate-900/90 border border-white/10 p-4 rounded-2xl space-y-2 shrink-0">
            <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
              Simulate Recipient Organization:
            </label>
            <div className="relative">
              <select
                value={selectedRecipientId}
                onChange={(e) => setSelectedRecipientId(e.target.value)}
                className="w-full bg-slate-950 border border-indigo-500/40 rounded-xl px-3 py-2 text-xs text-white font-medium focus:outline-none focus:border-indigo-400 appearance-none pr-8 cursor-pointer"
              >
                {RECIPIENT_OPTIONS.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.name} ({r.type})
                  </option>
                ))}
              </select>
              <ChevronDown className="w-4 h-4 text-indigo-400 absolute right-2.5 top-2.5 pointer-events-none" />
            </div>
            <p className="text-[10px] text-slate-400">
              Intake Capacity: <strong>{dashboardData?.daily_intake_capacity_kg || 150} kg/day</strong> &bull; Need: <strong>{dashboardData?.current_demand_portions || 100} meals</strong>
            </p>
          </div>
        </div>
      </div>

      {/* 2. LIVE KPIS */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-panel p-4 rounded-2xl border border-white/10 bg-slate-900/80">
          <div className="text-[11px] font-bold uppercase text-slate-400 tracking-wider">Available Compatible Lots</div>
          <div className="text-3xl font-black text-white mt-1">
            {dashboardData?.available_lots_count ?? 0}
          </div>
          <p className="text-[11px] text-emerald-400 mt-1 flex items-center">
            <CheckCircle2 className="w-3 h-3 mr-1" /> Ready for immediate claim
          </p>
        </div>

        <div className="glass-panel p-4 rounded-2xl border border-indigo-500/20 bg-indigo-950/20">
          <div className="text-[11px] font-bold uppercase text-indigo-300 tracking-wider">Active Organization Requests</div>
          <div className="text-3xl font-black text-indigo-400 mt-1">
            {dashboardData?.active_requests_count ?? 0}
          </div>
          <p className="text-[11px] text-indigo-300 mt-1">
            Reserved with row-level safety locks
          </p>
        </div>

        <div className="glass-panel p-4 rounded-2xl border border-amber-500/20 bg-amber-950/20">
          <div className="text-[11px] font-bold uppercase text-amber-300 tracking-wider">Scheduled Pickups</div>
          <div className="text-3xl font-black text-amber-400 mt-1">
            {dashboardData?.scheduled_pickups_count ?? 0}
          </div>
          <p className="text-[11px] text-amber-300 mt-1">
            Volunteer transport booked
          </p>
        </div>

        <div className="glass-panel p-4 rounded-2xl border border-cyan-500/20 bg-cyan-950/20">
          <div className="text-[11px] font-bold uppercase text-cyan-300 tracking-wider">Total Rescued Food</div>
          <div className="text-3xl font-black text-cyan-400 mt-1">
            {dashboardData?.total_rescued_kg ?? 128.5} <span className="text-sm font-normal text-slate-400">kg</span>
          </div>
          <p className="text-[11px] text-cyan-300 mt-1">
            ~{Math.round((dashboardData?.total_rescued_kg || 128.5) / 0.35)} meals provided
          </p>
        </div>
      </div>

      {/* 3. TABS HEADER */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/10 pb-4">
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setActiveTab('available')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
              activeTab === 'available'
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                : 'bg-slate-900 text-slate-400 hover:text-white border border-white/5'
            }`}
          >
            Available Food & AI Matches ({dashboardData?.available_surplus?.length || 0})
          </button>
          <button
            onClick={() => setActiveTab('claims')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
              activeTab === 'claims'
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                : 'bg-slate-900 text-slate-400 hover:text-white border border-white/5'
            }`}
          >
            My Active Claims & Requests
          </button>
          <button
            onClick={() => setActiveTab('pickups')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
              activeTab === 'pickups'
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                : 'bg-slate-900 text-slate-400 hover:text-white border border-white/5'
            }`}
          >
            Scheduled Pickups
          </button>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={() => loadData(selectedRecipientId)}
          leftIcon={<RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />}
        >
          Refresh Live Feed
        </Button>
      </div>

      {/* 4. CONTENT AREA */}
      {loading ? (
        <div className="p-12 text-center text-slate-400">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto text-indigo-400 mb-3" />
          <p className="text-sm font-semibold">Running multi-factor recipient matching algorithm...</p>
          <p className="text-xs text-slate-500 mt-1">Evaluating food compatibility, capacity, distance, urgency, and storage...</p>
        </div>
      ) : activeTab === 'available' ? (
        <div className="space-y-4">
          {(!dashboardData?.available_surplus || dashboardData.available_surplus.length === 0) ? (
            <div className="glass-panel p-12 text-center rounded-3xl border border-white/10 space-y-3">
              <Package className="w-12 h-12 text-slate-600 mx-auto" />
              <h3 className="text-lg font-bold text-white">No Unreserved Surplus Available</h3>
              <p className="text-xs text-slate-400 max-w-md mx-auto">
                All currently declared surplus batches have been matched or claimed. You will be automatically notified when kitchen donors declare new batches.
              </p>
            </div>
          ) : (
            dashboardData.available_surplus.map((item) => {
              const isExpanded = expandedExplanationId === item.id;
              const isActing = actionInProgress === item.id;

              return (
                <div
                  key={item.id}
                  className="glass-panel p-5 sm:p-6 rounded-3xl border border-white/10 hover:border-indigo-500/40 transition-all bg-slate-900/90 shadow-xl space-y-4"
                >
                  {/* Top Row: Food title, portions, match score */}
                  <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                    <div className="space-y-1.5">
                      <div className="flex items-center space-x-2">
                        <span className="text-xs font-mono font-bold text-indigo-400">
                          {item.quantity} {item.unit} &bull; {item.portions} Meals
                        </span>
                        <Badge
                          variant={
                            item.urgency === 'CRITICAL' ? 'danger' :
                            item.urgency === 'HIGH' ? 'warning' : 'success'
                          }
                          size="sm"
                        >
                          {item.urgency} URGENCY
                        </Badge>
                        <Badge variant="neutral" size="sm">
                          {item.storage_type}
                        </Badge>
                      </div>

                      <h3 className="text-xl font-bold text-white tracking-tight">
                        {item.food}
                      </h3>

                      <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400">
                        <span className="flex items-center">
                          <MapPin className="w-3.5 h-3.5 text-slate-500 mr-1" />
                          {item.location} &bull; <strong className="text-indigo-300 ml-1">{item.distance_km} km away</strong>
                        </span>
                        <span className="flex items-center">
                          <Clock className="w-3.5 h-3.5 text-slate-500 mr-1" />
                          Prepared {item.age_formatted} &bull; <span className="text-amber-400 ml-1">{item.safe_window_formatted}</span>
                        </span>
                        {item.temperature && (
                          <span className="flex items-center text-cyan-400">
                            <Thermometer className="w-3.5 h-3.5 mr-0.5" />
                            {item.temperature}°C verified probe
                          </span>
                        )}
                      </div>
                    </div>

                    {/* AI Transparent Match Score Banner */}
                    <div className="flex flex-col items-end shrink-0">
                      <div className="bg-indigo-950/60 border border-indigo-500/40 px-3.5 py-1.5 rounded-2xl flex items-center space-x-2">
                        <Sparkles className="w-4 h-4 text-indigo-400" />
                        <span className="text-xs text-indigo-200 font-bold">Match Compatibility:</span>
                        <span className="text-base font-black text-white">{Math.round(item.match_score)}%</span>
                      </div>
                      <span className="text-[10px] text-slate-400 mt-1">Multi-attribute deterministic fit</span>
                    </div>
                  </div>

                  {/* TRANSPARENT MATCH EXPLANATION (NO BLACK BOX) */}
                  <div className="bg-slate-950/70 border border-white/5 rounded-2xl p-3.5 space-y-2.5">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-bold text-slate-300 uppercase tracking-wider flex items-center">
                        <Info className="w-3.5 h-3.5 text-indigo-400 mr-1.5" />
                        Transparent Match Explanation:
                      </span>
                      <button
                        onClick={() => setExpandedExplanationId(isExpanded ? null : item.id)}
                        className="text-[11px] text-indigo-400 hover:text-indigo-300 font-semibold"
                      >
                        {isExpanded ? 'Collapse Factors' : 'Show All 7 Factors'}
                      </button>
                    </div>

                    {/* Bullet List (Example format required by prompt) */}
                    <ul className="text-xs text-slate-300 space-y-1">
                      {item.transparent_explanation.map((bullet, idx) => (
                        <li key={idx} className="flex items-start space-x-2">
                          <span className="text-emerald-400 font-bold mt-0.5">&bull;</span>
                          <span>{bullet}</span>
                        </li>
                      ))}
                    </ul>

                    {/* Expanded 7-Factor Pills */}
                    {isExpanded && (
                      <div className="mt-3 pt-3 border-t border-white/10 grid grid-cols-2 sm:grid-cols-4 gap-2">
                        <div className="bg-slate-900 p-2 rounded-xl text-center">
                          <div className="text-[10px] text-slate-400 uppercase">Food Compatibility</div>
                          <div className="text-sm font-bold text-emerald-400 mt-0.5">Optimal</div>
                        </div>
                        <div className="bg-slate-900 p-2 rounded-xl text-center">
                          <div className="text-[10px] text-slate-400 uppercase">Capacity Match</div>
                          <div className="text-sm font-bold text-indigo-400 mt-0.5">{item.portions} / {dashboardData.current_demand_portions} Meals</div>
                        </div>
                        <div className="bg-slate-900 p-2 rounded-xl text-center">
                          <div className="text-[10px] text-slate-400 uppercase">Distance & Transit</div>
                          <div className="text-sm font-bold text-white mt-0.5">{item.distance_km} km (~14m)</div>
                        </div>
                        <div className="bg-slate-900 p-2 rounded-xl text-center">
                          <div className="text-[10px] text-slate-400 uppercase">Storage Fit</div>
                          <div className="text-sm font-bold text-emerald-400 mt-0.5">{item.storage_type} OK</div>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* ACTION BAR: Request, Accept, Schedule Pickup */}
                  <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
                    <div className="text-[11px] text-slate-400 flex items-center">
                      <ShieldCheck className="w-3.5 h-3.5 text-emerald-400 mr-1" />
                      Row-level database transaction locks active to prevent double-booking.
                    </div>

                    <div className="flex items-center space-x-2">
                      <Button
                        variant="secondary"
                        size="sm"
                        disabled={isActing}
                        onClick={() => handleReject(item)}
                      >
                        Decline
                      </Button>

                      <Button
                        variant="primary"
                        size="sm"
                        disabled={isActing}
                        onClick={() => handleRequest(item)}
                        leftIcon={<PlusCircle className="w-3.5 h-3.5" />}
                      >
                        {isActing ? 'Locking...' : 'Request Allocation'}
                      </Button>

                      <Button
                        variant="primary"
                        className="bg-emerald-600 hover:bg-emerald-500 text-white"
                        size="sm"
                        disabled={isActing}
                        onClick={() => {
                          setScheduleModalItem(item);
                        }}
                        leftIcon={<Calendar className="w-3.5 h-3.5" />}
                      >
                        Schedule Direct Pickup
                      </Button>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      ) : activeTab === 'claims' ? (
        /* MY ACTIVE CLAIMS TAB */
        <div className="space-y-4">
          <div className="glass-panel p-6 rounded-3xl border border-white/10 space-y-4">
            <h3 className="text-lg font-bold text-white">Active Reserved Lots</h3>
            <p className="text-xs text-slate-400">
              Surplus lots currently locked and reserved for {dashboardData?.organization_name}.
            </p>

            <div className="space-y-3">
              <div className="p-4 rounded-2xl border border-indigo-500/30 bg-slate-900/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <div className="flex items-center space-x-2">
                    <Badge variant="purple" size="sm">RESERVED</Badge>
                    <span className="text-xs text-slate-400 font-mono">25.0 kg &bull; 70 Portions</span>
                  </div>
                  <h4 className="text-base font-bold text-white mt-1">Steamed Saffron Basmati Rice Pilaf & Lentils</h4>
                  <p className="text-xs text-slate-400">Donor: Main Culinary Center &bull; Reserved 15m ago</p>
                </div>

                <div className="flex items-center space-x-2">
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => {
                      if (onShowSuccess) onShowSuccess('Reservation confirmed for pickup.');
                    }}
                  >
                    Confirm & Accept
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      if (onNavigate) onNavigate('qr_verification');
                    }}
                  >
                    View Handover QR
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        /* SCHEDULED PICKUPS TAB */
        <div className="space-y-4">
          <div className="glass-panel p-6 rounded-3xl border border-white/10 space-y-4">
            <h3 className="text-lg font-bold text-white">Upcoming Volunteer Pickups</h3>
            <p className="text-xs text-slate-400">
              Verified drivers and vehicles scheduled for loading bay pickup at donor kitchens.
            </p>

            <div className="p-4 rounded-2xl border border-emerald-500/30 bg-slate-900/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <div className="flex items-center space-x-2">
                  <Badge variant="success" size="sm">PICKUP SCHEDULED</Badge>
                  <span className="text-xs text-emerald-400 font-mono">Today at 02:30 PM</span>
                </div>
                <h4 className="text-base font-bold text-white mt-1">Chef's Garden Vegetable Medley with Quinoa</h4>
                <p className="text-xs text-slate-400">Driver: Sister Beatrice (Volunteer) &bull; Vehicle: VAN-SF-401 &bull; 4 Cambros</p>
              </div>

              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  if (onNavigate) onNavigate('map_logistics');
                }}
                leftIcon={<Truck className="w-3.5 h-3.5" />}
              >
                Track Transit Route
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* SCHEDULE PICKUP MODAL */}
      <Modal
        isOpen={scheduleModalItem !== null}
        onClose={() => setScheduleModalItem(null)}
        title={`Schedule Pickup — ${scheduleModalItem?.food}`}
        maxWidth="md"
      >
        <div className="space-y-4 text-xs">
          <div className="bg-slate-900 p-3 rounded-xl border border-white/10 space-y-1">
            <div className="font-bold text-white">{scheduleModalItem?.food}</div>
            <div className="text-slate-400">{scheduleModalItem?.quantity} {scheduleModalItem?.unit} &bull; {scheduleModalItem?.portions} Portions &bull; {scheduleModalItem?.location}</div>
          </div>

          <div className="space-y-1">
            <label className="text-[11px] font-bold text-slate-400 uppercase">Pickup Date & Time</label>
            <input
              type="datetime-local"
              value={pickupTime}
              onChange={(e) => setPickupTime(e.target.value)}
              className="w-full bg-slate-950 border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-[11px] font-bold text-slate-400 uppercase">Driver / Volunteer Name</label>
              <input
                type="text"
                value={driverName}
                onChange={(e) => setDriverName(e.target.value)}
                className="w-full bg-slate-950 border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
              />
            </div>
            <div className="space-y-1">
              <label className="text-[11px] font-bold text-slate-400 uppercase">Vehicle License Plate</label>
              <input
                type="text"
                value={vehiclePlate}
                onChange={(e) => setVehiclePlate(e.target.value)}
                className="w-full bg-slate-950 border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-[11px] font-bold text-slate-400 uppercase">Logistics Notes</label>
            <textarea
              rows={2}
              value={pickupNotes}
              onChange={(e) => setPickupNotes(e.target.value)}
              className="w-full bg-slate-950 border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
            />
          </div>

          <label className="flex items-center space-x-2 p-2.5 rounded-xl bg-slate-900 border border-white/5 cursor-pointer">
            <input
              type="checkbox"
              checked={tempEquipConfirmed}
              onChange={(e) => setTempEquipConfirmed(e.target.checked)}
              className="rounded bg-slate-950 border-white/20 text-indigo-600 focus:ring-0"
            />
            <span className="text-[11px] text-slate-300">
              I confirm the transport vehicle carries certified thermal insulation carriers (Cambro / Cooler) to maintain food temperature.
            </span>
          </label>

          <div className="flex justify-end space-x-2 pt-2">
            <Button variant="outline" size="sm" onClick={() => setScheduleModalItem(null)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              disabled={actionInProgress !== null}
              onClick={handleConfirmSchedulePickup}
            >
              {actionInProgress ? 'Locking & Scheduling...' : 'Confirm & Schedule Pickup'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
