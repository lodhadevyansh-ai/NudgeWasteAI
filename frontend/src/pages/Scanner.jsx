import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { predictionApi } from '../api/predictionApi';
import { disposalApi } from '../api/disposalApi';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { ImageUploader } from '../components/scanner/ImageUploader';
import { PredictionResult } from '../components/scanner/PredictionResult';
import { DisposalConfirmModal } from '../components/scanner/DisposalConfirmModal';
import { RotateCcw } from 'lucide-react';

export const Scanner = () => {
  const [prediction, setPrediction] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isConfirmModalOpen, setIsConfirmModalOpen] = useState(false);
  const [isRecordingDisposal, setIsRecordingDisposal] = useState(false);
  const [verificationError, setVerificationError] = useState(null);

  const { refreshUser } = useAuth();
  const { showSuccess, showError } = useToast();
  const navigate = useNavigate();

  const handleAnalyze = async ({ file, itemLabel }) => {
    setIsAnalyzing(true);
    setPrediction(null);
    setVerificationError(null);
    try {
      let res;
      if (file) {
        res = await predictionApi.predictUpload(file, itemLabel, 0.60);
      } else {
        res = await predictionApi.predictPayload({
          item_label: itemLabel,
          min_confidence: 0.60,
        });
      }
      setPrediction(res);
    } catch (err) {
      showError(err.message || "We couldn't analyze this image. Please try another image.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleOpenModal = () => {
    setVerificationError(null);
    setIsConfirmModalOpen(true);
  };

  const handleConfirmDisposal = async (disposalPayload) => {
    setIsRecordingDisposal(true);
    setVerificationError(null);
    try {
      const res = await disposalApi.recordDisposal(disposalPayload);

      // Check if response is non-verified
      if (res.verified === false || res.success === false) {
        setVerificationError(res);
        showError(res.message || 'Wrong dustbin detected. Credits have not been awarded.');
        return;
      }

      setIsConfirmModalOpen(false);

      // Refresh authoritative credit balance from backend
      await refreshUser();

      showSuccess(`Disposal verified! +${res.credits_awarded || 10} Swachh Credits earned.`);
      navigate('/history');
    } catch (err) {
      if (err.raw?.response?.data) {
        const data = err.raw.response.data;
        setVerificationError(data);
        showError(data.message || err.message || 'Wrong dustbin detected. Credits have NOT been awarded.');
      } else {
        showError(err.message || 'Failed to verify disposal event.');
      }
    } finally {
      setIsRecordingDisposal(false);
    }
  };

  const handleResetScanner = () => {
    setPrediction(null);
    setVerificationError(null);
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Scanner Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-extrabold text-slate-900 dark:text-white tracking-tight">
            AI Waste Scanner
          </h2>
          <p className="text-xs md:text-sm text-slate-500 dark:text-slate-400 mt-1">
            Real-time PyTorch statutory waste classification & bin verification engine
          </p>
        </div>

        {prediction && (
          <button
            onClick={handleResetScanner}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 text-xs font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            <RotateCcw className="w-4 h-4" />
            <span>Scan Another Item</span>
          </button>
        )}
      </div>

      {/* Main Scanner Section */}
      {!prediction ? (
        <ImageUploader onAnalyze={handleAnalyze} isLoading={isAnalyzing} />
      ) : (
        <PredictionResult
          prediction={prediction}
          onConfirmDisposal={handleOpenModal}
          isConfirming={isRecordingDisposal}
        />
      )}

      {/* Disposal Confirmation Modal */}
      <DisposalConfirmModal
        isOpen={isConfirmModalOpen}
        onClose={() => setIsConfirmModalOpen(false)}
        prediction={prediction}
        onConfirm={handleConfirmDisposal}
        isLoading={isRecordingDisposal}
        verificationError={verificationError}
        onResetError={() => setVerificationError(null)}
      />
    </div>
  );
};
