from app.diagnostic.scoring import ScoringEngine
from app.diagnostic.test_picker import TestPicker
from app.onboarding.entry_point_resolver import EntryPoint
import pytest


def test_scoring_weights_and_speed_discount():
    # Easy: 1.0, Average: 1.5, Difficult: 2.0
    # Response 1: Easy, correct, 50s (no discount because 50 > 0.4 * 60)
    # Response 2: Average, correct, 5s (guess discount because 5 < 0.4 * 60)
    # Response 3: Difficult, incorrect, 10s
    responses = [
        {"difficulty": "Easy", "is_correct": True, "time_taken_seconds": 50, "estimated_seconds": 60},
        {"difficulty": "Average", "is_correct": True, "time_taken_seconds": 5, "estimated_seconds": 60},
        {"difficulty": "Difficult", "is_correct": False, "time_taken_seconds": 10, "estimated_seconds": 60}
    ]
    # Total Weight = 1.0 + 1.5 + 2.0 = 4.5
    # Earned Weight = 1.0 + 1.5 * 0.7 + 0.0 = 2.05
    # Expected Score = (2.05 / 4.5) * 100
    expected = (2.05 / 4.5) * 100.0
    score = ScoringEngine.compute_chapter_mastery(responses)
    assert abs(score - expected) < 1e-5


def test_aptitude_percentile_calculation():
    # Mean = 60.0, SD = 15.0
    # Let's get score for 1 correct EASY question (weight 1.0) out of 1.
    responses = [
        {"difficulty": "EASY", "is_correct": True}
    ]
    percentage, percentile = ScoringEngine.compute_aptitude_score_and_percentile(responses)
    assert percentage == 100.0
    # Percentile should be above 99% for 100% score (100 is 2.67 SDs above 60)
    assert percentile > 99.0


def test_test_picker_composition_and_order():
    # We should have 15 aptitude and 45 academic questions
    academic_pool = []
    # Generate 100 academic questions across subjects and standards
    for idx in range(100):
        std_num = 5 if idx % 3 == 0 else (6 if idx % 3 == 1 else 7)
        academic_pool.append({
            "question_id": idx,
            "subject_id": (idx % 7) + 1,
            "difficulty": "Easy" if idx % 2 == 0 else "Average",
            "estimated_seconds": 60,
            "chapter_id": idx,
            "chapter_number": (idx % 5) + 1,
            "standard_number": std_num
        })

    aptitude_pool = []
    categories = ["Numerical Reasoning", "Logical Reasoning", "Verbal Reasoning"]
    for idx in range(30):
        aptitude_pool.append({
            "question_id": idx,
            "category": categories[idx % len(categories)],
            "difficulty": "EASY",
            "estimated_seconds": 45
        })

    subjects_by_std = {
        5: [{"subject_id": idx, "subject_name": f"Sub {idx}"} for idx in range(1, 7)],
        6: [{"subject_id": idx, "subject_name": f"Sub {idx}"} for idx in range(1, 8)],
        7: [{"subject_id": idx, "subject_name": f"Sub {idx}"} for idx in range(1, 8)]
    }

    # START_OF_YEAR
    picked_soy = TestPicker.pick_questions(
        entry_point=EntryPoint.START_OF_YEAR,
        academic_pool=academic_pool,
        aptitude_pool=aptitude_pool,
        syllabus_progress={},
        subjects_by_std=subjects_by_std
    )
    # Total must be 60: 15 aptitude + 45 academic
    assert len(picked_soy) == 60
    # First 15 must be aptitude
    assert all(q['source'] == 'APTITUDE' for q in picked_soy[:15])
    # Next 45 must be academic
    assert all(q['source'] == 'ACADEMIC' for q in picked_soy[15:])
