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
    .narrative-prose { color: var(--foreground); line-height: 1.75; font-size: 0.95rem; }
    .narrative-prose p { margin-bottom: 1.15rem; }
    .narrative-prose strong { color: var(--foreground); font-weight: 700; }
    .narrative-prose code { background: var(--card); border: 1px solid var(--card-border); padding: 0.15rem 0.35rem; border-radius: 0.375rem; font-family: ui-monospace, monospace; font-size: 0.825em; }
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
  </style>
</head>
<body class="bg-[var(--background)] text-[var(--foreground)] font-sans antialiased selection:bg-[var(--primary)] selection:text-white p-4 md:p-8 min-h-screen">
  <div class="max-w-4xl mx-auto space-y-12">
    <!-- HERO HEADER: CONTEXTUAL ORIENTATION -->
    <header class="border-b border-[var(--border)] pb-8 space-y-4">
      <div class="flex flex-wrap items-center gap-2">
        <span class="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-[var(--primary)] text-white tracking-wide uppercase">{{TIER_BADGE}}</span>
        <span class="px-2.5 py-0.5 text-xs font-medium rounded-full bg-[var(--card)] border border-[var(--card-border)] text-[var(--muted-foreground)]">{{CLUSTER_BADGE}}</span>
        <span class="px-2.5 py-0.5 text-xs font-mono rounded-full bg-[var(--card)] border border-[var(--card-border)] text-[var(--muted-foreground)]">{{DEPTH_MARKERS}}</span>
        <span class="px-2.5 py-0.5 text-xs font-mono rounded-full bg-[var(--card)] border border-[var(--card-border)] text-[var(--primary)] font-semibold">🎨 {{THEME_NAME}}</span>
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

