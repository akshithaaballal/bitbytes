"""
LLM Technical Curator & Semantic Deduplication Engine for BitBytes.
Transforms raw scraped tech/AI news into structured micro-lessons for B.Tech students.
Takes ONLY the underlying Computer Science / AI concept from the news, using the news
purely as an opening hook: "As you heard [news event], what is [Concept]? Let's learn about this!"
Supports Google Gemini (SDK + REST), OpenAI, and a Smart Algorithmic Synthesizer fallback.
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


SYSTEM_PROMPT = """You are the Principal Curriculum Architect and Technical Educator for 'BitBytes', 
a daily micro-learning channel for B.Tech Computer Science and AI students.

YOUR CORE MANDATE:
Do NOT simply report or broadcast the news article.
Instead, use the news story PURELY as a pedagogical launchpad to teach the underlying COMPUTER SCIENCE or AI CONCEPT behind it.

CRITICAL CONTENT HOOK RULE:
The 'summary' field MUST start off with a conversational hook referencing the news event and pivoting to the technical concept:
Format: "As you might have heard recently, [1 sentence summarizing the real-world news, event, or announcement]. But what actually is *[Main Concept Name]*? Let's learn about this: [2-3 sentences explaining the underlying CS/AI mechanism, how it works under the hood, and why it matters]."

TITLE RULE:
The 'title' MUST be the clean, formal technical name of the Computer Science / AI Concept or Architecture itself (e.g., "Mixture-of-Experts (MoE) Architecture", "Multi-Head Latent Attention (MLA)", "Kernel Space vs. User Space Isolation", "Distributed Write-Ahead Logging"). 
Do NOT make the title a news headline like "Company X raises $10M" or "New paper published".

You MUST output a valid JSON object matching this EXACT schema:
{
  "id": "slug_id_here",
  "track": "Track Name (e.g. AI & Machine Learning, Distributed Systems, Database Engineering, Core Operating Systems, Computer Networks)",
  "day": "DayName (e.g. Monday, Tuesday, etc.)",
  "title": "Clean, Formal Technical Name of the Concept / Architecture (4-8 words)",
  "subtitle": "One crisp sentence explaining what the architecture/algorithm solves or its performance advantage",
  "summary": "As you might have heard recently, [news event]. But what actually is [Main Concept]? Let's learn about this: [clear explanation of the core technical mechanism].",
  "key_points": [
    "1st key engineering insight, internal data structure, or algorithm detail",
    "2nd benchmark, architectural trade-off, or hardware implication",
    "3rd practical implementation tip or best practice"
  ],
  "code_snippet": "A clean 5-10 line Python snippet or pseudocode demonstrating the concept clearly",
  "complexity": {
    "time_or_memory": "Key performance characteristic (e.g., O(1) cache lookup, O(N) memory scaling, 3x lower inference latency)",
    "paradigm": "e.g., Sparse Gating, Vector Indexing, WAL Persistence, Page Table Virtualization"
  },
  "interview_tip": "One sharp advice on how this concept is tested in FAANG / engineering interviews or exams.",
  "tags": ["#AI", "#ComputerScience", "#Engineering", "#TechConcepts"]
}

STRICT INSTRUCTIONS:
1. Return ONLY the raw JSON object. Do not wrap in markdown ```json ``` blocks.
2. Technical rigor is paramount. Ensure the code snippet is syntactically clean and directly illustrates the concept.
3. Keep the tone approachable yet deeply educational for B.Tech engineering students.
"""


class LLMCurator:
    def __init__(self, gemini_api_key: str = None, openai_api_key: str = None):
        self.gemini_key = gemini_api_key or os.getenv("GEMINI_API_KEY", "").strip() or os.getenv("GOOGLE_API_KEY", "").strip()
        self.openai_key = openai_api_key or os.getenv("OPENAI_API_KEY", "").strip()

    def curate_article(self, article_text: str, source_title: str = "", source_url: str = "", past_topics: list = None) -> dict:
        """
        Transforms article text into a BitBytes concept lesson with semantic deduplication.
        """
        past_topics_str = ", ".join(f"'{t}'" for t in (past_topics or [])[-20:])

        user_prompt = f"""
TRENDING NEWS HEADLINE: {source_title}
SOURCE URL: {source_url}

RECENTLY COVERED TOPICS (DO NOT DUPLICATE THESE):
[{past_topics_str}]

NEWS ARTICLE EXCERPT:
----------------------------------------
{article_text[:4000]}
----------------------------------------

