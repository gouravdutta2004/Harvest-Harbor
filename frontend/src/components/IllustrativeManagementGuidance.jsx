import React from 'react';
import {
  FileText,
  AlertCircle,
  Eye,
  Shield,
  Sprout,
  Users,
  CheckCircle2,
  HelpCircle,
} from 'lucide-react';
import { InfoTooltip } from './InfoTooltip';

export function IllustrativeManagementGuidance({
  diseaseInfo,
  prediction,
  crop,
  className = '',
}) {
  if (!diseaseInfo && !prediction) return null;

  // Extract structured management guidance safely
  const info = diseaseInfo || {};
  const management = info.management || {};
  const cultural = management.cultural_practices || info.cultural_controls || [];
  const monitoring = management.monitoring || info.monitoring_tips || [
    'Inspect surrounding plants for early symptom development or sporulation.',
    'Monitor local microclimate humidity, canopy wetness duration, and rainfall.',
  ];
  const generalPrevention = management.prevention || [
    'Maintain recommended plant spacing to facilitate airflow within the canopy.',
    'Sanitize pruning tools between rows to prevent mechanical pathogen spread.',
    'Avoid overhead sprinkler irrigation late in the evening to reduce leaf wetness.',
  ];

  return (
    <div
      className={`p-6 sm:p-7 rounded-3xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder shadow-subtle space-y-6 ${className}`}
    >
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Sprout className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
          <h3 className="text-sm font-bold uppercase tracking-wider text-gray-900 dark:text-white">
            Illustrative Management Guidance
          </h3>
          <InfoTooltip
            title="Educational Guidance Notice"
            content="This guidance is illustrative and educational. It outlines agronomic sanitation and scouting practices. It does not replace field consultation with a certified crop advisor."
          />
        </div>

        <span className="px-3 py-1 rounded-full text-[11px] font-mono font-semibold bg-gray-100 dark:bg-darkElevated text-gray-600 dark:text-gray-300 border border-gray-200 dark:border-darkBorder">
          Educational Support Only
        </span>
      </div>

      {/* Mandatory Scientific Disclaimer Banner */}
      <div className="p-3.5 rounded-2xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 text-xs text-amber-800 dark:text-amber-300 flex items-start gap-2.5">
        <AlertCircle className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
        <p className="leading-relaxed text-[11px]">
          <strong>Notice:</strong> This information is educational and illustrative. Chemical or biological interventions must adhere to regional label laws and be verified with a certified agronomic advisor or university extension agent before application.
        </p>
      </div>

      {/* 4 Core Pillars of Good Agricultural Practices */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* 1. Immediate Field Considerations */}
        <div className="p-4 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder space-y-2.5">
          <div className="flex items-center gap-2 font-bold text-xs text-gray-900 dark:text-white">
            <Shield className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            <span>Immediate Field Considerations</span>
          </div>
          <ul className="space-y-1.5 text-xs text-gray-600 dark:text-gray-400">
            {cultural.length > 0 ? (
              cultural.slice(0, 3).map((item, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shrink-0 mt-1.5" />
                  <span>{item}</span>
                </li>
              ))
            ) : (
              <>
                <li className="flex items-start gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shrink-0 mt-1.5" />
                  <span>Isolate severely damaged foliage to prevent airborne spore dispersal.</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shrink-0 mt-1.5" />
                  <span>Disinfect harvesting clippers and farm implements before moving to clean plots.</span>
                </li>
              </>
            )}
          </ul>
        </div>

        {/* 2. Scouting & Monitoring */}
        <div className="p-4 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder space-y-2.5">
          <div className="flex items-center gap-2 font-bold text-xs text-gray-900 dark:text-white">
            <Eye className="w-4 h-4 text-blue-600 dark:text-blue-400" />
            <span>Field Scouting &amp; Monitoring</span>
          </div>
          <ul className="space-y-1.5 text-xs text-gray-600 dark:text-gray-400">
            {monitoring.slice(0, 3).map((item, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-blue-500 shrink-0 mt-1.5" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* 3. General Prevention & Cultural Hygiene */}
        <div className="p-4 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder space-y-2.5">
          <div className="flex items-center gap-2 font-bold text-xs text-gray-900 dark:text-white">
            <CheckCircle2 className="w-4 h-4 text-purple-600 dark:text-purple-400" />
            <span>Canopy Hygiene &amp; Prevention</span>
          </div>
          <ul className="space-y-1.5 text-xs text-gray-600 dark:text-gray-400">
            {generalPrevention.slice(0, 3).map((item, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-purple-500 shrink-0 mt-1.5" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* 4. When to Consult an Agronomist */}
        <div className="p-4 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder space-y-2.5">
          <div className="flex items-center gap-2 font-bold text-xs text-gray-900 dark:text-white">
            <Users className="w-4 h-4 text-amber-600 dark:text-amber-400" />
            <span>When to Consult an Agronomist</span>
          </div>
          <ul className="space-y-1.5 text-xs text-gray-600 dark:text-gray-400">
            <li className="flex items-start gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-500 shrink-0 mt-1.5" />
              <span>When symptoms spread across more than 10% of field canopy within 48 hours.</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-500 shrink-0 mt-1.5" />
              <span>Before selecting or applying any chemical, biological, or regulated crop-protection products.</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-500 shrink-0 mt-1.5" />
              <span>If visual symptoms do not match typical host lesion patterns.</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}

export default IllustrativeManagementGuidance;
