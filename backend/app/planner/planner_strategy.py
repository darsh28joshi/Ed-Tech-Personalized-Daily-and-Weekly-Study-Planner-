"""
PlannerStrategy interface (Protocol).

HARD CONSTRAINT:
----------------
As per the product specification, the daily and weekly planners are strictly
academic-mastery-driven. This file, greedy_planner.py, and knapsack_planner.py
MUST NEVER import from:
- app.models.aptitude_category_scores
- app.models.diagnostic.DiagnosticReport (aptitude_score or aptitude_percentile)
- Or any aptitude-related scores table.

Aptitude category data is reserved exclusively for the opt-in Gap Analysis view
and has no influence on student study schedule generation.
"""

from typing import List, Protocol


class PlannerStrategy(Protocol):
    def plan_day(self, candidates: List[dict], time_budget_minutes: int) -> List[dict]:
        """
        Generates the daily study plan from a candidate pool.

        Parameters
        ----------
        candidates : A list of dictionaries, where each dict has:
                     - 'chapter_id': int
                     - 'value': float (weakness * exam_weight * overdue_ness)
                     - 'cost': int (allocated minutes, e.g. 45)
                     - 'metadata': dict
        time_budget_minutes : Maximum study time allowed for the day (e.g. 120 minutes).

        Returns
        -------
        A list of selected candidate dictionaries.
        """
        ...
