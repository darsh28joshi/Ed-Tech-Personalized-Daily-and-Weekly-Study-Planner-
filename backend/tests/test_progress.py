from datetime import date, timedelta
from app.progress.ema import compute_ema_mastery
from app.progress.sm2 import calculate_sm2, resolve_quality_rating
from app.progress.priority_queue import PriorityQueue
import pytest


def test_ema_blending():
    # Test case 1: no old mastery (first session)
    assert compute_ema_mastery(80.0, None) == 80.0

    # Test case 2: blending with alpha=0.45
    # new = 0.45 * 90.0 + 0.55 * 50.0 = 40.5 + 27.5 = 68.0
    assert abs(compute_ema_mastery(90.0, 50.0) - 68.0) < 1e-5


def test_sm2_pathways():
    today = date(2026, 8, 12)

    # Test case 1: Failure (accuracy = 30% -> quality = 1)
    # repetitions reset to 0, interval = 1, next_review = today + 1 day
    interval, ef, rep, next_review = calculate_sm2(
        accuracy=30.0,
        previous_interval=6,
        ease_factor=2.5,
        repetitions=2,
        today=today
    )
    assert interval == 1
    assert rep == 0
    assert next_review == today + timedelta(days=1)

    # Test case 2: Success 1st rep (accuracy = 95% -> quality = 5)
    # repetitions = 1, interval = 1, next_review = today + 1 day, EF changes
    interval, ef, rep, next_review = calculate_sm2(
        accuracy=95.0,
        previous_interval=1,
        ease_factor=2.5,
        repetitions=0,
        today=today
    )
    assert interval == 1
    assert rep == 1
    assert ef > 2.5  # Quality 5 increases ease factor
    assert next_review == today + timedelta(days=1)

    # Test case 3: Success 3rd rep (accuracy = 80% -> quality = 4)
    # repetitions = 3, interval = round(previous_interval * EF)
    interval, ef, rep, next_review = calculate_sm2(
        accuracy=80.0,
        previous_interval=6,
        ease_factor=2.0,
        repetitions=2,
        today=today
    )
    assert rep == 3
    # interval should be round(6 * new_ef)
    expected_interval = round(6 * ef)
    assert interval == expected_interval
    assert next_review == today + timedelta(days=expected_interval)


def test_priority_queue_ordering():
    pq = PriorityQueue()
    today = date(2026, 8, 12)

    # Push 3 items:
    # Item A: next_review = tomorrow, urgency = 50
    # Item B: next_review = today, urgency = 200
    # Item C: next_review = today, urgency = 300
    pq.push(chapter_id=1, next_review_date=today + timedelta(days=1), urgency_score=50.0)
    pq.push(chapter_id=2, next_review_date=today, urgency_score=200.0)
    pq.push(chapter_id=3, next_review_date=today, urgency_score=300.0)

    # Expected Pop Order:
    # 1st pop: Item C (today, highest urgency score 300)
    # 2nd pop: Item B (today, urgency score 200)
    # 3rd pop: Item A (tomorrow, urgency score 50)
    
    ch_id, next_review, urgency, _ = pq.pop()
    assert ch_id == 3
    assert next_review == today
    assert urgency == 300.0

    ch_id, next_review, urgency, _ = pq.pop()
    assert ch_id == 2
    assert next_review == today
    assert urgency == 200.0

    ch_id, next_review, urgency, _ = pq.pop()
    assert ch_id == 1
    assert next_review == today + timedelta(days=1)
    assert urgency == 50.0
