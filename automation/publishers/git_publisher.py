"""
Git & GitHub Publisher for BitBytes Daily Engineering Posts.
Generates structured Markdown files, updates the README knowledge index,
and stages/commits them locally or for GitHub Actions.
"""

import os
from datetime import datetime

def format_github_markdown(post: dict) -> str:
    """Formats the post into a full GitHub Flavored Markdown document."""
    track = post.get("track", "Engineering")
    day = post.get("day", "")
    title = post.get("title", "")
    subtitle = post.get("subtitle", "")
    summary = post.get("summary", "")
    
    md_lines = [
        f"# {title}",
        f"> **Track:** {track} | **Day:** {day} | **Date:** {datetime.now().strftime('%Y-%m-%d')}\n",
        f"**{subtitle}**\n" if subtitle else "",
        f"## 📌 Overview\n{summary}\n",
        "## 💡 Key Highlights"
    ]
    
    for point in post.get("key_points", []):
        md_lines.append(f"- {point}")
        
    if post.get("code_snippet"):
        code = post.get("code_snippet")
        lang = "python" if "def " in code or "import " in code else "sql" if "SELECT" in code else ""
        md_lines.append(f"\n## 💻 Code Example\n```{lang}\n{code}\n```")
        
    complexity = post.get("complexity", {})
    if complexity:
        md_lines.append("\n## ⚡ Complexity & Performance")
        for k, v in complexity.items():
            k_fmt = k.replace("_", " ").title()
            md_lines.append(f"- **{k_fmt}:** `{v}`")
            
    if post.get("interview_tip"):
        tip = post.get("interview_tip")
        md_lines.append(f"\n## 🎯 Interview Tip\n> [!TIP]\n> {tip}")
        
    tags = " ".join([f"`{t}`" for t in post.get("tags", [])])
    if tags:
        md_lines.append(f"\n---\n**Tags:** {tags}")
        
    return "\n".join(md_lines) + "\n"


def publish_to_git(post: dict, base_dir: str = None) -> dict:
    """
    Writes the post as a Markdown file in `archive/` directory
    and appends an entry to the Knowledge Base Index in `INDEX.md`.
    """
    base_dir = base_dir or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    archive_dir = os.path.join(base_dir, "archive")
    os.makedirs(archive_dir, exist_ok=True)
    
    now = datetime.now()
    timestamp_str = now.strftime("%Y-%m-%d %H:%M")
    date_code = now.strftime("%Y-%m-%d_%H%M")
    post_id = post.get("id", "post")
    filename = f"{date_code}_{post_id}.md"
    file_path = os.path.join(archive_dir, filename)
    
    content = format_github_markdown(post)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    # Update INDEX.md
    index_path = os.path.join(base_dir, "INDEX.md")
    index_entry = f"| {timestamp_str} | **{post.get('day', '')}** | {post.get('track', '')} | [{post.get('title', '')}](archive/{filename}) |\n"
    
    if not os.path.exists(index_path):
        header = "# 📚 BitBytes Engineering Knowledge Archive\n\n| Timestamp | Track Day | Track | Topic |\n| :--- | :--- | :--- | :--- |\n"
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(header + index_entry)
    else:
        with open(index_path, "a", encoding="utf-8") as f:
            f.write(index_entry)
            
    return {
        "success": True,
        "archive_file": file_path,
        "index_file": index_path,
        "relative_path": f"archive/{filename}"
    }
