import React, { useState, useRef } from 'react';
import { Modal } from '../common/Modal';
import { CATEGORY_DETAILS, STATUTORY_CATEGORIES } from '../../constants/categories';
import { CheckCircle2, Loader2, Upload, Video, Image as ImageIcon, ShieldCheck, AlertCircle, XCircle, RotateCcw } from 'lucide-react';

export const DisposalConfirmModal = ({ isOpen, onClose, prediction, onConfirm, isLoading, verificationError, onResetError }) => {
  const [proofFile, setProofFile] = useState(null);
  const [proofPreview, setProofPreview] = useState(null);
  const [proofType, setProofType] = useState('image'); // 'image' or 'video'
  const [localError, setLocalError] = useState(null);

  const fileInputRef = useRef(null);
  const videoInputRef = useRef(null);

  if (!prediction) return null;

  const category = prediction.category || STATUTORY_CATEGORIES.DRY;
  const meta = CATEGORY_DETAILS[category] || CATEGORY_DETAILS[STATUTORY_CATEGORIES.DRY];

  const handleFileChange = (e, type) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setProofFile(file);
    setProofType(type);
    setLocalError(null);
    if (onResetError) onResetError();

    const reader = new FileReader();
    reader.onloadend = () => {
      setProofPreview(reader.result);
    };
    reader.readAsDataURL(file);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!proofFile && !proofPreview) {
      setLocalError('Please upload an image or video clearly showing the waste being disposed of in the correct bin.');
      return;
    }

    onConfirm({
      prediction_id: prediction.prediction_id,
      predicted_category: category,
      confirmed_category: category,
      selected_bin_category: category,
      confidence: prediction.confidence || 0.85,
      item_label: prediction.item_label || 'Scanned Item',
      confirmation_proof: proofPreview || proofFile?.name || 'disposal_proof_sample',
    });
  };

  const handleResetProof = () => {
    setProofFile(null);
    setProofPreview(null);
    setLocalError(null);
    if (onResetError) onResetError();
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Now verify your disposal">
      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Status Box */}
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-2">
          <div className="flex justify-between items-center text-xs">
            <span className="text-slate-500 font-semibold">Original Waste Stream:</span>
            <span className="font-bold text-slate-900 dark:text-white flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" /> {category} Waste
            </span>
          </div>
          <div className="flex justify-between items-center text-xs">
            <span className="text-slate-500 font-semibold">Required Statutory Bin:</span>
            <span className="font-bold text-emerald-600 dark:text-emerald-400">
              {meta.binName} ({category})
            </span>
          </div>
        </div>

        {/* Verification Rejection / Wrong Bin Error State */}
        {verificationError ? (
          <div className="p-4 rounded-2xl bg-red-50 dark:bg-red-950/80 border-2 border-red-200 dark:border-red-800 space-y-3">
            <div className="flex items-center gap-2 text-red-700 dark:text-red-300 font-extrabold text-base">
              <XCircle className="w-5 h-5 text-red-600 shrink-0" />
              <span>❌ Wrong dustbin</span>
            </div>
            <p className="text-xs text-red-800 dark:text-red-200 leading-relaxed font-medium">
              {verificationError.message || `This item was classified as ${category} Waste and must be disposed of in the ${meta.binName}.`}
            </p>
            <div className="flex items-center justify-between text-xs font-bold pt-1 border-t border-red-200/60 dark:border-red-800/60 text-red-700 dark:text-red-400">
              <span>Status: REJECTED</span>
              <span>Credits Awarded: 0</span>
            </div>

            <button
              type="button"
              onClick={handleResetProof}
              className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl bg-red-600 hover:bg-red-700 text-white font-bold text-xs transition-colors shadow-sm"
            >
              <RotateCcw className="w-4 h-4" />
              <span>Try Again</span>
            </button>
          </div>
        ) : (
          <>
            <div>
              <h4 className="text-sm font-bold text-slate-900 dark:text-white">
                Upload Disposal Evidence
              </h4>
              <p className="text-xs text-slate-600 dark:text-slate-300 mt-1 leading-relaxed">
                Upload an image or video clearly showing the waste being disposed of in the correct{' '}
                <strong className="text-emerald-600 dark:text-emerald-400">{meta.binName}</strong>.
              </p>
            </div>

            {/* Proof Upload Area */}
            {proofPreview ? (
              <div className="relative rounded-xl border border-emerald-500/40 p-3 bg-emerald-50/50 dark:bg-emerald-950/40 flex items-center justify-between gap-3">
                <div className="flex items-center gap-3 truncate">
                  {proofType === 'video' ? (
                    <Video className="w-6 h-6 text-emerald-600 shrink-0" />
                  ) : (
                    <ImageIcon className="w-6 h-6 text-emerald-600 shrink-0" />
                  )}
                  <div className="truncate">
                    <p className="text-xs font-bold text-slate-900 dark:text-white truncate">
                      {proofFile?.name || 'Disposal_Proof_Media'}
                    </p>
                    <p className="text-[10px] text-emerald-700 dark:text-emerald-400">Proof attached & ready for real ML bin verification</p>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={handleResetProof}
                  className="text-xs font-semibold text-slate-500 hover:text-red-500 px-2 py-1 rounded-lg border border-slate-200 dark:border-slate-700 hover:border-red-200 transition-colors shrink-0"
                >
                  Change
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-3">
                <input
                  type="file"
                  ref={fileInputRef}
                  accept="image/*"
                  className="hidden"
                  onChange={(e) => handleFileChange(e, 'image')}
                />
                <input
                  type="file"
                  ref={videoInputRef}
                  accept="video/*"
                  className="hidden"
                  onChange={(e) => handleFileChange(e, 'video')}
                />

                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="flex flex-col items-center justify-center p-4 rounded-xl border-2 border-dashed border-slate-300 dark:border-slate-700 hover:border-emerald-500 bg-slate-50/50 dark:bg-slate-800/50 hover:bg-emerald-50/50 dark:hover:bg-emerald-950/40 transition-all text-center space-y-1.5"
                >
                  <Upload className="w-5 h-5 text-emerald-600" />
                  <span className="text-xs font-bold text-slate-800 dark:text-slate-200">Upload Image</span>
                  <span className="text-[10px] text-slate-400">JPEG, PNG frame</span>
                </button>

                <button
                  type="button"
                  onClick={() => videoInputRef.current?.click()}
                  className="flex flex-col items-center justify-center p-4 rounded-xl border-2 border-dashed border-slate-300 dark:border-slate-700 hover:border-emerald-500 bg-slate-50/50 dark:bg-slate-800/50 hover:bg-emerald-50/50 dark:hover:bg-emerald-950/40 transition-all text-center space-y-1.5"
                >
                  <Video className="w-5 h-5 text-emerald-600" />
                  <span className="text-xs font-bold text-slate-800 dark:text-slate-200">Upload Video</span>
                  <span className="text-[10px] text-slate-400">Short video clip</span>
                </button>
              </div>
            )}

            {/* Local Validation Error */}
            {localError && (
              <div className="p-3 rounded-xl bg-red-50 dark:bg-red-950/80 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 text-xs font-medium flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0 text-red-600" />
                <span>{localError}</span>
              </div>
            )}

            {/* Submit Action Buttons */}
            <div className="flex items-center gap-3 pt-2">
              <button
                type="button"
                onClick={onClose}
                disabled={isLoading}
                className="flex-1 py-2.5 px-4 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 font-semibold text-sm hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isLoading || (!proofPreview && !proofFile)}
                className="flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white font-bold text-sm shadow-md shadow-emerald-600/20 transition-all"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Verifying disposal...</span>
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Verify Disposal</span>
                  </>
                )}
              </button>
            </div>
          </>
        )}
      </form>
    </Modal>
  );
};
