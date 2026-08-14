import React, { useState, useEffect, useRef } from 'react';
import { Calendar, CheckCircle2, Circle, AlertTriangle, Lightbulb, TrendingUp, RefreshCw, BarChart2, BookOpen, Clock, User, Settings, Star } from 'lucide-react';

interface Task {
  task_id: number;
  chapter_id: number;
  chapter_name: string;
  subject_name: string;
  allocated_minutes: number;
  status: string;
  start_time?: string;
  end_time?: string;
}

interface DayPlan {
  day_number: number;
  allocated_minutes: number;
  capacity_minutes: number;
  tasks: Array<{
    chapter_id: number;
    chapter_name: string;
    subject_name: string;
    cost: number;
  }>;
}

interface GapSuggestion {
  category: string;
  accuracy: number;
  suggestion: string;
}

interface DashboardProps {
  studentId: number;
  sessionId: number;
  profileVersion: number;
}

// Helper: parse "hh:mm AM/PM" into a Date object for today (for time comparison)
function parseTimeToToday(timeStr: string | undefined): Date | null {
  if (!timeStr) return null;
  const match = timeStr.match(/^(\d{1,2}):(\d{2})\s*(AM|PM)$/i);
  if (!match) return null;
  let hours = parseInt(match[1], 10);
  const minutes = parseInt(match[2], 10);
  const ampm = match[3].toUpperCase();
  if (ampm === 'PM' && hours !== 12) hours += 12;
  if (ampm === 'AM' && hours === 12) hours = 0;
  const d = new Date();
  d.setHours(hours, minutes, 0, 0);
  return d;
}

// Completion confirmation state
interface CompletionFormState {
  taskId: number;
  chapterName: string;
  subjectName: string;
  startTime?: string;
  endTime?: string;
  rating: number;      // 0 = unset, 1-5 stars
  notes: string;
}

