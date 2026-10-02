import React from 'react';
import { Sprout, CheckCircle2, AlertCircle, Info, Sparkles } from 'lucide-react';
import { formatPercent, toTitleCase } from '../utils/formatters';
import { InfoTooltip } from './InfoTooltip';

export function CropIdentificationCard({ cropData, cropIdentification, className = '' }) {
  const data = cropData || cropIdentification;
  if (!data) return null;

  const predictedCrop = data.prediction || data.crop || 'Unknown';
  const confidence = data.confidence;
  const isUncertain = data.uncertain || (confidence !== null && confidence !== undefined && confidence < 60);
  const alternatives = data.alternatives || data.top_candidates || [];

  return (
    <div
      className={`p-6 sm:p-7 rounded-3xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder shadow-subtle space-y-4 ${className}`}
    >
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Sprout className="w-5 h-5 text-blue-600 dark:text-blue-400" />
          <h3 className="text-sm font-bold uppercase tracking-wider text-gray-900 dark:text-white">
            Crop Species Identification
          </h3>
          <InfoTooltip
            title="Why Crop Identification Matters"
            content="Crop identification verifies the botanical host before diagnosing diseases. This biological gate prevents impossible diagnoses (e.g., diagnosing an apple-specific fungus on a potato leaf)."
          />
        </div>

        <span className="text-xs font-mono px-2.5 py-1 rounded-md bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 font-semibold border border-blue-200 dark:border-blue-800">
          Botanical Host Gate
        </span>
      </div>

      {/* Main Crop Result */}
      <div className="p-4 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="space-y-1">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-gray-400 block">
            Detected Crop Host
          </span>
          <div className="flex items-center gap-2">
            <span className="text-xl sm:text-2xl font-black text-gray-900 dark:text-white capitalize">
              {toTitleCase(predictedCrop)}
            </span>
            {isUncertain ? (
              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 dark:bg-amber-900/60 dark:text-amber-200">
                Low Confidence
              </span>
            ) : (
              <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
            )}
          </div>
        </div>

        <div className="sm:text-right">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-gray-400 block">
            Host Confidence
          </span>
          <span className="text-xl sm:text-2xl font-mono font-extrabold text-gray-900 dark:text-white">
            {formatPercent(confidence)}
          </span>
        </div>
      </div>

      {/* Other possibilities if available */}
      {alternatives && alternatives.length > 0 && (
        <div className="space-y-1.5 pt-1">
          <span className="text-[11px] font-semibold text-gray-400 block">
            Alternative Possibilities Evaluated:
          </span>
          <div className="flex flex-wrap gap-2">
            {alternatives.map((alt, idx) => (
              <span
                key={idx}
                className="px-2.5 py-1 rounded-lg bg-gray-100 dark:bg-darkElevated text-gray-600 dark:text-gray-300 text-xs font-mono"
              >
                {toTitleCase(alt.crop || alt.name)}: <strong>{formatPercent(alt.confidence || alt.prob)}</strong>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Explanatory Note */}
      <p className="text-xs text-gray-500 dark:text-gray-400 leading-relaxed border-t border-gray-100 dark:border-darkBorder pt-3">
        The crop identification step helps the system check whether the predicted disease is compatible with the detected crop.
      </p>
    </div>
  );
}

export default CropIdentificationCard;
