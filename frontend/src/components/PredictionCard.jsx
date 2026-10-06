import React, { useState } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  ShieldAlert,
  Sparkles,
  Info,
  ChevronDown,
  ChevronUp,
  Target,
  HelpCircle,
} from 'lucide-react';
import { formatPercent, toTitleCase, getHealthStatusTheme } from '../utils/formatters';
import { ConfidenceBar } from './ConfidenceBar';
import { InfoTooltip } from './InfoTooltip';

export function PredictionCard({ data }) {
  const [showMeaning, setShowMeaning] = useState(false);

  if (!data) return null;

  const health = data.health_prediction || {};
  const crop = data.crop_prediction || data.crop_analysis || {};
  const disease = data.disease_analysis || {};
  const validationStatus = disease.validation?.status;
  const isValidationRejected = validationStatus === 'rejected';
  const isValidationSkipped = validationStatus === 'skipped_low_crop_confidence';

  const healthStatus = (health.prediction || data.status || 'unknown').toLowerCase();
  const isHealthy = healthStatus === 'healthy' || data.status === 'healthy_prediction';
  const isUncertain =
    !isHealthy &&
    (isValidationRejected ||
      isValidationSkipped ||
      data.status === 'uncertain_prediction' ||
      data.status?.includes('uncertain') ||
      disease.uncertainty?.toLowerCase() === 'high' ||
      health.uncertain ||
      (disease.confidence !== null && disease.confidence !== undefined && disease.confidence < 50));
  const isDiseased = !isHealthy && !isUncertain && (healthStatus === 'diseased' || data.status === 'disease_prediction');

  const theme = getHealthStatusTheme(isHealthy ? 'healthy' : isUncertain ? 'uncertain' : 'diseased');

  // Overall confidence
  const overallConfidence = isHealthy ? health.confidence : (disease.confidence ?? health.confidence);

  // Confidence tiering
  const getConfidenceTier = (conf) => {
    if (conf == null) return { label: 'Uncalibrated', color: 'text-gray-500', barColor: 'neutral' };
    if (conf >= 80) return { label: 'High Confidence', color: 'text-emerald-600 dark:text-emerald-400', barColor: 'emerald' };
    if (conf >= 50) return { label: 'Moderate Confidence', color: 'text-amber-600 dark:text-amber-400', barColor: 'amber' };
    return { label: 'Low Confidence', color: 'text-rose-600 dark:text-rose-400', barColor: 'rose' };
  };

  const confTier = getConfidenceTier(overallConfidence);

  const healthyProb = health.healthy_probability !== null && health.healthy_probability !== undefined
    ? (health.healthy_probability <= 1.0 ? health.healthy_probability * 100 : health.healthy_probability)
    : (health.confidence !== null && health.confidence !== undefined
        ? (isHealthy ? health.confidence : 100 - health.confidence)
        : null);

  const diseasedProb = health.diseased_probability !== null && health.diseased_probability !== undefined
    ? (health.diseased_probability <= 1.0 ? health.diseased_probability * 100 : health.diseased_probability)
    : (health.confidence !== null && health.confidence !== undefined
        ? (isDiseased ? health.confidence : 100 - health.confidence)
        : null);

  const detectedCropName = crop.prediction ? toTitleCase(crop.prediction) : 'Foliar Specimen';
  const displayPredictionTitle = isHealthy
    ? 'Healthy Leaf Surface'
    : isValidationRejected
    ? 'Candidate Rejected by Crop Check'
    : isValidationSkipped
    ? 'Uncertain Host Compatibility'
    : isUncertain
    ? (disease.prediction ? `Uncertain: ${toTitleCase(disease.prediction)}` : 'Uncertain Diagnosis')
    : isDiseased
    ? (disease.prediction ? toTitleCase(disease.prediction) : 'Diseased Foliage')
    : 'Uncertain Diagnosis';

  return (
    <div className="space-y-6 animate-fade-in">
      {/* SECTION 1 — AI Assessment Summary Card */}
      <div className={`p-6 sm:p-8 rounded-3xl border ${theme.border} ${theme.bg} shadow-subtle relative overflow-hidden space-y-5`}>
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400">
                AI Assessment Summary
              </span>
              <span className="w-1.5 h-1.5 rounded-full bg-gray-400" />
              <span className="px-2 py-0.5 rounded-md text-[10px] font-mono font-bold bg-white/80 dark:bg-darkCard text-gray-700 dark:text-gray-300 border border-gray-200/50 dark:border-darkBorder">
                {isHealthy
                  ? 'Status: Healthy Specimen'
                  : isValidationRejected
                  ? 'Status: Host Incompatible'
                  : isValidationSkipped
                  ? 'Status: Uncertain Host'
                  : isUncertain
                  ? 'Status: Uncertain Prediction'
                  : 'Status: AI Prediction'}
              </span>
            </div>

            <div className="flex items-center gap-3">
              <h2 className="text-2xl sm:text-3xl font-black tracking-tight text-gray-900 dark:text-white uppercase">
                {displayPredictionTitle}
              </h2>
              {isHealthy ? (
                <CheckCircle2 className="w-7 h-7 text-emerald-600 dark:text-emerald-400 shrink-0" />
              ) : isUncertain ? (
                <AlertTriangle className="w-7 h-7 text-amber-500 shrink-0" />
              ) : isDiseased ? (
                <ShieldAlert className="w-7 h-7 text-rose-600 dark:text-rose-400 shrink-0" />
              ) : (
                <AlertTriangle className="w-7 h-7 text-amber-500 shrink-0" />
              )}
            </div>

            {/* Quick Summary Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 pt-1 font-sans text-xs">
              <div className="p-2.5 rounded-xl bg-white/70 dark:bg-darkCard/80 border border-gray-200/50 dark:border-darkBorder">
                <span className="text-[10px] font-semibold text-gray-400 uppercase block">Host Crop</span>
                <strong className="text-gray-900 dark:text-white text-sm capitalize">{detectedCropName}</strong>
              </div>
              <div className="p-2.5 rounded-xl bg-white/70 dark:bg-darkCard/80 border border-gray-200/50 dark:border-darkBorder">
                <span className="text-[10px] font-semibold text-gray-400 uppercase block">Health State</span>
                <strong className={isHealthy ? 'text-emerald-700 dark:text-emerald-400 text-sm capitalize' : 'text-rose-700 dark:text-rose-400 text-sm capitalize'}>
                  {healthStatus}
                </strong>
              </div>
              <div className="p-2.5 rounded-xl bg-white/70 dark:bg-darkCard/80 border border-gray-200/50 dark:border-darkBorder col-span-2 sm:col-span-1">
                <span className="text-[10px] font-semibold text-gray-400 uppercase block">Confidence Tier</span>
                <strong className={`text-sm ${confTier.color}`}>{confTier.label}</strong>
              </div>
            </div>
          </div>

          {/* Confidence Badge */}
          <div className="sm:text-right p-4 rounded-2xl bg-white/80 dark:bg-darkCard/90 backdrop-blur-sm border border-gray-200/60 dark:border-darkBorder shrink-0 space-y-1">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-gray-400 block">
              Model Preference
            </span>
            <div className="text-3xl font-mono font-extrabold text-gray-900 dark:text-white">
              {formatPercent(overallConfidence)}
            </div>
            <span className="text-[10px] font-mono text-gray-500 block">
              Report: {data.report_id || 'ID Pending'}
            </span>
          </div>
        </div>

        {/* 'What does this mean?' Expandable Explanation */}
        <div className="border-t border-gray-200/60 dark:border-darkBorder/60 pt-3">
          <button
            type="button"
            onClick={() => setShowMeaning(!showMeaning)}
            className="flex items-center gap-1.5 text-xs font-bold text-gray-700 dark:text-gray-300 hover:text-emerald-700 dark:hover:text-emerald-400 transition-colors"
          >
            <Info className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
            <span>What does this assessment mean?</span>
            {showMeaning ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>

          {showMeaning && (
            <div className="mt-2.5 p-3.5 rounded-2xl bg-white/80 dark:bg-darkCard text-xs text-gray-600 dark:text-gray-300 space-y-2 border border-gray-200/60 dark:border-darkBorder animate-fade-in leading-relaxed">
              <p>
                {isHealthy
                  ? 'The EfficientNet-B0 health classifier evaluated the leaf as healthy with high posterior certainty. Fungal and bacterial disease predictions are suppressed to avoid unnecessary treatment.'
                  : isValidationRejected
                  ? 'The disease classification model returned a pathogen candidate that cannot biologically infect this host plant species. The system rejected this candidate and flagged it for agronomist confirmation.'
                  : isDiseased
                  ? `The deep learning model detected foliar patterns matching ${toTitleCase(disease.prediction || 'a foliar disease')}. Review the Grad-CAM visual heatmap below to see where the model focused.`
                  : 'Diagnostic certainty was low or the crop identity was uncertain. Field verification with a certified agronomist is recommended.'}
              </p>
              <div className="text-[11px] text-gray-500 font-mono flex items-center gap-1">
                <span>Botanical gate:</span>
                <span className="font-semibold text-gray-700 dark:text-gray-200">
                  {validationStatus ? validationStatus.toUpperCase() : 'AUTOMATICALLY VALIDATED'}
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* SECTION 2 — Model Confidence Explainer Card */}
      <div className="p-6 rounded-3xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder shadow-subtle space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <Target className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            <h3 className="text-sm font-bold uppercase tracking-wider text-gray-900 dark:text-white">
              Model Confidence
            </h3>
            <InfoTooltip
              title="Understanding Confidence"
              content="Confidence measures how strongly the neural network's final softmax layer preferred this class among its 115 learned classes. It is not equivalent to laboratory diagnostic truth."
            />
          </div>

          <span className={`text-xs font-bold font-mono ${confTier.color}`}>
            {confTier.label} ({formatPercent(overallConfidence)})
          </span>
        </div>

        <p className="text-xs text-gray-600 dark:text-gray-300 leading-relaxed">
          How strongly the model preferred this prediction among its learned classes.
        </p>

        <ConfidenceBar percentage={overallConfidence || 0} colorScheme={confTier.barColor} showValue={true} />

        {/* Mandatory Confidence Disclaimer */}
        <div className="p-3 rounded-xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder text-[11px] text-gray-500 dark:text-gray-400 flex items-start gap-2">
          <Info className="w-3.5 h-3.5 text-gray-400 shrink-0 mt-0.5" />
          <span>
            <strong>Scientific Note:</strong> Confidence is a statistical model output and is not the same as expert-confirmed accuracy. Unseen pathogens, mixed foliar infections, or atypical outdoor lighting can lead to high-confidence errors.
          </span>
        </div>
      </div>

      {/* SECTION 3 — Binary Health Screening Card */}
      <div className="p-6 rounded-3xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder shadow-subtle space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            <h3 className="text-sm font-bold uppercase tracking-wider text-gray-900 dark:text-white">
              Binary Health Screening (EfficientNet-B0)
            </h3>
          </div>
          <span className="text-xs font-mono text-gray-400">
            Decision Threshold: {formatPercent(health.threshold || 50, 0)}
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="p-4 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder space-y-2">
            <div className="flex justify-between text-xs">
              <span className="font-semibold text-emerald-700 dark:text-emerald-400">
                Healthy Probability
              </span>
              <span className="font-mono font-bold text-gray-900 dark:text-white">
                {formatPercent(healthyProb)}
              </span>
            </div>
            <ConfidenceBar percentage={healthyProb || 0} colorScheme="emerald" showValue={false} />
          </div>

          <div className="p-4 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder space-y-2">
            <div className="flex justify-between text-xs">
              <span className="font-semibold text-rose-700 dark:text-rose-400">
                Diseased Probability
              </span>
              <span className="font-mono font-bold text-gray-900 dark:text-white">
                {formatPercent(diseasedProb)}
              </span>
            </div>
            <ConfidenceBar percentage={diseasedProb || 0} colorScheme="rose" showValue={false} />
          </div>
        </div>
      </div>
    </div>
  );
}

export default PredictionCard;
