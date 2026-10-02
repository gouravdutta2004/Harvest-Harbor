import { useState, useEffect } from 'react';
import { fetchAuthenticatedAssetUrl } from '../services/api';

/**
 * Custom React Hook for loading authenticated images via fetch -> Blob -> object URL.
 * Automatically revokes object URLs on unmount/path change to prevent memory leaks.
 */
export function useAuthenticatedImage(path) {
  const [objectUrl, setObjectUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!path) {
      setObjectUrl(null);
      setLoading(false);
      setError(false);
      return;
    }

    if (typeof path === 'string' && (path.startsWith('blob:') || path.startsWith('data:'))) {
      setObjectUrl(path);
      setLoading(false);
      setError(false);
      return;
    }

    let isMounted = true;
    setLoading(true);
    setError(false);

    let createdUrl = null;

    fetchAuthenticatedAssetUrl(path)
      .then((url) => {
        if (isMounted) {
          if (url) {
            createdUrl = url;
            setObjectUrl(url);
            setError(false);
          } else {
            setError(true);
          }
          setLoading(false);
        } else if (url && url.startsWith('blob:')) {
          URL.revokeObjectURL(url);
        }
      })
      .catch(() => {
        if (isMounted) {
          setError(true);
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
      if (createdUrl && createdUrl.startsWith('blob:')) {
        URL.revokeObjectURL(createdUrl);
      }
    };
  }, [path]);

  return { src: objectUrl, loading, error };
}

export default useAuthenticatedImage;
