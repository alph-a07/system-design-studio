#!/usr/bin/env python3
"""
render-lesson.py
Deterministic HTML lesson renderer for System Design Studio.
Generates beautiful, accessible, interactive HTML lesson artifacts with embedded
simulators, workload contrasts, invariant tables, and reality checks.
"""

import os
import sys
import json
import argparse
import re

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
          <tbody class="divide-y divide-[var(--border)] text-xs md:text-sm">{{TABLE_ROWS}}</tbody>
        </table>
      </div>
    </section>

    <!-- SECTION 4: ENGINEERING REALITY CHECK -->
    <section class="space-y-6 border-t border-[var(--border)] pt-8">
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 rounded-lg bg-rose-500/10 text-rose-500 flex items-center justify-center font-bold text-sm">04</div>
        <h2 class="text-xl md:text-2xl font-bold tracking-tight">Engineering Reality Check: Active Verification</h2>
      </div>
      <div class="p-6 rounded-2xl bg-[var(--card)] border border-[var(--card-border)] space-y-4">
        <div class="flex items-start gap-3">
          <div class="text-rose-500 font-bold text-lg mt-0.5">⚠️</div>
          <div class="space-y-2">
            <h3 class="font-bold text-[var(--foreground)] text-base">The Scenario Challenge</h3>
            <p class="text-sm text-[var(--muted-foreground)] leading-relaxed">{{REALITY_CHECK_SCENARIO}}</p>
          </div>
        </div>
        <div class="pt-4 border-t border-[var(--border)]">
          <button id="toggle-solution-btn" onclick="toggleSolution()" class="px-4 py-2 text-xs font-semibold rounded-lg bg-[var(--primary)] text-white hover:opacity-90 transition">
            Reveal Architectural Breakdown & Trade-off
          </button>
          <div id="solution-box" class="hidden mt-4 p-4 rounded-xl bg-[var(--background)] border border-[var(--border)] text-sm space-y-3">
            {{REALITY_CHECK_SOLUTION}}
          </div>
        </div>
      </div>
    </section>

    <!-- FOOTER -->
    <footer class="border-t border-[var(--border)] pt-8 pb-12 flex flex-col md:flex-row items-center justify-between text-xs text-[var(--muted-foreground)] gap-4">
      <div>Part of the <span class="font-semibold text-[var(--foreground)]">System Design Studio</span> · Project Learning Instance</div>
      <div class="flex items-center gap-4">
        <span>Backward Anchor: <strong class="text-[var(--foreground)]">{{BACKWARD_ANCHOR}}</strong></span>
        <span>•</span>
        <span>Next Hook: <strong class="text-[var(--foreground)]">{{FORWARD_HOOK}}</strong></span>
      </div>
    </footer>
  </div>

  <script>
    function toggleSolution() {
      const box = document.getElementById('solution-box');
      const btn = document.getElementById('toggle-solution-btn');
      if (box.classList.contains('hidden')) {
        box.classList.remove('hidden');
        btn.textContent = 'Hide Architectural Breakdown';
      } else {
        box.classList.add('hidden');
        btn.textContent = 'Reveal Architectural Breakdown & Trade-off';
      }
    }
    {{EMBEDDED_JAVASCRIPT}}
  </script>
