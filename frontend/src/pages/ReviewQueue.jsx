import React, { useEffect, useState } from 'react';
import {
  CheckCircle2,
  RefreshCw,
  ShieldAlert,
  XCircle,
  Clock,
  AlertTriangle,
  UserCheck,
  FileText,
  Filter,
  Eye,
  MessageSquare,
  HelpCircle,
} from 'lucide-react';
import { getReviewQueue, resolveReviewItem } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { formatDate, formatPercent, toTitleCase, getSeverityTheme } from '../utils/formatters';
import { Link } from 'react-router-dom';
import { InfoTooltip } from '../components/InfoTooltip';

export function ReviewQueue() {
  const { currentRole } = useAuth();
  const [activeTab, setActiveTab] = useState('pending'); // 'pending' | 'resolved' | 'needs_attention'
  const [items, setItems] = useState([]);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState('');
  const [notes, setNotes] = useState({});
  const [actionError, setActionError] = useState({});
  const [resolvingId, setResolvingId] = useState(null);

  const load = async () => {
    setBusy(true);
    setError('');
    try {
      // Pass null to fetch all if on reviewed or needs_attention tabs
      const statusParam = activeTab === 'pending' ? 'pending' : activeTab === 'resolved' ? 'resolved' : null;
      const data = await getReviewQueue(statusParam);
      let list = data.items || [];
      if (activeTab === 'needs_attention') {
        list = list.filter((i) => i.priority === 'high' || (i.reasons && i.reasons.includes('health_prediction_uncertain')));
      }
      setItems(list);
    } catch (e) {
      setError(e.message || 'Failed to load agronomist review queue.');
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    load();
  }, [activeTab]);

  const handleResolve = async (id, decision) => {
    const itemNote = notes[id] || '';
    if (decision === 'rejected' && !itemNote.trim()) {
      setActionError({ ...actionError, [id]: 'Please provide reviewer rationale before rejecting this assessment.' });
      return;
    }
    setActionError({ ...actionError, [id]: null });
    setResolvingId(id);

    try {
      await resolveReviewItem(id, decision, itemNote);
      await load();
    } catch (e) {
      setActionError({ ...actionError, [id]: e.message || 'Failed to submit review resolution.' });
    } finally {
      setResolvingId(null);
    }
  };

  const reasonLabels = {
    low_disease_confidence: 'Model Confidence < 50%',
    crop_prediction_uncertain: 'Uncertain Crop Identification',
    no_compatible_disease: 'Pathogen Host Incompatible',
    health_prediction_uncertain: 'Borderline Health Screening',
    low_segmentation_quality: 'Low Lesion Segmentation Quality',
    severity_thresholds_not_validated: 'Unvalidated Severity Thresholds',
    user_requested_review: 'Inspector Manual Request',
  };

  const hasReviewPermission =
    currentRole.permissions.includes('review_reports') ||
    currentRole.permissions.includes('all');

  return (
    <div className="space-y-8 animate-fade-in max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 dark:text-white tracking-tight">
              Agronomist Human Review Queue
            </h1>
            <InfoTooltip
              title="Human-in-the-Loop AI Governance"
              content="Reports with borderline confidence, botanical incompatibilities, or unusual leaf symptoms are sequestered here. Verified agronomists confirm, reject, or request field re-sampling."
            />
          </div>
          <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">
            Escalation dashboard for low-trust AI assessments requiring agronomist verification before final review resolution.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={load}
            disabled={busy}
            className="px-3.5 py-2 rounded-xl border border-gray-200 dark:border-darkBorder bg-white dark:bg-darkCard hover:bg-gray-50 dark:hover:bg-darkElevated text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-subtle"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${busy ? 'animate-spin text-emerald-600' : ''}`} />
            <span>Refresh Queue</span>
          </button>
        </div>
      </div>

      {/* Role Notice if not authorized */}
      {!hasReviewPermission && (
        <div className="p-4 rounded-2xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 text-xs text-amber-900 dark:text-amber-200 flex items-start gap-3">
          <ShieldAlert className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
          <div>
            <strong>Observer Mode:</strong> Your active role persona ({currentRole.name}) has read-only access. Switch to <strong>Agronomist</strong> or <strong>Admin</strong> in the Security menu to submit binding review resolutions.
          </div>
        </div>
      )}

      {/* 3 Tabs (Pending Reviews, Reviewed, Needs Attention) */}
      <div className="flex flex-wrap items-center gap-2 border-b border-gray-200 dark:border-darkBorder pb-2">
        <button
          onClick={() => setActiveTab('pending')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
            activeTab === 'pending'
              ? 'bg-emerald-600 text-white shadow-subtle'
              : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-darkElevated'
          }`}
        >
          <Clock className="w-3.5 h-3.5" />
          <span>Pending Reviews</span>
        </button>

        <button
          onClick={() => setActiveTab('reviewed')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
            activeTab === 'reviewed'
              ? 'bg-emerald-600 text-white shadow-subtle'
              : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-darkElevated'
          }`}
        >
          <CheckCircle2 className="w-3.5 h-3.5" />
          <span>Reviewed &amp; Resolved</span>
        </button>

        <button
          onClick={() => setActiveTab('needs_attention')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
            activeTab === 'needs_attention'
              ? 'bg-emerald-600 text-white shadow-subtle'
              : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-darkElevated'
          }`}
        >
          <AlertTriangle className="w-3.5 h-3.5" />
          <span>High-Priority Attention</span>
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl border border-rose-200 bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 text-xs">
          {error}
        </div>
      )}

      {/* Main Review Items List */}
      {busy ? (
        <div className="p-12 text-center text-xs text-gray-500 rounded-3xl border border-gray-200 dark:border-darkBorder bg-white dark:bg-darkCard space-y-2">
          <RefreshCw className="w-6 h-6 animate-spin text-emerald-600 mx-auto" />
          <p>Loading agronomist queue records...</p>
        </div>
      ) : items.length === 0 ? (
        <div className="p-12 text-center text-xs text-gray-500 rounded-3xl border border-gray-200 dark:border-darkBorder bg-white dark:bg-darkCard space-y-2">
          <CheckCircle2 className="w-8 h-8 text-emerald-600 mx-auto" />
          <h3 className="text-sm font-bold text-gray-900 dark:text-white">
            Queue is Clear
          </h3>
          <p className="max-w-md mx-auto">
            No items currently match the &quot;{activeTab}&quot; filter. Cases requiring human evaluation will automatically populate here.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {items.map((item) => {
            const summary = item.summary || {};
            const crop = summary.crop_prediction?.prediction || summary.crop_analysis?.prediction || 'Unknown';
            const disease = summary.disease_analysis?.prediction || 'Uncertain';
            const conf = summary.disease_analysis?.confidence ?? summary.health_prediction?.confidence;
            const severityLevel = summary.severity?.severity_level || 'Moderate';
            const severityTheme = getSeverityTheme(severityLevel);
            const isItemPending = item.status === 'pending';

            return (
              <div
                key={item.review_id || `${item.report_id}::${item.created_at}`}
                className="p-5 sm:p-6 rounded-3xl border border-gray-200 dark:border-darkBorder bg-white dark:bg-darkCard shadow-subtle space-y-4"
              >
                {/* Header Row */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm font-bold text-gray-900 dark:text-white">
                        {item.review_id}
                      </span>
                      <span
                        className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                          item.priority === 'high'
                            ? 'bg-rose-50 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300 border border-rose-200'
                            : 'bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300 border border-amber-200'
                        }`}
                      >
                        {item.priority} Priority
                      </span>
                      <span className="text-[10px] text-gray-400 font-mono">
                        Report: {item.report_id}
                      </span>
                    </div>
                    <span className="text-[10px] text-gray-400 font-mono block mt-0.5">
                      Submitted {formatDate(item.created_at, { includeTime: true })}
                    </span>
                  </div>

                  <Link
                    to={`/report?id=${encodeURIComponent(item.report_id)}`}
                    className="px-3 py-1.5 rounded-xl border border-gray-200 dark:border-darkBorder text-gray-700 dark:text-gray-300 text-xs font-semibold hover:border-emerald-500 transition-colors flex items-center gap-1.5 self-start sm:self-auto"
                  >
                    <FileText className="w-3.5 h-3.5" />
                    <span>Inspect Full Report</span>
                  </Link>
                </div>

                {/* Case Telemetry Row */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs bg-gray-50 dark:bg-darkElevated p-3.5 rounded-2xl border border-gray-100 dark:border-darkBorder">
                  <div>
                    <span className="text-[10px] uppercase font-bold text-gray-400 block">Host Crop</span>
                    <strong className="text-gray-900 dark:text-white capitalize">{toTitleCase(crop)}</strong>
                  </div>
                  <div>
                    <span className="text-[10px] uppercase font-bold text-gray-400 block">AI Prediction</span>
                    <strong className="text-gray-900 dark:text-white capitalize">{toTitleCase(disease.replace(/_/g, ' '))}</strong>
                  </div>
                  <div>
                    <span className="text-[10px] uppercase font-bold text-gray-400 block">Model Confidence</span>
                    <strong className="text-gray-900 dark:text-white font-mono">{formatPercent(conf)}</strong>
                  </div>
                  <div>
                    <span className="text-[10px] uppercase font-bold text-gray-400 block">Est. Severity</span>
                    <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold ${severityTheme.badge}`}>
                      {severityLevel}
                    </span>
                  </div>
                </div>

                {/* Flagged Reasons Chips */}
                {item.reasons && item.reasons.length > 0 && (
                  <div className="space-y-1.5">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-gray-400 block">
                      Escalation Triggers:
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {item.reasons.map((r, i) => (
                        <span
                          key={`${r}-${i}`}
                          className="px-2.5 py-1 rounded-xl text-xs bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 text-amber-800 dark:text-amber-200 flex items-center gap-1.5 font-medium"
                        >
                          <AlertTriangle className="w-3 h-3 text-amber-600 shrink-0" />
                          <span>{reasonLabels[r] || r.replace(/_/g, ' ')}</span>
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Resolved Status if already handled */}
                {!isItemPending && (
                  <div className="p-3.5 rounded-2xl bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-800 text-xs space-y-1">
                    <div className="flex items-center justify-between font-mono text-[11px] text-blue-800 dark:text-blue-300">
                      <span>Decision: <strong>{item.decision?.toUpperCase()}</strong></span>
                      <span>Reviewer: <strong>{item.reviewer}</strong></span>
                      <span>{item.updated_at}</span>
                    </div>
                    {item.review_notes && (
                      <p className="text-gray-700 dark:text-gray-300 italic pt-1 border-t border-blue-200/50">
                        &quot;{item.review_notes}&quot;
                      </p>
                    )}
                  </div>
                )}

                {/* Reviewer Action Area for Pending Cases */}
                {isItemPending && hasReviewPermission && (
                  <div className="pt-3 border-t border-gray-100 dark:border-darkBorder space-y-3">
                    <div>
                      <label className="text-xs font-bold text-gray-900 dark:text-white block mb-1">
                        Agronomist Review Notes (Required for rejection):
                      </label>
                      <textarea
                        value={notes[item.review_id] || ''}
                        onChange={(e) => setNotes({ ...notes, [item.review_id]: e.target.value })}
                        placeholder="Add scientific confirmation notes, differential diagnosis, or re-sampling instructions..."
                        className="w-full p-3 rounded-2xl border border-gray-200 dark:border-darkBorder bg-gray-50 dark:bg-darkElevated text-xs focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                        rows={2}
                      />
                    </div>

                    {actionError[item.review_id] && (
                      <div className="text-rose-600 text-xs flex items-center gap-1.5">
                        <AlertTriangle className="w-3.5 h-3.5" />
                        <span>{actionError[item.review_id]}</span>
                      </div>
                    )}

                    <div className="flex flex-wrap items-center gap-2">
                      <button
                        onClick={() => handleResolve(item.review_id, 'confirmed')}
                        disabled={resolvingId === item.review_id}
                        className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-subtle flex items-center gap-1.5 transition-all disabled:opacity-50"
                      >
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>Confirm Assessment</span>
                      </button>

                      <button
                        onClick={() => handleResolve(item.review_id, 'rejected')}
                        disabled={resolvingId === item.review_id}
                        className="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs shadow-subtle flex items-center gap-1.5 transition-all disabled:opacity-50"
                      >
                        <XCircle className="w-3.5 h-3.5" />
                        <span>Reject Assessment</span>
                      </button>

                      <button
                        onClick={() => handleResolve(item.review_id, 'needs_more_evidence')}
                        disabled={resolvingId === item.review_id}
                        className="px-4 py-2 rounded-xl border border-gray-300 dark:border-darkBorder hover:bg-gray-100 dark:hover:bg-darkElevated text-gray-700 dark:text-gray-300 font-semibold text-xs transition-colors disabled:opacity-50"
                      >
                        Request Further Evidence
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default ReviewQueue;
