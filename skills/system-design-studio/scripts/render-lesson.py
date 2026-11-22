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

    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>{{PAGE_TITLE}}</title></head><body><h1>{{LESSON_TITLE}}</h1><div>{{SECTION_1_BODY}}{{SECTION_2_BODY}}{{SECTION_3_BODY}}{{SECTION_4_BODY}}{{SECTION_5_BODY}}</div></body></html>"""

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

def transform_jargons_to_tooltips(html):
    """
    Transforms verbose inline jargon cards into non-disruptive inline tooltip cues with popovers.
    Preserves 100% of the plain-English definitions while keeping reading flow unbroken.
    """
    if not html:
        return ""
    pattern = r'<div class=[\"\']jargon-card[\"\']>[\s\S]*?<span class=[\"\']jargon-title[\"\']>([\s\S]*?)</span>[\s\S]*?<span class=[\"\']jargon-pill[\"\']>([\s\S]*?)</span>[\s\S]*?<div class=[\"\']jargon-body[\"\']>([\s\S]*?)</div>\s*</div>'
    def repl(m):
        t = re.sub(r'<[^>]+>', '', m.group(1)).replace('💡', '').replace('Jargon Unpacked:', '').strip()
        p = re.sub(r'<[^>]+>', '', m.group(2)).strip()
        b = m.group(3).strip()
        return f'''<span class="jargon-tooltip-wrapper" tabindex="0">
  <span class="jargon-pill-cue" onclick="toggleJargonTooltip(this, event)">
    <span class="jargon-icon">💡</span>
    <span class="jargon-term-name">{t}</span>
    <span class="jargon-type-pill">{p}</span>
  </span>
  <span class="jargon-popover-card">
    <span class="jargon-popover-header">
      <span class="jargon-popover-title">💡 {t}</span>
      <span class="jargon-popover-badge">{p}</span>
    </span>
    <span class="jargon-popover-body">{b}</span>
  </span>
</span>'''
    return re.sub(pattern, repl, html)

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
    Converts callouts to GitHub alerts, jargon cards to structured blockquotes, and tables to markdown syntax.
    """
    if not html:
        return ""
    text = html

    # Simulator handling: provide a structured walkthrough rather than leaving an empty gap
    if 'sim-container' in text:
        sim_summary = (
            "\n> [!NOTE] Interactive Simulation Walkthrough\n"
            "> *The interactive HTML edition provides a live tactile simulator for this mechanism. Key invariants modeled:*\n"
            "> - Packet flight across physical network link bound by speed-of-light propagation latency.\n"
            "> - Under packet drops, observing kernel buffer hold vs. immediate uncoordinated pass-through.\n"
            "> - Reassembly, Head-of-Line blocking stalls, and retransmission recovery dynamics.\n"
        )
        text = re.sub(r'<div class=[\"\']sim-container[\"\']>[\s\S]*?</div>\s*(?=<div class="callout-box"|</div>|\Z)', sim_summary, text)

    # Convert Jargon Cards to structured markdown callouts
    def jargon_sub(m):
        t = re.sub(r'<[^>]+>', '', m.group(1)).replace('💡', '').replace('Jargon Unpacked:', '').strip()
        p = re.sub(r'<[^>]+>', '', m.group(2)).strip()
        b = re.sub(r'</?p[^>]*>', '\n', m.group(3))
        b = re.sub(r'<[^>]+>', '', b).strip()
        b_lines = '\n> '.join([line.strip() for line in b.split('\n') if line.strip()])
        return f"\n> 💡 **Jargon Unpacked: {t}** *({p})*\n> {b_lines}\n"
    text = re.sub(r'<div class=[\"\']jargon-card[\"\']>[\s\S]*?<span class=[\"\']jargon-title[\"\']>([\s\S]*?)</span>[\s\S]*?<span class=[\"\']jargon-pill[\"\']>([\s\S]*?)</span>[\s\S]*?<div class=[\"\']jargon-body[\"\']>([\s\S]*?)</div>\s*</div>', jargon_sub, text)

    # Convert Callout Boxes to GitHub alerts
    for kind, alert in [('callout-dilemma', 'WARNING'), ('callout-mechanism', 'NOTE'), ('callout-invariant', 'IMPORTANT'), ('callout-trap', 'CAUTION')]:
        def callout_sub(m, a=alert, k=kind):
            c = re.sub(r'</?p[^>]*>', '\n', m.group(1))
            c = re.sub(r'<[^>]+>', '', c).strip()
            lines = '\n> '.join([line.strip() for line in c.split('\n') if line.strip()])
            title = k.replace('callout-', '').capitalize()
            return f"\n> [!{a}] {title}\n> {lines}\n"
        text = re.sub(rf'<div class=[\"\']callout-box\s+{kind}[\"\']>([\s\S]*?)</div>', callout_sub, text)

    # Convert Analogy & Breakthrough Cards
    def analogy_sub(m):
        c = re.sub(r'</?p[^>]*>', '\n', m.group(1))
        c = re.sub(r'<[^>]+>', '', c).strip()
        lines = '\n> '.join([line.strip() for line in c.split('\n') if line.strip()])
        return f"\n> [!TIP] Intuitive Analogy\n> {lines}\n"
    text = re.sub(r'<div class=[\"\']analogy-card[\"\']>[\s\S]*?<div class=[\"\']analogy-body[\"\']>([\s\S]*?)</div>\s*</div>', analogy_sub, text)

    def aha_sub(m):
        c = re.sub(r'</?p[^>]*>', '\n', m.group(1))
        c = re.sub(r'<[^>]+>', '', c).strip()
        lines = '\n> '.join([line.strip() for line in c.split('\n') if line.strip()])
        return f"\n> [!NOTE] Breakthrough Realization\n> {lines}\n"
    text = re.sub(r'<div class=[\"\']aha-card[\"\']>[\s\S]*?<div class=[\"\']aha-body[\"\']>([\s\S]*?)</div>\s*</div>', aha_sub, text)

    # Convert Editorial Lead
    def lead_sub(m):
        c = re.sub(r'<[^>]+>', '', m.group(1)).strip()
        return f"\n> *{c}*\n"
    text = re.sub(r'<div class=[\"\']editorial-lead[\"\']>([\s\S]*?)</div>', lead_sub, text)

    # Strip scripts, styles, comments
    text = re.sub(r'<(script|style)[^>]*>[\s\S]*?</\1>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<!--[\s\S]*?-->', '', text)

    # Convert HTML tables to Markdown pipe syntax
    text = re.sub(r'<table[^>]*>[\s\S]*?</table>', html_table_to_markdown, text, flags=re.IGNORECASE)

    # Inline formatting
    text = re.sub(r'<code[^>]*>(.*?)</code>', r'`\1`', text)
    text = re.sub(r'<(?:strong|b)[^>]*>(.*?)</(?:strong|b)>', r'**\1**', text)
    text = re.sub(r'<(?:em|i)[^>]*>(.*?)</(?:em|i)>', r'*\1*', text)

    # Block conversions
    text = re.sub(r'</?(?:p|div|h\d|section|article)[^>]*>', '\n', text)
    text = re.sub(r'<br\s*/?>', '\n', text)

    # Strip any remaining tags
    text = re.sub(r'<[^>]+>', '', text)

    # Collapse multiple blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def render_markdown_lesson(data, topic_id, theme_name="Clean Markdown"):
    """
    Renders pure GitHub Flavored Markdown lesson artifact from JSON payload.
    Preserves 100% of first-principles depth, mathematical derivations, and sign-off defense gates.
    """
    title = data.get("LESSON_TITLE", "System Design Lesson")
    subtitle = data.get("LESSON_SUBTITLE", "")
    tier = data.get("TIER_BADGE", "Tier 0 · System Design Core")
    cluster = data.get("CLUSTER_BADGE", "Cluster")
    backward = data.get("BACKWARD_ANCHOR", "")
    forward = data.get("FORWARD_HOOK", "")

    sec1_title = strip_section_index(data.get("SECTION_1_TITLE", "Physical Dilemma & Inception"))
    sec1_body = clean_html_to_markdown(data.get("SECTION_1_BODY", ""))

    sec2_title = strip_section_index(data.get("SECTION_2_TITLE", "System Architecture & Placement"))
    sec2_body = clean_html_to_markdown(data.get("SECTION_2_BODY", ""))

    sec3_title = strip_section_index(data.get("SECTION_3_TITLE", "Internal Mechanics & Causality"))
    sec3_body = clean_html_to_markdown(data.get("SECTION_3_BODY", ""))

    sec4_title = strip_section_index(data.get("SECTION_4_TITLE", "Production Grounding & Mental Model"))
    sec4_body = clean_html_to_markdown(data.get("SECTION_4_BODY", ""))

    sec5_title = strip_section_index(data.get("SECTION_5_TITLE", "Architectural Defense Challenge"))
    sec5_body = clean_html_to_markdown(data.get("SECTION_5_BODY", ""))

    md = []
    md.append(f"# {title}\n")
    md.append(f"> **Hierarchy**: {tier} ➔ {cluster}  \n> **Topic ID**: `{topic_id}` | **Format**: Complete Markdown Edition\n")
    if subtitle:
        md.append(f"*{subtitle}*\n")
    md.append("---\n")

    if backward or forward:
        md.append(f"> **Backward Anchor**: {backward}  \n> **Forward Hook**: {forward}\n")
        md.append("---\n")

    md.append(f"## {sec1_title}\n")
    md.append(f"{sec1_body}\n")
    md.append("\n---\n")

    md.append(f"## {sec2_title}\n")
    md.append(f"{sec2_body}\n")
    md.append("\n---\n")

    md.append(f"## {sec3_title}\n")
    md.append(f"{sec3_body}\n")

    # Embedded Mermaid Protocol Sequence Diagram
    mermaid_block = data.get("MERMAID_DIAGRAM")
    if not mermaid_block:
        mermaid_block = """sequenceDiagram
    autonumber
    actor Client as Sender / Client Node
    participant Network as Physical Network (RTT ~ 50ms)
    actor Server as Receiver / Server Replica

    Client->>Network: Packet / Handshake SYN (SEQ = 100)
    Network->>Server: In-flight transit (RTT/2)
    Note over Server: Allocate Socket Buffer & Parse Headers
    Server->>Network: ACK / Response (ACK = 101, WIN = 65535)
    Network->>Client: In-flight transit (RTT/2)
    Note over Client: Sliding Window Advanced"""
    md.append("### Protocol & State Machine Transition")
    md.append("```mermaid")
    md.append(mermaid_block.strip())
    md.append("```\n")
    md.append("\n---\n")

    md.append(f"## {sec4_title}\n")
    md.append(f"{sec4_body}\n")
    md.append("\n---\n")

    md.append(f"## {sec5_title}\n")
    md.append("> [!IMPORTANT]")
    md.append("> **ARCHITECTURAL DEFENSE GATE (DEFEND IN CHAT)**")
    md.append(f">\n{sec5_body}\n")
    md.append(">\n> *Analyze the scenario above and defend your architectural recommendations cold in chat discussion to achieve topic sign-off.*\n")

    return "\n".join(md)

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

