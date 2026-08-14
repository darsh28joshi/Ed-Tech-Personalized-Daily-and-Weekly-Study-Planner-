AuraStudy — AI-Adaptive Personalized Daily & Weekly Study Planner

AuraStudy is a state-of-the-art, web-based AI-Adaptive Personalized Study Planner designed to dynamically customize educational paths for students. It maps individual knowledge levels via section-wise adaptive assessments, calculates dynamic block durations, and generates highly-personalized, auto-scheduled daily and weekly learning schedules.

---

## 🚀 Key Features

### 1. Dynamic Personalized Onboarding
- **Time Preferences**: Students can specify a `preferred_study_start_time` (e.g., `06:00 PM`) and their target daily study hours.
- **Computed End Times**: The system automatically computes and displays the expected study end time, taking into account required study blocks and intervals.
- **Configurable Parameters**: Collects academic year milestones, study focus paths, and visual theme preferences.

### 2. Section-Wise Adaptive Diagnostic Assessment
- **Curated Multi-Subject Structure**: The assessment contains exactly **49 questions** distributed evenly across **7 sections** (7 questions each):
  1. Aptitude Section
  2. Mathematics
  3. Science (General Science / Environmental Studies Part 1)
  4. History and Civics (History & Civics / Environmental Studies Part 2)
  5. Geography
  6. Hindi
  7. Marathi
- **End Test Capability**: A prominent, red **End Test** button allows students to complete and submit their progress early at any point during the assessment for grading.
- **Segmented Navigation**: Dynamic UI with section tabs and 7-dot pagination indicators per subject section.

### 3. Dynamic Planner Slot Durations
- **Time-Taken Analysis**: The planner evaluates total seconds spent per section in the latest completed diagnostic assessment.
- **Scale Formula**: Computes custom candidate costs (minutes) using:  
  $$\text{minutes} = \max(30, \min(90, \text{total\_seconds} \mathbin{/} 6))$$
- **Daily & Weekly Generation**: Custom subject durations are dynamically injected into daily and weekly schedules with strict **5-minute breaks** between study slots.

---

## 🛠️ Technology Stack

- **Backend**: FastAPI, SQLAlchemy Asyncio, Uvicorn, MySQL database.
- **Frontend**: Vite + React, TypeScript, TailwindCSS, Lucide React (for micro-animations and responsive icons).
- **Launcher**: Batch script orchestration (`run_project.bat`).

---

## 📂 Project Structure

```text
study planner/
├── backend/
│   ├── app/
│   │   ├── main.py              # Application entry point & migrations
│   │   ├── database.py          # SQLAlchemy engine & session setup
│   │   ├── models/              # SQLAlchemy DB models
│   │   ├── diagnostic/          # Assessment endpoints & test picker logic
│   │   ├── planner/             # Daily & weekly plan generation engine
│   │   └── onboarding/          # Profiles & credential management
│   └── venv/                    # Python virtual environment
├── frontend/
│   ├── src/
│   │   ├── components/          # Diagnostic, Dashboard, Onboarding, Profile
│   │   ├── App.tsx              # Main layout, router state, and modals
│   │   └── index.css            # Base Tailwind and glassmorphic designs
│   └── package.json
└── run_project.bat              # Dev server launcher batch script
```

---

## 🏃 Run the Project

1. Ensure you have **MySQL** installed and running on `localhost:3006` (or update database configurations in `backend/app/config.py`).
2. Make sure your Python dependencies and Node modules are installed.
3. From the project directory, run:
   ```cmd
   run_project.bat
   ```
4. Access the web interface at:
   - **Frontend App**: `http://localhost:3000`
   - **FastAPI docs**: `http://127.0.0.1:8001/docs`
```

