'use client';

import React, { useState } from 'react';
import { OptimizationResult } from '@/types';
import { 
  Truck, 
  Play, 
  CheckCircle2, 
  MapPin, 
  Clock, 
  Package, 
  Navigation, 
  Sparkles, 
  Zap,
  ArrowRight,
  ShieldAlert
} from 'lucide-react';
import { runDispatchOptimization } from '@/lib/api';

interface RouteOptimizerViewProps {
  optimization: OptimizationResult | null;
  onUpdateOptimization: (result: OptimizationResult) => void;
}

export const RouteOptimizerView: React.FC<RouteOptimizerViewProps> = ({
  optimization,
  onUpdateOptimization
}) => {
  const [running, setRunning] = useState(false);

  const handleRunOptimizer = async () => {
    setRunning(true);
    try {
      const res = await runDispatchOptimization();
      onUpdateOptimization(res);
    } catch (err: any) {
      alert('Optimization solver error');
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Header Banner & Solver Trigger */}
      <div className="glass-panel p-6 rounded-3xl border border-white/10 flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gradient-to-r from-slate-900 via-slate-900 to-indigo-950/40">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold tracking-wider uppercase bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
              Operations Research Engine
            </span>
            <span className="text-xs text-slate-400">Google OR-Tools CVRPTW</span>
          </div>
          <h2 className="text-xl font-extrabold text-white tracking-tight mt-1">
            Automated Courier Route Optimization & Dispatch
          </h2>
          <p className="text-xs text-slate-300 mt-1 max-w-2xl leading-relaxed">
            Solves multi-stop Capacitated Vehicle Routing with strict Expiry Time Windows (EEF).
            Pairs surplus donors with nearby verified food banks while enforcing vehicle payload limits.
          </p>
        </div>

        <button
          onClick={handleRunOptimizer}
          disabled={running}
          className="px-6 py-3 rounded-2xl bg-gradient-to-r from-emerald-500 to-teal-400 hover:from-emerald-400 hover:to-teal-300 text-slate-950 font-bold text-xs shadow-xl shadow-emerald-500/25 active:scale-95 transition-all flex items-center justify-center space-x-2 shrink-0 disabled:opacity-50"
        >
          {running ? (
            <>
              <Zap className="w-4 h-4 animate-spin text-slate-950" />
              <span>Solving Constraints...</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4 fill-slate-950" />
              <span>Re-Solve Fleet Routes</span>
            </>
          )}
        </button>
      </div>

      {/* Solver Metric Stat Cards */}
      {optimization && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="glass-panel p-4 rounded-2xl border border-white/10">
            <span className="text-[11px] font-medium text-slate-400">Solver Status</span>
            <div className="flex items-center space-x-1.5 mt-1">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span className="text-lg font-bold text-white font-mono">{optimization.solver_status}</span>
            </div>
          </div>

          <div className="glass-panel p-4 rounded-2xl border border-white/10">
            <span className="text-[11px] font-medium text-slate-400">Vehicles Dispatched</span>
            <div className="flex items-center space-x-1.5 mt-1">
              <Truck className="w-4 h-4 text-indigo-400" />
              <span className="text-lg font-bold text-white">{optimization.num_vehicles_dispatched} Couriers</span>
            </div>
          </div>

          <div className="glass-panel p-4 rounded-2xl border border-white/10">
            <span className="text-[11px] font-medium text-slate-400">Food Volume Rescued</span>
            <div className="flex items-center space-x-1.5 mt-1">
              <Package className="w-4 h-4 text-emerald-400" />
              <span className="text-lg font-bold text-emerald-400">{optimization.total_rescued_kg} kg</span>
            </div>
          </div>

          <div className="glass-panel p-4 rounded-2xl border border-white/10">
            <span className="text-[11px] font-medium text-slate-400">Fleet Distance & Time</span>
            <div className="flex items-center space-x-1.5 mt-1">
              <Navigation className="w-4 h-4 text-amber-400" />
              <span className="text-lg font-bold text-white">{optimization.total_distance_km} km</span>
              <span className="text-xs text-slate-400">({optimization.total_travel_time_mins}m)</span>
            </div>
          </div>
        </div>
      )}

      {/* Driver Itinerary Cards */}
      <div className="space-y-4">
        <h3 className="text-sm font-bold text-slate-300 uppercase tracking-wider">
          Active Multi-Stop Driver Itineraries
        </h3>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {optimization?.routes.map((route, rIdx) => {
            const loadPct = Math.min(100, Math.round((route.total_load_kg / route.vehicle_capacity_kg) * 100));

            return (
              <div 
                key={route.driver_id} 
                className="glass-panel rounded-2xl border border-white/10 p-5 space-y-4 hover:border-emerald-500/30 transition-all"
              >
                {/* Driver Vehicle Banner */}
                <div className="flex items-center justify-between border-b border-white/5 pb-3">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 rounded-xl bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 flex items-center justify-center font-bold">
                      {route.driver_name.charAt(0)}
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-white">{route.driver_name}</h4>
                      <p className="text-[11px] text-slate-400 capitalize">{route.vehicle_type.replace('_', ' ')}</p>
                    </div>
                  </div>

                  <div className="text-right">
                    <span className="text-xs font-bold text-emerald-400">{route.total_distance_km} km</span>
                    <p className="text-[10px] text-slate-400">{route.total_duration_mins} mins travel</p>
                  </div>
                </div>

                {/* Capacity Bar */}
                <div className="space-y-1">
                  <div className="flex justify-between text-[11px]">
                    <span className="text-slate-400">Payload Load Factor</span>
                    <span className="text-white font-bold">{route.total_load_kg} / {route.vehicle_capacity_kg} kg ({loadPct}%)</span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                    <div 
                      style={{ width: `${loadPct}%` }}
                      className={`h-full rounded-full transition-all ${
                        loadPct > 80 ? 'bg-amber-400' : 'bg-emerald-400'
                      }`}
                    />
                  </div>
                </div>

                {/* Stop by Stop Itinerary */}
                <div className="space-y-2.5 pt-2">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    Chronological Waypoints ({route.stops.length} Stops)
                  </span>

                  <div className="space-y-2">
                    {route.stops.map((stop, sIdx) => (
                      <div 
                        key={sIdx}
                        className="p-2.5 rounded-xl bg-slate-950/70 border border-white/5 flex items-center justify-between text-xs"
                      >
                        <div className="flex items-center space-x-2.5">
                          <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${
                            stop.stop_type === 'depot'
                              ? 'bg-slate-800 text-slate-300'
                              : (stop.stop_type === 'pickup' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-violet-500/20 text-violet-300')
                          }`}>
                            {stop.stop_index}
                          </span>
                          <div>
                            <div className="font-semibold text-white flex items-center space-x-1.5">
                              <span>{stop.name}</span>
                              <span className={`text-[9px] uppercase font-bold px-1.5 py-0.2 rounded ${
                                stop.stop_type === 'pickup' ? 'bg-emerald-500/10 text-emerald-400' : (stop.stop_type === 'dropoff' ? 'bg-violet-500/10 text-violet-400' : 'bg-slate-800 text-slate-400')
                              }`}>
                                {stop.stop_type}
                              </span>
                            </div>
                            <p className="text-[10px] text-slate-400 truncate max-w-[200px]">{stop.address}</p>
                          </div>
                        </div>

                        <div className="text-right">
                          <span className="text-[11px] font-mono text-amber-300 font-bold">
                            T+{stop.arrival_time_mins}m
                          </span>
                          {stop.demand_kg > 0 && (
                            <p className="text-[10px] text-emerald-400 font-semibold">
                              +{stop.demand_kg} kg
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

              </div>
            );
          })}
        </div>
      </div>

    </div>
  );
};
