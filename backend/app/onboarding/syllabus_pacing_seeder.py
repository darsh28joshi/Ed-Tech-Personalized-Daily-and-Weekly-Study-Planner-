"""
Syllabus Pacing Seeder — Pure Logic (no DB/network calls)

PLACEHOLDER heuristic for this prototype. A real deployment would replace this
with actual school-reported pacing data (e.g. from a curriculum-management feed).

Given how far into the academic year we are, this estimates which chapters have
been taught so far, and returns the `last_taught_chapter_number` per subject.
"""

import math
from typing import List


def calculate_last_taught_chapter(
    percent_elapsed: float,
    total_chapters: int,
) -> int:
    """
    Returns the chapter_number of the estimated last-taught chapter.

    Formula: ceil(percent_elapsed × total_chapters)

    Examples:
        50% elapsed, 10 chapters → 5
        25% elapsed, 10 chapters → 3  (ceil rounds up)
         0% elapsed, 10 chapters → 0  (nothing taught yet)

    percent_elapsed is clamped to [0.0, 1.0] as a safety net.
    """
    percent_elapsed = max(0.0, min(percent_elapsed, 1.0))

    if total_chapters == 0:
        return 0

    return math.ceil(percent_elapsed * total_chapters)


def compute_percent_elapsed(
    start_date,
    end_date,
    today,
) -> float:
    """
    Utility that mirrors the same clamped-percentage logic from the entry-point
    resolver, but returns the raw float for use by the pacing seeder.
    """
    total_days = (end_date - start_date).days
    if total_days <= 0:
        return 0.0
    elapsed_days = (today - start_date).days
    elapsed_days = max(0, min(elapsed_days, total_days))
    return elapsed_days / total_days
