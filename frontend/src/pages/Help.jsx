import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  HelpCircle,
  BookOpen,
  AlertTriangle,
  CheckCircle2,
  ScanLine,
  Layers,
  ShieldCheck,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Camera,
  Target,
  ArrowRight,
} from 'lucide-react';

export function Help() {
  const [activeFaq, setActiveFaq] = useState(null);

  const guideSteps = [
    {
      step: '01',
      title: 'Navigate to Analyze',
      description: 'Click "Analyze Crop" from the top navigation or sidebar to open the AI diagnostic studio.',
      icon: ScanLine,
    },
    {
      step: '02',
      title: 'Capture or Upload Leaf',
      description: 'Take a clear, well-lit field photo or drag-and-drop a JPG/PNG to run the diagnostic pipeline.',
      icon: Camera,
    },
    {
      step: '03',
      title: 'Pre-flight Resolution Verification',
      description: 'The client checks aspect ratio, resolution, and megapixel count to verify image quality before running inference.',
      icon: CheckCircle2,
    },
    {
      step: '04',
      title: 'Binary Health Screening',
      description: 'EfficientNet-B0 screens healthy leaves vs diseased foliage. If screened healthy, disease treatments are safely suppressed.',
      icon: ShieldCheck,
    },
    {
      step: '05',
      title: 'Botanical Crop Identification',
      description: 'The system identifies the crop family (Apple, Potato, Corn, Tomato, etc.) to enforce biological host compatibility.',
      icon: Sparkles,
    },
    {
      step: '06',
      title: 'Disease Classification',
      description: 'PlantWild v2 evaluates 115 disease classes, returning ranked candidate classes with softmax probabilities.',
      icon: Target,
    },
    {
      step: '07',
      title: 'Grad-CAM Attention Heatmap',
      description: 'Grad-CAM highlights the contributing leaf blade regions that drove the model prediction, ensuring the model focuses on actual lesions.',
      icon: Layers,
    },
    {
      step: '08',
      title: 'U-Net Lesion Segmentation',
      description: 'U-Net separates leaf foreground from chlorotic or necrotic spots to calculate the estimated percentage of affected blade area.',
      icon: Target,
    },
    {
      step: '09',
      title: 'Estimated Severity Assessment',
      description: 'Assigns a project-defined severity category (Healthy, Early, Moderate, Severe) based on visible symptom surface coverage.',
      icon: AlertTriangle,
    },
    {
      step: '10',
      title: 'Agronomist Review & Evidence Record',
      description: 'Cases with borderline confidence are flagged for human review, and a SHA-256 evidence record is recorded to the local evidence chain.',
      icon: BookOpen,
    },
  ];

  const faqs = [
    {
      q: 'Does Harvest Harbor replace an agronomist or plant pathologist?',
      a: 'No. Harvest Harbor is an AI decision-support platform designed to aid scouting and prioritization. It is not an official or legally binding diagnosis. Treatment applications must always be verified with a certified agronomic professional.',
    },
    {
      q: 'What does the model confidence score represent?',
      a: 'Confidence indicates how strongly the deep learning model preferred a specific disease class among its learned training classes. It is a mathematical output and should not be interpreted as absolute diagnostic correctness.',
    },
    {
      q: 'What do the red and yellow areas in Grad-CAM mean?',
      a: 'Warmer colors in Grad-CAM represent image regions that had the highest gradient activation contributing to the model class output. It shows where the AI looked—not laboratory proof of an active pathogen.',
    },
    {
      q: 'How is the affected leaf area calculated?',
      a: 'The U-Net segmentation network isolates pixels corresponding to visible lesions within estimated leaf boundaries. The metric is an estimate of visual foliar symptom coverage.',
    },
    {
      q: 'Why are some predicted diseases rejected by the system?',
      a: 'Botanical compatibility logic checks whether a pathogen can biologically infect the identified crop host. If a disease is botanically impossible for that plant species, the system rejects it and flags it for human review.',
    },
  ];

  return (
    <div className="space-y-10 animate-fade-in max-w-6xl mx-auto">
      {/* Hero Header */}
      <div className="p-8 sm:p-10 rounded-3xl bg-gradient-to-br from-emerald-950 via-emerald-900 to-gray-950 text-white shadow-premium border border-emerald-800/40 space-y-4">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-300 text-xs font-semibold backdrop-blur-sm border border-emerald-500/30">
          <BookOpen className="w-3.5 h-3.5" />
          <span>Documentation &amp; User Manual</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight">
          How to Use Harvest Harbor
        </h1>
        <p className="text-sm sm:text-base text-gray-300 max-w-2xl leading-relaxed">
          A step-by-step walkthrough of the 10-stage AI diagnostic journey from field leaf image to tamper-evident cryptographic report.
        </p>
        <div className="pt-2 flex flex-wrap gap-3">
          <Link
            to="/analyze"
            className="px-4 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-gray-950 text-xs font-bold shadow-glow-emerald transition-all"
          >
            Launch Analyze Studio
          </Link>
          <Link
            to="/limitations"
            className="px-4 py-2.5 rounded-xl bg-white/10 hover:bg-white/20 text-white text-xs font-semibold backdrop-blur-sm transition-all"
          >
            Read Scientific Limitations
          </Link>
        </div>
      </div>

      {/* 10-Step Visual Guide */}
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">
              The 10-Step Diagnostic Journey
            </h2>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Understanding the automated workflow behind every crop leaf evaluation.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5">
          {guideSteps.map((s) => {
            const Icon = s.icon;
            return (
              <div
                key={s.step}
                className="p-4 rounded-2xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder shadow-subtle space-y-2 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between text-gray-400 mb-2">
                    <span className="font-mono text-xs font-black text-emerald-600 dark:text-emerald-400">
                      STEP {s.step}
                    </span>
                    <Icon className="w-4 h-4" />
                  </div>
                  <h3 className="font-bold text-xs text-gray-900 dark:text-white">
                    {s.title}
                  </h3>
                  <p className="text-[11px] text-gray-500 dark:text-gray-400 mt-1 leading-relaxed">
                    {s.description}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* FAQ Section */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <HelpCircle className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
          <span>Frequently Asked Questions</span>
        </h2>

        <div className="space-y-2.5">
          {faqs.map((faq, idx) => (
            <div
              key={idx}
              className="rounded-2xl border border-gray-200 dark:border-darkBorder bg-white dark:bg-darkCard overflow-hidden"
            >
              <button
                type="button"
                onClick={() => setActiveFaq(activeFaq === idx ? null : idx)}
                className="w-full p-4 text-left flex items-center justify-between text-xs sm:text-sm font-bold text-gray-900 dark:text-white hover:bg-gray-50 dark:hover:bg-darkElevated transition-colors"
              >
                <span>{faq.q}</span>
                {activeFaq === idx ? (
                  <ChevronUp className="w-4 h-4 text-gray-400 shrink-0" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-gray-400 shrink-0" />
                )}
              </button>
              {activeFaq === idx && (
                <div className="p-4 pt-0 text-xs text-gray-600 dark:text-gray-300 leading-relaxed border-t border-gray-100 dark:border-darkBorder">
                  {faq.a}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default Help;
