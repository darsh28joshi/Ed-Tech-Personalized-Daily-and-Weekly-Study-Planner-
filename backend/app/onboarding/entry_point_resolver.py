"""
Entry Point Resolver — Pure Logic (no DB/network calls)

Determines the diagnostic entry point based on how far into the academic year
the student currently is. This runs once at onboarding time and the result is
stored on the diagnostic_sessions row — it is never re-derived later.
"""

from datetime import date
import enum


class EntryPoint(str, enum.Enum):
    """
    Maps directly to the MySQL enum on diagnostic_sessions.entry_point.
    """
    START_OF_YEAR = "START_OF_YEAR"
    MID_SEMESTER = "MID_SEMESTER"
    END_OF_TERM = "END_OF_TERM"


# ---------- Named thresholds (not magic numbers) ----------
# WHY 0.15: The first ~6–8 weeks of a ~10-month academic year. At this point,
# barely any Std 7 content has been covered, so testing Std 7 chapters would
# measure guessing, not mastery. The diagnostic uses only Std 5–6 questions.
EARLY_THRESHOLD = 0.15

# WHY 0.85: The last ~15% of the academic year is a revision/exam window.
# Testing new content this late isn't useful — the student should go straight
# to the planner using whatever chapter_mastery already exists.
LATE_THRESHOLD = 0.85


def resolve_entry_point(
    start_date: date,
    end_date: date,
    today: date | None = None,
) -> EntryPoint:
    """
    Pure function — fully unit-testable with no side effects.

    Parameters
    ----------
    start_date : Academic year start date.
    end_date   : Academic year end date.
    today      : Override for testing; defaults to date.today().

    Returns
    -------
    EntryPoint enum value.

    Clamping behaviour
    ------------------
    If `today` falls outside [start_date, end_date] (e.g. mid-summer testing),
    we clamp to the nearest boundary case rather than erroring:
    - Before start_date → treated as 0% elapsed → START_OF_YEAR
    - After end_date    → treated as 100% elapsed → END_OF_TERM
    """
    if start_date >= end_date:
        raise ValueError(
            f"start_date ({start_date}) must be strictly before end_date ({end_date})"
        )

    if today is None:
        today = date.today()

    total_days = (end_date - start_date).days
    elapsed_days = (today - start_date).days

    # Clamp elapsed_days into [0, total_days] so out-of-range dates
    # map to the nearest boundary instead of producing nonsensical results.
    elapsed_days = max(0, min(elapsed_days, total_days))

    percent_elapsed = elapsed_days / total_days

    if percent_elapsed < EARLY_THRESHOLD:
        return EntryPoint.START_OF_YEAR
    elif percent_elapsed <= LATE_THRESHOLD:
        return EntryPoint.MID_SEMESTER
    else:
        return EntryPoint.END_OF_TERM