def audit_lesson_payload(data, topic_id=None, inst_dir=None):
    """
    Automated pre-flight pedagogical quality linter.
    Enforces the Explainer's Contract, Anti-Compression Invariant,
    Jargon-Unpacking coverage, and Gate Alignment across all authored lessons.
    """
    audit_passes = []
    audit_warnings = []

    # 1. Word count & Anti-Compression check
    narrative_text = " ".join([
        str(data.get(f"SECTION_{i}_BODY", "")) for i in range(1, 6)
    ])
    clean_words = re.findall(r"\b[A-Za-z0-9_-]+\b", re.sub(r"<[^>]+>", " ", narrative_text))
    word_count = len(clean_words)

    if word_count < 1800:
        audit_warnings.append(
            f"Premature Compression / Cheat Sheet Risk: Word count is {word_count} (< 2,000 words). "
            "Expand explanations, step-by-step traces, and analogies with full breathing room."
        )
    else:
        audit_passes.append(f"Depth & Anti-Compression: Robust narrative ({word_count} words)")

    # 2. Jargon Unpacking Check
    jargon_cards = re.findall(r'class=["\'][^"\']*(?:jargon-card|jargon-pill|jargon-box|jargon-tooltip-wrapper|jargon-pill-cue)[^"\']*["\']', narrative_text)
    if len(jargon_cards) < 3:
        audit_warnings.append(
            f"Low Jargon Unpacking Density: Only {len(jargon_cards)} jargon callout elements (<div class=\"jargon-card|jargon-pill|jargon-box\">) found. "
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
    parser = argparse.ArgumentParser(description="Render interactive HTML or pure Markdown lesson artifact")
    parser.add_argument("--topic-id", required=True, help="Topic ID (e.g. topic.0.1.tcp-vs-udp)")
    parser.add_argument("--title", help="Lesson Title")
    parser.add_argument("--cluster", help="Cluster Title")
    parser.add_argument("--tier", help="Tier Title")
    parser.add_argument("--style", choices=list(STYLE_THEMES.keys()), help="Artifact visual style theme")
    parser.add_argument("--format", choices=["html", "markdown"], help="Output artifact format (html or markdown)")
    parser.add_argument("--instance-dir", "--settings", dest="settings", help="Path to settings.json or .system-design directory")
    parser.add_argument("--data-file", "--spec", dest="data_file", help="Path to JSON file containing lesson content")
    parser.add_argument("--data", help="Inline JSON string or '-' to read lesson payload from stdin")
    parser.add_argument("--allow-reference-fixture", action="store_true", help="Internal/Test only: Allow direct rendering of static reference fixtures")
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

    data = normalized_data

    # Allow CLI overrides
    if args.title:
        data["LESSON_TITLE"] = args.title
    if args.tier:
        data["TIER_BADGE"] = args.tier
    if args.cluster:
        data["CLUSTER_BADGE"] = args.cluster

    # Legacy token fallback mappings
    if "REALITY_CHECK_SCENARIO" in data and "SECTION_5_BODY" not in data:
        data["SECTION_5_BODY"] = f"<p>{data['REALITY_CHECK_SCENARIO']}</p>"
    if "SIGN_OFF_SCENARIO" in data and "SECTION_5_BODY" not in data:
        data["SECTION_5_BODY"] = f"<p>{data['SIGN_OFF_SCENARIO']}</p>"

    # Run automated pedagogical quality audit on lesson payload
    audit_target_dir = loaded_settings_path and os.path.dirname(os.path.abspath(loaded_settings_path))
    audit_lesson_payload(data, args.topic_id, audit_target_dir or os.getcwd())

    slug = args.topic_id.replace("topic.", "").replace(".", "-")
    os.makedirs(target_output_dir, exist_ok=True)

    # 1. Strip numerical indexing from section titles for unindexed clean headings
    for i in range(1, 6):
        tk = f"SECTION_{i}_TITLE"
        if tk in data:
            data[tk] = strip_section_index(data[tk])

    # 2. Render Markdown edition (clean, comprehensive GFM with alert boxes and unpacked definitions)
    md_filename = f"{slug}.md"
    rendered_md = render_markdown_lesson(data, args.topic_id, theme["name"])
    md_out_path = os.path.join(target_output_dir, md_filename)
    with open(md_out_path, "w", encoding="utf-8") as f:
        f.write(rendered_md)
    print(f"✅ Lesson rendered to {md_out_path} [Format: Markdown Clean]")

    # 3. Transform HTML bodies: jargons into non-disruptive inline tooltip cues with popovers
    html_data = dict(data)
    for i in range(1, 6):
        bk = f"SECTION_{i}_BODY"
        if bk in html_data:
            html_data[bk] = transform_jargons_to_tooltips(html_data[bk])

    # 4. Render Interactive HTML edition (vertically tabbed sidebar with live simulators)
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

    html_out_path = os.path.join(target_output_dir, html_filename)
    with open(html_out_path, "w", encoding="utf-8") as f:
        f.write(rendered_html)
    print(f"✅ Lesson rendered to {html_out_path} [Format: HTML | Style: {theme['name']}]")

    # 5. Stage both formats to conversation artifact dir if provided
    if args.brain_dir and os.path.exists(args.brain_dir):
        brain_html_path = os.path.join(args.brain_dir, html_filename)
        brain_md_path = os.path.join(args.brain_dir, md_filename)
        with open(brain_html_path, "w", encoding="utf-8") as f:
            f.write(rendered_html)
        with open(brain_md_path, "w", encoding="utf-8") as f:
            f.write(rendered_md)
        print(f"✅ Staged HTML & Markdown artifacts to conversation artifact dir: {args.brain_dir}")

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
                m_data["cursor"]["nextTeachingAction"] = f"Review delivered lesson artifact ({html_filename}) and engage in Socratic dialectic defense via /sds-discuss"
            for cl in m_data.get("curriculum", {}).get("clusters", []):
                for tp in cl.get("topics", []):
                    if tp.get("id") == args.topic_id:
                        tp["lessonArtifact"] = f"lessons/{html_filename}"
                        tp["markdownArtifact"] = f"lessons/{md_filename}"
            with open(m_path, "w", encoding="utf-8") as mf:
                json.dump(m_data, mf, indent=2)

            c_md_path = os.path.join(inst_dir, "CURSOR.md")
            if os.path.isfile(c_md_path):
                with open(c_md_path, "r", encoding="utf-8") as cf:
                    c_txt = cf.read()
                c_txt = re.sub(r"(\*Topic Foundation Status\*:\s*`?)[^`\n]+(`?)", r"\g<1>delivered\g<2>", c_txt)
                c_txt = re.sub(
                    r"(\*Immediate Next Teaching Action\*:)[\s\S]*?(?=\n\n|\n---|\Z)",
                    f"*Immediate Next Teaching Action*: Review delivered lesson artifact ({html_filename}) and engage in Socratic dialectic defense via /sds-discuss",
                    c_txt
                )
                with open(c_md_path, "w", encoding="utf-8") as cf:
                    cf.write(c_txt)
        except Exception:
            pass

if __name__ == "__main__":
    main()
