import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldCheck, Copy, ExternalLink, Cpu, Clock, Hash, Check } from 'lucide-react';
import { formatDate } from '../utils/formatters';
import { HashDisplay } from './HashDisplay';

export function TraceabilityCard({ traceability, reportId, imageHash, timestamp, data, className = '' }) {
  const trace = traceability || data?.traceability;
  const id = reportId || data?.report_id || trace?.report_id;
  if (!trace && !id) return null;

  const hash = imageHash || data?.image?.sha256 || data?.evidence?.image_sha256 || trace?.image_sha256;
  const time = timestamp || data?.timestamp || trace?.timestamp;
  const blockchain = trace?.blockchain;

  return (
    <div className={`p-6 sm:p-7 rounded-3xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder shadow-subtle space-y-5 ${className}`}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold uppercase tracking-wider text-gray-900 dark:text-white">
              Cryptographic Traceability
            </h3>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
              Tamper-evident record logged to the local SHA-256 evidence chain.
            </p>
          </div>
        </div>

        {id && (
          <Link
            to={`/traceability?query=${encodeURIComponent(id)}`}
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-700 hover:text-emerald-800 dark:text-emerald-400 dark:hover:text-emerald-300 hover:underline"
          >
            <span>Verify in Evidence Chain</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </Link>
        )}
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 text-xs">
        {/* Report ID */}
        <div className="p-4 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder space-y-1">
          <span className="font-semibold text-gray-500 dark:text-gray-400 block">
            Crop Report ID
          </span>
          <div className="font-mono font-bold text-gray-900 dark:text-white text-sm">
            {id || 'Pending'}
          </div>
          <span className="text-[10px] text-gray-400 dark:text-gray-500">
            Unique diagnostic identifier
          </span>
        </div>

        {/* Timestamp */}
        <div className="p-4 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder space-y-1">
          <span className="font-semibold text-gray-500 dark:text-gray-400 block flex items-center gap-1.5">
            <Clock className="w-3 h-3 text-gray-400" />
            UTC Timestamp
          </span>
          <div className="font-mono text-gray-800 dark:text-gray-200">
            {formatDate(time)}
          </div>
          <span className="text-[10px] text-gray-400 dark:text-gray-500">
            ISO-8601 atomic timestamp
          </span>
        </div>

        {/* Image Hash */}
        <div className="p-4 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder space-y-1 sm:col-span-2 lg:col-span-1">
          <span className="font-semibold text-gray-500 dark:text-gray-400 block flex items-center gap-1.5">
            <Hash className="w-3 h-3 text-gray-400" />
            Image SHA-256 Hash
          </span>
          <HashDisplay hash={hash} startChars={6} endChars={6} />
          <span className="text-[10px] text-gray-400 dark:text-gray-500 block">
            Cryptographic image digest
          </span>
        </div>
      </div>

      {/* Model Versions Section */}
      {trace?.health_model && (
        <div className="p-4 rounded-2xl bg-gray-50/70 dark:bg-darkElevated/50 border border-gray-200/80 dark:border-darkBorder space-y-2">
          <span className="text-[11px] font-bold uppercase tracking-wider text-gray-600 dark:text-gray-400 flex items-center gap-1.5">
            <Cpu className="w-3.5 h-3.5 text-emerald-600" />
            Model Version Signatures
          </span>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-[11px] font-mono">
            <div className="p-2 rounded-xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder">
              <span className="text-gray-500 dark:text-gray-400 block text-[10px]">Health Screening:</span>
              <span className="text-gray-900 dark:text-white font-semibold">
                {trace.health_model.name || 'health_disease_efficientnetb0'}
              </span>
            </div>
            <div className="p-2 rounded-xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder">
              <span className="text-gray-500 dark:text-gray-400 block text-[10px]">Disease Classifier:</span>
              <span className="text-gray-900 dark:text-white font-semibold">
                {trace.disease_model?.name || 'plantwild_v2_efficientnetb0'}
              </span>
            </div>
            <div className="p-2 rounded-xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder">
              <span className="text-gray-500 dark:text-gray-400 block text-[10px]">Segmentation Model:</span>
              <span className="text-gray-900 dark:text-white font-semibold">
                {trace.segmentation_model?.name || 'unet_plantseg'}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
export default TraceabilityCard;
