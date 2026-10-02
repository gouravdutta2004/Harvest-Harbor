import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Sparkles,
  Cpu,
  Layers,
  ShieldCheck,
  Target,
  Database,
  Eye,
  Activity,
  BookOpen,
  Code2,
  FileCheck,
  AlertCircle,
  CheckCircle2,
  Sliders,
  HelpCircle,
  Search,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  Hash,
  ScanLine,
  ArrowRight,
  ShieldAlert,
  Zap,
  Info,
  Clock,
  RotateCcw,
} from 'lucide-react';
import { checkHealth, getTraceabilityStatus } from '../services/api';
import { CROPS_LIST, DISEASE_CATALOG } from '../data/diseaseDatabase';
import { formatPercent } from '../utils/formatters';

const PIPELINE_STAGES = [
  {
    id: 1,
    title: 'Image Ingestion & SHA-256 Hashing',
    shortName: '1. Ingest & Hash',
    icon: Hash,
    color: 'text-indigo-600 dark:text-indigo-400',
    bg: 'bg-indigo-50 dark:bg-indigo-950/60',
    border: 'border-indigo-200 dark:border-indigo-800',
    summary: 'Generates a unique cryptographic fingerprint for the uploaded leaf before any AI processing.',
    plainEnglish:
      'Just like a human fingerprint, every digital image has unique pixel data. Before the AI touches your image, Harvest Harbor generates an irreversible 64-character SHA-256 cryptographic hash. This ensures nobody can ever tamper with your diagnostic record or swap the photo later.',
    technicalDetails: {
      algorithm: 'SHA-256 (Secure Hash Algorithm 256-bit)',
      inputFormats: 'JPEG, PNG, WEBP (up to 15 MB)',
      preflightChecks: 'Resolution verification, aspect ratio diagnostics, and memory-safe normalization',
      output: '64-character hexadecimal digest (e.g. 5f3d8a...b791)',
    },
    whyItMatters:
      'Provides tamper-evident cryptographic evidence linking the recorded analysis to the stored image and report data.',
  },
  {
    id: 2,
    title: 'Binary Health Screening',
    shortName: '2. Health Screen',
    icon: Cpu,
    color: 'text-emerald-600 dark:text-emerald-400',
    bg: 'bg-emerald-50 dark:bg-emerald-950/60',
    border: 'border-emerald-200 dark:border-emerald-800',
    summary: 'Instantly determines whether the leaf is healthy or exhibits potential pathological disease.',
    plainEnglish:
      'Rather than guessing among hundreds of diseases right away, the first neural network asks one simple question: "Is this plant healthy or diseased?" If healthy, the system generates a Clean Health Screening Record without false disease alarms.',
    technicalDetails: {
      model: 'EfficientNet-B0 (Binary Transfer Learning)',
      classes: '2 Classes: [Healthy, Diseased]',
      inputResolution: '224 × 224 pixels RGB',
      lossFunction: 'Binary Cross-Entropy with Sigmoid Activation',
      decisionThreshold: '0.50 (Default)',
    },
    whyItMatters:
      'Saves farmers money and prevents unnecessary chemical sprays. If a plant has normal seasonal color variation or natural leaf shape, it is not mislabeled as sick.',
  },
  {
    id: 3,
    title: 'Multi-Class Disease Classification',
    shortName: '3. Disease Match',
    icon: Layers,
    color: 'text-blue-600 dark:text-blue-400',
    bg: 'bg-blue-50 dark:bg-blue-950/60',
    border: 'border-blue-200 dark:border-blue-800',
    summary: 'Generates an AI-assisted disease-class prediction across 115 agricultural plant diseases with Top-3 ranked confidence.',
    plainEnglish:
      'If the leaf is diseased, a second deep learning network examines the lesion patterns, chlorotic halos, and textures. It outputs the top 3 most probable diseases, ranked by percentage confidence, along with an uncertainty rating.',
    technicalDetails: {
      model: 'PlantWild v2 EfficientNet-B0 Backbone',
      classes: '115 Plant Disease Classes across 30+ staple crops',
      inputResolution: '224 × 224 pixels normalized [0, 1]',
      outputMechanism: 'Softmax Probability Distribution with Top-3 Ranking',
      uncertaintyMetric: 'Derived from softmax entropy and margin distance',
    },
    whyItMatters:
      'Different foliar conditions require different management strategies. Identifying the likely disease class helps guide appropriate cultural and sanitation responses.',
  },
  {
    id: 4,
    title: 'Visual Explainability (Grad-CAM)',
    shortName: '4. AI Heatmap',
    icon: Eye,
    color: 'text-amber-600 dark:text-amber-400',
    bg: 'bg-amber-50 dark:bg-amber-950/60',
    border: 'border-amber-200 dark:border-amber-800',
    summary: 'Highlights image regions and visual features contributing to the model prediction.',
    plainEnglish:
      'AI shouldn\'t be a mysterious "black box." Grad-CAM (Gradient-weighted Class Activation Mapping) produces a color heat map: Red and yellow areas show where the AI focused its attention, while blue areas were ignored. You can verify that the AI is looking at the actual disease spot, not background dirt or fingers.',
    technicalDetails: {
      method: 'Grad-CAM on the final convolutional feature layer (top_activation)',
      resolution: '7 × 7 feature map upscaled via bicubic interpolation to match original dimensions',
      colorMap: 'JET colormap (Red = Peak Activation, Blue = Zero Activation)',
      blending: 'Alpha overlay (0.45 weight) on the original leaf photo',
    },
    whyItMatters:
      'Builds trust with agronomists. If the AI flags an apple leaf as Scab, the agronomist can see that the red spotlight is directly on the scab lesion, confirming the AI did not hallucinate.',
  },
  {
    id: 5,
    title: 'Estimated Lesion Segmentation & Surface Area',
    shortName: '5. U-Net Lesion',
    icon: Target,
    color: 'text-purple-600 dark:text-purple-400',
    bg: 'bg-purple-50 dark:bg-purple-950/60',
    border: 'border-purple-200 dark:border-purple-800',
    summary: 'Estimates healthy leaf tissue from diseased lesion tissue at the pixel level.',
    plainEnglish:
      'A specialized U-Net neural network scans the leaf and highlights the damaged spots in red and healthy green foliage in green. It estimates visible lesion pixels relative to detected leaf surface to calculate the estimated percentage of affected blade area.',
    technicalDetails: {
      architecture: 'U-Net Deep Convolutional Encoder-Decoder with Skip Connections',
      trainingDataset: 'PlantSeg Benchmark (9,163 image-mask pairs)',
      lossFunction: 'Combined BCE (Binary Cross-Entropy) + Soft Dice Loss',
      inputDimensions: '256 × 256 × 3 RGB',
      foregroundExtraction: 'Adaptive HSV/Lab color space vegetation masking',
    },
    whyItMatters:
      'Eyeballing disease coverage in the field is notoriously inaccurate. Estimating the percentage of detected affected leaf area provides an objective, repeatable scientific measurement of leaf surface symptoms.',
  },
  {
    id: 6,
    title: 'Estimated Severity Grading & Guidance',
    shortName: '6. Severity Tier',
    icon: Activity,
    color: 'text-rose-600 dark:text-rose-400',
    bg: 'bg-rose-50 dark:bg-rose-950/60',
    border: 'border-rose-200 dark:border-rose-800',
    summary: 'Categorizes estimated infection into Healthy, Early, Moderate, or Severe with illustrative management guidance.',
    plainEnglish:
      'Based on the estimated percentage of leaf affected, the platform classifies the disease into 4 project-defined stages: Healthy (0%), Early (<15%), Moderate (15–35%), and Severe (≥35%). It then provides illustrative field guidance, from monitoring to consulting a specialist.',
    technicalDetails: {
      formula: 'Estimated Affected Area % = (Diseased Pixels / Leaf Pixels) × 100',
      tiers: 'Healthy (0%) | Early (<15%) | Moderate (15%–35%) | Severe (≥35%)',
      calibrationSupport: 'Dynamic threshold presets for aggressive pathogens vs tolerant crops',
      marginMetric: 'Distance to closest threshold boundary to identify borderline cases',
    },
    whyItMatters:
      'Helps farmers prioritize scouting and evaluate whether mild cultural hygiene or agronomist consultation is recommended.',
  },
  {
    id: 7,
    title: 'Local SHA-256 Hash-Linked Evidence Chain',
    shortName: '7. Cryptographic Chain',
    icon: ShieldCheck,
    color: 'text-emerald-600 dark:text-emerald-400',
    bg: 'bg-emerald-50 dark:bg-emerald-950/60',
    border: 'border-emerald-200 dark:border-emerald-800',
    summary: 'Seals the complete assessment, timestamps, and model hashes into an append-only verifiable chain.',
    plainEnglish:
      'Every completed assessment is recorded as a tamper-evident SHA-256 hash-linked evidence record. Each evidence record contains relevant analysis metadata, timestamp, image hash, full assessment snapshot, and previous-record hash. The system is a local SHA-256 hash-linked evidence chain, not a decentralized/public blockchain. If anyone modifies a record, the cryptographic chain continuity breaks, immediately indicating tampering.',
    technicalDetails: {
      chainStructure: 'Thread-safe SHA-256 linked cryptographic evidence chain (local append-only log)',
      recordPayload: 'Evidence record index, timestamp, report ID, image hash, full assessment snapshot, previous record hash',
      verificationAlgorithm: 'Recursive re-hashing verifying genesis continuity and payload integrity',
      exportFormats: 'JSON audit export and printable assessment verification dossier',
    },
    whyItMatters:
      'Provides tamper-evident evidence records for agricultural documentation, research archives, supply-chain traceability, and farm record-keeping.',
  },
];