TASK:
1. Identify the fundamental Computer Science / AI / Systems concept behind this news.
2. Ensure the concept is NOT in the recently covered topics list above.
3. Start the summary with: "As you might have heard recently, [news event]. But what actually is [Main Concept]? Let's learn about this: ..."
4. Output the complete structured BitBytes lesson JSON.
"""

        # 1. Try Gemini API
        if self.gemini_key:
            print("   🤖 Curating with Google Gemini API...")
            res = self._call_gemini(user_prompt)
            if res:
                return res
            print("   ⚠️ Google Gemini did not return a valid lesson, checking next option...")

        # 2. Try OpenAI API
        if self.openai_key:
            print("   🤖 Curating with OpenAI API...")
            res = self._call_openai(user_prompt)
            if res:
                return res
            print("   ⚠️ OpenAI did not return a valid lesson, checking next option...")

        # 3. Smart Heuristic Synthesizer (Zero API key required fallback)
        print("   ℹ️ Using Smart Concept Synthesizer fallback...")
        return self._smart_synthesize(article_text, source_title, source_url, past_topics)

    def _call_gemini(self, user_prompt: str) -> dict:
        # A. Try official google-genai SDK first
        try:
            from google import genai
            client = genai.Client(api_key=self.gemini_key)
            full_prompt = f"{SYSTEM_PROMPT}\n\n{user_prompt}"
            
            # Use active models: gemini-3.8-flash, gemini-flash-latest, gemini-2.5-flash-lite
            for model_name in ["gemini-3.8-flash", "gemini-flash-latest", "gemini-2.5-flash-lite", "gemini-3.1-flash-lite"]:
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=full_prompt,
                    )
                    if response and response.text:
                        parsed = self._parse_json(response.text)
                        if parsed:
                            return parsed
                except Exception as model_err:
                    continue
        except Exception as sdk_err:
            print(f"   ℹ️ google-genai SDK note ({sdk_err}), trying direct REST API...")

        # B. Fallback to direct Gemini REST API
        try:
            for model_id in ["gemini-3.8-flash", "gemini-flash-latest", "gemini-2.5-flash-lite", "gemini-3.1-flash-lite"]:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent?key={self.gemini_key}"
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
                        "temperature": 0.3,
                        "responseMimeType": "application/json"
                    }
                }
                res = requests.post(url, headers=headers, json=payload, timeout=30)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        text = candidates[0]["content"]["parts"][0]["text"]
                        parsed = self._parse_json(text)
                        if parsed:
                            return parsed
                else:
                    continue
        except Exception as exc:
            print(f"   ⚠️ Gemini REST request failed: {exc}")

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
                "temperature": 0.3,
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
                    parsed["id"] = f"concept_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
                if not parsed.get("day"):
                    parsed["day"] = datetime.datetime.now().strftime("%A")
                return parsed
        except Exception as exc:
            print(f"   ⚠️ Failed to parse LLM JSON: {exc}")
        return None

    def _smart_synthesize(self, text: str, title: str, url: str, past_topics: list) -> dict:
        """
        Deterministic, zero-key intelligent synthesizer that extracts the core CS concept
        from trending headlines and guarantees the 'As you heard..., what is *concept*?' format.
        """
        now = datetime.datetime.now()
        day_name = now.strftime("%A")
        date_stamp = now.strftime("%Y%m%d_%H%M")

        clean_headline = (title or "Recent industry breakthroughs in scalable engineering").strip()
        lower_combined = (clean_headline + " " + text[:600]).lower()

        # Deduce concept and track from content
        if any(w in lower_combined for w in ["ai", "llm", "transformer", "neural", "attention", "gpu", "model", "deepseek", "gemini", "openai"]):
            concept_title = "Mixture-of-Experts (MoE) Architecture"
            track = "AI & Machine Learning"
            subtitle = "How routing tokens to sparse subnetworks achieves 4x inference throughput"
            hook = (
                f"As you might have heard recently, discussions around {clean_headline} have been surging across the AI community. "
                f"But what actually is *Mixture-of-Experts (MoE)*? Let's learn about this: instead of activating all billions of parameters "
                f"for every single token, MoE systems use a lightweight Router Gate to dynamically dispatch each token to only top-k expert subnetworks, "
                f"drastically slashing computation while maintaining high representation capacity."
            )
            snippet = (
                "# Sparse Mixture of Experts (MoE) Routing\n"
                "import torch\n"
                "def moe_routing(tokens, router_weights, top_k=2):\n"
                "    logits = torch.matmul(tokens, router_weights) # [batch, num_experts]\n"
                "    top_weights, top_indices = torch.topk(torch.softmax(logits, dim=-1), top_k)\n"
                "    return top_weights, top_indices # Send tokens only to selected experts"
            )
            complexity = {"time_or_memory": "O(k / total_experts) active compute", "paradigm": "Conditional Computation & Gating"}
            tip = "In AI interviews, be ready to explain how token routing load-balancing prevents expert collapse."
            tags = ["#AI", "#DeepLearning", "#MixtureOfExperts", "#Transformers", "#Python"]

        elif any(w in lower_combined for w in ["database", "sql", "cache", "redis", "storage", "disk", "postgres", "valkey"]):
            concept_title = "Write-Ahead Logging (WAL) in Distributed Storage"
            track = "Database Engineering"
            subtitle = "Achieving ACID durability with sequential append-only disk commits"
            hook = (
                f"As you might have heard recently, discussions surrounding {clean_headline} have put database reliability in the spotlight. "
                f"But what actually is *Write-Ahead Logging (WAL)*? Let's learn about this: to guarantee Durability without the huge latency penalty "
                f"of writing random disk blocks immediately, databases write changes sequentially to an append-only log file first before updating main tables, "
                f"enabling instant crash recovery and point-in-time rollbacks."
            )
            snippet = (
                "# Minimal Write-Ahead Logger (WAL) Simulation\n"
                "class WALLogger:\n"
                "    def log_operation(self, lsn: int, tx_id: str, op: str):\n"
                "        # Sequential disk writes are up to 100x faster than random I/O\n"
                "        with open('engine.wal', 'a') as wal_file:\n"
                "            wal_file.write(f'{lsn}:{tx_id}:{op}\\n')\n"
                "            wal_file.flush() # Force write to physical storage"
            )
            complexity = {"time_or_memory": "O(1) sequential append", "paradigm": "Durability & Crash Recovery"}
            tip = "Expect questions on how checkpointing prevents the WAL log from expanding indefinitely."
            tags = ["#Databases", "#ACID", "#SystemDesign", "#Storage", "#Backend"]

        elif any(w in lower_combined for w in ["kernel", "driver", "crash", "operating system", "linux", "windows", "memory", "thread", "concurrency"]):
            concept_title = "Kernel Space vs. User Space Protection Rings"
            track = "Core Operating Systems"
            subtitle = "Hardware privilege rings (Ring 0 vs. Ring 3) and memory boundary isolation"
            hook = (
                f"As you might have heard recently, widespread system outages highlighted in {clean_headline} raised questions about OS stability. "
                f"But what actually is *Kernel Space vs. User Space Isolation*? Let's learn about this: modern CPUs enforce hardware privilege levels "
                f"where user applications run in restricted Ring 3 without direct hardware access, while the OS kernel operates in privileged Ring 0. "
                f"A crash in Ring 3 terminates only that app, but an unhandled fault in Ring 0 triggers a full system crash (BSOD or Kernel Panic)."
            )
            snippet = (
                "# User Space System Call Transition\n"
                "# In user space (Ring 3), apps cannot directly access hardware.\n"
                "# They execute a Software Interrupt / Syscall Instruction:\n"
                "import os\n"
                "def safe_read(file_descriptor, byte_count):\n"
                "    # os.read traps into Ring 0 kernel mode safely\n"
                "    return os.read(file_descriptor, byte_count)"
            )
            complexity = {"time_or_memory": "Hardware context switch overhead (~100-500ns)", "paradigm": "Hardware Privilege Rings"}
            tip = "Know the difference between Context Switch (process-to-process) and Mode Switch (user-to-kernel)."
            tags = ["#OperatingSystems", "#Kernel", "#MemoryManagement", "#Architecture", "#CS"]

        else:
            concept_title = "Distributed Idempotency & Two-Phase Locking"
            track = "Distributed Systems & Cloud"
            subtitle = "Preventing double-spend and race conditions in distributed microservices"
            hook = (
                f"As you might have heard recently in discussions regarding {clean_headline}, scaling distributed services reliably remains critical. "
                f"But what actually is *Distributed Idempotency*? Let's learn about this: in a distributed network where requests can be retried due to packet loss, "
                f"an idempotent endpoint guarantees that receiving the exact same payload multiple times produces the identical side-effect as executing it once."
            )
            snippet = (
                "# Distributed Idempotency Key Pattern\n"
                "def process_payment(redis_client, idempotency_key, amount):\n"
                "    # Atomic setnx with 60-second expiration\n"
                "    is_new = redis_client.set(f'idemp:{idempotency_key}', 'PROCESSED', nx=True, ex=60)\n"
                "    if not is_new:\n"
                "        return {'status': 'ignored_duplicate_request'}\n"
                "    return {'status': 'processed', 'amount': amount}"
            )
            complexity = {"time_or_memory": "O(1) atomic lock verification", "paradigm": "Distributed Consensus & Idempotency"}
            tip = "Always highlight the trade-offs between at-least-once delivery vs exactly-once processing."
            tags = ["#DistributedSystems", "#Microservices", "#SystemDesign", "#Cloud", "#Backend"]

        return {
            "id": f"radar_{date_stamp}",
            "track": track,
            "day": day_name,
            "title": concept_title,
            "subtitle": subtitle,
            "summary": hook,
            "key_points": [
                "Underlying Mechanism: Solves critical performance or reliability constraints without brute-force hardware overhead.",
                "Architectural Trade-off: Balances computational throughput against state synchrony and memory footprint.",
                "Engineering Application: Universally deployed across modern enterprise scale and high-load production systems."
            ],
            "code_snippet": snippet,
            "complexity": complexity,
            "interview_tip": tip,
            "tags": tags,
            "source_headline": clean_headline,
            "source_url": url,
            "curator": "Autonomous Tech Radar"
        }
