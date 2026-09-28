'use client';

import React, { useState } from 'react';
import { 
  Sliders, 
  ShieldCheck, 
  Settings, 
  Save, 
  RotateCcw, 
  AlertTriangle, 
  Thermometer, 
  Clock, 
  TrendingUp, 
  Cpu, 
  Truck 
} from 'lucide-react';
import { Badge } from '@/components/design-system/Badge';
import { Button } from '@/components/design-system/Button';
import { Modal } from '@/components/design-system/Modal';
import { BusinessRule } from './types';

interface AdminBusinessRulesProps {
  rules: BusinessRule[];
  onUpdateRule: (ruleKey: string, payload: any) => Promise<void>;
  isLoading?: boolean;
}

export const AdminBusinessRules: React.FC<AdminBusinessRulesProps> = ({
  rules,
  onUpdateRule,
  isLoading = false
}) => {
  const [selectedRule, setSelectedRule] = useState<BusinessRule | null>(null);
  const [editedValue, setEditedValue] = useState<string>('');
  const [modalOpen, setModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'FOOD_SAFETY': return <Thermometer className="w-4 h-4 text-rose-400" />;
      case 'OPERATIONS': return <TrendingUp className="w-4 h-4 text-emerald-400" />;
      case 'LOGISTICS': return <Truck className="w-4 h-4 text-cyan-400" />;
      case 'ML_FORECAST': return <Cpu className="w-4 h-4 text-purple-400" />;
      default: return <Settings className="w-4 h-4 text-slate-400" />;
    }
  };

  const handleOpenEdit = (rule: BusinessRule) => {
    setSelectedRule(rule);
    setEditedValue(JSON.stringify(rule.value, null, 2));
    setErrorMsg(null);
    setModalOpen(true);
  };

  const handleSaveRule = async () => {
    if (!selectedRule) return;
    try {
      setErrorMsg(null);
      let parsedVal: any;
      try {
        parsedVal = JSON.parse(editedValue);
      } catch (e) {
        setErrorMsg('Invalid JSON format. Please ensure valid syntax.');
        return;
      }

      setIsSubmitting(true);
      await onUpdateRule(selectedRule.rule_key, {
        rule_key: selectedRule.rule_key,
        rule_name: selectedRule.rule_name,
        category: selectedRule.category,
        value: parsedVal,
        description: selectedRule.description,
        is_active: selectedRule.is_active
      });
      setModalOpen(false);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to update rule');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="p-4 rounded-2xl glass-panel bg-slate-900/60 border border-white/10 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-base font-bold text-white tracking-tight flex items-center gap-2">
            <Sliders className="w-5 h-5 text-emerald-400" />
            System Business Rules & Compliance Policies
          </h3>
          <p className="text-xs text-slate-400">
            Define dynamic food-safety shelf life, courier timeout thresholds, FEFO dispatch windows, and ML confidence limits
          </p>
        </div>
      </div>

      {/* Rules Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {rules.map((rule) => (
          <div
            key={rule.id}
            className="glass-panel p-5 rounded-3xl border border-white/10 bg-slate-900/70 hover:border-white/20 transition-all flex flex-col justify-between shadow-xl"
          >
            <div>
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-2.5">
                  <div className="p-2 rounded-xl bg-slate-950 border border-white/5">
                    {getCategoryIcon(rule.category)}
                  </div>
                  <div>
                    <Badge variant={rule.category === 'FOOD_SAFETY' ? 'danger' : rule.category === 'ML_FORECAST' ? 'purple' : 'emerald'} size="sm">
                      {rule.category}
                    </Badge>
                    <h4 className="text-sm font-bold text-white tracking-tight mt-1">{rule.rule_name}</h4>
                  </div>
                </div>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleOpenEdit(rule)}
                  leftIcon={<Settings className="w-3.5 h-3.5" />}
                >
                  Configure
                </Button>
              </div>

              <p className="text-xs text-slate-400 mt-2.5 leading-relaxed">
                {rule.description || 'Configurable operational threshold for platform automation.'}
              </p>

              {/* Formatted Rule Value Display */}
              <div className="mt-3 p-3 rounded-2xl bg-slate-950/80 border border-white/5 text-xs font-mono text-emerald-300">
                <pre className="overflow-x-auto text-[11px] whitespace-pre-wrap">
                  {JSON.stringify(rule.value, null, 2)}
                </pre>
              </div>
            </div>

            <div className="mt-3.5 pt-2.5 border-t border-white/5 flex items-center justify-between text-[10px] text-slate-500 font-mono">
              <span>KEY: {rule.rule_key}</span>
              <span>Updated: {new Date(rule.updated_at).toLocaleDateString()}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Business Rule Editor Modal */}
      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title={`Configure Rule: ${selectedRule?.rule_name}`}
        maxWidth="md"
      >
        <div className="space-y-4 text-xs">
          <div className="p-3.5 rounded-xl bg-slate-950 border border-white/10">
            <span className="text-slate-400 text-[11px]">System Rule Identifier:</span>
            <div className="font-mono text-emerald-400 font-bold mt-0.5">{selectedRule?.rule_key}</div>
            <p className="text-[11px] text-slate-400 mt-1">{selectedRule?.description}</p>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Rule JSON Parameter Value
            </label>
            <textarea
              rows={6}
              value={editedValue}
              onChange={(e) => setEditedValue(e.target.value)}
              className="w-full p-2.5 rounded-xl bg-slate-950 border border-white/10 font-mono text-xs text-emerald-300 focus:outline-none focus:border-emerald-500/50"
            />
            {errorMsg && (
              <p className="text-rose-400 text-[11px] mt-1 flex items-center gap-1">
                <AlertTriangle className="w-3 h-3" />
                {errorMsg}
              </p>
            )}
          </div>

          <div className="p-3 rounded-xl bg-slate-900 border border-emerald-500/30 text-emerald-300 text-[11px] flex items-center space-x-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>Updates to system rules take effect dynamically across all kitchen edge instances and are logged to the forensic audit ledger.</span>
          </div>

          <div className="flex items-center justify-end space-x-2 pt-2 border-t border-white/10">
            <Button variant="outline" size="sm" onClick={() => setModalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={handleSaveRule}
              isLoading={isSubmitting}
              leftIcon={<Save className="w-3.5 h-3.5" />}
            >
              Save Configuration
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
