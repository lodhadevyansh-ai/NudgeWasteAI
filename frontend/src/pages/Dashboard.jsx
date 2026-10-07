import React, { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { creditsApi } from '../api/creditsApi';
import { analyticsApi } from '../api/analyticsApi';
import { disposalApi } from '../api/disposalApi';
import { Card } from '../components/common/Card';
import { CategoryBadge, StatusBadge } from '../components/common/Badge';
import { SegregationTrendChart } from '../components/charts/SegregationTrendChart';
import { WasteStreamDistributionChart } from '../components/charts/WasteStreamDistributionChart';
import { EmptyState } from '../components/common/EmptyState';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import {
  Coins,
  CheckCircle2,
  Zap,
  Leaf,
  ScanLine,
  X,
  ArrowRight,
} from 'lucide-react';

export const Dashboard = () => {
  const { user } = useAuth();

  const [creditBalance, setCreditBalance] = useState(user?.swachh_credits || 500);
  const [userAnalytics, setUserAnalytics] = useState(null);
  const [wasteDist, setWasteDist] = useState(null);
  const [trends, setTrends] = useState([]);
  const [recentScans, setRecentScans] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showBanner, setShowBanner] = useState(true);

  useEffect(() => {
    let isMounted = true;

    const fetchDashboardData = async () => {
      try {
        const [balRes, analyticsRes, distRes, trendsRes, historyRes] = await Promise.all([
          creditsApi.getBalance().catch(() => null),
          analyticsApi.getUserSummary().catch(() => null),
          analyticsApi.getWasteDistribution().catch(() => null),
          analyticsApi.getTrends(7).catch(() => null),
          disposalApi.getHistory(5, 0).catch(() => []),
        ]);

        if (isMounted) {
          if (balRes?.swachh_credits !== undefined) {
            setCreditBalance(balRes.swachh_credits);
          }
          setUserAnalytics(analyticsRes);
          setWasteDist(distRes);
          if (trendsRes?.daily_trends) {
            setTrends(trendsRes.daily_trends);
          }
          if (Array.isArray(historyRes)) {
            setRecentScans(historyRes);
          }
        }
      } catch (err) {
        console.warn('Dashboard data fetch error:', err);
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    fetchDashboardData();

    return () => {
      isMounted = false;
    };
  }, []);

  // Dynamic Time-of-Day Greeting
  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 17) return 'Good afternoon';
    return 'Good evening';
  };

  const userName = user?.name ? user.name.split(' ')[0] : 'Citizen';
  const verifiedCount = userAnalytics?.verified_disposals || recentScans.length || 0;
  const totalAttempts = userAnalytics?.total_disposal_attempts || recentScans.length || 0;

  // Derive realistic waste diverted weight (avg 0.2 kg per item)
  const wasteDivertedKg = (verifiedCount * 0.2).toFixed(1);

  if (isLoading) {
    return <LoadingSpinner label="Loading your civic dashboard..." />;
  }

  return (
    <div className="space-y-6">
      {/* Top Banner Alert (Dismissible) */}
      {showBanner && (
        <div className="flex items-center justify-between p-4 rounded-2xl bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-200 dark:border-emerald-800 text-emerald-900 dark:text-emerald-200 text-xs md:text-sm font-medium shadow-2xs transition-all">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400 shrink-0" />
            <span>Account ready. Welcome to NudgeWasteAI! You have received 500 Swachh Credits.</span>
          </div>
          <button
            onClick={() => setShowBanner(false)}
            className="p-1 rounded-lg hover:bg-emerald-100 dark:hover:bg-emerald-900/60 text-emerald-700 dark:text-emerald-300"
            aria-label="Dismiss banner"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Greeting Header */}
      <div>
        <h2 className="text-2xl md:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
          {getGreeting()}, {userName}
        </h2>
        <p className="text-xs md:text-sm text-slate-500 dark:text-slate-400 mt-1">
          {verifiedCount === 0
            ? 'Start your civic impact journey today by scanning your first waste item.'
            : `${verifiedCount} verified disposals recorded. Keep the momentum going.`}
        </p>
      </div>

      {/* 4 Stat Cards Grid (Inspired by design reference screenshot 3) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Stat Card 1: Swachh Credits */}
        <Card hover padding="p-5" className="relative overflow-hidden">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold text-slate-500 dark:text-slate-400">Swachh Credits</span>
            <div className="w-8 h-8 rounded-xl bg-emerald-50 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
              <Coins className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl md:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
            {Number(creditBalance).toLocaleString('en-IN')}
          </div>
          <p className="text-[11px] font-semibold text-emerald-600 dark:text-emerald-400 mt-1">
            {verifiedCount === 0 ? 'Welcome bonus' : `Active credit points`}
          </p>
        </Card>

        {/* Stat Card 2: Items Segregated */}
        <Card hover padding="p-5" className="relative overflow-hidden">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold text-slate-500 dark:text-slate-400">Items Segregated</span>
            <div className="w-8 h-8 rounded-xl bg-blue-50 dark:bg-blue-950 text-blue-600 dark:text-blue-400 flex items-center justify-center">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl md:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
            {verifiedCount}
          </div>
          <p className="text-[11px] font-semibold text-slate-400 mt-1">
            {verifiedCount === 0 ? 'Start scanning waste' : `${totalAttempts} total attempts`}
          </p>
        </Card>

        {/* Stat Card 3: Current Streak */}
        <Card hover padding="p-5" className="relative overflow-hidden">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold text-slate-500 dark:text-slate-400">Current Streak</span>
            <div className="w-8 h-8 rounded-xl bg-amber-50 dark:bg-amber-950 text-amber-600 dark:text-amber-400 flex items-center justify-center">
              <Zap className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl md:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
            {verifiedCount > 0 ? '1 day' : '0 days'}
          </div>
          <p className="text-[11px] font-semibold text-slate-400 mt-1">
            {verifiedCount > 0 ? 'Streak active' : 'Start your streak'}
          </p>
        </Card>

        {/* Stat Card 4: Waste Diverted */}
        <Card hover padding="p-5" className="relative overflow-hidden">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold text-slate-500 dark:text-slate-400">Waste Diverted</span>
            <div className="w-8 h-8 rounded-xl bg-emerald-50 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
              <Leaf className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl md:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
            {wasteDivertedKg} <span className="text-base font-bold text-slate-400">kg</span>
          </div>
          <p className="text-[11px] font-semibold text-slate-400 mt-1">
            Estimated total
          </p>
        </Card>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <SegregationTrendChart
            trends={trends}
            title="Segregation activity"
            subtitle="Verified items over the past seven days"
          />
        </div>
        <div>
          <WasteStreamDistributionChart
            distributionData={wasteDist || {}}
            title="Waste streams"
            subtitle="All-time distribution"
          />
        </div>
      </div>

      {/* Recent Activity / Scan History Table */}
      <Card className="space-y-4">
        <div className="flex items-center justify-between pb-2 border-b border-slate-100 dark:border-slate-800">
          <div>
            <h3 className="text-base font-bold text-slate-900 dark:text-white">
              Recent Segregation Scans
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Your latest verified waste disposal events
            </p>
          </div>

          <NavLink
            to="/history"
            className="inline-flex items-center gap-1 text-xs font-bold text-emerald-600 dark:text-emerald-400 hover:underline"
          >
            <span>View all</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </NavLink>
        </div>

        {recentScans.length === 0 ? (
          <EmptyState
            icon={ScanLine}
            title="No scans yet"
            description="Your verified waste scans will appear here."
            actionLabel="Scan your first item"
            actionPath="/scanner"
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs md:text-sm">
              <thead>
                <tr className="text-slate-400 uppercase text-[10px] font-bold tracking-wider border-b border-slate-100 dark:border-slate-800">
                  <th className="pb-3 px-2">Item</th>
                  <th className="pb-3 px-2">Category</th>
                  <th className="pb-3 px-2">Status</th>
                  <th className="pb-3 px-2">Credits</th>
                  <th className="pb-3 px-2 text-right">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 font-medium text-slate-800 dark:text-slate-200">
                {recentScans.map((scan) => (
                  <tr key={scan.disposal_id || scan.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40">
                    <td className="py-3 px-2 font-semibold text-slate-900 dark:text-white">
                      {scan.item_label || 'Scanned Waste'}
                    </td>
                    <td className="py-3 px-2">
                      <CategoryBadge category={scan.confirmed_category || scan.predicted_category} />
                    </td>
                    <td className="py-3 px-2">
                      <StatusBadge status={scan.verification_status} />
                    </td>
                    <td className="py-3 px-2 font-bold text-emerald-600 dark:text-emerald-400">
                      +{scan.credits_awarded || 10}
                    </td>
                    <td className="py-3 px-2 text-right text-xs text-slate-400">
                      {scan.timestamp ? new Date(scan.timestamp).toLocaleDateString() : 'Today'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
};
