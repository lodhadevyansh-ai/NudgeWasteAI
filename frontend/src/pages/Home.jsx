import { NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Card } from '../components/common/Card';
import { STATUTORY_CATEGORIES, CATEGORY_DETAILS } from '../constants/categories';
import { ScanLine, Coins, Gift, BarChart3, ArrowRight, Sparkles } from 'lucide-react';

export const Home = () => {
  const { user } = useAuth();

  return (
    <div className="space-y-8">
      {/* Hero Welcome Card */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-[#0A192F] via-[#0D2847] to-slate-900 text-white p-8 md:p-10 shadow-xl">
        <div className="absolute top-0 right-0 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 max-w-2xl space-y-4">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-300 text-xs font-bold border border-emerald-500/30">
            <Sparkles className="w-3.5 h-3.5" /> Civic Waste Intelligence Platform
          </span>

          <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight leading-tight">
            Welcome to NudgeWaste<span className="text-emerald-400">AI</span>, {user?.name?.split(' ')[0] || 'Citizen'}!
          </h1>

          <p className="text-slate-300 text-sm md:text-base leading-relaxed">
            Classify municipal waste into India's statutory categories, receive instant positive micro-nudges, and earn Swachh Credits for verified segregation.
          </p>

          <div className="pt-2 flex flex-wrap gap-4">
            <NavLink
              to="/scanner"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-sm shadow-lg shadow-emerald-600/30 transition-all hover:scale-[1.02]"
            >
              <ScanLine className="w-5 h-5" />
              <span>Launch AI Scanner</span>
            </NavLink>

            <NavLink
              to="/rewards"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-bold text-sm border border-slate-700 transition-all"
            >
              <Gift className="w-5 h-5 text-emerald-400" />
              <span>Redeem Rewards</span>
            </NavLink>
          </div>
        </div>
      </div>

      {/* Quick Access Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <NavLink to="/scanner" className="group">
          <Card hover className="h-full border-emerald-500/20 group-hover:border-emerald-500 transition-all">
            <div className="w-12 h-12 rounded-2xl bg-emerald-50 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
              <ScanLine className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-1 group-hover:text-emerald-600 transition-colors">
              AI Waste Scanner
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed mb-4">
              Capture or upload an image to classify item into statutory streams using PyTorch ML models.
            </p>
            <div className="flex items-center text-xs font-bold text-emerald-600 dark:text-emerald-400">
              <span>Start Scan</span>
              <ArrowRight className="w-4 h-4 ml-1 group-hover:translate-x-1 transition-transform" />
            </div>
          </Card>
        </NavLink>

        <NavLink to="/credits" className="group">
          <Card hover className="h-full border-emerald-500/20 group-hover:border-emerald-500 transition-all">
            <div className="w-12 h-12 rounded-2xl bg-emerald-50 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
              <Coins className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-1 group-hover:text-emerald-600 transition-colors">
              Swachh Credits
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed mb-4">
              Your balance: <strong className="text-slate-900 dark:text-white font-bold">{user?.swachh_credits || 500} credits</strong>. View full transaction history.
            </p>
            <div className="flex items-center text-xs font-bold text-emerald-600 dark:text-emerald-400">
              <span>View Balance</span>
              <ArrowRight className="w-4 h-4 ml-1 group-hover:translate-x-1 transition-transform" />
            </div>
          </Card>
        </NavLink>

        <NavLink to="/impact" className="group">
          <Card hover className="h-full border-emerald-500/20 group-hover:border-emerald-500 transition-all">
            <div className="w-12 h-12 rounded-2xl bg-emerald-50 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
              <BarChart3 className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-1 group-hover:text-emerald-600 transition-colors">
              Civic Impact
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed mb-4">
              Track your waste diversion stats, daily streaks, and statutory stream contribution analytics.
            </p>
            <div className="flex items-center text-xs font-bold text-emerald-600 dark:text-emerald-400">
              <span>View Impact</span>
              <ArrowRight className="w-4 h-4 ml-1 group-hover:translate-x-1 transition-transform" />
            </div>
          </Card>
        </NavLink>
      </div>

      {/* Statutory Categories Reference Grid */}
      <div>
        <div className="mb-4">
          <h2 className="text-xl font-bold text-slate-900 dark:text-white">
            India's Statutory Waste Categories
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Four canonical waste streams for municipal waste management
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {Object.values(STATUTORY_CATEGORIES).map((catKey) => {
            const meta = CATEGORY_DETAILS[catKey];
            return (
              <Card key={catKey} padding="p-5" className="border-l-4" style={{ borderLeftColor: meta.binColor }}>
                <div className="flex items-center justify-between mb-3">
                  <span
                    style={{ backgroundColor: meta.bgColor, color: meta.textColor, borderColor: meta.borderColor }}
                    className="px-2.5 py-1 rounded-md text-xs font-bold border"
                  >
                    {catKey}
                  </span>
                  <span className="text-xs font-semibold text-slate-400">{meta.binName}</span>
                </div>
                <h4 className="text-sm font-bold text-slate-900 dark:text-white mb-1">
                  {meta.name}
                </h4>
                <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                  {meta.description}
                </p>
              </Card>
            );
          })}
        </div>
      </div>
    </div>
  );
};
