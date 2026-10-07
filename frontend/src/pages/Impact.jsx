import { useState, useEffect } from 'react';
import { analyticsApi } from '../api/analyticsApi';
import { Card } from '../components/common/Card';
import { SegregationTrendChart } from '../components/charts/SegregationTrendChart';
import { WasteStreamDistributionChart } from '../components/charts/WasteStreamDistributionChart';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { CheckCircle2, Leaf, Zap, ShieldCheck } from 'lucide-react';

export const Impact = () => {
  const [summary, setSummary] = useState(null);
  const [distribution, setDistribution] = useState(null);
  const [trends, setTrends] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    const fetchImpactData = async () => {
      try {
        const [summaryRes, distRes, trendsRes] = await Promise.all([
          analyticsApi.getUserSummary().catch(() => null),
          analyticsApi.getWasteDistribution().catch(() => null),
          analyticsApi.getTrends(30).catch(() => null),
        ]);

        if (isMounted) {
          setSummary(summaryRes);
          setDistribution(distRes);
          if (trendsRes?.daily_trends) setTrends(trendsRes.daily_trends);
        }
      } catch (err) {
        console.warn('Impact analytics error:', err);
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    fetchImpactData();

    return () => {
      isMounted = false;
    };
  }, []);

  const verifiedDisposals = summary?.verified_disposals || 0;
  const segregationRate = summary?.correct_segregation_rate || 0.0;
  const wasteDivertedKg = (verifiedDisposals * 0.2).toFixed(1);

  if (isLoading) {
    return <LoadingSpinner label="Aggregating your civic impact analytics..." />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-extrabold text-slate-900 dark:text-white tracking-tight">
          Civic Impact Analytics
        </h2>
        <p className="text-xs md:text-sm text-slate-500 dark:text-slate-400 mt-1">
          Your personal environmental contribution to municipal waste diversion
        </p>
      </div>

      {/* Impact Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card padding="p-5" className="flex flex-col justify-between">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-500 dark:text-slate-400">Total Segregated</span>
            <div className="p-2 rounded-xl bg-emerald-50 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-slate-900 dark:text-white">
            {verifiedDisposals}
          </div>
          <p className="text-[11px] font-semibold text-slate-400 mt-1">Verified waste items</p>
        </Card>

        <Card padding="p-5" className="flex flex-col justify-between">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-500 dark:text-slate-400">Segregation Accuracy</span>
            <div className="p-2 rounded-xl bg-blue-50 dark:bg-blue-950 text-blue-600 dark:text-blue-400">
              <ShieldCheck className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-slate-900 dark:text-white">
            {segregationRate}%
          </div>
          <p className="text-[11px] font-semibold text-slate-400 mt-1">Accuracy rate</p>
        </Card>

        <Card padding="p-5" className="flex flex-col justify-between">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-500 dark:text-slate-400">Waste Diverted</span>
            <div className="p-2 rounded-xl bg-teal-50 dark:bg-teal-950 text-teal-600 dark:text-teal-400">
              <Leaf className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-slate-900 dark:text-white">
            {wasteDivertedKg} <span className="text-base font-bold text-slate-400">kg</span>
          </div>
          <p className="text-[11px] font-semibold text-slate-400 mt-1">Diverted from landfills</p>
        </Card>

        <Card padding="p-5" className="flex flex-col justify-between">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-500 dark:text-slate-400">Active Streak</span>
            <div className="p-2 rounded-xl bg-amber-50 dark:bg-amber-950 text-amber-600 dark:text-amber-400">
              <Zap className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-slate-900 dark:text-white">
            {verifiedDisposals > 0 ? '1 day' : '0 days'}
          </div>
          <p className="text-[11px] font-semibold text-slate-400 mt-1">Daily segregation streak</p>
        </Card>
      </div>

      {/* Analytics Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <SegregationTrendChart
            trends={trends}
            title="30-Day Segregation Timeline"
            subtitle="Daily verified waste items"
          />
        </div>

        <div>
          <WasteStreamDistributionChart
            distributionData={distribution || {}}
            title="Waste Stream Breakdown"
            subtitle="Volume percentage across categories"
          />
        </div>
      </div>
    </div>
  );
};
