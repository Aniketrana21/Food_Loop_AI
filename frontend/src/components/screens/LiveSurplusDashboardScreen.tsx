'use client';

import React, { useState, useEffect } from 'react';
import { 
  Share2, 
  HeartHandshake, 
  Clock, 
  MapPin, 
  AlertTriangle, 
  ShieldAlert, 
  ShieldCheck, 
  Thermometer, 
  Truck, 
  CheckCircle2, 
  PlusCircle, 
  Search, 
  RefreshCw, 
  Building2, 
  PhoneCall, 
  FileText, 
  Sparkles, 
  X, 
  ChevronRight, 
  ArrowRight, 
  Flame, 
  Snowflake, 
  Layers, 
  Info,
  Calendar,
  UserCheck,
  Ban,
  Recycle,
  Leaf
} from 'lucide-react';
import { Button } from '@/components/design-system/Button';
import { Badge } from '@/components/design-system/Badge';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/design-system/Card';
import { Modal } from '@/components/design-system/Modal';
import { ScreenId } from '@/components/navigation/Sidebar';
import { 
  SurplusRecordOut, 
  SurplusRecordCreate, 
  StorageType, 
  SurplusStatus, 
  SurplusUrgency, 
  RecipientMatchItem, 
  LiveSurplusDashboardSummary 
} from '@/types';
import { 
  getLiveSurplusDashboard, 
  createSurplusRecord, 
  findMatchedRecipients, 
  allocateSurplusLot, 
  approveSurplusInspection, 
  updateSurplusLifecycleStatus 
} from '@/lib/api';

interface LiveSurplusDashboardProps {
  onNavigate?: (screen: ScreenId) => void;
  onOpenDonateModal?: () => void;
  onShowSuccess: (msg: string) => void;
}

