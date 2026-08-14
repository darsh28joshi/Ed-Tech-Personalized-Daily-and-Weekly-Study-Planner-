"""
Task Completion and Carry-Forward Logic — Pure Logic.

Provides rules for task status changes and scheduling forced carry-over items:
- COMPLETED: Retired from queue, next_review_date nudged forward (+1 day).
- IN_PROGRESS: Held steady, carried forward to tomorrow with standard priority.
- SKIPPED: Urgency penalty, carried forward to tomorrow with boosted priority.
"""

from datetime import date, timedelta
from typing import List, Dict, Tuple


def sweep_stale_tasks(today: date, pending_tasks: List[dict]) -> List[dict]:
    """
    Sweeps pending tasks that are past their plan_date, updating them to SKIPPED.
    """
    swept = []
    for t in pending_tasks:
        if t['plan_date'] < today and t['status'] == 'PENDING':
            updated = dict(t)
            updated['status'] = 'SKIPPED'
            swept.append(updated)
    return swept


def resolve_carry_forward_candidates(
    incomplete_tasks: List[dict],
    today: date
) -> Tuple[List[dict], int]:
    """
    Processes yesterday's IN_PROGRESS and SKIPPED tasks.
    Returns (forced_candidates, total_cost_reserved).

    Forced candidates have:
      - 'chapter_id': int
      - 'cost': int (allocated minutes)
      - 'value': very high priority to guarantee selection (floor priority)
      - 'carried_forward_from_task_id': int
      - 'metadata': dict
    """
    forced_candidates = []
    reserved_minutes = 0

    for task in incomplete_tasks:
        cost = task['allocated_minutes']
        status = task['status']

        # Determine value (urgency bump)
        # SKIPPED gets a higher urgency/value bump than IN_PROGRESS
        if status == 'SKIPPED':
            val = 10000.0  # High priority floor
        else:
            val = 5000.0   # Medium priority floor

        forced_candidates.append({
            "chapter_id": task['chapter_id'],
            "cost": cost,
            "value": val,
            "carried_forward_from_task_id": task['task_id'],
            "metadata": {
                "chapter_name": task['chapter_name'],
                "subject_name": task['subject_name']
            }
        })
        reserved_minutes += cost

    return forced_candidates, reserved_minutes
