"""Scrapers package — exports all scraper classes."""

from manipal_loop.scrapers.google_news import GoogleNewsScraper
from manipal_loop.scrapers.mahe_notices import MAHENoticesScraper
from manipal_loop.scrapers.power_cuts import PowerCutsScraper
from manipal_loop.scrapers.reddit import RedditScraper
from manipal_loop.scrapers.twitter import TwitterScraper
from manipal_loop.scrapers.weather import WeatherScraper

__all__ = [
    "GoogleNewsScraper",
    "MAHENoticesScraper",
    "PowerCutsScraper",
    "RedditScraper",
    "TwitterScraper",
    "WeatherScraper",
]