def generate_default_data(topic_id, title=None, cluster=None, tier=None, style_id="slate-clean"):
    clean_title = format_topic_title(topic_id, title)
    theme = STYLE_THEMES.get(style_id, STYLE_THEMES["slate-clean"])

    return {
        "PAGE_TITLE": f"Topic — {clean_title}",
        "THEME_CSS_VARS": theme["css_vars"],
        "THEME_NAME": theme["name"],
        "THEME_ID": theme["id"],
        "TIER_BADGE": tier or "Tier 0 · System Design Core",
        "CLUSTER_BADGE": cluster or "Foundation Mechanism",
        "DEPTH_MARKERS": "[concept] [mechanics] [contrast] [trap]",
        "LESSON_TITLE": clean_title,
        "LESSON_SUBTITLE": "A first-principles, causal breakdown of physical constraints, failure modes, and architectural trade-offs.",

        # PHASE 1: WHYs & optional WHENs
        "SECTION_1_TITLE": f"The Foundational Dilemma: What Breaks in the Absence of {clean_title}",
        "SECTION_1_BODY": f"""
        <p>
          Before examining the machinery of <strong>{clean_title}</strong>, we must isolate the concrete engineering dilemma that exists when this capability is absent. Every distributed system begins with the laws of physical hardware: finite network bandwidth, non-zero speed of light (~5 μs/km through fiber), and operating systems managing independent memory spaces across uncoordinated machines.
        </p>
        <div class="callout-box callout-dilemma">
          <div class="text-xs font-mono font-bold text-rose-400 uppercase tracking-wider mb-1">⚡ The Core Architectural Tension</div>
          <p class="text-sm text-[var(--foreground)] m-0">
            When multiple actors communicate without this abstraction, naive implementations either stall the pipeline waiting for synchronous acknowledgements (collapsing throughput) or broadcast without guarantees (risking silent data loss, duplicate execution, or corruption).
          </p>
        </div>
        <p>
          This establishes our baseline: the need arose not as an arbitrary convention, but as a mandatory physical response to uncoordinated networks and asynchronous execution.
        </p>
        """,

        # PHASE 2: WHATs & optional WHEREs
        "SECTION_2_TITLE": f"The Core Abstraction & Boundary Placement",
        "SECTION_2_BODY": f"""
        <p>
          Assuming zero prior familiarity with <strong>{clean_title}</strong>, what actually is it, and where does it sit in the architectural stack?
        </p>
        <p>
          Architecturally, <strong>{clean_title}</strong> establishes a contract between the underlying unreliable physical primitives and the user-space application layers above it. Rather than exposing raw hardware vagaries, it encapsulates state tracking, buffer management, and coordination rules into a well-defined boundary.
        </p>
        <div class="callout-box callout-mechanism">
          <div class="text-xs font-mono font-bold text-[var(--primary)] uppercase tracking-wider mb-1">🗺️ Boundary & Stack Placement</div>
          <p class="text-sm text-[var(--foreground)] m-0">
            Positioned directly between transport/storage primitives and domain application logic, governing queue allocations, socket descriptors, and invariant enforcement.
          </p>
        </div>
        """,

        # PHASE 3: HOWs & WHYs of HOWs (with inline interactive simulator)
        "SECTION_3_TITLE": f"Under the Hood: Internal Mechanics, Causality & Trade-offs",
        "SECTION_3_BODY": f"""
        <p>
          How does <strong>{clean_title}</strong> actually function internally, and why is it constructed in this specific way rather than alternative approaches?
        </p>
        <p>
          The system maintains dual kernel/storage states: tracking in-flight unacknowledged operations on the dispatch side, and maintaining an out-of-order reassembly buffer on the receiving side. If an element is delayed or dropped, the system must decide: stall delivery to preserve strict monotonic order, or deliver immediately and forfeit consistency guarantees.
        </p>

        <!-- Inline Embedded Execution Simulator -->
        <div class="sim-container">
          <div class="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-3 border-b border-[var(--border)]">
            <div>
              <div class="text-sm font-bold text-[var(--foreground)] flex items-center gap-2">
                <span class="inline-block w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
                Interactive Simulator: {clean_title} State Machine
              </div>
              <div class="text-xs text-[var(--muted-foreground)]">Step through state transitions, packet transmission, and failure recovery.</div>
            </div>
            <div class="flex items-center gap-2">
              <button onclick="simStep()" class="px-3 py-1.5 text-xs font-semibold rounded-lg bg-[var(--primary)] text-white hover:opacity-90 transition">Step Forward →</button>
              <button onclick="simReset()" class="px-3 py-1.5 text-xs font-semibold rounded-lg bg-[var(--background)] border border-[var(--border)] text-[var(--foreground)] hover:bg-[var(--card)] transition">Reset</button>
            </div>
          </div>
          <div class="sim-canvas my-3">
            <div class="flex items-center justify-between min-h-[120px]">
              <div class="p-3 rounded-lg bg-[var(--card)] border border-[var(--card-border)] w-32">
                <div class="text-xs font-bold text-blue-400">Sender / Host A</div>
                <div id="sim-sender-state" class="text-xs font-mono mt-1 text-[var(--muted-foreground)]">STATE: IDLE</div>
              </div>
              <div class="flex-1 flex flex-col items-center justify-center px-4">
                <div class="w-full h-1 bg-[var(--border)] relative flex items-center justify-center">
                  <div id="transit-chip" class="w-4 h-4 rounded-full bg-[var(--primary)] transition-all duration-300 transform scale-0"></div>
                </div>
                <div class="text-[10px] font-mono mt-2 text-[var(--muted-foreground)]">UNRELIABLE TRANSIT LINK</div>
              </div>
              <div class="p-3 rounded-lg bg-[var(--card)] border border-[var(--card-border)] w-32">
                <div class="text-xs font-bold text-emerald-400">Receiver / Host B</div>
                <div id="sim-receiver-state" class="text-xs font-mono mt-1 text-[var(--muted-foreground)]">STATE: LISTENING</div>
              </div>
            </div>
          </div>
          <div class="sim-log" id="sim-log">
            Click 'Step Forward' to trace the internal protocol sequence.
          </div>
        </div>

        <div class="callout-box callout-invariant">
          <div class="text-xs font-mono font-bold text-emerald-400 uppercase tracking-wider mb-1">⚖️ The Non-Negotiable Invariant Boundary</div>
          <p class="text-sm text-[var(--foreground)] m-0">
            <strong>Guaranteed:</strong> Causal ordering and data completeness within the established session boundary.<br/>
            <strong>Explicit Non-Guarantee:</strong> Bounded latency under network packet drops; recovery introduces tail latency spikes.
          </p>
        </div>
        """,

        # PHASE 4: MENTAL MODEL & REAL-WORLD CORRELATES
        "SECTION_4_TITLE": f"Mental Model Synthesis & Production Grounding",
        "SECTION_4_BODY": f"""
        <p>
          To make this mechanism intuitive, synthesize the moving parts into a unified mental model and correlate it with contrasting production workloads.
        </p>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 my-4">
          <div class="p-5 rounded-xl bg-[var(--card)] border border-[var(--card-border)] space-y-2">
            <div class="text-xs font-mono font-bold text-blue-400 uppercase">Workload A: Financial Ledger</div>
            <h4 class="text-sm font-bold text-[var(--foreground)]">Linearizable Money Movement</h4>
            <p class="text-xs text-[var(--muted-foreground)] leading-relaxed m-0">
              Dropping or reordering a single byte is an existential business failure. The system gladly accepts 300ms tail-latency stalls to guarantee byte-for-byte monotonicity.
            </p>
          </div>
          <div class="p-5 rounded-xl bg-[var(--card)] border border-[var(--card-border)] space-y-2">
            <div class="text-xs font-mono font-bold text-emerald-400 uppercase">Workload B: Real-Time Audio / Video</div>
            <h4 class="text-sm font-bold text-[var(--foreground)]">WebRTC Live Voice Stream</h4>
            <p class="text-xs text-[var(--muted-foreground)] leading-relaxed m-0">
              Late packets are completely useless—human auditory perception notices stalls over 150ms. Dropping late audio packets immediately beats waiting for a retransmission.
            </p>
          </div>
        </div>

        <table class="tradeoff-table">
          <thead>
            <tr>
              <th>Architectural Dimension</th>
              <th>High-Durability Stream (TCP)</th>
              <th>Bounded-Latency Datagram (UDP)</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td class="font-semibold">Ordering Invariant</td>
              <td class="font-mono text-emerald-400">Strict Total Order</td>
              <td class="font-mono text-amber-400">Unordered / Best-Effort</td>
            </tr>
            <tr>
              <td class="font-semibold">Packet Loss Response</td>
              <td class="font-mono text-rose-400">Stall queue; retransmit</td>
              <td class="font-mono text-emerald-400">Drop frame; proceed</td>
            </tr>
            <tr>
              <td class="font-semibold">Latency Bound Under Loss</td>
              <td class="font-mono text-rose-400">Unbounded (Jitter spikes)</td>
              <td class="font-mono text-emerald-400">Strictly bounded (Single RTT)</td>
            </tr>
          </tbody>
        </table>
        """,

        # PHASE 5: CONTEXTUAL SIGN-OFF VERIFICATION GATE
        "SECTION_5_TITLE": f"Contextual Sign-Off Verification: Active Defense Gate",
        "SECTION_5_BODY": f"""
        <div class="callout-box callout-trap">
          <div class="flex items-start gap-3">
            <div class="text-amber-400 font-bold text-lg mt-0.5">⚠️</div>
            <div class="space-y-2">
              <h4 class="font-bold text-[var(--foreground)] text-base m-0">Production Incident Defense Scenario</h4>
              <p class="text-sm text-[var(--muted-foreground)] leading-relaxed">
                A distributed real-time dashboard experiences severe tail-latency jitter spikes (P99 > 850ms) on lossy cellular networks, despite the backend CPU utilization staying below 25%. A junior engineer suggests increasing socket buffer sizes to smooth the spikes.
              </p>
              <p class="text-sm font-semibold text-[var(--foreground)] leading-relaxed m-0">
                Why will increasing socket buffer sizes fail to resolve the tail latency, where exactly in the stack is the queue accumulating, and how does transport protocol selection causally explain the symptom?
              </p>
            </div>
          </div>
        </div>

        <div class="p-4 rounded-xl bg-[var(--background)] border border-[var(--border)] space-y-2 text-xs text-[var(--muted-foreground)]">
          <div class="font-bold text-[var(--primary)] flex items-center gap-2">
            <span>🎯 Sign-Off Gate Defense Standard:</span>
          </div>
          <p class="leading-relaxed m-0">
            Tick off when: you can analyze and defend this scenario cold in chat discussion without notes, isolating the physical queue location, why buffer expansion exacerbates latency, and how the underlying transport invariant dictates the outcome.
          </p>
          <div class="pt-2 text-[11px] font-mono text-amber-400 flex items-center gap-2">
            <span class="inline-block w-2 h-2 rounded-full bg-amber-400"></span>
            <span>No solution is provided in this artifact. Discuss and defend your breakdown in chat to complete topic sign-off.</span>
          </div>
        </div>
        """,

        "BACKWARD_ANCHOR": "Physical network constraints & hardware bounds",
        "FORWARD_HOOK": "Distributed consensus & fault recovery",
        "EMBEDDED_JAVASCRIPT": """
        let simState = 0;
        function simStep() {
          const chip = document.getElementById('transit-chip');
          const sender = document.getElementById('sim-sender-state');
          const receiver = document.getElementById('sim-receiver-state');
          const log = document.getElementById('sim-log');
          if (!chip || !sender || !receiver || !log) return;
          if (simState === 0) {
            sender.textContent = "STATE: SENDING";
            chip.style.transform = "scale(1)";
            log.innerHTML = "<span class='text-blue-400 font-bold'>[SEND]</span> Dispatching message payload across network link...";
            simState = 1;
          } else if (simState === 1) {
            receiver.textContent = "STATE: PROCESSING";
            log.innerHTML = "<span class='text-emerald-400 font-bold'>[RECV]</span> Message received; verifying checksum and payload invariant.";
            simState = 2;
          } else {
            sender.textContent = "STATE: IDLE (ACK)";
            receiver.textContent = "STATE: LISTENING";
            chip.style.transform = "scale(0)";
            log.innerHTML = "<span class='text-purple-400 font-bold'>[ACK]</span> Acknowledgement complete. Ready for next cycle.";
            simState = 0;
          }
        }
        function simReset() {
          simState = 0;
          const chip = document.getElementById('transit-chip');
          const sender = document.getElementById('sim-sender-state');
          const receiver = document.getElementById('sim-receiver-state');
          const log = document.getElementById('sim-log');
          if (chip) chip.style.transform = "scale(0)";
          if (sender) sender.textContent = "STATE: IDLE";
          if (receiver) receiver.textContent = "STATE: LISTENING";
          if (log) log.textContent = "Click 'Step Forward' to trace the internal protocol sequence.";
        }
        """
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
        candidates.append(settings_path)
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
    parser = argparse.ArgumentParser(description="Render interactive HTML or pure Markdown lesson artifact")
    parser.add_argument("--topic-id", required=True, help="Topic ID (e.g. topic.0.1.tcp-vs-udp)")
    parser.add_argument("--title", help="Lesson Title")
    parser.add_argument("--cluster", help="Cluster Title")
    parser.add_argument("--tier", help="Tier Title")
    parser.add_argument("--style", choices=list(STYLE_THEMES.keys()), help="Artifact visual style theme")
    parser.add_argument("--format", choices=["html", "markdown"], help="Output artifact format (html or markdown)")
    parser.add_argument("--settings", help="Path to settings.json")
    parser.add_argument("--spec", help="Path to JSON file with lesson override tokens")
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

    data = generate_default_data(args.topic_id, args.title, args.cluster, args.tier, active_style)

    if args.spec and os.path.exists(args.spec):
        with open(args.spec) as f:
            spec_data = json.load(f)
            data.update(spec_data)

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

    if args.brain_dir and os.path.exists(args.brain_dir):
        brain_path = os.path.join(args.brain_dir, filename)
        with open(brain_path, "w", encoding="utf-8") as f:
            f.write(rendered)
        print(f"✅ Staged to conversation artifact dir: {brain_path}")

if __name__ == "__main__":
    main()
