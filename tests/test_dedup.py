"""Tests for content deduplication utilities."""

from unittest.mock import MagicMock

from manipal_loop.processing.dedup import generate_content_hash, is_duplicate


class TestGenerateContentHash:
    """Tests for generate_content_hash."""

    def test_returns_64_char_hex_string(self):
        """Hash must be a 64-character lowercase hex string (SHA-256)."""
        result = generate_content_hash("Test title", "Test source", "2024-01-01")
        assert isinstance(result, str)
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

    def test_same_inputs_same_hash(self):
        """Identical inputs must always produce the same hash."""
        h1 = generate_content_hash("Title", "Source", "2024-01-01")
        h2 = generate_content_hash("Title", "Source", "2024-01-01")
        assert h1 == h2

    def test_different_titles_different_hashes(self):
        """Different titles must yield different hashes."""
        h1 = generate_content_hash("Title A", "Source", "2024-01-01")
        h2 = generate_content_hash("Title B", "Source", "2024-01-01")
        assert h1 != h2

    def test_different_sources_different_hashes(self):
        """Different sources must yield different hashes."""
        h1 = generate_content_hash("Title", "Source A", "2024-01-01")
        h2 = generate_content_hash("Title", "Source B", "2024-01-01")
        assert h1 != h2

    def test_different_dates_different_hashes(self):
        """Different dates must yield different hashes."""
        h1 = generate_content_hash("Title", "Source", "2024-01-01")
        h2 = generate_content_hash("Title", "Source", "2024-01-02")
        assert h1 != h2

    def test_empty_strings(self):
        """Empty-string inputs should still produce a valid 64-char hash."""
        result = generate_content_hash("", "", "")
        assert len(result) == 64


class TestIsDuplicate:
    """Tests for is_duplicate."""

    def test_returns_false_for_new_hash(self):
        """is_duplicate should return False when the hash is not in the DB."""
        mock_db = MagicMock()
        mock_db.update_exists.return_value = False

        assert is_duplicate("some_hash_that_is_new", mock_db) is False
        mock_db.update_exists.assert_called_once_with("some_hash_that_is_new")

    def test_returns_true_for_existing_hash(self):
        """is_duplicate should return True when the hash is already in the DB."""
        mock_db = MagicMock()
        mock_db.update_exists.return_value = True

        assert is_duplicate("existing_hash", mock_db) is True

    def test_returns_false_on_db_exception(self):
        """is_duplicate should return False (safe default) if DB raises."""
        mock_db = MagicMock()
        mock_db.update_exists.side_effect = Exception("DB error")

        assert is_duplicate("any_hash", mock_db) is False
