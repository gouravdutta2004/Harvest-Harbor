/**
 * UI Formatters & Helpers for Harvest Harbor
 */

/**
 * Formats a float or number into a readable percentage string (assumes 0-100 scale).
 * @param {number|null|undefined} val
 * @param {number} decimals
 */
export function formatPercent(val, decimals = 2) {
  if (val === null || val === undefined || isNaN(Number(val))) {
    return 'Not available';
  }
  return `${Number(val).toFixed(decimals)}%`;
}

/**
 * Formats a probability fraction (0.0 to 1.0) into a readable percentage string.
 * @param {number|null|undefined} val
 * @param {number} decimals
 */
export function formatFractionPercent(val, decimals = 2) {
  if (val === null || val === undefined || isNaN(Number(val))) {
    return 'Not available';
  }
  const pct = Number(val) * 100;
  return `${pct.toFixed(decimals)}%`;
}

/**
 * Formats a raw integer pixel count or count.
 * @param {number|null|undefined} val
 */
export function formatNumber(val) {
  if (val === null || val === undefined || isNaN(Number(val))) {
    return '0';
  }
  return new Intl.NumberFormat().format(Number(val));
}

/**
 * Formats ISO timestamp to human readable format.
 * @param {string|null|undefined} isoString
 * @param {{ includeTime?: boolean }} [options]
 */
export function formatDate(isoString, { includeTime = true } = {}) {
  if (!isoString) return 'Not available';
  try {
    const d = new Date(isoString);
    if (isNaN(d.getTime())) return isoString;
    const dateOptions = {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    };
    if (includeTime) {
      dateOptions.hour = '2-digit';
      dateOptions.minute = '2-digit';
      dateOptions.second = '2-digit';
      dateOptions.timeZoneName = 'short';
    }
    return new Intl.DateTimeFormat('en-US', dateOptions).format(d);
  } catch {
    return isoString;
  }
}

/**
 * Truncates a long cryptographic hash (e.g. SHA-256) for compact display.
 * @param {string} hash
 * @param {number} startChars
 * @param {number} endChars
 */
export function truncateHash(hash, startChars = 8, endChars = 8) {
  if (!hash || typeof hash !== 'string') return 'Not available';
  if (hash.length <= startChars + endChars) return hash;
  return `${hash.slice(0, startChars)}...${hash.slice(-endChars)}`;
}

/**
 * Converts a snake_case or hyphenated string into Title Case.
 * @param {string} text
 */
export function toTitleCase(text) {
  if (!text || typeof text !== 'string') return '';
  return text
    .replace(/[_-]/g, ' ')
    .split(' ')
    .map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
    .join(' ');
}

/**
 * Returns color classes for health status.
 */
export function getHealthStatusTheme(status) {
  const s = String(status || '').toLowerCase();
  if (s === 'healthy') {
    return {
      bg: 'bg-emerald-50 dark:bg-emerald-950/40',
      border: 'border-emerald-200 dark:border-emerald-800',
      text: 'text-emerald-700 dark:text-emerald-300',
      dot: 'bg-emerald-500',
      badge: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/60 dark:text-emerald-200',
    };
  }
  if (s === 'diseased') {
    return {
      bg: 'bg-rose-50 dark:bg-rose-950/40',
      border: 'border-rose-200 dark:border-rose-800',
      text: 'text-rose-700 dark:text-rose-300',
      dot: 'bg-rose-500',
      badge: 'bg-rose-100 text-rose-800 dark:bg-rose-900/60 dark:text-rose-200',
    };
  }
  return {
    bg: 'bg-amber-50 dark:bg-amber-950/40',
    border: 'border-amber-200 dark:border-amber-800',
    text: 'text-amber-700 dark:text-amber-300',
    dot: 'bg-amber-500',
    badge: 'bg-amber-100 text-amber-800 dark:bg-amber-900/60 dark:text-amber-200',
  };
}

/**
 * Returns color classes for severity stages.
 */
export function getSeverityTheme(severity) {
  const s = String(severity || '').toLowerCase();
  switch (s) {
    case 'healthy':
      return {
        label: 'Healthy',
        color: 'text-emerald-600 dark:text-emerald-400',
        bg: 'bg-emerald-50 dark:bg-emerald-950/50',
        border: 'border-emerald-200 dark:border-emerald-800',
        badge: 'bg-emerald-100 dark:bg-emerald-900/60 text-emerald-800 dark:text-emerald-200',
      };
    case 'early':
      return {
        label: 'Early Stage',
        color: 'text-amber-600 dark:text-amber-400',
        bg: 'bg-amber-50 dark:bg-amber-950/50',
        border: 'border-amber-200 dark:border-amber-800',
        badge: 'bg-amber-100 dark:bg-amber-900/60 text-amber-800 dark:text-amber-200',
      };
    case 'moderate':
      return {
        label: 'Moderate Stage',
        color: 'text-orange-600 dark:text-orange-400',
        bg: 'bg-orange-50 dark:bg-orange-950/50',
        border: 'border-orange-200 dark:border-orange-800',
        badge: 'bg-orange-100 dark:bg-orange-900/60 text-orange-800 dark:text-orange-200',
      };
    case 'severe':
      return {
        label: 'Severe Stage',
        color: 'text-rose-600 dark:text-rose-400',
        bg: 'bg-rose-50 dark:bg-rose-950/50',
        border: 'border-rose-200 dark:border-rose-800',
        badge: 'bg-rose-100 dark:bg-rose-900/60 text-rose-800 dark:text-rose-200',
      };
    default:
      return {
        label: severity || 'Not available',
        color: 'text-gray-600 dark:text-gray-400',
        bg: 'bg-gray-50 dark:bg-darkCard',
        border: 'border-gray-200 dark:border-darkBorder',
        badge: 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200',
      };
  }
}
