"""Tests for the rule-based keyword classifier."""

from manipal_loop.processing.classifier import classify


class TestClassify:
    """Tests for the classify function."""

    def test_power_cut_classification(self):
        """MESCOM power cut keywords → 'Power Cut'."""
        assert classify("MESCOM power cut tonight", "") == "Power Cut"

    def test_traffic_classification(self):
        """NH66 traffic jam keywords → 'Traffic'."""
        assert classify("Traffic jam on NH66", "") == "Traffic"

    def test_weather_classification(self):
        """Heavy rain warning → 'Weather'."""
        assert classify("Heavy rain warning issued", "") == "Weather"

    def test_academic_classification(self):
        """Exam schedule → 'Academic'."""
        assert classify("Exam schedule released by university", "") == "Academic"

    def test_events_classification(self):
        """Hackathon keyword → 'Events'."""
        assert classify("Hackathon this weekend at MIT Manipal", "") == "Events"

    def test_emergency_classification(self):
        """Fire emergency → 'Emergency'."""
        assert classify("Fire emergency evacuation at hostel", "") == "Emergency"

    def test_food_classification(self):
        """New restaurant → 'Food'."""
        assert classify("New restaurant opening in Manipal", "") == "Food"

    def test_general_classification(self):
        """Unmatched keywords → 'General'."""
        assert classify("General update about something", "") == "General"

    def test_body_text_contributes_to_classification(self):
        """Classification should consider body text even when title is vague."""
        assert classify("Update", "There is a power cut in the area") == "Power Cut"

    def test_emergency_wins_over_events(self):
        """Emergency should win when both emergency and event keywords appear."""
        result = classify("Event cancelled due to fire emergency", "")
        assert result == "Emergency"

    def test_case_insensitive(self):
        """Matching should be case-insensitive."""
        assert classify("POWER CUT TONIGHT", "") == "Power Cut"
        assert classify("HEAVY RAIN WARNING", "") == "Weather"
