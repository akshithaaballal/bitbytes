"""
Social Image Generator for BitBytes Daily Posts.
Renders an aesthetic 1080x1080 educational infographic card using Pillow.
Ideal for Instagram posts, LinkedIn slides, and Telegram photo previews.
"""

import os
from PIL import Image, ImageDraw, ImageFont

def get_font(size: int, bold: bool = False):
    """Attempts to load a standard system font, falls back to default."""
    font_names = [
        "arialbd.ttf" if bold else "arial.ttf",
        "segoeuib.ttf" if bold else "segoeui.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    ]
    for font_name in font_names:
        try:
            return ImageFont.truetype(font_name, size)
        except IOError:
            continue
    return ImageFont.load_default()


def render_social_card(post: dict, output_path: str = None) -> str:
    """
    Renders a 1080x1080 Instagram-ready card from a post dictionary.
    Returns the absolute path to the generated PNG image.
    """
    width, height = 1080, 1080
    image = Image.new("RGB", (width, height), color="#0F172A") # Dark slate
    draw = ImageDraw.Draw(image)
    
    # 1. Header Bar / Accent Accent Border
    draw.rectangle([(0, 0), (width, 16)], fill="#3B82F6") # Blue top accent
    
    # Fonts
    brand_font = get_font(28, bold=True)
    badge_font = get_font(22, bold=True)
    title_font = get_font(42, bold=True)
    subtitle_font = get_font(24, bold=False)
    body_font = get_font(24, bold=False)
    code_font = get_font(20, bold=False)
    footer_font = get_font(20, bold=False)
    
    # 2. Brand & Track Badge
    draw.text((60, 50), "⚡ BITBYTES DAILY", fill="#60A5FA", font=brand_font)
    
    track = f"[{post.get('track', 'Engineering').upper()}]"
    draw.text((width - 60 - len(track) * 14, 54), track, fill="#94A3B8", font=badge_font)
    
    # Divider line
    draw.line([(60, 100), (width - 60, 100)], fill="#334155", width=2)
    
    # 3. Title & Subtitle
    title = post.get("title", "Daily Topic")
    draw.text((60, 130), title, fill="#F8FAFC", font=title_font)
    
    subtitle = post.get("subtitle", "")
    if subtitle:
        draw.text((60, 195), subtitle, fill="#94A3B8", font=subtitle_font)
        
    # 4. Summary & Key Points
    y_cursor = 250
    draw.text((60, y_cursor), "Key Takeaways:", fill="#38BDF8", font=get_font(24, bold=True))
    y_cursor += 40
    
    for pt in post.get("key_points", [])[:3]:
        # Truncate if line is too long for one slide
        if len(pt) > 78:
            pt = pt[:75] + "..."
        draw.text((80, y_cursor), f"• {pt}", fill="#E2E8F0", font=body_font)
        y_cursor += 38
        
    # 5. Code Box or Tip Box
    code_snippet = post.get("code_snippet")
    if code_snippet:
        y_cursor += 20
        box_top = y_cursor
        box_bottom = box_top + 280
        # Draw code box background
        draw.rounded_rectangle([(60, box_top), (width - 60, box_bottom)], radius=12, fill="#1E293B", outline="#475569", width=1)
        
        # Code box header bar
        draw.rectangle([(60, box_top), (width - 60, box_top + 36)], fill="#334155")
        draw.ellipse([(76, box_top + 12), (88, box_top + 24)], fill="#EF4444")
        draw.ellipse([(96, box_top + 12), (108, box_top + 24)], fill="#F59E0B")
        draw.ellipse([(116, box_top + 12), (128, box_top + 24)], fill="#10B981")
        draw.text((145, box_top + 8), "code_snippet.py", fill="#94A3B8", font=get_font(18, bold=False))
        
        # Code lines
        code_lines = code_snippet.strip().split("\n")[:8]
        code_y = box_top + 50
        for line in code_lines:
            draw.text((80, code_y), line, fill="#A7F3D0", font=code_font)
            code_y += 26
            
        y_cursor = box_bottom + 30
    else:
        y_cursor += 40
        
    # 6. Placement / Interview Tip Banner
    tip = post.get("interview_tip", "")
    if tip:
        tip_box_bottom = y_cursor + 90
        draw.rounded_rectangle([(60, y_cursor), (width - 60, tip_box_bottom)], radius=10, fill="#1E3A8A", outline="#3B82F6", width=1)
        draw.text((80, y_cursor + 12), "🎯 PLACEMENT TIP", fill="#93C5FD", font=get_font(18, bold=True))
        if len(tip) > 85:
            tip = tip[:82] + "..."
        draw.text((80, y_cursor + 42), tip, fill="#FFFFFF", font=get_font(20, bold=False))
        
    # 7. Footer
    draw.line([(60, 1000), (width - 60, 1000)], fill="#334155", width=1)
    draw.text((60, 1025), "bitbytes.dev • Computer Science & Engineering Daily", fill="#64748B", font=footer_font)
    draw.text((width - 320, 1025), "#BTechPlacements #BitBytes", fill="#60A5FA", font=footer_font)
    
    # Save Image
    if not output_path:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_dir = os.path.join(base_dir, "generated_images")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{post.get('id', 'post')}.png")
        
    image.save(output_path, "PNG")
    return output_path
