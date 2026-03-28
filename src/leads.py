#!/usr/bin/env python3
"""
Apex Lead Generation Engine
An autonomous AI-powered lead generation system for Reddit and Twitter.
"""

import argparse
import asyncio
import logging
import os
import sys
import time
from pathlib import Path

import yaml

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("apex")


def load_config():
    config_path = Path(__file__).parent.parent / "config" / "settings.yaml"
    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f)
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


def run_continuous(config):
    """Run continuous monitoring loop."""
    from src.scrapers.reddit_scraper import RedditScraper
    from src.scrapers.twitter_scraper import TwitterScraper
    from src.services.lead_scorer import LeadScorer
    from src.services.message_drafter import MessageDrafter
    from src.db.database import Database

    db = Database()

    scrapers = {}
    if "reddit" in config["monitoring"]["platforms"]:
        scrapers["reddit"] = RedditScraper()
    if "twitter" in config["monitoring"]["platforms"]:
        scrapers["twitter"] = TwitterScraper()

    scorer = LeadScorer(config)
    drafter = MessageDrafter(config)

    interval = config["monitoring"]["interval_minutes"] * 60

    logger.info(
        f"Starting continuous monitoring (interval: {config['monitoring']['interval_minutes']} min)"
    )

    while True:
        try:
            for platform, scraper in scrapers.items():
                logger.info(f"Scraping {platform}...")
                posts = scraper.scrape(config["monitoring"]["keywords"])
                logger.info(f"Found {len(posts)} posts on {platform}")

                for post in posts:
                    if db.is_duplicate(platform, post["id"]):
                        continue

                    score = scorer.score_lead(post)
                    post["total_score"] = score

                    if score >= config["scoring"]["engagement_threshold"]:
                        logger.info(f"Lead scored {score:.2f} - drafting message...")

                        if config["outreach"]["auto_draft"]:
                            draft = drafter.draft_message(post, platform)
                            post["drafted_message"] = draft

                        db.save_lead(platform, post)
                        logger.info(f"Lead saved: {post['author']}")
                    else:
                        db.save_lead(platform, post, status="rejected")
                        logger.debug(f"Lead below threshold: {post['author']}")

            logger.info(
                f"Sleeping for {config['monitoring']['interval_minutes']} minutes..."
            )
            time.sleep(interval)

        except KeyboardInterrupt:
            logger.info("Shutting down...")
            break
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")
            time.sleep(60)


def cmd_scrape(config):
    """Single scrape operation."""
    from src.scrapers.reddit_scraper import RedditScraper
    from src.scrapers.twitter_scraper import TwitterScraper
    from src.services.lead_scorer import LeadScorer
    from src.services.message_drafter import MessageDrafter
    from src.db.database import Database

    db = Database()
    scrapers = {}

    if "reddit" in config["monitoring"]["platforms"]:
        scrapers["reddit"] = RedditScraper()
    if "twitter" in config["monitoring"]["platforms"]:
        scrapers["twitter"] = TwitterScraper()

    scorer = LeadScorer(config)
    drafter = MessageDrafter(config)

    for platform, scraper in scrapers.items():
        posts = scraper.scrape(config["monitoring"]["keywords"])
        print(f"[{platform}] Found {len(posts)} posts")

        for post in posts:
            if db.is_duplicate(platform, post["id"]):
                print(f"  - Duplicate: {post['id']}")
                continue

            score = scorer.score_lead(post)
            post["total_score"] = score

            if score >= config["scoring"]["engagement_threshold"]:
                if config["outreach"]["auto_draft"]:
                    draft = drafter.draft_message(post, platform)
                    post["drafted_message"] = draft
                db.save_lead(platform, post)
                print(f"  + NEW LEAD: {post['author']} (score: {score:.2f})")
            else:
                print(f"  - Low score: {post['author']} ({score:.2f})")


def cmd_list(config):
    """List recent leads."""
    from src.db.database import Database

    db = Database()
    leads = db.get_recent_leads(limit=20)

    print("\n" + "=" * 80)
    print(f"{'ID':<6} {'Platform':<10} {'Author':<20} {'Score':<8} {'Status':<12}")
    print("=" * 80)

    for lead in leads:
        print(
            f"{lead['id']:<6} {lead['platform']:<10} {lead['author'][:18]:<20} {lead['total_score']:<8.2f} {lead['status']:<12}"
        )

    print("=" * 80 + "\n")


def cmd_view(config, lead_id):
    """View a specific lead."""
    from src.db.database import Database

    db = Database()
    lead = db.get_lead(lead_id)

    if not lead:
        print(f"Lead {lead_id} not found")
        return

    print("\n" + "=" * 80)
    print(f"LEAD #{lead['id']}")
    print("=" * 80)
    print(f"Platform:  {lead['platform']}")
    print(f"Author:    {lead['author']}")
    print(f"Post ID:   {lead['post_id']}")
    print(f"Score:     {lead['total_score']:.2f}")
    print(f"Status:    {lead['status']}")
    print(f"URL:       {lead['url']}")
    print(f"Created:   {lead['created_at']}")
    print("-" * 80)
    print(f"Content:\n{lead['content']}")

    if lead.get("drafted_message"):
        print("-" * 80)
        print("Drafted Message:")
        print(lead["drafted_message"])

    print("=" * 80 + "\n")


def cmd_export(config, format_type="csv"):
    """Export leads to file."""
    from src.db.database import Database
    import csv

    db = Database()
    leads = db.get_recent_leads(limit=1000)

    if format_type == "csv":
        filename = f"leads_export_{int(time.time())}.csv"
        with open(filename, "w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "id",
                    "platform",
                    "author",
                    "content",
                    "url",
                    "total_score",
                    "status",
                    "drafted_message",
                    "created_at",
                ],
            )
            writer.writeheader()
            writer.writerows(leads)
        print(f"Exported {len(leads)} leads to {filename}")


def cmd_init_db(config):
    """Initialize the database."""
    from src.db.database import Database

    db = Database()
    db.init_db()
    print("Database initialized successfully")


def main():
    parser = argparse.ArgumentParser(description="Apex Lead Generation Engine")
    parser.add_argument(
        "command",
        nargs="?",
        choices=["run", "scrape", "list", "view", "export", "init"],
        default="run",
        help="Command to run",
    )
    parser.add_argument("args", nargs="*", help="Additional arguments")

    args = parser.parse_args()
    config = load_config()

    if args.command == "run":
        run_continuous(config)
    elif args.command == "scrape":
        cmd_scrape(config)
    elif args.command == "list":
        cmd_list(config)
    elif args.command == "view":
        if not args.args:
            print("Please provide a lead ID")
            return
        cmd_view(config, int(args.args[0]))
    elif args.command == "export":
        cmd_export(config, args.args[0] if args.args else "csv")
    elif args.command == "init":
        cmd_init_db(config)


if __name__ == "__main__":
    main()
