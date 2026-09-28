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


# ---------------------------------------------------------
# 5. Tier Ordering, Bank Fallback, Telemetry & Bridge Tests
# ---------------------------------------------------------
import json
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta
from report import sanitize_secrets
from publishers.bridge_reporter import truncate_textarea, BRIDGE_ENCODING
from crawlers.tech_radar import harvest_tiered_post


def test_secret_redaction():
    text = "Error calling API: AIzaSyD1234567890123456789012345678901 with secret='super_secret_token_123456'"
    cleaned = sanitize_secrets(text)
    assert "AIzaSyD1234567890123456789012345678901" not in cleaned
    assert "[REDACTED_API_KEY]" in cleaned
    assert "[REDACTED_CREDENTIAL]" in cleaned


def test_report_truncation():
    huge_text = "x" * 2500
    truncated = truncate_textarea(huge_text, max_chars=1800)
    assert len(truncated) <= 1800
    assert truncated.endswith("...")

    short_text = "Short text"
    assert truncate_textarea(short_text, max_chars=1800) == short_text


def test_tier_ordering_stops_at_first_successful_tier():
    with patch("crawlers.tech_radar.fetch_tier_1_leads") as mock_t1, \
         patch("crawlers.tech_radar.fetch_tier_2_leads") as mock_t2, \
         patch("crawlers.tech_radar.fetch_tier_3_leads") as mock_t3, \
         patch("crawlers.tech_radar.filter_and_dedupe_candidates") as mock_filter, \
         patch("crawlers.tech_radar.attempt_candidates_in_tier") as mock_attempt:

        mock_t1.return_value = [{"title": "T1 Lead", "url": "https://postgresql.org/doc"}]
        mock_filter.return_value = ([{"title": "T1 Lead", "url": "https://postgresql.org/doc"}], "ok")
        mock_post = {"title": "PostgreSQL MVCC", "track": "Database Engineering", "engine": "t1_livesearch"}
        mock_attempt.return_value = (mock_post, [{"url": "https://postgresql.org/doc", "reject_reason": None}])

        post, tier, attempts = harvest_tiered_post(history=[])
        assert post is not None
        assert tier == "T1_LiveSearch"
        assert mock_t1.called
        assert not mock_t2.called
        assert not mock_t3.called


def test_tier_ordering_advances_to_t2_when_t1_fails():
    with patch("crawlers.tech_radar.fetch_tier_1_leads") as mock_t1, \
         patch("crawlers.tech_radar.fetch_tier_2_leads") as mock_t2, \
         patch("crawlers.tech_radar.fetch_tier_3_leads") as mock_t3, \
         patch("crawlers.tech_radar.filter_and_dedupe_candidates") as mock_filter, \
         patch("crawlers.tech_radar.attempt_candidates_in_tier") as mock_attempt:

        mock_t1.return_value = []
        mock_t2.return_value = [{"title": "T2 RSS Lead", "url": "https://blog.cloudflare.com/quic"}]
        mock_filter.side_effect = [
            ([], "no_candidates"),
            ([{"title": "T2 RSS Lead", "url": "https://blog.cloudflare.com/quic"}], "ok")
        ]
        mock_post = {"title": "Cloudflare QUIC", "track": "Computer Networks", "engine": "t2_rssfeeds"}
        mock_attempt.return_value = (mock_post, [{"url": "https://blog.cloudflare.com/quic", "reject_reason": None}])

        post, tier, attempts = harvest_tiered_post(history=[])
        assert post is not None
        assert tier == "T2_RSSFeeds"
        assert mock_t1.called
        assert mock_t2.called
        assert not mock_t3.called


def test_bank_last_behavior_only_when_all_tiers_exhausted():
    with patch("crawlers.tech_radar.fetch_tier_1_leads", return_value=[]), \
         patch("crawlers.tech_radar.fetch_tier_2_leads", return_value=[]), \
         patch("crawlers.tech_radar.fetch_tier_3_leads", return_value=[]), \
         patch("crawlers.tech_radar.filter_and_dedupe_candidates", return_value=([], "no_candidates")):

        post, tier_or_reason, attempts = harvest_tiered_post(history=[])
        assert post is None
        assert "All tiers exhausted" in tier_or_reason


def test_bank_repeat_14_day_detection():
    now_utc = datetime.now(timezone.utc)
    ten_days_ago = (now_utc - timedelta(days=10)).isoformat()
    twenty_days_ago = (now_utc - timedelta(days=20)).isoformat()

    history_recent = [{"id": "day_01", "timestamp": ten_days_ago}]
    history_old = [{"id": "day_01", "timestamp": twenty_days_ago}]

    fourteen_days_ago = now_utc - timedelta(days=14)
    is_recent = False
    for h in history_recent:
        if h.get("id") == "day_01":
            h_time = datetime.fromisoformat(h["timestamp"])
            if h_time >= fourteen_days_ago:
                is_recent = True
    assert is_recent is True

    is_old = False
    for h in history_old:
        if h.get("id") == "day_01":
            h_time = datetime.fromisoformat(h["timestamp"])
            if h_time >= fourteen_days_ago:
                is_old = True
    assert is_old is False


