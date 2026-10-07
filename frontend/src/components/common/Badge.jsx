import React from 'react';
import { CATEGORY_DETAILS } from '../../constants/categories';

export const CategoryBadge = ({ category }) => {
  const details = CATEGORY_DETAILS[category] || {
    name: category || 'Unknown',
    bgColor: '#F1F5F9',
    borderColor: '#E2E8F0',
    textColor: '#475569',
  };

  return (
    <span
      style={{
        backgroundColor: details.bgColor,
        borderColor: details.borderColor,
        color: details.textColor,
      }}
      className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold border tracking-wide shadow-2xs"
    >
      {details.name}
    </span>
  );
};

export const StatusBadge = ({ status }) => {
  const isVerified = status === 'verified';
  const isIncorrect = status === 'incorrect';

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${
        isVerified
          ? 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/60 dark:text-emerald-300 dark:border-emerald-800'
          : isIncorrect
          ? 'bg-red-50 text-red-700 border-red-200 dark:bg-red-950/60 dark:text-red-300 dark:border-red-800'
          : 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/60 dark:text-amber-300 dark:border-amber-800'
      }`}
    >
      {status ? status.charAt(0).toUpperCase() + status.slice(1) : 'Pending'}
    </span>
  );
};
