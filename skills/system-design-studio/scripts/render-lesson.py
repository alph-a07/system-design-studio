#!/usr/bin/env python3
"""
render-lesson.py
Deterministic HTML lesson renderer for System Design Studio.
Generates beautiful, accessible, interactive HTML lesson artifacts with embedded
simulators, workload contrasts, invariant tables, and reality checks.
Supports 5 distinct visual theme variants and respects .system-design/settings.json
for both theme preferences and directory output paths (paths.lessonsDir).
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

DEFAULT_TEMPLATE = """<!DOCTYPE html>
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
    .animate-pulse-subtle { animation: pulse-subtle 2s infinite ease-in-out; }
    .interactive-element { transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1); }
    {{THEME_CSS_VARS}}
  </style>
</head>
<body class="bg-[var(--background)] text-[var(--foreground)] font-sans antialiased selection:bg-[var(--primary)] selection:text-white p-4 md:p-8">
  <div class="max-w-4xl mx-auto space-y-12">
    <!-- HERO HEADER -->
    <header class="border-b border-[var(--border)] pb-8 space-y-4">
      <div class="flex flex-wrap items-center gap-2">
        <span class="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-[var(--primary)] text-white tracking-wide uppercase">{{TIER_BADGE}}</span>
        <span class="px-2.5 py-0.5 text-xs font-medium rounded-full bg-[var(--card)] border border-[var(--card-border)] text-[var(--muted-foreground)]">{{CLUSTER_BADGE}}</span>
        <span class="px-2.5 py-0.5 text-xs font-mono rounded-full bg-[var(--card)] border border-[var(--card-border)] text-[var(--muted-foreground)]">[concept] [mechanics] [contrast] [trap]</span>
        <span class="px-2.5 py-0.5 text-xs font-mono rounded-full bg-[var(--card)] border border-[var(--card-border)] text-[var(--primary)] font-semibold">🎨 {{THEME_NAME}}</span>
      </div>
      <h1 class="text-3xl md:text-4xl font-extrabold tracking-tight text-[var(--foreground)]">{{LESSON_TITLE}}</h1>
      <p class="text-base md:text-lg text-[var(--muted-foreground)] leading-relaxed max-w-3xl">{{LESSON_SUBTITLE}}</p>
    </header>

    <!-- SECTION 1: PHYSICAL MOTIVATION -->
    <section class="space-y-6">
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 rounded-lg bg-blue-500/10 text-blue-500 flex items-center justify-center font-bold text-sm">01</div>
        <h2 class="text-xl md:text-2xl font-bold tracking-tight">{{SECTION_1_TITLE}}</h2>
      </div>
      <div class="prose text-[var(--foreground)] leading-relaxed space-y-4 text-sm md:text-base">{{SECTION_1_BODY}}</div>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">{{METRIC_CARDS}}</div>
    </section>

    <!-- SECTION 2: MECHANISTIC CORE & SIMULATOR -->
    <section class="space-y-6">
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-500 flex items-center justify-center font-bold text-sm">02</div>
        <h2 class="text-xl md:text-2xl font-bold tracking-tight">{{SECTION_2_TITLE}}</h2>
      </div>
      <div class="prose text-[var(--foreground)] leading-relaxed space-y-4 text-sm md:text-base">{{SECTION_2_BODY}}</div>
      <div class="rounded-2xl bg-[var(--card)] border border-[var(--card-border)] p-6 shadow-sm space-y-6">
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-[var(--border)]">
          <div>
            <h3 class="text-lg font-bold text-[var(--foreground)] flex items-center gap-2">
              <span class="inline-block w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
              {{SIMULATOR_TITLE}}
            </h3>
            <p class="text-xs text-[var(--muted-foreground)]">{{SIMULATOR_SUBTITLE}}</p>
          </div>
          <div class="flex items-center gap-2" id="sim-controls">{{SIMULATOR_CONTROLS}}</div>
        </div>
        {{SIMULATOR_CANVAS}}
        <div class="p-4 rounded-xl bg-[var(--background)] border border-[var(--border)] text-xs text-[var(--muted-foreground)] space-y-1" id="sim-log-panel">
          {{SIMULATOR_LOG_PANEL}}
        </div>
      </div>
    </section>

    <!-- SECTION 3: WORKLOAD COMPARISON & INVARIANTS -->
    <section class="space-y-6">
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 rounded-lg bg-purple-500/10 text-purple-500 flex items-center justify-center font-bold text-sm">03</div>
        <h2 class="text-xl md:text-2xl font-bold tracking-tight">Workload Comparison: The Architectural Invariant</h2>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">{{WORKLOAD_CARDS}}</div>
      <div class="rounded-xl border border-[var(--card-border)] overflow-hidden">
        <table class="w-full text-left text-sm">
          <thead class="bg-[var(--card)] border-b border-[var(--card-border)] text-xs font-mono uppercase text-[var(--muted-foreground)]">
            <tr>
              <th class="p-4">Dimension</th>
              <th class="p-4">{{TABLE_COL_1_HEADER}}</th>
              <th class="p-4">{{TABLE_COL_2_HEADER}}</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-[var(--border)] text-xs md:text-sm">
            {{TABLE_ROWS}}
          </tbody>
        </table>
      </div>
    </section>

    <!-- SECTION 4: FINAL SIGN-OFF CHALLENGE (UNASSISTED VERIFICATION) -->
    <section class="space-y-6 border-t border-[var(--border)] pt-8">
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 rounded-lg bg-rose-500/10 text-rose-500 flex items-center justify-center font-bold text-sm border border-rose-500/20">04</div>
        <h2 class="text-xl md:text-2xl font-bold tracking-tight">Final Sign-Off Challenge: Active Verification</h2>
      </div>
      <div class="p-6 rounded-2xl bg-[var(--card)] border border-[var(--card-border)] space-y-4">
        <div class="flex items-start gap-3">
          <div class="text-rose-500 font-bold text-lg mt-0.5">⚠️</div>
          <div class="space-y-2">
            <h3 class="font-bold text-[var(--foreground)] text-base">The Scenario Challenge</h3>
            <p class="text-sm text-[var(--muted-foreground)] leading-relaxed">{{SIGN_OFF_SCENARIO}}</p>
          </div>
        </div>
        <div class="p-4 rounded-xl bg-[var(--background)] border border-[var(--border)] space-y-2 text-xs text-[var(--muted-foreground)]">
          <div class="font-bold text-[var(--primary)] flex items-center gap-2">
            <span>🎯 Sign-Off Gate Criteria:</span>
          </div>
          <p class="leading-relaxed">
            {{SIGN_OFF_CRITERIA}}
          </p>
          <div class="pt-2 text-[11px] font-mono text-[var(--muted-foreground)] flex items-center gap-2">
            <span class="inline-block w-2 h-2 rounded-full bg-amber-400"></span>
            <span>No solution is provided in this artifact. Analyze and defend your breakdown in chat to complete topic sign-off.</span>
          </div>
        </div>
      </div>
    </section>

    <!-- FOOTER NAV -->
    <footer class="border-t border-[var(--border)] pt-8 pb-12 flex flex-col md:flex-row items-center justify-between text-xs text-[var(--muted-foreground)] gap-4">
      <div>
        Part of the <span class="font-semibold text-[var(--foreground)]">System Design Studio</span> · Project Learning Instance
      </div>
      <div class="flex items-center gap-4">
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

