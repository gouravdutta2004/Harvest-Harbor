import React from 'react';

export function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  iconColor = 'text-emerald-600 dark:text-emerald-400',
  iconBg = 'bg-emerald-50 dark:bg-emerald-950/50',
  badge = null,
  badgeType = 'neutral', // 'success' | 'warning' | 'danger' | 'neutral'
  className = '',
}) {
  const getBadgeStyle = () => {
    switch (badgeType) {
      case 'success':
        return 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300';
      case 'warning':
        return 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300';
      case 'danger':
        return 'bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-300';
      default:
        return 'bg-gray-100 text-gray-700 dark:bg-darkElevated dark:text-gray-300';
    }
  };

  return (
    <div
      className={`p-6 rounded-2xl bg-white dark:bg-darkCard border border-gray-200/80 dark:border-darkBorder shadow-subtle hover:shadow-premium hover:border-gray-300 dark:hover:border-darkBorderSubtle transition-all ${className}`}
    >
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <span className="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">
            {title}
          </span>
          <div className="text-2xl sm:text-3xl font-extrabold text-gray-900 dark:text-white tracking-tight">
            {value}
          </div>
        </div>
        {Icon && (
          <div className={`p-3 rounded-xl ${iconBg} ${iconColor}`}>
            <Icon className="w-5 h-5" />
          </div>
        )}
      </div>

      {(subtitle || badge) && (
        <div className="mt-4 flex items-center justify-between gap-2 pt-3 border-t border-gray-100 dark:border-darkBorder">
          {subtitle && (
            <span className="text-xs text-gray-500 dark:text-gray-400 truncate">
              {subtitle}
            </span>
          )}
          {badge && (
            <span
              className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${getBadgeStyle()}`}
            >
              {badge}
            </span>
          )}
        </div>
      )}
    </div>
  );
}
export default StatCard;
