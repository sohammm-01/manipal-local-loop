"""Rule-based keyword classifier for local news categories."""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

# Category → list of keyword triggers (all lowercase)
_CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "Power Cut": [
        "power cut", "power outage", "electricity cut", "load shedding",
        "mescom", "shutdown", "no electricity", "power interruption",
    ],
    "Traffic": [
        "traffic", "road block", "accident", "jam", "nh66", "highway",
        "road closure", "diversion", "flyover", "signal", "congestion",
    ],
    "Weather": [
        "rain", "flood", "storm", "cyclone", "thunder", "lightning",
        "heat wave", "warning", "weather", "monsoon", "drought",
    ],
    "Academic": [
        "exam", "result", "schedule", "college", "university",
        "mahe", "manipal university", "semester", "admission", "grade",
    ],
    "Events": [
        "event", "fest", "hackathon", "workshop", "seminar", "concert",
        "exhibition", "competition", "tournament", "fest", "celebration",
    ],
    "Emergency": [
        "emergency", "fire", "explosion", "earthquake", "evacuation",
        "accident", "ambulance", "police", "rescue", "disaster",
    ],
    "Food": [
        "restaurant", "cafe", "food", "dining", "canteen",
        "menu", "cuisine", "delivery", "zomato", "swiggy",
    ],
}

_DEFAULT_CATEGORY = "General"


def classify(title: str, body: str) -> str:
    """Classify content into a category using keyword matching.

    Categories are checked in priority order so that 'Emergency' wins
    over 'Events', etc.

    Args:
        title: Headline text.
        body: Body / summary text.

    Returns:
        One of the defined category strings, or 'General'.
    """
    combined = f"{title} {body}".lower()

    priority_order = [
        "Emergency",
        "Power Cut",
        "Weather",
        "Traffic",
        "Academic",
        "Events",
        "Food",
    ]

    for category in priority_order:
        keywords = _CATEGORY_KEYWORDS.get(category, [])
        if any(kw in combined for kw in keywords):
            logger.debug("Classified as '%s'", category)
            return category

    return _DEFAULT_CATEGORY
