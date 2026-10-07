import React from 'react';
import { Card } from '../common/Card';
import { STATUTORY_CATEGORIES, CATEGORY_DETAILS } from '../../constants/categories';

export const WasteStreamDistributionChart = ({
  distributionData = {},
  title = 'Waste streams',
  subtitle = 'All-time distribution across statutory categories',
}) => {
  const counts = distributionData.waste_counts_by_stream || {
    [STATUTORY_CATEGORIES.DRY]: 0,
    [STATUTORY_CATEGORIES.WET]: 0,
    [STATUTORY_CATEGORIES.SANITARY]: 0,
    [STATUTORY_CATEGORIES.SPECIAL_CARE]: 0,
  };

  const total = Object.values(counts).reduce((sum, val) => sum + val, 0);

  const categories = [
    { key: STATUTORY_CATEGORIES.DRY, label: 'Dry', color: CATEGORY_DETAILS[STATUTORY_CATEGORIES.DRY].binColor },
    { key: STATUTORY_CATEGORIES.WET, label: 'Wet', color: CATEGORY_DETAILS[STATUTORY_CATEGORIES.WET].binColor },
    { key: STATUTORY_CATEGORIES.SANITARY, label: 'Sanitary', color: CATEGORY_DETAILS[STATUTORY_CATEGORIES.SANITARY].binColor },
    { key: STATUTORY_CATEGORIES.SPECIAL_CARE, label: 'Special Care', color: CATEGORY_DETAILS[STATUTORY_CATEGORIES.SPECIAL_CARE].binColor },
  ];

  // Calculate SVG donut stroke offsets
  let accumulatedAngle = 0;
  const strokeWidth = 24;
  const radius = 60;
  const circumference = 2 * Math.PI * radius;

  const arcs = categories.map((cat) => {
    const val = counts[cat.key] || 0;
    const pct = total > 0 ? val / total : 0;
    const strokeDasharray = `${pct * circumference} ${circumference}`;
    const strokeDashoffset = -accumulatedAngle * circumference;
    accumulatedAngle += pct;

    return {
      ...cat,
      count: val,
      percentage: Math.round(pct * 100),
      strokeDasharray,
      strokeDashoffset,
    };
  });

  return (
    <Card className="flex flex-col justify-between">
      <div className="mb-4">
        <h3 className="text-base font-bold text-slate-900 dark:text-white">{title}</h3>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{subtitle}</p>
      </div>

      <div className="flex flex-col sm:flex-row items-center justify-between gap-6 py-2">
        {/* Donut Chart SVG */}
        <div className="relative w-40 h-40 flex items-center justify-center shrink-0">
          <svg viewBox="0 0 160 160" className="w-full h-full transform -rotate-90">
            {/* Background Circle */}
            <circle
              cx="80"
              cy="80"
              r={radius}
              fill="transparent"
              stroke="currentColor"
              strokeWidth={strokeWidth}
              className="text-slate-100 dark:text-slate-800"
            />

            {/* Category Donut Segments */}
            {total > 0 &&
              arcs.map((arc) =>
                arc.percentage > 0 ? (
                  <circle
                    key={arc.key}
                    cx="80"
                    cy="80"
                    r={radius}
                    fill="transparent"
                    stroke={arc.color}
                    strokeWidth={strokeWidth}
                    strokeDasharray={arc.strokeDasharray}
                    strokeDashoffset={arc.strokeDashoffset}
                    strokeLinecap="butt"
                    className="transition-all duration-500 hover:opacity-90"
                  />
                ) : null
              )}
          </svg>

          {/* Center Text */}
          <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
            <span className="text-2xl font-extrabold text-slate-900 dark:text-white leading-none">
              {total}
            </span>
            <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mt-1">
              Items
            </span>
          </div>
        </div>

        {/* Categories Legend List */}
        <div className="flex-1 w-full space-y-2.5">
          {arcs.map((arc) => (
            <div key={arc.key} className="flex items-center justify-between text-xs">
              <div className="flex items-center gap-2">
                <span
                  className="w-2.5 h-2.5 rounded-full shrink-0"
                  style={{ backgroundColor: arc.color }}
                />
                <span className="font-semibold text-slate-700 dark:text-slate-300">
                  {arc.label}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-slate-900 dark:text-white">
                  {total > 0 ? `${arc.percentage}%` : '0%'}
                </span>
                <span className="text-slate-400 text-[11px] min-w-[28px] text-right">
                  ({arc.count})
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
};
