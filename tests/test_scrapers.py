"""
Tests for scraper services.
"""

import pytest
from unittest.mock import MagicMock, patch


class TestRedditScraper:
    """Tests for Reddit scraper."""

    @patch("src.scrapers.reddit_scraper.praw.Reddit")
    def test_init(self, mock_reddit):
        """Test Reddit scraper initialization."""
        from src.scrapers.reddit_scraper import RedditScraper

        with patch.dict(
            "os.environ",
            {
                "REDDIT_CLIENT_ID": "test",
                "REDDIT_CLIENT_SECRET": "test",
                "REDDIT_USERNAME": "test",
                "REDDIT_PASSWORD": "test",
            },
        ):
            scraper = RedditScraper()
            assert scraper.reddit is not None


class TestTwitterScraper:
    """Tests for Twitter scraper."""

    @patch("src.scrapers.twitter_scraper.tweepy.Client")
    def test_init(self, mock_client):
        """Test Twitter scraper initialization."""
        from src.scrapers.twitter_scraper import TwitterScraper

        with patch.dict(
            "os.environ",
            {
                "TWITTER_BEARER_TOKEN": "test",
                "TWITTER_API_KEY": "test",
                "TWITTER_API_SECRET": "test",
                "TWITTER_ACCESS_TOKEN": "test",
                "TWITTER_ACCESS_SECRET": "test",
            },
        ):
            scraper = TwitterScraper()
            assert scraper.client is not None
