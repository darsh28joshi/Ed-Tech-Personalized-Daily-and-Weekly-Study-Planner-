"""
GreedyPlanner Strategy.

Selects chapters by sorting candidates in descending order of their
value/cost (value/time) ratio, adding them until the time budget is exhausted.
"""

from typing import List
from .planner_strategy import PlannerStrategy


class GreedyPlanner(PlannerStrategy):
    def plan_day(self, candidates: List[dict], time_budget_minutes: int) -> List[dict]:
        """
        Sorts candidates by value/cost descending and takes what fits.
        """
        # Sort by ratio descending; avoid divide-by-zero by checking cost > 0
        sorted_candidates = sorted(
            candidates,
            key=lambda x: (x['value'] / x['cost']) if x['cost'] > 0 else 0.0,
            reverse=True
        )

        selected = []
        remaining_budget = time_budget_minutes

        for item in sorted_candidates:
            cost = item['cost']
            if cost <= remaining_budget:
                selected.append(item)
                remaining_budget -= cost

        return selected
