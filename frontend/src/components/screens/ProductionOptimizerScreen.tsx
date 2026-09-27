'use client';

import React, { useState, useEffect, useTransition } from 'react';
import { 
  Sliders, 
  Sparkles, 
  TrendingUp, 
  AlertTriangle, 
  CheckCircle2, 
  ShieldAlert, 
  ShieldCheck, 
  Layers, 
  DollarSign, 
  Trash2, 
  Scale, 
  RefreshCw, 
  ChevronRight, 
  ArrowRight, 
  Flame, 
  ChefHat, 
  Clock, 
  HelpCircle,
  FileCheck,
  Zap,
  Info,
  Calendar,
  Building2,
  Package
} from 'lucide-react';
import { Button } from '@/components/design-system/Button';
import { Badge } from '@/components/design-system/Badge';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/design-system/Card';
import { AIRecommendationCard } from '@/components/design-system/AIRecommendationCard';
import { ConfirmDialog } from '@/components/design-system/ConfirmDialog';
import { ScreenId } from '@/components/navigation/Sidebar';
import { 
  ProductionOptimizeRequest, 
  ProductionOptimizeResponse, 
  WhatIfSimulationRequest, 
  WhatIfSimulationResponse 
} from '@/types';
import { optimizeProduction, simulateWhatIf } from '@/lib/api';
import { 
  ResponsiveContainer, 
  AreaChart, 
  Area, 
  LineChart, 
  Line, 
  BarChart,
  Bar,
  XAxis, 
  YAxis, 
  Tooltip, 
  CartesianGrid, 
  Legend 
} from 'recharts';

interface ProductionOptimizerProps {
  onNavigate?: (screen: ScreenId) => void;
  onOpenDonateModal?: () => void;
  onShowSuccess: (msg: string) => void;
}

// Preset scenarios for the What-If Simulator
const SIMULATOR_PRESETS = [
  {
    id: 'normal',
    label: 'Balanced Baseline',
    icon: '🥗',
    desc: 'Regular Tuesday lunch cycle with healthy attendance and standard prep',
    attendance: 1850,
    menu: 'VEGETARIAN',
    dish: 'Herb Roasted Seasonal Vegetables & Quinoa',
    category: 'VEGETABLES',
    production: 240,
    inventory: 25,
    foodCost: 3.20,
    capacity: 320,
    ingredients: 350,
    minDemand: 160,
  },
  {
    id: 'surge',
    label: 'High Turnout Event',
    icon: '🎓',
    desc: 'Campus orientation symposium with 35% attendance surge',
    attendance: 2750,
    menu: 'HIGH_PROTEIN',
    dish: 'Grilled Lemon-Herb Chicken Breast',
    category: 'MEAT_POULTRY',
    production: 320,
    inventory: 15,
    foodCost: 4.80,
    capacity: 400,
    ingredients: 450,
    minDemand: 280,
  },
  {
    id: 'rainy',
    label: 'Rainy Slow Friday',
    icon: '🌧️',
    desc: 'Heavy rain reducing campus footfall by 30% — high overproduction risk',
    attendance: 1100,
    menu: 'COMFORT',
    dish: 'Hearty Braised Beef & Vegetable Stew',
    category: 'MEAT_POULTRY',
    production: 260,
    inventory: 40,
    foodCost: 5.10,
    capacity: 300,
    ingredients: 350,
    minDemand: 120,
  },
  {
    id: 'infeasible',
    label: 'Supply Bottleneck (Test Infeasibility)',
    icon: '⚠️',
    desc: 'Strict service SLA of 220 portions while raw ingredients cap out at 130 portions',
    attendance: 2100,
    menu: 'SEAFOOD',
    dish: 'Pan-Seared Pacific Salmon Fillet',
    category: 'SEAFOOD',
    production: 180,
    inventory: 10,
    foodCost: 7.50,
    capacity: 120, // Lower than required demand!
    ingredients: 130, // Insufficient!
    minDemand: 220, // Forces infeasibility!
  },
];

// Active Kitchen Prep line items
interface PrepLineItem {
  id: string;
  dishName: string;
  category: string;
  station: string;
  chef: string;
  plannedPortions: number;
  inventoryOnHand: number;
  demandForecast: number;
  recommendedPortions: number;
  expectedWasteSavedKg: number;
  costSavingsUSD: number;
  shortageRiskPct: number;
  applied: boolean;
  status: 'PENDING' | 'OPTIMIZED' | 'DISPATCHED';
}

const INITIAL_PREP_LINE: PrepLineItem[] = [
  {
    id: 'prep-1',
    dishName: 'Herb Roasted Seasonal Vegetables',
    category: 'VEGETABLES',
    station: 'Station 1 (Convection)',
    chef: 'Chef Marcus',
    plannedPortions: 260,
    inventoryOnHand: 35,
    demandForecast: 215,
    recommendedPortions: 185,
    expectedWasteSavedKg: 14.4,
    costSavingsUSD: 240.0,
    shortageRiskPct: 3.2,
    applied: false,
    status: 'PENDING',
  },
  {
    id: 'prep-2',
    dishName: 'Braised Lemon Thyme Chicken',
    category: 'MEAT_POULTRY',
    station: 'Station 2 (Rotisserie)',
    chef: 'Chef Elena',
    plannedPortions: 340,
    inventoryOnHand: 20,
    demandForecast: 310,
    recommendedPortions: 295,
    expectedWasteSavedKg: 8.6,
    costSavingsUSD: 216.0,
    shortageRiskPct: 4.8,
    applied: false,
    status: 'PENDING',
  },
  {
    id: 'prep-3',
    dishName: 'Mediterranean Quinoa Pilaf',
    category: 'GRAINS',
    station: 'Station 3 (Steamers)',
    chef: 'Chef Jamal',
    plannedPortions: 190,
    inventoryOnHand: 15,
    demandForecast: 175,
    recommendedPortions: 165,
    expectedWasteSavedKg: 5.2,
    costSavingsUSD: 72.5,
    shortageRiskPct: 2.1,
    applied: false,
    status: 'PENDING',
  },
];

