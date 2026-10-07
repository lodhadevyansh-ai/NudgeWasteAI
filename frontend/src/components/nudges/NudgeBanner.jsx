import { Sparkles, AlertTriangle } from 'lucide-react';

export const NudgeBanner = ({ nudge, category, severity = 'information' }) => {
  if (!nudge) return null;

  const isWarning = severity === 'warning';

  return (
    <div
      className={`p-4 rounded-2xl border flex items-start gap-3 transition-all ${
        isWarning
          ? 'bg-amber-50 dark:bg-amber-950/40 border-amber-200 dark:border-amber-800 text-amber-900 dark:text-amber-200'
          : 'bg-emerald-50/80 dark:bg-emerald-950/40 border-emerald-200 dark:border-emerald-800/80 text-emerald-900 dark:text-emerald-200'
      }`}
    >
      <div
        className={`p-2 rounded-xl shrink-0 mt-0.5 ${
          isWarning
            ? 'bg-amber-100 dark:bg-amber-900 text-amber-700 dark:text-amber-300'
            : 'bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-300'
        }`}
      >
        {isWarning ? <AlertTriangle className="w-5 h-5" /> : <Sparkles className="w-5 h-5" />}
      </div>

      <div className="flex-1">
        <h4 className="text-xs font-bold uppercase tracking-wider mb-1 flex items-center gap-1.5">
          <span>{isWarning ? 'Segregation Guidance' : 'Positive Micro-Nudge'}</span>
          {category && <span className="opacity-75">• {category} Stream</span>}
        </h4>
        <p className="text-sm font-medium leading-relaxed">{nudge}</p>
      </div>
    </div>
  );
};
