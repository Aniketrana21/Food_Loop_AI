'use client';

import React, { useState } from 'react';
import { 
  HeartHandshake, 
  Search, 
  ShieldCheck, 
  CheckCircle2, 
  XCircle, 
  Clock, 
  MapPin, 
  Thermometer, 
  FileText,
  Lock,
  Phone,
  UserCheck
} from 'lucide-react';
import { Badge } from '@/components/design-system/Badge';
import { Button } from '@/components/design-system/Button';
import { Modal } from '@/components/design-system/Modal';
import { AdminRecipient } from './types';

interface AdminRecipientsManagerProps {
  recipients: AdminRecipient[];
  onApproveRecipient: (recipientId: string, status: 'VERIFIED' | 'REJECTED', notes?: string) => Promise<void>;
  isLoading?: boolean;
}

export const AdminRecipientsManager: React.FC<AdminRecipientsManagerProps> = ({
  recipients,
  onApproveRecipient,
  isLoading = false
}) => {
  const [search, setSearch] = useState('');
  const [selectedRecipient, setSelectedRecipient] = useState<AdminRecipient | null>(null);
  const [targetStatus, setTargetStatus] = useState<'VERIFIED' | 'REJECTED'>('VERIFIED');
  const [notes, setNotes] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'PENDING' | 'VERIFIED' | 'REJECTED'>('ALL');

  const filteredRecipients = recipients
    .filter(r => statusFilter === 'ALL' || r.verification_status === statusFilter)
    .filter(r => 
      r.name.toLowerCase().includes(search.toLowerCase()) ||
      r.address.toLowerCase().includes(search.toLowerCase()) ||
      (r.contact_person && r.contact_person.toLowerCase().includes(search.toLowerCase()))
    );

  const handleOpenModal = (recipient: AdminRecipient, status: 'VERIFIED' | 'REJECTED') => {
    setSelectedRecipient(recipient);
    setTargetStatus(status);
    setNotes('');
    setModalOpen(true);
  };

  const handleConfirm = async () => {
    if (!selectedRecipient) return;
    try {
      setIsSubmitting(true);
      await onApproveRecipient(selectedRecipient.id, targetStatus, notes.trim() || undefined);
      setModalOpen(false);
    } catch (err) {
      console.error('Failed to update recipient verification status:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header & Filter Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-2xl glass-panel bg-slate-900/60 border border-white/10">
        <div>
          <h3 className="text-base font-bold text-white tracking-tight flex items-center gap-2">
            <HeartHandshake className="w-5 h-5 text-indigo-400" />
            Recipient Charities & Food Bank Approval
          </h3>
          <p className="text-xs text-slate-400">
            Verify 501(c)(3) tax exemptions, cold chain intake readiness, and safe food redistribution qualifications
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Status Filter Pills */}
          <div className="flex items-center space-x-1 bg-slate-950 p-1 rounded-xl border border-white/10 text-xs">
            {(['ALL', 'PENDING', 'VERIFIED', 'REJECTED'] as const).map(st => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                className={`px-2.5 py-1 rounded-lg font-semibold transition-all ${
                  statusFilter === st ? 'bg-slate-800 text-white' : 'text-slate-400 hover:text-white'
                }`}
              >
                {st}
              </button>
            ))}
          </div>

          <div className="relative w-48 sm:w-60">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search charity or contact..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 text-xs bg-slate-950 border border-white/10 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500/50"
            />
          </div>
        </div>
      </div>

      {/* Recipient Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredRecipients.length === 0 ? (
          <div className="col-span-full p-12 text-center rounded-3xl glass-panel bg-slate-900/30 border border-white/5">
            <HeartHandshake className="w-10 h-10 text-slate-600 mx-auto" />
            <h4 className="text-sm font-bold text-white mt-2">No Recipient Organizations Found</h4>
            <p className="text-xs text-slate-500 mt-1">Try adjusting your verification status filter or search keywords.</p>
          </div>
        ) : (
          filteredRecipients.map((recipient) => (
            <div
              key={recipient.id}
              className="glass-panel p-5 rounded-3xl border border-white/10 bg-slate-900/70 hover:border-white/20 transition-all flex flex-col justify-between shadow-xl"
            >
              <div>
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-2.5">
                    <div className="w-9 h-9 rounded-2xl bg-indigo-500/15 border border-indigo-500/30 flex items-center justify-center text-indigo-400 font-bold shrink-0">
                      <HeartHandshake className="w-4 h-4" />
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-white tracking-tight leading-snug">{recipient.name}</h4>
                      <span className="text-[10px] text-slate-400 uppercase font-semibold">
                        {recipient.facility_type.replace('_', ' ')}
                      </span>
                    </div>
                  </div>

                  <Badge
                    variant={
                      recipient.verification_status === 'VERIFIED'
                        ? 'emerald'
                        : recipient.verification_status === 'PENDING'
                        ? 'warning'
                        : 'danger'
                    }
                    size="sm"
                  >
                    {recipient.verification_status}
                  </Badge>
                </div>

                <p className="text-xs text-slate-300 mt-3 flex items-start gap-1.5 leading-snug">
                  <MapPin className="w-3.5 h-3.5 text-slate-500 shrink-0 mt-0.5" />
                  <span>{recipient.address}</span>
                </p>

                {/* Specs Box */}
                <div className="grid grid-cols-2 gap-2 mt-3.5 p-3 rounded-2xl bg-slate-950/70 border border-white/5 text-[11px]">
                  <div>
                    <span className="text-slate-500 text-[9px] uppercase font-bold">Max Intake</span>
                    <p className="font-bold text-white mt-0.5">{recipient.max_daily_intake_kg} kg/day</p>
                  </div>
                  <div>
                    <span className="text-slate-500 text-[9px] uppercase font-bold">Cold Storage</span>
                    <p className="font-bold text-indigo-300 mt-0.5 flex items-center gap-1">
                      <Thermometer className="w-3 h-3 text-indigo-400" />
                      {recipient.cold_storage_available ? 'Verified Cold Chain' : 'Ambient Only'}
                    </p>
                  </div>
                  <div>
                    <span className="text-slate-500 text-[9px] uppercase font-bold">Charity ID</span>
                    <p className="font-mono text-slate-300 mt-0.5">{recipient.verified_charity_id || 'Pending Check'}</p>
                  </div>
                  <div>
                    <span className="text-slate-500 text-[9px] uppercase font-bold">Reliability</span>
                    <p className="font-bold text-emerald-400 mt-0.5">{Math.round((recipient.reliability_score || 0.95) * 100)}% Match Score</p>
                  </div>
                </div>

                {recipient.contact_person && (
                  <div className="mt-3 text-[11px] text-slate-400 flex items-center justify-between border-t border-white/5 pt-2">
                    <span className="font-medium text-slate-300">{recipient.contact_person}</span>
                    <span className="flex items-center gap-1 text-slate-500">
                      <Phone className="w-3 h-3" />
                      {recipient.contact_phone || 'No phone'}
                    </span>
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              <div className="flex items-center space-x-2 mt-4 pt-3 border-t border-white/5">
                {recipient.verification_status !== 'VERIFIED' && (
                  <Button
                    variant="primary"
                    size="sm"
                    className="flex-1"
                    onClick={() => handleOpenModal(recipient, 'VERIFIED')}
                    leftIcon={<UserCheck className="w-3.5 h-3.5" />}
                  >
                    Approve
                  </Button>
                )}

                {recipient.verification_status !== 'REJECTED' && (
                  <Button
                    variant="destructive"
                    size="sm"
                    className="flex-1"
                    onClick={() => handleOpenModal(recipient, 'REJECTED')}
                    leftIcon={<XCircle className="w-3.5 h-3.5" />}
                  >
                    Reject
                  </Button>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Recipient Verification Governance Modal */}
      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title={targetStatus === 'VERIFIED' ? 'Approve Recipient Charity' : 'Reject Recipient Charity'}
        maxWidth="md"
      >
        <div className="space-y-4 text-xs">
          <div className="p-3.5 rounded-xl bg-slate-950/80 border border-white/10">
            <span className="text-slate-400 text-[11px]">Recipient Organization:</span>
            <h4 className="text-sm font-bold text-white mt-0.5">{selectedRecipient?.name}</h4>
            <span className="text-[10px] text-slate-400">{selectedRecipient?.address}</span>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Auditor / Verification Inspection Notes
            </label>
            <textarea
              rows={3}
              placeholder="e.g. 501(c)(3) tax ID verified, food safety storage inspected, HACCP handling accepted..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full p-2.5 rounded-xl bg-slate-950 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500/50 text-xs"
            />
          </div>

          <div className="p-3 rounded-xl bg-slate-900 border border-emerald-500/30 text-emerald-300 text-[11px] flex items-center space-x-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>This verification decision will be hashed with SHA-256 and committed to the tamper-evident audit ledger.</span>
          </div>

          <div className="flex items-center justify-end space-x-2 pt-2 border-t border-white/10">
            <Button variant="outline" size="sm" onClick={() => setModalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant={targetStatus === 'VERIFIED' ? 'primary' : 'destructive'}
              size="sm"
              onClick={handleConfirm}
              isLoading={isSubmitting}
            >
              {targetStatus === 'VERIFIED' ? 'Confirm Approval' : 'Confirm Rejection'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
