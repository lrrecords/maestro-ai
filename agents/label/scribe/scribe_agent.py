"""
SCRIBE: Blog Master & Content Strategist for LRRecords
"""

from core.base_agent import BaseAgent
from core.job_store import JobStore
import os

SCRIBE_SYSTEM_PROMPT = (
    """
    You are SCRIBE, the Blog Master and Content Strategist for LRRecords.
    Your domain: blog content generation, social campaign creation, EasyFunnels blog API, Google Business Profile API, n8n webhook dispatch, approval queue submission.

    STRICT RULES (DO NOT BREAK):
    - ONLY generate topics about: drumming, bass playing, music production, mixing, recording, mastering, music business, record labels, music distribution, brand reviews, gear reviews.
    - DO NOT generate topics about productivity, communication, personal branding, or any general business skills UNLESS they are directly and explicitly about the music industry or music professionals.
    - EXCLUDE: music release reviews (Rascal Recommends handles these — refuse any such request).
    - Target: producers, musicians, bands, DJs, music industry professionals.
    - Tone: authoritative but accessible, LRRecords perspective, human-first.
    - Brand voice: no generative AI hype, no corporate language, grounded in real music industry experience.
    - Blog length: 800–1200 words.
    - One blog topic per week (propose 3, CEO must approve before writing).
    - All protected actions must pass through CEO approval queue before execution.

    If you are asked to generate topics outside these areas, respond: "Sorry, I only cover music industry topics as described above."
    """
)

