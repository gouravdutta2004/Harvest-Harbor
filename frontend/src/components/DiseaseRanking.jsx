import React from 'react';
import { Layers, AlertCircle, CheckCircle2, XCircle, HelpCircle, ShieldAlert, Info } from 'lucide-react';
import { formatPercent, toTitleCase } from '../utils/formatters';
import { ConfidenceBar } from './ConfidenceBar';
import { InfoTooltip } from './InfoTooltip';

export function DiseaseRanking({
  top3 = [],
  activePrediction = null,
  validationStatus = null,
  crop = null,
  className = '',
}) {
  if (!top3 || !Array.isArray(top3) || top3.length === 0) {
    return (
      <div className="p-6 rounded-3xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder shadow-subtle text-center text-gray-500 dark:text-gray-400 text-sm">
        No multi-class disease ranking available for this sample.
      </div>
    );
  }

  const isRejected = validationStatus === 'rejected';
  const isSkipped = validationStatus === 'skipped_low_crop_confidence';
  const isCompatible = validationStatus === 'compatible' || validationStatus === 'validated';

  const getCompatibilityBadge = (itemStatus, isItemPrimary) => {
    const status = itemStatus || (isRejected ? 'rejected' : isSkipped ? 'low_crop_confidence' : isCompatible ? 'compatible' : 'not_evaluated');

    switch (status) {
      case 'compatible':
      case 'validated':
        return {
          label: 'Compatible',
          style: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800',
          icon: CheckCircle2,
        };
      case 'rejected':
        return {
          label: 'Rejected by Host Check',
          style: 'bg-rose-50 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300 border-rose-200 dark:border-rose-800',
          icon: XCircle,
        };
      case 'low_crop_confidence':
        return {
          label: 'Low Crop Confidence',
          style: 'bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300 border-amber-200 dark:border-amber-800',
          icon: AlertCircle,
        };
      default:
        return {
          label: 'Not Evaluated',
          style: 'bg-gray-100 text-gray-600 dark:bg-darkElevated dark:text-gray-400 border-gray-200 dark:border-darkBorder',
          icon: HelpCircle,
        };
    }
  };

  return (
    <div
      className={`p-6 sm:p-7 rounded-3xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder shadow-subtle space-y-5 ${className}`}
    >
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
          <h3 className="text-sm font-bold uppercase tracking-wider text-gray-900 dark:text-white">
            AI Disease Assessment (PlantWild v2 - Top 3 Candidates)
          </h3>
          <InfoTooltip
            title="How Candidates Are Evaluated"
            content="The 115-class classifier outputs softmax probabilities. Each candidate is checked against botanical plant pathology matrices to ensure the pathogen can biologically infect the detected host."
          />
        </div>
        <span className="text-[11px] text-gray-500 dark:text-gray-400 font-mono">
          Botanical Filter Active
        </span>
      </div>

      {/* Warning Banner if Candidate Rejected by Crop Compatibility */}
      {isRejected && (
        <div className="p-4 rounded-2xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-xs text-rose-800 dark:text-rose-200 space-y-1.5">
          <div className="flex items-center gap-2 font-bold">
            <ShieldAlert className="w-4 h-4 text-rose-600 dark:text-rose-400 shrink-0" />
            <span>Candidate rejected by crop compatibility check</span>
          </div>
          <p className="leading-relaxed">
            The statistical top prediction is incompatible with the detected crop host {crop ? `(${toTitleCase(crop)})` : ''}. To prevent a false assessment, this candidate is excluded from the primary prediction and flagged for human agronomist review.
          </p>
        </div>
      )}

      {/* Candidate List */}
      <div className="space-y-3">
        {top3.map((item, index) => {
          const rank = item.rank || index + 1;
          const name = item.class || item.prediction || 'Unknown Disease';
          const conf = item.confidence ?? item.score;
          const classIdx = item.class_idx;
          const isPrimary = !isRejected && !isSkipped && activePrediction && name
            ? name.toLowerCase() === activePrediction.toLowerCase()
            : false;

          const badge = getCompatibilityBadge(item.compatibility_status || (isPrimary ? 'compatible' : null), isPrimary);
          const BadgeIcon = badge.icon;

          return (
            <div
              key={index}
              className={`p-4 rounded-2xl border transition-all space-y-2 ${
                isPrimary
                  ? 'bg-emerald-50/60 dark:bg-emerald-950/30 border-emerald-200 dark:border-emerald-800/80 shadow-subtle'
                  : 'bg-gray-50/60 dark:bg-darkElevated/50 border-gray-200/80 dark:border-darkBorder'
              }`}
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex items-center gap-3">
                  <span
                    className={`w-7 h-7 rounded-lg flex items-center justify-center font-mono text-xs font-bold ${
                      isPrimary
                        ? 'bg-emerald-600 text-white shadow-glow-emerald'
                        : 'bg-gray-200 dark:bg-darkBorder text-gray-700 dark:text-gray-300'
                    }`}
                  >
                    0{rank}
                  </span>
                  <div>
                    <h4 className="text-xs sm:text-sm font-bold text-gray-900 dark:text-white capitalize">
                      {toTitleCase(name.replace(/_/g, ' '))}
                    </h4>
                    {classIdx !== undefined && classIdx !== null && (
                      <span className="text-[10px] font-mono text-gray-400">
                        Class Index #{classIdx}
                      </span>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2 sm:text-right">
                  <span
                    className={`px-2.5 py-0.5 rounded-full text-[10px] font-semibold border flex items-center gap-1 ${badge.style}`}
                  >
                    <BadgeIcon className="w-3 h-3" />
                    <span>{badge.label}</span>
                  </span>

                  <div className="text-sm font-mono font-bold text-gray-900 dark:text-white">
                    {formatPercent(conf)}
                  </div>
                </div>
              </div>

              <ConfidenceBar
                percentage={conf || 0}
                colorScheme={isPrimary ? 'emerald' : 'dynamic'}
                showValue={false}
                height="h-1.5"
              />
            </div>
          );
        })}
      </div>

      {/* Footer note */}
      <div className="p-3 rounded-xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder text-[11px] text-gray-500 dark:text-gray-400 flex items-start gap-2">
        <Info className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
        <span>
          Disease class names correspond to the standardized 115-category PlantWild v2 benchmark. Probabilities reflect model softmax confidence across candidate classes.
        </span>
      </div>
    </div>
  );
}

export default DiseaseRanking;
