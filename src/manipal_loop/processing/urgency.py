"""Urgency scorer for content items (1 = low, 5 = critical)."""

import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)

# (score, [keywords]) — evaluated in descending score order
_RULES: List[Tuple[int, List[str]]] = [
    (
        5,
        [
            "emergency", "fire", "explosion", "earthquake",
            "evacuation", "power cut now", "immediate", "urgent",
        ],
    ),
    (
        4,
        [
            "weather warning", "heavy rain", "flood", "cyclone",
            "traffic accident", "road block", "thunderstorm",
        ],
    ),
    (
        3,
        [
            "scheduled power cut", "power shutdown", "exam schedule",
            "result released", "notice", "circular",
        ],
    ),
    (
        2,
        [
            "event", "fest", "hackathon", "workshop", "seminar",
            "campus chatter", "reddit",
        ],
    ),
]

# Category-based baseline scores
_CATEGORY_SCORES = {
    "Emergency": 5,
    "Power Cut": 4,
    "Weather": 4,
    "Traffic": 3,
    "Academic": 3,
    "Official Alert": 3,
    "Events": 2,
    "Campus Chatter": 2,
    "City News": 2,
    "Food": 1,
    "General": 1,
}


def score_urgency(title: str, body: str, category: str) -> int:
    """Compute an urgency score from 1 (low) to 5 (critical).

    Keyword rules take precedence over the category baseline.

    Args:
        title: Headline text.
        body: Body / summary text.
        category: Pre-classified category string.

    Returns:
        Integer urgency score in the range [1, 5].
    """
    combined = f"{title} {body}".lower()

    for score, keywords in _RULES:
        if any(kw in combined for kw in keywords):
            logger.debug("Urgency %d from keyword match", score)
            return score

    baseline = _CATEGORY_SCORES.get(category, 1)
    logger.debug("Urgency %d from category '%s'", baseline, category)
    return baseline
