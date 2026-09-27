import React from 'react';
import { Inbox, RotateCcw, AlertTriangle } from 'lucide-react';
import { Button } from './Button';

export interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description: string;
  actionText?: string;
  onAction?: () => void;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon = <Inbox className="w-10 h-10 text-slate-500" />,
  title,
  description,
  actionText,
  onAction,
  className = '',
}) => {
  return (
    <div className={`p-10 rounded-2xl glass-panel border border-white/5 flex flex-col items-center justify-center text-center space-y-3 ${className}`}>
      <div className="p-3.5 rounded-2xl bg-slate-900 border border-white/10 text-slate-400 shadow-inner">
        {icon}
      </div>
      <div className="space-y-1 max-w-sm">
        <h4 className="text-sm font-bold text-white tracking-tight">{title}</h4>
        <p className="text-xs text-slate-400 leading-relaxed">{description}</p>
      </div>
      {actionText && onAction && (
        <div className="pt-2">
          <Button variant="primary" size="sm" onClick={onAction}>
            {actionText}
          </Button>
        </div>
      )}
    </div>
  );
};

export interface ErrorStateProps {
  title?: string;
  error?: string;
  onRetry?: () => void;
  className?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Failed to load telemetry',
  error = 'Unable to establish real-time connection with data services. Please check credentials or try again.',
  onRetry,
  className = '',
}) => {
  return (
    <div className={`p-8 rounded-2xl bg-rose-950/20 border border-rose-500/20 flex flex-col items-center justify-center text-center space-y-3 ${className}`}>
      <div className="p-3 rounded-2xl bg-rose-500/10 text-rose-400 border border-rose-500/30">
        <AlertTriangle className="w-6 h-6" />
      </div>
      <div className="space-y-1 max-w-sm">
        <h4 className="text-sm font-bold text-rose-300">{title}</h4>
        <p className="text-xs text-slate-400 leading-relaxed">{error}</p>
      </div>
      {onRetry && (
        <div className="pt-2">
          <Button variant="outline" size="sm" onClick={onRetry} leftIcon={<RotateCcw className="w-3.5 h-3.5" />}>
            Retry Request
          </Button>
        </div>
      )}
    </div>
  );
};
