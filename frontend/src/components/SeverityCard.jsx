import React, { useState } from 'react';
import {
  Activity,
  AlertTriangle,
  AlertCircle,
  Sliders,
  RotateCcw,
  CheckCircle2,
  Sparkles,
  Info,
} from 'lucide-react';
import { formatPercent, getSeverityTheme } from '../utils/formatters';

const PRESETS = {
  baseline: {
    id: 'baseline',
    name: 'PlantSeg Baseline',
    earlyMax: 15,
    moderateMax: 35,
    description: 'Project-defined standard model benchmark for general foliar evaluation.',
  },
  aggressive: {
    id: 'aggressive',
    name: 'High-Risk Blight / Rust',
    earlyMax: 5,
    moderateMax: 15,
    description: 'High sensitivity for rapidly spreading foliar conditions (e.g. Late Blight, Apple Scab).',
  },
  tolerant: {
    id: 'tolerant',
    name: 'High-Tolerance Canopy',
    earlyMax: 20,
    moderateMax: 45,
    description: 'Higher tolerance thresholds for mildews and cosmetic foliar leaf spots.',
  },
  custom: {
    id: 'custom',
    name: 'Custom Threshold Simulation',
    earlyMax: 15,
    moderateMax: 35,
    description: 'Custom project threshold simulation. These thresholds are not expert-validated agronomic standards.',
  },
};

const STORAGE_KEY = 'harvest_harbor_severity_calibration';

