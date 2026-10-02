import React, { useState } from 'react';
import { Eye, Maximize2, X, Sparkles, Layers, Info, ChevronDown, ChevronUp } from 'lucide-react';
import { resolveAssetUrl } from '../services/api';
import AuthenticatedImage from './AuthenticatedImage';
import { InfoTooltip } from './InfoTooltip';

export function GradCAMViewer({ explainability, originalImageSrc, className = '' }) {
  const [activeTab, setActiveTab] = useState('overlay'); // 'overlay' | 'heatmap' | 'original' | 'split'
  const [modalImage, setModalImage] = useState(null);
  const [showGradCamExplainer, setShowGradCamExplainer] = useState(false);

  if (!explainability || !explainability.available) {
    return (
      <div className={`p-6 rounded-3xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder shadow-subtle space-y-3 ${className}`}>
        <div className="flex items-center gap-2">
          <Eye className="w-4 h-4 text-gray-400" />
          <h3 className="text-sm font-bold uppercase tracking-wider text-gray-900 dark:text-white">
            Visual Explainability (Grad-CAM)
          </h3>
        </div>
        <p className="text-xs text-gray-500 dark:text-gray-400">
          {explainability?.message || 'Visual activation map not available for this sample'}
        </p>
      </div>
    );
  }

  const overlayUrl = explainability.overlay;
  const heatmapUrl = explainability.heatmap;
  const originalUrl = originalImageSrc;

  return (
    <div className={`p-6 sm:p-7 rounded-3xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder shadow-subtle space-y-5 ${className}`}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            <h3 className="text-sm font-bold uppercase tracking-wider text-gray-900 dark:text-white">
              Why did the AI make this prediction?
            </h3>
            <InfoTooltip
              title="Visual Explainability"
              content="Grad-CAM tracks backpropagated gradients to the final convolutional layer, projecting a heatmap of which leaf features most influenced the disease decision."
            />
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
            The highlighted regions show areas that contributed to the model's prediction. They should be interpreted as model explanations, not proof of disease.
          </p>
        </div>

        {/* Technical Tags */}
        <div className="flex items-center gap-2 text-[11px] font-mono">
          {explainability.target_layer && (
            <span className="px-2.5 py-1 rounded-md bg-gray-100 dark:bg-darkElevated text-gray-700 dark:text-gray-300 border border-gray-200 dark:border-darkBorder">
              Layer: <span className="font-semibold text-emerald-700 dark:text-emerald-400">{explainability.target_layer}</span>
            </span>
          )}
          {explainability.target_class_idx !== undefined && (
            <span className="px-2.5 py-1 rounded-md bg-gray-100 dark:bg-darkElevated text-gray-700 dark:text-gray-300 border border-gray-200 dark:border-darkBorder">
              Class Index: <span className="font-semibold">{explainability.target_class_idx}</span>
            </span>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex flex-wrap items-center gap-1.5 p-1 rounded-xl bg-gray-100 dark:bg-darkElevated border border-gray-200/80 dark:border-darkBorder w-fit text-xs font-semibold">
        <button
          onClick={() => setActiveTab('overlay')}
          className={`px-3.5 py-1.5 rounded-lg transition-all ${
            activeTab === 'overlay'
              ? 'bg-white dark:bg-darkCard text-emerald-800 dark:text-emerald-300 shadow-subtle'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
          }`}
        >
          Overlay
        </button>
        <button
          onClick={() => setActiveTab('heatmap')}
          className={`px-3.5 py-1.5 rounded-lg transition-all ${
            activeTab === 'heatmap'
              ? 'bg-white dark:bg-darkCard text-emerald-800 dark:text-emerald-300 shadow-subtle'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
          }`}
        >
          AI Attention
        </button>
        {originalUrl && (
          <button
            onClick={() => setActiveTab('original')}
            className={`px-3.5 py-1.5 rounded-lg transition-all ${
              activeTab === 'original'
                ? 'bg-white dark:bg-darkCard text-emerald-800 dark:text-emerald-300 shadow-subtle'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
            }`}
          >
            Original Image
          </button>
        )}
        {originalUrl && (
          <button
            onClick={() => setActiveTab('split')}
            className={`px-3.5 py-1.5 rounded-lg transition-all ${
              activeTab === 'split'
                ? 'bg-white dark:bg-darkCard text-emerald-800 dark:text-emerald-300 shadow-subtle'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
            }`}
          >
            Side-by-Side
          </button>
        )}
      </div>

      {/* Main Image Display Area */}
      <div className="relative rounded-2xl overflow-hidden bg-gray-950 border border-gray-200 dark:border-darkBorder group">
        {activeTab === 'split' ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-1 bg-black">
            <div className="relative aspect-square">
              <AuthenticatedImage
                src={originalUrl}
                alt="Original crop leaf"
                className="w-full h-full object-cover"
              />
              <span className="absolute top-3 left-3 px-2 py-1 rounded bg-black/60 backdrop-blur-sm text-white text-[11px] font-medium">
                Original Image
              </span>
            </div>
            <div className="relative aspect-square">
              <AuthenticatedImage
                src={overlayUrl || heatmapUrl}
                alt="Grad-CAM Overlay"
                className="w-full h-full object-cover"
              />
              <span className="absolute top-3 left-3 px-2 py-1 rounded bg-black/60 backdrop-blur-sm text-white text-[11px] font-medium">
                AI Attention Overlay
              </span>
            </div>
          </div>
        ) : (
          <div className="relative aspect-[4/3] sm:aspect-[16/10] flex items-center justify-center bg-black">
            <AuthenticatedImage
              src={
                activeTab === 'heatmap'
                  ? heatmapUrl
                  : activeTab === 'original'
                  ? originalUrl
                  : overlayUrl
              }
              alt="Grad-CAM explanation"
              className="max-h-full max-w-full object-contain"
            />

            {/* Expand / Fullscreen button */}
            <button
              onClick={() =>
                setModalImage(
                  activeTab === 'heatmap'
                    ? heatmapUrl
                    : activeTab === 'original'
                    ? originalUrl
                    : overlayUrl
                )
              }
              className="absolute top-3 right-3 p-2 rounded-xl bg-black/50 hover:bg-black/80 backdrop-blur-md text-white opacity-0 group-hover:opacity-100 transition-opacity"
              title="Expand view"
              aria-label="Expand image view"
            >
              <Maximize2 className="w-4 h-4" />
            </button>

            {/* Label overlay */}
            <div className="absolute bottom-3 left-3 px-3 py-1.5 rounded-xl bg-black/60 backdrop-blur-md text-white text-xs flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
              <span>
                {activeTab === 'heatmap'
                  ? 'Normalized JET Activation Intensity'
                  : activeTab === 'original'
                  ? 'Original Uploaded Leaf'
                  : 'Heatmap Alpha Blended on Original'}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Explanatory Footer & 'What is Grad-CAM?' Accordion */}
      <div className="space-y-2">
        <div className="p-3.5 rounded-xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder text-xs text-gray-500 dark:text-gray-400 flex items-start gap-2.5">
          <Info className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
          <span>
            Warmer colors (red, orange, yellow) indicate leaf regions where the deep learning model identified high diagnostic relevance for this prediction.
          </span>
        </div>

        {/* 'What is Grad-CAM?' Expandable */}
        <div className="border border-gray-200 dark:border-darkBorder rounded-2xl overflow-hidden bg-white dark:bg-darkCard">
          <button
            type="button"
            onClick={() => setShowGradCamExplainer(!showGradCamExplainer)}
            className="w-full p-3.5 flex items-center justify-between text-xs font-bold text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-darkElevated transition-colors text-left"
          >
            <span className="flex items-center gap-1.5">
              <Eye className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
              <span>What is Grad-CAM and how should I interpret it?</span>
            </span>
            {showGradCamExplainer ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
          {showGradCamExplainer && (
            <div className="p-4 pt-0 text-xs text-gray-600 dark:text-gray-300 leading-relaxed space-y-2 border-t border-gray-100 dark:border-darkBorder">
              <p>
                <strong>Gradient-weighted Class Activation Mapping (Grad-CAM)</strong> computes the gradients of the predicted class score with respect to the feature maps of the final convolutional layer.
              </p>
              <p>
                Grad-CAM reveals which visual textures (such as necrotic rings, halo spots, or vein chlorosis) influenced the classification. It does <strong>not</strong> prove biological pathogen viability or count bacteria under a microscope; it helps human reviewers ensure the AI is not looking at irrelevant background artifacts like soil, ruler marks, or camera glare.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Fullscreen Modal */}
      {modalImage && (
        <div
          className="fixed inset-0 z-50 bg-black/90 backdrop-blur-md flex items-center justify-center p-4"
          onClick={() => setModalImage(null)}
        >
          <div className="relative max-w-5xl max-h-[90vh]" onClick={(e) => e.stopPropagation()}>
            <button
              onClick={() => setModalImage(null)}
              className="absolute -top-12 right-0 p-2 text-white/80 hover:text-white"
              aria-label="Close modal"
            >
              <X className="w-6 h-6" />
            </button>
            <AuthenticatedImage
              src={modalImage}
              alt="Grad-CAM Enlarged"
              className="max-h-[85vh] max-w-full rounded-2xl object-contain shadow-2xl border border-white/10"
            />
          </div>
        </div>
      )}
    </div>
  );
}

export default GradCAMViewer;
