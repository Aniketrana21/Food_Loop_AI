'use client';

import React, { useState } from 'react';
import { 
  Users, 
  Search, 
  ShieldAlert, 
  ShieldCheck, 
  UserX, 
  UserCheck, 
  Lock, 
  Mail, 
  Building2, 
  AlertCircle 
} from 'lucide-react';
import { Badge } from '@/components/design-system/Badge';
import { Button } from '@/components/design-system/Button';
import { Modal } from '@/components/design-system/Modal';
import { AdminUser } from './types';

interface AdminAccountsManagerProps {
  users: AdminUser[];
  onSetUserStatus: (userId: string, isActive: boolean, reason: string) => Promise<void>;
  isLoading?: boolean;
}

export const AdminAccountsManager: React.FC<AdminAccountsManagerProps> = ({
  users,
  onSetUserStatus,
  isLoading = false
}) => {
  const [search, setSearch] = useState('');
  const [selectedUser, setSelectedUser] = useState<AdminUser | null>(null);
  const [targetActiveState, setTargetActiveState] = useState<boolean>(false);
  const [reason, setReason] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [roleFilter, setRoleFilter] = useState<string>('ALL');

  const filteredUsers = users
    .filter(u => roleFilter === 'ALL' || u.role.toUpperCase() === roleFilter)
    .filter(u => 
      u.full_name.toLowerCase().includes(search.toLowerCase()) ||
      u.email.toLowerCase().includes(search.toLowerCase()) ||
      (u.organization_name && u.organization_name.toLowerCase().includes(search.toLowerCase()))
    );

  const handleOpenModal = (user: AdminUser, makeActive: boolean) => {
    setSelectedUser(user);
    setTargetActiveState(makeActive);
    setReason('');
    setModalOpen(true);
  };

  const handleConfirmStatusChange = async () => {
    if (!selectedUser || reason.trim().length < 5) return;
    try {
      setIsSubmitting(true);
      await onSetUserStatus(selectedUser.id, targetActiveState, reason.trim());
      setModalOpen(false);
    } catch (err) {
      console.error('Failed to change user account status:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const getRoleBadgeVariant = (role: string) => {
    switch (role.toUpperCase()) {
      case 'ADMIN':
      case 'SUPER_ADMIN': return 'danger';
      case 'KITCHEN_MANAGER': return 'emerald';
      case 'PROCESSOR': return 'purple';
      case 'NGO': return 'indigo';
      case 'DRIVER': return 'cyan';
      default: return 'neutral';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header & Filter Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-2xl glass-panel bg-slate-900/60 border border-white/10">
        <div>
          <h3 className="text-base font-bold text-white tracking-tight flex items-center gap-2">
            <Users className="w-5 h-5 text-emerald-400" />
            Platform User Governance & Access Control
          </h3>
          <p className="text-xs text-slate-400">
            Audit user accounts, enforce zero-trust session integrity, and suspend compromised credentials
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Role Filter */}
          <select
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value)}
            className="px-3 py-1.5 text-xs bg-slate-950 border border-white/10 rounded-xl text-white focus:outline-none focus:border-emerald-500/50"
          >
            <option value="ALL">All Roles</option>
            <option value="ADMIN">Super Admins</option>
            <option value="KITCHEN_MANAGER">Kitchen Managers</option>
            <option value="PROCESSOR">FPU Processors</option>
            <option value="NGO">NGO Recipients</option>
            <option value="DRIVER">Logistics Drivers</option>
          </select>

          <div className="relative w-48 sm:w-64">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search user name or email..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 text-xs bg-slate-950 border border-white/10 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500/50"
            />
          </div>
        </div>
      </div>

      {/* Security Disclaimer Banner */}
      <div className="p-3.5 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs flex items-center space-x-3">
        <Lock className="w-4 h-4 shrink-0 text-amber-400" />
        <div>
          <span className="font-bold">Cryptographically Audited Account Suspension:</span> Account suspension revokes JWT access tokens immediately across all active web and mobile devices. A permanent forensic audit record is stamped upon execution.
        </div>
      </div>

      {/* Users Table */}
      <div className="glass-panel bg-slate-900/60 rounded-3xl border border-white/10 overflow-hidden shadow-2xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/80 border-b border-white/10 text-slate-400 uppercase font-bold text-[10px] tracking-wider">
              <tr>
                <th className="px-5 py-3.5">User</th>
                <th className="px-4 py-3.5">Role</th>
                <th className="px-4 py-3.5">Organization</th>
                <th className="px-4 py-3.5">Account Status</th>
                <th className="px-4 py-3.5">Created</th>
                <th className="px-5 py-3.5 text-right">Governed Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {filteredUsers.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-10 text-slate-500 text-xs">
                    No platform accounts found matching your query.
                  </td>
                </tr>
              ) : (
                filteredUsers.map((user) => (
                  <tr key={user.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="px-5 py-4">
                      <div className="flex items-center space-x-3">
                        <div className="w-9 h-9 rounded-xl bg-slate-800 border border-white/10 flex items-center justify-center text-white font-bold shrink-0">
                          {user.full_name ? user.full_name.slice(0, 2).toUpperCase() : 'FL'}
                        </div>
                        <div>
                          <h4 className="font-bold text-white text-sm">{user.full_name || 'Anonymous User'}</h4>
                          <span className="text-[11px] text-slate-400 flex items-center gap-1">
                            <Mail className="w-3 h-3 text-slate-500" />
                            {user.email}
                          </span>
                        </div>
                      </div>
                    </td>

                    <td className="px-4 py-4">
                      <Badge variant={getRoleBadgeVariant(user.role)} size="sm">
                        {user.role.replace('_', ' ')}
                      </Badge>
                    </td>

                    <td className="px-4 py-4 text-slate-300 text-[11px]">
                      <div className="flex items-center space-x-1.5 font-medium">
                        <Building2 className="w-3.5 h-3.5 text-slate-500" />
                        <span>{user.organization_name || 'FoodLoop Member'}</span>
                      </div>
                    </td>

                    <td className="px-4 py-4">
                      <Badge variant={user.is_active ? 'emerald' : 'danger'} size="sm">
                        {user.is_active ? 'Active' : 'Suspended'}
                      </Badge>
                    </td>

                    <td className="px-4 py-4 text-slate-400 text-[11px]">
                      {new Date(user.created_at).toLocaleDateString()}
                    </td>

                    <td className="px-5 py-4 text-right">
                      {user.is_active ? (
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={() => handleOpenModal(user, false)}
                          leftIcon={<UserX className="w-3.5 h-3.5" />}
                        >
                          Suspend Account
                        </Button>
                      ) : (
                        <Button
                          variant="primary"
                          size="sm"
                          onClick={() => handleOpenModal(user, true)}
                          leftIcon={<UserCheck className="w-3.5 h-3.5" />}
                        >
                          Reactivate
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

      {/* Governed User Suspension Modal */}
      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title={targetActiveState ? 'Reactivate User Account' : 'Suspend User Account'}
        maxWidth="md"
      >
        <div className="space-y-4 text-xs">
          <div className="p-3.5 rounded-xl bg-slate-950/80 border border-white/10">
            <span className="text-slate-400 text-[11px]">Target Account:</span>
            <h4 className="text-sm font-bold text-white mt-0.5">{selectedUser?.full_name} ({selectedUser?.email})</h4>
            <span className="text-[10px] text-slate-400 font-mono">User ID: {selectedUser?.id}</span>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Mandatory Audit Reason / Justification <span className="text-rose-400">*</span>
            </label>
            <textarea
              rows={3}
              placeholder="e.g. Account suspended due to anomalous automated batch cancellations or security review..."
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="w-full p-2.5 rounded-xl bg-slate-950 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500/50 text-xs"
            />
            <span className="text-[10px] text-slate-500">Minimum 5 characters required for forensic audit entry.</span>
          </div>

          <div className="p-3 rounded-xl bg-slate-900 border border-emerald-500/30 text-emerald-300 text-[11px] flex items-center space-x-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>This suspension event will be hashed with SHA-256 and committed to the immutable forensic audit ledger.</span>
          </div>

          <div className="flex items-center justify-end space-x-2 pt-2 border-t border-white/10">
            <Button variant="outline" size="sm" onClick={() => setModalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant={targetActiveState ? 'primary' : 'destructive'}
              size="sm"
              onClick={handleConfirmStatusChange}
              isLoading={isSubmitting}
              disabled={reason.trim().length < 5}
            >
              {targetActiveState ? 'Confirm Reactivation' : 'Confirm Suspension'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
