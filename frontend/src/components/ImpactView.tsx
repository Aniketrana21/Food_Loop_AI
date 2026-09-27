'use client';

import React, { useState } from 'react';
import { ImpactSummary } from '@/types';
import { 
  TrendingUp, 
  Leaf, 
  Droplet, 
  DollarSign, 
  Award, 
  Utensils, 
  Zap, 
  ChevronRight,
  ShieldCheck,
  Scale
} from 'lucide-react';
import { predictSurplus } from '@/lib/api';

interface ImpactViewProps {
  impact: ImpactSummary | null;
}

export const ImpactView: React.FC<ImpactViewProps> = ({ impact }) => {
  // ML Simulator State
  const [simData, setSimData] = useState({
    business_type: 'restaurant',
    category: 'cooked_meals',
    planned_covers: 180,
    prepared_volume_kg: 85.0,
    temp_c: 24.0,
    is_weekend: 1,
    is_rainy: 0,
    event_nearby: 1
  });
  const [simResult, setSimResult] = useState<any>(null);
  const [simLoading, setSimLoading] = useState(false);

  const handleSimulate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSimLoading(true);
    try {
      const res = await predictSurplus({
        ...simData,
        day_of_week: simData.is_weekend ? 5 : 2,
        rainfall_mm: simData.is_rainy ? 12.0 : 0.0
      });
      setSimResult(res);
    } catch (err: any) {
      alert('ML Simulation error');
    } finally {
      setSimLoading(false);
    }
  };

  const kgSaved = impact?.total_food_diverted_kg || 1420.5;
  const meals = impact?.total_meals_provided || 3150;
  const co2 = impact?.total_co2_avoided_kg || 3551.2;
  const water = impact?.total_water_saved_liters || 1420000;
  const value = impact?.total_economic_value_usd || 6392.25;

  return (
    <div className="space-y-8 animate-fade-in">
      
      {/* Top Banner */}
      <div className="text-center max-w-2xl mx-auto space-y-2">
        <span className="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          Global Sustainability Ledger
        </span>
        <h2 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
          Quantifiable Environmental & Community Impact
        </h2>
        <p className="text-xs text-slate-400 leading-relaxed">
          Every kilogram of surplus rescued diverts methane from municipal landfills and feeds communities.
          Our metrics follow the EPA Food Recovery Hierarchy and GHG protocol.
        </p>
      </div>

      {/* Hero Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        
        <div className="glass-panel p-5 rounded-2xl border border-emerald-500/20 bg-gradient-to-br from-emerald-950/40 to-slate-900 shadow-xl">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-bold uppercase tracking-wider">Food Rescued</span>
            <div className="w-8 h-8 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center">
              <Scale className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-black text-white">{kgSaved.toLocaleString()} kg</div>
          <p className="text-[11px] text-emerald-400 mt-1 font-semibold">
            ≈ {meals.toLocaleString()} Nutritious Meals Served
          </p>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-teal-500/20 bg-gradient-to-br from-teal-950/40 to-slate-900 shadow-xl">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-bold uppercase tracking-wider">CO₂e Avoided</span>
            <div className="w-8 h-8 rounded-lg bg-teal-500/20 text-teal-400 flex items-center justify-center">
              <Leaf className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-black text-white">{co2.toLocaleString()} kg</div>
          <p className="text-[11px] text-teal-400 mt-1 font-semibold">
            ≈ {Math.round(co2 / 4.6)} Miles driven by gas passenger car
          </p>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-cyan-500/20 bg-gradient-to-br from-cyan-950/40 to-slate-900 shadow-xl">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-bold uppercase tracking-wider">Water Conserved</span>
            <div className="w-8 h-8 rounded-lg bg-cyan-500/20 text-cyan-400 flex items-center justify-center">
              <Droplet className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-black text-white">{(water / 1000).toLocaleString()} kL</div>
          <p className="text-[11px] text-cyan-400 mt-1 font-semibold">
            Direct agricultural footprint savings
          </p>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-amber-500/20 bg-gradient-to-br from-amber-950/40 to-slate-900 shadow-xl">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-bold uppercase tracking-wider">Economic Value</span>
            <div className="w-8 h-8 rounded-lg bg-amber-500/20 text-amber-400 flex items-center justify-center">
              <DollarSign className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-black text-white">${value.toLocaleString()}</div>
          <p className="text-[11px] text-amber-400 mt-1 font-semibold">
            Tax deductible inventory write-off
          </p>
        </div>

      </div>

      {/* Two Column Layout: ML Surplus Simulator & Corporate Leaderboard */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* ML Surplus Forecast Simulator */}
        <div className="glass-panel p-6 rounded-3xl border border-white/10 space-y-4">
          <div className="flex items-center justify-between border-b border-white/5 pb-3">
            <div>
              <h3 className="text-base font-bold text-white flex items-center space-x-2">
                <span>AI Surplus & Waste Risk Simulator</span>
                <span className="text-[10px] bg-emerald-500/20 text-emerald-400 font-mono px-2 py-0.5 rounded border border-emerald-500/30">
                  XGBoost v1.2
                </span>
              </h3>
              <p className="text-xs text-slate-400">Forecast expected food surplus based on weather and covers</p>
            </div>
          </div>

          <form onSubmit={handleSimulate} className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[11px] font-semibold text-slate-300 mb-1">
                  Business Entity Type
                </label>
                <select
                  value={simData.business_type}
                  onChange={(e) => setSimData({ ...simData, business_type: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-white/10 text-white text-xs focus:outline-none focus:border-emerald-500"
                >
                  <option value="restaurant">Full Service Restaurant</option>
                  <option value="hotel">Hotel & Catering Banquet</option>
                  <option value="supermarket">Grocery / Supermarket</option>
                  <option value="bakery">Artisan Bakery</option>
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-300 mb-1">
                  Food Category
                </label>
                <select
                  value={simData.category}
                  onChange={(e) => setSimData({ ...simData, category: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-white/10 text-white text-xs focus:outline-none focus:border-emerald-500"
                >
                  <option value="cooked_meals">Cooked Entrees</option>
                  <option value="bakery">Breads & Pastries</option>
                  <option value="dairy">Chilled Dairy</option>
                  <option value="fresh_produce">Salads & Produce</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[11px] font-semibold text-slate-300 mb-1">
                  Planned Covers / Patrons
                </label>
                <input
                  type="number"
                  min="20"
                  max="1000"
                  value={simData.planned_covers}
                  onChange={(e) => setSimData({ ...simData, planned_covers: parseInt(e.target.value) || 0 })}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-white/10 text-white text-xs focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-300 mb-1">
                  Prepared Weight (kg)
                </label>
                <input
                  type="number"
                  min="10"
                  max="500"
                  value={simData.prepared_volume_kg}
                  onChange={(e) => setSimData({ ...simData, prepared_volume_kg: parseFloat(e.target.value) || 0 })}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-white/10 text-white text-xs focus:outline-none focus:border-emerald-500"
                />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-2 pt-1 text-[11px] text-slate-300">
              <label className="flex items-center space-x-1.5 cursor-pointer bg-slate-950 p-2 rounded-xl border border-white/5">
                <input
                  type="checkbox"
                  checked={simData.is_weekend === 1}
                  onChange={(e) => setSimData({ ...simData, is_weekend: e.target.checked ? 1 : 0 })}
                  className="accent-emerald-500"
                />
                <span>Weekend Surge</span>
              </label>

              <label className="flex items-center space-x-1.5 cursor-pointer bg-slate-950 p-2 rounded-xl border border-white/5">
                <input
                  type="checkbox"
                  checked={simData.is_rainy === 1}
                  onChange={(e) => setSimData({ ...simData, is_rainy: e.target.checked ? 1 : 0 })}
                  className="accent-emerald-500"
                />
                <span>Rain Forecast</span>
              </label>

              <label className="flex items-center space-x-1.5 cursor-pointer bg-slate-950 p-2 rounded-xl border border-white/5">
                <input
                  type="checkbox"
                  checked={simData.event_nearby === 1}
                  onChange={(e) => setSimData({ ...simData, event_nearby: e.target.checked ? 1 : 0 })}
                  className="accent-emerald-500"
                />
                <span>Nearby Event</span>
              </label>
            </div>

            <button
              type="submit"
              disabled={simLoading}
              className="w-full py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 text-xs font-bold transition-all shadow-md shadow-emerald-500/20 active:scale-95 flex items-center justify-center space-x-2"
            >
              <Zap className="w-3.5 h-3.5" />
              <span>{simLoading ? 'Running Inference...' : 'Run Surplus ML Inference'}</span>
            </button>
          </form>

          {/* Inference Output Card */}
          {simResult && (
            <div className="p-4 rounded-2xl bg-slate-950 border border-emerald-500/30 space-y-2 animate-fade-in">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-400">Predicted Surplus:</span>
                <span className="font-bold text-emerald-400 text-sm">
                  {simResult.predicted_surplus_kg} kg ({simResult.predicted_portions} meals)
                </span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-400">Spoilage Risk Severity:</span>
                <span className="font-bold text-amber-300">
                  {Math.round(simResult.spoilage_risk_score * 100)}% ({simResult.risk_tier})
                </span>
              </div>
              <div className="text-[11px] text-slate-300 pt-1 border-t border-white/5">
                💡 <span className="font-semibold text-slate-200">{simResult.recommendation}</span>
              </div>
            </div>
          )}
        </div>

        {/* Corporate & Community Leaderboard */}
        <div className="glass-panel p-6 rounded-3xl border border-white/10 space-y-4">
          <div className="flex items-center justify-between border-b border-white/5 pb-3">
            <div>
              <h3 className="text-base font-bold text-white flex items-center space-x-2">
                <Award className="w-4 h-4 text-amber-400" />
                <span>Zero-Waste Partner Leaderboard</span>
              </h3>
              <p className="text-xs text-slate-400">Verified corporate donors making an extraordinary impact</p>
            </div>
          </div>

          <div className="space-y-3">
            {impact?.leaderboard.map((item, idx) => (
              <div
                key={idx}
                className="p-3.5 rounded-2xl bg-slate-950/70 border border-white/5 flex items-center justify-between hover:border-emerald-500/30 transition-all"
              >
                <div className="flex items-center space-x-3">
                  <div className={`w-8 h-8 rounded-xl flex items-center justify-center font-bold text-xs ${
                    idx === 0 ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' :
                    (idx === 1 ? 'bg-slate-300/20 text-slate-200 border border-slate-300/30' : 'bg-slate-800 text-slate-400')
                  }`}>
                    #{idx + 1}
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-white">{item.name}</h4>
                    <p className="text-[10px] text-slate-400">Verified FoodLoop Partner</p>
                  </div>
                </div>

                <div className="text-right">
                  <span className="text-xs font-bold text-emerald-400">{item.meals_donated.toLocaleString()} meals</span>
                  <p className="text-[10px] text-slate-400">{item.co2_saved_kg} kg CO₂ saved</p>
                </div>
              </div>
            ))}
          </div>

          <div className="p-3 rounded-2xl bg-indigo-950/30 border border-indigo-500/20 flex items-center justify-between text-xs text-indigo-300">
            <span>Want your kitchen on the leaderboard?</span>
            <button
              onClick={() => alert('Tax receipts & corporate certificates can be exported via FoodLoop Admin Portal.')}
              className="font-bold underline hover:text-white"
            >
              Export ESG Report
            </button>
          </div>
        </div>

      </div>

    </div>
  );
};