def generate_default_data(topic_id, title=None, cluster=None, tier=None, style_id="slate-clean"):
    clean_title = title or topic_id.replace("topic.", "").replace("-", " ").title()
    theme = STYLE_THEMES.get(style_id, STYLE_THEMES["slate-clean"])

    return {
        "PAGE_TITLE": f"Topic — {clean_title}",
        "THEME_CSS_VARS": theme["css_vars"],
        "THEME_NAME": theme["name"],
        "THEME_ID": theme["id"],
        "TIER_BADGE": tier or "Tier 0 · System Design Core",
        "CLUSTER_BADGE": cluster or "Foundation Mechanism",
        "LESSON_TITLE": clean_title,
        "LESSON_SUBTITLE": "A first-principles, causal breakdown of physical constraints, failure modes, and architectural trade-offs.",
        "SECTION_1_TITLE": "Physical Motivation & The Speed of Light",
        "SECTION_1_BODY": f"<p>Every distributed system begins with the laws of physics. When designing <strong>{clean_title}</strong>, we face non-negotiable hardware limits: speed of light through medium, disk I/O seek times, and network queue bufferbloat.</p>",
        "METRIC_CARDS": """
        <div class="p-4 rounded-xl bg-[var(--card)] border border-[var(--card-border)] space-y-1">
          <div class="text-xs uppercase font-mono text-[var(--muted-foreground)]">Propagation Limit</div>
          <div class="text-2xl font-black text-[var(--primary)]">~5 μs / km</div>
          <div class="text-xs text-[var(--muted-foreground)]">Round-trip physical latency across networks is bounded by medium physics.</div>
        </div>
        <div class="p-4 rounded-xl bg-[var(--card)] border border-[var(--card-border)] space-y-1">
          <div class="text-xs uppercase font-mono text-[var(--muted-foreground)]">Queue Delay</div>
          <div class="text-2xl font-black text-amber-500">Bufferbloat</div>
          <div class="text-xs text-[var(--muted-foreground)]">Buffers smooth bursts but inject unpredictable multi-second tail latency under saturation.</div>
        </div>
        <div class="p-4 rounded-xl bg-[var(--card)] border border-[var(--card-border)] space-y-1">
          <div class="text-xs uppercase font-mono text-[var(--muted-foreground)]">The Core Trade-off</div>
          <div class="text-2xl font-black text-rose-500">Latency vs Safety</div>
          <div class="text-xs text-[var(--muted-foreground)]">Guaranteeing consistency requires communication; avoiding communication forfeits coordination.</div>
        </div>
        """,
        "SECTION_2_TITLE": "Mechanistic Core & Invariant Preservation",
        "SECTION_2_BODY": f"<p>How does the protocol guarantee its state invariants across independent failure domains? Below is the interactive execution trace for <strong>{clean_title}</strong>.</p>",
        "SIMULATOR_TITLE": f"Execution Simulator: {clean_title}",
        "SIMULATOR_SUBTITLE": "Step through state transitions, packet transmission, and failure recovery.",
        "SIMULATOR_CONTROLS": """
        <button onclick="simStep()" class="px-3 py-1.5 text-xs font-semibold rounded-lg bg-[var(--primary)] text-white hover:opacity-90 transition">Step Forward →</button>
        <button onclick="simReset()" class="px-3 py-1.5 text-xs font-semibold rounded-lg bg-[var(--background)] border border-[var(--border)] text-[var(--foreground)] hover:bg-[var(--card)] transition">Reset</button>
        """,
        "SIMULATOR_CANVAS": """
        <div class="flex items-center justify-between p-6 rounded-xl bg-[var(--background)] border border-[var(--border)] min-h-[160px]" id="sim-canvas">
          <div class="p-4 rounded-lg bg-[var(--card)] border border-[var(--border)] w-36">
            <div class="text-xs font-bold text-blue-500">Sender / Client</div>
            <div id="sim-sender-state" class="text-xs font-mono mt-1 text-[var(--muted-foreground)]">STATE: IDLE</div>
          </div>
          <div class="flex-1 flex flex-col items-center justify-center px-4">
            <div class="w-full h-1 bg-[var(--border)] relative flex items-center justify-center">
              <div id="transit-chip" class="w-4 h-4 rounded-full bg-[var(--primary)] transition-all duration-300 transform scale-0"></div>
            </div>
            <div class="text-[10px] font-mono mt-2 text-[var(--muted-foreground)]">TRANSIT MEDIUM (UNRELIABLE)</div>
          </div>
          <div class="p-4 rounded-lg bg-[var(--card)] border border-[var(--border)] w-36">
            <div class="text-xs font-bold text-emerald-500">Receiver / Node</div>
            <div id="sim-receiver-state" class="text-xs font-mono mt-1 text-[var(--muted-foreground)]">STATE: LISTENING</div>
          </div>
        </div>
        """,
        "SIMULATOR_LOG_PANEL": "<div id='sim-log'>Click 'Step Forward' to initiate the protocol sequence.</div>",
        "WORKLOAD_CARDS": f"""
        <div class="p-6 rounded-2xl bg-[var(--card)] border border-[var(--card-border)] space-y-3">
          <div class="text-xs font-bold font-mono text-[var(--primary)] uppercase tracking-wide">Workload Profile A: High Durability</div>
          <h3 class="text-base font-bold text-[var(--foreground)]">Financial Ledger & Audit Store</h3>
          <p class="text-xs text-[var(--muted-foreground)] leading-relaxed">
            Every transaction must be strictly linearizable and fsynced. Sacrifices raw throughput for zero-loss guarantees under node crash.
          </p>
        </div>
        <div class="p-6 rounded-2xl bg-[var(--card)] border border-[var(--card-border)] space-y-3">
          <div class="text-xs font-bold font-mono text-emerald-500 uppercase tracking-wide">Workload Profile B: High Throughput</div>
          <h3 class="text-base font-bold text-[var(--foreground)]">Telemetry Ingestion & Edge Metrics</h3>
          <p class="text-xs text-[var(--muted-foreground)] leading-relaxed">
            Sustains 500,000 writes/sec. Drops individual frames gracefully to preserve low-latency buffer queues.
          </p>
        </div>
        """,
        "TABLE_COL_1_HEADER": "Workload A (Durability)",
        "TABLE_COL_2_HEADER": "Workload B (Throughput)",
        "TABLE_ROWS": """
        <tr>
          <td class="p-4 font-medium text-[var(--foreground)]">Ordering Guarantee</td>
          <td class="p-4 text-emerald-500 font-mono">Strict Total Order</td>
          <td class="p-4 text-amber-500 font-mono">Partial / Best-Effort</td>
        </tr>
        <tr>
          <td class="p-4 font-medium text-[var(--foreground)]">Disk Write Strategy</td>
          <td class="p-4 text-[var(--muted-foreground)]">Synchronous WAL fsync</td>
          <td class="p-4 text-[var(--muted-foreground)]">Asynchronous batched flush</td>
        </tr>
        <tr>
          <td class="p-4 font-medium text-[var(--foreground)]">Crash Recovery Cost</td>
          <td class="p-4 text-[var(--muted-foreground)]">Replay uncommitted WAL entries</td>
          <td class="p-4 text-[var(--muted-foreground)]">Drop in-flight buffer window</td>
        </tr>
        """,
        "SIGN_OFF_SCENARIO": f"A developer observes that under 99th percentile load, requests in {clean_title} experience a 10x tail-latency spike, even though CPU and RAM utilization are under 40%. Where is the queue hiding, why did latency spike, and how would you verify it?",
        "SIGN_OFF_CRITERIA": f"Tick off when: you can explain this out loud or defend in chat without notes, isolating the queue location, the underlying causal mechanism, and the exact verification command.",
        "BACKWARD_ANCHOR": "Physical network constraints & hardware bounds",
        "FORWARD_HOOK": "Distributed consensus & fault recovery",
        "EMBEDDED_JAVASCRIPT": """
        let simState = 0;
        function simStep() {
          const chip = document.getElementById('transit-chip') || document.getElementById('sim-transit-chip');
          const sender = document.getElementById('sim-sender-state');
          const receiver = document.getElementById('sim-receiver-state');
          const log = document.getElementById('sim-log');
          if (simState === 0) {
            sender.textContent = "STATE: SENDING";
            chip.style.transform = "scale(1)";
            log.innerHTML = "<span class='text-blue-500 font-bold'>[SEND]</span> Dispatching message payload across network link...";
            simState = 1;
          } else if (simState === 1) {
            receiver.textContent = "STATE: PROCESSING";
            log.innerHTML = "<span class='text-emerald-500 font-bold'>[RECV]</span> Message received; verifying checksum and payload invariant.";
            simState = 2;
          } else {
            sender.textContent = "STATE: IDLE (ACK)";
            receiver.textContent = "STATE: LISTENING";
            chip.style.transform = "scale(0)";
            log.innerHTML = "<span class='text-purple-500 font-bold'>[ACK]</span> Acknowledgement complete. Ready for next cycle.";
            simState = 0;
          }
        }
        function simReset() {
          simState = 0;
          const chip = document.getElementById('transit-chip') || document.getElementById('sim-transit-chip');
          const sender = document.getElementById('sim-sender-state');
          const receiver = document.getElementById('sim-receiver-state');
          const log = document.getElementById('sim-log');
          if (chip) chip.style.transform = "scale(0)";
          if (sender) sender.textContent = "STATE: IDLE";
          if (receiver) receiver.textContent = "STATE: LISTENING";
          if (log) log.textContent = "Click 'Step Forward' to initiate the protocol sequence.";
        }
        """
    }

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

