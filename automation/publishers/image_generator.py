"""
Social Image Generator for BitBytes Daily Posts.
Renders an aesthetic, balanced 1080x1080 educational infographic card using Pillow.
Features:
  - Bundled DejaVuSans & DejaVuSansMono typography with fail-fast loading.
  - Pixel-width text wrapping with word-boundary ellipsis (no mid-sentence cuts).
  - Dynamic layout allocating remaining canvas height to code snippet.
  - Overlap-free header badge and footer domain line.
"""

import os
import re
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


def get_font(size: int, bold: bool = False, mono: bool = False) -> ImageFont.FreeTypeFont:
    """
    Loads font from bundled automation/assets/fonts/ or system directories.
    Fails loudly if font cannot be loaded (never silently falls back to tiny load_default).
    """
    assets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "fonts")
    if mono:
        preferred = ["DejaVuSansMono.ttf", "Consolas.ttf", "cour.ttf"]
    elif bold:
        preferred = ["DejaVuSans-Bold.ttf", "arialbd.ttf", "segoeuib.ttf"]
    else:
        preferred = ["DejaVuSans.ttf", "arial.ttf", "segoeui.ttf"]

    candidates = []
    # 1. Bundled assets directory
    for name in preferred:
        candidates.append(os.path.join(assets_dir, name))

    # 2. Linux system paths
    if mono:
        candidates.append("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf")
    elif bold:
        candidates.append("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    else:
        candidates.append("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")

    # 3. Windows system paths
    windir = os.environ.get("WINDIR", "C:\\Windows")
    for name in preferred:
        candidates.append(os.path.join(windir, "Fonts", name))

    # 4. Bare font names for Pillow font manager
    candidates.extend(preferred)

    for path in candidates:
        if path and (os.path.exists(path) or not os.path.isabs(path)):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue

    raise RuntimeError(
        f"Could not load TrueType font (size={size}, bold={bold}, mono={mono}). "
        f"Font files are missing from automation/assets/fonts/ and system fonts."
    )


def wrap_text_by_pixels(text: str, font: ImageFont.FreeTypeFont, max_width: float) -> list[str]:
    """Wraps text into lines such that each line's rendered width does not exceed max_width."""
    words = text.split()
    if not words:
        return []
    lines = []
    current_line = []
    for word in words:
        candidate = " ".join(current_line + [word])
        if font.getlength(candidate) <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
                current_line = [word]
            else:
                lines.append(word)
                current_line = []
    if current_line:
        lines.append(" ".join(current_line))
    return lines


def truncate_to_width(text: str, font: ImageFont.FreeTypeFont, max_width: float) -> str:
    """Truncates text at a word boundary, appending '…' so it fits within max_width."""
    if font.getlength(text) <= max_width:
        return text
    words = text.split()
    while words and font.getlength(" ".join(words) + "…") > max_width:
        words.pop()
    return (" ".join(words) + "…") if words else "…"


def render_social_card(post: dict, output_path: str = None) -> str:
    """
    Renders an aesthetic, balanced 1080x1080 card from a post dictionary.
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
    code_font = get_font(18, mono=True)
    footer_font = get_font(18, bold=False)

    # 2. Brand & Track Badge (Right-aligned using font.getlength)
    draw.text((60, 45), "BITBYTES NOTEBOOK", fill="#5B8DEF", font=brand_font)

    raw_track = post.get("track", "Engineering")
    track = f"[{drop_emojis(raw_track).upper()}]"
    badge_w = badge_font.getlength(track)
    draw.text((width - 60 - badge_w, 48), track, fill="#8A93A6", font=badge_font)

    draw.line([(60, 90), (width - 60, 90)], fill="#334155", width=1)

    # 3. Title & Subtitle with 8px explicit gap
    raw_title = drop_emojis(post.get("title", "Technical Concept"))
    max_title_w = width - 120
    title_lines = wrap_text_by_pixels(raw_title, title_font, max_title_w)
    if len(title_lines) > 2:
        title_lines = [title_lines[0], truncate_to_width(title_lines[1] + " " + title_lines[2], title_font, max_title_w)]

    y_cursor = 115
    for t_line in title_lines:
        draw.text((60, y_cursor), t_line, fill="#F8FAFC", font=title_font)
        y_cursor += 46

    raw_sub = drop_emojis(post.get("subtitle", ""))
    if raw_sub:
        y_cursor += 8  # 8px spacing between title and subtitle
        sub_lines = wrap_text_by_pixels(raw_sub, subtitle_font, max_title_w)
        if len(sub_lines) > 2:
            sub_lines = [sub_lines[0], truncate_to_width(sub_lines[1] + " " + sub_lines[2], subtitle_font, max_title_w)]
        for s_line in sub_lines:
            draw.text((60, y_cursor), s_line, fill="#8A93A6", font=subtitle_font)
            y_cursor += 30

    y_cursor += 20

    # 4. Key Mechanics (allowing up to 4 key points, wrapped with word-boundary ellipsis)
    key_points = post.get("key_points", [])
    has_code = bool(post.get("code_snippet"))
    max_pts = 4 if not has_code else 3

    if key_points:
        draw.text((60, y_cursor), "Key Mechanics:", fill="#38BDF8", font=get_font(22, bold=True))
        y_cursor += 34

        pt_max_w = width - 120 - 25  # Hanging indent for bullet
        for pt in key_points[:max_pts]:
            clean_pt = drop_emojis(pt)
            wrapped_pt = wrap_text_by_pixels(clean_pt, body_font, pt_max_w)
            if not wrapped_pt:
                continue

            # Allow up to 2 wrapped lines per bullet without clipping mid-sentence
            if len(wrapped_pt) > 2:
                truncated_second = truncate_to_width(wrapped_pt[1] + " " + wrapped_pt[2], body_font, pt_max_w)
                wrapped_pt = [wrapped_pt[0], truncated_second]

            draw.text((80, y_cursor), f"- {wrapped_pt[0]}", fill="#E2E8F0", font=body_font)
            y_cursor += 30
            for extra in wrapped_pt[1:]:
                draw.text((96, y_cursor), extra, fill="#E2E8F0", font=body_font)
                y_cursor += 30

    # 5. Code Box (dynamic height filling remaining space down to footer)
    code_snippet = post.get("code_snippet")
    if code_snippet:
        box_top = y_cursor + 10
        box_bottom = 970  # Stretches down to fill canvas, leaving 20px before footer line at 990
        available_height = box_bottom - box_top

        # Only render box if there is sufficient vertical space
        if available_height >= 120:
            draw.rectangle([(60, box_top), (width - 60, box_bottom)], fill="#1E293B", outline="#475569", width=1)
            draw.rectangle([(60, box_top), (width - 60, box_top + 32)], fill="#334155")
            draw.text((80, box_top + 6), "implementation.py", fill="#8A93A6", font=get_font(16, bold=False))

            # Code lines (preserving indentation, monospace font, showing … if clipped)
            raw_lines = drop_emojis(code_snippet).rstrip().split("\n")
            max_code_w = width - 120 - 40
            line_h = 24
            code_content_h = box_bottom - (box_top + 45)
            max_lines = max(1, code_content_h // line_h)

            display_lines = raw_lines[:max_lines]
            has_more = len(raw_lines) > max_lines

            code_y = box_top + 45
            for idx, line in enumerate(display_lines):
                # If last line and there are more lines, show ellipsis
                if idx == max_lines - 1 and has_more:
                    draw.text((80, code_y), "...", fill="#64748B", font=code_font)
                    break

                # Preserve leading whitespace, clip line with … if wider than box
                if code_font.getlength(line) > max_code_w:
                    clipped = line
                    while len(clipped) > 1 and code_font.getlength(clipped + "…") > max_code_w:
                        clipped = clipped[:-1]
                    draw.text((80, code_y), clipped + "…", fill="#A7F3D0", font=code_font)
                else:
                    draw.text((80, code_y), line, fill="#A7F3D0", font=code_font)
                code_y += line_h

    # 6. Footer (overlap-proof)
    draw.line([(60, 990), (width - 60, 990)], fill="#334155", width=1)
    right_text = "bitbytes.dev • telegram @csbites"
    right_w = footer_font.getlength(right_text)
    right_x = width - 60 - right_w
    draw.text((right_x, 1015), right_text, fill="#5B8DEF", font=footer_font)

    source = post.get("source") or {}
    domain = source.get("domain") or "bitbytes.dev"
    max_left_w = right_x - 60 - 24  # Ensure at least 24px gap between left and right footer text
    left_text = truncate_to_width(f"Source: {domain}", footer_font, max_left_w)
    draw.text((60, 1015), left_text, fill="#8A93A6", font=footer_font)

    if not output_path:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_dir = os.path.join(base_dir, "generated_images")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{post.get('id', 'post')}.png")

    image.save(output_path, "PNG")
    return output_path
