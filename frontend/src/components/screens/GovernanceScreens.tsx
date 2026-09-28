'use client';

import React, { useState } from 'react';
import { 
  BarChart3, 
  Bell, 
  Settings, 
  ShieldCheck, 
  Download, 
  CheckCircle2, 
  Leaf, 
  Droplets, 
  DollarSign, 
  Utensils, 
  Search, 
  Filter, 
  Key, 
  Webhook, 
  Sliders, 
  Save, 
  ExternalLink,
  Lock,
  FileCheck
} from 'lucide-react';
import { Button } from '@/components/design-system/Button';
import { Badge } from '@/components/design-system/Badge';
import { Input, Select } from '@/components/design-system/Input';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/design-system/Card';
import { KpiCard } from '@/components/design-system/KpiCard';
import { ScreenId } from '@/components/navigation/Sidebar';
import { 
  MOCK_NOTIFICATIONS, 
  MOCK_AUDIT_LOGS, 
  NotificationItem, 
  AuditLogEntry 
} from '@/lib/mockData';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip } from 'recharts';

import { ImpactAnalyticsScreen } from './ImpactAnalyticsScreen';

interface GovernanceProps {
  onNavigate: (screen: ScreenId) => void;
  onShowSuccess: (msg: string) => void;
}

// -------------------------------------------------------------
// 1. IMPACT DASHBOARD SCREEN (PHASE 15: SUSTAINABILITY ANALYTICS ENGINE)
// -------------------------------------------------------------
export const ImpactDashboardScreen: React.FC<GovernanceProps> = ({ onNavigate, onShowSuccess }) => {
  return <ImpactAnalyticsScreen onNavigate={onNavigate} onShowSuccess={onShowSuccess} />;
};

export { ImpactAnalyticsScreen };

// -------------------------------------------------------------
// 2. NOTIFICATIONS SCREEN (PHASE 17 CENTRALIZED HUB)
// -------------------------------------------------------------
import { NotificationsHubScreen } from '@/components/notifications';

export const NotificationsScreen: React.FC<GovernanceProps> = ({ onNavigate, onShowSuccess }) => {
  return <NotificationsHubScreen onNavigate={onNavigate} onShowSuccess={onShowSuccess} />;
};

// -------------------------------------------------------------
// 3. SETTINGS SCREEN
// -------------------------------------------------------------
export const SettingsScreen: React.FC<GovernanceProps> = ({ onShowSuccess }) => {
  const [apiKey, setApiKey] = useState('fl_live_9941a8e2b8344e7c81d89fa31');
  const [copied, setCopied] = useState(false);

  const handleSaveSettings = (e: React.FormEvent) => {
    e.preventDefault();
    onShowSuccess('Enterprise tenant settings successfully updated.');
  };

  const handleCopyKey = () => {
    navigator.clipboard.writeText(apiKey);
    setCopied(true);
    onShowSuccess('API Key copied securely.');
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="glass-panel p-5 rounded-3xl border border-white/10 bg-slate-900 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <Badge variant="purple" size="sm">Tenant Configuration</Badge>
          <h1 className="text-2xl font-black text-white tracking-tight mt-1">Platform Settings & Integrations</h1>
          <p className="text-xs text-slate-400">Configure HACCP tolerances, API webhook endpoints, and RBAC policies</p>
        </div>
      </div>

      <form onSubmit={handleSaveSettings} className="space-y-6">
        {/* Section 1: Facility Profile */}
        <Card>
          <CardHeader>
            <CardTitle>Kitchen / Organization Profile</CardTitle>
            <CardDescription>Primary legal identity for Bill Emerson Act compliance manifests</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input label="Facility Name" defaultValue="Grand Hyatt San Francisco Culinary Center" required />
              <Input label="Responsible Executive Chef" defaultValue="Executive Chef Marcus Vance" required />
              <Input label="Physical Loading Dock Address" defaultValue="345 Stockton St, San Francisco, CA" required />
              <Input label="Cold Chain Dispatch Phone" defaultValue="+1 (415) 398-1234" required />
            </div>
          </CardContent>
        </Card>

        {/* Section 2: HACCP & Safety Limits */}
        <Card>
          <CardHeader>
            <CardTitle>HACCP Critical Control Point Tolerances</CardTitle>
            <CardDescription>Automated alert triggers for probe thermometers and vehicle telemetry</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Input label="Max Chilled Hold Temp (°C)" type="number" defaultValue="4.0" required />
              <Input label="Danger Zone Threshold (°C)" type="number" defaultValue="8.0" required />
              <Input label="Two-Stage Cooling Window (Hours)" type="number" defaultValue="4" required />
            </div>
          </CardContent>
        </Card>

        {/* Section 3: API & Webhooks */}
        <Card>
          <CardHeader>
            <CardTitle>API & Real-Time Webhooks</CardTitle>
            <CardDescription>Connect POS inventory feeds and ERP systems (Micros, Oracle, Toast)</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-300">Live Secret API Key</label>
              <div className="flex items-center space-x-2">
                <input
                  type="password"
                  value={apiKey}
                  readOnly
                  className="flex-1 bg-slate-900 border border-white/10 rounded-xl px-4 py-2 font-mono text-xs text-white"
                />
                <Button type="button" variant="outline" size="sm" onClick={handleCopyKey}>
                  {copied ? 'Copied' : 'Copy'}
                </Button>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setApiKey(`fl_live_${Math.random().toString(36).substring(2, 15)}`);
                    onShowSuccess('New API Secret Key generated.');
                  }}
                >
                  Regenerate
                </Button>
              </div>
            </div>

            <Input
              label="Surplus Broadcast Webhook URL"
              defaultValue="https://api.hyatt-culinary.com/v1/surplus/webhook"
              helperText="Receives POST requests on courier dispatch and delivery verification"
            />
          </CardContent>
        </Card>

        <div className="flex justify-end">
          <Button type="submit" variant="primary" leftIcon={<Save className="w-4 h-4" />}>
            Save All Preferences
          </Button>
        </div>
      </form>
    </div>
  );
};

