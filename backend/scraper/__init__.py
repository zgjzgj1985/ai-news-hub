"""Scraper package."""

from scraper.rss_parser import fetch_all_feeds, _fetch_feed_with_timeout
from scraper.classifier import classify

__all__ = ["fetch_all_feeds", "_fetch_feed_with_timeout", "classify"]
