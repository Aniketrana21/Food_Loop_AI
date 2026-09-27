'use client';

import React from 'react';
import { 
  Menu, 
  Search, 
  Bell, 
  Sparkles, 
  UserCheck, 
  PlusCircle, 
  AlertTriangle,
  ChevronRight
} from 'lucide-react';
import { Button } from '@/components/design-system/Button';
import { ScreenId, UserRole } from './Sidebar';

interface TopHeaderProps {
  currentScreen: ScreenId;
  userRole: UserRole;
  onRoleChange: (role: UserRole) => void;
  onOpenMobileMenu: () => void;
  onOpenDonateModal: () => void;
  onOpenAICoPilot: () => void;
  onOpenNotifications: () => void;
  unreadCount?: number;
}

export const TopHeader: React.FC<TopHeaderProps> = ({
  currentScreen,
  userRole,
  onRoleChange,
  onOpenMobileMenu,
  onOpenDonateModal,
  onOpenAICoPilot,
  onOpenNotifications,
  unreadCount = 3,
}) => {
  const formatScreenTitle = (screen: ScreenId) => {
    return screen
      .split('_')
      .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
      .join(' ');
  };

  return (
    <header className="sticky top-0 z-30 w-full border-b border-white/10 glass-panel bg-slate-950/80 backdrop-blur-xl">
      <div className="px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
        
        {/* Left: Mobile Trigger & Breadcrumbs */}
        <div className="flex items-center space-x-3">
          <button
            onClick={onOpenMobileMenu}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-white/10 md:hidden"
            aria-label="Open Navigation Drawer"
          >
            <Menu className="w-5 h-5" />
          </button>

          <div className="hidden sm:flex items-center space-x-2 text-xs font-semibold">
            <span className="text-slate-400">FoodLoop AI</span>
            <ChevronRight className="w-3.5 h-3.5 text-slate-600" />
            <span className="text-emerald-400 font-bold">{formatScreenTitle(currentScreen)}</span>
          </div>
        </div>

        {/* Center: Global Search Bar */}
        <div className="hidden lg:flex items-center flex-1 max-w-md mx-4">
          <div className="relative w-full">
            <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              placeholder="Search batches, ingredients, recipes, donation manifests..."
              className="w-full pl-10 pr-4 py-2 rounded-xl bg-slate-900 border border-white/10 text-white text-xs focus:outline-none focus:border-emerald-500 placeholder:text-slate-500 transition-colors"
            />
          </div>
        </div>

        {/* Right Action Suite */}
        <div className="flex items-center space-x-2.5 sm:space-x-3">
          
          {/* Role Switcher Dropdown */}
          <div className="flex items-center space-x-1.5 bg-slate-900 px-2.5 py-1.5 rounded-xl border border-white/10 text-xs">
            <UserCheck className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
            <select
              value={userRole}
              onChange={(e) => onRoleChange(e.target.value as UserRole)}
              className="bg-transparent text-slate-200 text-xs font-semibold focus:outline-none cursor-pointer py-0.5"
            >
              <option value="kitchen_mgr" className="bg-slate-900 text-white">Kitchen Manager</option>
              <option value="super_admin" className="bg-slate-900 text-white">Super Admin</option>
              <option value="fpu_mgr" className="bg-slate-900 text-white">Processing Unit Mgr</option>
              <option value="ngo_lead" className="bg-slate-900 text-white">NGO / Food Bank</option>
              <option value="driver" className="bg-slate-900 text-white">Logistics Courier</option>
              <option value="auditor" className="bg-slate-900 text-white">Authorized Auditor</option>
            </select>
          </div>

          {/* AI Co-Pilot Button */}
          <button
            onClick={onOpenAICoPilot}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-indigo-950/60 hover:bg-indigo-900/60 text-indigo-300 border border-indigo-500/30 transition-all shadow-sm"
          >
            <Sparkles className="w-3.5 h-3.5 text-indigo-400 animate-pulse" />
            <span className="hidden xl:inline">AI Copilot</span>
          </button>

          {/* Notifications Bell */}
          <button
            onClick={onOpenNotifications}
            className="relative p-2 rounded-xl text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
            aria-label="Notifications"
          >
            <Bell className="w-4 h-4" />
            {unreadCount > 0 && (
              <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
            )}
            {unreadCount > 0 && (
              <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-emerald-500" />
            )}
          </button>

          {/* Quick Donate Action (Kitchen & FPU & Admin) */}
          {['kitchen_mgr', 'fpu_mgr', 'super_admin'].includes(userRole) && (
            <Button
              variant="primary"
              size="sm"
              onClick={onOpenDonateModal}
              leftIcon={<PlusCircle className="w-3.5 h-3.5" />}
            >
              <span className="hidden sm:inline">Declare Surplus</span>
            </Button>
          )}

        </div>

      </div>
    </header>
  );
};
