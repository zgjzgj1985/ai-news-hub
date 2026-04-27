"""Scraper package."""

from scraper.rss_parser import fetch_all_feeds, fetch_feed
from scraper.classifier import classify

__all__ = ["fetch_all_feeds", "fetch_feed", "classify"]