def main():
    parser = argparse.ArgumentParser(description="Render interactive HTML lesson artifact")
    parser.add_argument("--topic-id", required=True, help="Topic ID (e.g. topic.0.1.tcp-vs-udp)")
    parser.add_argument("--title", help="Lesson Title")
    parser.add_argument("--cluster", help="Cluster Title")
    parser.add_argument("--tier", help="Tier Title")
    parser.add_argument("--style", choices=list(STYLE_THEMES.keys()), help="Artifact visual style theme")
    parser.add_argument("--settings", help="Path to settings.json")
    parser.add_argument("--spec", help="Path to JSON file with lesson override tokens")
    parser.add_argument("--template", help="Path to custom HTML template")
    parser.add_argument("--output-dir", help="Output directory (defaults to lessonsDir in settings.json or .system-design/lessons)")
    parser.add_argument("--brain-dir", help="App data artifact directory (<appDataDir>/brain/<id>)")

    args = parser.parse_args()

    settings_data, loaded_settings_path = load_settings(args.settings)

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

    # Backwards compatibility fallback
    if "REALITY_CHECK_SCENARIO" in data and "SIGN_OFF_SCENARIO" not in data:
        data["SIGN_OFF_SCENARIO"] = data["REALITY_CHECK_SCENARIO"]
    if "SIGN_OFF_CRITERIA" not in data:
        data["SIGN_OFF_CRITERIA"] = "Tick off when: you can explain this out loud or defend in chat in your own words, including why it exists and what it costs."

    # Ensure theme variables are bound
    data["THEME_CSS_VARS"] = theme["css_vars"]
    data["THEME_NAME"] = theme["name"]
    data["THEME_ID"] = theme["id"]

    template_str = DEFAULT_TEMPLATE
    if args.template and os.path.exists(args.template):
        with open(args.template) as f:
            template_str = f.read()

    rendered = template_str
    for k, v in data.items():
        rendered = rendered.replace(f"{{{{{k}}}}}", str(v))

    slug = args.topic_id.replace("topic.", "").replace(".", "-")
    filename = f"{slug}.html"

    os.makedirs(target_output_dir, exist_ok=True)
    out_path = os.path.join(target_output_dir, filename)
    with open(out_path, "w") as f:
        f.write(rendered)

    print(f"✅ Lesson rendered to {out_path} [Style: {theme['name']}]")

    if args.brain_dir and os.path.exists(args.brain_dir):
        brain_path = os.path.join(args.brain_dir, filename)
        with open(brain_path, "w") as f:
            f.write(rendered)
        print(f"✅ Staged to conversation artifact dir: {brain_path}")

if __name__ == "__main__":
    main()
