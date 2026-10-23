"""
Social Image Generator for BitBytes Daily Posts.
Renders an aesthetic 1080x1080 educational infographic card using Pillow.
Wraps text with textwrap, drops emoji glyphs, and displays Source: <domain> in footer.
"""

import os
import re
import textwrap
from PIL import Image, ImageDraw, ImageFont


def drop_emojis(text: str) -> str:
    """Removes emoji glyphs that fail rendering in basic TTF fonts."""
    if not text:
        return ""
    # Strip high surrogate / emoji codepoints
    cleaned = re.sub(r"[\U00010000-\U0010ffff]", "", text)
    # Strip common symbol emoji blocks
    cleaned = re.sub(r"[\u2600-\u27bf\u2300-\u23ff\u2b50]", "", cleaned)
    return cleaned.strip()


def get_font(size: int, bold: bool = False):
    """Attempts to load a standard system font or bundled font, falls back to default."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    bundled_font = os.path.join(current_dir, "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf")

    font_names = [
        bundled_font,
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "arialbd.ttf" if bold else "arial.ttf",
        "segoeuib.ttf" if bold else "segoeui.ttf"
    ]
    for font_name in font_names:
        try:
            return ImageFont.truetype(font_name, size)
        except (IOError, OSError):
            continue
    return ImageFont.load_default()


def render_social_card(post: dict, output_path: str = None) -> str:
    """
    Renders a 1080x1080 card from a post dictionary.
    Returns the absolute path to the generated PNG image.
    """
    width, height = 1080, 1080
    image = Image.new("RGB", (width, height), color="#0F172A")
    draw = ImageDraw.Draw(image)

    # 1. Top Accent Bar
    draw.rectangle([(0, 0), (width, 14)], fill="#2F6FEB")

    brand_font = get_font(26, bold=True)
    badge_font = get_font(20, bold=True)
    title_font = get_font(38, bold=True)
    subtitle_font = get_font(22, bold=False)
    body_font = get_font(22, bold=False)
    code_font = get_font(18, bold=False)
    footer_font = get_font(18, bold=False)

    # 2. Brand & Track Badge
    draw.text((60, 45), "BITBYTES NOTEBOOK", fill="#5B8DEF", font=brand_font)

    raw_track = post.get("track", "Engineering")
    track = f"[{drop_emojis(raw_track).upper()}]"
    draw.text((width - 60 - len(track) * 12, 48), track, fill="#8A93A6", font=badge_font)

    draw.line([(60, 90), (width - 60, 90)], fill="#334155", width=1)

    # 3. Title & Subtitle
    raw_title = drop_emojis(post.get("title", "Technical Concept"))
    title_lines = textwrap.wrap(raw_title, width=38)[:2]
    y_cursor = 115
    for t_line in title_lines:
        draw.text((60, y_cursor), t_line, fill="#F8FAFC", font=title_font)
        y_cursor += 46

    raw_sub = drop_emojis(post.get("subtitle", ""))
    if raw_sub:
        sub_lines = textwrap.wrap(raw_sub, width=65)[:2]
        for s_line in sub_lines:
            draw.text((60, y_cursor), s_line, fill="#8A93A6", font=subtitle_font)
            y_cursor += 28

    y_cursor += 15

    # 4. Key Takeaways
    draw.text((60, y_cursor), "Key Mechanics:", fill="#38BDF8", font=get_font(22, bold=True))
    y_cursor += 34

    for pt in post.get("key_points", [])[:3]:
        clean_pt = drop_emojis(pt)
        wrapped_pt = textwrap.wrap(clean_pt, width=68)
        if wrapped_pt:
            draw.text((80, y_cursor), f"- {wrapped_pt[0]}", fill="#E2E8F0", font=body_font)
            y_cursor += 30
            for extra in wrapped_pt[1:2]:
                draw.text((95, y_cursor), extra, fill="#E2E8F0", font=body_font)
                y_cursor += 30

    y_cursor += 10

    # 5. Code Box
    code_snippet = post.get("code_snippet")
    if code_snippet:
        box_top = y_cursor
        box_bottom = min(box_top + 260, 920)
        draw.rectangle([(60, box_top), (width - 60, box_bottom)], fill="#1E293B", outline="#475569", width=1)
        draw.rectangle([(60, box_top), (width - 60, box_top + 32)], fill="#334155")
        draw.text((80, box_top + 6), "implementation.py", fill="#8A93A6", font=get_font(16, bold=False))

        code_lines = drop_emojis(code_snippet).strip().split("\n")[:8]
        code_y = box_top + 45
        for line in code_lines:
            draw.text((80, code_y), line[:75], fill="#A7F3D0", font=code_font)
            code_y += 24

    # 6. Footer: Source: <domain>
    source = post.get("source") or {}
    domain = source.get("domain") or "bitbytes.dev"
    draw.line([(60, 990), (width - 60, 990)], fill="#334155", width=1)
    draw.text((60, 1015), f"Source: {domain}", fill="#8A93A6", font=footer_font)
    draw.text((width - 320, 1015), "bitbytes.dev • telegram @csbites", fill="#5B8DEF", font=footer_font)

    if not output_path:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_dir = os.path.join(base_dir, "generated_images")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{post.get('id', 'post')}.png")

    image.save(output_path, "PNG")
    return output_path
