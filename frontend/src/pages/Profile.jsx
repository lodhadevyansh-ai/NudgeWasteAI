import React from 'react';
import { useAuth } from '../context/AuthContext';
import { Card } from '../components/common/Card';
import { User, Mail, MapPin, Phone, Coins, Calendar, ShieldCheck } from 'lucide-react';

export const Profile = () => {
  const { user } = useAuth();

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <div>
        <h2 className="text-2xl font-extrabold text-slate-900 dark:text-white tracking-tight">
          Citizen Profile
        </h2>
        <p className="text-xs md:text-sm text-slate-500 dark:text-slate-400 mt-1">
          Your registered NudgeWasteAI platform profile and municipal details
        </p>
      </div>

      <Card padding="p-6 md:p-8" className="space-y-6">
        {/* Avatar & Header */}
        <div className="flex items-center gap-4 pb-6 border-b border-slate-100 dark:border-slate-800">
          <div className="w-16 h-16 rounded-full bg-emerald-600 text-white font-extrabold text-2xl flex items-center justify-center shadow-lg shadow-emerald-600/30">
            {user?.name ? user.name.charAt(0).toUpperCase() : 'U'}
          </div>

          <div>
            <h3 className="text-xl font-bold text-slate-900 dark:text-white">{user?.name || 'Civic User'}</h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{user?.email || 'citizen@gmail.com'}</p>
            <span className="inline-flex items-center gap-1 mt-2 px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300 text-xs font-bold border border-emerald-200 dark:border-emerald-800">
              <ShieldCheck className="w-3.5 h-3.5" /> Verified Citizen
            </span>
          </div>
        </div>

        {/* Details Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="flex items-start gap-3 p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/50">
            <User className="w-5 h-5 text-slate-400 mt-0.5 shrink-0" />
            <div>
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">Full Name</span>
              <span className="text-sm font-semibold text-slate-900 dark:text-white">{user?.name || 'N/A'}</span>
            </div>
          </div>

          <div className="flex items-start gap-3 p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/50">
            <Mail className="w-5 h-5 text-slate-400 mt-0.5 shrink-0" />
            <div>
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">Email Address</span>
              <span className="text-sm font-semibold text-slate-900 dark:text-white">{user?.email || 'N/A'}</span>
            </div>
          </div>

          <div className="flex items-start gap-3 p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/50">
            <MapPin className="w-5 h-5 text-slate-400 mt-0.5 shrink-0" />
            <div>
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">City / Municipality</span>
              <span className="text-sm font-semibold text-slate-900 dark:text-white">{user?.city || 'Indore Municipal Corporation'}</span>
            </div>
          </div>

          <div className="flex items-start gap-3 p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/50">
            <Coins className="w-5 h-5 text-emerald-500 mt-0.5 shrink-0" />
            <div>
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">Swachh Credits</span>
              <span className="text-sm font-extrabold text-emerald-600 dark:text-emerald-400">
                {user?.swachh_credits !== undefined ? user.swachh_credits : 500} credits
              </span>
            </div>
          </div>

          <div className="flex items-start gap-3 p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/50">
            <Phone className="w-5 h-5 text-slate-400 mt-0.5 shrink-0" />
            <div>
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">Mobile Number</span>
              <span className="text-sm font-semibold text-slate-900 dark:text-white">{user?.mobile || 'Not provided'}</span>
            </div>
          </div>

          <div className="flex items-start gap-3 p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/50">
            <Calendar className="w-5 h-5 text-slate-400 mt-0.5 shrink-0" />
            <div>
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">Joined Date</span>
              <span className="text-sm font-semibold text-slate-900 dark:text-white">
                {user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'Today'}
              </span>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};
