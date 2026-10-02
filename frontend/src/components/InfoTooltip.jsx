import React, { useState } from 'react';
import { HelpCircle, Info, X } from 'lucide-react';

/**
 * Accessible InfoTooltip / Explainer component for progressive disclosure.
 * Provides a subtle icon and an optional popover or inline drawer explaining complex AI concepts.
 */
export function InfoTooltip({
  title,
  content,
  learnMoreUrl,
  buttonLabel = 'What does this mean?',
  variant = 'icon', // 'icon' | 'link' | 'badge'
  className = '',
}) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className={`relative inline-flex items-center ${className}`}>
      {variant === 'icon' && (
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className="text-gray-400 hover:text-emerald-600 dark:hover:text-emerald-400 p-0.5 rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
          title={title || 'Learn more'}
          aria-label={title || 'Learn more'}
        >
          <HelpCircle className="w-3.5 h-3.5" />
        </button>
      )}

      {variant === 'link' && (
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className="text-[11px] font-medium text-emerald-600 dark:text-emerald-400 hover:underline inline-flex items-center gap-1 focus:outline-none"
        >
          <Info className="w-3 h-3" />
          <span>{buttonLabel}</span>
        </button>
      )}

      {variant === 'badge' && (
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-gray-100 dark:bg-darkElevated text-gray-600 dark:text-gray-300 hover:bg-emerald-50 dark:hover:bg-emerald-950/40 hover:text-emerald-700 dark:hover:text-emerald-300 border border-gray-200 dark:border-darkBorder transition-colors inline-flex items-center gap-1"
        >
          <Info className="w-2.5 h-2.5" />
          <span>{buttonLabel}</span>
        </button>
      )}

      {/* Popover Card */}
      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
            aria-hidden="true"
          />
          <div className="absolute z-50 bottom-full mb-2 left-0 sm:left-auto sm:right-0 w-72 sm:w-80 p-4 rounded-2xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder shadow-premium text-left text-xs space-y-2 animate-fade-in">
            <div className="flex items-center justify-between border-b border-gray-100 dark:border-darkBorder pb-2">
              <span className="font-bold text-gray-900 dark:text-white flex items-center gap-1.5">
                <Info className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                <span>{title || 'Understanding this AI Metric'}</span>
              </span>
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 p-0.5 rounded-md"
                aria-label="Close explainer"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
            <div className="text-gray-600 dark:text-gray-300 leading-relaxed text-[11px]">
              {content}
            </div>
            {learnMoreUrl && (
              <div className="pt-1 border-t border-gray-100 dark:border-darkBorder">
                <a
                  href={learnMoreUrl}
                  className="text-[11px] font-semibold text-emerald-600 dark:text-emerald-400 hover:underline"
                >
                  Read full scientific documentation &rarr;
                </a>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

export default InfoTooltip;
