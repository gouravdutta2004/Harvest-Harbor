import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, Sun, Moon, ScanLine, ShieldCheck } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { SecurityModal } from './SecurityModal';

export function Topbar({ onToggleSidebar, isDarkMode, onToggleTheme }) {
  const location = useLocation();
  const { currentRole } = useAuth();
  const [securityModalOpen, setSecurityModalOpen] = useState(false);

  // Compute clean breadcrumb / page title
  const getPageTitle = () => {
    switch (location.pathname) {
      case '/':
        return 'Dashboard';
      case '/analyze':
        return 'Analyze Crop';
      case '/history':
        return 'Assessment History';
      case '/report':
        return 'Diagnostic Reports';
      case '/traceability':
        return 'Evidence Traceability';
      case '/review-queue':
      case '/review':
        return 'Human Review Queue';
      case '/about':
        return 'About the Platform';
      case '/help':
        return 'User Guide & FAQ';
      case '/limitations':
        return 'Scientific Scope';
      default:
        return 'Harvest Harbor';
    }
  };

  return (
    <>
      <header className="sticky top-0 z-30 h-16 sm:h-20 bg-white/90 dark:bg-darkCard/90 backdrop-blur-md border-b border-gray-200 dark:border-darkBorder px-4 sm:px-8 flex items-center justify-between transition-colors">
        {/* Left: Mobile Toggle & Page Title */}
        <div className="flex items-center gap-3 sm:gap-4">
          <button
            onClick={onToggleSidebar}
            className="p-2 rounded-xl text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-darkElevated lg:hidden"
            aria-label="Toggle navigation menu"
          >
            <Menu className="w-5 h-5" />
          </button>

          <Link to="/" className="flex items-center gap-2 lg:hidden flex-shrink-0" aria-label="Harvest Harbor Home">
            <img src="/logo.png" alt="Harvest Harbor Logo" className="w-8 h-8 rounded-lg object-cover border border-emerald-500/30" />
          </Link>

          <div>
            <h1 className="text-base sm:text-xl font-bold text-gray-900 dark:text-white tracking-tight">
              {getPageTitle()}
            </h1>
          </div>
        </div>

        {/* Right: Clean, Uncluttered Controls */}
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Active Role & Security Access */}
          <button
            onClick={() => setSecurityModalOpen(true)}
            type="button"
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl border border-gray-200 dark:border-darkBorder bg-gray-50 dark:bg-darkElevated text-gray-700 dark:text-gray-300 hover:text-emerald-600 dark:hover:text-emerald-400 hover:border-emerald-300 dark:hover:border-emerald-700/60 text-xs font-semibold transition-colors"
            title="Security & Access Governance (Role / API Key)"
          >
            <ShieldCheck className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            <span className="hidden sm:inline">{currentRole?.name || 'Field Agronomist'}</span>
          </button>

          {/* Theme Toggle */}
          <button
            onClick={onToggleTheme}
            className="p-2 rounded-xl border border-gray-200 dark:border-darkBorder bg-gray-50 dark:bg-darkElevated text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white hover:border-gray-300 dark:hover:border-emerald-700/60 transition-colors"
            aria-label={isDarkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            title={isDarkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
          >
            {isDarkMode ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-gray-600" />}
          </button>

          {/* Primary Action Button */}
          {location.pathname !== '/analyze' && (
            <Link
              to="/analyze"
              className="inline-flex items-center gap-2 px-3.5 sm:px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs sm:text-sm font-semibold shadow-glow-emerald transition-all transform active:scale-95"
            >
              <ScanLine className="w-4 h-4" />
              <span className="hidden sm:inline">New Analysis</span>
            </Link>
          )}
        </div>
      </header>

      {/* Security Governance & Persona Switcher Modal */}
      <SecurityModal
        isOpen={securityModalOpen}
        onClose={() => setSecurityModalOpen(false)}
      />
    </>
  );
}

export default Topbar;
