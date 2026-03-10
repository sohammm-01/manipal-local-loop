"""Tests for the urgency scoring module."""

from manipal_loop.processing.urgency import score_urgency


class TestScoreUrgency:
    """Tests for the score_urgency function."""

    def test_emergency_fire_keywords_score_5(self):
        """Emergency + fire keywords → score 5."""
        score = score_urgency("Fire emergency at hostel", "Evacuation underway", "Emergency")
        assert score == 5

    def test_emergency_category_baseline_is_5(self):
        """'Emergency' category alone should yield baseline 5."""
        score = score_urgency("Campus update", "Something happened", "Emergency")
        assert score == 5

    def test_weather_warning_score_4(self):
        """Weather warning keyword → score 4."""
        score = score_urgency("Weather warning for heavy rain", "", "Weather")
        assert score == 4

    def test_traffic_accident_score_4(self):
        """Traffic accident keyword → score 4."""
        score = score_urgency("Traffic accident on NH66", "", "Traffic")
        assert score == 4

    def test_scheduled_power_cut_score_3(self):
        """Scheduled power cut keyword → score 3."""
        score = score_urgency("Scheduled power cut tomorrow", "", "Power Cut")
        assert score == 3

    def test_exam_notice_score_3(self):
        """Exam schedule keyword → score 3 (category baseline)."""
        score = score_urgency("Exam schedule released", "", "Academic")
        assert score == 3

    def test_events_category_score_2(self):
        """Events category with no high-urgency keywords → score 2."""
        score = score_urgency("Hackathon this weekend", "", "Events")
        assert score == 2

    def test_campus_chatter_category_score_2(self):
        """Campus Chatter category baseline → score 2."""
        score = score_urgency("Random post about food", "", "Campus Chatter")
        assert score == 2

    def test_food_category_score_1(self):
        """Food category baseline → score 1."""
        score = score_urgency("New cafe opened", "", "Food")
        assert score == 1

    def test_general_category_score_1(self):
        """General category baseline → score 1."""
        score = score_urgency("General news update", "", "General")
        assert score == 1

    def test_score_range(self):
        """Score should always be in [1, 5]."""
        test_cases = [
            ("Random text", "", "General"),
            ("Emergency fire", "evacuate now", "Emergency"),
            ("Exam results", "", "Academic"),
        ]
        for title, body, cat in test_cases:
            score = score_urgency(title, body, cat)
            assert 1 <= score <= 5, f"Score {score} out of range for '{title}'"
