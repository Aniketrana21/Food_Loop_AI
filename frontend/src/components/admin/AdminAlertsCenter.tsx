'use client';

import React, { useState } from 'react';
import { 
  AlertTriangle, 
  AlertOctagon, 
  XCircle, 
  Clock, 
  Cpu, 
  Eye, 
  ServerCrash, 
  CheckCircle, 
  Filter, 
  ArrowRight, 
  RefreshCw,
  TrendingUp,
  ShieldAlert
} from 'lucide-react';
import { Badge } from '@/components/design-system/Badge';
import { Button } from '@/components/design-system/Button';
import { Card } from '@/components/design-system/Card';
import { AdminAlert, AlertCategory, AlertSeverity } from './types';

interface AdminAlertsCenterProps {
  alerts: AdminAlert[];
  onAcknowledgeAlert?: (alertId: string) => void;
  onRefresh?: () => void;
  isLoading?: boolean;
}

export const AdminAlertsCenter: React.FC<AdminAlertsCenterProps> = ({
  alerts,
  onAcknowledgeAlert,
  onRefresh,
  isLoading = false
}) => {
  const [selectedCategory, setSelectedCategory] = useState<AlertCategory | 'ALL'>('ALL');
  const [selectedSeverity, setSelectedSeverity] = useState<AlertSeverity | 'ALL'>('ALL');
  const [acknowledgedIds, setAcknowledgedIds] = useState<Set<string>>(new Set());

  const categoryConfigs: Record<AlertCategory, { label: string; icon: React.ReactNode; color: string; desc: string }> = {
    expired_surplus: {
      label: 'Expired Surplus',
      icon: <Clock className="w-4 h-4 text-amber-400" />,
      color: 'warning',
      desc: 'Safe consumption window passed for uncollected inventory batches'
    },
    failed_delivery: {
      label: 'Failed Delivery',
      icon: <XCircle className="w-4 h-4 text-rose-400" />,
      color: 'danger',
      desc: 'Courier logistics disruption or cancellation requiring re-routing'
    },
    abnormal_waste_increase: {
      label: 'Abnormal Waste Spike',
      icon: <TrendingUp className="w-4 h-4 text-amber-400" />,
      color: 'warning',
      desc: 'Kitchen logged waste > 20% exceeding historic moving baseline'
    },
    model_failure: {
      label: 'Model Failure',
      icon: <Cpu className="w-4 h-4 text-rose-400" />,
      color: 'danger',
      desc: 'Forecasting or Bayesian estimation pipeline exception or drift'
    },
    low_prediction_confidence: {
      label: 'Low CV Confidence',
      icon: <Eye className="w-4 h-4 text-sky-400" />,
      color: 'info',
      desc: 'Computer Vision food scan confidence < 75% requiring human check'
    },
    system_errors: {
      label: 'System Errors',
      icon: <ServerCrash className="w-4 h-4 text-rose-400" />,
      color: 'danger',
      desc: 'Database timeouts, API latency anomalies, or security log triggers'
    }
  };

  const handleAcknowledge = (id: string) => {
    setAcknowledgedIds(prev => new Set(prev).add(id));
    if (onAcknowledgeAlert) onAcknowledgeAlert(id);
  };

  const filteredAlerts = alerts
    .filter(a => !acknowledgedIds.has(a.id))
    .filter(a => selectedCategory === 'ALL' || a.category === selectedCategory)
    .filter(a => selectedSeverity === 'ALL' || a.severity === selectedSeverity);

  // Tally active alerts by category
  const tallyByCategory = (cat: AlertCategory) => {
    return alerts.filter(a => !acknowledgedIds.has(a.id) && a.category === cat).length;
  };

  return (
    <div className="space-y-6">
      {/* 6 Category Summary Cards Header */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {(Object.keys(categoryConfigs) as AlertCategory[]).map((cat) => {
          const cfg = categoryConfigs[cat];
          const count = tallyByCategory(cat);
          const isSelected = selectedCategory === cat;

          return (
            <div
              key={cat}
              onClick={() => setSelectedCategory(isSelected ? 'ALL' : cat)}
              className={`p-3.5 rounded-2xl border transition-all cursor-pointer flex flex-col justify-between ${
                isSelected
                  ? 'bg-slate-800/90 border-emerald-500/50 ring-2 ring-emerald-500/20 shadow-lg'
                  : 'bg-slate-900/60 border-white/10 hover:border-white/20'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="p-2 rounded-xl bg-slate-950/60 border border-white/5">
                  {cfg.icon}
                </div>
                <span className={`text-xl font-black ${count > 0 ? (cfg.color === 'danger' ? 'text-rose-400' : 'text-amber-400') : 'text-slate-500'}`}>
                  {count}
                </span>
              </div>
              <div className="mt-3">
                <h4 className="text-xs font-bold text-white tracking-tight leading-snug">{cfg.label}</h4>
                <p className="text-[10px] text-slate-400 truncate mt-0.5">{cfg.desc}</p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Control Filter Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-2xl glass-panel bg-slate-900/60 border border-white/10">
        <div className="flex items-center space-x-2">
          <ShieldAlert className="w-5 h-5 text-emerald-400" />
          <div>
            <h3 className="text-sm font-bold text-white tracking-wide">
              Active Administrative Alerts ({filteredAlerts.length})
            </h3>
            <p className="text-[11px] text-slate-400">Mandatory multi-channel telemetry monitoring</p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Severity Filter */}
          <div className="flex items-center space-x-1 bg-slate-950/80 p-1 rounded-xl border border-white/10 text-xs">
            <button
              onClick={() => setSelectedSeverity('ALL')}
              className={`px-2.5 py-1 rounded-lg font-semibold transition-all ${
                selectedSeverity === 'ALL' ? 'bg-slate-800 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              All Severities
            </button>
            <button
              onClick={() => setSelectedSeverity('CRITICAL')}
              className={`px-2.5 py-1 rounded-lg font-semibold transition-all ${
                selectedSeverity === 'CRITICAL' ? 'bg-rose-500/20 text-rose-300 font-bold border border-rose-500/40' : 'text-slate-400 hover:text-rose-300'
              }`}
            >
              Critical
            </button>
            <button
              onClick={() => setSelectedSeverity('HIGH')}
              className={`px-2.5 py-1 rounded-lg font-semibold transition-all ${
                selectedSeverity === 'HIGH' ? 'bg-amber-500/20 text-amber-300 font-bold border border-amber-500/40' : 'text-slate-400 hover:text-amber-300'
              }`}
            >
              High
            </button>
          </div>

          {onRefresh && (
            <Button
              variant="outline"
              size="sm"
              onClick={onRefresh}
              isLoading={isLoading}
              leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
            >
              Refresh
            </Button>
          )}
        </div>
      </div>

      {/* Alerts Feed List */}
      <div className="space-y-3">
        {filteredAlerts.length === 0 ? (
          <div className="p-12 text-center rounded-3xl glass-panel bg-slate-900/30 border border-white/5">
            <CheckCircle className="w-12 h-12 text-emerald-400 mx-auto opacity-70" />
            <h4 className="text-base font-bold text-white mt-3">No Active Alerts In Category</h4>
            <p className="text-xs text-slate-400 max-w-sm mx-auto mt-1">
              All multi-facility logistics, food-safety deadlines, and ML pipelines are currently running within optimal operating limits.
            </p>
          </div>
        ) : (
          filteredAlerts.map((alert) => {
            const cfg = categoryConfigs[alert.category] || {
              label: alert.category,
              icon: <AlertTriangle className="w-4 h-4 text-amber-400" />,
              color: 'warning'
            };

            return (
              <div
                key={alert.id}
                className="p-4 rounded-2xl glass-panel bg-slate-900/80 border border-white/10 hover:border-white/20 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-xl"
              >
                <div className="flex items-start space-x-3.5">
                  <div className={`p-2.5 rounded-xl border mt-0.5 shrink-0 ${
                    alert.severity === 'CRITICAL'
                      ? 'bg-rose-500/15 border-rose-500/30 text-rose-400'
                      : alert.severity === 'HIGH'
                      ? 'bg-amber-500/15 border-amber-500/30 text-amber-400'
                      : 'bg-sky-500/15 border-sky-500/30 text-sky-400'
                  }`}>
                    {cfg.icon}
                  </div>

                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge
                        variant={alert.severity === 'CRITICAL' ? 'danger' : alert.severity === 'HIGH' ? 'warning' : 'info'}
                        size="sm"
                      >
                        {alert.severity}
                      </Badge>

                      <span className="text-xs font-semibold text-slate-300">
                        {cfg.label}
                      </span>

                      {alert.entity_type && (
                        <span className="text-[10px] px-2 py-0.5 rounded-md bg-slate-950 text-slate-400 border border-white/5 font-mono">
                          {alert.entity_type} {alert.entity_id ? `(#${alert.entity_id.slice(0, 8)})` : ''}
                        </span>
                      )}

                      <span className="text-[11px] text-slate-500 ml-auto sm:ml-0">
                        {new Date(alert.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>

                    <h4 className="text-sm font-bold text-white tracking-tight mt-1">{alert.title}</h4>
                    <p className="text-xs text-slate-400 mt-0.5 leading-relaxed">{alert.message}</p>
                  </div>
                </div>

                <div className="flex items-center space-x-2 shrink-0 self-end sm:self-center">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleAcknowledge(alert.id)}
                    leftIcon={<CheckCircle className="w-3.5 h-3.5" />}
                  >
                    Acknowledge
                  </Button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
