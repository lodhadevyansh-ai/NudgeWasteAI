import React, { useState } from 'react';
import { Card } from '../common/Card';
import { CategoryBadge } from '../common/Badge';
import { CATEGORY_DETAILS, STATUTORY_CATEGORIES } from '../../constants/categories';
import { NudgeBanner } from '../nudges/NudgeBanner';
import { CheckCircle2, AlertTriangle, Cpu, ShieldCheck, Lock, Info, XCircle } from 'lucide-react';

export const PredictionResult = ({ prediction, onConfirmDisposal, isConfirming }) => {
  const [selectedBin, setSelectedBin] = useState(null);
  const [hoveredDisabledBin, setHoveredDisabledBin] = useState(null);
  const [attemptedWrongBin, setAttemptedWrongBin] = useState(null);

  if (!prediction) return null;

  const category = prediction.category || STATUTORY_CATEGORIES.DRY;
  const confidence = prediction.confidence ? Math.round(prediction.confidence * 100) : 85;
  const isUncertain = prediction.is_uncertain;
  const categoryMeta = CATEGORY_DETAILS[category] || CATEGORY_DETAILS[STATUTORY_CATEGORIES.DRY];
  const activeSelectedBin = selectedBin || category;

  const handleSelectBin = (catKey) => {
    if (catKey !== category) {
      setAttemptedWrongBin(catKey);
      return; // Only AI-predicted bin is selectable
    }
    setAttemptedWrongBin(null);
    setSelectedBin(catKey);
  };

  return (
    <Card className="max-w-2xl mx-auto space-y-6 border-emerald-500/30">
      {/* Header Result Bar */}
      <div className="flex items-start justify-between gap-4 pb-4 border-b border-slate-100 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
              Step 1 — AI Classification
            </span>
            {isUncertain ? (
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-amber-600 bg-amber-50 dark:bg-amber-950 px-2 py-0.5 rounded-md border border-amber-200 dark:border-amber-800">
                <AlertTriangle className="w-3 h-3" /> Low Confidence
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-600 bg-emerald-50 dark:bg-emerald-950 px-2 py-0.5 rounded-md border border-emerald-200 dark:border-emerald-800">
                <ShieldCheck className="w-3 h-3" /> Verified ML Prediction
              </span>
            )}
          </div>
          <h3 className="text-xl font-extrabold text-slate-900 dark:text-white">
            AI recommends: {category} Waste
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Identified item: <span className="font-semibold text-slate-700 dark:text-slate-300">{prediction.item_label || 'Scanned Waste Item'}</span>
          </p>
        </div>

        <CategoryBadge category={category} />
      </div>

      {/* Recommended Bin Banner */}
      <div
        style={{ backgroundColor: categoryMeta.bgColor, borderColor: categoryMeta.borderColor }}
        className="p-5 rounded-2xl border flex items-start gap-4"
      >
        <div
          style={{ backgroundColor: categoryMeta.binColor }}
          className="w-12 h-12 rounded-xl text-white flex items-center justify-center font-bold text-sm shrink-0 shadow-md"
        >
          {category.charAt(0)}
        </div>
        <div>
          <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100">
            Required Bin: {categoryMeta.binName} ({category})
          </h4>
          <p className="text-xs text-slate-700 dark:text-slate-300 mt-1 leading-relaxed">
            {categoryMeta.disposalGuide}
          </p>
        </div>
      </div>

      {/* Step 2 — Four Bin Options Selection */}
      <div className="space-y-3 pt-2">
        <div className="flex items-center justify-between">
          <label className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
            Step 2 — Select Waste Stream Bin
          </label>
          <span className="text-[11px] text-slate-400">Only required stream bin is enabled</span>
        </div>

        {/* Hover / Click Warning Message */}
        {(hoveredDisabledBin || attemptedWrongBin) && (
          <div className="p-3.5 rounded-xl bg-red-50 dark:bg-red-950/80 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-200 text-xs font-medium flex items-center gap-2 animate-fadeIn">
            <XCircle className="w-4 h-4 text-red-600 shrink-0" />
            <span>
              Wrong bin — this item was classified as <strong>{category} Waste</strong> and must go into the <strong>{categoryMeta.binName}</strong>.
            </span>
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {Object.values(STATUTORY_CATEGORIES).map((catKey) => {
            const meta = CATEGORY_DETAILS[catKey];
            const isMatch = catKey === category;
            const isSelected = activeSelectedBin === catKey;

            return (
              <div
                key={catKey}
                onMouseEnter={() => !isMatch && setHoveredDisabledBin(catKey)}
                onMouseLeave={() => setHoveredDisabledBin(null)}
                onClick={() => handleSelectBin(catKey)}
                className={`relative flex items-center justify-between p-4 rounded-xl border transition-all ${
                  isMatch
                    ? isSelected
                      ? 'bg-emerald-50/90 dark:bg-emerald-950/80 border-emerald-500 ring-2 ring-emerald-500/30 cursor-pointer shadow-sm'
                      : 'bg-white dark:bg-slate-800 border-emerald-300 dark:border-emerald-700 hover:border-emerald-500 cursor-pointer'
                    : 'bg-slate-100/70 dark:bg-slate-900/60 border-slate-200 dark:border-slate-800 opacity-60 cursor-not-allowed'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div
                    style={{ backgroundColor: isMatch ? meta.binColor : '#94A3B8' }}
                    className="w-9 h-9 rounded-lg text-white font-bold text-xs flex items-center justify-center shadow-xs shrink-0"
                  >
                    {catKey.charAt(0)}
                  </div>
                  <div>
                    <h5 className="text-sm font-bold text-slate-900 dark:text-white">
                      {catKey} Bin
                    </h5>
                    <p className="text-[11px] text-slate-500 dark:text-slate-400">{meta.binName}</p>
                  </div>
                </div>

                {isMatch ? (
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-bold bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-300">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Required Bin
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-slate-400 bg-slate-200/50 dark:bg-slate-800 px-2 py-0.5 rounded-md">
                    <Lock className="w-3 h-3" /> Disabled
                  </span>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Confidence Bar */}
      <div>
        <div className="flex justify-between items-center text-xs font-semibold mb-1.5">
          <span className="text-slate-600 dark:text-slate-400">ML Prediction Confidence</span>
          <span className="text-slate-900 dark:text-white font-bold">{confidence}%</span>
        </div>
        <div className="w-full h-2.5 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
          <div
            style={{ width: `${confidence}%`, backgroundColor: categoryMeta.binColor }}
            className="h-full rounded-full transition-all duration-500"
          />
        </div>
      </div>

      {/* Nudge Banner */}
      {prediction.feedback_nudge && (
        <NudgeBanner
          nudge={prediction.feedback_nudge}
          category={category}
          severity={isUncertain ? 'warning' : 'information'}
        />
      )}

      {/* Model Metadata */}
      <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1">
        <span className="flex items-center gap-1">
          <Cpu className="w-3.5 h-3.5" /> Model: {prediction.model_version || 'v1.0.0-statutory'}
        </span>
        {prediction.processing_time_ms && (
          <span>Inference time: {prediction.processing_time_ms}ms</span>
        )}
      </div>

      {/* Action: Proceed to Disposal Confirmation */}
      <div className="pt-2">
        <button
          type="button"
          onClick={() => onConfirmDisposal({ ...prediction, selected_bin_category: activeSelectedBin })}
          disabled={isConfirming || isUncertain}
          className="w-full flex items-center justify-center gap-2 py-3 px-6 rounded-xl bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white font-bold text-sm shadow-md shadow-emerald-600/20 transition-all hover:scale-[1.01]"
        >
          <CheckCircle2 className="w-5 h-5" />
          <span>Now verify your disposal</span>
        </button>
      </div>
    </Card>
  );
};
