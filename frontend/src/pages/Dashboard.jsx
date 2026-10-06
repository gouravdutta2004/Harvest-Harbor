import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  ScanLine,
  FileText,
  ShieldCheck,
  Activity,
  Layers,
  Sparkles,
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Cpu,
  UserCheck,
  Camera,
  Target,
  HelpCircle,
  X,
  Info,
  ExternalLink,
} from 'lucide-react';
import { StatCard } from '../components/StatCard';
import { HashDisplay } from '../components/HashDisplay';
import { useBackendStatus } from '../hooks/useBackendStatus';
import { getTraceabilityChain, getTraceabilityStatus } from '../services/api';
import { formatDate } from '../utils/formatters';
import { InfoTooltip } from '../components/InfoTooltip';

export function Dashboard() {
  const { isOnline, healthData } = useBackendStatus();
  const [chainInfo, setChainInfo] = useState(null);
  const [recentBlocks, setRecentBlocks] = useState([]);
  const [stats, setStats] = useState({
    totalReports: 0,
    healthyCrops: 0,
    diseasedCrops: 0,
    verifiedBlocks: 0,
  });
  const [loadingChain, setLoadingChain] = useState(true);
  const [selectedWorkflowStep, setSelectedWorkflowStep] = useState(null);
  const [pipelineLearnMore, setPipelineLearnMore] = useState(null);

  useEffect(() => {
    let isMounted = true;
    async function loadData() {
      setLoadingChain(true);
      try {
        const [chainRes, statusRes] = await Promise.all([
          getTraceabilityChain(),
          getTraceabilityStatus(),
        ]);

        if (!isMounted) return;

        if (statusRes) {
          setChainInfo(statusRes);
        }

        if (chainRes && Array.isArray(chainRes.chain)) {
          const blocks = chainRes.chain;
          let healthyCount = 0;
          let diseasedCount = 0;
          let reportsCount = 0;

          blocks.forEach((block) => {
            if (block.block_type === 'evidence') {
              reportsCount += 1;
              const evData = block.data || block.evidence_data || {};
              const pred = (evData.health?.prediction || evData.report_snapshot?.health_prediction?.prediction || '').toLowerCase();
              if (pred === 'healthy') healthyCount += 1;
              if (pred === 'diseased') diseasedCount += 1;
            }
          });

          setStats({
            totalReports: reportsCount,
            healthyCrops: healthyCount,
            diseasedCrops: diseasedCount,
            verifiedBlocks: blocks.length,
          });

          setRecentBlocks([...blocks].reverse().slice(0, 5));
        }
      } catch (err) {
        if (isMounted) console.error('Failed to load dashboard metrics:', err);
      } finally {
        if (isMounted) setLoadingChain(false);
      }
    }

    loadData();
    return () => {
      isMounted = false;
    };
  }, []);

  const workflowSteps = [
    {
      num: 1,
      title: 'Upload Leaf Image',
      short: 'Snap or upload photo',
      desc: 'Capture a clear, well-lit image of the leaf blade. The client verifies resolution and minimum megapixels.',
      icon: Camera,
      link: '/analyze',
    },
    {
      num: 2,
      title: 'AI Checks Image & Crop',
      short: 'Botanical Host Gate',
      desc: 'Identifies the botanical crop species (Apple, Potato, Corn, etc.) and validates that the host matches known flora.',
      icon: Sparkles,
      link: '/help',
    },
    {
      num: 3,
      title: 'Disease Prediction',
      short: 'PlantWild v2 (115 Classes)',
      desc: 'Compares foliar visual patterns against learned pathological classes, calibrating probabilities via temperature scaling.',
      icon: Target,
      link: '/help',
    },
    {
      num: 4,
      title: 'Visual Explanation',
      short: 'Grad-CAM Attention Map',
      desc: 'Highlights the specific leaf blade regions that drove the model classification, ensuring the AI focuses on true lesions.',
      icon: Layers,
      link: '/help',
    },
    {
      num: 5,
      title: 'Affected Area Estimation',
      short: 'U-Net Lesion Segmentation',
      desc: 'Calculates the estimated percentage of detected leaf area covered by chlorotic or necrotic tissue.',
      icon: Target,
      link: '/help',
    },
    {
      num: 6,
      title: 'Severity Assessment',
      short: 'Standardized Staging',
      desc: 'Assigns project-defined severity tiers (Healthy, Early, Moderate, Severe) to aid agricultural scouting prioritization.',
      icon: AlertTriangle,
      link: '/help',
    },
    {
      num: 7,
      title: 'Human Review if Needed',
      short: 'Agronomist Escalation',
      desc: 'Flags low-confidence, borderline health states, or botanically incompatible predictions for agronomist confirmation.',
      icon: UserCheck,
      link: '/review-queue',
    },
    {
      num: 8,
      title: 'Evidence Record',
      short: 'Local SHA-256 Chain',
      desc: 'Records a tamper-evident audit record linked by SHA-256 hashes for agricultural traceability.',
      icon: ShieldCheck,
      link: '/traceability',
    },
  ];

  const pipelineStages = [
    {
      id: 'crop_id',
      title: 'Crop Identification',
      oneLiner: 'Identifies the most likely crop visible in the uploaded image.',
      detail:
        'The crop identification head uses deep convolutional transfer learning to classify plant taxonomy. By identifying whether the plant is an apple, potato, corn, or tomato, the system enforces biological host compatibility and prevents diagnosing diseases on plants that cannot biologically host them.',
      icon: Sparkles,
      color: 'text-blue-600 dark:text-blue-400',
      bg: 'bg-blue-50 dark:bg-blue-950/50 border-blue-200 dark:border-blue-800',
    },
    {
      id: 'disease_assess',
      title: 'Disease Assessment',
      oneLiner: 'Compares the image with learned disease patterns.',
      detail:
        'The PlantWild v2 multi-class classifier evaluates 115 distinct crop disease classes. Output logits can be adjusted using empirical temperature scaling to mitigate overconfident misclassifications.',
      icon: Target,
      color: 'text-amber-600 dark:text-amber-400',
      bg: 'bg-amber-50 dark:bg-amber-950/50 border-amber-200 dark:border-amber-800',
    },
    {
      id: 'explainability',
      title: 'Explainability (Grad-CAM)',
      oneLiner: 'Highlights image regions that contributed to the prediction.',
      detail:
        'Gradient-weighted Class Activation Mapping (Grad-CAM) projects heatmaps of final convolutional layer gradients. It visually answers "Why did the AI predict this?" so agronomists can verify the model focused on foliar pustules or blights rather than background artifacts.',
      icon: Layers,
      color: 'text-emerald-600 dark:text-emerald-400',
      bg: 'bg-emerald-50 dark:bg-emerald-950/50 border-emerald-200 dark:border-emerald-800',
    },
    {
      id: 'segmentation',
      title: 'Segmentation',
      oneLiner: 'Estimates the visible affected area using an image segmentation model.',
      detail:
        'A U-Net convolutional network trained on PlantSeg isolates foreground foliage from necrotic spots at 256×256 resolution. It computes pixel counts for leaf surface versus symptom area, providing an estimated percentage of foliar damage.',
      icon: Activity,
      color: 'text-purple-600 dark:text-purple-400',
      bg: 'bg-purple-50 dark:bg-purple-950/50 border-purple-200 dark:border-purple-800',
    },
    {
      id: 'severity',
      title: 'Severity Assessment',
      oneLiner: 'Assigns a project-defined severity category based on estimated affected area.',
      detail:
        'Estimated affected area is mapped to standardized tiers: Healthy (0%), Early (<15%), Moderate (15–35%), and Severe (≥35%). These thresholds are project-defined decision-support heuristics and should be calibrated for specific regional cultivars.',
      icon: AlertTriangle,
      color: 'text-rose-600 dark:text-rose-400',
      bg: 'bg-rose-50 dark:bg-rose-950/50 border-rose-200 dark:border-rose-800',
    },
    {
      id: 'human_review',
      title: 'Human Review',
      oneLiner: 'Flags cases where additional review may be useful.',
      detail:
        'Whenever confidence drops below 50%, crop identification is ambiguous, or a candidate disease violates botanical compatibility, the report is automatically queued for agronomist review. Decisions and notes are recorded for complete accountability.',
      icon: UserCheck,
      color: 'text-indigo-600 dark:text-indigo-400',
      bg: 'bg-indigo-50 dark:bg-indigo-950/50 border-indigo-200 dark:border-indigo-800',
    },
    {
      id: 'traceability',
      title: 'Traceability',
      oneLiner: 'Stores a tamper-evident record of the analysis.',
      detail:
        'Every assessment is hashed and appended to a local SHA-256 evidence chain. Each block references the previous hash, preventing retrospective tampering and providing verifiable provenance for farm audits and agricultural record-keeping.',
      icon: ShieldCheck,
      color: 'text-emerald-700 dark:text-emerald-300',
      bg: 'bg-emerald-50 dark:bg-emerald-950/50 border-emerald-200 dark:border-emerald-800',
    },
  ];

  return (
    <div className="space-y-10 animate-fade-in max-w-7xl mx-auto">
      {/* Top Welcome Section (Section 7) */}
      <div className="relative p-6 sm:p-10 rounded-3xl bg-gradient-to-br from-emerald-900 via-emerald-950 to-gray-950 text-white overflow-hidden shadow-premium border border-emerald-800/40">
        <div className="relative z-10 space-y-4 max-w-3xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-300 text-xs font-semibold backdrop-blur-sm border border-emerald-500/30">
            <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
            <span>AI-Assisted Precision Agriculture</span>
          </div>

          <div className="flex items-center gap-4 pt-1">
            <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-2xl overflow-hidden border border-emerald-400/40 shadow-glow-emerald bg-black/40 backdrop-blur-sm p-1 flex-shrink-0">
              <img src="/logo.png" alt="Harvest Harbor Logo" className="w-full h-full object-cover rounded-xl" />
            </div>
            <div className="space-y-1.5">
              <h1 className="text-3xl sm:text-4xl font-black tracking-tight text-white">
                Welcome to Harvest Harbor
              </h1>
              <p className="text-base sm:text-lg text-emerald-300 font-medium">
                AI for healthier crops, brighter tomorrows
              </p>
            </div>
          </div>

          <p className="text-xs sm:text-sm text-gray-300 leading-relaxed max-w-2xl">
            Upload field leaf photos for multi-branch neural disease assessment, Grad-CAM visual explainability, U-Net lesion segmentation, and tamper-evident cryptographic evidence recording.
          </p>

          {/* Quick Actions (Section 7) */}
          <div className="pt-2 flex flex-wrap items-center gap-3">
            <Link
              to="/analyze"
              className="px-5 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-gray-950 text-xs sm:text-sm font-bold shadow-glow-emerald flex items-center gap-2 transition-all transform active:scale-95"
            >
              <ScanLine className="w-4 h-4" />
              <span>Analyze a Crop</span>
            </Link>

            <Link
              to="/history"
              className="px-5 py-2.5 rounded-xl bg-white/10 hover:bg-white/20 text-white text-xs sm:text-sm font-semibold backdrop-blur-sm border border-white/10 flex items-center gap-2 transition-all"
            >
              <FileText className="w-4 h-4 text-emerald-300" />
              <span>View Previous Reports</span>
            </Link>

            <Link
              to="/review-queue"
              className="px-5 py-2.5 rounded-xl bg-white/10 hover:bg-white/20 text-white text-xs sm:text-sm font-semibold backdrop-blur-sm border border-white/10 flex items-center gap-2 transition-all"
            >
              <UserCheck className="w-4 h-4 text-emerald-300" />
              <span>Review Cases</span>
            </Link>
          </div>
        </div>

        {/* Ambient background decoration */}
        <div className="absolute -right-10 -bottom-10 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
      </div>

      {/* 3-Step Simple Guide for Everyday Users */}
      <div className="p-6 sm:p-8 rounded-3xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder shadow-subtle space-y-4">
        <div className="flex items-center justify-between pb-2 border-b border-gray-100 dark:border-darkBorder">
          <div>
            <h2 className="text-base sm:text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
              <span>How It Works in 3 Simple Steps</span>
            </h2>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Anyone can analyze plant health with zero training required.
            </p>
          </div>
          <Link
            to="/analyze"
            className="text-xs font-bold text-emerald-600 dark:text-emerald-400 hover:underline flex items-center gap-1"
          >
            <span>Try it now</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 rounded-2xl bg-emerald-50/60 dark:bg-emerald-950/30 border border-emerald-100 dark:border-emerald-900/60 space-y-2">
            <div className="w-9 h-9 rounded-xl bg-emerald-500 text-white font-black flex items-center justify-center text-sm shadow-subtle">
              1
            </div>
            <h3 className="font-bold text-gray-900 dark:text-white text-sm flex items-center gap-1.5">
              <Camera className="w-4 h-4 text-emerald-600" />
              <span>Snap or Upload a Photo</span>
            </h3>
            <p className="text-xs text-gray-600 dark:text-gray-300 leading-relaxed">
              Snap a clear photo of the leaf blade in natural daylight with the lesion in focus.
            </p>
          </div>

          <div className="p-4 rounded-2xl bg-blue-50/60 dark:bg-blue-950/30 border border-blue-100 dark:border-blue-900/60 space-y-2">
            <div className="w-9 h-9 rounded-xl bg-blue-500 text-white font-black flex items-center justify-center text-sm shadow-subtle">
              2
            </div>
            <h3 className="font-bold text-gray-900 dark:text-white text-sm flex items-center gap-1.5">
              <Sparkles className="w-4 h-4 text-blue-600" />
              <span>Instant AI Health Scan</span>
            </h3>
            <p className="text-xs text-gray-600 dark:text-gray-300 leading-relaxed">
              Our neural network validates the botanical crop species, screens health, and maps exact lesion spots.
            </p>
          </div>

          <div className="p-4 rounded-2xl bg-purple-50/60 dark:bg-purple-950/30 border border-purple-100 dark:border-purple-900/60 space-y-2">
            <div className="w-9 h-9 rounded-xl bg-purple-500 text-white font-black flex items-center justify-center text-sm shadow-subtle">
              3
            </div>
            <h3 className="font-bold text-gray-900 dark:text-white text-sm flex items-center gap-1.5">
              <FileText className="w-4 h-4 text-purple-600" />
              <span>Clear Guidance &amp; Audit</span>
            </h3>
            <p className="text-xs text-gray-600 dark:text-gray-300 leading-relaxed">
              Get plain-English next steps, recommended cultural practices, and a tamper-evident cryptographic record.
            </p>
          </div>
        </div>
      </div>

      {/* Top Statistics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
        <StatCard
          title="Total Reports"
          value={stats.totalReports}
          subtitle="Recorded in local evidence chain"
          icon={FileText}
          iconColor="text-blue-600 dark:text-blue-400"
          iconBg="bg-blue-50 dark:bg-blue-950/50"
          badge={stats.totalReports > 0 ? 'Active' : 'No records yet'}
          badgeType={stats.totalReports > 0 ? 'success' : 'neutral'}
        />

        <StatCard
          title="Healthy Crops"
          value={stats.healthyCrops}
          subtitle="Screened free of foliar disease"
          icon={CheckCircle2}
          iconColor="text-emerald-600 dark:text-emerald-400"
          iconBg="bg-emerald-50 dark:bg-emerald-950/50"
          badge="Verified"
          badgeType="success"
        />

        <StatCard
          title="Potential Diseases"
          value={stats.diseasedCrops}
          subtitle="Detected lesions & spots"
          icon={AlertTriangle}
          iconColor="text-rose-600 dark:text-rose-400"
          iconBg="bg-rose-50 dark:bg-rose-950/50"
          badge="Action Recommended"
          badgeType={stats.diseasedCrops > 0 ? 'danger' : 'neutral'}
        />

        <StatCard
          title="Evidence Blocks"
          value={stats.verifiedBlocks}
          subtitle="Local SHA-256 hash-linked chain"
          icon={ShieldCheck}
          iconColor="text-emerald-600 dark:text-emerald-400"
          iconBg="bg-emerald-50 dark:bg-emerald-950/50"
          badge={chainInfo?.chain_valid ? 'Chain Verified' : 'Verifying'}
          badgeType={chainInfo?.chain_valid ? 'success' : 'warning'}
        />
      </div>

      {/* 8-Step Interactive Workflow Visualization (Section 7) */}
      <div className="p-6 sm:p-8 rounded-3xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder shadow-subtle space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-gray-100 dark:border-darkBorder pb-4">
          <div>
            <h2 className="text-base sm:text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
              <Layers className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
              <span>Diagnostic Workflow (Click Any Step to Inspect)</span>
            </h2>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              The 8-step journey from raw leaf photo to tamper-evident cryptographic report.
            </p>
          </div>
          <span className="text-[11px] font-mono text-gray-400 bg-gray-100 dark:bg-darkElevated px-3 py-1 rounded-full w-fit">
            Interactive Flow
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2.5">
          {workflowSteps.map((step) => {
            const Icon = step.icon;
            const isSelected = selectedWorkflowStep?.num === step.num;
            return (
              <button
                key={step.num}
                type="button"
                onClick={() => setSelectedWorkflowStep(step)}
                className={`p-3 rounded-2xl border text-left transition-all flex flex-col justify-between space-y-2 group cursor-pointer ${
                  isSelected
                    ? 'bg-emerald-50 dark:bg-emerald-950/60 border-emerald-400 dark:border-emerald-600 shadow-subtle scale-105'
                    : 'bg-gray-50/70 dark:bg-darkElevated/50 border-gray-200/80 dark:border-darkBorder hover:border-emerald-300 dark:hover:border-emerald-700'
                }`}
              >
                <div className="flex items-center justify-between text-gray-400 group-hover:text-emerald-600 transition-colors">
                  <span className="font-mono text-[10px] font-black">
                    STEP {step.num}
                  </span>
                  <Icon className="w-3.5 h-3.5" />
                </div>
                <div>
                  <h4 className="text-[11px] font-bold text-gray-900 dark:text-white leading-tight">
                    {step.title}
                  </h4>
                  <span className="text-[9px] text-gray-500 dark:text-gray-400 block mt-0.5 truncate">
                    {step.short}
                  </span>
                </div>
              </button>
            );
          })}
        </div>

        {/* Selected Workflow Step Detail Card */}
        {selectedWorkflowStep && (
          <div className="p-4 sm:p-5 rounded-2xl bg-emerald-50/60 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-xs space-y-3 animate-fade-in">
            <div className="flex items-center justify-between">
              <span className="font-bold text-emerald-900 dark:text-emerald-200 text-sm flex items-center gap-2">
                <span>Step {selectedWorkflowStep.num}: {selectedWorkflowStep.title}</span>
              </span>
              <button
                type="button"
                onClick={() => setSelectedWorkflowStep(null)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <p className="text-gray-700 dark:text-gray-300 leading-relaxed text-xs">
              {selectedWorkflowStep.desc}
            </p>
            <div className="pt-1">
              <Link
                to={selectedWorkflowStep.link}
                className="text-xs font-bold text-emerald-700 dark:text-emerald-400 hover:underline inline-flex items-center gap-1"
              >
                <span>Go to relevant page</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        )}
      </div>

      {/* DASHBOARD EDUCATION SECTION — How Harvest Harbor Works (Section 8) */}
      <div className="p-6 sm:p-8 rounded-3xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder shadow-subtle space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-gray-100 dark:border-darkBorder pb-4">
          <div>
            <h2 className="text-base sm:text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
              <span>How Harvest Harbor Works</span>
            </h2>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              An illustrated multi-branch scientific architecture designed for transparent decision support.
            </p>
          </div>
          <Link
            to="/about"
            className="text-xs font-bold text-emerald-600 dark:text-emerald-400 hover:underline flex items-center gap-1"
          >
            <span>Full Research Details</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {/* Illustrated Pipeline Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {pipelineStages.map((stage) => {
            const Icon = stage.icon;
            return (
              <div
                key={stage.id}
                className={`p-5 rounded-2xl border shadow-subtle space-y-3 bg-white dark:bg-darkCard ${stage.bg} flex flex-col justify-between`}
              >
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className={`p-2 rounded-xl bg-white dark:bg-darkElevated ${stage.color}`}>
                      <Icon className="w-4 h-4" />
                    </div>
                    <button
                      type="button"
                      onClick={() => setPipelineLearnMore(stage)}
                      className="text-[11px] font-bold text-emerald-700 dark:text-emerald-400 hover:underline flex items-center gap-1"
                    >
                      <span>Learn more</span>
                      <ArrowRight className="w-3 h-3" />
                    </button>
                  </div>
                  <h3 className="font-bold text-xs sm:text-sm text-gray-900 dark:text-white">
                    {stage.title}
                  </h3>
                  <p className="text-xs text-gray-600 dark:text-gray-400 leading-relaxed">
                    {stage.oneLiner}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Learn More Modal for Pipeline Stages */}
      {pipelineLearnMore && (
        <div
          className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4"
          onClick={() => setPipelineLearnMore(null)}
        >
          <div
            className="relative max-w-lg w-full bg-white dark:bg-darkCard rounded-3xl p-6 sm:p-8 shadow-2xl border border-gray-200 dark:border-darkBorder space-y-4 text-xs animate-fade-in"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-gray-100 dark:border-darkBorder pb-3">
              <div className="flex items-center gap-2">
                <div className={`p-2 rounded-xl bg-gray-50 dark:bg-darkElevated ${pipelineLearnMore.color}`}>
                  <pipelineLearnMore.icon className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-sm text-gray-900 dark:text-white">
                    {pipelineLearnMore.title}
                  </h3>
                  <span className="text-[10px] text-gray-400 uppercase font-mono">Scientific Deep-Dive</span>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setPipelineLearnMore(null)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-xs text-gray-700 dark:text-gray-300 leading-relaxed">
              {pipelineLearnMore.detail}
            </p>

            <div className="p-3 rounded-xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder text-[11px] text-gray-500">
              <strong>Ethical Notice:</strong> All metrics produced by this stage are decision-support estimates and should be confirmed with certified agronomists prior to chemical treatment.
            </div>

            <div className="flex justify-end pt-2">
              <button
                type="button"
                onClick={() => setPipelineLearnMore(null)}
                className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs"
              >
                Got it
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Recent Evidence Blocks Preview */}
      {recentBlocks.length > 0 && (
        <div className="p-6 sm:p-8 rounded-3xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder shadow-subtle space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base sm:text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
                <Clock className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                <span>Recent Evidence Chain Records</span>
              </h2>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Latest tamper-evident diagnostic records written to the SHA-256 chain.
              </p>
            </div>
            <Link
              to="/history"
              className="text-xs font-bold text-emerald-600 dark:text-emerald-400 hover:underline flex items-center gap-1"
            >
              <span>View All History</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="space-y-2">
            {recentBlocks.map((block) => {
              const data = block.data || block.evidence_data || {};
              const snap = data.report_snapshot || {};
              const pred = (data.health?.prediction || snap.health_prediction?.prediction || '').toLowerCase();
              const crop = data.crop?.prediction || snap.crop_prediction?.prediction || snap.crop_analysis?.prediction;
              const disease = data.disease?.prediction || snap.disease_analysis?.prediction;
              const isHealthy = pred === 'healthy';

              return (
                <div
                  key={block.block_index !== undefined ? block.block_index : (block.current_hash || block.hash)}
                  className="p-3.5 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs"
                >
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-xs font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/60 px-2 py-1 rounded-lg">
                      #{block.block_index}
                    </span>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-gray-900 dark:text-white font-mono">
                          {block.report_id || data.report_id || 'Evidence Block'}
                        </span>
                        {crop && (
                          <span className="text-[10px] text-gray-500 dark:text-gray-400 capitalize bg-white dark:bg-darkCard px-2 py-0.5 rounded-md border border-gray-200/60 dark:border-darkBorder font-medium">
                            {crop}
                          </span>
                        )}
                      </div>
                      <span className="text-[10px] text-gray-400 font-mono">
                        {formatDate(block.timestamp, { includeTime: true })}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    {pred && (
                      <span
                        className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                          isHealthy
                            ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300'
                            : 'bg-rose-50 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300'
                        }`}
                      >
                        {isHealthy ? <CheckCircle2 className="w-3 h-3 text-emerald-600" /> : <AlertTriangle className="w-3 h-3 text-rose-600" />}
                        <span className="capitalize">{isHealthy ? 'Healthy Leaf' : (disease ? disease.replace(/_/g, ' ') : 'Attention Needed')}</span>
                      </span>
                    )}
                    <span className="text-[11px] font-mono text-gray-400 truncate max-w-[120px] hidden md:inline">
                      {(block.current_hash || block.hash)?.substring(0, 10)}...
                    </span>
                    <Link
                      to={`/report?id=${encodeURIComponent(block.report_id || data.report_id || '')}`}
                      className="px-3 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white dark:bg-darkCard dark:hover:bg-emerald-950/60 border border-transparent dark:border-darkBorder text-xs font-semibold hover:border-emerald-500 transition-all shadow-subtle"
                    >
                      View Report
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

export default Dashboard;
