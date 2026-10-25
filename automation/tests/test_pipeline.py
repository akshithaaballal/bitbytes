"""
Unit tests for BitBytes content automation pipeline.
Covers:
1. Source filter (including rejection of off-topic cooking story and blanket github.com)
2. Grounding gate (quote verification, relevance, deduplication, reject flag)
3. Rotation order (longest ago / unposted first across whole history)
4. Telegram formatting (length <= 4096 chars, source link, *x* to <i>x</i>)
"""

import os
import sys
import pytest

# Ensure automation root is in sys.path
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
AUTOMATION_DIR = os.path.dirname(TEST_DIR)
if AUTOMATION_DIR not in sys.path:
    sys.path.insert(0, AUTOMATION_DIR)

from crawlers.tech_radar import is_verified_source, validate_grounding, canonicalise_url, token_jaccard, tokenize_title
from publishers.telegram_publisher import format_telegram_html, build_telegram_message
from main import pick_next_post


# ---------------------------------------------------------
# 1. Source Filter Tests
# ---------------------------------------------------------
def test_source_filter_cooking_rejected():
    url = "https://danluu.com/cooking-daily"
    title = "Why we maintain our daily cooking again and again"
    assert is_verified_source(url, title) is False


def test_source_filter_negative_keywords():
    url = "https://cloudflare.com/election-results"
    title = "Election politics and celebrity news update"
    assert is_verified_source(url, title) is False


def test_source_filter_blanket_github_rejected():
    # Blanket github repo not in allowed orgs
    url = "https://github.com/someuser123/my-pet-project"
    title = "An open source LLM transformer project"
    assert is_verified_source(url, title) is False


def test_source_filter_allowed_github_org_accepted():
    url = "https://github.com/deepseek-ai/DeepSeek-V3"
    title = "DeepSeek V3 Multi-Head Latent Attention and Sparse MoE Routing"
    assert is_verified_source(url, title) is True


def test_source_filter_verified_domain_accepted():
    url = "https://postgresql.org/docs/btree"
    title = "B-Tree Indexing and Memory Buffer Allocation"
    assert is_verified_source(url, title) is True


def test_source_filter_subdomain_accepted():
    url = "https://blog.cloudflare.com/quic-udp"
    title = "QUIC Protocol and UDP Packet Transport Architecture"
    assert is_verified_source(url, title) is True


def test_source_filter_unverified_domain_rejected():
    url = "https://randomblog.xyz/post123"
    title = "B-Tree Indexes in Database Systems"
    assert is_verified_source(url, title) is False


# ---------------------------------------------------------
# 2. Grounding Gate Tests
# ---------------------------------------------------------
@pytest.fixture
def sample_article():
    return (
        "Cerebras has announced the deployment of frontier models on wafer-scale clusters. "
        "By replacing quadratic softmax attention with linear associative operators, "
        "inference latency drops dramatically while eliminating the memory footprint of past tokens. "
        "The hardware utilizes massive on-chip SRAM instead of external DRAM buses."
    )


def test_grounding_gate_valid(sample_article):
    post = {
        "title": "Linear Attention Mechanisms in Transformers",
        "source_claims": [
            {
                "claim": "Linear operators reduce latency",
                "quote": "replacing quadratic softmax attention with linear associative operators"
            }
        ],
        "relevance": {"score": 0.95, "reason": "Direct architectural explanation"},
        "reject": False
    }
    is_valid, reason = validate_grounding(post, sample_article, past_titles=[])
    assert is_valid is True
    assert "Passed" in reason


def test_grounding_gate_reject_flag(sample_article):
    post = {
        "reject": True,
        "reject_reason": "Article is an executive interview, not about technical systems."
    }
    is_valid, reason = validate_grounding(post, sample_article, past_titles=[])
    assert is_valid is False
    assert "LLM rejected" in reason


def test_grounding_gate_hallucinated_quote(sample_article):
    post = {
        "title": "Linear Attention Mechanisms",
        "source_claims": [
            {
                "claim": "Fake company claim",
                "quote": "This exact sentence does not appear anywhere in the source article text"
            }
        ],
        "relevance": {"score": 0.9, "reason": "Good"},
        "reject": False
    }
    is_valid, reason = validate_grounding(post, sample_article, past_titles=[])
    assert is_valid is False
    assert "hallucinated" in reason


