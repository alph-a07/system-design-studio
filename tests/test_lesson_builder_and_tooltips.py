#!/usr/bin/env python3
"""
test_lesson_builder_and_tooltips.py — Verification suite for LessonBuilder,
inline jargon tooltips, and the --full-depth rendering mode.
"""

import os
import sys
import json
import unittest
import subprocess

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "skills", "system-design-studio", "scripts")
sys.path.insert(0, SCRIPTS_DIR)

from lesson_builder import (
    LessonBuilder,
    build_jargon_tooltip,
    build_editorial_lead,
    build_dilemma_callout,
    build_callout,
    build_analogy_card,
    build_aha_card,
    build_mental_model_box,
    build_defense_scenario
)
import importlib
rl = importlib.import_module("render-lesson")


class TestLessonBuilderAndTooltips(unittest.TestCase):

    def test_01_ui_node_generators(self):
        # 1. Jargon Tooltip
        tip = build_jargon_tooltip("fsync()", "fsync()", "POSIX System Call", "Forces OS dirty pages to disk.")
        self.assertIn('class="jargon-tooltip-wrapper"', tip)
        self.assertIn('class="jargon-inline-cue"', tip)
        self.assertIn('class="jargon-popover-card"', tip)
        self.assertIn("fsync()", tip)
        self.assertIn("POSIX System Call", tip)

        # Invariant: Tooltip must be 100% legal phrasing content (zero <div> or <p> tags) to prevent browser auto-closing enclosing <p> tags
        self.assertNotIn('<div', tip.lower(), "Tooltip popover must not contain <div> tags that break enclosing <p> flow")
        self.assertNotIn('<p', tip.lower(), "Tooltip popover must not contain <p> tags that break enclosing <p> flow")
        self.assertIn('<span class="jargon-popover-card">', tip)
        self.assertIn('<span class="jargon-popover-desc">', tip)

        # Pill cue variant
        tip_pill = build_jargon_tooltip("BDP", "BDP", "Metric", "Bandwidth × RTT", cue_type="pill")
        self.assertIn('class="jargon-pill-cue"', tip_pill)
        self.assertNotIn('<div', tip_pill.lower())

        # 2. Editorial Lead
        lead = build_editorial_lead("Physics dictates durability.")
        self.assertIn('class="editorial-lead"', lead)
        self.assertIn("Physics dictates durability.", lead)

        # 3. Dilemma Callout
        dilemma = build_dilemma_callout(
            "Durability Dilemma",
            "Impossible trade-off between speed and persistence:",
            "Extreme 1: Direct Sync Writes", "10 ms seek latency, 100 TPS cap", "Every write flushes disk",
            "Extreme 2: Pure DRAM Buffering", "0.01 ms latency, crash loses data"
        )
        self.assertIn('callout-dilemma', dilemma)
        self.assertIn("Durability Dilemma", dilemma)
        self.assertIn("Extreme 1: Direct Sync Writes", dilemma)

        # 4. Callout Variants
        trap = build_callout("trap", "Bufferbloat Pitfall", "Bloated intermediate buffers increase latency.")
        self.assertIn('callout-trap', trap)
        self.assertIn("Bufferbloat Pitfall", trap)

        # 5. Analogy Card
        analogy = build_analogy_card("Card Catalog", "Mental Model", "Like drawers in a library.")
        self.assertIn('class="analogy-card"', analogy)
        self.assertIn("Card Catalog", analogy)

        # 6. Mental Model Box
        mm = build_mental_model_box("TCP stretches time. UDP makes time the app's problem.", "Core rule.")
        self.assertIn("The Architectural Mental Model", mm)
        self.assertIn("TCP stretches time", mm)

    def test_02_lesson_builder_standard_and_fulldepth(self):
        # Construct standard builder
        builder = LessonBuilder(
            topic_id="topic.test.durability",
            lesson_title="Durability Under Pressure",
            lesson_subtitle="How write-ahead logs balance latency and persistence",
            tier_badge="Tier 0 · System Design Core",
            cluster_badge="Storage Engines"
        )

        tip1 = build_jargon_tooltip("fsync()", "fsync()", "Syscall", "Flushes disk.")
        tip2 = build_jargon_tooltip("WAL", "Write-Ahead Log", "Storage Pattern", "Append-only log.")
        tip3 = build_jargon_tooltip("Page Cache", "Page Cache", "Kernel Subsystem", "OS DRAM cache.")

        # Section 1
        builder.section(1).set_title("The Mechanical Dilemma") \
            .add_lead("Storage engines face an inescapable tradeoff.") \
            .add_paragraph(f"Applications invoke {tip1} to commit records.") \
            .add_dilemma(
                "Write Friction",
                "Two unacceptable choices:",
                "Extreme 1", "100 TPS", "Direct disk flushes",
                "Extreme 2", "Data loss on power cutoff"
            )

        # Section 2
        builder.section(2).set_title("Where Durability Sits") \
            .add_paragraph(f"The operating system buffers dirty pages in the {tip3}.") \
            .add_analogy("Ledger", "Accounting", "Like writing to a receipt book before updating accounts.")

        # Section 3
        builder.section(3).set_title("Internal Mechanics of the Log") \
            .add_paragraph(f"By writing sequentially to the {tip2}, disk head movement is eliminated.") \
            .add_paragraph("Sequential disk writes achieve 150 MB/s on HDDs and 3,000 MB/s on NVMe SSDs.")

        # Section 4
        builder.section(4).set_title("Production Grounding") \
            .add_mental_model("Sequential appends turn random I/O into amortized batch commits.", "Key invariant.")

        # Section 5
        builder.section(5).set_title("Architectural Defense") \
            .add_defense_scenario(
                "High-Throughput Ledger",
                ["A banking platform processes 50,000 transactions per second."],
                [("WAL Batching", "Defend group commits under fsync barriers.")]
            )

        payload = builder.to_dict()
        self.assertEqual(payload["LESSON_TITLE"], "Durability Under Pressure")
        self.assertEqual(payload["SECTION_1_TITLE"], "The Mechanical Dilemma")
        self.assertIn("callout-dilemma", payload["SECTION_1_BODY"])

        # Test validation
        is_valid, warnings, metrics = builder.validate()
        self.assertEqual(metrics["jargon_count"], 3)
        self.assertFalse(builder.full_depth)

        # Test full-depth switch
        builder.set_full_depth(True)
        self.assertTrue(builder.full_depth)

    def test_03_markdown_conversion_with_inline_tooltips(self):
        # Test that clean_html_to_markdown cleanly transforms inline tooltips (new all-span phrasing)
        sample_html = (
            '<div class="editorial-lead">Physics sets the latency floor.</div>\n'
            '<p>When an application executes <span class="jargon-tooltip-wrapper">'
            '<span class="jargon-inline-cue" onclick="toggleJargonTooltip(this, event)">fsync()</span>'
            '<span class="jargon-popover-card">'
            '<span class="jargon-popover-header">'
            '<span class="jargon-popover-title">💡 fsync()</span>'
            '<span class="jargon-popover-badge">POSIX Syscall</span>'
            '</span>'
            '<span class="jargon-popover-body"><span class="jargon-popover-desc">Forces page cache flush to non-volatile disk.</span></span>'
            '</span>'
            '</span>, the thread blocks.</p>'
        )

        md = rl.clean_html_to_markdown(sample_html)
        # Inline sentence must read cleanly as **fsync()** without mangled popover HTML
        self.assertIn("When an application executes **fsync()**, the thread blocks.", md)
        self.assertNotIn("jargon-popover-card", md)
        self.assertNotIn("onclick", md)

        # The term must be cleanly collected in the section glossary block
        self.assertIn("💡 **Jargon & Concepts Unpacked in this Section:**", md)
        self.assertIn("- **fsync()** *(POSIX Syscall)*: Forces page cache flush to non-volatile disk.", md)

        # Test backward-compatibility with legacy div-based popovers as well
        legacy_html = (
            '<p>A socket is bound to <span class="jargon-tooltip-wrapper">'
            '<span class="jargon-inline-cue" onclick="toggleJargonTooltip(this, event)">Socket Buffer</span>'
            '<div class="jargon-popover-card">'
            '<div class="jargon-popover-header"><span class="jargon-popover-title">💡 Socket Buffer</span><span class="jargon-popover-badge">OS Queue</span></div>'
            '<div class="jargon-popover-body"><p>Non-swappable queue.</p></div>'
            '</div></span> in kernel memory.</p>'
        )
        md_legacy = rl.clean_html_to_markdown(legacy_html)
        self.assertIn("A socket is bound to **Socket Buffer** in kernel memory.", md_legacy)
        self.assertNotIn("jargon-popover-card", md_legacy)

        # Test sanitize_tooltips_to_spans converts legacy div-based popovers into pure phrasing spans
        sanitized = rl.sanitize_tooltips_to_spans(legacy_html)
        self.assertNotIn("<div", sanitized.lower())
        self.assertNotIn("<p", sanitized[len("<p>"):sanitized.rfind("</p>")].lower())
        self.assertIn('<span class="jargon-popover-card">', sanitized)
        self.assertIn('<span class="jargon-popover-desc">', sanitized)

    def test_04_render_lesson_script_full_depth(self):
        # Test CLI invocation with --full-depth
        render_script = os.path.join(SCRIPTS_DIR, "render-lesson.py")
        fixture_path = os.path.join(REPO_ROOT, "tests", "fixtures", "0-1-tcp-vs-udp.json")
        out_dir = "/tmp/test-sds-fulldepth"
        os.makedirs(out_dir, exist_ok=True)

        res = subprocess.run([
            sys.executable, render_script,
            "--topic-id", "topic.0.1.tcp-vs-udp",
            "--data-file", fixture_path,
            "--output-dir", out_dir,
            "--full-depth"
        ], capture_output=True, text=True)

        self.assertEqual(res.returncode, 0, f"Error: {res.stderr}")
        self.assertIn("Depth & Anti-Compression (Full-Depth Mechanical Closure)", res.stdout)
        self.assertIn("Lesson rendered to", res.stdout)

        md_file = os.path.join(out_dir, "0-1-tcp-vs-udp.md")
        with open(md_file, "r", encoding="utf-8") as f:
            md_content = f.read()

        self.assertIn("Depth**: Full-Depth Mechanical Closure", md_content)


if __name__ == "__main__":
    unittest.main()
