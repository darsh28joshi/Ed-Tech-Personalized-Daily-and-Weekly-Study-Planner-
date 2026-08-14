import React from 'react';
import { Play, Clock, BookOpen, Brain, ArrowRight, CheckCircle, SkipForward, ArrowLeft, Shield } from 'lucide-react';

interface DiagnosticLandingProps {
  onStart: () => void;
}

export default function DiagnosticLanding({ onStart }: DiagnosticLandingProps) {
  return (
    <div className="max-w-4xl mx-auto py-16 px-4">
      {/* Hero Section */}
      <div className="text-center space-y-5 mb-14">
        <div className="inline-flex items-center gap-2 bg-violet-50 dark:bg-violet-950/30 border border-violet-200 dark:border-violet-500/20 px-4 py-1.5 rounded-full text-xs font-semibold text-violet-700 dark:text-violet-400 uppercase tracking-widest">
          <Shield size={12} /> Adaptive Assessment
        </div>
        <h1 className="text-4xl md:text-5xl font-extrabold font-outfit tracking-tight text-slate-900 dark:text-slate-100">
          Diagnostic Assessment
        </h1>
        <p className="text-slate-650 dark:text-slate-400 text-base md:text-lg max-w-2xl mx-auto leading-relaxed font-light">
          This assessment maps your current knowledge across all subjects and identifies areas
          where you shine — and where you can grow. Your personalised study plan is built from these results.
        </p>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-12">
        <div className="glass-dark rounded-2xl p-6 text-center space-y-3 glow-purple hover:scale-[1.02] transition-transform duration-205 border border-slate-200/40 dark:border-slate-800/40">
          <div className="mx-auto w-12 h-12 rounded-xl bg-violet-600/20 border border-violet-500/30 flex items-center justify-center">
            <BookOpen className="text-violet-600 dark:text-violet-400" size={22} />
          </div>
          <h3 className="text-2xl font-bold font-outfit text-slate-900 dark:text-slate-100">49</h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 uppercase tracking-wider font-semibold">Questions</p>
          <p className="text-[11px] text-slate-600 dark:text-slate-500 leading-relaxed">
            7 sections of 7 questions each (Aptitude + 6 Academic subjects)
          </p>
        </div>

        <div className="glass-dark rounded-2xl p-6 text-center space-y-3 glow-purple hover:scale-[1.02] transition-transform duration-205 border border-slate-200/40 dark:border-slate-800/40">
          <div className="mx-auto w-12 h-12 rounded-xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center">
            <Clock className="text-blue-600 dark:text-blue-400" size={22} />
          </div>
          <h3 className="text-2xl font-bold font-outfit text-slate-900 dark:text-slate-100">~35 min</h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 uppercase tracking-wider font-semibold">Estimated Duration</p>
          <p className="text-[11px] text-slate-600 dark:text-slate-500 leading-relaxed">
            Take your time — there is no hard time limit on any question
          </p>
        </div>

        <div className="glass-dark rounded-2xl p-6 text-center space-y-3 glow-purple hover:scale-[1.02] transition-transform duration-205 border border-slate-200/40 dark:border-slate-800/40">
          <div className="mx-auto w-12 h-12 rounded-xl bg-fuchsia-600/20 border border-fuchsia-500/30 flex items-center justify-center">
            <Brain className="text-fuchsia-600 dark:text-fuchsia-400" size={22} />
          </div>
          <h3 className="text-2xl font-bold font-outfit text-slate-900 dark:text-slate-100">Adaptive</h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 uppercase tracking-wider font-semibold">Smart Scoring</p>
          <p className="text-[11px] text-slate-600 dark:text-slate-500 leading-relaxed">
            Results feed your personalised study plan and mastery tracker
          </p>
        </div>
      </div>

      <div className="glass-dark rounded-3xl p-8 md:p-10 mb-10 space-y-6 border border-slate-200/40 dark:border-slate-800/40">
        <h2 className="text-lg font-bold font-outfit text-slate-900 dark:text-slate-200 flex items-center gap-2">
          <CheckCircle size={18} className="text-violet-600 dark:text-violet-400" />
          Before You Begin
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex items-start gap-3 bg-white/60 dark:bg-slate-900/40 rounded-xl p-4 border border-slate-200 dark:border-slate-800/50">
            <div className="mt-0.5 h-6 w-6 rounded-lg bg-violet-600/20 flex items-center justify-center shrink-0">
              <ArrowRight size={12} className="text-violet-600 dark:text-violet-400" />
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-800 dark:text-slate-300">Navigate freely</p>
              <p className="text-xs text-slate-550 dark:text-slate-500 mt-0.5">Use Previous and Next buttons to move between questions at any time.</p>
            </div>
          </div>

          <div className="flex items-start gap-3 bg-white/60 dark:bg-slate-900/40 rounded-xl p-4 border border-slate-200 dark:border-slate-800/50">
            <div className="mt-0.5 h-6 w-6 rounded-lg bg-blue-600/20 flex items-center justify-center shrink-0">
              <SkipForward size={12} className="text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-800 dark:text-slate-300">Skip if unsure</p>
              <p className="text-xs text-slate-550 dark:text-slate-500 mt-0.5">No question is compulsory. Skip any question you're not sure about.</p>
            </div>
          </div>

          <div className="flex items-start gap-3 bg-white/60 dark:bg-slate-900/40 rounded-xl p-4 border border-slate-200 dark:border-slate-800/50">
            <div className="mt-0.5 h-6 w-6 rounded-lg bg-emerald-600/20 flex items-center justify-center shrink-0">
              <Clock size={12} className="text-emerald-600 dark:text-emerald-400" />
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-800 dark:text-slate-300">No time pressure</p>
              <p className="text-xs text-slate-550 dark:text-slate-500 mt-0.5">Each question has its own timer, but it's only for analytics — take as long as you need.</p>
            </div>
          </div>

          <div className="flex items-start gap-3 bg-white/60 dark:bg-slate-900/40 rounded-xl p-4 border border-slate-200 dark:border-slate-800/50">
            <div className="mt-0.5 h-6 w-6 rounded-lg bg-amber-600/20 flex items-center justify-center shrink-0">
              <ArrowLeft size={12} className="text-amber-600 dark:text-amber-405" />
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-800 dark:text-slate-300">Change your answers</p>
              <p className="text-xs text-slate-550 dark:text-slate-500 mt-0.5">Go back to any previous question and change your selection before submitting.</p>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Button */}
      <div className="text-center">
        <button
          id="start-diagnostic-btn"
          onClick={onStart}
          className="group relative inline-flex items-center gap-3 bg-gradient-to-r from-violet-600 to-blue-600 hover:from-violet-500 hover:to-blue-500 text-white font-bold rounded-2xl px-10 py-4 text-lg shadow-2xl shadow-violet-950/40 transition-all duration-200 hover:scale-[1.03] hover:shadow-violet-900/50"
        >
          <Play size={20} className="transition-transform group-hover:scale-110" />
          Start Diagnostic Test
          <ArrowRight size={18} className="transition-transform group-hover:translate-x-1" />
        </button>
        <p className="text-xs text-slate-600 mt-4">
          You can complete this in one sitting or come back later.
        </p>
      </div>
    </div>
  );
}
