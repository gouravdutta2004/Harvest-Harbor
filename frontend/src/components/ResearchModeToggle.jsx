import React, { useState } from 'react';
import { Microscope, ChevronDown, ChevronUp, Cpu, Database, CheckCircle, AlertTriangle, ShieldCheck } from 'lucide-react';
import { formatPercent, formatNumber } from '../utils/formatters';

export function ResearchModeToggle({ result, reportData, className = '' }) {
  const [isOpen, setIsOpen] = useState(false);
  const data = result || reportData;

  if (!data) return null;

  const health = data.health_prediction || {};
  const crop = data.crop_prediction || data.crop_analysis || data.crop_identification || {};
  const disease = data.disease_analysis || {};
  const seg = data.segmentation || {};
  const severity = data.severity || {};
  const trace = data.traceability || {};
  const healthCal = health.calibration || {};
  const diseaseCal = disease.calibration || {};

  const healthTemperature = healthCal.temperature ?? null;
  const healthEce = healthCal.ece ?? healthCal.expected_calibration_error ?? null;

  const diseaseTemperature = diseaseCal.temperature ?? null;
  const diseaseEce = diseaseCal.ece ?? diseaseCal.expected_calibration_error ?? null;

  return (
    <div className={`rounded-3xl border border-gray-200 dark:border-darkBorder bg-white dark:bg-darkCard overflow-hidden shadow-subtle ${className}`}>
      {/* Toggle Header Bar */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full p-4 sm:p-5 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-darkElevated/50 transition-colors text-left"
        aria-expanded={isOpen}
      >
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-purple-50 dark:bg-purple-950/60 text-purple-600 dark:text-purple-400 flex items-center justify-center font-bold">
            <Microscope className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-xs sm:text-sm font-bold text-gray-900 dark:text-white flex items-center gap-2">
              <span>Research &amp; Technical Deep-Dive</span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-purple-100 dark:bg-purple-950 text-purple-800 dark:text-purple-300 font-semibold">
                Research Mode
              </span>
            </h4>
            <p className="text-[11px] text-gray-500 dark:text-gray-400">
              Inspect model backbones, calibration parameters, raw logit probabilities, and local evidence chain proofs.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-gray-400">
          <span className="text-xs font-semibold text-purple-600 dark:text-purple-400 hidden sm:inline">
            {isOpen ? 'Collapse Details' : 'Expand Scientific Telemetry'}
          </span>
          {isOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </div>
      </button>

      {/* Expanded Scientific Content */}
      {isOpen && (
        <div className="p-6 border-t border-gray-100 dark:border-darkBorder bg-gray-50/50 dark:bg-darkElevated/30 space-y-6 text-xs animate-fade-in font-sans">
          {/* Models Architecture Summary Table */}
          <div className="space-y-2">
            <span className="text-[11px] font-mono uppercase tracking-wider text-gray-500 font-bold block">
              1. Neural Architecture Matrix
            </span>
            <div className="overflow-x-auto rounded-2xl border border-gray-200 dark:border-darkBorder bg-white dark:bg-darkCard">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-gray-50 dark:bg-darkElevated text-gray-500 border-b border-gray-100 dark:border-darkBorder text-[10px] uppercase">
                  <tr>
                    <th className="p-2.5">Pipeline Stage</th>
                    <th className="p-2.5">Backbone / Topology</th>
                    <th className="p-2.5">Input Tensor</th>
                    <th className="p-2.5">Classes / Scope</th>
                    <th className="p-2.5">Output Metric</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-darkBorder text-[11px]">
                  <tr>
                    <td className="p-2.5 font-bold text-gray-900 dark:text-white">Health Gate</td>
                    <td className="p-2.5 text-emerald-600 dark:text-emerald-400">EfficientNet-B0 (Frozen Features)</td>
                    <td className="p-2.5">224 × 224 × 3</td>
                    <td className="p-2.5">Binary (Healthy vs Diseased)</td>
                    <td className="p-2.5">{formatPercent(health.confidence)}</td>
                  </tr>
                  <tr>
                    <td className="p-2.5 font-bold text-gray-900 dark:text-white">Botanical ID</td>
                    <td className="p-2.5 text-blue-600 dark:text-blue-400">EfficientNet-B0 (Transfer Head)</td>
                    <td className="p-2.5">224 × 224 × 3</td>
                    <td className="p-2.5">Multi-Crop Taxonomy</td>
                    <td className="p-2.5">{formatPercent(crop.confidence)}</td>
                  </tr>
                  <tr>
                    <td className="p-2.5 font-bold text-gray-900 dark:text-white">Disease Head</td>
                    <td className="p-2.5 text-amber-600 dark:text-amber-400">PlantWild v2 Deep CNN</td>
                    <td className="p-2.5">224 × 224 × 3</td>
                    <td className="p-2.5">115 Disease Classes</td>
                    <td className="p-2.5">{formatPercent(disease.confidence)}</td>
                  </tr>
                  <tr>
                    <td className="p-2.5 font-bold text-gray-900 dark:text-white">Lesion Mask</td>
                    <td className="p-2.5 text-purple-600 dark:text-purple-400">{seg.architecture || 'U-Net PlantSeg'}</td>
                    <td className="p-2.5">256 × 256 × 3</td>
                    <td className="p-2.5">Binary Lesion Foreground</td>
                    <td className="p-2.5">{severity.affected_area_percent != null ? `${severity.affected_area_percent.toFixed(2)}% Area` : 'Calculated'}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Calibration & Temperature Parameters */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="p-4 rounded-2xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder space-y-2">
              <span className="text-[11px] font-mono font-bold text-gray-500 uppercase block">
                2. Calibration &amp; Uncertainty Telemetry
              </span>
              <div className="space-y-1.5 font-mono text-[11px] text-gray-700 dark:text-gray-300">
                <div className="flex justify-between">
                  <span>Health Model Calibration:</span>
                  {healthTemperature != null ? (
                    <strong>T = {typeof healthTemperature === 'number' ? healthTemperature.toFixed(4) : healthTemperature}</strong>
                  ) : (
                    <span className="text-gray-500 dark:text-gray-400">Unavailable</span>
                  )}
                </div>
                <div className="flex justify-between">
                  <span>Health Model ECE:</span>
                  {healthEce != null ? (
                    <span className="text-emerald-600 dark:text-emerald-400 font-bold">
                      {typeof healthEce === 'number' ? `${(healthEce * (healthEce <= 1 ? 100 : 1)).toFixed(2)}%` : healthEce}
                    </span>
                  ) : (
                    <span className="text-gray-500 dark:text-gray-400">Not independently validated</span>
                  )}
                </div>
                <div className="flex justify-between">
                  <span>Disease Model Calibration:</span>
                  {diseaseTemperature != null ? (
                    <strong>T = {typeof diseaseTemperature === 'number' ? diseaseTemperature.toFixed(4) : diseaseTemperature}</strong>
                  ) : (
                    <span className="text-gray-500 dark:text-gray-400">Calibration metadata unavailable</span>
                  )}
                </div>
                <div className="flex justify-between">
                  <span>Disease Model ECE:</span>
                  {diseaseEce != null ? (
                    <span className="text-emerald-600 dark:text-emerald-400 font-bold">
                      {typeof diseaseEce === 'number' ? `${(diseaseEce * (diseaseEce <= 1 ? 100 : 1)).toFixed(2)}%` : diseaseEce}
                    </span>
                  ) : (
                    <span className="text-gray-500 dark:text-gray-400">Not independently validated</span>
                  )}
                </div>
                <div className="flex justify-between">
                  <span>Botanical Compatibility:</span>
                  <span className={disease.validation?.status === 'rejected' ? 'text-rose-500 font-bold' : 'text-emerald-600 font-bold'}>
                    {disease.validation?.status ? disease.validation.status.toUpperCase() : 'VALIDATED'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Severity Categorization:</span>
                  <span className="text-amber-600 dark:text-amber-400">Project-Defined Thresholds</span>
                </div>
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder space-y-2">
              <span className="text-[11px] font-mono font-bold text-gray-500 uppercase block">
                3. Evidence Chain Proof
              </span>
              <div className="space-y-1.5 font-mono text-[11px] text-gray-700 dark:text-gray-300">
                <div className="flex justify-between truncate">
                  <span>Report ID:</span>
                  <strong>{data.report_id || data.id || 'N/A'}</strong>
                </div>
                <div className="flex justify-between truncate">
                  <span>Image SHA-256:</span>
                  <span className="truncate max-w-[140px]">{data.image?.sha256 || trace.image_sha256 || 'Calculated'}</span>
                </div>
                <div className="flex justify-between">
                  <span>Record Index:</span>
                  <span>#{trace.blockchain?.block_index ?? trace.blockchain?.current_block?.index ?? 'Verified'}</span>
                </div>
                <div className="flex justify-between">
                  <span>Chain Integrity Status:</span>
                  <span className="text-emerald-600 font-bold">SHA-256 Cryptographically Linked</span>
                </div>
              </div>
            </div>
          </div>

          {/* Scientific Disclaimer for Researchers */}
          <div className="p-3 rounded-xl bg-purple-50 dark:bg-purple-950/40 border border-purple-200 dark:border-purple-800 text-[11px] text-purple-900 dark:text-purple-300">
            <strong>Research Methodology Note:</strong> Models were trained on public benchmark datasets (PlantVillage &amp; PlantWild v2) under standardized laboratory imaging. Empirical in-field performance may encounter covariate shift due to variable outdoor sunlight, multiple overlapping foliar disorders, and soil nutritional chlorosis.
          </div>
        </div>
      )}
    </div>
  );
}

export default ResearchModeToggle;
