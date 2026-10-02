/**
 * Harvest Harbor Centralized API Service
 * Connects to the existing FastAPI backend with rich error handling and RBAC support.
 */

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

/**
 * Resolves static asset paths (e.g. /generated/gradcam/... or /uploads/...) into full URLs.
 * Handles null, undefined, absolute URLs, relative URLs, and filesystem paths gracefully.
 */
export function resolveAssetUrl(path) {
  if (!path) return null;
  if (typeof path !== 'string') return null;
  if (path.startsWith('http://') || path.startsWith('https://') || path.startsWith('blob:') || path.startsWith('data:')) {
    return path;
  }

  let normalized = path.replace(/\\/g, '/');

  const genIdx = normalized.indexOf('/generated/');
  if (genIdx !== -1) {
    normalized = normalized.slice(genIdx);
  } else {
    const uplIdx = normalized.indexOf('/uploads/');
    if (uplIdx !== -1) {
      normalized = normalized.slice(uplIdx);
    }
  }

  const cleanBase = API_BASE_URL.replace(/\/+$/, '');
  const cleanPath = normalized.startsWith('/') ? normalized : `/${normalized}`;
  return `${cleanBase}${cleanPath}`;
}

/**
 * Fetches static assets (e.g. /uploads/... or /generated/...) using authenticated HTTP fetch
 * and converts the response stream to a Blob object URL.
 */
export async function fetchAuthenticatedAssetUrl(path) {
  if (!path) return null;
  if (typeof path === 'string' && (path.startsWith('blob:') || path.startsWith('data:'))) {
    return path;
  }
  const resolved = resolveAssetUrl(path);
  if (!resolved) return null;

  try {
    const res = await fetchWithTimeout(resolved, { timeout: 15000 });
    if (!res.ok) return null;
    const blob = await res.blob();
    return URL.createObjectURL(blob);
  } catch (err) {
    console.error('Failed to fetch authenticated asset:', err);
    return null;
  }
}

const isProd = import.meta.env?.MODE === 'production' || Boolean(import.meta.env?.PROD);

// Dev keys are read from .env.development env variables only — never hardcoded in production.
export const DEFAULT_DEV_KEYS = isProd ? {
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

/**
 * Helper to retrieve stored security credentials for API requests.
 */
export function getStoredAuthHeaders() {
  const headers = {};
  const role = (sessionStorage.getItem('harvest_harbor_user_role') || 'agronomist').toLowerCase();
  const storedKey = sessionStorage.getItem('harvest_harbor_api_key');
  const authType = sessionStorage.getItem('harvest_harbor_auth_header_type') || 'bearer';
  const inspectorId = sessionStorage.getItem('harvest_harbor_inspector_id') || 'AGRO-7402';

  const defaultKey = DEFAULT_DEV_KEYS[role] || DEFAULT_DEV_KEYS['agronomist'] || (!isProd ? `dev-${role}-key` : '');
  const effectiveKey = (storedKey && storedKey.trim()) ? storedKey.trim() : defaultKey;

  if (effectiveKey) {
    if (authType === 'bearer') {
      headers['Authorization'] = `Bearer ${effectiveKey}`;
    } else {
      headers['X-API-Key'] = effectiveKey;
    }
  }
  headers['X-Inspector-ID'] = inspectorId;
  headers['X-User-Role'] = role;
  return headers;
}

/**
 * Formats specific error messages according to HTTP status code (Fix #9).
 */
function parseHttpError(res, data) {
  const detail = data?.detail || data?.error;
  if (detail && typeof detail === 'string') return detail;

  switch (res.status) {
    case 401:
      return '401 Unauthorized: Authentication required. Please check your API key or Bearer token.';
    case 403:
      return '403 Forbidden: Permission denied for the active role persona.';
    case 404:
      return '404 Not Found: The requested report ID or resource was not found.';
    case 422:
      return '422 Unprocessable Entity: Invalid image file, unsupported format, or invalid request arguments.';
    case 500:
      return '500 Internal Server Error: An unexpected error occurred on the backend during model execution.';
    case 503:
      return '503 Service Unavailable: One or more required AI neural network models are currently unavailable.';
    default:
      return `Request failed with HTTP status ${res.status}`;
  }
}

/**
 * Standard fetch wrapper with timeout, security headers, and JSON parsing.
 */
async function fetchWithTimeout(resource, options = {}) {
  const { timeout = 30000, headers = {}, retries = 2, ...fetchOptions } = options;
  const requestMethod = String(fetchOptions.method || 'GET').toUpperCase();
  const retryCount = ['GET', 'HEAD', 'OPTIONS'].includes(requestMethod) ? retries : 0;
  let delay = 500;

  for (let attempt = 0; attempt <= retryCount; attempt += 1) {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeout);

    const authHeaders = getStoredAuthHeaders();
    const combinedHeaders = { ...authHeaders, ...headers };

    try {
      const response = await fetch(resource, {
        ...fetchOptions,
        headers: combinedHeaders,
        signal: controller.signal,
      });
      clearTimeout(id);

      if (response.status >= 500 && attempt < retryCount) {
        await new Promise((resolve) => setTimeout(resolve, delay));
        delay *= 2;
        continue;
      }
      return response;
    } catch (error) {
      clearTimeout(id);
      if (attempt >= retryCount) {
        if (error.name === 'AbortError') {
          throw new Error('Request Timeout: Backend did not respond within the allocated timeframe.');
        }
        throw error;
      }
      await new Promise((resolve) => setTimeout(resolve, delay));
      delay *= 2;
    }
  }

  throw new Error('Request failed after retries.');
}

