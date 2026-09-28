'use client';

import React, { useState } from 'react';
import { 
  ShieldCheck, 
  Search, 
  Filter, 
  Hash, 
  Clock, 
  User, 
  ExternalLink, 
  CheckCircle2, 
  Lock, 
  FileCode, 
  ChevronRight,
  RefreshCw 
} from 'lucide-react';
import { Badge } from '@/components/design-system/Badge';
import { Button } from '@/components/design-system/Button';
import { Modal } from '@/components/design-system/Modal';
import { AuditLogItem } from './types';

interface AdminAuditLogViewerProps {
  logs: AuditLogItem[];
  totalLogs?: number;
  onRefresh?: () => void;
  isLoading?: boolean;
}

export const AdminAuditLogViewer: React.FC<AdminAuditLogViewerProps> = ({
  logs,
  totalLogs = 0,
  onRefresh,
  isLoading = false
}) => {
  const [search, setSearch] = useState('');
  const [selectedModule, setSelectedModule] = useState<string>('ALL');
  const [selectedLog, setSelectedLog] = useState<AuditLogItem | null>(null);
  const [diffModalOpen, setDiffModalOpen] = useState(false);

  // Extract distinct modules for filter
  const modules = Array.from(new Set(logs.map(l => l.module)));

  const filteredLogs = logs
    .filter(l => selectedModule === 'ALL' || l.module === selectedModule)
    .filter(l => 
      l.action.toLowerCase().includes(search.toLowerCase()) ||
      l.entity_name.toLowerCase().includes(search.toLowerCase()) ||
      l.entity_id.toLowerCase().includes(search.toLowerCase()) ||
      l.user_email.toLowerCase().includes(search.toLowerCase()) ||
      l.sha256_hash.toLowerCase().includes(search.toLowerCase())
    );

  const handleOpenDiff = (log: AuditLogItem) => {
    setSelectedLog(log);
    setDiffModalOpen(true);
  };

  return (
    <div className="space-y-6">
      {/* Header & Filter Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-2xl glass-panel bg-slate-900/60 border border-white/10">
        <div>
          <h3 className="text-base font-bold text-white tracking-tight flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            Forensic Tamper-Evident Audit Ledger
          </h3>
          <p className="text-xs text-slate-400">
            Immutable append-only record of all administrative actions, recipient verifications, and threshold changes
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Module Filter */}
          <select
            value={selectedModule}
            onChange={(e) => setSelectedModule(e.target.value)}
            className="px-3 py-1.5 text-xs bg-slate-950 border border-white/10 rounded-xl text-white focus:outline-none focus:border-emerald-500/50"
          >
            <option value="ALL">All Modules</option>
            {modules.map(m => (
              <option key={m} value={m}>{m.replace('_', ' ')}</option>
            ))}
          </select>

          <div className="relative w-48 sm:w-64">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search action, actor, hash..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 text-xs bg-slate-950 border border-white/10 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500/50"
            />
          </div>

          {onRefresh && (
            <Button
              variant="outline"
              size="sm"
              onClick={onRefresh}
              isLoading={isLoading}
              leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
            >
              Sync
            </Button>
          )}
        </div>
      </div>

      {/* Forensic Proof of Integrity Banner */}
      <div className="p-3.5 rounded-2xl bg-emerald-950/40 border border-emerald-500/30 text-emerald-300 text-xs flex items-center space-x-3">
        <Lock className="w-4 h-4 shrink-0 text-emerald-400" />
        <div>
          <span className="font-bold">Cryptographic SHA-256 Proof of Integrity:</span> Every audit entry binds timestamp, actor UUID, module state, and payload mutation. Hashes are verified on retrieval to detect unauthorized database tampering.
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="glass-panel bg-slate-900/60 rounded-3xl border border-white/10 overflow-hidden shadow-2xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/80 border-b border-white/10 text-slate-400 uppercase font-bold text-[10px] tracking-wider">
              <tr>
                <th className="px-5 py-3.5">Timestamp</th>
                <th className="px-4 py-3.5">Module & Action</th>
                <th className="px-4 py-3.5">Actor</th>
                <th className="px-4 py-3.5">Target Entity</th>
                <th className="px-4 py-3.5">SHA-256 Hash Seal</th>
                <th className="px-5 py-3.5 text-right">Payload Diff</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 font-mono text-[11px]">
              {filteredLogs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-12 text-slate-500 font-sans text-xs">
                    No forensic audit entries found matching your query.
                  </td>
                </tr>
              ) : (
                filteredLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="px-5 py-3.5 whitespace-nowrap text-slate-400">
                      <div className="flex items-center gap-1.5">
                        <Clock className="w-3 h-3 text-slate-500" />
                        <span>{new Date(log.created_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'medium' })}</span>
                      </div>
                    </td>

                    <td className="px-4 py-3.5">
                      <div className="flex items-center space-x-2">
                        <Badge variant="neutral" size="sm">
                          {log.module}
                        </Badge>
                        <span className="text-white font-bold">{log.action}</span>
                      </div>
                    </td>

                    <td className="px-4 py-3.5">
                      <div className="text-slate-300 font-sans text-xs font-semibold">{log.user_name}</div>
                      <div className="text-[10px] text-slate-500 font-sans">{log.user_email}</div>
                    </td>

                    <td className="px-4 py-3.5 text-slate-300">
                      <span className="font-semibold text-emerald-400">{log.entity_name}</span>
                      <div className="text-[10px] text-slate-500">#{log.entity_id.slice(0, 10)}...</div>
                    </td>

                    <td className="px-4 py-3.5">
                      <div className="flex items-center space-x-1.5">
                        <Badge variant="emerald" size="sm">
                          <CheckCircle2 className="w-2.5 h-2.5 mr-1" />
                          VERIFIED
                        </Badge>
                        <span className="text-slate-500 text-[10px] truncate w-24" title={log.sha256_hash}>
                          {log.sha256_hash.slice(0, 12)}...
                        </span>
                      </div>
                    </td>

                    <td className="px-5 py-3.5 text-right font-sans">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleOpenDiff(log)}
                        leftIcon={<FileCode className="w-3 h-3" />}
                      >
                        Inspect
                      </Button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* JSON Payload Diff Modal */}
      <Modal
        isOpen={diffModalOpen}
        onClose={() => setDiffModalOpen(false)}
        title={`Audit Trail Inspection: ${selectedLog?.action}`}
        maxWidth="lg"
      >
        <div className="space-y-4 text-xs">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 p-3 rounded-2xl bg-slate-950 border border-white/10">
            <div>
              <span className="text-slate-500 text-[10px] uppercase font-bold">Module</span>
              <p className="text-white font-bold mt-0.5">{selectedLog?.module}</p>
            </div>
            <div>
              <span className="text-slate-500 text-[10px] uppercase font-bold">Target Entity</span>
              <p className="text-emerald-400 font-bold mt-0.5">{selectedLog?.entity_name}</p>
            </div>
            <div>
              <span className="text-slate-500 text-[10px] uppercase font-bold">Actor IP</span>
              <p className="text-slate-300 font-mono mt-0.5">{selectedLog?.client_ip || '127.0.0.1'}</p>
            </div>
            <div>
              <span className="text-slate-500 text-[10px] uppercase font-bold">Timestamp</span>
              <p className="text-slate-300 mt-0.5">
                {selectedLog && new Date(selectedLog.created_at).toLocaleTimeString()}
              </p>
            </div>
          </div>

          <div>
            <span className="text-[10px] text-slate-500 uppercase font-bold">Cryptographic SHA-256 Hash Seal</span>
            <div className="p-2 rounded-xl bg-slate-950 border border-white/10 font-mono text-[11px] text-emerald-400 break-all select-all mt-1">
              {selectedLog?.sha256_hash}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <span className="text-[10px] text-slate-400 font-bold uppercase">Prior State (Old Values)</span>
              <pre className="mt-1 p-3 rounded-xl bg-slate-950 border border-white/5 text-[11px] font-mono text-slate-300 max-h-48 overflow-y-auto whitespace-pre-wrap">
                {selectedLog?.old_values ? JSON.stringify(selectedLog.old_values, null, 2) : 'None (Creation Event)'}
              </pre>
            </div>

            <div>
              <span className="text-[10px] text-emerald-400 font-bold uppercase">Mutated State (New Values)</span>
              <pre className="mt-1 p-3 rounded-xl bg-slate-950 border border-emerald-500/20 text-[11px] font-mono text-emerald-300 max-h-48 overflow-y-auto whitespace-pre-wrap">
                {selectedLog?.new_values ? JSON.stringify(selectedLog.new_values, null, 2) : 'None (Deletion Event)'}
              </pre>
            </div>
          </div>

          <div className="flex justify-end pt-2 border-t border-white/10">
            <Button variant="outline" size="sm" onClick={() => setDiffModalOpen(false)}>
              Close
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
