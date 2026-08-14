import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Award, Clock, ArrowRight, ArrowLeft, BookOpen, AlertCircle, HelpCircle, SkipForward } from 'lucide-react';

interface Question {
  diagnostic_question_id: number;
  question_id: number;
  source: string;
  section: string;
  order: number;
  question_text: string;
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
}

interface AnswerRecord {
  question_id: number;
  source: string;
  selected_option: string | null;
  time_taken_seconds: number;
}

interface DiagnosticProps {
  studentId: number;
  entryPoint: string;
  onComplete: (sessionId: number, reportData?: any) => void;
}

export default function Diagnostic({ studentId, entryPoint, onComplete }: DiagnosticProps) {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [activeSection, setActiveSection] = useState<string>("Aptitude section");
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  // Map-based answer state: keyed by question_id
  const [answersMap, setAnswersMap] = useState<Record<number, AnswerRecord>>({});
  // Map-based timer state: accumulated seconds per question_id
  const [timerMap, setTimerMap] = useState<Record<number, number>>({});

  // Per-question timer
  const [seconds, setSeconds] = useState(0);
  const timerRef = useRef<any>(null);

  // Session ID from API
  const [sessionIdStore, setSessionIdStore] = useState<number>(0);
  const initiatedRef = useRef(false);

  const SECTIONS = [
    "Aptitude section",
    "Mathematics",
    "Science",
    "History and Civics",
    "Geography",
    "Hindi",
    "Marathi"
  ];

  // Get questions filtered for current active section
  const activeQuestions = questions.filter(q => q.section === activeSection);

  // Start or resume timer for current question
  const startTimer = useCallback(() => {
    if (timerRef.current) clearInterval(timerRef.current);
    timerRef.current = setInterval(() => {
      setSeconds((prev) => prev + 1);
    }, 1000);
  }, []);

  const stopTimer = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  // Save current question state before navigating away
  const saveCurrentState = useCallback(() => {
    if (questions.length === 0 || activeQuestions.length === 0) return;
    const currentQ = activeQuestions[currentIndex];
    if (!currentQ) return;
    // Save accumulated time
    setTimerMap((prev) => ({ ...prev, [currentQ.question_id]: seconds }));
    // Save answer if selected
    if (selectedOption !== null) {
      setAnswersMap((prev) => ({
        ...prev,
        [currentQ.question_id]: {
          question_id: currentQ.question_id,
          source: currentQ.source,
          selected_option: selectedOption,
          time_taken_seconds: seconds,
        },
      }));
    }
  }, [questions, activeQuestions, currentIndex, selectedOption, seconds]);

  // Submit all answers
  const handleSubmit = useCallback(async () => {
    if (activeQuestions.length === 0) return;
    // Save current question first
    const currentQ = activeQuestions[currentIndex];
    const finalAnswersMap = {
      ...answersMap,
      [currentQ.question_id]: {
        question_id: currentQ.question_id,
        source: currentQ.source,
        selected_option: selectedOption,
        time_taken_seconds: seconds,
      },
    };

    // Convert map to array for all questions
    const responsesArray = questions.map((q) => {
      const ans = finalAnswersMap[q.question_id];
      return {
        question_id: q.question_id,
        source: q.source,
        selected_option: ans?.selected_option ?? null,
        time_taken_seconds: ans?.time_taken_seconds ?? 0,
      };
    });

    setSubmitting(true);
    stopTimer();

    try {
      const response = await fetch('http://127.0.0.1:8001/diagnostic/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionIdStore,
          responses: responsesArray,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to submit diagnostic test results.');
      }

      const data = await response.json();
      onComplete(data.session_id, data);
    } catch (err: any) {
      setError(err.message || 'Submission failed.');
      setSubmitting(false);
    }
  }, [questions, activeQuestions, currentIndex, selectedOption, seconds, answersMap, sessionIdStore, onComplete, stopTimer]);

  // Navigate to next question or section
  const handleNext = useCallback(() => {
    if (activeQuestions.length === 0) return;
    saveCurrentState();

    const currentQ = activeQuestions[currentIndex];
    const newAnswers = {
      ...answersMap,
      [currentQ.question_id]: {
        question_id: currentQ.question_id,
        source: currentQ.source,
        selected_option: selectedOption,
        time_taken_seconds: seconds,
      }
    };
    setAnswersMap(newAnswers);
    setTimerMap((prev) => ({ ...prev, [currentQ.question_id]: seconds }));

    if (currentIndex + 1 < activeQuestions.length) {
      const nextIndex = currentIndex + 1;
      setCurrentIndex(nextIndex);
      const nextQ = activeQuestions[nextIndex];
      setSelectedOption(newAnswers[nextQ.question_id]?.selected_option ?? null);
      setSeconds(timerMap[nextQ.question_id] || 0);
    } else {
      // End of section! Advance to next section if there is one
      const currentSecIdx = SECTIONS.indexOf(activeSection);
      if (currentSecIdx + 1 < SECTIONS.length) {
        const nextSec = SECTIONS[currentSecIdx + 1];
        setActiveSection(nextSec);
        setCurrentIndex(0);
        const nextSecQs = questions.filter(q => q.section === nextSec);
        const firstQ = nextSecQs[0];
        if (firstQ) {
          setSelectedOption(newAnswers[firstQ.question_id]?.selected_option ?? null);
          setSeconds(timerMap[firstQ.question_id] || 0);
        }
      } else {
        // Last question of last section -> submit
        handleSubmit();
      }
    }
  }, [questions, activeQuestions, currentIndex, selectedOption, seconds, answersMap, timerMap, activeSection, saveCurrentState, handleSubmit]);

  // Navigate to previous question or section
  const handlePrevious = useCallback(() => {
    if (activeQuestions.length === 0) return;
    saveCurrentState();

    const currentQ = activeQuestions[currentIndex];
    const newAnswers = {
      ...answersMap,
      [currentQ.question_id]: {
        question_id: currentQ.question_id,
        source: currentQ.source,
        selected_option: selectedOption,
        time_taken_seconds: seconds,
      }
    };
    setAnswersMap(newAnswers);
    setTimerMap((prev) => ({ ...prev, [currentQ.question_id]: seconds }));

    if (currentIndex > 0) {
      const prevIndex = currentIndex - 1;
      setCurrentIndex(prevIndex);
      const prevQ = activeQuestions[prevIndex];
      setSelectedOption(newAnswers[prevQ.question_id]?.selected_option ?? null);
      setSeconds(timerMap[prevQ.question_id] || 0);
    } else {
      // Start of section! Go to previous section if there is one
      const currentSecIdx = SECTIONS.indexOf(activeSection);
      if (currentSecIdx > 0) {
        const prevSec = SECTIONS[currentSecIdx - 1];
        setActiveSection(prevSec);
        const prevSecQs = questions.filter(q => q.section === prevSec);
        const lastIdx = prevSecQs.length - 1;
        setCurrentIndex(lastIdx);
        const lastQ = prevSecQs[lastIdx];
        if (lastQ) {
          setSelectedOption(newAnswers[lastQ.question_id]?.selected_option ?? null);
          setSeconds(timerMap[lastQ.question_id] || 0);
        }
      }
    }
  }, [questions, activeQuestions, currentIndex, selectedOption, seconds, answersMap, timerMap, activeSection, saveCurrentState]);

  // Skip current question (record as null answer)
  const handleSkip = useCallback(() => {
    if (activeQuestions.length === 0) return;
    const currentQ = activeQuestions[currentIndex];
    
    const newAnswers = {
      ...answersMap,
      [currentQ.question_id]: {
        question_id: currentQ.question_id,
        source: currentQ.source,
        selected_option: null,
        time_taken_seconds: seconds,
      }
    };
    setAnswersMap(newAnswers);
    setTimerMap((prev) => ({ ...prev, [currentQ.question_id]: seconds }));

    if (currentIndex + 1 < activeQuestions.length) {
      const nextIndex = currentIndex + 1;
      setCurrentIndex(nextIndex);
      const nextQ = activeQuestions[nextIndex];
      setSelectedOption(newAnswers[nextQ.question_id]?.selected_option ?? null);
      setSeconds(timerMap[nextQ.question_id] || 0);
    } else {
      // End of section! Advance to next section if there is one
      const currentSecIdx = SECTIONS.indexOf(activeSection);
      if (currentSecIdx + 1 < SECTIONS.length) {
        const nextSec = SECTIONS[currentSecIdx + 1];
        setActiveSection(nextSec);
        setCurrentIndex(0);
        const nextSecQs = questions.filter(q => q.section === nextSec);
        const firstQ = nextSecQs[0];
        if (firstQ) {
          setSelectedOption(newAnswers[firstQ.question_id]?.selected_option ?? null);
          setSeconds(timerMap[firstQ.question_id] || 0);
        }
      } else {
        // Last question of last section -> submit
        handleSubmit();
      }
    }
  }, [questions, activeQuestions, currentIndex, seconds, answersMap, timerMap, activeSection, handleSubmit]);

  // Initial session load
  useEffect(() => {
    if (initiatedRef.current) return;
    initiatedRef.current = true;

    const initSessionWithStore = async () => {
      try {
        const response = await fetch('http://127.0.0.1:8001/diagnostic/start', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ student_id: studentId }),
        });

        if (!response.ok) {
          const errData = await response.json();
          throw new Error(errData.detail || 'Could not initiate diagnostic test');
        }

        const data = await response.json();
        setSessionIdStore(data.session_id);
        localStorage.setItem('sessionId', data.session_id.toString());

        if (data.questions.length === 0) {
          localStorage.setItem('diagnosticCompleted', 'true');
          onComplete(data.session_id);
          return;
        }

        setQuestions(data.questions);
      } catch (err: any) {
        setError(err.message || 'Failed to fetch diagnostic questions.');
      } finally {
        setLoading(false);
      }
    };

    initSessionWithStore();
  }, [studentId]);

  // Restart timer on question/section change
  useEffect(() => {
    if (activeQuestions.length > 0) {
      startTimer();
    }
    return () => stopTimer();
  }, [currentIndex, activeSection, questions.length, startTimer, stopTimer]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-24 space-y-4">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-violet-500"></div>
        <p className="text-slate-400 font-light">Loading adaptive question bank...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-xl mx-auto py-16 text-center space-y-6">
        <AlertCircle className="mx-auto text-red-500" size={48} />
        <h3 className="text-xl font-bold font-outfit text-slate-200">Diagnostic Assessment Error</h3>
        <p className="text-slate-400 text-sm">{error}</p>
        <button
          onClick={() => window.location.reload()}
          className="bg-violet-600 hover:bg-violet-500 text-white rounded-xl px-6 py-2 transition"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!activeQuestions || activeQuestions.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-24 space-y-4">
        <p className="text-slate-400 font-light">Loading section questions...</p>
      </div>
    );
  }

  const currentQuestion = activeQuestions[currentIndex];
  const progressPercent = Math.round(((currentIndex + 1) / activeQuestions.length) * 100);
  
  const currentSecIdx = SECTIONS.indexOf(activeSection);
  const isFirstQuestion = currentIndex === 0 && currentSecIdx === 0;
  const isLastQuestionOfTest = currentIndex + 1 === activeQuestions.length && currentSecIdx === SECTIONS.length - 1;

  return (
    <div className="max-w-3xl mx-auto py-12 px-4">
      {/* Section Navigation Tabs */}
      <div className="flex gap-2 mb-6 overflow-x-auto pb-2 scrollbar-thin">
        {SECTIONS.map((sec) => {
          const secQs = questions.filter(q => q.section === sec);
          const answeredSecCount = secQs.filter(q => answersMap[q.question_id]?.selected_option !== null && answersMap[q.question_id]?.selected_option !== undefined).length;
          const isActive = activeSection === sec;
          
          return (
            <button
              key={sec}
              onClick={() => {
                saveCurrentState();
                
                // Save current question's state explicitly before jumping
                if (activeQuestions.length > 0) {
                  const curQ = activeQuestions[currentIndex];
                  setAnswersMap((prev) => ({
                    ...prev,
                    [curQ.question_id]: {
                      question_id: curQ.question_id,
                      source: curQ.source,
                      selected_option: selectedOption,
                      time_taken_seconds: seconds,
                    },
                  }));
                  setTimerMap((prev) => ({ ...prev, [curQ.question_id]: seconds }));
                }

                setActiveSection(sec);
                setCurrentIndex(0);
                const nextSecQs = questions.filter(q => q.section === sec);
                const firstQ = nextSecQs[0];
                if (firstQ) {
                  setSelectedOption(answersMap[firstQ.question_id]?.selected_option ?? null);
                  setSeconds(timerMap[firstQ.question_id] || 0);
                }
              }}
              className={`px-4 py-2.5 rounded-2xl text-xs font-bold whitespace-nowrap transition-all border duration-200 ${
                isActive
                  ? 'bg-gradient-to-r from-violet-600 to-blue-600 border-violet-500 text-white shadow-lg scale-[1.02]'
                  : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-850 hover:border-slate-300 dark:hover:border-slate-700'
              }`}
            >
              {sec} ({answeredSecCount}/{secQs.length})
            </button>
          );
        })}
      </div>

      {/* Header and Progress */}
      <div className="flex justify-between items-center mb-4">
        <span className="text-xs uppercase tracking-wider font-semibold text-slate-750 dark:text-slate-400 bg-slate-200 dark:bg-slate-800 px-3 py-1 rounded-full flex items-center gap-1.5">
          <BookOpen size={12} /> {activeSection} BLOCK ({currentIndex + 1}/{activeQuestions.length})
        </span>
        <span className="text-xs font-mono text-slate-750 dark:text-slate-400 bg-slate-200 dark:bg-slate-800 px-3 py-1 rounded-full flex items-center gap-1.5">
          <Clock size={12} /> Timer: {seconds}s
        </span>
      </div>

      {/* Question Progress Dots */}
      <div className="flex gap-1.5 mb-4 flex-wrap justify-center">
        {activeQuestions.map((q, idx) => {
          const ans = answersMap[q.question_id];
          const isCurrent = idx === currentIndex;
          let dotColor = 'bg-slate-300 dark:bg-slate-700'; // unanswered
          if (ans) {
            dotColor = ans.selected_option !== null ? 'bg-violet-500' : 'bg-amber-500'; // answered vs skipped
          }
          if (isCurrent) {
            dotColor = 'bg-slate-900 dark:bg-white ring-2 ring-violet-400';
          }
          return (
            <button
              key={q.question_id}
              onClick={() => {
                saveCurrentState();
                
                const curQ = activeQuestions[currentIndex];
                const newAnswers = {
                  ...answersMap,
                  [curQ.question_id]: {
                    question_id: curQ.question_id,
                    source: curQ.source,
                    selected_option: selectedOption,
                    time_taken_seconds: seconds,
                  }
                };
                setAnswersMap(newAnswers);
                setTimerMap((prev) => ({ ...prev, [curQ.question_id]: seconds }));
                
                setCurrentIndex(idx);
                const targetAns = newAnswers[q.question_id];
                setSelectedOption(targetAns?.selected_option ?? null);
                setSeconds(timerMap[q.question_id] || 0);
              }}
              className={`w-2.5 h-2.5 rounded-full transition-all duration-200 hover:scale-150 ${dotColor}`}
              title={`Question ${idx + 1}`}
            />
          );
        })}
      </div>

      <div className="w-full bg-slate-200 dark:bg-slate-800 rounded-full h-1.5 mb-8">
        <div
          className="bg-gradient-to-r from-violet-500 to-blue-500 h-1.5 rounded-full transition-all duration-300"
          style={{ width: `${progressPercent}%` }}
        ></div>
      </div>

      {/* Main card */}
      <div className="glass-dark rounded-3xl p-8 md:p-10 shadow-2xl glow-purple space-y-8 border border-slate-200/40 dark:border-slate-800/40">
        <div className="space-y-4">
          <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 font-outfit leading-relaxed">
            {currentQuestion.question_text}
          </h2>
        </div>

        {/* Options */}
        <div className="grid grid-cols-1 gap-4">
          {[
            { key: 'A', text: currentQuestion.option_a },
            { key: 'B', text: currentQuestion.option_b },
            { key: 'C', text: currentQuestion.option_c },
            { key: 'D', text: currentQuestion.option_d },
          ].map((opt) => {
            if (!opt.text) return null;
            const isSelected = selectedOption === opt.key;
            return (
              <button
                key={opt.key}
                onClick={() => setSelectedOption(opt.key)}
                className={`w-full text-left p-5 rounded-2xl border transition duration-150 flex items-center justify-between ${
                  isSelected
                    ? 'bg-violet-50 dark:bg-violet-950/40 border-violet-500 text-violet-800 dark:text-violet-200 font-semibold'
                    : 'bg-white dark:bg-slate-900/40 border-slate-200 dark:border-slate-700/50 hover:border-slate-400 dark:hover:border-slate-600 text-slate-700 dark:text-slate-300'
                }`}
              >
                <div className="flex items-center gap-4">
                  <span
                    className={`h-8 w-8 rounded-xl flex items-center justify-center font-bold text-sm ${
                      isSelected
                        ? 'bg-violet-600 text-white'
                        : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-transparent'
                    }`}
                  >
                    {opt.key}
                  </span>
                  <span className="text-sm font-medium">{opt.text}</span>
                </div>
              </button>
            );
          })}
        </div>

        {/* Action Buttons */}
        <div className="flex justify-between items-center pt-4 border-t border-slate-200 dark:border-slate-800">
          <div className="flex gap-3">
            {/* Previous */}
            <button
              onClick={handlePrevious}
              disabled={isFirstQuestion}
              className="flex items-center gap-2 text-sm font-semibold text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 rounded-xl px-5 py-3 border border-slate-200 dark:border-slate-800 hover:border-slate-350 dark:hover:border-slate-700 bg-white dark:bg-slate-900/20 transition disabled:opacity-30 disabled:pointer-events-none"
            >
              <ArrowLeft size={16} />
              Previous
            </button>

            {/* End Test */}
            <button
              onClick={() => {
                if (window.confirm("Are you sure you want to end the test early? Your answers so far will be submitted and graded.")) {
                  handleSubmit();
                }
              }}
              disabled={submitting}
              className="flex items-center gap-2 text-sm font-semibold text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 rounded-xl px-5 py-3 border border-red-200 dark:border-red-800/40 hover:border-red-350 dark:hover:border-red-700 bg-red-50/50 dark:bg-red-950/10 transition disabled:opacity-30"
            >
              End Test
            </button>
          </div>

          <div className="flex gap-3">
            {/* Skip */}
            {!isLastQuestionOfTest && (
              <button
                onClick={handleSkip}
                className="flex items-center gap-2 text-sm font-semibold text-amber-700 dark:text-amber-300 rounded-xl px-5 py-3 border border-amber-300 dark:border-amber-500/20 bg-amber-50 dark:bg-amber-950/10 hover:bg-amber-100 dark:hover:bg-amber-950/20 transition animate-in fade-in"
              >
                <SkipForward size={14} />
                Skip
              </button>
            )}

            {/* Next / Submit */}
            {isLastQuestionOfTest ? (
              <button
                onClick={handleSubmit}
                disabled={submitting}
                className="bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-semibold rounded-xl px-8 py-3 shadow-lg flex items-center gap-2 transition disabled:opacity-50 disabled:pointer-events-none"
              >
                {submitting ? 'Submitting...' : 'Submit Assessment'}
                <ArrowRight size={16} />
              </button>
            ) : (
              <button
                onClick={handleNext}
                className="bg-gradient-to-r from-violet-600 to-blue-600 hover:from-violet-500 hover:to-blue-600 text-white font-semibold rounded-xl px-8 py-3 shadow-lg hover:shadow-violet-950/40 flex items-center gap-2 transition"
              >
                Next Question
                <ArrowRight size={16} />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Status Bar */}
      <div className="flex justify-center gap-6 mt-6 text-xs text-slate-650 dark:text-slate-500">
        <span className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-violet-500 inline-block"></span>
          Answered
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-amber-500 inline-block"></span>
          Skipped
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-slate-300 dark:bg-slate-700 inline-block"></span>
          Unanswered
        </span>
      </div>
    </div>
  );
}
