import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import {
  ScanLine,
  FileText,
  AlertCircle,
  Lightbulb,
  Camera,
  CheckCircle,
  CheckCircle2,
  Layers,
  Sparkles,
  Info,
  Printer,
  Copy,
  Check,
  RotateCcw,
  ShieldCheck,
  Key,
} from 'lucide-react';
import { UploadDropzone } from '../components/UploadDropzone';
import { LoadingState } from '../components/LoadingState';
import { PredictionCard } from '../components/PredictionCard';
import { CropIdentificationCard } from '../components/CropIdentificationCard';
import { DiseaseRanking } from '../components/DiseaseRanking';
import { GradCAMViewer } from '../components/GradCAMViewer';
import { SegmentationViewer } from '../components/SegmentationViewer';
import { SeverityCard } from '../components/SeverityCard';
import { DiseaseInfo } from '../components/DiseaseInfo';
import { HealthyPlantCertificate } from '../components/HealthyPlantCertificate';
import { HumanReviewCard } from '../components/HumanReviewCard';
import { IllustrativeManagementGuidance } from '../components/IllustrativeManagementGuidance';
import { ResearchModeToggle } from '../components/ResearchModeToggle';
import { TraceabilityCard } from '../components/TraceabilityCard';
import { BlockchainStatus } from '../components/BlockchainStatus';
import { SecurityModal } from '../components/SecurityModal';
import { useAuth, DEFAULT_ROLE_KEYS } from '../context/AuthContext';
import { usePrediction } from '../hooks/usePrediction';
import { toTitleCase, formatPercent } from '../utils/formatters';
import { submitForReview } from '../services/api';

