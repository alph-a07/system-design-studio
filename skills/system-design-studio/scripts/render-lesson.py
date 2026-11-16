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


def build_tcp_vs_udp_data(theme, tier=None, cluster=None):
    sim_html = """
        <div class="sim-container">
          <div class="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-3 border-b border-[var(--border)]">
            <div>
              <div class="text-sm font-bold text-[var(--foreground)] flex items-center gap-2">
                <span class="inline-block w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
                Tactile Simulator: TCP vs UDP Head-of-Line Blocking & Packet Loss
              </div>
              <div class="text-xs text-[var(--muted-foreground)]">Compare kernel receive queue stalling vs immediate datagram consumption under packet drop.</div>
            </div>
            <div class="flex flex-wrap items-center gap-2">
              <div class="flex items-center gap-1 bg-[var(--background)] p-1 rounded-lg border border-[var(--border)] text-xs font-mono">
                <button id="proto-tcp-btn" onclick="setSimProtocol('tcp')" class="px-2.5 py-1 rounded font-bold bg-[var(--primary)] text-white transition">TCP</button>
                <button id="proto-udp-btn" onclick="setSimProtocol('udp')" class="px-2.5 py-1 rounded text-[var(--muted-foreground)] hover:text-white transition">UDP</button>
              </div>
              <label class="flex items-center gap-1.5 text-xs font-mono text-amber-400 cursor-pointer bg-[var(--card)] px-2.5 py-1.5 rounded-lg border border-amber-900/50">
                <input type="checkbox" id="drop-packet-2" checked onchange="toggleDrop(this.checked)" class="accent-amber-500 rounded">
                <span>Drop Packet #2 (Router Burst)</span>
              </label>
              <button onclick="startSimulation()" class="px-3 py-1.5 text-xs font-semibold rounded-lg bg-[var(--primary)] text-white hover:opacity-90 transition">Transmit 5 Packets →</button>
              <button onclick="resetSimulation()" class="px-3 py-1.5 text-xs font-semibold rounded-lg bg-[var(--background)] border border-[var(--border)] text-[var(--foreground)] hover:bg-[var(--card)] transition">Reset</button>
            </div>
          </div>

          <!-- Main Visual Canvas -->
          <div class="sim-canvas my-4 space-y-4">
            <!-- Top Lane: Sender to Network to Receiver -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-3 items-center">
              <!-- Sender -->
              <div class="p-3.5 rounded-xl bg-[var(--card)] border border-[var(--card-border)]">
                <div class="flex items-center justify-between mb-2">
                  <span class="text-xs font-bold text-blue-400">Host A (Sender)</span>
                  <span id="sender-status-badge" class="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-950 text-blue-300">IDLE</span>
                </div>
                <div class="text-[11px] text-[var(--muted-foreground)]">Socket Send Buffer (5 Segments / 7,300 B)</div>
                <div class="flex gap-1 mt-2" id="sender-queue">
                  <span class="px-1.5 py-0.5 text-[10px] font-mono rounded bg-blue-900/60 text-blue-200 border border-blue-700">#1</span>
                  <span class="px-1.5 py-0.5 text-[10px] font-mono rounded bg-blue-900/60 text-blue-200 border border-blue-700">#2</span>
                  <span class="px-1.5 py-0.5 text-[10px] font-mono rounded bg-blue-900/60 text-blue-200 border border-blue-700">#3</span>
                  <span class="px-1.5 py-0.5 text-[10px] font-mono rounded bg-blue-900/60 text-blue-200 border border-blue-700">#4</span>
                  <span class="px-1.5 py-0.5 text-[10px] font-mono rounded bg-blue-900/60 text-blue-200 border border-blue-700">#5</span>
                </div>
              </div>

              <!-- Network Pipe -->
              <div class="p-3.5 rounded-xl bg-[var(--card)] border border-[var(--card-border)] flex flex-col items-center justify-center text-center">
                <div class="text-[11px] font-mono text-[var(--muted-foreground)] mb-1">UNRELIABLE IP TRANSIT (MTU: 1500B)</div>
                <div class="w-full h-8 bg-[var(--background)] rounded-lg border border-[var(--border)] relative overflow-hidden flex items-center px-2" id="network-pipe">
                  <div class="text-[10px] text-stone-500 font-mono w-full text-center" id="pipe-placeholder">Ready for transmission</div>
                </div>
                <div class="text-[10px] font-mono mt-1 text-amber-400" id="network-loss-indicator">Loss Injection: Packet #2 will drop at congested router</div>
              </div>

              <!-- Receiver -->
              <div class="p-3.5 rounded-xl bg-[var(--card)] border border-[var(--card-border)]">
                <div class="flex items-center justify-between mb-2">
                  <span class="text-xs font-bold text-emerald-400">Host B (Receiver Kernel)</span>
                  <span id="receiver-status-badge" class="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-300">LISTENING</span>
                </div>
                <div class="text-[11px] text-[var(--muted-foreground)]">Kernel TCP Receive Buffer (Out-of-Order Queue)</div>
                <div class="flex gap-1 mt-2 min-h-[22px]" id="kernel-buffer">
                  <span class="text-[10px] text-stone-500 font-mono italic">Buffer empty</span>
                </div>
              </div>
            </div>

            <!-- Bottom Lane: Application Delivery Layer (The Crucial Difference!) -->
            <div class="p-4 rounded-xl bg-[var(--card)] border border-[var(--card-border)]">
              <div class="flex flex-col md:flex-row md:items-center justify-between gap-2 mb-2">
                <div class="flex items-center gap-2">
                  <span class="text-xs font-bold uppercase tracking-wider text-[var(--foreground)]">User Application Read Stream (`recv()` / `read()`)</span>
                  <span id="hol-badge" class="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-stone-800 text-stone-400">IDLE</span>
                </div>
                <div id="retransmit-action-area" class="hidden">
                  <button onclick="retransmitPacket2()" class="px-2.5 py-1 text-xs font-bold rounded bg-amber-500 text-black hover:bg-amber-400 transition animate-pulse">
                    ⚡ Retransmit Packet #2 (Fast Retransmit / RTO)
                  </button>
                </div>
              </div>

              <div class="p-3 rounded-lg bg-[var(--background)] border border-[var(--border)] min-h-[44px] flex items-center gap-2 flex-wrap" id="app-read-stream">
                <span class="text-xs text-stone-500 font-mono italic">Waiting for application syscall delivery...</span>
              </div>
            </div>

            <!-- Real-Time Telemetry Gauges -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-2 pt-1">
              <div class="p-2.5 rounded-lg bg-[var(--card)] border border-[var(--card-border)] text-center">
                <div class="text-[10px] font-mono text-[var(--muted-foreground)] uppercase">Delivery Latency</div>
                <div class="text-sm font-bold font-mono text-[var(--foreground)]" id="telemetry-latency">-- ms</div>
              </div>
              <div class="p-2.5 rounded-lg bg-[var(--card)] border border-[var(--card-border)] text-center">
                <div class="text-[10px] font-mono text-[var(--muted-foreground)] uppercase">Head-of-Line Blocking</div>
                <div class="text-sm font-bold font-mono text-emerald-400" id="telemetry-hol">NONE</div>
              </div>
              <div class="p-2.5 rounded-lg bg-[var(--card)] border border-[var(--card-border)] text-center">
                <div class="text-[10px] font-mono text-[var(--muted-foreground)] uppercase">Packets Consumed by App</div>
                <div class="text-sm font-bold font-mono text-[var(--foreground)]" id="telemetry-consumed">0 / 5</div>
              </div>
              <div class="p-2.5 rounded-lg bg-[var(--card)] border border-[var(--card-border)] text-center">
                <div class="text-[10px] font-mono text-[var(--muted-foreground)] uppercase">Memory Locked in Kernel</div>
                <div class="text-sm font-bold font-mono text-stone-400" id="telemetry-mem">0 B</div>
              </div>
            </div>
          </div>

          <div class="sim-log" id="sim-log">
            Click 'Transmit 5 Packets' to trace the packet flight across physical wire.
          </div>
        </div>
    """

    sim_js = """
        let currentProtocol = 'tcp';
        let dropPacket2 = true;
        let isTransmitting = false;

        function setSimProtocol(p) {
          if (isTransmitting) return;
          currentProtocol = p;
          const tcpBtn = document.getElementById('proto-tcp-btn');
          const udpBtn = document.getElementById('proto-udp-btn');
          if (p === 'tcp') {
            tcpBtn.className = 'px-2.5 py-1 rounded font-bold bg-[var(--primary)] text-white transition';
            udpBtn.className = 'px-2.5 py-1 rounded text-[var(--muted-foreground)] hover:text-white transition';
          } else {
            udpBtn.className = 'px-2.5 py-1 rounded font-bold bg-[var(--primary)] text-white transition';
            tcpBtn.className = 'px-2.5 py-1 rounded text-[var(--muted-foreground)] hover:text-white transition';
          }
          resetSimulation();
        }

        function toggleDrop(checked) {
          dropPacket2 = checked;
          const ind = document.getElementById('network-loss-indicator');
          if (ind) {
            ind.textContent = checked ? 'Loss Injection: Packet #2 will drop at congested router' : 'Loss Injection: Disabled (Clean Fiber Link)';
            ind.className = checked ? 'text-[10px] font-mono mt-1 text-amber-400' : 'text-[10px] font-mono mt-1 text-emerald-400';
          }
        }

        function resetSimulation() {
          isTransmitting = false;
          const sBadge = document.getElementById('sender-status-badge');
          const rBadge = document.getElementById('receiver-status-badge');
          const kBuf = document.getElementById('kernel-buffer');
          const aStream = document.getElementById('app-read-stream');
          const rArea = document.getElementById('retransmit-action-area');
          const hBadge = document.getElementById('hol-badge');
          const tLat = document.getElementById('telemetry-latency');
          const tHol = document.getElementById('telemetry-hol');
          const tCon = document.getElementById('telemetry-consumed');
          const tMem = document.getElementById('telemetry-mem');
          const nPipe = document.getElementById('network-pipe');
          const log = document.getElementById('sim-log');

          if (sBadge) { sBadge.textContent = 'IDLE'; sBadge.className = 'text-[10px] font-mono px-2 py-0.5 rounded bg-blue-950 text-blue-300'; }
          if (rBadge) { rBadge.textContent = 'LISTENING'; }
          if (kBuf) { kBuf.innerHTML = '<span class="text-[10px] text-stone-500 font-mono italic">Buffer empty</span>'; }
          if (aStream) { aStream.innerHTML = '<span class="text-xs text-stone-500 font-mono italic">Waiting for application syscall delivery...</span>'; }
          if (rArea) { rArea.classList.add('hidden'); }
          if (hBadge) { hBadge.textContent = 'IDLE'; hBadge.className = 'text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-stone-800 text-stone-400'; }
          if (tLat) { tLat.textContent = '-- ms'; }
          if (tHol) { tHol.textContent = 'NONE'; tHol.className = 'text-sm font-bold font-mono text-emerald-400'; }
          if (tCon) { tCon.textContent = '0 / 5'; }
          if (tMem) { tMem.textContent = '0 B'; }
          if (nPipe) { nPipe.innerHTML = '<div class="text-[10px] text-stone-500 font-mono w-full text-center" id="pipe-placeholder">Ready for transmission</div>'; }
          if (log) { log.innerHTML = 'Select protocol, toggle loss injection, and click <strong>Transmit 5 Packets</strong>.'; }
        }

        function startSimulation() {
          if (isTransmitting) return;
          resetSimulation();
          isTransmitting = true;
          document.getElementById('sender-status-badge').textContent = 'TRANSMITTING';
          document.getElementById('pipe-placeholder')?.remove();

          const pipe = document.getElementById('network-pipe');
          pipe.innerHTML = '';
          const log = document.getElementById('sim-log');
          log.innerHTML = `<span class="text-blue-400 font-bold">[SEND]</span> ${currentProtocol.toUpperCase()} Sender dispatched 5 segments (Packets #1..#5, 7,300 Bytes total)`;

          for (let i = 1; i <= 5; i++) {
            const pkt = document.createElement('div');
            pkt.id = `pkt-${i}`;
            pkt.className = 'px-2 py-0.5 text-[10px] font-mono rounded bg-blue-600 text-white font-bold mr-1 inline-block transition-all duration-500';
            pkt.textContent = `#${i}`;
            pipe.appendChild(pkt);
          }

          setTimeout(() => {
            deliverPacket(1);

            if (dropPacket2) {
              const p2 = document.getElementById('pkt-2');
              if (p2) {
                p2.className = 'px-2 py-0.5 text-[10px] font-mono rounded bg-rose-600 text-white font-bold mr-1 inline-block animate-pulse';
                p2.textContent = '💥 #2 DROPPED';
              }
              log.innerHTML += `<br/><span class="text-rose-400 font-bold">[ROUTER DROP]</span> Packet #2 dropped by intermediate queue overflow!`;
            } else {
              deliverPacket(2);
            }

            setTimeout(() => {
              [3, 4, 5].forEach(i => deliverPacket(i));

              if (currentProtocol === 'tcp' && dropPacket2) {
                document.getElementById('hol-badge').textContent = '🚨 HEAD-OF-LINE BLOCKING';
                document.getElementById('hol-badge').className = 'text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-rose-950 text-rose-300 border border-rose-800 animate-pulse';
                document.getElementById('telemetry-hol').textContent = '340 ms STALL';
                document.getElementById('telemetry-hol').className = 'text-sm font-bold font-mono text-rose-400';
                document.getElementById('telemetry-latency').textContent = '340 ms (P99)';
                document.getElementById('telemetry-consumed').textContent = '1 / 5';
                document.getElementById('telemetry-mem').textContent = '4,380 B';

                document.getElementById('app-read-stream').innerHTML += `
                  <div class="w-full mt-2 p-2 rounded bg-rose-950/40 border border-rose-800 text-[11px] text-rose-300 font-mono">
                    ⛔ App read() blocked: Kernel holds Packets #3, #4, #5 in receive queue, but cannot deliver them because Byte 1461 (#2) is missing from monotonic stream!
                  </div>
                `;
                document.getElementById('retransmit-action-area').classList.remove('hidden');
                log.innerHTML += `<br/><span class="text-amber-400 font-bold">[TCP STALL]</span> App blocked on socket read(). Packets 3, 4, 5 buffered out-of-order in kernel.`;
              } else if (currentProtocol === 'udp' && dropPacket2) {
                document.getElementById('hol-badge').textContent = '✅ FLUID DATAGRAM STREAM';
                document.getElementById('hol-badge').className = 'text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800';
                document.getElementById('telemetry-hol').textContent = 'NONE (0 ms)';
                document.getElementById('telemetry-hol').className = 'text-sm font-bold font-mono text-emerald-400';
                document.getElementById('telemetry-latency').textContent = '12 ms';
                document.getElementById('telemetry-consumed').textContent = '4 / 5 (Best Effort)';
                document.getElementById('telemetry-mem').textContent = '0 B';
                log.innerHTML += `<br/><span class="text-emerald-400 font-bold">[UDP DELIVER]</span> 4 datagrams passed directly to app with 0ms stall. Packet 2 loss ignored!`;
              } else {
                document.getElementById('hol-badge').textContent = '✅ COMPLETE';
                document.getElementById('hol-badge').className = 'text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-emerald-950 text-emerald-300';
                document.getElementById('telemetry-latency').textContent = '14 ms';
                document.getElementById('telemetry-consumed').textContent = '5 / 5';
                document.getElementById('telemetry-mem').textContent = '0 B';
              }
              isTransmitting = false;
            }, 700);
          }, 500);
        }

        function deliverPacket(num) {
          const kernelBuf = document.getElementById('kernel-buffer');
          const appStream = document.getElementById('app-read-stream');
          if (kernelBuf.innerHTML.includes('Buffer empty')) kernelBuf.innerHTML = '';
          if (appStream.innerHTML.includes('Waiting for application')) appStream.innerHTML = '';

          if (currentProtocol === 'tcp') {
            if (num === 1 || !dropPacket2) {
              appStream.innerHTML += `<span class="px-2 py-1 text-[11px] font-mono rounded bg-emerald-950 border border-emerald-700 text-emerald-300">ByteSeq: #${num} (1460B)</span>`;
            } else {
              kernelBuf.innerHTML += `<span class="px-2 py-0.5 text-[10px] font-mono rounded bg-amber-950 border border-amber-700 text-amber-300">OutOfOrder: #${num}</span>`;
            }
          } else {
            appStream.innerHTML += `<span class="px-2 py-1 text-[11px] font-mono rounded bg-emerald-950 border border-emerald-700 text-emerald-300">Datagram: #${num}</span>`;
          }
        }

        function retransmitPacket2() {
          const pipe = document.getElementById('network-pipe');
          const log = document.getElementById('sim-log');
          log.innerHTML += `<br/><span class="text-blue-400 font-bold">[RETRANSMIT]</span> Retransmitting Packet #2 across wire...`;

          const pkt2 = document.createElement('div');
          pkt2.className = 'px-2 py-0.5 text-[10px] font-mono rounded bg-amber-500 text-black font-bold mr-1 inline-block animate-bounce';
          pkt2.textContent = '⚡ #2 RETRANSMIT';
          pipe.appendChild(pkt2);

          setTimeout(() => {
            document.getElementById('kernel-buffer').innerHTML = '<span class="text-[10px] text-emerald-400 font-mono">✅ Monotonic sequence complete. Buffer flushed to application.</span>';
            const appStream = document.getElementById('app-read-stream');
            appStream.innerHTML = `
              <span class="px-2 py-1 text-[11px] font-mono rounded bg-emerald-950 border border-emerald-700 text-emerald-300">ByteSeq: #1</span>
              <span class="px-2 py-1 text-[11px] font-mono rounded bg-amber-900 border border-amber-500 text-white font-bold">ByteSeq: #2 (Recovered)</span>
              <span class="px-2 py-1 text-[11px] font-mono rounded bg-emerald-950 border border-emerald-700 text-emerald-300">ByteSeq: #3</span>
              <span class="px-2 py-1 text-[11px] font-mono rounded bg-emerald-950 border border-emerald-700 text-emerald-300">ByteSeq: #4</span>
              <span class="px-2 py-1 text-[11px] font-mono rounded bg-emerald-950 border border-emerald-700 text-emerald-300">ByteSeq: #5</span>
            `;
            document.getElementById('hol-badge').textContent = '✅ RESOLVED (5/5 CONSUMED)';
            document.getElementById('hol-badge').className = 'text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800';
            document.getElementById('telemetry-hol').textContent = 'RESOLVED';
            document.getElementById('telemetry-hol').className = 'text-sm font-bold font-mono text-emerald-400';
            document.getElementById('telemetry-consumed').textContent = '5 / 5 (Monotonic)';
            document.getElementById('telemetry-mem').textContent = '0 B';
            document.getElementById('retransmit-action-area').classList.add('hidden');
            log.innerHTML += `<br/><span class="text-emerald-400 font-bold">[FLUSH]</span> Packet #2 arrived! Kernel reassembled stream and flushed bytes 1461-7300 to application.`;
          }, 600);
        }
    """

    return {
        "PAGE_TITLE": "Topic — TCP vs UDP",
        "THEME_CSS_VARS": theme["css_vars"],
        "THEME_NAME": theme["name"],
        "THEME_ID": theme["id"],
        "TIER_BADGE": tier or "Tier 0 · System Design Core",
        "CLUSTER_BADGE": cluster or "1. [0.1] APIs & Network Transport for Design",
        "LESSON_TITLE": "TCP vs UDP",
        "LESSON_SUBTITLE": "A first-principles, causal breakdown of physical network constraints, packet loss recovery, and the trade-off between reliability and tail latency.",

        # PHASE 1: The Raw Physical Reality & Forcing Dilemma
        "SECTION_1_TITLE": "The Physical Reality: Why Transport Layer Abstractions Exist",
        "SECTION_1_BODY": """
        <p>
          Before analyzing the software machinery of <strong>TCP and UDP</strong>, we must confront the immutable laws of physical network hardware: the non-zero speed of light in silica glass, finite router buffer memories, and the uncoordinated nature of packet-switched networks.
        </p>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-3 my-4">
          <div class="p-3.5 rounded-xl bg-[var(--card)] border border-[var(--card-border)]">
            <div class="text-[11px] font-mono font-bold text-amber-400 uppercase">Speed of Light in Fiber</div>
            <div class="text-base font-bold text-[var(--foreground)] mt-1">~5 μs per km</div>
            <p class="text-xs text-[var(--muted-foreground)] mt-1 mb-0 leading-relaxed">
              Propagating photons through glass refractive index (n ≈ 1.47) means a 6,000 km trans-Atlantic link has an unbreakable physical lower bound of ~30 ms one-way (~60 ms RTT).
            </p>
          </div>
          <div class="p-3.5 rounded-xl bg-[var(--card)] border border-[var(--card-border)]">
            <div class="text-[11px] font-mono font-bold text-blue-400 uppercase">Ethernet MTU Limit</div>
            <div class="text-base font-bold text-[var(--foreground)] mt-1">1,500 Bytes</div>
            <p class="text-xs text-[var(--muted-foreground)] mt-1 mb-0 leading-relaxed">
              Standard physical Ethernet frames cap payloads at 1500 bytes. A single 10 MB payload must be fragmented into ~7,100 discrete network frames.
            </p>
          </div>
          <div class="p-3.5 rounded-xl bg-[var(--card)] border border-[var(--card-border)]">
            <div class="text-[11px] font-mono font-bold text-rose-400 uppercase">IP Layer Unreliability</div>
            <div class="text-base font-bold text-[var(--foreground)] mt-1">Best-Effort Datagrams</div>
            <p class="text-xs text-[var(--muted-foreground)] mt-1 mb-0 leading-relaxed">
              Routers have finite queue buffers. Under burst load, routers silently drop packets (tail drop). Dynamic routing can deliver packets out-of-order or duplicated.
            </p>
          </div>
        </div>

        <div class="callout-box callout-dilemma">
          <div class="text-xs font-mono font-bold text-rose-400 uppercase tracking-wider mb-1">⚡ The Core Architectural Tension</div>
          <p class="text-sm text-[var(--foreground)] m-0">
            If an application transmits 7,100 discrete IP packets across an uncoordinated network, it faces an inescapable dilemma:
            <strong>Stop-and-Wait</strong> (send 1 packet, wait 60ms for ACK) collapses throughput to 1460 B / 0.06s = <strong>24 KB/s</strong> over a 10 Gbps fiber line.
            <strong>Unthrottled Broadcast</strong> (blast all 7,100 packets immediately) overflows router buffers, causing catastrophic packet drops and silent corruption.
            Transport protocols are the mathematical and operational resolution to this physical tension.
          </p>
        </div>
        """,

        # PHASE 2: The Core Abstraction & Header Anatomy
        "SECTION_2_TITLE": "The Architectural Contract: Stream vs Datagram Semantics",
        "SECTION_2_BODY": """
        <p>
          At Layer 4 of the OSI model, operating systems provide two fundamentally distinct contracts to bridge physical packet switching and user-space application code:
        </p>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 my-4">
          <div class="p-5 rounded-xl bg-[var(--card)] border border-[var(--card-border)] space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-xs font-mono font-bold text-blue-400 uppercase">Transmission Control Protocol (TCP)</span>
              <span class="text-[11px] font-mono px-2 py-0.5 rounded bg-blue-950 text-blue-300">20–60 Bytes Header</span>
            </div>
            <h4 class="text-sm font-bold text-[var(--foreground)]">Full-Duplex, Ordered Byte-Stream</h4>
            <p class="text-xs text-[var(--muted-foreground)] leading-relaxed m-0">
              Presents the illusion of a continuous, error-free pipe. Sequences and acknowledges every byte offset. Maintains a Transmission Control Block (TCB) in kernel memory (~2–4 KB per socket) tracking window sizing, timers, and state machines.
            </p>
          </div>
          <div class="p-5 rounded-xl bg-[var(--card)] border border-[var(--card-border)] space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-xs font-mono font-bold text-emerald-400 uppercase">User Datagram Protocol (UDP)</span>
              <span class="text-[11px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-300">Lean 8 Bytes Header</span>
            </div>
            <h4 class="text-sm font-bold text-[var(--foreground)]">Stateless, Boundary-Preserving Datagram</h4>
            <p class="text-xs text-[var(--muted-foreground)] leading-relaxed m-0">
              A thin multiplexing wrapper around raw IP. Adds only source/dest port addressing and an optional 16-bit checksum. Zero kernel connection state, zero handshakes, zero delivery or ordering guarantees.
            </p>
          </div>
        </div>

        <div class="callout-box callout-mechanism">
          <div class="text-xs font-mono font-bold text-[var(--primary)] uppercase tracking-wider mb-1">🔍 Byte-Level Header Anatomy</div>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-2 font-mono text-xs">
            <div class="p-3 rounded bg-[var(--background)] border border-[var(--border)]">
              <div class="text-blue-400 font-bold mb-1">TCP Header Layout (Minimum 20 Bytes)</div>
              <div class="space-y-1 text-[11px] text-[var(--muted-foreground)]">
                <div>• Source Port (16b) | Dest Port (16b)</div>
                <div>• Sequence Number (32b: byte offset in stream)</div>
                <div>• Acknowledgment Number (32b: cumulative next byte)</div>
                <div>• Data Offset (4b) | Flags: SYN, ACK, FIN, RST, PSH, URG (9b)</div>
                <div>• Receive Window `rwnd` (16b: flow control buffer)</div>
                <div>• Checksum (16b) | Urgent Pointer (16b)</div>
                <div>• Options (0–40B: MSS, Window Scale, SACK)</div>
              </div>
            </div>
            <div class="p-3 rounded bg-[var(--background)] border border-[var(--border)]">
              <div class="text-emerald-400 font-bold mb-1">UDP Header Layout (Strictly 8 Bytes)</div>
              <div class="space-y-1 text-[11px] text-[var(--muted-foreground)]">
                <div>• Source Port (16 bits)</div>
                <div>• Destination Port (16 bits)</div>
                <div>• Length (16 bits: header + payload in bytes)</div>
                <div>• Checksum (16 bits: header + pseudo-header)</div>
                <div class="text-stone-500 italic pt-2">No sequence numbers. No window sizes. No flags. No connection state.</div>
              </div>
            </div>
          </div>
        </div>
        """,

        # PHASE 3: Under the Hood, HoL Blocking & Interactive Simulator
        "SECTION_3_TITLE": "Under the Hood: Flow Control, Congestion Control & Head-of-Line Blocking",
        "SECTION_3_BODY": f"""
        <p>
          To understand why one protocol thrives while the other collapses under specific network conditions, we must isolate three kernel mechanisms:
        </p>

        <div class="space-y-3 my-3">
          <div class="p-3 rounded-lg bg-[var(--card)] border border-[var(--card-border)]">
            <strong class="text-xs font-mono text-[var(--primary)]">1. The 1-RTT Handshake Penalty:</strong>
            <span class="text-xs text-[var(--muted-foreground)] ml-1">
              TCP mandates a 3-way handshake (<code>SYN &rarr; SYN-ACK &rarr; ACK</code>). Before any application byte moves, the client pays a full 60ms Round-Trip Time. UDP has zero connection establishment (0-RTT); the very first packet carries application data.
            </span>
          </div>
          <div class="p-3 rounded-lg bg-[var(--card)] border border-[var(--card-border)]">
            <strong class="text-xs font-mono text-[var(--primary)]">2. Flow Control (rwnd) vs Congestion Control (cwnd):</strong>
            <span class="text-xs text-[var(--muted-foreground)] ml-1">
              <strong>Flow control</strong> protects the <em>receiver</em> from buffer exhaustion via advertised <code>rwnd</code>. <strong>Congestion control</strong> protects the <em>network</em> from collapse using a dynamic congestion window (<code>cwnd</code>), dynamically probing bandwidth via Slow Start and AIMD (Additive Increase, Multiplicative Decrease).
            </span>
          </div>
          <div class="p-3 rounded-lg bg-[var(--card)] border border-[var(--card-border)]">
            <strong class="text-xs font-mono text-rose-400">3. Head-of-Line (HoL) Blocking at the Transport Layer:</strong>
            <span class="text-xs text-[var(--muted-foreground)] ml-1">
              The POSIX socket API (<code>read()</code> / <code>recv()</code>) exposes a contiguous, sequential byte stream. If Packet #2 is dropped by an intermediate router, but Packets #3, #4, and #5 arrive safely, the receiver kernel buffers them in its TCP socket queue, but <strong>strictly refuses</strong> to deliver them to user-space! The application thread stalls until Packet #2 is retransmitted and acknowledged.
            </span>
          </div>
        </div>
        {sim_html}
        <div class="callout-box callout-invariant">
          <div class="text-xs font-mono font-bold text-emerald-400 uppercase tracking-wider mb-1">⚖️ The Fundamental Invariant Trade-off</div>
          <p class="text-sm text-[var(--foreground)] m-0">
            <strong>TCP guarantees completeness and monotonic ordering at the expense of unbounded tail latency.</strong> Under packet loss, jitter spikes uncontrollably.<br/>
            <strong>UDP guarantees bounded latency and zero Head-of-Line blocking at the expense of completeness.</strong> The application must tolerate dropped or out-of-order datagrams.
          </p>
        </div>
        """,

        # PHASE 4: Mental Model Synthesis & Production Grounding
        "SECTION_4_TITLE": "Mental Model Synthesis, Production Grounding & Sizing Reality",
        "SECTION_4_BODY": """
        <p>
          Every architectural decision in production systems boils down to which penalty your domain can afford to pay: <em>tail-latency jitter</em> or <em>loss recovery complexity</em>.
        </p>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 my-4">
          <div class="p-5 rounded-xl bg-[var(--card)] border border-[var(--card-border)] space-y-2">
            <div class="text-xs font-mono font-bold text-blue-400 uppercase">Durability-Critical: Financial Ledgers & DB Logs</div>
            <h4 class="text-sm font-bold text-[var(--foreground)]">Postgres WAL Streaming / Payment Transactions</h4>
            <p class="text-xs text-[var(--muted-foreground)] leading-relaxed m-0">
              Dropping a single byte of a write-ahead log invalidates database consistency. Systems gladly absorb a 400ms tail-latency stall while TCP recovers dropped segments, because data corruption is existential failure.
            </p>
          </div>
          <div class="p-5 rounded-xl bg-[var(--card)] border border-[var(--card-border)] space-y-2">
            <div class="text-xs font-mono font-bold text-emerald-400 uppercase">Latency-Critical: Real-Time Audio / Video & Games</div>
            <h4 class="text-sm font-bold text-[var(--foreground)]">WebRTC Voice Stream / Online Game Physics</h4>
            <p class="text-xs text-[var(--muted-foreground)] leading-relaxed m-0">
              Human auditory perception detects speech stalls over 150ms. A 400ms late audio frame is worthless garbage. Dropping the late frame and rendering the next frame immediately produces seamless audio.
            </p>
          </div>
        </div>

        <div class="callout-box callout-trap">
          <div class="text-xs font-mono font-bold text-amber-400 uppercase tracking-wider mb-1">🚀 The Modern Revolution: QUIC & HTTP/3</div>
          <p class="text-sm text-[var(--foreground)] m-0">
            Why did HTTP/2 (multiplexing streams over a single TCP connection) suffer on lossy cellular networks? Because TCP's transport-level Head-of-Line blocking meant 1 dropped packet stalled <strong>every single multiplexed stream</strong> simultaneously!
            <strong>QUIC (HTTP/3)</strong> solves this by moving reliable stream state and TLS 1.3 into user-space on top of <strong>UDP</strong>. A dropped packet on Stream A only pauses Stream A; Streams B and C proceed with zero stall!
          </p>
        </div>

        <div class="p-4 rounded-xl bg-[var(--card)] border border-[var(--card-border)] my-4">
          <h4 class="text-xs font-mono font-bold text-[var(--primary)] uppercase tracking-wider mb-2">📐 Production Sizing Formulas</h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
            <div class="p-3 rounded bg-[var(--background)] border border-[var(--border)]">
              <div class="font-bold text-[var(--foreground)]">Bandwidth-Delay Product (BDP)</div>
              <div class="font-mono text-cyan-400 mt-0.5">BDP = Bandwidth (bps) × RTT (s)</div>
              <p class="text-[11px] text-[var(--muted-foreground)] mt-1 mb-0">
                A 10 Gbps transcontinental link with 50ms RTT requires <code>10e9 × 0.050 / 8 = 62.5 MB</code> of in-flight unacknowledged data in socket buffers to fully saturate link capacity.
              </p>
            </div>
            <div class="p-3 rounded bg-[var(--background)] border border-[var(--border)]">
              <div class="font-bold text-[var(--foreground)]">Ephemeral Port Exhaustion (TIME_WAIT)</div>
              <div class="font-mono text-amber-400 mt-0.5">2MSL = 60s to 120s Retention</div>
              <p class="text-[11px] text-[var(--muted-foreground)] mt-1 mb-0">
                A microservice opening and closing short-lived TCP connections at > 1,000 req/sec will rapidly exhaust the 65,535 ephemeral port range due to kernel TIME_WAIT socket states.
              </p>
            </div>
          </div>
        </div>
        """,

        # PHASE 5: Contextual Sign-Off Verification Gate
        "SECTION_5_TITLE": "Contextual Sign-Off Verification: Active Defense Gate",
        "SECTION_5_BODY": """
        <div class="callout-box callout-trap">
          <div class="flex items-start gap-3">
            <div class="text-amber-400 font-bold text-lg mt-0.5">⚠️</div>
            <div class="space-y-2">
              <h4 class="font-bold text-[var(--foreground)] text-base m-0">Production Incident: The Cellular Dashboard Tail-Latency Mystery</h4>
              <p class="text-sm text-[var(--muted-foreground)] leading-relaxed">
                A distributed real-time dashboard tracking vehicle telemetry on 4G/5G cellular links experiences catastrophic P99 tail-latency spikes exceeding 850ms, even though backend server CPU utilization is below 20% and network bandwidth is only 15% utilized.
              </p>
              <p class="text-sm text-[var(--muted-foreground)] leading-relaxed">
                A junior engineer suggests: <em>"Let's double the TCP socket receive buffer (<code>SO_RCVBUF</code>) on both client and server to smooth out the spikes."</em>
              </p>
              <div class="p-3 rounded-lg bg-[var(--background)] border border-[var(--border)] space-y-1">
                <div class="text-xs font-mono font-bold text-rose-400 uppercase">Your Defense Challenge:</div>
                <ul class="text-xs text-[var(--foreground)] space-y-1 m-0 pl-4 list-disc">
                  <li>Why will expanding socket buffer sizes fail to resolve the latency spikes, and why does it actually worsen P99 tail latency (Bufferbloat)?</li>
                  <li>Where in the physical and kernel stack is the queue accumulating when cellular packets encounter transient radio interference?</li>
                  <li>How does transport protocol selection (TCP vs UDP/QUIC) causally explain why CPU is idle while latency is spiking?</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        <div class="p-4 rounded-xl bg-[var(--background)] border border-[var(--border)] space-y-2 text-xs text-[var(--muted-foreground)]">
          <div class="font-bold text-[var(--primary)] flex items-center gap-2">
            <span>🎯 Sign-Off Gate Defense Standard:</span>
          </div>
          <p class="leading-relaxed m-0">
            Tick off when: you can defend this incident scenario cold in chat discussion without notes, tracing the buffer queue location in cellular base stations, the mathematics of Bufferbloat, and why application-layer retry over TCP causes cascading tail spikes.
          </p>
          <div class="pt-2 text-[11px] font-mono text-amber-400 flex items-center gap-2">
            <span class="inline-block w-2 h-2 rounded-full bg-amber-400"></span>
            <span>No solution is provided in this artifact. Discuss and defend your architectural breakdown in chat using <code>/sds-discuss</code>.</span>
          </div>
        </div>
        """,

        "BACKWARD_ANCHOR": "Physical network boundaries & hardware constraints",
        "FORWARD_HOOK": "HTTP/1.1 vs HTTP/2 vs HTTP/3: Multiplexing over Single Transport Stream",
        "EMBEDDED_JAVASCRIPT": sim_js
    }