// -------------------------------------------------------------
// 4. AUDIT LOGS SCREEN
// -------------------------------------------------------------
export const AuditLogsScreen: React.FC<GovernanceProps> = ({ onShowSuccess }) => {
  const [logs, setLogs] = useState<AuditLogEntry[]>(MOCK_AUDIT_LOGS);
  const [filterSeverity, setFilterSeverity] = useState('all');
  const [search, setSearch] = useState('');

  const filtered = logs.filter((l) => {
    const matchesSev = filterSeverity === 'all' || l.severity === filterSeverity;
    const matchesSearch =
      l.action.toLowerCase().includes(search.toLowerCase()) ||
      l.actor.toLowerCase().includes(search.toLowerCase()) ||
      l.entity.toLowerCase().includes(search.toLowerCase());
    return matchesSev && matchesSearch;
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 glass-panel p-5 rounded-3xl border border-white/10 bg-slate-900">
        <div>
          <div className="flex items-center space-x-2">
            <Badge variant="teal" size="sm">Immutable SHA-256 Ledger</Badge>
            <span className="text-xs text-slate-400">Cryptographically Chained</span>
          </div>
          <h1 className="text-2xl font-black text-white tracking-tight mt-1">Platform Audit Trail & Security Logs</h1>
          <p className="text-xs text-slate-400">Tamper-evident logs of all surplus releases, temperature overrides, and courier verifications</p>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={() => onShowSuccess('Audit trail cryptographically verified: Zero tampering detected.')}
          leftIcon={<ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />}
        >
          Verify Cryptographic Hashes
        </Button>
      </div>

      {/* Filter and Search */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 glass-panel p-4 rounded-2xl border border-white/10">
        <div className="flex items-center space-x-2">
          {['all', 'low', 'medium', 'high'].map((sev) => (
            <button
              key={sev}
              onClick={() => setFilterSeverity(sev)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold uppercase tracking-wider transition-all ${
                filterSeverity === sev
                  ? 'bg-emerald-500 text-slate-950 font-bold'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {sev}
            </button>
          ))}
        </div>

        <div className="relative min-w-[260px]">
          <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search action, actor, or entity..."
            className="w-full pl-10 pr-4 py-2 rounded-xl bg-slate-950 border border-white/10 text-white text-xs focus:outline-none focus:border-emerald-500 placeholder:text-slate-500"
          />
        </div>
      </div>

      {/* Logs Table */}
      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left text-slate-300">
              <thead className="text-[11px] uppercase tracking-wider text-slate-400 bg-slate-900/80 border-b border-white/10">
                <tr>
                  <th className="py-3 px-4">Timestamp (UTC)</th>
                  <th className="py-3 px-4">Actor & Role</th>
                  <th className="py-3 px-4">Action Event</th>
                  <th className="py-3 px-4">Entity Reference</th>
                  <th className="py-3 px-4">SHA-256 Hash</th>
                  <th className="py-3 px-4 text-right">Severity</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {filtered.map((log) => (
                  <tr key={log.id} className="hover:bg-white/5">
                    <td className="py-3 px-4 font-mono text-[11px] text-slate-400">{log.timestamp}</td>
                    <td className="py-3 px-4">
                      <div className="font-bold text-white">{log.actor}</div>
                      <div className="text-[10px] text-slate-400">{log.role}</div>
                    </td>
                    <td className="py-3 px-4 font-mono font-bold text-emerald-400">{log.action}</td>
                    <td className="py-3 px-4 text-[11px] text-slate-300">{log.entity}</td>
                    <td className="py-3 px-4 font-mono text-[10px] text-slate-500 truncate max-w-xs" title={log.sha256Hash}>
                      {log.sha256Hash.substring(0, 16)}...
                    </td>
                    <td className="py-3 px-4 text-right">
                      <Badge
                        variant={
                          log.severity === 'low' ? 'neutral' :
                          log.severity === 'medium' ? 'warning' : 'danger'
                        }
                        size="sm"
                      >
                        {log.severity}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
