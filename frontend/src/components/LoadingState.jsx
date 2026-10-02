import React from 'react';
import { CheckCircle2, Loader2, Circle, Sparkles } from 'lucide-react';
import { ANALYSIS_STAGES } from '../hooks/usePrediction';

export function LoadingState({ currentStageIndex = 0, stages = ANALYSIS_STAGES }) {
  const progressPercent = Math.min(
    100,
    Math.round(((currentStageIndex + 1) / stages.length) * 100)
  );

  return (
    <div className="p-8 sm:p-12 rounded-3xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder shadow-premium max-w-xl mx-auto space-y-8 animate-fade-in text-center">
      <div className="space-y-3">
        <div className="inline-flex p-3 rounded-2xl bg-emerald-50 dark:bg-emerald-950/70 text-emerald-600 dark:text-emerald-400 shadow-glow-emerald">
          <Sparkles className="w-6 h-6 animate-pulse" />
        </div>
        <h3 className="text-xl font-extrabold text-gray-900 dark:text-white tracking-tight">
          Analyzing Crop Sample
        </h3>
        <p className="text-xs text-gray-500 dark:text-gray-400">
          Running multi-branch neural network diagnostics and generating explainability overlays.
        </p>
      </div>

      {/* Progress Bar */}
      <div className="space-y-1.5 text-left">
        <div className="flex justify-between text-xs font-mono font-medium text-gray-500 dark:text-gray-400">
          <span>Processing Pipeline</span>
          <span>{progressPercent}%</span>
        </div>
        <div className="w-full h-2 bg-gray-100 dark:bg-darkElevated rounded-full overflow-hidden">
          <div
            className="h-full bg-emerald-500 rounded-full transition-all duration-500 ease-out"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </div>

      {/* Stages List */}
      <div className="space-y-2.5 text-left border-t border-gray-100 dark:border-darkBorder pt-6">
        {stages.map((stage, idx) => {
          const isDone = idx < currentStageIndex;
          const isCurrent = idx === currentStageIndex;

          return (
            <div
              key={stage.id}
              className={`flex items-center gap-3 text-xs transition-colors ${
                isDone
                  ? 'text-gray-900 dark:text-gray-200'
                  : isCurrent
                  ? 'text-emerald-700 dark:text-emerald-400 font-semibold'
                  : 'text-gray-400 dark:text-gray-600'
              }`}
            >
              {isDone ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
              ) : isCurrent ? (
                <Loader2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400 animate-spin shrink-0" />
              ) : (
                <Circle className="w-4 h-4 text-gray-300 dark:text-gray-700 shrink-0" />
              )}
              <span className="truncate">{stage.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
export default LoadingState;
