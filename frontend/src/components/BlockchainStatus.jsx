import React from 'react';
import { ShieldCheck, ShieldAlert, ArrowDown, Database, CheckCircle2, AlertTriangle, Layers } from 'lucide-react';
import { formatDate, truncateHash } from '../utils/formatters';
import { HashDisplay } from './HashDisplay';

export function BlockchainStatus({
  blockchain,
  currentReportId = null,
  chain = [],
  className = '',
}) {
  if (!blockchain) return null;

  const isValid = blockchain.chain_valid === true;
  const isEnabled = blockchain.enabled !== false;
  const blockIndex = blockchain.block_index;
  const checkedBlocks = blockchain.checked_blocks;
  const invalidBlock = blockchain.invalid_block;

  return (
    <div className={`p-6 sm:p-7 rounded-3xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder shadow-subtle space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div
            className={`p-2.5 rounded-xl ${
              isValid
                ? 'bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400'
                : 'bg-rose-50 dark:bg-rose-950/60 text-rose-600 dark:text-rose-400'
            }`}
          >
            {isValid ? <ShieldCheck className="w-5 h-5" /> : <ShieldAlert className="w-5 h-5" />}
          </div>
          <div>
            <h3 className="text-sm font-bold uppercase tracking-wider text-gray-900 dark:text-white">
              Tamper-Evident Evidence Chain
            </h3>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
              Local SHA-256 hash-linked evidence chain preventing post-hoc alteration.
            </p>
          </div>
        </div>

        {/* Verification Status Pill */}
        <div
          className={`px-3.5 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider flex items-center gap-2 border ${
            isValid
              ? 'bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800'
              : 'bg-rose-50 dark:bg-rose-950/50 text-rose-700 dark:text-rose-300 border-rose-200 dark:border-rose-800'
          }`}
        >
          {isValid ? (
            <>
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
              <span>Evidence Chain Valid</span>
            </>
          ) : (
            <>
              <AlertTriangle className="w-3.5 h-3.5 text-rose-600 dark:text-rose-400" />
              <span>Integrity Check Failed</span>
            </>
          )}
        </div>
      </div>

      {/* Current Block Metadata Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Record Index */}
        <div className="p-4 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder space-y-1">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 block">
            Evidence Record Index
          </span>
          <div className="text-xl font-mono font-bold text-gray-900 dark:text-white">
            #{blockIndex !== undefined ? blockIndex : 'N/A'}
          </div>
          <span className="text-[10px] text-gray-400 dark:text-gray-500">
            {checkedBlocks ? `${checkedBlocks} records verified` : 'Evidence chain position'}
          </span>
        </div>

        {/* Previous Hash */}
        <div className="p-4 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder space-y-1 sm:col-span-1">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 block">
            Previous Hash
          </span>
          <HashDisplay hash={blockchain.previous_hash} startChars={6} endChars={6} />
          <span className="text-[10px] text-gray-400 dark:text-gray-500 block truncate">
            Parent record linkage
          </span>
        </div>

        {/* Current Hash */}
        <div className="p-4 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder space-y-1 sm:col-span-2">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 block">
            Current Record Hash (SHA-256)
          </span>
          <HashDisplay hash={blockchain.current_hash} startChars={10} endChars={10} />
          <span className="text-[10px] text-gray-400 dark:text-gray-500 block truncate">
            Canonical JSON digest of assessment payload
          </span>
        </div>
      </div>

      {/* Visual Chain Progression (If chain list is provided) */}
      {chain && chain.length > 0 && (
        <div className="space-y-3 pt-2">
          <span className="text-xs font-bold uppercase tracking-wider text-gray-700 dark:text-gray-300 flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-emerald-600" />
            Evidence Chain Progression
          </span>

          <div className="space-y-2">
            {chain.map((block, idx) => {
              const isCurrent =
                (currentReportId && block.report_id === currentReportId) ||
                block.block_index === blockIndex;

              return (
                <div key={block.block_index ?? idx}>
                  <div
                    className={`p-3.5 rounded-2xl border transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs ${
                      isCurrent
                        ? 'bg-emerald-50/70 dark:bg-emerald-950/40 border-emerald-300 dark:border-emerald-800 shadow-subtle scale-[1.01]'
                        : 'bg-gray-50/60 dark:bg-darkElevated/50 border-gray-200 dark:border-darkBorder'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <span
                        className={`w-6 h-6 rounded-lg flex items-center justify-center font-mono text-[11px] font-bold ${
                          isCurrent
                            ? 'bg-emerald-600 text-white'
                            : 'bg-gray-200 dark:bg-darkBorder text-gray-700 dark:text-gray-300'
                        }`}
                      >
                        {block.block_index}
                      </span>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-gray-900 dark:text-white">
                            {block.report_id}
                          </span>
                          {block.block_type === 'genesis' && (
                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-100 text-blue-800 dark:bg-blue-900/60 dark:text-blue-300 uppercase font-semibold">
                              Genesis
                            </span>
                          )}
                          {isCurrent && (
                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-800 dark:bg-emerald-900/60 dark:text-emerald-300 uppercase font-semibold">
                              Current Record
                            </span>
                          )}
                        </div>
                        <span className="text-[10px] text-gray-500 dark:text-gray-400">
                          {formatDate(block.timestamp)}
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 sm:text-right font-mono text-[11px]">
                      <HashDisplay hash={block.current_hash} startChars={6} endChars={6} />
                    </div>
                  </div>

                  {idx < chain.length - 1 && (
                    <div className="flex justify-center py-1 text-gray-300 dark:text-gray-600">
                      <ArrowDown className="w-3.5 h-3.5" />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
export default BlockchainStatus;
