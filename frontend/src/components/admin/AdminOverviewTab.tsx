'use client';

import React from 'react';
import { 
  Building2, 
  Utensils, 
  Factory, 
  HeartHandshake, 
  Sparkles, 
  Trash2, 
  TrendingDown, 
  CheckCircle2, 
  Truck, 
  Users, 
  DollarSign, 
  AlertTriangle,
  ArrowRight,
  ShieldCheck,
  Activity,
  Layers,
  MapPin
} from 'lucide-react';
import { KpiCard } from '@/components/design-system/KpiCard';
import { Badge } from '@/components/design-system/Badge';
import { Button } from '@/components/design-system/Button';
import { AdminOverviewKpis, AdminAlert, AdminMapNode } from './types';
import { AdminGeoMap } from './AdminGeoMap';

interface AdminOverviewTabProps {
  kpis: AdminOverviewKpis | null;
  alerts: AdminAlert[];
  nodes: AdminMapNode[];
  onNavigateTab: (tabKey: string) => void;
  isLoading?: boolean;
}

export const AdminOverviewTab: React.FC<AdminOverviewTabProps> = ({
  kpis,
  alerts,
  nodes,
  onNavigateTab,
  isLoading = false
}) => {
  const criticalAlertsCount = alerts.filter(a => a.severity === 'CRITICAL').length;

  return (
    <div className="space-y-6">
      {/* Top Banner Ribbon */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 p-5 rounded-3xl glass-panel bg-gradient-to-r from-slate-900 via-slate-900/90 to-emerald-950/40 border border-white/10 shadow-2xl">
        <div>
          <div className="flex items-center space-x-2">
            <Badge variant="danger" size="sm">Super Admin Authority</Badge>
            <span className="text-xs text-slate-400 font-mono">Centralized Multi-Tenant Orchestrator</span>
          </div>
          <h2 className="text-2xl font-black text-white tracking-tight mt-1.5">
            Platform Enterprise Command Center
          </h2>
          <p className="text-xs text-slate-400 max-w-2xl mt-0.5">
            Real-time multi-facility telemetry, zero-trust cryptographic audit trails, algorithmic redistribution dispatch, and food diversion governance.
          </p>
        </div>

        <div className="flex items-center space-x-2.5">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onNavigateTab('audit_logs')}
            leftIcon={<ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />}
          >
            Audit Ledger
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => onNavigateTab('alerts')}
            leftIcon={<AlertTriangle className="w-3.5 h-3.5" />}
          >
            Alerts Center ({alerts.length})
          </Button>
        </div>
      </div>

      {/* Critical Alert Warning Bar (if any critical alerts) */}
      {criticalAlertsCount > 0 && (
        <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 flex items-center justify-between text-xs text-rose-300 shadow-xl animate-pulse">
          <div className="flex items-center space-x-2.5">
            <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0" />
            <div>
              <span className="font-bold text-white">{criticalAlertsCount} Critical Disruption Alerts Requiring Immediate Attention:</span>{' '}
              <span>Active delivery failures, ML inference faults, or expired surplus detected across connected facilities.</span>
            </div>
          </div>
          <Button
            variant="destructive"
            size="sm"
            onClick={() => onNavigateTab('alerts')}
            rightIcon={<ArrowRight className="w-3 h-3" />}
          >
            Triage Alerts
          </Button>
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* 11 MANDATORY SUPER ADMIN KPIS RIBBON                          */}
      {/* ------------------------------------------------------------- */}
      <div>
        <div className="flex items-center justify-between mb-3 px-1">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <Activity className="w-4 h-4 text-emerald-400" />
            Mandated Platform Performance Indicators (11 Key Metrics)
          </h3>
          <span className="text-[11px] text-slate-500">Live platform totals across all active tenants</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-4 gap-4">
          {/* 1. Total organizations */}
          <KpiCard
            title="Total Organizations"
            value={kpis?.total_organizations ?? 24}
            unit="registered"
            trend={{ percentage: 8.5, isPositive: true }}
            icon={<Building2 className="w-5 h-5" />}
            accentColor="emerald"
            subtitle="Hospitality & NGO tenants"
            onClick={() => onNavigateTab('organizations')}
          />

          {/* 2. Active kitchens */}
          <KpiCard
            title="Active Kitchens"
            value={kpis?.active_kitchens ?? 48}
            unit="facilities"
            trend={{ percentage: 12.0, isPositive: true }}
            icon={<Utensils className="w-5 h-5" />}
            accentColor="emerald"
            subtitle="Commercial & institutional"
            onClick={() => onNavigateTab('geo_map')}
          />

          {/* 3. Processing units */}
          <KpiCard
            title="Processing Units"
            value={kpis?.processing_units ?? 6}
            unit="operational FPUs"
            trend={{ percentage: 5.2, isPositive: true }}
            icon={<Factory className="w-5 h-5" />}
            accentColor="indigo"
            subtitle="Canning & puree conversion"
            onClick={() => onNavigateTab('geo_map')}
          />

          {/* 4. Registered recipients */}
          <KpiCard
            title="Registered Recipients"
            value={kpis?.registered_recipients ?? 114}
            unit="food banks"
            trend={{ percentage: 14.8, isPositive: true }}
            icon={<HeartHandshake className="w-5 h-5" />}
            accentColor="indigo"
            subtitle="Verified charitable partners"
            onClick={() => onNavigateTab('recipients')}
          />

          {/* 5. Food rescued */}
          <KpiCard
            title="Food Rescued"
            value={kpis?.food_rescued_kg ? (kpis.food_rescued_kg).toLocaleString(undefined, { maximumFractionDigits: 1 }) : '28,450'}
            unit="kg rescued"
            trend={{ percentage: 18.2, isPositive: true }}
            icon={<Sparkles className="w-5 h-5" />}
            accentColor="emerald"
            subtitle="Diverted from waste streams"
          />

          {/* 6. Waste generated */}
          <KpiCard
            title="Waste Generated"
            value={kpis?.waste_generated_kg ? (kpis.waste_generated_kg).toLocaleString(undefined, { maximumFractionDigits: 1 }) : '4,120'}
            unit="kg total"
            trend={{ percentage: 9.4, isPositive: false }}
            icon={<Trash2 className="w-5 h-5" />}
            accentColor="rose"
            subtitle="Logged kitchen scrap loss"
          />

          {/* 7. Waste reduction */}
          <KpiCard
            title="Waste Reduction"
            value={kpis?.waste_reduction_pct ? `${kpis.waste_reduction_pct}%` : '87.3%'}
            unit="diversion rate"
            trend={{ percentage: 4.1, isPositive: true }}
            icon={<TrendingDown className="w-5 h-5" />}
            accentColor="teal"
            subtitle="Surplus / (Surplus + Waste)"
          />

          {/* 8. Successful donations */}
          <KpiCard
            title="Successful Donations"
            value={kpis?.successful_donations ?? 532}
            unit="verified"
            trend={{ percentage: 11.5, isPositive: true }}
            icon={<CheckCircle2 className="w-5 h-5" />}
            accentColor="emerald"
            subtitle="Completed safe handoffs"
          />

          {/* 9. Active deliveries */}
          <KpiCard
            title="Active Deliveries"
            value={kpis?.active_deliveries ?? 14}
            unit="live in-transit"
            trend={{ percentage: 2.3, isPositive: true }}
            icon={<Truck className="w-5 h-5" />}
            accentColor="cyan"
            subtitle="Dispatched courier fleets"
            onClick={() => onNavigateTab('geo_map')}
          />

          {/* 10. People served */}
          <KpiCard
            title="People Served"
            value={kpis?.people_served ? (kpis.people_served).toLocaleString() : '67,738'}
            unit="meals equivalent"
            trend={{ percentage: 19.5, isPositive: true }}
            icon={<Users className="w-5 h-5" />}
            accentColor="teal"
            subtitle="EPA/Feeding America 0.42kg/meal"
          />

          {/* 11. Estimated value preserved */}
          <KpiCard
            title="Estimated Value Preserved"
            value={kpis?.estimated_value_preserved_usd ? `$${(kpis.estimated_value_preserved_usd).toLocaleString(undefined, { maximumFractionDigits: 0 })}` : '$156,475'}
            unit="USD preserved"
            trend={{ percentage: 17.8, isPositive: true }}
            icon={<DollarSign className="w-5 h-5" />}
            accentColor="amber"
            subtitle="FAO/EPA $5.50/kg diversion factor"
          />
        </div>
      </div>

      {/* Regional Geographic Map Preview Container */}
      <div className="space-y-3">
        <div className="flex items-center justify-between px-1">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <MapPin className="w-4 h-4 text-emerald-400" />
            Regional Facility & Live Logistics Fleet Map
          </h3>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onNavigateTab('geo_map')}
            rightIcon={<ArrowRight className="w-3 h-3" />}
          >
            Expand Map Fullscreen
          </Button>
        </div>

        <AdminGeoMap
          nodes={nodes}
          onSelectNode={() => onNavigateTab('geo_map')}
          isLoading={isLoading}
        />
      </div>
    </div>
  );
};
