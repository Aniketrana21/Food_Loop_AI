'use client';

import React from 'react';
import { 
  LayoutDashboard, 
  TrendingUp, 
  CalendarClock, 
  Package, 
  Trash2, 
  Share2, 
  Users, 
  HeartHandshake, 
  Truck, 
  BarChart3, 
  Sparkles, 
  Bell, 
  Settings, 
  ShieldCheck, 
  BookOpen, 
  QrCode, 
  FileText,
  ChevronLeft,
  ChevronRight,
  LogOut,
  Building2,
  UtensilsCrossed,
  Camera,
  X
} from 'lucide-react';
import { Badge } from '@/components/design-system/Badge';

export type ScreenId =
  | 'kitchen_dashboard'
  | 'kitchen_profile'
  | 'admin_dashboard'
  | 'processing_dashboard'
  | 'ngo_dashboard'
  | 'driver_dashboard'
  | 'inventory'
  | 'menu_management'
  | 'production_planning'
  | 'consumption'
  | 'waste_reporting'
  | 'computer_vision'
  | 'ai_forecast'
  | 'production_optimizer'
  | 'surplus_marketplace'
  | 'recipient_matching'
  | 'donation_details'
  | 'map_logistics'
  | 'qr_verification'
  | 'impact_dashboard'
  | 'ai_assistant'
  | 'rag_knowledge'
  | 'notifications'
  | 'settings'
  | 'audit_logs'
  | 'login'
  | 'register'
  | 'org_setup';

export type UserRole =
  | 'super_admin'
  | 'kitchen_mgr'
  | 'fpu_mgr'
  | 'ngo_lead'
  | 'driver'
  | 'auditor';

interface NavItem {
  id: ScreenId;
  label: string;
  icon: React.ReactNode;
  badge?: string;
  allowedRoles?: UserRole[];
  group: 'Operations' | 'Intelligence & Forecasting' | 'Redistribution & Logistics' | 'Governance & System';
}

