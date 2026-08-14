from app.planner.knapsack_planner import KnapsackPlanner
from app.planner.greedy_planner import GreedyPlanner
from app.planner.chapter_dag import ChapterDAG
from app.planner.weekly_bin_packer import WeeklyBinPacker
from app.planner.task_completion import resolve_carry_forward_candidates
import pytest


def test_knapsack_planner_optimization():
    planner = KnapsackPlanner()
    # 4 candidates
    candidates = [
        {"chapter_id": 1, "cost": 30, "value": 10.0},
        {"chapter_id": 2, "cost": 45, "value": 25.0},
        {"chapter_id": 3, "cost": 60, "value": 30.0},
        {"chapter_id": 4, "cost": 30, "value": 15.0}
    ]
    # Budget = 90
    # Option 1: item 1 + 2 + 4 (cost=105, over budget)
    # Option 2: item 2 + 3 (cost=105, over budget)
    # Option 3: item 2 + 4 + 1 (cost=105, over budget)
    # Option 4: item 2 + 3 (cost=105)
    # Best fit <= 90:
    # item 2 + 3? No, cost=105.
    # item 1 + 3? cost=90, value=40.
    # item 2 + 4? cost=75, value=40.
    # item 2 + 4 + 1? cost=105.
    # Let's check item 2 + 3 -> too large.
    # What about item 1 + 2 + 4? cost=105 -> too large.
    # What about item 1 + 4? cost=60, value=25.
    # What about item 2 + 4? cost=75, value=40.
    # What about item 2 + 1? cost=75, value=35.
    # What about item 3 + 4? cost=90, value=45. (Best!)
    
    selected = planner.plan_day(candidates, 90)
    selected_ids = [c['chapter_id'] for c in selected]
    assert set(selected_ids) == {3, 4}


def test_greedy_planner_heuristics():
    planner = GreedyPlanner()
    # Candidates with different value/cost ratios
    # Item 1: ratio = 10/10 = 1.0
    # Item 2: ratio = 40/20 = 2.0
    # Item 3: ratio = 30/15 = 2.0 (same ratio, let's see)
    # Item 4: ratio = 5/10 = 0.5
    candidates = [
        {"chapter_id": 1, "cost": 10, "value": 10.0},
        {"chapter_id": 2, "cost": 20, "value": 40.0},
        {"chapter_id": 3, "cost": 15, "value": 30.0},
        {"chapter_id": 4, "cost": 10, "value": 5.0}
    ]
    # Budget = 35
    # Sorted by ratio: Item 2 (2.0), Item 3 (2.0), Item 1 (1.0), Item 4 (0.5)
    # Item 2 fits (cost=20, remaining=15)
    # Item 3 fits (cost=15, remaining=0)
    # Item 1 and 4 do not fit.
    # Selected should be {2, 3}
    selected = planner.plan_day(candidates, 35)
    selected_ids = [c['chapter_id'] for c in selected]
    assert set(selected_ids) == {2, 3}


def test_chapter_dag_sorting():
    chapters = [
        {"chapter_id": 1, "subject_id": 101, "chapter_number": 3, "display_order": 3},
        {"chapter_id": 2, "subject_id": 101, "chapter_number": 1, "display_order": 1},
        {"chapter_id": 3, "subject_id": 101, "chapter_number": 2, "display_order": 2},
        {"chapter_id": 4, "subject_id": 102, "chapter_number": 2, "display_order": 2},
        {"chapter_id": 5, "subject_id": 102, "chapter_number": 1, "display_order": 1}
    ]
    sorted_list = ChapterDAG.topological_sort(chapters)
    # For subject 101: order should be 2, 3, 1
    # For subject 102: order should be 5, 4
    sub101_sorted = [c['chapter_id'] for c in sorted_list if c['subject_id'] == 101]
    sub102_sorted = [c['chapter_id'] for c in sorted_list if c['subject_id'] == 102]
    
    assert sub101_sorted == [2, 3, 1]
    assert sub102_sorted == [5, 4]


def test_weekly_bin_packer_monotony():
    # Capacity = 90 minutes per day
    # Chapter size = 45 minutes
    # Let's try to schedule 8 chapters of subject 101 (cost=45 each).
    # If we place them on Day 1 (cost=90, 2 tasks), Day 2 (cost=90, 2 tasks).
    # On Day 3, we cannot schedule subject 101 because it would make it scheduled on 3 consecutive days!
    # Day 3 should have 0 tasks from subject 101.
    chapters = []
    for idx in range(1, 10):
        chapters.append({
            "chapter_id": idx,
            "cost": 45,
            "subject_id": 101,
            "subject_name": "Math",
            "chapter_name": f"Ch {idx}"
        })

    plan = WeeklyBinPacker.pack_chapters(chapters, daily_study_hours=1.5, num_days=7)
    # Check that Day 3 has no tasks scheduled since they all belong to subject 101,
    # which would violate the monotony rule.
    assert len(plan[2]["tasks"]) == 0  # Day 3 (0-indexed index 2)
    assert len(plan[0]["tasks"]) == 2  # Day 1
    assert len(plan[1]["tasks"]) == 2  # Day 2
    assert len(plan[3]["tasks"]) == 2  # Day 4
    assert len(plan[4]["tasks"]) == 2  # Day 5
    assert len(plan[5]["tasks"]) == 0  # Day 6 (monotony again)
