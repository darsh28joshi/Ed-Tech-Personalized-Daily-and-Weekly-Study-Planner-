"""
WeeklyBinPacker — Pure Logic (no DB/network calls)

Distributes chapters across 7 days using a modified First-Fit-Decreasing (FFD)
heuristic. Bins correspond to days 1 to 7, each with daily_study_hours capacity.
Subject monotony rule: avoids scheduling the same subject on more than 2 consecutive days.
"""

from typing import List, Dict, Any


class WeeklyBinPacker:
    @classmethod
    def pack_chapters(
        cls,
        chapters: List[dict],
        daily_study_hours: float,
        num_days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Packs chapters into bins (days).
        
        Parameters
        ----------
        chapters : List of due chapter dicts, sorted in descending order of priority.
                   Each has:
                     - 'chapter_id': int
                     - 'cost': int (allocated minutes, e.g. 45)
                     - 'subject_id': int
                     - 'subject_name': str
                     - 'chapter_name': str
        daily_study_hours : Float capacity in hours (e.g. 2.0).
        num_days : Total bins (default 7 days).

        Returns
        -------
        A list of days, where each day has:
          - 'day_number': int (1 to 7)
          - 'allocated_minutes': int
          - 'capacity_minutes': int
          - 'tasks': List[dict]
        """
        capacity_minutes = int(daily_study_hours * 60)
        
        # Initialize bins
        bins = []
        for i in range(1, num_days + 1):
            bins.append({
                "day_number": i,
                "allocated_minutes": 0,
                "capacity_minutes": capacity_minutes,
                "tasks": [],
                # Track scheduled subjects on this day
                "subjects": set()
            })

        # Helper to check subject monotony
        def causes_consecutive_monotony(day_idx: int, subject_id: int) -> bool:
            """
            Checks if scheduling subject_id on day_idx would make it scheduled
            on 3 consecutive days (e.g. day_idx-2, day_idx-1, day_idx).
            """
            # Check backward
            if day_idx >= 2:
                prev1 = bins[day_idx - 1]
                prev2 = bins[day_idx - 2]
                if (subject_id in prev1["subjects"]) and (subject_id in prev2["subjects"]):
                    return True
            # Check forward
            if day_idx <= num_days - 3:
                next1 = bins[day_idx + 1]
                next2 = bins[day_idx + 2]
                if (subject_id in next1["subjects"]) and (subject_id in next2["subjects"]):
                    return True
            # Check middle
            if 1 <= day_idx <= num_days - 2:
                prev = bins[day_idx - 1]
                nxt = bins[day_idx + 1]
                if (subject_id in prev["subjects"]) and (subject_id in nxt["subjects"]):
                    return True
            return False

        for ch in chapters:
            cost = ch['cost']
            sub_id = ch['subject_id']

            # Find first bin it fits into
            for idx, day in enumerate(bins):
                if day["allocated_minutes"] + cost <= capacity_minutes:
                    # Check subject monotony
                    if not causes_consecutive_monotony(idx, sub_id):
                        day["tasks"].append(ch)
                        day["allocated_minutes"] += cost
                        day["subjects"].add(sub_id)
                        break

        # Convert set of subjects to list for JSON serialization
        for day in bins:
            if "subjects" in day:
                del day["subjects"]

        return bins
