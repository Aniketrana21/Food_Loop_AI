'use client';

import React, { useState } from 'react';
import { 
  Bell, 
  Mail, 
  Smartphone, 
  Moon, 
  Save, 
  Check, 
  AlertTriangle, 
  ShieldCheck, 
  Clock 
} from 'lucide-react';
import { Button } from '@/components/design-system/Button';
import { Badge } from '@/components/design-system/Badge';
import { NotificationPreference } from './types';

interface NotificationPreferencesTabProps {
  preferences: NotificationPreference;
  onSavePreferences: (updated: Partial<NotificationPreference>) => Promise<void>;
  isLoading?: boolean;
}

const CANONICAL_EVENT_ROWS = [
  { key: 'surplus.urgent', label: 'Surplus Urgent Alert', category: 'Food Safety', critical: true },
  { key: 'expiry.approaching', label: 'FEFO Expiry Approaching', category: 'Inventory', critical: false },
  { key: 'recipient.accepted', label: 'Recipient Accepted Donation', category: 'Redistribution', critical: false },
  { key: 'pickup.assigned', label: 'Logistics Courier Assigned', category: 'Dispatch', critical: false },
  { key: 'pickup.delayed', label: 'Pickup Delayed Notice', category: 'Logistics', critical: false },
  { key: 'delivery.completed', label: 'Delivery Completed Confirmation', category: 'Impact', critical: false },
  { key: 'waste.high_detected', label: 'Abnormal Waste Spike (>30%)', category: 'Sustainability', critical: false },
  { key: 'forecast.generated', label: 'AI Demand & Surplus Forecast', category: 'ML Insights', critical: false },
  { key: 'ai.recommendation_generated', label: 'AI Repurposing Recommendation', category: 'Assistant', critical: false },
];

