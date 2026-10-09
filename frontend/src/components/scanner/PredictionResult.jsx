import React, { useState } from 'react';
import { Card } from '../common/Card';
import { CategoryBadge } from '../common/Badge';
import { CATEGORY_DETAILS, STATUTORY_CATEGORIES } from '../../constants/categories';
import { NudgeBanner } from '../nudges/NudgeBanner';
import { CheckCircle2, AlertTriangle, Cpu, ShieldCheck, Lock, Info, XCircle, Tag } from 'lucide-react';

const PHYSICAL_BINS = [
  STATUTORY_CATEGORIES.WET,
  STATUTORY_CATEGORIES.DRY,
  STATUTORY_CATEGORIES.SANITARY,
  STATUTORY_CATEGORIES.SPECIAL_CARE,
];

export const PredictionResult = ({ prediction, onConfirmDisposal, isConfirming }) => {
  const [selectedBin, setSelectedBin] = useState(null);
  const [hoveredDisabledBin, setHoveredDisabledBin] = useState(null);
  const [attemptedWrongBin, setAttemptedWrongBin] = useState(null);

  if (!prediction) return null;

  const isUncertain = Boolean(
    prediction.is_uncertain ||
    !prediction.category ||
    prediction.category === STATUTORY_CATEGORIES.UNKNOWN
  );

  const statutoryCategory = isUncertain
    ? STATUTORY_CATEGORIES.UNKNOWN
    : prediction.category;

  const categoryMeta = CATEGORY_DETAILS[statutoryCategory] || CATEGORY_DETAILS[STATUTORY_CATEGORIES.UNKNOWN];
  const confidence = prediction.confidence ? Math.round(prediction.confidence * 100) : (isUncertain ? 45 : 85);

  const materialName = prediction.material_category || (isUncertain ? 'Needs Review' : `${statutoryCategory} Stream`);
  const itemLabel = prediction.item_label || 'Scanned Waste Item';

  // For uncertain predictions, allow user to pick any physical bin.
  // For verified predictions, AI-predicted bin is enforced.
  const activeSelectedBin = selectedBin || (!isUncertain ? statutoryCategory : null);

  const handleSelectBin = (catKey) => {
    if (!isUncertain && catKey !== statutoryCategory) {
      setAttemptedWrongBin(catKey);
      return;
    }
    setAttemptedWrongBin(null);
    setSelectedBin(catKey);
  };

  return (
    <Card className={`max-w-2xl mx-auto space-y-6 ${isUncertain ? 'border-amber-500/40' : 'border-emerald-500/30'}`}>
      {/* Header Result Bar */}
      <div className="flex items-start justify-between gap-4 pb-4 border-b border-slate-100 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
              Step 1 — AI Classification
            </span>
            {isUncertain ? (
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-amber-700 dark:text-amber-300 bg-amber-50 dark:bg-amber-950 px-2.5 py-0.5 rounded-md border border-amber-200 dark:border-amber-800">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-500" /> Unknown / Needs Review
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-600 bg-emerald-50 dark:bg-emerald-950 px-2.5 py-0.5 rounded-md border border-emerald-200 dark:border-emerald-800">
                <ShieldCheck className="w-3.5 h-3.5" /> Verified ML Prediction
              </span>
            )}
          </div>

          <h3 className="text-xl font-extrabold text-slate-900 dark:text-white">
            {isUncertain ? (
              <span>Item Unverified — Needs Manual Review</span>
            ) : (
              <span>AI recommends: {statutoryCategory} Waste</span>
            )}
          </h3>

          <div className="flex flex-wrap items-center gap-2 mt-1.5 text-xs text-slate-500 dark:text-slate-400">
            <span>Item: <strong className="text-slate-800 dark:text-slate-200">{itemLabel}</strong></span>
            <span className="text-slate-300 dark:text-slate-700">•</span>
            <span className="inline-flex items-center gap-1 font-medium text-slate-700 dark:text-slate-300">
              <Tag className="w-3 h-3 text-emerald-600 dark:text-emerald-400" /> Material: <strong>{materialName}</strong>
            </span>
          </div>
        </div>

        <CategoryBadge category={statutoryCategory} />
      </div>

      {/* Recommended Bin Banner / Guidance */}
      <div
        style={{ backgroundColor: categoryMeta.bgColor, borderColor: categoryMeta.borderColor }}
        className="p-5 rounded-2xl border flex items-start gap-4"
      >
        <div
          style={{ backgroundColor: categoryMeta.binColor }}
          className="w-12 h-12 rounded-xl text-white flex items-center justify-center font-bold text-sm shrink-0 shadow-md"
        >
          {statutoryCategory.charAt(0)}
        </div>
        <div>
          <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100">
            {isUncertain ? 'Manual Inspection Required' : `Required Bin: ${categoryMeta.binName} (${statutoryCategory})`}
          </h4>
          <p className="text-xs text-slate-700 dark:text-slate-300 mt-1 leading-relaxed">
            {prediction.disposal_guide || categoryMeta.disposalGuide}
          </p>
        </div>
      </div>

      {/* Step 2 — Four Bin Options Selection */}
      <div className="space-y-3 pt-2">
        <div className="flex items-center justify-between">
          <label className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
            Step 2 — Select Waste Stream Bin
          </label>
          <span className="text-[11px] text-slate-400">
            {isUncertain ? 'Select correct bin manually to proceed' : 'Only required stream bin is enabled'}
          </span>
        </div>

        {/* Hover / Click Warning Message */}
        {(hoveredDisabledBin || attemptedWrongBin) && (
          <div className="p-3.5 rounded-xl bg-red-50 dark:bg-red-950/80 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-200 text-xs font-medium flex items-center gap-2 animate-fadeIn">
            <XCircle className="w-4 h-4 text-red-600 shrink-0" />
            <span>
              Wrong bin — this item was verified as <strong>{statutoryCategory} Waste</strong> and must go into the <strong>{categoryMeta.binName}</strong>.
            </span>
          </div>
        )}

        {isUncertain && (
          <div className="p-3.5 rounded-xl bg-amber-50 dark:bg-amber-950/80 border border-amber-200 dark:border-amber-800 text-amber-900 dark:text-amber-200 text-xs font-medium flex items-center gap-2">
            <Info className="w-4 h-4 text-amber-600 shrink-0" />
            <span>
              Confidence was below threshold. Please manually pick the appropriate bin below based on the actual material ({materialName}).
            </span>
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {PHYSICAL_BINS.map((catKey) => {
            const meta = CATEGORY_DETAILS[catKey];
            const isMatch = !isUncertain && catKey === statutoryCategory;
            const isSelected = activeSelectedBin === catKey;
            const isSelectable = isUncertain || isMatch;

            return (
              <div
                key={catKey}
                onMouseEnter={() => !isSelectable && setHoveredDisabledBin(catKey)}
                onMouseLeave={() => setHoveredDisabledBin(null)}
                onClick={() => handleSelectBin(catKey)}
                className={`relative flex items-center justify-between p-4 rounded-xl border transition-all ${
                  isSelectable
                    ? isSelected
                      ? 'bg-emerald-50/90 dark:bg-emerald-950/80 border-emerald-500 ring-2 ring-emerald-500/30 cursor-pointer shadow-sm'
                      : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 hover:border-emerald-500 cursor-pointer'
                    : 'bg-slate-100/70 dark:bg-slate-900/60 border-slate-200 dark:border-slate-800 opacity-60 cursor-not-allowed'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div
                    style={{ backgroundColor: isSelectable ? meta.binColor : '#94A3B8' }}
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

                {isSelected ? (
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-bold bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-300">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Selected
                  </span>
                ) : isMatch ? (
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-bold bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-300">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Required Bin
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-slate-400 bg-slate-200/50 dark:bg-slate-800 px-2 py-0.5 rounded-md">
                    {isUncertain ? 'Click to select' : <><Lock className="w-3 h-3" /> Disabled</>}
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
            style={{ width: `${confidence}%`, backgroundColor: isUncertain ? '#F59E0B' : categoryMeta.binColor }}
            className="h-full rounded-full transition-all duration-500"
          />
        </div>
      </div>

      {/* Nudge Banner */}
      {prediction.feedback_nudge && (
        <NudgeBanner
          nudge={prediction.feedback_nudge}
          category={statutoryCategory}
          severity={isUncertain ? 'warning' : 'information'}
        />
      )}

      {/* Model Metadata */}
      <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1">
        <span className="flex items-center gap-1">
          <Cpu className="w-3.5 h-3.5" /> Model: {prediction.model_version || 'v1.0.0-mobilenetv3-small'}
        </span>
        {prediction.processing_time_ms && (
          <span>Inference time: {prediction.processing_time_ms}ms</span>
        )}
      </div>

      {/* Action: Proceed to Disposal Confirmation */}
      <div className="pt-2">
        <button
          type="button"
          onClick={() => onConfirmDisposal({
            ...prediction,
            category: activeSelectedBin || statutoryCategory,
            selected_bin_category: activeSelectedBin || statutoryCategory,
          })}
          disabled={isConfirming || (isUncertain && !activeSelectedBin)}
          className="w-full flex items-center justify-center gap-2 py-3 px-6 rounded-xl bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white font-bold text-sm shadow-md shadow-emerald-600/20 transition-all hover:scale-[1.01]"
        >
          <CheckCircle2 className="w-5 h-5" />
          <span>{isUncertain && !activeSelectedBin ? 'Please select a bin above to proceed' : 'Now verify your disposal'}</span>
        </button>
      </div>
    </Card>
  );
};