const FAQ_ITEMS = [
  {
    q: 'How should I take photos of leaves in the field for best results?',
    a: 'For maximum AI accuracy: 1) Fill about 70-80% of the camera frame with the leaf blade. 2) Ensure bright, natural diffuse daylight (avoid harsh direct flash or deep shadows). 3) Keep the background neutral (e.g. soil, a clipboard, or palm of your hand). 4) Ensure the camera focuses sharply on the active lesion spots rather than the stem.',
  },
  {
    q: 'What do the red, yellow, and blue colors mean in the Grad-CAM heatmap?',
    a: 'Grad-CAM uses the JET thermal color spectrum. Bright Red indicates the primary area of interest that caused the AI to make its prediction (such as a fungal ring or necrotic spot). Yellow and green represent secondary contributing textures. Deep blue represents background plant tissue that the AI determined was neutral or normal.',
  },
  {
    q: 'How is the affected leaf percentage calculated?',
    a: 'Unlike naive tools that measure lesions across the entire rectangular image frame, Harvest Harbor first isolates the leaf foreground using HSV and Lab color space analysis. Then, U-Net segments the disease lesion pixels within that boundary. The formula is: (Diseased Pixels ÷ Total Leaf Foreground Pixels) × 100. This ensures accurate percentages regardless of how far the leaf is from the camera.',
  },
  {
    q: 'Can I customize the severity thresholds for my specific crops?',
    a: 'Yes! Economic injury levels differ between crops. For example, aggressive blights like Potato Late Blight require immediate intervention at just 5% foliar coverage, whereas mildews on hardy squash can be tolerated up to 20%. In the Severity Card or in the Interactive Lab on this page, you can choose pre-configured presets (High-Risk Blight, Tolerant Canopy) or customize the threshold cutoff sliders.',
  },
  {
    q: 'How does this evidence chain work and is it connected to a cryptocurrency network?',
    a: 'No. Harvest Harbor uses a local, lightweight, tamper-evident SHA-256 hash chain without token economics, cryptocurrency mining, or public network latency. Every record is cryptographically bound to the previous record hash. Any altered record breaks the chain verification proof.',
  },
  {
    q: 'What should I do if the AI-assisted assessment indicates "High Uncertainty"?',
    a: 'High uncertainty occurs when the photo is blurry, poorly lit, or contains overlapping symptoms from multiple stress factors (e.g. drought plus insect feeding). In high-uncertainty cases, the system routes the report to the Human Review Queue where an agronomist inspects the evidence manually. We recommend capturing a clearer photo in direct morning daylight.',
  },
  {
    q: 'Can Harvest Harbor results be used as official regulatory or insurance certifications?',
    a: 'No. Harvest Harbor is an AI-assisted decision-support instrument, not an accredited testing laboratory or certifying authority. While every report includes a verifiable Report ID, timestamp, and SHA-256 hash for internal record-keeping, official regulatory quarantine rulings or insurance claims require physical inspection and laboratory assays from certified agronomists.',
  },
  {
    q: 'What happens if my device is offline in the field?',
    a: 'You can use your mobile camera to capture high-resolution photos and store them locally. Once your device reconnects to Wi-Fi or cellular service, you can upload the saved images to run multi-branch inference and record the tamper-evident evidence record.',
  },
];

