"""
GapAnalysisEngine — Pure Logic (no DB/network calls)

Rule-based mapping of aptitude category scores into plain-language study suggestions.
Surfaced to the student via opt-in view; never impacts planner scheduling.
"""

from typing import Dict, List


class GapAnalysisEngine:
    SUGGESTIONS = {
        "Numerical Reasoning": (
            "Practice basic mental math daily. Focus on word problems and estimating "
            "answers before calculating to improve arithmetic fluency."
        ),
        "Logical Reasoning": (
            "Practice solving logical deduction puzzles like Sudoku and sequence "
            "completions. Work on breaking down complex premises step-by-step."
        ),
        "Verbal Reasoning": (
            "Read widely across languages and subjects. Practice summarizing paragraphs, "
            "identifying central themes, and resolving vocabulary context clues."
        ),
        "Pattern Recognition": (
            "Look for mathematical and visual patterns in sequences of shapes and numbers. "
            "Work on identifying structural rules in puzzles."
        ),
        "Spatial Reasoning": (
            "Engage in geometry/mensuration visualization practice. Try sketch drawings, "
            "visualizing 3D shapes from flat nets, and paper-folding puzzles."
        ),
        "Analytical Problem Solving": (
            "Work on solving multi-step optimization and scheduling problems. practice "
            "identifying core constraints and planning tasks systematically."
        ),
        "Data Interpretation": (
            "Spend time reading tables, bar graphs, and pie charts. Practice calculating "
            "differences, sums, and percentages from raw visual data formats."
        )
    }

    @classmethod
    def generate_suggestions(cls, category_scores: Dict[str, dict], threshold_accuracy: float = 60.0) -> List[dict]:
        """
        Takes category_scores output from ScoringEngine.
        Returns a list of suggestion dictionaries for categories below the threshold.
        """
        suggestions = []

        for category, scores in category_scores.items():
            if scores['accuracy'] < threshold_accuracy:
                suggestion_text = cls.SUGGESTIONS.get(
                    category,
                    "Review core concepts and practice consistently."
                )
                suggestions.append({
                    "category": category,
                    "accuracy": scores['accuracy'],
                    "suggestion": suggestion_text
                })

        # Sort by lowest accuracy first (most urgent gaps first)
        suggestions.sort(key=lambda x: x['accuracy'])
        return suggestions
