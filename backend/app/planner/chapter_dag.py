"""
Chapter DAG — Pure Logic (no DB/network calls)

Handles prerequisite ordering of chapters. Since Standard 7 chapters follow
a sequential curriculum, we topologically sort them based on subject_id
and chapter_number / display_order.
"""

from typing import List, Dict


class ChapterDAG:
    @classmethod
    def topological_sort(cls, chapters: List[dict]) -> List[dict]:
        """
        Sorts chapters with prerequisite ordering (chapter_number ascending within
        each subject) and round-robin interleaving across subjects so that no
        single subject dominates the head of the list.

        Input list elements should have:
          - 'chapter_id': int
          - 'subject_id': int
          - 'chapter_number': int
          - 'display_order': int
        """
        from collections import deque

        # 1. Group by subject
        subject_groups: Dict[int, list] = {}
        for ch in chapters:
            sub_id = ch['subject_id']
            subject_groups.setdefault(sub_id, []).append(ch)

        # 2. Sort each group internally by chapter_number, then display_order
        queues: List[deque] = []
        for sub_id in sorted(subject_groups.keys()):
            sorted_group = sorted(
                subject_groups[sub_id],
                key=lambda x: (x.get('chapter_number', 0), x.get('display_order', 0))
            )
            queues.append(deque(sorted_group))

        # 3. Round-robin interleave across subjects
        interleaved: List[dict] = []
        while queues:
            next_round_queues = []
            for q in queues:
                interleaved.append(q.popleft())
                if q:
                    next_round_queues.append(q)
            queues = next_round_queues

        return interleaved
