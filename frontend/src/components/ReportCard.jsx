import React, { useState } from 'react';
import { Printer, Copy, Check, ShieldCheck, Download, Calendar, Hash, FileText } from 'lucide-react';
import { formatDate, formatPercent, toTitleCase, getHealthStatusTheme, getSeverityTheme } from '../utils/formatters';
import { resolveAssetUrl, submitForReview } from '../services/api';
import AuthenticatedImage from './AuthenticatedImage';
import { HashDisplay } from './HashDisplay';
import { PredictionCard } from './PredictionCard';
import { CropIdentificationCard } from './CropIdentificationCard';
import { DiseaseRanking } from './DiseaseRanking';
import { GradCAMViewer } from './GradCAMViewer';
import { SegmentationViewer } from './SegmentationViewer';
import { SeverityCard } from './SeverityCard';
import { HumanReviewCard } from './HumanReviewCard';
import { IllustrativeManagementGuidance } from './IllustrativeManagementGuidance';
import { ResearchModeToggle } from './ResearchModeToggle';
import { DiseaseInfo } from './DiseaseInfo';
import { HealthyPlantCertificate } from './HealthyPlantCertificate';
import { BlockchainStatus } from './BlockchainStatus';

export function ReportCard({ reportData, originalImageSrc = null, onDownloadJson = null }) {
  const [copiedId, setCopiedId] = useState(false);

  if (!reportData) return null;

  const reportId = reportData.report_id || reportData.data?.report_id || 'CR-UNKNOWN';
  const timestamp = reportData.timestamp || reportData.data?.timestamp;
  const imageHash = reportData.image?.sha256 || reportData.data?.image_sha256;
  const blockchain = reportData.traceability?.blockchain || {
    block_index: reportData.block_index,
    current_hash: reportData.current_hash,
    previous_hash: reportData.previous_hash,
    chain_valid: reportData.chain_verification?.valid ?? true,
    checked_blocks: reportData.chain_verification?.checked_blocks ?? 1,
  };

  const handleCopyId = async () => {
    try {
      await navigator.clipboard.writeText(reportId);
      setCopiedId(true);
      setTimeout(() => setCopiedId(false), 2000);
    } catch (err) {
      console.error('Failed to copy report id:', err);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  const handleExportJson = () => {
    const jsonStr = JSON.stringify(reportData, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${reportId}_harvest_harbor_report.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto print:max-w-none">
      {/* Report Action Header (Hidden during print) */}
      <div className="no-print p-4 sm:p-5 rounded-3xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder shadow-subtle flex flex-wrap items-center justify-between gap-4">
        <div>
          <span className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider block">
            AI-Assisted Assessment Record
          </span>
          <h2 className="text-lg sm:text-xl font-bold text-gray-900 dark:text-white font-mono">
            {reportId}
          </h2>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={handleCopyId}
            type="button"
            className="px-3.5 py-2 rounded-xl bg-gray-50 dark:bg-darkElevated border border-gray-200 dark:border-darkBorder text-gray-700 dark:text-gray-300 text-xs font-semibold hover:bg-gray-100 dark:hover:bg-gray-800 flex items-center gap-1.5 transition-colors"
          >
            {copiedId ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copiedId ? 'Copied ID' : 'Copy ID'}</span>
          </button>

          <button
            onClick={handleExportJson}
            type="button"
            className="px-3.5 py-2 rounded-xl bg-gray-50 dark:bg-darkElevated border border-gray-200 dark:border-darkBorder text-gray-700 dark:text-gray-300 text-xs font-semibold hover:bg-gray-100 dark:hover:bg-gray-800 flex items-center gap-1.5 transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>JSON Audit</span>
          </button>

          <button
            onClick={handlePrint}
            type="button"
            className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold shadow-glow-emerald flex items-center gap-1.5 transition-all"
          >
            <Printer className="w-3.5 h-3.5" />
            <span>Print Report</span>
          </button>
        </div>
      </div>

      {/* Main Report Container */}
      <div className="p-6 sm:p-10 rounded-3xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder shadow-subtle space-y-8 print:border-none print:shadow-none print:p-0">
        {/* Report Header Banner */}
        <div className="border-b border-gray-200 dark:border-darkBorder pb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 sm:w-16 sm:h-16 rounded-2xl overflow-hidden border border-emerald-500/30 flex-shrink-0 bg-white dark:bg-darkCard shadow-subtle">
              <img src="/logo.png" alt="Harvest Harbor Logo" className="w-full h-full object-cover" />
            </div>
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="text-emerald-700 dark:text-emerald-400 font-bold text-sm tracking-wider uppercase">
                  HARVEST HARBOR
                </span>
                <span className="text-gray-400">•</span>
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  AI Agricultural Decision-Support Dossier
                </span>
              </div>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 dark:text-white tracking-tight">
                AI-Assisted Crop Assessment Report
              </h1>
              <p className="text-xs text-gray-500 dark:text-gray-400 font-mono">
                Report Identifier: {reportId}
              </p>
            </div>
          </div>

          <div className="p-3.5 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-200/80 dark:border-darkBorder text-right text-xs space-y-1">
            <div className="flex items-center justify-end gap-1.5 text-gray-600 dark:text-gray-400">
              <Calendar className="w-3.5 h-3.5" />
              <span>{formatDate(timestamp)}</span>
            </div>
            <div className="font-mono text-gray-500 dark:text-gray-400 flex items-center justify-end gap-1">
              <Hash className="w-3 h-3" />
              <HashDisplay hash={imageHash} startChars={6} endChars={6} />
            </div>
          </div>
        </div>

        {/* Section 1: Executive Summary & Section 4: Binary Health Screening */}
        <section aria-labelledby="sec-summary">
          <div className="text-[11px] font-bold uppercase tracking-wider text-emerald-700 dark:text-emerald-400 mb-2 flex items-center gap-1.5">
            <span>Section 1 &amp; 4</span>
            <span>•</span>
            <span>Executive Summary &amp; Binary Health Screening</span>
          </div>
          <PredictionCard data={reportData} />
        </section>

        {/* Healthy Plant Assessment if healthy */}
        {(reportData.status === 'healthy_prediction' || reportData.health_prediction?.prediction === 'healthy') && (
          <HealthyPlantCertificate
            reportId={reportId}
            confidence={reportData.health_prediction?.confidence}
          />
        )}

        {/* Section 2: Input Image & Metadata */}
        {(originalImageSrc || reportData.image?.url) && (
          <section aria-labelledby="sec-image">
            <div className="text-[11px] font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-2">
              Section 2 • Input Image &amp; Cryptographic Integrity
            </div>
            <div className="p-4 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-200 dark:border-darkBorder flex flex-col sm:flex-row items-center gap-4">
              <AuthenticatedImage
                src={reportData.image?.url || originalImageSrc}
                alt="Analyzed leaf specimen"
                className="w-32 h-32 object-cover rounded-xl border border-gray-200 dark:border-darkBorder shadow-sm"
              />
              <div className="text-xs text-gray-600 dark:text-gray-300 space-y-1 flex-1">
                <p className="font-semibold text-gray-900 dark:text-white">Specimen Verification Record</p>
                <p>Report ID: <span className="font-mono">{reportId}</span></p>
                <p>SHA-256 Digest: <span className="font-mono text-[11px] break-all">{imageHash || 'Available on chain'}</span></p>
                <p className="text-[11px] text-gray-500 dark:text-gray-400">Specimen pixels hashed before neural inference to ensure end-to-end auditability.</p>
              </div>
            </div>
          </section>
        )}

        {/* Section 3 & 6: Botanical Crop Identification & Biological Plausibility Gating */}
        <section aria-labelledby="sec-crop">
          <div className="text-[11px] font-bold uppercase tracking-wider text-emerald-700 dark:text-emerald-400 mb-2 flex items-center gap-1.5">
            <span>Section 3 &amp; 6</span>
            <span>•</span>
            <span>Botanical Crop Identification &amp; Biological Plausibility Gating</span>
          </div>
          <CropIdentificationCard cropData={reportData.crop_identification || reportData.crop_prediction || reportData.crop_analysis} />
        </section>

        {/* Section 5: Disease Classification */}
        {(reportData.disease_analysis?.compatible_top_3 || reportData.disease_analysis?.top_3) && (
          <section aria-labelledby="sec-disease">
            <div className="text-[11px] font-bold uppercase tracking-wider text-emerald-700 dark:text-emerald-400 mb-2">
              Section 5 • Disease Candidates &amp; Compatibility Evaluation
            </div>
            <DiseaseRanking
              top3={reportData.disease_analysis.compatible_top_3 || reportData.disease_analysis.top_3}
              activePrediction={reportData.disease_analysis?.prediction}
              validationStatus={reportData.disease_analysis?.validation?.status}
              crop={reportData.crop_identification?.prediction || reportData.crop_prediction?.prediction || reportData.crop_analysis?.prediction}
            />
          </section>
        )}

        {/* Section 7: Model Confidence & Temperature Calibration */}
        <section aria-labelledby="sec-calibration">
          <div className="text-[11px] font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-2">
            Section 7 • Model Confidence &amp; Temperature Calibration
          </div>
          <ResearchModeToggle result={reportData} />
        </section>

        {/* Section 8: Grad-CAM Interpretability */}
        <section aria-labelledby="sec-gradcam">
          <div className="text-[11px] font-bold uppercase tracking-wider text-emerald-700 dark:text-emerald-400 mb-2">
            Section 8 • Explainability (Grad-CAM Salience Activation)
          </div>
          <GradCAMViewer
            explainability={reportData.explainability}
            originalImageSrc={reportData.image?.url || originalImageSrc}
          />
        </section>

        {/* Section 9: Lesion Segmentation & Estimated Affected Area */}
        <section aria-labelledby="sec-seg">
          <div className="text-[11px] font-bold uppercase tracking-wider text-emerald-700 dark:text-emerald-400 mb-2">
            Section 9 • Lesion Segmentation &amp; Estimated Affected Area
          </div>
          <SegmentationViewer
            segmentation={reportData.segmentation}
            severity={reportData.severity}
            originalImageSrc={reportData.image?.url || originalImageSrc}
            diseaseValidationStatus={reportData.disease_analysis?.validation?.status}
          />
        </section>

        {/* Section 10: Estimated Severity Categorization */}
        <section aria-labelledby="sec-sev">
          <div className="text-[11px] font-bold uppercase tracking-wider text-emerald-700 dark:text-emerald-400 mb-2">
            Section 10 • Estimated Severity Categorization
          </div>
          <SeverityCard severity={reportData.severity} />
        </section>

        {/* Section 11: Human Review Recommendation */}
        <section aria-labelledby="sec-review">
          <div className="text-[11px] font-bold uppercase tracking-wider text-emerald-700 dark:text-emerald-400 mb-2">
            Section 11 • Agronomic Human Review Recommendation
          </div>
          <HumanReviewCard
            humanReview={reportData.human_review}
            reviewHistory={reportData.review_history}
            reportId={reportId}
            onSendForReview={submitForReview}
          />
        </section>

        {/* Section 12: Illustrative Management Guidance */}
        <section aria-labelledby="sec-guidance">
          <div className="text-[11px] font-bold uppercase tracking-wider text-emerald-700 dark:text-emerald-400 mb-2">
            Section 12 • Illustrative Management Guidance
          </div>
          <IllustrativeManagementGuidance
            diseaseInfo={reportData.disease_information}
            cropIdentification={reportData.crop_identification}
            prediction={reportData.disease_analysis?.prediction || reportData.health_prediction?.prediction}
          />
          {reportData.disease_information && (
            <div className="mt-4">
              <DiseaseInfo diseaseInfo={reportData.disease_information} />
            </div>
          )}
        </section>

        {/* Section 13: SHA-256 Tamper-Evident Evidence Chain */}
        <section aria-labelledby="sec-traceability">
          <div className="text-[11px] font-bold uppercase tracking-wider text-emerald-700 dark:text-emerald-400 mb-2">
            Section 13 • SHA-256 Tamper-Evident Evidence Chain
          </div>
          <BlockchainStatus
            blockchain={blockchain}
            currentReportId={reportId}
          />
        </section>

        {/* Section 14: Scientific Disclaimers & Intended Use */}
        <section aria-labelledby="sec-disclaimer" className="p-5 rounded-2xl bg-amber-50/70 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800/80 text-xs space-y-2">
          <div className="font-bold text-amber-900 dark:text-amber-200 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
            <span>Section 14 • Scientific Disclaimers &amp; Intended Use Boundary</span>
          </div>
          <p className="text-amber-800 dark:text-amber-300 leading-relaxed">
            Harvest Harbor is an artificial intelligence-assisted decision-support platform designed for agronomic educational research and triage guidance. All predictions, estimated affected areas, and severity levels are mathematical model outputs derived from 2D optical images. They do not constitute an official laboratory pathology test, agricultural warranty, or certified pesticide prescription.
          </p>
          <p className="text-amber-800 dark:text-amber-300 leading-relaxed">
            Before undertaking chemical or biological control actions, always consult a certified local agronomist, agricultural extension agent, or phytosanitary regulatory body.
          </p>
        </section>

        {/* Report Footer / Signature */}
        <div className="pt-6 border-t border-gray-200 dark:border-darkBorder flex flex-col sm:flex-row items-center justify-between text-[11px] text-gray-500 dark:text-gray-400 gap-4">
          <div className="space-y-0.5">
            <p className="font-semibold text-gray-800 dark:text-gray-200">
              Harvest Harbor AI Diagnostic Engine v1.0
            </p>
            <p>
              Verified by SHA-256 tamper-evident evidence chain.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            <span className="font-mono font-semibold">
              Status: {blockchain?.chain_valid ? 'Cryptographically Verified' : 'Unverified'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
export default ReportCard;
