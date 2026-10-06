import React, { useState, useRef, useEffect } from 'react';
import {
  UploadCloud,
  Camera,
  X,
  AlertCircle,
  ScanLine,
  FileCheck,
  CheckCircle2,
  Sparkles,
} from 'lucide-react';
import AuthenticatedImage from './AuthenticatedImage';
import { PhotoTipsModal } from './PhotoTipsModal';

export function UploadDropzone({
  onFileSelected,
  selectedFile,
  previewUrl,
  onAnalyze,
  isAnalyzing,
  onReset,
}) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [fileError, setFileError] = useState(null);
  const [imageMeta, setImageMeta] = useState(null);
  const [photoTipsOpen, setPhotoTipsOpen] = useState(false);
  const fileInputRef = useRef(null);
  const cameraInputRef = useRef(null);

  const allowedExtensions = ['.jpg', '.jpeg', '.png', '.webp'];
  const maxSizeBytes = 15 * 1024 * 1024; // 15 MB

  // Extract client-side image metadata for pre-flight AI validation
  useEffect(() => {
    if (previewUrl) {
      const img = new Image();
      img.onload = () => {
        const w = img.naturalWidth;
        const h = img.naturalHeight;
        const totalPixels = w * h;
        if (totalPixels > 50000000) {
          setFileError(`Image resolution (${w}×${h}, ${(totalPixels / 1000000).toFixed(1)} MP) exceeds the 50 MP safety limit.`);
          return;
        }
        setImageMeta({
          width: w,
          height: h,
          aspectRatio: (w / h).toFixed(2),
          megapixels: (totalPixels / 1000000).toFixed(2),
          isOptimal: w >= 224 && h >= 224,
        });
      };
      img.onerror = () => {
        setImageMeta(null);
      };
      img.src = previewUrl;
    } else {
      setImageMeta(null);
    }
  }, [previewUrl]);

  const validateAndSelect = (file) => {
    setFileError(null);
    if (!file) return;

    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!allowedExtensions.includes(ext)) {
      setFileError('Invalid file type. Please upload a JPG, JPEG, PNG, or WEBP image.');
      return;
    }

    if (file.size > maxSizeBytes) {
      setFileError('File exceeds 15 MB limit. Please select a smaller leaf image.');
      return;
    }

    onFileSelected(file);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (isAnalyzing) return;

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndSelect(e.dataTransfer.files[0]);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    if (!isAnalyzing) {
      setIsDragOver(true);
    }
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleFileInputChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndSelect(e.target.files[0]);
    }
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="w-full space-y-4">
      {/* Upload Zone */}
      {!previewUrl ? (
        <>
          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onClick={() => fileInputRef.current?.click()}
            className={`relative border-2 border-dashed rounded-3xl p-8 sm:p-10 text-center cursor-pointer transition-all ${
              isDragOver
                ? 'border-emerald-500 bg-emerald-50/60 dark:bg-emerald-950/30 scale-[1.01]'
                : 'border-gray-300 dark:border-darkBorder hover:border-emerald-400 dark:hover:border-emerald-600/70 bg-white dark:bg-darkCard hover:bg-emerald-50/30 dark:hover:bg-darkElevated'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp,image/jpg"
              className="hidden"
              onChange={handleFileInputChange}
              aria-label="Upload leaf image"
            />

            <input
              ref={cameraInputRef}
              type="file"
              accept="image/*"
              capture="environment"
              className="hidden"
              onChange={handleFileInputChange}
              aria-label="Capture leaf image via camera"
            />

            <div className="flex flex-col items-center justify-center space-y-3.5">
              <div className="w-14 h-14 rounded-2xl bg-emerald-100 dark:bg-emerald-950/70 text-emerald-600 dark:text-emerald-400 flex items-center justify-center shadow-subtle">
                <UploadCloud className="w-7 h-7" />
              </div>

              <div className="space-y-1">
                <h3 className="text-base font-bold text-gray-900 dark:text-white">
                  Drop Leaf Image Here
                </h3>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Drag &amp; drop leaf photo, or{' '}
                  <span className="text-emerald-600 dark:text-emerald-400 font-semibold underline underline-offset-2">
                    browse files
                  </span>
                </p>
              </div>

              <div className="flex items-center gap-2 pt-1">
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    cameraInputRef.current?.click();
                  }}
                  className="px-3 py-1.5 rounded-xl bg-gray-100 hover:bg-gray-200 dark:bg-darkElevated dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300 text-xs font-semibold flex items-center gap-1.5 transition-colors"
                >
                  <Camera className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                  <span>Take Field Photo</span>
                </button>

                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setPhotoTipsOpen(true);
                  }}
                  className="px-3 py-1.5 rounded-xl bg-emerald-50 hover:bg-emerald-100 dark:bg-emerald-950/40 dark:hover:bg-emerald-900/60 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800/80 text-xs font-semibold flex items-center gap-1.5 transition-colors"
                  title="View photography tips for best AI accuracy"
                >
                  <Sparkles className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                  <span>Photo Tips</span>
                </button>
              </div>

              <div className="flex flex-wrap items-center justify-center gap-1.5 pt-1 text-[11px] text-gray-400 dark:text-gray-500 font-mono">
                <span className="px-2 py-0.5 rounded bg-gray-100 dark:bg-darkElevated">JPG</span>
                <span className="px-2 py-0.5 rounded bg-gray-100 dark:bg-darkElevated">PNG</span>
                <span className="px-2 py-0.5 rounded bg-gray-100 dark:bg-darkElevated">WEBP</span>
                <span className="font-sans">• Max 15 MB</span>
              </div>
            </div>
          </div>
        </>
      ) : (
        /* Preview Card */
        <div className="rounded-3xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder p-5 sm:p-6 shadow-subtle space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FileCheck className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
              <span className="text-xs font-bold uppercase tracking-wider text-gray-900 dark:text-white">
                Image Staged for AI Inference
              </span>
            </div>
            {!isAnalyzing && (
              <button
                onClick={onReset}
                type="button"
                className="p-1.5 rounded-lg text-gray-400 hover:text-rose-500 hover:bg-gray-100 dark:hover:bg-darkElevated transition-colors"
                title="Remove image"
                aria-label="Remove image"
              >
                <X className="w-5 h-5" />
              </button>
            )}
          </div>

          <div className="relative rounded-2xl overflow-hidden bg-gray-100 dark:bg-darkElevated border border-gray-200 dark:border-darkBorder aspect-[4/3] flex items-center justify-center">
            <AuthenticatedImage
              src={previewUrl}
              alt="Leaf sample preview"
              className="w-full h-full object-contain"
            />
          </div>

          {/* Pre-flight Image Quality Check */}
          {imageMeta && (
            <div className="p-3 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder text-xs space-y-1.5">
              <div className="flex items-center justify-between font-mono text-[11px] text-gray-600 dark:text-gray-400">
                <span>
                  {imageMeta.width} × {imageMeta.height} px ({imageMeta.megapixels} MP)
                </span>
                <span>{selectedFile ? formatFileSize(selectedFile.size) : ''}</span>
              </div>
              <div className="flex items-center gap-1.5 text-[11px]">
                {imageMeta.isOptimal ? (
                  <>
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400 flex-shrink-0" />
                    <span className="text-emerald-700 dark:text-emerald-300 font-medium">
                      Optimal resolution for EfficientNet-B0 &amp; U-Net
                    </span>
                  </>
                ) : (
                  <>
                    <AlertCircle className="w-3.5 h-3.5 text-amber-500 flex-shrink-0" />
                    <span className="text-amber-700 dark:text-amber-300 font-medium">
                      Resolution below 224px. Upscaling will be applied.
                    </span>
                  </>
                )}
              </div>
            </div>
          )}

          <div className="pt-1 flex gap-3">
            <button
              onClick={() => onAnalyze()}
              disabled={isAnalyzing}
              type="button"
              className="flex-1 py-3 px-6 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:bg-gray-300 dark:disabled:bg-gray-800 disabled:cursor-not-allowed text-white text-sm font-bold shadow-glow-emerald flex items-center justify-center gap-2 transition-all transform active:scale-[0.98]"
            >
              <ScanLine className="w-4 h-4" />
              {isAnalyzing ? 'Analyzing Image...' : 'Analyze Crop'}
            </button>

            {!isAnalyzing && (
              <button
                onClick={() => fileInputRef.current?.click()}
                type="button"
                className="py-3 px-4 rounded-xl border border-gray-200 dark:border-darkBorder bg-gray-50 dark:bg-darkElevated text-gray-700 dark:text-gray-200 text-sm font-medium hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              >
                Change
              </button>
            )}
          </div>

          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/png,image/webp,image/jpg"
            className="hidden"
            onChange={handleFileInputChange}
          />
        </div>
      )}

      {/* Error Banner */}
      {fileError && (
        <div className="p-3.5 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-rose-700 dark:text-rose-300 text-xs flex items-center gap-2.5">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{fileError}</span>
        </div>
      )}

      {/* Photography Tips & Camera Guide Modal */}
      <PhotoTipsModal
        isOpen={photoTipsOpen}
        onClose={() => setPhotoTipsOpen(false)}
      />
    </div>
  );
}
export default UploadDropzone;
