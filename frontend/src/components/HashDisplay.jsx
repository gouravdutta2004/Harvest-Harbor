import React, { useState } from 'react';
import { Copy, Check } from 'lucide-react';
import { truncateHash } from '../utils/formatters';

export function HashDisplay({
  hash,
  label = null,
  truncate = true,
  startChars = 8,
  endChars = 8,
  className = '',
}) {
  const [copied, setCopied] = useState(false);

  if (!hash) {
    return <span className="text-gray-400 dark:text-gray-500 italic text-sm">Not available</span>;
  }

  const displayText = truncate ? truncateHash(hash, startChars, endChars) : hash;

  const handleCopy = async (e) => {
    e.stopPropagation();
    try {
      await navigator.clipboard.writeText(hash);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy hash:', err);
    }
  };

  return (
    <div className={`inline-flex items-center gap-1.5 font-mono text-xs ${className}`}>
      {label && <span className="text-gray-500 dark:text-gray-400 font-sans">{label}:</span>}
      <code
        className="px-2 py-0.5 rounded bg-gray-100 dark:bg-darkElevated border border-gray-200 dark:border-darkBorder text-gray-800 dark:text-gray-200 select-all"
        title={hash}
      >
        {displayText}
      </code>
      <button
        onClick={handleCopy}
        type="button"
        className="p-1 rounded text-gray-400 hover:text-emerald-600 dark:hover:text-emerald-400 hover:bg-gray-100 dark:hover:bg-darkElevated transition-colors"
        title={copied ? 'Copied!' : 'Copy full hash'}
        aria-label="Copy hash to clipboard"
      >
        {copied ? (
          <Check className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
        ) : (
          <Copy className="w-3.5 h-3.5" />
        )}
      </button>
    </div>
  );
}
export default HashDisplay;
