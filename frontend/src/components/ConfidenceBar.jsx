import React from 'react';
import { formatPercent } from '../utils/formatters';

export function ConfidenceBar({
  percentage,
  label = null,
  colorScheme = 'emerald', // 'emerald' | 'amber' | 'rose' | 'dynamic'
  height = 'h-2.5',
  showValue = true,
  className = '',
}) {
  const numeric = typeof percentage === 'number' ? Math.max(0, Math.min(100, percentage)) : 0;

  const getColorClass = () => {
    if (colorScheme === 'dynamic') {
      if (numeric >= 75) return 'bg-emerald-500';
      if (numeric >= 50) return 'bg-amber-500';
      return 'bg-rose-500';
    }
    switch (colorScheme) {
      case 'rose':
        return 'bg-rose-500';
      case 'amber':
        return 'bg-amber-500';
      case 'emerald':
      default:
        return 'bg-emerald-500';
    }
  };

  return (
    <div className={`space-y-1.5 ${className}`}>
      {(label || showValue) && (
        <div className="flex justify-between items-center text-xs">
          {label && (
            <span className="font-medium text-gray-700 dark:text-gray-300">
              {label}
            </span>
          )}
          {showValue && (
            <span className="font-mono font-semibold text-gray-900 dark:text-white">
              {formatPercent(percentage)}
            </span>
          )}
        </div>
      )}

      <div className={`w-full bg-gray-100 dark:bg-darkElevated rounded-full overflow-hidden ${height}`}>
        <div
          className={`${height} ${getColorClass()} rounded-full transition-all duration-500 ease-out`}
          style={{ width: `${numeric}%` }}
        />
      </div>
    </div>
  );
}
export default ConfidenceBar;