export const ProductionOptimizerScreen: React.FC<ProductionOptimizerProps> = ({ 
  onNavigate, 
  onOpenDonateModal, 
  onShowSuccess 
}) => {
  // Navigation tabs
  const [activeTab, setActiveTab] = useState<'simulator' | 'custom_solver' | 'prep_sheet'>('simulator');

  // What-If Simulator Inputs
  const [attendance, setAttendance] = useState<number>(1850);
  const [menuTheme, setMenuTheme] = useState<string>('VEGETARIAN');
  const [selectedDish, setSelectedDish] = useState<string>('Herb Roasted Seasonal Vegetables & Quinoa');
  const [foodCategory, setFoodCategory] = useState<string>('VEGETABLES');
  const [plannedProduction, setPlannedProduction] = useState<number>(240);
  const [inventoryOnHand, setInventoryOnHand] = useState<number>(25);
  const [foodCost, setFoodCost] = useState<number>(3.20);
  const [kitchenCapacity, setKitchenCapacity] = useState<number>(320);
  const [ingredientSupply, setIngredientSupply] = useState<number>(350);
  const [minDemandRequirement, setMinDemandRequirement] = useState<number>(160);
  const [inventoryAgeHours, setInventoryAgeHours] = useState<number>(1.5);

  // Simulation Results & Loading State
  const [isSimulating, setIsSimulating] = useState<boolean>(false);
  const [simulationResult, setSimulationResult] = useState<WhatIfSimulationResponse | null>(null);

  // Custom Solver State
  const [solverDemandForecast, setSolverDemandForecast] = useState<number>(240);
  const [solverCiLow, setSolverCiLow] = useState<number>(210);
  const [solverCiHigh, setSolverCiHigh] = useState<number>(275);
  const [solverInventory, setSolverInventory] = useState<number>(30);
  const [solverIngredients, setSolverIngredients] = useState<number>(300);
  const [solverCapacity, setSolverCapacity] = useState<number>(280);
  const [solverMaxCapacity, setSolverMaxCapacity] = useState<number>(350);
  const [solverHistoricalWaste, setSolverHistoricalWaste] = useState<number>(8.5);
  const [solverFoodCost, setSolverFoodCost] = useState<number>(3.80);
  const [solverMinRequiredDemand, setSolverMinRequiredDemand] = useState<number>(180);
  const [solverInventoryAge, setSolverInventoryAge] = useState<number>(2.0);
  const [isSolvingCustom, setIsSolvingCustom] = useState<boolean>(false);
  const [customSolveResult, setCustomSolveResult] = useState<ProductionOptimizeResponse | null>(null);

  // Active Kitchen Prep Line State
  const [prepLine, setPrepLine] = useState<PrepLineItem[]>(INITIAL_PREP_LINE);
  const [confirmCommitAllOpen, setConfirmCommitAllOpen] = useState<boolean>(false);

  // Trigger real-time What-If simulation on input changes
  const runSimulation = async () => {
    setIsSimulating(true);
    try {
      const payload: WhatIfSimulationRequest = {
        attendance,
        menu: menuTheme,
        production: plannedProduction,
        inventory: inventoryOnHand,
        dish_name: selectedDish,
        food_category: foodCategory,
        food_cost: foodCost,
        kitchen_capacity: kitchenCapacity,
        ingredient_availability: ingredientSupply,
        minimum_required_demand: minDemandRequirement,
        inventory_age_hours: inventoryAgeHours,
      };
      const result = await simulateWhatIf(payload);
      setSimulationResult(result);
    } catch (err) {
      console.error('Simulation error:', err);
    } finally {
      setIsSimulating(false);
    }
  };

  // Run on mount or when key slider values change
  useEffect(() => {
    const timer = setTimeout(() => {
      runSimulation();
    }, 180); // Debounce slider events
    return () => clearTimeout(timer);
  }, [
    attendance, 
    plannedProduction, 
    inventoryOnHand, 
    foodCost, 
    kitchenCapacity, 
    ingredientSupply, 
    minDemandRequirement, 
    inventoryAgeHours, 
    menuTheme, 
    selectedDish
  ]);

  // Load a preset scenario into the What-If Simulator
  const handleApplyPreset = (presetId: string) => {
    const preset = SIMULATOR_PRESETS.find((p) => p.id === presetId);
    if (!preset) return;
    setAttendance(preset.attendance);
    setMenuTheme(preset.menu);
    setSelectedDish(preset.dish);
    setFoodCategory(preset.category);
    setPlannedProduction(preset.production);
    setInventoryOnHand(preset.inventory);
    setFoodCost(preset.foodCost);
    setKitchenCapacity(preset.capacity);
    setIngredientSupply(preset.ingredients);
    setMinDemandRequirement(preset.minDemand);
  };

  // Run custom Google OR-Tools optimization
  const handleRunCustomOptimizer = async () => {
    setIsSolvingCustom(true);
    try {
      const payload: ProductionOptimizeRequest = {
        dish_name: 'Custom Batch Allocation',
        food_category: 'GENERAL',
        demand_forecast: solverDemandForecast,
        confidence_interval: {
          lower: solverCiLow,
          upper: solverCiHigh,
          low: solverCiLow,
          high: solverCiHigh,
          confidence_level: 0.95,
        },
        inventory: solverInventory,
        inventory_age_hours: solverInventoryAge,
        ingredient_availability: solverIngredients,
        kitchen_capacity: solverCapacity,
        maximum_production_capacity: solverMaxCapacity,
        historical_waste: solverHistoricalWaste,
        food_cost: solverFoodCost,
        minimum_required_demand: solverMinRequiredDemand,
      };
      const res = await optimizeProduction(payload);
      setCustomSolveResult(res);
      if (res.feasible) {
        onShowSuccess(`OR-Tools SCIP solved optimal batch: ${res.recommended_production} portions.`);
      } else {
        onShowSuccess(`Solver safely diagnosed conflicting constraints without generating invalid output.`);
      }
    } catch (err: any) {
      console.error('Custom optimizer error:', err);
    } finally {
      setIsSolvingCustom(false);
    }
  };

  // Apply single dish optimization to Prep Sheet
  const handleApplySinglePrep = (id: string) => {
    setPrepLine((prev) =>
      prev.map((item) =>
        item.id === id ? { ...item, applied: true, status: 'OPTIMIZED' } : item
      )
    );
    onShowSuccess('Dish production quantity locked and committed to prep sheet.');
  };

  // Apply all optimizations
  const handleApplyAllPrep = () => {
    setPrepLine((prev) =>
      prev.map((item) => ({ ...item, applied: true, status: 'OPTIMIZED' }))
    );
    setConfirmCommitAllOpen(false);
    onShowSuccess('All 3 batch preparation lines updated with OR-Tools optimal targets.');
  };

  // Infeasibility check helper
  const isInfeasible = simulationResult?.optimization_result?.feasible === false;
  const infeasibilityDetails = simulationResult?.optimization_result?.infeasibility_details;

  return (
    <div className="space-y-6 pb-12">
      {/* Top Header Card */}
      <div className="glass-panel p-6 rounded-3xl border border-white/10 bg-slate-900/90 relative overflow-hidden shadow-2xl">
        <div className="absolute top-0 right-0 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl pointer-events-none -mr-20 -mt-20" />
        <div className="absolute bottom-0 left-1/3 w-80 h-80 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none -mb-20" />

        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-5">
          <div>
            <div className="flex flex-wrap items-center gap-2 mb-2">
              <Badge variant="purple" size="sm" className="gap-1 px-3 py-1">
                <Sparkles className="w-3 h-3" /> Google OR-Tools SCIP MILP
              </Badge>
              <Badge variant="info" size="sm">
                Asymmetric Loss Newsvendor
              </Badge>
              <Badge variant="emerald" size="sm">
                HACCP FDA Code § 3-501.19
              </Badge>
              <Badge variant="neutral" size="sm">
                Integer Guarantees
              </Badge>
            </div>
            <h1 className="text-3xl font-black text-white tracking-tight flex items-center gap-3">
              Production Batch Optimizer & What-If Simulator
            </h1>
            <p className="text-sm text-slate-400 mt-1 max-w-3xl leading-relaxed">
              Determines mathematically optimal production quantities minimizing the joint sum of{' '}
              <strong className="text-slate-200">food waste</strong>,{' '}
              <strong className="text-slate-200">shortage risk</strong>, and{' '}
              <strong className="text-slate-200">production cost</strong> under strict kitchen capacity, ingredient availability, and food safety constraints.
            </p>
          </div>

          <div className="flex items-center gap-3 self-start lg:self-auto">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                runSimulation();
                onShowSuccess('Simulation refreshed with current telemetry.');
              }}
              leftIcon={<RefreshCw className={`w-3.5 h-3.5 ${isSimulating ? 'animate-spin' : ''}`} />}
            >
              Refresh Telemetry
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={() => {
                setActiveTab('prep_sheet');
                setConfirmCommitAllOpen(true);
              }}
              leftIcon={<FileCheck className="w-3.5 h-3.5" />}
            >
              Commit Prep Sheet
            </Button>
          </div>
        </div>

        {/* View Mode Tabs */}
        <div className="flex items-center space-x-2 mt-6 border-b border-white/10 pb-1">
          <button
            onClick={() => setActiveTab('simulator')}
            className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all ${
              activeTab === 'simulator'
                ? 'bg-purple-600 text-white shadow-lg shadow-purple-600/30'
                : 'text-slate-400 hover:text-white hover:bg-white/5'
            }`}
          >
            <Sliders className="w-3.5 h-3.5" />
            <span>⚡ Interactive What-If Simulator</span>
          </button>

          <button
            onClick={() => setActiveTab('custom_solver')}
            className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all ${
              activeTab === 'custom_solver'
                ? 'bg-purple-600 text-white shadow-lg shadow-purple-600/30'
                : 'text-slate-400 hover:text-white hover:bg-white/5'
            }`}
          >
            <Scale className="w-3.5 h-3.5" />
            <span>⚙️ 9-Parameter OR-Tools Engine</span>
          </button>

          <button
            onClick={() => setActiveTab('prep_sheet')}
            className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all ${
              activeTab === 'prep_sheet'
                ? 'bg-purple-600 text-white shadow-lg shadow-purple-600/30'
                : 'text-slate-400 hover:text-white hover:bg-white/5'
            }`}
          >
            <ChefHat className="w-3.5 h-3.5" />
            <span>📋 Kitchen Prep Line Schedule</span>
            <span className="ml-1.5 px-1.5 py-0.2 bg-white/20 rounded-full text-[10px]">
              {prepLine.filter((p) => !p.applied).length} pending
            </span>
          </button>
        </div>
      </div>

      {/* ========================================================= */}
      {/* TAB 1: INTERACTIVE WHAT-IF SIMULATOR                     */}
      {/* ========================================================= */}
      {activeTab === 'simulator' && (
        <div className="space-y-6">
          {/* Quick Scenario Preset Chips */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 p-4 glass-panel rounded-2xl border border-white/5 bg-slate-900/60">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <Zap className="w-3.5 h-3.5 text-amber-400" /> Quick Simulation Presets:
            </span>
            <div className="flex flex-wrap gap-2">
              {SIMULATOR_PRESETS.map((preset) => (
                <button
                  key={preset.id}
                  onClick={() => handleApplyPreset(preset.id)}
                  className="px-3 py-1.5 rounded-xl text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-white/10 hover:border-purple-500/40 transition-all flex items-center gap-1.5 group"
                >
                  <span>{preset.icon}</span>
                  <span className="group-hover:text-purple-300">{preset.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Infeasibility Alert Banner if Triggered */}
          {isInfeasible && (
            <div className="p-5 rounded-2xl border-2 border-rose-500/40 bg-rose-950/40 backdrop-blur-md text-white shadow-xl animate-pulse">
              <div className="flex items-start gap-4">
                <div className="p-2.5 bg-rose-500/20 rounded-xl text-rose-400 mt-0.5">
                  <ShieldAlert className="w-6 h-6" />
                </div>
                <div className="space-y-2 flex-1">
                  <div className="flex items-center justify-between">
                    <h3 className="text-base font-bold text-rose-300 flex items-center gap-2">
                      <span>CRITICAL INFEASIBILITY DETECTED: Physical Limits Conflict with Service Policy</span>
                      <Badge variant="danger" size="sm">Solver Safeguard Active</Badge>
                    </h3>
                    <span className="text-xs text-rose-200 font-mono">Status: INFEASIBLE_CONSTRAINED</span>
                  </div>
                  <p className="text-sm text-rose-100/90 leading-relaxed">
                    The optimizer verified that <strong className="text-white">no mathematically valid production batch exists</strong> that can satisfy the guaranteed minimum service requirement ({minDemandRequirement} portions) within available kitchen station capacity ({kitchenCapacity} portions) and raw ingredient inventory ({ingredientSupply} portions).
                  </p>
                  
                  {infeasibilityDetails?.root_cause_conflicts && (
                    <div className="p-3 bg-black/40 rounded-xl border border-rose-500/20 text-xs font-mono text-rose-200 space-y-1">
                      <div className="font-bold text-rose-300 uppercase tracking-wider text-[10px]">Root Cause Conflict:</div>
                      {infeasibilityDetails.root_cause_conflicts.map((conflict, idx) => (
                        <div key={idx} className="flex items-start gap-2">
                          <span className="text-rose-400">•</span>
                          <span>{conflict}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {infeasibilityDetails?.actionable_bottleneck_resolutions && (
                    <div className="mt-2 text-xs text-slate-300">
                      <span className="font-semibold text-white">Recommended Actionable Steps to Restore Feasibility:</span>
                      <ul className="list-disc list-inside mt-1 space-y-1 text-slate-300 text-[11px]">
                        {infeasibilityDetails.actionable_bottleneck_resolutions.map((step, idx) => (
                          <li key={idx}>{step}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <div className="pt-1 text-[11px] text-amber-300/90 italic flex items-center gap-1.5">
                    <Info className="w-3.5 h-3.5" />
                    Strict Operational Policy: FoodLoop AI will never silently emit an unconstrained or false production quantity.
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Main 2-Column Grid: Sliders on Left, Immediate Results on Right */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left Column: Interactive Sliders & Inputs (5 Cols) */}
            <div className="lg:col-span-5 space-y-5">
              <Card className="border-white/10 bg-slate-900/80">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base flex items-center gap-2">
                      <Sliders className="w-4 h-4 text-purple-400" />
                      Simulator Parameters
                    </CardTitle>
                    <span className="text-[11px] text-slate-400">Live Reaction</span>
                  </div>
                  <CardDescription className="text-xs">
                    Adjust variables below to instantly evaluate demand impact, optimal batch size, and waste delta.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-5">
                  {/* Parameter 1: Expected Attendance */}
                  <div className="space-y-2 p-3.5 rounded-xl bg-slate-800/50 border border-white/5">
                    <div className="flex justify-between items-center text-xs">
                      <label className="font-semibold text-slate-200 flex items-center gap-1.5">
                        <Building2 className="w-3.5 h-3.5 text-sky-400" /> Expected Attendance
                      </label>
                      <span className="font-mono font-bold text-sky-400 text-sm">{attendance.toLocaleString()} diners</span>
                    </div>
                    <input
                      type="range"
                      min={500}
                      max={3500}
                      step={50}
                      value={attendance}
                      onChange={(e) => setAttendance(Number(e.target.value))}
                      className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-sky-400"
                    />
                    <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                      <span>500 (Off-Peak)</span>
                      <span>1,850 (Normal)</span>
                      <span>3,500 (Gala Surge)</span>
                    </div>
                  </div>

                  {/* Parameter 2: Menu Dish & Category */}
                  <div className="space-y-2 p-3.5 rounded-xl bg-slate-800/50 border border-white/5">
                    <div className="flex justify-between items-center text-xs">
                      <label className="font-semibold text-slate-200 flex items-center gap-1.5">
                        <ChefHat className="w-3.5 h-3.5 text-purple-400" /> Menu Selection
                      </label>
                      <Badge variant="purple" size="sm">{menuTheme}</Badge>
                    </div>
                    <select
                      value={selectedDish}
                      onChange={(e) => {
                        const val = e.target.value;
                        setSelectedDish(val);
                        if (val.includes('Vegetables')) {
                          setFoodCategory('VEGETABLES');
                          setFoodCost(3.20);
                        } else if (val.includes('Chicken')) {
                          setFoodCategory('MEAT_POULTRY');
                          setFoodCost(4.80);
                        } else if (val.includes('Salmon')) {
                          setFoodCategory('SEAFOOD');
                          setFoodCost(7.50);
                        } else if (val.includes('Quinoa')) {
                          setFoodCategory('GRAINS');
                          setFoodCost(2.90);
                        } else {
                          setFoodCategory('COMFORT');
                          setFoodCost(4.20);
                        }
                      }}
                      className="w-full bg-slate-900 border border-white/15 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-purple-500"
                    >
                      <option value="Herb Roasted Seasonal Vegetables & Quinoa">Herb Roasted Seasonal Vegetables & Quinoa ($3.20)</option>
                      <option value="Grilled Lemon-Herb Chicken Breast">Grilled Lemon-Herb Chicken Breast ($4.80)</option>
                      <option value="Pan-Seared Pacific Salmon Fillet">Pan-Seared Pacific Salmon Fillet ($7.50)</option>
                      <option value="Mediterranean Quinoa Pilaf">Mediterranean Quinoa Pilaf ($2.90)</option>
                      <option value="Hearty Braised Beef & Vegetable Stew">Hearty Braised Beef & Vegetable Stew ($5.10)</option>
                    </select>
                  </div>

                  {/* Parameter 3: Planned Production Portions */}
                  <div className="space-y-2 p-3.5 rounded-xl bg-slate-800/50 border border-white/5">
                    <div className="flex justify-between items-center text-xs">
                      <label className="font-semibold text-slate-200 flex items-center gap-1.5">
                        <Flame className="w-3.5 h-3.5 text-amber-400" /> Planned Production (Chef Baseline)
                      </label>
                      <span className="font-mono font-bold text-amber-400 text-sm">{plannedProduction} portions</span>
                    </div>
                    <input
                      type="range"
                      min={50}
                      max={500}
                      step={5}
                      value={plannedProduction}
                      onChange={(e) => setPlannedProduction(Number(e.target.value))}
                      className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-amber-400"
                    />
                    <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                      <span>50 portions</span>
                      <span>250 portions</span>
                      <span>500 portions</span>
                    </div>
                  </div>

                  {/* Parameter 4: On-Hand Inventory & HACCP Food Safety */}
                  <div className="space-y-2 p-3.5 rounded-xl bg-slate-800/50 border border-white/5">
                    <div className="flex justify-between items-center text-xs">
                      <label className="font-semibold text-slate-200 flex items-center gap-1.5">
                        <Package className="w-3.5 h-3.5 text-emerald-400" /> On-Hand Inventory & Holding Age
                      </label>
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold text-emerald-400 text-sm">{inventoryOnHand} portions</span>
                        <span className="text-[10px] text-slate-400 font-mono">({inventoryAgeHours}h old)</span>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <div className="text-[10px] text-slate-400 mb-1">Cold Hold Stock:</div>
                        <input
                          type="range"
                          min={0}
                          max={100}
                          step={5}
                          value={inventoryOnHand}
                          onChange={(e) => setInventoryOnHand(Number(e.target.value))}
                          className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-emerald-400"
                        />
                      </div>
                      <div>
                        <div className="text-[10px] text-slate-400 mb-1">Holding Age (Hours):</div>
                        <input
                          type="range"
                          min={0.5}
                          max={5.0}
                          step={0.5}
                          value={inventoryAgeHours}
                          onChange={(e) => setInventoryAgeHours(Number(e.target.value))}
                          className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-teal-400"
                        />
                      </div>
                    </div>
                    {/* HACCP Compliance Indicator */}
                    <div className="flex items-center justify-between pt-1">
                      {inventoryAgeHours <= 3.0 ? (
                        <div className="flex items-center gap-1.5 text-[10px] text-emerald-400 font-medium">
                          <ShieldCheck className="w-3.5 h-3.5" /> HACCP Safe: Stock fully offsets production need.
                        </div>
                      ) : inventoryAgeHours < 4.0 ? (
                        <div className="flex items-center gap-1.5 text-[10px] text-amber-400 font-medium">
                          <AlertTriangle className="w-3.5 h-3.5" /> Approaching 4-Hour Discard Threshold.
                        </div>
                      ) : (
                        <div className="flex items-center gap-1.5 text-[10px] text-rose-400 font-medium">
                          <ShieldAlert className="w-3.5 h-3.5" /> Expired (&gt;4.0h): Zero inventory credit allowed!
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Parameter 5: Physical Constraints (Kitchen & Ingredients) */}
                  <div className="space-y-3 p-3.5 rounded-xl bg-slate-800/50 border border-white/5">
                    <div className="text-xs font-semibold text-slate-200 flex items-center justify-between">
                      <span className="flex items-center gap-1.5">
                        <Scale className="w-3.5 h-3.5 text-cyan-400" /> Physical Kitchen & Supply Ceilings
                      </span>
                      <span className="text-[10px] text-slate-400 font-mono">Bound Limits</span>
                    </div>

                    <div className="grid grid-cols-3 gap-2 text-center">
                      <div className="p-2 rounded-lg bg-slate-900 border border-white/5">
                        <div className="text-[9px] uppercase tracking-wider text-slate-400">Kitchen Cap</div>
                        <input
                          type="number"
                          value={kitchenCapacity}
                          onChange={(e) => setKitchenCapacity(Number(e.target.value))}
                          className="w-full bg-transparent text-center font-mono font-bold text-white text-xs mt-1 border-b border-white/20 focus:outline-none"
                        />
                      </div>
                      <div className="p-2 rounded-lg bg-slate-900 border border-white/5">
                        <div className="text-[9px] uppercase tracking-wider text-slate-400">Raw Ingredients</div>
                        <input
                          type="number"
                          value={ingredientSupply}
                          onChange={(e) => setIngredientSupply(Number(e.target.value))}
                          className="w-full bg-transparent text-center font-mono font-bold text-white text-xs mt-1 border-b border-white/20 focus:outline-none"
                        />
                      </div>
                      <div className="p-2 rounded-lg bg-slate-900 border border-white/5">
                        <div className="text-[9px] uppercase tracking-wider text-slate-400">Min Demand SLA</div>
                        <input
                          type="number"
                          value={minDemandRequirement}
                          onChange={(e) => setMinDemandRequirement(Number(e.target.value))}
                          className="w-full bg-transparent text-center font-mono font-bold text-white text-xs mt-1 border-b border-white/20 focus:outline-none"
                        />
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Right Column: Immediate Live Simulation Outcomes (7 Cols) */}
            <div className="lg:col-span-7 space-y-5">
              {/* 4 KPI Outcome Cards */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {/* 1. Expected Demand */}
                <div className="glass-panel p-3.5 rounded-2xl border border-white/10 bg-slate-900/80 flex flex-col justify-between">
                  <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 flex items-center justify-between">
                    <span>Expected Demand</span>
                    <TrendingUp className="w-3.5 h-3.5 text-sky-400" />
                  </div>
                  <div className="mt-2">
                    <div className="text-2xl font-black text-white font-mono">
                      {simulationResult?.expected_demand ?? Math.round(attendance * 0.22)}
                    </div>
                    <span className="text-[10px] text-sky-400">portions</span>
                  </div>
                  <div className="mt-1 text-[10px] text-slate-400">
                    Turnout factor: 22%
                  </div>
                </div>

                {/* 2. Recommended Production */}
                <div className="glass-panel p-3.5 rounded-2xl border border-purple-500/30 bg-purple-950/20 flex flex-col justify-between shadow-lg shadow-purple-500/5">
                  <div className="text-[10px] font-bold uppercase tracking-wider text-purple-300 flex items-center justify-between">
                    <span>AI Optimal Batch</span>
                    <Sparkles className="w-3.5 h-3.5 text-purple-400" />
                  </div>
                  <div className="mt-2">
                    <div className="text-2xl font-black text-purple-300 font-mono">
                      {simulationResult?.recommended_production ?? 0}
                    </div>
                    <span className="text-[10px] text-purple-400">portions to cook</span>
                  </div>
                  <div className="mt-1 text-[10px] text-slate-400">
                    Delta: {(simulationResult?.recommended_production ?? 0) - plannedProduction > 0 ? '+' : ''}
                    {(simulationResult?.recommended_production ?? 0) - plannedProduction} vs chef
                  </div>
                </div>

                {/* 3. Predicted Waste */}
                <div className="glass-panel p-3.5 rounded-2xl border border-white/10 bg-slate-900/80 flex flex-col justify-between">
                  <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 flex items-center justify-between">
                    <span>Predicted Waste</span>
                    <Trash2 className="w-3.5 h-3.5 text-emerald-400" />
                  </div>
                  <div className="mt-2">
                    <div className="text-2xl font-black text-emerald-400 font-mono">
                      {simulationResult?.predicted_waste_kg ?? 0}
                    </div>
                    <span className="text-[10px] text-emerald-300">kg expected surplus</span>
                  </div>
                  <div className="mt-1 text-[10px] text-emerald-400 font-medium">
                    {simulationResult?.comparison_vs_planned?.waste_saved_kg ?? 0} kg saved!
                  </div>
                </div>

                {/* 4. Estimated Total Cost */}
                <div className="glass-panel p-3.5 rounded-2xl border border-white/10 bg-slate-900/80 flex flex-col justify-between">
                  <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 flex items-center justify-between">
                    <span>Estimated Cost</span>
                    <DollarSign className="w-3.5 h-3.5 text-amber-400" />
                  </div>
                  <div className="mt-2">
                    <div className="text-2xl font-black text-amber-300 font-mono">
                      ${Math.round(simulationResult?.estimated_cost?.total_expected_cost_usd ?? 0)}
                    </div>
                    <span className="text-[10px] text-amber-400">joint objective</span>
                  </div>
                  <div className="mt-1 text-[10px] text-emerald-400 font-medium">
                    ${Math.round(simulationResult?.comparison_vs_planned?.cost_saved_usd ?? 0)} saved vs plan
                  </div>
                </div>
              </div>

              {/* Head-to-Head Comparison Card: Chef Plan vs OR-Tools Optimal */}
              <div className="p-4 rounded-2xl border border-white/10 bg-slate-900/80 space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
                    <Scale className="w-3.5 h-3.5 text-purple-400" />
                    Head-to-Head: Chef Baseline vs OR-Tools Recommended
                  </h4>
                  <Badge variant={simulationResult?.comparison_vs_planned?.is_optimizer_better ? 'success' : 'neutral'} size="sm">
                    {simulationResult?.comparison_vs_planned?.is_optimizer_better ? 'AI Prevents Overproduction' : 'Calibrated'}
                  </Badge>
                </div>

                <div className="grid grid-cols-3 gap-3 text-center">
                  <div className="p-3 rounded-xl bg-slate-800/40 border border-white/5">
                    <div className="text-[10px] text-slate-400">Portions Prepared</div>
                    <div className="mt-1 text-sm font-mono font-bold text-white flex items-center justify-center gap-2">
                      <span className="text-slate-400 line-through">{plannedProduction}</span>
                      <ArrowRight className="w-3 h-3 text-purple-400" />
                      <span className="text-purple-300">{simulationResult?.recommended_production ?? 0}</span>
                    </div>
                    <div className="text-[10px] text-slate-400 mt-0.5">
                      + {inventoryOnHand} in stock
                    </div>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-800/40 border border-white/5">
                    <div className="text-[10px] text-slate-400">Waste Generated</div>
                    <div className="mt-1 text-sm font-mono font-bold text-white flex items-center justify-center gap-2">
                      <span className="text-rose-400">{simulationResult?.comparison_vs_planned?.planned_waste_kg ?? 0} kg</span>
                      <ArrowRight className="w-3 h-3 text-emerald-400" />
                      <span className="text-emerald-400">{simulationResult?.predicted_waste_kg ?? 0} kg</span>
                    </div>
                    <div className="text-[10px] text-emerald-300 mt-0.5 font-bold">
                      -{simulationResult?.comparison_vs_planned?.waste_saved_kg ?? 0} kg avoided
                    </div>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-800/40 border border-white/5">
                    <div className="text-[10px] text-slate-400">Net Financial Impact</div>
                    <div className="mt-1 text-sm font-mono font-bold text-white flex items-center justify-center gap-2">
                      <span className="text-slate-400">${Math.round(simulationResult?.comparison_vs_planned?.planned_cost_usd ?? 0)}</span>
                      <ArrowRight className="w-3 h-3 text-emerald-400" />
                      <span className="text-emerald-300">${Math.round(simulationResult?.estimated_cost?.total_expected_cost_usd ?? 0)}</span>
                    </div>
                    <div className="text-[10px] text-emerald-400 mt-0.5 font-bold">
                      +${Math.round(simulationResult?.comparison_vs_planned?.cost_saved_usd ?? 0)} net savings
                    </div>
                  </div>
                </div>

                {/* Asymmetric Cost Penalty Breakdown Bar */}
                <div className="pt-2">
                  <div className="flex justify-between items-center text-[10px] text-slate-400 mb-1">
                    <span>Joint Cost Breakdown (Production + Waste + Stockout Risk):</span>
                    <span className="font-mono text-slate-300">
                      Raw: ${Math.round(simulationResult?.estimated_cost?.production_cost_usd ?? 0)} | 
                      Waste Penalty: ${Math.round(simulationResult?.estimated_cost?.expected_waste_cost_usd ?? 0)} | 
                      Shortage Risk: ${Math.round(simulationResult?.estimated_cost?.expected_shortage_cost_usd ?? 0)}
                    </span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden flex">
                    <div 
                      className="bg-sky-500 h-full" 
                      style={{ 
                        width: `${Math.min(100, Math.max(10, ((simulationResult?.estimated_cost?.production_cost_usd ?? 1) / Math.max(1, simulationResult?.estimated_cost?.total_expected_cost_usd ?? 1)) * 100))}%` 
                      }} 
                      title="Raw Food Cost"
                    />
                    <div 
                      className="bg-emerald-500 h-full" 
                      style={{ 
                        width: `${Math.min(100, Math.max(5, ((simulationResult?.estimated_cost?.expected_waste_cost_usd ?? 1) / Math.max(1, simulationResult?.estimated_cost?.total_expected_cost_usd ?? 1)) * 100))}%` 
                      }} 
                      title="Waste Disposal Penalty ($1.25x)"
                    />
                    <div 
                      className="bg-rose-500 h-full" 
                      style={{ 
                        width: `${Math.min(100, Math.max(5, ((simulationResult?.estimated_cost?.expected_shortage_cost_usd ?? 1) / Math.max(1, simulationResult?.estimated_cost?.total_expected_cost_usd ?? 1)) * 100))}%` 
                      }} 
                      title="Shortage Risk Penalty ($3.20x)"
                    />
                  </div>
                  <div className="flex justify-between text-[9px] text-slate-400 mt-1">
                    <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-sky-500 inline-block"/> Production Cost ($1.0x)</span>
                    <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-500 inline-block"/> Disposal Penalty ($1.25x)</span>
                    <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-rose-500 inline-block"/> Shortage Risk ($3.20x)</span>
                  </div>
                </div>
              </div>

              {/* Sensitivity Analysis Curve Chart across attendance variations */}
              <div className="p-4 rounded-2xl border border-white/10 bg-slate-900/80 space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
                      <TrendingUp className="w-3.5 h-3.5 text-sky-400" />
                      Attendance Sensitivity Curve (-20% to +20%)
                    </h4>
                    <p className="text-[11px] text-slate-400 mt-0.5">
                      Dynamic response of demand, recommended production, and predicted surplus across turnout swings.
                    </p>
                  </div>
                  <Badge variant="cyan" size="sm">Stochastic Scenarios</Badge>
                </div>

                <div className="h-44 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart
                      data={simulationResult?.sensitivity_curve ?? []}
                      margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
                    >
                      <defs>
                        <linearGradient id="colorDemand" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.4}/>
                          <stop offset="95%" stopColor="#38bdf8" stopOpacity={0}/>
                        </linearGradient>
                        <linearGradient id="colorProd" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#c084fc" stopOpacity={0.4}/>
                          <stop offset="95%" stopColor="#c084fc" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.4} />
                      <XAxis dataKey="scenario" stroke="#94a3b8" fontSize={10} tickLine={false} />
                      <YAxis stroke="#94a3b8" fontSize={10} tickLine={false} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#0f172a',
                          border: '1px solid rgba(255,255,255,0.1)',
                          borderRadius: '12px',
                          fontSize: '11px',
                        }}
                      />
                      <Area
                        type="monotone"
                        dataKey="demand"
                        name="Expected Demand"
                        stroke="#38bdf8"
                        strokeWidth={2}
                        fillOpacity={1}
                        fill="url(#colorDemand)"
                      />
                      <Area
                        type="monotone"
                        dataKey="recommended_production"
                        name="Optimal Production"
                        stroke="#c084fc"
                        strokeWidth={2}
                        fillOpacity={1}
                        fill="url(#colorProd)"
                      />
                      <Line
                        type="monotone"
                        dataKey="waste_portions"
                        name="Expected Surplus"
                        stroke="#10b981"
                        strokeWidth={1.5}
                        dot={{ r: 3, fill: '#10b981' }}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Mathematical Rationale & Optimizer Reasoning */}
              <div className="p-4 rounded-2xl border border-white/10 bg-slate-900/60 space-y-2">
                <div className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-purple-400" />
                  Optimizer Reasoning & Decision Rationale
                </div>
                <div className="text-xs text-slate-300 space-y-1.5 leading-relaxed">
                  {simulationResult?.optimization_result?.reasoning?.map((reason, idx) => (
                    <div key={idx} className="flex items-start gap-2">
                      <span className="text-purple-400 font-bold">•</span>
                      <span>{reason}</span>
                    </div>
                  )) ?? (
                    <p className="text-slate-400 italic">Adjusting parameters recalculates OR-Tools SCIP solver rationale.</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================= */}
      {/* TAB 2: 9-PARAMETER CUSTOM OR-TOOLS ENGINE                 */}
      {/* ========================================================= */}
      {activeTab === 'custom_solver' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Form Inputs (6 Cols) */}
            <div className="lg:col-span-6 space-y-4">
              <Card className="border-white/10 bg-slate-900/80">
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2">
                    <Scale className="w-4 h-4 text-purple-400" />
                    9-Parameter MILP Formulation Inputs
                  </CardTitle>
                  <CardDescription className="text-xs">
                    Directly configure the formal Google OR-Tools Newsvendor loss model parameters.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Row 1: Demand & CI */}
                  <div className="grid grid-cols-3 gap-3">
                    <div>
                      <label className="text-[11px] font-semibold text-slate-300 block mb-1">
                        1. Demand Forecast
                      </label>
                      <input
                        type="number"
                        value={solverDemandForecast}
                        onChange={(e) => setSolverDemandForecast(Number(e.target.value))}
                        className="w-full bg-slate-800 border border-white/10 rounded-xl px-3 py-1.5 text-xs text-white focus:outline-none focus:border-purple-500 font-mono"
                      />
                    </div>
                    <div>
                      <label className="text-[11px] font-semibold text-slate-300 block mb-1">
                        2a. CI Low (95%)
                      </label>
                      <input
                        type="number"
                        value={solverCiLow}
                        onChange={(e) => setSolverCiLow(Number(e.target.value))}
                        className="w-full bg-slate-800 border border-white/10 rounded-xl px-3 py-1.5 text-xs text-white focus:outline-none focus:border-purple-500 font-mono"
                      />
                    </div>
                    <div>
                      <label className="text-[11px] font-semibold text-slate-300 block mb-1">
                        2b. CI High (95%)
                      </label>
                      <input
                        type="number"
                        value={solverCiHigh}
                        onChange={(e) => setSolverCiHigh(Number(e.target.value))}
                        className="w-full bg-slate-800 border border-white/10 rounded-xl px-3 py-1.5 text-xs text-white focus:outline-none focus:border-purple-500 font-mono"
                      />
                    </div>
                  </div>

                  {/* Row 2: Inventory & Holding Age */}
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-[11px] font-semibold text-slate-300 block mb-1">
                        3. Usable Inventory (Portions)
                      </label>
                      <input
                        type="number"
                        value={solverInventory}
                        onChange={(e) => setSolverInventory(Number(e.target.value))}
                        className="w-full bg-slate-800 border border-white/10 rounded-xl px-3 py-1.5 text-xs text-white focus:outline-none focus:border-purple-500 font-mono"
                      />
                    </div>
                    <div>
                      <label className="text-[11px] font-semibold text-slate-300 block mb-1">
                        Holding Age (HACCP Hours)
                      </label>
                      <input
                        type="number"
                        step="0.5"
                        value={solverInventoryAge}
                        onChange={(e) => setSolverInventoryAge(Number(e.target.value))}
                        className="w-full bg-slate-800 border border-white/10 rounded-xl px-3 py-1.5 text-xs text-white focus:outline-none focus:border-purple-500 font-mono"
                      />
                    </div>
                  </div>

                  {/* Row 3: Ingredients & Kitchen Capacity */}
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-[11px] font-semibold text-slate-300 block mb-1">
                        4. Ingredient Availability Limit
                      </label>
                      <input
                        type="number"
                        value={solverIngredients}
                        onChange={(e) => setSolverIngredients(Number(e.target.value))}
                        className="w-full bg-slate-800 border border-white/10 rounded-xl px-3 py-1.5 text-xs text-white focus:outline-none focus:border-purple-500 font-mono"
                      />
                    </div>
                    <div>
                      <label className="text-[11px] font-semibold text-slate-300 block mb-1">
                        5. Kitchen Station Capacity
                      </label>
                      <input
                        type="number"
                        value={solverCapacity}
                        onChange={(e) => setSolverCapacity(Number(e.target.value))}
                        className="w-full bg-slate-800 border border-white/10 rounded-xl px-3 py-1.5 text-xs text-white focus:outline-none focus:border-purple-500 font-mono"
                      />
                    </div>
                  </div>

                  {/* Row 4: Historical Waste & Food Cost */}
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-[11px] font-semibold text-slate-300 block mb-1">
                        6. Historical Waste Rate (%)
                      </label>
                      <input
                        type="number"
                        step="0.1"
                        value={solverHistoricalWaste}
                        onChange={(e) => setSolverHistoricalWaste(Number(e.target.value))}
                        className="w-full bg-slate-800 border border-white/10 rounded-xl px-3 py-1.5 text-xs text-white focus:outline-none focus:border-purple-500 font-mono"
                      />
                    </div>
                    <div>
                      <label className="text-[11px] font-semibold text-slate-300 block mb-1">
                        7. Unit Food Cost ($/portion)
                      </label>
                      <input
                        type="number"
                        step="0.1"
                        value={solverFoodCost}
                        onChange={(e) => setSolverFoodCost(Number(e.target.value))}
                        className="w-full bg-slate-800 border border-white/10 rounded-xl px-3 py-1.5 text-xs text-white focus:outline-none focus:border-purple-500 font-mono"
                      />
                    </div>
                  </div>

                  {/* Row 5: Minimum Required Demand & Max Capacity */}
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-[11px] font-semibold text-slate-300 block mb-1">
                        8. Minimum Required Demand (SLA)
                      </label>
                      <input
                        type="number"
                        value={solverMinRequiredDemand}
                        onChange={(e) => setSolverMinRequiredDemand(Number(e.target.value))}
                        className="w-full bg-slate-800 border border-white/10 rounded-xl px-3 py-1.5 text-xs text-white focus:outline-none focus:border-purple-500 font-mono"
                      />
                    </div>
                    <div>
                      <label className="text-[11px] font-semibold text-slate-300 block mb-1">
                        9. Max Facility Capacity
                      </label>
                      <input
                        type="number"
                        value={solverMaxCapacity}
                        onChange={(e) => setSolverMaxCapacity(Number(e.target.value))}
                        className="w-full bg-slate-800 border border-white/10 rounded-xl px-3 py-1.5 text-xs text-white focus:outline-none focus:border-purple-500 font-mono"
                      />
                    </div>
                  </div>

                  <Button
                    variant="primary"
                    fullWidth
                    onClick={handleRunCustomOptimizer}
                    isLoading={isSolvingCustom}
                    leftIcon={<Sparkles className="w-4 h-4" />}
                  >
                    Solve Optimal Batch (POST /api/v1/production/optimize)
                  </Button>
                </CardContent>
              </Card>
            </div>

            {/* Results & Solver Telemetry (6 Cols) */}
            <div className="lg:col-span-6 space-y-4">
              {customSolveResult ? (
                <Card className={`border ${customSolveResult.feasible ? 'border-purple-500/30' : 'border-rose-500/40'} bg-slate-900/90`}>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-base flex items-center gap-2">
                        {customSolveResult.feasible ? (
                          <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                        ) : (
                          <AlertTriangle className="w-5 h-5 text-rose-400" />
                        )}
                        OR-Tools Solver Output
                      </CardTitle>
                      <Badge variant={customSolveResult.feasible ? 'purple' : 'danger'} size="sm">
                        {customSolveResult.status}
                      </Badge>
                    </div>
                    <CardDescription className="text-xs font-mono">
                      Engine: {customSolveResult.solver}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* Primary Output Numbers */}
                    <div className="grid grid-cols-2 gap-3 text-center">
                      <div className="p-3 rounded-xl bg-purple-950/30 border border-purple-500/20">
                        <div className="text-[10px] uppercase tracking-wider text-purple-300">Recommended Production</div>
                        <div className="text-3xl font-black text-purple-300 font-mono mt-1">
                          {customSolveResult.recommended_production}
                        </div>
                        <span className="text-[10px] text-slate-400">portions to cook</span>
                      </div>
                      <div className="p-3 rounded-xl bg-slate-800/40 border border-white/5">
                        <div className="text-[10px] uppercase tracking-wider text-slate-400">Total Available Portions</div>
                        <div className="text-3xl font-black text-white font-mono mt-1">
                          {customSolveResult.total_available_portions}
                        </div>
                        <span className="text-[10px] text-slate-400">including usable inventory</span>
                      </div>
                    </div>

                    <div className="grid grid-cols-3 gap-2 text-center">
                      <div className="p-2.5 rounded-lg bg-slate-800/30 border border-white/5">
                        <div className="text-[9px] uppercase tracking-wider text-slate-400">Expected Surplus</div>
                        <div className="text-base font-bold text-emerald-400 font-mono mt-0.5">
                          {customSolveResult.expected_surplus} portions
                        </div>
                        <span className="text-[9px] text-slate-400">({customSolveResult.estimated_waste_kg} kg)</span>
                      </div>
                      <div className="p-2.5 rounded-lg bg-slate-800/30 border border-white/5">
                        <div className="text-[9px] uppercase tracking-wider text-slate-400">Shortage Risk</div>
                        <div className="text-base font-bold text-sky-400 font-mono mt-0.5">
                          {customSolveResult.expected_shortage_risk}%
                        </div>
                        <span className="text-[9px] text-slate-400">under peak scenario</span>
                      </div>
                      <div className="p-2.5 rounded-lg bg-slate-800/30 border border-white/5">
                        <div className="text-[9px] uppercase tracking-wider text-slate-400">Estimated Cost</div>
                        <div className="text-base font-bold text-amber-400 font-mono mt-0.5">
                          ${Math.round(customSolveResult.estimated_cost?.total_expected_cost_usd ?? 0)}
                        </div>
                        <span className="text-[9px] text-slate-400">joint objective</span>
                      </div>
                    </div>

                    {/* Infeasibility Details if Not Feasible */}
                    {!customSolveResult.feasible && customSolveResult.infeasibility_details && (
                      <div className="p-4 rounded-xl bg-rose-950/50 border border-rose-500/30 space-y-2 text-xs">
                        <div className="font-bold text-rose-300 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
                          <ShieldAlert className="w-4 h-4" /> Root Cause Conflicts:
                        </div>
                        <ul className="list-disc list-inside space-y-1 text-rose-200">
                          {customSolveResult.infeasibility_details.root_cause_conflicts.map((c, i) => (
                            <li key={i}>{c}</li>
                          ))}
                        </ul>
                        <div className="font-semibold text-white pt-1">Recommended Resolutions:</div>
                        <ul className="list-disc list-inside space-y-1 text-slate-300 text-[11px]">
                          {customSolveResult.infeasibility_details.actionable_bottleneck_resolutions.map((r, i) => (
                            <li key={i}>{r}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Reasoning Section */}
                    <div className="space-y-2 pt-2 border-t border-white/10">
                      <div className="text-xs font-bold text-slate-300">Model Reasoning:</div>
                      <div className="space-y-1 text-xs text-slate-300">
                        {customSolveResult.reasoning.map((r, idx) => (
                          <div key={idx} className="flex items-start gap-1.5">
                            <span className="text-purple-400 font-bold">•</span>
                            <span>{r}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ) : (
                <div className="h-full min-h-[360px] flex flex-col items-center justify-center p-8 rounded-2xl border border-dashed border-white/15 text-center text-slate-400 space-y-3">
                  <Scale className="w-10 h-10 text-purple-400/50" />
                  <div className="text-sm font-semibold text-slate-300">Awaiting Optimization Parameters</div>
                  <p className="text-xs max-w-sm">
                    Configure your 9 operational inputs on the left and click "Solve Optimal Batch" to execute Google OR-Tools SCIP MILP solver.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ========================================================= */}
      {/* TAB 3: KITCHEN PREP LINE SCHEDULE                        */}
      {/* ========================================================= */}
      {activeTab === 'prep_sheet' && (
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-2xl glass-panel border border-white/10 bg-slate-900/80">
            <div>
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <ChefHat className="w-5 h-5 text-purple-400" />
                Active Shift Batch Preparation Schedule
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Kitchen line prep sheets updated with OR-Tools batch quantities. Apply single dish or commit entire shift.
              </p>
            </div>
            <Button
              variant="primary"
              size="sm"
              onClick={() => setConfirmCommitAllOpen(true)}
              leftIcon={<Sparkles className="w-3.5 h-3.5" />}
            >
              Commit All 3 Line Batches
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {prepLine.map((item) => (
              <AIRecommendationCard
                key={item.id}
                title={item.dishName}
                category={`OR-Tools Batch: ${item.station}`}
                confidencePercentage={96}
                reasoning={`Chef baseline planned ${item.plannedPortions} portions. Accounting for ${item.inventoryOnHand} on-hand portions and ${item.demandForecast} forecasted demand, optimal batch is ${item.recommendedPortions} portions, reducing surplus risk by ${Math.round((item.expectedWasteSavedKg / 20) * 100)}%.`}
                impactMetrics={[
                  { label: 'Planned Baseline', value: `${item.plannedPortions} portions` },
                  { label: 'Optimized Batch', value: `${item.recommendedPortions} portions` },
                  { label: 'Waste Diverted', value: `${item.expectedWasteSavedKg} kg` },
                  { label: 'Estimated Savings', value: `$${item.costSavingsUSD}` },
                ]}
                actionLabel={item.applied ? '✓ Committed to Prep' : 'Apply Optimization'}
                onApply={() => handleApplySinglePrep(item.id)}
                isApplied={item.applied}
                modelSource="Google OR-Tools SCIP + Newsvendor Theorem"
              />
            ))}
          </div>
        </div>
      )}

      {/* Commit All Dialog */}
      <ConfirmDialog
        isOpen={confirmCommitAllOpen}
        onClose={() => setConfirmCommitAllOpen(false)}
        onConfirm={handleApplyAllPrep}
        title="Commit All Production Optimizations to Kitchen Prep Sheet?"
        description="This will lock optimal batch sizes for all active kitchen stations. Prep cooks and chef stations will immediately receive calibrated ingredient weights and batch targets."
        confirmText="Commit to Kitchen Line"
      />
    </div>
  );
};
