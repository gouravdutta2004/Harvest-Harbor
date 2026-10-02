import React, { useState } from 'react';
import { Target, Maximize2, X, PieChart, Layers, Info, CheckCircle2, AlertTriangle } from 'lucide-react';
import { formatNumber, formatPercent } from '../utils/formatters';
import AuthenticatedImage from './AuthenticatedImage';
import { InfoTooltip } from './InfoTooltip';

export function SegmentationViewer({
  segmentation,
  severity,
  originalImageSrc,
  diseaseValidationStatus,
  className = '',
}) {
  const [activeTab, setActiveTab] = useState('composite'); // 'composite' | 'overlay' | 'disease_mask' | 'leaf_mask' | 'original'
  const [modalImage, setModalImage] = useState(null);

  if (!segmentation || !segmentation.available) {
    return (
      <div className={`p-6 rounded-3xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder shadow-subtle space-y-3 ${className}`}>
        <div className="flex items-center gap-2">
          <Target className="w-4 h-4 text-gray-400" />
          <h3 className="text-sm font-bold uppercase tracking-wider text-gray-900 dark:text-white">
            Estimated Affected Area
          </h3>
        </div>
        <p className="text-xs text-gray-500 dark:text-gray-400">
          {segmentation?.message || 'Segmentation model unavailable for this historical record'}
        </p>
      </div>
    );
  }

  const compositeUrl = segmentation.composite_path;
  const overlayUrl = segmentation.overlay_path;
  const diseaseMaskUrl = segmentation.disease_mask_path;
  const leafMaskUrl = segmentation.leaf_mask_path;
  const originalUrl = originalImageSrc;

  const isFallback =
    segmentation.method === 'hsv_lab_fallback' ||
    segmentation.architecture?.toLowerCase().includes('fallback') ||
    segmentation.fallback === true;

  const architectureLabel = isFallback
    ? 'Image-based segmentation fallback'
    : (segmentation.architecture || 'U-Net PlantSeg');

  const affectedPercent = severity?.affected_area_percent ?? segmentation.affected_percentage ?? (segmentation.affected_ratio ? segmentation.affected_ratio * 100 : 0);
  const leafPixels = segmentation.leaf_pixels;
  const diseasedPixels = segmentation.diseased_pixels;
  const totalPixels = segmentation.total_pixels;

  const qualityLevel = segmentation.confidence?.level || (leafPixels > 1000 ? 'High' : 'Low');

  // Donut SVG circumference math
  const radius = 38;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (Math.min(100, Math.max(0, affectedPercent)) / 100) * circumference;

  const getImageForTab = () => {
    switch (activeTab) {
      case 'overlay':
        return overlayUrl;
      case 'disease_mask':
        return diseaseMaskUrl;
      case 'leaf_mask':
        return leafMaskUrl;
      case 'original':
        return originalUrl;
      case 'composite':
      default:
        return compositeUrl || overlayUrl;
    }
  };

  return (
    <div className={`p-6 sm:p-7 rounded-3xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder shadow-subtle space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Target className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            <h3 className="text-sm font-bold uppercase tracking-wider text-gray-900 dark:text-white">
              Estimated Affected Area
            </h3>
            <InfoTooltip
              title="Understanding Lesion Segmentation"
              content="The segmentation model estimates 2D image regions associated with visible foliar symptoms. This calculation represents the estimated percentage of detected leaf blade area."
            />
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
            The segmentation model estimates regions of the image associated with visible symptoms or lesions.
          </p>
        </div>

        {/* Architecture Badges & Quality Indicator */}
        <div className="flex flex-wrap items-center gap-2 text-[11px] font-mono">
          <span
            className={`px-2.5 py-1 rounded-md border font-semibold ${
              isFallback
                ? 'bg-amber-50 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300 border-amber-200 dark:border-amber-800'
                : 'bg-emerald-50 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800'
            }`}
          >
            {architectureLabel}
          </span>
          <span className="px-2 py-1 rounded-md bg-gray-100 dark:bg-darkElevated text-gray-600 dark:text-gray-300 border border-gray-200 dark:border-darkBorder">
            Quality: <strong>{qualityLevel}</strong>
          </span>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Estimated Affected Area with Donut Indicator */}
        <div className="p-4 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder flex items-center justify-between">
          <div>
            <span className="text-[11px] font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 block">
              Estimated Affected Area
            </span>
            <div className="text-2xl font-mono font-black text-gray-900 dark:text-white mt-0.5">
              {formatPercent(affectedPercent)}
            </div>
            <span className="text-[10px] text-gray-400 dark:text-gray-500">
              Of detected leaf surface
            </span>
          </div>

          {/* SVG Donut */}
          <div className="relative w-16 h-16 flex items-center justify-center">
            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
              <circle
                cx="50"
                cy="50"
                r={radius}
                className="stroke-gray-200 dark:stroke-darkBorder"
                strokeWidth="8"
                fill="transparent"
              />
              <circle
                cx="50"
                cy="50"
                r={radius}
                className="stroke-rose-500 transition-all duration-700"
                strokeWidth="8"
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="round"
                fill="transparent"
              />
            </svg>
            <span className="absolute text-[11px] font-mono font-bold text-gray-800 dark:text-gray-200">
              {Math.round(affectedPercent)}%
            </span>
          </div>
        </div>

        {/* Leaf Pixels */}
        <div className="p-4 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder space-y-1">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 block">
            Estimated Leaf Area
          </span>
          <div className="text-2xl font-mono font-bold text-emerald-700 dark:text-emerald-400">
            {formatNumber(leafPixels)} px
          </div>
          <span className="text-[10px] text-gray-400 dark:text-gray-500 block truncate">
            {totalPixels ? `${formatPercent((leafPixels / totalPixels) * 100, 1)} of frame` : 'Active leaf pixels'}
          </span>
        </div>

        {/* Diseased Pixels */}
        <div className="p-4 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder space-y-1">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 block">
            Estimated Lesion Pixels
          </span>
          <div className="text-2xl font-mono font-bold text-rose-600 dark:text-rose-400">
            {formatNumber(diseasedPixels)} px
          </div>
          <span className="text-[10px] text-gray-400 dark:text-gray-500 block truncate">
            Segmented symptom pixels
          </span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex flex-wrap items-center gap-1.5 p-1 rounded-xl bg-gray-100 dark:bg-darkElevated border border-gray-200/80 dark:border-darkBorder w-fit text-xs font-semibold">
        {compositeUrl && (
          <button
            onClick={() => setActiveTab('composite')}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              activeTab === 'composite'
                ? 'bg-white dark:bg-darkCard text-emerald-800 dark:text-emerald-300 shadow-subtle'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
            }`}
          >
            4-Panel Composite
          </button>
        )}
        <button
          onClick={() => setActiveTab('overlay')}
          className={`px-3 py-1.5 rounded-lg transition-all ${
            activeTab === 'overlay'
              ? 'bg-white dark:bg-darkCard text-emerald-800 dark:text-emerald-300 shadow-subtle'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
          }`}
        >
          Lesion Overlay
        </button>
        <button
          onClick={() => setActiveTab('disease_mask')}
          className={`px-3 py-1.5 rounded-lg transition-all ${
            activeTab === 'disease_mask'
              ? 'bg-white dark:bg-darkCard text-emerald-800 dark:text-emerald-300 shadow-subtle'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
          }`}
        >
          Estimated Lesion Mask
        </button>
        <button
          onClick={() => setActiveTab('leaf_mask')}
          className={`px-3 py-1.5 rounded-lg transition-all ${
            activeTab === 'leaf_mask'
              ? 'bg-white dark:bg-darkCard text-emerald-800 dark:text-emerald-300 shadow-subtle'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
          }`}
        >
          Leaf Mask
        </button>
        {originalUrl && (
          <button
            onClick={() => setActiveTab('original')}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              activeTab === 'original'
                ? 'bg-white dark:bg-darkCard text-emerald-800 dark:text-emerald-300 shadow-subtle'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
            }`}
          >
            Original Image
          </button>
        )}
      </div>

      {/* Main Image View */}
      <div className="relative rounded-2xl overflow-hidden bg-gray-950 border border-gray-200 dark:border-darkBorder group">
        <div className="relative aspect-[4/3] sm:aspect-[16/9] flex items-center justify-center bg-black">
          <AuthenticatedImage
            src={getImageForTab()}
            alt="Estimated segmentation visualization"
            className="max-h-full max-w-full object-contain"
          />

          {/* Expand Modal Trigger */}
          <button
            onClick={() => setModalImage(getImageForTab())}
            className="absolute top-3 right-3 p-2 rounded-xl bg-black/50 hover:bg-black/80 backdrop-blur-md text-white opacity-0 group-hover:opacity-100 transition-opacity"
            title="Expand view"
            aria-label="Expand image view"
          >
            <Maximize2 className="w-4 h-4" />
          </button>

          {/* Badge */}
          <div className="absolute bottom-3 left-3 px-3 py-1.5 rounded-xl bg-black/60 backdrop-blur-md text-white text-xs flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-rose-400" />
            <span>
              {activeTab === 'composite'
                ? `Composite: [Original | Leaf Mask | ${diseaseValidationStatus === 'rejected' ? 'Symptom' : 'Lesion'} Mask | Overlay]`
                : activeTab === 'overlay'
                ? `Estimated Lesion Highlight (Red) on Leaf Outline (Green)`
                : activeTab === 'disease_mask'
                ? `Binary Estimated Lesion Mask`
                : activeTab === 'leaf_mask'
                ? 'Leaf Foreground Estimation Mask'
                : 'Original Image'}
            </span>
          </div>
        </div>
      </div>

      {/* Notice */}
      <div className="p-3.5 rounded-xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder text-xs text-gray-500 dark:text-gray-400 flex items-start gap-2.5">
        <Info className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
        <span>
          U-Net segmentation isolates visible foliar lesions within estimated leaf boundaries. Affected area percentage represents estimated 2D visual surface symptom coverage.
        </span>
      </div>

      {/* Modal */}
      {modalImage && (
        <div
          className="fixed inset-0 z-50 bg-black/90 backdrop-blur-md flex items-center justify-center p-4"
          onClick={() => setModalImage(null)}
        >
          <div className="relative max-w-6xl max-h-[90vh]" onClick={(e) => e.stopPropagation()}>
            <button
              onClick={() => setModalImage(null)}
              className="absolute -top-12 right-0 p-2 text-white/80 hover:text-white"
              aria-label="Close modal"
            >
              <X className="w-6 h-6" />
            </button>
            <AuthenticatedImage
              src={modalImage}
              alt="Segmentation enlarged view"
              className="max-h-[85vh] max-w-full rounded-2xl object-contain shadow-2xl border border-white/10"
            />
          </div>
        </div>
      )}
    </div>
  );
}

export default SegmentationViewer;
