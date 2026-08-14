"""
PlannerComparisonHarness.

Runs both KnapsackPlanner and GreedyPlanner on the same set of candidates
and reports differences in selected chapters, total value, and cost.
"""

from typing import Dict, List, Any
from .knapsack_planner import KnapsackPlanner
from .greedy_planner import GreedyPlanner


class PlannerComparisonHarness:
    @classmethod
    def compare_strategies(
        cls,
        candidates: List[dict],
        time_budget_minutes: int
    ) -> Dict[str, Any]:
        """
        Executes both planners and compiles comparison metrics.
        """
        kp = KnapsackPlanner()
        gp = GreedyPlanner()

        kp_selected = kp.plan_day(candidates, time_budget_minutes)
        gp_selected = gp.plan_day(candidates, time_budget_minutes)

        kp_ids = set(c['chapter_id'] for c in kp_selected)
        gp_ids = set(c['chapter_id'] for c in gp_selected)

        kp_value = sum(c['value'] for c in kp_selected)
        kp_cost = sum(c['cost'] for c in kp_selected)

        gp_value = sum(c['value'] for c in gp_selected)
        gp_cost = sum(c['cost'] for c in gp_selected)

        diverged = (kp_ids != gp_ids)

        return {
            "diverged": diverged,
            "knapsack": {
                "chapter_ids": list(c['chapter_id'] for c in kp_selected),
                "total_value": kp_value,
                "total_cost": kp_cost,
                "count": len(kp_selected)
            },
            "greedy": {
                "chapter_ids": list(c['chapter_id'] for c in gp_selected),
                "total_value": gp_value,
                "total_cost": gp_cost,
                "count": len(gp_selected)
            }
        }
