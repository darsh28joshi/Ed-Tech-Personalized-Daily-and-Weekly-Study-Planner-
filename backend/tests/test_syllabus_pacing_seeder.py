from datetime import date
from app.onboarding.syllabus_pacing_seeder import calculate_last_taught_chapter, compute_percent_elapsed


def test_calculate_pacing():
    # 0%
    assert calculate_last_taught_chapter(0.0, 10) == 0
    # 50%
    assert calculate_last_taught_chapter(0.5, 10) == 5
    # 100%
    assert calculate_last_taught_chapter(1.0, 10) == 10
    # Between chapters rounds up (ceil)
    assert calculate_last_taught_chapter(0.25, 10) == 3
    # Clamping
    assert calculate_last_taught_chapter(-0.5, 10) == 0
    assert calculate_last_taught_chapter(1.5, 10) == 10


def test_compute_percent_elapsed():
    start = date(2026, 6, 1)
    end = date(2027, 4, 30)
    today = date(2026, 12, 1)

    pct = compute_percent_elapsed(start, end, today)
    assert 0.0 <= pct <= 1.0
