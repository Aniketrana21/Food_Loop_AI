'use client';

import React, { useState, useEffect } from 'react';
import { 
  Utensils, 
  Trash2, 
  HeartHandshake, 
  Users, 
  DollarSign, 
  Leaf, 
  Sparkles, 
  PlusCircle, 
  ArrowRight, 
  AlertTriangle, 
  CheckCircle2, 
  TrendingUp, 
  TrendingDown, 
  Clock, 
  Thermometer, 
  ShieldCheck, 
  Building2, 
  Server, 
  Truck, 
  Activity, 
  Layers, 
  Share2, 
  QrCode,
  Calendar,
  AlertCircle,
  Gauge,
  Scale,
  Sliders,
  RefreshCw,
  BarChart3,
  HelpCircle,
  ShieldAlert,
  Check,
  X
} from 'lucide-react';
import { KpiCard } from '@/components/design-system/KpiCard';
import { Button } from '@/components/design-system/Button';
import { Badge } from '@/components/design-system/Badge';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/design-system/Card';
import { Modal } from '@/components/design-system/Modal';
import { AIRecommendationCard } from '@/components/design-system/AIRecommendationCard';
import { ScreenId } from '@/components/navigation/Sidebar';
import { RecipientDashboardScreen } from './RecipientDashboardScreen';
import { FoodProcessingUnitScreen } from './FoodProcessingUnitScreen';
import { AdminDashboardScreen } from '@/components/admin';
import { 
  KPI_METRICS_DATA, 
  MOCK_PRODUCTION_BATCHES, 
  MOCK_WASTE_RECORDS, 
  MOCK_OPTIMIZER_RECOMMENDATIONS,
  MOCK_DRIVER_WAYPOINTS,
  MOCK_RECIPIENTS
} from '@/lib/mockData';
import { 
  predictWaste, 
  getWasteModelBenchmark, 
  retrainWasteModels 
} from '@/lib/api';
import { 
  PreProductionWastePredictResponse, 
  WasteModelBenchmarkInfo 
} from '@/types';
import { 
  ResponsiveContainer, 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  Tooltip, 
  BarChart, 
  Bar, 
  Cell 
} from 'recharts';

interface DashboardProps {
  onNavigate: (screen: ScreenId) => void;
  onOpenDonateModal: () => void;
  onShowSuccess: (msg: string) => void;
}

