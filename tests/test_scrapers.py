"""Tests for scraper classes using mocked HTTP responses."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

REQUIRED_FIELDS = {
    "content_hash",
    "timestamp",
    "title",
    "body_text",
    "source",
    "category",
    "url",
    "raw_language",
}

# ---------------------------------------------------------------------------
# GoogleNewsScraper
# ---------------------------------------------------------------------------

_GOOGLE_NEWS_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Google News</title>
    <item>
      <title>Manipal hosts tech fest - Deccan Herald</title>
      <link>https://example.com/story1</link>
      <pubDate>Mon, 01 Jan 2024 08:00:00 GMT</pubDate>
      <description>Manipal University hosted its annual tech fest.</description>
    </item>
    <item>
      <title>Udupi traffic update - Times of India</title>
      <link>https://example.com/story2</link>
      <pubDate>Mon, 01 Jan 2024 09:00:00 GMT</pubDate>
      <description>NH66 traffic jam near Udupi.</description>
    </item>
  </channel>
</rss>"""


class TestGoogleNewsScraper:
    """Unit tests for GoogleNewsScraper."""

    @staticmethod
    def _parsed_rss():
        """Parse the fixture RSS string BEFORE mocking feedparser."""
        import feedparser
        return feedparser.parse(_GOOGLE_NEWS_RSS)

    def test_fetch_returns_items_with_correct_schema(self):
        """fetch() should return items containing all required schema fields."""
        # Parse RSS outside the mock context so the real parser is used
        parsed = self._parsed_rss()

        with patch("feedparser.parse", return_value=parsed):
            from manipal_loop.scrapers.google_news import GoogleNewsScraper

            scraper = GoogleNewsScraper()
            items = scraper.fetch()

        assert len(items) >= 1
        for item in items:
            assert REQUIRED_FIELDS.issubset(set(item.keys())), (
                f"Missing fields: {REQUIRED_FIELDS - set(item.keys())}"
            )

    def test_fetch_extracts_source_from_title(self):
        """Source should be the last segment after ' - ' in the title."""
        parsed = self._parsed_rss()

        with patch("feedparser.parse", return_value=parsed):
            from manipal_loop.scrapers.google_news import GoogleNewsScraper

            scraper = GoogleNewsScraper()
            items = scraper.fetch()

        sources = {item["source"] for item in items}
        assert "Deccan Herald" in sources or "Times of India" in sources

    def test_fetch_category_is_city_news(self):
        """All items should have category 'City News'."""
        parsed = self._parsed_rss()

        with patch("feedparser.parse", return_value=parsed):
            from manipal_loop.scrapers.google_news import GoogleNewsScraper

            scraper = GoogleNewsScraper()
            items = scraper.fetch()

        for item in items:
            assert item["category"] == "City News"

    def test_fetch_handles_feedparser_exception(self):
        """fetch() should return empty list when feedparser raises."""
        with patch("feedparser.parse", side_effect=Exception("network error")):
            from manipal_loop.scrapers.google_news import GoogleNewsScraper

            scraper = GoogleNewsScraper()
            items = scraper.fetch()

        assert items == []


# ---------------------------------------------------------------------------
# RedditScraper
# ---------------------------------------------------------------------------

def _make_reddit_response(posts):
    return {"data": {"children": posts}}


def _make_post(title, selftext="", stickied=False, permalink="/r/manipal/abc"):
    return {
        "data": {
            "title": title,
            "selftext": selftext,
            "stickied": stickied,
            "permalink": permalink,
            "created_utc": datetime.now(timezone.utc).timestamp(),
            "thumbnail": "",
            "subreddit": "manipal",
        }
    }


class TestRedditScraper:
    """Unit tests for RedditScraper."""

    def test_fetch_returns_items_with_correct_schema(self):
        """fetch() should return items with all required schema fields."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = _make_reddit_response(
            [_make_post("Hostel update in Manipal"), _make_post("Food review MCC")]
        )

        from manipal_loop.scrapers.reddit import RedditScraper

        scraper = RedditScraper()
        with patch.object(scraper, "_make_request", return_value=mock_response):
            items = scraper.fetch()

        assert len(items) == 2
        for item in items:
            assert REQUIRED_FIELDS.issubset(set(item.keys()))

    def test_fetch_skips_stickied_posts(self):
        """fetch() must not include stickied posts."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = _make_reddit_response(
            [
                _make_post("Regular post"),
                _make_post("Stickied mod post", stickied=True),
                _make_post("Another regular"),
            ]
        )

        from manipal_loop.scrapers.reddit import RedditScraper

        scraper = RedditScraper()
        with patch.object(scraper, "_make_request", return_value=mock_response):
            items = scraper.fetch()

        titles = [i["title"] for i in items]
        assert "Stickied mod post" not in titles
        assert len(items) == 2

    def test_fetch_returns_empty_on_429(self):
        """fetch() should return empty list on rate-limit response."""
        mock_response = MagicMock()
        mock_response.status_code = 429

        from manipal_loop.scrapers.reddit import RedditScraper

        scraper = RedditScraper()
        with patch.object(scraper, "_make_request", return_value=mock_response):
            items = scraper.fetch()

        assert items == []

    def test_fetch_returns_empty_on_request_failure(self):
        """fetch() should return empty list when _make_request returns None."""
        from manipal_loop.scrapers.reddit import RedditScraper

        scraper = RedditScraper()
        with patch.object(scraper, "_make_request", return_value=None):
            items = scraper.fetch()

        assert items == []

    def test_fetch_category_is_campus_chatter(self):
        """All Reddit items should have category 'Campus Chatter'."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = _make_reddit_response(
            [_make_post("Random campus post")]
        )

        from manipal_loop.scrapers.reddit import RedditScraper

        scraper = RedditScraper()
        with patch.object(scraper, "_make_request", return_value=mock_response):
            items = scraper.fetch()

        for item in items:
            assert item["category"] == "Campus Chatter"
