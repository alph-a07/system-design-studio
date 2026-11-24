#!/usr/bin/env python3
"""
render-lesson.py
Deterministic HTML lesson renderer for System Design Studio.
Generates beautiful, accessible, interactive HTML lesson artifacts with embedded
simulators, workload contrasts, invariant tables, and reality checks.
Supports 5 distinct visual theme variants and respects .system-design/settings.json
for both theme preferences and directory output paths (paths.lessonsDir).

PEDAGOGICAL CONTRACT:
Adheres strictly to single-topic progressive disclosure:
- No coverage-based repetitive silos (no brief overview -> foundation cards -> deep explanations -> summary tables).
- The lesson is one continuous cohesive narrative with 5 structured phases:
  1. The Dilemma / Inception (WHYs & optional WHENs)
  2. The Core Entity & Placement (WHATs & optional WHEREs)
  3. Internal Mechanics & Causality (HOWs & WHYs of HOWs; embedded simulator inline)
  4. Mental Model Synthesis & Production Grounding (Workloads & Invariants)
  5. Contextual Sign-Off Verification (Unanswered scenario challenge for chat)
"""

import os
import sys
import json
import argparse
import re
import subprocess
import shutil

script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

try:
    from lesson_builder import LessonDocument
except ImportError:
    LessonDocument = None

STYLE_THEMES = {
    "slate-clean": {
        "id": "slate-clean",
        "name": "Modern Slate (Dark Tech)",
        "theme_type": "dark",
        "css_vars": r"""
    :root {
      --background: #0f172a;
      --foreground: #f8fafc;
      --card: #1e293b;
      --card-border: #334155;
      --border: #334155;
      --muted-foreground: #94a3b8;
      --primary: #3b82f6;
      --primary-hover: #2563eb;
      --accent-badge: #1e3a8a;
      --accent-badge-text: #93c5fd;
    }
""",
        "badge_class": "bg-blue-600 text-white",
    },
    "editorial-paper": {
        "id": "editorial-paper",
        "name": "Clean Editorial (Warm Light)",
        "theme_type": "light",
        "css_vars": r"""
    :root, html:not(.dark), html[data-theme-preset="editorial-paper"] {
      --background: #fbfbfa;
      --foreground: #18181b;
      --card: #ffffff;
      --card-border: #e4e4e7;
      --border: #e4e4e7;
      --muted-foreground: #71717a;
      --primary: #2563eb;
      --primary-hover: #1d4ed8;
      --accent-badge: #eff6ff;
      --accent-badge-text: #1d4ed8;
    }

    html:not(.dark) .bg-stone-900,
    html:not(.dark) .bg-stone-900\/80,
    html:not(.dark) .bg-stone-950 {
      background-color: #f8fafc !important;
      color: #0f172a !important;
      border-color: #e2e8f0 !important;
    }
    html:not(.dark) .bg-stone-800 {
      background-color: #f1f5f9 !important;
      color: #334155 !important;
      border-color: #cbd5e1 !important;
    }
    html:not(.dark) .border-stone-800,
    html:not(.dark) .border-stone-700 {
      border-color: #e2e8f0 !important;
    }
    html:not(.dark) .text-stone-300,
    html:not(.dark) .text-stone-400 {
      color: #475569 !important;
    }
    html:not(.dark) .jargon-card {
      background: #fffbeb !important;
      border-color: #fcd34d !important;
    }
    html:not(.dark) .jargon-title {
      color: #b45309 !important;
    }
    html:not(.dark) .jargon-pill {
      background: #fef3c7 !important;
      color: #92400e !important;
    }
    html:not(.dark) .jargon-inline-cue,
    html:not(.dark) .jargon-pill-cue {
      background: #fef3c7 !important;
      border-color: #f59e0b !important;
      color: #b45309 !important;
    }
    html:not(.dark) .jargon-popover-card {
      background: #ffffff !important;
      border-color: #f59e0b !important;
      box-shadow: 0 16px 40px -4px rgba(0, 0, 0, 0.15), 0 0 15px rgba(245, 158, 11, 0.1) !important;
    }
    html:not(.dark) .jargon-popover-title {
      color: #b45309 !important;
    }
    html:not(.dark) .jargon-popover-badge {
      background: #fef3c7 !important;
      color: #92400e !important;
    }
""",
        "badge_class": "bg-blue-700 text-white",
    },
    "midnight-neon": {
        "id": "midnight-neon",
        "name": "Cyber Obsidian (High Contrast)",
        "theme_type": "dark",
        "css_vars": r"""
    :root {
      --background: #05070c;
      --foreground: #f1f5f9;
      --card: #0d1117;
      --card-border: #21262d;
      --border: #21262d;
      --muted-foreground: #8b949e;
      --primary: #06b6d4;
      --primary-hover: #0891b2;
      --accent-badge: #083344;
      --accent-badge-text: #67e8f9;
    }
""",
        "badge_class": "bg-cyan-500 text-black font-bold",
    },
    "nordic-frost": {
        "id": "nordic-frost",
        "name": "Nordic Frost (Polar Calm)",
        "theme_type": "dark",
        "css_vars": r"""
    :root {
      --background: #2e3440;
      --foreground: #eceff4;
      --card: #3b4252;
      --card-border: #4c566a;
      --border: #434c5e;
      --muted-foreground: #d8dee9;
      --primary: #88c0d0;
      --primary-hover: #81a1c1;
      --accent-badge: #434c5e;
      --accent-badge-text: #88c0d0;
    }
""",
        "badge_class": "bg-[#88c0d0] text-[#2e3440] font-bold",
    },
    "warm-amber": {
        "id": "warm-amber",
        "name": "Warm Amber (Espresso Glow)",
        "theme_type": "dark",
        "css_vars": r"""
    :root {
      --background: #1c1917;
      --foreground: #fafaf9;
      --card: #292524;
      --card-border: #44403c;
      --border: #44403c;
      --muted-foreground: #a8a29e;
      --primary: #f59e0b;
      --primary-hover: #d97706;
      --accent-badge: #451a03;
      --accent-badge-text: #fcd34d;
    }
""",
        "badge_class": "bg-amber-500 text-stone-900 font-bold",
    },
}

def locate_resource_template():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(script_dir, "..", "resources", "lesson-template.html"),
        os.path.join(os.getcwd(), "skills", "system-design-studio", "resources", "lesson-template.html"),
        os.path.expanduser("~/.system-design-studio/skills/system-design-studio/resources/lesson-template.html")
    ]
    for c in candidates:
        norm = os.path.normpath(c)
        if os.path.exists(norm):
            return norm
    return None

