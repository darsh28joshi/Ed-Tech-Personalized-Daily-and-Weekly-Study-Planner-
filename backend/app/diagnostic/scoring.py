"""
ScoringEngine — Pure Logic (no DB/network calls)

Handles grading, speed-guess discounting, percentile calculation via normal CDF,
and composite study health score computation.
"""

import math
from typing import List, Dict


class ScoringEngine:
    # Difficulty weights from specification
    # Easy = 1.0, Average = 1.5, Difficult = 2.0
    WEIGHTS = {
        'Easy': 1.0,
        'Average': 1.5,
        'Difficult': 2.0,
        # Handle uppercase variations if any (e.g. for aptitude questions)
        'EASY': 1.0,
        'AVERAGE': 1.5,
        'DIFFICULT': 2.0
    }

    @classmethod
    def _normal_cdf(cls, x: float, mu: float = 60.0, sigma: float = 15.0) -> float:
        """
        Approximates the normal Cumulative Distribution Function (CDF) using math.erf.
        Used to convert raw percentage scores into percentiles.
        Reference mean (mu) = 60.0, standard deviation (sigma) = 15.0.
        """
        if sigma <= 0.0:
            return 100.0
        return (1.0 + math.erf((x - mu) / (sigma * math.sqrt(2.0)))) / 2.0 * 100.0

    @classmethod
    def compute_chapter_mastery(cls, responses: List[dict]) -> float:
        """
        Computes the difficulty-weighted accuracy for a set of academic responses.
        Each response dict must contain:
        - is_correct: bool
        - difficulty: str ('Easy', 'Average', 'Difficult')
        - time_taken_seconds: int
        - estimated_seconds: int
        """
        if not responses:
            return 0.0

        total_weight = 0.0
        earned_weight = 0.0

        for r in responses:
            diff = r.get('difficulty') or 'Average'
            w = cls.WEIGHTS.get(diff, 1.5)
            total_weight += w

            if r.get('is_correct'):
                time_taken = r.get('time_taken_seconds')
                est_seconds = r.get('estimated_seconds')

                # Speed-guess discount:
                # Apply 30% weight discount (multiplier = 0.7) if time_taken < 40% of estimated_seconds.
                # Reason: Very fast correct answers are likely due to lucky guesses.
                if time_taken is not None and est_seconds is not None and est_seconds > 0:
                    if time_taken < 0.4 * est_seconds:
                        earned_weight += w * 0.7
                    else:
                        earned_weight += w
                else:
                    earned_weight += w

        if total_weight == 0.0:
            return 0.0

        return (earned_weight / total_weight) * 100.0

    @classmethod
    def compute_aptitude_score_and_percentile(cls, responses: List[dict]) -> tuple[float, float]:
        """
        Computes raw aptitude score percentage (0-100) and normal-CDF approximated percentile.
        Reference cohort: Mean = 60.0, SD = 15.0.
        Each response dict must contain:
        - is_correct: bool
        - difficulty: str ('EASY', 'AVERAGE', 'DIFFICULT')
        """
        if not responses:
            return 0.0, 0.0

        total_weight = 0.0
        earned_weight = 0.0

        for r in responses:
            diff = r.get('difficulty') or 'AVERAGE'
            w = cls.WEIGHTS.get(diff, 1.5)
            total_weight += w
            if r.get('is_correct'):
                earned_weight += w

        if total_weight == 0.0:
            return 0.0, 0.0

        raw_percentage = (earned_weight / total_weight) * 100.0
        percentile = cls._normal_cdf(raw_percentage, mu=60.0, sigma=15.0)

        # Clamp percentile between 0.1 and 99.9 for realistic output
        percentile = max(0.1, min(percentile, 99.9))

        return raw_percentage, percentile

    @classmethod
    def compute_aptitude_category_breakdown(cls, responses: List[dict]) -> Dict[str, dict]:
        """
        Groups responses by category and computes accuracy & percentile for each.
        Each response must contain:
        - category: str
        - is_correct: bool
        - difficulty: str
        """
        grouped = {}
        for r in responses:
            cat = r.get('category')
            if cat:
                grouped.setdefault(cat, []).append(r)

        results = {}
        for cat, cat_responses in grouped.items():
            acc, pct = cls.compute_aptitude_score_and_percentile(cat_responses)
            results[cat] = {"accuracy": acc, "percentile": pct}

        return results

    @classmethod
    def compute_study_health_score(
        cls,
        avg_chapter_mastery: float,
        aptitude_percentile: float,
        syllabus_coverage_confidence: float
    ) -> float:
        """
        Composite reporting metric.
        Formula: 0.5 * avg(chapter_mastery) + 0.3 * aptitude_percentile + 0.2 * syllabus_coverage_confidence
        """
        return (avg_chapter_mastery * 0.5) + (aptitude_percentile * 0.3) + (syllabus_coverage_confidence * 0.2)