def build_http_versions_data(theme, tier=None, cluster=None):
    sim_html = """
        <div class="sim-container">
          <div class="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-3 border-b border-[var(--border)]">
            <div>
              <div class="text-sm font-bold text-[var(--foreground)] flex items-center gap-2">
                <span class="inline-block w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
                Tactile Simulator: Where Head-of-Line Blocking Lives Across HTTP Generations
              </div>
              <div class="text-xs text-[var(--muted-foreground)]">Switch between HTTP/1.1, HTTP/2, and HTTP/3 to observe Application vs Transport HoL blocking.</div>
            </div>
            <div class="flex flex-wrap items-center gap-2">
              <div class="flex items-center gap-1 bg-[var(--background)] p-1 rounded-lg border border-[var(--border)] text-xs font-mono">
                <button id="h-btn-1" onclick="setHttpVersion('h1')" class="px-2.5 py-1 rounded font-bold bg-[var(--primary)] text-white transition">HTTP/1.1</button>
                <button id="h-btn-2" onclick="setHttpVersion('h2')" class="px-2.5 py-1 rounded text-[var(--muted-foreground)] hover:text-white transition">HTTP/2</button>
                <button id="h-btn-3" onclick="setHttpVersion('h3')" class="px-2.5 py-1 rounded text-[var(--muted-foreground)] hover:text-white transition">HTTP/3 (QUIC)</button>
              </div>
              <div class="flex items-center gap-1 bg-[var(--card)] px-2 py-1 rounded-lg border border-[var(--border)] text-xs font-mono">
                <label class="cursor-pointer text-[var(--muted-foreground)] hover:text-white flex items-center gap-1">
                  <input type="radio" name="sim-scenario" value="slow" id="scen-slow" checked onchange="setHttpScenario('slow')" class="accent-[var(--primary)]">
                  <span>Slow Server API</span>
                </label>
                <span class="text-stone-600">|</span>
                <label class="cursor-pointer text-[var(--muted-foreground)] hover:text-white flex items-center gap-1">
                  <input type="radio" name="sim-scenario" value="drop" id="scen-drop" onchange="setHttpScenario('drop')" class="accent-[var(--primary)]">
                  <span>Packet Drop (Cellular)</span>
                </label>
              </div>
              <button onclick="runHttpSimulation()" class="px-3 py-1.5 text-xs font-semibold rounded-lg bg-[var(--primary)] text-white hover:opacity-90 transition">Load Web Page →</button>
              <button onclick="resetHttpSimulation()" class="px-3 py-1.5 text-xs font-semibold rounded-lg bg-[var(--background)] border border-[var(--border)] text-[var(--foreground)] hover:bg-[var(--card)] transition">Reset</button>
            </div>
          </div>

          <!-- Main Visual Grid -->
          <div class="sim-canvas my-4 space-y-4">
            <!-- Resource Request Pipeline -->
            <div class="space-y-2">
              <div class="text-[11px] font-mono text-[var(--muted-foreground)] uppercase">Browser Parallel Resource Requests:</div>
              <div class="grid grid-cols-1 md:grid-cols-3 gap-2">
                <!-- Resource 1 -->
                <div class="p-3 rounded-lg bg-[var(--card)] border border-[var(--card-border)] flex items-center justify-between" id="card-res-1">
                  <div>
                    <div class="text-xs font-bold text-amber-400">Stream #1: /api/user.json</div>
                    <div class="text-[10px] text-[var(--muted-foreground)] font-mono" id="desc-res-1">Backend DB Query (400ms)</div>
                  </div>
                  <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-stone-800 text-stone-400" id="badge-res-1">QUEUED</span>
                </div>
                <!-- Resource 2 -->
                <div class="p-3 rounded-lg bg-[var(--card)] border border-[var(--card-border)] flex items-center justify-between" id="card-res-2">
                  <div>
                    <div class="text-xs font-bold text-blue-400">Stream #2: /styles/app.css</div>
                    <div class="text-[10px] text-[var(--muted-foreground)] font-mono">Render-Blocking CSS (15ms)</div>
                  </div>
                  <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-stone-800 text-stone-400" id="badge-res-2">QUEUED</span>
                </div>
                <!-- Resource 3 -->
                <div class="p-3 rounded-lg bg-[var(--card)] border border-[var(--card-border)] flex items-center justify-between" id="card-res-3">
                  <div>
                    <div class="text-xs font-bold text-emerald-400">Stream #3: /scripts/main.js</div>
                    <div class="text-[10px] text-[var(--muted-foreground)] font-mono">App Logic (20ms)</div>
                  </div>
                  <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-stone-800 text-stone-400" id="badge-res-3">QUEUED</span>
                </div>
              </div>
            </div>

            <!-- Wire & Transport Pipe Layer -->
            <div class="p-3.5 rounded-xl bg-[var(--card)] border border-[var(--card-border)]">
              <div class="flex items-center justify-between mb-1.5">
                <span class="text-xs font-mono font-bold text-[var(--foreground)]" id="wire-layer-title">TCP Pipe: Single Connection (Strict Monotonic Byte Stream)</span>
                <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-stone-800 text-stone-400" id="wire-status">IDLE</span>
              </div>
              <div class="w-full h-10 bg-[var(--background)] rounded-lg border border-[var(--border)] flex items-center px-3 relative overflow-hidden" id="wire-display">
                <span class="text-[10px] font-mono text-stone-500 w-full text-center" id="wire-idle-msg">Ready to initiate page load sequence</span>
              </div>
            </div>

            <!-- Browser DOM & Render Engine State -->
            <div class="p-3.5 rounded-xl bg-[var(--card)] border border-[var(--card-border)]">
              <div class="flex items-center justify-between mb-1.5">
                <span class="text-xs font-mono font-bold uppercase tracking-wider text-[var(--foreground)]">Browser Rendering Engine (FCP & DOM Parsing)</span>
                <span class="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-stone-800 text-stone-400" id="render-status">AWAITING STYLESHEET</span>
              </div>
              <div class="p-2.5 rounded-lg bg-[var(--background)] border border-[var(--border)] min-h-[40px] flex items-center gap-2 text-xs font-mono" id="render-display">
                <span class="text-stone-500 italic">Page blank (white screen). Waiting for render-blocking CSS...</span>
              </div>
            </div>

            <!-- Telemetry Metrics -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-2 pt-1">
              <div class="p-2.5 rounded-lg bg-[var(--card)] border border-[var(--card-border)] text-center">
                <div class="text-[10px] font-mono text-[var(--muted-foreground)] uppercase">First Contentful Paint (FCP)</div>
                <div class="text-sm font-bold font-mono text-[var(--foreground)]" id="h-tel-fcp">-- ms</div>
              </div>
              <div class="p-2.5 rounded-lg bg-[var(--card)] border border-[var(--card-border)] text-center">
                <div class="text-[10px] font-mono text-[var(--muted-foreground)] uppercase">HoL Blocking Location</div>
                <div class="text-sm font-bold font-mono text-amber-400" id="h-tel-hol">NONE</div>
              </div>
              <div class="p-2.5 rounded-lg bg-[var(--card)] border border-[var(--card-border)] text-center">
                <div class="text-[10px] font-mono text-[var(--muted-foreground)] uppercase">TCP / UDP Sockets</div>
                <div class="text-sm font-bold font-mono text-[var(--foreground)]" id="h-tel-sockets">1 TCP</div>
              </div>
              <div class="p-2.5 rounded-lg bg-[var(--card)] border border-[var(--card-border)] text-center">
                <div class="text-[10px] font-mono text-[var(--muted-foreground)] uppercase">Connection Handshake Cost</div>
                <div class="text-sm font-bold font-mono text-cyan-400" id="h-tel-rtt">1 RTT (TCP)</div>
              </div>
            </div>
          </div>

          <div class="sim-log" id="sim-log">
            Select an HTTP version, choose a failure scenario, and click <strong>Load Web Page</strong>.
          </div>
        </div>
    """

    sim_js = """
        let httpVer = 'h1';
        let httpScen = 'slow';
        let httpRunning = false;

        function setHttpVersion(v) {
          if (httpRunning) return;
          httpVer = v;
          ['h1', 'h2', 'h3'].forEach(k => {
            const b = document.getElementById('h-btn-' + k.slice(1));
            if (b) {
              if (k === v) {
                b.className = 'px-2.5 py-1 rounded font-bold bg-[var(--primary)] text-white transition';
              } else {
                b.className = 'px-2.5 py-1 rounded text-[var(--muted-foreground)] hover:text-white transition';
              }
            }
          });
          updateWireTitle();
          resetHttpSimulation();
        }

        function setHttpScenario(s) {
          if (httpRunning) return;
          httpScen = s;
          const desc1 = document.getElementById('desc-res-1');
          if (desc1) {
            desc1.textContent = s === 'slow' ? 'Backend DB Query (400ms)' : 'Cellular Loss (Packet Dropped)';
          }
          resetHttpSimulation();
        }

        function updateWireTitle() {
          const t = document.getElementById('wire-layer-title');
          const sock = document.getElementById('h-tel-sockets');
          const rtt = document.getElementById('h-tel-rtt');
          if (httpVer === 'h1') {
            if (t) t.textContent = 'HTTP/1.1 Pipe: Single TCP Connection (FIFO Request/Response Queue)';
            if (sock) sock.textContent = '1 TCP (or 6 sharded)';
            if (rtt) rtt.textContent = '1 RTT (TCP) + 1 RTT (TLS)';
          } else if (httpVer === 'h2') {
            if (t) t.textContent = 'HTTP/2 Pipe: Single TCP Connection (Interleaved Binary Frames)';
            if (sock) sock.textContent = '1 TCP Socket';
            if (rtt) rtt.textContent = '1 RTT (TCP) + 1 RTT (TLS)';
          } else {
            if (t) t.textContent = 'HTTP/3 Pipe: QUIC over UDP (Independent Byte Streams per Resource)';
            if (sock) sock.textContent = '1 Stateless UDP';
            if (rtt) rtt.textContent = '0-RTT / 1-RTT Fused';
          }
        }

        function resetHttpSimulation() {
          httpRunning = false;
          ['1', '2', '3'].forEach(i => {
            const b = document.getElementById('badge-res-' + i);
            if (b) { b.textContent = 'QUEUED'; b.className = 'text-[10px] font-mono px-2 py-0.5 rounded bg-stone-800 text-stone-400'; }
          });
          const wireStatus = document.getElementById('wire-status');
          const wireDisp = document.getElementById('wire-display');
          const rStatus = document.getElementById('render-status');
          const rDisp = document.getElementById('render-display');
          const telFcp = document.getElementById('h-tel-fcp');
          const telHol = document.getElementById('h-tel-hol');
          const log = document.getElementById('sim-log');

          if (wireStatus) { wireStatus.textContent = 'IDLE'; wireStatus.className = 'text-[10px] font-mono px-2 py-0.5 rounded bg-stone-800 text-stone-400'; }
          if (wireDisp) { wireDisp.innerHTML = '<span class="text-[10px] font-mono text-stone-500 w-full text-center" id="wire-idle-msg">Ready to initiate page load sequence</span>'; }
          if (rStatus) { rStatus.textContent = 'AWAITING STYLESHEET'; rStatus.className = 'text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-stone-800 text-stone-400'; }
          if (rDisp) { rDisp.innerHTML = '<span class="text-stone-500 italic">Page blank (white screen). Waiting for render-blocking CSS...</span>'; }
          if (telFcp) { telFcp.textContent = '-- ms'; }
          if (telHol) { telHol.textContent = 'NONE'; telHol.className = 'text-sm font-bold font-mono text-emerald-400'; }
          if (log) { log.innerHTML = 'Click <strong>Load Web Page</strong> to trace request execution across the network.'; }
          updateWireTitle();
        }

        function runHttpSimulation() {
          if (httpRunning) return;
          resetHttpSimulation();
          httpRunning = true;
          const log = document.getElementById('sim-log');
          const wire = document.getElementById('wire-display');
          wire.innerHTML = '';

          if (httpVer === 'h1') {
            // HTTP/1.1 Execution
            log.innerHTML = `<span class="text-blue-400 font-bold">[HTTP/1.1]</span> Dispatched Request #1 (/api/user.json) over TCP connection...`;
            document.getElementById('badge-res-1').textContent = 'SENT (IN-FLIGHT)';
            document.getElementById('badge-res-1').className = 'text-[10px] font-mono px-2 py-0.5 rounded bg-amber-950 text-amber-300 animate-pulse';
            
            document.getElementById('badge-res-2').textContent = 'WAITING ON #1';
            document.getElementById('badge-res-2').className = 'text-[10px] font-mono px-2 py-0.5 rounded bg-rose-950 text-rose-300';
            document.getElementById('badge-res-3').textContent = 'WAITING ON #2';
            document.getElementById('badge-res-3').className = 'text-[10px] font-mono px-2 py-0.5 rounded bg-rose-950 text-rose-300';

            document.getElementById('h-tel-hol').textContent = 'APPLICATION LAYER';
            document.getElementById('h-tel-hol').className = 'text-sm font-bold font-mono text-rose-400 animate-pulse';

            wire.innerHTML = `
              <div class="px-2 py-1 rounded bg-amber-900 border border-amber-600 text-[10px] font-mono text-amber-200 animate-pulse">
                [HTTP/1.1 FIFO] Req #1 Processing on Server (Slow DB Query)... Stylesheet #2 blocked behind it!
              </div>
            `;

            setTimeout(() => {
              document.getElementById('badge-res-1').textContent = '200 OK (420ms)';
              document.getElementById('badge-res-1').className = 'text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-300';
              log.innerHTML += `<br/><span class="text-amber-400 font-bold">[HOL DELAY]</span> Response #1 finished after 420ms. Only NOW can Request #2 (/styles/app.css) enter the wire!`;

              document.getElementById('badge-res-2').textContent = 'IN-FLIGHT (435ms)';
              document.getElementById('badge-res-2').className = 'text-[10px] font-mono px-2 py-0.5 rounded bg-blue-950 text-blue-300';

              setTimeout(() => {
                document.getElementById('badge-res-2').textContent = '200 OK (450ms)';
                document.getElementById('badge-res-2').className = 'text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-300';
                document.getElementById('render-status').textContent = 'RENDERED (FCP: 450ms)';
                document.getElementById('render-status').className = 'text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-emerald-950 text-emerald-300';
                document.getElementById('render-display').innerHTML = '<span class="text-emerald-400 font-bold">🎨 Stylesheet loaded! DOM rendered after 450ms application stall.</span>';
                document.getElementById('h-tel-fcp').textContent = '450 ms';

                document.getElementById('badge-res-3').textContent = '200 OK (475ms)';
                document.getElementById('badge-res-3').className = 'text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-300';
                httpRunning = false;
              }, 400);
            }, 600);

          } else if (httpVer === 'h2') {
            // HTTP/2 Execution
            log.innerHTML = `<span class="text-cyan-400 font-bold">[HTTP/2]</span> Binary Framing Active: Interleaving Streams #1, #2, #3 over single TCP connection...`;
            ['1', '2', '3'].forEach(i => {
              const b = document.getElementById('badge-res-' + i);
              b.textContent = 'MULTIPLEXED';
              b.className = 'text-[10px] font-mono px-2 py-0.5 rounded bg-blue-950 text-blue-300';
            });

            if (httpScen === 'slow') {
              // Scenario Slow: H2 wins over H1!
              wire.innerHTML = `
                <div class="flex gap-1.5 w-full items-center">
                  <span class="px-2 py-0.5 rounded bg-blue-700 text-white text-[10px] font-mono">Stream 2: CSS Frame (Done in 25ms)</span>
                  <span class="px-2 py-0.5 rounded bg-emerald-700 text-white text-[10px] font-mono">Stream 3: JS Frame (Done in 35ms)</span>
                  <span class="px-2 py-0.5 rounded bg-amber-900 border border-amber-600 text-amber-200 text-[10px] font-mono animate-pulse">Stream 1: Data Frame (Pending DB)</span>
                </div>
              `;
              setTimeout(() => {
                document.getElementById('badge-res-2').textContent = '200 OK (25ms)';
                document.getElementById('badge-res-2').className = 'text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-300';
                document.getElementById('badge-res-3').textContent = '200 OK (35ms)';
                document.getElementById('badge-res-3').className = 'text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-300';

                document.getElementById('render-status').textContent = 'RENDERED (FCP: 25ms)';
                document.getElementById('render-status').className = 'text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-emerald-950 text-emerald-300';
                document.getElementById('render-display').innerHTML = '<span class="text-emerald-400 font-bold">🚀 Fast First Paint! CSS multiplexed ahead of slow DB query in 25ms.</span>';
                document.getElementById('h-tel-fcp').textContent = '25 ms';
                document.getElementById('h-tel-hol').textContent = 'NONE (App Layer Solved)';
                document.getElementById('h-tel-hol').className = 'text-sm font-bold font-mono text-emerald-400';

                setTimeout(() => {
                  document.getElementById('badge-res-1').textContent = '200 OK (420ms)';
                  document.getElementById('badge-res-1').className = 'text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-300';
                  httpRunning = false;
                }, 400);
              }, 400);

            } else {
              // Scenario Drop: H2 collapses due to TCP HoL Blocking!
              log.innerHTML += `<br/><span class="text-rose-400 font-bold">[PACKET LOSS]</span> 1 IP packet in Stream #1 was dropped by cellular network!`;
              wire.innerHTML = `
                <div class="p-1.5 rounded bg-rose-950/80 border border-rose-700 text-[10px] font-mono text-rose-200 w-full text-center animate-pulse">
                  🚨 TCP RECEIVE BUFFER LOCKED: Kernel holding Stream 2 & Stream 3 frames because Stream 1 segment is missing!
                </div>
              `;
              document.getElementById('h-tel-hol').textContent = 'TCP TRANSPORT LAYER';
              document.getElementById('h-tel-hol').className = 'text-sm font-bold font-mono text-rose-400 animate-pulse';

              document.getElementById('badge-res-1').textContent = 'RETRANSMITTING';
              document.getElementById('badge-res-1').className = 'text-[10px] font-mono px-2 py-0.5 rounded bg-rose-950 text-rose-300 animate-pulse';
              document.getElementById('badge-res-2').textContent = 'TCP STALLED';
              document.getElementById('badge-res-2').className = 'text-[10px] font-mono px-2 py-0.5 rounded bg-rose-950 text-rose-300';
              document.getElementById('badge-res-3').textContent = 'TCP STALLED';
              document.getElementById('badge-res-3').className = 'text-[10px] font-mono px-2 py-0.5 rounded bg-rose-950 text-rose-300';

              setTimeout(() => {
                log.innerHTML += `<br/><span class="text-amber-400 font-bold">[TCP RECOVERY]</span> Retransmit arrived after 380ms. Kernel socket queue finally unblocked.`;
                ['1', '2', '3'].forEach(i => {
                  const b = document.getElementById('badge-res-' + i);
                  b.textContent = '200 OK (390ms)';
                  b.className = 'text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-300';
                });
                document.getElementById('render-status').textContent = 'DELAYED (FCP: 390ms)';
                document.getElementById('render-status').className = 'text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-rose-950 text-rose-300';
                document.getElementById('render-display').innerHTML = '<span class="text-rose-400 font-bold">⛔ High Tail Latency: Dropped packet in Stream 1 stalled the CSS & JS streams!</span>';
                document.getElementById('h-tel-fcp').textContent = '390 ms';
                httpRunning = false;
              }, 700);
            }

          } else {
            // HTTP/3 (QUIC) Execution
            log.innerHTML = `<span class="text-emerald-400 font-bold">[HTTP/3 QUIC]</span> Dispatched across UDP with independent stream loss recovery...`;
            ['1', '2', '3'].forEach(i => {
              const b = document.getElementById('badge-res-' + i);
              b.textContent = 'INDEPENDENT STREAM';
              b.className = 'text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-300';
            });

            if (httpScen === 'drop') {
              wire.innerHTML = `
                <div class="flex gap-1.5 w-full items-center">
                  <span class="px-2 py-0.5 rounded bg-rose-900 border border-rose-600 text-rose-200 text-[10px] font-mono animate-pulse">Stream 1: Packet Dropped (Retransmitting alone)</span>
                  <span class="px-2 py-0.5 rounded bg-emerald-700 text-white text-[10px] font-mono">Stream 2: CSS Delivered (18ms)</span>
                  <span class="px-2 py-0.5 rounded bg-emerald-700 text-white text-[10px] font-mono">Stream 3: JS Delivered (22ms)</span>
                </div>
              `;
              log.innerHTML += `<br/><span class="text-emerald-400 font-bold">[ZERO HOL BLOCKING]</span> Packet loss on Stream 1 had ZERO effect on Streams 2 and 3!`;
            } else {
              wire.innerHTML = `
                <div class="flex gap-1.5 w-full items-center">
                  <span class="px-2 py-0.5 rounded bg-emerald-700 text-white text-[10px] font-mono">Stream 2: CSS Delivered (18ms)</span>
                  <span class="px-2 py-0.5 rounded bg-emerald-700 text-white text-[10px] font-mono">Stream 3: JS Delivered (22ms)</span>
                  <span class="px-2 py-0.5 rounded bg-amber-900 text-amber-200 text-[10px] font-mono">Stream 1: DB Pending</span>
                </div>
              `;
            }

            setTimeout(() => {
              document.getElementById('badge-res-2').textContent = '200 OK (18ms)';
              document.getElementById('badge-res-2').className = 'text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-300';
              document.getElementById('badge-res-3').textContent = '200 OK (22ms)';
              document.getElementById('badge-res-3').className = 'text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-300';

              document.getElementById('render-status').textContent = 'RENDERED (FCP: 18ms)';
              document.getElementById('render-status').className = 'text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-emerald-950 text-emerald-300';
              document.getElementById('render-display').innerHTML = '<span class="text-emerald-400 font-bold">✨ Instant FCP! CSS & JS rendered in 18ms. No transport or application HoL blocking.</span>';
              document.getElementById('h-tel-fcp').textContent = '18 ms';
              document.getElementById('h-tel-hol').textContent = 'NONE (Fully Isolated)';
              document.getElementById('h-tel-hol').className = 'text-sm font-bold font-mono text-emerald-400';

              setTimeout(() => {
                document.getElementById('badge-res-1').textContent = '200 OK (410ms)';
                document.getElementById('badge-res-1').className = 'text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-300';
                httpRunning = false;
              }, 400);
            }, 350);
          }
        }
    """

    return {
        "PAGE_TITLE": "Topic — HTTP/1.1 vs HTTP/2 vs HTTP/3",
        "THEME_CSS_VARS": theme["css_vars"],
        "THEME_NAME": theme["name"],
        "THEME_ID": theme["id"],
        "TIER_BADGE": tier or "Tier 0 · System Design Core",
        "CLUSTER_BADGE": cluster or "1. [0.1] APIs & Network Transport for Design",
        "LESSON_TITLE": "HTTP/1.1 vs HTTP/2 vs HTTP/3",
        "LESSON_SUBTITLE": "Where Head-of-Line blocking lives at each layer of the network stack, and why QUIC moved to UDP.",

        # PHASE 1: The Evolution of Web Concurrency & The HoL Dilemma
        "SECTION_1_TITLE": "The Concurrency Crisis: Why Web Performance Shifted Layers",
        "SECTION_1_BODY": """
        <p>
          In 1996, the World Wide Web loaded simple documents: a single HTML page referencing two or three small icons. By 2015, the median web application demanded over <strong>100 discrete network resources</strong> (CSS bundles, JavaScript chunks, fonts, high-res images, analytics beacons).
        </p>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-3 my-4">
          <div class="p-3.5 rounded-xl bg-[var(--card)] border border-[var(--card-border)]">
            <div class="text-[11px] font-mono font-bold text-amber-400 uppercase">HTTP/1.0: 1 Conn Per Req</div>
            <div class="text-base font-bold text-[var(--foreground)] mt-1">100 RTT Penalty</div>
            <p class="text-xs text-[var(--muted-foreground)] mt-1 mb-0 leading-relaxed">
              Every resource required its own TCP 3-way handshake + Slow Start. Loading 100 assets on a 50ms RTT trans-Atlantic link cost 5+ seconds in pure transport negotiation.
            </p>
          </div>
          <div class="p-3.5 rounded-xl bg-[var(--card)] border border-[var(--card-border)]">
            <div class="text-[11px] font-mono font-bold text-blue-400 uppercase">HTTP/1.1: Keep-Alive & Sharding</div>
            <div class="text-base font-bold text-[var(--foreground)] mt-1">Application HoL Stall</div>
            <p class="text-xs text-[var(--muted-foreground)] mt-1 mb-0 leading-relaxed">
              Connections persisted across requests, but responses were strictly FIFO. Browsers resorted to opening 6 parallel TCP connections per host (domain sharding) to bypass application queues.
            </p>
          </div>
          <div class="p-3.5 rounded-xl bg-[var(--card)] border border-[var(--card-border)]">
            <div class="text-[11px] font-mono font-bold text-rose-400 uppercase">HTTP/2: Binary Multiplexing</div>
            <div class="text-base font-bold text-[var(--foreground)] mt-1">Transport HoL Trap</div>
            <p class="text-xs text-[var(--muted-foreground)] mt-1 mb-0 leading-relaxed">
              Multiplexed 100 streams as binary frames over 1 TCP connection. But if 1 packet dropped on a cellular network, TCP held ALL 100 streams in the kernel receive queue.
            </p>
          </div>
        </div>

        <div class="callout-box callout-dilemma">
          <div class="text-xs font-mono font-bold text-rose-400 uppercase tracking-wider mb-1">⚡ The Core Architectural Dilemma</div>
          <p class="text-sm text-[var(--foreground)] m-0">
            <strong>Head-of-Line (HoL) Blocking is not a single bug; it is an architectural leak that migrates down the network stack.</strong>
            HTTP/1.1 suffered from HoL blocking at the <em>Application Layer</em> (HTTP message ordering).
            HTTP/2 solved application ordering by interleaving binary frames, but in doing so, concentrated all streams into a single TCP connection—pushing HoL blocking down into the <em>Transport Layer</em> (TCP byte-stream reassembly).
            HTTP/3 is the radical admission that TCP cannot solve this problem: it abandons TCP entirely and rebuilds stream-aware transport over UDP.
          </p>
        </div>
        """,

        # PHASE 2: Where HoL Blocking Lives at Each Layer
        "SECTION_2_TITLE": "Anatomy of Head-of-Line Blocking: Layer by Layer",
        "SECTION_2_BODY": """
        <p>
          To diagnose production network performance, an architect must pinpoint the exact physical boundary where packets stall:
        </p>

        <div class="space-y-4 my-4">
          <div class="p-4 rounded-xl bg-[var(--card)] border border-[var(--card-border)] space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-xs font-mono font-bold text-amber-400 uppercase">1. HTTP/1.1: Application-Layer HoL Blocking</span>
              <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-950 text-amber-300">Location: HTTP Message Queue</span>
            </div>
            <p class="text-xs text-[var(--muted-foreground)] leading-relaxed m-0">
              HTTP/1.1 introduced pipelining: a client can dispatch Request A and Request B without waiting. However, the server <strong>must return Response A before Response B</strong> because HTTP/1.1 has no request ID in headers. If Request A is a slow database query taking 500ms, and Request B is a 5ms static CSS file, the CSS file sits fully generated on the server, completely blocked behind A.
            </p>
          </div>

          <div class="p-4 rounded-xl bg-[var(--card)] border border-[var(--card-border)] space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-xs font-mono font-bold text-rose-400 uppercase">2. HTTP/2: Transport-Layer (TCP) HoL Blocking</span>
              <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-rose-950 text-rose-300">Location: Kernel TCP Receive Buffer</span>
            </div>
            <p class="text-xs text-[var(--muted-foreground)] leading-relaxed m-0">
              HTTP/2 breaks requests into binary frames tagged with a <code>Stream ID</code>. Frames can be interleaved in any order over a single TCP connection.
              <strong>The catch:</strong> The underlying TCP layer knows nothing about Stream IDs; it only knows a contiguous sequence of byte offsets. If a single IP packet carrying bytes for Stream #1 drops on a cellular tower, the receiver kernel holds all subsequent arrived frames for Stream #2 and Stream #3 in the socket buffer until the missing packet is retransmitted. One dropped packet stalls the entire connection!
            </p>
          </div>

          <div class="p-4 rounded-xl bg-[var(--card)] border border-[var(--card-border)] space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-xs font-mono font-bold text-emerald-400 uppercase">3. HTTP/3 (QUIC): Zero Transport HoL Blocking</span>
              <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-300">Location: Fully Isolated UDP Streams</span>
            </div>
            <p class="text-xs text-[var(--muted-foreground)] leading-relaxed m-0">
              QUIC replaces TCP with UDP. Because UDP is stateless, QUIC implements stream multiplexing, loss recovery, and TLS 1.3 encryption directly in user space. Each stream has independent packet sequencing. If Packet for Stream #1 is dropped, <strong>only Stream #1 stalls</strong>. Streams #2 and #3 deliver their datagrams to the browser engine immediately with 0ms delay.
            </p>
          </div>
        </div>
        """,

        # PHASE 3: Internal Mechanics & The Tactile Simulator
        "SECTION_3_TITLE": "Under the Hood: Why QUIC Moved to UDP and Fused TLS 1.3",
        "SECTION_3_BODY": """
        <p>
          Why did the IETF invent a completely new protocol on top of UDP rather than modifying TCP? Because of <strong>middlebox ossification</strong>: firewalls, NAT routers, and load balancers across the global internet drop any TCP packet with unrecognized flags or new options. UDP allowed deployment without upgrading every router on earth.
        </p>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 my-4">
          <div class="p-4 rounded-xl bg-[var(--card)] border border-[var(--card-border)] space-y-1.5">
            <div class="text-xs font-mono font-bold text-cyan-400">Fused 0-RTT / 1-RTT Handshake</div>
            <p class="text-xs text-[var(--muted-foreground)] m-0 leading-relaxed">
              In HTTP/2 over TCP+TLS 1.3: 1 RTT for TCP SYN/ACK + 1 RTT for TLS ClientHello/ServerHello = 2 RTTs before application data.
              In QUIC: The cryptographic handshake and transport connection are fused into a single exchange (1 RTT for new sessions, <strong>0-RTT</strong> for resumed sessions via TLS session tickets).
            </p>
          </div>
          <div class="p-4 rounded-xl bg-[var(--card)] border border-[var(--card-border)] space-y-1.5">
            <div class="text-xs font-mono font-bold text-purple-400">Connection Migration (Mobile 5G &larr;&rarr; Wi-Fi)</div>
            <p class="text-xs text-[var(--muted-foreground)] m-0 leading-relaxed">
              TCP identifies connections by a 4-tuple: <code>(Src IP, Src Port, Dst IP, Dst Port)</code>. When a phone leaves Wi-Fi and switches to cellular, its IP changes, breaking the TCP socket completely (broken download, video buffer reset).
              QUIC uses a random 64-bit <strong>Connection ID (CID)</strong>. The IP can change freely while the session continues seamlessly.
            </p>
          </div>
        </div>
        """ + sim_html + """
        <div class="callout-box callout-invariant">
          <div class="text-xs font-mono font-bold text-emerald-400 uppercase tracking-wider mb-1">⚖️ The Mechanical Invariant</div>
          <p class="text-sm text-[var(--foreground)] m-0">
            <strong>Multiplexing over a single reliable stream guarantees Transport HoL Blocking under packet loss.</strong>
            True multi-stream independence requires either multiple transport connections (HTTP/1.1 sharding) or moving stream sequencing into a packet-independent protocol (QUIC over UDP).
          </p>
        </div>
        """,

        # PHASE 4: Mental Model Synthesis & Production Grounding
        "SECTION_4_TITLE": "Mental Model Synthesis, Production Grounding & Sizing Reality",
        "SECTION_4_BODY": """
        <p>
          Modern web systems operate on a hybrid network tier. Here is how top engineering organizations ground HTTP version selection in production reality:
        </p>

        <table class="tradeoff-table my-4">
          <thead>
            <tr>
              <th>Protocol Dimension</th>
              <th>HTTP/1.1</th>
              <th>HTTP/2</th>
              <th>HTTP/3 (QUIC)</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td class="font-semibold">Transport Protocol</td>
              <td class="font-mono text-stone-300">TCP</td>
              <td class="font-mono text-blue-400">TCP</td>
              <td class="font-mono text-emerald-400">UDP</td>
            </tr>
            <tr>
              <td class="font-semibold">Multiplexing Mechanism</td>
              <td class="font-mono text-rose-400">None (Domain Sharding: 6 TCP sockets)</td>
              <td class="font-mono text-cyan-400">Binary Framing (1 TCP socket)</td>
              <td class="font-mono text-emerald-400">Independent Streams (1 UDP session)</td>
            </tr>
            <tr>
              <td class="font-semibold">HoL Blocking Location</td>
              <td class="font-mono text-rose-400">Application Layer (FIFO queue)</td>
              <td class="font-mono text-rose-400">Transport Layer (TCP receive queue)</td>
              <td class="font-mono text-emerald-400">None (Fully Isolated Streams)</td>
            </tr>
            <tr>
              <td class="font-semibold">Connection Establishment</td>
              <td class="font-mono text-stone-400">2–3 RTTs (TCP + TLS)</td>
              <td class="font-mono text-cyan-400">1–2 RTTs (TCP + TLS 1.3)</td>
              <td class="font-mono text-emerald-400">0–1 RTT (Fused QUIC + TLS 1.3)</td>
            </tr>
            <tr>
              <td class="font-semibold">Mobile IP Roaming</td>
              <td class="font-mono text-rose-400">Connection drops & reconnects</td>
              <td class="font-mono text-rose-400">Connection drops & reconnects</td>
              <td class="font-mono text-emerald-400">Seamless Migration (via 64-bit CID)</td>
            </tr>
            <tr>
              <td class="font-semibold">Server CPU Cost</td>
              <td class="font-mono text-emerald-400">Low (Kernel offload)</td>
              <td class="font-mono text-emerald-400">Low to Moderate</td>
              <td class="font-mono text-amber-400">2–3× Higher (User-space crypto & UDP)</td>
            </tr>
          </tbody>
        </table>

        <div class="callout-box callout-trap">
          <div class="text-xs font-mono font-bold text-amber-400 uppercase tracking-wider mb-1">⚠️ The Production Gotcha: UDP Blocking & Alt-Svc Fallback</div>
          <p class="text-sm text-[var(--foreground)] m-0">
            Many corporate firewalls, hotel Wi-Fi networks, and enterprise proxies strictly drop UDP traffic on port 443, assuming UDP is only for DNS or torrenting.
            Because of this, <strong>browsers NEVER connect with HTTP/3 on the initial request</strong>. Browsers connect via HTTP/2 over TCP first; the server advertises HTTP/3 capability via an HTTP header: <code>Alt-Svc: h3=":443"; ma=86400</code>. Only on subsequent requests does the browser attempt QUIC over UDP, gracefully falling back to HTTP/2 if UDP is blocked.
          </p>
        </div>
        """,

        # PHASE 5: Contextual Sign-Off Verification Gate
        "SECTION_5_TITLE": "Contextual Sign-Off Verification: Active Defense Gate",
        "SECTION_5_BODY": """
        <div class="callout-box callout-trap">
          <div class="flex items-start gap-3">
            <div class="text-amber-400 font-bold text-lg mt-0.5">⚠️</div>
            <div class="space-y-2">
              <h4 class="font-bold text-[var(--foreground)] text-base m-0">Production Incident: The Commuter Train Streaming Drop Mystery</h4>
              <p class="text-sm text-[var(--muted-foreground)] leading-relaxed">
                A video-on-demand streaming service deployed HTTP/2 multiplexing across their global CDN edge servers. Analytics reveal that users on suburban commuter trains experience frequent 2–4 second video buffering freezes, even though cell towers report solid 5G coverage with 40 Mbps bandwidth.
              </p>
              <p class="text-sm text-[var(--muted-foreground)] leading-relaxed">
                A junior engineer submits a pull request increasing the HTTP/2 maximum concurrent streams setting (<code>SETTINGS_MAX_CONCURRENT_STREAMS</code>) from 100 to 500, arguing: <em>"Higher concurrency will allow audio, video chunks, and subtitles to stream faster simultaneously."</em>
              </p>
              <div class="p-3 rounded-lg bg-[var(--background)] border border-[var(--border)] space-y-1">
                <div class="text-xs font-mono font-bold text-rose-400 uppercase">Your Defense Challenge:</div>
                <ul class="text-xs text-[var(--foreground)] space-y-1 m-0 pl-4 list-disc">
                  <li>Why will increasing the concurrent stream limit completely fail to resolve the commuter train buffering spikes?</li>
                  <li>Where in the network stack is the bottleneck occurring when the train transitions between cellular towers, and how does HTTP/2 multiplexing exacerbate the failure?</li>
                  <li>Why does migrating to HTTP/3 (QUIC) resolve the issue, and what two specific QUIC mechanisms eliminate the buffering?</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        <div class="p-4 rounded-xl bg-[var(--background)] border border-[var(--border)] space-y-2 text-xs text-[var(--muted-foreground)]">
          <div class="font-bold text-[var(--primary)] flex items-center gap-2">
            <span>🎯 Sign-Off Gate Defense Standard:</span>
          </div>
          <p class="leading-relaxed m-0">
            Tick off when: you can explain this out loud, unprompted, in your own words, including why Head-of-Line blocking exists at each layer, what it costs in user experience, and why QUIC moved to UDP.
          </p>
          <div class="pt-2 text-[11px] font-mono text-amber-400 flex items-center gap-2">
            <span class="inline-block w-2 h-2 rounded-full bg-amber-400"></span>
            <span>No solution is provided in this artifact. Discuss and defend your architectural breakdown in chat using <code>/sds-discuss</code>.</span>
          </div>
        </div>
        """,

        "BACKWARD_ANCHOR": "TCP vs UDP: Sliding Window, Flow Control, and Transport HoL Blocking",
        "FORWARD_HOOK": "TLS Handshake Cost & Session Resumption (0-RTT & Session Tickets)",
        "EMBEDDED_JAVASCRIPT": sim_js
    }

def generate_default_data(topic_id, title=None, cluster=None, tier=None, style_id="slate-clean"):
    clean_title = format_topic_title(topic_id, title)
    theme = STYLE_THEMES.get(style_id, STYLE_THEMES["slate-clean"])
    if "tcp-vs-udp" in topic_id.lower() or clean_title.lower() == "tcp vs udp":
        return build_tcp_vs_udp_data(theme, tier, cluster)
    if "http-1-1" in topic_id.lower() or "http/1.1" in clean_title.lower() or "http/2" in clean_title.lower():
        return build_http_versions_data(theme, tier, cluster)


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
