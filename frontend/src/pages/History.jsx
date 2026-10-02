import React, { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import {
  History as HistoryIcon,
  Search,
  Filter,
  FileText,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Calendar,
  Layers,
  ArrowRight,
  Download,
  RefreshCw,
  Info,
} from 'lucide-react';
import { getTraceabilityChain } from '../services/api';
import { formatDate, formatPercent, toTitleCase, getSeverityTheme } from '../utils/formatters';
import { InfoTooltip } from '../components/InfoTooltip';

export function History() {
  const [blocks, setBlocks] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters & search
  const [searchQuery, setSearchQuery] = useState('');
  const [cropFilter, setCropFilter] = useState('ALL');
  const [healthFilter, setHealthFilter] = useState('ALL');
  const [severityFilter, setSeverityFilter] = useState('ALL');

  const loadChain = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await getTraceabilityChain();
      if (res && Array.isArray(res.chain)) {
        // Extract evidence reports
        const evidenceBlocks = res.chain
          .filter((b) => b.block_type === 'evidence')
          .reverse();
        setBlocks(evidenceBlocks);
      } else {
        setBlocks([]);
      }
    } catch (err) {
      setError(err.message || 'Failed to load historical diagnostic records.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadChain();
  }, []);

  // Compute unique crops for filter dropdown
  const uniqueCrops = useMemo(() => {
    const crops = new Set();
    blocks.forEach((b) => {
      const c = b.data?.crop?.prediction || b.data?.report_snapshot?.crop_analysis?.prediction;
      if (c) crops.add(c.toLowerCase());
    });
    return Array.from(crops).sort();
  }, [blocks]);

  // Filtered rows
  const filteredBlocks = useMemo(() => {
    return blocks.filter((b) => {
      const data = b.data || {};
      const snap = data.report_snapshot || {};
      const crop = (data.crop?.prediction || snap.crop_analysis?.prediction || '').toLowerCase();
      const disease = (data.disease?.prediction || snap.disease_analysis?.prediction || '').toLowerCase();
      const health = (data.health?.prediction || snap.health_prediction?.prediction || '').toLowerCase();
      const severity = (data.severity?.severity || snap.severity?.severity || '').toLowerCase();
      const reportId = (b.report_id || '').toLowerCase();

      // Search query filter
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matches =
          crop.includes(q) ||
          disease.includes(q) ||
          reportId.includes(q) ||
          health.includes(q);
        if (!matches) return false;
      }

      // Crop filter
      if (cropFilter !== 'ALL' && crop !== cropFilter.toLowerCase()) {
        return false;
      }

      // Health filter
      if (healthFilter !== 'ALL' && health !== healthFilter.toLowerCase()) {
        return false;
      }

      // Severity filter
      if (severityFilter !== 'ALL' && severity !== severityFilter.toLowerCase()) {
        return false;
      }

      return true;
    });
  }, [blocks, searchQuery, cropFilter, healthFilter, severityFilter]);

  return (
    <div className="space-y-8 animate-fade-in max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 dark:text-white tracking-tight">
              Diagnostic Audit History
            </h1>
            <InfoTooltip
              title="Tamper-Evident History"
              content="All completed crop analyses are cryptographically recorded in the local SHA-256 evidence chain. This log preserves historical integrity for agricultural audits, certifications, and farm records."
            />
          </div>
          <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">
            Tamper-evident log of all AI assessments, estimated lesion severities, and agronomist review events.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            type="button"
            onClick={loadChain}
            className="px-3.5 py-2 rounded-xl border border-gray-200 dark:border-darkBorder bg-white dark:bg-darkCard hover:bg-gray-50 dark:hover:bg-darkElevated text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-subtle"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-emerald-600' : ''}`} />
            <span>Refresh</span>
          </button>

          <Link
            to="/analyze"
            className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold shadow-glow-emerald flex items-center gap-1.5 transition-all"
          >
            <HistoryIcon className="w-3.5 h-3.5" />
            <span>New Diagnosis</span>
          </Link>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="p-4 sm:p-5 rounded-3xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder shadow-subtle space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {/* Search Box */}
          <div className="relative">
            <Search className="w-4 h-4 text-gray-400 absolute left-3 top-3" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search crop, disease, or ID..."
              className="w-full pl-9 pr-3 py-2 rounded-xl border border-gray-200 dark:border-darkBorder bg-gray-50 dark:bg-darkElevated text-xs focus:ring-2 focus:ring-emerald-500 focus:outline-none"
            />
          </div>

          {/* Crop Filter */}
          <div>
            <select
              value={cropFilter}
              onChange={(e) => setCropFilter(e.target.value)}
              className="w-full px-3 py-2 rounded-xl border border-gray-200 dark:border-darkBorder bg-gray-50 dark:bg-darkElevated text-xs focus:ring-2 focus:ring-emerald-500 focus:outline-none capitalize"
            >
              <option value="ALL">All Crops ({uniqueCrops.length})</option>
              {uniqueCrops.map((c) => (
                <option key={c} value={c}>
                  {toTitleCase(c)}
                </option>
              ))}
            </select>
          </div>

          {/* Health Filter */}
          <div>
            <select
              value={healthFilter}
              onChange={(e) => setHealthFilter(e.target.value)}
              className="w-full px-3 py-2 rounded-xl border border-gray-200 dark:border-darkBorder bg-gray-50 dark:bg-darkElevated text-xs focus:ring-2 focus:ring-emerald-500 focus:outline-none"
            >
              <option value="ALL">All Health States</option>
              <option value="healthy">Healthy Leaf</option>
              <option value="diseased">Potential Disease</option>
            </select>
          </div>

          {/* Severity Filter */}
          <div>
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="w-full px-3 py-2 rounded-xl border border-gray-200 dark:border-darkBorder bg-gray-50 dark:bg-darkElevated text-xs focus:ring-2 focus:ring-emerald-500 focus:outline-none"
            >
              <option value="ALL">All Severity Levels</option>
              <option value="healthy">Healthy (0%)</option>
              <option value="early">Early (&gt;0% and &lt;15%)</option>
              <option value="moderate">Moderate (&ge;15% and &lt;35%)</option>
              <option value="severe">Severe (&ge;35%)</option>
            </select>
          </div>
        </div>

        <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 font-mono pt-1 border-t border-gray-100 dark:border-darkBorder">
          <span>
            Showing <strong>{filteredBlocks.length}</strong> of <strong>{blocks.length}</strong> verified reports
          </span>
          <span className="text-[11px] text-gray-400">
            Backed by Local SHA-256 Chain
          </span>
        </div>
      </div>

      {/* History Table */}
      <div className="rounded-3xl border border-gray-200 dark:border-darkBorder bg-white dark:bg-darkCard shadow-subtle overflow-hidden">
        {isLoading ? (
          <div className="p-12 text-center space-y-3">
            <RefreshCw className="w-6 h-6 animate-spin text-emerald-600 mx-auto" />
            <p className="text-xs text-gray-500">Loading historical evidence chain...</p>
          </div>
        ) : error ? (
          <div className="p-8 text-center text-xs text-rose-600 space-y-2">
            <AlertTriangle className="w-6 h-6 mx-auto text-rose-500" />
            <p>{error}</p>
          </div>
        ) : filteredBlocks.length === 0 ? (
          <div className="p-12 text-center space-y-3">
            <HistoryIcon className="w-8 h-8 text-gray-400 mx-auto" />
            <h3 className="text-sm font-bold text-gray-800 dark:text-gray-200">
              No matching records found
            </h3>
            <p className="text-xs text-gray-500 max-w-sm mx-auto">
              {searchQuery || cropFilter !== 'ALL' || healthFilter !== 'ALL' || severityFilter !== 'ALL'
                ? 'Try resetting the search filters to inspect all historical evidence blocks.'
                : 'Upload your first leaf image on the Analyze page to create a tamper-evident record.'}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-gray-50 dark:bg-darkElevated border-b border-gray-200 dark:border-darkBorder text-[11px] uppercase font-mono text-gray-500">
                <tr>
                  <th className="p-3.5 font-bold">Report &amp; Date</th>
                  <th className="p-3.5 font-bold">Crop Species</th>
                  <th className="p-3.5 font-bold">Health Status</th>
                  <th className="p-3.5 font-bold">Primary Prediction</th>
                  <th className="p-3.5 font-bold">Confidence</th>
                  <th className="p-3.5 font-bold">Est. Severity</th>
                  <th className="p-3.5 font-bold">Review Status</th>
                  <th className="p-3.5 font-bold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-darkBorder">
                {filteredBlocks.map((b) => {
                  const data = b.data || {};
                  const snap = data.report_snapshot || {};
                  const reportId = b.report_id || data.report_id || `BLK-${b.block_index}`;
                  const crop = data.crop?.prediction || snap.crop_analysis?.prediction || 'Unknown';
                  const health = (data.health?.prediction || snap.health_prediction?.prediction || 'unknown').toLowerCase();
                  const disease = data.disease?.prediction || snap.disease_analysis?.prediction || 'None detected';
                  const confidence = data.disease?.confidence ?? snap.disease_analysis?.confidence ?? data.health?.confidence;
                  const severityLevel = data.severity?.severity || snap.severity?.severity || (health === 'healthy' ? 'Healthy' : 'Moderate');
                  const severityTheme = getSeverityTheme(severityLevel);
                  const isHealthy = health === 'healthy';

                  return (
                    <tr
                      key={b.current_hash || b.report_id || `blk-${b.block_index}`}
                      className="hover:bg-gray-50/80 dark:hover:bg-darkElevated/50 transition-colors"
                    >
                      <td className="p-3.5">
                        <span className="font-mono font-bold text-gray-900 dark:text-white block">
                          {reportId}
                        </span>
                        <span className="text-[10px] text-gray-400 flex items-center gap-1 mt-0.5 font-mono">
                          <Calendar className="w-3 h-3" />
                          <span>{formatDate(b.timestamp, { includeTime: true })}</span>
                        </span>
                      </td>

                      <td className="p-3.5 font-semibold text-gray-800 dark:text-gray-200 capitalize">
                        {crop}
                      </td>

                      <td className="p-3.5">
                        <span
                          className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                            isHealthy
                              ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300'
                              : 'bg-rose-50 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300'
                          }`}
                        >
                          {isHealthy ? (
                            <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                          ) : (
                            <AlertTriangle className="w-3 h-3 text-rose-600" />
                          )}
                          <span className="capitalize">{health}</span>
                        </span>
                      </td>

                      <td className="p-3.5 font-medium text-gray-900 dark:text-white capitalize">
                        {isHealthy ? 'Healthy Leaf' : toTitleCase(disease)}
                      </td>

                      <td className="p-3.5 font-mono font-bold text-gray-700 dark:text-gray-300">
                        {formatPercent(confidence)}
                      </td>

                      <td className="p-3.5">
                        <span className={`inline-block px-2 py-0.5 rounded-md text-[10px] font-bold ${severityTheme.badge}`}>
                          {severityLevel}
                        </span>
                      </td>

                      <td className="p-3.5">
                        {data.human_review?.resolution_status ? (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-50 text-blue-700 dark:bg-blue-950/60 dark:text-blue-300">
                            {data.human_review.resolution_status}
                          </span>
                        ) : data.human_review?.required ? (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-50 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300">
                            Review Required
                          </span>
                        ) : (
                          <span className="text-[11px] text-gray-400">Verified</span>
                        )}
                      </td>

                      <td className="p-3.5 text-right">
                        <Link
                          to={`/report?id=${encodeURIComponent(reportId)}`}
                          className="px-3 py-1.5 rounded-lg bg-gray-100 hover:bg-emerald-50 hover:text-emerald-700 dark:bg-darkElevated dark:hover:bg-emerald-950/60 dark:hover:text-emerald-300 font-semibold text-xs inline-flex items-center gap-1 transition-colors"
                        >
                          <FileText className="w-3 h-3" />
                          <span>View Report</span>
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

export default History;
