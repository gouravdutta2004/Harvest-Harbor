import React, { useState, useEffect } from 'react';
import { useAuthenticatedImage } from '../hooks/useAuthenticatedImage';

/**
 * Reusable image component that performs authenticated fetch -> Blob -> object URL.
 */
export function AuthenticatedImage({ src, alt, className = '', style, onClick, title, placeholderText = 'Loading asset...', ...props }) {
  const { src: objectUrl, loading, error } = useAuthenticatedImage(src);
  const [imgLoadError, setImgLoadError] = useState(false);

  useEffect(() => {
    setImgLoadError(false);
  }, [objectUrl]);

  if (loading) {
    return (
      <div
        className={`flex items-center justify-center bg-gray-900/60 text-gray-400 text-xs animate-pulse min-h-[120px] rounded-xl ${className}`}
        style={style}
      >
        <span className="font-mono text-[11px] opacity-80">{placeholderText}</span>
      </div>
    );
  }

  if (error || imgLoadError || !objectUrl) {
    return (
      <div
        className={`flex flex-col items-center justify-center bg-gray-950/80 text-gray-500 text-xs p-4 text-center min-h-[120px] rounded-xl border border-gray-800 ${className}`}
        style={style}
      >
        <span className="font-mono text-[11px] text-gray-400">Image unavailable</span>
        <span className="text-[10px] text-gray-500 mt-1">Requires valid authentication or resource missing</span>
      </div>
    );
  }

  return (
    <img
      src={objectUrl}
      alt={alt || ''}
      className={className}
      style={style}
      onClick={onClick}
      title={title}
      onError={() => setImgLoadError(true)}
      {...props}
    />
  );
}

export default AuthenticatedImage;
