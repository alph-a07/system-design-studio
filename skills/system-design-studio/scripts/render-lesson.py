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

# Invariant cohesive fallback template matching resources/lesson-template.html
DEFAULT_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{PAGE_TITLE}}</title>
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
  <style>
    @keyframes pulse-subtle {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.85; transform: scale(0.98); }
    }
    .animate-pulse-subtle { animation: pulse-subtle 2.5s infinite ease-in-out; }
    .interactive-element { transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1); }
    /* Dynamic Theme Variables (Delegated to SDS Dashboard) */
    :root {
      --background: transparent;
      --foreground: inherit;
      --card: transparent;
      --card-border: rgba(128, 128, 128, 0.2);
      --border: rgba(128, 128, 128, 0.2);
      --muted-foreground: inherit;
      --primary: #2563eb;
      --primary-hover: #1d4ed8;
      --accent-badge: rgba(37, 99, 235, 0.1);
      --accent-badge-text: #2563eb;
    }
    /* Scrollbar styling */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: var(--background, transparent); }
    ::-webkit-scrollbar-thumb { background: var(--card-border, #cbd5e1); border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: var(--muted-foreground, #94a3b8); }
    /* Universal Responsive Layout */
    body { background-color: var(--background, transparent); color: var(--foreground, inherit); font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; line-height: 1.6; margin: 0; padding: 1.5rem; }
    .max-w-4xl { max-width: 56rem; margin-left: auto; margin-right: auto; }
    .space-y-12 > * + * { margin-top: 3rem; }
    .space-y-8 > * + * { margin-top: 2rem; }
    .space-y-6 > * + * { margin-top: 1.5rem; }
    .space-y-4 > * + * { margin-top: 1rem; }
    .space-y-2 > * + * { margin-top: 0.5rem; }
    .flex { display: flex; }
    .flex-wrap { flex-wrap: wrap; }
    .items-center { align-items: center; }
    .justify-between { justify-content: space-between; }
    .gap-2 { gap: 0.5rem; }
    .gap-4 { gap: 1rem; }
    .gap-6 { gap: 1.5rem; }
    .grid { display: grid; gap: 1rem; }
    .grid-cols-1 { grid-template-columns: repeat(1, minmax(0, 1fr)); }
    @media (min-width: 768px) {
      .md\:grid-cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .md\:grid-cols-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
      .md\:p-8 { padding: 2rem; }
      .md\:text-5xl { font-size: 3rem; line-height: 1; }
      .md\:text-2xl { font-size: 1.5rem; }
    }
    .rounded-xl { border-radius: 0.75rem; }
    .rounded-lg { border-radius: 0.5rem; }
    .rounded-full { border-radius: 9999px; }
    .font-mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }
    button { cursor: pointer; border: none; font-family: inherit; }
    .narrative-prose { color: var(--foreground); line-height: 1.85; font-size: 1.025rem; }
    .narrative-prose p { margin-bottom: 1.35rem; }
    .narrative-prose strong { color: var(--foreground); font-weight: 700; }
    .narrative-prose code { background: var(--card); border: 1px solid var(--card-border); padding: 0.2rem 0.4rem; border-radius: 0.375rem; font-family: ui-monospace, monospace; font-size: 0.85em; }
    .editorial-lead { font-size: 1.15rem; line-height: 1.8; color: var(--foreground); font-weight: 400; border-left: 3px solid var(--primary); padding-left: 1.25rem; margin: 1.5rem 0 2rem 0; }
    .jargon-card { background: rgba(245, 158, 11, 0.06); border: 1px solid rgba(245, 158, 11, 0.35); border-radius: 0.875rem; padding: 1rem 1.25rem; margin: 1.5rem 0; }
    .jargon-header { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.4rem; }
    .jargon-title { font-family: ui-monospace, monospace; font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #fbbf24; }
    .jargon-pill { font-size: 0.7rem; padding: 0.1rem 0.45rem; border-radius: 9999px; background: rgba(245, 158, 11, 0.2); color: #fde68a; font-family: ui-monospace, monospace; }
    .jargon-body { font-size: 0.925rem; line-height: 1.6; color: var(--foreground); margin: 0; }
    .analogy-card { background: rgba(59, 130, 246, 0.06); border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 0.875rem; padding: 1.25rem 1.5rem; margin: 1.5rem 0; }
    .analogy-header { display: flex; align-items: center; gap: 0.5rem; font-family: ui-monospace, monospace; font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #60a5fa; margin-bottom: 0.5rem; }
    .analogy-body { font-size: 0.95rem; line-height: 1.7; color: var(--foreground); margin: 0; }
    .aha-card { background: rgba(16, 185, 129, 0.07); border: 1px solid rgba(16, 185, 129, 0.35); border-radius: 0.875rem; padding: 1.25rem 1.5rem; margin: 1.5rem 0; }
    .aha-header { display: flex; align-items: center; gap: 0.5rem; font-family: ui-monospace, monospace; font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #34d399; margin-bottom: 0.5rem; }
    .aha-body { font-size: 0.95rem; line-height: 1.7; color: var(--foreground); margin: 0; }
    .callout-box { background: var(--card); border: 1px solid var(--card-border); border-radius: 1rem; padding: 1.25rem 1.5rem; margin: 1.5rem 0; }
    .callout-dilemma { border-left: 4px solid #ef4444; }
    .callout-mechanism { border-left: 4px solid var(--primary); }
    .callout-invariant { border-left: 4px solid #10b981; }
    .callout-trap { border-left: 4px solid #f59e0b; }
    .sim-container { background: var(--card); border: 1px solid var(--card-border); border-radius: 1rem; padding: 1.25rem; margin: 1.75rem 0; box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.2); }
    .sim-canvas { background: var(--background); border: 1px solid var(--border); border-radius: 0.75rem; padding: 1.25rem; }
    .sim-log { background: var(--background); border: 1px solid var(--border); border-radius: 0.5rem; font-family: ui-monospace, monospace; font-size: 0.75rem; padding: 0.75rem; max-height: 8rem; overflow-y: auto; }
    .tradeoff-table { width: 100%; text-align: left; border-collapse: separate; border-spacing: 0; border-radius: 0.75rem; overflow: hidden; border: 1px solid var(--card-border); margin: 1.5rem 0; font-size: 0.85rem; }
    .tradeoff-table th { background: var(--card); padding: 0.75rem 1rem; font-family: ui-monospace, monospace; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 1px solid var(--border); color: var(--muted-foreground); }
    .tradeoff-table td { padding: 0.75rem 1rem; border-bottom: 1px solid var(--border); color: var(--foreground); }
    .tradeoff-table tr:last-child td { border-bottom: none; }

    /* Clean, content-hugging text selection inside lessons */
    html::selection,
    body::selection,
    main::selection,
    section::selection,
    article::selection,
    header::selection,
    footer::selection {
      background-color: transparent !important;
    }
    ::selection {
      background-color: rgba(0, 229, 255, 0.28) !important;
      color: inherit !important;
    }
    p, .editorial-lead, h1, h2, h3, h4, h5, h6, li, blockquote,
    .notion-p, .notion-h1, .notion-h2, .notion-h3 {
      width: fit-content;
      max-width: 100%;
    }
  </style>
</head>
<body class="bg-[var(--background)] text-[var(--foreground)] font-sans antialiased p-4 md:p-8 min-h-screen">

  <div class="max-w-4xl mx-auto space-y-12">
    <!-- HERO HEADER: CONTEXTUAL ORIENTATION -->
    <header class="border-b border-[var(--border)] pb-8 space-y-4">
      <div class="flex flex-wrap items-center gap-2">
        <span class="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-[var(--primary)] text-white tracking-wide uppercase">{{TIER_BADGE}}</span>
        <span class="px-2.5 py-0.5 text-xs font-medium rounded-full bg-[var(--card)] border border-[var(--card-border)] text-[var(--muted-foreground)]">{{CLUSTER_BADGE}}</span>
        <span class="px-2.5 py-0.5 text-xs font-medium rounded-full bg-[var(--card)] border border-[var(--card-border)] text-[var(--muted-foreground)]">⚡ First-Principles Systems</span>
        <span class="px-2.5 py-0.5 text-xs font-medium rounded-full bg-emerald-950/40 border border-emerald-800 text-emerald-400 flex items-center gap-1.5">
          <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
          Live Interactive Simulator
        </span>
      </div>
      <h1 class="text-3xl md:text-5xl font-black tracking-tight text-[var(--foreground)]">{{LESSON_TITLE}}</h1>
      <p class="text-base md:text-lg text-[var(--muted-foreground)] leading-relaxed max-w-3xl">{{LESSON_SUBTITLE}}</p>
    </header>

    <main class="space-y-12">
      <!-- PHASE 1: BACKGROUND CONTEXT & FORCING DILEMMA (WHYs & optional WHENs) -->
      <section class="space-y-4">
        <h2 class="text-xl md:text-2xl font-bold tracking-tight text-[var(--foreground)] flex items-center gap-2">{{SECTION_1_TITLE}}</h2>
        <div class="narrative-prose">{{SECTION_1_BODY}}</div>
      </section>

      <!-- PHASE 2: THE ACTIVE TOPIC & SURROUNDING LANDSCAPE (WHATs & optional WHEREs) -->
      <section class="space-y-4 border-t border-[var(--border)] pt-8">
        <h2 class="text-xl md:text-2xl font-bold tracking-tight text-[var(--foreground)] flex items-center gap-2">{{SECTION_2_TITLE}}</h2>
        <div class="narrative-prose">{{SECTION_2_BODY}}</div>
      </section>

      <!-- PHASE 3: INTERNAL MECHANICS, INVARIANTS & CAUSALITY (HOWs & WHYs OF HOWs) -->
      <section class="space-y-4 border-t border-[var(--border)] pt-8">
        <h2 class="text-xl md:text-2xl font-bold tracking-tight text-[var(--foreground)] flex items-center gap-2">{{SECTION_3_TITLE}}</h2>
        <div class="narrative-prose">{{SECTION_3_BODY}}</div>
      </section>

      <!-- PHASE 4: MENTAL MODEL SYNTHESIS & PRODUCTION CORRELATION -->
      <section class="space-y-4 border-t border-[var(--border)] pt-8">
        <h2 class="text-xl md:text-2xl font-bold tracking-tight text-[var(--foreground)] flex items-center gap-2">{{SECTION_4_TITLE}}</h2>
        <div class="narrative-prose">{{SECTION_4_BODY}}</div>
      </section>

      <!-- PHASE 5: CONTEXTUAL SIGN-OFF VERIFICATION GATE -->
      <section class="space-y-4 border-t border-[var(--border)] pt-8">
        <h2 class="text-xl md:text-2xl font-bold tracking-tight text-[var(--foreground)] flex items-center gap-2">{{SECTION_5_TITLE}}</h2>
        <div class="narrative-prose">{{SECTION_5_BODY}}</div>
      </section>
    </main>

    <!-- FOOTER NAV: RUNNING CONTEXT & COGNITIVE LINEAGE -->
    <footer class="border-t border-[var(--border)] pt-8 pb-12 flex flex-col md:flex-row items-center justify-between text-xs text-[var(--muted-foreground)] gap-4">
      <div>Part of <span class="font-semibold text-[var(--foreground)]">System Design Studio</span> · Project Learning Instance</div>
      <div class="flex items-center gap-4 font-mono text-[11px]">
        <span>Backward Anchor: <strong class="text-[var(--foreground)]">{{BACKWARD_ANCHOR}}</strong></span>
        <span>•</span>
        <span>Next Hook: <strong class="text-[var(--foreground)]">{{FORWARD_HOOK}}</strong></span>
      </div>
    </footer>
  </div>

  <script>
    {{EMBEDDED_JAVASCRIPT}}
  </script>

</body>
</html>
"""

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
    if not html:
        return ""
    # Strip scripts and styles
    cleaned = re.sub(r'<(script|style)[^>]*>[\s\S]*?</\1>', '', html, flags=re.IGNORECASE)
    # Strip simulator UI containers completely
    cleaned = re.sub(r'<!-- Inline Embedded Execution Simulator -->[\s\S]*?(?=<div class="callout-box|\Z)', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'<div class="sim-container"[\s\S]*?(?=<div class="callout-box|\Z)', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'Click [\'"]Step Forward[\'"][^\n\.]*\.?', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'<!--[\s\S]*?-->', '', cleaned)
    # Convert HTML tables to Markdown pipe syntax before tag stripping
    cleaned = re.sub(r'<table[^>]*>[\s\S]*?</table>', html_table_to_markdown, cleaned, flags=re.IGNORECASE)
    # Block conversions
    cleaned = re.sub(r'</?(?:p|div|h\d|section|article)[^>]*>', '\n', cleaned)
    cleaned = re.sub(r'<br\s*/?>', '\n', cleaned)
    # Inline code
    cleaned = re.sub(r'<code[^>]*>(.*?)</code>', r'`\1`', cleaned)
    # Bold / Strong
    cleaned = re.sub(r'<(?:strong|b)[^>]*>(.*?)</(?:strong|b)>', r'**\1**', cleaned)
    # Strip any remaining tags
    cleaned = re.sub(r'<[^>]+>', '', cleaned)
    # Strip residual simulator buttons or status text if any slipped through
    cleaned = re.sub(r'^\s*(?:Step Forward\s*→?|Reset|STATE:\s*[A-Z\s\(\)]+|UNRELIABLE TRANSIT LINK|Sender\s*/\s*Host\s*[A-Z]|Receiver\s*/\s*Host\s*[A-Z])\s*$', '', cleaned, flags=re.MULTILINE)
    # Collapse multiple blank lines
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    return cleaned.strip()

def render_markdown_lesson(data, topic_id, theme_name):
    """
    Renders pure GitHub Flavored Markdown lesson artifact without raw HTML or JavaScript.
    Embeds Mermaid diagrams, ASCII state trace tables, and unassisted sign-off scenarios.
    """
    title = data.get("LESSON_TITLE", "System Design Lesson")
    subtitle = data.get("LESSON_SUBTITLE", "")
    tier = data.get("TIER_BADGE", "Tier")
    cluster = data.get("CLUSTER_BADGE", "Cluster")
    depth = data.get("DEPTH_MARKERS", "[mechanics]")

    dilemma_title = data.get("SECTION_1_TITLE", "1. The Inception & Forcing Problem")
    dilemma_body = clean_html_to_markdown(data.get("SECTION_1_BODY", ""))

    placement_title = data.get("SECTION_2_TITLE", "2. Core Architectural Abstraction")
    placement_body = clean_html_to_markdown(data.get("SECTION_2_BODY", ""))

    mechanics_title = data.get("SECTION_3_TITLE", "3. Internal Mechanics & Causality")
    mechanics_body = clean_html_to_markdown(data.get("SECTION_3_BODY", ""))

    mental_title = data.get("SECTION_4_TITLE", "4. Mental Model Synthesis & Production Grounding")
    mental_body = clean_html_to_markdown(data.get("SECTION_4_BODY", ""))

    signoff_title = data.get("SECTION_5_TITLE", "5. Contextual Sign-Off Verification Gate")
    signoff_body = clean_html_to_markdown(data.get("SECTION_5_BODY", ""))

    md = []
    md.append(f"# {title}\n")
    md.append(f"> **Hierarchy**: {tier} ➔ {cluster}  \n> **Depth**: `{depth}` | **Format**: Clean Markdown (Zero-JS)\n")
    if subtitle:
        md.append(f"*{subtitle}*\n")
    md.append("---\n")

    md.append(f"## {dilemma_title}\n")
    md.append(f"{dilemma_body}\n")

    md.append(f"## {placement_title}\n")
    md.append(f"{placement_body}\n")

    md.append(f"## {mechanics_title}\n")
    md.append(f"{mechanics_body}\n")

    # Embedded Mermaid Protocol Sequence Diagram
    md.append("### Protocol & State Machine Transition")
    md.append("```mermaid")
    md.append("sequenceDiagram")
    md.append("    autonumber")
    md.append("    actor Client as Sender / Client Node")
    md.append("    participant Network as Physical Network (RTT ~ 50ms)")
    md.append("    actor Server as Receiver / Server Replica")
    md.append("")
    md.append("    Client->>Network: Packet / Handshake SYN (SEQ = 100)")
    md.append("    Network->>Server: In-flight transit (RTT/2)")
    md.append("    Note over Server: Allocate Socket Buffer & Parse Headers")
    md.append("    Server->>Network: ACK / Response (ACK = 101, WIN = 65535)")
    md.append("    Network->>Client: In-flight transit (RTT/2)")
    md.append("    Note over Client: Sliding Window Advanced")
    md.append("```\n")

    # ASCII Hardware State Trace
    md.append("### Hardware & Buffer State Trace")
    md.append("```text")
    md.append("+-----------------------------------------------------------------+")
    md.append("| INVARIANT: Speed of Light in Silica ~ 5 μs/km                  |")
    md.append("| TRANSIT:   Trans-Atlantic RTT ~ 70 ms | Local DC RTT ~ 0.5 ms   |")
    md.append("+-----------------------------------------------------------------+")
    md.append("| [Sender Socket Buffer] --------> [Kernel NIC Ring Buffer]       |")
    md.append("|          |                                  |                   |")
    md.append("|    (Write to FD)                    (Packet Serialization)      |")
    md.append("|          v                                  v                   |")
    md.append("| [TCP TX Queue: 64KB]             [Wire: IP/TCP Frame Header]   |")
    md.append("+-----------------------------------------------------------------+")
    md.append("```\n")

    md.append(f"## {mental_title}\n")
    md.append(f"{mental_body}\n")

    md.append("### Architectural Trade-Off Invariant Matrix")
    md.append("| Dimension | Primary Architectural Mechanism | Uncoordinated / Naive Alternative |")
    md.append("| :--- | :--- | :--- |")
    md.append("| **Latency Floor** | Predictable bound under normal conditions | Low initial RTT, catastrophic jitter on drop |")
    md.append("| **Coordination Cost** | Strict ordering & write amplification | Split-brain risk, out-of-order anomalies |")
    md.append("| **Failure Domain** | Bounded blast radius via timeouts & WAL | Cascading failure under thundering herd |\n")

    md.append(f"## {signoff_title}\n")
    md.append("> [!IMPORTANT]")
    md.append("> **UNASSISTED SIGN-OFF CHALLENGE (DEFEND IN CHAT)**")
    md.append(f"> {signoff_body}")
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
    jargon_cards = re.findall(r'class=["\'][^"\']*(?:jargon-card|jargon-pill|jargon-box)[^"\']*["\']', narrative_text)
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

    if output_format == "markdown":
        filename = f"{slug}.md"
        rendered = render_markdown_lesson(data, args.topic_id, theme["name"])
        out_path = os.path.join(target_output_dir, filename)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(rendered)
        print(f"✅ Lesson rendered to {out_path} [Format: Markdown Clean]")
    else:
        filename = f"{slug}.html"
        # Theming is delegated dynamically to dashboard based on live theme preset
        data["THEME_CSS_VARS"] = ""
        data["THEME_NAME"] = "Dynamic Dashboard Theme"
        data["THEME_ID"] = "dynamic"

        template_str = DEFAULT_TEMPLATE
        custom_template = args.template or locate_resource_template()
        if custom_template and os.path.exists(custom_template):
            try:
                with open(custom_template, "r", encoding="utf-8") as f:
                    template_str = f.read()
            except Exception as e:
                print(f"⚠️ Warning: Could not read template at {custom_template}: {e}. Using built-in default.")

        rendered = template_str
        for k, v in data.items():
            rendered = rendered.replace(f"{{{{{k}}}}}", str(v))

        out_path = os.path.join(target_output_dir, filename)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(rendered)
        print(f"✅ Lesson rendered to {out_path} [Format: HTML | Style: {theme['name']}]")

    if args.brain_dir and os.path.exists(args.brain_dir):
        brain_path = os.path.join(args.brain_dir, filename)
        with open(brain_path, "w", encoding="utf-8") as f:
            f.write(rendered)
        print(f"✅ Staged to conversation artifact dir: {brain_path}")

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
                m_data["cursor"]["nextTeachingAction"] = f"Review delivered lesson artifact ({filename}) and engage in Socratic dialectic defense via /sds-discuss"
            for cl in m_data.get("curriculum", {}).get("clusters", []):
                for tp in cl.get("topics", []):
                    if tp.get("id") == args.topic_id:
                        tp["lessonArtifact"] = f"lessons/{filename}"
            with open(m_path, "w", encoding="utf-8") as mf:
                json.dump(m_data, mf, indent=2)

            c_md_path = os.path.join(inst_dir, "CURSOR.md")
            if os.path.isfile(c_md_path):
                with open(c_md_path, "r", encoding="utf-8") as cf:
                    c_txt = cf.read()
                c_txt = re.sub(r"(\*Topic Foundation Status\*:\s*`?)[^`\n]+(`?)", r"\g<1>delivered\g<2>", c_txt)
                c_txt = re.sub(
                    r"(\*Immediate Next Teaching Action\*:)[\s\S]*?(?=\n\n|\n---|\Z)",
                    f"*Immediate Next Teaching Action*: Review delivered lesson artifact ({filename}) and engage in Socratic dialectic defense via /sds-discuss",
                    c_txt
                )
                with open(c_md_path, "w", encoding="utf-8") as cf:
                    cf.write(c_txt)
        except Exception:
            pass

if __name__ == "__main__":
    main()
