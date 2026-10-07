import React from 'react';

export const Card = ({ children, className = '', hover = false, padding = 'p-6' }) => {
  return (
    <div
      className={`bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800/80 shadow-sm ${
        hover ? 'hover:shadow-md hover:border-slate-300 dark:hover:border-slate-700 transition-all duration-200' : ''
      } ${padding} ${className}`}
    >
      {children}
    </div>
  );
};
