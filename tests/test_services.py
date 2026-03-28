"""
Tests for lead scoring service.
"""

import pytest
from src.services.lead_scorer import LeadScorer


@pytest.fixture
def config():
    return {
        "monitoring": {
            "keywords": ["ADHD tax", "productivity help", "routine manager"],
            "platforms": ["reddit", "twitter"],
            "interval_minutes": 15,
        },
        "scoring": {
            "engagement_threshold": 5,
            "relevance_weight": 0.7,
            "recent_weight": 0.3,
        },
        "outreach": {
            "auto_draft": True,
            "draft_style": "professional but friendly",
            "max_draft_length": 280,
        },
    }


@pytest.fixture
def scorer(config):
    return LeadScorer(config)


def test_score_engagement_reddit(scorer):
    """Test engagement scoring for Reddit posts."""
    post = {"platform": "reddit", "engagement": 100}
    score = scorer._score_engagement(post)
    assert 0 <= score <= 40


def test_score_engagement_twitter(scorer):
    """Test engagement scoring for Twitter posts."""
    post = {"platform": "twitter", "engagement": 50}
    score = scorer._score_engagement(post)
    assert 0 <= score <= 40


def test_score_relevance(scorer):
    """Test relevance scoring based on keyword match."""
    post = {
        "title": "Struggling with ADHD tax and productivity",
        "content": "My ADHD tax is killing my productivity.",
        "matched_keyword": "ADHD tax",
    }
    score = scorer._score_relevance(post)
    assert score > 0


def test_score_recency_recent(scorer):
    """Test recency scoring for recent posts."""
    import time

    post = {
        "created_utc": time.time() - 1800  # 30 minutes ago
    }
    score = scorer._score_recency(post)
    assert score >= 8


def test_score_recency_old(scorer):
    """Test recency scoring for old posts."""
    import time

    post = {
        "created_utc": time.time() - 604800  # 1 week ago
    }
    score = scorer._score_recency(post)
    assert score < 5


def test_full_lead_score(scorer):
    """Test full lead scoring."""
    import time

    post = {
        "platform": "reddit",
        "author": "test_user",
        "title": "Managing ADHD tax and productivity",
        "content": "Looking for help with routine management.",
        "engagement": 100,
        "matched_keyword": "ADHD tax",
        "created_utc": time.time() - 3600,
    }
    score = scorer.score_lead(post)
    assert score >= 0
    assert score <= 100


def test_is_qualified(scorer):
    """Test qualification threshold."""
    assert scorer.is_qualified(10) is True
    assert scorer.is_qualified(5) is True
    assert scorer.is_qualified(4) is False
