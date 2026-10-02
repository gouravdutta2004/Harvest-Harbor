/**
 * Harvest Harbor Role-Based Access Control (RBAC) Context.
 *
 * DEVELOPMENT NOTE ON LOCALSTORAGE SECURITY:
 * For this prototype, API keys and Inspector metadata are stored in localStorage
 * so that developers can test persona switching (Farmer, Agronomist, Auditor, Admin).
 * In a production architecture, credentials should be managed via secure HttpOnly,
 * SameSite cookies and OAuth2/OIDC session tokens to prevent XSS credential extraction.
 */
import React, { createContext, useContext, useState } from 'react';

const AuthContext = createContext(null);

export const ROLES = {
  FARMER: {
    id: 'farmer',
    name: 'Field Farmer',
    badge: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/80 dark:text-emerald-300 border-emerald-300 dark:border-emerald-800',
    description: 'Standard crop assessment, verification record viewing, and field scouting.',
    permissions: ['scan', 'view_reports', 'print_reports', 'print_certificates'],
  },
  AGRONOMIST: {
    id: 'agronomist',
    name: 'Field Agronomist',
    badge: 'bg-blue-100 text-blue-800 dark:bg-blue-950/80 dark:text-blue-300 border-blue-300 dark:border-blue-800',
    description: 'Expert diagnostic access, severity threshold calibration, treatment planning, and report review.',
    permissions: ['scan', 'view_reports', 'verify_blockchain', 'calibrate_severity', 'export_protocols', 'review_reports', 'print_reports', 'print_certificates'],
  },
  AUDITOR: {
    id: 'auditor',
    name: 'Supply Chain Auditor',
    badge: 'bg-purple-100 text-purple-800 dark:bg-purple-950/80 dark:text-purple-300 border-purple-300 dark:border-purple-800',
    description: 'Tamper-evident evidence chain verification, hash integrity auditing, and report export.',
    permissions: ['view_reports', 'verify_blockchain', 'audit_hashes', 'export_raw_json'],
  },
  ADMIN: {
    id: 'admin',
    name: 'Enterprise Admin',
    badge: 'bg-amber-100 text-amber-800 dark:bg-amber-950/80 dark:text-amber-300 border-amber-300 dark:border-amber-800',
    description: 'Full administrative access, API key injection, and backend endpoint configuration.',
    permissions: ['all'],
  },
};

const STORAGE_KEYS = {
  ROLE: 'harvest_harbor_user_role',
  API_KEY: 'harvest_harbor_api_key',
  INSPECTOR_ID: 'harvest_harbor_inspector_id',
  INSPECTOR_NAME: 'harvest_harbor_inspector_name',
  AUTH_HEADER_TYPE: 'harvest_harbor_auth_header_type', // 'bearer' or 'apikey'
};

const isProd = Boolean(import.meta.env.PROD);

// Dev keys are read from .env.development environment variables only.
// They are NEVER hardcoded here so they cannot appear in a production bundle.
// Set VITE_DEV_FARMER_KEY etc. in your local .env.development file.
export const DEFAULT_ROLE_KEYS = isProd ? {
  farmer: '',
  agronomist: '',
  auditor: '',
  admin: '',
} : {
  farmer: import.meta.env.VITE_DEV_FARMER_KEY || 'dev-farmer-key',
  agronomist: import.meta.env.VITE_DEV_AGRONOMIST_KEY || 'dev-agronomist-key',
  auditor: import.meta.env.VITE_DEV_AUDITOR_KEY || 'dev-auditor-key',
  admin: import.meta.env.VITE_DEV_ADMIN_KEY || 'dev-admin-key',
};

