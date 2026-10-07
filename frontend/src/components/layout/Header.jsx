import { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { Menu, Bell, Coins, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export const Header = ({ onOpenSidebar, title = 'Dashboard' }) => {
  const { user } = useAuth();
  const [showNotifications, setShowNotifications] = useState(false);

  const [isOffline, setIsOffline] = useState(false);

  // Format credit balance safely
  const credits = user?.swachh_credits !== undefined ? user.swachh_credits : 500;

  useEffect(() => {
    const handleOffline = () => setIsOffline(true);
    window.addEventListener('nudgewaste:offline-mode', handleOffline);
    return () => window.removeEventListener('nudgewaste:offline-mode', handleOffline);
  }, []);

  return (
    <header className="sticky top-0 z-30 h-16 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 px-4 md:px-8 flex items-center justify-between transition-colors">
      {/* Left: Mobile Toggle + Title */}
      <div className="flex items-center gap-3">
        <button
          onClick={onOpenSidebar}
          className="p-2 rounded-xl text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-100 hover:bg-slate-100 dark:hover:bg-slate-800 md:hidden"
          aria-label="Open Sidebar"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3">
          <h1 className="text-lg md:text-xl font-bold text-slate-900 dark:text-white tracking-tight">
            {title}
          </h1>
          {isOffline && (
            <span
              className="px-2.5 py-0.5 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-600 dark:text-amber-400 text-[11px] font-bold flex items-center gap-1.5"
              title="Backend server (port 8000) not detected. Operating seamlessly with local mock data."
            >
              <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse"></span>
              Demo Mode
            </span>
          )}
        </div>
      </div>

      {/* Right: Credits Pill + Notification Bell + User Avatar */}
      <div className="flex items-center gap-3 md:gap-4">
        {/* Credits Balance Pill */}
        <NavLink
          to="/credits"
          className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-50 dark:bg-emerald-950/50 border border-emerald-200 dark:border-emerald-800/80 text-emerald-700 dark:text-emerald-300 hover:bg-emerald-100 dark:hover:bg-emerald-900/50 transition-all shadow-sm group"
          title="View Swachh Credits balance & transaction history"
        >
          <Coins className="w-4 h-4 text-emerald-600 dark:text-emerald-400 group-hover:rotate-12 transition-transform" />
          <span className="text-xs md:text-sm font-bold tracking-tight">
            {Number(credits).toLocaleString('en-IN')}
          </span>
          <span className="text-[11px] font-semibold opacity-90 hidden sm:inline">
            credits
          </span>
        </NavLink>

        {/* Notification Bell */}
        <div className="relative">
          <button
            onClick={() => setShowNotifications((prev) => !prev)}
            className="relative p-2 rounded-full text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            aria-label="Notifications"
          >
            <Bell className="w-5 h-5" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-emerald-500 ring-2 ring-white dark:ring-slate-900"></span>
          </button>

          {/* Notifications Dropdown */}
          {showNotifications && (
            <div className="absolute right-0 mt-2 w-80 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-xl p-4 z-50 animate-in fade-in zoom-in-95 duration-200">
              <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-100 dark:border-slate-800">
                <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                  Notifications
                </h3>
                <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/60 px-2 py-0.5 rounded-full">
                  1 New
                </span>
              </div>
              <div className="space-y-3">
                <div className="flex items-start gap-3 p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/50">
                  <div className="p-1.5 rounded-lg bg-emerald-100 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 mt-0.5">
                    <CheckCircle2 className="w-4 h-4" />
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-slate-800 dark:text-slate-200">
                      Welcome Bonus Received!
                    </p>
                    <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                      500 Swachh Credits credited to your account.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* User Profile Pill */}
        <NavLink
          to="/profile"
          className="flex items-center gap-2 pl-1.5 pr-3 py-1 rounded-full bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors border border-slate-200 dark:border-slate-700"
        >
          <div className="w-7 h-7 rounded-full bg-slate-900 dark:bg-emerald-600 text-white font-bold text-xs flex items-center justify-center">
            {user?.name ? user.name.charAt(0).toUpperCase() : 'U'}
          </div>
          <span className="text-xs font-semibold text-slate-800 dark:text-slate-200 hidden md:inline max-w-[100px] truncate">
            {user?.name?.split(' ')[0] || 'User'}
          </span>
        </NavLink>
      </div>
    </header>
  );
};