def test_send_record_payload_keys():
    agent_dir = os.path.abspath(os.path.join(AUTOMATION_DIR, "..", "agent"))
    if agent_dir not in sys.path:
        sys.path.insert(0, agent_dir)
    import Bot

    with patch("requests.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"ErrorCode": 0, "ErrorMessage": "BRG-12345"}
        mock_post.return_value = mock_resp

        values = {
            1: "DP-100-TEST",
            2: "TechRadar-Pipeline",
            4: "Completed"
        }
        res = Bot.send_record("DataProcessing", values)
        assert res.get("success") is True
        assert res.get("bridgeId") == "BRG-12345"

        assert mock_post.called
        call_kwargs = mock_post.call_args[1]
        data_sent = json.loads(call_kwargs["data"]["Data"])
        base_flow = "BitBytesData_DataProcessing"
        payload = data_sent[base_flow]

        keys = list(payload.keys())
        assert any(k.endswith("_1") for k in keys)
        assert any(k.endswith("_2") for k in keys)
        assert any(k.endswith("_4") for k in keys)


# ---------------------------------------------------------
# 6. Social Card Image Rendering & Telegram Photo Tests
# ---------------------------------------------------------
from PIL import Image
from publishers.image_generator import render_social_card
from publishers.telegram_publisher import publish_to_telegram


def test_render_social_card_long_content(tmp_path):
    post = {
        "id": "test_card_long",
        "track": "Computer Networks & Systems Architecture",
        "title": "QUIC Protocol and UDP Datagram Multiplexing Across High-Latency Distributed Clusters",
        "subtitle": "Eliminating head-of-line blocking and speeding up TLS 1.3 handshakes across the globe",
        "key_points": [
            "Connection IDs decouple transport state from client IP address or network interface migrations.",
            "Independent stream flow control prevents single packet loss from stalling concurrent application requests.",
            "Zero round-trip time resumption caches server parameters to accelerate repeated connection attempts.",
            "Congestion control algorithms like BBRv2 continuously probe bandwidth bottlenecks without packet loss spikes."
        ],
        "code_snippet": """def parse_quic_header(packet_bytes):
    # Extract flag byte and packet type
    header_form = (packet_bytes[0] & 0x80) >> 7
    fixed_bit = (packet_bytes[0] & 0x40) >> 6
    if header_form == 1:
        # Long header for initial connection setup
        long_packet_type = (packet_bytes[0] & 0x30) >> 4
        return "LongHeader", long_packet_type
    return "ShortHeader", None""",
        "source": {"domain": "blog.cloudflare.com"}
    }
    out_file = str(tmp_path / "card.png")
    result_path = render_social_card(post, output_path=out_file)
    assert result_path == out_file
    assert os.path.exists(out_file)

    with Image.open(out_file) as im:
        assert im.size == (1080, 1080)


def test_telegram_send_photo_then_message(tmp_path):
    img_file = tmp_path / "test.png"
    img_file.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82")

    post = {
        "title": "Test Topic",
        "track": "Systems",
        "summary": "Summary text",
        "key_points": ["Point 1"]
    }

    photo_resp = MagicMock()
    photo_resp.status_code = 200
    photo_resp.json.return_value = {"ok": True, "result": {"message_id": 101, "chat": {"title": "TestChan"}}}

    msg_resp = MagicMock()
    msg_resp.status_code = 200
    msg_resp.json.return_value = {"ok": True, "result": {"message_id": 102, "chat": {"title": "TestChan"}}}

    with patch("requests.post", side_effect=[photo_resp, msg_resp]) as mock_post:
        res = publish_to_telegram(post, bot_token="faketoken", channel_id="@testchan", image_path=str(img_file))
        assert res["success"] is True
        assert res["photo_sent"] is True
        assert res["photo_message_id"] == 101
        assert res["message_id"] == 102
        assert mock_post.call_count == 2
        assert "sendPhoto" in mock_post.call_args_list[0][0][0]
        assert "sendMessage" in mock_post.call_args_list[1][0][0]


def test_telegram_send_photo_failure_still_sends_message(tmp_path):
    img_file = tmp_path / "test.png"
    img_file.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82")

    post = {
        "title": "Test Topic",
        "track": "Systems",
        "summary": "Summary text",
        "key_points": ["Point 1"]
    }

    # Photo upload fails with 400 Bad Request
    photo_resp = MagicMock()
    photo_resp.status_code = 400
    photo_resp.json.return_value = {"ok": False, "description": "Bad Request: wrong file"}

    # Text message succeeds
    msg_resp = MagicMock()
    msg_resp.status_code = 200
    msg_resp.json.return_value = {"ok": True, "result": {"message_id": 202, "chat": {"title": "TestChan"}}}

    with patch("requests.post", side_effect=[photo_resp, msg_resp]) as mock_post:
        res = publish_to_telegram(post, bot_token="faketoken", channel_id="@testchan", image_path=str(img_file))
        assert res["success"] is True
        assert res["photo_sent"] is False
        assert res["message_id"] == 202
        assert mock_post.call_count == 2