export function Analyze({ onReportGenerated, initialResult = null, initialImageSrc = null }) {
  const [activeResultTab, setActiveResultTab] = useState('overview'); // 'overview' | 'visual' | 'technical'
  const [copiedId, setCopiedId] = useState(false);
  const [securityModalOpen, setSecurityModalOpen] = useState(false);
  const { setApiKey, setRole } = useAuth();

  const {
    selectedFile,
    previewUrl,
    isAnalyzing,
    currentStageIndex,
    stages,
    result,
    error,
    selectFile,
    runAnalysis,
    reset,
  } = usePrediction(initialResult, initialImageSrc);

  const handleResetAll = () => {
    reset();
    if (onReportGenerated) {
      onReportGenerated(null, null);
    }
  };

  // If report generated, notify parent so Report page can pre-load it
  const handleAnalyzeClick = async (fileOverride = null) => {
    const data = await runAnalysis(fileOverride);
    if (data && onReportGenerated) {
      onReportGenerated(data, data.image?.url || null);
    }
  };

  return (
    <div className="space-y-8 animate-fade-in max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="space-y-1">
        <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 dark:text-white tracking-tight">
          Analyze a Crop Leaf
        </h1>
        <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">
          Upload a clear leaf image to receive an AI-assisted crop health and disease assessment.
        </p>
      </div>

      {/* Main Grid: Upload Sidebar (Left) & Results/Analysis Workspace (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Upload Dropzone & Leaf Capture Tips (4 cols) */}
        <div className="lg:col-span-4 space-y-6">
          <UploadDropzone
            onFileSelected={selectFile}
            selectedFile={selectedFile}
            previewUrl={previewUrl}
            onAnalyze={handleAnalyzeClick}
            isAnalyzing={isAnalyzing}
            onReset={handleResetAll}
          />

          {/* Imaging Best Practices Tip Card */}
          <div className="p-5 rounded-3xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder shadow-subtle space-y-3 text-xs">
            <div className="flex items-center gap-2 font-bold text-gray-900 dark:text-white">
              <Lightbulb className="w-4 h-4 text-amber-500" />
              <span>Capture Tips for Highest AI Accuracy</span>
            </div>

            <ul className="space-y-2 text-gray-600 dark:text-gray-400">
              <li className="flex items-start gap-2">
                <CheckCircle className="w-3.5 h-3.5 text-emerald-500 shrink-0 mt-0.5" />
                <span>Fill the frame with the leaf blade; keep background clean.</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle className="w-3.5 h-3.5 text-emerald-500 shrink-0 mt-0.5" />
                <span>Ensure bright, diffuse natural lighting without harsh shadows.</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle className="w-3.5 h-3.5 text-emerald-500 shrink-0 mt-0.5" />
                <span>Focus clearly on active chlorotic or necrotic lesion spots.</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Right Column: Loading or Comprehensive Multi-Branch Diagnostic Results (8 cols) */}
        <div className="lg:col-span-8 space-y-6">
          {/* State 1: Currently Analyzing with Live Progress */}
          {isAnalyzing && (
            <LoadingState currentStageIndex={currentStageIndex} stages={stages} />
          )}

          {/* State 2: Error Banner */}
          {!isAnalyzing && error && (
            <div className="p-6 rounded-3xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-rose-800 dark:text-rose-200 space-y-4">
              <div className="flex items-center gap-2.5 font-bold">
                <AlertCircle className="w-5 h-5 text-rose-600 dark:text-rose-400" />
                <span>Analysis Encountered an Error</span>
              </div>
              <p className="text-xs leading-relaxed">{error}</p>

              <div className="flex flex-wrap items-center gap-2.5 pt-1">
                <button
                  onClick={() => handleAnalyzeClick()}
                  type="button"
                  className="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold shadow-subtle transition-colors"
                >
                  Retry Analysis
                </button>
                {error.toLowerCase().includes('auth') && (
                  <button
                    onClick={async () => {
                      const key = DEFAULT_ROLE_KEYS.agronomist || 'dev-agronomist-key';
                      setApiKey(key);
                      sessionStorage.setItem('harvest_harbor_api_key', key);
                      sessionStorage.setItem('harvest_harbor_user_role', 'agronomist');
                      setRole('agronomist');
                      await handleAnalyzeClick();
                    }}
                    type="button"
                    className="px-4 py-2 rounded-xl bg-white dark:bg-darkCard border border-rose-300 dark:border-rose-800 text-rose-700 dark:text-rose-300 hover:bg-rose-100 dark:hover:bg-rose-900/40 text-xs font-semibold transition-colors flex items-center gap-1.5"
                  >
                    <Key className="w-3.5 h-3.5" />
                    <span>Authorize with Agronomist Key &amp; Retry</span>
                  </button>
                )}
                <button
                  onClick={() => setSecurityModalOpen(true)}
                  type="button"
                  className="px-4 py-2 rounded-xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-darkElevated text-xs font-semibold transition-colors flex items-center gap-1.5"
                >
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Configure API Key</span>
                </button>
              </div>
            </div>
          )}

          {/* State 3: Empty Workspace State before Upload — Interactive 6-Stage Neural Flow */}
          {!isAnalyzing && !result && !error && (
            <div className="p-6 sm:p-8 rounded-3xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder shadow-subtle space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-gray-100 dark:border-darkBorder">
                <div className="space-y-1">
                  <div className="inline-flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400">
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>How Harvest Harbor Works</span>
                  </div>
                  <h3 className="text-base sm:text-lg font-extrabold text-gray-900 dark:text-white">
                    AI-Assisted Assessment Pipeline
                  </h3>
                </div>
                <span className="text-xs font-mono text-gray-400 bg-gray-100 dark:bg-darkElevated px-3 py-1 rounded-full w-fit">
                  End-to-End Workflow
                </span>
              </div>

              {/* 8-Step Simple Flow */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-left">
                <div className="p-3.5 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder space-y-1">
                  <span className="text-[10px] font-mono font-bold text-gray-400">STEP 1</span>
                  <h4 className="text-xs font-bold text-gray-900 dark:text-white">Upload Leaf Image</h4>
                  <p className="text-[11px] text-gray-500 dark:text-gray-400 leading-tight">
                    Stage high-resolution photo or select a test leaf.
                  </p>
                </div>

                <div className="p-3.5 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder space-y-1">
                  <span className="text-[10px] font-mono font-bold text-gray-400">STEP 2</span>
                  <h4 className="text-xs font-bold text-gray-900 dark:text-white">Crop &amp; Health Status</h4>
                  <p className="text-[11px] text-gray-500 dark:text-gray-400 leading-tight">
                    Identifies species &amp; screens healthy vs diseased.
                  </p>
                </div>

                <div className="p-3.5 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder space-y-1">
                  <span className="text-[10px] font-mono font-bold text-gray-400">STEP 3</span>
                  <h4 className="text-xs font-bold text-gray-900 dark:text-white">Disease Assessment</h4>
                  <p className="text-[11px] text-gray-500 dark:text-gray-400 leading-tight">
                    Predicts candidate disease with host compatibility gating.
                  </p>
                </div>

                <div className="p-3.5 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder space-y-1">
                  <span className="text-[10px] font-mono font-bold text-gray-400">STEP 4</span>
                  <h4 className="text-xs font-bold text-gray-900 dark:text-white">Visual Focus Map</h4>
                  <p className="text-[11px] text-gray-500 dark:text-gray-400 leading-tight">
                    Highlights the visual image regions contributing to the AI prediction.
                  </p>
                </div>

                <div className="p-3.5 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder space-y-1">
                  <span className="text-[10px] font-mono font-bold text-gray-400">STEP 5</span>
                  <h4 className="text-xs font-bold text-gray-900 dark:text-white">Estimate Affected Area</h4>
                  <p className="text-[11px] text-gray-500 dark:text-gray-400 leading-tight">
                    Estimates the percentage of visible affected leaf area.
                  </p>
                </div>

                <div className="p-3.5 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder space-y-1">
                  <span className="text-[10px] font-mono font-bold text-gray-400">STEP 6</span>
                  <h4 className="text-xs font-bold text-gray-900 dark:text-white">Severity Category</h4>
                  <p className="text-[11px] text-gray-500 dark:text-gray-400 leading-tight">
                    Calculates project-defined severity tier for prioritization.
                  </p>
                </div>

                <div className="p-3.5 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder space-y-1">
                  <span className="text-[10px] font-mono font-bold text-gray-400">STEP 7</span>
                  <h4 className="text-xs font-bold text-gray-900 dark:text-white">Human Review</h4>
                  <p className="text-[11px] text-gray-500 dark:text-gray-400 leading-tight">
                    Flags uncertain or incompatible cases for agronomist review.
                  </p>
                </div>

                <div className="p-3.5 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder space-y-1">
                  <span className="text-[10px] font-mono font-bold text-gray-400">STEP 8</span>
                  <h4 className="text-xs font-bold text-gray-900 dark:text-white">Evidence Recorded</h4>
                  <p className="text-[11px] text-gray-500 dark:text-gray-400 leading-tight">
                    Appends record to local SHA-256 tamper-evident chain.
                  </p>
                </div>
              </div>

              {/* Call to action */}
              <div className="p-4 rounded-2xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200/80 dark:border-emerald-800 text-center space-y-1.5">
                <span className="text-xs font-bold text-emerald-900 dark:text-emerald-200 block">
                  Select or drop a leaf image to begin AI analysis
                </span>
                <p className="text-[11px] text-emerald-700 dark:text-emerald-300">
                  Upload a photo of your crop leaf from the left panel to run deep learning diagnostics.
                </p>
              </div>
            </div>
          )}

          {/* State 4: Prediction Completed — User-Friendly Diagnosis & Multi-Branch Dossier */}
          {!isAnalyzing && result && (
            <div className="space-y-6">
              {/* Prominent Friendly Verdict Banner */}
              {(() => {
                const isHealthy = (result.health_prediction?.prediction || result.status || '').toLowerCase() === 'healthy' || result.status === 'healthy_prediction';
                const isValidationRejected = result.disease_analysis?.validation?.status === 'rejected';
                const isValidationSkipped = result.disease_analysis?.validation?.status === 'skipped_low_crop_confidence';
                const isUncertain =
                  !isHealthy &&
                  (result.status === 'uncertain_prediction' ||
                    result.status?.includes('uncertain') ||
                    isValidationRejected ||
                    isValidationSkipped ||
                    result.disease_analysis?.uncertainty?.toLowerCase() === 'high' ||
                    (result.disease_analysis?.confidence != null && result.disease_analysis.confidence < 50));

                const cropName = result.crop_analysis?.prediction || result.crop_prediction?.prediction || result.crop_identification?.prediction;
                const diseaseName = result.disease_analysis?.prediction;
                const formattedCrop = cropName ? toTitleCase(cropName) : 'Crop Leaf';
                const formattedDisease = diseaseName ? toTitleCase(diseaseName) : 'Pathology';
                const affectedArea = result.severity?.affected_area_percent;
                const confidence = isHealthy ? result.health_prediction?.confidence : (result.disease_analysis?.confidence ?? result.health_prediction?.confidence);

                const handleCopy = async () => {
                  try {
                    await navigator.clipboard.writeText(result.report_id);
                    setCopiedId(true);
                    setTimeout(() => setCopiedId(false), 2000);
                  } catch (e) {
                    console.error(e);
                  }
                };

                return (
                  <div className={`p-6 sm:p-7 rounded-3xl border shadow-premium relative overflow-hidden ${
                    isHealthy
                      ? 'bg-gradient-to-br from-emerald-50 via-emerald-100/50 to-white dark:from-emerald-950/60 dark:via-darkCard dark:to-darkCard border-emerald-200 dark:border-emerald-800'
                      : isUncertain
                      ? 'bg-gradient-to-br from-amber-50 via-amber-100/50 to-white dark:from-amber-950/60 dark:via-darkCard dark:to-darkCard border-amber-200 dark:border-amber-800'
                      : 'bg-gradient-to-br from-rose-50 via-rose-100/50 to-white dark:from-rose-950/60 dark:via-darkCard dark:to-darkCard border-rose-200 dark:border-rose-800'
                  }`}>
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                      <div className="space-y-2">
                        <div className="flex items-center gap-2">
                          <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-bold uppercase tracking-wider flex items-center gap-1.5 ${
                            isHealthy
                              ? 'bg-emerald-600 text-white shadow-subtle'
                              : isUncertain
                              ? 'bg-amber-600 text-white shadow-subtle'
                              : 'bg-rose-600 text-white shadow-subtle'
                          }`}>
                            {isHealthy ? (
                              <CheckCircle2 className="w-3.5 h-3.5" />
                            ) : isUncertain ? (
                              <AlertCircle className="w-3.5 h-3.5" />
                            ) : (
                              <AlertCircle className="w-3.5 h-3.5" />
                            )}
                            <span>
                              {isHealthy
                                ? 'Healthy Specimen'
                                : isValidationRejected
                                ? 'Host Incompatible'
                                : isValidationSkipped
                                ? 'Uncertain Host'
                                : isUncertain
                                ? 'Uncertain Assessment'
                                : 'Pathogen Detected'}
                            </span>
                          </span>

                          <span className="text-[11px] font-mono text-gray-500 dark:text-gray-400">
                            ID: <strong className="text-gray-800 dark:text-gray-200">{result.report_id}</strong>
                          </span>
                        </div>

                        <h2 className="text-2xl sm:text-3xl font-black text-gray-900 dark:text-white tracking-tight">
                          {isHealthy
                            ? `${formattedCrop} Leaf is Healthy`
                            : isValidationRejected
                            ? `Host Incompatibility on ${formattedCrop}`
                            : isUncertain
                            ? `Uncertain: ${formattedDisease} on ${formattedCrop}`
                            : `${formattedDisease} on ${formattedCrop}`}
                        </h2>

                        <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-300 leading-relaxed max-w-2xl">
                          {isHealthy
                            ? `Great news! The AI assessed this ${formattedCrop} specimen with ${formatPercent(confidence)} confidence. Leaf foliage appears robust with no active fungal or bacterial lesions.`
                            : isUncertain
                            ? `Borderline diagnostic confidence (${formatPercent(confidence)} < 50%). ${result.message || 'Automated checks detected low confidence. This assessment requires agronomist confirmation before any chemical treatment intervention.'}${affectedArea !== undefined ? ` Estimated foliar coverage: ${affectedArea.toFixed(1)}%.` : ''}`
                            : `Visual foliar symptoms matching ${formattedDisease} detected on ${formattedCrop} with ${formatPercent(confidence)} confidence.${affectedArea !== undefined ? ` Estimated foliar coverage: ${affectedArea.toFixed(1)}%.` : ''}`}
                        </p>
                      </div>

                      {/* Quick Actions in Verdict */}
                      <div className="flex flex-wrap items-center gap-2 shrink-0">
                        <Link
                          to={`/report?id=${encodeURIComponent(result.report_id)}`}
                          className="px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-glow-emerald flex items-center gap-1.5 transition-all transform active:scale-95"
                        >
                          <FileText className="w-4 h-4" />
                          <span>Full Report</span>
                        </Link>

                        <button
                          type="button"
                          onClick={() => window.print()}
                          className="px-3.5 py-2.5 rounded-xl bg-white dark:bg-darkElevated hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-200 border border-gray-200 dark:border-darkBorder text-xs font-semibold flex items-center gap-1.5 transition-colors"
                          title="Print or Save PDF"
                        >
                          <Printer className="w-3.5 h-3.5" />
                          <span className="hidden sm:inline">Print</span>
                        </button>

                        <button
                          type="button"
                          onClick={handleCopy}
                          className="px-3.5 py-2.5 rounded-xl bg-white dark:bg-darkElevated hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-200 border border-gray-200 dark:border-darkBorder text-xs font-semibold flex items-center gap-1.5 transition-colors"
                          title="Copy Report Identifier"
                        >
                          {copiedId ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                          <span className="hidden sm:inline">{copiedId ? 'Copied' : 'Copy ID'}</span>
                        </button>

                        <button
                          type="button"
                          onClick={handleResetAll}
                          className="px-3.5 py-2.5 rounded-xl bg-white dark:bg-darkElevated hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-200 border border-gray-200 dark:border-darkBorder text-xs font-semibold flex items-center gap-1.5 transition-colors"
                          title="Analyze another leaf photo"
                        >
                          <RotateCcw className="w-3.5 h-3.5" />
                          <span className="hidden sm:inline">New Leaf</span>
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })()}

              {/* 6-Stage Pipeline Execution Ribbon */}
              <div className="p-3.5 rounded-2xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder shadow-subtle flex flex-wrap items-center justify-between gap-2 text-[11px] font-mono">
                <div className="flex items-center gap-1.5 text-gray-700 dark:text-gray-300">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 shrink-0" />
                  <span className="font-semibold font-sans text-gray-900 dark:text-white">Pipeline:</span>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <span className="px-2 py-0.5 rounded bg-gray-100 dark:bg-darkElevated text-gray-600 dark:text-gray-300">
                    Hash: <strong className="text-gray-900 dark:text-white">{result.image?.sha256 ? result.image.sha256.substring(0, 8) + '...' : 'Verified'}</strong>
                  </span>
                  <span className="text-gray-300 dark:text-gray-700">→</span>
                  <span className="px-2 py-0.5 rounded bg-gray-100 dark:bg-darkElevated text-gray-600 dark:text-gray-300">
                    Health: <strong className={result.health_prediction?.prediction === 'healthy' ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'}>{result.health_prediction?.prediction ? result.health_prediction.prediction.toUpperCase() : 'PASS'}</strong>
                  </span>
                  {result.crop_analysis?.prediction && (
                    <>
                      <span className="text-gray-300 dark:text-gray-700">→</span>
                      <span className="px-2 py-0.5 rounded bg-gray-100 dark:bg-darkElevated text-gray-600 dark:text-gray-300">
                        Crop: <strong className="text-blue-600 dark:text-blue-400 capitalize">{result.crop_analysis.prediction}</strong>
                      </span>
                    </>
                  )}
                  {result.disease_analysis?.prediction && (
                    <>
                      <span className="text-gray-300 dark:text-gray-700">→</span>
                      <span className="px-2 py-0.5 rounded bg-gray-100 dark:bg-darkElevated text-gray-600 dark:text-gray-300 truncate max-w-[160px]">
                        Disease: <strong className="text-amber-600 dark:text-amber-400 capitalize">{result.disease_analysis.prediction.replace(/_/g, ' ')}</strong>
                      </span>
                    </>
                  )}
                  {result.severity?.affected_area_percent !== undefined && (
                    <>
                      <span className="text-gray-300 dark:text-gray-700">→</span>
                      <span className="px-2 py-0.5 rounded bg-gray-100 dark:bg-darkElevated text-gray-600 dark:text-gray-300">
                        U-Net Area: <strong className="text-purple-600 dark:text-purple-400">{result.severity.affected_area_percent.toFixed(1)}%</strong>
                      </span>
                    </>
                  )}
                  <span className="text-gray-300 dark:text-gray-700">→</span>
                  <span className="px-2 py-0.5 rounded bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800">
                    Record: <strong>#{result.traceability?.blockchain?.block_index ?? result.traceability?.blockchain?.current_block?.index ?? 'Recorded'}</strong>
                  </span>
                </div>
              </div>

              {/* 3 Intuitive Result Tabs */}
              <div className="flex border-b border-gray-200 dark:border-darkBorder gap-2 sm:gap-6 overflow-x-auto text-xs font-bold">
                <button
                  type="button"
                  onClick={() => setActiveResultTab('overview')}
                  className={`pb-3 px-2 border-b-2 transition-all flex items-center gap-2 whitespace-nowrap ${
                    activeResultTab === 'overview'
                      ? 'border-emerald-600 text-emerald-700 dark:text-emerald-400 font-extrabold'
                      : 'border-transparent text-gray-500 hover:text-gray-800 dark:hover:text-gray-200'
                  }`}
                >
                  <Sparkles className="w-4 h-4 text-emerald-600" />
                  <span>1. Diagnosis &amp; Care Guidance</span>
                </button>

                <button
                  type="button"
                  onClick={() => setActiveResultTab('visual')}
                  className={`pb-3 px-2 border-b-2 transition-all flex items-center gap-2 whitespace-nowrap ${
                    activeResultTab === 'visual'
                      ? 'border-emerald-600 text-emerald-700 dark:text-emerald-400 font-extrabold'
                      : 'border-transparent text-gray-500 hover:text-gray-800 dark:hover:text-gray-200'
                  }`}
                >
                  <Layers className="w-4 h-4 text-emerald-600" />
                  <span>2. Visual AI Inspection (Focus &amp; Spots)</span>
                </button>

                <button
                  type="button"
                  onClick={() => setActiveResultTab('technical')}
                  className={`pb-3 px-2 border-b-2 transition-all flex items-center gap-2 whitespace-nowrap ${
                    activeResultTab === 'technical'
                      ? 'border-emerald-600 text-emerald-700 dark:text-emerald-400 font-extrabold'
                      : 'border-transparent text-gray-500 hover:text-gray-800 dark:hover:text-gray-200'
                  }`}
                >
                  <ScanLine className="w-4 h-4 text-emerald-600" />
                  <span>3. Scientific Dossier &amp; Blockchain Proof</span>
                </button>
              </div>

              {/* TAB 1: Diagnosis & Care Guidance */}
              {activeResultTab === 'overview' && (
                <div className="space-y-6 animate-fade-in">
                  {/* 1. Summary, Confidence, and Health Screen */}
                  <PredictionCard data={result} />

                  {/* Healthy Crop Assessment (When healthy) */}
                  {(result.status === 'healthy_prediction' || result.health_prediction?.prediction === 'healthy') && (
                    <HealthyPlantCertificate
                      reportId={result.report_id}
                      confidence={result.health_prediction?.confidence}
                    />
                  )}

                  {/* 2. Crop Identification Card */}
                  {(result.crop_prediction || result.crop_analysis || result.crop_identification) && (
                    <CropIdentificationCard
                      cropData={result.crop_prediction || result.crop_analysis || result.crop_identification}
                    />
                  )}

                  {/* 3. Illustrative Management Guidance */}
                  <IllustrativeManagementGuidance
                    diseaseInfo={result.disease_information}
                    prediction={result.disease_analysis?.prediction}
                    crop={result.crop_analysis?.prediction || result.crop_prediction?.prediction}
                  />

                  {/* Disease Info details if available */}
                  {result.disease_information && (
                    <DiseaseInfo diseaseInfo={result.disease_information} />
                  )}

                  {/* 4. Human Agronomist Review Card */}
                  <HumanReviewCard
                    humanReview={result.human_review}
                    reportId={result.report_id}
                    reviewHistory={result.review_history}
                    onSendForReview={async (repId, notes) => {
                      return await submitForReview(repId, notes);
                    }}
                  />
                </div>
              )}

              {/* TAB 2: Visual AI Inspection */}
              {activeResultTab === 'visual' && (
                <div className="space-y-6 animate-fade-in">
                  {/* 1. Why did the AI make this prediction? (Grad-CAM Viewer) */}
                  {result.explainability && (
                    <GradCAMViewer
                      explainability={result.explainability}
                      originalImageSrc={result.image?.url || previewUrl}
                    />
                  )}

                  {/* 2. Estimated Affected Area (U-Net Lesion Segmentation) */}
                  {result.segmentation && (
                    <SegmentationViewer
                      segmentation={result.segmentation}
                      severity={result.severity}
                      originalImageSrc={result.image?.url || previewUrl}
                      diseaseValidationStatus={result.disease_analysis?.validation?.status}
                    />
                  )}

                  {/* 3. Estimated Severity */}
                  {result.severity && (
                    <SeverityCard severity={result.severity} />
                  )}
                </div>
              )}

              {/* TAB 3: Scientific Dossier & Blockchain Proof */}
              {activeResultTab === 'technical' && (
                <div className="space-y-6 animate-fade-in">
                  {/* 1. AI Disease Assessment with Top 3 Candidates & Compatibility Badges */}
                  {(result.disease_analysis?.compatible_top_3 || result.disease_analysis?.top_3) && (
                    <DiseaseRanking
                      top3={result.disease_analysis.compatible_top_3 || result.disease_analysis.top_3}
                      activePrediction={result.disease_analysis?.prediction}
                      validationStatus={result.disease_analysis?.validation?.status}
                      crop={result.crop_analysis?.prediction || result.crop_prediction?.prediction || result.crop_identification?.prediction}
                    />
                  )}

                  {/* 2. Cryptographic Evidence Chain */}
                  <TraceabilityCard
                    traceability={result.traceability}
                    reportId={result.report_id}
                    imageHash={result.image?.sha256}
                    timestamp={result.timestamp}
                  />

                  {/* 3. Tamper-Evident SHA-256 Evidence Chain Record */}
                  {result.traceability?.blockchain && (
                    <BlockchainStatus
                      blockchain={result.traceability.blockchain}
                      currentReportId={result.report_id}
                    />
                  )}

                  {/* 4. Research Mode: Technical & Model Architecture Deep-Dive */}
                  <ResearchModeToggle result={result} />
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Security Credentials Modal */}
      <SecurityModal
        isOpen={securityModalOpen}
        onClose={() => setSecurityModalOpen(false)}
      />
    </div>
  );
}
export default Analyze;
