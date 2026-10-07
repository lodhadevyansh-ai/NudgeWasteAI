import { Card } from '../common/Card';
import { TrendingUp, Calendar } from 'lucide-react';

export const SegregationTrendChart = ({ trends = [], title = 'Segregation activity', subtitle = 'Verified items over the past days' }) => {
  const hasData = trends && trends.length > 0 && trends.some((t) => t.total_disposals > 0);

  if (!hasData) {
    return (
      <Card className="flex flex-col justify-between min-h-[300px]">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-base font-bold text-slate-900 dark:text-white">{title}</h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{subtitle}</p>
          </div>
          <span className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400">
            <TrendingUp className="w-3.5 h-3.5" /> 0%
          </span>
        </div>

        <div className="flex-1 flex flex-col items-center justify-center p-6 text-center border border-dashed border-slate-200 dark:border-slate-800 rounded-xl bg-slate-50/50 dark:bg-slate-900/30">
          <Calendar className="w-10 h-10 text-slate-300 dark:text-slate-700 mb-2" />
          <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">No activity recorded yet</p>
          <p className="text-xs text-slate-400 dark:text-slate-500 mt-1 max-w-xs">
            Scan waste items to start building your daily segregation timeline.
          </p>
        </div>
      </Card>
    );
  }

  // Calculate SVG line points for actual time-series data
  const maxVal = Math.max(...trends.map((t) => t.total_disposals), 5);
  const width = 500;
  const height = 180;
  const padding = 20;

  const points = trends.map((t, idx) => {
    const x = padding + (idx / Math.max(1, trends.length - 1)) * (width - 2 * padding);
    const y = height - padding - (t.total_disposals / maxVal) * (height - 2 * padding);
    return `${x},${y}`;
  });

  const pathD = `M ${points.join(' L ')}`;
  const areaD = `M ${padding},${height - padding} L ${points.join(' L ')} L ${width - padding},${height - padding} Z`;

  return (
    <Card className="flex flex-col justify-between">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-base font-bold text-slate-900 dark:text-white">{title}</h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{subtitle}</p>
        </div>
        <span className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
          <TrendingUp className="w-3.5 h-3.5" /> Active
        </span>
      </div>

      <div className="w-full overflow-hidden">
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-auto overflow-visible">
          <defs>
            <linearGradient id="trendGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#10B981" stopOpacity="0.3" />
              <stop offset="100%" stopColor="#10B981" stopOpacity="0.0" />
            </linearGradient>
          </defs>

          {/* Area Fill */}
          <path d={areaD} fill="url(#trendGradient)" />

          {/* Curved Trend Line */}
          <path d={pathD} fill="none" stroke="#10B981" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />

          {/* Data Points */}
          {trends.map((t, idx) => {
            const x = padding + (idx / Math.max(1, trends.length - 1)) * (width - 2 * padding);
            const y = height - padding - (t.total_disposals / maxVal) * (height - 2 * padding);
            return (
              <circle
                key={idx}
                cx={x}
                cy={y}
                r="4"
                fill="#FFFFFF"
                stroke="#10B981"
                strokeWidth="2.5"
                className="hover:r-6 transition-all cursor-pointer"
              />
            );
          })}
        </svg>
      </div>

      {/* X-Axis Labels */}
      <div className="flex justify-between items-center text-[10px] text-slate-400 font-medium pt-2 border-t border-slate-100 dark:border-slate-800/80">
        {trends.slice(-7).map((t, i) => (
          <span key={i}>{t.date?.slice(5) || `Day ${i + 1}`}</span>
        ))}
      </div>
    </Card>
  );
};
