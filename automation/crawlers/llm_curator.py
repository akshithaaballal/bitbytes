"""
LLM Technical Curator for BitBytes.
Transforms raw scraped tech/AI news into structured micro-lessons for B.Tech students.
Grounds lessons strictly in supplied articles.
Supports Google Gemini (SDK + REST) and OpenAI.
"""

import os
import sys
import re
import json
import time
import logging
import requests

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

logger = logging.getLogger("llm_curator")

# SYSTEM PROMPT (Verbatim as required by specification)
SYSTEM_PROMPT = """You are the technical editor of BitBytes, a micro-learning channel for B.Tech CS/AI students.
You receive ONE article. Teach the underlying CS/AI concept the article is genuinely about.
Rules:
1. Make claims about the news ONLY from the supplied article. Never invent events, numbers,
   companies or outages. If the article is not substantively about a teachable CS/AI/systems
   concept, return {"reject": true, "reject_reason": "..."} and nothing else.
2. summary: "As you might have heard, <one sentence of what the article reports, using only
   facts in source_claims>. So what is <Concept>? <2-3 sentences on the mechanism>."
   Plain text; no markdown or asterisks.
3. title: the formal concept name, 3-8 words. Not a headline.
4. key_points: exactly 3 specific points (internal data structure or algorithm detail,
   trade-off, practical tip). No generic filler.
5. code_snippet: 5-12 lines of Python or clearly-labelled pseudocode illustrating the concept.
6. source_claims: 1-3 objects {claim, quote}. quote is copied verbatim from the article,
   max 25 words.
7. relevance: {score: 0-1, reason}. How directly the article teaches this concept.
8. Do not output a day name, date or URLs. The system adds them.
Return only JSON: id, track, title, subtitle, summary, key_points[3], code_snippet,
complexity{time_or_memory, paradigm}, interview_tip, tags[], source_claims[], relevance{},
or the reject object."""


class LLMCurator:
    def __init__(self, gemini_api_key: str = None, openai_api_key: str = None):
        self.gemini_key = gemini_api_key or os.getenv("GEMINI_API_KEY", "").strip() or os.getenv("GOOGLE_API_KEY", "").strip()
        self.openai_key = openai_api_key or os.getenv("OPENAI_API_KEY", "").strip()
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest").strip()
        self.gemini_fallback = os.getenv("GEMINI_MODEL_FALLBACK", "gemini-3-flash-preview").strip()

    def curate_article(self, article_text: str, source_title: str = "", source_url: str = "", past_topics: list = None) -> dict:
        """
        Transforms article text into a BitBytes concept lesson grounded in the source article.
        Returns parsed lesson dictionary or None if not grounded / rejected.
        """
        past_topics_str = ", ".join(f"'{t}'" for t in (past_topics or [])[-30:])

        user_prompt = f"""SOURCE TITLE: {source_title}
SOURCE URL: {source_url}

RECENTLY COVERED TOPICS (DO NOT DUPLICATE THESE):
[{past_topics_str}]

ARTICLE TEXT:
----------------------------------------
{article_text[:12000]}
----------------------------------------

TASK:
1. Read the article text above.
2. If it is not substantively about a teachable CS/AI/systems concept, return {{"reject": true, "reject_reason": "..."}}.
3. Otherwise, teach the underlying concept following all rules in the system prompt.
"""

        # 1. Try Gemini API (Primary model, then Fallback model)
        if self.gemini_key:
            res = self._call_gemini_with_models(user_prompt)
            if res:
                return res

        # 2. Try OpenAI API if configured
        if self.openai_key:
            res = self._call_openai(user_prompt)
            if res:
                return res

        logger.warning("No LLM provider returned a valid lesson.")
        return None

    def _call_gemini_with_models(self, user_prompt: str) -> dict:
        models_to_try = [self.gemini_model]
        if self.gemini_fallback and self.gemini_fallback != self.gemini_model:
            models_to_try.append(self.gemini_fallback)

        for model in models_to_try:
            # Try SDK first
            res = self._call_gemini_sdk(model, user_prompt)
            if res:
                return res
            # Fall back to REST
            res = self._call_gemini_rest(model, user_prompt)
            if res:
                return res

        return None

    def _call_gemini_sdk(self, model_name: str, user_prompt: str) -> dict:
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.gemini_key)
            config = types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
                temperature=0.2,
            )

            # Retry with backoff on 429/5xx
            for attempt in range(2):
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=user_prompt,
                        config=config
                    )
                    if response and response.text:
                        parsed = self._parse_json(response.text)
                        if parsed:
                            return parsed
                except Exception as sdk_err:
                    err_str = str(sdk_err)
                    logger.warning(f"Gemini SDK error (provider: Google, model: {model_name}): {err_str}")
                    if ("429" in err_str or "500" in err_str or "503" in err_str) and attempt == 0:
                        time.sleep(2)
                        continue
                    break
        except Exception as init_err:
            logger.warning(f"Gemini SDK initialization note (model: {model_name}): {init_err}")

        return None

    def _call_gemini_rest(self, model_id: str, user_prompt: str) -> dict:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent?key={self.gemini_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "systemInstruction": {
                "parts": [{"text": SYSTEM_PROMPT}]
            },
            "contents": [
                {"parts": [{"text": user_prompt}]}
            ],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json"
            }
        }

        for attempt in range(2):
            try:
                res = requests.post(url, headers=headers, json=payload, timeout=30)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        parsed = self._parse_json(text)
                        if parsed:
                            return parsed
                elif res.status_code in (429, 500, 502, 503, 504) and attempt == 0:
                    logger.warning(f"Gemini REST transient status {res.status_code} (provider: Google, model: {model_id}), retrying...")
                    time.sleep(2)
                    continue
                else:
                    logger.warning(f"Gemini REST error HTTP {res.status_code} (provider: Google, model: {model_id}): {res.text[:200]}")
                    break
            except Exception as exc:
                logger.warning(f"Gemini REST exception (provider: Google, model: {model_id}): {exc}")
                if attempt == 0:
                    time.sleep(2)
                    continue
                break

        return None

    def _call_openai(self, user_prompt: str) -> dict:
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
            "temperature": 0.2,
            "response_format": {"type": "json_object"}
        }

        for attempt in range(2):
            try:
                res = requests.post(url, headers=headers, json=payload, timeout=30)
                if res.status_code == 200:
                    data = res.json()
                    text = data["choices"][0]["message"]["content"]
                    return self._parse_json(text)
                elif res.status_code in (429, 500, 502, 503) and attempt == 0:
                    logger.warning(f"OpenAI transient status {res.status_code} (model: gpt-4o-mini), retrying...")
                    time.sleep(2)
                    continue
                else:
                    logger.warning(f"OpenAI error HTTP {res.status_code} (model: gpt-4o-mini): {res.text[:200]}")
                    break
            except Exception as exc:
                logger.warning(f"OpenAI exception (model: gpt-4o-mini): {exc}")
                if attempt == 0:
                    time.sleep(2)
                    continue
                break

        return None

    def _parse_json(self, raw_text: str) -> dict:
        if not raw_text:
            return None
        try:
            cleaned = raw_text.strip()
            if cleaned.startswith("```"):
                cleaned = re.sub(r"^```(?:json)?\n?", "", cleaned)
                cleaned = re.sub(r"\n?```$", "", cleaned)
            parsed = json.loads(cleaned)
            return parsed
        except Exception as exc:
            logger.warning(f"Failed to parse LLM JSON response: {exc}")
            return None
