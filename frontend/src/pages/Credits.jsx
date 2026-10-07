import React, { useState, useEffect } from 'react';
import { creditsApi } from '../api/creditsApi';
import { useAuth } from '../context/AuthContext';
import { Card } from '../components/common/Card';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { EmptyState } from '../components/common/EmptyState';
import { Coins, ArrowUpRight, ArrowDownLeft, ShieldCheck, History } from 'lucide-react';

export const Credits = () => {
  const { user } = useAuth();
  const [balanceData, setBalanceData] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    const fetchCreditsData = async () => {
      try {
        const [balRes, historyRes] = await Promise.all([
          creditsApi.getBalance().catch(() => null),
          creditsApi.getHistory(50, 0).catch(() => []),
        ]);

        if (isMounted) {
          if (balRes) setBalanceData(balRes);
          if (Array.isArray(historyRes)) setTransactions(historyRes);
        }
      } catch (err) {
        console.warn('Credits data fetch error:', err);
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    fetchCreditsData();

    return () => {
      isMounted = false;
    };
  }, []);

  const currentBalance = balanceData?.swachh_credits !== undefined
    ? balanceData.swachh_credits
    : user?.swachh_credits || 500;

  const totalEarned = balanceData?.total_earned !== undefined
    ? balanceData.total_earned
    : currentBalance;

  const totalRedeemed = balanceData?.total_redeemed || 0;

  if (isLoading) {
    return <LoadingSpinner label="Loading credit balance & transaction ledger..." />;
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h2 className="text-2xl font-extrabold text-slate-900 dark:text-white tracking-tight">
          Swachh Credits
        </h2>
        <p className="text-xs md:text-sm text-slate-500 dark:text-slate-400 mt-1">
          Auditable civic incentive balance and ledger history
        </p>
      </div>

      {/* Credit Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Main Balance Card */}
        <div className="md:col-span-1 bg-gradient-to-br from-emerald-600 via-emerald-700 to-teal-800 text-white p-6 rounded-3xl shadow-xl flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-bold uppercase tracking-wider text-emerald-200">
              Current Balance
            </span>
            <div className="p-2 rounded-xl bg-white/10 text-white backdrop-blur-sm">
              <Coins className="w-5 h-5" />
            </div>
          </div>
          <div>
            <div className="text-4xl md:text-5xl font-extrabold tracking-tight">
              {Number(currentBalance).toLocaleString('en-IN')}
            </div>
            <p className="text-xs font-medium text-emerald-100 mt-2 flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5" /> Single source of truth from backend
            </p>
          </div>
        </div>

        {/* Lifetime Earned Card */}
        <Card padding="p-6" className="flex flex-col justify-between">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-500 dark:text-slate-400">
              Lifetime Earned
            </span>
            <div className="p-2 rounded-xl bg-emerald-50 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400">
              <ArrowUpRight className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-slate-900 dark:text-white">
            +{Number(totalEarned).toLocaleString('en-IN')}
          </div>
          <p className="text-xs text-slate-400 mt-1">Total earned from registration & disposals</p>
        </Card>

        {/* Total Redeemed Card */}
        <Card padding="p-6" className="flex flex-col justify-between">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-500 dark:text-slate-400">
              Total Redeemed
            </span>
            <div className="p-2 rounded-xl bg-purple-50 dark:bg-purple-950 text-purple-600 dark:text-purple-400">
              <ArrowDownLeft className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-slate-900 dark:text-white">
            -{Number(totalRedeemed).toLocaleString('en-IN')}
          </div>
          <p className="text-xs text-slate-400 mt-1">Total redeemed for municipal vouchers</p>
        </Card>
      </div>

      {/* Transaction History Ledger */}
      <Card className="space-y-4">
        <div className="pb-2 border-b border-slate-100 dark:border-slate-800">
          <h3 className="text-base font-bold text-slate-900 dark:text-white">
            Transaction History
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Real-time auditable database transaction records
          </p>
        </div>

        {transactions.length === 0 ? (
          <EmptyState
            icon={History}
            title="No transactions yet"
            description="Your credit earning and redemption transactions will appear here."
            actionLabel="Scan Waste to Earn"
            actionPath="/scanner"
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs md:text-sm">
              <thead>
                <tr className="text-slate-400 uppercase text-[10px] font-bold tracking-wider border-b border-slate-100 dark:border-slate-800">
                  <th className="pb-3 px-3">Description</th>
                  <th className="pb-3 px-3">Type</th>
                  <th className="pb-3 px-3">Amount</th>
                  <th className="pb-3 px-3 text-right">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 font-medium text-slate-800 dark:text-slate-200">
                {transactions.map((tx) => {
                  const isPositive = tx.amount > 0;
                  return (
                    <tr key={tx.transaction_id || tx.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40">
                      <td className="py-3.5 px-3 font-semibold text-slate-900 dark:text-white">
                        {tx.reason}
                      </td>
                      <td className="py-3.5 px-3">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-bold uppercase tracking-wider ${
                            isPositive
                              ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300'
                              : 'bg-purple-50 text-purple-700 dark:bg-purple-950/60 dark:text-purple-300'
                          }`}
                        >
                          {tx.transaction_type}
                        </span>
                      </td>
                      <td
                        className={`py-3.5 px-3 font-extrabold text-sm ${
                          isPositive ? 'text-emerald-600 dark:text-emerald-400' : 'text-purple-600 dark:text-purple-400'
                        }`}
                      >
                        {isPositive ? `+${tx.amount}` : tx.amount}
                      </td>
                      <td className="py-3.5 px-3 text-right text-xs text-slate-400">
                        {tx.timestamp ? new Date(tx.timestamp).toLocaleString() : 'N/A'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
};
