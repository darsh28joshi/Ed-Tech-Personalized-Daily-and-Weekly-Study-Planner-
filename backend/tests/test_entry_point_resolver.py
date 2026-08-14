from datetime import date
from app.onboarding.entry_point_resolver import resolve_entry_point, EntryPoint
import pytest


def test_start_of_year_entry_point():
    start_date = date(2026, 6, 1)
    end_date = date(2027, 4, 30)
    # Total days approx 333. 10% is ~33 days.
    today = date(2026, 7, 1)

    entry = resolve_entry_point(start_date, end_date, today)
    assert entry == EntryPoint.START_OF_YEAR


def test_mid_semester_entry_point():
    start_date = date(2026, 6, 1)
    end_date = date(2027, 4, 30)
    # Middle of the year
    today = date(2026, 12, 1)

    entry = resolve_entry_point(start_date, end_date, today)
    assert entry == EntryPoint.MID_SEMESTER


def test_end_of_term_entry_point():
    start_date = date(2026, 6, 1)
    end_date = date(2027, 4, 30)
    # Late in the year
    today = date(2027, 4, 1)

    entry = resolve_entry_point(start_date, end_date, today)
    assert entry == EntryPoint.END_OF_TERM


def test_clamp_before_start():
    start_date = date(2026, 6, 1)
    end_date = date(2027, 4, 30)
    # Before start date
    today = date(2026, 5, 1)

    entry = resolve_entry_point(start_date, end_date, today)
    assert entry == EntryPoint.START_OF_YEAR


def test_clamp_after_end():
    start_date = date(2026, 6, 1)
    end_date = date(2027, 4, 30)
    # After end date
    today = date(2027, 5, 10)

    entry = resolve_entry_point(start_date, end_date, today)
    assert entry == EntryPoint.END_OF_TERM


def test_invalid_dates():
    start_date = date(2027, 4, 30)
    end_date = date(2026, 6, 1)
    today = date(2026, 12, 1)

    with pytest.raises(ValueError):
        resolve_entry_point(start_date, end_date, today)