export const LiveSurplusDashboardScreen: React.FC<LiveSurplusDashboardProps> = ({
  onNavigate,
  onOpenDonateModal,
  onShowSuccess
}) => {
  // Main Data States
  const [dashboardData, setDashboardData] = useState<LiveSurplusDashboardSummary | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedStatusFilter, setSelectedStatusFilter] = useState<string>('ALL');
  const [selectedUrgencyFilter, setSelectedUrgencyFilter] = useState<string>('ALL');

  // Modal States
  const [createModalOpen, setCreateModalOpen] = useState<boolean>(false);
  const [matchModalOpen, setMatchModalOpen] = useState<boolean>(false);
  const [alternativeWorkflowModalOpen, setAlternativeWorkflowModalOpen] = useState<boolean>(false);
  const [approvalModalOpen, setApprovalModalOpen] = useState<boolean>(false);

  // Active Selection for Modals
  const [activeItem, setActiveItem] = useState<SurplusRecordOut | null>(null);
  const [recipientsList, setRecipientsList] = useState<RecipientMatchItem[]>([]);
  const [isLoadingRecipients, setIsLoadingRecipients] = useState<boolean>(false);
  const [isAllocating, setIsAllocating] = useState<boolean>(false);

  // New Surplus Form Inputs
  const [newFood, setNewFood] = useState<string>('');
  const [newQuantity, setNewQuantity] = useState<number>(20.0);
  const [newUnit, setNewUnit] = useState<string>('kg');
  const [newPreparedAt, setNewPreparedAt] = useState<string>(
    new Date(Date.now() - 1.5 * 3600 * 1000).toISOString().slice(0, 16)
  );
  const [newStorageType, setNewStorageType] = useState<StorageType>('HOT_HOLD');
  const [newTemperature, setNewTemperature] = useState<string>('62.5');
  const [newBatch, setNewBatch] = useState<string>('BATCH-' + new Date().toISOString().slice(0, 10) + '-01');
  const [newLocation, setNewLocation] = useState<string>('Station 1 Holding Cart');
  const [newNotes, setNewNotes] = useState<string>('');
  const [newCategory, setNewCategory] = useState<string>('COOKED_MEALS');
  const [isSubmittingNew, setIsSubmittingNew] = useState<boolean>(false);

  // Manager Approval Form Inputs
  const [approvalVerifiedTemp, setApprovalVerifiedTemp] = useState<string>('61.0');
  const [approvalNotes, setApprovalNotes] = useState<string>('Visual sensory check passed. Steam holding verified.');
  const [isSubmittingApproval, setIsSubmittingApproval] = useState<boolean>(false);

  // Fetch Dashboard Telemetry
  const fetchDashboard = async () => {
    setIsLoading(true);
    try {
      const data = await getLiveSurplusDashboard(
        selectedStatusFilter !== 'ALL' ? selectedStatusFilter : undefined,
        selectedUrgencyFilter !== 'ALL' ? selectedUrgencyFilter : undefined
      );
      setDashboardData(data);
    } catch (err) {
      console.error('Failed to load live surplus data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
    // Auto-refresh countdown every 30 seconds
    const interval = setInterval(fetchDashboard, 30000);
    return () => clearInterval(interval);
  }, [selectedStatusFilter, selectedUrgencyFilter]);

  // Handle Create Record Submit
  const handleCreateSurplusSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newFood) return;
    setIsSubmittingNew(true);

    try {
      const payload: SurplusRecordCreate = {
        food: newFood,
        quantity: Number(newQuantity),
        unit: newUnit,
        prepared_at: new Date(newPreparedAt).toISOString(),
        storage_type: newStorageType,
        temperature: newTemperature ? parseFloat(newTemperature) : null,
        batch: newBatch,
        best_use_before: null,
        location: newLocation,
        notes: newNotes,
        category: newCategory
      };

      const created = await createSurplusRecord(payload);
      onShowSuccess(`Surplus lot '${created.food}' declared! Safe window: ${created.remaining_safe_window_formatted}.`);
      setCreateModalOpen(false);
      // Reset form
      setNewFood('');
      setNewNotes('');
      fetchDashboard();
    } catch (err: any) {
      alert(err.message || 'Failed to create surplus lot');
    } finally {
      setIsSubmittingNew(false);
    }
  };

  // Open Matching Drawer
  const handleOpenRecipients = async (item: SurplusRecordOut) => {
    setActiveItem(item);
    setRecipientsList([]);
    setMatchModalOpen(true);
    setIsLoadingRecipients(true);

    try {
      const matches = await findMatchedRecipients(item.id);
      setRecipientsList(matches);
    } catch (err: any) {
      console.error('Failed to fetch recipients:', err);
    } finally {
      setIsLoadingRecipients(false);
    }
  };

  // Confirm Allocation to Recipient
  const handleConfirmAllocation = async (recipientId: string) => {
    if (!activeItem) return;
    setIsAllocating(true);
    try {
      await allocateSurplusLot(activeItem.id, recipientId);
      onShowSuccess(`Surplus lot successfully allocated! Courier dispatch initialized.`);
      setMatchModalOpen(false);
      fetchDashboard();
    } catch (err: any) {
      alert(err.message || 'Allocation rejected: Food safety violation');
    } finally {
      setIsAllocating(false);
    }
  };

  // Open Alternative Waste Modal
  const handleOpenAlternativeWorkflow = (item: SurplusRecordOut) => {
    setActiveItem(item);
    setAlternativeWorkflowModalOpen(true);
  };

  // Open Manager Approval Modal
  const handleOpenApproval = (item: SurplusRecordOut) => {
    setActiveItem(item);
    setApprovalVerifiedTemp(item.temperature ? String(item.temperature) : '60.0');
    setApprovalModalOpen(true);
  };

  // Submit Manager Approval
  const handleSubmitApproval = async (approved: boolean) => {
    if (!activeItem) return;
    setIsSubmittingApproval(true);
    try {
      await approveSurplusInspection(activeItem.id, {
        approved,
        notes: approvalNotes,
        verified_temp: approvalVerifiedTemp ? parseFloat(approvalVerifiedTemp) : null
      });
      onShowSuccess(approved ? 'Manager inspection sign-off approved!' : 'Manager marked lot for waste diversion.');
      setApprovalModalOpen(false);
      fetchDashboard();
    } catch (err: any) {
      alert(err.message || 'Failed to submit approval');
    } finally {
      setIsSubmittingApproval(false);
    }
  };

  // Status Progression Helper
  const handleAdvanceStatus = async (item: SurplusRecordOut, nextStatus: SurplusStatus) => {
    try {
      await updateSurplusLifecycleStatus(item.id, nextStatus);
      onShowSuccess(`Status updated to ${nextStatus.replace('_', ' ')}.`);
      fetchDashboard();
    } catch (err: any) {
      alert(err.message || 'Status transition error');
    }
  };

  // Filter listings by search
  const filteredItems = (dashboardData?.items || []).filter((item) => {
    const q = searchQuery.toLowerCase();
    return (
      item.food.toLowerCase().includes(q) ||
      item.location.toLowerCase().includes(q) ||
      (item.batch && item.batch.toLowerCase().includes(q))
    );
  });

  return (
    <div className="space-y-6 pb-12">
      {/* ========================================================= */}
      {/* 1. TOP HEADER & TELEMETRY CONTROLS                       */}
      {/* ========================================================= */}
      <div className="glass-panel p-6 rounded-3xl border border-white/10 bg-slate-900/90 relative overflow-hidden shadow-2xl">
        <div className="absolute top-0 right-0 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none -mr-20 -mt-20" />
        <div className="absolute bottom-0 left-1/3 w-80 h-80 bg-sky-500/10 rounded-full blur-3xl pointer-events-none -mb-20" />

        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-5">
          <div>
            <div className="flex flex-wrap items-center gap-2 mb-2">
              <Badge variant="emerald" size="sm" className="gap-1 px-3 py-1">
                <ShieldCheck className="w-3 h-3" /> Deterministic Food Safety Engine
              </Badge>
              <Badge variant="info" size="sm">
                FDA Food Code § 3-501.19
              </Badge>
              <Badge variant="purple" size="sm">
                Zero LLM Decision Safeguard
              </Badge>
              <Badge variant="neutral" size="sm">
                Authorized Human Sign-Off
              </Badge>
            </div>
            <h1 className="text-3xl font-black text-white tracking-tight flex items-center gap-3">
              Real-Time Surplus Management & Rescue Hub
            </h1>
            <p className="text-sm text-slate-400 mt-1 max-w-3xl leading-relaxed">
              Live tracking of post-service surplus lots with deterministic food safety windows, automated urgency alerts,
              and instant non-profit matching. Prevents expired food from being allocated.
            </p>
          </div>

          <div className="flex items-center gap-3 self-start lg:self-auto">
            <Button
              variant="outline"
              size="sm"
              onClick={fetchDashboard}
              isLoading={isLoading}
              leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
            >
              Refresh
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={() => setCreateModalOpen(true)}
              leftIcon={<PlusCircle className="w-3.5 h-3.5" />}
            >
              Declare Surplus Food Lot
            </Button>
          </div>
        </div>

        {/* 4 Summary Metric Counters */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-6 pt-5 border-t border-white/10">
          <div className="p-3 rounded-xl bg-slate-800/40 border border-white/5">
            <div className="text-[10px] uppercase tracking-wider text-slate-400">Total Active Lots</div>
            <div className="text-2xl font-black text-white font-mono mt-0.5">
              {dashboardData?.total_active_lots ?? 0}
            </div>
            <span className="text-[10px] text-slate-400">monitored in facility</span>
          </div>

          <div className="p-3 rounded-xl bg-emerald-950/20 border border-emerald-500/20">
            <div className="text-[10px] uppercase tracking-wider text-emerald-300">Available For Rescue</div>
            <div className="text-2xl font-black text-emerald-400 font-mono mt-0.5">
              {dashboardData?.total_available_quantity_kg ?? 0} kg
            </div>
            <span className="text-[10px] text-emerald-300">{dashboardData?.available_lots_count ?? 0} lots available</span>
          </div>

          <div className="p-3 rounded-xl bg-amber-950/20 border border-amber-500/20">
            <div className="text-[10px] uppercase tracking-wider text-amber-300">Critical Window (&lt;60m)</div>
            <div className="text-2xl font-black text-amber-400 font-mono mt-0.5">
              {dashboardData?.critical_urgency_count ?? 0}
            </div>
            <span className="text-[10px] text-amber-300">requires expedited action</span>
          </div>

          <div className="p-3 rounded-xl bg-rose-950/20 border border-rose-500/20">
            <div className="text-[10px] uppercase tracking-wider text-rose-300">Expired / Diverted</div>
            <div className="text-2xl font-black text-rose-400 font-mono mt-0.5">
              {dashboardData?.expired_lots_count ?? 0}
            </div>
            <span className="text-[10px] text-rose-300">routed to compost / digestion</span>
          </div>
        </div>
      </div>

      {/* ========================================================= */}
      {/* 2. AUTOMATIC URGENCY & EXPIRY ALERT BANNER               */}
      {/* ========================================================= */}
      {(dashboardData?.urgent_alerts && dashboardData.urgent_alerts.length > 0) && (
        <div className="p-4 rounded-2xl border-2 border-amber-500/40 bg-amber-950/30 backdrop-blur-md space-y-2.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-amber-300 font-bold text-xs uppercase tracking-wider">
              <AlertTriangle className="w-4 h-4 text-amber-400 animate-pulse" />
              <span>Live Food Safety Alerts & Urgency Notifications ({dashboardData.urgent_alerts.length})</span>
            </div>
            <Badge variant="warning" size="sm">HACCP Critical Window</Badge>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {dashboardData.urgent_alerts.map((alert, idx) => (
              <div
                key={idx}
                className={`p-3 rounded-xl border text-xs flex items-start justify-between gap-3 ${
                  alert.urgency === 'EXPIRED'
                    ? 'border-rose-500/30 bg-rose-950/40 text-rose-200'
                    : 'border-amber-500/30 bg-amber-950/40 text-amber-200'
                }`}
              >
                <div className="space-y-1">
                  <div className="font-bold text-white flex items-center gap-2">
                    <span>{alert.food}</span>
                    <span className="font-mono text-[10px] px-1.5 py-0.2 rounded bg-black/40">
                      {alert.remaining_window}
                    </span>
                  </div>
                  <p className="text-[11px] opacity-90 leading-tight">
                    {alert.action}
                  </p>
                  <div className="text-[10px] opacity-75 flex items-center gap-1">
                    <MapPin className="w-3 h-3" /> {alert.location}
                  </div>
                </div>

                <Badge variant={alert.urgency === 'EXPIRED' ? 'danger' : 'warning'} size="sm">
                  {alert.urgency}
                </Badge>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ========================================================= */}
      {/* 3. SEARCH & FILTERS BAR                                   */}
      {/* ========================================================= */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 glass-panel p-4 rounded-2xl border border-white/10 bg-slate-900/60">
        {/* Status Filters */}
        <div className="flex items-center space-x-1 overflow-x-auto pb-1 sm:pb-0">
          {['ALL', 'AVAILABLE', 'RESERVED', 'PICKUP_SCHEDULED', 'IN_TRANSIT', 'DELIVERED', 'EXPIRED'].map((st) => (
            <button
              key={st}
              onClick={() => setSelectedStatusFilter(st)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${
                selectedStatusFilter === st
                  ? 'bg-emerald-500 text-slate-950 font-bold shadow-md shadow-emerald-500/20'
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
            >
              {st.replace('_', ' ')}
            </button>
          ))}
        </div>

        {/* Search Input */}
        <div className="relative min-w-[240px]">
          <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search surplus by food, batch, location..."
            className="w-full pl-10 pr-4 py-2 rounded-xl bg-slate-950 border border-white/10 text-white text-xs focus:outline-none focus:border-emerald-500 placeholder:text-slate-500"
          />
        </div>
      </div>

      {/* ========================================================= */}
      {/* 4. LIVE SURPLUS CARDS GRID                                */}
      {/* Each Card Displays: Food, Quantity, Age, Remaining Window, */}
      {/* Urgency, Location, Status                                */}
      {/* ========================================================= */}
      {filteredItems.length === 0 ? (
        <div className="p-12 text-center rounded-3xl border border-dashed border-white/10 bg-slate-900/40 space-y-3">
          <Leaf className="w-10 h-10 text-slate-500 mx-auto" />
          <div className="text-base font-bold text-white">No Surplus Food Lots Found</div>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            All kitchen stations are clear or no surplus records match the selected filters. Click "Declare Surplus Food Lot" to register prepared surplus.
          </p>
          <Button
            variant="primary"
            size="sm"
            onClick={() => setCreateModalOpen(true)}
            leftIcon={<PlusCircle className="w-3.5 h-3.5" />}
          >
            Declare Surplus Lot
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-6">
          {filteredItems.map((item) => {
            const isExpired = item.status === 'EXPIRED' || item.urgency === 'EXPIRED';
            const isCritical = item.urgency === 'CRITICAL';
            const isAvailable = item.status === 'AVAILABLE';
            const needsApproval = item.eligibility === 'NEEDS_HUMAN_INSPECTION' && item.approval_status !== 'APPROVED';

            return (
              <div
                key={item.id}
                className={`glass-panel p-6 rounded-3xl border transition-all flex flex-col justify-between space-y-4 shadow-xl ${
                  isExpired
                    ? 'border-rose-500/30 bg-rose-950/10'
                    : isCritical
                    ? 'border-amber-500/40 bg-amber-950/10'
                    : 'border-white/10 hover:border-emerald-500/30 bg-slate-900/80'
                }`}
              >
                {/* Top Card Row: Food Name & Status Badge */}
                <div className="space-y-3">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="flex items-center gap-2">
                        {/* Storage Type Pill */}
                        <Badge
                          variant={
                            item.storage_type === 'HOT_HOLD'
                              ? 'warning'
                              : item.storage_type === 'FROZEN'
                              ? 'cyan'
                              : 'info'
                          }
                          size="sm"
                        >
                          {item.storage_type === 'HOT_HOLD' ? (
                            <Flame className="w-3 h-3 mr-1 inline" />
                          ) : (
                            <Snowflake className="w-3 h-3 mr-1 inline" />
                          )}
                          {item.storage_type.replace('_', ' ')}
                        </Badge>

                        {/* Urgency Pill */}
                        <Badge
                          variant={
                            item.urgency === 'CRITICAL'
                              ? 'danger'
                              : item.urgency === 'HIGH'
                              ? 'warning'
                              : item.urgency === 'LOW'
                              ? 'success'
                              : 'neutral'
                          }
                          size="sm"
                          className={isCritical ? 'animate-pulse' : ''}
                        >
                          {item.urgency} Urgency
                        </Badge>
                      </div>

                      {/* 1. Food Name */}
                      <h3 className="text-lg font-bold text-white mt-1.5 tracking-tight">
                        {item.food}
                      </h3>

                      {/* 6. Location */}
                      <p className="text-xs text-slate-400 flex items-center space-x-1 mt-0.5">
                        <MapPin className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
                        <span>{item.location}</span>
                        {item.batch && (
                          <span className="font-mono text-[10px] text-slate-400">
                            &bull; {item.batch}
                          </span>
                        )}
                      </p>
                    </div>

                    {/* 7. Status Badge */}
                    <Badge
                      variant={
                        item.status === 'AVAILABLE'
                          ? 'success'
                          : item.status === 'EXPIRED'
                          ? 'danger'
                          : item.status === 'DELIVERED'
                          ? 'info'
                          : 'purple'
                      }
                      size="md"
                    >
                      {item.status.replace('_', ' ')}
                    </Badge>
                  </div>

                  {/* 7 Core Spec Metrics: Food, Quantity, Age, Remaining window, Urgency, Location, Status */}
                  <div className="grid grid-cols-3 gap-2.5 p-3 rounded-2xl bg-slate-950/70 border border-white/5 text-center">
                    {/* 2. Quantity */}
                    <div>
                      <span className="text-[10px] text-slate-400 block uppercase font-semibold">
                        Quantity
                      </span>
                      <span className="font-bold text-white font-mono text-sm">
                        {item.quantity} {item.unit}
                      </span>
                    </div>

                    {/* 3. Age */}
                    <div>
                      <span className="text-[10px] text-slate-400 block uppercase font-semibold">
                        Age
                      </span>
                      <span className="font-bold text-slate-300 font-mono text-sm">
                        {item.age_formatted}
                      </span>
                    </div>

                    {/* 4. Remaining Safe Window */}
                    <div>
                      <span className="text-[10px] text-slate-400 block uppercase font-semibold">
                        Safe Window
                      </span>
                      <span
                        className={`font-black font-mono text-sm ${
                          isExpired
                            ? 'text-rose-400'
                            : isCritical
                            ? 'text-amber-400'
                            : 'text-emerald-400'
                        }`}
                      >
                        {item.remaining_safe_window_formatted}
                      </span>
                    </div>
                  </div>

                  {/* Temperature Probe & Safety Rule Applied */}
                  <div className="flex items-center justify-between text-[11px] px-1 text-slate-400">
                    <span className="flex items-center gap-1">
                      <Thermometer className="w-3.5 h-3.5 text-sky-400" />
                      {item.temperature !== null && item.temperature !== undefined ? (
                        <span className="text-white font-mono font-semibold">
                          {item.temperature.toFixed(1)}°C Probe
                        </span>
                      ) : (
                        <span className="italic">Standard Storage</span>
                      )}
                    </span>
                    <span className="text-[10px] font-mono text-slate-400 truncate max-w-[220px]">
                      {item.safety_rule_applied}
                    </span>
                  </div>

                  {/* Required Action Banner */}
                  <div
                    className={`p-2.5 rounded-xl border text-xs leading-relaxed flex items-start gap-2 ${
                      isExpired
                        ? 'border-rose-500/20 bg-rose-950/30 text-rose-200'
                        : isCritical
                        ? 'border-amber-500/20 bg-amber-950/30 text-amber-200'
                        : 'border-white/5 bg-slate-950/40 text-slate-300'
                    }`}
                  >
                    <Info className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
                    <span>{item.required_action}</span>
                  </div>

                  {/* Notes if available */}
                  {item.notes && (
                    <div className="text-[11px] text-slate-400 italic px-1">
                      "{item.notes}"
                    </div>
                  )}
                </div>

                {/* Bottom Action Controls */}
                <div className="pt-2 border-t border-white/10 flex flex-wrap items-center justify-between gap-2">
                  {/* Case 1: Ineligible / Expired -> Strict Allocation Lockout */}
                  {isExpired ? (
                    <div className="w-full flex items-center justify-between gap-2">
                      <div className="flex items-center gap-1.5 text-xs text-rose-400 font-semibold">
                        <Ban className="w-4 h-4" />
                        <span>Allocation Disabled (Food Safety Rule)</span>
                      </div>
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => handleOpenAlternativeWorkflow(item)}
                        leftIcon={<Recycle className="w-3.5 h-3.5 text-emerald-400" />}
                      >
                        Waste Diversion Workflow
                      </Button>
                    </div>
                  ) : needsApproval ? (
                    /* Case 2: Needs Manager Sign-Off */
                    <div className="w-full flex items-center justify-between gap-2">
                      <span className="text-xs text-amber-300 font-semibold flex items-center gap-1">
                        <AlertTriangle className="w-3.5 h-3.5" />
                        Manager Sign-Off Required
                      </span>
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => handleOpenApproval(item)}
                        leftIcon={<UserCheck className="w-3.5 h-3.5" />}
                      >
                        Inspect & Sign Off
                      </Button>
                    </div>
                  ) : isAvailable ? (
                    /* Case 3: Available for Rescue */
                    <div className="w-full flex items-center justify-between gap-2">
                      <span className="text-xs text-emerald-400 font-medium flex items-center gap-1">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        Verified for Rescue
                      </span>
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => handleOpenRecipients(item)}
                        leftIcon={<HeartHandshake className="w-3.5 h-3.5" />}
                      >
                        Find Recipients & Dispatch
                      </Button>
                    </div>
                  ) : (
                    /* Case 4: In Progress Lifecycle States */
                    <div className="w-full flex items-center justify-between gap-2">
                      <span className="text-xs text-purple-300 font-mono">
                        Pipeline: {item.status.replace('_', ' ')}
                      </span>
                      {item.status === 'RESERVED' && (
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => handleAdvanceStatus(item, 'PICKUP_SCHEDULED')}
                          leftIcon={<Truck className="w-3.5 h-3.5" />}
                        >
                          Schedule Courier
                        </Button>
                      )}
                      {item.status === 'PICKUP_SCHEDULED' && (
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => handleAdvanceStatus(item, 'PICKED_UP')}
                        >
                          Mark Picked Up
                        </Button>
                      )}
                      {item.status === 'PICKED_UP' && (
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => handleAdvanceStatus(item, 'IN_TRANSIT')}
                        >
                          Mark In Transit
                        </Button>
                      )}
                      {item.status === 'IN_TRANSIT' && (
                        <Button
                          variant="primary"
                          size="sm"
                          onClick={() => handleAdvanceStatus(item, 'DELIVERED')}
                          leftIcon={<CheckCircle2 className="w-3.5 h-3.5" />}
                        >
                          Confirm Delivery
                        </Button>
                      )}
                      {item.status === 'DELIVERED' && (
                        <span className="text-xs text-emerald-400 font-bold flex items-center gap-1">
                          <CheckCircle2 className="w-3.5 h-3.5" /> Delivered to Shelter
                        </span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* ========================================================= */}
      {/* MODAL 1: CREATE SURPLUS RECORD                            */}
      {/* ========================================================= */}
      <Modal
        isOpen={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        title="Declare Prepared Surplus Food Lot"
      >
        <form onSubmit={handleCreateSurplusSubmit} className="space-y-4">
          <p className="text-xs text-slate-400">
            Enter preparation details. The deterministic food safety rules engine will immediately compute the safe consumption window and required action.
          </p>

          <div className="space-y-3">
            {/* Food Name */}
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">
                Food Description / Dish Name *
              </label>
              <input
                type="text"
                required
                value={newFood}
                onChange={(e) => setNewFood(e.target.value)}
                placeholder="e.g. Braised Lemon Thyme Roasted Chicken"
                className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
              />
            </div>

            {/* Quantity & Unit */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">
                  Quantity *
                </label>
                <input
                  type="number"
                  step="0.5"
                  required
                  min={1}
                  value={newQuantity}
                  onChange={(e) => setNewQuantity(Number(e.target.value))}
                  className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500 font-mono"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">
                  Unit
                </label>
                <select
                  value={newUnit}
                  onChange={(e) => setNewUnit(e.target.value)}
                  className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                >
                  <option value="kg">kg (Kilograms)</option>
                  <option value="portions">portions</option>
                  <option value="lbs">lbs (Pounds)</option>
                  <option value="trays">hotel pans / trays</option>
                </select>
              </div>
            </div>

            {/* Storage Type & Probe Temperature */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">
                  Storage Type *
                </label>
                <select
                  value={newStorageType}
                  onChange={(e) => {
                    const st = e.target.value as StorageType;
                    setNewStorageType(st);
                    if (st === 'HOT_HOLD') setNewTemperature('62.5');
                    else if (st === 'REFRIGERATED') setNewTemperature('3.5');
                    else if (st === 'FROZEN') setNewTemperature('-19.0');
                    else setNewTemperature('21.0');
                  }}
                  className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                >
                  <option value="HOT_HOLD">Hot Hold (Min 57°C / 135°F)</option>
                  <option value="REFRIGERATED">Refrigerated (Max 5°C / 41°F)</option>
                  <option value="FROZEN">Deep Freeze (Max -18°C / 0°F)</option>
                  <option value="ROOM_TEMP">Ambient / Room Temp</option>
                </select>
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">
                  Probe Temperature (°C)
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={newTemperature}
                  onChange={(e) => setNewTemperature(e.target.value)}
                  placeholder="e.g. 62.5"
                  className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500 font-mono"
                />
              </div>
            </div>

            {/* Prepared At Timestamp */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">
                  Prepared At *
                </label>
                <input
                  type="datetime-local"
                  required
                  value={newPreparedAt}
                  onChange={(e) => setNewPreparedAt(e.target.value)}
                  className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">
                  Kitchen Location / Station
                </label>
                <input
                  type="text"
                  value={newLocation}
                  onChange={(e) => setNewLocation(e.target.value)}
                  placeholder="e.g. Station 2 Warmer"
                  className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                />
              </div>
            </div>

            {/* Batch & Notes */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">
                  Batch Code
                </label>
                <input
                  type="text"
                  value={newBatch}
                  onChange={(e) => setNewBatch(e.target.value)}
                  className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500 font-mono"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">
                  Category
                </label>
                <select
                  value={newCategory}
                  onChange={(e) => setNewCategory(e.target.value)}
                  className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                >
                  <option value="COOKED_MEALS">Cooked Meals</option>
                  <option value="PROTEIN">Meat & Poultry</option>
                  <option value="VEGETABLES">Vegetables & Sides</option>
                  <option value="BAKERY">Bakery & Bread</option>
                  <option value="DAIRY">Dairy & Yogurt</option>
                  <option value="SOUP">Soups & Broths</option>
                </select>
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">
                Packaging & Dietary Notes
              </label>
              <textarea
                rows={2}
                value={newNotes}
                onChange={(e) => setNewNotes(e.target.value)}
                placeholder="e.g. Steam table hotel pan with foil lid. Halal compliant."
                className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-3 border-t border-white/10">
            <Button variant="outline" type="button" onClick={() => setCreateModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" type="submit" isLoading={isSubmittingNew}>
              Declare Surplus Lot
            </Button>
          </div>
        </form>
      </Modal>

      {/* ========================================================= */}
      {/* MODAL 2: RECIPIENT MATCHING DRAWER                        */}
      {/* ========================================================= */}
      <Modal
        isOpen={matchModalOpen}
        onClose={() => setMatchModalOpen(false)}
        title="Find Matched Non-Profit Recipients"
      >
        <div className="space-y-4">
          {activeItem && (
            <div className="p-3.5 rounded-2xl bg-slate-900 border border-white/10 flex items-center justify-between">
              <div>
                <h4 className="text-xs font-bold text-white">{activeItem.food}</h4>
                <div className="text-[11px] text-slate-400 mt-0.5">
                  {activeItem.quantity} {activeItem.unit} &bull; Safe Window: {activeItem.remaining_safe_window_formatted}
                </div>
              </div>
              <Badge variant="emerald" size="sm">Rescue Eligible</Badge>
            </div>
          )}

          {isLoadingRecipients ? (
            <div className="p-8 text-center text-slate-400 text-xs">
              <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-emerald-400" />
              Scanning regional food rescue partner network...
            </div>
          ) : recipientsList.length === 0 ? (
            <div className="p-6 text-center text-slate-400 text-xs">
              No matching recipients within safe transit window.
            </div>
          ) : (
            <div className="space-y-2.5 max-h-96 overflow-y-auto pr-1">
              {recipientsList.map((rec) => (
                <div
                  key={rec.recipient_id}
                  className="p-3.5 rounded-2xl bg-slate-900/80 border border-white/10 hover:border-emerald-500/30 transition-all flex items-start justify-between gap-3"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <h4 className="text-xs font-bold text-white">{rec.organization_name}</h4>
                      <Badge variant="purple" size="sm">{rec.match_score}% Match</Badge>
                    </div>
                    <p className="text-[11px] text-slate-400 flex items-center gap-1">
                      <MapPin className="w-3 h-3 text-slate-500" />
                      {rec.address} &bull; {rec.distance_km} km ({rec.estimated_transit_minutes} min transit)
                    </p>
                    <div className="text-[10px] text-emerald-400 font-medium">
                      Safe buffer remaining after arrival: {rec.safe_margin_minutes} minutes
                    </div>
                    <div className="text-[10px] text-slate-400">
                      Contact: {rec.contact_person} &bull; {rec.phone}
                    </div>
                  </div>

                  <Button
                    variant="primary"
                    size="sm"
                    disabled={isAllocating}
                    onClick={() => handleConfirmAllocation(rec.recipient_id)}
                  >
                    Allocate & Dispatch
                  </Button>
                </div>
              ))}
            </div>
          )}
        </div>
      </Modal>

      {/* ========================================================= */}
      {/* MODAL 3: ALTERNATIVE WASTE WORKFLOW DRAWER                */}
      {/* ========================================================= */}
      <Modal
        isOpen={alternativeWorkflowModalOpen}
        onClose={() => setAlternativeWorkflowModalOpen(false)}
        title="Institutional Waste Diversion Protocol"
      >
        <div className="space-y-4">
          {activeItem && (
            <div className="space-y-3">
              <div className="p-3.5 rounded-2xl bg-rose-950/30 border border-rose-500/30 text-rose-200 text-xs">
                <div className="font-bold flex items-center gap-1.5 text-rose-300">
                  <ShieldAlert className="w-4 h-4 text-rose-400" />
                  <span>Human Consumption Disallowed by Food Safety Rules</span>
                </div>
                <p className="mt-1 text-[11px] leading-relaxed">
                  {activeItem.required_action}
                </p>
              </div>

              <div className="p-4 rounded-2xl bg-slate-900 border border-white/10 space-y-2.5">
                <div className="text-xs font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
                  <Recycle className="w-4 h-4 text-emerald-400" />
                  Mandatory Alternative Waste Workflow:
                </div>
                <div className="text-base font-bold text-white">
                  {activeItem.suggested_waste_workflow?.replace('_', ' ')}
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Per campus sustainability bylaws, this food lot is diverted to high-efficiency biological recovery
                  preventing organic landfill methane emission.
                </p>

                <div className="grid grid-cols-2 gap-2 text-xs pt-2">
                  <div className="p-2 rounded-xl bg-slate-800/60">
                    <span className="text-[10px] text-slate-400 uppercase">Weight Diverted</span>
                    <div className="font-bold text-white font-mono mt-0.5">{activeItem.quantity} {activeItem.unit}</div>
                  </div>
                  <div className="p-2 rounded-xl bg-slate-800/60">
                    <span className="text-[10px] text-slate-400 uppercase">CO2e Offset</span>
                    <div className="font-bold text-emerald-400 font-mono mt-0.5">
                      {(activeItem.quantity * 2.5).toFixed(1)} kg CO2e
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <Button
                  variant="primary"
                  onClick={() => {
                    setAlternativeWorkflowModalOpen(false);
                    onShowSuccess(`Waste diversion logged. Composting manifest generated.`);
                  }}
                  leftIcon={<Leaf className="w-3.5 h-3.5" />}
                >
                  Generate Diversion Manifest
                </Button>
              </div>
            </div>
          )}
        </div>
      </Modal>

      {/* ========================================================= */}
      {/* MODAL 4: MANAGER INSPECTION SIGN-OFF MODAL                 */}
      {/* ========================================================= */}
      <Modal
        isOpen={approvalModalOpen}
        onClose={() => setApprovalModalOpen(false)}
        title="Kitchen Manager Physical Inspection Sign-Off"
      >
        <div className="space-y-4">
          {activeItem && (
            <div className="space-y-3">
              <div className="p-3 rounded-2xl bg-amber-950/30 border border-amber-500/30 text-amber-200 text-xs">
                <div className="font-bold flex items-center gap-1.5 text-amber-300">
                  <UserCheck className="w-4 h-4 text-amber-400" />
                  <span>Authorized Physical Inspection Gate</span>
                </div>
                <p className="mt-1 text-[11px]">
                  This surplus lot has entered the critical 30-60 minute window. A Kitchen Manager must physically verify
                  temperature probe reading and sensory quality before donation dispatch is permitted.
                </p>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">
                  Verified Temperature Probe (°C) *
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={approvalVerifiedTemp}
                  onChange={(e) => setApprovalVerifiedTemp(e.target.value)}
                  className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500 font-mono"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">
                  Inspector Sensory Notes & Observations *
                </label>
                <textarea
                  rows={2}
                  value={approvalNotes}
                  onChange={(e) => setApprovalNotes(e.target.value)}
                  className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-white/10">
                <Button
                  variant="destructive"
                  isLoading={isSubmittingApproval}
                  onClick={() => handleSubmitApproval(false)}
                >
                  Reject & Route to Waste
                </Button>
                <Button
                  variant="primary"
                  isLoading={isSubmittingApproval}
                  onClick={() => handleSubmitApproval(true)}
                  leftIcon={<ShieldCheck className="w-3.5 h-3.5" />}
                >
                  Authorize For Donation
                </Button>
              </div>
            </div>
          )}
        </div>
      </Modal>
    </div>
  );
};
