import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  ShieldCheck,
  ShieldAlert,
  Search,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Hash,
  Database,
  Clock,
  Layers,
  Cpu,
  ArrowDown,
  Info,
} from 'lucide-react';
import {
  getTraceabilityStatus,
  verifyTraceabilityChain,
  getTraceabilityChain,
  getTraceabilityReport,
} from '../services/api';
import { HashDisplay } from '../components/HashDisplay';
import { formatDate, formatPercent, toTitleCase } from '../utils/formatters';

export function Traceability() {
  const [searchParams, setSearchParams] = useSearchParams();
  const queryParam = searchParams.get('query') || '';

  const [searchQuery, setSearchQuery] = useState(queryParam);
  const [reportResult, setReportResult] = useState(null);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState(null);

  // Global chain status
  const [chainStatus, setChainStatus] = useState(null);
  const [fullChain, setFullChain] = useState([]);
  const [isVerifyingChain, setIsVerifyingChain] = useState(false);
  const [chainVerification, setChainVerification] = useState(null);
  const [loadingChain, setLoadingChain] = useState(true);

  // Load status and chain list on mount
  const loadChainData = async () => {
    setLoadingChain(true);
    try {
      const [statusRes, chainRes] = await Promise.all([
        getTraceabilityStatus(),
        getTraceabilityChain(),
      ]);

      if (statusRes) {
        setChainStatus(statusRes);
        setChainVerification(statusRes.verification);
      }

      if (chainRes && Array.isArray(chainRes.chain)) {
        setFullChain(chainRes.chain);
      }
    } catch (err) {
      console.error('Failed to load traceability state:', err);
    } finally {
      setLoadingChain(false);
    }
  };

  useEffect(() => {
    loadChainData();
  }, []);

  // Handle auto-search from query param
  useEffect(() => {
    if (queryParam && queryParam.trim()) {
      handleSearch(queryParam.trim());
    }
  }, [queryParam]);

  const handleSearch = async (idToSearch) => {
    if (!idToSearch || !idToSearch.trim()) return;

    setSearchLoading(true);
    setSearchError(null);

    try {
      const data = await getTraceabilityReport(idToSearch.trim());
      if (data && data.report) {
        setReportResult(data);
      } else {
        throw new Error('Report not found in the evidence chain.');
      }
    } catch (err) {
      setReportResult(null);
      setSearchError(err.message || 'Report not found in the evidence chain.');
    } finally {
      setSearchLoading(false);
    }
  };

  const handleVerifyEntireChain = async () => {
    setIsVerifyingChain(true);
    try {
      const res = await verifyTraceabilityChain();
      setChainVerification(res);
      // reload status
      const statusRes = await getTraceabilityStatus();
      if (statusRes) setChainStatus(statusRes);
    } catch (err) {
      console.error('Verification failed:', err);
    } finally {
      setIsVerifyingChain(false);
    }
  };

  return (
    <div className="space-y-8 animate-fade-in max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="space-y-1">
        <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 dark:text-white tracking-tight">
          Tamper-Evident Evidence Chain Explorer
        </h1>
        <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">
          Verify individual assessment reports or run cryptographic integrity proofs across the local SHA-256 evidence chain.
        </p>
      </div>

      {/* Global Chain Verification Summary Card */}
      <div className="p-6 sm:p-8 rounded-3xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder shadow-subtle space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div
              className={`p-3 rounded-2xl ${
                chainVerification?.valid
                  ? 'bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 shadow-glow-emerald'
                  : 'bg-rose-50 dark:bg-rose-950/60 text-rose-600 dark:text-rose-400'
              }`}
            >
              {chainVerification?.valid ? (
                <ShieldCheck className="w-6 h-6" />
              ) : (
                <ShieldAlert className="w-6 h-6" />
              )}
            </div>

            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base sm:text-lg font-bold text-gray-900 dark:text-white">
                  Evidence Chain Status
                </h3>
                <span
                  className={`text-[11px] font-bold uppercase px-2 py-0.5 rounded-full ${
                    chainVerification?.valid
                      ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/60 dark:text-emerald-300'
                      : 'bg-rose-100 text-rose-800 dark:bg-rose-900/60 dark:text-rose-300'
                  }`}
                >
                  {chainVerification?.valid ? '✓ Verified Valid' : '⚠ Invalid'}
                </span>
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {chainVerification?.message || 'Cryptographic chain state checked on demand.'}
              </p>
            </div>
          </div>

          <button
            onClick={handleVerifyEntireChain}
            disabled={isVerifyingChain}
            type="button"
            className="px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:bg-gray-300 dark:disabled:bg-gray-800 text-white text-xs font-bold shadow-glow-emerald flex items-center gap-2 transition-all transform active:scale-95"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isVerifyingChain ? 'animate-spin' : ''}`} />
            <span>{isVerifyingChain ? 'Verifying Chain...' : 'Verify Entire Chain'}</span>
          </button>
        </div>

        {/* Global Statistics Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
          <div className="p-4 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder space-y-1">
            <span className="text-gray-500 dark:text-gray-400 font-semibold uppercase tracking-wider text-[11px] block">
              Total Blocks
            </span>
            <div className="text-xl font-mono font-bold text-gray-900 dark:text-white">
              {chainStatus?.total_blocks ?? fullChain.length}
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder space-y-1">
            <span className="text-gray-500 dark:text-gray-400 font-semibold uppercase tracking-wider text-[11px] block">
              Checked Blocks
            </span>
            <div className="text-xl font-mono font-bold text-emerald-700 dark:text-emerald-400">
              {chainVerification?.checked_blocks ?? fullChain.length}
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder space-y-1">
            <span className="text-gray-500 dark:text-gray-400 font-semibold uppercase tracking-wider text-[11px] block">
              Invalid Blocks
            </span>
            <div className="text-xl font-mono font-bold text-gray-900 dark:text-white">
              {chainVerification?.invalid_block !== null && chainVerification?.invalid_block !== undefined
                ? `#${chainVerification.invalid_block}`
                : 'None (0)'}
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder space-y-1">
            <span className="text-gray-500 dark:text-gray-400 font-semibold uppercase tracking-wider text-[11px] block">
              Latest Hash
            </span>
            <HashDisplay
              hash={chainVerification?.latest_hash || chainStatus?.latest_hash}
              startChars={5}
              endChars={5}
            />
          </div>
        </div>
      </div>

      {/* Report Verification Search Section */}
      <div className="p-6 sm:p-8 rounded-3xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder shadow-subtle space-y-5">
        <div>
          <h2 className="text-base sm:text-lg font-bold text-gray-900 dark:text-white">
            Verify a Specific Crop Report
          </h2>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            Enter any Report ID to inspect its canonical payload, hashes, and model signatures.
          </p>
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (searchQuery.trim()) {
              setSearchParams({ query: searchQuery.trim() });
              handleSearch(searchQuery.trim());
            }
          }}
          className="flex flex-col sm:flex-row gap-3"
        >
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-gray-400 absolute left-4 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Enter Crop Report ID (e.g. CR-53C3945AC954)"
              className="w-full pl-11 pr-4 py-3 rounded-xl border border-gray-200 dark:border-darkBorder bg-gray-50 dark:bg-darkElevated text-gray-900 dark:text-white text-sm font-mono placeholder:font-sans focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
            />
          </div>

          <button
            type="submit"
            disabled={searchLoading}
            className="py-3 px-6 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:bg-gray-300 dark:disabled:bg-gray-800 text-white text-sm font-bold shadow-glow-emerald flex items-center justify-center gap-2 transition-all transform active:scale-95"
          >
            <ShieldCheck className="w-4 h-4" />
            <span>{searchLoading ? 'Verifying...' : 'Verify Report'}</span>
          </button>
        </form>

        {searchError && (
          <div className="p-4 rounded-2xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-rose-800 dark:text-rose-200 text-xs flex items-center gap-2.5">
            <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{searchError}</span>
          </div>
        )}

        {/* Verification Result Card if Report Found */}
        {reportResult && reportResult.report && (() => {
          const blockData = reportResult.report.data || reportResult.report.evidence_data || {};
          return (
          <div className="p-6 rounded-3xl bg-emerald-50/50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800/80 shadow-subtle space-y-6 animate-fade-in">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-emerald-200/60 dark:border-emerald-800/60 pb-4">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-800 dark:text-emerald-400">
                    Block #{reportResult.report.block_index}
                  </span>
                  <span className="text-gray-400">•</span>
                  <span className="text-xs font-mono font-bold text-gray-900 dark:text-white">
                    {reportResult.report.report_id}
                  </span>
                </div>
                <h3 className="text-base font-bold text-gray-900 dark:text-white">
                  Report Recorded &amp; Cryptographically Linked in Evidence Chain
                </h3>
              </div>

              <div className="px-3 py-1 rounded-full bg-emerald-100 dark:bg-emerald-900/60 text-emerald-800 dark:text-emerald-200 text-xs font-bold flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Integrity Verified</span>
              </div>
            </div>

            {/* Diagnostic Details recorded in Block */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
              <div className="p-4 rounded-2xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder space-y-1">
                <span className="text-gray-500 font-semibold uppercase tracking-wider text-[11px] block">
                  Health Screening
                </span>
                <div className="font-bold text-gray-900 dark:text-white capitalize text-sm">
                  {blockData.health?.prediction || 'Not available'}
                </div>
                <span className="text-gray-400">
                  Confidence: {formatPercent(blockData.health?.confidence)}
                </span>
              </div>

              <div className="p-4 rounded-2xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder space-y-1">
                <span className="text-gray-500 font-semibold uppercase tracking-wider text-[11px] block">
                  Disease Prediction
                </span>
                <div className="font-bold text-gray-900 dark:text-white text-sm truncate">
                  {blockData.disease?.prediction
                    ? toTitleCase(blockData.disease.prediction)
                    : 'None (Healthy)'}
                </div>
                <span className="text-gray-400">
                  {blockData.disease?.confidence
                    ? `Confidence: ${formatPercent(blockData.disease.confidence)}`
                    : 'Clean leaf screening'}
                </span>
              </div>

              <div className="p-4 rounded-2xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder space-y-1">
                <span className="text-gray-500 font-semibold uppercase tracking-wider text-[11px] block">
                  Severity &amp; Coverage
                </span>
                <div className="font-bold text-gray-900 dark:text-white text-sm">
                  {blockData.severity?.severity || 'Not available'}
                </div>
                <span className="text-gray-400">
                  Affected area: {formatPercent(blockData.severity?.affected_area_percent)}
                </span>
              </div>
            </div>

            {/* Cryptographic Linkage Block Hashes */}
            <div className="p-4 rounded-2xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder space-y-3 text-xs">
              <span className="font-bold uppercase tracking-wider text-gray-700 dark:text-gray-300 flex items-center gap-1.5">
                <Hash className="w-3.5 h-3.5 text-emerald-600" />
                Tamper-Evident Cryptographic Signatures
              </span>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                <div>
                  <span className="text-gray-500 dark:text-gray-400 block text-[11px] mb-1">
                    Previous Block Hash:
                  </span>
                  <HashDisplay hash={reportResult.report.previous_hash} />
                </div>
                <div>
                  <span className="text-gray-500 dark:text-gray-400 block text-[11px] mb-1">
                    Current Block Hash:
                  </span>
                  <HashDisplay hash={reportResult.report.current_hash} />
                </div>
                <div>
                  <span className="text-gray-500 dark:text-gray-400 block text-[11px] mb-1">
                    Image SHA-256 Digest:
                  </span>
                  <HashDisplay hash={blockData.image_sha256} />
                </div>
                <div>
                  <span className="text-gray-500 dark:text-gray-400 block text-[11px] mb-1">
                    Logged Timestamp:
                  </span>
                  <span className="font-mono text-gray-700 dark:text-gray-300">
                    {formatDate(reportResult.report.timestamp)}
                  </span>
                </div>
              </div>
            </div>
          </div>
          );
        })()}
      </div>

      {/* Complete Evidence Chain History Timeline */}
      <div className="p-6 sm:p-8 rounded-3xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder shadow-subtle space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base sm:text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
              <Layers className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
              <span>Complete Evidence Chain Timeline</span>
            </h2>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Each record contains a cryptographic digest of the assessment payload linked to its parent.
            </p>
          </div>

          <span className="text-xs font-mono font-bold px-3 py-1 rounded-full bg-gray-100 dark:bg-darkElevated text-gray-700 dark:text-gray-300">
            {fullChain.length} Records
          </span>
        </div>

        {loadingChain ? (
          <div className="py-12 text-center text-xs text-gray-400 animate-pulse">
            Loading evidence chain...
          </div>
        ) : fullChain.length === 0 ? (
          <div className="py-12 text-center text-xs text-gray-400">
            No records found in evidence chain.
          </div>
        ) : (
          <div className="space-y-3">
            {fullChain.map((block, idx) => (
              <div key={block.block_index ?? idx}>
                <div className="p-4 sm:p-5 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-200/80 dark:border-darkBorder space-y-3 transition-all hover:border-emerald-300 dark:hover:border-emerald-800">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
                    <div className="flex items-center gap-2.5">
                      <span className="px-2.5 py-1 rounded-lg bg-emerald-600 text-white font-mono font-bold text-xs">
                        Block #{block.block_index}
                      </span>
                      <span className="font-mono font-bold text-gray-900 dark:text-white text-sm">
                        {block.report_id}
                      </span>
                      {block.block_type === 'genesis' && (
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900/60 dark:text-blue-300 uppercase font-bold">
                          Genesis Block
                        </span>
                      )}
                    </div>

                    <div className="text-[11px] text-gray-500 dark:text-gray-400 flex items-center gap-1.5">
                      <Clock className="w-3.5 h-3.5" />
                      <span>{formatDate(block.timestamp)}</span>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-2 border-t border-gray-200/50 dark:border-darkBorder text-[11px]">
                    <div className="flex items-center justify-between sm:justify-start sm:gap-2">
                      <span className="text-gray-500 dark:text-gray-400">Prev Hash:</span>
                      <HashDisplay hash={block.previous_hash} startChars={6} endChars={6} />
                    </div>
                    <div className="flex items-center justify-between sm:justify-start sm:gap-2">
                      <span className="text-gray-500 dark:text-gray-400">Curr Hash:</span>
                      <HashDisplay hash={block.current_hash} startChars={6} endChars={6} />
                    </div>
                  </div>
                </div>

                {idx < fullChain.length - 1 && (
                  <div className="flex justify-center py-1 text-gray-300 dark:text-gray-600">
                    <ArrowDown className="w-3.5 h-3.5" />
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
export default Traceability;
