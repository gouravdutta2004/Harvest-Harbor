import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Sidebar } from './components/Sidebar';
import { Topbar } from './components/Topbar';
import { Dashboard } from './pages/Dashboard';
import { Analyze } from './pages/Analyze';
import { Report } from './pages/Report';
import { Traceability } from './pages/Traceability';
import { About } from './pages/About';
import { ReviewQueue } from './pages/ReviewQueue';
import { History } from './pages/History';
import { Help } from './pages/Help';
import { Limitations } from './pages/Limitations';
import { AuthProvider } from './context/AuthContext';
import { ErrorBoundary } from './components/ErrorBoundary';

export function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(() => {
    const saved = localStorage.getItem('harvest_harbor_theme');
    if (saved) return saved === 'dark';
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  });

  // Store latest report in session memory to effortlessly transition between Analyze & Report tabs
  const [latestReport, setLatestReport] = useState(null);
  const [latestImageSrc, setLatestImageSrc] = useState(null);

  // Sync theme to DOM
  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('harvest_harbor_theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('harvest_harbor_theme', 'light');
    }
  }, [isDarkMode]);

  const toggleTheme = () => {
    setIsDarkMode((prev) => !prev);
  };

  const handleReportGenerated = (reportData, imageSrc) => {
    setLatestReport(reportData);
    setLatestImageSrc(reportData?.image?.url || imageSrc);
  };

  return (
    <AuthProvider>
      <ErrorBoundary>
        <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
          <div className="min-h-screen bg-gray-50 dark:bg-darkBg text-gray-900 dark:text-gray-100 flex transition-colors duration-200">
            {/* Left Sidebar */}
            <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

            {/* Main Content Area */}
            <div className="flex-1 flex flex-col lg:pl-64 min-w-0">
              {/* Topbar */}
              <Topbar
                onToggleSidebar={() => setSidebarOpen((prev) => !prev)}
                isDarkMode={isDarkMode}
                onToggleTheme={toggleTheme}
              />

              {/* Routed Page Container */}
              <main className="flex-1 p-4 sm:p-8 overflow-y-auto">
                <ErrorBoundary>
                  <Routes>
                    <Route path="/" element={<Dashboard />} />
                    <Route
                      path="/analyze"
                      element={
                        <Analyze
                          onReportGenerated={handleReportGenerated}
                        />
                      }
                    />
                    <Route path="/history" element={<History />} />
                    <Route
                      path="/report"
                      element={<Report latestReport={latestReport} latestImageSrc={latestImageSrc} />}
                    />
                    <Route path="/traceability" element={<Traceability />} />
                    <Route path="/review-queue" element={<ReviewQueue />} />
                    <Route path="/review" element={<ReviewQueue />} />
                    <Route path="/about" element={<About />} />
                    <Route path="/help" element={<Help />} />
                    <Route path="/limitations" element={<Limitations />} />
                    <Route path="*" element={<Navigate to="/" replace />} />
                  </Routes>
                </ErrorBoundary>
              </main>
            </div>
          </div>
        </Router>
      </ErrorBoundary>
    </AuthProvider>
  );
}
export default App;