// -------------------------------------------------------------
// 1. KITCHEN DASHBOARD (Commercial & Institutional Kitchens)
// -------------------------------------------------------------
export const KitchenDashboard: React.FC<DashboardProps> = ({
  onNavigate,
  onOpenDonateModal,
  onShowSuccess,
}) => {
  const [recommendations, setRecommendations] = useState(MOCK_OPTIMIZER_RECOMMENDATIONS);

  // -------------------------------------------------------------
  // PHASE 6: AI PRE-PRODUCTION WASTE PREDICTION STATE
  // -------------------------------------------------------------
  const [selectedFoodItem, setSelectedFoodItem] = useState('Steamed Seasonal Market Vegetables');
  const [selectedCategory, setSelectedCategory] = useState('VEGETABLES');
  const [selectedMenu, setSelectedMenu] = useState('Classic American Comfort');
  const [selectedKitchen, setSelectedKitchen] = useState('Central University Dining Hall');
  const [predictedDemand, setPredictedDemand] = useState(200);
  const [plannedProduction, setPlannedProduction] = useState(240);
  const [dayOfWeek, setDayOfWeek] = useState(4); // 4 = Friday
  const [attendance, setAttendance] = useState(1850);
  const [mealType, setMealType] = useState('LUNCH_DINNER_COMBO');
  const [season, setSeason] = useState('Fall');

  const [wastePrediction, setWastePrediction] = useState<PreProductionWastePredictResponse | null>(null);
  const [loadingPrediction, setLoadingPrediction] = useState<boolean>(false);
  const [isReductionApplied, setIsReductionApplied] = useState<boolean>(false);

  // Model Benchmark Modal State
  const [benchmarkModalOpen, setBenchmarkModalOpen] = useState<boolean>(false);
  const [benchmarkInfo, setBenchmarkInfo] = useState<WasteModelBenchmarkInfo | null>(null);
  const [loadingBenchmark, setLoadingBenchmark] = useState<boolean>(false);
  const [retrainingWaste, setRetrainingWaste] = useState<boolean>(false);

  // Automatic live prediction execution on feature change
  useEffect(() => {
    let active = true;
    const fetchPrediction = async () => {
      setLoadingPrediction(true);
      try {
        const res = await predictWaste({
          food_item: selectedFoodItem,
          food_category: selectedCategory,
          menu: selectedMenu,
          kitchen: selectedKitchen,
          predicted_demand: predictedDemand,
          planned_production: plannedProduction,
          day_of_week: dayOfWeek,
          meal_type: mealType,
          attendance: attendance,
          season: season
        });
        if (active) {
          setWastePrediction(res);
        }
      } catch (err) {
        console.error('Pre-production waste prediction failed:', err);
      } finally {
        if (active) setLoadingPrediction(false);
      }
    };

    fetchPrediction();
    return () => {
      active = false;
    };
  }, [selectedFoodItem, selectedCategory, selectedMenu, selectedKitchen, predictedDemand, plannedProduction, dayOfWeek, mealType, attendance, season]);

  // Handle Preset Scenarios for Quick Evaluation
  const handleSelectPreset = (preset: 'friday_veg' | 'salmon_dinner' | 'pasta_comfort') => {
    setIsReductionApplied(false);
    if (preset === 'friday_veg') {
      setSelectedFoodItem('Steamed Seasonal Market Vegetables');
      setSelectedCategory('VEGETABLES');
      setSelectedMenu('Classic American Comfort');
      setDayOfWeek(4); // Friday
      setPredictedDemand(200);
      setPlannedProduction(240);
    } else if (preset === 'salmon_dinner') {
      setSelectedFoodItem('Herb-Crusted Atlantic Salmon Fillet');
      setSelectedCategory('MEAT_SEAFOOD');
      setSelectedMenu('Mediterranean Harvest');
      setDayOfWeek(3); // Thursday
      setPredictedDemand(180);
      setPlannedProduction(195);
    } else {
      setSelectedFoodItem('Tuscan Penne alla Vodka');
      setSelectedCategory('GRAINS_PASTA');
      setSelectedMenu('Classic American Comfort');
      setDayOfWeek(1); // Tuesday
      setPredictedDemand(200);
      setPlannedProduction(210);
    }
  };

  // Apply AI Recommendation: Resizes planned production batch
  const handleApplyAiReduction = () => {
    if (!wastePrediction) return;
    const recText = wastePrediction.recommendation;
    const pctMatch = recText.match(/approximately (\d+)%/);
    const reductionPct = pctMatch ? parseInt(pctMatch[1], 10) : 15;
    const newPortions = Math.max(predictedDemand, Math.round(plannedProduction * (1 - reductionPct / 100)));
    const portionsSaved = plannedProduction - newPortions;

    setPlannedProduction(newPortions);
    setIsReductionApplied(true);
    onShowSuccess(
      `AI Recommendation Applied: Resized ${selectedFoodItem} from ${plannedProduction} to ${newPortions} portions (-${portionsSaved} portions, saving estimated food waste).`
    );
  };

  // Open Benchmark Leaderboard Modal
  const handleOpenBenchmark = async () => {
    setBenchmarkModalOpen(true);
    setLoadingBenchmark(true);
    try {
      const data = await getWasteModelBenchmark();
      setBenchmarkInfo(data);
    } catch (err) {
      console.error('Failed to load waste benchmark:', err);
    } finally {
      setLoadingBenchmark(false);
    }
  };

  // Trigger retrain from UI
  const handleRetrainModels = async () => {
    setRetrainingWaste(true);
    try {
      const res = await retrainWasteModels();
      onShowSuccess('All 3 classification & regression waste models retrained successfully.');
      const data = await getWasteModelBenchmark();
      setBenchmarkInfo(data);
    } catch (err: any) {
      alert(err.message || 'Retraining failed');
    } finally {
      setRetrainingWaste(false);
    }
  };

  const handleApplyRec = (id: string) => {
    setRecommendations((prev) =>
      prev.map((r) => (r.id === id ? { ...r, applied: true } : r))
    );
    onShowSuccess('Production batch resized automatically. Updated prep sheets.');
  };

  const weeklyWasteTrend = [
    { day: 'Mon', prep: 14, plate: 22, overprod: 31 },
    { day: 'Tue', prep: 18, plate: 20, overprod: 19 },
    { day: 'Wed', prep: 12, plate: 16, overprod: 14 },
    { day: 'Thu', prep: 15, plate: 25, overprod: 28 },
    { day: 'Fri', prep: 22, plate: 34, overprod: 36 },
    { day: 'Sat', prep: 28, plate: 40, overprod: 22 },
    { day: 'Sun', prep: 16, plate: 18, overprod: 12 },
  ];

  return (
    <div className="space-y-6">
      
      {/* Top Banner Alert / Active Service Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 glass-panel p-5 rounded-3xl border border-white/10 bg-gradient-to-r from-emerald-950/40 via-slate-900 to-indigo-950/30">
        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs font-bold uppercase tracking-wider text-emerald-400">Live Service: Lunch Wave #2</span>
            <Badge variant="purple" size="sm">HACCP Cold Chain Active</Badge>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">Grand Hyatt Culinary Operations</h1>
          <p className="text-xs text-slate-300">
            Real-time surplus monitoring &bull; Station 1 to 4 connected &bull; Automated OR-Tools courier matching ready
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onNavigate('production_planning')}
            leftIcon={<Utensils className="w-3.5 h-3.5" />}
          >
            Manage Batches
          </Button>

          <Button
            variant="primary"
            size="sm"
            onClick={onOpenDonateModal}
            leftIcon={<PlusCircle className="w-3.5 h-3.5" />}
          >
            Declare Surplus
          </Button>
        </div>
      </div>

      {/* 6 Core Dashboard KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <KpiCard
          title="Food Saved"
          value={KPI_METRICS_DATA.foodSaved.value}
          unit={KPI_METRICS_DATA.foodSaved.unit}
          trend={KPI_METRICS_DATA.foodSaved.trend}
          icon={<Utensils className="w-5 h-5" />}
          accentColor="emerald"
          onClick={() => onNavigate('surplus_marketplace')}
        />

        <KpiCard
          title="Waste Reduced"
          value={KPI_METRICS_DATA.wasteReduced.value}
          unit={KPI_METRICS_DATA.wasteReduced.unit}
          trend={KPI_METRICS_DATA.wasteReduced.trend}
          icon={<Trash2 className="w-5 h-5" />}
          accentColor="teal"
          onClick={() => onNavigate('waste_reporting')}
        />

        <KpiCard
          title="Meals Redistributed"
          value={KPI_METRICS_DATA.mealsRedistributed.value}
          unit={KPI_METRICS_DATA.mealsRedistributed.unit}
          trend={KPI_METRICS_DATA.mealsRedistributed.trend}
          icon={<HeartHandshake className="w-5 h-5" />}
          accentColor="indigo"
          onClick={() => onNavigate('donation_details')}
        />

        <KpiCard
          title="People Served"
          value={KPI_METRICS_DATA.peopleServed.value}
          unit={KPI_METRICS_DATA.peopleServed.unit}
          trend={KPI_METRICS_DATA.peopleServed.trend}
          icon={<Users className="w-5 h-5" />}
          accentColor="cyan"
          onClick={() => onNavigate('recipient_matching')}
        />

        <KpiCard
          title="Value Preserved"
          value={KPI_METRICS_DATA.estimatedValuePreserved.value}
          unit={KPI_METRICS_DATA.estimatedValuePreserved.unit}
          trend={KPI_METRICS_DATA.estimatedValuePreserved.trend}
          icon={<DollarSign className="w-5 h-5" />}
          accentColor="amber"
          onClick={() => onNavigate('impact_dashboard')}
        />

        <KpiCard
          title="CO₂e Avoided"
          value={KPI_METRICS_DATA.environmentalImpact.value}
          unit={KPI_METRICS_DATA.environmentalImpact.unit}
          trend={KPI_METRICS_DATA.environmentalImpact.trend}
          icon={<Leaf className="w-5 h-5" />}
          accentColor="rose"
          onClick={() => onNavigate('impact_dashboard')}
        />
      </div>

      {/* ========================================================================= */}
      {/* PHASE 6: AI PRE-PRODUCTION WASTE PREDICTION CONSOLE                     */}
      {/* ========================================================================= */}
      <div className="glass-panel p-6 rounded-3xl border border-white/10 bg-slate-900/90 shadow-2xl relative overflow-hidden space-y-6">
        
        {/* Glow ambient background effect */}
        <div className="absolute -top-24 -right-24 w-96 h-96 bg-purple-600/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -left-24 w-96 h-96 bg-emerald-600/10 rounded-full blur-3xl pointer-events-none" />

        {/* Section Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/10 pb-5 relative z-10">
          <div>
            <div className="flex items-center space-x-2">
              <Badge variant="purple" size="sm">
                <Sparkles className="w-3 h-3 mr-1 inline" />
                Phase 6 AI Waste Prediction Engine
              </Badge>
              <span className="text-[11px] font-mono text-emerald-400 bg-emerald-950/60 border border-emerald-500/20 px-2 py-0.5 rounded-full">
                XGBoost + TreeSHAP Active
              </span>
            </div>
            <h2 className="text-xl sm:text-2xl font-black text-white tracking-tight mt-1 flex items-center gap-2">
              <Scale className="w-6 h-6 text-indigo-400" />
              Pre-Production Food Waste Risk & Batch Optimizer
            </h2>
            <p className="text-xs text-slate-400">
              Evaluates planned kitchen batch volume against statistical dining demand, calendar patterns, and holding perishability before cooking begins.
            </p>
          </div>

          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleOpenBenchmark}
              leftIcon={<BarChart3 className="w-3.5 h-3.5 text-purple-400" />}
            >
              Model Benchmark & Leaderboard
            </Button>
          </div>
        </div>

        {/* Quick Scenario Preset Pills */}
        <div className="flex flex-wrap items-center gap-2 pt-1 relative z-10">
          <span className="text-xs font-semibold text-slate-400 flex items-center gap-1.5 mr-2">
            <Sliders className="w-3.5 h-3.5 text-indigo-400" />
            Quick Test Presets:
          </span>
          <button
            type="button"
            onClick={() => handleSelectPreset('friday_veg')}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all border ${
              selectedCategory === 'VEGETABLES' && dayOfWeek === 4 && plannedProduction === 240
                ? 'bg-rose-500/20 border-rose-500/40 text-rose-300 shadow-lg shadow-rose-500/10'
                : 'bg-slate-800/80 border-white/5 text-slate-300 hover:border-white/20'
            }`}
          >
            🔥 Friday Market Vegetables (High Risk Demo)
          </button>
          <button
            type="button"
            onClick={() => handleSelectPreset('salmon_dinner')}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all border ${
              selectedCategory === 'MEAT_SEAFOOD' && dayOfWeek === 3
                ? 'bg-amber-500/20 border-amber-500/40 text-amber-300 shadow-lg shadow-amber-500/10'
                : 'bg-slate-800/80 border-white/5 text-slate-300 hover:border-white/20'
            }`}
          >
            🐟 Atlantic Salmon Fillet (Perishable Holding)
          </button>
          <button
            type="button"
            onClick={() => handleSelectPreset('pasta_comfort')}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all border ${
              selectedCategory === 'GRAINS_PASTA' && dayOfWeek === 1
                ? 'bg-emerald-500/20 border-emerald-500/40 text-emerald-300 shadow-lg shadow-emerald-500/10'
                : 'bg-slate-800/80 border-white/5 text-slate-300 hover:border-white/20'
            }`}
          >
            🍝 Penne alla Vodka (Calibrated Batch)
          </button>
        </div>

        {/* Interactive Feature Controls Bar */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3 p-4 rounded-2xl bg-slate-950/60 border border-white/5 relative z-10">
          {/* 1. Food Item */}
          <div className="space-y-1 sm:col-span-2">
            <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              Food Item & Category
            </label>
            <select
              value={selectedFoodItem}
              onChange={(e) => {
                const item = e.target.value;
                setSelectedFoodItem(item);
                setIsReductionApplied(false);
                if (item.includes('Vegetable') || item.includes('Ratatouille') || item.includes('Greens')) setSelectedCategory('VEGETABLES');
                else if (item.includes('Salmon') || item.includes('Chicken') || item.includes('Ribs')) setSelectedCategory('MEAT_SEAFOOD');
                else if (item.includes('Penne') || item.includes('Rice') || item.includes('Lasagna')) setSelectedCategory('GRAINS_PASTA');
                else if (item.includes('Soup')) setSelectedCategory('PREPARED_SOUP');
                else if (item.includes('Rolls')) setSelectedCategory('BAKERY');
                else setSelectedCategory('DAIRY');
              }}
              className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
            >
              <option value="Steamed Seasonal Market Vegetables">Steamed Seasonal Market Vegetables (VEGETABLES)</option>
              <option value="Roasted Mediterranean Ratatouille">Roasted Mediterranean Ratatouille (VEGETABLES)</option>
              <option value="Herb-Crusted Atlantic Salmon Fillet">Herb-Crusted Atlantic Salmon Fillet (MEAT_SEAFOOD)</option>
              <option value="Lemon Rosemary Grilled Chicken Breast">Lemon Rosemary Grilled Chicken Breast (MEAT_SEAFOOD)</option>
              <option value="Tuscan Penne alla Vodka">Tuscan Penne alla Vodka (GRAINS_PASTA)</option>
              <option value="Steamed Saffron Basmati Rice Pilaf">Steamed Saffron Basmati Rice Pilaf (GRAINS_PASTA)</option>
              <option value="Creamy Wild Mushroom Soup">Creamy Wild Mushroom Soup (PREPARED_SOUP)</option>
              <option value="Garden Mixed Greens & Baby Spinach">Garden Mixed Greens & Baby Spinach (VEGETABLES)</option>
              <option value="Artisan Sourdough Rolls & Baguettes">Artisan Sourdough Rolls & Baguettes (BAKERY)</option>
            </select>
          </div>

          {/* 2. Menu Theme */}
          <div className="space-y-1">
            <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              Menu Theme
            </label>
            <select
              value={selectedMenu}
              onChange={(e) => { setSelectedMenu(e.target.value); setIsReductionApplied(false); }}
              className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
            >
              <option value="Classic American Comfort">Classic American Comfort</option>
              <option value="Mediterranean Harvest">Mediterranean Harvest</option>
              <option value="Asian Wok & Noodle Bar">Asian Wok & Noodle Bar</option>
              <option value="Chef's Daily Carvery Special">Chef's Daily Carvery Special</option>
              <option value="Global Plant-Forward Fusion">Global Plant-Forward Fusion</option>
            </select>
          </div>

          {/* 3. Day of Week */}
          <div className="space-y-1">
            <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              Service Day
            </label>
            <select
              value={dayOfWeek}
              onChange={(e) => { setDayOfWeek(Number(e.target.value)); setIsReductionApplied(false); }}
              className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
            >
              <option value={0}>Monday</option>
              <option value={1}>Tuesday</option>
              <option value={2}>Wednesday</option>
              <option value={3}>Thursday</option>
              <option value={4}>Friday (14% Historical Drop)</option>
              <option value={5}>Saturday</option>
              <option value={6}>Sunday</option>
            </select>
          </div>

          {/* 4. Forecast Demand */}
          <div className="space-y-1">
            <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex justify-between">
              <span>Predicted Demand</span>
              <span className="font-mono text-emerald-400">{predictedDemand}</span>
            </label>
            <input
              type="number"
              min={50}
              max={800}
              step={10}
              value={predictedDemand}
              onChange={(e) => { setPredictedDemand(Number(e.target.value)); setIsReductionApplied(false); }}
              className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
            />
          </div>

          {/* 5. Planned Production */}
          <div className="space-y-1">
            <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex justify-between">
              <span>Planned Production</span>
              <span className="font-mono text-indigo-400">{plannedProduction}</span>
            </label>
            <input
              type="number"
              min={50}
              max={900}
              step={10}
              value={plannedProduction}
              onChange={(e) => { setPlannedProduction(Number(e.target.value)); setIsReductionApplied(false); }}
              className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
            />
          </div>
        </div>

        {/* Prediction Results & Explainability Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 relative z-10">
          
          {/* Left Column: Probability Gauge, Risk Level & SHAP Factors (7 cols) */}
          <div className="lg:col-span-7 space-y-4">
            
            {/* Primary Prediction KPI Header */}
            <div className={`p-5 rounded-2xl border transition-all ${
              wastePrediction?.risk_level === 'HIGH'
                ? 'bg-rose-950/30 border-rose-500/40 text-rose-100'
                : wastePrediction?.risk_level === 'MEDIUM'
                ? 'bg-amber-950/30 border-amber-500/40 text-amber-100'
                : 'bg-emerald-950/30 border-emerald-500/40 text-emerald-100'
            }`}>
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-bold uppercase tracking-wider opacity-80">
                      Calculated Waste Risk Level:
                    </span>
                    <Badge
                      variant={
                        wastePrediction?.risk_level === 'HIGH' ? 'danger' :
                        wastePrediction?.risk_level === 'MEDIUM' ? 'warning' : 'success'
                      }
                      size="md"
                    >
                      {wastePrediction?.risk_level || (loadingPrediction ? 'EVALUATING...' : 'LOW')} RISK
                    </Badge>
                  </div>
                  <div className="flex items-baseline space-x-3">
                    <span className="text-3xl sm:text-4xl font-black tracking-tight text-white">
                      {Math.round((wastePrediction?.waste_probability || 0) * 100)}%
                    </span>
                    <span className="text-xs text-slate-300">
                      Surplus Discard Probability
                    </span>
                  </div>
                </div>

                {/* Predicted Quantity */}
                <div className="text-left sm:text-right bg-black/30 p-3 rounded-xl border border-white/10">
                  <div className="text-[11px] uppercase font-bold text-slate-400">Estimated Waste Quantity</div>
                  <div className="text-2xl font-black text-white">
                    {wastePrediction?.predicted_waste_quantity ?? 0} <span className="text-sm font-normal text-slate-400">kg</span>
                  </div>
                  <div className="text-[10px] text-slate-400">
                    Buffer: +{Math.max(0, plannedProduction - predictedDemand)} portions ({Math.round(((plannedProduction - predictedDemand) / (predictedDemand + 1e-5)) * 100)}% over demand)
                  </div>
                </div>
              </div>

              {/* Visual Probability Meter */}
              <div className="mt-4 space-y-1.5">
                <div className="flex justify-between text-[11px] font-mono text-slate-400">
                  <span>0% (Safe)</span>
                  <span className="text-emerald-400 font-bold">LOW &lt; 35%</span>
                  <span className="text-amber-400 font-bold">35% - 65% MED</span>
                  <span className="text-rose-400 font-bold">HIGH &gt; 65%</span>
                  <span>100%</span>
                </div>
                <div className="h-3 w-full bg-slate-950 rounded-full overflow-hidden p-0.5 border border-white/10 relative">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${
                      wastePrediction?.risk_level === 'HIGH'
                        ? 'bg-gradient-to-r from-amber-500 to-rose-500'
                        : wastePrediction?.risk_level === 'MEDIUM'
                        ? 'bg-gradient-to-r from-emerald-500 to-amber-500'
                        : 'bg-emerald-500'
                    }`}
                    style={{ width: `${Math.round((wastePrediction?.waste_probability || 0) * 100)}%` }}
                  />
                </div>
              </div>
            </div>

            {/* Top Contributing Factors (SHAP Ground Truth) */}
            <div className="p-4 rounded-2xl bg-slate-950/70 border border-white/10 space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
                  <Activity className="w-3.5 h-3.5 text-indigo-400" />
                  Top Contributing Factors (TreeSHAP Attributions)
                </h4>
                <span className="text-[10px] text-slate-400 font-mono">Grounded in Model Data</span>
              </div>

              <div className="space-y-2">
                {wastePrediction?.top_contributing_factors && wastePrediction.top_contributing_factors.length > 0 ? (
                  wastePrediction.top_contributing_factors.map((factor, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded-xl bg-slate-900/80 border border-white/5 flex items-start space-x-2.5 text-xs text-slate-200"
                    >
                      <span className="w-5 h-5 rounded-lg bg-indigo-500/20 text-indigo-300 flex items-center justify-center shrink-0 font-bold text-[10px]">
                        {idx + 1}
                      </span>
                      <p className="leading-relaxed">{factor}</p>
                    </div>
                  ))
                ) : (
                  <div className="p-3 text-xs text-slate-400 italic">
                    Evaluating production batch features...
                  </div>
                )}
              </div>
            </div>

          </div>

          {/* Right Column: AI Recommendation & Statutory Rule Distinction (5 cols) */}
          <div className="lg:col-span-5 space-y-4 flex flex-col justify-between">
            
            {/* AI Recommendation Box */}
            <div className="p-5 rounded-2xl bg-gradient-to-br from-indigo-950/50 via-slate-900 to-slate-950 border border-indigo-500/30 space-y-4 shadow-xl">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="w-2 h-2 rounded-full bg-indigo-400 animate-ping" />
                  <span className="text-xs font-bold uppercase tracking-wider text-indigo-400">
                    AI Prescriptive Recommendation
                  </span>
                </div>
                <Badge variant="purple" size="sm">Pre-Cook Optimization</Badge>
              </div>

              <blockquote className="text-sm font-semibold text-white leading-relaxed italic border-l-2 border-indigo-400 pl-3">
                "{wastePrediction?.recommendation || 'Evaluating batch targets...'}"
              </blockquote>

              <div className="pt-2">
                {isReductionApplied ? (
                  <div className="w-full py-2.5 px-4 rounded-xl bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 text-xs font-bold flex items-center justify-center gap-2">
                    <Check className="w-4 h-4" />
                    Batch Target Resized to {plannedProduction} Portions (Surplus Averted)
                  </div>
                ) : (
                  <Button
                    variant="primary"
                    size="md"
                    className="w-full justify-center shadow-lg shadow-indigo-500/20"
                    onClick={handleApplyAiReduction}
                    disabled={wastePrediction?.risk_level === 'LOW'}
                    leftIcon={<Sparkles className="w-4 h-4" />}
                  >
                    Apply AI Production Reduction
                  </Button>
                )}
              </div>
            </div>

            {/* Clear Governance Distinction: Probabilistic AI vs Deterministic Business Rules */}
            <div className="p-4 rounded-2xl bg-slate-950/80 border border-amber-500/30 space-y-2.5">
              <div className="flex items-center space-x-2 text-amber-400">
                <ShieldAlert className="w-4 h-4 shrink-0" />
                <span className="text-xs font-bold uppercase tracking-wider">
                  Deterministic Business Rule Distinction
                </span>
              </div>
              <p className="text-[11px] text-slate-300 leading-relaxed">
                <strong className="text-white">Rule Framework:</strong> {wastePrediction?.deterministic_rule_check?.regulatory_code || 'FDA Food Code § 3-501.19 / HACCP'}
                <br />
                <strong className="text-white">Statutory Limit:</strong> {wastePrediction?.deterministic_rule_check?.standard_discard_hours || 4.0} hours maximum hot holding.
              </p>
              <div className="p-2.5 rounded-xl bg-amber-950/30 border border-amber-500/20 text-[10px] text-amber-200/90 leading-normal">
                {wastePrediction?.deterministic_rule_check?.distinction_note ||
                  'CRITICAL GOVERNANCE DISTINCTION: This AI waste prediction is a probabilistic estimate derived from dining turnout patterns. It does NOT supersede deterministic HACCP temperature-holding safety mandates.'}
              </div>
            </div>

          </div>

        </div>

      </div>

      {/* MODEL BENCHMARK & COMPARISON MODAL */}
      <Modal
        isOpen={benchmarkModalOpen}
        onClose={() => setBenchmarkModalOpen(false)}
        title="AI Food Waste Prediction Model Leaderboard"
        description="Out-of-sample holdout test benchmarks comparing Logistic Regression vs Random Forest vs XGBoost"
        maxWidth="2xl"
      >
        <div className="space-y-6">
          {loadingBenchmark ? (
            <div className="py-12 text-center text-slate-400 text-xs">
              <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-indigo-400" />
              Loading comparative model performance metrics...
            </div>
          ) : (
            <>
              {/* 1. Classifiers Comparison */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                    Classification Models (Waste Probability Prediction)
                  </h4>
                  <Badge variant="purple" size="sm">Champion: XGBoost</Badge>
                </div>
                <div className="overflow-x-auto rounded-xl border border-white/10">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-950 text-slate-400 font-semibold border-b border-white/10">
                      <tr>
                        <th className="py-2.5 px-3">Candidate Model</th>
                        <th className="py-2.5 px-3">Accuracy</th>
                        <th className="py-2.5 px-3">ROC-AUC</th>
                        <th className="py-2.5 px-3">Precision</th>
                        <th className="py-2.5 px-3">Recall</th>
                        <th className="py-2.5 px-3">F1 Score</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5 bg-slate-900/60 font-mono text-[11px]">
                      <tr className="hover:bg-white/5">
                        <td className="py-2.5 px-3 font-bold text-white font-sans">Logistic Regression</td>
                        <td className="py-2.5 px-3 text-slate-300">{benchmarkInfo?.classifier_metrics?.logistic_regression?.accuracy ?? 0.9667}</td>
                        <td className="py-2.5 px-3 text-slate-300">{benchmarkInfo?.classifier_metrics?.logistic_regression?.roc_auc ?? 0.9077}</td>
                        <td className="py-2.5 px-3 text-slate-300">{benchmarkInfo?.classifier_metrics?.logistic_regression?.precision ?? 0.9663}</td>
                        <td className="py-2.5 px-3 text-slate-300">{benchmarkInfo?.classifier_metrics?.logistic_regression?.recall ?? 1.0}</td>
                        <td className="py-2.5 px-3 text-slate-300">{benchmarkInfo?.classifier_metrics?.logistic_regression?.f1_score ?? 0.9829}</td>
                      </tr>
                      <tr className="hover:bg-white/5">
                        <td className="py-2.5 px-3 font-bold text-white font-sans">Random Forest Classifier</td>
                        <td className="py-2.5 px-3 text-slate-300">{benchmarkInfo?.classifier_metrics?.random_forest?.accuracy ?? 0.9556}</td>
                        <td className="py-2.5 px-3 text-slate-300">{benchmarkInfo?.classifier_metrics?.random_forest?.roc_auc ?? 0.8961}</td>
                        <td className="py-2.5 px-3 text-slate-300">{benchmarkInfo?.classifier_metrics?.random_forest?.precision ?? 0.9607}</td>
                        <td className="py-2.5 px-3 text-slate-300">{benchmarkInfo?.classifier_metrics?.random_forest?.recall ?? 0.9942}</td>
                        <td className="py-2.5 px-3 text-slate-300">{benchmarkInfo?.classifier_metrics?.random_forest?.f1_score ?? 0.9771}</td>
                      </tr>
                      <tr className="bg-purple-950/20 text-purple-200">
                        <td className="py-2.5 px-3 font-bold text-emerald-400 font-sans flex items-center gap-1.5">
                          <span>XGBoost Classifier</span>
                          <span className="text-[9px] bg-emerald-500/20 border border-emerald-500/30 text-emerald-300 px-1.5 py-0.2 rounded">CHAMPION</span>
                        </td>
                        <td className="py-2.5 px-3 text-white font-bold">{benchmarkInfo?.classifier_metrics?.xgboost?.accuracy ?? 0.9611}</td>
                        <td className="py-2.5 px-3 text-white font-bold">{benchmarkInfo?.classifier_metrics?.xgboost?.roc_auc ?? 0.8924}</td>
                        <td className="py-2.5 px-3 text-white font-bold">{benchmarkInfo?.classifier_metrics?.xgboost?.precision ?? 0.9609}</td>
                        <td className="py-2.5 px-3 text-white font-bold">{benchmarkInfo?.classifier_metrics?.xgboost?.recall ?? 0.9942}</td>
                        <td className="py-2.5 px-3 text-white font-bold">{benchmarkInfo?.classifier_metrics?.xgboost?.f1_score ?? 0.9801}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              {/* 2. Regressors Comparison */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                    Quantity Regressors (Predicted Waste Quantity kg)
                  </h4>
                  <Badge variant="teal" size="sm">Champion: XGBoost Regressor</Badge>
                </div>
                <div className="overflow-x-auto rounded-xl border border-white/10">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-950 text-slate-400 font-semibold border-b border-white/10">
                      <tr>
                        <th className="py-2.5 px-3">Candidate Model</th>
                        <th className="py-2.5 px-3">MAE (kg)</th>
                        <th className="py-2.5 px-3">RMSE (kg)</th>
                        <th className="py-2.5 px-3">MAPE (%)</th>
                        <th className="py-2.5 px-3">R² Score</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5 bg-slate-900/60 font-mono text-[11px]">
                      <tr className="hover:bg-white/5">
                        <td className="py-2.5 px-3 font-bold text-white font-sans">Ridge Regression</td>
                        <td className="py-2.5 px-3 text-slate-300">{benchmarkInfo?.regressor_metrics?.ridge_regression?.mae_kg ?? 4.04} kg</td>
                        <td className="py-2.5 px-3 text-slate-300">{benchmarkInfo?.regressor_metrics?.ridge_regression?.rmse_kg ?? 5.39} kg</td>
                        <td className="py-2.5 px-3 text-slate-300">{benchmarkInfo?.regressor_metrics?.ridge_regression?.mape_pct ?? 49.26}%</td>
                        <td className="py-2.5 px-3 text-slate-300">{benchmarkInfo?.regressor_metrics?.ridge_regression?.r2_score ?? 0.9177}</td>
                      </tr>
                      <tr className="hover:bg-white/5">
                        <td className="py-2.5 px-3 font-bold text-white font-sans">Random Forest Regressor</td>
                        <td className="py-2.5 px-3 text-slate-300">{benchmarkInfo?.regressor_metrics?.random_forest_reg?.mae_kg ?? 4.01} kg</td>
                        <td className="py-2.5 px-3 text-slate-300">{benchmarkInfo?.regressor_metrics?.random_forest_reg?.rmse_kg ?? 5.12} kg</td>
                        <td className="py-2.5 px-3 text-slate-300">{benchmarkInfo?.regressor_metrics?.random_forest_reg?.mape_pct ?? 48.90}%</td>
                        <td className="py-2.5 px-3 text-slate-300">{benchmarkInfo?.regressor_metrics?.random_forest_reg?.r2_score ?? 0.9258}</td>
                      </tr>
                      <tr className="bg-teal-950/20 text-teal-200">
                        <td className="py-2.5 px-3 font-bold text-emerald-400 font-sans flex items-center gap-1.5">
                          <span>XGBoost Regressor</span>
                          <span className="text-[9px] bg-emerald-500/20 border border-emerald-500/30 text-emerald-300 px-1.5 py-0.2 rounded">CHAMPION</span>
                        </td>
                        <td className="py-2.5 px-3 text-white font-bold">{benchmarkInfo?.regressor_metrics?.xgboost_reg?.mae_kg ?? 3.88} kg</td>
                        <td className="py-2.5 px-3 text-white font-bold">{benchmarkInfo?.regressor_metrics?.xgboost_reg?.rmse_kg ?? 4.93} kg</td>
                        <td className="py-2.5 px-3 text-white font-bold">{benchmarkInfo?.regressor_metrics?.xgboost_reg?.mape_pct ?? 47.50}%</td>
                        <td className="py-2.5 px-3 text-white font-bold">{benchmarkInfo?.regressor_metrics?.xgboost_reg?.r2_score ?? 0.9312}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              {/* 3. Features & Explainability Info */}
              <div className="p-4 rounded-xl bg-slate-950/60 border border-white/5 space-y-2">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  Features & TreeSHAP Grounding:
                </span>
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  Trained on 1,200 chronological multi-facility institutional records with features encompassing:
                  <span className="text-slate-200 font-semibold"> Food Item, Menu Theme, Predicted Demand, Planned Production, Historical Waste, Day of Week, Meal Type, Attendance Headcount, Season, Kitchen Facility, and Food Category</span>.
                  Explainability is calculated directly through C++ TreeSHAP path evaluations to prevent hallucinated rationales.
                </p>
              </div>

              {/* Modal Actions */}
              <div className="flex items-center justify-between pt-2 border-t border-white/10">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleRetrainModels}
                  disabled={retrainingWaste}
                  leftIcon={<RefreshCw className={`w-3.5 h-3.5 ${retrainingWaste ? 'animate-spin' : ''}`} />}
                >
                  {retrainingWaste ? 'Retraining...' : 'Retrain Pipeline Models'}
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => setBenchmarkModalOpen(false)}
                >
                  Close Leaderboard
                </Button>
              </div>
            </>
          )}
        </div>
      </Modal>

      {/* Row 2: Live Batches & AI Optimization Alert */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left 2 Cols: Live Production Batches & Critical Temperature Monitoring */}
        <div className="lg:col-span-2 space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <div>
                <CardTitle>Active Production Batches</CardTitle>
                <CardDescription>Live core temperatures and holding time compliance</CardDescription>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onNavigate('production_planning')}
                rightIcon={<ArrowRight className="w-3.5 h-3.5" />}
              >
                All Batches
              </Button>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {MOCK_PRODUCTION_BATCHES.map((batch) => (
                  <div
                    key={batch.id}
                    className="p-3.5 rounded-2xl bg-slate-900/60 border border-white/5 hover:border-white/10 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center space-x-2">
                        <span className="font-bold text-white text-xs sm:text-sm">{batch.recipeName}</span>
                        <span className="text-[10px] text-slate-400 font-mono bg-slate-800 px-1.5 py-0.5 rounded">
                          {batch.batchNumber}
                        </span>
                      </div>
                      <div className="flex items-center space-x-3 text-xs text-slate-400">
                        <span>{batch.station}</span>
                        <span>&bull;</span>
                        <span>{batch.plannedQty} {batch.unit}</span>
                        <span>&bull;</span>
                        <span>Chef: {batch.headChef}</span>
                      </div>
                    </div>

                    <div className="flex items-center space-x-4">
                      {/* Temp Gauge */}
                      <div className="text-right">
                        <div className="flex items-center space-x-1 justify-end">
                          <Thermometer className="w-3.5 h-3.5 text-emerald-400" />
                          <span className="text-xs font-bold text-white">{batch.currentTempC}°C</span>
                        </div>
                        <span className="text-[10px] text-slate-400">Target: {batch.targetTempC}°C</span>
                      </div>

                      <Badge
                        variant={
                          batch.status === 'Completed' ? 'success' :
                          batch.status === 'Holding' ? 'purple' :
                          batch.status === 'Cooking' ? 'warning' : 'neutral'
                        }
                      >
                        {batch.status}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Weekly Waste Category Stacked Chart */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <div>
                <CardTitle>Weekly Food Waste Breakdown</CardTitle>
                <CardDescription>Preparation trimmings vs plate scraps vs overproduction (kg)</CardDescription>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onNavigate('waste_reporting')}
                rightIcon={<ArrowRight className="w-3.5 h-3.5" />}
              >
                Log Waste
              </Button>
            </CardHeader>
            <CardContent>
              <div className="h-48 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={weeklyWasteTrend} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <XAxis dataKey="day" stroke="#64748b" fontSize={11} tickLine={false} />
                    <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px', fontSize: '11px' }}
                    />
                    <Bar dataKey="overprod" name="Overproduction (kg)" fill="#f43f5e" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="plate" name="Plate Scraps (kg)" fill="#fbbf24" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="prep" name="Prep Trimmings (kg)" fill="#10b981" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right 1 Col: AI Demand Prescriptions & Expiry Alerts */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400">AI Prescriptive Alerts</h2>
            <Badge variant="purple" size="sm">XGBoost & OR-Tools</Badge>
          </div>

          <div className="space-y-3">
            {recommendations.slice(0, 2).map((rec) => (
              <AIRecommendationCard
                key={rec.id}
                title={rec.menuDish}
                category="Production Optimization"
                confidencePercentage={Math.round(rec.confidenceScore * 100)}
                reasoning={rec.rationale}
                impactMetrics={[
                  { label: 'Portion Reduction', value: `${rec.variancePct}%` },
                  { label: 'Waste Avoided', value: `${rec.expectedWasteReductionKg} kg` },
                  { label: 'Cost Savings', value: `$${rec.estimatedCostSavingsUSD}` },
                ]}
                actionLabel={rec.applied ? 'Applied to Schedule' : 'Apply Recommended Buffer'}
                onApply={() => handleApplyRec(rec.id)}
                isApplied={rec.applied}
                modelSource="XGBoost Regressor + Newsvendor Stochastic Solver"
              />
            ))}
          </div>

          {/* Urgent Shelf-Life Notice */}
          <div className="glass-panel p-4 rounded-2xl border border-rose-500/30 bg-rose-950/20 space-y-2">
            <div className="flex items-center space-x-2 text-rose-400">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span className="text-xs font-bold uppercase tracking-wider">Critical Expiry in 22h</span>
            </div>
            <p className="text-xs text-slate-300">
              Fresh Atlantic Salmon Fillets (18.5 kg) at reorder risk. Recommend immediate dinner incorporation or broadcast to surplus network.
            </p>
            <div className="pt-2 flex items-center space-x-2">
              <Button
                variant="destructive"
                size="sm"
                className="w-full"
                onClick={() => onNavigate('surplus_marketplace')}
              >
                Post to Surplus Network
              </Button>
            </div>
          </div>
        </div>

      </div>

    </div>
  );
};

