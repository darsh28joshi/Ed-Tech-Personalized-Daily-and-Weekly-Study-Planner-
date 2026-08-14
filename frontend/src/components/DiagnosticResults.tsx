import React from 'react';
import { Award, Brain, Shield, ArrowRight, CheckCircle2, TrendingUp, AlertTriangle } from 'lucide-react';

interface CategoryScore {
  accuracy: number;
  percentile: number;
}

interface DiagnosticResultsProps {
  results: {
    academic_accuracy: number;
    aptitude_score: number;
    aptitude_percentile: number;
    study_health_score: number;
    category_scores: Record<string, CategoryScore>;
    weakest_chapter_ids: number[];
  };
  onProceed: () => void;
}

export default function DiagnosticResults({ results, onProceed }: DiagnosticResultsProps) {
  // Destructure results safely
  const {
    academic_accuracy = 0,
    aptitude_score = 0,
    aptitude_percentile = 0,
    study_health_score = 0,
    category_scores = {},
  } = results || {};

  return (
    <div className="max-w-4xl mx-auto py-12 px-4 space-y-10">
      {/* Hero Header */}
      <div className="text-center space-y-4">
        <div className="mx-auto w-16 h-16 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mb-2">
          <CheckCircle2 size={36} className="text-emerald-500 dark:text-emerald-400" />
        </div>
        <h1 className="text-3xl md:text-4xl font-extrabold font-outfit tracking-tight text-slate-900 dark:text-slate-100">
          Diagnostic Assessment Complete
        </h1>
        <p className="text-slate-650 dark:text-slate-400 text-sm max-w-xl mx-auto font-light leading-relaxed">
          Your diagnostic answers have been analyzed by the adaptive scheduler. Here is your profile summary before accessing the planner.
        </p>
      </div>

      {/* Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="glass-dark rounded-2xl p-6 text-center space-y-2.5 glow-purple border border-slate-200/40 dark:border-slate-800/40">
          <span className="block text-[10px] uppercase tracking-widest font-semibold text-slate-500 dark:text-slate-400">Study Health</span>
          <span className="block text-3xl font-extrabold font-outfit text-violet-600 dark:text-violet-300">
            {parseFloat(study_health_score as any).toFixed(1)}%
          </span>
          <p className="text-[11px] text-slate-600 dark:text-slate-500 font-light leading-snug">
            Your general baseline readiness index
          </p>
        </div>

        <div className="glass-dark rounded-2xl p-6 text-center space-y-2.5 glow-purple border border-slate-200/40 dark:border-slate-800/40">
          <span className="block text-[10px] uppercase tracking-widest font-semibold text-slate-500 dark:text-slate-400">Academic Accuracy</span>
          <span className="block text-3xl font-extrabold font-outfit text-fuchsia-600 dark:text-fuchsia-300">
            {parseFloat(academic_accuracy as any).toFixed(1)}%
          </span>
          <p className="text-[11px] text-slate-600 dark:text-slate-500 font-light leading-snug">
            Baseline accuracy across subjects
          </p>
        </div>

        <div className="glass-dark rounded-2xl p-6 text-center space-y-2.5 glow-purple border border-slate-200/40 dark:border-slate-800/40">
          <span className="block text-[10px] uppercase tracking-widest font-semibold text-slate-500 dark:text-slate-400">Aptitude Score</span>
          <span className="block text-3xl font-extrabold font-outfit text-blue-600 dark:text-blue-300">
            {parseFloat(aptitude_score as any).toFixed(1)}%
          </span>
          <p className="text-[11px] text-slate-600 dark:text-slate-500 font-light leading-snug">
            Cognitive test raw score
          </p>
        </div>

        <div className="glass-dark rounded-2xl p-6 text-center space-y-2.5 glow-purple border border-slate-200/40 dark:border-slate-800/40">
          <span className="block text-[10px] uppercase tracking-widest font-semibold text-slate-500 dark:text-slate-400">Aptitude Percentile</span>
          <span className="block text-3xl font-extrabold font-outfit text-teal-605 dark:text-teal-300">
            {parseFloat(aptitude_percentile as any).toFixed(1)}th
          </span>
          <p className="text-[11px] text-slate-600 dark:text-slate-500 font-light leading-snug">
            Ranked against peer benchmarks
          </p>
        </div>
      </div>

      {/* Details Box */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left column: Info panel */}
        <div className="lg:col-span-1 space-y-6">
          <div className="glass-dark rounded-2xl p-6 border border-slate-200 dark:border-slate-800 space-y-4">
            <h3 className="text-md font-bold font-outfit text-slate-800 dark:text-slate-200 flex items-center gap-2">
              <Shield size={16} className="text-violet-650 dark:text-violet-400" />
              What this means
            </h3>
            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed font-light">
              Your academic scores are used to identify weak chapters and initialize baseline mastery values in the spaced repetition database.
            </p>
            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed font-light">
              Aptitude scores provide cognitive analysis in the "Gap Analysis" dashboard tab but do not directly restrict your curriculum study pace.
            </p>
          </div>

          <div className="glass-dark rounded-2xl p-6 border border-amber-250 dark:border-amber-950/30 bg-amber-50 dark:bg-amber-950/5 space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-amber-700 dark:text-amber-400 flex items-center gap-1.5">
              <AlertTriangle size={14} /> Spaced Repetition Active
            </h4>
            <p className="text-[11px] text-slate-650 dark:text-slate-400 leading-relaxed font-light">
              The SM-2 study algorithms will automatically schedule revisions for chapters you missed to bring them back to high confidence.
            </p>
          </div>
        </div>

        {/* Right column: Category scores */}
        <div className="lg:col-span-2 glass-dark rounded-2xl p-6 md:p-8 border border-slate-200 dark:border-slate-800 space-y-6">
          <h3 className="text-md font-bold font-outfit text-slate-800 dark:text-slate-200 flex items-center gap-2">
            <Brain size={18} className="text-blue-600 dark:text-blue-400" />
            Cognitive Category Breakdown
          </h3>

          <div className="space-y-4">
            {Object.keys(category_scores).length === 0 ? (
              <p className="text-xs text-slate-500 italic py-4">No categories recorded.</p>
            ) : (
              Object.entries(category_scores).map(([category, score]) => (
                <div key={category} className="bg-white/70 dark:bg-slate-900/40 rounded-xl p-4 border border-slate-200 dark:border-slate-850 flex justify-between items-center gap-4 hover:border-slate-350 dark:hover:border-slate-800 transition">
                  <div className="space-y-0.5">
                    <span className="text-xs font-bold text-slate-800 dark:text-slate-200 font-outfit">{category}</span>
                  </div>
                  <div className="flex gap-4 text-center">
                    <div className="min-w-[70px] bg-slate-50 dark:bg-slate-950/40 rounded-lg py-1 px-2 border border-slate-200 dark:border-slate-800/80">
                      <span className="block text-[8px] uppercase font-semibold text-slate-500">Accuracy</span>
                      <span className="text-xs font-bold font-mono text-violet-600 dark:text-violet-300">{score.accuracy}%</span>
                    </div>
                    <div className="min-w-[70px] bg-slate-50 dark:bg-slate-950/40 rounded-lg py-1 px-2 border border-slate-200 dark:border-slate-800/80">
                      <span className="block text-[8px] uppercase font-semibold text-slate-500">Percentile</span>
                      <span className="text-xs font-bold font-mono text-blue-600 dark:text-blue-300">{score.percentile}th</span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Proceed button */}
      <div className="text-center pt-4">
        <button
          onClick={onProceed}
          className="group relative inline-flex items-center gap-3 bg-gradient-to-r from-violet-600 to-blue-600 hover:from-violet-500 hover:to-blue-500 text-white font-bold rounded-2xl px-12 py-4 text-base shadow-2xl shadow-violet-950/40 transition hover:scale-[1.02] hover:shadow-violet-900/50"
        >
          Proceed to Study Planner
          <ArrowRight size={16} className="transition-transform group-hover:translate-x-1" />
        </button>
      </div>
    </div>
  );
}