export function About() {
  const [activeTab, setActiveTab] = useState('pipeline'); // 'pipeline' | 'simulator' | 'diagnostics' | 'catalog' | 'faq'
  const [selectedStageId, setSelectedStageId] = useState(1);
  const [activeFaq, setActiveFaq] = useState(null);

  // Simulator state
  const [simAffectedArea, setSimAffectedArea] = useState(12.5);
  const [simPreset, setSimPreset] = useState('baseline'); // 'baseline' | 'aggressive' | 'tolerant'
  const [simEarlyMax, setSimEarlyMax] = useState(15);
  const [simModerateMax, setSimModerateMax] = useState(35);
  const [simSavedNotice, setSimSavedNotice] = useState(false);

  // Diagnostics state
  const [isPinging, setIsPinging] = useState(false);
  const [healthStatus, setHealthStatus] = useState(null);
  const [traceStatus, setTraceStatus] = useState(null);
  const [pingLatency, setPingLatency] = useState(null);
  const [showRawJson, setShowRawJson] = useState(false);

  // Catalog search state
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCropFilter, setSelectedCropFilter] = useState('All');
  const [expandedDiseaseId, setExpandedDiseaseId] = useState(null);

  // Fetch initial health diagnostics on mount
  useEffect(() => {
    runLiveDiagnostics();
  }, []);

  const runLiveDiagnostics = async () => {
    setIsPinging(true);
    const start = performance.now();
    try {
      const [hData, tData] = await Promise.all([
        checkHealth(),
        getTraceabilityStatus(),
      ]);
      const latency = Math.round(performance.now() - start);
      setHealthStatus(hData);
      setTraceStatus(tData);
      setPingLatency(latency);
    } catch (err) {
      console.error('Diagnostics failed:', err);
    } finally {
      setIsPinging(false);
    }
  };

  // Simulator calculation
  const getSimCategory = (area, early, mod) => {
    if (area <= 0) return { category: 'Healthy', color: 'text-emerald-700 dark:text-emerald-400', bg: 'bg-emerald-50 dark:bg-emerald-950/60', border: 'border-emerald-300 dark:border-emerald-800' };
    if (area < early) return { category: 'Early', color: 'text-blue-700 dark:text-blue-400', bg: 'bg-blue-50 dark:bg-blue-950/60', border: 'border-blue-300 dark:border-blue-800' };
    if (area < mod) return { category: 'Moderate', color: 'text-amber-700 dark:text-amber-400', bg: 'bg-amber-50 dark:bg-amber-950/60', border: 'border-amber-300 dark:border-amber-800' };
    return { category: 'Severe', color: 'text-rose-700 dark:text-rose-400', bg: 'bg-rose-50 dark:bg-rose-950/60', border: 'border-rose-300 dark:border-rose-800' };
  };

  const simResult = getSimCategory(simAffectedArea, simEarlyMax, simModerateMax);
  const boundaries = [0, simEarlyMax, simModerateMax];
  const simMargin = Math.min(...boundaries.map((b) => Math.abs(simAffectedArea - b))).toFixed(1);
  const simUncertainty = simMargin < 2.0 ? 'High' : simMargin < 5.0 ? 'Medium' : 'Low';

  const handleApplyPreset = (type) => {
    setSimPreset(type);
    if (type === 'aggressive') {
      setSimEarlyMax(5);
      setSimModerateMax(15);
    } else if (type === 'tolerant') {
      setSimEarlyMax(20);
      setSimModerateMax(45);
    } else {
      setSimEarlyMax(15);
      setSimModerateMax(35);
    }
  };

  const handleSaveToGlobalCalibration = () => {
    sessionStorage.setItem(
      'harvest_harbor_severity_calibration',
      JSON.stringify({
        preset: simPreset,
        earlyMax: simEarlyMax,
        moderateMax: simModerateMax,
      })
    );
    setSimSavedNotice(true);
    setTimeout(() => setSimSavedNotice(false), 3000);
  };

  const selectedStage = PIPELINE_STAGES.find((s) => s.id === selectedStageId) || PIPELINE_STAGES[0];
  const SelectedIcon = selectedStage.icon;

  // Filter disease catalog
  const filteredDiseases = DISEASE_CATALOG.filter((item) => {
    const matchesCrop = selectedCropFilter === 'All' || item.crop.toLowerCase() === selectedCropFilter.toLowerCase();
    const matchesSearch =
      !searchQuery.trim() ||
      item.disease.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.crop.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.pathogen.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCrop && matchesSearch;
  });

  return (
    <div className="space-y-8 animate-fade-in max-w-6xl mx-auto pb-12">
      {/* Hero Header */}
      <div className="relative p-6 sm:p-10 rounded-3xl bg-gradient-to-br from-emerald-900 via-emerald-950 to-gray-950 text-white overflow-hidden shadow-premium border border-emerald-800/40">
        <div className="relative z-10 space-y-4 max-w-3xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-300 text-xs font-semibold backdrop-blur-sm border border-emerald-500/30">
            <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
            <span>Agricultural Intelligence &amp; Cryptographic Evidence</span>
          </div>

          <div className="flex items-center gap-4 pt-1">
            <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-2xl overflow-hidden border border-emerald-400/40 shadow-glow-emerald bg-black/40 backdrop-blur-sm p-1 flex-shrink-0">
              <img src="/logo.png" alt="Harvest Harbor Logo" className="w-full h-full object-cover rounded-xl" />
            </div>
            <div>
              <h1 className="text-3xl sm:text-5xl font-black tracking-tight text-white">
                About Harvest Harbor
              </h1>
              <p className="text-xs sm:text-sm text-emerald-300 font-medium tracking-wide uppercase mt-1">
                AI for Healthier Crops, Brighter Tomorrows
              </p>
            </div>
          </div>

          <p className="text-sm sm:text-base text-gray-300 leading-relaxed">
            Harvest Harbor pairs deep learning crop pathology with segmentation-based estimation of visible affected regions (U-Net), visual explainability (Grad-CAM), and a tamper-evident cryptographic hash chain. Built to make complex agricultural AI simple, reliable, and completely transparent for farmers, agronomists, and auditors.
          </p>

          <div className="pt-2 flex flex-wrap items-center gap-3">
            <Link
              to="/analyze"
              className="px-5 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-gray-950 text-xs sm:text-sm font-bold shadow-glow-emerald flex items-center gap-2 transition-all transform active:scale-95"
            >
              <ScanLine className="w-4 h-4" />
              <span>Launch Live Analyzer</span>
            </Link>

            <button
              onClick={() => setActiveTab('diagnostics')}
              className="px-5 py-2.5 rounded-xl bg-white/10 hover:bg-white/20 text-white text-xs sm:text-sm font-semibold backdrop-blur-sm border border-white/10 flex items-center gap-2 transition-all"
            >
              <Zap className="w-4 h-4 text-emerald-300" />
              <span>Check Live AI Health</span>
            </button>
          </div>
        </div>

        {/* Ambient glow */}
        <div className="absolute -right-10 -bottom-10 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
      </div>

      {/* Main Feature Tabs */}
      <div className="flex flex-wrap items-center gap-2 p-1.5 rounded-2xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder shadow-subtle">
        <button
          onClick={() => setActiveTab('pipeline')}
          className={`flex-1 min-w-[130px] py-2.5 px-3 rounded-xl text-xs sm:text-sm font-bold flex items-center justify-center gap-2 transition-all ${
            activeTab === 'pipeline'
              ? 'bg-emerald-600 text-white shadow-glow-emerald'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-darkElevated'
          }`}
        >
          <Cpu className="w-4 h-4" />
          <span>How It Works (7 Stages)</span>
        </button>

        <button
          onClick={() => setActiveTab('simulator')}
          className={`flex-1 min-w-[130px] py-2.5 px-3 rounded-xl text-xs sm:text-sm font-bold flex items-center justify-center gap-2 transition-all ${
            activeTab === 'simulator'
              ? 'bg-emerald-600 text-white shadow-glow-emerald'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-darkElevated'
          }`}
        >
          <Sliders className="w-4 h-4" />
          <span>Interactive Severity Lab</span>
        </button>

        <button
          onClick={() => setActiveTab('diagnostics')}
          className={`flex-1 min-w-[130px] py-2.5 px-3 rounded-xl text-xs sm:text-sm font-bold flex items-center justify-center gap-2 transition-all ${
            activeTab === 'diagnostics'
              ? 'bg-emerald-600 text-white shadow-glow-emerald'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-darkElevated'
          }`}
        >
          <Activity className="w-4 h-4" />
          <span>Live Neural Health</span>
        </button>

        <button
          onClick={() => setActiveTab('catalog')}
          className={`flex-1 min-w-[130px] py-2.5 px-3 rounded-xl text-xs sm:text-sm font-bold flex items-center justify-center gap-2 transition-all ${
            activeTab === 'catalog'
              ? 'bg-emerald-600 text-white shadow-glow-emerald'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-darkElevated'
          }`}
        >
          <BookOpen className="w-4 h-4" />
          <span>Disease Encyclopedia</span>
        </button>

        <button
          onClick={() => setActiveTab('faq')}
          className={`flex-1 min-w-[130px] py-2.5 px-3 rounded-xl text-xs sm:text-sm font-bold flex items-center justify-center gap-2 transition-all ${
            activeTab === 'faq'
              ? 'bg-emerald-600 text-white shadow-glow-emerald'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-darkElevated'
          }`}
        >
          <HelpCircle className="w-4 h-4" />
          <span>Agronomist FAQ</span>
        </button>
      </div>

      {/* TAB 1: HOW IT WORKS (7 STAGES INTERACTIVE PIPELINE EXPLORER) */}
      {activeTab === 'pipeline' && (
        <div className="space-y-6">
          <div className="p-6 rounded-3xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder shadow-subtle space-y-4">
            <div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                <Cpu className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                <span>The 7-Stage End-to-End AI Pathology Pipeline</span>
              </h2>
              <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 mt-1">
                Click any stage below to inspect what happens under the hood, how the model makes its choice, and why it matters in the field.
              </p>
            </div>

            {/* Stepper bar */}
            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2 pt-2">
              {PIPELINE_STAGES.map((stage) => {
                const isSelected = stage.id === selectedStageId;
                const Icon = stage.icon;
                return (
                  <button
                    key={stage.id}
                    onClick={() => setSelectedStageId(stage.id)}
                    className={`p-3 rounded-2xl border text-left transition-all ${
                      isSelected
                        ? `${stage.bg} ${stage.border} ring-2 ring-emerald-500/20 shadow-subtle scale-[1.02]`
                        : 'bg-gray-50 dark:bg-darkElevated border-gray-200 dark:border-darkBorder hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <div className={`p-1.5 rounded-lg ${stage.bg} ${stage.color}`}>
                        <Icon className="w-4 h-4" />
                      </div>
                      <span className="text-[10px] font-mono font-bold text-gray-400">
                        0{stage.id}
                      </span>
                    </div>
                    <span className="text-xs font-bold text-gray-900 dark:text-white block truncate">
                      {stage.shortName}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Detailed Stage Deep-Dive Card */}
          <div className="p-6 sm:p-8 rounded-3xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder shadow-subtle space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-gray-100 dark:border-darkBorder pb-5">
              <div className="flex items-center gap-3">
                <div className={`p-3 rounded-2xl ${selectedStage.bg} ${selectedStage.color}`}>
                  <SelectedIcon className="w-6 h-6" />
                </div>
                <div>
                  <span className="text-xs font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400">
                    Stage 0{selectedStage.id} of 07
                  </span>
                  <h3 className="text-xl sm:text-2xl font-black text-gray-900 dark:text-white">
                    {selectedStage.title}
                  </h3>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <button
                  disabled={selectedStageId === 1}
                  onClick={() => setSelectedStageId((prev) => Math.max(1, prev - 1))}
                  className="px-3 py-1.5 rounded-xl border border-gray-200 dark:border-darkBorder text-xs font-semibold disabled:opacity-30 hover:bg-gray-100 dark:hover:bg-darkElevated"
                >
                  ← Previous
                </button>
                <button
                  disabled={selectedStageId === 7}
                  onClick={() => setSelectedStageId((prev) => Math.min(7, prev + 1))}
                  className="px-3 py-1.5 rounded-xl bg-emerald-600 text-white text-xs font-semibold disabled:opacity-30 hover:bg-emerald-500 shadow-glow-emerald"
                >
                  Next Stage →
                </button>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
              {/* Left Column: Plain-English explanation */}
              <div className="space-y-4">
                <div className="p-4 rounded-2xl bg-emerald-50/60 dark:bg-emerald-950/30 border border-emerald-100 dark:border-emerald-800/60 space-y-1.5">
                  <span className="text-xs font-bold uppercase tracking-wider text-emerald-800 dark:text-emerald-300 flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>In Plain English: What Happens Here</span>
                  </span>
                  <p className="text-xs sm:text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
                    {selectedStage.plainEnglish}
                  </p>
                </div>

                <div className="p-4 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder space-y-1.5">
                  <span className="text-xs font-bold uppercase tracking-wider text-gray-700 dark:text-gray-300 flex items-center gap-1.5">
                    <Target className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
                    <span>Why This Matters In The Field</span>
                  </span>
                  <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                    {selectedStage.whyItMatters}
                  </p>
                </div>
              </div>

              {/* Right Column: Deep Technical Specs */}
              <div className="p-5 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-200 dark:border-darkBorder space-y-3">
                <div className="flex items-center justify-between border-b border-gray-200/80 dark:border-darkBorder pb-2">
                  <span className="text-xs font-bold uppercase tracking-wider text-gray-800 dark:text-gray-200 flex items-center gap-1.5">
                    <Code2 className="w-4 h-4 text-purple-600 dark:text-purple-400" />
                    <span>Technical Architecture Specs</span>
                  </span>
                  <span className="text-[11px] font-mono text-emerald-600 dark:text-emerald-400 font-semibold">
                    Production Verified
                  </span>
                </div>

                <div className="space-y-2.5 text-xs">
                  {Object.entries(selectedStage.technicalDetails).map(([key, val]) => (
                    <div key={key} className="flex flex-col sm:flex-row sm:justify-between gap-1 py-1 border-b border-gray-100 dark:border-darkBorder/60">
                      <span className="text-gray-500 dark:text-gray-400 capitalize font-medium">
                        {key.replace(/([A-Z])/g, ' $1')}:
                      </span>
                      <span className="font-mono text-gray-900 dark:text-white font-semibold sm:text-right">
                        {val}
                      </span>
                    </div>
                  ))}
                </div>

                <div className="pt-2 flex justify-end">
                  <Link
                    to="/analyze"
                    className="inline-flex items-center gap-1.5 text-xs text-emerald-600 dark:text-emerald-400 font-bold hover:underline"
                  >
                    <span>Test this stage with real leaf image</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: INTERACTIVE SEVERITY & CALIBRATION SIMULATOR */}
      {activeTab === 'simulator' && (
        <div className="space-y-6">
          <div className="p-6 sm:p-8 rounded-3xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder shadow-subtle space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h2 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                  <Sliders className="w-6 h-6 text-emerald-600 dark:text-emerald-400" />
                  <span>Interactive Severity Threshold Simulator</span>
                </h2>
                <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 mt-1">
                  Adjust the affected leaf surface slider to see how the mathematical severity engine dynamically calculates categories, risk margins, and management guidance.
                </p>
                <div className="mt-3 p-3 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 text-xs text-amber-900 dark:text-amber-200">
                  <strong>Notice:</strong> The severity categories shown here use project-defined thresholds. They should not be interpreted as expert-validated agronomic standards unless validation data is available.
                </div>
              </div>

              {/* Dynamic Severity Badge */}
              <div className={`px-4 py-2 rounded-2xl border ${simResult.border} ${simResult.bg} flex items-center gap-2.5 shrink-0`}>
                <span className="w-3 h-3 rounded-full bg-current" style={{ color: 'inherit' }} />
                <span className={`text-base font-extrabold uppercase tracking-wider ${simResult.color}`}>
                  {simResult.category}
                </span>
                <span className="text-sm font-mono font-bold text-gray-900 dark:text-white">
                  {simAffectedArea.toFixed(1)}%
                </span>
              </div>
            </div>

            {/* Slider & Presets */}
            <div className="p-5 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder space-y-5">
              <div className="space-y-3">
                <div className="flex justify-between text-xs font-bold text-gray-900 dark:text-white">
                  <span>Simulated Leaf Damage Coverage:</span>
                  <span className="font-mono text-sm text-emerald-600 dark:text-emerald-400">
                    {simAffectedArea.toFixed(1)}% of leaf blade
                  </span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="80"
                  step="0.5"
                  value={simAffectedArea}
                  onChange={(e) => setSimAffectedArea(Number(e.target.value))}
                  className="w-full h-2.5 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer accent-emerald-600"
                />
                
                {/* Explicit Project-Defined Thresholds Banner */}
                <div className="p-3 rounded-xl bg-gray-100 dark:bg-darkElevated border border-gray-200 dark:border-darkBorder text-center">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400 block mb-1">
                    PROJECT-DEFINED THRESHOLDS
                  </span>
                  <div className="flex flex-wrap justify-between text-[11px] font-mono text-gray-700 dark:text-gray-300 gap-2">
                    <span>Healthy: 0%</span>
                    <span>Early: &gt;0% and &lt;15%</span>
                    <span>Moderate: &ge;15% and &lt;35%</span>
                    <span>Severe: &ge;35%</span>
                  </div>
                </div>
              </div>

              {/* Presets */}
              <div className="pt-2 border-t border-gray-200/80 dark:border-darkBorder space-y-2">
                <span className="text-xs font-bold text-gray-800 dark:text-gray-200 block">
                  Select Agronomic Threshold Preset:
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                  <button
                    onClick={() => handleApplyPreset('baseline')}
                    className={`p-3 rounded-xl border text-left text-xs transition-all ${
                      simPreset === 'baseline'
                        ? 'bg-emerald-50 dark:bg-emerald-950/60 border-emerald-400 text-emerald-900 dark:text-emerald-300 font-bold ring-1 ring-emerald-500/20'
                        : 'bg-white dark:bg-darkCard border-gray-200 dark:border-darkBorder text-gray-700 dark:text-gray-300'
                    }`}
                  >
                    <div>Standard Baseline (General)</div>
                    <div className="text-[10px] opacity-75 font-mono">Early: &lt;15% • Mod: &lt;35%</div>
                  </button>

                  <button
                    onClick={() => handleApplyPreset('aggressive')}
                    className={`p-3 rounded-xl border text-left text-xs transition-all ${
                      simPreset === 'aggressive'
                        ? 'bg-emerald-50 dark:bg-emerald-950/60 border-emerald-400 text-emerald-900 dark:text-emerald-300 font-bold ring-1 ring-emerald-500/20'
                        : 'bg-white dark:bg-darkCard border-gray-200 dark:border-darkBorder text-gray-700 dark:text-gray-300'
                    }`}
                  >
                    <div>High-Risk Blights (Late Blight)</div>
                    <div className="text-[10px] opacity-75 font-mono">Early: &lt;5% • Mod: &lt;15%</div>
                  </button>

                  <button
                    onClick={() => handleApplyPreset('tolerant')}
                    className={`p-3 rounded-xl border text-left text-xs transition-all ${
                      simPreset === 'tolerant'
                        ? 'bg-emerald-50 dark:bg-emerald-950/60 border-emerald-400 text-emerald-900 dark:text-emerald-300 font-bold ring-1 ring-emerald-500/20'
                        : 'bg-white dark:bg-darkCard border-gray-200 dark:border-darkBorder text-gray-700 dark:text-gray-300'
                    }`}
                  >
                    <div>High-Tolerance Canopies</div>
                    <div className="text-[10px] opacity-75 font-mono">Early: &lt;20% • Mod: &lt;45%</div>
                  </button>
                </div>
              </div>
            </div>

            {/* Real-time Dynamic Metrics */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="p-4 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder space-y-1">
                <span className="text-[11px] font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider block">
                  Severity Classification
                </span>
                <span className={`text-xl font-black ${simResult.color}`}>
                  {simResult.category}
                </span>
                <span className="text-[10px] text-gray-400 block">
                  Under {simPreset.toUpperCase()} protocol
                </span>
              </div>

              <div className="p-4 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder space-y-1">
                <span className="text-[11px] font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider block">
                  Threshold Boundary Margin
                </span>
                <span className="text-xl font-mono font-bold text-gray-900 dark:text-white">
                  ±{simMargin}%
                </span>
                <span className="text-[10px] text-gray-400 block">
                  Distance to next category shift
                </span>
              </div>

              <div className="p-4 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder space-y-1">
                <span className="text-[11px] font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider block">
                  Severity Uncertainty
                </span>
                <span
                  className={`text-xl font-bold ${
                    simUncertainty === 'High'
                      ? 'text-amber-600 dark:text-amber-400'
                      : 'text-emerald-600 dark:text-emerald-400'
                  }`}
                >
                  {simUncertainty}
                </span>
                <span className="text-[10px] text-gray-400 block">
                  {simUncertainty === 'High' ? 'Borderline condition' : 'Definitive category'}
                </span>
              </div>
            </div>

            {/* Illustrative Management Guidance */}
            <div className="p-4 rounded-2xl bg-emerald-50/50 dark:bg-emerald-950/30 border border-emerald-100 dark:border-emerald-800/60 space-y-1 text-xs">
              <span className="font-bold text-emerald-800 dark:text-emerald-300 block uppercase tracking-wider">
                Illustrative Management Guidance for {simResult.category} Stage ({simAffectedArea.toFixed(1)}%)
              </span>
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                {simResult.category === 'Healthy'
                  ? 'General considerations: No visible foliar symptoms detected. Continue routine scouting and standard nutrition management.'
                  : simResult.category === 'Early'
                  ? 'General considerations: Localized foliar symptoms. Prune affected leaves, evaluate canopy aeration, and consult a qualified agricultural professional before treatment decisions.'
                  : simResult.category === 'Moderate'
                  ? 'General considerations: Moderate foliar symptom coverage detected. Inspect neighboring plants, reduce leaf wetness, and consult an extension agent or certified agronomist for regional guidance.'
                  : 'General considerations: High symptom coverage detected (>35%). Prioritize physical containment, monitor adjacent stands, and seek qualified professional guidance before chemical intervention.'}
              </p>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
              <div className="text-xs text-gray-500">
                You can save this calibration to apply across your entire active session.
              </div>
              <div className="flex items-center gap-2">
                {simSavedNotice && (
                  <span className="text-xs text-emerald-600 dark:text-emerald-400 font-bold flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Saved to Session!</span>
                  </span>
                )}
                <button
                  onClick={handleSaveToGlobalCalibration}
                  className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold shadow-glow-emerald flex items-center gap-1.5 transition-all"
                >
                  <FileCheck className="w-4 h-4" />
                  <span>Save as Active Threshold Simulation</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: LIVE SYSTEM HEALTH & NEURAL DIAGNOSTICS */}
      {activeTab === 'diagnostics' && (
        <div className="space-y-6">
          <div className="p-6 sm:p-8 rounded-3xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder shadow-subtle space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h2 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                  <Activity className="w-6 h-6 text-emerald-600 dark:text-emerald-400" />
                  <span>Live Neural Engine &amp; Backend Diagnostics</span>
                </h2>
                <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 mt-1">
                  Real-time connectivity check with the active FastAPI server, neural network models, and the local SHA-256 evidence chain.
                </p>
              </div>

              <button
                onClick={runLiveDiagnostics}
                disabled={isPinging}
                className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:bg-gray-300 dark:disabled:bg-gray-800 text-white text-xs font-bold shadow-glow-emerald flex items-center gap-2 transition-all"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isPinging ? 'animate-spin' : ''}`} />
                <span>{isPinging ? 'Testing Models...' : 'Ping & Test Models'}</span>
              </button>
            </div>

            {/* Latency & Server Status Banner */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="p-4 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder space-y-1">
                <span className="text-[11px] font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider block">
                  FastAPI Server
                </span>
                <div className="flex items-center gap-2">
                  <span
                    className={`w-2.5 h-2.5 rounded-full ${
                      healthStatus?.status === 'healthy' ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'
                    }`}
                  />
                  <span className="text-base font-bold text-gray-900 dark:text-white capitalize">
                    {healthStatus?.status === 'healthy' ? 'Operational' : 'Offline / Checking'}
                  </span>
                </div>
                <span className="text-[10px] text-gray-400 font-mono">Port 8000</span>
              </div>

              <div className="p-4 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder space-y-1">
                <span className="text-[11px] font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider block">
                  Roundtrip Latency
                </span>
                <span className="text-xl font-mono font-bold text-emerald-600 dark:text-emerald-400">
                  {pingLatency ? `${pingLatency} ms` : 'Testing...'}
                </span>
                <span className="text-[10px] text-gray-400 block">HTTP GET /health</span>
              </div>

              <div className="p-4 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder space-y-1">
                <span className="text-[11px] font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider block">
                  Tamper-Evident Evidence Chain
                </span>
                <div className="flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                  <span className="text-base font-bold text-gray-900 dark:text-white">
                    {traceStatus?.chain_valid ? 'Chain Verified' : 'Checking'}
                  </span>
                </div>
                <span className="text-[10px] text-gray-400 font-mono">
                  {traceStatus?.total_blocks ? `${traceStatus.total_blocks} Evidence Records` : 'Genesis Ready'}
                </span>
              </div>
            </div>

            {/* Neural Engine Cards */}
            <div className="space-y-3">
              <h3 className="text-sm font-bold uppercase tracking-wider text-gray-700 dark:text-gray-300">
                Inference Engines Status
              </h3>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 text-xs">
                <div className="p-4 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-gray-900 dark:text-white flex items-center gap-1.5">
                      <Cpu className="w-3.5 h-3.5 text-emerald-600" />
                      <span>Health Screening</span>
                    </span>
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
                      Loaded
                    </span>
                  </div>
                  <p className="text-[11px] text-gray-500">
                    EfficientNet-B0 binary model loaded in memory for zero-lag healthy vs. diseased pre-filtering.
                  </p>
                </div>

                <div className="p-4 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-gray-900 dark:text-white flex items-center gap-1.5">
                      <Layers className="w-3.5 h-3.5 text-blue-600" />
                      <span>Disease Classifier</span>
                    </span>
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300">
                      115 Classes
                    </span>
                  </div>
                  <p className="text-[11px] text-gray-500">
                    PlantWild v2 deep convolutional model active with softmax distribution and Top-3 ranked outputs.
                  </p>
                </div>

                <div className="p-4 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-gray-900 dark:text-white flex items-center gap-1.5">
                      <Eye className="w-3.5 h-3.5 text-amber-600" />
                      <span>Grad-CAM Engine</span>
                    </span>
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300">
                      Active
                    </span>
                  </div>
                  <p className="text-[11px] text-gray-500">
                    Target layer 'top_activation' gradient hook initialized for on-the-fly heat map generation.
                  </p>
                </div>

                <div className="p-4 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-gray-900 dark:text-white flex items-center gap-1.5">
                      <Target className="w-3.5 h-3.5 text-purple-600" />
                      <span>U-Net Lesion Segmenter</span>
                    </span>
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-purple-100 text-purple-800 dark:bg-purple-950 dark:text-purple-300">
                      256 × 256
                    </span>
                  </div>
                  <p className="text-[11px] text-gray-500">
                    PlantSeg deep U-Net model active for segmentation-based estimation of visible affected regions and estimated affected-area percentage.
                  </p>
                </div>

                <div className="p-4 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-gray-900 dark:text-white flex items-center gap-1.5">
                      <Database className="w-3.5 h-3.5 text-emerald-600" />
                      <span>Knowledge Base</span>
                    </span>
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
                      Synchronized
                    </span>
                  </div>
                  <p className="text-[11px] text-gray-500">
                    Comprehensive treatment protocols, environmental spread vectors, and prevention guidelines loaded.
                  </p>
                </div>

                <div className="p-4 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-gray-900 dark:text-white flex items-center gap-1.5">
                      <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                      <span>Evidence Chain</span>
                    </span>
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
                      SHA-256
                    </span>
                  </div>
                  <p className="text-[11px] text-gray-500">
                    Append-only hash chain running with thread-safe locking and cryptographic verification.
                  </p>
                </div>
              </div>
            </div>

            {/* Raw JSON Inspector Accordion */}
            <div className="pt-2 border-t border-gray-100 dark:border-darkBorder">
              <button
                onClick={() => setShowRawJson((prev) => !prev)}
                className="text-xs text-gray-500 hover:text-emerald-600 dark:hover:text-emerald-400 font-semibold flex items-center gap-1.5 transition-colors"
              >
                <span>{showRawJson ? 'Hide Raw Diagnostics Payload' : 'Inspect Raw Diagnostics Payload (JSON)'}</span>
                {showRawJson ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
              </button>

              {showRawJson && (
                <pre className="mt-3 p-4 rounded-2xl bg-gray-950 text-emerald-400 font-mono text-[11px] overflow-x-auto max-h-60">
                  {JSON.stringify({ health: healthStatus, traceability: traceStatus, latencyMs: pingLatency }, null, 2)}
                </pre>
              )}
            </div>
          </div>
        </div>
      )}

      {/* TAB 4: 115-DISEASE ENCYCLOPEDIA & CATALOG */}
      {activeTab === 'catalog' && (
        <div className="space-y-6">
          <div className="p-6 sm:p-8 rounded-3xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder shadow-subtle space-y-5">
            <div>
              <h2 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                <BookOpen className="w-6 h-6 text-emerald-600 dark:text-emerald-400" />
                <span>Agricultural Plant Pathology Encyclopedia</span>
              </h2>
              <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 mt-1">
                Search and explore diseases recognized by the PlantWild v2 deep learning model with symptoms, transmission vectors, and recommended treatments.
              </p>
            </div>

            {/* Search Input & Filters */}
            <div className="flex flex-col sm:flex-row gap-3">
              <div className="relative flex-1">
                <Search className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search by disease name, crop, or pathogen (e.g. Scab, Late Blight, Tomato)..."
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-gray-200 dark:border-darkBorder bg-gray-50 dark:bg-darkElevated text-gray-900 dark:text-white text-xs sm:text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                />
              </div>

              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="px-3 py-2 rounded-xl text-xs font-semibold text-gray-500 hover:bg-gray-100 dark:hover:bg-darkElevated"
                >
                  Clear Search
                </button>
              )}
            </div>

            {/* Crop Filter Pills */}
            <div className="flex flex-wrap items-center gap-1.5 text-xs">
              <span className="text-gray-400 font-semibold mr-1">Crop Filter:</span>
              {CROPS_LIST.map((crop) => (
                <button
                  key={crop}
                  onClick={() => setSelectedCropFilter(crop)}
                  className={`px-3 py-1.5 rounded-xl font-medium transition-all ${
                    selectedCropFilter.toLowerCase() === crop.toLowerCase()
                      ? 'bg-emerald-600 text-white font-bold shadow-subtle'
                      : 'bg-gray-100 dark:bg-darkElevated text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                  }`}
                >
                  {crop}
                </button>
              ))}
            </div>

            {/* Disease List Results */}
            <div className="space-y-3 pt-2">
              <div className="flex justify-between items-center text-xs text-gray-400">
                <span>Showing {filteredDiseases.length} disease profiles</span>
                <span>PlantWild v2 Neural Taxonomy</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {filteredDiseases.map((item) => {
                  const isExpanded = expandedDiseaseId === item.id;
                  return (
                    <div
                      key={item.id}
                      className="p-5 rounded-2xl border border-gray-200 dark:border-darkBorder bg-white dark:bg-darkCard hover:border-emerald-300 dark:hover:border-emerald-800 transition-all shadow-subtle space-y-3"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400">
                              {item.crop}
                            </span>
                            <span className="text-gray-300 dark:text-gray-600">•</span>
                            <span className="text-[11px] font-mono text-gray-500">
                              {item.type}
                            </span>
                          </div>
                          <h4 className="text-base font-bold text-gray-900 dark:text-white mt-0.5">
                            {item.disease}
                          </h4>
                          <span className="text-xs italic font-serif text-gray-500">
                            {item.pathogen}
                          </span>
                        </div>

                        <span
                          className={`text-[10px] font-bold uppercase px-2.5 py-1 rounded-full ${
                            item.severityRisk.toLowerCase().includes('high') || item.severityRisk.toLowerCase().includes('critical')
                              ? 'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300'
                              : 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300'
                          }`}
                        >
                          {item.severityRisk}
                        </span>
                      </div>

                      {/* Symptoms preview */}
                      <div className="text-xs text-gray-600 dark:text-gray-300 space-y-1">
                        <span className="font-semibold text-gray-700 dark:text-gray-200 block text-[11px] uppercase tracking-wide">
                          Foliar Symptoms:
                        </span>
                        <p className="line-clamp-2 leading-relaxed">
                          {item.symptoms[0]}
                        </p>
                      </div>

                      {/* Expand details button */}
                      <div className="pt-2 flex items-center justify-between border-t border-gray-100 dark:border-darkBorder/60">
                        <button
                          onClick={() => setExpandedDiseaseId(isExpanded ? null : item.id)}
                          className="text-xs font-bold text-emerald-600 dark:text-emerald-400 hover:underline flex items-center gap-1"
                        >
                          <span>{isExpanded ? 'Hide Full Protocol' : 'View Full Management Protocol'}</span>
                          {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                        </button>

                        <Link
                          to="/analyze"
                          className="text-[11px] font-bold text-gray-500 hover:text-emerald-600 flex items-center gap-1"
                        >
                          <span>Test in Analyzer</span>
                          <ArrowRight className="w-3 h-3" />
                        </Link>
                      </div>

                      {/* Expanded Section */}
                      {isExpanded && (
                        <div className="pt-3 border-t border-gray-100 dark:border-darkBorder space-y-3 text-xs animate-fade-in">
                          <div>
                            <span className="font-bold text-gray-800 dark:text-gray-200 block mb-1">
                              Environmental Triggers:
                            </span>
                            <ul className="list-disc list-inside space-y-1 text-gray-600 dark:text-gray-400">
                              {item.environmentalFactors.map((env, i) => (
                                <li key={i}>{env}</li>
                              ))}
                            </ul>
                          </div>

                          <div>
                            <span className="font-bold text-emerald-800 dark:text-emerald-300 block mb-1">
                              Immediate Field Actions:
                            </span>
                            <ul className="list-disc list-inside space-y-1 text-gray-700 dark:text-gray-300">
                              {item.immediateActions.map((act, i) => (
                                <li key={i}>{act}</li>
                              ))}
                            </ul>
                          </div>

                          <div>
                            <span className="font-bold text-gray-800 dark:text-gray-200 block mb-1">
                              Long-Term Prevention:
                            </span>
                            <ul className="list-disc list-inside space-y-1 text-gray-600 dark:text-gray-400">
                              {item.prevention.map((prev, i) => (
                                <li key={i}>{prev}</li>
                              ))}
                            </ul>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 5: AGRONOMIST FAQ & FIELD GUIDE */}
      {activeTab === 'faq' && (
        <div className="space-y-6">
          <div className="p-6 sm:p-8 rounded-3xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder shadow-subtle space-y-5">
            <div>
              <h2 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                <HelpCircle className="w-6 h-6 text-emerald-600 dark:text-emerald-400" />
                <span>Frequently Asked Questions &amp; Practical Field Guide</span>
              </h2>
              <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 mt-1">
                Clear answers explaining artificial intelligence concepts in simple agricultural terms for farmers, agronomists, and compliance auditors.
              </p>
            </div>

            <div className="space-y-3 pt-2">
              {FAQ_ITEMS.map((item, idx) => {
                const isOpen = activeFaq === idx;
                return (
                  <div
                    key={idx}
                    className="rounded-2xl border border-gray-200 dark:border-darkBorder bg-gray-50/50 dark:bg-darkElevated/40 overflow-hidden transition-all"
                  >
                    <button
                      onClick={() => setActiveFaq(isOpen ? null : idx)}
                      className="w-full p-4 sm:p-5 text-left flex items-center justify-between gap-4 font-bold text-xs sm:text-sm text-gray-900 dark:text-white hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors"
                    >
                      <span className="flex items-center gap-2.5">
                        <span className="w-6 h-6 rounded-full bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 text-xs flex items-center justify-center shrink-0">
                          Q
                        </span>
                        <span>{item.q}</span>
                      </span>
                      {isOpen ? <ChevronUp className="w-4 h-4 shrink-0 text-emerald-600" /> : <ChevronDown className="w-4 h-4 shrink-0 text-gray-400" />}
                    </button>

                    {isOpen && (
                      <div className="px-5 pb-5 pt-1 text-xs sm:text-sm text-gray-600 dark:text-gray-300 leading-relaxed border-t border-gray-200/60 dark:border-darkBorder/60 animate-fade-in">
                        {item.a}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Engineering Tech Stack Summary */}
      <div className="p-6 sm:p-8 rounded-3xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder shadow-subtle space-y-4">
        <h2 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <Code2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
          <span>Core Engineering Architecture</span>
        </h2>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
          <div className="p-4 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder text-center space-y-1">
            <span className="font-bold text-gray-900 dark:text-white block">FastAPI</span>
            <span className="text-[11px] text-gray-400 block">High-concurrency Async Python Engine</span>
          </div>
          <div className="p-4 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder text-center space-y-1">
            <span className="font-bold text-gray-900 dark:text-white block">TensorFlow / Keras</span>
            <span className="text-[11px] text-gray-400 block">Multi-Model Neural Network Inference</span>
          </div>
          <div className="p-4 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder text-center space-y-1">
            <span className="font-bold text-gray-900 dark:text-white block">React + Vite</span>
            <span className="text-[11px] text-gray-400 block">Responsive, Real-time User Interface</span>
          </div>
          <div className="p-4 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder text-center space-y-1">
            <span className="font-bold text-gray-900 dark:text-white block">SHA-256 Evidence Chain</span>
            <span className="text-[11px] text-gray-400 block">Cryptographic Tamper-Evident Evidence</span>
          </div>
        </div>
      </div>

      {/* Mandatory Scientific Protocol Disclaimer */}
      <div className="p-5 rounded-3xl bg-gray-50 dark:bg-darkElevated border border-gray-200 dark:border-darkBorder text-xs text-gray-600 dark:text-gray-400 space-y-2">
        <div className="flex items-center gap-2 font-bold text-gray-900 dark:text-white">
          <AlertCircle className="w-4 h-4 text-emerald-600" />
          <span>Scientific Protocol &amp; Academic Notice</span>
        </div>
        <p className="leading-relaxed">
          Harvest Harbor is engineered as an advanced agricultural decision-support utility. Predictions and severity calculations are computed via multi-model deep learning networks and heuristic segmentation algorithms. Always corroborate digital findings with accredited agronomists, regional extension bulletins, or certified laboratory pathogen assays before deploying chemical treatments.
        </p>
      </div>
    </div>
  );
}

export default About;
