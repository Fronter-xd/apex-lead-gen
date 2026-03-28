"""
Message Drafting Service using Ollama (Local Llama-3).
Generates personalized outreach messages for leads.
"""

import logging
import os
from typing import Dict

import requests

logger = logging.getLogger("apex.drafter")


class MessageDrafter:
    """Drafts personalized outreach messages using local Llama-3."""

    def __init__(self, config: Dict):
        self.config = config
        self.ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "llama3")
        self.max_length = config.get("outreach", {}).get("max_draft_length", 280)
        self.style = config.get("outreach", {}).get(
            "draft_style", "professional but friendly"
        )

    def draft_message(self, lead: Dict, platform: str) -> str:
        """
        Generate a personalized outreach message for a lead.

        Args:
            lead: Lead data dictionary
            platform: Platform name ('reddit' or 'twitter')

        Returns:
            Drafted message string
        """
        prompt = self._build_prompt(lead, platform)

        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.7, "top_p": 0.9, "num_predict": 300},
                },
                timeout=60,
            )

            if response.status_code == 200:
                result = response.json()
                message = result.get("response", "").strip()
                return self._clean_message(message, platform)
            else:
                logger.error(f"Ollama error: {response.status_code}")
                return self._fallback_draft(lead, platform)

        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to Ollama. Is it running?")
            return self._fallback_draft(lead, platform)
        except requests.exceptions.Timeout:
            logger.error("Ollama request timed out")
            return self._fallback_draft(lead, platform)
        except Exception as e:
            logger.error(f"Error drafting message: {e}")
            return self._fallback_draft(lead, platform)

    def _build_prompt(self, lead: Dict, platform: str) -> str:
        """Build the prompt for Llama-3."""

        platform_guidance = {
            "reddit": "Write a Reddit comment reply. Keep it conversational and authentic. Don't be overly promotional.",
            "twitter": "Write a Twitter/X reply. Be concise and engaging. Can use some emojis naturally. Max 280 characters.",
        }

        author = lead.get("author", "someone")
        content = lead.get("content", lead.get("title", ""))
        title = lead.get("title", "")

        prompt = f"""You are a helpful assistant drafting personalized outreach messages for potential customers.

CONTEXT:
- Person: {author}
- Platform: {platform.upper()}
- Original Post/Tweet: {title or content[:500]}

TASK:
Draft a {platform} response that:
1. Shows genuine empathy and understanding of their challenge
2. Offers helpful value (not spammy or salesy)
3. Naturally mentions how you might help (without being pushy)
4. Feels like a real human trying to help another human

STYLE: {self.style}
PLATFORM GUIDANCE: {platform_guidance.get(platform, "")}

Keep the response under {self.max_length} characters.

Your drafted response:"""

        return prompt

    def _clean_message(self, message: str, platform: str) -> str:
        """Clean and format the generated message."""
        message = message.strip()

        if platform == "twitter":
            if len(message) > 280:
                message = message[:277] + "..."

        message = message.replace("\\n", "\n")

        return message

    def _fallback_draft(self, lead: Dict, platform: str) -> str:
        """Generate a simple fallback draft when Ollama is unavailable."""
        author = lead.get("author", "there")
        content = lead.get("content", lead.get("title", ""))[:200]

        if platform == "reddit":
            return f"""Hey {author}, I completely understand what you're going through. This is something many people struggle with. I'd be happy to share some strategies that have worked for me and others - feel free to check out my profile if you'd like to learn more!"""
        else:
            return f"""Hey {author}! I totally get it - dealing with this is tough. I've found some approaches that might help. Happy to share if you're interested! 😊"""

    def batch_draft(self, leads: list, platform: str) -> list:
        """Draft messages for multiple leads."""
        results = []
        for lead in leads:
            draft = self.draft_message(lead, platform)
            results.append({**lead, "drafted_message": draft})
        return results
