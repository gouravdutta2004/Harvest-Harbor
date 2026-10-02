import React, { useState, useRef, useEffect } from 'react';
import {
  UploadCloud,
  Camera,
  X,
  AlertCircle,
  ScanLine,
  FileCheck,
  Sparkles,
  CheckCircle2,
  Info,
  Maximize2,
  Zap,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import AuthenticatedImage from './AuthenticatedImage';
import { PhotoTipsModal } from './PhotoTipsModal';

export const REAL_WORLD_SAMPLES = [
  {
    id: 'apple_healthy',
    name: 'Apple Healthy',
    badge: 'Healthy Leaf',
    crop: 'Pome Fruit (Malus)',
    status: 'healthy',
    path: '/samples/sample_leaf.jpg',
    filename: 'sample_apple_healthy.jpg',
    description: 'High-confidence healthy screening with disease suppression & assessment summary',
    theme: {
      bg: 'bg-emerald-50 dark:bg-emerald-950/40 hover:bg-emerald-100 dark:hover:bg-emerald-900/60',
      border: 'border-emerald-200 dark:border-emerald-800/80',
      text: 'text-emerald-800 dark:text-emerald-300',
      dot: 'text-emerald-600',
    },
  },
  {
    id: 'potato_blight',
    name: 'Potato Early Blight',
    badge: 'Foliar Blight',
    crop: 'Solanaceous (Solanum)',
    status: 'diseased',
    path: '/samples/diseased_leaf.jpg',
    filename: 'sample_potato_early_blight.jpg',
    description: 'Alternaria solani target lesions with U-Net lesion mask and Grad-CAM focus',
    theme: {
      bg: 'bg-rose-50 dark:bg-rose-950/40 hover:bg-rose-100 dark:hover:bg-rose-900/60',
      border: 'border-rose-200 dark:border-rose-800/80',
      text: 'text-rose-800 dark:text-rose-300',
      dot: 'text-rose-600',
    },
  },
  {
    id: 'corn_spot',
    name: 'Corn Gray Spot',
    badge: 'Cereal Spot',
    crop: 'Gramineae (Zea mays)',
    status: 'diseased',
    path: '/samples/corn_gray_leaf_spot.jpg',
    filename: 'sample_corn_gray_leaf_spot.jpg',
    description: 'Cercospora zeae-maydis on cereal maize with calibrated severity estimation',
    theme: {
      bg: 'bg-amber-50 dark:bg-amber-950/40 hover:bg-amber-100 dark:hover:bg-amber-900/60',
      border: 'border-amber-200 dark:border-amber-800/80',
      text: 'text-amber-800 dark:text-amber-300',
      dot: 'text-amber-600',
    },
  },
  {
    id: 'apple_rot',
    name: 'Apple Black Rot',
    badge: 'Necrotic Rot',
    crop: 'Pome Fruit (Malus)',
    status: 'diseased',
    path: '/samples/apple_black_rot.jpg',
    filename: 'sample_apple_black_rot.jpg',
    description: 'Botryosphaeria obtusa necrotic rot with actionable agronomic treatment plan',
    theme: {
      bg: 'bg-purple-50 dark:bg-purple-950/40 hover:bg-purple-100 dark:hover:bg-purple-900/60',
      border: 'border-purple-200 dark:border-purple-800/80',
      text: 'text-purple-800 dark:text-purple-300',
      dot: 'text-purple-600',
    },
  },
];

export function UploadDropzone({
  onFileSelected,
  selectedFile,
  previewUrl,
  onAnalyze,
  onQuickAnalyze,
  isAnalyzing,
  onReset,
  autoLoadSampleId = null,
}) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [fileError, setFileError] = useState(null);
  const [imageMeta, setImageMeta] = useState(null);
  const [showTips, setShowTips] = useState(true);
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

  // Support 1-click loading from dashboard links
  useEffect(() => {
    if (!autoLoadSampleId || isAnalyzing) return;
    const match = REAL_WORLD_SAMPLES.find(
      (s) => s.id === autoLoadSampleId || s.filename.includes(autoLoadSampleId)
    );
    if (match) {
      handleLoadSample(match.path, match.filename, true);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoLoadSampleId]);

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

  const handleLoadSample = async (samplePath, filename, autoAnalyze = false) => {
    try {
      setFileError(null);
      const res = await fetch(samplePath);
      if (!res.ok) throw new Error(`Could not load ${filename}`);
      const blob = await res.blob();
      const file = new File([blob], filename, { type: 'image/jpeg' });
      onFileSelected(file);
      if (autoAnalyze) {
        if (onQuickAnalyze) {
          onQuickAnalyze(file);
        } else if (onAnalyze) {
          setTimeout(() => onAnalyze(file), 50);
        }
      }
    } catch (err) {
      setFileError(`Failed to load sample leaf: ${err.message}`);
    }
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

          {/* Tips for Better Results Checklist */}
          <div className="rounded-2xl border border-emerald-200/70 dark:border-emerald-900/60 bg-emerald-50/50 dark:bg-emerald-950/20 overflow-hidden transition-all">
            <button
              type="button"
              onClick={() => setShowTips(!showTips)}
              className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-emerald-100/40 dark:hover:bg-emerald-900/30 transition-colors"
            >
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
                <span className="text-xs font-bold text-emerald-900 dark:text-emerald-200">
                  Tips for Better Results
                </span>
                <span className="text-[11px] text-emerald-700/80 dark:text-emerald-400/80">
                  (5 essential field practices)
                </span>
              </div>
              <div className="text-emerald-700 dark:text-emerald-400">
                {showTips ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              </div>
            </button>

            {showTips && (
              <div className="px-4 pb-4 pt-1 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5 text-xs text-gray-700 dark:text-gray-300 border-t border-emerald-100/80 dark:border-emerald-900/40">
                <div className="flex items-start gap-2 p-2 rounded-xl bg-white/70 dark:bg-darkCard/70 border border-emerald-100 dark:border-emerald-950">
                  <span className="text-emerald-600 dark:text-emerald-400 font-bold shrink-0">✓</span>
                  <div>
                    <span className="font-semibold text-gray-900 dark:text-white block">Clear lighting</span>
                    <span className="text-[11px] text-gray-500 dark:text-gray-400">Diffused daylight; avoid harsh shadows or direct flash reflection.</span>
                  </div>
                </div>

                <div className="flex items-start gap-2 p-2 rounded-xl bg-white/70 dark:bg-darkCard/70 border border-emerald-100 dark:border-emerald-950">
                  <span className="text-emerald-600 dark:text-emerald-400 font-bold shrink-0">✓</span>
                  <div>
                    <span className="font-semibold text-gray-900 dark:text-white block">Avoid blur</span>
                    <span className="text-[11px] text-gray-500 dark:text-gray-400">Hold steady; tap to focus on foliar lesions and vein patterns.</span>
                  </div>
                </div>

                <div className="flex items-start gap-2 p-2 rounded-xl bg-white/70 dark:bg-darkCard/70 border border-emerald-100 dark:border-emerald-950">
                  <span className="text-emerald-600 dark:text-emerald-400 font-bold shrink-0">✓</span>
                  <div>
                    <span className="font-semibold text-gray-900 dark:text-white block">Fill most of the frame</span>
                    <span className="text-[11px] text-gray-500 dark:text-gray-400">Maximize leaf area (at least 60-70% of frame) for neural input resolution.</span>
                  </div>
                </div>

                <div className="flex items-start gap-2 p-2 rounded-xl bg-white/70 dark:bg-darkCard/70 border border-emerald-100 dark:border-emerald-950">
                  <span className="text-emerald-600 dark:text-emerald-400 font-bold shrink-0">✓</span>
                  <div>
                    <span className="font-semibold text-gray-900 dark:text-white block">Keep the leaf centered</span>
                    <span className="text-[11px] text-gray-500 dark:text-gray-400">Position suspected pathology near center for Grad-CAM activation.</span>
                  </div>
                </div>

                <div className="flex items-start gap-2 p-2 rounded-xl bg-white/70 dark:bg-darkCard/70 border border-emerald-100 dark:border-emerald-950 sm:col-span-2 lg:col-span-2">
                  <span className="text-emerald-600 dark:text-emerald-400 font-bold shrink-0">✓</span>
                  <div>
                    <span className="font-semibold text-gray-900 dark:text-white block">Plain background works best</span>
                    <span className="text-[11px] text-gray-500 dark:text-gray-400">Neutral background (soil, paper, or hand away from blade) prevents soil/weed false features.</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* 4 Real-World Diagnostic Test Samples */}
          <div className="p-4 sm:p-5 rounded-3xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder shadow-subtle space-y-3.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-gray-800 dark:text-gray-200">
                <Sparkles className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                <span>Real-World Field Test Suite</span>
              </div>
              <span className="text-[10px] text-gray-400 font-mono">1-Click Test</span>
            </div>
            <p className="text-[11px] text-gray-500 dark:text-gray-400 leading-relaxed">
              Select a field-verified sample to inspect leaf pre-flight checks, or click <strong>Test</strong> to run the full diagnostic pipeline instantly.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {REAL_WORLD_SAMPLES.map((sample) => (
                <div
                  key={sample.filename}
                  onClick={() => handleLoadSample(sample.path, sample.filename, false)}
                  className={`p-3 rounded-2xl border text-left transition-all text-xs group cursor-pointer flex flex-col justify-between space-y-2 ${sample.theme.bg} ${sample.theme.border}`}
                >
                  <div>
                    <div className={`font-bold flex items-center justify-between ${sample.theme.text}`}>
                      <span className="truncate">{sample.name}</span>
                      <span className={`text-[10px] font-black ${sample.theme.dot}`}>
                        {sample.status === 'healthy' ? '✓' : '⚠'}
                      </span>
                    </div>
                    <div className="text-[10px] text-gray-500 dark:text-gray-400 flex items-center justify-between mt-0.5">
                      <span className="font-medium">{sample.badge}</span>
                      <span className="opacity-75 text-[9px]">{sample.crop}</span>
                    </div>
                    <p className="text-[10px] text-gray-600 dark:text-gray-400 mt-1 line-clamp-2 leading-tight">
                      {sample.description}
                    </p>
                  </div>

                  <div className="pt-1 flex items-center justify-between gap-2 border-t border-gray-200/50 dark:border-darkBorder/50">
                    <span className="text-[10px] text-gray-400 group-hover:text-gray-600 dark:group-hover:text-gray-300 transition-colors">
                      Click to stage
                    </span>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleLoadSample(sample.path, sample.filename, true);
                      }}
                      className="px-2.5 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-[10px] flex items-center gap-1 shadow-subtle transition-all transform active:scale-95"
                      title={`Run instant assessment on ${sample.name}`}
                    >
                      <Zap className="w-3 h-3 text-amber-300 fill-amber-300" />
                      <span>Test</span>
                    </button>
                  </div>
                </div>
              ))}
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

          {/* Quick switcher to other samples while staged */}
          {!isAnalyzing && (
            <div className="pt-2 border-t border-gray-100 dark:border-darkBorder space-y-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-gray-400 block">
                Quick switch sample:
              </span>
              <div className="flex flex-wrap gap-1.5">
                {REAL_WORLD_SAMPLES.map((sample) => (
                  <button
                    key={sample.filename}
                    type="button"
                    onClick={() => handleLoadSample(sample.path, sample.filename, false)}
                    className="px-2 py-1 rounded-lg bg-gray-100 dark:bg-darkElevated hover:bg-emerald-50 dark:hover:bg-emerald-950/40 text-[10px] font-medium text-gray-700 dark:text-gray-300 transition-colors border border-gray-200/60 dark:border-darkBorder truncate max-w-[140px]"
                    title={`Switch to ${sample.name}`}
                  >
                    {sample.name}
                  </button>
                ))}
              </div>
            </div>
          )}

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