def test_grounding_gate_low_relevance(sample_article):
    post = {
        "title": "Linear Attention Mechanisms",
        "source_claims": [
            {
                "claim": "Hardware details",
                "quote": "The hardware utilizes massive on-chip SRAM"
            }
        ],
        "relevance": {"score": 0.45, "reason": "Tangential mention only"},
        "reject": False
    }
    is_valid, reason = validate_grounding(post, sample_article, past_titles=[])
    assert is_valid is False
    assert "Relevance score" in reason


def test_grounding_gate_duplicate_title(sample_article):
    past = ["Linear Attention Mechanisms in Transformers"]
    post = {
        "title": "Linear Attention Mechanisms in Transformers",
        "source_claims": [
            {
                "claim": "Hardware details",
                "quote": "The hardware utilizes massive on-chip SRAM"
            }
        ],
        "relevance": {"score": 0.9, "reason": "Relevant"},
        "reject": False
    }
    is_valid, reason = validate_grounding(post, sample_article, past_titles=past)
    assert is_valid is False
    assert "matches recent post" in reason


# ---------------------------------------------------------
# 3. Rotation Order Tests
# ---------------------------------------------------------
def test_pick_next_post_unposted_first():
    posts = [
        {"id": "day_01", "title": "Post 1"},
        {"id": "day_02", "title": "Post 2"},
        {"id": "day_03", "title": "Post 3"}
    ]
    # day_01 and day_02 were posted; day_03 was never posted
    history = [
        {"post_id": "day_01"},
        {"post_id": "day_02"}
    ]
    picked = pick_next_post(posts, history)
    assert picked["id"] == "day_03"


def test_pick_next_post_longest_ago():
    posts = [
        {"id": "day_01", "title": "Post 1"},
        {"id": "day_02", "title": "Post 2"},
        {"id": "day_03", "title": "Post 3"}
    ]
    # All were posted, but day_02 was posted longest ago
    history = [
        {"post_id": "day_02"},
        {"post_id": "day_01"},
        {"post_id": "day_03"},
        {"post_id": "day_01"}
    ]
    picked = pick_next_post(posts, history)
    assert picked["id"] == "day_02"


# ---------------------------------------------------------
# 4. Telegram Formatting & Length Tests
# ---------------------------------------------------------
def test_telegram_message_length_and_source_link():
    post = {
        "track": "Computer Networks",
        "day": "Friday",
        "title": "TCP 3-Way Handshake vs UDP",
        "subtitle": "Transport Layer Protocols Explained",
        "summary": "As you heard, network performance depends on *packet latency* and reliability.",
        "key_points": [
            "SYN, SYN-ACK, ACK handshake establishes sequence synchrony.",
            "UDP avoids connection state, ideal for real-time video audio datagrams.",
            "QUIC runs over UDP with built-in TLS 1.3 encryption."
        ],
        "code_snippet": "import socket\ns = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)",
        "complexity": {"overhead": "O(1) connectionless"},
        "interview_tip": "Highlight head-of-line blocking differences in TCP byte streams.",
        "source": {
            "title": "RFC 9293 Transmission Control Protocol",
            "url": "https://www.rfc-editor.org/rfc/rfc9293.html",
            "domain": "rfc-editor.org"
        },
        "tags": ["#TCP", "#UDP", "#Networks"]
    }

    msg = build_telegram_message(post)
    assert len(msg) <= 4096
    # Clickable source link present
    assert '<a href="https://www.rfc-editor.org/rfc/rfc9293.html">' in msg
    assert "(rfc-editor.org)" in msg
    # *x* converted to <i>x</i>
    assert "<i>packet latency</i>" in msg
    assert "*packet latency*" not in msg


def test_telegram_enforces_4096_by_dropping_complexity_then_tip_never_source():
    # Create massive post exceeding 4096 chars
    post = {
        "track": "Distributed Systems",
        "day": "Tuesday",
        "title": "Massive Long Post Testing 4096 Character Enforcing",
        "subtitle": "Huge payload test",
        "summary": "Summary text " * 150, # ~2000 chars
        "key_points": ["Point " + str(i) + " " + ("long text " * 30) for i in range(3)],
        "code_snippet": "# code\n" * 30,
        "complexity": {"detail": "Drop this first " * 20},
        "interview_tip": "Drop this second " * 20,
        "source": {
            "title": "Crucial Authoritative Source",
            "url": "https://kernel.org/patch",
            "domain": "kernel.org"
        },
        "tags": ["#Systems"]
    }

    msg = build_telegram_message(post)
    assert len(msg) <= 4096
    # Source line must never be dropped!
    assert "https://kernel.org/patch" in msg
    assert "Crucial Authoritative Source" in msg
