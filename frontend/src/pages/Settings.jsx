import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { Card } from '../components/common/Card';
import { Modal } from '../components/common/Modal';
import { Bell, Lock, LogOut, Check, AlertTriangle, Trash2, Loader2 } from 'lucide-react';

export const Settings = () => {
  const { logout, deleteAccount } = useAuth();
  const { showSuccess, showError } = useToast();
  const navigate = useNavigate();

  const [emailNotifications, setEmailNotifications] = useState(true);
  const [nudgesEnabled, setNudgesEnabled] = useState(true);

  // Delete modal state
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [confirmText, setConfirmText] = useState('');
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteErrorMessage, setDeleteErrorMessage] = useState('');

  const handleSavePreferences = (e) => {
    e.preventDefault();
    showSuccess('Settings preferences updated successfully.');
  };

  const handleOpenDeleteModal = () => {
    setConfirmText('');
    setDeleteErrorMessage('');
    setIsDeleteModalOpen(true);
  };

  const handleCloseDeleteModal = () => {
    if (isDeleting) return;
    setIsDeleteModalOpen(false);
    setConfirmText('');
    setDeleteErrorMessage('');
  };

  const handleDeleteAccountConfirm = async (e) => {
    e.preventDefault();
    if (confirmText.trim() !== 'DELETE' || isDeleting) return;

    setIsDeleting(true);
    setDeleteErrorMessage('');

    try {
      await deleteAccount();
      showSuccess('Your account has been deleted successfully.');
      setIsDeleteModalOpen(false);
      navigate('/login', { replace: true });
    } catch (err) {
      setIsDeleting(false);
      const errMsg = err?.message || 'Unable to delete your account. Please try again.';
      setDeleteErrorMessage(errMsg);
      showError(errMsg);
    }
  };

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <div>
        <h2 className="text-2xl font-extrabold text-slate-900 dark:text-white tracking-tight">
          Settings
        </h2>
        <p className="text-xs md:text-sm text-slate-500 dark:text-slate-400 mt-1">
          Manage your account preferences and notification settings
        </p>
      </div>

      <form onSubmit={handleSavePreferences} className="space-y-6">
        {/* Notifications Section */}
        <Card padding="p-6" className="space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-slate-100 dark:border-slate-800">
            <Bell className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
            <h3 className="text-base font-bold text-slate-900 dark:text-white">
              Notifications & Nudges
            </h3>
          </div>

          <div className="space-y-4">
            <label className="flex items-center justify-between cursor-pointer">
              <div>
                <h4 className="text-sm font-bold text-slate-900 dark:text-white">
                  Behavioural Micro-Nudges
                </h4>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Receive real-time educational tips on statutory bin segregation.
                </p>
              </div>
              <input
                type="checkbox"
                checked={nudgesEnabled}
                onChange={(e) => setNudgesEnabled(e.target.checked)}
                className="w-5 h-5 text-emerald-600 rounded focus:ring-emerald-500"
              />
            </label>

            <label className="flex items-center justify-between cursor-pointer pt-2 border-t border-slate-100 dark:border-slate-800">
              <div>
                <h4 className="text-sm font-bold text-slate-900 dark:text-white">
                  Swachh Credit Updates
                </h4>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Notify when credits are earned or municipal vouchers redeemed.
                </p>
              </div>
              <input
                type="checkbox"
                checked={emailNotifications}
                onChange={(e) => setEmailNotifications(e.target.checked)}
                className="w-5 h-5 text-emerald-600 rounded focus:ring-emerald-500"
              />
            </label>
          </div>
        </Card>

        {/* Security Section */}
        <Card padding="p-6" className="space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-slate-100 dark:border-slate-800">
            <Lock className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
            <h3 className="text-base font-bold text-slate-900 dark:text-white">
              Account & Security
            </h3>
          </div>

          <p className="text-xs text-slate-500 dark:text-slate-400">
            Your account is secured with JWT Bearer authentication tokens issued by NudgeWasteAI backend.
          </p>

          <button
            type="submit"
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs md:text-sm shadow-md shadow-emerald-600/20 transition-all"
          >
            <Check className="w-4 h-4" />
            <span>Save Preferences</span>
          </button>
        </Card>

        {/* Sign Out Section */}
        <Card padding="p-6" className="border-slate-200 dark:border-slate-800">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="text-sm font-bold text-slate-900 dark:text-white">Sign Out</h4>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                End your active session on this device.
              </p>
            </div>

            <button
              type="button"
              onClick={logout}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-700 hover:bg-slate-800 text-white font-bold text-xs md:text-sm shadow-md transition-all"
            >
              <LogOut className="w-4 h-4" />
              <span>Sign Out</span>
            </button>
          </div>
        </Card>

        {/* Danger Zone Section */}
        <Card padding="p-6" className="border-red-300 dark:border-red-900 bg-red-50/40 dark:bg-red-950/20 space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-red-200 dark:border-red-900">
            <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400" />
            <h3 className="text-base font-bold text-red-700 dark:text-red-400">
              Danger Zone
            </h3>
          </div>

          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div>
              <h4 className="text-sm font-bold text-slate-900 dark:text-white">
                Delete your account
              </h4>
              <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">
                Permanently delete your NudgeWasteAI account and associated data.
              </p>
            </div>

            <button
              type="button"
              onClick={handleOpenDeleteModal}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-red-600 hover:bg-red-700 text-white font-bold text-xs md:text-sm shadow-md shadow-red-600/20 transition-all shrink-0"
            >
              <Trash2 className="w-4 h-4" />
              <span>Delete Account</span>
            </button>
          </div>
        </Card>
      </form>

      {/* Confirmation Modal */}
      <Modal
        isOpen={isDeleteModalOpen}
        onClose={handleCloseDeleteModal}
        title="Delete your account?"
      >
        <form onSubmit={handleDeleteAccountConfirm} className="space-y-4">
          <div className="p-4 rounded-xl bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900 text-red-700 dark:text-red-300 text-xs md:text-sm space-y-2">
            <p className="font-semibold">This action is permanent.</p>
            <p>
              Your profile, scan history, disposal history, credit history, reward redemptions and other account data will be deleted.
            </p>
            <p className="font-bold text-red-800 dark:text-red-200">This cannot be undone.</p>
          </div>

          {deleteErrorMessage && (
            <div className="p-3 rounded-lg bg-red-100 dark:bg-red-900/50 text-red-800 dark:text-red-200 text-xs font-semibold">
              {deleteErrorMessage}
            </div>
          )}

          <div className="space-y-2">
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-300">
              Type <span className="font-extrabold text-red-600 dark:text-red-400">DELETE</span> below to permanently remove your account:
            </label>
            <input
              type="text"
              value={confirmText}
              onChange={(e) => setConfirmText(e.target.value)}
              disabled={isDeleting}
              placeholder="DELETE"
              className="w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm focus:ring-2 focus:ring-red-500 focus:outline-none"
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100 dark:border-slate-800">
            <button
              type="button"
              onClick={handleCloseDeleteModal}
              disabled={isDeleting}
              className="px-4 py-2 rounded-xl border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 font-bold text-xs md:text-sm transition-all"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={confirmText.trim() !== 'DELETE' || isDeleting}
              className="flex items-center gap-2 px-5 py-2 rounded-xl bg-red-600 hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold text-xs md:text-sm shadow-md shadow-red-600/20 transition-all"
            >
              {isDeleting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Deleting account...</span>
                </>
              ) : (
                <span>Delete Account</span>
              )}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

