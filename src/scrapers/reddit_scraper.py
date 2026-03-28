"""
Reddit Scraper using PRAW.
Monitors Reddit for target keywords in posts and comments.
"""

import logging
import os
from datetime import datetime, timedelta
from typing import List, Dict

import praw

logger = logging.getLogger("apex.reddit")


class RedditScraper:
    """Scrapes Reddit for posts matching target keywords."""

    def __init__(self):
        self.reddit = self._init_reddit()

    def _init_reddit(self) -> praw.Reddit:
        """Initialize Reddit client with credentials."""
        reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            username=os.getenv("REDDIT_USERNAME"),
            password=os.getenv("REDDIT_PASSWORD"),
            user_agent=os.getenv("REDDIT_USER_AGENT", "ApexLeadGen/1.0"),
        )
        logger.info("Reddit client initialized")
        return reddit

    def scrape(self, keywords: List[str]) -> List[Dict]:
        """
        Scrape Reddit for posts containing any of the keywords.

        Args:
            keywords: List of keywords to search for

        Returns:
            List of post dictionaries with relevant data
        """
        posts = []
        seen_ids = set()

        subreddits = [
            "adhd",
            "productivity",
            "getdisciplined",
            " Forbes ",
            "selfimprovement",
        ]

        for keyword in keywords:
            for subreddit_name in subreddits:
                try:
                    subreddit = self.reddit.subreddit(subreddit_name.replace(" ", ""))

                    for submission in subreddit.search(
                        keyword, limit=20, time_filter="week"
                    ):
                        if submission.id in seen_ids:
                            continue

                        seen_ids.add(submission.id)

                        post_data = self._extract_post_data(submission, keyword)
                        if post_data:
                            posts.append(post_data)

                except Exception as e:
                    logger.error(
                        f"Error searching r/{subreddit_name} for '{keyword}': {e}"
                    )

        logger.info(f"Scraped {len(posts)} unique posts from Reddit")
        return posts

    def _extract_post_data(self, submission, matched_keyword: str) -> Dict:
        """Extract relevant data from a Reddit submission."""
        try:
            engagement = submission.score + submission.num_comments

            return {
                "id": submission.id,
                "post_id": submission.id,
                "author": str(submission.author) if submission.author else "[deleted]",
                "title": submission.title,
                "content": submission.selftext[:2000]
                if submission.selftext
                else submission.title,
                "url": f"https://reddit.com{submission.permalink}",
                "subreddit": submission.subreddit.display_name,
                "score": submission.score,
                "num_comments": submission.num_comments,
                "engagement": engagement,
                "created_utc": submission.created_utc,
                "matched_keyword": matched_keyword,
                "platform": "reddit",
            }
        except Exception as e:
            logger.error(f"Error extracting post data: {e}")
            return None

    def get_post_comments(self, post_id: str) -> List[Dict]:
        """Get comments from a specific post."""
        try:
            submission = self.reddit.submission(id=post_id)
            submission.comments.replace_more(limit=3)

            comments = []
            for comment in submission.comments[:10]:
                comments.append(
                    {
                        "id": comment.id,
                        "author": str(comment.author)
                        if comment.author
                        else "[deleted]",
                        "body": comment.body[:1000],
                        "score": comment.score,
                    }
                )

            return comments
        except Exception as e:
            logger.error(f"Error getting comments: {e}")
            return []
