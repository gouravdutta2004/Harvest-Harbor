import React, { useState } from 'react';
import {
  UserCheck,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Send,
  ShieldAlert,
  ChevronDown,
  ChevronUp,
  FileCheck,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { submitForReview } from '../services/api';
import { InfoTooltip } from './InfoTooltip';

export function HumanReviewCard({
  humanReview,
  reportId,
  reviewHistory = [],
  onSendForReview,
  className = '',
}) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [userNote, setUserNote] = useState('');
  const [showNoteField, setShowNoteField] = useState(false);
  const [submittedStatus, setSubmittedStatus] = useState(null);
  const [showHistory, setShowHistory] = useState(false);

  // Determine review state
  // Can be: "required", "recommended", or "not_required"
  const isRequired = humanReview?.required === true;
  const reasons = humanReview?.reasons || [];
  const latestResolution = reviewHistory && reviewHistory.length > 0
    ? reviewHistory[reviewHistory.length - 1]
    : null;

  const isResolved = latestResolution != null;
  const isRecommended = !isRequired && !isResolved && reasons.length > 0;
  const isNotRequired = !isRequired && !isRecommended && !isResolved;

  // Translate technical reason keys into farmer/agronomist plain language
  const reasonLabels = {
    low_disease_confidence: 'Model confidence is low (< 50%)',
    crop_prediction_uncertain: 'Crop botanical identification is uncertain',
    no_compatible_disease: 'No compatible disease was identified for this crop species',
    health_prediction_uncertain: 'Health vs disease screening had borderline certainty',
    low_segmentation_quality: 'Lesion segmentation image quality is low or noisy',
    severity_thresholds_not_validated: 'Severity assessment uses project thresholds and has not been expert validated',
    user_requested_review: 'Manually requested by inspector or farmer',
  };

  const handleSend = async () => {
    setIsSubmitting(true);
    try {
      if (onSendForReview) {
        await onSendForReview(reportId, userNote);
      } else {
        await submitForReview(reportId, userNote);
      }
      setSubmittedStatus('Case submitted to agronomist review queue.');
      setShowNoteField(false);
    } catch (err) {
      setSubmittedStatus(`Failed to submit: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div
      className={`p-6 sm:p-7 rounded-3xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder shadow-subtle space-y-5 ${className}`}
    >
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <UserCheck className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
          <h3 className="text-sm font-bold uppercase tracking-wider text-gray-900 dark:text-white">
            Human Agronomist Review
          </h3>
          <InfoTooltip
            title="Why Human Review?"
            content="AI models are decision-support tools. Borderline confidence, unusual leaf symptoms, or cross-species inconsistencies are flagged for confirmation by a human agronomist."
          />
        </div>

        {/* Status Badge */}
        <div>
          {isResolved ? (
            <span className="px-3 py-1 rounded-full text-xs font-bold bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800 flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Resolved: {latestResolution.decision?.replace(/_/g, ' ').toUpperCase()}</span>
            </span>
          ) : isRequired ? (
            <span className="px-3 py-1 rounded-full text-xs font-bold bg-rose-50 dark:bg-rose-950/60 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-800 flex items-center gap-1.5">
              <ShieldAlert className="w-3.5 h-3.5" />
              <span>Review Required</span>
            </span>
          ) : isRecommended ? (
            <span className="px-3 py-1 rounded-full text-xs font-bold bg-amber-50 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800 flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>Review Recommended</span>
            </span>
          ) : (
            <span className="px-3 py-1 rounded-full text-xs font-bold bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Review Not Required</span>
            </span>
          )}
        </div>
      </div>

      {/* Main explanation paragraph */}
      <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-300 leading-relaxed">
        {isResolved
          ? `This case was evaluated by verified reviewer ${latestResolution.reviewer || 'Agronomist'} with outcome "${latestResolution.decision}".`
          : isRequired
          ? 'Automated checks detected inconsistencies or low diagnostic certainty. This assessment should not be treated as final until confirmed by an agronomist.'
          : isRecommended
          ? 'While an AI disease prediction was produced, additional verification by a local crop consultant is recommended before treatment intervention.'
          : 'High diagnostic confidence and verified host compatibility. No anomalies detected that require mandatory agronomist escalation.'}
      </p>

      {/* Flagged Reason Chips */}
      {reasons.length > 0 && (
        <div className="space-y-2">
          <span className="text-[11px] font-bold uppercase tracking-wider text-gray-400 block">
            Flagged Review Triggers:
          </span>
          <div className="flex flex-wrap gap-2">
            {reasons.map((r, idx) => (
              <span
                key={idx}
                className="px-2.5 py-1 rounded-xl text-xs bg-gray-50 dark:bg-darkElevated border border-gray-200 dark:border-darkBorder text-gray-700 dark:text-gray-300 flex items-center gap-1.5"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                <span>{reasonLabels[r] || r.replace(/_/g, ' ')}</span>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Existing Review Outcome Card (if already resolved) */}
      {latestResolution && (
        <div className="p-4 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-200 dark:border-darkBorder space-y-2 text-xs">
          <div className="flex items-center justify-between font-mono text-[11px] text-gray-500">
            <span>Reviewer: <strong>{latestResolution.reviewer}</strong></span>
            <span>{latestResolution.resolved_at || latestResolution.timestamp}</span>
          </div>
          {latestResolution.review_notes && (
            <div className="p-2.5 rounded-xl bg-white dark:bg-darkCard border border-gray-100 dark:border-darkBorder">
              <span className="text-[10px] font-bold uppercase text-gray-400 block mb-0.5">Reviewer Notes:</span>
              <p className="text-gray-800 dark:text-gray-200 italic">"{latestResolution.review_notes}"</p>
            </div>
          )}
        </div>
      )}

      {/* Action Area: Send for Review */}
      {!isResolved && (
        <div className="pt-2 border-t border-gray-100 dark:border-darkBorder flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
          <div className="text-[11px] text-gray-500 dark:text-gray-400">
            {submittedStatus || 'Need an agronomist second opinion on this leaf?'}
          </div>

          <div className="flex items-center gap-2">
            {!showNoteField && !submittedStatus && (
              <button
                type="button"
                onClick={() => setShowNoteField(true)}
                className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold shadow-subtle flex items-center justify-center gap-1.5 transition-all"
              >
                <Send className="w-3.5 h-3.5" />
                <span>Send for Human Review</span>
              </button>
            )}

            <Link
              to="/review-queue"
              className="px-3 py-2 rounded-xl border border-gray-200 dark:border-darkBorder text-gray-600 dark:text-gray-300 text-xs font-medium hover:bg-gray-50 dark:hover:bg-darkElevated transition-colors text-center"
            >
              Open Review Queue
            </Link>
          </div>
        </div>
      )}

      {/* Note input drawer if user clicked Send for Review */}
      {showNoteField && (
        <div className="p-4 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-200 dark:border-darkBorder space-y-3 text-xs animate-fade-in">
          <label className="font-bold text-gray-900 dark:text-white block">
            Add notes for reviewing agronomist (optional):
          </label>
          <textarea
            value={userNote}
            onChange={(e) => setUserNote(e.target.value)}
            placeholder="e.g., Symptoms noticed on lower foliage after 3 days of rainfall..."
            rows={2}
            className="w-full p-2.5 rounded-xl border border-gray-200 dark:border-darkBorder bg-white dark:bg-darkCard text-xs focus:ring-2 focus:ring-emerald-500 focus:outline-none"
          />
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={() => setShowNoteField(false)}
              className="px-3 py-1.5 rounded-lg text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
            >
              Cancel
            </button>
            <button
              type="button"
              disabled={isSubmitting}
              onClick={handleSend}
              className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold flex items-center gap-1 shadow-subtle disabled:opacity-50"
            >
              <Send className="w-3 h-3" />
              <span>{isSubmitting ? 'Sending...' : 'Confirm Submission'}</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default HumanReviewCard;