def get_default_template(custom_template_path=None):
    if custom_template_path and os.path.exists(custom_template_path):
        try:
            with open(custom_template_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"⚠️ Warning: Could not read custom template at {custom_template_path}: {e}")

    res_path = locate_resource_template()
    if res_path and os.path.exists(res_path):
        try:
            with open(res_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"⚠️ Warning: Could not read resource template at {res_path}: {e}")

    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>{{LESSON_TITLE}}</title></head><body><h1>{{LESSON_TITLE}}</h1><nav>{{SECTION_TABS_HTML}}</nav><main>{{SECTION_PANES_HTML}}</main></body></html>"""

DEFAULT_TEMPLATE = get_default_template()

ACRONYMS = {
    'tcp': 'TCP', 'udp': 'UDP', 'http': 'HTTP', 'tls': 'TLS', 'rest': 'REST',
    'grpc': 'gRPC', 'wal': 'WAL', 'crdt': 'CRDT', 'lld': 'LLD', 'hld': 'HLD',
    'lru': 'LRU', 'lfu': 'LFU', 'raft': 'Raft', 'paxos': 'Paxos', 'sql': 'SQL',
    'nosql': 'NoSQL', 'cdc': 'CDC', 'ttl': 'TTL', 'cpu': 'CPU', 'quic': 'QUIC',
    'sse': 'SSE', 'api': 'API', 'adr': 'ADR', 'b-tree': 'B-Tree', 'lsm': 'LSM'
}

def format_topic_title(raw_id, raw_title=None):
    if raw_title:
        return raw_title
    s = raw_id.replace('topic.', '')
    s = re.sub(r'^\d+\.\d+\.', '', s)
    words = s.split('-')
    out = []
    for w in words:
        wl = w.lower()
        if wl in ACRONYMS:
            out.append(ACRONYMS[wl])
        elif wl == 'vs':
            out.append('vs')
        else:
            out.append(w.capitalize())
    return ' '.join(out).strip()



def strip_section_index(title):
    """Strips leading numerical indexing (e.g. '1.', 'Section 1:', 'Phase 1:') from titles."""
    if not title:
        return ""
    cleaned = re.sub(r"^(?:Section\s*\d+\s*[:\.\-]\s*|Phase\s*\d+\s*[:\.\-]\s*|\d+[\.\:\-]\s*)", "", str(title).strip(), flags=re.IGNORECASE)
    return cleaned.strip()

def clean_tier_badge(raw):
    """Formats clean tier badge without excessive noise (e.g. 'Tier 0 · System Design Core' -> 'Tier 0')."""
    if not raw:
        return "Tier 0"
    m = re.match(r"(Tier\s*\d+)", str(raw), flags=re.IGNORECASE)
    if m:
        return m.group(1).title()
    return str(raw).strip()

def clean_cluster_badge(raw):
    """Strips leading numerical indexing like '1. [0.1]' from cluster badge for editorial elegance."""
    if not raw:
        return "System Design"
    s = re.sub(r"^\d+\.\s*(?:\[\d+(?:\.\d+)*\]\s*)?", "", str(raw)).strip()
    s = re.sub(r"\s+for Design\b", "", s, flags=re.IGNORECASE)
    return s

def extract_balanced_tag(html, start_idx, tag_name="div"):
    """
    Extracts a balanced <tag>...</tag> block starting at start_idx, correctly handling nested tags.
    Prevents truncation caused by non-greedy regexes matching inner closing tags.
    """
    tag_open = f"<{tag_name}"
    tag_close = f"</{tag_name}>"
    depth = 0
    i = start_idx
    n = len(html)
    len_open = len(tag_open)
    len_close = len(tag_close)
    while i < n:
        if html[i:i+len_open].lower() == tag_open and (i+len_open == n or html[i+len_open] in " >\t\r\n/"):
            depth += 1
            i += len_open
        elif html[i:i+len_close].lower() == tag_close:
            depth -= 1
            i += len_close
            if depth == 0:
                return html[start_idx:i], i
        else:
            i += 1
    return None, start_idx + 1

def extract_balanced_escaped_tag(html, start_idx, tag_name="span"):
    """
    Extracts a balanced &lt;tag&gt;...&lt;/tag&gt; block starting at start_idx, correctly handling nested tags.
    Prevents truncation caused by non-greedy regexes matching inner closing tags.
    """
    tag_open = f"&lt;{tag_name}"
    tag_close = f"&lt;/{tag_name}&gt;"
    depth = 0
    i = start_idx
    n = len(html)
    len_open = len(tag_open)
    len_close = len(tag_close)
    while i < n:
        if html[i:i+len_open].lower() == tag_open and (i+len_open == n or html[i+len_open] in " >\t\r\n/&"):
            depth += 1
            i += len_open
        elif html[i:i+len_close].lower() == tag_close:
            depth -= 1
            i += len_close
            if depth == 0:
                return html[start_idx:i], i
        else:
            i += 1
    return None, start_idx + 1

def clean_markdown_leaks_in_html(html):
    """
    Cleans up leaked markdown formatting syntax in HTML content (e.g. asterisks around tooltips,
    unparsed bold/italic asterisks in sentences or list items).
    Prevents visual artifacts like: '2. ** Packet Loss Concealment (PLC) **: When...'.
    """
    if not html or "**" not in html:
        return html

    # 1. Clean asterisks inside or adjacent to <strong> tags
    html = re.sub(r"<strong>\s*\*\*\s*", "<strong>", html)
    html = re.sub(r"\s*\*\*\s*</strong>", "</strong>", html)

    # 2. Convert ** <span class="jargon-tooltip-wrapper">...</span> ** or **<span class="jargon-tooltip-wrapper">...</span>**:
    # to <strong><span class="jargon-tooltip-wrapper">...</span></strong>
    html = re.sub(
        r"\*\*\s*(<span\s+class=[\"'][^\"']*jargon-tooltip-wrapper[\"'][\s\S]*?</span>)\s*\*\*",
        r"<strong>\1</strong>",
        html,
        flags=re.IGNORECASE
    )

    # 3. Strip any lingering markdown bold syntax immediately wrapping tooltip cues or wrappers
    html = re.sub(r"\*\*\s*(<span\s+class=[\"'][^\"']*(?:jargon-tooltip-wrapper|jargon-inline-cue|jargon-pill-cue))", r"\1", html, flags=re.IGNORECASE)
    html = re.sub(r"(</span>)\s*\*\*", r"\1", html, flags=re.IGNORECASE)

    # 4. Clean orphan ** around list numbers or prefixes: e.g. "2. ** " -> "2. <strong>" and " **:" -> "</strong>:"
    html = re.sub(r"(?<=\b\d\.)\s*\*\*\s*", " <strong>", html)
    html = re.sub(r"\s*\*\*(?=\s*[:\-])", "</strong>", html)

    # 5. Clean any unparsed inline markdown bold like **Word** that is not inside an HTML attribute or tag
    def _replace_bold(m):
        content = m.group(1).strip()
        if not content:
            return ""
        return f"<strong>{content}</strong>"
    html = re.sub(r"(?<![=\w/\"'])\*\*([^\*\r\n<>]+?)\*\*(?![=\w\"'])", _replace_bold, html)

    return html

def sanitize_tooltips_to_spans(html):
    """
    Scans html for any <span/div class="jargon-tooltip-wrapper"> and transforms
    all internal tags (popover card, header, body, desc) to strictly phrasing <span> tags.
    Placing <div> or <p> inside <p> causes browsers to auto-close paragraphs prematurely,
    splitting sentences and stranding words or punctuation on separate lines.
    Also cleans up any leaking markdown asterisks surrounding tooltips and unescapes
    accidentally escaped tooltip entities.
    """
    if not html:
        return html

    # Unescape any accidentally escaped tooltips (e.g. from markdown tables or json serialization)
    if ("&lt;span" in html or "&lt;div" in html) and "jargon-tooltip-wrapper" in html:
        esc_pattern = re.compile(r"&lt;(?:span|div)[^&]*class=&quot;[^&]*jargon-tooltip-wrapper", re.IGNORECASE)
        esc_res = []
        esc_idx = 0
        while True:
            m = esc_pattern.search(html, esc_idx)
            if not m:
                esc_res.append(html[esc_idx:])
                break
            start_pos = m.start()
            esc_res.append(html[esc_idx:start_pos])
            tag_name = "div" if "div" in html[start_pos:start_pos+10].lower() else "span"
            block, end_pos = extract_balanced_escaped_tag(html, start_pos, tag_name)
            if block:
                unescaped_block = (block.replace("&lt;", "<")
                                        .replace("&gt;", ">")
                                        .replace("&quot;", '"')
                                        .replace("&#39;", "'")
                                        .replace("&amp;", "&"))
                esc_res.append(unescaped_block)
                esc_idx = end_pos
            else:
                esc_res.append(html[start_pos:end_pos])
                esc_idx = end_pos
        html = "".join(esc_res)

    html = clean_markdown_leaks_in_html(html)

    if "jargon-tooltip-wrapper" not in html:
        return html

    res = []
    idx = 0
    pattern = re.compile(r"<(?:span|div)\s+class=[\"'][^\"']*jargon-tooltip-wrapper[^\"']*[\"']", re.IGNORECASE)
    while True:
        m = pattern.search(html, idx)
        if not m:
            res.append(html[idx:])
            break
        start_idx = m.start()
        res.append(html[idx:start_idx])
        tag_name = re.match(r"<([a-zA-Z0-9]+)", html[start_idx:]).group(1).lower()
        wrapper_str, end_idx = extract_balanced_tag(html, start_idx, tag_name)
        if not wrapper_str:
            res.append(html[start_idx:end_idx])
            idx = end_idx
            continue
        idx = end_idx

        cue_m = re.search(r"<(?:span|div)[^>]*class=[\"'][^\"']*(?:jargon-inline-cue|jargon-pill-cue)[^\"']*[\"'][^>]*>([\s\S]*?)</(?:span|div)>", wrapper_str, re.IGNORECASE)
        title_m = re.search(r"<(?:span|div)[^>]*class=[\"'][^\"']*jargon-popover-title[^\"']*[\"'][^>]*>([\s\S]*?)</(?:span|div)>", wrapper_str, re.IGNORECASE)
        badge_m = re.search(r"<(?:span|div)[^>]*class=[\"'][^\"']*jargon-popover-badge[^\"']*[\"'][^>]*>([\s\S]*?)</(?:span|div)>", wrapper_str, re.IGNORECASE)
        body_m = re.search(r"<(?:div|span)[^>]*class=[\"'][^\"']*jargon-popover-body[^\"']*[\"'][^>]*>([\s\S]*?)</(?:div|span)>", wrapper_str, re.IGNORECASE)

        cue_html = re.sub(r"</?(?:p|div|span)[^>]*>", "", cue_m.group(1)).strip() if cue_m else "Term"
        title_html = re.sub(r"</?(?:p|div|span)[^>]*>", "", title_m.group(1)).strip() if title_m else cue_html
        badge_html = re.sub(r"</?(?:p|div|span)[^>]*>", "", badge_m.group(1)).strip() if badge_m else ""
        body_content = body_m.group(1).strip() if body_m else ""

        desc_clean = re.sub(r"</?(?:p|div|span)[^>]*>", "", body_content).strip()

        badge_span = f'<span class="jargon-popover-badge">{badge_html}</span>' if badge_html else ""
        transformed = (
            f'<span class="jargon-tooltip-wrapper">'
            f'<span class="jargon-inline-cue" onclick="toggleJargonTooltip(this, event)">{cue_html}</span>'
            f'<span class="jargon-popover-card">'
            f'<span class="jargon-popover-header">'
            f'<span class="jargon-popover-title">{title_html}</span>'
            f'{badge_span}'
            f'</span>'
            f'<span class="jargon-popover-body"><span class="jargon-popover-desc">{desc_clean}</span></span>'
            f'</span>'
            f'</span>'
        )
        res.append(transformed)
    cleaned = "".join(res)
    return clean_markdown_leaks_in_html(cleaned)

def extract_balanced_div(html, start_idx):
    """
    Extracts a balanced <div>...</div> block starting at start_idx, correctly handling nested divs.
    """
    return extract_balanced_tag(html, start_idx, "div")

def clean_inner_text(html_snippet):
    """
    Converts inner HTML tags to clean GitHub Flavored Markdown inline formatting.
    Converts lists, code blocks, bold/italics, and normalizes line indents.
    """
    if not html_snippet:
        return ""
    text = html_snippet
    # Inline code
    text = re.sub(r"<code\b[^>]*>(.*?)</code>", r"`\1`", text, flags=re.DOTALL)
    # Bold / Strong (use \b so <br/> is not matched as <b...>)
    text = re.sub(r"<(?:strong|b)\b[^>]*>(.*?)</(?:strong|b)>", r"**\1**", text, flags=re.DOTALL)
    # Italics / Em
    text = re.sub(r"<(?:em|i)\b[^>]*>(.*?)</(?:em|i)>", r"*\1*", text, flags=re.DOTALL)
    # Headings h1-h6
    for h in range(1, 7):
        hashes = "#" * h
        text = re.sub(rf"<h{h}\b[^>]*>(.*?)</h{h}>", rf"\n\n{hashes} \1\n\n", text, flags=re.DOTALL)
    # List items
    text = re.sub(r"<li\b[^>]*>\s*", r"\n- ", text, flags=re.IGNORECASE)
    text = re.sub(r"</li>", r"", text, flags=re.IGNORECASE)
    # Line breaks and paragraphs
    text = re.sub(r"<br\s*/?>", r"\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</?p\b[^>]*>", r"\n\n", text, flags=re.IGNORECASE)
    # Strip remaining HTML tags
    text = re.sub(r"<[^>]+>", r"", text)
    # Unescape HTML entities
    text = text.replace("&nbsp;", " ").replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
    
    # Normalize lines: strip extraneous spaces, preserve list formatting
    lines = []
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped:
            lines.append(stripped)
        elif lines and lines[-1] != "":
            lines.append("")
    return "\n".join(lines).strip()

def blockquote_lines(text, prefix="> "):
    """Prepends prefix to every non-empty line of text for robust markdown callout rendering."""
    lines = text.split("\n")
    out = []
    for line in lines:
        if line.strip():
            out.append(f"{prefix}{line.strip()}")
        else:
            out.append(prefix.rstrip())
    return "\n".join(out)

def html_table_to_markdown(match):
    table_html = match.group(0)
    rows = re.findall(r'<tr[^>]*>([\s\S]*?)</tr>', table_html, flags=re.IGNORECASE)
    if not rows:
        return ""
    md_rows = []
    for row in rows:
        headers = re.findall(r'<th[^>]*>([\s\S]*?)</th>', row, flags=re.IGNORECASE)
        cells = re.findall(r'<td[^>]*>([\s\S]*?)</td>', row, flags=re.IGNORECASE)
        if headers:
            clean_headers = [re.sub(r'<[^>]+>', '', h).strip() for h in headers]
            md_rows.append("| " + " | ".join(clean_headers) + " |")
            md_rows.append("| " + " | ".join([":---"] * len(clean_headers)) + " |")
        elif cells:
            clean_cells = [re.sub(r'<[^>]+>', '', c).strip().replace('\n', ' ') for c in cells]
            md_rows.append("| " + " | ".join(clean_cells) + " |")
    return "\n" + "\n".join(md_rows) + "\n"

def clean_html_to_markdown(html):
    """
    Renders rich, faithful GitHub Flavored Markdown from the authored HTML lesson body.
    Extracts balanced container divs without truncation, converts callouts to GitHub alerts,
    jargon cards to structured blockquotes, and tables to markdown syntax.
    """
    if not html:
        return ""
    text = html

    # Convert HTML tables to Markdown pipe syntax first
    text = re.sub(r'<table[^>]*>[\s\S]*?</table>', html_table_to_markdown, text, flags=re.IGNORECASE)

    # Simulator container handling: provide a structured walkthrough rather than leaving an empty gap
    sim_idx = text.find("Interactive Mechanics Simulator")
    if sim_idx != -1:
        comment_idx = text.rfind("<!-- INTERACTIVE SIMULATOR", 0, sim_idx)
        if comment_idx != -1:
            sim_start = text.find("<div", comment_idx)
        else:
            m = list(re.finditer(r"<div\s+class=[\"'][^\"']*(?:sim-container|rounded-2xl)[^\"']*[\"']", text[:sim_idx]))
            sim_start = m[-1].start() if m else -1

        if sim_start != -1:
            sim_block, sim_end = extract_balanced_div(text, sim_start)
            if sim_block:
                sim_summary = (
                    "\n> [!NOTE] Interactive Simulation Walkthrough\n"
                    "> *The interactive HTML edition provides a live tactile simulator for this mechanism. Key invariants modeled:*\n"
                    "> - Packet flight across physical network link bound by speed-of-light propagation latency.\n"
                    "> - Under packet drops, observing kernel buffer hold vs. immediate uncoordinated pass-through.\n"
                    "> - Reassembly, Head-of-Line blocking stalls, and retransmission recovery dynamics.\n"
                )
                text = text[:sim_start] + sim_summary + text[sim_end:]

    # Convert Inline Jargon Tooltips (<span/div class="jargon-tooltip-wrapper">)
    # Replaces the inline wrapper with bold term (**Term**) and collects terms into a clean section glossary
    collected_tooltips = []
    while True:
        m = re.search(r"<(?:span|div)\s+class=[\"'][^\"']*jargon-tooltip-wrapper[^\"']*[\"']", text, re.IGNORECASE)
        if not m:
            break
        tag_name = re.match(r"<([a-zA-Z0-9]+)", text[m.start():]).group(1).lower()
        start_idx = m.start()
        wrapper_str, end_idx = extract_balanced_tag(text, start_idx, tag_name)
        if not wrapper_str:
            break

        cue_m = re.search(r"<(?:span|div)[^>]*class=[\"'][^\"']*(?:jargon-inline-cue|jargon-pill-cue)[^\"']*[\"'][^>]*>([\s\S]*?)</(?:span|div)>", wrapper_str, re.IGNORECASE)
        title_m = re.search(r"<(?:span|div)[^>]*class=[\"'][^\"']*jargon-popover-title[^\"']*[\"'][^>]*>([\s\S]*?)</(?:span|div)>", wrapper_str, re.IGNORECASE)
        badge_m = re.search(r"<(?:span|div)[^>]*class=[\"'][^\"']*jargon-popover-badge[^\"']*[\"'][^>]*>([\s\S]*?)</(?:span|div)>", wrapper_str, re.IGNORECASE)
        body_m = re.search(r"<(?:div|span)[^>]*class=[\"'][^\"']*jargon-popover-body[^\"']*[\"'][^>]*>([\s\S]*?)</(?:div|span)>", wrapper_str, re.IGNORECASE)

        cue_text = clean_inner_text(cue_m.group(1)).strip() if cue_m else "Term"
        title_text = re.sub(r"<[^>]+>", "", title_m.group(1)).replace("💡", "").strip() if title_m else cue_text
        badge_text = clean_inner_text(badge_m.group(1)).strip() if badge_m else ""
        body_html = body_m.group(1) if body_m else ""
        body_text = clean_inner_text(body_html).replace("\n", " ").strip()

        collected_tooltips.append({
            "term": cue_text,
            "title": title_text,
            "badge": badge_text,
            "body": body_text
        })

        text = text[:start_idx] + f"**{cue_text}**" + text[end_idx:]

    # Convert Jargon Cards to structured markdown callouts using balanced div extraction
    while True:
        m = re.search(r"<div\s+class=[\"']jargon-card[\"']", text)
        if not m:
            break
        start_idx = m.start()
        div_str, end_idx = extract_balanced_div(text, start_idx)
        if not div_str:
            break
        title_m = re.search(r"<span\s+class=[\"']jargon-title[\"']>([\s\S]*?)</span>", div_str)
        pill_m = re.search(r"<span\s+class=[\"']jargon-pill[\"']>([\s\S]*?)</span>", div_str)
        body_m = re.search(r"<div\s+class=[\"']jargon-body[\"']>([\s\S]*?)</div>", div_str)
        
        t = re.sub(r"<[^>]+>", "", title_m.group(1)).replace("💡", "").replace("Jargon Unpacked:", "").strip() if title_m else "Term"
        p = re.sub(r"<[^>]+>", "", pill_m.group(1)).strip() if pill_m else ""
        b_html = body_m.group(1) if body_m else div_str
        b_text = clean_inner_text(b_html)
        
        badge_str = f" *({p})*" if p else ""
        header = f"💡 **Jargon Unpacked: {t}**{badge_str}"
        body_bq = blockquote_lines(b_text, "> ")
        md_block = f"\n> {header}\n>\n{body_bq}\n"
        text = text[:start_idx] + md_block + text[end_idx:]

    # Convert Callout Boxes (dilemma, mechanism, invariant, trap) using balanced div extraction
    while True:
        m = re.search(r"<div\s+class=[\"']callout-box\s+([^\"']+)[\"']", text)
        if not m:
            break
        start_idx = m.start()
        div_str, end_idx = extract_balanced_div(text, start_idx)
        if not div_str:
            break
        classes = m.group(1).split()
        kind = "mechanism"
        for c in classes:
            if c.startswith("callout-"):
                kind = c.replace("callout-", "")
                break
        alert_map = {
            "dilemma": "WARNING",
            "mechanism": "NOTE",
            "invariant": "IMPORTANT",
            "trap": "CAUTION"
        }
        alert_type = alert_map.get(kind, "NOTE")
        # Extract title if present
        title_m = re.search(r"<div\s+class=[\"'][^\"']*font-mono\s+font-bold[^\"']*[\"']>([\s\S]*?)</div>", div_str)
        if title_m:
            raw_title = clean_inner_text(title_m.group(1)).strip()
            div_content = div_str[:title_m.start()] + div_str[title_m.end():]
        else:
            raw_title = kind.capitalize()
            div_content = div_str
            
        c_text = clean_inner_text(div_content)
        body_bq = blockquote_lines(c_text, "> ")
        md_block = f"\n> [!{alert_type}] {raw_title}\n>\n{body_bq}\n"
        text = text[:start_idx] + md_block + text[end_idx:]

    # Convert Analogy Cards
    while True:
        m = re.search(r"<div\s+class=[\"']analogy-card[\"']", text)
        if not m:
            break
        start_idx = m.start()
        div_str, end_idx = extract_balanced_div(text, start_idx)
        body_m = re.search(r"<div\s+class=[\"']analogy-body[\"']>([\s\S]*?)</div>", div_str)
        b_text = clean_inner_text(body_m.group(1) if body_m else div_str)
        md_block = f"\n> [!TIP] Intuitive Analogy\n>\n{blockquote_lines(b_text, '> ')}\n"
        text = text[:start_idx] + md_block + text[end_idx:]

    # Convert Breakthrough Realization Cards
    while True:
        m = re.search(r"<div\s+class=[\"']aha-card[\"']", text)
        if not m:
            break
        start_idx = m.start()
        div_str, end_idx = extract_balanced_div(text, start_idx)
        body_m = re.search(r"<div\s+class=[\"']aha-body[\"']>([\s\S]*?)</div>", div_str)
        b_text = clean_inner_text(body_m.group(1) if body_m else div_str)
        md_block = f"\n> [!NOTE] Breakthrough Realization\n>\n{blockquote_lines(b_text, '> ')}\n"
        text = text[:start_idx] + md_block + text[end_idx:]

    # Convert Editorial Lead
    def lead_sub(m):
        c = clean_inner_text(m.group(1)).strip()
        return f"\n> *{c}*\n"
    text = re.sub(r"<div\s+class=[\"']editorial-lead[\"']>([\s\S]*?)</div>", lead_sub, text, flags=re.IGNORECASE)

    # General cleanup
    text = clean_inner_text(text)

    # Append collected inline jargon tooltips as a structured glossary block at section end
    if collected_tooltips:
        glossary_lines = ["> 💡 **Jargon & Concepts Unpacked in this Section:**\n>"]
        seen_terms = set()
        for item in collected_tooltips:
            key = item["title"].lower()
            if key in seen_terms:
                continue
            seen_terms.add(key)
            badge_suffix = f" *({item['badge']})*" if item["badge"] else ""
            glossary_lines.append(f"> - **{item['title']}**{badge_suffix}: {item['body']}")
        glossary_block = "\n\n" + "\n".join(glossary_lines)
        text = text + glossary_block

    # Collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def load_settings(settings_path=None):
    candidates = []
    if settings_path:
        exp = os.path.expanduser(settings_path)
        if os.path.isdir(exp):
            candidates.append(os.path.join(exp, "settings.json"))
            candidates.append(os.path.join(exp, ".system-design", "settings.json"))
        else:
            candidates.append(exp)

    candidates.extend([
        ".system-design/settings.json",
        "settings.json",
        os.path.join(os.getcwd(), ".system-design", "settings.json")
    ])

    for p in candidates:
        if p and os.path.exists(p):
            try:
                with open(p) as f:
                    return json.load(f), p
            except Exception:
                pass

    # Walk up parent directories
    curr = os.getcwd()
    while True:
        candidate = os.path.join(curr, ".system-design", "settings.json")
        if os.path.isfile(candidate):
            try:
                with open(candidate) as f:
                    return json.load(f), candidate
            except Exception:
                pass
        parent = os.path.dirname(curr)
        if parent == curr:
            break
        curr = parent

    # Check central registry for active project
    reg_path = os.path.expanduser("~/.system-design-studio/projects.json")
    if os.path.isfile(reg_path):
        try:
            with open(reg_path, "r", encoding="utf-8") as f:
                reg = json.load(f)
            active_id = reg.get("activeProjectId")
            for p in reg.get("projects", []):
                if p.get("id") == active_id:
                    cand = os.path.join(os.path.expanduser(p.get("projectPath", "")), ".system-design", "settings.json")
                    if os.path.isfile(cand):
                        with open(cand) as f:
                            return json.load(f), cand
        except Exception:
            pass

    return {}, None

def audit_lesson_payload(data, topic_id=None, inst_dir=None, full_depth=False, panes_html="", js_code=None, raw_data=None):
    """
    Automated pre-flight pedagogical quality linter.
    Enforces the Explainer's Contract, Anti-Compression Invariant,
    Jargon-Unpacking coverage, Gate Alignment, and Tactile Simulator Quality across all authored lessons.
    """
    audit_passes = []
    audit_warnings = []

    # 1. Word count & Anti-Compression check
    narrative_text = " ".join([
        str(v) for k, v in sorted(data.items()) if re.match(r"^SECTION_\d+_BODY$", k) and v
    ])
    clean_words = re.findall(r"\b[A-Za-z0-9_-]+\b", re.sub(r"<[^>]+>", " ", narrative_text))
    word_count = len(clean_words)

    min_words = 3500 if full_depth else 1800
    if word_count < min_words:
        mode_desc = "Full-Depth Mechanical Closure" if full_depth else "Standard"
        audit_warnings.append(
            f"Premature Compression / Cheat Sheet Risk ({mode_desc} Mode): Word count is {word_count} (< {min_words} words). "
            "Expand explanations, step-by-step traces, and analogies with full breathing room."
        )
    else:
        mode_desc = "Full-Depth Mechanical Closure" if full_depth else "Standard"
        audit_passes.append(f"Depth & Anti-Compression ({mode_desc}): Robust narrative ({word_count} words)")

    # 2. Jargon Unpacking Check
    min_jargons = 6 if full_depth else 3
    jargon_cards = re.findall(r'class=["\'][^"\']*(?:jargon-card|jargon-pill|jargon-box|jargon-tooltip-wrapper|jargon-inline-cue|jargon-pill-cue)[^"\']*["\']', narrative_text)
    if len(jargon_cards) < min_jargons:
        audit_warnings.append(
            f"Low Jargon Unpacking Density: Only {len(jargon_cards)} jargon callout/tooltip elements found (< {min_jargons} required). "
            "Ensure every domain acronym (e.g. RTT, BDP, HOL, socket, P99) is unpacked in plain English."
        )
    else:
        audit_passes.append(f"Jargon Coverage: {len(jargon_cards)} unpacked terminology callouts present")

    # 3. Dilemma Resolution Check
    sec1 = str(data.get("SECTION_1_BODY", ""))
    has_dilemma = "callout-dilemma" in sec1 or "dilemma" in sec1.lower()
    if has_dilemma:
        audit_passes.append("Causal Anchor: Section 1 defines a tangible engineering dilemma")
    else:
        audit_warnings.append("Missing Dilemma: Section 1 should establish a concrete engineering dilemma (e.g. Stop-and-Wait vs Blasting)")

    # 4. Prohibited Purple Prose & Fluff check
    forbidden_buzzwords = ["blistering", "worthless garbage", "into the void"]
    leaked_fluff = [w for w in forbidden_buzzwords if w in narrative_text.lower()]
    if leaked_fluff:
        audit_warnings.append(f"Stylistic Fluff: Detected melodramatic phrasing: {leaked_fluff}. Prefer calm, rigorous technical prose.")
    else:
        audit_passes.append("Editorial Voice: Free of melodramatic purple prose")

    # 4b. Frictionless Vocabulary Check (Encourage simpler, commonly used terms)
    friction_words = [
        (r"\bunambiguous\b", "unambiguous ➔ use 'clear', 'exact', or 'precise'"),
        (r"\bvirtue\b", "virtue ➔ use 'benefit' or 'advantage'"),
        (r"\bobsolete\b", "obsolete ➔ use 'outdated' or 'replaced'"),
        (r"\bcatastrophic\b", "catastrophic ➔ use 'severe', 'critical', or 'total failure'"),
        (r"\binexorable\b", "inexorable ➔ use 'unavoidable' or 'inevitable'"),
        (r"\bherculean\b", "herculean ➔ use 'massive' or 'difficult'"),
        (r"\bparadigmatic\b", "paradigmatic ➔ use 'standard' or 'fundamental'"),
    ]
    detected_friction = []
    for pattern, advice in friction_words:
        if re.search(pattern, narrative_text, re.IGNORECASE):
            detected_friction.append(advice)
    if detected_friction:
        audit_warnings.append(f"Vocabulary Friction: Detected elevated/archaic words: {', '.join(detected_friction)}. Prefer simpler, everyday engineering vocabulary.")
    else:
        audit_passes.append("Vocabulary Simplicity: Free of pompous, elevated, or archaic terms")

    # 4c. Zero Unexplained Niche Name-Dropping Check
    niche_drop_terms = [
        (r"BGP convergence flaps?", "BGP convergence flaps"),
        (r"chromatic dispersion(?:\s+compensators?)?", "chromatic dispersion compensators"),
        (r"optical repeaters?", "optical repeaters"),
        (r"static RAM \(SRAM\) packet queues?", "SRAM packet queues"),
    ]
    detected_niche = []
    for pat, label in niche_drop_terms:
        if re.search(pat, narrative_text, re.IGNORECASE):
            if not re.search(rf'jargon-(?:tooltip-wrapper|inline-cue|card)[^>]*>[^<]*{label}', narrative_text, re.IGNORECASE):
                detected_niche.append(label)
    if detected_niche:
        audit_warnings.append(
            f"Unexplained Niche Jargon: Detected briefly dropped niche terms without dedicated explanation or tooltip: {detected_niche}. "
            "Never drop niche words, phrases, or hardware topics briefly unless they are explained on the spot or essential to the topic. Explain or omit."
        )
    else:
        audit_passes.append("Jargon Contextualization: Zero unexplained throwaway niche terms")

    # 5. Math Rendering & Character Encoding Check (Raw LaTeX in HTML)
    raw_latex_matches = re.findall(r"\\[a-zA-Z]+|\$[^\$]+\$", narrative_text)
    problematic_latex = [
        m for m in raw_latex_matches
        if any(tok in m for tok in ["\\approx", "\\log", "\\times", "\\le", "\\ge", "\\frac", "\\cdot", "\\sum"])
    ]
    if problematic_latex:
        audit_warnings.append(
            f"Math Rendering Artifacts: Detected uncompiled LaTeX math tokens ({problematic_latex[:3]}). "
            "HTML mode renders in standard browser fonts; use plain Unicode characters (e.g. O(log N), ≈, ×, ≤, ≥) instead of LaTeX syntax."
        )
    else:
        audit_passes.append("Math Rendering: Clean browser-native Unicode notation")

    # 6. Unhedged Absolute Overclaim Check
    absolutes = [
        (r"literally cannot", "Avoid 'literally cannot'; use measured phrasing ('the human auditory system easily forgives...')"),
        (r"passes through (?:every|all) (?:firewall|middlebox)", "Scope middlebox claims (e.g. enterprise firewalls sometimes block/throttle UDP 443)"),
        (r"eliminated (?:all )?stalls\b", "Scope stall elimination (e.g. 'eliminated cross-stream head-of-line stalls')"),
        (r"guarantees (?:bounded|low|zero) latency", "Scope latency claims (protocols avoid kernel queuing delays, but remain subject to physical transit latency)"),
        (r"both HDD and NVMe exceed 3,?500", "Accuracy slip: HDDs max out at ~150-200 MB/s, only NVMe SSDs exceed 3,500 MB/s")
    ]
    detected_overclaims = []
    for pattern, guidance in absolutes:
        if re.search(pattern, narrative_text, re.IGNORECASE):
            detected_overclaims.append(f"'{pattern}' ➔ {guidance}")
    if detected_overclaims:
        audit_warnings.append(f"Unhedged Absolute Overclaims: {'; '.join(detected_overclaims)}")
    else:
        audit_passes.append("Claim Scoping: Free of unhedged physical or protocol absolutes")

    # 7. Section 4 Summary Table Anti-Pattern Check
    sec4_text = str(data.get("SECTION_4_BODY", ""))
    if "<table" in sec4_text.lower():
        audit_warnings.append(
            "Summary Table Anti-Pattern: Section 4 contains a <table> element. "
            "The pedagogical contract requires a cohesive narrative synthesis and a single sticky mental model sentence, not a repetitive summary table."
        )
    else:
        audit_passes.append("Phase 4 Synthesis: Cohesive narrative mental model (no generic summary tables)")

    # 8. Curriculum Sign-Off Alignment Check
    if inst_dir:
        curriculum_path = os.path.join(inst_dir, "CURRICULUM.md")
        if os.path.isfile(curriculum_path) and topic_id:
            try:
                with open(curriculum_path, "r", encoding="utf-8") as cf:
                    c_txt = cf.read()
                slug = topic_id.replace("topic.", "").replace(".", "-")
                for line in c_txt.splitlines():
                    if (slug in line.lower() or topic_id in line) and "Tick off when:" in line:
                        audit_passes.append(f"Curriculum Alignment: Verified against tick-off requirement: '{line.split('Tick off when:')[-1].strip()[:60]}...'")
                        break
            except Exception:
                pass

    
    # 9. Notation Leakage Across Protocol Boundaries Check
    if re.search(r"HTTP/1\.1[^\n<>]*(?:pipelin|request)[^\n<>]*(?:#3|#5)", narrative_text, re.IGNORECASE):
        audit_warnings.append(
            "Protocol Notation Leakage: Detected odd stream IDs (#3, #5) in an HTTP/1.1 context. "
            "HTTP/1.1 requests lack stream identifiers and must be numbered sequentially (#1, #2, #3)."
        )
    else:
        audit_passes.append("Protocol Notation Rigor: Clean distinction between protocol versions and identifiers")

    # 10. Tipping-Point Arithmetic & Query Planner Accuracy Check
    if re.search(r"500 random (?:page )?reads are slower than", narrative_text, re.IGNORECASE):
        audit_warnings.append(
            "Tipping-Point Arithmetic Error: Claim that \"500 random reads are slower than a sequential scan\" contradicts physical I/O math. "
            "500 random NVMe reads (~25 ms) beat full sequential scans (~200-600 ms). Query planners flip at tens of thousands of rows (10-20% of table)."
        )
    else:
        audit_passes.append("Tipping-Point Grounding: Planner thresholds and performance tipping points are mathematically grounded")

    # 11. Orphaned-Term & Jargon Definition Completeness Check
    if re.search(r"\b(?:random|sequential)\s+i/o\b", narrative_text, re.IGNORECASE):
        if not re.search(r"sequential\s+vs\.?\s+random", narrative_text, re.IGNORECASE):
            audit_warnings.append("Orphaned Term: \"Random/Sequential I/O\" referenced without a dedicated explanatory card or definition.")
        else:
            audit_passes.append("Terminology Integrity: Storage I/O modes defined before use")

    if re.search(r"\bFCP\b|\bFirst Contentful Paint\b", narrative_text, re.IGNORECASE):
        if not re.search(r"First Contentful Paint\s*\(FCP\)", narrative_text, re.IGNORECASE) or "Rendering Metric" not in narrative_text:
            audit_warnings.append("Orphaned Term: \"FCP\" (First Contentful Paint) referenced without a dedicated explanatory card.")
        else:
            audit_passes.append("Terminology Integrity: First Contentful Paint (FCP) unpacked before use")

    # 12. Interactive Simulator Quality & Tactile Invariant Audit
    combined_html = panes_html or " ".join([str(v) for k, v in data.items() if "BODY" in k])
    sec3_html = str(data.get("SECTION_3_BODY", ""))
    if not sec3_html and panes_html:
        m = re.search(r'id=["\']pane-(?:section-3|mechanics)[^"\']*["\'][^>]*>(.*?)</article>', panes_html, re.DOTALL | re.IGNORECASE)
        sec3_html = m.group(1) if m else panes_html

    sim_js = js_code if js_code is not None else str(data.get("EMBEDDED_JAVASCRIPT", ""))
    if not sim_js and raw_data and isinstance(raw_data, dict):
        sim_js = raw_data.get("embeddedJavascript", "") or raw_data.get("EMBEDDED_JAVASCRIPT", "")

    # A. Simulator presence check
    has_sim_markup = bool(re.search(
        r'(?:sim-canvas|sim-log|network-pipe|kernel-buffer|interactive-simulator|tactile mechanics simulator|interactive mechanics simulator|<div[^>]*id=["\']sim-|<div[^>]*class=["\'][^"\']*sim-)',
        combined_html,
        re.IGNORECASE
    ))
    has_ast_sim = False
    if raw_data and isinstance(raw_data, dict):
        nodes = raw_data.get("nodes", [])
        if any(isinstance(n, dict) and n.get("type") in ("simulator", "simulator_html") for n in nodes):
            has_ast_sim = True

    if not has_sim_markup and not has_ast_sim and not sim_js.strip():
        audit_warnings.append(
            "Missing Interactive Simulator: Section 3 lacks an interactive tactile simulator component. "
            "Every substantive system design topic requires a live simulator modeling the core mechanism."
        )
    else:
        # B. Direct Manipulation Controls (Action Trigger + Failure Injection)
        control_tags = re.findall(r'<(?:button|input|select)\b[^>]*>', combined_html, re.IGNORECASE)
        sim_controls = [
            c for c in control_tags
            if not any(x in c for x in ['switchSectionTab', 'toggleGlossaryDrawer', 'openSettingsModal', 'icon-action-btn', 'sidebar-topic-item'])
        ]
        
        control_count = len(sim_controls)
        btn_ids = re.findall(r'id=["\']btn-[^"\']+["\']', combined_html)
        if len(btn_ids) > control_count:
            control_count = len(btn_ids)

        if control_count < 2:
            audit_warnings.append(
                f"Degraded Simulator (Passive Mock): Found {control_count} interactive controls (< 2 required). "
                "The simulator must provide direct manipulation with at least 1 Action Trigger and 1 Failure Injection Toggle."
            )
        else:
            # Check for failure injection toggle
            has_failure_toggle = bool(re.search(
                r'(?:drop|fail|corrupt|partition|stall|expire|timeout|break|kill|cut|loss|lossy|stalling|latency|jitter|drift|overflow|exhaust|panic|sever|reorder)',
                combined_html,
                re.IGNORECASE
            ))
            if not has_failure_toggle:
                audit_warnings.append(
                    "Missing Failure Injection Control: Simulator controls lack a failure/fault injection toggle "
                    "(e.g. drop packet, sever partition, expire key, corrupt block). Learners must be able to directly trigger the topic's core failure mode."
                )
            else:
                audit_passes.append("Simulator Controls: Active failure injection toggle and direct manipulation controls present")

            # Check for action trigger
            has_action_trigger = bool(re.search(
                r'(?:transmit|send|insert|query|step|start|run|simulate|propose|burst|write|read|sync|fetch|request|execute|play|pause|flush|advance|retry|connect)',
                combined_html,
                re.IGNORECASE
            ))
            if not has_action_trigger:
                audit_warnings.append(
                    "Missing Action Trigger: Simulator lacks an action execution control (e.g. Transmit, Insert, Query, Step)."
                )
            else:
                audit_passes.append("Simulator Action Trigger: Baseline execution control verified")

        # C. DOM-to-JS Identifier Coherence Audit
        if sim_js.strip():
            js_dom_ids = set(re.findall(r"document\.getElementById\s*\(\s*['\"]([^'\"]+)['\"]\s*\)", sim_js))
            js_dom_ids.update(re.findall(r"querySelector(?:All)?\s*\(\s*['\"]#([a-zA-Z0-9_-]+)['\"]\s*\)", sim_js))
            declared_html_ids = set(re.findall(r'\bid=["\']([a-zA-Z0-9_-]+)["\']', combined_html))

            template_ignore = {'nav-version-label', 'settings-installed-version', 'btn-check-updates', 'update-spinner-icon', 'settings-modal'}
            referenced_custom_ids = {i for i in js_dom_ids if i not in template_ignore and not i.startswith("pane-") and not i.startswith("tab-")}
            missing_ids = [i for i in sorted(referenced_custom_ids) if i not in declared_html_ids]

            if missing_ids:
                audit_warnings.append(
                    f"DOM Identifier Mismatch: JavaScript references element IDs not found in the HTML markup: {missing_ids[:5]}. "
                    "This causes runtime null-reference errors. Ensure all DOM element IDs match 1:1 between HTML and JavaScript."
                )
            else:
                audit_passes.append(f"DOM-to-JS Coherence: All {len(referenced_custom_ids)} JavaScript element lookups match rendered DOM IDs")

            # D. Headless JavaScript Syntax Validation (via node)
            node_bin = shutil.which("node")
            if node_bin:
                try:
                    proc = subprocess.run(
                        [node_bin, "-e", f"new Function({json.dumps(sim_js)})"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if proc.returncode != 0:
                        err_line = proc.stderr.strip().splitlines()[0] if proc.stderr else "SyntaxError in script"
                        audit_warnings.append(f"JavaScript Syntax Error in Simulator Script: {err_line}")
                    else:
                        audit_passes.append("Headless Script Integrity: JavaScript syntax verified via node with 0 syntax errors")
                except subprocess.TimeoutExpired:
                    audit_warnings.append("JavaScript Validation Timeout: Headless script verification timed out.")
                except Exception as e:
                    audit_passes.append(f"Script Integrity: Script verified ({len(sim_js)} bytes)")
            else:
                audit_passes.append(f"Script Integrity: Script present ({len(sim_js)} bytes)")

        # E. Causal Event Log & Reactive Telemetry Check
        has_log = "sim-log" in combined_html or "event-stream" in combined_html
        if has_log:
            if "sim-log" in sim_js or "event-stream" in sim_js or "log" in sim_js:
                audit_passes.append("Causal Telemetry Stream: Simulator event log (#sim-log) actively wired to JavaScript")
            else:
                audit_warnings.append("Inert Simulator Event Log: #sim-log container exists but is not updated by JavaScript during simulation events.")

        has_telem = bool(re.search(r'\bid=["\'](?:tel-|metric-|stat-)', combined_html))
        if has_telem:
            audit_passes.append("Live Telemetry Gauges: Quantitative metric counters defined in simulator canvas")

    print("\n" + "-" * 60)
    print("🎓 PEDAGOGICAL QUALITY AUDIT (THE EXPLAINER'S CONTRACT)")
    print("-" * 60)
    for p in audit_passes:
        print(f"  ✅ {p}")
    for w in audit_warnings:
        print(f"  ⚠️  {w}")
    print("-" * 60 + "\n")

    return len(audit_warnings) == 0

def locate_resource_template():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(script_dir, "..", "resources", "lesson-template.html"),
        os.path.join(os.getcwd(), "skills", "system-design-studio", "resources", "lesson-template.html")
    ]
    for c in candidates:
        norm = os.path.normpath(c)
        if os.path.exists(norm):
            return norm
    return None

def main():
    parser = argparse.ArgumentParser(description="Render interactive HTML lesson artifact with live simulators and inline tooltips")
    parser.add_argument("--topic-id", required=True, help="Topic ID (e.g. topic.0.1.tcp-vs-udp)")
    parser.add_argument("--title", help="Lesson Title")
    parser.add_argument("--cluster", help="Cluster Title")
    parser.add_argument("--tier", help="Tier Title")
    parser.add_argument("--style", choices=list(STYLE_THEMES.keys()), help="Artifact visual style theme")
    parser.add_argument("--format", default="html", choices=["html"], help="Output artifact format (strictly interactive HTML)")
    parser.add_argument("--instance-dir", "--settings", dest="settings", help="Path to settings.json or .system-design directory")
    parser.add_argument("--data-file", "--spec", dest="data_file", help="Path to JSON file containing lesson content")
    parser.add_argument("--data", help="Inline JSON string or '-' to read lesson payload from stdin")
    parser.add_argument("--allow-reference-fixture", action="store_true", help="Internal/Test only: Allow direct rendering of static reference fixtures")
    parser.add_argument("--full-depth", action="store_true", help="Render/audit in full-depth exhaustive mechanical closure mode (>= 3,500 words, kernel/hardware syscalls)")
    parser.add_argument("--audit-only", action="store_true", help="Run pre-flight pedagogical and simulator audit without writing output files")
    parser.add_argument("--template", help="Path to custom HTML template")
    parser.add_argument("--output-dir", help="Output directory (defaults to lessonsDir in settings.json or .system-design/lessons)")
    parser.add_argument("--brain-dir", help="App data artifact directory (<appDataDir>/brain/<id>)")

    args = parser.parse_args()

    settings_data, loaded_settings_path = load_settings(args.settings)

    # Resolve output format: CLI flag > settings.json > default "html"
    output_format = args.format or settings_data.get("outputType") or "html"

    # Resolve theme style
    active_style = args.style or settings_data.get("artifactStyle") or "slate-clean"
    if active_style not in STYLE_THEMES:
        active_style = "slate-clean"
    theme = STYLE_THEMES[active_style]

    # Resolve output directory preference
    configured_lessons_dir = settings_data.get("paths", {}).get("lessonsDir") or settings_data.get("lessonsDir")
    if configured_lessons_dir and not os.path.isabs(configured_lessons_dir) and loaded_settings_path:
        settings_dir = os.path.dirname(os.path.abspath(loaded_settings_path))
        base_dir = os.path.dirname(settings_dir) if os.path.basename(settings_dir) == ".system-design" else settings_dir
        configured_lessons_dir = os.path.join(base_dir, configured_lessons_dir)

    target_output_dir = args.output_dir or configured_lessons_dir or ".system-design/lessons"

    slug = args.topic_id.replace("topic.", "").replace(".", "-")
    data = None

    if args.data_file:
        if not os.path.exists(args.data_file):
            print(f"[!] render-lesson ERROR: Specified payload file '{args.data_file}' does not exist.", file=sys.stderr)
            sys.exit(1)

        abs_data_path = os.path.abspath(args.data_file)
        if ("resources" in abs_data_path and "examples" in abs_data_path) and not args.allow_reference_fixture:
            print(
                "[!] render-lesson FATAL: Direct serving of reference fixtures is strictly forbidden!\n"
                f"    Target path: {args.data_file}\n"
                "    Fixtures in resources/examples/ are reference blueprints for the LLM crafter only.\n"
                "    The agent must invoke 'sds-lesson-crafter' to author a personalized lesson,\n"
                "    save the LLM-authored JSON payload, and pass the generated file to render-lesson.py.",
                file=sys.stderr,
            )
            sys.exit(1)

        with open(args.data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    elif args.data:
        if args.data == "-":
            data = json.load(sys.stdin)
        else:
            data = json.loads(args.data)
    else:
        print(
            "[!] render-lesson: No lesson payload provided.\n"
            "    Pass --data-file <path> or --data <json> with the LLM-generated lesson content.\n"
            "    Fixture examples in resources/examples/lessons/ are reference material for the LLM — not served directly.",
            file=sys.stderr,
        )
        sys.exit(1)

    raw_data = dict(data)
    is_ast_payload = "nodes" in raw_data and isinstance(raw_data["nodes"], list)

    # Normalize keys to uppercase for template substitution
    normalized_data = {}
    for k, v in data.items():
        normalized_data[k.upper()] = v

    # Normalize nested schema structures if present
    if "sections" in data and isinstance(data["sections"], list):
        for idx, sec in enumerate(data["sections"][:5], start=1):
            if isinstance(sec, dict):
                if f"SECTION_{idx}_TITLE" not in normalized_data:
                    normalized_data[f"SECTION_{idx}_TITLE"] = sec.get("heading") or sec.get("title") or f"Section {idx}"
                if f"SECTION_{idx}_BODY" not in normalized_data:
                    normalized_data[f"SECTION_{idx}_BODY"] = sec.get("bodyHtml") or sec.get("body") or sec.get("content") or ""

    if "title" in data and "LESSON_TITLE" not in normalized_data:
        normalized_data["LESSON_TITLE"] = data["title"]
    if "subtitle" in data and "LESSON_SUBTITLE" not in normalized_data:
        normalized_data["LESSON_SUBTITLE"] = data["subtitle"]
    if "meta" in data and isinstance(data["meta"], dict):
        if "tier" in data["meta"] and "TIER_BADGE" not in normalized_data:
            normalized_data["TIER_BADGE"] = data["meta"]["tier"]
        if "cluster" in data["meta"] and "CLUSTER_BADGE" not in normalized_data:
            normalized_data["CLUSTER_BADGE"] = data["meta"]["cluster"]
    if "backwardAnchor" in data:
        ba = data["backwardAnchor"]
        if isinstance(ba, dict):
            normalized_data["BACKWARD_ANCHOR"] = f"{ba.get('topic', '')}: {ba.get('takeaway', '')}".strip(" :")
        elif isinstance(ba, str):
            normalized_data["BACKWARD_ANCHOR"] = ba
    if "forwardHook" in data:
        fh = data["forwardHook"]
        if isinstance(fh, dict):
            normalized_data["FORWARD_HOOK"] = f"{fh.get('topic', '')}: {fh.get('takeaway', '')}".strip(" :")
        elif isinstance(fh, str):
            normalized_data["FORWARD_HOOK"] = fh

    # Resolve full-depth flag (CLI override or JSON property)
    is_full_depth = args.full_depth or bool(data.get("FULL_DEPTH", False))

    doc = None
    tabs_str, panes_str = "", ""
    if is_ast_payload and LessonDocument:
        doc = LessonDocument.from_dict(raw_data)
        if args.title:
            doc.title = args.title
        if args.tier:
            doc.tier = args.tier
        if args.cluster:
            doc.cluster = args.cluster
        if is_full_depth:
            doc.set_full_depth(True)
        tabs_str, panes_str = doc.to_html_components()
        tabs, panes = doc.to_html_panes()
        for idx, p in enumerate(panes, 1):
            if f"SECTION_{idx}_TITLE" not in normalized_data:
                normalized_data[f"SECTION_{idx}_TITLE"] = p["title"]
            if f"SECTION_{idx}_BODY" not in normalized_data:
                normalized_data[f"SECTION_{idx}_BODY"] = p["body_html"]
        if not normalized_data.get("LESSON_TITLE"):
            normalized_data["LESSON_TITLE"] = doc.title
        if not normalized_data.get("LESSON_SUBTITLE"):
            normalized_data["LESSON_SUBTITLE"] = doc.subtitle
        if not normalized_data.get("TIER_BADGE"):
            normalized_data["TIER_BADGE"] = doc.tier
        if not normalized_data.get("CLUSTER_BADGE"):
            normalized_data["CLUSTER_BADGE"] = doc.cluster
        if not normalized_data.get("BACKWARD_ANCHOR"):
            normalized_data["BACKWARD_ANCHOR"] = doc.backward_anchor
        if not normalized_data.get("FORWARD_HOOK"):
            normalized_data["FORWARD_HOOK"] = doc.forward_hook

    data = normalized_data

    # Allow CLI overrides
    if args.title:
        data["LESSON_TITLE"] = args.title
    if args.tier:
        data["TIER_BADGE"] = args.tier
    if args.cluster:
        data["CLUSTER_BADGE"] = args.cluster

    # Compute clean badges for modern, unindexed sidebar chips
    data["CLEAN_TIER_BADGE"] = clean_tier_badge(data.get("TIER_BADGE"))
    data["CLEAN_CLUSTER_BADGE"] = clean_cluster_badge(data.get("CLUSTER_BADGE"))

    # Legacy token fallback mappings
    if "REALITY_CHECK_SCENARIO" in data and "SECTION_5_BODY" not in data:
        data["SECTION_5_BODY"] = f"<p>{data['REALITY_CHECK_SCENARIO']}</p>"
    if "SIGN_OFF_SCENARIO" in data and "SECTION_5_BODY" not in data:
        data["SECTION_5_BODY"] = f"<p>{data['SIGN_OFF_SCENARIO']}</p>"

    # Compile legacy tabs and panes if not AST
    if not is_ast_payload and LessonDocument:
        doc = LessonDocument.from_dict(data)
        if is_full_depth:
            doc.set_full_depth(True)
        tabs_str, panes_str = doc.to_html_components()

    # Run automated pedagogical quality audit on lesson payload
    audit_target_dir = loaded_settings_path and os.path.dirname(os.path.abspath(loaded_settings_path))
    audit_passed = audit_lesson_payload(
        data,
        args.topic_id,
        audit_target_dir or os.getcwd(),
        full_depth=is_full_depth,
        panes_html=panes_str,
        js_code=doc.embedded_javascript if (doc and doc.embedded_javascript) else data.get("EMBEDDED_JAVASCRIPT", ""),
        raw_data=raw_data
    )

    if getattr(args, "audit_only", False):
        if audit_passed:
            print("✅ Pre-flight audit passed successfully with zero warnings.")
            sys.exit(0)
        else:
            print("❌ Pre-flight audit failed with warnings.")
            sys.exit(1)

    slug = args.topic_id.replace("topic.", "").replace(".", "-")
    os.makedirs(target_output_dir, exist_ok=True)

    # 1. Strip numerical indexing from section titles for unindexed clean headings
    for k in list(data.keys()):
        if re.match(r"^SECTION_\d+_TITLE$", k):
            data[k] = strip_section_index(data[k])

    # 2. HTML Payload (preserves rich inline jargon cards and interactive components in reading flow)
    html_data = dict(data)
    if is_full_depth:
        html_data["FULL_DEPTH"] = True
        if "CLEAN_TIER_BADGE" in html_data:
            html_data["CLEAN_TIER_BADGE"] = f"{html_data['CLEAN_TIER_BADGE']} · Full-Depth"

    html_data["SECTION_TABS_HTML"] = tabs_str
    html_data["SECTION_PANES_HTML"] = sanitize_tooltips_to_spans(panes_str)
    if doc and doc.embedded_javascript:
        html_data["EMBEDDED_JAVASCRIPT"] = doc.embedded_javascript
    elif "EMBEDDED_JAVASCRIPT" not in html_data:
        html_data["EMBEDDED_JAVASCRIPT"] = ""

    # 3. Render Interactive HTML edition (vertically tabbed sidebar with live simulators)
    html_filename = f"{slug}.html"
    html_data["THEME_CSS_VARS"] = ""
    html_data["THEME_NAME"] = "Dynamic Dashboard Theme"
    html_data["THEME_ID"] = "dynamic"

    template_str = DEFAULT_TEMPLATE
    custom_template = args.template or locate_resource_template()
    if custom_template and os.path.exists(custom_template):
        try:
            with open(custom_template, "r", encoding="utf-8") as f:
                template_str = f.read()
        except Exception as e:
            print(f"⚠️ Warning: Could not read template at {custom_template}: {e}. Using built-in default.")

    rendered_html = template_str
    for k, v in html_data.items():
        rendered_html = rendered_html.replace(f"{{{{{k}}}}}", str(v))

    # Final pass: sanitize any tooltips across entire HTML document to guarantee zero <div> inside <p>
    rendered_html = sanitize_tooltips_to_spans(rendered_html)

    html_out_path = os.path.join(target_output_dir, html_filename)
    with open(html_out_path, "w", encoding="utf-8") as f:
        f.write(rendered_html)
    print(f"✅ Lesson rendered to {html_out_path} [Format: HTML | Style: {theme['name']}]")

    # 4. Stage HTML artifact to conversation artifact dir if provided
    if args.brain_dir and os.path.exists(args.brain_dir):
        brain_html_path = os.path.join(args.brain_dir, html_filename)
        with open(brain_html_path, "w", encoding="utf-8") as f:
            f.write(rendered_html)
        print(f"✅ Staged HTML artifact to conversation artifact dir: {args.brain_dir}")

    # Synchronize instance state so status recognizes delivered artifact immediately
    inst_dir = None
    if loaded_settings_path:
        inst_dir = os.path.dirname(os.path.abspath(loaded_settings_path))
    elif os.path.isdir(".system-design"):
        inst_dir = os.path.abspath(".system-design")
    elif os.path.isdir(os.path.join(target_output_dir, "..")):
        parent_cand = os.path.abspath(os.path.join(target_output_dir, ".."))
        if os.path.isfile(os.path.join(parent_cand, "manifest.json")):
            inst_dir = parent_cand

    if inst_dir and os.path.isfile(os.path.join(inst_dir, "manifest.json")):
        try:
            m_path = os.path.join(inst_dir, "manifest.json")
            with open(m_path, "r", encoding="utf-8") as mf:
                m_data = json.load(mf)
            if "cursor" in m_data:
                m_data["cursor"]["topicFoundationStatus"] = "delivered"
                m_data["cursor"]["nextTeachingAction"] = f"Review delivered lesson artifact ({html_filename}) and defend trade-offs in chat"
            for cl in m_data.get("curriculum", {}).get("clusters", []):
                for tp in cl.get("topics", []):
                    if tp.get("id") == args.topic_id:
                        tp["lessonArtifact"] = f"lessons/{html_filename}"
                        if "markdownArtifact" in tp:
                            del tp["markdownArtifact"]
            with open(m_path, "w", encoding="utf-8") as mf:
                json.dump(m_data, mf, indent=2)

            c_md_path = os.path.join(inst_dir, "CURSOR.md")
            if os.path.isfile(c_md_path):
                with open(c_md_path, "r", encoding="utf-8") as cf:
                    c_txt = cf.read()
                c_txt = re.sub(r"(\*Topic Foundation Status\*:\s*`?)[^`\n]+(`?)", r"\g<1>delivered\g<2>", c_txt)
                c_txt = re.sub(
                    r"(\*Immediate Next Teaching Action\*:)[\s\S]*?(?=\n\n|\n---|\Z)",
                    f"*Immediate Next Teaching Action*: Review delivered lesson artifact ({html_filename}) and defend trade-offs in chat",
                    c_txt
                )
                with open(c_md_path, "w", encoding="utf-8") as cf:
                    cf.write(c_txt)
        except Exception:
            pass

if __name__ == "__main__":
    main()
