import React, { useState } from 'react';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { Leaf, CheckCircle2, ArrowRight, Loader2 } from 'lucide-react';

export const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { login, authError } = useAuth();
  const { showSuccess, showError } = useToast();
  const navigate = useNavigate();
  const location = useLocation();

  const from = location.state?.from?.pathname || '/dashboard';

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email.trim() || !password) return;

    setIsSubmitting(true);
    try {
      await login(email.trim(), password);
      showSuccess('Welcome back to NudgeWasteAI!');
      navigate(from, { replace: true });
    } catch (err) {
      showError(err.message || 'Invalid email or password');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen w-full flex flex-col md:flex-row bg-slate-50 dark:bg-slate-950 font-sans">
      {/* Left Branding Hero Panel */}
      <div className="md:w-1/2 bg-[#0A192F] text-white p-8 md:p-16 flex flex-col justify-between relative overflow-hidden">
        {/* Subtle Background Glow */}
        <div className="absolute -top-24 -left-24 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -right-24 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />

        {/* Top Logo */}
        <div className="relative z-10 mb-12">
          <div className="w-14 h-14 rounded-2xl bg-emerald-600 flex items-center justify-center shadow-lg shadow-emerald-600/30 mb-8">
            <Leaf className="w-8 h-8 fill-current text-white" />
          </div>

          <h1 className="text-3xl md:text-5xl font-extrabold tracking-tight mb-4">
            NudgeWasteAI
          </h1>
          <p className="text-slate-300 text-lg md:text-xl font-normal leading-relaxed max-w-md">
            AI-powered civic waste intelligence for cleaner, more responsible cities.
          </p>
        </div>

        {/* Bottom Feature Highlighting */}
        <div className="relative z-10 pt-8 border-t border-slate-800/80">
          <div className="flex items-start gap-3">
            <div className="p-1 rounded-full bg-emerald-500/20 text-emerald-400 mt-1">
              <CheckCircle2 className="w-5 h-5" />
            </div>
            <div>
              <h4 className="font-bold text-white text-base">
                Four-stream segregation guidance
              </h4>
              <p className="text-slate-400 text-sm mt-0.5">
                Built for India's statutory waste categories.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Right Form Panel */}
      <div className="md:w-1/2 p-8 md:p-16 flex flex-col justify-center bg-white dark:bg-slate-900">
        <div className="max-w-md w-full mx-auto">
          {/* Badge & Title */}
          <div className="mb-8">
            <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider block mb-2">
              Citizen Portal
            </span>
            <h2 className="text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
              Welcome back
            </h2>
            <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">
              Sign in to continue your civic impact.
            </p>
          </div>

          {/* Global Auth Error Alert */}
          {authError && (
            <div className="mb-6 p-4 rounded-xl bg-red-50 dark:bg-red-950/50 border border-red-200 dark:border-red-900 text-red-700 dark:text-red-300 text-sm font-medium">
              {authError}
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-2">
                Email address
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@gmail.com"
                className="w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 transition-all"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-2">
                Password
              </label>
              <input
                type="password"
                required
                minLength={6}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Minimum 6 characters"
                className="w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 transition-all"
              />
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full flex items-center justify-center gap-2 py-3.5 px-6 rounded-xl bg-slate-700 hover:bg-slate-800 dark:bg-slate-700 dark:hover:bg-slate-600 disabled:opacity-50 text-white font-bold text-sm transition-all shadow-md mt-2"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>Signing in...</span>
                </>
              ) : (
                <>
                  <span>Sign in</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Create Account Link */}
          <div className="mt-8 text-center pt-6 border-t border-slate-100 dark:border-slate-800">
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Don’t have an account?{' '}
              <NavLink
                to="/register"
                className="font-bold text-emerald-600 dark:text-emerald-400 hover:underline"
              >
                Create account
              </NavLink>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