export function AuthProvider({ children }) {
  const [role, setRoleState] = useState(() => {
    const saved = sessionStorage.getItem(STORAGE_KEYS.ROLE);
    return ROLES[saved?.toUpperCase()] ? saved : 'agronomist';
  });

  const [apiKey, setApiKeyState] = useState(() => {
    const saved = sessionStorage.getItem(STORAGE_KEYS.API_KEY);
    const savedRole = sessionStorage.getItem(STORAGE_KEYS.ROLE) || 'agronomist';
    const fallback = DEFAULT_ROLE_KEYS[savedRole.toLowerCase()] || (!isProd ? 'dev-agronomist-key' : '');
    return (saved && saved.trim()) ? saved.trim() : fallback;
  });

  const [authHeaderType, setAuthHeaderTypeState] = useState(() => {
    return sessionStorage.getItem(STORAGE_KEYS.AUTH_HEADER_TYPE) || 'bearer';
  });

  const [inspectorId, setInspectorIdState] = useState(() => {
    return sessionStorage.getItem(STORAGE_KEYS.INSPECTOR_ID) || 'AGRO-7402';
  });

  const [inspectorName, setInspectorNameState] = useState(() => {
    return sessionStorage.getItem(STORAGE_KEYS.INSPECTOR_NAME) || 'Dr. Elena Rostova';
  });

  const currentRole = ROLES[role.toUpperCase()] || ROLES.AGRONOMIST;

  const setRole = (newRoleId) => {
    if (ROLES[newRoleId.toUpperCase()]) {
      const lowerNew = newRoleId.toLowerCase();
      setRoleState(newRoleId);
      sessionStorage.setItem(STORAGE_KEYS.ROLE, newRoleId);

      const storedKey = sessionStorage.getItem(STORAGE_KEYS.API_KEY);
      const isDefaultDevKey = !storedKey || Object.values(DEFAULT_ROLE_KEYS).includes(storedKey) || storedKey.startsWith('dev-');
      if (isDefaultDevKey) {
        const nextKey = DEFAULT_ROLE_KEYS[lowerNew] || (!isProd ? `dev-${lowerNew}-key` : '');
        setApiKeyState(nextKey);
        if (nextKey) {
          sessionStorage.setItem(STORAGE_KEYS.API_KEY, nextKey);
        } else {
          sessionStorage.removeItem(STORAGE_KEYS.API_KEY);
        }
      }
    }
  };

  const setApiKey = (key) => {
    setApiKeyState(key);
    if (key && key.trim()) {
      sessionStorage.setItem(STORAGE_KEYS.API_KEY, key.trim());
    } else {
      sessionStorage.removeItem(STORAGE_KEYS.API_KEY);
    }
  };

  const setAuthHeaderType = (type) => {
    setAuthHeaderTypeState(type);
    sessionStorage.setItem(STORAGE_KEYS.AUTH_HEADER_TYPE, type);
  };

  const setInspectorInfo = (id, name) => {
    setInspectorIdState(id);
    setInspectorNameState(name);
    sessionStorage.setItem(STORAGE_KEYS.INSPECTOR_ID, id);
    sessionStorage.setItem(STORAGE_KEYS.INSPECTOR_NAME, name);
  };

  const hasPermission = (permission) => {
    if (currentRole.permissions.includes('all')) return true;
    return currentRole.permissions.includes(permission);
  };

  const getAuthHeaders = () => {
    const headers = {};
    const effectiveKey = (apiKey && apiKey.trim())
      ? apiKey.trim()
      : (DEFAULT_ROLE_KEYS[role.toLowerCase()] || (!isProd ? `dev-${role.toLowerCase()}-key` : ''));

    if (effectiveKey) {
      if (authHeaderType === 'bearer') {
        headers['Authorization'] = `Bearer ${effectiveKey}`;
      } else {
        headers['X-API-Key'] = effectiveKey;
      }
    }
    headers['X-Inspector-ID'] = inspectorId;
    headers['X-User-Role'] = role;
    return headers;
  };

  const value = {
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
    hasPermission,
    getAuthHeaders,
    availableRoles: Object.values(ROLES),
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
