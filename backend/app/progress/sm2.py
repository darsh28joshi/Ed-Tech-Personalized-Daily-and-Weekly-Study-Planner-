"""
SM-2 Spaced Repetition — Pure Logic (no DB/network calls)

Implements the SuperMemo-2 (SM-2) algorithm for calculating next review date,
interval, ease factor, and repetitions based on quality ratings.
"""

from datetime import date, timedelta
from typing import Tuple


def resolve_quality_rating(accuracy: float) -> int:
    """
    Resolves a 0-5 quality rating from session accuracy percentage.
    - >= 90% -> 5 (perfect response)
    - >= 75% -> 4 (correct response after a hesitation)
    - >= 60% -> 3 (correct response with serious difficulty)
    - >= 40% -> 2 (incorrect response; where the correct one seemed easy to recall)
    - >= 20% -> 1 (incorrect response; the correct one remembered)
    - Else   -> 0 (complete blackout)
    """
    if accuracy >= 90.0:
        return 5
    elif accuracy >= 75.0:
        return 4
    elif accuracy >= 60.0:
        return 3
    elif accuracy >= 40.0:
        return 2
    elif accuracy >= 20.0:
        return 1
    else:
        return 0


def calculate_sm2(
    accuracy: float,
    previous_interval: int = 1,
    ease_factor: float = 2.5,
    repetitions: int = 0,
    today: date | None = None,
) -> Tuple[int, float, int, date]:
    """
    Runs the SM-2 algorithm update.

    Parameters
    ----------
    accuracy          : Session accuracy (0-100).
    previous_interval : Interval of previous repetition in days.
    ease_factor       : Ease factor float (defaults to 2.5).
    repetitions       : Number of consecutive successful repetitions.
    today             : Override for current date; defaults to date.today().

    Returns
    -------
    Tuple[new_interval_days, new_ease_factor, new_repetitions, next_review_date]
    """
    if today is None:
        today = date.today()

    quality = resolve_quality_rating(accuracy)

    if quality < 3:
        # Failure: reset repetition count and set interval to 1 day
        interval = 1
        new_repetitions = 0
        # Ease factor remains unchanged under standard failure
    else:
        # Success: update ease factor and repetitions
        new_repetitions = repetitions + 1

        # Update Ease Factor according to formula:
        # EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        ease_factor = ease_factor + (0.1 - (5.0 - quality) * (0.08 + (5.0 - quality) * 0.02))
        ease_factor = max(1.3, ease_factor)

        # Update Interval:
        # - 1st successful rep: 1 day
        # - 2nd successful rep: 6 days
        # - 3rd+ successful rep: interval = previous_interval * EF
        if new_repetitions == 1:
            interval = 1
        elif new_repetitions == 2:
            interval = 6
        else:
            interval = round(previous_interval * ease_factor)

    # Safety bounds on interval
    interval = max(1, interval)
    next_review_date = today + timedelta(days=interval)

    return interval, ease_factor, new_repetitions, next_review_date