/**
 * Check backend operational status, ping latency, and loaded models.
 * GET /health
 */
export async function checkHealth() {
  const startTime = performance.now();
  try {
    const res = await fetchWithTimeout(`${API_BASE_URL}/health`, { timeout: 5000 });
    const latencyMs = Math.round(performance.now() - startTime);
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(parseHttpError(res, data));
    }
    const data = await res.json();
    return {
      ...data,
      latencyMs,
      timestamp: new Date().toISOString(),
    };
  } catch (err) {
    return {
      status: 'offline',
      latencyMs: null,
      error: err.message || 'Cannot reach FastAPI backend at ' + API_BASE_URL,
    };
  }
}

/**
 * Get root system version and state.
 * GET /
 */
export async function getRootStatus() {
  try {
    const res = await fetchWithTimeout(`${API_BASE_URL}/`, { timeout: 5000 });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(parseHttpError(res, data));
    }
    return await res.json();
  } catch (err) {
    return null;
  }
}

/**
 * Perform comprehensive crop analysis.
 * POST /predict
 * @param {File} file - Image file (JPG, PNG, WEBP)
 */
export async function predictCrop(file) {
  if (!file) {
    throw new Error('Please select a leaf image file to analyze.');
  }

  const formData = new FormData();
  formData.append('file', file);

  try {
    const res = await fetchWithTimeout(`${API_BASE_URL}/predict`, {
      method: 'POST',
      body: formData,
      timeout: 60000,
    });

    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      throw new Error(parseHttpError(res, data));
    }

    return data;
  } catch (err) {
    if (err.message.includes('Failed to fetch') || err.message.includes('NetworkError')) {
      throw new Error('Unable to connect to the AI backend. Please verify FastAPI is running at ' + API_BASE_URL);
    }
    throw err;
  }
}

/**
 * Get summary information about the evidence chain.
 * GET /traceability/status
 */
export async function getTraceabilityStatus() {
  try {
    const res = await fetchWithTimeout(`${API_BASE_URL}/traceability/status`, { timeout: 6000 });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(parseHttpError(res, data));
    }
    return data;
  } catch (err) {
    return {
      chain_valid: false,
      error: err.message || 'Failed to fetch traceability status',
    };
  }
}

/**
 * Run cryptographic verification on the entire evidence chain.
 * GET /traceability/verify
 */
export async function verifyTraceabilityChain() {
  try {
    const res = await fetchWithTimeout(`${API_BASE_URL}/traceability/verify`, { timeout: 10000 });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(parseHttpError(res, data));
    }
    return data;
  } catch (err) {
    return {
      valid: false,
      message: err.message || 'Verification request failed',
    };
  }
}

/**
 * Fetch all records in the evidence chain.
 * GET /traceability/chain
 */
export async function getTraceabilityChain() {
  try {
    const res = await fetchWithTimeout(`${API_BASE_URL}/traceability/chain`, { timeout: 10000 });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(parseHttpError(res, data));
    }
    return data;
  } catch (err) {
    return {
      success: false,
      chain: [],
      error: err.message,
    };
  }
}

/**
 * Retrieve a specific report block by its Report ID.
 * GET /traceability/report/{report_id}
 * @param {string} reportId
 */
export async function getTraceabilityReport(reportId) {
  if (!reportId || !reportId.trim()) {
    throw new Error('Report ID is required.');
  }

  const cleanId = reportId.trim();
  try {
    const res = await fetchWithTimeout(`${API_BASE_URL}/traceability/report/${encodeURIComponent(cleanId)}`, {
      timeout: 10000,
    });

    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      throw new Error(parseHttpError(res, data));
    }

    return data;
  } catch (err) {
    if (err.message.includes('Failed to fetch')) {
      throw new Error('Unable to connect to the backend server.');
    }
    throw err;
  }
}

export async function getReviewQueue(status = 'pending') {
  const query = status ? `?status=${encodeURIComponent(status)}` : '';
  const res = await fetchWithTimeout(`${API_BASE_URL}/review-queue${query}`, { timeout: 10000 });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(parseHttpError(res, data));
  return data;
}

export async function getReviewItem(reviewId) {
  const res = await fetchWithTimeout(`${API_BASE_URL}/review-queue/${encodeURIComponent(reviewId)}`, { timeout: 10000 });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(parseHttpError(res, data));
  return data;
}

export async function resolveReviewItem(reviewId, decision, notes = '') {
  const res = await fetchWithTimeout(`${API_BASE_URL}/review-queue/${encodeURIComponent(reviewId)}/resolve`, {
    method: 'POST',
    timeout: 10000,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ decision, notes }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(parseHttpError(res, data));
  return data;
}

export async function submitForReview(reportId, notes = '') {
  const res = await fetchWithTimeout(`${API_BASE_URL}/review-queue/submit`, {
    method: 'POST',
    timeout: 10000,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ report_id: reportId, notes, reasons: ['user_requested_review'] }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(parseHttpError(res, data));
  return data;
}