</body>
</html>
"""

def generate_default_data(topic_id, title=None, cluster_title=None, tier=None):
    slug = topic_id.replace("topic.", "").replace(".", "-")
    clean_title = title or topic_id.replace("topic.", "").replace(".", " ").title()
    return {
        "PAGE_TITLE": f"Topic — {clean_title}",
        "TIER_BADGE": tier or "Tier 0 · System Design Core",
        "CLUSTER_BADGE": cluster_title or "Foundation Mechanism",
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
        "SECTION_2_BODY": f"<p>Let's trace how <strong>{clean_title}</strong> preserves state invariants across distributed boundaries when messages are delayed or dropped.</p>",
        "SIMULATOR_TITLE": f"Interactive State Simulator: {clean_title}",
        "SIMULATOR_SUBTITLE": "Step through event lifecycles and observe state mutations under injected faults.",
        "SIMULATOR_CONTROLS": """
        <button onclick="simStep()" class="px-3 py-1.5 text-xs font-semibold rounded-lg bg-[var(--primary)] text-white hover:opacity-90 transition">Step Forward</button>
        <button onclick="simReset()" class="px-3 py-1.5 text-xs font-semibold rounded-lg bg-[var(--card)] border border-[var(--border)] text-[var(--foreground)] hover:bg-[var(--border)] transition">Reset</button>
        """,
        "SIMULATOR_CANVAS": """
        <div class="p-8 rounded-xl bg-[var(--background)] border border-[var(--border)] flex items-center justify-around text-center" id="sim-canvas">
          <div class="p-4 rounded-lg bg-[var(--card)] border border-[var(--border)] w-36">
            <div class="text-xs font-bold text-[var(--primary)]">Sender / Client</div>
            <div id="sim-sender-state" class="text-xs font-mono mt-1 text-[var(--muted-foreground)]">STATE: IDLE</div>
          </div>
          <div class="flex-1 px-4 relative flex items-center justify-center">
            <div class="w-full h-1 bg-[var(--border)] rounded"></div>
            <div id="sim-transit-chip" class="absolute px-2.5 py-1 text-xs rounded-full bg-emerald-500 text-white font-mono scale-0 transition-transform">PAYLOAD</div>
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
        "REALITY_CHECK_SCENARIO": f"A developer observes that under 99th percentile load, requests in {clean_title} experience a 10x tail-latency spike, even though CPU and RAM utilization are under 40%. Where is the queue hiding, and how would you verify it?",
        "REALITY_CHECK_SOLUTION": """
        <p class="font-bold text-emerald-500">Solution & Root-Cause Trace:</p>
        <p class="text-xs text-[var(--muted-foreground)] leading-relaxed">
          The queue is sitting in kernel socket buffers (TCP receive window exhaustion) or connection pool thread starvation. When downstream services stall, the sender buffer fills, triggering TCP zero-window probes or connection pool wait-time inflation. Verify using <code>ss -ti</code> or thread pool saturation metrics.
        </p>
        """,
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

def main():
    parser = argparse.ArgumentParser(description="Render interactive HTML lesson artifact")
    parser.add_argument("--topic-id", required=True, help="Topic ID (e.g. topic.0.1.tcp-vs-udp)")
    parser.add_argument("--title", help="Lesson Title")
    parser.add_argument("--cluster", help="Cluster Title")
    parser.add_argument("--tier", help="Tier Title")
    parser.add_argument("--spec", help="Path to JSON file with lesson override tokens")
    parser.add_argument("--template", help="Path to custom HTML template")
    parser.add_argument("--output-dir", default=".system-design/lessons", help="Output directory")
    parser.add_argument("--brain-dir", help="App data artifact directory (<appDataDir>/brain/<id>)")

    args = parser.parse_args()
    data = generate_default_data(args.topic_id, args.title, args.cluster, args.tier)

    if args.spec and os.path.exists(args.spec):
        with open(args.spec) as f:
            spec_data = json.load(f)
            data.update(spec_data)

    template_str = DEFAULT_TEMPLATE
    if args.template and os.path.exists(args.template):
        with open(args.template) as f:
            template_str = f.read()

    rendered = template_str
    for k, v in data.items():
        rendered = rendered.replace(f"{{{{{k}}}}}", str(v))

    slug = args.topic_id.replace("topic.", "").replace(".", "-")
    filename = f"{slug}.html"

    os.makedirs(args.output_dir, exist_ok=True)
    out_path = os.path.join(args.output_dir, filename)
    with open(out_path, "w") as f:
        f.write(rendered)

    print(f"✅ Lesson rendered to {out_path}")

    if args.brain_dir and os.path.exists(args.brain_dir):
        brain_path = os.path.join(args.brain_dir, filename)
        with open(brain_path, "w") as f:
            f.write(rendered)
        print(f"✅ Staged to conversation artifact dir: {brain_path}")

if __name__ == "__main__":
    main()
