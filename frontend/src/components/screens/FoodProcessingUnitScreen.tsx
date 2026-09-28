'use client';

import React, { useState, useEffect } from 'react';
import { 
  Building2, 
  Package, 
  Layers, 
  AlertTriangle, 
  ShieldAlert, 
  Clock, 
  Sparkles, 
  ArrowRight, 
  PlusCircle, 
  CheckCircle2, 
  HeartHandshake, 
  Search, 
  Filter, 
  Sliders, 
  RefreshCw, 
  FileText, 
  Barcode, 
  Truck, 
  Flame, 
  Wind, 
  Box, 
  Cpu, 
  Check, 
  X, 
  ExternalLink, 
  ChevronRight,
  ChevronDown,
  Info,
  Calendar,
  DollarSign,
  TrendingUp,
  Activity
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/design-system/Card';
import { KpiCard } from '@/components/design-system/KpiCard';
import { Badge } from '@/components/design-system/Badge';
import { Button } from '@/components/design-system/Button';
import { Modal } from '@/components/design-system/Modal';
import { ScreenId } from '@/components/navigation/Sidebar';
import { 
  FpuDashboardData,
  FpuRawMaterialItem,
  FpuProductionBatchItem,
  FefoQueueItem,
  FefoAllocationResult,
  FpuAlertItem,
  FpuThresholdRule,
  FpuTraceabilityChain
} from '@/types';
import { 
  fetchFpuDashboard,
  fetchFpuRawMaterials,
  intakeFpuRawMaterial,
  updateFpuRawMaterialStatus,
  allocateFpuFefo,
  fetchFpuFefoQueue,
  fetchFpuBatches,
  createFpuBatch,
  updateFpuBatchQuality,
  redistributeFpuBatchSurplus,
  fetchFpuTraceability,
  fetchFpuAlerts,
  fetchFpuThresholdRules,
  configureFpuThresholdRule
} from '@/lib/api';

interface FoodProcessingUnitScreenProps {
  onNavigate?: (screen: ScreenId) => void;
  onOpenDonateModal?: () => void;
  onShowSuccess?: (msg: string) => void;
}

type TabType = 'overview' | 'raw_materials' | 'fefo_engine' | 'production_batches' | 'quality_rejected' | 'traceability' | 'redistribution';

export const FoodProcessingUnitScreen: React.FC<FoodProcessingUnitScreenProps> = ({
  onNavigate,
  onOpenDonateModal,
  onShowSuccess
}) => {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [loading, setLoading] = useState(true);

  // Core Data States
  const [dashboard, setDashboard] = useState<FpuDashboardData | null>(null);
  const [rawMaterials, setRawMaterials] = useState<FpuRawMaterialItem[]>([]);
  const [batches, setBatches] = useState<FpuProductionBatchItem[]>([]);
  const [fefoQueue, setFefoQueue] = useState<FefoQueueItem[]>([]);
  const [thresholdRules, setThresholdRules] = useState<FpuThresholdRule[]>([]);
  const [alerts, setAlerts] = useState<FpuAlertItem[]>([]);

  // Traceability State
  const [traceSearchQuery, setTraceSearchQuery] = useState('PB-TOM-PUREE-2026-041');
  const [traceChain, setTraceChain] = useState<FpuTraceabilityChain | null>(null);
  const [loadingTrace, setLoadingTrace] = useState(false);

  // FEFO Simulator State
  const [simMaterial, setSimMaterial] = useState('Organic Roma Tomatoes');
  const [simQty, setSimQty] = useState(250);
  const [simResult, setSimResult] = useState<FefoAllocationResult | null>(null);
  const [loadingSim, setLoadingSim] = useState(false);

  // Modals
  const [showIntakeModal, setShowIntakeModal] = useState(false);
  const [showBatchModal, setShowBatchModal] = useState(false);
  const [showThresholdModal, setShowThresholdModal] = useState(false);
  const [showRedistributeModal, setShowRedistributeModal] = useState(false);
  const [showQcModal, setShowQcModal] = useState(false);

  // Selected item for QC or Redistribution
  const [selectedBatchForRedist, setSelectedBatchForRedist] = useState<FpuProductionBatchItem | null>(null);
  const [selectedBatchForQc, setSelectedBatchForQc] = useState<FpuProductionBatchItem | null>(null);

  // Form States
  const [intakeForm, setIntakeForm] = useState({
    material_name: '',
    category: 'PRODUCE',
    lot_number: '',
    initial_quantity: 500,
    unit: 'kg',
    storage_condition: 'REFRIGERATED',
    storage_location: 'Cold Room B-1',
    harvest_or_mfg_date: new Date().toISOString().split('T')[0],
    expiry_date: new Date(Date.now() + 5 * 86400000).toISOString().split('T')[0],
    supplier: 'Central Valley Growers',
    cost_per_unit: 1.20,
    quality_status: 'APPROVED',
    packaging_condition: 'INTACT'
  });

  const [batchForm, setBatchForm] = useState({
    product_name: '',
    category: 'PUREE',
    batch_number: '',
    planned_quantity: 300,
    actual_quantity: 290,
    unit: 'kg',
    manufacturing_date: new Date().toISOString().split('T')[0],
    expiry_date: new Date(Date.now() + 180 * 86400000).toISOString().split('T')[0],
    quality_status: 'PASSED',
    packaging_condition: 'INTACT',
    damaged_packaging_units: 0,
    rejected_quantity: 0,
    surplus_quantity: 60,
    raw_material_id: '',
    raw_qty: 300
  });

  const [redistForm, setRedistForm] = useState({
    redistribute_quantity: 50,
    recipient_id: 'rec-second-harvest',
    recipient_name: 'Second Harvest Regional Food Bank',
    notes: 'Aseptic pallet containers ready for emergency community meal kits'
  });

  const [thresholdForm, setThresholdForm] = useState({
    target_type: 'CATEGORY' as 'CATEGORY' | 'PRODUCT',
    target_name: 'DAIRY',
    warning_threshold_days: 7,
    urgent_threshold_days: 3,
    critical_threshold_days: 1,
    custom_safety_notes: ''
  });

  const [qcForm, setQcForm] = useState({
    quality_status: 'REJECTED' as 'PASSED' | 'UNDER_REVIEW' | 'REJECTED' | 'DAMAGED_PACKAGING',
    packaging_condition: 'DAMAGED_PACKAGING',
    damaged_packaging_units: 12,
    rejected_quantity: 12,
    rejection_reason: 'Vacuum seal compromise on aseptic packaging line',
    disposition_action: 'ANIMAL_FEED_VALORIZATION',
    qc_officer: 'Elena Rostova, QA Lead',
    notes: ''
  });

  // Filter States
  const [materialFilterCategory, setMaterialFilterCategory] = useState<string>('all');
  const [materialSearch, setMaterialSearch] = useState('');

  // Initial Load
  const loadAllData = async () => {
    setLoading(true);
    try {
      const [dashData, rmData, batchData, qData, rulesData, alertsData] = await Promise.all([
        fetchFpuDashboard(),
        fetchFpuRawMaterials(),
        fetchFpuBatches(),
        fetchFpuFefoQueue(),
        fetchFpuThresholdRules(),
        fetchFpuAlerts()
      ]);
      setDashboard(dashData);
      setRawMaterials(rmData);
      setBatches(batchData);
      setFefoQueue(qData);
      setThresholdRules(rulesData);
      setAlerts(alertsData.alerts);

      // Default Traceability Chain
      if (batchData.length > 0) {
        const trace = await fetchFpuTraceability(batchData[0].batch_number);
        setTraceChain(trace);
        setTraceSearchQuery(batchData[0].batch_number);
      }
    } catch (e) {
      console.error('Error loading FPU data', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAllData();
  }, []);

  // Handle FEFO Simulator
  const handleRunFefoSim = async () => {
    setLoadingSim(true);
    try {
      const result = await allocateFpuFefo('bay-area-fpu-04', {
        material_name: simMaterial,
        required_quantity: Number(simQty),
        unit: 'kg'
      });
      setSimResult(result);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingSim(false);
    }
  };

  // Handle Trace Search
  const handleSearchTrace = async () => {
    if (!traceSearchQuery.trim()) return;
    setLoadingTrace(true);
    try {
      const chain = await fetchFpuTraceability(traceSearchQuery.trim());
      setTraceChain(chain);
    } catch (e) {
      onShowSuccess?.(`No traceability record found for "${traceSearchQuery}". Try PB-TOM-PUREE-2026-041.`);
    } finally {
      setLoadingTrace(false);
    }
  };

  // Handle Intake Submit
  const handleIntakeSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await intakeFpuRawMaterial('bay-area-fpu-04', {
        ...intakeForm,
        harvest_or_mfg_date: new Date(intakeForm.harvest_or_mfg_date).toISOString(),
        expiry_date: new Date(intakeForm.expiry_date).toISOString()
      });
      setShowIntakeModal(false);
      onShowSuccess?.(`Successfully intaked ${intakeForm.initial_quantity} ${intakeForm.unit} of ${intakeForm.material_name}.`);
      loadAllData();
    } catch (err: any) {
      alert(err.message || 'Failed to intake raw material');
    }
  };

  // Handle Batch Submit
  const handleBatchSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createFpuBatch('bay-area-fpu-04', {
        product_name: batchForm.product_name,
        category: batchForm.category,
        batch_number: batchForm.batch_number || `PB-${Date.now().toString().slice(-6)}`,
        planned_quantity: Number(batchForm.planned_quantity),
        actual_quantity: Number(batchForm.actual_quantity),
        unit: batchForm.unit,
        manufacturing_date: new Date(batchForm.manufacturing_date).toISOString(),
        expiry_date: new Date(batchForm.expiry_date).toISOString(),
        quality_status: batchForm.quality_status,
        packaging_condition: batchForm.packaging_condition,
        damaged_packaging_units: Number(batchForm.damaged_packaging_units),
        rejected_quantity: Number(batchForm.rejected_quantity),
        surplus_quantity: Number(batchForm.surplus_quantity),
        raw_materials: batchForm.raw_material_id ? [
          {
            raw_material_id: batchForm.raw_material_id,
            quantity_used: Number(batchForm.raw_qty),
            fefo_sequence_order: 1
          }
        ] : []
      });
      setShowBatchModal(false);
      onShowSuccess?.(`Production batch "${batchForm.product_name}" generated with FEFO material allocation.`);
      loadAllData();
    } catch (err: any) {
      alert(err.message || 'Failed to create batch');
    }
  };

  // Handle Redistribution Submit
  const handleRedistributeSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedBatchForRedist) return;
    try {
      await redistributeFpuBatchSurplus(selectedBatchForRedist.id, {
        redistribute_quantity: Number(redistForm.redistribute_quantity),
        recipient_id: redistForm.recipient_id,
        notes: redistForm.notes
      });
      setShowRedistributeModal(false);
      onShowSuccess?.(`Declared ${redistForm.redistribute_quantity} ${selectedBatchForRedist.unit} of surplus for ${redistForm.recipient_name}.`);
      loadAllData();
    } catch (err: any) {
      alert(err.message || 'Failed to redistribute surplus');
    }
  };

  // Handle QC / Rejection Submit
  const handleQcSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedBatchForQc) return;
    try {
      await updateFpuBatchQuality(selectedBatchForQc.id, {
        quality_status: qcForm.quality_status,
        packaging_condition: qcForm.packaging_condition,
        damaged_packaging_units: Number(qcForm.damaged_packaging_units),
        rejected_quantity: Number(qcForm.rejected_quantity),
        rejection_reason: qcForm.rejection_reason,
        disposition_action: qcForm.disposition_action,
        qc_officer: qcForm.qc_officer,
        notes: qcForm.notes
      });
      setShowQcModal(false);
      onShowSuccess?.(`Quality check saved: Batch routed to ${qcForm.disposition_action.replace('_', ' ')}.`);
      loadAllData();
    } catch (err: any) {
      alert(err.message || 'Failed to update QC');
    }
  };

  // Handle Threshold Rule Save
  const handleThresholdSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await configureFpuThresholdRule('bay-area-fpu-04', {
        target_type: thresholdForm.target_type,
        target_name: thresholdForm.target_name,
        warning_threshold_days: Number(thresholdForm.warning_threshold_days),
        urgent_threshold_days: Number(thresholdForm.urgent_threshold_days),
        critical_threshold_days: Number(thresholdForm.critical_threshold_days),
        custom_safety_notes: thresholdForm.custom_safety_notes
      });
      setShowThresholdModal(false);
      onShowSuccess?.(`Configured alert threshold rule for ${thresholdForm.target_name}: 7d / 3d / 1d calibrated.`);
      loadAllData();
    } catch (err: any) {
      alert(err.message || 'Failed to save threshold rule');
    }
  };

  // Filtered raw materials
  const filteredMaterials = rawMaterials.filter((m) => {
    const matchesCat = materialFilterCategory === 'all' || m.category === materialFilterCategory;
    const matchesSearch = !materialSearch || 
      m.material_name.toLowerCase().includes(materialSearch.toLowerCase()) ||
      m.lot_number.toLowerCase().includes(materialSearch.toLowerCase());
    return matchesCat && matchesSearch;
  });

  return (
    <div className="space-y-6 animate-fade-in pb-12">
      
      {/* 1. Header Banner & Quick Action Buttons */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 glass-panel p-6 rounded-3xl border border-white/10 bg-slate-900 shadow-2xl relative overflow-hidden">
        <div className="absolute -top-12 -right-12 w-64 h-64 bg-amber-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10">
          <div className="flex items-center space-x-2.5">
            <span className="p-1.5 rounded-lg bg-amber-500/20 text-amber-400 border border-amber-500/30">
              <Building2 className="w-4 h-4" />
            </span>
            <Badge variant="warning" size="md">Phase 14 — Food Processing Unit</Badge>
            <span className="text-xs font-mono text-slate-400">Bay Area Valorization Plant #04</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight mt-1.5 flex items-center gap-2">
            Industrial Processing & Upcycling Console
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 max-w-2xl mt-1">
            Raw material intake, production batch yield, FEFO allocation engine, automated expiry alerts, 
            damaged packaging rejections, and complete 5-hop batch traceability.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5 relative z-10">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowThresholdModal(true)}
            leftIcon={<Sliders className="w-3.5 h-3.5 text-amber-400" />}
          >
            Alert Thresholds
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setActiveTab('fefo_engine');
              if (!simResult) handleRunFefoSim();
            }}
            leftIcon={<Flame className="w-3.5 h-3.5 text-cyan-400" />}
          >
            FEFO Simulator
          </Button>

          <Button
            variant="secondary"
            size="sm"
            onClick={() => setShowIntakeModal(true)}
            leftIcon={<PlusCircle className="w-3.5 h-3.5" />}
          >
            Intake Raw Material
          </Button>

          <Button
            variant="primary"
            size="sm"
            onClick={() => setShowBatchModal(true)}
            leftIcon={<Layers className="w-3.5 h-3.5" />}
          >
            New Batch
          </Button>
        </div>
      </div>

      {/* 2. Top Executive KPI Metric Bar (6 Core Requirements) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        {/* KPI 1: Inventory */}
        <KpiCard
          title="Total Inventory"
          value={dashboard ? dashboard.inventory.total_inventory_kg.toLocaleString() : '7,090'}
          unit="kg"
          subtitle={`${dashboard?.inventory.total_raw_material_kg ?? 4250}kg Raw · ${dashboard?.inventory.total_finished_product_kg ?? 2840}kg Finished`}
          icon={<Package className="w-5 h-5 text-emerald-400" />}
          accentColor="emerald"
          onClick={() => setActiveTab('raw_materials')}
        />

        {/* KPI 2: Near Expiry */}
        <KpiCard
          title="Near Expiry"
          value={dashboard ? dashboard.near_expiry.total_near_expiry_count : 5}
          unit="lots"
          subtitle={`${dashboard?.near_expiry.total_near_expiry_kg ?? 680}kg · 7d / 3d / 1d Alert`}
          icon={<AlertTriangle className="w-5 h-5 text-amber-400" />}
          accentColor="amber"
          onClick={() => setActiveTab('overview')}
        />

        {/* KPI 3: Expired */}
        <KpiCard
          title="Expired / Quarantined"
          value={dashboard ? dashboard.expired.total_expired_count : 1}
          unit="lots"
          subtitle={`${dashboard?.expired.total_expired_kg ?? 45}kg Quarantined`}
          icon={<ShieldAlert className="w-5 h-5 text-rose-400" />}
          accentColor="rose"
          onClick={() => setActiveTab('quality_rejected')}
        />

        {/* KPI 4: Production */}
        <KpiCard
          title="Production Batches"
          value={dashboard ? dashboard.production.completed_batches_count : 45}
          unit="batches"
          subtitle={`${dashboard?.production.average_yield_percentage ?? 97.4}% Yield · FEFO: 98.8%`}
          icon={<Cpu className="w-5 h-5 text-cyan-400" />}
          accentColor="cyan"
          onClick={() => setActiveTab('production_batches')}
        />

        {/* KPI 5: Rejected */}
        <KpiCard
          title="Rejected / Damaged"
          value={dashboard ? dashboard.rejected.damaged_units_count : 24}
          unit="units"
          subtitle={`${dashboard?.rejected.total_rejected_kg ?? 85}kg diverted to feed/biogas`}
          icon={<Box className="w-5 h-5 text-rose-400" />}
          accentColor="rose"
          onClick={() => setActiveTab('quality_rejected')}
        />

        {/* KPI 6: Redistributable Stock */}
        <KpiCard
          title="Redistributable Stock"
          value={dashboard ? dashboard.redistributable_stock.current_redistributable_stock_kg : 520}
          unit="kg"
          subtitle={`${dashboard?.redistributable_stock.active_recipient_partners_count ?? 6} Food Banks connected`}
          icon={<HeartHandshake className="w-5 h-5 text-indigo-400" />}
          accentColor="indigo"
          onClick={() => setActiveTab('redistribution')}
        />
      </div>

      {/* 3. Navigation Tab Bar */}
      <div className="flex border-b border-white/10 overflow-x-auto no-scrollbar space-x-1 sm:space-x-2">
        {[
          { id: 'overview', label: 'Dashboard & Expiry Alerts', icon: <Activity className="w-4 h-4" /> },
          { id: 'raw_materials', label: 'Raw Material Inventory', icon: <Package className="w-4 h-4" />, count: rawMaterials.length },
          { id: 'fefo_engine', label: 'FEFO Queue & Simulator', icon: <Flame className="w-4 h-4" /> },
          { id: 'production_batches', label: 'Production Batches', icon: <Layers className="w-4 h-4" />, count: batches.length },
          { id: 'quality_rejected', label: 'QC & Packaging Defects', icon: <ShieldAlert className="w-4 h-4" />, count: dashboard?.rejected.rejected_products_count ?? 2 },
          { id: 'redistribution', label: 'Surplus Redistribution', icon: <HeartHandshake className="w-4 h-4" />, count: `${dashboard?.redistributable_stock.current_redistributable_stock_kg ?? 520}kg` },
          { id: 'traceability', label: '5-Hop Batch Traceability', icon: <Barcode className="w-4 h-4" /> },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as TabType)}
            className={`flex items-center space-x-2 py-3 px-4 font-bold text-xs uppercase tracking-wider rounded-t-xl transition-all border-b-2 whitespace-nowrap ${
              activeTab === tab.id
                ? 'border-amber-400 text-white bg-white/5'
                : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-white/[0.02]'
            }`}
          >
            {tab.icon}
            <span>{tab.label}</span>
            {tab.count !== undefined && (
              <span className="ml-1.5 px-1.5 py-0.5 rounded-full text-[10px] bg-slate-800 text-slate-300 font-mono">
                {tab.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* ------------------------------------------------------------- */}
      {/* TAB 1: OVERVIEW & REAL-TIME AUTOMATIC EXPIRY ALERTS           */}
      {/* ------------------------------------------------------------- */}
      {activeTab === 'overview' && (
        <div className="space-y-6 animate-fade-in">
          
          {/* Automatic Expiry Alerts Panel */}
          <div className="p-6 rounded-3xl glass-panel border border-amber-500/30 bg-gradient-to-br from-amber-950/20 via-slate-900 to-slate-950">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-white/10">
              <div className="flex items-center space-x-3">
                <div className="p-2.5 rounded-xl bg-amber-500/20 text-amber-400 border border-amber-500/30">
                  <AlertTriangle className="w-5 h-5 animate-pulse" />
                </div>
                <div>
                  <h2 className="text-lg font-black text-white tracking-tight flex items-center gap-2">
                    Automated Expiry & Quality Alert System
                    <Badge variant="warning" size="sm">Configurable Thresholds</Badge>
                  </h2>
                  <p className="text-xs text-slate-400">
                    Proactive 7-day, 3-day, and 1-day threshold monitoring. Tailored per product and category rules.
                  </p>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowThresholdModal(true)}
                  leftIcon={<Sliders className="w-3.5 h-3.5" />}
                >
                  Configure Rules
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={loadAllData}
                  leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
                >
                  Re-evaluate
                </Button>
              </div>
            </div>

            {/* Alert Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-5">
              {alerts.map((alt) => {
                const isCrit = alt.alert_severity === 'CRITICAL_1_DAY';
                const isUrg = alt.alert_severity === 'URGENT_3_DAYS';
                const isWarn = alt.alert_severity === 'WARNING_7_DAYS';
                const isExp = alt.alert_severity === 'EXPIRED';
                const isDmg = alt.alert_severity === 'DAMAGED_PACKAGING';

                const borderCls = isExp ? 'border-rose-500/50 bg-rose-950/30' :
                  isCrit ? 'border-rose-500/40 bg-rose-950/20' :
                  isDmg ? 'border-amber-500/50 bg-amber-950/30' :
                  isUrg ? 'border-amber-500/30 bg-amber-950/15' : 'border-sky-500/20 bg-slate-900/80';

                return (
                  <div key={alt.alert_id} className={`p-4 rounded-2xl border transition-all ${borderCls} flex flex-col justify-between space-y-3`}>
                    <div>
                      <div className="flex items-start justify-between">
                        <Badge
                          variant={isExp || isCrit ? 'danger' : isDmg || isUrg ? 'warning' : 'info'}
                          size="sm"
                        >
                          {isExp ? 'EXPIRED' : isCrit ? '1-DAY CRITICAL' : isUrg ? '3-DAY URGENT' : isDmg ? 'DAMAGED PACKAGING' : '7-DAY WARNING'}
                        </Badge>
                        <span className="text-[11px] font-mono text-slate-400">
                          {alt.days_remaining <= 0 ? '0d remaining' : `${alt.days_remaining}d left`}
                        </span>
                      </div>

                      <div className="mt-2.5">
                        <div className="text-sm font-black text-white">{alt.name}</div>
                        <div className="text-xs font-mono text-slate-400 mt-0.5">
                          {alt.item_type === 'RAW_MATERIAL' ? `Lot: ${alt.code}` : `Batch: ${alt.code}`} · {alt.quantity} {alt.unit}
                        </div>
                      </div>

                      <div className="mt-2 text-[11px] text-slate-300 bg-black/30 p-2.5 rounded-xl border border-white/5">
                        <span className="font-semibold text-slate-200">Recommended Action:</span> {alt.recommended_action}
                      </div>
                    </div>

                    <div className="pt-2 border-t border-white/5 flex items-center justify-between text-[10px] text-slate-400">
                      <span>Rule: {alt.applicable_rule}</span>
                      <button
                        onClick={() => {
                          if (alt.item_type === 'RAW_MATERIAL') {
                            setActiveTab('fefo_engine');
                            setSimMaterial(alt.name);
                            setSimQty(Math.min(alt.quantity, 200));
                          } else {
                            setActiveTab('production_batches');
                          }
                        }}
                        className="text-amber-400 hover:text-white font-semibold flex items-center gap-1"
                      >
                        Action <ArrowRight className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Operational Facility Gauges */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Continuous Thermal Canning Line</CardTitle>
                <CardDescription>Aseptic Steam Sterilization (121°C)</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-baseline justify-between">
                  <span className="text-3xl font-black text-white">485 kg</span>
                  <span className="text-xs text-emerald-400 font-bold">Line Active · 18 min dwell</span>
                </div>
                <div className="w-full bg-slate-800 h-3 rounded-full overflow-hidden">
                  <div className="bg-emerald-500 h-full rounded-full" style={{ width: '92%' }} />
                </div>
                <p className="text-[11px] text-slate-400">
                  Processing surplus Roma tomato feedstock into hermetically sealed aseptic bag-in-box puree.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Dehydration & Powdering Line B</CardTitle>
                <CardDescription>Low-temp Fruit & Veg Air Drying</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-baseline justify-between">
                  <span className="text-3xl font-black text-white">188 kg</span>
                  <span className="text-xs text-amber-400 font-bold">Drying at 60°C · Aw 0.35</span>
                </div>
                <div className="w-full bg-slate-800 h-3 rounded-full overflow-hidden">
                  <div className="bg-amber-500 h-full rounded-full" style={{ width: '74%' }} />
                </div>
                <p className="text-[11px] text-slate-400">
                  Dehydrating sliced surplus apples into shelf-stable snacks. 14 units identified with seal defects routed to valorization.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Valorization Diversion (EPA Tier)</CardTitle>
                <CardDescription>Non-commercial byproduct allocation</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2.5 text-xs">
                <div className="flex justify-between items-center p-2 rounded-xl bg-slate-900 border border-white/5">
                  <span className="text-slate-300">Human Secondary Upcycling</span>
                  <span className="font-bold text-emerald-400">74.2%</span>
                </div>
                <div className="flex justify-between items-center p-2 rounded-xl bg-slate-900 border border-white/5">
                  <span className="text-slate-300">Livestock Feed Supplement</span>
                  <span className="font-bold text-amber-400">18.5%</span>
                </div>
                <div className="flex justify-between items-center p-2 rounded-xl bg-slate-900 border border-white/5">
                  <span className="text-slate-300">Compost & Biogas Digestion</span>
                  <span className="font-bold text-indigo-400">7.3%</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* TAB 2: RAW MATERIAL INVENTORY (FEFO RANKED)                   */}
      {/* ------------------------------------------------------------- */}
      {activeTab === 'raw_materials' && (
        <div className="space-y-4 animate-fade-in">
          
          {/* Controls Bar */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 glass-panel p-4 rounded-2xl border border-white/10">
            <div className="flex items-center space-x-2 w-full sm:w-auto">
              <div className="relative flex-1 sm:w-72">
                <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search raw material name, lot #, supplier..."
                  value={materialSearch}
                  onChange={(e) => setMaterialSearch(e.target.value)}
                  className="w-full bg-slate-900 border border-white/10 rounded-xl pl-9 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-amber-500"
                />
              </div>

              <select
                value={materialFilterCategory}
                onChange={(e) => setMaterialFilterCategory(e.target.value)}
                className="bg-slate-900 border border-white/10 rounded-xl px-3 py-1.5 text-xs text-white focus:outline-none focus:border-amber-500"
              >
                <option value="all">All Categories</option>
                <option value="PRODUCE">Produce</option>
                <option value="DAIRY">Dairy</option>
                <option value="GRAINS">Grains</option>
                <option value="BAKERY_TRIMMINGS">Bakery Trimmings</option>
                <option value="LIQUIDS">Liquids</option>
              </select>
            </div>

            <Button
              variant="primary"
              size="sm"
              onClick={() => setShowIntakeModal(true)}
              leftIcon={<PlusCircle className="w-3.5 h-3.5" />}
            >
              Intake Feedstock Lot
            </Button>
          </div>

          {/* Table */}
          <div className="glass-panel rounded-2xl border border-white/10 overflow-hidden shadow-xl">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-900/90 text-slate-400 font-semibold uppercase tracking-wider border-b border-white/10">
                  <tr>
                    <th className="py-3 px-4">Lot # / Material</th>
                    <th className="py-3 px-4">Category</th>
                    <th className="py-3 px-4">Available Qty</th>
                    <th className="py-3 px-4">Storage Location</th>
                    <th className="py-3 px-4">Mfg / Harvest</th>
                    <th className="py-3 px-4">Expiry Date</th>
                    <th className="py-3 px-4">Urgency Tier</th>
                    <th className="py-3 px-4">Quality & Packaging</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5 font-normal text-slate-300">
                  {filteredMaterials.map((m) => (
                    <tr key={m.id} className="hover:bg-white/[0.02] transition-colors">
                      <td className="py-3 px-4">
                        <div className="font-bold text-white">{m.material_name}</div>
                        <div className="text-[11px] font-mono text-amber-400">{m.lot_number}</div>
                        <div className="text-[10px] text-slate-400">{m.supplier || 'Regional Co-op'}</div>
                      </td>
                      <td className="py-3 px-4">
                        <Badge variant="neutral" size="sm">{m.category}</Badge>
                      </td>
                      <td className="py-3 px-4 font-mono font-bold text-white">
                        {m.current_quantity} <span className="text-[10px] text-slate-400 font-normal">/ {m.initial_quantity} {m.unit}</span>
                      </td>
                      <td className="py-3 px-4">
                        <div>{m.storage_location}</div>
                        <div className="text-[10px] text-slate-400 font-mono">{m.storage_condition}</div>
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-400">
                        {new Date(m.harvest_or_mfg_date).toLocaleDateString()}
                      </td>
                      <td className="py-3 px-4 font-mono">
                        {new Date(m.expiry_date).toLocaleDateString()}
                      </td>
                      <td className="py-3 px-4">
                        <Badge
                          variant={
                            m.expiry_urgency_tier === 'EXPIRED' ? 'danger' :
                            m.expiry_urgency_tier === 'CRITICAL_1_DAY' ? 'danger' :
                            m.expiry_urgency_tier === 'URGENT_3_DAYS' ? 'warning' :
                            m.expiry_urgency_tier === 'WARNING_7_DAYS' ? 'info' : 'success'
                          }
                          size="sm"
                        >
                          {m.days_to_expiry <= 0 ? 'EXPIRED' : `${m.days_to_expiry}d left`}
                        </Badge>
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-center space-x-1.5">
                          <Badge
                            variant={m.quality_status === 'APPROVED' ? 'success' : 'danger'}
                            size="sm"
                          >
                            {m.quality_status}
                          </Badge>
                          {m.packaging_condition === 'DAMAGED_PACKAGING' && (
                            <Badge variant="warning" size="sm">DAMAGED</Badge>
                          )}
                        </div>
                        {m.rejection_reason && (
                          <div className="text-[10px] text-rose-400 mt-1">{m.rejection_reason}</div>
                        )}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={() => {
                            setActiveTab('fefo_engine');
                            setSimMaterial(m.material_name);
                            setSimQty(Math.min(m.current_quantity, 150));
                          }}
                          className="px-2.5 py-1 rounded-lg text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20 hover:bg-amber-500/20"
                        >
                          FEFO Pick
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* TAB 3: FEFO (FIRST EXPIRE, FIRST OUT) QUEUE & SIMULATOR       */}
      {/* ------------------------------------------------------------- */}
      {activeTab === 'fefo_engine' && (
        <div className="space-y-6 animate-fade-in">
          
          {/* FEFO Interactive Simulator Banner */}
          <div className="p-6 rounded-3xl glass-panel border border-cyan-500/30 bg-gradient-to-br from-cyan-950/30 via-slate-900 to-slate-950 shadow-2xl">
            <div className="flex items-center space-x-3 pb-4 border-b border-white/10">
              <div className="p-2.5 rounded-xl bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
                <Flame className="w-5 h-5 animate-pulse" />
              </div>
              <div>
                <h2 className="text-lg font-black text-white tracking-tight flex items-center gap-2">
                  FEFO (First Expire, First Out) Optimization Engine
                  <Badge variant="cyan" size="sm">Strict Expiry Sequencing</Badge>
                </h2>
                <p className="text-xs text-slate-400">
                  Guarantees that raw material lots with the earliest expiration dates are consumed first. Prevents spoilage and ensures food quality.
                </p>
              </div>
            </div>

            {/* Interactive Inputs */}
            <div className="grid grid-cols-1 sm:grid-cols-12 gap-4 mt-5">
              <div className="sm:col-span-6 space-y-1">
                <label className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Target Raw Material Name</label>
                <input
                  type="text"
                  value={simMaterial}
                  onChange={(e) => setSimMaterial(e.target.value)}
                  placeholder="e.g. Organic Roma Tomatoes, Sweet Apples"
                  className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="sm:col-span-3 space-y-1">
                <label className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Batch Quantity Required (kg)</label>
                <input
                  type="number"
                  min={10}
                  max={5000}
                  step={10}
                  value={simQty}
                  onChange={(e) => setSimQty(Number(e.target.value))}
                  className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="sm:col-span-3 flex items-end">
                <Button
                  variant="primary"
                  size="md"
                  onClick={handleRunFefoSim}
                  disabled={loadingSim}
                  className="w-full"
                  leftIcon={<Sparkles className="w-4 h-4 text-cyan-300" />}
                >
                  {loadingSim ? 'Calculating...' : 'Run FEFO Allocation'}
                </Button>
              </div>
            </div>

            {/* Allocation Results */}
            {simResult && (
              <div className="mt-6 p-5 rounded-2xl bg-black/40 border border-white/10 space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">FEFO Compliance Score:</span>
                      <Badge variant="success" size="md">{simResult.fefo_compliance_score}% ADHERENCE</Badge>
                    </div>
                    <div className="text-sm font-semibold text-white mt-1">
                      {simResult.total_allocated} kg allocated of {simResult.required_quantity} kg requested
                    </div>
                  </div>

                  <div className="text-xs font-mono text-emerald-400 bg-emerald-950/30 px-3 py-1.5 rounded-xl border border-emerald-500/30">
                    {simResult.is_fulfilled ? '✓ Requirement Fully Fulfilled' : `⚠ Shortage: ${simResult.shortage_quantity} kg`}
                  </div>
                </div>

                {/* Step-by-Step Pick Table */}
                <div className="space-y-2">
                  <div className="text-xs font-bold uppercase tracking-wider text-slate-400">Optimal FEFO Pick Sequence:</div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {simResult.pick_list.map((step) => (
                      <div key={step.raw_material_id} className="p-3.5 rounded-xl bg-slate-900 border border-white/10 flex items-start justify-between">
                        <div className="space-y-1">
                          <div className="flex items-center space-x-2">
                            <span className="w-5 h-5 rounded-full bg-cyan-500/20 text-cyan-400 font-bold text-xs flex items-center justify-center border border-cyan-500/30">
                              {step.fefo_sequence}
                            </span>
                            <span className="font-bold text-white text-xs">{step.material_name}</span>
                          </div>
                          <div className="text-[11px] font-mono text-amber-400">Lot: {step.lot_number}</div>
                          <div className="text-[10px] text-slate-400">
                            Location: {step.storage_location} · Expires in {step.days_to_expiry} days
                          </div>
                        </div>

                        <div className="text-right">
                          <div className="text-sm font-black text-white font-mono">{step.allocated_quantity} {step.unit}</div>
                          <div className="text-[10px] text-slate-400 font-mono">
                            Remaining in lot: {step.remaining_in_lot} {step.unit}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Priority Real-time Consumption Queue */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-black uppercase tracking-wider text-white">Live FEFO Consumption Priority Queue</h3>
                <p className="text-xs text-slate-400">Active lots arranged strictly by earliest expiration date</p>
              </div>
              <Badge variant="neutral" size="sm">{fefoQueue.length} Lots Queued</Badge>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {fefoQueue.map((item) => (
                <div key={item.raw_material_id} className="p-4 rounded-2xl glass-panel border border-white/10 bg-slate-900/80 flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <span className="w-8 h-8 rounded-xl bg-slate-800 text-slate-300 font-black text-xs flex items-center justify-center border border-white/10 font-mono">
                      #{item.fefo_priority_rank}
                    </span>
                    <div>
                      <div className="text-xs font-bold text-white">{item.material_name}</div>
                      <div className="text-[11px] font-mono text-amber-400">{item.lot_number}</div>
                      <div className="text-[10px] text-slate-400">{item.current_quantity} {item.unit} available</div>
                    </div>
                  </div>

                  <div className="text-right space-y-1">
                    <Badge
                      variant={
                        item.urgency_tier === 'EXPIRED' ? 'danger' :
                        item.urgency_tier === 'CRITICAL_1_DAY' ? 'danger' :
                        item.urgency_tier === 'URGENT_3_DAYS' ? 'warning' : 'info'
                      }
                      size="sm"
                    >
                      {item.days_to_expiry <= 0 ? 'EXPIRED' : `${item.days_to_expiry}d left`}
                    </Badge>
                    <div className="text-[9px] text-slate-400 font-mono">
                      {new Date(item.expiry_date).toLocaleDateString()}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* TAB 4: PRODUCTION BATCHES & UPCYCLING LINE                   */}
      {/* ------------------------------------------------------------- */}
      {activeTab === 'production_batches' && (
        <div className="space-y-4 animate-fade-in">
          
          <div className="flex justify-between items-center glass-panel p-4 rounded-2xl border border-white/10">
            <div>
              <h3 className="text-sm font-black text-white">Active & Completed Production Batches</h3>
              <p className="text-xs text-slate-400">Tracking planned vs actual yield, quality verification, and surplus declaration</p>
            </div>

            <Button
              variant="primary"
              size="sm"
              onClick={() => setShowBatchModal(true)}
              leftIcon={<PlusCircle className="w-3.5 h-3.5" />}
            >
              New Batch Line
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {batches.map((b) => (
              <div key={b.id} className="p-5 rounded-3xl glass-panel border border-white/10 bg-slate-900/90 shadow-xl flex flex-col justify-between space-y-4">
                <div>
                  <div className="flex items-start justify-between">
                    <div>
                      <Badge variant="neutral" size="sm">{b.category}</Badge>
                      <h4 className="text-base font-black text-white mt-1.5">{b.product_name}</h4>
                      <div className="text-xs font-mono text-amber-400">{b.batch_number}</div>
                    </div>
                    <Badge
                      variant={b.quality_status === 'PASSED' ? 'success' : 'danger'}
                      size="sm"
                    >
                      {b.quality_status}
                    </Badge>
                  </div>

                  {/* Quantity & Yield Metrics */}
                  <div className="grid grid-cols-2 gap-2 mt-4 p-3 rounded-2xl bg-black/40 border border-white/5 text-xs">
                    <div>
                      <span className="text-[10px] uppercase font-bold text-slate-400">Yield Quantity</span>
                      <div className="font-mono font-bold text-white text-sm">
                        {b.actual_quantity} <span className="text-xs font-normal text-slate-400">{b.unit}</span>
                      </div>
                      <div className="text-[10px] text-emerald-400 font-mono">{b.yield_percentage}% efficiency</div>
                    </div>

                    <div>
                      <span className="text-[10px] uppercase font-bold text-slate-400">Surplus Available</span>
                      <div className="font-mono font-bold text-indigo-400 text-sm">
                        {b.redistributable_stock} <span className="text-xs font-normal text-slate-400">{b.unit}</span>
                      </div>
                      <div className="text-[10px] text-slate-400">Ready for donation</div>
                    </div>
                  </div>

                  {/* Manufacturing & Expiry */}
                  <div className="mt-3 space-y-1 text-[11px] text-slate-300">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Mfg Date:</span>
                      <span className="font-mono">{new Date(b.manufacturing_date).toLocaleDateString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Best Before:</span>
                      <span className="font-mono font-bold text-amber-400">{new Date(b.expiry_date).toLocaleDateString()}</span>
                    </div>
                    {b.damaged_packaging_units > 0 && (
                      <div className="flex justify-between text-rose-400">
                        <span>Damaged Units:</span>
                        <span className="font-bold">{b.damaged_packaging_units} units</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Card Action Buttons */}
                <div className="pt-3 border-t border-white/10 flex items-center justify-between gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setSelectedBatchForQc(b);
                      setQcForm({
                        quality_status: b.quality_status as any,
                        packaging_condition: b.packaging_condition,
                        damaged_packaging_units: b.damaged_packaging_units,
                        rejected_quantity: b.rejected_quantity,
                        rejection_reason: b.rejection_reason || '',
                        disposition_action: b.disposition_action || 'ANIMAL_FEED_VALORIZATION',
                        qc_officer: b.qc_officer || 'Elena Rostova, QA Lead',
                        notes: ''
                      });
                      setShowQcModal(true);
                    }}
                    className="flex-1 text-xs"
                  >
                    Inspect QC
                  </Button>

                  {b.redistributable_stock > 0 && (
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => {
                        setSelectedBatchForRedist(b);
                        setRedistForm({
                          ...redistForm,
                          redistribute_quantity: b.redistributable_stock
                        });
                        setShowRedistributeModal(true);
                      }}
                      className="flex-1 text-xs"
                      leftIcon={<HeartHandshake className="w-3.5 h-3.5" />}
                    >
                      Redistribute
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* TAB 5: QUALITY CONTROL, DAMAGED PACKAGING & REJECTIONS        */}
      {/* ------------------------------------------------------------- */}
      {activeTab === 'quality_rejected' && (
        <div className="space-y-6 animate-fade-in">
          
          <div className="p-6 rounded-3xl glass-panel border border-rose-500/30 bg-gradient-to-br from-rose-950/20 via-slate-900 to-slate-950 shadow-2xl">
            <div className="flex items-center space-x-3 pb-4 border-b border-white/10">
              <div className="p-2.5 rounded-xl bg-rose-500/20 text-rose-400 border border-rose-500/30">
                <ShieldAlert className="w-5 h-5 animate-pulse" />
              </div>
              <div>
                <h2 className="text-lg font-black text-white tracking-tight flex items-center gap-2">
                  Quality Assurance & Valorization Station
                  <Badge variant="danger" size="sm">HACCP Audit Station</Badge>
                </h2>
                <p className="text-xs text-slate-400">
                  Inspection of damaged packaging, seal integrity failures, and rejected goods. Direct diversion to animal feed or biogas to avoid landfill waste.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-5">
              {batches.filter(b => b.quality_status === 'REJECTED' || b.quality_status === 'DAMAGED_PACKAGING').map((b) => (
                <div key={b.id} className="p-4 rounded-2xl bg-black/40 border border-rose-500/30 space-y-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <Badge variant="danger" size="sm">QC REJECTION / DEFECT</Badge>
                      <h4 className="text-sm font-black text-white mt-1">{b.product_name}</h4>
                      <div className="text-xs font-mono text-amber-400">{b.batch_number}</div>
                    </div>
                    <span className="text-xs font-bold text-rose-400 font-mono">
                      {b.damaged_packaging_units} units compromised
                    </span>
                  </div>

                  <div className="text-xs text-slate-300 bg-slate-900/80 p-3 rounded-xl border border-white/5 space-y-1">
                    <div><span className="font-semibold text-slate-400">Defect Reason:</span> {b.rejection_reason || 'Vacuum seal failure during packaging cycle'}</div>
                    <div><span className="font-semibold text-slate-400">Disposition Tier:</span> <span className="text-amber-400 font-bold">{b.disposition_action?.replace('_', ' ') || 'ANIMAL FEED VALORIZATION'}</span></div>
                    <div><span className="font-semibold text-slate-400">Inspected By:</span> {b.qc_officer || 'Elena Rostova, QA Lead'}</div>
                  </div>

                  <div className="text-[11px] text-emerald-400 bg-emerald-950/20 p-2 rounded-lg border border-emerald-500/20">
                    ✓ Diverted from landfill. EPA tier compliance certified.
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* TAB 6: SURPLUS REDISTRIBUTION HUB                             */}
      {/* ------------------------------------------------------------- */}
      {activeTab === 'redistribution' && (
        <div className="space-y-6 animate-fade-in">
          
          <div className="p-6 rounded-3xl glass-panel border border-indigo-500/30 bg-gradient-to-br from-indigo-950/20 via-slate-900 to-slate-950 shadow-2xl">
            <div className="flex items-center space-x-3 pb-4 border-b border-white/10">
              <div className="p-2.5 rounded-xl bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
                <HeartHandshake className="w-5 h-5 text-indigo-400" />
              </div>
              <div>
                <h2 className="text-lg font-black text-white tracking-tight flex items-center gap-2">
                  Redistributable Surplus Finished Goods
                  <Badge variant="indigo" size="sm">Regional Rescue Network</Badge>
                </h2>
                <p className="text-xs text-slate-400">
                  Finished products exceeding planned demand ready for broadcast and distribution to local food banks and soup kitchens.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-5">
              {batches.filter(b => b.redistributable_stock > 0).map((b) => (
                <div key={b.id} className="p-4 rounded-2xl bg-black/40 border border-indigo-500/30 space-y-3 flex flex-col justify-between">
                  <div>
                    <Badge variant="indigo" size="sm">READY FOR DONATION</Badge>
                    <h4 className="text-sm font-black text-white mt-1.5">{b.product_name}</h4>
                    <div className="text-xs font-mono text-amber-400">{b.batch_number}</div>

                    <div className="mt-3 p-3 rounded-xl bg-slate-900/80 border border-white/5 space-y-1 text-xs">
                      <div className="flex justify-between">
                        <span className="text-slate-400">Surplus Balance:</span>
                        <span className="font-bold text-white font-mono">{b.redistributable_stock} {b.unit}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Shelf Life Expiry:</span>
                        <span className="font-bold text-amber-400 font-mono">{new Date(b.expiry_date).toLocaleDateString()}</span>
                      </div>
                    </div>
                  </div>

                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => {
                      setSelectedBatchForRedist(b);
                      setRedistForm({
                        ...redistForm,
                        redistribute_quantity: b.redistributable_stock
                      });
                      setShowRedistributeModal(true);
                    }}
                    className="w-full"
                    leftIcon={<Truck className="w-3.5 h-3.5" />}
                  >
                    Allocate to Food Bank
                  </Button>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* TAB 7: 5-HOP BATCH TRACEABILITY EXPLORER                      */}
      {/* ------------------------------------------------------------- */}
      {activeTab === 'traceability' && (
        <div className="space-y-6 animate-fade-in">
          
          {/* Search Header */}
          <div className="glass-panel p-6 rounded-3xl border border-white/10 bg-slate-900 shadow-xl space-y-4">
            <div>
              <h2 className="text-lg font-black text-white tracking-tight flex items-center gap-2">
                <Barcode className="w-5 h-5 text-amber-400" />
                End-to-End Batch Traceability Explorer
              </h2>
              <p className="text-xs text-slate-400">
                Complete unbroken digital lineage from intake farm lot through factory sterilization, finished product packaging, surplus broadcast, to certified recipient handoff.
              </p>
            </div>

            <div className="flex items-center space-x-2 max-w-xl">
              <div className="relative flex-1">
                <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type="text"
                  placeholder="Enter Batch Code (e.g. PB-TOM-PUREE-2026-041) or Lot #"
                  value={traceSearchQuery}
                  onChange={(e) => setTraceSearchQuery(e.target.value)}
                  className="w-full bg-slate-950 border border-white/15 rounded-xl pl-9 pr-3 py-2 text-xs text-white focus:outline-none focus:border-amber-400"
                />
              </div>
              <Button
                variant="primary"
                size="md"
                onClick={handleSearchTrace}
                disabled={loadingTrace}
                leftIcon={<Search className="w-3.5 h-3.5" />}
              >
                {loadingTrace ? 'Tracing...' : 'Trace Batch'}
              </Button>
            </div>
          </div>

          {/* Trace Results Visualization */}
          {traceChain && (
            <div className="space-y-6">
              
              {/* Chain Overview Banner */}
              <div className="p-4 rounded-2xl bg-emerald-950/20 border border-emerald-500/30 text-emerald-300 text-xs flex items-center space-x-3">
                <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
                <div>
                  <span className="font-bold">Digital Chain of Custody Verified:</span> {traceChain.summary}
                </div>
              </div>

              {/* 5-Step Visual Flowchart */}
              <div className="grid grid-cols-1 lg:grid-cols-5 gap-3 relative">
                {traceChain.linear_trace_steps.map((node, index) => {
                  const isFirst = index === 0;
                  const isLast = index === traceChain.linear_trace_steps.length - 1;

                  return (
                    <div key={node.step} className="p-4 rounded-2xl glass-panel border border-white/10 bg-slate-900/90 flex flex-col justify-between space-y-3 relative group hover:border-amber-400/50 transition-all shadow-xl">
                      <div>
                        <div className="flex items-center justify-between">
                          <span className="w-6 h-6 rounded-full bg-amber-500/20 text-amber-400 font-black text-xs flex items-center justify-center border border-amber-500/30">
                            {node.step}
                          </span>
                          <Badge variant="neutral" size="sm">{node.stage.replace('_', ' ')}</Badge>
                        </div>

                        <div className="mt-3">
                          <div className="text-xs font-mono text-amber-400 font-bold">{node.identifier}</div>
                          <div className="text-sm font-black text-white mt-0.5 leading-snug">{node.name}</div>
                        </div>

                        <div className="mt-3 p-2.5 rounded-xl bg-black/40 border border-white/5 text-[11px] space-y-1 text-slate-300">
                          <div><span className="text-slate-400">Facility / Org:</span> {node.facility_or_org}</div>
                          <div><span className="text-slate-400">Qty:</span> <span className="font-mono font-bold text-white">{node.quantity} {node.unit}</span></div>
                          <div><span className="text-slate-400">Status:</span> <span className="text-emerald-400 font-bold">{node.quality_status}</span></div>
                        </div>
                      </div>

                      <div className="text-[10px] text-slate-400 font-mono pt-2 border-t border-white/5">
                        {node.timestamp ? new Date(node.timestamp).toLocaleString() : 'Logged & Audited'}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ============================================================= */}
      {/* MODAL 1: INTAKE RAW MATERIAL MODAL                            */}
      {/* ============================================================= */}
      <Modal
        isOpen={showIntakeModal}
        onClose={() => setShowIntakeModal(false)}
        title="Intake Raw Material Feedstock"
      >
        <form onSubmit={handleIntakeSubmit} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-[11px] font-bold uppercase text-slate-400">Material Name *</label>
              <input
                type="text"
                required
                value={intakeForm.material_name}
                onChange={(e) => setIntakeForm({ ...intakeForm, material_name: e.target.value })}
                placeholder="e.g. Organic Roma Tomatoes"
                className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-500"
              />
            </div>

            <div className="space-y-1">
              <label className="text-[11px] font-bold uppercase text-slate-400">Category *</label>
              <select
                value={intakeForm.category}
                onChange={(e) => setIntakeForm({ ...intakeForm, category: e.target.value })}
                className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-500"
              >
                <option value="PRODUCE">Produce</option>
                <option value="DAIRY">Dairy</option>
                <option value="GRAINS">Grains</option>
                <option value="BAKERY_TRIMMINGS">Bakery Trimmings</option>
                <option value="LIQUIDS">Liquids</option>
                <option value="PACKAGING">Packaging</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="space-y-1">
              <label className="text-[11px] font-bold uppercase text-slate-400">Lot Number *</label>
              <input
                type="text"
                required
                value={intakeForm.lot_number}
                onChange={(e) => setIntakeForm({ ...intakeForm, lot_number: e.target.value })}
                placeholder="e.g. LOT-TOM-2026-08"
                className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-500"
              />
            </div>

            <div className="space-y-1">
              <label className="text-[11px] font-bold uppercase text-slate-400">Quantity *</label>
              <input
                type="number"
                required
                min={1}
                value={intakeForm.initial_quantity}
                onChange={(e) => setIntakeForm({ ...intakeForm, initial_quantity: Number(e.target.value) })}
                className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-500"
              />
            </div>

            <div className="space-y-1">
              <label className="text-[11px] font-bold uppercase text-slate-400">Unit</label>
              <input
                type="text"
                value={intakeForm.unit}
                onChange={(e) => setIntakeForm({ ...intakeForm, unit: e.target.value })}
                className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-[11px] font-bold uppercase text-slate-400">Harvest / Mfg Date *</label>
              <input
                type="date"
                required
                value={intakeForm.harvest_or_mfg_date}
                onChange={(e) => setIntakeForm({ ...intakeForm, harvest_or_mfg_date: e.target.value })}
                className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-500"
              />
            </div>

            <div className="space-y-1">
              <label className="text-[11px] font-bold uppercase text-slate-400">Expiry Date (FEFO) *</label>
              <input
                type="date"
                required
                value={intakeForm.expiry_date}
                onChange={(e) => setIntakeForm({ ...intakeForm, expiry_date: e.target.value })}
                className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-[11px] font-bold uppercase text-slate-400">Storage Location</label>
              <input
                type="text"
                value={intakeForm.storage_location}
                onChange={(e) => setIntakeForm({ ...intakeForm, storage_location: e.target.value })}
                className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-500"
              />
            </div>

            <div className="space-y-1">
              <label className="text-[11px] font-bold uppercase text-slate-400">Supplier Name</label>
              <input
                type="text"
                value={intakeForm.supplier}
                onChange={(e) => setIntakeForm({ ...intakeForm, supplier: e.target.value })}
                className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-500"
              />
            </div>
          </div>

          <div className="flex justify-end space-x-2 pt-3 border-t border-white/10">
            <Button variant="outline" size="sm" onClick={() => setShowIntakeModal(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" type="submit">
              Save Feedstock Intake
            </Button>
          </div>
        </form>
      </Modal>

      {/* ============================================================= */}
      {/* MODAL 2: NEW PRODUCTION BATCH MODAL                           */}
      {/* ============================================================= */}
      <Modal
        isOpen={showBatchModal}
        onClose={() => setShowBatchModal(false)}
        title="Launch Production Batch (With FEFO Allocation)"
      >
        <form onSubmit={handleBatchSubmit} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-[11px] font-bold uppercase text-slate-400">Finished Product Name *</label>
              <input
                type="text"
                required
                value={batchForm.product_name}
                onChange={(e) => setBatchForm({ ...batchForm, product_name: e.target.value })}
                placeholder="e.g. Sterilized Tomato Puree"
                className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-500"
              />
            </div>

            <div className="space-y-1">
              <label className="text-[11px] font-bold uppercase text-slate-400">Category *</label>
              <select
                value={batchForm.category}
                onChange={(e) => setBatchForm({ ...batchForm, category: e.target.value })}
                className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-500"
              >
                <option value="PUREE">Puree (Canned)</option>
                <option value="PROCESSED_CANNING">Aseptic Canning</option>
                <option value="DEHYDRATED">Dehydrated / Dried</option>
                <option value="BAKERY_REPROCESSED">Bakery Flour / Crumbs</option>
                <option value="JUICE_BEVERAGE">Juice / Beverage</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="space-y-1">
              <label className="text-[11px] font-bold uppercase text-slate-400">Planned Qty (kg) *</label>
              <input
                type="number"
                required
                value={batchForm.planned_quantity}
                onChange={(e) => setBatchForm({ ...batchForm, planned_quantity: Number(e.target.value) })}
                className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-500"
              />
            </div>

            <div className="space-y-1">
              <label className="text-[11px] font-bold uppercase text-slate-400">Actual Yield (kg) *</label>
              <input
                type="number"
                required
                value={batchForm.actual_quantity}
                onChange={(e) => setBatchForm({ ...batchForm, actual_quantity: Number(e.target.value) })}
                className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-500"
              />
            </div>

            <div className="space-y-1">
              <label className="text-[11px] font-bold uppercase text-slate-400">Surplus Output (kg)</label>
              <input
                type="number"
                value={batchForm.surplus_quantity}
                onChange={(e) => setBatchForm({ ...batchForm, surplus_quantity: Number(e.target.value) })}
                className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-500"
              />
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-[11px] font-bold uppercase text-slate-400">Consume Raw Material Lot (FEFO Auto-Pick)</label>
            <select
              value={batchForm.raw_material_id}
              onChange={(e) => setBatchForm({ ...batchForm, raw_material_id: e.target.value })}
              className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-500"
            >
              <option value="">Select available lot...</option>
              {rawMaterials.filter(r => r.status === 'AVAILABLE').map(r => (
                <option key={r.id} value={r.id}>
                  {r.material_name} (Lot: {r.lot_number} · {r.current_quantity} {r.unit} · Exp: {new Date(r.expiry_date).toLocaleDateString()})
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-[11px] font-bold uppercase text-slate-400">Manufacturing Date *</label>
              <input
                type="date"
                required
                value={batchForm.manufacturing_date}
                onChange={(e) => setBatchForm({ ...batchForm, manufacturing_date: e.target.value })}
                className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-500"
              />
            </div>

            <div className="space-y-1">
              <label className="text-[11px] font-bold uppercase text-slate-400">Best Before / Expiry *</label>
              <input
                type="date"
                required
                value={batchForm.expiry_date}
                onChange={(e) => setBatchForm({ ...batchForm, expiry_date: e.target.value })}
                className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-500"
              />
            </div>
          </div>

          <div className="flex justify-end space-x-2 pt-3 border-t border-white/10">
            <Button variant="outline" size="sm" onClick={() => setShowBatchModal(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" type="submit">
              Produce Batch & Deduct FEFO Lots
            </Button>
          </div>
        </form>
      </Modal>

      {/* ============================================================= */}
      {/* MODAL 3: SURPLUS REDISTRIBUTION MODAL                         */}
      {/* ============================================================= */}
      <Modal
        isOpen={showRedistributeModal}
        onClose={() => setShowRedistributeModal(false)}
        title={`Redistribute Surplus: ${selectedBatchForRedist?.product_name || 'Batch'}`}
      >
        <form onSubmit={handleRedistributeSubmit} className="space-y-4">
          <div className="p-3 rounded-2xl bg-indigo-950/30 border border-indigo-500/30 text-xs space-y-1 text-slate-300">
            <div><span className="font-semibold text-slate-400">Batch Code:</span> {selectedBatchForRedist?.batch_number}</div>
            <div><span className="font-semibold text-slate-400">Available Surplus Balance:</span> <span className="font-bold text-white font-mono">{selectedBatchForRedist?.redistributable_stock} {selectedBatchForRedist?.unit}</span></div>
          </div>

          <div className="space-y-1">
            <label className="text-[11px] font-bold uppercase text-slate-400">Quantity to Donate (kg) *</label>
            <input
              type="number"
              required
              min={1}
              max={selectedBatchForRedist?.redistributable_stock || 1000}
              value={redistForm.redistribute_quantity}
              onChange={(e) => setRedistForm({ ...redistForm, redistribute_quantity: Number(e.target.value) })}
              className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div className="space-y-1">
            <label className="text-[11px] font-bold uppercase text-slate-400">Target Charitable Recipient *</label>
            <select
              value={redistForm.recipient_name}
              onChange={(e) => setRedistForm({ ...redistForm, recipient_name: e.target.value })}
              className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
            >
              <option value="Second Harvest Regional Food Bank">Second Harvest Regional Food Bank (Family Kitchen Box)</option>
              <option value="St. Jude Community Kitchen">St. Jude Community Kitchen & Pantry</option>
              <option value="Silicon Valley Shelter Network">Silicon Valley Shelter Network</option>
              <option value="San Jose Youth Hope Mission">San Jose Youth Hope Mission</option>
            </select>
          </div>

          <div className="space-y-1">
            <label className="text-[11px] font-bold uppercase text-slate-400">Dispatch & Packing Notes</label>
            <textarea
              rows={2}
              value={redistForm.notes}
              onChange={(e) => setRedistForm({ ...redistForm, notes: e.target.value })}
              className="w-full bg-slate-900 border border-white/10 rounded-xl p-2.5 text-xs text-white focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div className="flex justify-end space-x-2 pt-3 border-t border-white/10">
            <Button variant="outline" size="sm" onClick={() => setShowRedistributeModal(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" type="submit" leftIcon={<HeartHandshake className="w-3.5 h-3.5" />}>
              Confirm Donation Allocation
            </Button>
          </div>
        </form>
      </Modal>

      {/* ============================================================= */}
      {/* MODAL 4: QC INSPECTION & DAMAGED PACKAGING REJECTION MODAL    */}
      {/* ============================================================= */}
      <Modal
        isOpen={showQcModal}
        onClose={() => setShowQcModal(false)}
        title={`Quality Inspection & Valorization: ${selectedBatchForQc?.batch_number || 'Batch'}`}
      >
        <form onSubmit={handleQcSubmit} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-[11px] font-bold uppercase text-slate-400">Quality Status *</label>
              <select
                value={qcForm.quality_status}
                onChange={(e) => setQcForm({ ...qcForm, quality_status: e.target.value as any })}
                className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-500"
              >
                <option value="PASSED">PASSED (Optimal)</option>
                <option value="UNDER_REVIEW">UNDER REVIEW (Holding)</option>
                <option value="DAMAGED_PACKAGING">DAMAGED PACKAGING (Defect)</option>
                <option value="REJECTED">REJECTED (Failed Standard)</option>
              </select>
            </div>

            <div className="space-y-1">
              <label className="text-[11px] font-bold uppercase text-slate-400">Packaging Integrity</label>
              <select
                value={qcForm.packaging_condition}
                onChange={(e) => setQcForm({ ...qcForm, packaging_condition: e.target.value })}
                className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-500"
              >
                <option value="INTACT">INTACT (Aseptic)</option>
                <option value="DAMAGED_PACKAGING">DAMAGED PACKAGING</option>
                <option value="SEAL_FAILURE">SEAL FAILURE</option>
                <option value="DEFECTIVE_LABEL">DEFECTIVE LABEL</option>
                <option value="DENTED_CONTAINER">DENTED CONTAINER</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-[11px] font-bold uppercase text-slate-400">Damaged Packaging Units</label>
              <input
                type="number"
                min={0}
                value={qcForm.damaged_packaging_units}
                onChange={(e) => setQcForm({ ...qcForm, damaged_packaging_units: Number(e.target.value), rejected_quantity: Number(e.target.value) })}
                className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-500"
              />
            </div>

            <div className="space-y-1">
              <label className="text-[11px] font-bold uppercase text-slate-400">Valorization Disposition Routing</label>
              <select
                value={qcForm.disposition_action}
                onChange={(e) => setQcForm({ ...qcForm, disposition_action: e.target.value })}
                className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-500"
              >
                <option value="ANIMAL_FEED_VALORIZATION">Livestock Feed Supplement (Animal Feed)</option>
                <option value="COMPOST_BIOGAS">Anaerobic Digest & Composting (Biogas)</option>
                <option value="RE_PROCESS">Thermal Re-processing / Re-pasteurize</option>
                <option value="HAZARDOUS_DISPOSAL">Certified Hazardous Disposal</option>
              </select>
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-[11px] font-bold uppercase text-slate-400">Rejection Reason</label>
            <input
              type="text"
              value={qcForm.rejection_reason}
              onChange={(e) => setQcForm({ ...qcForm, rejection_reason: e.target.value })}
              className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-500"
            />
          </div>

          <div className="flex justify-end space-x-2 pt-3 border-t border-white/10">
            <Button variant="outline" size="sm" onClick={() => setShowQcModal(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" type="submit">
              Save QC Station Decision
            </Button>
          </div>
        </form>
      </Modal>

      {/* ============================================================= */}
      {/* MODAL 5: CONFIGURABLE ALERT THRESHOLD RULES                   */}
      {/* ============================================================= */}
      <Modal
        isOpen={showThresholdModal}
        onClose={() => setShowThresholdModal(false)}
        title="Configurable Expiry Alert Threshold Rules"
      >
        <form onSubmit={handleThresholdSave} className="space-y-4">
          <div className="p-3.5 rounded-2xl bg-amber-950/20 border border-amber-500/30 text-xs text-amber-300 space-y-1">
            <div className="flex items-center space-x-1.5 font-bold">
              <Info className="w-4 h-4 text-amber-400" />
              <span>HACCP Calibration Notice:</span>
            </div>
            <p className="text-[11px] leading-relaxed text-slate-300">
              Thresholds are configured per product or category. Do not treat example periods (7d, 3d, 1d) as universal food-safety rules. Customize based on microbial susceptibility and thermal packaging type.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-[11px] font-bold uppercase text-slate-400">Rule Level</label>
              <select
                value={thresholdForm.target_type}
                onChange={(e) => setThresholdForm({ ...thresholdForm, target_type: e.target.value as any })}
                className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-500"
              >
                <option value="CATEGORY">Category Wide Rule</option>
                <option value="PRODUCT">Specific Product Override</option>
              </select>
            </div>

            <div className="space-y-1">
              <label className="text-[11px] font-bold uppercase text-slate-400">Target Name *</label>
              <input
                type="text"
                required
                value={thresholdForm.target_name}
                onChange={(e) => setThresholdForm({ ...thresholdForm, target_name: e.target.value })}
                placeholder="e.g. DAIRY, PRODUCE, Tomato Puree"
                className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div className="space-y-1">
              <label className="text-[11px] font-bold uppercase text-sky-400">Warning (Days)</label>
              <input
                type="number"
                step="0.5"
                min="0.1"
                required
                value={thresholdForm.warning_threshold_days}
                onChange={(e) => setThresholdForm({ ...thresholdForm, warning_threshold_days: Number(e.target.value) })}
                className="w-full bg-slate-900 border border-sky-500/30 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-sky-400"
              />
            </div>

            <div className="space-y-1">
              <label className="text-[11px] font-bold uppercase text-amber-400">Urgent (Days)</label>
              <input
                type="number"
                step="0.5"
                min="0.1"
                required
                value={thresholdForm.urgent_threshold_days}
                onChange={(e) => setThresholdForm({ ...thresholdForm, urgent_threshold_days: Number(e.target.value) })}
                className="w-full bg-slate-900 border border-amber-500/30 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-400"
              />
            </div>

            <div className="space-y-1">
              <label className="text-[11px] font-bold uppercase text-rose-400">Critical (Days)</label>
              <input
                type="number"
                step="0.5"
                min="0.1"
                required
                value={thresholdForm.critical_threshold_days}
                onChange={(e) => setThresholdForm({ ...thresholdForm, critical_threshold_days: Number(e.target.value) })}
                className="w-full bg-slate-900 border border-rose-500/30 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-rose-400"
              />
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-[11px] font-bold uppercase text-slate-400">Custom Safety Guidelines</label>
            <input
              type="text"
              value={thresholdForm.custom_safety_notes}
              onChange={(e) => setThresholdForm({ ...thresholdForm, custom_safety_notes: e.target.value })}
              placeholder="e.g. Pasteurized refrigerated dairy microbial growth rule"
              className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-500"
            />
          </div>

          {/* Current Rules List */}
          <div className="pt-2 border-t border-white/10 space-y-2">
            <div className="text-[11px] font-bold uppercase text-slate-400">Active Configured Rules:</div>
            <div className="space-y-1.5 max-h-36 overflow-y-auto pr-1">
              {thresholdRules.map(r => (
                <div key={r.id} className="p-2 rounded-xl bg-slate-900 border border-white/5 flex items-center justify-between text-xs">
                  <div>
                    <span className="font-bold text-white">{r.target_name}</span>
                    <span className="text-[10px] text-slate-400 ml-2">({r.target_type})</span>
                  </div>
                  <div className="font-mono text-[11px]">
                    <span className="text-sky-400">{r.warning_threshold_days}d</span> · <span className="text-amber-400">{r.urgent_threshold_days}d</span> · <span className="text-rose-400">{r.critical_threshold_days}d</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="flex justify-end space-x-2 pt-3 border-t border-white/10">
            <Button variant="outline" size="sm" onClick={() => setShowThresholdModal(false)}>
              Close
            </Button>
            <Button variant="primary" size="sm" type="submit">
              Save Rule Configuration
            </Button>
          </div>
        </form>
      </Modal>

    </div>
  );
};
