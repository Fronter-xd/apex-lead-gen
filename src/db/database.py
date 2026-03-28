"""
PostgreSQL Database handler for Apex Lead Gen.
"""

import logging
import os
from typing import Dict, List, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool

from .models import Base, Lead, ScrapeLog

logger = logging.getLogger("apex.db")


class Database:
    """Database handler for lead storage and retrieval."""

    def __init__(self, database_url: str = None):
        if database_url is None:
            database_url = os.getenv(
                "DATABASE_URL",
                "postgresql://apex:apex_secret@localhost:5432/apex_leads",
            )

        self.engine = create_engine(database_url, poolclass=NullPool, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
        logger.info(
            f"Database connected: {database_url.split('@')[1] if '@' in database_url else 'localhost'}"
        )

    def init_db(self):
        """Initialize database tables."""
        Base.metadata.create_all(self.engine)
        logger.info("Database tables created")

    def _get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()

    def save_lead(
        self, platform: str, post: Dict, status: str = "new"
    ) -> Optional[int]:
        """Save a new lead to the database."""
        session = self._get_session()
        try:
            lead = Lead(
                platform=platform,
                post_id=post.get("id", post.get("post_id")),
                author=post.get("author", "unknown"),
                title=post.get("title", ""),
                content=post.get("content", ""),
                url=post.get("url", ""),
                subreddit=post.get("subreddit", ""),
                engagement_score=post.get("engagement", 0),
                relevance_score=post.get("relevance_score", 0),
                total_score=post.get("total_score", 0),
                status=status,
                drafted_message=post.get("drafted_message"),
                matched_keyword=post.get("matched_keyword", ""),
            )
            session.add(lead)
            session.commit()
            session.refresh(lead)
            logger.debug(f"Lead saved: {lead.id}")
            return lead.id
        except Exception as e:
            session.rollback()
            if "unique constraint" in str(e).lower() or "duplicate" in str(e).lower():
                logger.debug(f"Duplicate lead: {post.get('id')}")
                return None
            logger.error(f"Error saving lead: {e}")
            return None
        finally:
            session.close()

    def is_duplicate(self, platform: str, post_id: str) -> bool:
        """Check if a post has already been saved."""
        session = self._get_session()
        try:
            lead = (
                session.query(Lead)
                .filter(Lead.platform == platform, Lead.post_id == post_id)
                .first()
            )
            return lead is not None
        finally:
            session.close()

    def get_lead(self, lead_id: int) -> Optional[Dict]:
        """Get a specific lead by ID."""
        session = self._get_session()
        try:
            lead = session.query(Lead).filter(Lead.id == lead_id).first()
            return lead.to_dict() if lead else None
        finally:
            session.close()

    def get_recent_leads(self, limit: int = 20, status: str = None) -> List[Dict]:
        """Get recent leads, optionally filtered by status."""
        session = self._get_session()
        try:
            query = session.query(Lead).order_by(Lead.created_at.desc())
            if status:
                query = query.filter(Lead.status == status)
            leads = query.limit(limit).all()
            return [lead.to_dict() for lead in leads]
        finally:
            session.close()

    def update_lead_status(self, lead_id: int, status: str) -> bool:
        """Update the status of a lead."""
        session = self._get_session()
        try:
            lead = session.query(Lead).filter(Lead.id == lead_id).first()
            if lead:
                lead.status = status
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating lead status: {e}")
            return False
        finally:
            session.close()

    def update_draft(self, lead_id: int, draft: str) -> bool:
        """Update the drafted message for a lead."""
        session = self._get_session()
        try:
            lead = session.query(Lead).filter(Lead.id == lead_id).first()
            if lead:
                lead.drafted_message = draft
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating draft: {e}")
            return False
        finally:
            session.close()

    def log_scrape(
        self, platform: str, posts_found: int, new_leads: int, errors: str = None
    ):
        """Log a scrape operation."""
        session = self._get_session()
        try:
            log = ScrapeLog(
                platform=platform,
                posts_found=posts_found,
                new_leads=new_leads,
                errors=errors,
            )
            session.add(log)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error logging scrape: {e}")
        finally:
            session.close()

    def get_stats(self) -> Dict:
        """Get database statistics."""
        session = self._get_session()
        try:
            total = session.query(Lead).count()
            new = session.query(Lead).filter(Lead.status == "new").count()
            contacted = session.query(Lead).filter(Lead.status == "contacted").count()
            converted = session.query(Lead).filter(Lead.status == "converted").count()

            return {
                "total_leads": total,
                "new_leads": new,
                "contacted": contacted,
                "converted": converted,
            }
        finally:
            session.close()
