"""
Priority Queue — Pure Logic (no DB/network calls)

Maintains a min-heap priority queue keyed by (next_review_date, -urgency_score).
This provides O(log n) access to the most overdue and urgent chapters.
"""

import heapq
from datetime import date
from typing import List, Tuple, Any


class PriorityQueue:
    """
    A wrapper around python's heapq module that stores items as:
    (next_review_date, neg_urgency, chapter_id, data)
    
    Since heapq is a min-heap:
    1. It pops the earliest next_review_date first (most overdue).
    2. If next_review_date is equal, it pops the item with the smallest neg_urgency
       (which means the largest positive urgency_score).
    """

    def __init__(self):
        self._heap: List[Tuple[date, float, int, Any]] = []

    def push(self, chapter_id: int, next_review_date: date, urgency_score: float, data: Any = None):
        """
        Pushes a chapter onto the queue.
        urgency_score should be positive; we store -urgency_score to invert priority order in min-heap.
        """
        # Element format: (next_review_date, -urgency_score, chapter_id, data)
        heapq.heappush(self._heap, (next_review_date, -urgency_score, chapter_id, data))

    def pop(self) -> Tuple[int, date, float, Any]:
        """
        Pops and returns the highest priority item as:
        (chapter_id, next_review_date, urgency_score, data)
        """
        if not self._heap:
            raise IndexError("pop from empty priority queue")
        
        next_review_date, neg_urgency, chapter_id, data = heapq.heappop(self._heap)
        return chapter_id, next_review_date, -neg_urgency, data

    def peek(self) -> Tuple[int, date, float, Any] | None:
        """
        Returns the highest priority item without removing it.
        """
        if not self._heap:
            return None
        next_review_date, neg_urgency, chapter_id, data = self._heap[0]
        return chapter_id, next_review_date, -neg_urgency, data

    def is_empty(self) -> bool:
        return len(self._heap) == 0

    def size(self) -> int:
        return len(self._heap)

    def get_all_ordered(self) -> List[Tuple[int, date, float, Any]]:
        """
        Drains the queue and returns all elements in priority order.
        """
        temp_heap = list(self._heap)
        ordered = []
        while temp_heap:
            next_review_date, neg_urgency, chapter_id, data = heapq.heappop(temp_heap)
            ordered.append((chapter_id, next_review_date, -neg_urgency, data))
        return ordered
