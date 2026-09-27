'use client';

import React from 'react';
import { Sparkles, CheckCircle2, ChevronRight, HelpCircle } from 'lucide-react';
import { Button } from './Button';
import { Badge } from './Badge';

export interface AIRecommendationCardProps {
  title: string;
  recommendation?: string;
  reasoning?: string;
  impactPreview?: string;
  impactMetrics?: Array<{ label: string; value: string }>;
  confidenceScore?: number; // 0 to 1
  confidencePercentage?: number; // 0 to 100
  modelOrigin?: string;
  modelSource?: string;
  category?: string;
  actionLabel?: string;
  onApply: () => void;
  isApplied?: boolean;
  className?: string;
}

export const AIRecommendationCard: React.FC<AIRecommendationCardProps> = ({
  title,
  recommendation,
  reasoning,
  impactPreview,
  impactMetrics,
  confidenceScore,
  confidencePercentage,
  modelOrigin,
  modelSource,
  category,
  actionLabel,
  onApply,
  isApplied = false,
  className = '',
}) => {
  const confidencePct = confidencePercentage !== undefined 
    ? confidencePercentage 
    : confidenceScore !== undefined 
      ? Math.round(confidenceScore * 100) 
      : 92;

  const displayModel = modelSource || modelOrigin || 'XGBoost & OR-Tools';
  const displayReasoning = reasoning || recommendation || 'Recommended optimization based on historical demand.';

  return (
    <div
      className={`p-5 rounded-2xl glass-panel border border-indigo-500/30 bg-gradient-to-br from-indigo-950/40 via-slate-900 to-slate-950 shadow-xl space-y-3 relative overflow-hidden ${className}`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className="p-1.5 rounded-lg bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
            <Sparkles className="w-4 h-4 animate-pulse" />
          </div>
          <span className="text-xs font-bold text-white tracking-tight">{title}</span>
        </div>

        <div className="flex items-center space-x-2">
          <Badge variant="purple" size="sm">
            {displayModel}
          </Badge>
          <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
            {confidencePct}% Confidence
          </span>
        </div>
      </div>

      <p className="text-xs text-slate-300 leading-relaxed font-medium">
        {displayReasoning}
      </p>

      {impactMetrics && impactMetrics.length > 0 ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 p-2.5 rounded-xl bg-slate-950/80 border border-white/5 text-xs">
          {impactMetrics.map((m, idx) => (
            <div key={idx} className="space-y-0.5">
              <span className="text-[10px] text-slate-400 block uppercase">{m.label}</span>
              <span className="font-bold text-white font-mono">{m.value}</span>
            </div>
          ))}
        </div>
      ) : impactPreview ? (
        <div className="p-3 rounded-xl bg-slate-950/80 border border-white/5 flex items-center justify-between text-xs text-slate-400">
          <div className="flex items-center space-x-1.5 text-emerald-400 font-semibold">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Expected Benefit:</span>
          </div>
          <span className="font-bold text-white">{impactPreview}</span>
        </div>
      ) : null}

      <div className="pt-1 flex items-center justify-between">
        <span className="text-[10px] text-slate-500 flex items-center">
          <HelpCircle className="w-3 h-3 mr-1" /> Transparent explainable AI
        </span>

        <Button
          variant={isApplied ? 'secondary' : 'ai'}
          size="sm"
          onClick={onApply}
          disabled={isApplied}
          rightIcon={!isApplied && <ChevronRight className="w-3.5 h-3.5" />}
        >
          {isApplied ? 'Applied' : (actionLabel || 'Apply Recommendation')}
        </Button>
      </div>
    </div>
  );
};