export default function Dashboard({ studentId, sessionId, profileVersion }: DashboardProps) {
  const initiatedRef = useRef(false);
  const [activeTab, setActiveTab] = useState<'daily' | 'weekly' | 'gap'>('daily');
  const [dailyTasks, setDailyTasks] = useState<Task[]>([]);
  const [weeklyPlan, setWeeklyPlan] = useState<DayPlan[]>([]);
  const [gapSuggestions, setGapSuggestions] = useState<GapSuggestion[]>([]);
  const [reportCard, setReportCard] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [strategy, setStrategy] = useState<'knapsack' | 'greedy'>('knapsack');

  // Completion confirmation form
  const [completionForm, setCompletionForm] = useState<CompletionFormState | null>(null);

  // Current time (refreshed every 30s for active-task detection)
  const [now, setNow] = useState(new Date());
  useEffect(() => {
    const interval = setInterval(() => setNow(new Date()), 30000);
    return () => clearInterval(interval);
  }, []);

  const todayStr = '2026-08-12'; // Default plan_date corresponding to system time

  const fetchDailyPlan = async (strat: 'knapsack' | 'greedy', forceRegen: boolean = false) => {
    try {
      const response = await fetch('http://127.0.0.1:8001/planner/daily', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          student_id: studentId,
          plan_date: todayStr,
          strategy: strat,
          force_regenerate: forceRegen
        }),
      });
      if (!response.ok) throw new Error('Failed to load daily plan.');
      const data = await response.json();
      setDailyTasks(data.tasks);
    } catch (err: any) {
      setError(err.message || 'Connection error.');
    }
  };

  const fetchWeeklyPlan = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8001/planner/weekly', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ student_id: studentId }),
      });
      if (!response.ok) throw new Error('Failed to load weekly plan.');
      const data = await response.json();
      setWeeklyPlan(data.days);
    } catch (err: any) {
      setError(err.message || 'Connection error.');
    }
  };

  const fetchGapAnalysis = async () => {
    try {
      const response = await fetch(`http://127.0.0.1:8001/diagnostic/${sessionId}/gap-analysis`);
      if (!response.ok) throw new Error('No gap analysis available yet.');
      const data = await response.json();
      setGapSuggestions(data.suggestions);
    } catch (err: any) {
      // Opt-in analysis might not be initialized
      setGapSuggestions([]);
    }
  };

  const fetchDiagnosticReport = async () => {
    try {
      const response = await fetch(`http://127.0.0.1:8001/diagnostic/${sessionId}/report`);
      if (response.ok) {
        const data = await response.json();
        setReportCard(data);
      }
    } catch (err) {
      // Report card optional
    }
  };

  // Profile functions removed (moved to App.tsx)

  useEffect(() => {
    if (initiatedRef.current) return;
    initiatedRef.current = true;

    const initDashboard = async () => {
      setLoading(true);
      await Promise.all([
        fetchDailyPlan(strategy),
        fetchWeeklyPlan(),
        fetchGapAnalysis(),
        fetchDiagnosticReport()
      ]);
      setLoading(false);
    };
    initDashboard();
  }, [studentId, sessionId]);

  useEffect(() => {
    // Dynamically re-pack planner whenever profileVersion is updated
    if (profileVersion > 0) {
      const reloadDashboardPlans = async () => {
        setLoading(true);
        await Promise.all([
          fetchDailyPlan(strategy, true), // Force regeneration on hours/settings edits!
          fetchWeeklyPlan()
        ]);
        setLoading(false);
      };
      reloadDashboardPlans();
    }
  }, [profileVersion]);

  const handleStatusChange = async (taskId: number, newStatus: string) => {
    try {
      const response = await fetch(`http://127.0.0.1:8001/planner/daily/task/${taskId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus }),
      });
      if (!response.ok) throw new Error('Failed to update task.');

      // Update locally
      setDailyTasks((prev) =>
        prev.map((t) => (t.task_id === taskId ? { ...t, status: newStatus } : t))
      );

      // Re-trigger weekly re-pack locally
      fetchWeeklyPlan();
    } catch (err: any) {
      alert(err.message || 'Status update failed.');
    }
  };

  // Open completion confirmation overlay
  const openCompletionForm = (task: Task) => {
    setCompletionForm({
      taskId: task.task_id,
      chapterName: task.chapter_name,
      subjectName: task.subject_name,
      startTime: task.start_time,
      endTime: task.end_time,
      rating: 0,
      notes: '',
    });
  };

  // Confirm completion from overlay
  const confirmCompletion = () => {
    if (!completionForm) return;
    // Log optional data (can be persisted via API later)
    if (completionForm.rating > 0 || completionForm.notes.trim()) {
      console.log('[AuraStudy] Completion feedback:', {
        task_id: completionForm.taskId,
        difficulty_rating: completionForm.rating,
        notes: completionForm.notes,
      });
    }
    handleStatusChange(completionForm.taskId, 'COMPLETED');
    setCompletionForm(null);
  };

  // Determine active/overdue status for each task
  const getTaskTimeStatus = (task: Task): 'active' | 'overdue' | 'upcoming' | 'none' => {
    if (task.status === 'COMPLETED' || task.status === 'SKIPPED') return 'none';
    const startDt = parseTimeToToday(task.start_time);
    const endDt = parseTimeToToday(task.end_time);
    if (!startDt || !endDt) return 'none';
    if (now >= startDt && now < endDt) return 'active';
    if (now >= endDt && (task.status === 'PENDING' || task.status === 'IN_PROGRESS')) return 'overdue';
    return 'upcoming';
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-24 space-y-4">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        <p className="text-slate-400 font-light">Loading study workspace...</p>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto py-10 px-4 space-y-10">
      {/* Upper overview header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 pb-6 border-b border-slate-200 dark:border-slate-800">
        <div>
          <h1 className="text-3xl font-extrabold font-outfit tracking-tight text-slate-900 dark:text-slate-100">
            Welcome Back, Scholar!
          </h1>
          <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">
            Standard 7 • Academic year dashboard
          </p>
        </div>

        {reportCard && (
          <div className="flex gap-4">
            <div className="glass px-4 py-2.5 rounded-2xl text-center glow-purple">
              <span className="block text-[10px] uppercase tracking-widest font-semibold text-slate-500 dark:text-slate-400">Study Health</span>
              <span className="text-lg font-bold font-outfit text-violet-600 dark:text-violet-300">{parseFloat(reportCard.study_health_score).toFixed(1)}%</span>
            </div>
            <div className="glass px-4 py-2.5 rounded-2xl text-center glow-purple">
              <span className="block text-[10px] uppercase tracking-widest font-semibold text-slate-500 dark:text-slate-400">Aptitude Percentile</span>
              <span className="text-lg font-bold font-outfit text-blue-600 dark:text-blue-300">{parseFloat(reportCard.aptitude_percentile).toFixed(1)}th</span>
            </div>
            <div className="glass px-4 py-2.5 rounded-2xl text-center glow-purple">
              <span className="block text-[10px] uppercase tracking-widest font-semibold text-slate-500 dark:text-slate-400">Academic Accuracy</span>
              <span className="text-lg font-bold font-outfit text-fuchsia-600 dark:text-fuchsia-300">{parseFloat(reportCard.academic_accuracy).toFixed(1)}%</span>
            </div>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200 dark:border-slate-800 space-x-6 text-sm font-medium">
        <button
          onClick={() => setActiveTab('daily')}
          className={`pb-4 transition relative ${
            activeTab === 'daily' ? 'text-violet-600 dark:text-violet-400 border-b-2 border-violet-500' : 'text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200'
          }`}
        >
          Daily Study Plan
        </button>
        <button
          onClick={() => setActiveTab('weekly')}
          className={`pb-4 transition relative ${
            activeTab === 'weekly' ? 'text-violet-600 dark:text-violet-400 border-b-2 border-violet-500' : 'text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200'
          }`}
        >
          Weekly Schedule
        </button>
        <button
          onClick={() => setActiveTab('gap')}
          className={`pb-4 transition relative ${
            activeTab === 'gap' ? 'text-violet-600 dark:text-violet-400 border-b-2 border-violet-500' : 'text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200'
          }`}
        >
          Gap Analysis Suggestions
        </button>
      </div>

      {/* Tab Contents */}
      {activeTab === 'daily' && (
        <div className="space-y-6">
          <div className="flex justify-between items-center bg-white/60 dark:bg-slate-900/40 border border-slate-200 dark:border-slate-800 rounded-2xl p-4">
            <span className="text-sm font-light text-slate-600 dark:text-slate-400">
              Select solver strategy for study slot packing:
            </span>
            <div className="flex gap-2 text-xs">
              <button
                onClick={() => { setStrategy('knapsack'); fetchDailyPlan('knapsack'); }}
                className={`px-4 py-2 rounded-xl font-semibold border transition ${
                  strategy === 'knapsack'
                    ? 'bg-violet-600 border-violet-500 text-white'
                    : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
                }`}
              >
                0/1 Knapsack (Optimal)
              </button>
              <button
                onClick={() => { setStrategy('greedy'); fetchDailyPlan('greedy'); }}
                className={`px-4 py-2 rounded-xl font-semibold border transition ${
                  strategy === 'greedy'
                    ? 'bg-violet-600 border-violet-500 text-white'
                    : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
                }`}
              >
                Greedy (Heuristic)
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4">
            {dailyTasks.length === 0 ? (
              <div className="text-center py-12 text-slate-650 bg-slate-100/50 dark:bg-slate-900/20 border border-slate-200 dark:border-slate-800 rounded-3xl">
                No tasks generated for today. Hit daily study goal limits?
              </div>
            ) : (
              dailyTasks.map((task) => {
                const isDone = task.status === 'COMPLETED';
                const isInProgress = task.status === 'IN_PROGRESS';
                const isSkipped = task.status === 'SKIPPED';
                const timeStatus = getTaskTimeStatus(task);

                return (
                  <div
                    key={task.task_id}
                    className={`glass-dark rounded-2xl p-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 transition border border-slate-200/40 dark:border-slate-800/40 hover:border-slate-350 dark:hover:border-slate-700 ${
                      timeStatus === 'active' ? 'task-active scale-[1.01]' : ''
                    } ${timeStatus === 'overdue' ? 'task-overdue' : ''}`}
                  >
                    {/* Left: Time badge + task info */}
                    <div className="flex items-start gap-4">
                      {/* Time slot badge */}
                      {task.start_time && task.end_time && (
                        <div className="flex-shrink-0 bg-violet-50 dark:bg-violet-950/30 border border-violet-200 dark:border-violet-800/50 rounded-xl px-3 py-2.5 text-center min-w-[90px]">
                          <div className="flex items-center justify-center gap-1 mb-0.5">
                            <Clock size={10} className="text-violet-500 dark:text-violet-400" />
                          </div>
                          <span className="block text-xs font-bold text-violet-700 dark:text-violet-300 font-mono">
                            {task.start_time}
                          </span>
                          <span className="block text-[9px] text-slate-400 dark:text-slate-500 my-0.5">to</span>
                          <span className="block text-xs font-bold text-violet-700 dark:text-violet-300 font-mono">
                            {task.end_time}
                          </span>
                        </div>
                      )}

                      {/* Task details */}
                      <div className="space-y-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-[10px] uppercase font-bold tracking-wider text-slate-600 dark:text-slate-400 bg-slate-200/80 dark:bg-slate-800 px-2 py-0.5 rounded">
                            {task.subject_name}
                          </span>
                          {timeStatus === 'active' && (
                            <span className="text-[10px] uppercase font-extrabold tracking-wider text-white bg-violet-600 dark:bg-violet-500 px-2 py-0.5 rounded animate-pulse">
                              NOW
                            </span>
                          )}
                          {timeStatus === 'overdue' && (
                            <span className="text-[10px] uppercase font-extrabold tracking-wider text-amber-800 dark:text-amber-200 bg-amber-100 dark:bg-amber-900/40 px-2 py-0.5 rounded">
                              Overdue
                            </span>
                          )}
                        </div>
                        <h3 className="text-lg font-bold text-slate-900 dark:text-slate-200 font-outfit">{task.chapter_name}</h3>
                        <p className="text-xs text-slate-500 flex items-center gap-1">
                          <Clock size={12} /> Study allocation: {task.allocated_minutes} minutes
                        </p>
                      </div>
                    </div>

                    {/* Right: Status buttons */}
                    <div className="flex gap-2">
                      <button
                        onClick={() => openCompletionForm(task)}
                        className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition ${
                          isDone
                            ? 'bg-green-50 dark:bg-green-950/40 border border-green-200 dark:border-green-500 text-green-700 dark:text-green-300'
                            : 'bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:border-slate-300 dark:hover:border-slate-700'
                        }`}
                      >
                        <CheckCircle2 size={14} /> Completed
                      </button>
                      <button
                        onClick={() => handleStatusChange(task.task_id, 'IN_PROGRESS')}
                        className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition ${
                          isInProgress
                            ? 'bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-500 text-blue-700 dark:text-blue-300'
                            : 'bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:border-slate-300 dark:hover:border-slate-700'
                        }`}
                      >
                        <TrendingUp size={14} /> In Progress
                      </button>
                      <button
                        onClick={() => handleStatusChange(task.task_id, 'SKIPPED')}
                        className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition ${
                          isSkipped
                            ? 'bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-500 text-red-700 dark:text-red-300'
                            : 'bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:border-slate-300 dark:hover:border-slate-700'
                        }`}
                      >
                        <AlertTriangle size={14} /> Skipped
                      </button>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}

      {activeTab === 'weekly' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {weeklyPlan.map((day) => (
            <div key={day.day_number} className="glass-dark rounded-2xl p-5 space-y-4 shadow glow-purple border border-slate-200/40 dark:border-slate-800/40">
              <div className="flex justify-between items-center border-b border-slate-200 dark:border-slate-800 pb-3">
                <h3 className="font-bold text-lg font-outfit text-slate-800 dark:text-slate-300">
                  Day {day.day_number}
                </h3>
                <span className="text-[10px] font-mono text-slate-500 dark:text-slate-400">
                  {day.allocated_minutes}m / {day.capacity_minutes}m
                </span>
              </div>

              <div className="space-y-3">
                {day.tasks.length === 0 ? (
                  <p className="text-xs text-slate-500 italic py-4 text-center">Rest day / Unallocated</p>
                ) : (
                  day.tasks.map((task, idx) => (
                    <div key={idx} className="bg-white/80 dark:bg-slate-900/60 rounded-xl p-3 border border-slate-150 dark:border-slate-800/40">
                      <span className="text-[9px] uppercase font-semibold text-violet-600 dark:text-violet-400 bg-violet-100 dark:bg-violet-950/20 px-1.5 py-0.5 rounded">
                        {task.subject_name}
                      </span>
                      <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200 mt-1 line-clamp-1">{task.chapter_name}</h4>
                      <span className="text-[10px] text-slate-500">{task.cost} mins study</span>
                    </div>
                  ))
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'gap' && (
        <div className="space-y-6">
          <div className="flex items-start gap-4 bg-violet-50 dark:bg-violet-955/20 border border-violet-200 dark:border-violet-500/20 rounded-3xl p-6">
            <Lightbulb className="text-violet-600 dark:text-violet-400 shrink-0 mt-0.5" size={24} />
            <div className="space-y-1">
              <h3 className="text-lg font-semibold font-outfit text-violet-700 dark:text-violet-300">Opt-In Aptitude Gap Analysis</h3>
              <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
                This panel maps your cognitive aptitude scores directly into concrete academic study recommendations. 
                <strong> Important note:</strong> This analysis is purely informational. In accordance with clinical EdTech requirements, cognitive performance scores do NOT influence the daily/weekly planner schedules.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-6">
            {gapSuggestions.length === 0 ? (
              <div className="text-center py-16 text-slate-500 bg-slate-100/50 dark:bg-slate-900/20 border border-slate-200 dark:border-slate-800 rounded-3xl">
                Fantastic! All cognitive aptitude areas are above the 60% mastery threshold. No gaps detected.
              </div>
            ) : (
              gapSuggestions.map((s, idx) => (
                <div key={idx} className="glass-dark rounded-2xl p-6 border-l-4 border-l-violet-500 flex flex-col md:flex-row justify-between items-start md:items-center gap-6 border border-slate-200/40 dark:border-slate-800/40">
                  <div className="space-y-2 max-w-2xl">
                    <h4 className="text-lg font-bold text-slate-900 dark:text-slate-200 font-outfit">{s.category}</h4>
                    <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">{s.suggestion}</p>
                  </div>
                  <div className="bg-white/85 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-2.5 text-center min-w-[100px]">
                    <span className="block text-[10px] uppercase font-semibold text-slate-500">Accuracy</span>
                    <span className="text-md font-bold font-mono text-violet-600 dark:text-violet-300">{s.accuracy}%</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Completion Confirmation Overlay */}
      {completionForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="relative w-full max-w-md bg-white dark:bg-slate-900/95 border border-slate-200 dark:border-slate-800 rounded-3xl shadow-2xl overflow-hidden glow-purple">
            {/* Header */}
            <div className="p-6 border-b border-slate-200 dark:border-slate-800">
              <div className="flex items-center gap-2 mb-2">
                <CheckCircle2 className="text-green-500" size={20} />
                <h3 className="text-lg font-bold font-outfit text-slate-900 dark:text-slate-100">
                  Mark as Completed
                </h3>
              </div>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                <span className="font-semibold text-slate-700 dark:text-slate-300">{completionForm.chapterName}</span>
                <span className="mx-1.5">•</span>
                <span>{completionForm.subjectName}</span>
              </p>
              {completionForm.startTime && completionForm.endTime && (
                <p className="text-xs text-slate-400 dark:text-slate-500 mt-1 flex items-center gap-1">
                  <Clock size={11} /> {completionForm.startTime} → {completionForm.endTime}
                </p>
              )}
            </div>

            {/* Body */}
            <div className="p-6 space-y-5">
              {/* Difficulty Rating */}
              <div>
                <label className="block text-[10px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
                  How difficult was this session? (Optional)
                </label>
                <div className="flex gap-1.5">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      onClick={() => setCompletionForm({ ...completionForm, rating: completionForm.rating === star ? 0 : star })}
                      className={`p-1.5 rounded-lg transition ${
                        star <= completionForm.rating
                          ? 'text-amber-400 scale-110'
                          : 'text-slate-300 dark:text-slate-700 hover:text-amber-300 dark:hover:text-amber-500'
                      }`}
                    >
                      <Star size={22} fill={star <= completionForm.rating ? 'currentColor' : 'none'} />
                    </button>
                  ))}
                  <span className="ml-2 text-xs text-slate-400 dark:text-slate-500 self-center">
                    {completionForm.rating === 0 && 'Not rated'}
                    {completionForm.rating === 1 && 'Very Easy'}
                    {completionForm.rating === 2 && 'Easy'}
                    {completionForm.rating === 3 && 'Moderate'}
                    {completionForm.rating === 4 && 'Hard'}
                    {completionForm.rating === 5 && 'Very Hard'}
                  </span>
                </div>
              </div>

              {/* Notes */}
              <div>
                <label className="block text-[10px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
                  Quick notes (Optional)
                </label>
                <textarea
                  value={completionForm.notes}
                  onChange={(e) => setCompletionForm({ ...completionForm, notes: e.target.value.slice(0, 200) })}
                  placeholder="e.g., Need to revisit section 3.2..."
                  rows={3}
                  className="w-full bg-white/50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-800 dark:text-slate-200 focus:outline-none focus:border-violet-500 transition resize-none placeholder-slate-400 dark:placeholder-slate-600"
                />
                <span className="text-[10px] text-slate-400 dark:text-slate-600 mt-1 block text-right">
                  {completionForm.notes.length}/200
                </span>
              </div>
            </div>

            {/* Footer */}
            <div className="flex justify-end gap-3 p-6 border-t border-slate-200 dark:border-slate-800">
              <button
                onClick={() => setCompletionForm(null)}
                className="bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 text-xs font-bold px-4 py-2 rounded-xl transition"
              >
                Cancel
              </button>
              <button
                onClick={confirmCompletion}
                className="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-500 hover:to-emerald-500 text-white text-xs font-bold px-5 py-2 rounded-xl shadow-lg hover:shadow-green-950/40 transition flex items-center gap-1.5"
              >
                <CheckCircle2 size={14} /> Confirm Completion
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
