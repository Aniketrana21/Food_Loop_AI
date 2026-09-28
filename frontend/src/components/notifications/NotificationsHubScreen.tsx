'use client';

import React, { useState, useEffect } from 'react';
import { 
  Bell, 
  Settings, 
  FileText, 
  Send, 
  CheckCircle2, 
  RotateCcw, 
  AlertTriangle,
  Clock,
  Sparkles,
  Inbox
} from 'lucide-react';
import { Button } from '@/components/design-system/Button';
import { Badge } from '@/components/design-system/Badge';
import { NotificationPreferencesTab } from './NotificationPreferencesTab';
import { NotificationTemplatesTab } from './NotificationTemplatesTab';
import { NotificationOutboxTab } from './NotificationOutboxTab';
import { 
  NotificationPreference, 
  NotificationTemplate, 
  NotificationEvent, 
  NotificationDeliveryStats 
} from './types';
import { MOCK_NOTIFICATIONS, NotificationItem } from '@/lib/mockData';

interface NotificationsHubScreenProps {
  onNavigate?: (screen: any) => void;
  onShowSuccess?: (msg: string) => void;
}

export const NotificationsHubScreen: React.FC<NotificationsHubScreenProps> = ({
  onNavigate,
  onShowSuccess,
}) => {
  const [activeTab, setActiveTab] = useState<'feed' | 'preferences' | 'templates' | 'outbox'>('feed');
  const [inAppFeed, setInAppFeed] = useState<NotificationItem[]>(MOCK_NOTIFICATIONS);
  const [feedCategory, setFeedCategory] = useState<string>('all');
  
  // State for Preferences
  const [preferences, setPreferences] = useState<NotificationPreference>({
    id: 'pref-default-01',
    user_id: 'user-001',
    in_app_enabled: true,
    email_enabled: true,
    push_enabled: true,
    email_address: 'kitchen.manager@foodloop.ai',
    push_token: 'webpush_active_sample_token_8899',
    quiet_hours_enabled: false,
    quiet_hours_start: '22:00',
    quiet_hours_end: '07:00',
    event_overrides: {
      'surplus.urgent': { email: true, push: true, in_app: true },
      'waste.high_detected': { email: true, push: true, in_app: true }
    },
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  });

  // State for Templates
  const [templates, setTemplates] = useState<NotificationTemplate[]>([]);
  // State for Events & Stats
  const [events, setEvents] = useState<NotificationEvent[]>([]);
  const [stats, setStats] = useState<NotificationDeliveryStats | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Fetch live templates, events, preferences from API
  const fetchData = async () => {
    setIsLoading(true);
    try {
      // 1. Fetch templates
      const resTmpl = await fetch('/api/v1/notifications/templates');
      if (resTmpl.ok) {
        const data = await resTmpl.json();
        setTemplates(data);
      }

      // 2. Fetch preferences
      const resPref = await fetch('/api/v1/notifications/preferences');
      if (resPref.ok) {
        const data = await resPref.json();
        setPreferences(data);
      }

      // 3. Fetch events outbox
      const resEvents = await fetch('/api/v1/notifications/events');
      if (resEvents.ok) {
        const data = await resEvents.json();
        setEvents(data);
      }

      // 4. Fetch stats
      const resStats = await fetch('/api/v1/notifications/stats');
      if (resStats.ok) {
        const data = await resStats.json();
        setStats(data);
      }
    } catch (e) {
      console.warn('Using local state for notifications hub:', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSavePreferences = async (updated: Partial<NotificationPreference>) => {
    try {
      const res = await fetch('/api/v1/notifications/preferences', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updated)
      });
      if (res.ok) {
        const data = await res.json();
        setPreferences(data);
        if (onShowSuccess) onShowSuccess('Notification preferences updated successfully.');
      } else {
        setPreferences(prev => ({ ...prev, ...updated }));
        if (onShowSuccess) onShowSuccess('Preferences updated locally.');
      }
    } catch {
      setPreferences(prev => ({ ...prev, ...updated }));
      if (onShowSuccess) onShowSuccess('Preferences saved locally.');
    }
  };

  const handleTestRender = async (eventType: string, payload: Record<string, any>) => {
    const res = await fetch('/api/v1/notifications/templates/test-render', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ event_type: eventType, payload })
    });
    if (res.ok) {
      return await res.json();
    }
    throw new Error('Test render request failed.');
  };

  const handleRetrySingle = async (eventId: string) => {
    const res = await fetch(`/api/v1/notifications/events/${eventId}/retry`, {
      method: 'POST'
    });
    if (res.ok) {
      if (onShowSuccess) onShowSuccess(`Event #${eventId.slice(0, 8)} successfully retried.`);
      fetchData();
    }
  };

  const handleBatchRetry = async () => {
    const res = await fetch('/api/v1/notifications/events/retry-failed?limit=25', {
      method: 'POST'
    });
    if (res.ok) {
      const data = await res.json();
      if (onShowSuccess) onShowSuccess(`Batch retry completed: ${data.succeeded_count} succeeded, ${data.failed_count} failed.`);
      fetchData();
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await fetch('/api/v1/notifications/read-all', { method: 'PATCH' });
    } catch {}
    setInAppFeed(prev => prev.map(n => ({ ...n, read: true })));
    if (onShowSuccess) onShowSuccess('All notifications marked as read.');
  };

  const filteredFeed = inAppFeed.filter(item => {
    if (feedCategory === 'all') return true;
    return item.category === feedCategory;
  });

  return (
    <div className="space-y-6">
      {/* Top Header Card */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 glass-panel p-5 rounded-3xl border border-white/10 bg-slate-900">
        <div>
          <div className="flex items-center space-x-2">
            <Badge variant="purple" size="sm">Notification Center</Badge>
            <span className="text-xs text-slate-400">Phase 17 Multi-Channel Alerting Hub</span>
          </div>
          <h1 className="text-2xl font-black text-white tracking-tight mt-1">Notifications & Dispatch Core</h1>
          <p className="text-xs text-slate-400">
            Multi-channel notifications (In-App, Email, Push), 10 canonical event templates, deduplication, and retry automation.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          {activeTab === 'feed' && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleMarkAllRead}
              leftIcon={<CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />}
            >
              Mark All Read
            </Button>
          )}
        </div>
      </div>

      {/* Main Tab Switcher */}
      <div className="flex items-center space-x-2 border-b border-white/10 pb-3">
        <button
          onClick={() => setActiveTab('feed')}
          className={`flex items-center space-x-2 px-4 py-2 rounded-2xl text-xs font-bold transition-all ${
            activeTab === 'feed'
              ? 'bg-emerald-500 text-slate-950 shadow-lg font-black'
              : 'glass-panel text-slate-400 hover:text-white border border-white/5'
          }`}
        >
          <Bell className="w-4 h-4" />
          <span>In-App Feed ({inAppFeed.filter(n => !n.read).length})</span>
        </button>

        <button
          onClick={() => setActiveTab('preferences')}
          className={`flex items-center space-x-2 px-4 py-2 rounded-2xl text-xs font-bold transition-all ${
            activeTab === 'preferences'
              ? 'bg-cyan-500 text-slate-950 shadow-lg font-black'
              : 'glass-panel text-slate-400 hover:text-white border border-white/5'
          }`}
        >
          <Settings className="w-4 h-4" />
          <span>Preferences & Quiet Hours</span>
        </button>

        <button
          onClick={() => setActiveTab('templates')}
          className={`flex items-center space-x-2 px-4 py-2 rounded-2xl text-xs font-bold transition-all ${
            activeTab === 'templates'
              ? 'bg-purple-500 text-white shadow-lg font-black'
              : 'glass-panel text-slate-400 hover:text-white border border-white/5'
          }`}
        >
          <FileText className="w-4 h-4" />
          <span>Event Templates (10)</span>
        </button>

        <button
          onClick={() => setActiveTab('outbox')}
          className={`flex items-center space-x-2 px-4 py-2 rounded-2xl text-xs font-bold transition-all ${
            activeTab === 'outbox'
              ? 'bg-indigo-500 text-white shadow-lg font-black'
              : 'glass-panel text-slate-400 hover:text-white border border-white/5'
          }`}
        >
          <Send className="w-4 h-4" />
          <span>Outbox & Retries ({events.length})</span>
        </button>
      </div>

      {/* Tab Contents */}
      {activeTab === 'feed' && (
        <div className="space-y-4">
          {/* Feed Filter Tags */}
          <div className="flex items-center space-x-2 overflow-x-auto pb-1">
            {['all', 'urgent', 'logistics', 'production', 'audit'].map((cat) => (
              <button
                key={cat}
                onClick={() => setFeedCategory(cat)}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold uppercase tracking-wider transition-all ${
                  feedCategory === cat
                    ? 'bg-emerald-500 text-slate-950 font-bold'
                    : 'glass-panel text-slate-400 hover:text-white border border-white/5'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>

          {/* Feed Items */}
          <div className="space-y-3">
            {filteredFeed.length === 0 ? (
              <div className="p-12 text-center rounded-3xl glass-panel bg-slate-900 border border-white/10 text-slate-400">
                <Inbox className="w-10 h-10 mx-auto text-slate-600 mb-2" />
                <h4 className="text-white font-bold text-sm">No Active Notifications</h4>
                <p className="text-xs text-slate-500 mt-0.5">Your kitchen and facility inbox is completely up to date.</p>
              </div>
            ) : (
              filteredFeed.map((item) => (
                <div
                  key={item.id}
                  onClick={() => {
                    if (item.actionTarget && onNavigate) onNavigate(item.actionTarget);
                  }}
                  className={`p-4 rounded-2xl border transition-all flex items-start justify-between gap-4 cursor-pointer ${
                    item.read
                      ? 'bg-slate-900/60 border-white/5 hover:border-white/10'
                      : 'bg-slate-900 border-emerald-500/30 hover:border-emerald-500/50 shadow-md'
                  }`}
                >
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      {!item.read && <span className="w-2 h-2 rounded-full bg-emerald-400 shrink-0" />}
                      <span className="font-bold text-xs sm:text-sm text-white">{item.title}</span>
                      <Badge
                        variant={item.category === 'urgent' ? 'danger' : item.category === 'logistics' ? 'cyan' : 'neutral'}
                        size="sm"
                      >
                        {item.category}
                      </Badge>
                    </div>
                    <p className="text-xs text-slate-400 leading-relaxed">{item.message}</p>
                    <span className="text-[10px] text-slate-500">{item.timestamp}</span>
                  </div>

                  {item.actionTarget && (
                    <Button variant="outline" size="sm" className="shrink-0 self-center">
                      View Action
                    </Button>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {activeTab === 'preferences' && (
        <NotificationPreferencesTab
          preferences={preferences}
          onSavePreferences={handleSavePreferences}
          isLoading={isLoading}
        />
      )}

      {activeTab === 'templates' && (
        <NotificationTemplatesTab
          templates={templates}
          onTestRender={handleTestRender}
        />
      )}

      {activeTab === 'outbox' && (
        <NotificationOutboxTab
          events={events}
          stats={stats}
          onRetryEvent={handleRetrySingle}
          onBatchRetry={handleBatchRetry}
          onRefresh={fetchData}
          isLoading={isLoading}
        />
      )}
    </div>
  );
};
