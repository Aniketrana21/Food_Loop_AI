import React from 'react';
import { AlertCircle, CheckCircle2, Info, AlertTriangle, X } from 'lucide-react';

export interface AlertProps {
  variant?: 'info' | 'success' | 'warning' | 'error';
  title?: string;
  children: React.ReactNode;
  onDismiss?: () => void;
  className?: string;
}

export const Alert: React.FC<AlertProps> = ({
  variant = 'info',
  title,
  children,
  onDismiss,
  className = '',
}) => {
  const variantStyles = {
    info: 'bg-indigo-950/40 border-indigo-500/30 text-indigo-200',
    success: 'bg-emerald-950/40 border-emerald-500/30 text-emerald-200',
    warning: 'bg-amber-950/40 border-amber-500/30 text-amber-200',
    error: 'bg-rose-950/40 border-rose-500/30 text-rose-200',
  };

  const icons = {
    info: <Info className="w-5 h-5 text-indigo-400 shrink-0 mt-0.5" />,
    success: <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />,
    warning: <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />,
    error: <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />,
  };

  return (
    <div className={`p-4 rounded-2xl border flex items-start justify-between gap-3 text-xs leading-relaxed animate-fade-in ${variantStyles[variant]} ${className}`}>
      <div className="flex items-start space-x-3">
        {icons[variant]}
        <div className="space-y-0.5">
          {title && <h5 className="font-bold tracking-tight text-white">{title}</h5>}
          <div>{children}</div>
        </div>
      </div>
      {onDismiss && (
        <button onClick={onDismiss} className="p-1 rounded-lg hover:bg-white/10 text-slate-400 hover:text-white transition-colors">
          <X className="w-4 h-4" />
        </button>
      )}
    </div>
  );
};
