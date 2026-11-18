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
        "css_vars": """
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
        "css_vars": """
    :root {
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
""",
        "badge_class": "bg-blue-700 text-white",
    },
    "midnight-neon": {
        "id": "midnight-neon",
        "name": "Cyber Obsidian (High Contrast)",
        "theme_type": "dark",
        "css_vars": """
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
        "css_vars": """
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
        "css_vars": """
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
    {{THEME_CSS_VARS}}
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: var(--background); }
    ::-webkit-scrollbar-thumb { background: var(--card-border); border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: var(--muted-foreground); }
    /* Offline Fallback Styles (Air-Gapped & CDN Resilience) */
    body { background-color: var(--background, #0f172a); color: var(--foreground, #f8fafc); font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; line-height: 1.6; margin: 0; padding: 1.5rem; }
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

    /* ══ BUILT-IN ACTIVE LEARNING HIGHLIGHTER ══════════════════════════ */
    mark[data-hl-id] {
      color: inherit;
      border-radius: 3px;
      cursor: pointer;
      padding: 1px 0;
      transition: filter 0.12s ease, box-shadow 0.12s ease;
      box-decoration-break: clone;
      -webkit-box-decoration-break: clone;
    }
    mark[data-hl-id].hl-hovered {
      filter: brightness(0.82) saturate(1.35);
      box-shadow: 0 1.5px 0 0 currentColor;
    }
    .hl-yellow { background-color: rgba(250, 204, 21, 0.40); }
    .hl-green  { background-color: rgba( 34, 197, 94, 0.35); }
    .hl-blue   { background-color: rgba( 59, 130, 246, 0.35); }
    .hl-pink   { background-color: rgba(236,  72, 153, 0.35); }
    .hl-orange { background-color: rgba(249, 115,  22, 0.40); }

    #hl-toolbar {
      position: fixed; z-index: 99999; display: none; align-items: center; gap: 5px;
      padding: 5px 8px; background: var(--card, #1e293b); border: 1px solid var(--card-border, #334155);
      border-radius: 10px; box-shadow: 0 4px 18px -2px rgba(0,0,0,0.25), 0 0 0 1px rgba(0,0,0,0.06);
      white-space: nowrap; user-select: none; pointer-events: auto;
    }
    #hl-toolbar.active { display: flex; }
    .hl-swatch {
      width: 18px; height: 18px; border-radius: 50%; border: 2px solid transparent;
      cursor: pointer; flex-shrink: 0; transition: transform 0.12s, box-shadow 0.12s;
    }
    .hl-swatch:hover { transform: scale(1.22); box-shadow: 0 0 0 2px var(--foreground, #fff); }
    .hl-swatch.selected { box-shadow: 0 0 0 2px var(--foreground, #fff); transform: scale(1.1); }
    .hl-divider { width: 1px; height: 16px; background: var(--card-border, #334155); margin: 0 2px; flex-shrink: 0; }
    .hl-btn {
      display: flex; align-items: center; justify-content: center; width: 24px; height: 24px;
      border-radius: 6px; border: none; background: transparent; color: var(--muted-foreground, #94a3b8);
      cursor: pointer; transition: background 0.1s, color 0.1s; flex-shrink: 0;
    }
    .hl-btn:hover { background: var(--card-border, #334155); color: var(--foreground, #fff); }

    #hl-popover {
      position: fixed; z-index: 99998; display: none; flex-direction: column; gap: 8px;
      padding: 10px 12px; background: var(--card, #1e293b); border: 1px solid var(--card-border, #334155);
      border-radius: 10px; box-shadow: 0 6px 24px -2px rgba(0,0,0,0.3); width: 240px;
    }
    #hl-popover.active { display: flex; }
    #hl-popover-header {
      display: flex; align-items: center; justify-content: space-between;
      font-size: 11px; font-weight: 600; color: var(--muted-foreground, #94a3b8);
      text-transform: uppercase; letter-spacing: 0.04em;
    }
    #hl-popover-text {
      border: 1px solid var(--card-border, #334155); border-radius: 6px;
      background: var(--background, #0f172a); color: var(--foreground, #fff);
      padding: 6px 8px; font-size: 12px; font-family: inherit; resize: none;
      outline: none; height: 56px; line-height: 1.4; transition: border-color 0.12s;
    }
    #hl-popover-text:focus { border-color: var(--primary, #3b82f6); }
    #hl-popover-actions { display: flex; align-items: center; justify-content: space-between; gap: 6px; }
    .hl-action-del {
      font-size: 11px; color: #ef4444; background: transparent; border: none;
      cursor: pointer; padding: 2px 4px; border-radius: 4px; transition: background 0.1s;
    }
    .hl-action-del:hover { background: rgba(239, 68, 68, 0.15); }
    .hl-action-save {
      font-size: 11px; font-weight: 500; padding: 3px 10px; border-radius: 5px;
      border: none; background: var(--primary, #3b82f6); color: #fff; cursor: pointer;
    }
    .hl-action-save:hover { opacity: 0.88; }

    #hl-status-pill {
      position: fixed; bottom: 14px; right: 14px; display: flex; align-items: center; gap: 5px;
      font-size: 11px; padding: 3px 9px; border-radius: 20px; background: var(--card, #1e293b);
      border: 1px solid var(--card-border, #334155); color: var(--muted-foreground, #94a3b8);
      pointer-events: none; opacity: 0; transform: translateY(4px); transition: opacity 0.25s, transform 0.25s;
      z-index: 99990;
    }
    #hl-status-pill.show { opacity: 1; transform: translateY(0); }
    #hl-status-pill .dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
    #hl-status-pill.ok { color: #22c55e; }
  </style>
</head>
<body class="bg-[var(--background)] text-[var(--foreground)] font-sans antialiased selection:bg-[var(--primary)] selection:text-white p-4 md:p-8 min-h-screen">

  <!-- ══ BUILT-IN ACTIVE LEARNING HIGHLIGHTER ══════════════════════════ -->
  <div id="hl-toolbar" role="toolbar" aria-label="Highlighter">
    <div class="hl-swatch selected" data-color="yellow" style="background:#facc15" title="Yellow (1)"></div>
    <div class="hl-swatch"          data-color="green"  style="background:#22c55e" title="Green (2)"></div>
    <div class="hl-swatch"          data-color="blue"   style="background:#3b82f6" title="Blue (3)"></div>
    <div class="hl-swatch"          data-color="pink"   style="background:#ec4899" title="Pink (4)"></div>
    <div class="hl-swatch"          data-color="orange" style="background:#f97316" title="Orange (5)"></div>
    <div class="hl-divider"></div>
    <button class="hl-btn" id="hl-btn-note" title="Add Note (N)">
      <svg width="13" height="13" viewBox="0 0 16 16" fill="none">
        <path d="M11 2l3 3-8 8H3v-3l8-8z" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/>
        <path d="M9 4l3 3" stroke="currentColor" stroke-width="1.4"/>
      </svg>
    </button>
    <button class="hl-btn" id="hl-btn-close" title="Dismiss (Esc)">
      <svg width="11" height="11" viewBox="0 0 12 12" fill="none">
        <path d="M2 2l8 8M10 2L2 10" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
      </svg>
    </button>
  </div>

  <div id="hl-popover">
    <div id="hl-popover-header">
      <span id="hl-popover-title">Annotation</span>
      <button class="hl-btn" id="hl-popover-close" style="width:18px;height:18px;">
        <svg width="9" height="9" viewBox="0 0 12 12" fill="none">
          <path d="M2 2l8 8M10 2L2 10" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
        </svg>
      </button>
    </div>
    <textarea id="hl-popover-text" placeholder="Add an annotation…"></textarea>
    <div id="hl-popover-actions">
      <button class="hl-action-del" id="hl-popover-del">Delete</button>
      <button class="hl-action-save" id="hl-popover-save">Save</button>
    </div>
  </div>

  <div id="hl-status-pill"><span class="dot"></span><span id="hl-status-text"></span></div>
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

  <!-- BUILT-IN ACTIVE LEARNING HIGHLIGHT ENGINE -->
  <script>
  (function() {
    'use strict';
    const SERVER = 'http://127.0.0.1:7723';
    const CONTENT = document.querySelector('main') || document.body;

    const ARTIFACT_PATH = window.location.href.startsWith('file://')
      ? decodeURIComponent(window.location.href.slice(7).split('?')[0].split('#')[0])
      : window.location.pathname;

    const STORAGE_KEY = 'sds_hl_' + ARTIFACT_PATH.replace(/[^a-zA-Z0-9_-]/g, '_');

    let highlights = [];
    let activeColor = 'yellow';
    let pendingSlices = null;
    let activeHighlightId = null;
    let pillTimer = null;
    let currentHoveredId = null;

    function getBlocks() {
      const blocks = [];
      function collect(el) {
        for (const child of el.children) {
          const tag = child.tagName.toLowerCase();
          if (['p', 'h1', 'h2', 'h3', 'h4', 'li', 'blockquote', 'pre', 'tr'].includes(tag)) {
            blocks.push(child);
          } else if (child.children.length > 0) {
            collect(child);
          }
        }
      }
      collect(CONTENT);
      return blocks.length > 0 ? blocks : Array.from(CONTENT.children);
    }

    function showStatus(msg, type = 'ok') {
      const pill = document.getElementById('hl-status-pill');
      const text = document.getElementById('hl-status-text');
      if (!pill || !text) return;
      text.textContent = msg;
      pill.className = `show ${type}`;
      clearTimeout(pillTimer);
      pillTimer = setTimeout(() => pill.classList.remove('show'), 2200);
    }

    function saveLocal() {
      try { localStorage.setItem(STORAGE_KEY, JSON.stringify(highlights)); } catch (e) {}
    }

    function loadLocal() {
      try {
        const raw = localStorage.getItem(STORAGE_KEY);
        if (raw) {
          const parsed = JSON.parse(raw);
          if (Array.isArray(parsed)) return parsed;
        }
      } catch (e) {}
      return [];
    }

    async function syncServer() {
      try {
        await fetch(`${SERVER}/highlights?artifact=${encodeURIComponent(ARTIFACT_PATH)}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(highlights),
          signal: AbortSignal.timeout(1200)
        });
        showStatus('synced');
      } catch (e) {}
    }

    async function fetchServer() {
      try {
        const res = await fetch(`${SERVER}/highlights?artifact=${encodeURIComponent(ARTIFACT_PATH)}`, {
          signal: AbortSignal.timeout(800)
        });
        if (res.ok) {
          const data = await res.json();
          if (Array.isArray(data) && data.length > 0) {
            highlights = data;
            saveLocal();
            renderAllHighlights();
          }
        }
      } catch (e) {}
    }

    function unwrapBlockMarks(block) {
      const marks = block.querySelectorAll('mark[data-hl-id]');
      for (const mark of marks) {
        const parent = mark.parentNode;
        if (!parent) continue;
        while (mark.firstChild) parent.insertBefore(mark.firstChild, mark);
        parent.removeChild(mark);
      }
      block.normalize();
    }

    function applyHighlightToBlock(block, startOff, endOff, color, id, note) {
      const textNodes = [];
      const walker = document.createTreeWalker(block, NodeFilter.SHOW_TEXT);
      let offset = 0;
      while (walker.nextNode()) {
        const node = walker.currentNode;
        textNodes.push({ node, start: offset, end: offset + node.length });
        offset += node.length;
      }

      for (const { node, start, end } of textNodes) {
        if (end <= startOff || start >= endOff) continue;

        const localStart = Math.max(0, startOff - start);
        const localEnd   = Math.min(node.length, endOff - start);
        if (localStart >= localEnd) continue;

        if (localEnd < node.length) node.splitText(localEnd);
        let target = node;
        if (localStart > 0) target = node.splitText(localStart);

        const mark = document.createElement('mark');
        mark.className = `hl-${color}`;
        mark.dataset.hlId = id;
        if (note) mark.title = note;

        target.parentNode.insertBefore(mark, target);
        mark.appendChild(target);
      }
    }

    function renderAllHighlights() {
      const blocks = getBlocks();
      blocks.forEach(b => unwrapBlockMarks(b));

      const slicesByBlock = new Map();
      for (const h of highlights) {
        for (const s of h.slices) {
          if (!slicesByBlock.has(s.blockIndex)) slicesByBlock.set(s.blockIndex, []);
          slicesByBlock.get(s.blockIndex).push({
            start: s.start, end: s.end, color: h.color, id: h.id, note: h.note
          });
        }
      }

      for (const [blockIdx, slices] of slicesByBlock.entries()) {
        const block = blocks[blockIdx];
        if (!block) continue;
        slices.sort((a, b) => a.start - b.start);
        for (const s of slices) {
          applyHighlightToBlock(block, s.start, s.end, s.color, s.id, s.note);
        }
      }
    }

    function measureBlockIntersection(block, range) {
      if (!range.intersectsNode(block)) return null;
      const preRange = document.createRange();
      preRange.selectNodeContents(block);

      let startOffset = 0;
      try {
        preRange.setEnd(range.startContainer, range.startOffset);
        startOffset = preRange.toString().length;
      } catch (e) { startOffset = 0; }

      let endOffset = block.textContent.length;
      try {
        preRange.setEnd(range.endContainer, range.endOffset);
        endOffset = preRange.toString().length;
      } catch (e) { endOffset = block.textContent.length; }

      if (startOffset >= endOffset) return null;
      const text = block.textContent.slice(startOffset, endOffset);
      if (!text.trim()) return null;
      return { start: startOffset, end: endOffset, text };
    }

    function captureSelectionSlices() {
      const sel = window.getSelection();
      if (!sel || sel.isCollapsed || !sel.toString().trim()) return null;

      const range = sel.getRangeAt(0);
      const blocks = getBlocks();
      const slices = [];

      blocks.forEach((block, idx) => {
        const match = measureBlockIntersection(block, range);
        if (match) slices.push({ blockIndex: idx, ...match });
      });

      return slices.length > 0 ? slices : null;
    }

    function commitHighlight(note = '') {
      if (!pendingSlices || pendingSlices.length === 0) return;
      const id = crypto.randomUUID();
      const h = { id, color: activeColor, note: note.trim(), slices: pendingSlices };
      highlights.push(h);
      saveLocal();
      renderAllHighlights();
      syncServer();
      pendingSlices = null;
      hideToolbar();
      hidePopover();
      window.getSelection()?.removeAllRanges();
    }

    function updateHighlightNote(id, note) {
      const h = highlights.find(x => x.id === id);
      if (!h) return;
      h.note = note.trim();
      saveLocal();
      renderAllHighlights();
      syncServer();
    }

    function deleteHighlight(id) {
      highlights = highlights.filter(x => x.id !== id);
      saveLocal();
      renderAllHighlights();
      syncServer();
      hidePopover();
      showStatus('deleted');
    }

    const toolbar = document.getElementById('hl-toolbar');
    const popover = document.getElementById('hl-popover');
    const popoverText = document.getElementById('hl-popover-text');
    const popoverTitle = document.getElementById('hl-popover-title');
    const popoverDel = document.getElementById('hl-popover-del');

    function showToolbar(x, y) {
      const tw = 210;
      const left = Math.min(Math.max(12, x - tw / 2), window.innerWidth - tw - 12);
      const top = Math.max(12, y - 52);
      toolbar.style.left = `${left}px`;
      toolbar.style.top = `${top}px`;
      toolbar.classList.add('active');
    }

    function hideToolbar() {
      toolbar.classList.remove('active');
      pendingSlices = null;
    }

    function openPopoverForNew(anchorEl) {
      activeHighlightId = null;
      popoverTitle.textContent = 'Annotation';
      popoverText.value = '';
      popoverDel.style.display = 'none';
      const rect = anchorEl.getBoundingClientRect();
      const left = Math.min(Math.max(12, rect.left), window.innerWidth - 250);
      popover.style.left = `${left}px`;
      popover.style.top = `${rect.bottom + 8}px`;
      popover.classList.add('active');
      popoverText.focus();
    }

    function openPopoverForExisting(id, x, y) {
      const h = highlights.find(item => item.id === id);
      if (!h) return;
      activeHighlightId = id;
      popoverTitle.textContent = 'Edit Note';
      popoverText.value = h.note || '';
      popoverDel.style.display = 'block';
      const left = Math.min(Math.max(12, x - 120), window.innerWidth - 250);
      const top = Math.min(y + 12, window.innerHeight - 150);
      popover.style.left = `${left}px`;
      popover.style.top = `${top}px`;
      popover.classList.add('active');
      hideToolbar();
      popoverText.focus();
    }

    function hidePopover() {
      popover.classList.remove('active');
      activeHighlightId = null;
    }

    document.querySelectorAll('.hl-swatch').forEach(sw => {
      sw.addEventListener('mousedown', e => e.preventDefault());
      sw.addEventListener('click', () => {
        document.querySelectorAll('.hl-swatch').forEach(s => s.classList.remove('selected'));
        sw.classList.add('selected');
        activeColor = sw.dataset.color;
        if (pendingSlices) commitHighlight();
      });
    });

    document.getElementById('hl-btn-note')?.addEventListener('mousedown', e => e.preventDefault());
    document.getElementById('hl-btn-note')?.addEventListener('click', () => {
      if (popover.classList.contains('active')) hidePopover();
      else openPopoverForNew(toolbar);
    });

    document.getElementById('hl-btn-close')?.addEventListener('click', hideToolbar);
    document.getElementById('hl-popover-close')?.addEventListener('click', hidePopover);
    popoverDel?.addEventListener('click', () => {
      if (activeHighlightId) deleteHighlight(activeHighlightId);
    });
    document.getElementById('hl-popover-save')?.addEventListener('click', () => {
      if (activeHighlightId) {
        updateHighlightNote(activeHighlightId, popoverText.value);
        hidePopover();
      } else {
        commitHighlight(popoverText.value);
      }
    });

    CONTENT.addEventListener('mouseover', e => {
      const targetEl = e.target instanceof Element ? e.target : e.target?.parentElement;
      const mark = targetEl?.closest('mark[data-hl-id]');
      const id = mark?.dataset.hlId;
      if (id === currentHoveredId) return;

      if (currentHoveredId) {
        document.querySelectorAll('mark[data-hl-id="' + currentHoveredId + '"]').forEach(m => {
          m.classList.remove('hl-hovered');
        });
        currentHoveredId = null;
      }

      if (id) {
        currentHoveredId = id;
        document.querySelectorAll('mark[data-hl-id="' + id + '"]').forEach(m => {
          m.classList.add('hl-hovered');
        });
      }
    });

    CONTENT.addEventListener('mouseout', e => {
      if (!currentHoveredId) return;
      const related = e.relatedTarget instanceof Element ? e.relatedTarget : e.relatedTarget?.parentElement;
      const stillInSame = related?.closest('mark[data-hl-id="' + currentHoveredId + '"]');
      if (!stillInSame) {
        document.querySelectorAll('mark[data-hl-id="' + currentHoveredId + '"]').forEach(m => {
          m.classList.remove('hl-hovered');
        });
        currentHoveredId = null;
      }
    });

    document.addEventListener('mouseup', e => {
      if (toolbar.contains(e.target) || popover.contains(e.target)) return;
      const targetEl = e.target instanceof Element ? e.target : e.target?.parentElement;
      const mark = targetEl?.closest('mark[data-hl-id]');
      if (mark) {
        openPopoverForExisting(mark.dataset.hlId, e.clientX, e.clientY);
        return;
      }
      setTimeout(() => {
        const slices = captureSelectionSlices();
        if (!slices) { hideToolbar(); return; }
        pendingSlices = slices;
        hidePopover();
        showToolbar(e.clientX, e.clientY);
      }, 15);
    });

    document.addEventListener('mousedown', e => {
      if (!toolbar.contains(e.target) && !popover.contains(e.target)) {
        toolbar.classList.remove('active');
        popover.classList.remove('active');
      }
    });

    document.addEventListener('keydown', e => {
      if (['INPUT', 'TEXTAREA'].includes(document.activeElement?.tagName)) return;
      if (e.key === 'Escape') { hideToolbar(); hidePopover(); return; }
      if ((e.key === 'h' || e.key === 'H') && pendingSlices) { commitHighlight(); return; }
      if ((e.key === 'n' || e.key === 'N') && pendingSlices) { openPopoverForNew(toolbar); return; }
      const colMap = { '1': 'yellow', '2': 'green', '3': 'blue', '4': 'pink', '5': 'orange' };
      if (colMap[e.key]) document.querySelector('.hl-swatch[data-color="' + colMap[e.key] + '"]')?.click();
    });

    const localData = loadLocal();
    if (localData.length > 0) {
      highlights = localData;
      renderAllHighlights();
    }
    fetchServer();
  })();
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



def locate_resource_fixture(topic_id, slug):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(script_dir, "..", "resources", "examples", "lessons", f"{slug}.json"),
        os.path.join(script_dir, "..", "resources", "examples", "lessons", f"{topic_id}.json"),
        os.path.join(os.getcwd(), "skills", "system-design-studio", "resources", "examples", "lessons", f"{slug}.json"),
    ]
    slug_no_prefix = re.sub(r"^\d+-\d+-", "", slug)
    if slug_no_prefix != slug:
        candidates.append(os.path.join(script_dir, "..", "resources", "examples", "lessons", f"{slug_no_prefix}.json"))

    for c in candidates:
        norm = os.path.normpath(c)
        if os.path.exists(norm):
            try:
                with open(norm, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
    return None

def generate_scaffold_data(topic_id, title=None, cluster=None, tier=None):
    clean_title = format_topic_title(topic_id, title)
    return {
        "PAGE_TITLE": f"Topic — {clean_title}",
        "TIER_BADGE": tier or "Tier 0 · System Design Core",
        "CLUSTER_BADGE": cluster or "Foundation Mechanism",
        "LESSON_TITLE": clean_title,
        "LESSON_SUBTITLE": "A first-principles, causal breakdown of physical constraints, failure modes, and architectural trade-offs.",
        "SECTION_1_TITLE": f"1. Background Context & Core Dilemma: What Breaks Without {clean_title}",
        "SECTION_1_BODY": f"""
        <div class="editorial-lead">
          Every distributed system begins with the laws of physical hardware: finite network bandwidth, non-zero speed of light, and uncoordinated machines.
        </div>
        <p>
          Before analyzing the software machinery of <strong>{clean_title}</strong>, we must isolate the concrete dilemma that exists when this abstraction is missing.
        </p>
        """,
        "SECTION_2_TITLE": f"2. The Core Abstraction & Boundary Placement",
        "SECTION_2_BODY": f"""
        <p>
          Positioned directly between transport/storage primitives and domain application logic, governing queue allocations and invariant enforcement.
        </p>
        """,
        "SECTION_3_TITLE": f"3. Internal Mechanics, Invariants & Causality",
        "SECTION_3_BODY": f"""
        <p>
          How <strong>{clean_title}</strong> operates under the hood, why alternatives fail, and what invariants it guarantees.
        </p>
        """,
        "SECTION_4_TITLE": f"4. Production Grounding & Trade-Offs",
        "SECTION_4_BODY": f"""
        <p>
          Real-world production trade-offs and domain applications for <strong>{clean_title}</strong>.
        </p>
        """,
        "SECTION_5_TITLE": f"5. Active Defense Gate: Real-World Incident Scenario",
        "SECTION_5_BODY": f"""
        <div class="callout-box callout-trap">
          <h4 class="font-bold text-[var(--foreground)] text-base m-0">Production Incident Scenario</h4>
          <p class="text-sm text-[var(--muted-foreground)] leading-relaxed">
            A production incident occurs exposing the core trade-off of {clean_title}. Discuss and defend your architectural breakdown in chat using <code>/sds-discuss</code>.
          </p>
        </div>
        """,
        "BACKWARD_ANCHOR": "Prerequisite foundational mechanisms",
        "FORWARD_HOOK": "Downstream distributed systems invariants",
        "EMBEDDED_JAVASCRIPT": "// Bespoke simulator code or interactive logic"
    }

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
    try:
        from pathlib import Path
        _ensure_script = Path(__file__).resolve().parent / 'ensure-highlight-server.py'
        if _ensure_script.is_file():
            import subprocess, sys
            subprocess.run([sys.executable, str(_ensure_script)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1.0)
    except Exception:
        pass
    
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

    if args.data_file and os.path.exists(args.data_file):
        with open(args.data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    elif args.data:
        if args.data == "-":
            data = json.load(sys.stdin)
        else:
            data = json.loads(args.data)
    else:
        data = locate_resource_fixture(args.topic_id, slug)
        if not data:
            data = generate_scaffold_data(args.topic_id, args.title, args.cluster, args.tier)

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
        # Ensure theme variables are bound
        data["THEME_CSS_VARS"] = theme["css_vars"]
        data["THEME_NAME"] = theme["name"]
        data["THEME_ID"] = theme["id"]

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

if __name__ == "__main__":
    main()
