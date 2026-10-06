import React from 'react';
import { Link } from 'react-router-dom';
import {
  AlertTriangle,
  ShieldAlert,
  Info,
  Layers,
  Camera,
  Target,
  CheckCircle2,
  Users,
  Database,
  ArrowRight,
} from 'lucide-react';

export function Limitations() {
  const limitations = [
    {
      title: 'AI Predictions Can Be Wrong',
      icon: AlertTriangle,
      color: 'text-amber-600 dark:text-amber-400',
      bg: 'bg-amber-50 dark:bg-amber-950/40 border-amber-200 dark:border-amber-800',
      content:
        'Deep learning models are statistical pattern matchers. An image with unusual leaf coloration, nutritional deficiency, or insect damage can trigger an incorrect disease classification.',
    },
    {
      title: 'Image Quality & Lighting Variance',
      icon: Camera,
      color: 'text-blue-600 dark:text-blue-400',
      bg: 'bg-blue-50 dark:bg-blue-950/40 border-blue-200 dark:border-blue-800',
      content:
        'Motion blur, low illumination, harsh glare, and busy backgrounds degrade model accuracy. Input images must be reasonably centered, sharp, and well-lit for reliable feature extraction.',
    },
    {
      title: 'Laboratory vs. Real Field Conditions (Covariate Shift)',
      icon: Database,
      color: 'text-purple-600 dark:text-purple-400',
      bg: 'bg-purple-50 dark:bg-purple-950/40 border-purple-200 dark:border-purple-800',
      content:
        'Models trained predominantly on standardized laboratory datasets (such as PlantVillage) under artificial backgrounds should NOT be interpreted as fully field-validated across diverse outdoor weather conditions and mixed foliar disorders.',
    },
    {
      title: 'Confidence Is Not Correctness',
      icon: Target,
      color: 'text-rose-600 dark:text-rose-400',
      bg: 'bg-rose-50 dark:bg-rose-950/40 border-rose-200 dark:border-rose-800',
      content:
        'A model confidence score represents the normalized mathematical preference of the neural network among its learned categories. Even a 95% confidence score can be erroneous if the actual disease is outside the training split.',
    },
    {
      title: 'Grad-CAM Is an Explanation, Not Proof',
      icon: Layers,
      color: 'text-emerald-600 dark:text-emerald-400',
      bg: 'bg-emerald-50 dark:bg-emerald-950/40 border-emerald-200 dark:border-emerald-800',
      content:
        'Grad-CAM indicates which image regions contributed most strongly to the model activation. It visualizes the internal attention of the convolutional filters, but it does NOT constitute biological or laboratory proof of pathogen presence.',
    },
    {
      title: 'Lesion Segmentation Is an Estimate',
      icon: Target,
      color: 'text-indigo-600 dark:text-indigo-400',
      bg: 'bg-indigo-50 dark:bg-indigo-950/40 border-indigo-200 dark:border-indigo-800',
      content:
        'U-Net lesion masks isolate visible surface symptoms. Leaf curling, 3D leaf perspective distortion, and partial occlusion mean the calculated percentage is an estimated 2D surface coverage, not a volumetric biopsy.',
    },
    {
      title: 'Severity Categories Use Project-Defined Thresholds',
      icon: AlertTriangle,
      color: 'text-amber-600 dark:text-amber-400',
      bg: 'bg-amber-50 dark:bg-amber-950/40 border-amber-200 dark:border-amber-800',
      content:
        'Severity levels (Healthy, Early, Moderate, Severe) are assigned using project-defined percentage cutoffs. These thresholds have not been established as universal agronomic standards unless regional validation data is explicitly attached.',
    },
    {
      title: 'Decision Support Only — Certified Consultation Required',
      icon: Users,
      color: 'text-emerald-700 dark:text-emerald-300',
      bg: 'bg-emerald-50 dark:bg-emerald-950/40 border-emerald-200 dark:border-emerald-800',
      content:
        'Harvest Harbor is designed as an agricultural decision-support tool. It does NOT replace qualified agronomists, university extension pathologists, or certified crop advisors. Chemical treatments must always be verified with local agricultural authorities.',
    },
  ];

  return (
    <div className="space-y-8 animate-fade-in max-w-5xl mx-auto">
      {/* Header Banner */}
      <div className="p-8 sm:p-10 rounded-3xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder shadow-subtle space-y-3">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-50 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300 text-xs font-bold border border-amber-200 dark:border-amber-800">
          <ShieldAlert className="w-3.5 h-3.5" />
          <span>Scientific Transparency &amp; Research Ethics</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 dark:text-white tracking-tight">
          Understanding the Scientific Limitations
        </h1>
        <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-300 leading-relaxed max-w-3xl">
          Harvest Harbor adheres to rigorous scientific principles. For research credibility and agricultural safety, all users and reviewers must understand what the AI models can and cannot guarantee.
        </p>
      </div>

      {/* Grid of Limitations */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {limitations.map((item, idx) => {
          const Icon = item.icon;
          return (
            <div
              key={idx}
              className={`p-5 rounded-3xl border shadow-subtle space-y-2.5 bg-white dark:bg-darkCard ${item.bg}`}
            >
              <div className="flex items-center gap-2.5">
                <div className={`p-2 rounded-xl bg-white/80 dark:bg-darkElevated ${item.color}`}>
                  <Icon className="w-4 h-4" />
                </div>
                <h3 className="font-bold text-xs sm:text-sm text-gray-900 dark:text-white">
                  {item.title}
                </h3>
              </div>
              <p className="text-xs text-gray-600 dark:text-gray-300 leading-relaxed">
                {item.content}
              </p>
            </div>
          );
        })}
      </div>

      {/* Callout Footer */}
      <div className="p-6 rounded-3xl bg-gray-50 dark:bg-darkElevated border border-gray-200 dark:border-darkBorder flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 text-xs">
        <div className="space-y-1">
          <span className="font-bold text-gray-900 dark:text-white block">
            Have questions about field validation or model evaluation?
          </span>
          <p className="text-gray-500 dark:text-gray-400">
            Read our complete research architecture in the About section or analyze a leaf in the Analyze studio.
          </p>
        </div>
        <Link
          to="/about"
          className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold flex items-center gap-1.5 shadow-subtle shrink-0"
        >
          <span>Read Research Details</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  );
}

export default Limitations;
