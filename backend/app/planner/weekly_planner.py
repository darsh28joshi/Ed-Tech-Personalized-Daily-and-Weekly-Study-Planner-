"""
WeeklyPlanner Orchestrator — Pure Logic.

Combines ChapterDAG and WeeklyBinPacker to build the 7-day study schedule.
"""

from typing import List, Dict, Any
from .chapter_dag import ChapterDAG
from .weekly_bin_packer import WeeklyBinPacker


class WeeklyPlanner:
    @classmethod
    def generate_weekly_plan(
        cls,
        due_chapters: List[dict],  # Chapters ordered by priority
        daily_study_hours: float
    ) -> List[Dict[str, Any]]:
        """
        Creates the weekly plan:
        1. Topological sort per subject to respect curriculum sequence.
        2. First-Fit-Decreasing bin packing across 7 days.
        """
        if not due_chapters:
            return []

        # 1. Topological sort
        # Standard 7 chapters must follow sequential numbering order
        topo_sorted = ChapterDAG.topological_sort(due_chapters)

        # Re-sort slightly to keep priority:
        # A chapter with higher priority should still be packed first, unless it violates topo order.
        # Since ChapterDAG.topological_sort returns subject groupings in alphabetical/id order,
        # we can pass it directly to the bin packer which walks the list in sequence.
        # Let's preserve the sorted sequence returned by ChapterDAG.
        
        # 2. Bin packing
        return WeeklyBinPacker.pack_chapters(
            chapters=topo_sorted,
            daily_study_hours=daily_study_hours,
            num_days=7
        )
