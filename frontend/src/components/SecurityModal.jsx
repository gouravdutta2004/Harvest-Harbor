import React, { useState } from 'react';
import {
  Shield,
  ShieldCheck,
  Key,
  UserCheck,
  X,
  Lock,
  Check,
  Info,
  Cpu,
  Fingerprint,
  RefreshCw,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export function SecurityModal({ isOpen, onClose }) {
  const {
    role,
    currentRole,
    setRole,
    apiKey,
    setApiKey,
    authHeaderType,
    setAuthHeaderType,
    inspectorId,
    inspectorName,
    setInspectorInfo,
    availableRoles,
  } = useAuth();

  const [tempApiKey, setTempApiKey] = useState(apiKey);
  const [tempHeaderType, setTempHeaderType] = useState(authHeaderType);
  const [tempInspectorId, setTempInspectorId] = useState(inspectorId);
  const [tempInspectorName, setTempInspectorName] = useState(inspectorName);
  const [savedSuccess, setSavedSuccess] = useState(false);

  if (!isOpen) return null;

  const handleSave = (e) => {
    e.preventDefault();
    setApiKey(tempApiKey);
    setAuthHeaderType(tempHeaderType);
    setInspectorInfo(tempInspectorId, tempInspectorName);
    setSavedSuccess(true);
    setTimeout(() => {
      setSavedSuccess(false);
      onClose();
    }, 800);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div
        className="w-full max-w-2xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder rounded-3xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-6 border-b border-gray-100 dark:border-darkBorder flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-2xl bg-emerald-100 dark:bg-emerald-950/80 text-emerald-600 dark:text-emerald-400">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-gray-900 dark:text-white">
                Security &amp; Access Governance
              </h2>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Role-based access control, cryptographic verification, and API credentials.
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            type="button"
            className="p-2 rounded-xl text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-darkElevated transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <form onSubmit={handleSave} className="p-6 overflow-y-auto space-y-6">
          {/* 1. Active Role Selection */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold uppercase tracking-wider text-gray-700 dark:text-gray-300 flex items-center gap-1.5">
                <UserCheck className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                <span>Active User Persona / Role</span>
              </label>
              <span className="text-[11px] font-mono text-gray-400">
                RBAC Policy: Active
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {availableRoles.map((r) => {
                const isSelected = role === r.id;
                return (
                  <button
                    key={r.id}
                    type="button"
                    onClick={() => setRole(r.id)}
                    className={`p-3.5 rounded-2xl border text-left transition-all ${
                      isSelected
                        ? 'border-emerald-500 bg-emerald-50/70 dark:bg-emerald-950/40 ring-2 ring-emerald-500/20'
                        : 'border-gray-200 dark:border-darkBorder bg-gray-50/50 dark:bg-darkElevated/40 hover:border-gray-300 dark:hover:border-darkBorder'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-bold text-gray-900 dark:text-white">
                        {r.name}
                      </span>
                      {isSelected && (
                        <Check className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                      )}
                    </div>
                    <p className="text-[11px] text-gray-500 dark:text-gray-400 line-clamp-2">
                      {r.description}
                    </p>
                  </button>
                );
              })}
            </div>
          </div>

          {/* 2. Inspector Metadata (Stamped on generated reports) */}
          <div className="space-y-3 pt-2 border-t border-gray-100 dark:border-darkBorder">
            <label className="text-xs font-bold uppercase tracking-wider text-gray-700 dark:text-gray-300 flex items-center gap-1.5">
              <Fingerprint className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
              <span>Inspector Attestation Metadata</span>
            </label>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="text-[11px] text-gray-500 dark:text-gray-400 block mb-1">
                  Inspector Name / Title
                </label>
                <input
                  type="text"
                  value={tempInspectorName}
                  onChange={(e) => setTempInspectorName(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-gray-200 dark:border-darkBorder bg-gray-50 dark:bg-darkElevated text-gray-900 dark:text-white text-xs focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="text-[11px] text-gray-500 dark:text-gray-400 block mb-1">
                  Inspector Stamp / Badge ID
                </label>
                <input
                  type="text"
                  value={tempInspectorId}
                  onChange={(e) => setTempInspectorId(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-gray-200 dark:border-darkBorder bg-gray-50 dark:bg-darkElevated text-gray-900 dark:text-white text-xs font-mono focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                />
              </div>
            </div>
          </div>

          {/* 3. API Authentication Credentials */}
          <div className="space-y-3 pt-2 border-t border-gray-100 dark:border-darkBorder">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold uppercase tracking-wider text-gray-700 dark:text-gray-300 flex items-center gap-1.5">
                <Key className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                <span>Backend Security Credentials (Optional)</span>
              </label>
              <div className="flex items-center gap-1 text-[11px]">
                <button
                  type="button"
                  onClick={() => setTempHeaderType('bearer')}
                  className={`px-2 py-0.5 rounded-md ${
                    tempHeaderType === 'bearer'
                      ? 'bg-emerald-600 text-white font-semibold'
                      : 'text-gray-400 hover:text-gray-600'
                  }`}
                >
                  Bearer
                </button>
                <button
                  type="button"
                  onClick={() => setTempHeaderType('apikey')}
                  className={`px-2 py-0.5 rounded-md ${
                    tempHeaderType === 'apikey'
                      ? 'bg-emerald-600 text-white font-semibold'
                      : 'text-gray-400 hover:text-gray-600'
                  }`}
                >
                  X-API-Key
                </button>
              </div>
            </div>

            <div>
              <input
                type="password"
                value={tempApiKey}
                onChange={(e) => setTempApiKey(e.target.value)}
                placeholder="Enter enterprise API key or Bearer token (leave blank for local dev)"
                className="w-full px-3.5 py-2.5 rounded-xl border border-gray-200 dark:border-darkBorder bg-gray-50 dark:bg-darkElevated text-gray-900 dark:text-white text-xs font-mono focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
              />
              <p className="text-[10px] text-gray-400 mt-1">
                When provided, this credential is automatically attached to all diagnostic &amp; traceability requests.
              </p>
            </div>
          </div>

          {/* 4. Security Audit & Integrity Check */}
          <div className="p-4 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder space-y-2 text-xs">
            <span className="font-bold text-gray-900 dark:text-white block">
              Cryptographic Integrity Verification
            </span>
            <div className="grid grid-cols-2 gap-2 text-[11px] text-gray-600 dark:text-gray-400">
              <div>• Hash Algorithm: <span className="font-mono font-bold text-gray-800 dark:text-gray-200">SHA-256</span></div>
              <div>• Chain Type: <span className="font-mono font-bold text-gray-800 dark:text-gray-200">Tamper-Evident Hash Chain</span></div>
              <div>• Request Headers: <span className="font-mono font-bold text-gray-800 dark:text-gray-200">Sanitized</span></div>
              <div>• Local Storage: <span className="font-mono font-bold text-gray-800 dark:text-gray-200">Session-Scoped</span></div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="pt-2 flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2.5 rounded-xl border border-gray-200 dark:border-darkBorder text-gray-600 dark:text-gray-300 text-xs font-semibold hover:bg-gray-50 dark:hover:bg-darkElevated transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold shadow-glow-emerald flex items-center gap-1.5 transition-all"
            >
              {savedSuccess ? (
                <>
                  <Check className="w-4 h-4 text-white" />
                  <span>Preferences Saved</span>
                </>
              ) : (
                <>
                  <Lock className="w-4 h-4" />
                  <span>Apply Security Settings</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default SecurityModal;
