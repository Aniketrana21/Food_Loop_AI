'use client';

import React from 'react';
import { 
  Cpu, 
  Activity, 
  CheckCircle2, 
  AlertTriangle, 
  RefreshCw, 
  Gauge, 
  Zap, 
  Eye, 
  TrendingUp, 
  Server,
  Layers
} from 'lucide-react';
import { Badge } from '@/components/design-system/Badge';
import { Button } from '@/components/design-system/Button';
import { AdminModelPerformance, ModelMetricDetail } from './types';

interface AdminModelPerformanceProps {
  performance: AdminModelPerformance | null;
  onRetrainModel?: (modelName: string) => void;
  isLoading?: boolean;
}

export const AdminModelPerformanceView: React.FC<AdminModelPerformanceProps> = ({
  performance,
  onRetrainModel,
  isLoading = false
}) => {
  const models = performance?.models || [];

  return (
    <div className="space-y-6">
      {/* Telemetry Summary Banner */}
      <div className="p-5 rounded-3xl glass-panel bg-slate-900/70 border border-white/10 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-2xl bg-purple-500/20 text-purple-400 flex items-center justify-center border border-purple-500/30">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <Badge variant="purple" size="sm">AI Engine Telemetry</Badge>
              <Badge variant="emerald" size="sm">
                Status: {performance?.overall_health || 'OPTIMAL'}
              </Badge>
            </div>
            <h3 className="text-base font-bold text-white tracking-tight mt-1">
              Predictive Models & Optical Edge Telemetry
            </h3>
            <p className="text-xs text-slate-400">
              Live validation loss, R² correlation scores, inference latencies, and data drift detection
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <div className="text-right hidden sm:block">
            <span className="text-[10px] text-slate-400 font-semibold uppercase">Engine Latency</span>
            <div className="text-sm font-bold text-emerald-400">~42ms avg</div>
          </div>
        </div>
      </div>

      {/* Model Cards Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {models.map((model) => (
          <div
            key={model.model_name}
            className="glass-panel p-6 rounded-3xl border border-white/10 bg-slate-900/80 hover:border-white/20 transition-all flex flex-col justify-between shadow-2xl"
          >
            <div>
              <div className="flex items-start justify-between">
                <div>
                  <Badge variant={model.task === 'COMPUTER_VISION' ? 'cyan' : model.task === 'DEMAND_FORECAST' ? 'purple' : 'emerald'} size="sm">
                    {model.task.replace('_', ' ')}
                  </Badge>
                  <h4 className="text-base font-bold text-white tracking-tight mt-1.5">{model.model_name}</h4>
                  <span className="text-[11px] text-slate-400 font-mono">Version {model.version}</span>
                </div>

                <div className={`p-2 rounded-xl border ${
                  model.status === 'OPTIMAL'
                    ? 'bg-emerald-500/15 border-emerald-500/30 text-emerald-400'
                    : 'bg-amber-500/15 border-amber-500/30 text-amber-400'
                }`}>
                  <CheckCircle2 className="w-4 h-4" />
                </div>
              </div>

              {/* Telemetry Metrics Grid */}
              <div className="grid grid-cols-2 gap-2.5 mt-5 p-3.5 rounded-2xl bg-slate-950/70 border border-white/5 text-xs">
                {model.r2_score !== undefined && (
                  <div>
                    <span className="text-[10px] text-slate-500 uppercase font-bold">R² Score</span>
                    <p className="text-sm font-black text-emerald-400 mt-0.5">{model.r2_score.toFixed(3)}</p>
                  </div>
                )}

                {model.accuracy_pct !== undefined && (
                  <div>
                    <span className="text-[10px] text-slate-500 uppercase font-bold">Top-1 Accuracy</span>
                    <p className="text-sm font-black text-cyan-300 mt-0.5">{model.accuracy_pct.toFixed(1)}%</p>
                  </div>
                )}

                {model.mae !== undefined && (
                  <div>
                    <span className="text-[10px] text-slate-500 uppercase font-bold">Mean Abs Error</span>
                    <p className="text-sm font-black text-white mt-0.5">±{model.mae} kg</p>
                  </div>
                )}

                {model.mean_confidence !== undefined && (
                  <div>
                    <span className="text-[10px] text-slate-500 uppercase font-bold">Mean Confidence</span>
                    <p className="text-sm font-black text-emerald-400 mt-0.5">{(model.mean_confidence * 100).toFixed(1)}%</p>
                  </div>
                )}

                <div>
                  <span className="text-[10px] text-slate-500 uppercase font-bold">Inference Latency</span>
                  <p className="text-sm font-black text-purple-300 mt-0.5 flex items-center gap-1">
                    <Zap className="w-3.5 h-3.5 text-purple-400" />
                    {model.inference_latency_ms} ms
                  </p>
                </div>

                <div>
                  <span className="text-[10px] text-slate-500 uppercase font-bold">Samples Evaluated</span>
                  <p className="text-sm font-black text-white mt-0.5">{model.total_predictions_analyzed.toLocaleString()}</p>
                </div>
              </div>

              {/* Status bar */}
              <div className="mt-4 p-2.5 rounded-xl bg-slate-900 border border-white/5 flex items-center justify-between text-[11px]">
                <span className="text-slate-400">Drift Assessment:</span>
                <span className={`font-bold ${model.status === 'OPTIMAL' ? 'text-emerald-400' : 'text-amber-400'}`}>
                  {model.status === 'OPTIMAL' ? 'No Concept Drift' : 'Drift Alert Detected'}
                </span>
              </div>
            </div>

            <div className="mt-5 pt-3 border-t border-white/5 flex items-center justify-between">
              <span className="text-[10px] text-slate-500">
                Last Evaluated {new Date(model.last_updated).toLocaleTimeString()}
              </span>
              {onRetrainModel && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onRetrainModel(model.model_name)}
                  leftIcon={<RefreshCw className="w-3 h-3" />}
                >
                  Trigger Retraining
                </Button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
