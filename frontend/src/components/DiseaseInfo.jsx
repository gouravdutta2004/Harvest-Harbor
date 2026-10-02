import React, { useState } from 'react';
import { BookOpen, AlertCircle, ShieldAlert, Thermometer, Wind, CheckCircle2, Sprout } from 'lucide-react';
import { toTitleCase } from '../utils/formatters';

export function DiseaseInfo({ diseaseInfo, className = '' }) {
  if (!diseaseInfo || !diseaseInfo.available || !diseaseInfo.information) {
    return (
      <div className={`p-6 rounded-3xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder shadow-subtle space-y-3 ${className}`}>
        <div className="flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-gray-400" />
          <h3 className="text-sm font-bold uppercase tracking-wider text-gray-900 dark:text-white">
            Agronomic Knowledge Base
          </h3>
        </div>
        <p className="text-xs text-gray-500 dark:text-gray-400">
          {diseaseInfo?.message || 'Not available in historical record'}
        </p>
      </div>
    );
  }

  const info = diseaseInfo.information;
  const [activeTab, setActiveTab] = useState('overview'); // 'overview' | 'actions' | 'environment'

  return (
    <div className={`p-6 sm:p-7 rounded-3xl bg-white dark:bg-darkCard border border-gray-200 dark:border-darkBorder shadow-subtle space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400">
            <BookOpen className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400">
                Agronomic Knowledge Base
              </span>
              {info.pathogen && (
                <span className="text-xs italic font-serif text-gray-500 dark:text-gray-400">
                  ({info.pathogen})
                </span>
              )}
            </div>
            <h3 className="text-lg font-bold text-gray-900 dark:text-white">
              {info.crop ? `${info.crop} ` : ''}
              {info.disease ? info.disease : toTitleCase(diseaseInfo.disease_key)}
            </h3>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center gap-1 p-1 rounded-xl bg-gray-100 dark:bg-darkElevated border border-gray-200/80 dark:border-darkBorder text-xs font-semibold">
          <button
            onClick={() => setActiveTab('overview')}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              activeTab === 'overview'
                ? 'bg-white dark:bg-darkCard text-emerald-800 dark:text-emerald-300 shadow-subtle'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
            }`}
          >
            Symptoms &amp; Causes
          </button>
          <button
            onClick={() => setActiveTab('actions')}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              activeTab === 'actions'
                ? 'bg-white dark:bg-darkCard text-emerald-800 dark:text-emerald-300 shadow-subtle'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
            }`}
          >
            Actions &amp; Prevention
          </button>
          <button
            onClick={() => setActiveTab('environment')}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              activeTab === 'environment'
                ? 'bg-white dark:bg-darkCard text-emerald-800 dark:text-emerald-300 shadow-subtle'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
            }`}
          >
            Spread &amp; Weather
          </button>
        </div>
      </div>

      {/* Tab: Overview (Symptoms & Causes) */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 text-xs">
          {/* Symptoms */}
          <div className="p-4 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder space-y-3">
            <span className="font-bold uppercase tracking-wider text-gray-900 dark:text-white flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-amber-500" />
              Common Symptoms
            </span>
            {Array.isArray(info.symptoms) && info.symptoms.length > 0 ? (
              <ul className="space-y-2 text-gray-700 dark:text-gray-300">
                {info.symptoms.map((symptom, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-1.5 shrink-0" />
                    <span>{symptom}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-500 italic">No symptoms documented.</p>
            )}
          </div>

          {/* Causes */}
          <div className="p-4 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder space-y-3">
            <span className="font-bold uppercase tracking-wider text-gray-900 dark:text-white flex items-center gap-2">
              <Sprout className="w-4 h-4 text-emerald-600" />
              Primary Causes &amp; Pathogens
            </span>
            {Array.isArray(info.causes) && info.causes.length > 0 ? (
              <ul className="space-y-2 text-gray-700 dark:text-gray-300">
                {info.causes.map((cause, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-1.5 shrink-0" />
                    <span>{cause}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-500 italic">No cause details documented.</p>
            )}
          </div>
        </div>
      )}

      {/* Tab: Actions & Prevention */}
      {activeTab === 'actions' && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 text-xs">
          {/* Immediate Actions */}
          <div className="p-4 rounded-2xl bg-emerald-50/50 dark:bg-emerald-950/30 border border-emerald-100 dark:border-emerald-800/60 space-y-3">
            <span className="font-bold uppercase tracking-wider text-emerald-900 dark:text-emerald-300 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
              Immediate Field Actions
            </span>
            {Array.isArray(info.immediate_actions) && info.immediate_actions.length > 0 ? (
              <ul className="space-y-2 text-gray-700 dark:text-gray-300">
                {info.immediate_actions.map((action, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-1.5 shrink-0" />
                    <span>{action}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-500 italic">No immediate actions listed.</p>
            )}
          </div>

          {/* Prevention */}
          <div className="p-4 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder space-y-3">
            <span className="font-bold uppercase tracking-wider text-gray-900 dark:text-white flex items-center gap-2">
              <Sprout className="w-4 h-4 text-emerald-600" />
              Long-Term Preventive Measures
            </span>
            {Array.isArray(info.prevention) && info.prevention.length > 0 ? (
              <ul className="space-y-2 text-gray-700 dark:text-gray-300">
                {info.prevention.map((prev, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-1.5 shrink-0" />
                    <span>{prev}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-500 italic">No preventive measures listed.</p>
            )}
          </div>
        </div>
      )}

      {/* Tab: Spread & Weather */}
      {activeTab === 'environment' && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 text-xs">
          {/* Environment */}
          <div className="p-4 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder space-y-3">
            <span className="font-bold uppercase tracking-wider text-gray-900 dark:text-white flex items-center gap-2">
              <Thermometer className="w-4 h-4 text-rose-500" />
              Environmental Triggers
            </span>
            {Array.isArray(info.environment) && info.environment.length > 0 ? (
              <ul className="space-y-2 text-gray-700 dark:text-gray-300">
                {info.environment.map((env, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-1.5 shrink-0" />
                    <span>{env}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-500 italic">No environmental factors listed.</p>
            )}
          </div>

          {/* Spread */}
          <div className="p-4 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-100 dark:border-darkBorder space-y-3">
            <span className="font-bold uppercase tracking-wider text-gray-900 dark:text-white flex items-center gap-2">
              <Wind className="w-4 h-4 text-blue-500" />
              Transmission &amp; Spread Vectors
            </span>
            {Array.isArray(info.spread) && info.spread.length > 0 ? (
              <ul className="space-y-2 text-gray-700 dark:text-gray-300">
                {info.spread.map((sp, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-1.5 shrink-0" />
                    <span>{sp}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-500 italic">No spread factors listed.</p>
            )}
          </div>
        </div>
      )}

      {/* Mandatory Regulatory / Chemical Guidance Disclaimer */}
      <div className="p-4 rounded-2xl bg-gray-50 dark:bg-darkElevated border border-gray-200 dark:border-darkBorder text-xs text-gray-600 dark:text-gray-400 space-y-1">
        <div className="flex items-center gap-2 font-bold text-gray-800 dark:text-gray-200">
          <AlertCircle className="w-4 h-4 text-emerald-600" />
          <span>Agricultural Treatment Protocol Disclaimer</span>
        </div>
        <p className="leading-relaxed">
          {info.treatment_note ||
            'Follow locally approved crop-specific treatment guidance, extension advisory bulletins, and regulatory product labels. Do not administer chemical treatments without field verification.'}
        </p>
      </div>
    </div>
  );
}
export default DiseaseInfo;
