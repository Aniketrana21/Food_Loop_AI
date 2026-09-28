'use client';

import React, { useState } from 'react';
import { 
  Send, 
  RotateCcw, 
  CheckCircle, 
  AlertTriangle, 
  XCircle, 
  Copy, 
  Clock, 
  Layers, 
  RefreshCw,
  Search,
  Filter
} from 'lucide-react';
import { Button } from '@/components/design-system/Button';
import { Badge } from '@/components/design-system/Badge';
import { Modal } from '@/components/design-system/Modal';
import { NotificationEvent, NotificationDeliveryStats } from './types';

interface NotificationOutboxTabProps {
  events: NotificationEvent[];
  stats?: NotificationDeliveryStats | null;
  onRetryEvent: (eventId: string) => Promise<void>;
  onBatchRetry: () => Promise<void>;
  onRefresh: () => Promise<void>;
  isLoading?: boolean;
}

export const NotificationOutboxTab: React.FC<NotificationOutboxTabProps> = ({
  events,
  stats,
  onRetryEvent,
  onBatchRetry,
  onRefresh,
  isLoading = false,
}) => {
  const [selectedEvent, setSelectedEvent] = useState<NotificationEvent | null>(null);
  const [inspectModalOpen, setInspectModalOpen] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [retryingId, setRetryingId] = useState<string | null>(null);
  const [batchRetrying, setBatchRetrying] = useState(false);

  const filteredEvents = events.filter(ev => {
    if (statusFilter !== 'ALL' && ev.status !== statusFilter) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchType = ev.event_type.toLowerCase().includes(q);
      const matchTitle = (ev.rendered_title || '').toLowerCase().includes(q);
      const matchKey = (ev.idempotency_key || '').toLowerCase().includes(q);
      if (!matchType && !matchTitle && !matchKey) return false;
    }
    return true;
  });

  const handleRetrySingle = async (ev: NotificationEvent) => {
    setRetryingId(ev.id);
    try {
      await onRetryEvent(ev.id);
    } finally {
      setRetryingId(null);
    }
  };

  const handleBatchRetryAll = async () => {
    setBatchRetrying(true);
    try {
      await onBatchRetry();
    } finally {
      setBatchRetrying(false);
    }
  };

  const retryableCount = events.filter(e => e.status === 'RETRYING' || e.status === 'FAILED').length;

  return (
    <div className="space-y-6">
      {/* Metrics Ribbon */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="p-4 rounded-2xl glass-panel bg-slate-900 border border-white/10">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Total Dispatches</span>
            <div className="text-2xl font-black text-white mt-1">{stats.total_events}</div>
            <span className="text-[10px] text-slate-500">Across all 3 channels</span>
          </div>

          <div className="p-4 rounded-2xl glass-panel bg-slate-900 border border-emerald-500/20">
            <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-400">Delivery Success Rate</span>
            <div className="text-2xl font-black text-emerald-400 mt-1">{stats.success_rate_pct}%</div>
            <span className="text-[10px] text-slate-500">{stats.delivered_events} confirmed deliveries</span>
          </div>

          <div className="p-4 rounded-2xl glass-panel bg-slate-900 border border-amber-500/20">
            <span className="text-[10px] font-bold uppercase tracking-wider text-amber-400">Deduplicated</span>
            <div className="text-2xl font-black text-amber-400 mt-1">{stats.deduplicated_events}</div>
            <span className="text-[10px] text-slate-500">Spam duplicate alerts suppressed</span>
          </div>

          <div className="p-4 rounded-2xl glass-panel bg-slate-900 border border-indigo-500/20">
            <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-400">Quiet Hours Muted</span>
            <div className="text-2xl font-black text-indigo-400 mt-1">{stats.suppressed_quiet_hours}</div>
            <span className="text-[10px] text-slate-500">Scheduled during shift rest</span>
          </div>
        </div>
      )}

      {/* Control Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 glass-panel p-4 rounded-3xl border border-white/10 bg-slate-900">
        <div className="flex items-center space-x-2 flex-1 max-w-md">
          <div className="relative w-full">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search event type, title, or idempotency key..."
              className="w-full pl-9 pr-3 py-1.5 rounded-xl bg-slate-950 border border-white/10 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
            />
          </div>
        </div>

        <div className="flex items-center space-x-2 overflow-x-auto pb-1 sm:pb-0">
          <Button
            variant="outline"
            size="sm"
            onClick={onRefresh}
            isLoading={isLoading}
            leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
          >
            Sync
          </Button>

          {retryableCount > 0 && (
            <Button
              variant="ai"
              size="sm"
              onClick={handleBatchRetryAll}
              isLoading={batchRetrying}
              leftIcon={<RotateCcw className="w-3.5 h-3.5" />}
            >
              Retry Failed ({retryableCount})
            </Button>
          )}
        </div>
      </div>

      {/* Status Filter Badges */}
      <div className="flex items-center space-x-2 overflow-x-auto pb-1">
        {['ALL', 'DELIVERED', 'RETRYING', 'FAILED', 'DEDUPLICATED', 'SUPPRESSED_QUIET_HOURS'].map((st) => (
          <button
            key={st}
            onClick={() => setStatusFilter(st)}
            className={`px-3 py-1 rounded-xl text-[11px] font-bold uppercase tracking-wider transition-all ${
              statusFilter === st
                ? 'bg-cyan-500 text-slate-950 shadow-md'
                : 'glass-panel text-slate-400 hover:text-white border border-white/5'
            }`}
          >
            {st.replace('_', ' ')}
          </button>
        ))}
      </div>

      {/* Event Outbox Table */}
      <div className="rounded-3xl glass-panel bg-slate-900 border border-white/10 overflow-hidden shadow-2xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-white/10 text-slate-400 bg-slate-950/40">
                <th className="py-3 px-4">Event Type & Title</th>
                <th className="py-3 px-4">Channels</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Attempts</th>
                <th className="py-3 px-4">Created Time</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {filteredEvents.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-500">
                    No notification events matching current filter
                  </td>
                </tr>
              ) : (
                filteredEvents.map((ev) => {
                  const isRetryable = ev.status === 'RETRYING' || ev.status === 'FAILED';

                  return (
                    <tr key={ev.id} className="hover:bg-white/[0.02] transition-colors">
                      <td className="py-3.5 px-4">
                        <div className="font-bold text-white tracking-tight flex items-center space-x-2">
                          <span>{ev.rendered_title || ev.event_type}</span>
                        </div>
                        <div className="flex items-center space-x-2 text-[10px] text-slate-400 font-mono mt-0.5">
                          <span className="text-cyan-400">{ev.event_type}</span>
                          {ev.idempotency_key && (
                            <span className="text-slate-500">
                              • key: {ev.idempotency_key.slice(0, 10)}...
                            </span>
                          )}
                        </div>
                      </td>

                      <td className="py-3.5 px-4">
                        <div className="flex items-center gap-1">
                          {ev.channels.map((ch) => (
                            <span
                              key={ch}
                              className={`text-[9px] uppercase px-1.5 py-0.5 rounded font-bold ${
                                ch === 'in_app'
                                  ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/20'
                                  : ch === 'email'
                                  ? 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/20'
                                  : 'bg-purple-500/15 text-purple-400 border border-purple-500/20'
                              }`}
                            >
                              {ch}
                            </span>
                          ))}
                        </div>
                      </td>

                      <td className="py-3.5 px-4">
                        <Badge
                          variant={
                            ev.status === 'DELIVERED'
                              ? 'success'
                              : ev.status === 'RETRYING'
                              ? 'warning'
                              : ev.status === 'FAILED'
                              ? 'danger'
                              : ev.status === 'DEDUPLICATED'
                              ? 'indigo'
                              : 'neutral'
                          }
                          size="sm"
                        >
                          {ev.status}
                        </Badge>
                      </td>

                      <td className="py-3.5 px-4 font-mono text-[11px] text-slate-300">
                        {ev.attempts} / {ev.max_retries}
                      </td>

                      <td className="py-3.5 px-4 text-slate-400 text-[11px] font-mono">
                        {new Date(ev.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                      </td>

                      <td className="py-3.5 px-4 text-right space-x-1.5">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setSelectedEvent(ev);
                            setInspectModalOpen(true);
                          }}
                        >
                          Inspect
                        </Button>

                        {isRetryable && (
                          <Button
                            variant="primary"
                            size="sm"
                            onClick={() => handleRetrySingle(ev)}
                            isLoading={retryingId === ev.id}
                            leftIcon={<RotateCcw className="w-3 h-3" />}
                          >
                            Retry
                          </Button>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Inspect Event Modal */}
      <Modal
        isOpen={inspectModalOpen}
        onClose={() => setInspectModalOpen(false)}
        title={`Notification Dispatch Audit: ${selectedEvent?.event_type}`}
        maxWidth="lg"
      >
        <div className="space-y-4 text-xs">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 p-3 rounded-2xl bg-slate-950 border border-white/10">
            <div>
              <span className="text-slate-500 text-[10px] uppercase font-bold">Status</span>
              <p className="text-white font-bold mt-0.5">{selectedEvent?.status}</p>
            </div>
            <div>
              <span className="text-slate-500 text-[10px] uppercase font-bold">Attempts</span>
              <p className="text-white font-bold mt-0.5">{selectedEvent?.attempts} of {selectedEvent?.max_retries}</p>
            </div>
            <div>
              <span className="text-slate-500 text-[10px] uppercase font-bold">Created</span>
              <p className="text-white font-bold mt-0.5">
                {selectedEvent ? new Date(selectedEvent.created_at).toLocaleTimeString() : ''}
              </p>
            </div>
            <div>
              <span className="text-slate-500 text-[10px] uppercase font-bold">Sent Time</span>
              <p className="text-white font-bold mt-0.5">
                {selectedEvent?.sent_at ? new Date(selectedEvent.sent_at).toLocaleTimeString() : 'N/A'}
              </p>
            </div>
          </div>

          {selectedEvent?.last_error && (
            <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300">
              <span className="font-bold text-[10px] uppercase tracking-wider block">Last Delivery Exception:</span>
              <p className="mt-1 font-mono text-[11px]">{selectedEvent.last_error}</p>
            </div>
          )}

          <div>
            <span className="text-slate-400 font-bold uppercase text-[10px]">Rendered Copy:</span>
            <div className="p-3 rounded-xl bg-slate-950 border border-white/10 space-y-1.5 mt-1">
              <div className="font-bold text-white">{selectedEvent?.rendered_title}</div>
              <div className="text-slate-300 leading-relaxed whitespace-pre-wrap">{selectedEvent?.rendered_body}</div>
            </div>
          </div>

          <div>
            <span className="text-slate-400 font-bold uppercase text-[10px]">Channel Delivery Telemetry:</span>
            <pre className="p-3 rounded-xl bg-slate-950 border border-white/10 text-emerald-400 font-mono text-[11px] max-h-40 overflow-y-auto mt-1">
              {JSON.stringify(selectedEvent?.channel_delivery_results || {}, null, 2)}
            </pre>
          </div>

          <div>
            <span className="text-slate-400 font-bold uppercase text-[10px]">Event Payload Variables:</span>
            <pre className="p-3 rounded-xl bg-slate-950 border border-white/10 text-cyan-300 font-mono text-[11px] max-h-40 overflow-y-auto mt-1">
              {JSON.stringify(selectedEvent?.payload || {}, null, 2)}
            </pre>
          </div>
        </div>
      </Modal>
    </div>
  );
};
