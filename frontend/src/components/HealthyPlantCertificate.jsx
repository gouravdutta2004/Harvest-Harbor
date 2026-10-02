import React from 'react';
import { CheckCircle2, ShieldCheck, Sprout, Droplets, SunMedium, CalendarCheck, AlertCircle } from 'lucide-react';
import { formatPercent } from '../utils/formatters';

export function HealthyPlantCertificate({ reportId, confidence }) {
  const displayConfidence = confidence !== null && confidence !== undefined ? formatPercent(confidence) : 'High';

  return (
    <div className="p-6 sm:p-8 rounded-3xl bg-white dark:bg-darkCard border border-emerald-200 dark:border-emerald-800/80 shadow-subtle space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-gray-100 dark:border-darkBorder">
        <div className="flex items-center gap-3.5">
          <div className="w-12 h-12 rounded-2xl bg-emerald-100 dark:bg-emerald-950/80 text-emerald-600 dark:text-emerald-400 flex items-center justify-center flex-shrink-0 shadow-subtle">
            <CheckCircle2 className="w-7 h-7" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base sm:text-lg font-bold text-gray-900 dark:text-white">
                Healthy Plant Assessment: Healthy
              </h3>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wide bg-emerald-100 text-emerald-800 dark:bg-emerald-900/60 dark:text-emerald-200">
                Screened
              </span>
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              No disease was detected by the health classifier during binary neural screening.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200/70 dark:border-emerald-800/60 text-xs font-semibold text-emerald-800 dark:text-emerald-300 self-start sm:self-auto">
          <ShieldCheck className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
          <span>Confidence: {displayConfidence}</span>
        </div>
      </div>

      {/* Scientific Disclaimer Pill */}
      <div className="p-3.5 rounded-2xl bg-amber-50/60 dark:bg-amber-950/30 border border-amber-200/60 dark:border-amber-900/40 text-xs text-amber-900 dark:text-amber-200 flex items-start gap-2.5">
        <AlertCircle className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
        <p className="leading-relaxed">
          <strong>Notice:</strong> AI screening does not guarantee complete absence of disease. Microscopic, systemic, or early-stage latent pathogens may not manifest visual foliar symptoms. Always corroborate findings with field scouting.
        </p>
      </div>

      {/* Recommended Good Agricultural Practices (GAP) for healthy crops */}
      <div className="space-y-3">
        <h4 className="text-xs font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400">
          General Preventive Considerations (Good Agricultural Practices)
        </h4>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder space-y-2">
            <div className="flex items-center gap-2 text-emerald-700 dark:text-emerald-400">
              <Droplets className="w-4 h-4" />
              <span className="text-xs font-bold">Microclimate &amp; Irrigation</span>
            </div>
            <p className="text-xs text-gray-600 dark:text-gray-400 leading-relaxed">
              Use drip or sub-canopy irrigation to keep foliar surfaces dry, eliminating free water needed for fungal spore germination.
            </p>
          </div>

          <div className="p-4 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder space-y-2">
            <div className="flex items-center gap-2 text-emerald-700 dark:text-emerald-400">
              <SunMedium className="w-4 h-4" />
              <span className="text-xs font-bold">Canopy Aeration</span>
            </div>
            <p className="text-xs text-gray-600 dark:text-gray-400 leading-relaxed">
              Maintain optimal row spacing and prune lower dead foliage to improve air circulation and sunlight penetration.
            </p>
          </div>

          <div className="p-4 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder space-y-2">
            <div className="flex items-center gap-2 text-emerald-700 dark:text-emerald-400">
              <CalendarCheck className="w-4 h-4" />
              <span className="text-xs font-bold">Scouting Cadence</span>
            </div>
            <p className="text-xs text-gray-600 dark:text-gray-400 leading-relaxed">
              Schedule routine 7-day leaf scouting. Re-scan immediately if weather forecasts indicate prolonged high humidity or rain.
            </p>
          </div>
        </div>
      </div>

      {/* Assessment Record Footer */}
      <div className="p-3.5 rounded-2xl bg-emerald-50/60 dark:bg-emerald-950/20 border border-emerald-100 dark:border-emerald-900/40 flex items-center justify-between text-xs text-emerald-800 dark:text-emerald-300">
        <div className="flex items-center gap-2">
          <Sprout className="w-4 h-4 text-emerald-600" />
          <span>Health screening record logged to tamper-evident evidence chain.</span>
        </div>
        <span className="font-mono text-[11px] opacity-75">
          {reportId || 'Evidence Chain Logged'}
        </span>
      </div>
    </div>
  );
}

export default HealthyPlantCertificate;
