"""
Twitter Scraper using Tweepy.
Monitors Twitter/X for tweets containing target keywords.
"""

import logging
import os
from datetime import datetime, timedelta
from typing import List, Dict

import tweepy

logger = logging.getLogger("apex.twitter")


class TwitterScraper:
    """Scrapes Twitter for tweets matching target keywords."""

    def __init__(self):
        self.client = self._init_twitter()

    def _init_twitter(self) -> tweepy.Client:
        """Initialize Twitter client with credentials."""
        client = tweepy.Client(
            bearer_token=os.getenv("TWITTER_BEARER_TOKEN"),
            consumer_key=os.getenv("TWITTER_API_KEY"),
            consumer_secret=os.getenv("TWITTER_API_SECRET"),
            access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
            access_token_secret=os.getenv("TWITTER_ACCESS_SECRET"),
            wait_on_rate_limit=True,
        )
        logger.info("Twitter client initialized")
        return client

    def scrape(self, keywords: List[str]) -> List[Dict]:
        """
        Scrape Twitter for tweets containing any of the keywords.

        Args:
            keywords: List of keywords to search for

        Returns:
            List of tweet dictionaries with relevant data
        """
        tweets = []

        for keyword in keywords:
            try:
                response = self.client.search_recent_tweets(
                    query=keyword,
                    max_results=50,
                    tweet_fields=["created_at", "public_metrics", "author_id", "text"],
                    expansions=["author_id"],
                    user_fields=["username", "public_metrics"],
                )

                if not response.data:
                    continue

                users = {u.id: u for u in (response.includes.get("users") or [])}

                for tweet in response.data:
                    user = users.get(tweet.author_id)
                    if not user:
                        continue

                    public_metrics = tweet.public_metrics or {}
                    engagement = (
                        public_metrics.get("retweet_count", 0)
                        + public_metrics.get("like_count", 0)
                        + public_metrics.get("reply_count", 0)
                    )

                    tweets.append(
                        {
                            "id": str(tweet.id),
                            "post_id": str(tweet.id),
                            "author": f"@{user.username}"
                            if user.username
                            else "[unknown]",
                            "content": tweet.text[:2000],
                            "url": f"https://twitter.com/i/web/status/{tweet.id}",
                            "followers_count": user.public_metrics.get(
                                "followers_count", 0
                            )
                            if user.public_metrics
                            else 0,
                            "retweets": public_metrics.get("retweet_count", 0),
                            "likes": public_metrics.get("like_count", 0),
                            "replies": public_metrics.get("reply_count", 0),
                            "engagement": engagement,
                            "created_at": tweet.created_at.isoformat()
                            if tweet.created_at
                            else None,
                            "matched_keyword": keyword,
                            "platform": "twitter",
                        }
                    )

            except tweepy.TooManyRequests:
                logger.warning("Rate limit reached, waiting...")
                continue
            except Exception as e:
                logger.error(f"Error searching Twitter for '{keyword}': {e}")

        logger.info(f"Scraped {len(tweets)} tweets from Twitter")
        return tweets

    def get_user_tweets(self, username: str, max_results: int = 10) -> List[Dict]:
        """Get recent tweets from a specific user."""
        try:
            user = self.client.get_user(username=username.replace("@", ""))
            if not user.data:
                return []

            tweets = self.client.get_users_tweets(
                id=user.data.id,
                max_results=max_results,
                tweet_fields=["created_at", "public_metrics"],
            )

            result = []
            for tweet in tweets.data or []:
                metrics = tweet.public_metrics or {}
                result.append(
                    {
                        "id": str(tweet.id),
                        "content": tweet.text,
                        "created_at": tweet.created_at,
                        "engagement": metrics.get("retweet_count", 0)
                        + metrics.get("like_count", 0),
                    }
                )

            return result
        except Exception as e:
            logger.error(f"Error getting user tweets: {e}")
            return []
