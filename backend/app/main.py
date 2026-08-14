from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.onboarding.router import router as onboarding_router
from app.diagnostic.router import router as diagnostic_router
from app.progress.router import router as progress_router
from app.planner.router import router as planner_router

app = FastAPI(
    title="Personalized Study Planner API",
    description="Adaptive daily and weekly academic study scheduler prototype."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount feature routers
app.include_router(onboarding_router)
app.include_router(diagnostic_router)
app.include_router(progress_router)
app.include_router(planner_router)


@app.on_event("startup")
async def startup_db_migration():
    from app.database import engine
    from sqlalchemy import text
    try:
        async with engine.begin() as conn:
            # Check if columns exist using SHOW COLUMNS
            res = await conn.execute(text("SHOW COLUMNS FROM student_profiles LIKE 'username'"))
            row = res.fetchone()
            if not row:
                # Add columns username and password
                await conn.execute(text("ALTER TABLE student_profiles ADD COLUMN username VARCHAR(100) UNIQUE NULL"))
                await conn.execute(text("ALTER TABLE student_profiles ADD COLUMN password VARCHAR(255) NULL"))

            # Check for preferred_study_start_time and preferred_study_end_time
            res_time = await conn.execute(text("SHOW COLUMNS FROM student_profiles LIKE 'preferred_study_start_time'"))
            row_time = res_time.fetchone()
            if not row_time:
                await conn.execute(text("ALTER TABLE student_profiles ADD COLUMN preferred_study_start_time VARCHAR(5) NULL"))
                await conn.execute(text("ALTER TABLE student_profiles ADD COLUMN preferred_study_end_time VARCHAR(5) NULL"))

            pass
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Startup DB migration failed: {e}")


@app.get("/")
def read_root():
    return {
        "message": "Welcome to the Personalized Study Planner API",
        "version": "2.0.0",
        "docs_url": "/docs"
    }
