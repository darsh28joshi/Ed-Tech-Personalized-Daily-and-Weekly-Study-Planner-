"""
EMA Mastery Blending — Pure Logic (no DB/network calls)

Blends the latest quiz score with the old chapter mastery using an
Exponential Moving Average (EMA) formula.
Formula:
    new_mastery = alpha * latest_session_score + (1 - alpha) * old_mastery
Default alpha = 0.45.
"""


def compute_ema_mastery(
    latest_score: float,
    old_mastery: float | None = None,
    alpha: float = 0.45,
) -> float:
    """
    Computes the new blended mastery score.
    If there is no prior score (old_mastery is None), the new score
    becomes the mastery directly.
    """
    if old_mastery is None:
        return float(latest_score)

    new_mastery = (alpha * latest_score) + ((1.0 - alpha) * old_mastery)
    # Clamp score between 0.0 and 100.0
    return max(0.0, min(new_mastery, 100.0))
