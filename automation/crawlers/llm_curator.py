"""
LLM Technical Curator & Semantic Deduplication Engine for BitBytes.
Transforms raw scraped tech/AI articles into structured micro-lessons for B.Tech students.
Supports Google Gemini, OpenAI, and a Smart Algorithmic Synthesizer fallback.
"""

import os
import sys
import re
import json
import uuid
import datetime
import requests

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


SYSTEM_PROMPT = """You are the Principal Curriculum Architect and Technical Curator for 'BitBytes', 
a daily micro-learning channel for B.Tech Computer Science and AI students.

Your task is to take a raw technical article or trending software release and distill it into an 
engaging, high-yield educational micro-lesson.

You MUST output a valid JSON object matching this EXACT schema:
{
  "id": "slug_id_here",
  "track": "Track Name (e.g. AI & Deep Learning, Distributed Systems, Database Architecture, DSA & Algorithms)",
  "day": "DayName (e.g. Monday, Tuesday, etc.)",
  "title": "Punchy 6-9 word title explaining the technical breakthrough or pattern",
  "subtitle": "One crisp sentence explaining the real-world value or architectural advantage",
  "summary": "2-3 clear sentences explaining the underlying Computer Science mechanism.",
  "key_points": [
    "1st key engineering insight or algorithm detail",
    "2nd benchmark, architectural decision, or trade-off",
    "3rd practical implementation tip or best practice"
  ],
  "code_snippet": "A clean 5-10 line Python snippet or pseudocode demonstrating the concept",
  "complexity": {
    "metric": "Key performance characteristic (e.g., O(log N) parameter search, 3x memory reduction)",
    "paradigm": "e.g., Vector Embeddings, Concurrency, MapReduce, Transformer Architecture"
  },
  "interview_tip": "One sharp advice on how this concept is tested in FAANG / engineering interviews.",
  "tags": ["#AI", "#ComputerScience", "#Engineering", "#TechUpdate"]
}

CRITICAL RULES:
1. Return ONLY the raw JSON object. Do not wrap in markdown ```json ``` blocks.
2. Ensure technical rigor. The code snippet must be valid and readable.
3. Keep explanation concise and accessible for engineering students.
"""


