"""
SQLAlchemy models for Apex Lead Gen.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Lead(Base):
    """Lead model representing a potential customer."""

    __tablename__ = "leads"

    id = Column(Integer, primary_key=True)
    platform = Column(String(20), nullable=False)
    post_id = Column(String(100), nullable=False, unique=True)
    author = Column(String(100), nullable=False)
    title = Column(String(500))
    content = Column(Text, nullable=False)
    url = Column(Text, nullable=False)
    subreddit = Column(String(100))

    engagement_score = Column(Integer, default=0)
    relevance_score = Column(Float, default=0)
    total_score = Column(Float, default=0)

    status = Column(String(20), default="new")
    drafted_message = Column(Text)

    matched_keyword = Column(String(100))

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_platform_status", "platform", "status"),
        Index("idx_total_score", "total_score"),
        Index("idx_created_at", "created_at"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "platform": self.platform,
            "post_id": self.post_id,
            "author": self.author,
            "title": self.title,
            "content": self.content,
            "url": self.url,
            "subreddit": self.subreddit,
            "engagement_score": self.engagement_score,
            "relevance_score": self.relevance_score,
            "total_score": self.total_score,
            "status": self.status,
            "drafted_message": self.drafted_message,
            "matched_keyword": self.matched_keyword,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ScrapeLog(Base):
    """Log of scrape operations."""

    __tablename__ = "scrape_logs"

    id = Column(Integer, primary_key=True)
    platform = Column(String(20), nullable=False)
    posts_found = Column(Integer, default=0)
    new_leads = Column(Integer, default=0)
    errors = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "platform": self.platform,
            "posts_found": self.posts_found,
            "new_leads": self.new_leads,
            "errors": self.errors,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
