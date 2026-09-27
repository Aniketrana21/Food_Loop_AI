'use client';

import React from 'react';
import { UserRole } from '@/types';
import { 
  Sparkles, 
  MapPin, 
  PlusCircle, 
  Layers, 
  Truck, 
  BarChart3, 
  ShoppingBag,
  ShieldCheck,
  UserCheck
} from 'lucide-react';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  userRole: UserRole;
  setUserRole: (role: UserRole) => void;
  openDonateModal: () => void;
  openAICoPilot: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  userRole,
  setUserRole,
  openDonateModal,
  openAICoPilot
}) => {
  return (
    <header className="sticky top-0 z-40 w-full border-b border-white/10 glass-panel">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          
          {/* Logo & Platform Name */}
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab('marketplace')}>
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 flex items-center justify-center shadow-lg shadow-emerald-500/25 ring-1 ring-white/20">
              <span className="text-xl font-black text-white tracking-tighter">FL</span>
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-slate-100 to-emerald-300">
                  FoodLoop <span className="text-emerald-400 font-extrabold">AI</span>
                </span>
                <span className="px-2 py-0.5 text-[10px] font-semibold tracking-wider uppercase rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  v1.0 Live
                </span>
              </div>
              <p className="text-[11px] text-slate-400 font-medium hidden sm:block">
                Predictive Surplus Rescue & Autonomous Dispatch
              </p>
            </div>
          </div>

          {/* Center Navigation Tabs */}
          <nav className="hidden md:flex items-center space-x-1 bg-slate-900/60 p-1.5 rounded-xl border border-white/5">
            <button
              id="nav-tab-marketplace"
              onClick={() => setActiveTab('marketplace')}
              className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeTab === 'marketplace'
                  ? 'bg-emerald-500 text-white shadow-md shadow-emerald-500/30'
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <ShoppingBag className="w-3.5 h-3.5" />
              <span>Rescue Feed</span>
            </button>

            <button
              id="nav-tab-map"
              onClick={() => setActiveTab('map')}
              className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeTab === 'map'
                  ? 'bg-emerald-500 text-white shadow-md shadow-emerald-500/30'
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <MapPin className="w-3.5 h-3.5" />
              <span>Live Dispatch Map</span>
            </button>

            <button
              id="nav-tab-optimizer"
              onClick={() => setActiveTab('optimizer')}
              className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeTab === 'optimizer'
                  ? 'bg-emerald-500 text-white shadow-md shadow-emerald-500/30'
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <Truck className="w-3.5 h-3.5" />
              <span>OR-Tools Routing</span>
            </button>

            <button
              id="nav-tab-impact"
              onClick={() => setActiveTab('impact')}
              className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeTab === 'impact'
                  ? 'bg-emerald-500 text-white shadow-md shadow-emerald-500/30'
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <BarChart3 className="w-3.5 h-3.5" />
              <span>Impact Ledger</span>
            </button>
          </nav>

          {/* Right Action Suite: Role Switcher & CTA */}
          <div className="flex items-center space-x-2.5">
            
            {/* Role Switcher Pill */}
            <div className="flex items-center space-x-1.5 bg-slate-900/80 px-2 py-1 rounded-xl border border-white/10 text-xs">
              <UserCheck className="w-3.5 h-3.5 text-emerald-400" />
              <select
                id="role-selector"
                value={userRole}
                onChange={(e) => setUserRole(e.target.value as UserRole)}
                className="bg-transparent text-slate-200 text-xs font-medium focus:outline-none cursor-pointer py-0.5"
              >
                <option value="donor" className="bg-slate-900 text-white">Donor: Hotel / Bakery</option>
                <option value="recipient" className="bg-slate-900 text-white">Recipient: Food Bank / Shelter</option>
                <option value="driver" className="bg-slate-900 text-white">Courier: Volunteer Driver</option>
                <option value="admin" className="bg-slate-900 text-white">Admin: Dispatch Lead</option>
              </select>
            </div>

            {/* AI Co-Pilot Button */}
            <button
              id="btn-ai-copilot"
              onClick={openAICoPilot}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-gradient-to-r from-violet-600/30 to-indigo-600/30 text-indigo-200 border border-indigo-500/30 hover:border-indigo-400 hover:bg-indigo-600/40 transition-all shadow-sm"
              title="AI Food Safety & Recipe Co-Pilot"
            >
              <Sparkles className="w-3.5 h-3.5 text-indigo-400 animate-pulse" />
              <span className="hidden sm:inline">AI Co-Pilot</span>
            </button>

            {/* Quick Donate Modal Trigger (Visible to Donors & Admins) */}
            <button
              id="btn-quick-donate"
              onClick={openDonateModal}
              className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-emerald-500 hover:bg-emerald-400 text-slate-950 shadow-md shadow-emerald-500/25 transition-all active:scale-95"
            >
              <PlusCircle className="w-3.5 h-3.5 stroke-[2.5]" />
              <span className="font-bold">Donate Surplus</span>
            </button>

          </div>
        </div>
      </div>
    </header>
  );
};