class ScribeAgent(BaseAgent):
    """
    SCRIBE: Blog Master & Content Strategist for LRRecords
    PREMIUM AGENT — requires subscription
    """
    premium = True
    def __init__(self, job_store: JobStore, llm_provider="anthropic"):
        super().__init__(
            name="SCRIBE",
            department="Label",
            role="Blog Master & Content Strategist",
            system_prompt=SCRIBE_SYSTEM_PROMPT,
            job_store=job_store
        )
        self.job_store = job_store
        self.llm_provider = llm_provider
    # Add any SCRIBE-specific initialization here

    def llm(self, prompt, system=None):
        from core.llm_client import call_llm
        return call_llm(prompt)

    def run(self, context: dict) -> dict:
        """Stub run method for Agent Loader compatibility."""
        return {"status": "SCRIBE run method not yet implemented."}

    # Implement workflow steps as methods
    def propose_topics(self, topic_preferences=None):
        """Step 1: Generate 3 blog topic options with rationale, submit for CEO approval."""
        prompt = (
            "Generate 3 blog topic options for the LRRecords blog. "
            "All topics must be strictly about the music industry, music production, or the areas listed in the system prompt. "
            "Do not generate general business, productivity, or personal branding topics unless they are directly about music professionals. "
            "For each, provide a short rationale."
        )
        if topic_preferences:
            prompt += f"\nFocus on these preferences: {topic_preferences}"
        response = self.llm(prompt, system=SCRIBE_SYSTEM_PROMPT)
        # Try to parse as JSON, fallback to plain text
        try:
            topics = self.parse_json(response)
        except Exception:
            topics = response
        # Robust normalization: always produce a list of dicts with title/rationale
        def normalize_topics(raw):
            import ast
            import re
            def to_topic_dict(item):
                if isinstance(item, dict):
                    title = item.get('title') or item.get('option') or str(item)
                    rationale = item.get('rationale') or item.get('reason') or ''
                    return {'title': title, 'rationale': rationale}
                elif isinstance(item, str):
                    return {'title': item, 'rationale': ''}
                return {'title': str(item), 'rationale': ''}

            # Handle stringified Python dicts from Ollama
            if isinstance(raw, str):
                s = raw.strip()
                if (s.startswith('{') and s.endswith('}')) and ("blogTopic" in s or "title" in s):
                    try:
                        parsed = ast.literal_eval(s)
                        if parsed.keys() and all(k.startswith('blogTopic') for k in parsed.keys()):
                            topics = [to_topic_dict(v) for v in parsed.values()]
                            return {'blogTopics': topics}
                        if 'title' in parsed:
                            return {'blogTopics': [to_topic_dict(parsed)]}
                    except Exception:
                        pass
                try:
                    import json
                    parsed = json.loads(s)
                    if isinstance(parsed, dict):
                        if 'blogTopics' in parsed and isinstance(parsed['blogTopics'], list):
                            return {'blogTopics': [to_topic_dict(t) for t in parsed['blogTopics']]}
                        if 'topics' in parsed and isinstance(parsed['topics'], list):
                            return {'blogTopics': [to_topic_dict(t) for t in parsed['topics']]}
                        if parsed.keys() and all(k.startswith('blogTopic') for k in parsed.keys()):
                            topics = [to_topic_dict(v) for v in parsed.values()]
                            return {'blogTopics': topics}
                        if 'title' in parsed:
                            return {'blogTopics': [to_topic_dict(parsed)]}
                    if isinstance(parsed, list):
                        return {'blogTopics': [to_topic_dict(t) for t in parsed]}
                except Exception:
                    pass
                return {'blogTopics': [{'title': raw, 'rationale': ''}]}

            if isinstance(raw, dict):
                if 'blogTopics' in raw and isinstance(raw['blogTopics'], list):
                    return {'blogTopics': [to_topic_dict(t) for t in raw['blogTopics']]}
                if 'topics' in raw and isinstance(raw['topics'], list):
                    return {'blogTopics': [to_topic_dict(t) for t in raw['topics']]}
                if raw.keys() and all(k.startswith('blogTopic') for k in raw.keys()):
                    topics = [to_topic_dict(v) for v in raw.values()]
                    return {'blogTopics': topics}
                if 'title' in raw:
                    return {'blogTopics': [to_topic_dict(raw)]}
                return {'blogTopics': [to_topic_dict(raw)]}
            if isinstance(raw, list):
                return {'blogTopics': [to_topic_dict(t) for t in raw]}
            return {'blogTopics': []}

        output = normalize_topics(topics)
        import uuid
        from datetime import datetime
        job_id = str(uuid.uuid4())
        job_data = {
            "id": job_id,
            "agent": "SCRIBE",
            "type": "propose_topics",
            "status": "pending_approval",
            "input": {"topic_preferences": topic_preferences, "llm_provider": self.llm_provider},
            "output": output,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        self.job_store.add_job(job_id, job_data)
        return output

    def generate_blog_versions(self, approved_topic):
        """Step 2: Generate blog in EasyFunnels and Google Business Profile formats, submit for CEO approval."""
        import uuid
        from datetime import datetime
        prompt = (
            "You are SCRIBE. Write a full blog post (800-1200 words) for the LRRecords blog "
            "based on the following approved topic. "
            "Provide two versions: one for EasyFunnels (HTML-formatted) and one for Google Business Profile (plain text, ~500 words). "
            "Strictly follow the LRRecords brand voice: authoritative but accessible, music-industry focus, human-first, no AI hype.\n\n"
            f"Approved topic: {approved_topic}"
        )
        response = self.llm(prompt, system=SCRIBE_SYSTEM_PROMPT)
        try:
            output = self.parse_json(response)
        except Exception:
            output = {"easyfunnels_version": response, "google_business_version": response}
        job_id = str(uuid.uuid4())
        job_data = {
            "id": job_id,
            "agent": "SCRIBE",
            "type": "blog_versions",
            "status": "pending_approval",
            "input": {"approved_topic": approved_topic},
            "output": output,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        self.job_store.add_job(job_id, job_data)
        return output

    def generate_social_campaign(self, approved_blog):
        """Step 3: Generate social posts for all platforms, submit for CEO approval."""
        import uuid
        from datetime import datetime
        prompt = (
            "You are SCRIBE. Based on the following approved blog post, generate a social media campaign. "
            "Provide short posts for: X/Twitter (280 chars), Facebook, Instagram (with hashtags), "
            "Telegram, and Mastodon. Keep the LRRecords brand voice.\n\n"
            f"Blog content: {approved_blog}"
        )
        response = self.llm(prompt, system=SCRIBE_SYSTEM_PROMPT)
        try:
            output = self.parse_json(response)
        except Exception:
            output = {"social_posts": response}
        job_id = str(uuid.uuid4())
        job_data = {
            "id": job_id,
            "agent": "SCRIBE",
            "type": "social_campaign",
            "status": "pending_approval",
            "input": {"approved_blog": str(approved_blog)[:500]},
            "output": output,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        self.job_store.add_job(job_id, job_data)
        return output

    def dispatch_publish(self, approved_social):
        """Step 4: POST to n8n webhook with all approved content, log results to Redis."""
        import os
        import json
        try:
            import requests
        except ImportError:
            return {"ok": False, "error": "requests library not available"}
        webhook_url = os.environ.get("SCRIBE_N8N_WEBHOOK_URL", "")
        if not webhook_url:
            return {"ok": False, "error": "SCRIBE_N8N_WEBHOOK_URL not configured"}
        payload = {"approved_social": approved_social}
        try:
            resp = requests.post(webhook_url, json=payload, timeout=10)
            return {"ok": resp.ok, "status_code": resp.status_code}
        except Exception as e:
            return {"ok": False, "error": str(e)}
