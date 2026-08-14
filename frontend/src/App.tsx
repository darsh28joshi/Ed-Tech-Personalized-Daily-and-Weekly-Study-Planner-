import React, { useState, useEffect } from 'react';
import Onboarding from './components/Onboarding';
import DiagnosticLanding from './components/DiagnosticLanding';
import Diagnostic from './components/Diagnostic';
import DiagnosticResults from './components/DiagnosticResults';
import Dashboard from './components/Dashboard';
import { Compass, GraduationCap, Github, RefreshCw, User, Settings, LogOut, X, Sun, Moon } from 'lucide-react';

type FlowState = 'onboarding' | 'pre-diagnostic' | 'diagnostic' | 'results' | 'dashboard';

// Helper to calculate end time string
function calculateEndTime(startTimeStr: string | undefined, hours: number): string {
  if (!startTimeStr) return '';
  const [hStr, mStr] = startTimeStr.split(':');
  let h = parseInt(hStr, 10);
  let m = parseInt(mStr, 10);
  if (isNaN(h) || isNaN(m)) return '';
  
  const totalMinutes = h * 60 + m + Math.round(hours * 60);
  const endH = Math.floor(totalMinutes / 60) % 24;
  const endM = totalMinutes % 60;
  
  const period = endH >= 12 ? 'PM' : 'AM';
  const displayH = endH % 12 === 0 ? 12 : endH % 12;
  const displayM = endM.toString().padStart(2, '0');
  return `${displayH}:${displayM} ${period}`;
}

// Helper to format 24h to 12h
function formatTime12h(time24: string | undefined): string {
  if (!time24) return '';
  const parts = time24.split(':');
  if (parts.length < 2) return time24;
  let h = parseInt(parts[0], 10);
  const m = parseInt(parts[1], 10);
  if (isNaN(h) || isNaN(m)) return time24;
  const period = h >= 12 ? 'PM' : 'AM';
  const displayH = h % 12 === 0 ? 12 : h % 12;
  const displayM = m.toString().padStart(2, '0');
  return `${displayH}:${displayM} ${period}`;
}