export const NotificationPreferencesTab: React.FC<NotificationPreferencesTabProps> = ({
  preferences,
  onSavePreferences,
  isLoading = false,
}) => {
  const [inApp, setInApp] = useState(preferences.in_app_enabled);
  const [email, setEmail] = useState(preferences.email_enabled);
  const [push, setPush] = useState(preferences.push_enabled);
  const [emailAddress, setEmailAddress] = useState(preferences.email_address || '');
  const [pushToken, setPushToken] = useState(preferences.push_token || '');
  const [quietHoursEnabled, setQuietHoursEnabled] = useState(preferences.quiet_hours_enabled);
  const [quietStart, setQuietStart] = useState(preferences.quiet_hours_start || '22:00');
  const [quietEnd, setQuietEnd] = useState(preferences.quiet_hours_end || '07:00');
  const [eventOverrides, setEventOverrides] = useState<Record<string, Record<string, boolean>>>(
    preferences.event_overrides || {}
  );
  const [savedSuccess, setSavedSuccess] = useState(false);

  const toggleEventChannel = (eventKey: string, channel: string) => {
    setEventOverrides(prev => {
      const currentEvent = prev[eventKey] || { in_app: true, email: true, push: true };
      const currentVal = currentEvent[channel] ?? true;
      return {
        ...prev,
        [eventKey]: {
          ...currentEvent,
          [channel]: !currentVal
        }
      };
    });
  };

  const handleSave = async () => {
    await onSavePreferences({
      in_app_enabled: inApp,
      email_enabled: email,
      push_enabled: push,
      email_address: emailAddress.trim() || null,
      push_token: pushToken.trim() || null,
      quiet_hours_enabled: quietHoursEnabled,
      quiet_hours_start: quietStart,
      quiet_hours_end: quietEnd,
      event_overrides: eventOverrides,
    });
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 3000);
  };

  return (
    <div className="space-y-6">
      {/* Top Banner / Card */}
      <div className="p-5 rounded-3xl glass-panel bg-slate-900 border border-white/10 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <Badge variant="purple" size="sm">Channel Routing</Badge>
            <span className="text-xs text-slate-400">Zero-Waste Operational Broadcasts</span>
          </div>
          <h2 className="text-xl font-black text-white tracking-tight mt-1">Multi-Channel Preferences</h2>
          <p className="text-xs text-slate-400">Configure how and when your kitchen receives critical expiry warnings, dispatch updates, and AI recommendations.</p>
        </div>

        <Button
          variant="primary"
          size="sm"
          onClick={handleSave}
          isLoading={isLoading}
          leftIcon={savedSuccess ? <Check className="w-3.5 h-3.5 text-emerald-300" /> : <Save className="w-3.5 h-3.5" />}
        >
          {savedSuccess ? 'Preferences Saved' : 'Save Preferences'}
        </Button>
      </div>

      {/* Global Channel Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* In-App */}
        <div className={`p-5 rounded-2xl border transition-all ${
          inApp ? 'bg-slate-900/90 border-emerald-500/30' : 'bg-slate-900/40 border-white/5 opacity-75'
        }`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <Bell className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-white">In-App Alerts</h4>
                <p className="text-[11px] text-slate-400">Real-time bell notification feed</p>
              </div>
            </div>
            <button
              onClick={() => setInApp(!inApp)}
              className={`w-11 h-6 flex items-center rounded-full p-1 transition-colors ${
                inApp ? 'bg-emerald-500 justify-end' : 'bg-slate-800 justify-start'
              }`}
            >
              <span className="bg-white w-4 h-4 rounded-full shadow-md transform transition-transform" />
            </button>
          </div>
          <div className="mt-4 pt-3 border-t border-white/5 text-[11px] text-slate-400">
            Enabled across web dashboard, kitchen touchscreens, and processing units.
          </div>
        </div>

        {/* Email */}
        <div className={`p-5 rounded-2xl border transition-all ${
          email ? 'bg-slate-900/90 border-cyan-500/30' : 'bg-slate-900/40 border-white/5 opacity-75'
        }`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2.5 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                <Mail className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-white">Email Delivery</h4>
                <p className="text-[11px] text-slate-400">Summaries & emergency alerts</p>
              </div>
            </div>
            <button
              onClick={() => setEmail(!email)}
              className={`w-11 h-6 flex items-center rounded-full p-1 transition-colors ${
                email ? 'bg-cyan-500 justify-end' : 'bg-slate-800 justify-start'
              }`}
            >
              <span className="bg-white w-4 h-4 rounded-full shadow-md transform transition-transform" />
            </button>
          </div>
          <div className="mt-3">
            <input
              type="email"
              value={emailAddress}
              onChange={(e) => setEmailAddress(e.target.value)}
              placeholder="verified.email@organization.org"
              className="w-full px-3 py-1.5 rounded-xl bg-slate-950 border border-white/10 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
            />
          </div>
        </div>

        {/* Push */}
        <div className={`p-5 rounded-2xl border transition-all ${
          push ? 'bg-slate-900/90 border-purple-500/30' : 'bg-slate-900/40 border-white/5 opacity-75'
        }`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2.5 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20">
                <Smartphone className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-white">Push Notifications</h4>
                <p className="text-[11px] text-slate-400">Mobile & Web Push dispatch</p>
              </div>
            </div>
            <button
              onClick={() => setPush(!push)}
              className={`w-11 h-6 flex items-center rounded-full p-1 transition-colors ${
                push ? 'bg-purple-500 justify-end' : 'bg-slate-800 justify-start'
              }`}
            >
              <span className="bg-white w-4 h-4 rounded-full shadow-md transform transition-transform" />
            </button>
          </div>
          <div className="mt-3">
            <input
              type="text"
              value={pushToken}
              onChange={(e) => setPushToken(e.target.value)}
              placeholder="WebPush / FCM device registration key"
              className="w-full px-3 py-1.5 rounded-xl bg-slate-950 border border-white/10 text-xs text-white placeholder-slate-500 font-mono text-[11px] focus:outline-none focus:border-purple-500/50"
            />
          </div>
        </div>
      </div>

      {/* Quiet Hours Settings */}
      <div className="p-5 rounded-3xl glass-panel bg-slate-900 border border-white/10 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <Moon className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">Quiet Hours Filter</h3>
              <p className="text-xs text-slate-400">Mutes non-critical notifications outside operational kitchen shifts</p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <span className="text-xs font-semibold text-slate-400">
              {quietHoursEnabled ? 'Enabled' : 'Disabled'}
            </span>
            <button
              onClick={() => setQuietHoursEnabled(!quietHoursEnabled)}
              className={`w-11 h-6 flex items-center rounded-full p-1 transition-colors ${
                quietHoursEnabled ? 'bg-indigo-500 justify-end' : 'bg-slate-800 justify-start'
              }`}
            >
              <span className="bg-white w-4 h-4 rounded-full shadow-md transform transition-transform" />
            </button>
          </div>
        </div>

        {quietHoursEnabled && (
          <div className="pt-3 border-t border-white/10 grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="text-[11px] font-semibold text-slate-400 flex items-center gap-1.5 mb-1.5">
                <Clock className="w-3.5 h-3.5 text-indigo-400" />
                Quiet Hours Start Time (24h format)
              </label>
              <input
                type="text"
                value={quietStart}
                onChange={(e) => setQuietStart(e.target.value)}
                placeholder="22:00"
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-white/10 text-xs text-white focus:outline-none focus:border-indigo-500/50"
              />
            </div>
            <div>
              <label className="text-[11px] font-semibold text-slate-400 flex items-center gap-1.5 mb-1.5">
                <Clock className="w-3.5 h-3.5 text-indigo-400" />
                Quiet Hours End Time (24h format)
              </label>
              <input
                type="text"
                value={quietEnd}
                onChange={(e) => setQuietEnd(e.target.value)}
                placeholder="07:00"
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-white/10 text-xs text-white focus:outline-none focus:border-indigo-500/50"
              />
            </div>
          </div>
        )}

        <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 shrink-0 text-amber-400" />
          <span>
            <strong>Safety Mandate:</strong> Critical safety events (such as <code>surplus.urgent</code> and critical FEFO temperature excursions) automatically bypass quiet hours.
          </span>
        </div>
      </div>

      {/* Canonical Event Granular Toggles */}
      <div className="p-5 rounded-3xl glass-panel bg-slate-900 border border-white/10 space-y-4">
        <div>
          <h3 className="text-sm font-bold text-white">Granular Event Subscriptions</h3>
          <p className="text-xs text-slate-400">Opt into specific delivery channels for each of the 10 canonical operational events.</p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-white/10 text-slate-400">
                <th className="py-2.5 px-3">Event Type</th>
                <th className="py-2.5 px-3">Category</th>
                <th className="py-2.5 px-3 text-center">In-App</th>
                <th className="py-2.5 px-3 text-center">Email</th>
                <th className="py-2.5 px-3 text-center">Push</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {CANONICAL_EVENT_ROWS.map((ev) => {
                const override = eventOverrides[ev.key] || { in_app: true, email: true, push: true };
                const isInApp = override.in_app ?? inApp;
                const isEmail = override.email ?? email;
                const isPush = override.push ?? push;

                return (
                  <tr key={ev.key} className="hover:bg-white/[0.02] transition-colors">
                    <td className="py-3 px-3">
                      <div className="font-semibold text-white flex items-center space-x-2">
                        <span>{ev.label}</span>
                        {ev.critical && (
                          <Badge variant="danger" size="sm">CRITICAL</Badge>
                        )}
                      </div>
                      <div className="text-[10px] text-slate-400 font-mono mt-0.5">{ev.key}</div>
                    </td>
                    <td className="py-3 px-3 text-slate-400">
                      <span className="text-[11px] px-2 py-0.5 rounded-md bg-slate-950 border border-white/5">
                        {ev.category}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-center">
                      <input
                        type="checkbox"
                        checked={isInApp}
                        onChange={() => toggleEventChannel(ev.key, 'in_app')}
                        className="rounded border-white/20 bg-slate-900 text-emerald-500 focus:ring-emerald-500"
                      />
                    </td>
                    <td className="py-3 px-3 text-center">
                      <input
                        type="checkbox"
                        checked={isEmail}
                        onChange={() => toggleEventChannel(ev.key, 'email')}
                        className="rounded border-white/20 bg-slate-900 text-cyan-500 focus:ring-cyan-500"
                      />
                    </td>
                    <td className="py-3 px-3 text-center">
                      <input
                        type="checkbox"
                        checked={isPush}
                        onChange={() => toggleEventChannel(ev.key, 'push')}
                        className="rounded border-white/20 bg-slate-900 text-purple-500 focus:ring-purple-500"
                      />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
