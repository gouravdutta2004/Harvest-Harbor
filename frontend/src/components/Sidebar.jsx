import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  ScanLine,
  FileText,
  ShieldCheck,
  Info,
  Activity,
  X,
  Sparkles,
  ClipboardList,
  History as HistoryIcon,
  HelpCircle,
  ShieldAlert,
  Key,
} from 'lucide-react';
import { useBackendStatus } from '../hooks/useBackendStatus';
import { useAuth } from '../context/AuthContext';
import { SecurityModal } from './SecurityModal';

export function Sidebar({ isOpen, onClose }) {
  const { isOnline, status, healthData } = useBackendStatus();
  const { hasPermission, currentRole } = useAuth();
  const [securityModalOpen, setSecurityModalOpen] = useState(false);

  const navItems = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/analyze', label: 'Analyze Crop', icon: ScanLine, highlight: true },
    { to: '/history', label: 'History', icon: HistoryIcon },
    { to: '/report', label: 'Reports', icon: FileText },
    { to: '/traceability', label: 'Traceability', icon: ShieldCheck },
    { to: '/about', label: 'About', icon: Info },
    { to: '/help', label: 'Help & Guide', icon: HelpCircle },
    { to: '/limitations', label: 'Limitations', icon: ShieldAlert },
  ];

  const reviewItem = { to: '/review-queue', label: 'Review Queue', icon: ClipboardList };

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm lg:hidden transition-opacity"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 w-64 bg-white dark:bg-darkCard border-r border-gray-200 dark:border-darkBorder flex flex-col transition-transform duration-200 ease-in-out lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Brand Header */}
        <div className="h-20 px-6 border-b border-gray-100 dark:border-darkBorder flex items-center justify-between">
          <NavLink to="/" className="flex items-center gap-3 group" onClick={onClose}>
            <div className="w-10 h-10 rounded-xl overflow-hidden shadow-glow-emerald group-hover:scale-105 transition-transform flex-shrink-0 bg-emerald-950 flex items-center justify-center border border-emerald-500/30">
              <img src="/logo.png" alt="Harvest Harbor Logo" className="w-full h-full object-cover" />
            </div>
            <div>
              <div className="flex items-center gap-1.5 font-bold tracking-tight text-gray-900 dark:text-white leading-tight">
                <span className="text-emerald-700 dark:text-emerald-400">HARVEST</span>
                <span>HARBOR</span>
              </div>
              <div className="text-[11px] font-medium text-gray-600 dark:text-emerald-400/90 tracking-wide uppercase">
                AI Crop Intelligence
              </div>
            </div>
          </NavLink>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-darkElevated lg:hidden"
            aria-label="Close navigation"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation Links */}
        <nav className="flex-1 px-4 py-6 space-y-1.5 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={onClose}
                end={item.to === '/'}
                className={({ isActive }) =>
                  `flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-emerald-50 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300 font-semibold shadow-subtle border border-emerald-100 dark:border-emerald-800/60'
                      : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-darkElevated hover:text-gray-900 dark:hover:text-gray-200'
                  }`
                }
              >
                {({ isActive }) => (
                  <div className="flex items-center gap-3">
                    <Icon
                      className={`w-5 h-5 ${
                        isActive
                          ? 'text-emerald-700 dark:text-emerald-400'
                          : 'text-gray-400 dark:text-gray-500'
                      }`}
                    />
                    <span>{item.label}</span>
                  </div>
                )}
              </NavLink>
            );
          })}

          {/* Review Queue — visible to agronomist/admin only */}
          {hasPermission('review_reports') && (() => {
            const Icon = reviewItem.icon;
            return (
              <NavLink
                key={reviewItem.to}
                to={reviewItem.to}
                onClick={onClose}
                className={({ isActive }) =>
                  `flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-emerald-50 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300 font-semibold shadow-subtle border border-emerald-100 dark:border-emerald-800/60'
                      : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-darkElevated hover:text-gray-900 dark:hover:text-gray-200'
                  }`
                }
              >
                {({ isActive }) => (
                  <div className="flex items-center gap-3">
                    <Icon
                      className={`w-5 h-5 ${
                        isActive
                          ? 'text-emerald-700 dark:text-emerald-400'
                          : 'text-gray-400 dark:text-gray-500'
                      }`}
                    />
                    <span>{reviewItem.label}</span>
                  </div>
                )}
              </NavLink>
            );
          })()}

        </nav>

        {/* Active Role & Security Access */}
        <div className="px-4 pt-3 border-t border-gray-100 dark:border-darkBorder">
          <button
            onClick={() => setSecurityModalOpen(true)}
            type="button"
            className="w-full px-3 py-2 rounded-xl bg-gray-50 hover:bg-gray-100 dark:bg-darkElevated dark:hover:bg-darkBorder border border-gray-200 dark:border-darkBorder flex items-center justify-between transition-colors text-left group"
          >
            <div className="flex items-center gap-2.5">
              <div className="w-6 h-6 rounded-lg bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-400 flex items-center justify-center flex-shrink-0">
                <ShieldCheck className="w-3.5 h-3.5" />
              </div>
              <div>
                <div className="text-xs font-bold text-gray-900 dark:text-white leading-none">
                  {currentRole?.name || 'Field Agronomist'}
                </div>
                <div className="text-[10px] text-gray-500 dark:text-gray-400 mt-0.5">
                  RBAC &amp; API Key
                </div>
              </div>
            </div>
            <Key className="w-3.5 h-3.5 text-gray-400 group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors" />
          </button>
        </div>

        {/* System Health / Status Card at Bottom */}
        <div className="p-4 border-t border-gray-100 dark:border-darkBorder">
          <div className="p-3.5 rounded-xl bg-gray-50 dark:bg-darkElevated border border-gray-200 dark:border-darkBorder">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 flex items-center gap-1.5">
                <Activity className="w-3.5 h-3.5" />
                System Status
              </span>
              <span
                className={`inline-flex items-center gap-1.5 text-xs font-medium px-2 py-0.5 rounded-full ${
                  isOnline
                    ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300'
                    : 'bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-300'
                }`}
              >
                <span
                  className={`w-1.5 h-1.5 rounded-full animate-pulse ${
                    isOnline ? 'bg-emerald-500' : 'bg-rose-500'
                  }`}
                />
                {status === 'checking'
                  ? 'Checking...'
                  : isOnline
                  ? 'Connected'
                  : 'Offline'}
              </span>
            </div>

            <div className="text-[11px] text-gray-500 dark:text-gray-400 space-y-1">
              <div className="flex justify-between">
                <span>FastAPI Backend:</span>
                <span className="font-mono text-gray-700 dark:text-gray-300">
                  {isOnline ? 'Active (Port 8000)' : 'Unreachable'}
                </span>
              </div>
              {healthData?.knowledge_base?.disease_count && (
                <div className="flex justify-between">
                  <span>Knowledge Base:</span>
                  <span className="text-gray-700 dark:text-gray-300 font-medium">
                    {healthData.knowledge_base.disease_count} diseases
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      </aside>

      {/* Security & Access Modal */}
      <SecurityModal
        isOpen={securityModalOpen}
        onClose={() => setSecurityModalOpen(false)}
      />
    </>
  );
}
export default Sidebar;
