"""
Lead Scoring Service.
Scores and ranks leads based on engagement, relevance, and recency.
"""

import logging
from datetime import datetime
from typing import Dict

logger = logging.getLogger("apex.scorer")


class LeadScorer:
    """Scores leads based on multiple factors."""

    def __init__(self, config: Dict):
        self.config = config
        self.relevance_weight = config.get("scoring", {}).get("relevance_weight", 0.7)
        self.recent_weight = config.get("scoring", {}).get("recent_weight", 0.3)
        self.engagement_threshold = config.get("scoring", {}).get(
            "engagement_threshold", 5
        )

        self.keywords = config.get("monitoring", {}).get("keywords", [])

    def score_lead(self, post: Dict) -> float:
        """
        Calculate overall score for a lead.

        Args:
            post: Post data dictionary

        Returns:
            Composite score (0-100)
        """
        engagement_score = self._score_engagement(post)
        relevance_score = self._score_relevance(post)
        recency_score = self._score_recency(post)

        total_score = (
            engagement_score * 0.4
            + relevance_score * self.relevance_weight * 10
            + recency_score * self.recent_weight * 10
        )

        logger.debug(
            f"Lead {post.get('author', 'unknown')}: "
            f"eng={engagement_score:.2f}, rel={relevance_score:.2f}, "
            f"rec={recency_score:.2f}, total={total_score:.2f}"
        )

        return total_score

    def _score_engagement(self, post: Dict) -> float:
        """Score based on engagement metrics."""
        engagement = post.get("engagement", 0)

        if post.get("platform") == "reddit":
            return min(engagement / 100, 1.0) * 40
        else:
            return min(engagement / 50, 1.0) * 40

    def _score_relevance(self, post: Dict) -> float:
        """Score based on keyword match relevance."""
        content = f"{post.get('title', '')} {post.get('content', '')}".lower()
        matched_keyword = post.get("matched_keyword", "").lower()

        score = 0.0

        for keyword in self.keywords:
            if keyword.lower() in content:
                score += 2.0
                if keyword.lower() == matched_keyword.lower():
                    score += 3.0

        content_length = len(content)
        if content_length > 100:
            score += 2.0
        if content_length > 500:
            score += 1.0

        return min(score, 10.0)

    def _score_recency(self, post: Dict) -> float:
        """Score based on how recent the post is."""
        created_utc = post.get("created_utc")

        if not created_utc:
            return 5.0

        if isinstance(created_utc, str):
            try:
                created_utc = float(created_utc)
            except (ValueError, TypeError):
                return 5.0

        now = datetime.now().timestamp()
        age_hours = (now - created_utc) / 3600

        if age_hours < 1:
            return 10.0
        elif age_hours < 6:
            return 8.0
        elif age_hours < 24:
            return 6.0
        elif age_hours < 72:
            return 4.0
        else:
            return 2.0

    def is_qualified(self, score: float) -> bool:
        """Check if a score meets the qualification threshold."""
        return score >= self.engagement_threshold
