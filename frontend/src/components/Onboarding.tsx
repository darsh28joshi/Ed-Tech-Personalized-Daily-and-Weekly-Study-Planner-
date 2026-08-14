import React, { useState } from 'react';
import { Compass, Calendar, BookOpen, Clock, Award, Star, LogIn, UserPlus } from 'lucide-react';

interface OnboardingProps {
  onSuccess: (studentId: number, entryPoint: string, diagnosticCompleted?: boolean, sessionId?: number | null) => void;
}

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

export default function Onboarding({ onSuccess }: OnboardingProps) {
  const [isLogin, setIsLogin] = useState(false);
  
  const [formData, setFormData] = useState({
    board_id: 1,
    standard_id: 3,
    first_name: '',
    last_name: '',
    username: '',
    password: '',
    date_of_birth: '',
    school_name: '',
    medium: 'English',
    study_goal: 'EXAM_PREPARATION',
    daily_study_hours: 2.0,
    preferred_study_time: 'EVENING',
    preferred_study_start_time: '18:00', // Default start time for EVENING
    revision_preference: 'BOTH',
    academic_year_start_date: '2026-06-01',
    academic_year_end_date: '2027-04-30',
  });

  const [loginData, setLoginData] = useState({
    username: '',
    password: '',
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      if (isLogin) {
        // Handle login lookup
        const response = await fetch('http://127.0.0.1:8001/onboarding/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(loginData),
        });

        if (!response.ok) {
          const errData = await response.json();
          if (errData.detail && Array.isArray(errData.detail)) {
            const msgs = errData.detail.map((err: any) => `${err.loc[err.loc.length - 1]}: ${err.msg}`).join(', ');
            throw new Error(msgs);
          }
          throw new Error(errData.detail || 'Login failed. Please check student credentials.');
        }

        const data = await response.json();
        onSuccess(data.student_id, data.entry_point, data.diagnostic_completed, data.session_id);
      } else {
        // Clean up optional fields so they don't send empty strings to date/string parsing
        const cleanedData = {
          ...formData,
          daily_study_hours: parseFloat(formData.daily_study_hours as any),
          date_of_birth: formData.date_of_birth || null,
          school_name: formData.school_name || null,
        };

        // Handle onboarding creation
        const response = await fetch('http://127.0.0.1:8001/onboarding/student', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(cleanedData),
        });

        if (!response.ok) {
          const errData = await response.json();
          if (errData.detail && Array.isArray(errData.detail)) {
            const msgs = errData.detail.map((err: any) => `${err.loc[err.loc.length - 1]}: ${err.msg}`).join(', ');
            throw new Error(msgs);
          }
          throw new Error(errData.detail || 'Onboarding failed');
        }

        const data = await response.json();
        // New students have diagnosticCompleted = false
        onSuccess(data.student_id, data.entry_point, false, null);
      }
    } catch (err: any) {
      setError(err.message || 'Connection to backend failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => {
      const updated = { ...prev, [name]: value };
      if (name === 'preferred_study_time') {
        if (value === 'MORNING') updated.preferred_study_start_time = '08:00';
        else if (value === 'AFTERNOON') updated.preferred_study_start_time = '14:00';
        else if (value === 'EVENING') updated.preferred_study_start_time = '18:00';
        else if (value === 'NIGHT') updated.preferred_study_start_time = '21:00';
      }
      return updated;
    });
  };

  const handleLoginChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setLoginData((prev) => ({ ...prev, [name]: value }));
  };

  return (
    <div className="max-w-4xl mx-auto py-12 px-4">
      {/* Header */}
      <div className="text-center mb-10">
        <h1 className="text-4xl md:text-5xl font-extrabold font-outfit tracking-tight bg-gradient-to-r from-violet-400 via-fuchsia-400 to-blue-400 bg-clip-text text-transparent">
          {isLogin ? 'Welcome Back!' : 'AuraStudy Onboarding'}
        </h1>
        <p className="text-slate-400 mt-3 text-lg font-light">
          {isLogin 
            ? 'Enter your credentials to load your personalized study planner' 
            : 'Set up your profile to activate your adaptive study engine'}
        </p>
      </div>

      <form onSubmit={handleSubmit} className="glass-dark rounded-3xl p-8 md:p-10 shadow-2xl glow-purple space-y-8">
        {error && (
          <div className="bg-red-900/30 border border-red-500/50 text-red-200 px-4 py-3 rounded-xl text-sm">
            {error}
          </div>
        )}

        {isLogin ? (
          /* LOGIN MODE */
          <div className="space-y-6 max-w-md mx-auto py-4">
            <h3 className="text-xl font-bold font-outfit text-violet-300 flex items-center gap-2">
              <LogIn size={20} /> Student Login
            </h3>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">Username</label>
                <input
                  type="text"
                  name="username"
                  required
                  placeholder="e.g. pranav123"
                  value={loginData.username}
                  onChange={handleLoginChange}
                  className="w-full bg-white/50 dark:bg-slate-900/50 border border-slate-300 dark:border-slate-700/50 rounded-xl px-4 py-3 text-slate-800 dark:text-slate-200 placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:border-violet-500 transition"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">Password</label>
                <input
                  type="password"
                  name="password"
                  required
                  placeholder="Enter your password"
                  value={loginData.password}
                  onChange={handleLoginChange}
                  className="w-full bg-white/50 dark:bg-slate-900/50 border border-slate-300 dark:border-slate-700/50 rounded-xl px-4 py-3 text-slate-800 dark:text-slate-200 placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:border-violet-500 transition"
                />
              </div>
            </div>

            <div className="pt-6 text-center space-y-4">
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-gradient-to-r from-violet-600 to-blue-600 hover:from-violet-500 hover:to-blue-500 text-white font-semibold rounded-2xl px-12 py-4 shadow-lg hover:shadow-violet-900/40 hover:-translate-y-0.5 transition duration-150 disabled:opacity-50 disabled:pointer-events-none"
              >
                {loading ? 'Logging in...' : 'Load Planner'}
              </button>
              
              <button
                type="button"
                onClick={() => setIsLogin(false)}
                className="text-xs text-slate-400 hover:text-slate-200 underline block mx-auto transition"
              >
                New student? Create an onboarding profile
              </button>
            </div>
          </div>
        ) : (
          /* ONBOARDING MODE */
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Identity Section */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold font-outfit text-violet-300 flex items-center gap-2">
                  <Star size={18} /> Personal Identity
                </h3>
                
                <div>
                  <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">First Name</label>
                  <input
                    type="text"
                    name="first_name"
                    required
                    placeholder="e.g. Rahul"
                    value={formData.first_name}
                    onChange={handleChange}
                    className="w-full bg-white/50 dark:bg-slate-900/50 border border-slate-300 dark:border-slate-700/50 rounded-xl px-4 py-3 text-slate-800 dark:text-slate-200 placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:border-violet-500 transition"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">Last Name</label>
                  <input
                    type="text"
                    name="last_name"
                    required
                    placeholder="e.g. Sharma"
                    value={formData.last_name}
                    onChange={handleChange}
                    className="w-full bg-white/50 dark:bg-slate-900/50 border border-slate-300 dark:border-slate-700/50 rounded-xl px-4 py-3 text-slate-800 dark:text-slate-200 placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:border-violet-500 transition"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">Username</label>
                  <input
                    type="text"
                    name="username"
                    required
                    placeholder="e.g. rahul123"
                    value={formData.username}
                    onChange={handleChange}
                    className="w-full bg-white/50 dark:bg-slate-900/50 border border-slate-300 dark:border-slate-700/50 rounded-xl px-4 py-3 text-slate-800 dark:text-slate-200 placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:border-violet-500 transition"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">Password</label>
                  <input
                    type="password"
                    name="password"
                    required
                    placeholder="Create a password"
                    value={formData.password}
                    onChange={handleChange}
                    className="w-full bg-white/50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-xl px-4 py-3 text-slate-800 dark:text-slate-200 placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:border-violet-500 transition"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">Date of Birth</label>
                  <input
                    type="date"
                    name="date_of_birth"
                    value={formData.date_of_birth}
                    onChange={handleChange}
                    className="w-full bg-white/50 dark:bg-slate-900/50 border border-slate-300 dark:border-slate-700/50 rounded-xl px-4 py-3 text-slate-800 dark:text-slate-200 focus:outline-none focus:border-violet-500 transition"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">School Name</label>
                  <input
                    type="text"
                    name="school_name"
                    placeholder="e.g. St. Xavier High School"
                    value={formData.school_name}
                    onChange={handleChange}
                    className="w-full bg-white/50 dark:bg-slate-900/50 border border-slate-300 dark:border-slate-700/50 rounded-xl px-4 py-3 text-slate-800 dark:text-slate-200 placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:border-violet-500 transition"
                  />
                </div>
              </div>

              {/* Preferences Section */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold font-outfit text-blue-300 flex items-center gap-2">
                  <Compass size={18} /> Planner Preferences
                </h3>

                <div>
                  <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">Medium of Instruction</label>
                  <select
                    name="medium"
                    value={formData.medium}
                    onChange={handleChange}
                    className="w-full bg-white/50 dark:bg-slate-900/50 border border-slate-300 dark:border-slate-700/50 rounded-xl px-4 py-3 text-slate-800 dark:text-slate-200 focus:outline-none focus:border-blue-500 transition"
                  >
                    <option value="English">English</option>
                    <option value="Marathi">Marathi</option>
                    <option value="Hindi">Hindi</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">Study Goal</label>
                  <select
                    name="study_goal"
                    value={formData.study_goal}
                    onChange={handleChange}
                    className="w-full bg-white/50 dark:bg-slate-900/50 border border-slate-300 dark:border-slate-700/50 rounded-xl px-4 py-3 text-slate-800 dark:text-slate-200 focus:outline-none focus:border-blue-500 transition"
                  >
                    <option value="EXAM_PREPARATION">Exam Preparation (Rigorous)</option>
                    <option value="SKILL_BUILDING">Skill Building (General)</option>
                    <option value="GENERAL_LEARNING">General Learning (Balanced)</option>
                  </select>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">Daily Hours</label>
                    <input
                      type="number"
                      name="daily_study_hours"
                      required
                      min="0.5"
                      max="12"
                      step="0.5"
                      value={formData.daily_study_hours}
                      onChange={handleChange}
                      className="w-full bg-white/50 dark:bg-slate-900/50 border border-slate-300 dark:border-slate-700/50 rounded-xl px-4 py-3 text-slate-800 dark:text-slate-200 focus:outline-none focus:border-blue-500 transition"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">Time of Day</label>
                    <select
                      name="preferred_study_time"
                      value={formData.preferred_study_time}
                      onChange={handleChange}
                      className="w-full bg-white/50 dark:bg-slate-900/50 border border-slate-300 dark:border-slate-700/50 rounded-xl px-4 py-3 text-slate-800 dark:text-slate-200 focus:outline-none focus:border-blue-500 transition"
                    >
                      <option value="MORNING">Morning</option>
                      <option value="AFTERNOON">Afternoon</option>
                      <option value="EVENING">Evening</option>
                      <option value="NIGHT">Night</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">Preferred Start Time</label>
                    <input
                      type="time"
                      name="preferred_study_start_time"
                      required
                      value={formData.preferred_study_start_time}
                      onChange={handleChange}
                      className="w-full bg-white/50 dark:bg-slate-900/50 border border-slate-300 dark:border-slate-700/50 rounded-xl px-4 py-3 text-slate-800 dark:text-slate-200 focus:outline-none focus:border-blue-500 transition"
                    />
                  </div>
                  <div className="flex flex-col justify-end">
                    <span className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">Auto-Calculated End Time</span>
                    <div className="w-full bg-slate-100/50 dark:bg-slate-900/30 border border-dashed border-slate-350 dark:border-slate-800 rounded-xl px-4 py-3 text-slate-850 dark:text-slate-250 font-bold font-mono">
                      {calculateEndTime(formData.preferred_study_start_time, formData.daily_study_hours) || 'N/A'}
                    </div>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">Revision Preference</label>
                  <select
                    name="revision_preference"
                    value={formData.revision_preference}
                    onChange={handleChange}
                    className="w-full bg-white/50 dark:bg-slate-900/50 border border-slate-300 dark:border-slate-700/50 rounded-xl px-4 py-3 text-slate-800 dark:text-slate-200 focus:outline-none focus:border-blue-500 transition"
                  >
                    <option value="DAILY">Daily Revision Slots Only</option>
                    <option value="WEEKLY">Weekly Pack Revision Only</option>
                    <option value="BOTH">Both Daily & Weekly Revision</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Academic Calendar Bounds */}
            <div className="space-y-4 pt-4 border-t border-slate-800">
              <h3 className="text-lg font-semibold font-outfit text-fuchsia-300 flex items-center gap-2">
                <Calendar size={18} /> Academic Year Settings
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                The entry-point resolver relies on these dates to determine whether to start you on Standard 5-6 baseline diagnostics or Standard 7 current syllabus tasks.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-xs font-semibold text-slate-505 dark:text-slate-400 uppercase tracking-wider mb-2">Start Date</label>
                  <input
                    type="date"
                    name="academic_year_start_date"
                    required
                    value={formData.academic_year_start_date}
                    onChange={handleChange}
                    className="w-full bg-white/50 dark:bg-slate-900/50 border border-slate-300 dark:border-slate-700/50 rounded-xl px-4 py-3 text-slate-800 dark:text-slate-200 focus:outline-none focus:border-fuchsia-500 transition"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-505 dark:text-slate-400 uppercase tracking-wider mb-2">End Date</label>
                  <input
                    type="date"
                    name="academic_year_end_date"
                    required
                    value={formData.academic_year_end_date}
                    onChange={handleChange}
                    className="w-full bg-white/50 dark:bg-slate-900/50 border border-slate-300 dark:border-slate-700/50 rounded-xl px-4 py-3 text-slate-800 dark:text-slate-200 focus:outline-none focus:border-fuchsia-500 transition"
                  />
                </div>
              </div>
            </div>

            {/* Submit */}
            <div className="pt-6 text-center space-y-4">
              <button
                type="submit"
                disabled={loading}
                className="bg-gradient-to-r from-violet-600 to-blue-600 hover:from-violet-500 hover:to-blue-500 text-white font-semibold rounded-2xl px-12 py-4 shadow-lg hover:shadow-violet-900/40 hover:-translate-y-0.5 transition duration-150 disabled:opacity-50 disabled:pointer-events-none"
              >
                {loading ? 'Initializing Profile...' : 'Begin Onboarding'}
              </button>
              
              <button
                type="button"
                onClick={() => setIsLogin(true)}
                className="text-xs text-slate-400 hover:text-slate-200 underline block mx-auto transition"
              >
                Already onboarded? Sign in to load your workspace
              </button>
            </div>
          </>
        )}
      </form>
    </div>
  );
}
