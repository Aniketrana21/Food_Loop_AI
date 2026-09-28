'use client';

import React, { useState } from 'react';
import { 
  Building2, 
  Search, 
  ShieldCheck, 
  ShieldAlert, 
  CheckCircle2, 
  XCircle, 
  Users, 
  Factory, 
  Utensils, 
  AlertTriangle,
  Lock,
  ExternalLink
} from 'lucide-react';
import { Badge } from '@/components/design-system/Badge';
import { Button } from '@/components/design-system/Button';
import { Modal } from '@/components/design-system/Modal';
import { AdminOrg } from './types';

interface AdminOrganizationsManagerProps {
  organizations: AdminOrg[];
  onManageOrg: (orgId: string, action: 'ACTIVATE' | 'SUSPEND', reason: string) => Promise<void>;
  isLoading?: boolean;
}

export const AdminOrganizationsManager: React.FC<AdminOrganizationsManagerProps> = ({
  organizations,
  onManageOrg,
  isLoading = false
}) => {
  const [search, setSearch] = useState('');
  const [selectedOrg, setSelectedOrg] = useState<AdminOrg | null>(null);
  const [actionType, setActionType] = useState<'ACTIVATE' | 'SUSPEND'>('SUSPEND');
  const [reason, setReason] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const filteredOrgs = organizations.filter(o => 
    o.name.toLowerCase().includes(search.toLowerCase()) ||
    o.registration_number.toLowerCase().includes(search.toLowerCase()) ||
    o.contact_email.toLowerCase().includes(search.toLowerCase())
  );

  const handleOpenActionModal = (org: AdminOrg, action: 'ACTIVATE' | 'SUSPEND') => {
    setSelectedOrg(org);
    setActionType(action);
    setReason('');
    setModalOpen(true);
  };

  const handleConfirmAction = async () => {
    if (!selectedOrg || reason.trim().length < 5) return;
    try {
      setIsSubmitting(true);
      await onManageOrg(selectedOrg.id, actionType, reason.trim());
      setModalOpen(false);
    } catch (err) {
      console.error('Failed to update organization status:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header & Search */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-2xl glass-panel bg-slate-900/60 border border-white/10">
        <div>
          <h3 className="text-base font-bold text-white tracking-tight flex items-center gap-2">
            <Building2 className="w-5 h-5 text-emerald-400" />
            Tenant Organizations Governance
          </h3>
          <p className="text-xs text-slate-400">
            Regulated institutional hospitality chains, enterprise food processing plants, and charity food networks
          </p>
        </div>

        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search by name, reg #, email..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-950 border border-white/10 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500/50"
          />
        </div>
      </div>

      {/* Governed Action Disclaimer Notice */}
      <div className="p-3.5 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs flex items-center space-x-3">
        <Lock className="w-4 h-4 shrink-0 text-amber-400" />
        <div>
          <span className="font-bold">Governed Administration Policy:</span> Direct unrestricted database mutation is blocked. 
          All organization activations and suspensions require documented justification and are recorded in the SHA-256 tamper-evident forensic ledger.
        </div>
      </div>

      {/* Organizations Table Card */}
      <div className="glass-panel bg-slate-900/60 rounded-3xl border border-white/10 overflow-hidden shadow-2xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/80 border-b border-white/10 text-slate-400 uppercase font-bold text-[10px] tracking-wider">
              <tr>
                <th className="px-5 py-3.5">Organization</th>
                <th className="px-4 py-3.5">Type & Reg #</th>
                <th className="px-4 py-3.5">Facilities</th>
                <th className="px-4 py-3.5">Status</th>
                <th className="px-4 py-3.5">Primary Contact</th>
                <th className="px-5 py-3.5 text-right">Governed Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {filteredOrgs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-10 text-slate-500 text-xs">
                    No organizations match your search criteria.
                  </td>
                </tr>
              ) : (
                filteredOrgs.map((org) => (
                  <tr key={org.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="px-5 py-4">
                      <div className="flex items-center space-x-3">
                        <div className="w-9 h-9 rounded-xl bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center text-emerald-400 font-bold shrink-0">
                          {org.name.slice(0, 2).toUpperCase()}
                        </div>
                        <div>
                          <h4 className="font-bold text-white text-sm">{org.name}</h4>
                          <span className="text-[11px] text-slate-400">{org.contact_email}</span>
                        </div>
                      </div>
                    </td>

                    <td className="px-4 py-4">
                      <Badge variant="neutral" size="sm">
                        {org.org_type.replace('_', ' ')}
                      </Badge>
                      <div className="text-[11px] text-slate-400 font-mono mt-1">
                        Reg: {org.registration_number}
                      </div>
                    </td>

                    <td className="px-4 py-4">
                      <div className="flex items-center space-x-3 text-[11px] text-slate-300">
                        <span className="flex items-center gap-1" title="Kitchens">
                          <Utensils className="w-3.5 h-3.5 text-emerald-400" />
                          {org.kitchens_count}
                        </span>
                        <span className="flex items-center gap-1" title="Processing Units">
                          <Factory className="w-3.5 h-3.5 text-purple-400" />
                          {org.fpus_count}
                        </span>
                        <span className="flex items-center gap-1" title="Users">
                          <Users className="w-3.5 h-3.5 text-indigo-400" />
                          {org.members_count}
                        </span>
                      </div>
                    </td>

                    <td className="px-4 py-4">
                      <div className="flex items-center space-x-1.5">
                        <Badge variant={org.is_active ? 'emerald' : 'danger'} size="sm">
                          {org.is_active ? 'Active' : 'Suspended'}
                        </Badge>
                        {org.is_verified && (
                          <Badge variant="info" size="sm">Verified</Badge>
                        )}
                      </div>
                    </td>

                    <td className="px-4 py-4 text-slate-300 text-[11px]">
                      <div>{org.contact_phone || 'None provided'}</div>
                      <div className="text-[10px] text-slate-500">
                        Registered {new Date(org.created_at).toLocaleDateString()}
                      </div>
                    </td>

                    <td className="px-5 py-4 text-right">
                      {org.is_active ? (
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={() => handleOpenActionModal(org, 'SUSPEND')}
                          leftIcon={<ShieldAlert className="w-3.5 h-3.5" />}
                        >
                          Suspend
                        </Button>
                      ) : (
                        <Button
                          variant="primary"
                          size="sm"
                          onClick={() => handleOpenActionModal(org, 'ACTIVATE')}
                          leftIcon={<CheckCircle2 className="w-3.5 h-3.5" />}
                        >
                          Activate
                        </Button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Governed Action Modal */}
      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title={actionType === 'SUSPEND' ? 'Suspend Organization' : 'Reactivate Organization'}
        maxWidth="md"
      >
        <div className="space-y-4 text-xs">
          <div className="p-3.5 rounded-xl bg-slate-950/80 border border-white/10">
            <span className="text-slate-400 text-[11px]">Target Entity:</span>
            <h4 className="text-sm font-bold text-white mt-0.5">{selectedOrg?.name}</h4>
            <span className="text-[10px] text-slate-400 font-mono">ID: {selectedOrg?.id}</span>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Mandatory Governance Justification / Reason <span className="text-rose-400">*</span>
            </label>
            <textarea
              rows={3}
              placeholder="Provide regulatory, food safety, or commercial justification for this action..."
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="w-full p-2.5 rounded-xl bg-slate-950 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500/50 text-xs"
            />
            <span className="text-[10px] text-slate-500">Minimum 5 characters required for forensic audit entry.</span>
          </div>

          <div className="p-3 rounded-xl bg-slate-900 border border-emerald-500/30 text-emerald-300 text-[11px] flex items-center space-x-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>This action will be hashed using SHA-256 and committed to the permanent forensic audit ledger.</span>
          </div>

          <div className="flex items-center justify-end space-x-2 pt-2 border-t border-white/10">
            <Button variant="outline" size="sm" onClick={() => setModalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant={actionType === 'SUSPEND' ? 'destructive' : 'primary'}
              size="sm"
              onClick={handleConfirmAction}
              isLoading={isSubmitting}
              disabled={reason.trim().length < 5}
            >
              {actionType === 'SUSPEND' ? 'Confirm Suspension' : 'Confirm Activation'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