export function SeverityCard({ severity, className = '' }) {
  const [isCalibrating, setIsCalibrating] = useState(false);
  const [activePreset, setActivePreset] = useState(() => {
    const saved = sessionStorage.getItem(STORAGE_KEY);
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        return parsed.preset || 'baseline';
      } catch {
        return 'baseline';
      }
    }
    return 'baseline';
  });

  const [earlyCutoff, setEarlyCutoff] = useState(() => {
    const saved = sessionStorage.getItem(STORAGE_KEY);
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        return parsed.earlyMax ?? 15;
      } catch {
        return 15;
      }
    }
    return 15;
  });

  const [moderateCutoff, setModerateCutoff] = useState(() => {
    const saved = sessionStorage.getItem(STORAGE_KEY);
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        return parsed.moderateMax ?? 35;
      } catch {
        return 35;
      }
    }
    return 35;
  });

  const saveCalibration = (presetKey, early, moderate) => {
    setActivePreset(presetKey);
    setEarlyCutoff(early);
    setModerateCutoff(moderate);
    sessionStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        preset: presetKey,
        earlyMax: early,
        moderateMax: moderate,
      })
    );
  };

  const handleSelectPreset = (presetKey) => {
    const p = PRESETS[presetKey];
    if (p) {
      saveCalibration(presetKey, p.earlyMax, p.moderateMax);
    }
  };

  const handleResetBaseline = () => {
    saveCalibration('baseline', 15, 35);
  };

  if (!severity || !severity.available) {
    return (
      <div className={`p-6 rounded-3xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder shadow-subtle space-y-3 ${className}`}>
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-gray-400" />
          <h3 className="text-sm font-bold uppercase tracking-wider text-gray-900 dark:text-white">
            Disease Severity Assessment
          </h3>
        </div>
        <p className="text-xs text-gray-500 dark:text-gray-400">
          {severity?.message || 'Not available in historical record'}
        </p>
      </div>
    );
  }

  // System Severity calculated by Backend
  const baselineCategory = severity.severity || 'Not available';
  const affected = Number(severity.affected_area_percent) || 0;
  const description = severity.description;
  const recommendation = severity.recommendation;
  const warning = severity.diagnostic_warning;

  // Local Visualization Recalculation (Labelled explicitly as Visualization Only)
  const computeCalibratedCategory = (pct, early, mod) => {
    if (pct <= 0) return 'Healthy';
    if (pct < early) return 'Early';
    if (pct < mod) return 'Moderate';
    return 'Severe';
  };

  const isCalibratedActive = activePreset !== 'baseline' || earlyCutoff !== 15 || moderateCutoff !== 35;
  const visualizedCategory = isCalibratedActive
    ? computeCalibratedCategory(affected, earlyCutoff, moderateCutoff)
    : baselineCategory;

  const baselineTheme = getSeverityTheme(baselineCategory);
  const visualizedTheme = getSeverityTheme(visualizedCategory);

  const stages = [
    { key: 'Healthy', label: 'Healthy', threshold: '0%' },
    { key: 'Early', label: 'Early', threshold: `<${earlyCutoff}%` },
    { key: 'Moderate', label: 'Moderate', threshold: `${earlyCutoff}–${moderateCutoff}%` },
    { key: 'Severe', label: 'Severe', threshold: `≥${moderateCutoff}%` },
  ];

  const currentStageIndex = stages.findIndex(
    (s) => s.key.toLowerCase() === String(baselineCategory).toLowerCase()
  );

  return (
    <div className={`p-6 sm:p-7 rounded-3xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder shadow-subtle space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            <h3 className="text-sm font-bold uppercase tracking-wider text-gray-900 dark:text-white">
              Estimated Severity
            </h3>
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
            Category assigned based on estimated visible symptom coverage of the leaf blade.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setIsCalibrating((prev) => !prev)}
            className={`px-3 py-1.5 rounded-xl border text-xs font-semibold flex items-center gap-1.5 transition-all ${
              isCalibrating || isCalibratedActive
                ? 'bg-emerald-50 dark:bg-emerald-950/60 border-emerald-300 dark:border-emerald-700 text-emerald-800 dark:text-emerald-300'
                : 'bg-gray-50 dark:bg-darkElevated border-gray-200 dark:border-darkBorder text-gray-700 dark:text-gray-300 hover:border-gray-300'
            }`}
          >
            <Sliders className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
            <span>{isCalibratedActive ? 'Simulate Cutoffs' : 'Simulate'}</span>
          </button>

          {/* System Baseline Severity Badge */}
          <div className={`px-3.5 py-1.5 rounded-2xl border ${baselineTheme.border} ${baselineTheme.bg} flex items-center gap-2`}>
            <span className="w-2.5 h-2.5 rounded-full bg-current" style={{ color: 'inherit' }} />
            <span className={`text-sm sm:text-base font-extrabold uppercase tracking-wide ${baselineTheme.color}`}>
              {baselineCategory}
            </span>
            <span className="text-xs font-mono font-bold text-gray-700 dark:text-gray-300">
              ({formatPercent(affected)})
            </span>
          </div>
        </div>
      </div>

      {/* Interactive Calibration / Simulation Panel */}
      {isCalibrating && (
        <div className="p-5 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-200 dark:border-darkBorder space-y-4 animate-fade-in">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-amber-500" />
              <span className="text-xs font-bold uppercase tracking-wider text-gray-900 dark:text-white">
                Threshold Simulation (Visualization Only)
              </span>
            </div>
            {isCalibratedActive && (
              <button
                type="button"
                onClick={handleResetBaseline}
                className="text-[11px] font-semibold text-gray-500 hover:text-emerald-600 flex items-center gap-1 transition-colors"
              >
                <RotateCcw className="w-3 h-3" />
                <span>Reset to Baseline</span>
              </button>
            )}
          </div>

          <div className="p-3 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 text-[11px] text-amber-900 dark:text-amber-200 flex items-center gap-2">
            <Info className="w-4 h-4 text-amber-600 shrink-0" />
            <span>
              <strong>Note:</strong> Sliders alter the interactive visualization preview only. The assessment record in the local evidence chain remains calculated by the backend.
            </span>
          </div>

          {/* Preset Buttons */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
            {Object.values(PRESETS).filter(p => p.id !== 'custom').map((p) => {
              const isSelected = activePreset === p.id;
              return (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => handleSelectPreset(p.id)}
                  className={`p-3 rounded-xl border text-left transition-all text-xs ${
                    isSelected
                      ? 'bg-emerald-50 dark:bg-emerald-950/50 border-emerald-400 dark:border-emerald-700 text-emerald-900 dark:text-emerald-200 ring-1 ring-emerald-500/30'
                      : 'bg-white dark:bg-darkCard border-gray-200 dark:border-darkBorder text-gray-700 dark:text-gray-300 hover:border-gray-300'
                  }`}
                >
                  <div className="font-bold flex items-center justify-between">
                    <span>{p.name}</span>
                    {isSelected && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />}
                  </div>
                  <div className="text-[10px] font-mono text-gray-500 dark:text-gray-400 mt-1">
                    Early: &lt;{p.earlyMax}% • Mod: &lt;{p.moderateMax}%
                  </div>
                  <p className="text-[10px] text-gray-500 dark:text-gray-400 mt-1 line-clamp-2">
                    {p.description}
                  </p>
                </button>
              );
            })}
          </div>

          {/* Custom Cutoff Range Sliders */}
          <div className="pt-3 border-t border-gray-200/70 dark:border-darkBorder space-y-3">
            <div className="flex items-center justify-between text-xs">
              <span className="font-bold text-gray-800 dark:text-gray-200">
                Custom Cutoff Sliders
              </span>
              <span className="text-[11px] font-mono text-gray-500">
                Early: &lt;{earlyCutoff}% | Moderate: {earlyCutoff}–{moderateCutoff}% | Severe: ≥{moderateCutoff}%
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1">
                <div className="flex justify-between text-[11px] text-gray-600 dark:text-gray-400">
                  <span>Early Stage Upper Limit</span>
                  <span className="font-mono font-bold text-emerald-600 dark:text-emerald-400">{earlyCutoff}%</span>
                </div>
                <input
                  type="range"
                  min="2"
                  max="25"
                  value={earlyCutoff}
                  onChange={(e) => {
                    const val = Number(e.target.value);
                    saveCalibration('custom', val, Math.max(val + 5, moderateCutoff));
                  }}
                  className="w-full accent-emerald-600"
                />
              </div>

              <div className="space-y-1">
                <div className="flex justify-between text-[11px] text-gray-600 dark:text-gray-400">
                  <span>Moderate Stage Upper Limit</span>
                  <span className="font-mono font-bold text-orange-600 dark:text-orange-400">{moderateCutoff}%</span>
                </div>
                <input
                  type="range"
                  min={earlyCutoff + 5}
                  max="60"
                  value={moderateCutoff}
                  onChange={(e) => {
                    const val = Number(e.target.value);
                    saveCalibration('custom', earlyCutoff, val);
                  }}
                  className="w-full accent-emerald-600"
                />
              </div>
            </div>

            {isCalibratedActive && (
              <div className="p-3 rounded-xl bg-gray-100 dark:bg-darkCard border border-gray-200 dark:border-darkBorder text-xs flex items-center justify-between">
                <span>Visualized Preview Rating:</span>
                <span className={`font-bold ${visualizedTheme.color}`}>
                  {visualizedCategory} (Visualization Only)
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Stage Stepper Visualizer */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-[11px] font-mono font-bold text-amber-700 dark:text-amber-300 bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800/80 px-3 py-1.5 rounded-xl">
          <span>PROJECT-DEFINED THRESHOLDS — NOT EXPERT VALIDATED</span>
          <span className="text-[10px] font-normal text-amber-600 dark:text-amber-400">Illustrative classification</span>
        </div>
        <div className="grid grid-cols-4 gap-2">
          {stages.map((stage, idx) => {
            const isActive = idx <= currentStageIndex;
            const isCurrent = idx === currentStageIndex;
            return (
              <div
                key={stage.key}
                className={`p-3 rounded-xl border text-center transition-all ${
                  isCurrent
                    ? `${baselineTheme.bg} ${baselineTheme.border} shadow-subtle scale-[1.02]`
                    : isActive
                    ? 'bg-gray-100 dark:bg-darkElevated border-gray-300 dark:border-darkBorder text-gray-700 dark:text-gray-300'
                    : 'bg-gray-50/50 dark:bg-darkCard/50 border-gray-200 dark:border-darkBorder text-gray-400 dark:text-gray-600'
                }`}
              >
                <span className={`text-xs font-bold block ${isCurrent ? baselineTheme.color : ''}`}>
                  {stage.label}
                </span>
                <span className="text-[10px] font-mono text-gray-500 dark:text-gray-400 block mt-0.5">
                  {stage.threshold}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Diagnostic Warning */}
      {warning && (
        <div className="p-4 rounded-2xl bg-amber-50 dark:bg-amber-950/40 border border-amber-300 dark:border-amber-800 text-amber-900 dark:text-amber-200 text-xs flex items-start gap-3">
          <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold uppercase tracking-wider block">Diagnostic Warning</span>
            <p className="mt-0.5">{warning}</p>
          </div>
        </div>
      )}

      {/* Description & Action Advice */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
        {description && (
          <div className="p-4 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder space-y-1">
            <span className="font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400 block">
              System Stage Description
            </span>
            <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
              {description}
            </p>
          </div>
        )}

        {recommendation && (
          <div className="p-4 rounded-2xl bg-emerald-50/50 dark:bg-emerald-950/30 border border-emerald-100 dark:border-emerald-800/60 space-y-1">
            <span className="font-bold uppercase tracking-wider text-emerald-800 dark:text-emerald-400 block">
              Illustrative Management Guidance
            </span>
            <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
              {recommendation}
            </p>
          </div>
        )}
      </div>

      {/* How is this calculated? Disclaimer */}
      <div className="p-3.5 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder space-y-1.5 text-xs text-gray-500 dark:text-gray-400">
        <span className="font-bold text-gray-700 dark:text-gray-300 block">
          How is this calculated?
        </span>
        <p className="leading-relaxed text-[11px]">
          The current severity category uses project-defined thresholds based on the estimated affected area. These thresholds have not been established as expert-validated agronomic standards unless validation data is available.
        </p>
      </div>
    </div>
  );
}

export default SeverityCard;