const NAV_ITEMS: NavItem[] = [
  // Operations Group
  {
    id: 'kitchen_dashboard',
    label: 'Dashboard',
    icon: <LayoutDashboard className="w-4 h-4" />,
    allowedRoles: ['kitchen_mgr'],
    group: 'Operations',
  },
  {
    id: 'kitchen_profile',
    label: 'Kitchen & Staff',
    icon: <UtensilsCrossed className="w-4 h-4" />,
    allowedRoles: ['kitchen_mgr', 'super_admin'],
    group: 'Operations',
  },
  {
    id: 'admin_dashboard',
    label: 'Admin Overview',
    icon: <LayoutDashboard className="w-4 h-4" />,
    allowedRoles: ['super_admin'],
    group: 'Operations',
  },
  {
    id: 'processing_dashboard',
    label: 'FPU Processing Plant',
    icon: <Building2 className="w-4 h-4" />,
    allowedRoles: ['fpu_mgr', 'super_admin', 'kitchen_mgr'],
    group: 'Operations',
  },
  {
    id: 'ngo_dashboard',
    label: 'NGO Portal',
    icon: <LayoutDashboard className="w-4 h-4" />,
    allowedRoles: ['ngo_lead'],
    group: 'Operations',
  },
  {
    id: 'driver_dashboard',
    label: 'Courier Hub',
    icon: <Truck className="w-4 h-4" />,
    allowedRoles: ['driver'],
    group: 'Operations',
  },
  {
    id: 'inventory',
    label: 'Inventory',
    icon: <Package className="w-4 h-4" />,
    badge: '12 Low',
    allowedRoles: ['kitchen_mgr', 'fpu_mgr', 'super_admin', 'auditor'],
    group: 'Operations',
  },
  {
    id: 'menu_management',
    label: 'Menu Planning',
    icon: <CalendarClock className="w-4 h-4" />,
    allowedRoles: ['kitchen_mgr', 'super_admin'],
    group: 'Operations',
  },
  {
    id: 'production_planning',
    label: 'Production Batches',
    icon: <Building2 className="w-4 h-4" />,
    allowedRoles: ['kitchen_mgr', 'fpu_mgr', 'super_admin'],
    group: 'Operations',
  },
  {
    id: 'consumption',
    label: 'Consumption',
    icon: <Users className="w-4 h-4" />,
    allowedRoles: ['kitchen_mgr', 'super_admin', 'auditor'],
    group: 'Operations',
  },
  {
    id: 'waste_reporting',
    label: 'Waste Reporting',
    icon: <Trash2 className="w-4 h-4" />,
    allowedRoles: ['kitchen_mgr', 'fpu_mgr', 'super_admin', 'auditor'],
    group: 'Operations',
  },
  {
    id: 'computer_vision',
    label: 'Vision Food Scanner',
    icon: <Camera className="w-4 h-4 text-amber-400" />,
    badge: 'AI Vision',
    allowedRoles: ['kitchen_mgr', 'fpu_mgr', 'super_admin', 'auditor'],
    group: 'Operations',
  },

  // Intelligence & Forecasting Group
  {
    id: 'ai_forecast',
    label: 'AI Demand Forecast',
    icon: <TrendingUp className="w-4 h-4" />,
    badge: 'XGBoost',
    allowedRoles: ['kitchen_mgr', 'fpu_mgr', 'super_admin', 'auditor'],
    group: 'Intelligence & Forecasting',
  },
  {
    id: 'production_optimizer',
    label: 'Production Optimizer',
    icon: <Sparkles className="w-4 h-4 text-emerald-400" />,
    badge: 'OR-Tools',
    allowedRoles: ['kitchen_mgr', 'fpu_mgr', 'super_admin'],
    group: 'Intelligence & Forecasting',
  },
  {
    id: 'ai_assistant',
    label: 'AI Assistant & Copilot',
    icon: <Sparkles className="w-4 h-4 text-indigo-400" />,
    allowedRoles: ['kitchen_mgr', 'fpu_mgr', 'ngo_lead', 'super_admin', 'auditor'],
    group: 'Intelligence & Forecasting',
  },
  {
    id: 'rag_knowledge',
    label: 'RAG Knowledge Center',
    icon: <BookOpen className="w-4 h-4" />,
    allowedRoles: ['kitchen_mgr', 'fpu_mgr', 'ngo_lead', 'driver', 'super_admin', 'auditor'],
    group: 'Intelligence & Forecasting',
  },

  // Redistribution & Logistics Group
  {
    id: 'surplus_marketplace',
    label: 'Surplus Marketplace',
    icon: <Share2 className="w-4 h-4" />,
    badge: 'Active',
    allowedRoles: ['kitchen_mgr', 'fpu_mgr', 'ngo_lead', 'super_admin'],
    group: 'Redistribution & Logistics',
  },
  {
    id: 'recipient_matching',
    label: 'Recipient Matching',
    icon: <HeartHandshake className="w-4 h-4" />,
    allowedRoles: ['kitchen_mgr', 'fpu_mgr', 'ngo_lead', 'super_admin'],
    group: 'Redistribution & Logistics',
  },
  {
    id: 'donation_details',
    label: 'Donation Manifests',
    icon: <FileText className="w-4 h-4" />,
    allowedRoles: ['kitchen_mgr', 'fpu_mgr', 'ngo_lead', 'super_admin', 'auditor'],
    group: 'Redistribution & Logistics',
  },
  {
    id: 'map_logistics',
    label: 'Logistics & Maps',
    icon: <Truck className="w-4 h-4" />,
    allowedRoles: ['kitchen_mgr', 'fpu_mgr', 'ngo_lead', 'driver', 'super_admin', 'auditor'],
    group: 'Redistribution & Logistics',
  },
  {
    id: 'qr_verification',
    label: 'QR Handover Scan',
    icon: <QrCode className="w-4 h-4" />,
    badge: 'HMAC',
    allowedRoles: ['kitchen_mgr', 'fpu_mgr', 'ngo_lead', 'driver', 'super_admin'],
    group: 'Redistribution & Logistics',
  },

  // Governance & System Group
  {
    id: 'impact_dashboard',
    label: 'Impact Analytics',
    icon: <BarChart3 className="w-4 h-4" />,
    allowedRoles: ['kitchen_mgr', 'fpu_mgr', 'ngo_lead', 'super_admin', 'auditor'],
    group: 'Governance & System',
  },
  {
    id: 'audit_logs',
    label: 'Audit Logs',
    icon: <ShieldCheck className="w-4 h-4" />,
    allowedRoles: ['super_admin', 'auditor'],
    group: 'Governance & System',
  },
  {
    id: 'notifications',
    label: 'Notifications',
    icon: <Bell className="w-4 h-4" />,
    badge: '3',
    allowedRoles: ['kitchen_mgr', 'fpu_mgr', 'ngo_lead', 'driver', 'super_admin', 'auditor'],
    group: 'Governance & System',
  },
  {
    id: 'settings',
    label: 'Settings',
    icon: <Settings className="w-4 h-4" />,
    allowedRoles: ['kitchen_mgr', 'fpu_mgr', 'ngo_lead', 'driver', 'super_admin', 'auditor'],
    group: 'Governance & System',
  },
];