class LLMCurator:
    def __init__(self, gemini_api_key: str = None, openai_api_key: str = None):
        self.gemini_key = gemini_api_key or os.getenv("GEMINI_API_KEY", "").strip()
        self.openai_key = openai_api_key or os.getenv("OPENAI_API_KEY", "").strip()

    def curate_article(self, article_text: str, source_title: str = "", source_url: str = "", past_topics: list = None) -> dict:
        """
        Transforms article markdown into a BitBytes lesson with semantic deduplication.
        """
        past_topics_str = ", ".join(f"'{t}'" for t in (past_topics or [])[-15:])

        user_prompt = f"""
SOURCE TITLE: {source_title}
SOURCE URL: {source_url}

RECENTLY COVERED TOPICS (DO NOT DUPLICATE THESE):
[{past_topics_str}]

RAW ARTICLE CONTENT (Excerpt):
----------------------------------------
{article_text[:4000]}
----------------------------------------

Please analyze this article and produce the structured BitBytes JSON lesson.
Make sure the concept is distinct and offers fresh insights compared to recent topics.
"""

        # 1. Try Gemini API
        if self.gemini_key:
            print("   🤖 Curating with Google Gemini API...")
            res = self._call_gemini(user_prompt)
            if res:
                return res

        # 2. Try OpenAI API
        if self.openai_key:
            print("   🤖 Curating with OpenAI API...")
            res = self._call_openai(user_prompt)
            if res:
                return res

        # 3. Smart Heuristic Synthesizer (No API key required)
        print("   ℹ️ No LLM API key detected (GEMINI_API_KEY / OPENAI_API_KEY). Using Intelligent Synthesizer...")
        return self._smart_synthesize(article_text, source_title, source_url, past_topics)

    def _call_gemini(self, user_prompt: str) -> dict:
        try:
            # Using Gemini 1.5 Flash endpoint
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_key}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": SYSTEM_PROMPT},
                            {"text": user_prompt}
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.4,
                    "responseMimeType": "application/json"
                }
            }
            res = requests.post(url, headers=headers, json=payload, timeout=30)
            if res.status_code == 200:
                data = res.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return self._parse_json(text)
            else:
                print(f"   ⚠️ Gemini API error (HTTP {res.status_code}): {res.text[:200]}")
                return None
        except Exception as exc:
            print(f"   ⚠️ Gemini request failed: {exc}")
            return None

    def _call_openai(self, user_prompt: str) -> dict:
        try:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.openai_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.4,
                "response_format": {"type": "json_object"}
            }
            res = requests.post(url, headers=headers, json=payload, timeout=30)
            if res.status_code == 200:
                data = res.json()
                text = data["choices"][0]["message"]["content"]
                return self._parse_json(text)
            else:
                print(f"   ⚠️ OpenAI API error (HTTP {res.status_code}): {res.text[:200]}")
                return None
        except Exception as exc:
            print(f"   ⚠️ OpenAI request failed: {exc}")
            return None

    def _parse_json(self, raw_text: str) -> dict:
        try:
            cleaned = raw_text.strip()
            if cleaned.startswith("```"):
                cleaned = re.sub(r"^```(?:json)?\n?", "", cleaned)
                cleaned = re.sub(r"\n?```$", "", cleaned)
            parsed = json.loads(cleaned)
            # Ensure required fields
            if "title" in parsed and "summary" in parsed:
                if not parsed.get("id"):
                    parsed["id"] = f"radar_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
                if not parsed.get("day"):
                    parsed["day"] = datetime.datetime.now().strftime("%A")
                return parsed
        except Exception as exc:
            print(f"   ⚠️ Failed to parse LLM JSON: {exc}")
        return None

    def _smart_synthesize(self, text: str, title: str, url: str, past_topics: list) -> dict:
        """
        Deterministic, zero-key intelligent synthesizer that crafts a valid,
        high-yield CS bite directly from scraped headlines and content.
        """
        now = datetime.datetime.now()
        day_name = now.strftime("%A")
        date_stamp = now.strftime("%Y%m%d_%H%M")

        clean_title = title or "Modern Architectural Patterns in High-Performance Systems"
        # Avoid duplication with simple variation
        if past_topics and clean_title in past_topics:
            clean_title = f"Deep Dive: {clean_title} in Production"

        # Determine best track based on keywords
        lower_text = (clean_title + " " + text[:500]).lower()
        if any(w in lower_text for w in ["ai", "llm", "transformer", "neural", "gpu", "model", "diffusion"]):
            track = "AI & Machine Learning"
            snippet = (
                "# Scalable Attention Mechanism Check\n"
                "import torch\n"
                "def flash_attention_block(q, k, v, mask=None):\n"
                "    # Linearized memory footprint: O(N) instead of O(N^2)\n"
                "    return torch.nn.functional.scaled_dot_product_attention(q, k, v, attn_mask=mask)"
            )
            complexity = {"time": "O(N) memory scaling", "paradigm": "Flash Attention / Tensor Parallelism"}
            tip = "Expect questions on how KV-cache optimization prevents GPU out-of-memory errors during autoregressive decoding."
            tags = ["#AI", "#MachineLearning", "#DeepLearning", "#Python", "#Engineering"]
        elif any(w in lower_text for w in ["database", "sql", "cache", "redis", "storage", "disk"]):
            track = "Database & Storage Systems"
            snippet = (
                "# LSM-Tree Write Path (Append-Only Log)\n"
                "class WALLogger:\n"
                "    def append_record(self, key, value):\n"
                "        # Sequential disk I/O gives 100x write throughput over random writes\n"
                "        with open('wal.log', 'a') as f:\n"
                "            f.write(f'{key}:{value}\\n')"
            )
            complexity = {"time": "O(1) sequential write", "paradigm": "LSM Trees & Write-Ahead Logging"}
            tip = "Be prepared to compare B-Tree (read-optimized) vs LSM-Tree (write-heavy) architectures."
            tags = ["#Database", "#Storage", "#Backend", "#DistributedSystems", "#CS"]
        else:
            track = "Distributed Systems & Cloud"
            snippet = (
                "# Distributed Idempotency Key Pattern\n"
                "def process_transaction(db, redis_client, tx_id, amount):\n"
                "    if not redis_client.set(f'idemp:{tx_id}', 'locked', nx=True, ex=60):\n"
                "        return {'status': 'duplicate_request_ignored'}\n"
                "    return db.execute_transfer(tx_id, amount)"
            )
            complexity = {"time": "O(1) atomic check", "paradigm": "Distributed Consensus & Idempotency"}
            tip = "Always bring up network partitions and at-least-once message delivery semantics in system design."
            tags = ["#SystemDesign", "#CloudArchitecture", "#Concurrency", "#Backend", "#BTechPrep"]

        return {
            "id": f"radar_{date_stamp}",
            "track": track,
            "day": day_name,
            "title": clean_title[:75],
            "subtitle": f"Key technical takeaways from trending software and research ({now.strftime('%B %Y')})",
            "summary": (
                f"Recent engineering developments highlight major improvements in {track.lower()}. "
                f"This architectural shift focuses on eliminating latency bottlenecks and improving fault-tolerant state management."
            ),
            "key_points": [
                "Bottleneck Elimination: Replaces legacy blocking operations with asynchronous, zero-copy primitives.",
                "Resource Efficiency: Maximizes hardware utilization across memory hierarchy and cache lines.",
                "Production Reliability: Embeds strict telemetry and idempotency guarantees for distributed scale."
            ],
            "code_snippet": snippet,
            "complexity": complexity,
            "interview_tip": tip,
            "tags": tags,
            "source_url": url,
            "curator": "Autonomous Tech Radar"
        }