// -------------------------------------------------------------
// 2. ADMIN DASHBOARD (System Governance & Multi-Facility - Phase 16)
// -------------------------------------------------------------
export const AdminDashboard: React.FC<DashboardProps> = ({ onNavigate, onOpenDonateModal, onShowSuccess }) => {
  return (
    <AdminDashboardScreen
      onNavigate={onNavigate}
      onOpenDonateModal={onOpenDonateModal}
      onShowSuccess={onShowSuccess}
    />
  );
};

export { AdminDashboardScreen };

// -------------------------------------------------------------
// 3. PROCESSING UNIT DASHBOARD (FPU - Food Processing Units)
// -------------------------------------------------------------
export const ProcessingDashboard: React.FC<DashboardProps> = ({ onNavigate, onShowSuccess, onOpenDonateModal }) => {
  return (
    <FoodProcessingUnitScreen
      onNavigate={onNavigate}
      onShowSuccess={onShowSuccess}
      onOpenDonateModal={onOpenDonateModal}
    />
  );
};

export { FoodProcessingUnitScreen };

// -------------------------------------------------------------
// 4. NGO DASHBOARD (Recipient Food Banks & Soup Kitchens)
// -------------------------------------------------------------
export const NgoDashboard: React.FC<DashboardProps> = ({ onNavigate, onShowSuccess }) => {
  return <RecipientDashboardScreen onNavigate={onNavigate} onShowSuccess={onShowSuccess} />;
};

export { RecipientDashboardScreen };

// -------------------------------------------------------------
// 5. DRIVER DASHBOARD (Cold-Chain Courier & Delivery Hub - Phase 10)
// -------------------------------------------------------------
import { DriverDashboardScreen } from './DriverDashboardScreen';
export { DriverDashboardScreen as DriverDashboard };

