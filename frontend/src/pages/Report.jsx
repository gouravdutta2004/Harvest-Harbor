import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Search, FileText, AlertCircle, Loader2, Clock, CheckCircle2 } from 'lucide-react';
import { ReportCard } from '../components/ReportCard';
import { getTraceabilityReport, getTraceabilityChain } from '../services/api';
import { formatDate } from '../utils/formatters';

export function Report({ latestReport = null, latestImageSrc = null }) {
  const [searchParams, setSearchParams] = useSearchParams();
  const queryId = searchParams.get('id') || '';

  const isMatchingLatest = Boolean(queryId && latestReport && latestReport.report_id === queryId.trim());
  const initialActive = isMatchingLatest ? latestReport : (!queryId ? latestReport : null);
  const initialImg = isMatchingLatest ? (latestReport.image?.url || null) : (!queryId ? (latestReport?.image?.url || null) : null);

  const [inputReportId, setInputReportId] = useState(queryId);
  const [activeReport, setActiveReport] = useState(initialActive);
  const [originalImage, setOriginalImage] = useState(initialImg);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [recentReports, setRecentReports] = useState([]);

  // Fetch recent reports from chain for quick navigation
  useEffect(() => {
    async function loadRecent() {
      try {
        const res = await getTraceabilityChain();
        if (res && Array.isArray(res.chain)) {
          const evidenceBlocks = res.chain
            .filter((b) => b.block_type === 'evidence')
            .reverse();
          setRecentReports(evidenceBlocks);
        }
      } catch (err) {
        console.error('Could not load recent chain reports:', err);
      }
    }
    loadRecent();
  }, []);

  // If query parameter changes or is present on load, fetch that report
  useEffect(() => {
    setInputReportId(queryId);
    if (queryId && queryId.trim()) {
      // If we already have this report in memory (rich data from Analyze page), use it
      if (latestReport && latestReport.report_id === queryId.trim()) {
        setActiveReport(latestReport);
        // Use backend-relative URL only — never a blob URL which is revoked on navigate
        setOriginalImage(latestReport.image?.url || null);
      } else {
        handleFetchReport(queryId.trim());
      }
    } else if (latestReport && !queryId) {
      setActiveReport(latestReport);
      setOriginalImage(latestReport.image?.url || null);
    } else {
      setActiveReport(null);
      setOriginalImage(null);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [queryId]);

  // Sync in-memory latestReport if no queryId set (e.g. navigating directly to /report)
  useEffect(() => {
    if (!queryId && latestReport) {
      setActiveReport(latestReport);
      setOriginalImage(latestReport.image?.url || null);
    }
  }, [latestReport, queryId]);

  const handleFetchReport = async (reportIdToFetch) => {
    if (!reportIdToFetch || !reportIdToFetch.trim()) {
      setError('Please enter a valid Report ID.');
      return;
    }

    setIsLoading(true);
    setError(null);
    setActiveReport(null);
    setOriginalImage(null);

    try {
      const data = await getTraceabilityReport(reportIdToFetch.trim());
      if (data && data.report) {
        // Adapt evidence chain report data into the ReportCard schema
        const block = data.report;
        const evidenceData = block.data || block.evidence_data || {};

        const isHealthyBlock = (evidenceData.health?.prediction || '').toLowerCase() === 'healthy';
        const healthConf = evidenceData.health?.confidence; // Already 0-100 percentage

        // Derive probabilities from confidence (which is max(p_healthy, p_diseased) * 100)
        const confFraction = (healthConf != null) ? Math.min(100, Math.max(0, healthConf)) : null;
        const healthyProbability = confFraction !== null
          ? (isHealthyBlock ? confFraction : 100 - confFraction)
          : null;
        const diseasedProbability = confFraction !== null
          ? (isHealthyBlock ? 100 - confFraction : confFraction)
          : null;

        // Use report_snapshot if available for full reconstruction
        const snapshot = evidenceData.report_snapshot;
        // Prefer the image URL stored in the snapshot (stable backend-relative path).
        // The top-level evidenceData has no image_url field; the snapshot always has image.url.
        const persistentImageUrl = snapshot?.image?.url || null;

        const reconstructedReport = snapshot ? {
          ...snapshot,
          human_review: evidenceData.human_review || snapshot.human_review,
          review_history: evidenceData.review_history || snapshot.review_history,
          // Always use the persistent backend image URL, not any ephemeral blob from the snapshot
          image: {
            ...(snapshot.image || {}),
            url: persistentImageUrl,
            sha256: evidenceData.image_sha256 || snapshot.image?.sha256,
          },
          // Ensure block-level traceability data is always correct
          traceability: {
            ...(snapshot.traceability || {}),
            report_id: block.report_id,
            timestamp: block.timestamp,
            image_sha256: evidenceData.image_sha256,
            blockchain: {
              block_index: block.block_index,
              previous_hash: block.previous_hash,
              current_hash: block.current_hash,
              chain_valid: data.chain_verification?.valid ?? true,
              checked_blocks: data.chain_verification?.checked_blocks ?? 1,
            },
          },
        } : {
          report_id: block.report_id,
          timestamp: block.timestamp,
          human_review: evidenceData.human_review,
          review_history: evidenceData.review_history,
          image: {
            sha256: evidenceData.image_sha256,
            // No reliable image URL is available without a snapshot — show unavailable gracefully
            url: null,
          },
          crop_identification: evidenceData.crop ? {
            prediction: evidenceData.crop.prediction,
            confidence: evidenceData.crop.confidence,
          } : null,
          crop_analysis: evidenceData.crop ? {
            prediction: evidenceData.crop.prediction,
            confidence: evidenceData.crop.confidence,
          } : null,
          health_prediction: {
            prediction: evidenceData.health?.prediction,
            confidence: healthConf,
            healthy_probability: healthyProbability,
            diseased_probability: diseasedProbability,
          },
          disease_analysis: {
            prediction: evidenceData.disease?.prediction,
            confidence: evidenceData.disease?.confidence,
            uncertainty: evidenceData.disease?.uncertainty,
            predicted_class_idx: evidenceData.disease?.class_idx,
            top_3: evidenceData.disease?.top_3 || [],
          },
          severity: {
            available: evidenceData.severity?.severity != null,
            severity: evidenceData.severity?.severity,
            affected_area_percent: evidenceData.severity?.affected_area_percent,
          },
          traceability: {
            report_id: block.report_id,
            timestamp: block.timestamp,
            image_sha256: evidenceData.image_sha256,
            blockchain: {
              block_index: block.block_index,
              previous_hash: block.previous_hash,
              current_hash: block.current_hash,
              chain_valid: data.chain_verification?.valid ?? true,
              checked_blocks: data.chain_verification?.checked_blocks ?? 1,
            },
          },
          status: evidenceData.disease?.prediction ? 'disease_prediction' : 'healthy_prediction',
        };

        setActiveReport(reconstructedReport);
        // Always use the backend-relative image URL (never a blob URL) for the report display
        setOriginalImage(reconstructedReport.image?.url || null);
      } else {
        throw new Error('Report data format not recognized.');
      }
    } catch (err) {
      setActiveReport(null);
      setError(err.message || 'Report not found in the evidence chain.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleFormSubmit = (e) => {
    e.preventDefault();
    if (inputReportId.trim()) {
      setSearchParams({ id: inputReportId.trim() });
    }
  };

  return (
    <div className="space-y-8 animate-fade-in max-w-7xl mx-auto">
      {/* Search Header Bar */}
      <div className="p-6 sm:p-8 rounded-3xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder shadow-subtle space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h1 className="text-xl sm:text-2xl font-black text-gray-900 dark:text-white tracking-tight">
              Crop Diagnostic Reports &amp; Verification Dossiers
            </h1>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Lookup any verified report from the tamper-evident SHA-256 evidence chain.
            </p>
          </div>
        </div>

        <form onSubmit={handleFormSubmit} className="flex flex-col sm:flex-row gap-3 pt-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-gray-400 absolute left-4 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={inputReportId}
              onChange={(e) => setInputReportId(e.target.value)}
              placeholder="Enter Crop Report ID (e.g. CR-53C3945AC954)"
              className="w-full pl-11 pr-4 py-3 rounded-xl border border-gray-200 dark:border-darkBorder bg-gray-50 dark:bg-darkElevated text-gray-900 dark:text-white text-sm font-mono placeholder:font-sans focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="py-3 px-6 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:bg-gray-300 dark:disabled:bg-gray-800 text-white text-sm font-bold shadow-glow-emerald flex items-center justify-center gap-2 transition-all transform active:scale-95"
          >
            {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileText className="w-4 h-4" />}
            <span>{isLoading ? 'Searching...' : 'Find Report'}</span>
          </button>
        </form>

        {/* Quick select chips for recent reports */}
        {recentReports.length > 0 && (
          <div className="pt-2 flex flex-wrap items-center gap-2 text-xs">
            <span className="text-gray-400 font-medium">Recent Reports:</span>
            {recentReports.slice(0, 5).map((block) => (
              <button
                key={block.report_id}
                onClick={() => {
                  setInputReportId(block.report_id);
                  setSearchParams({ id: block.report_id });
                }}
                className={`px-2.5 py-1 rounded-lg border font-mono transition-colors ${
                  activeReport?.report_id === block.report_id
                    ? 'bg-emerald-50 dark:bg-emerald-950/60 border-emerald-300 text-emerald-800 dark:text-emerald-300 font-semibold'
                    : 'bg-gray-50 dark:bg-darkElevated border-gray-200 dark:border-darkBorder text-gray-600 dark:text-gray-300 hover:border-emerald-400'
                }`}
              >
                {block.report_id}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Error state */}
      {error && (
        <div className="p-6 rounded-3xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-rose-800 dark:text-rose-200 text-xs flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-rose-600 dark:text-rose-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <span className="font-bold uppercase tracking-wider block">Report Not Found</span>
            <p>{error}</p>
          </div>
        </div>
      )}

      {/* Display Report */}
      {activeReport ? (
        <ReportCard reportData={activeReport} originalImageSrc={originalImage} />
      ) : !isLoading && !error ? (
        <div className="p-16 rounded-3xl bg-white dark:bg-darkCard border border-dashed border-gray-300 dark:border-darkBorder text-center space-y-3">
          <div className="w-16 h-16 rounded-2xl bg-gray-100 dark:bg-darkElevated text-gray-400 flex items-center justify-center mx-auto">
            <FileText className="w-8 h-8" />
          </div>
          <h3 className="text-base font-bold text-gray-900 dark:text-white">
            No Report Selected
          </h3>
          <p className="text-xs text-gray-500 dark:text-gray-400 max-w-sm mx-auto">
            Enter a Report ID above or run an analysis on the Analyze page to view your verified diagnostic report.
          </p>
        </div>
      ) : null}
    </div>
  );
}
export default Report;
