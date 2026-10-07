import React from 'react';
import { NavLink } from 'react-router-dom';
import { ScanLine, ArrowRight } from 'lucide-react';

export const EmptyState = ({
  icon: Icon = ScanLine,
  title = 'No items found',
  description = 'Your activity will appear here as you interact with NudgeWasteAI.',
  actionLabel = 'Scan Waste Item',
  actionPath = '/scanner',
}) => {
  return (
    <div className="flex flex-col items-center justify-center p-8 md:p-12 text-center rounded-2xl bg-slate-50/50 dark:bg-slate-900/40 border border-dashed border-slate-200 dark:border-slate-800">
      <div className="w-14 h-14 rounded-2xl bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 flex items-center justify-center mb-4 shadow-sm border border-emerald-100 dark:border-emerald-900/50">
        <Icon className="w-7 h-7" />
      </div>
      <h3 className="text-base font-bold text-slate-900 dark:text-white mb-1">
        {title}
      </h3>
      <p className="text-xs md:text-sm text-slate-500 dark:text-slate-400 max-w-md mb-6 leading-relaxed">
        {description}
      </p>

      {actionLabel && actionPath && (
        <NavLink
          to={actionPath}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs md:text-sm shadow-md shadow-emerald-600/20 transition-all hover:scale-[1.02] active:scale-[0.98]"
        >
          <span>{actionLabel}</span>
          <ArrowRight className="w-4 h-4" />
        </NavLink>
      )}
    </div>
  );
};
