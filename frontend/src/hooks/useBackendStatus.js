import { useState, useEffect, useCallback } from 'react';
import { checkHealth, getRootStatus } from '../services/api';

/**
 * Hook to monitor live FastAPI backend status.
 * Never fakes status; queries /health directly.
 */
export function useBackendStatus(pollIntervalMs = 20000) {
  const [status, setStatus] = useState('checking'); // 'online' | 'offline' | 'checking'
  const [healthData, setHealthData] = useState(null);
  const [lastChecked, setLastChecked] = useState(null);
  const [error, setError] = useState(null);

  const verifyStatus = useCallback(async () => {
    try {
      const data = await checkHealth();
      if (data && (data.status === 'healthy' || data.status === 'ok' || data.status === 'degraded')) {
        setStatus('online');
        setHealthData(data);
        setError(null);
      } else {
        setStatus('offline');
        setHealthData(null);
        setError(data?.error || 'Backend reported unhealthy state');
      }
    } catch (err) {
      setStatus('offline');
      setHealthData(null);
      setError(err.message || 'Connection refused');
    } finally {
      setLastChecked(new Date());
    }
  }, []);

  useEffect(() => {
    verifyStatus();
    const interval = setInterval(verifyStatus, pollIntervalMs);
    return () => clearInterval(interval);
  }, [verifyStatus, pollIntervalMs]);

  return {
    status,
    isOnline: status === 'online',
    healthData,
    lastChecked,
    error,
    refresh: verifyStatus,
  };
}
