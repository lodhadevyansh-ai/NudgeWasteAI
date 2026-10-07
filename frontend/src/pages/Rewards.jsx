import React, { useState, useEffect } from 'react';
import { rewardsApi } from '../api/rewardsApi';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { Card } from '../components/common/Card';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { Modal } from '../components/common/Modal';
import { Gift, Coins, CheckCircle2, Ticket, AlertCircle, Loader2 } from 'lucide-react';

export const Rewards = () => {
  const { user, refreshUser } = useAuth();
  const { showSuccess, showError } = useToast();

  const [catalog, setCatalog] = useState([]);
  const [redemptions, setRedemptions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedReward, setSelectedReward] = useState(null);
  const [isRedeeming, setIsRedeeming] = useState(false);

  useEffect(() => {
    let isMounted = true;

    const fetchData = async () => {
      try {
        const [catRes, redRes] = await Promise.all([
          rewardsApi.getCatalog().catch(() => []),
          rewardsApi.getMyRedemptions().catch(() => []),
        ]);

        if (isMounted) {
          if (Array.isArray(catRes)) setCatalog(catRes);
          if (Array.isArray(redRes)) setRedemptions(redRes);
        }
      } catch (err) {
        console.warn('Rewards catalog fetch error:', err);
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    fetchData();

    return () => {
      isMounted = false;
    };
  }, []);

  const currentBalance = user?.swachh_credits !== undefined ? user.swachh_credits : 500;

  const handleOpenConfirm = (reward) => {
    setSelectedReward(reward);
  };

  const handleRedeem = async () => {
    if (!selectedReward) return;
    const cost = Number(selectedReward.credit_cost ?? selectedReward.cost_credits ?? selectedReward.credits_required ?? 0);

    if (currentBalance < cost) {
      const needed = cost - currentBalance;
      showError(`Insufficient Swachh Credits. You need ${needed} more credits.`);
      setSelectedReward(null);
      return;
    }

    setIsRedeeming(true);
    try {
      const res = await rewardsApi.redeemReward(selectedReward.reward_id);

      // Refresh user balance authoritatively from backend
      await refreshUser();

      // Refresh user redemptions list
      const updatedReds = await rewardsApi.getMyRedemptions().catch(() => []);
      setRedemptions(updatedReds);

      showSuccess(`Reward redeemed! Claim Voucher Code: ${res.redemption_code}`);
      setSelectedReward(null);
    } catch (err) {
      showError(err.message || 'Insufficient Swachh Credits.');
    } finally {
      setIsRedeeming(false);
    }
  };

  if (isLoading) {
    return <LoadingSpinner label="Loading municipal rewards catalog..." />;
  }

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-extrabold text-slate-900 dark:text-white tracking-tight">
            Municipal Rewards Marketplace
          </h2>
          <p className="text-xs md:text-sm text-slate-500 dark:text-slate-400 mt-1">
            Redeem your earned Swachh Credits for municipal vouchers & property tax rebates
          </p>
        </div>

        <div className="flex items-center gap-2 px-4 py-2 rounded-2xl bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-200 shadow-2xs self-start">
          <Coins className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
          <span className="text-xs font-semibold">Your Balance:</span>
          <span className="text-base font-extrabold">{Number(currentBalance).toLocaleString('en-IN')} credits</span>
        </div>
      </div>

      {/* Rewards Catalog Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {catalog.map((reward) => {
          const cost = Number(reward.credit_cost ?? reward.cost_credits ?? reward.credits_required ?? 0);
          const canAfford = currentBalance >= cost;

          return (
            <Card key={reward.reward_id || reward.id} hover padding="p-6" className="flex flex-col justify-between">
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-3">
                  <div className="p-3 rounded-2xl bg-emerald-50 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 border border-emerald-100 dark:border-emerald-900/50">
                    <Gift className="w-6 h-6" />
                  </div>

                  <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-white text-xs font-bold border border-slate-200 dark:border-slate-700">
                    <Coins className="w-3.5 h-3.5 text-emerald-600" /> Cost: {cost} credits
                  </span>
                </div>

                <div>
                  <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                    {reward.title}
                  </h3>
                  <p className="text-xs md:text-sm text-slate-500 dark:text-slate-400 mt-1 leading-relaxed">
                    {reward.description}
                  </p>
                </div>
              </div>

              <div className="pt-5 mt-4 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between">
                {!canAfford && (
                  <span className="text-xs font-semibold text-amber-600 dark:text-amber-400 flex items-center gap-1">
                    <AlertCircle className="w-3.5 h-3.5" /> Insufficient Swachh Credits. You need {cost - currentBalance} more credits.
                  </span>
                )}

                <button
                  type="button"
                  onClick={() => handleOpenConfirm(reward)}
                  disabled={!canAfford}
                  className={`ml-auto px-5 py-2.5 rounded-xl font-bold text-xs md:text-sm transition-all ${
                    canAfford
                      ? 'bg-emerald-600 hover:bg-emerald-700 text-white shadow-md shadow-emerald-600/20'
                      : 'bg-slate-200 dark:bg-slate-800 text-slate-400 dark:text-slate-500 cursor-not-allowed opacity-60'
                  }`}
                >
                  Redeem Reward
                </button>
              </div>
            </Card>
          );
        })}
      </div>

      {/* My Redeemed Vouchers Section */}
      {redemptions.length > 0 && (
        <Card className="space-y-4 mt-8">
          <div className="flex items-center gap-2 pb-2 border-b border-slate-100 dark:border-slate-800">
            <Ticket className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">
                My Redeemed Vouchers
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Your active municipal voucher claim codes
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {redemptions.map((red) => (
              <div
                key={red.redemption_id || red.id}
                className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50 space-y-2"
              >
                <div className="flex justify-between items-center">
                  <h4 className="text-sm font-bold text-slate-900 dark:text-white truncate">
                    {red.reward_title}
                  </h4>
                  <span className="text-[11px] font-bold text-emerald-600 bg-emerald-50 dark:bg-emerald-950 px-2 py-0.5 rounded">
                    Active
                  </span>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-900 text-emerald-400 font-mono text-center font-bold text-sm tracking-wider select-all border border-slate-700">
                  {red.redemption_code}
                </div>
                <p className="text-[10px] text-slate-400 text-right">
                  Redeemed on {new Date(red.timestamp).toLocaleDateString()}
                </p>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Confirmation Modal */}
      <Modal
        isOpen={!!selectedReward}
        onClose={() => setSelectedReward(null)}
        title="Confirm Reward Redemption"
      >
        {selectedReward && (() => {
          const cost = Number(selectedReward.credit_cost ?? selectedReward.cost_credits ?? selectedReward.credits_required ?? 0);
          return (
            <div className="space-y-4">
              <p className="text-sm text-slate-600 dark:text-slate-300">
                Are you sure you want to redeem{' '}
                <strong className="text-slate-900 dark:text-white">"{selectedReward.title}"</strong> for{' '}
                <strong className="text-emerald-600 dark:text-emerald-400">{cost} credits</strong>?
              </p>

              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800 text-xs space-y-1">
                <div className="flex justify-between text-slate-600 dark:text-slate-400">
                  <span>Current Credits:</span>
                  <span className="font-bold text-slate-900 dark:text-white">{currentBalance}</span>
                </div>
                <div className="flex justify-between text-slate-600 dark:text-slate-400">
                  <span>Deduction:</span>
                  <span className="font-bold text-red-500">-{cost}</span>
                </div>
                <div className="flex justify-between text-slate-900 dark:text-white font-bold pt-1 border-t border-slate-200 dark:border-slate-700">
                  <span>Remaining Balance:</span>
                  <span className="text-emerald-600 dark:text-emerald-400">{currentBalance - cost}</span>
                </div>
              </div>

              <div className="flex items-center gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setSelectedReward(null)}
                  disabled={isRedeeming}
                  className="flex-1 py-2.5 px-4 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 font-semibold text-sm hover:bg-slate-100 dark:hover:bg-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleRedeem}
                  disabled={isRedeeming}
                  className="flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white font-bold text-sm shadow-md shadow-emerald-600/20"
                >
                  {isRedeeming ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Processing...</span>
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="w-4 h-4" />
                      <span>Confirm & Redeem</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          );
        })()}
      </Modal>
    </div>
  );
};