export default function App() {
  const [studentId, setStudentId] = useState<number | null>(() => {
    const saved = localStorage.getItem('studentId');
    return saved ? parseInt(saved, 10) : null;
  });

  const [sessionId, setSessionId] = useState<number | null>(() => {
    const saved = localStorage.getItem('sessionId');
    return saved ? parseInt(saved, 10) : null;
  });

  const [entryPoint, setEntryPoint] = useState<string>(() => {
    return localStorage.getItem('entryPoint') || '';
  });

  const [flow, setFlow] = useState<FlowState>(() => {
    const savedStudent = localStorage.getItem('studentId');
    const savedSession = localStorage.getItem('sessionId');
    const savedDiagnosticCompleted = localStorage.getItem('diagnosticCompleted');
    
    if (savedStudent && savedSession && savedDiagnosticCompleted === 'true') {
      return 'dashboard';
    } else if (savedStudent) {
      return 'pre-diagnostic';
    }
    return 'onboarding';
  });

  const [testResults, setTestResults] = useState<any>(null);

  // Profile management states
  const [profile, setProfile] = useState<any>(null);
  const [editForm, setEditForm] = useState<any>({});
  const [profileVersion, setProfileVersion] = useState(0);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [activeModal, setActiveModal] = useState<'view' | 'edit' | null>(null);

  // Theme state
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    const saved = localStorage.getItem('theme');
    return (saved as 'light' | 'dark') || 'dark';
  });

  // Sync theme with HTML class
  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
  }, [theme]);

  // Fetch student profile details automatically when studentId is resolved
  useEffect(() => {
    if (studentId) {
      const loadProfile = async () => {
        try {
          const response = await fetch(`http://127.0.0.1:8001/onboarding/student/${studentId}`);
          if (response.ok) {
            const data = await response.json();
            setProfile(data);
            setEditForm(data);
          }
        } catch (err) {
          console.error('Failed to load student profile details:', err);
        }
      };
      loadProfile();
    } else {
      setProfile(null);
      setEditForm({});
    }
  }, [studentId, profileVersion]);

  const handleOnboardingSuccess = (
    id: number, 
    ep: string, 
    diagnosticCompleted: boolean = false, 
    sessId: number | null = null
  ) => {
    setStudentId(id);
    setEntryPoint(ep);
    localStorage.setItem('studentId', id.toString());
    localStorage.setItem('entryPoint', ep);

    if (diagnosticCompleted && sessId !== null) {
      setSessionId(sessId);
      localStorage.setItem('sessionId', sessId.toString());
      localStorage.setItem('diagnosticCompleted', 'true');
      setFlow('dashboard');
    } else {
      localStorage.removeItem('sessionId');
      localStorage.removeItem('diagnosticCompleted');
      setSessionId(null);
      setFlow('pre-diagnostic');
    }
  };

  const handleDiagnosticComplete = (sessId: number, reportData?: any) => {
    setSessionId(sessId);
    localStorage.setItem('sessionId', sessId.toString());
    localStorage.setItem('diagnosticCompleted', 'true');

    if (reportData) {
      setTestResults(reportData);
      setFlow('results');
    } else {
      setFlow('dashboard');
    }
  };

  const handleResetSession = () => {
    localStorage.clear();
    setStudentId(null);
    setSessionId(null);
    setEntryPoint('');
    setTestResults(null);
    setFlow('onboarding');
  };

  const handleUpdateProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await fetch(`http://127.0.0.1:8001/onboarding/student/${studentId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          first_name: editForm.first_name,
          last_name: editForm.last_name,
          password: editForm.password,
          date_of_birth: editForm.date_of_birth || null,
          school_name: editForm.school_name || null,
          medium: editForm.medium,
          study_goal: editForm.study_goal,
          daily_study_hours: parseFloat(editForm.daily_study_hours),
          preferred_study_time: editForm.preferred_study_time,
          preferred_study_start_time: editForm.preferred_study_start_time || null,
          revision_preference: editForm.revision_preference,
          academic_year_start_date: editForm.academic_year_start_date,
          academic_year_end_date: editForm.academic_year_end_date,
        }),
      });

      if (!response.ok) throw new Error('Failed to save profile changes.');
      const data = await response.json();
      setProfile(data);
      setProfileVersion((prev) => prev + 1);
      setActiveModal(null);
    } catch (err: any) {
      alert(err.message || 'Failed to save profile changes.');
    }
  };

  return (
    <div className="flex flex-col min-h-screen">
      {/* Top Navbar */}
      <header className="border-b border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-950/40 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="bg-gradient-to-r from-violet-600 to-blue-600 p-2 rounded-xl shadow-md">
              <GraduationCap className="text-white" size={20} />
            </div>
            <span className="font-extrabold font-outfit text-xl tracking-tight text-slate-900 dark:text-slate-100">
              AuraStudy
            </span>
          </div>

          <div className="flex items-center gap-4">
            <div className="hidden sm:flex items-center gap-2 text-xs font-medium text-slate-500">
              {flow === 'onboarding' && <span className="text-violet-600 dark:text-violet-400">Onboarding Stage</span>}
              {flow === 'pre-diagnostic' && <span className="text-violet-600 dark:text-violet-400">Ready for Assessment</span>}
              {flow === 'diagnostic' && <span className="text-blue-600 dark:text-blue-400 animate-pulse">Diagnostic Stage</span>}
              {flow === 'results' && <span className="text-fuchsia-600 dark:text-fuchsia-400">Results Summary</span>}
              {flow === 'dashboard' && <span className="text-emerald-600 dark:text-emerald-400">Active Workspace</span>}
            </div>

            {/* Theme Toggle Button */}
            <button
              id="theme-toggle-btn"
              onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
              className="p-2 rounded-xl bg-white/60 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 transition duration-150"
              title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            >
              {theme === 'dark' ? <Sun size={15} className="text-yellow-400" /> : <Moon size={15} className="text-indigo-400" />}
            </button>

            {/* Profile Dropdown */}
            {flow !== 'onboarding' && profile && (
              <div className="relative">
                <button
                  id="profile-dropdown-btn"
                  onClick={() => setDropdownOpen(!dropdownOpen)}
                  className="flex items-center gap-2.5 bg-white/60 dark:bg-slate-900/60 hover:bg-slate-100 dark:hover:bg-slate-900 border border-slate-200 dark:border-slate-850 hover:border-slate-350 dark:hover:border-slate-700 text-slate-700 dark:text-slate-200 text-xs px-3.5 py-2 rounded-xl transition duration-150"
                >
                  <div className="w-5 h-5 rounded-lg bg-gradient-to-br from-violet-600 to-blue-600 flex items-center justify-center font-extrabold text-[10px] text-white">
                    {profile.first_name[0].toUpperCase()}
                  </div>
                  <span className="font-bold">{profile.first_name} {profile.last_name}</span>
                </button>

                {dropdownOpen && (
                  <>
                    <div className="fixed inset-0 z-10" onClick={() => setDropdownOpen(false)}></div>
                    <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-slate-950/95 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl p-1.5 z-20 backdrop-blur-lg animate-in fade-in slide-in-from-top-2 duration-150">
                      <button
                        onClick={() => {
                          setDropdownOpen(false);
                          setActiveModal('view');
                        }}
                        className="w-full text-left px-3 py-2 rounded-lg text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-900 hover:text-slate-950 dark:hover:text-white text-xs font-semibold flex items-center gap-2 transition"
                      >
                        <User size={14} className="text-violet-600 dark:text-violet-400" />
                        View Profile
                      </button>
                      <button
                        onClick={() => {
                          setDropdownOpen(false);
                          setActiveModal('edit');
                        }}
                        className="w-full text-left px-3 py-2 rounded-lg text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-900 hover:text-slate-950 dark:hover:text-white text-xs font-semibold flex items-center gap-2 transition"
                      >
                        <Settings size={14} className="text-blue-600 dark:text-blue-400" />
                        Edit Profile
                      </button>
                      <hr className="border-slate-100 dark:border-slate-900 my-1.5" />
                      <button
                        onClick={() => {
                          setDropdownOpen(false);
                          handleResetSession();
                        }}
                        className="w-full text-left px-3 py-2 rounded-lg text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/20 text-xs font-semibold flex items-center gap-2 transition"
                      >
                        <LogOut size={14} />
                        Log Out
                      </button>
                    </div>
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-grow">
        {flow === 'onboarding' && (
          <Onboarding onSuccess={handleOnboardingSuccess} />
        )}
        {flow === 'pre-diagnostic' && (
          <DiagnosticLanding onStart={() => setFlow('diagnostic')} />
        )}
        {flow === 'diagnostic' && studentId && (
          <Diagnostic
            studentId={studentId}
            entryPoint={entryPoint}
            onComplete={handleDiagnosticComplete}
          />
        )}
        {flow === 'results' && testResults && (
          <DiagnosticResults
            results={testResults}
            onProceed={() => setFlow('dashboard')}
          />
        )}
        {flow === 'dashboard' && studentId && sessionId && (
          <Dashboard
            studentId={studentId}
            sessionId={sessionId}
            profileVersion={profileVersion}
          />
        )}
      </main>

      {/* Profile Modals */}
      {activeModal !== null && profile && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-200">
          <div className="relative w-full max-w-2xl bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 rounded-3xl shadow-2xl overflow-hidden glow-purple max-h-[90vh] flex flex-col">
            {/* Modal Header */}
            <div className="flex justify-between items-center p-6 border-b border-slate-200 dark:border-slate-800">
              <h3 className="text-lg font-bold font-outfit text-slate-900 dark:text-slate-100 flex items-center gap-2">
                {activeModal === 'view' ? <User className="text-violet-600 dark:text-violet-400" size={18} /> : <Settings className="text-blue-600 dark:text-blue-400" size={18} />}
                {activeModal === 'view' ? 'Student Settings Profile' : 'Edit Planner Preferences'}
              </h3>
              <button
                onClick={() => setActiveModal(null)}
                className="text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200 transition"
              >
                <X size={18} />
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6 overflow-y-auto flex-grow">
              {activeModal === 'view' ? (
                /* VIEW MODAL */
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 text-sm">
                  <div className="space-y-4">
                    <h4 className="text-xs uppercase font-bold tracking-wider text-violet-650 dark:text-violet-400 pb-1 border-b border-slate-200 dark:border-slate-850">Personal Identity</h4>
                    <div className="grid grid-cols-2 gap-y-3">
                      <span className="text-slate-500 font-medium">Full Name:</span>
                      <span className="text-slate-800 dark:text-slate-200 font-bold">{profile.first_name} {profile.last_name}</span>
                      
                      <span className="text-slate-500 font-medium">Username:</span>
                      <span className="text-slate-800 dark:text-slate-200 font-mono">{profile.username}</span>

                      <span className="text-slate-500 font-medium">Date of Birth:</span>
                      <span className="text-slate-800 dark:text-slate-200">{profile.date_of_birth ? new Date(profile.date_of_birth).toLocaleDateString() : 'Not provided'}</span>

                      <span className="text-slate-500 font-medium">School:</span>
                      <span className="text-slate-800 dark:text-slate-200">{profile.school_name || 'Not provided'}</span>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h4 className="text-xs uppercase font-bold tracking-wider text-blue-600 dark:text-blue-400 pb-1 border-b border-slate-200 dark:border-slate-850">Planner Config</h4>
                    <div className="grid grid-cols-2 gap-y-3">
                      <span className="text-slate-500 font-medium">Daily Target:</span>
                      <span className="text-slate-800 dark:text-slate-200 font-semibold">{profile.daily_study_hours} hours</span>

                      <span className="text-slate-500 font-medium">Medium:</span>
                      <span className="text-slate-800 dark:text-slate-200">{profile.medium}</span>

                      <span className="text-slate-500 font-medium">Goal:</span>
                      <span className="text-slate-800 dark:text-slate-200">{profile.study_goal.replace('_', ' ')}</span>

                      <span className="text-slate-500 font-medium">Preferred Time:</span>
                      <span className="text-slate-800 dark:text-slate-200">{profile.preferred_study_time}</span>

                      <span className="text-slate-500 font-medium">Start Time:</span>
                      <span className="text-slate-800 dark:text-slate-200">{profile.preferred_study_start_time ? formatTime12h(profile.preferred_study_start_time) : 'Not set'}</span>

                      <span className="text-slate-500 font-medium">Calculated End:</span>
                      <span className="text-slate-800 dark:text-slate-200 font-bold text-violet-600 dark:text-violet-400">{profile.preferred_study_end_time ? formatTime12h(profile.preferred_study_end_time) : 'Not calculated'}</span>

                      <span className="text-slate-500 font-medium">Revision Model:</span>
                      <span className="text-slate-800 dark:text-slate-200">{profile.revision_preference}</span>
                    </div>
                  </div>

                  <div className="md:col-span-2 space-y-4 pt-4 border-t border-slate-200 dark:border-slate-800/80">
                    <h4 className="text-xs uppercase font-bold tracking-wider text-fuchsia-600 dark:text-fuchsia-400 pb-1 border-b border-slate-200 dark:border-slate-855">Academic Bounds</h4>
                    <div className="grid grid-cols-2 gap-y-3 max-w-md">
                      <span className="text-slate-500 font-medium">Year Start Date:</span>
                      <span className="text-slate-800 dark:text-slate-200">{new Date(profile.academic_year_start_date).toLocaleDateString()}</span>

                      <span className="text-slate-500 font-medium">Year End Date:</span>
                      <span className="text-slate-800 dark:text-slate-200">{new Date(profile.academic_year_end_date).toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>
              ) : (
                /* EDIT MODAL */
                <form onSubmit={handleUpdateProfileSubmit} className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-4">
                      <h4 className="text-xs uppercase font-bold tracking-wider text-violet-400">Personal Info</h4>
                      <div>
                        <label className="block text-[10px] font-semibold text-slate-500 uppercase mb-1">First Name</label>
                        <input
                          type="text"
                          required
                          value={editForm.first_name}
                          onChange={(e) => setEditForm({ ...editForm, first_name: e.target.value })}
                          className="w-full bg-white/50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-xl px-4 py-2 text-sm text-slate-800 dark:text-slate-200 focus:outline-none focus:border-violet-500 transition"
                        />
                      </div>
                      <div>
                        <label className="block text-[10px] font-semibold text-slate-500 uppercase mb-1">Last Name</label>
                        <input
                          type="text"
                          required
                          value={editForm.last_name}
                          onChange={(e) => setEditForm({ ...editForm, last_name: e.target.value })}
                          className="w-full bg-white/50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-xl px-4 py-2 text-sm text-slate-800 dark:text-slate-200 focus:outline-none focus:border-violet-500 transition"
                        />
                      </div>
                      <div>
                        <label className="block text-[10px] font-semibold text-slate-500 uppercase mb-1">Password</label>
                        <input
                          type="password"
                          required
                          value={editForm.password}
                          onChange={(e) => setEditForm({ ...editForm, password: e.target.value })}
                          className="w-full bg-white/50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-xl px-4 py-2 text-sm text-slate-800 dark:text-slate-200 focus:outline-none focus:border-violet-500 transition"
                        />
                      </div>
                      <div>
                        <label className="block text-[10px] font-semibold text-slate-500 uppercase mb-1">School Name</label>
                        <input
                          type="text"
                          value={editForm.school_name || ''}
                          onChange={(e) => setEditForm({ ...editForm, school_name: e.target.value })}
                          className="w-full bg-white/50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-xl px-4 py-2 text-sm text-slate-800 dark:text-slate-200 focus:outline-none focus:border-violet-500 transition"
                        />
                      </div>
                      <div>
                        <label className="block text-[10px] font-semibold text-slate-500 uppercase mb-1">Date of Birth</label>
                        <input
                          type="date"
                          value={editForm.date_of_birth || ''}
                          onChange={(e) => setEditForm({ ...editForm, date_of_birth: e.target.value })}
                          className="w-full bg-white/50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-xl px-4 py-2 text-sm text-slate-800 dark:text-slate-200 focus:outline-none focus:border-violet-500 transition"
                        />
                      </div>
                    </div>

                    <div className="space-y-4">
                      <h4 className="text-xs uppercase font-bold tracking-wider text-blue-400">Preferences</h4>
                      <div>
                        <label className="block text-[10px] font-semibold text-slate-500 uppercase mb-1">Daily Study Hours</label>
                        <input
                          type="number"
                          required
                          min="0.5"
                          max="12"
                          step="0.5"
                          value={editForm.daily_study_hours}
                          onChange={(e) => setEditForm({ ...editForm, daily_study_hours: e.target.value })}
                          className="w-full bg-white/50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-xl px-4 py-2 text-sm text-slate-800 dark:text-slate-200 focus:outline-none focus:border-blue-500 transition"
                        />
                      </div>
                      <div>
                        <label className="block text-[10px] font-semibold text-slate-500 uppercase mb-1">Medium of Instruction</label>
                        <select
                          value={editForm.medium}
                          onChange={(e) => setEditForm({ ...editForm, medium: e.target.value })}
                          className="w-full bg-white/50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-800 dark:text-slate-200 focus:outline-none focus:border-blue-500 transition"
                        >
                          <option value="English">English</option>
                          <option value="Marathi">Marathi</option>
                          <option value="Hindi">Hindi</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-[10px] font-semibold text-slate-500 uppercase mb-1">Study Goal</label>
                        <select
                          value={editForm.study_goal}
                          onChange={(e) => setEditForm({ ...editForm, study_goal: e.target.value })}
                          className="w-full bg-white/50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-800 dark:text-slate-200 focus:outline-none focus:border-blue-500 transition"
                        >
                          <option value="EXAM_PREPARATION">Exam Preparation</option>
                          <option value="SKILL_BUILDING">Skill Building</option>
                          <option value="GENERAL_LEARNING">General Learning</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-[10px] font-semibold text-slate-500 uppercase mb-1">Preferred Study Time</label>
                        <select
                          value={editForm.preferred_study_time}
                          onChange={(e) => {
                            const val = e.target.value;
                            let startVal = editForm.preferred_study_start_time;
                            if (val === 'MORNING') startVal = '08:00';
                            else if (val === 'AFTERNOON') startVal = '14:00';
                            else if (val === 'EVENING') startVal = '18:00';
                            else if (val === 'NIGHT') startVal = '21:00';
                            setEditForm({ ...editForm, preferred_study_time: val, preferred_study_start_time: startVal });
                          }}
                          className="w-full bg-white/50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-800 dark:text-slate-200 focus:outline-none focus:border-blue-500 transition"
                        >
                          <option value="MORNING">Morning</option>
                          <option value="AFTERNOON">Afternoon</option>
                          <option value="EVENING">Evening</option>
                          <option value="NIGHT">Night</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-[10px] font-semibold text-slate-500 uppercase mb-1">Preferred Start Time</label>
                        <input
                          type="time"
                          required
                          value={editForm.preferred_study_start_time || '18:00'}
                          onChange={(e) => setEditForm({ ...editForm, preferred_study_start_time: e.target.value })}
                          className="w-full bg-white/50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-xl px-4 py-2 text-sm text-slate-800 dark:text-slate-200 focus:outline-none focus:border-blue-500 transition"
                        />
                      </div>
                      <div className="flex flex-col justify-end">
                        <span className="block text-[10px] font-semibold text-slate-500 uppercase mb-1">Calculated End Time</span>
                        <div className="w-full bg-slate-100/50 dark:bg-slate-900/30 border border-dashed border-slate-300 dark:border-slate-850 rounded-xl px-4 py-2.5 text-sm text-slate-800 dark:text-slate-200 font-bold font-mono">
                          {calculateEndTime(editForm.preferred_study_start_time, editForm.daily_study_hours) || 'N/A'}
                        </div>
                      </div>
                      <div>
                        <label className="block text-[10px] font-semibold text-slate-500 uppercase mb-1">Revision Preference</label>
                        <select
                          value={editForm.revision_preference}
                          onChange={(e) => setEditForm({ ...editForm, revision_preference: e.target.value })}
                          className="w-full bg-white/50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-800 dark:text-slate-200 focus:outline-none focus:border-blue-500 transition"
                        >
                          <option value="DAILY">Daily Revision Slots Only</option>
                          <option value="WEEKLY">Weekly Pack Revision Only</option>
                          <option value="BOTH">Both Daily & Weekly Revision</option>
                        </select>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-4 pt-4 border-t border-slate-200 dark:border-slate-800/80">
                    <h4 className="text-xs uppercase font-bold tracking-wider text-fuchsia-600 dark:text-fuchsia-400">Academic Year Dates</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <label className="block text-[10px] font-semibold text-slate-500 uppercase mb-1">Academic Year Start Date</label>
                        <input
                          type="date"
                          required
                          value={editForm.academic_year_start_date}
                          onChange={(e) => setEditForm({ ...editForm, academic_year_start_date: e.target.value })}
                          className="w-full bg-white/50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-xl px-4 py-2 text-sm text-slate-800 dark:text-slate-200 focus:outline-none focus:border-fuchsia-500 transition"
                        />
                      </div>
                      <div>
                        <label className="block text-[10px] font-semibold text-slate-500 uppercase mb-1">Academic Year End Date</label>
                        <input
                          type="date"
                          required
                          value={editForm.academic_year_end_date}
                          onChange={(e) => setEditForm({ ...editForm, academic_year_end_date: e.target.value })}
                          className="w-full bg-white/50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-xl px-4 py-2 text-sm text-slate-800 dark:text-slate-200 focus:outline-none focus:border-fuchsia-500 transition"
                        />
                      </div>
                    </div>
                  </div>

                  <div className="flex justify-end gap-3 pt-4 border-t border-slate-200 dark:border-slate-800">
                    <button
                      type="button"
                      onClick={() => {
                        setActiveModal(null);
                        setEditForm(profile);
                      }}
                      className="bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 text-xs font-bold px-4 py-2 rounded-xl transition"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="bg-gradient-to-r from-violet-600 to-blue-600 hover:from-violet-500 hover:to-blue-500 text-white text-xs font-bold px-5 py-2 rounded-xl shadow-lg hover:shadow-violet-950/40 transition"
                    >
                      Save Settings
                    </button>
                  </div>
                </form>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950/20 py-6 text-center text-xs text-slate-600">
        <div className="max-w-6xl mx-auto px-4 flex flex-col md:flex-row justify-between items-center gap-4">
          <p>© 2026 AuraStudy. EdTech Internship Prototype.</p>
          <div className="flex items-center gap-1.5 text-slate-500">
            <span>MySQL-Backed Adaptive Scheduler</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