interface SidebarProps {
  currentScreen: ScreenId;
  onNavigate: (screen: ScreenId) => void;
  userRole: UserRole;
  isMobileOpen: boolean;
  onCloseMobile: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentScreen,
  onNavigate,
  userRole,
  isMobileOpen,
  onCloseMobile,
}) => {
  const [collapsed, setCollapsed] = React.useState(false);

  // Filter items by role
  const visibleItems = NAV_ITEMS.filter(
    (item) => !item.allowedRoles || item.allowedRoles.includes(userRole)
  );

  const groups = ['Operations', 'Intelligence & Forecasting', 'Redistribution & Logistics', 'Governance & System'] as const;

  const roleLabels: Record<UserRole, { title: string; color: string }> = {
    kitchen_mgr: { title: 'Kitchen Manager', color: 'emerald' },
    super_admin: { title: 'Super Admin', color: 'rose' },
    fpu_mgr: { title: 'FPU Plant Manager', color: 'amber' },
    ngo_lead: { title: 'NGO / Food Bank', color: 'indigo' },
    driver: { title: 'Logistics Courier', color: 'cyan' },
    auditor: { title: 'Safety Auditor', color: 'teal' },
  };

  const content = (
    <div className="flex flex-col h-full bg-[#0a0f1d] border-r border-white/10 select-none">
      
      {/* Brand Header */}
      <div className="p-4 border-b border-white/10 flex items-center justify-between">
        <div
          className="flex items-center space-x-3 cursor-pointer"
          onClick={() => {
            const defaultScreen = userRole === 'super_admin' ? 'admin_dashboard' :
                                  userRole === 'fpu_mgr' ? 'processing_dashboard' :
                                  userRole === 'ngo_lead' ? 'ngo_dashboard' :
                                  userRole === 'driver' ? 'driver_dashboard' : 'kitchen_dashboard';
            onNavigate(defaultScreen);
          }}
        >
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 flex items-center justify-center shadow-lg shadow-emerald-500/25 ring-1 ring-white/20 shrink-0">
            <span className="text-base font-black text-white tracking-tighter">FL</span>
          </div>
          {!collapsed && (
            <div>
              <div className="flex items-center space-x-1.5">
                <span className="text-base font-bold text-white tracking-tight">FoodLoop</span>
                <span className="text-xs font-black text-emerald-400 bg-emerald-500/10 px-1 py-0.2 rounded border border-emerald-500/20">
                  AI
                </span>
              </div>
              <p className="text-[10px] text-slate-400 font-medium">Enterprise Sustainability</p>
            </div>
          )}
        </div>

        {/* Mobile Close Button */}
        <button
          onClick={onCloseMobile}
          className="p-1 rounded-lg text-slate-400 hover:text-white md:hidden"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Role Pill Strip */}
      {!collapsed && (
        <div className="px-4 py-2 bg-slate-900/60 border-b border-white/5 flex items-center justify-between text-xs">
          <span className="text-[11px] text-slate-400">Context:</span>
          <Badge variant="purple" size="sm">
            {roleLabels[userRole].title}
          </Badge>
        </div>
      )}

      {/* Navigation Group Sections */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-5">
        {groups.map((group) => {
          const groupItems = visibleItems.filter((item) => item.group === group);
          if (groupItems.length === 0) return null;

          return (
            <div key={group} className="space-y-1">
              {!collapsed && (
                <div className="px-2.5 pb-1 text-[10px] font-bold uppercase tracking-wider text-slate-500">
                  {group}
                </div>
              )}
              {groupItems.map((item) => {
                const isActive = currentScreen === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => {
                      onNavigate(item.id);
                      onCloseMobile();
                    }}
                    title={collapsed ? item.label : undefined}
                    className={`w-full flex items-center ${
                      collapsed ? 'justify-center px-2' : 'justify-between px-3'
                    } py-2 rounded-xl text-xs font-medium transition-all duration-150 ${
                      isActive
                        ? 'bg-emerald-500 text-slate-950 font-bold shadow-md shadow-emerald-500/20'
                        : 'text-slate-400 hover:text-white hover:bg-white/5'
                    }`}
                  >
                    <div className="flex items-center space-x-2.5 truncate">
                      <span className={isActive ? 'text-slate-950' : 'text-slate-400'}>{item.icon}</span>
                      {!collapsed && <span className="truncate">{item.label}</span>}
                    </div>

                    {!collapsed && item.badge && (
                      <span
                        className={`text-[9px] font-bold px-1.5 py-0.5 rounded-full ${
                          isActive
                            ? 'bg-slate-950/20 text-slate-950 font-black'
                            : 'bg-slate-800 text-slate-300 border border-white/5'
                        }`}
                      >
                        {item.badge}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          );
        })}
      </div>

      {/* Footer Profile & Collapse Toggle */}
      <div className="p-3 border-t border-white/10 bg-slate-950/70 space-y-2">
        {!collapsed && (
          <div className="flex items-center justify-between p-2 rounded-xl bg-slate-900 border border-white/5 text-xs">
            <div className="flex items-center space-x-2 truncate">
              <div className="w-7 h-7 rounded-lg bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 flex items-center justify-center font-bold text-[11px] shrink-0">
                {userRole.charAt(0).toUpperCase()}
              </div>
              <div className="truncate">
                <p className="font-bold text-white truncate text-[11px] leading-tight">Chef Operations</p>
                <p className="text-[10px] text-slate-400 truncate">Grand Hyatt Culinary</p>
              </div>
            </div>
            <button
              onClick={() => onNavigate('login')}
              title="Sign Out"
              className="p-1 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-white/5 transition-colors"
            >
              <LogOut className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        {/* Desktop Collapse Button */}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="w-full hidden md:flex items-center justify-center py-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 text-xs transition-colors"
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4 mr-1.5" />}
          {!collapsed && <span className="text-[11px]">Collapse View</span>}
        </button>
      </div>

    </div>
  );

  return (
    <>
      {/* Desktop Persistent Sidebar */}
      <aside
        className={`hidden md:block shrink-0 transition-all duration-300 h-screen sticky top-0 ${
          collapsed ? 'w-20' : 'w-64'
        }`}
      >
        {content}
      </aside>

      {/* Mobile Drawer Backdrop */}
      {isMobileOpen && (
        <div
          className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm md:hidden animate-fade-in"
          onClick={onCloseMobile}
        >
          <div
            className="w-72 h-full bg-[#0a0f1d]"
            onClick={(e) => e.stopPropagation()}
          >
            {content}
          </div>
        </div>
      )}
    </>
  );
};
