import React from 'react';
import { X, Camera, Sun, Focus, Layers, AlertCircle, CheckCircle2, Check, Sparkles } from 'lucide-react';

export function PhotoTipsModal({ isOpen, onClose }) {
  if (!isOpen) return null;

  const bestPractices = [
    {
      icon: Sun,
      title: 'Good Natural Lighting',
      desc: 'Take photos in bright, indirect daylight. Avoid harsh flash reflections or deep shadows that hide leaf textures.',
      color: 'text-amber-500 bg-amber-50 dark:bg-amber-950/60 border-amber-200 dark:border-amber-900',
    },
    {
      icon: Focus,
      title: 'Fill the Frame & Focus',
      desc: 'Get close enough so the leaf fills 70–80% of your camera screen. Tap your phone screen to focus on spots or veins.',
      color: 'text-emerald-600 bg-emerald-50 dark:bg-emerald-950/60 border-emerald-200 dark:border-emerald-900',
    },
    {
      icon: Layers,
      title: 'Clean, Plain Background',
      desc: 'Position the leaf away from background weeds, grass, or clutter. A plain surface helps the AI focus on true lesions.',
      color: 'text-blue-600 bg-blue-50 dark:bg-blue-950/60 border-blue-200 dark:border-blue-900',
    },
    {
      icon: Camera,
      title: 'Keep Both Sides Steady',
      desc: 'Hold the camera flat and parallel to the leaf blade. If symptoms appear on the underside (like mildew), photograph that side.',
      color: 'text-purple-600 bg-purple-50 dark:bg-purple-950/60 border-purple-200 dark:border-purple-900',
    },
  ];

  const commonMistakes = [
    'Blurry or moving leaf caused by wind',
    'Leaf too small in the distance with too much soil or weeds',
    'Dark indoor photo without adequate illumination',
    'Overexposed flash washing out discoloration',
  ];

  return (
    <div
      className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 animate-fade-in"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="photo-tips-title"
    >
      <div
        className="relative max-w-2xl w-full bg-white dark:bg-darkCard rounded-3xl p-6 sm:p-8 shadow-2xl border border-gray-200 dark:border-darkBorder space-y-6 text-xs max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-start justify-between border-b border-gray-100 dark:border-darkBorder pb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-emerald-100 dark:bg-emerald-950/80 text-emerald-600 dark:text-emerald-400 flex items-center justify-center shadow-subtle">
              <Camera className="w-5 h-5" />
            </div>
            <div>
              <h2 id="photo-tips-title" className="text-base sm:text-lg font-bold text-gray-900 dark:text-white">
                How to Take Photos for Best AI Accuracy
              </h2>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Simple tips to help the neural network recognize crop species and foliar symptoms accurately.
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-xl text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-darkElevated transition-colors"
            aria-label="Close photo tips"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* 4 Best Practices Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
          {bestPractices.map((practice) => {
            const Icon = practice.icon;
            return (
              <div
                key={practice.title}
                className="p-4 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder space-y-2"
              >
                <div className="flex items-center gap-2">
                  <div className={`p-2 rounded-xl border ${practice.color}`}>
                    <Icon className="w-4 h-4" />
                  </div>
                  <h3 className="font-bold text-gray-900 dark:text-white text-xs">
                    {practice.title}
                  </h3>
                </div>
                <p className="text-[11px] text-gray-600 dark:text-gray-300 leading-relaxed">
                  {practice.desc}
                </p>
              </div>
            );
          })}
        </div>

        {/* Mistakes to Avoid */}
        <div className="p-4 rounded-2xl bg-rose-50/60 dark:bg-rose-950/20 border border-rose-200/80 dark:border-rose-900/60 space-y-2">
          <div className="flex items-center gap-1.5 text-xs font-bold text-rose-800 dark:text-rose-300">
            <AlertCircle className="w-4 h-4 text-rose-500 shrink-0" />
            <span>Common Pitfalls to Avoid:</span>
          </div>
          <ul className="grid grid-cols-1 sm:grid-cols-2 gap-1.5 text-[11px] text-rose-900 dark:text-rose-200">
            {commonMistakes.map((mistake) => (
              <li key={mistake} className="flex items-start gap-1.5">
                <span className="text-rose-500 font-bold">✕</span>
                <span>{mistake}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Plain Language Reassurance */}
        <div className="p-3.5 rounded-2xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200/80 dark:border-emerald-800 text-[11px] text-emerald-800 dark:text-emerald-300 flex items-center gap-2.5">
          <Sparkles className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>
            <strong>Field Photography Tip:</strong> Keep the leaf blade steady and frame the suspect foliage clearly for best diagnostic results.
          </span>
        </div>

        {/* Footer */}
        <div className="flex justify-end pt-2">
          <button
            type="button"
            onClick={onClose}
            className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-glow-emerald transition-all transform active:scale-95"
          >
            Got it, Let&apos;s Analyze!
          </button>
        </div>
      </div>
    </div>
  );
}

export default PhotoTipsModal;
