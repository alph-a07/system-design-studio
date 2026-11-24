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
import shutil

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
        shutil.rmtree(out_dir, ignore_errors=True)
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

        html_file = os.path.join(out_dir, "0-1-tcp-vs-udp.html")
        self.assertTrue(os.path.isfile(html_file))
        with open(html_file, "r", encoding="utf-8") as f:
            html_content = f.read()

        self.assertIn("Full-Depth", html_content)
        # Verify markdown lesson output format is completely eliminated
        md_file = os.path.join(out_dir, "0-1-tcp-vs-udp.md")
        self.assertFalse(os.path.isfile(md_file), "Markdown lesson file should not be emitted")

    def test_05_markdown_leak_sanitization_and_popover_fixes(self):
        # 1. Test that leaking markdown bold asterisks around tooltips are cleaned
        raw_leaked_html = (
            '<p>2. ** <span class="jargon-tooltip-wrapper">'
            '<span class="jargon-inline-cue" onclick="toggleJargonTooltip(this, event)">Packet Loss Concealment (PLC)</span>'
            '<span class="jargon-popover-card">'
            '<span class="jargon-popover-header"><span class="jargon-popover-title">💡 Packet Loss Concealment (PLC)</span><span class="jargon-popover-badge">Acoustic Synthesis</span></span>'
            '<span class="jargon-popover-body"><span class="jargon-popover-desc">A continuous surrogate waveform synthesis algorithm.</span></span>'
            '</span></span> **: When an audio packet drops, codecs like **Opus** do not stall.</p>'
        )
        sanitized = rl.sanitize_tooltips_to_spans(raw_leaked_html)
        self.assertNotIn("**", sanitized, "All raw markdown bold asterisks must be cleaned or converted to <strong>")
        self.assertIn("<strong>", sanitized)
        self.assertIn("Opus", sanitized)

        # 2. Test build_jargon_tooltip cleans asterisks from terms
        cue_html = build_jargon_tooltip("**Packet Loss Concealment (PLC)**", "**Packet Loss Concealment (PLC)**", "Acoustic", "Synthesizes waveform")
        self.assertNotIn("**", cue_html)
        self.assertIn(">Packet Loss Concealment (PLC)<", cue_html)

        # 3. Verify lesson template popover CSS styles and collision detection logic
        template_path = os.path.join(REPO_ROOT, "skills", "system-design-studio", "resources", "lesson-template.html")
        with open(template_path, "r", encoding="utf-8") as f:
            tmpl = f.read()
        self.assertIn("z-index: 9999;", tmpl)
        self.assertIn("max-height: calc(100vh - 48px);", tmpl)
        self.assertIn("spaceAbove < cardHeight + safetyMargin", tmpl)
        self.assertIn("popover-below", tmpl)
        self.assertIn("minAllowedLeft", tmpl)
        self.assertIn("maxAllowedRight", tmpl)
        self.assertIn("Math.max(containerRect.left", tmpl)
        self.assertIn("card.style.transform = 'none'", tmpl)

    def test_popover_clamping_geometry_simulation(self):
        """Simulate popover positioning math across various viewport & container boundaries."""
        def calculate_popover_geometry(container_left, container_width, wrapper_left, wrapper_width, card_w=420):
            container_right = container_left + container_width
            min_allowed_left = max(container_left + 16, 16)
            max_allowed_right = min(container_right - 16, 1920 - 16)
            max_avail_width = max_allowed_right - min_allowed_left
            card_max_w = max(260, min(card_w, max_avail_width))
            card_width = min(card_w, card_max_w)

            wrapper_center = wrapper_left + wrapper_width / 2
            target_left = wrapper_center - card_width / 2

            if target_left < min_allowed_left:
                target_left = min_allowed_left
            if target_left + card_width > max_allowed_right:
                target_left = max_allowed_right - card_width
            if target_left < min_allowed_left:
                target_left = min_allowed_left

            offset_left = round(target_left - wrapper_left)
            rendered_card_left = wrapper_left + offset_left
            rendered_card_right = rendered_card_left + card_width
            return rendered_card_left, rendered_card_right, min_allowed_left, max_allowed_right

        # Case 1: Cue at left edge of main viewport (e.g. SO_SNDBUF next to 352px sidebar)
        c_left, c_right, min_l, max_r = calculate_popover_geometry(
            container_left=352, container_width=1000, wrapper_left=370, wrapper_width=80
        )
        self.assertGreaterEqual(c_left, min_l, "Card left edge must not clip left container boundary")
        self.assertLessEqual(c_right, max_r, "Card right edge must not clip right container boundary")

        # Case 2: Cue at far right edge of main viewport
        c_left, c_right, min_l, max_r = calculate_popover_geometry(
            container_left=352, container_width=1000, wrapper_left=1300, wrapper_width=40
        )
        self.assertGreaterEqual(c_left, min_l)
        self.assertLessEqual(c_right, max_r)

        # Case 3: Mobile narrow viewport (360px screen, 0px sidebar)
        c_left, c_right, min_l, max_r = calculate_popover_geometry(
            container_left=0, container_width=360, wrapper_left=20, wrapper_width=50
        )
        self.assertGreaterEqual(c_left, min_l)
        self.assertLessEqual(c_right, max_r)
        self.assertLessEqual(c_right - c_left, 360)

    def test_highlight_styles_and_storage_recovery(self):
        """Verify highlight styles in lesson template and robust cross-format storage recovery."""
        template_path = os.path.join(REPO_ROOT, "skills", "system-design-studio", "resources", "lesson-template.html")
        with open(template_path, "r", encoding="utf-8") as f:
            tmpl = f.read()
        self.assertIn(".sds-highlight", tmpl)
        self.assertIn(".sds-hl-yellow", tmpl)
        self.assertIn(".sds-hl-emerald", tmpl)
        self.assertIn(".sds-hl-cyan", tmpl)

        # Import serve-dashboard functions
        sd = importlib.import_module("serve-dashboard")
        import tempfile

        with tempfile.TemporaryDirectory() as tmp_inst:
            hl_dir = os.path.join(tmp_inst, "highlights")
            os.makedirs(hl_dir, exist_ok=True)

            # Test 1: get_highlights_candidates
            candidates = sd.get_highlights_candidates(tmp_inst, "lessons/0-1-tcp-vs-udp.html")
            self.assertTrue(candidates[0].endswith("lessons--0-1-tcp-vs-udp.html.json"))
            self.assertTrue(any(c.endswith("lessons--0-1-tcp-vs-udp.md.json") for c in candidates))

            # Test 2: load_highlights_data recovers legacy .md.json highlights
            legacy_md_json = os.path.join(hl_dir, "lessons--0-1-tcp-vs-udp.md.json")
            with open(legacy_md_json, "w", encoding="utf-8") as f:
                json.dump([
                    {"id": "hl-1", "text": "TCP is a byte stream", "color": "yellow"},
                    {"id": "hl-2", "text": "UDP preserves message boundaries", "color": "cyan"}
                ], f)

            loaded = sd.load_highlights_data(tmp_inst, "lessons/0-1-tcp-vs-udp.html")
            self.assertEqual(len(loaded), 2)
            self.assertEqual(loaded[0]["id"], "hl-1")
            self.assertEqual(loaded[1]["id"], "hl-2")

            # Test 3: save_highlights_data writes to canonical .html.json and cleans legacy .md.json
            sd.save_highlights_data(tmp_inst, "lessons/0-1-tcp-vs-udp.html", loaded)
            canonical_path = os.path.join(hl_dir, "lessons--0-1-tcp-vs-udp.html.json")
            self.assertTrue(os.path.isfile(canonical_path), "Canonical .html.json must be written")
            self.assertFalse(os.path.isfile(legacy_md_json), "Legacy .md.json must be safely migrated and cleaned")

    def test_settings_modal_excludes_markdown_format(self):
        """Verify dashboard settings modal no longer exposes markdown lesson delivery option."""
        dashboard_path = os.path.join(SCRIPTS_DIR, "serve-dashboard.py")
        with open(dashboard_path, "r", encoding="utf-8") as f:
            code = f.read()

        # Invariant: Settings modal must not contain settings-lesson-format dropdown or radio
        self.assertNotIn('id="settings-lesson-format"', code)
        self.assertNotIn("settings-lesson-format", code)

    def test_escaped_tooltip_sanitization_preserves_all_panes(self):
        """Verify sanitize_tooltips_to_spans correctly unescapes nested tooltips without truncating remaining panes."""
        rl = importlib.import_module("render-lesson")
        
        # Construct multi-pane HTML with an accidentally escaped tooltip inside pane 1
        escaped_tip = (
            '&lt;span class=&quot;jargon-tooltip-wrapper&quot;&gt;'
            '&lt;span class=&quot;jargon-inline-cue&quot; onclick=&quot;toggleJargonTooltip(this, event)&quot;&gt;MSS&lt;/span&gt;'
            '&lt;span class=&quot;jargon-popover-card&quot;&gt;'
            '&lt;span class=&quot;jargon-popover-header&quot;&gt;&lt;span class=&quot;jargon-popover-title&quot;&gt;💡 MSS&lt;/span&gt;'
            '&lt;span class=&quot;jargon-popover-badge&quot;&gt;Metric&lt;/span&gt;&lt;/span&gt;'
            '&lt;span class=&quot;jargon-popover-body&quot;&gt;&lt;span class=&quot;jargon-popover-desc&quot;&gt;Maximum Segment Size&lt;/span&gt;&lt;/span&gt;'
            '&lt;/span&gt;&lt;/span&gt;'
        )
        sample_panes = (
            f'<article id="pane-section-1" class="section-pane active">\n'
            f'  <p>Here is payload ({escaped_tip}) for testing.</p>\n'
            f'  <button onclick="switchSectionTab(\'section-2\')">Next</button>\n'
            f'</article>\n'
            f'<article id="pane-section-2" class="section-pane">\n'
            f'  <p>Stage 2 content here.</p>\n'
            f'  <button onclick="switchSectionTab(\'section-3\')">Next</button>\n'
            f'</article>\n'
            f'<article id="pane-section-3" class="section-pane">\n'
            f'  <p>Stage 3 content here.</p>\n'
            f'</article>'
        )

        sanitized = rl.sanitize_tooltips_to_spans(sample_panes)
        self.assertIn('id="pane-section-1"', sanitized)
        self.assertIn('id="pane-section-2"', sanitized, "Pane 2 must not be truncated by tooltip sanitization")
        self.assertIn('id="pane-section-3"', sanitized, "Pane 3 must not be truncated by tooltip sanitization")
        self.assertNotIn('&lt;span class=&quot;jargon-tooltip-wrapper', sanitized)
        self.assertIn('class="jargon-tooltip-wrapper"', sanitized)
        self.assertIn('Maximum Segment Size', sanitized)

    def test_popover_card_zero_vertical_bar_styling(self):
        """Verify popover card enforces overflow: hidden and hides all scrollbars to eliminate vertical bars."""
        template_path = os.path.join(REPO_ROOT, "skills", "system-design-studio", "resources", "lesson-template.html")
        with open(template_path, "r", encoding="utf-8") as f:
            tmpl = f.read()
        self.assertIn(".jargon-popover-card", tmpl)
        self.assertIn("overflow: hidden;", tmpl)
        self.assertIn("scrollbar-width: none !important;", tmpl)
        self.assertIn("-ms-overflow-style: none !important;", tmpl)
        self.assertIn("display: none !important;", tmpl)

    def test_seamless_highlight_styles_and_atomic_deletion(self):
        """Verify seamless multi-node highlighting, no fragmentation gaps, and atomic deletion."""
        dashboard_path = os.path.join(SCRIPTS_DIR, "serve-dashboard.py")
        with open(dashboard_path, "r", encoding="utf-8") as f:
            code = f.read()

        # Invariant 1: Seamless highlight styling
        self.assertIn("cursor: text;", code)
        self.assertIn(".sds-highlight.sds-hl-head", code)
        self.assertIn(".sds-highlight.sds-hl-tail", code)
        self.assertIn(".sds-hl-del-btn", code)
        self.assertIn("box-decoration-break: clone;", code)

        # Invariant 2: Context-aware capture
        self.assertIn("cloned.querySelectorAll('.jargon-popover-card", code)
        self.assertIn("prefix = ", code)
        self.assertIn("suffix = ", code)
        self.assertIn("paneId = ", code)

        # Invariant 3: Atomic deletion
        self.assertIn('rootDoc.querySelectorAll(`mark[data-hl-id="${hlId}"]`)', code)
        self.assertIn('sds-hl-del-btn', code)

    def test_tooltip_selection_suppression_and_clean_drop(self):
        """Verify tooltip cues and popover cards strictly suppress selection backgrounds and clean drops."""
        template_path = os.path.join(REPO_ROOT, "skills", "system-design-studio", "resources", "lesson-template.html")
        with open(template_path, "r", encoding="utf-8") as f:
            tmpl = f.read()

        dashboard_path = os.path.join(SCRIPTS_DIR, "serve-dashboard.py")
        with open(dashboard_path, "r", encoding="utf-8") as f:
            dash = f.read()

        # Invariant 1: Both template and dashboard suppress selection on tooltip cues and wrappers
        for source, name in [(tmpl, "lesson-template.html"), (dash, "serve-dashboard.py")]:
            self.assertIn(".jargon-tooltip-wrapper::selection", source, f"Missing tooltip selection suppression in {name}")
            self.assertIn(".jargon-inline-cue::selection", source, f"Missing inline cue selection suppression in {name}")
            self.assertIn(".jargon-popover-card::selection", source, f"Missing popover card selection suppression in {name}")
            self.assertIn("user-select: none !important;", source, f"Missing user-select none !important in {name}")

        # Invariant 2: Universal clearAllSelectionArtifacts function in dashboard
        self.assertIn("function clearAllSelectionArtifacts()", dash)
        self.assertIn("clearAllSelectionArtifacts();", dash)
        self.assertIn("iframe.contentWindow.clearAllSelectionArtifacts = clearAllSelectionArtifacts;", dash)

        # Invariant 3: Zero overflowY = 'auto' on tooltip cards to prevent scrollbar tracks
        self.assertNotIn("card.style.overflowY = 'auto'", tmpl)

    def test_notes_workbench_highlights_sidebar_and_persistence(self):
        """Verify split editor bug fix, Notion-grade upgrades, highlights sidebar, atomic persistence, and sds-complete highlights."""
        dashboard_path = os.path.join(SCRIPTS_DIR, "serve-dashboard.py")
        with open(dashboard_path, "r", encoding="utf-8") as f:
            dash = f.read()

        # 1. Split editor bug fix: no phantom boilerplate default text in openTopicNote
        self.assertNotIn("# System Architecture Notes: ${topicTitle || topicId}", dash)
        self.assertIn("NOTE_EMPTY_HTML", dash)
        self.assertIn("NOTE_SLASH_COMMANDS", dash)
        self.assertIn("function handleNoteEditorKeyDown(e)", dash)
        self.assertIn("function toggleNoteTaskCheckbox(", dash)
        self.assertIn("function syncNoteSplitScroll()", dash)

        # 2. Highlights slide-over sidebar replaces toolbar dropover
        self.assertIn('id="highlights-drawer"', dash)
        self.assertNotIn('class="hl-popover-menu"', dash)
        self.assertIn("function toggleHighlightsSidebar(surfaceHint)", dash)
        self.assertIn("function navigateToHighlight(surfaceHint, hlId)", dash)
        self.assertIn("sds-hl-pulse", dash)
        # Highlight colors are purely decorative (no semantic labels like Key Concept / Invariant)
        self.assertNotIn("yellow: 'Key Concept'", dash)
        self.assertNotIn("emerald: 'Invariant'", dash)
        self.assertNotIn("cyan: 'Question'", dash)

        # 3. Atomic disk persistence for notes & highlights
        self.assertIn("def atomic_write_text(target_path, content):", dash)
        self.assertIn("atomic_write_text(canonical,", dash)
        self.assertIn("atomic_write_text(target, content)", dash)

        # 4. sds-complete / generate-notes.py integrates highlights into clean reference notes
        import importlib.util
        import tempfile
        gen_path = os.path.join(SCRIPTS_DIR, "generate-notes.py")
        spec = importlib.util.spec_from_file_location("generate_notes", gen_path)
        gen_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gen_mod)

        with tempfile.TemporaryDirectory() as tmpdir:
            inst_dir = os.path.join(tmpdir, ".system-design")
            hl_dir = os.path.join(inst_dir, "highlights")
            os.makedirs(hl_dir, exist_ok=True)
            hl_file = os.path.join(hl_dir, "lessons--0-1-tcp-vs-udp.html.json")
            with open(hl_file, "w", encoding="utf-8") as hf:
                json.dump([
                    {"id": "hl_1", "color": "yellow", "text": "TCP enforces ordered byte stream delivery.", "paneId": "pane-section-2"},
                    {"id": "hl_2", "color": "emerald", "text": "Head-of-line blocking stalls all packets behind a lost segment.", "paneId": "pane-section-3"},
                ], hf)
            loaded = gen_mod.load_topic_highlights(inst_dir, "topic.0.1.tcp-vs-udp")
            self.assertEqual(len(loaded), 2)
            md_section = gen_mod.format_highlights_markdown_section(loaded)
            self.assertIn("## Highlighted Passages", md_section)
            self.assertIn("**[Stage 2]**", md_section)
            self.assertIn("**[Stage 3]**", md_section)
            self.assertNotIn("Key Concept", md_section)
            self.assertNotIn("Invariant", md_section)
            self.assertIn("TCP enforces ordered byte stream delivery.", md_section)

            note_md = gen_mod.build_note_markdown(
                {"code": "0", "name": "Tier 0"},
                {"code": "0.1", "title": "Transport"},
                {"id": "topic.0.1.tcp-vs-udp", "title": "TCP vs UDP"},
                "", "", "", "2026-11-25"
            )
            self.assertIn("## 1. Core Context & Problem Space", note_md)
            self.assertNotIn("Socratic", note_md)
            self.assertNotIn("proved cold", note_md)
            self.assertNotIn("Where the Model Broke", note_md)

    def test_agentic_notes_crafter_and_auditor_pipeline(self):
        """Verify sds-notes-crafter, auditor Notes Audit Mode, sds-complete orchestration, and NoteDocument JSON rendering."""
        crafter_md = os.path.join(REPO_ROOT, "agents", "sds-notes-crafter.md")
        crafter_agent = os.path.join(REPO_ROOT, "agents", "sds-notes-crafter", "AGENT.md")
        auditor_md = os.path.join(REPO_ROOT, "agents", "sds-pedagogy-auditor.md")
        complete_skill = os.path.join(REPO_ROOT, "skills", "sds-complete", "SKILL.md")

        for p in [crafter_md, crafter_agent, auditor_md, complete_skill]:
            self.assertTrue(os.path.isfile(p), f"Missing required file: {p}")

        with open(crafter_md, "r", encoding="utf-8") as f:
            crafter_txt = f.read()
        self.assertIn("notes-adaptiveness.json", crafter_txt)
        self.assertIn(".generated-note-", crafter_txt)
        self.assertIn("future_safe_anchors", crafter_txt)

        with open(auditor_md, "r", encoding="utf-8") as f:
            auditor_txt = f.read()
        self.assertIn("Notes Audit Mode", auditor_txt)
        self.assertIn("Temporal Distance Check", auditor_txt)

        with open(complete_skill, "r", encoding="utf-8") as f:
            complete_txt = f.read()
        self.assertIn("sds-notes-crafter", complete_txt)
        self.assertIn("sds-pedagogy-auditor", complete_txt)
        self.assertIn("--notes-data-file", complete_txt)

        from lesson_builder import NoteDocument
        payload = {
            "topic_id": "topic.0.1.tcp-vs-udp",
            "title": "TCP vs UDP",
            "tier": {"code": "0", "name": "Tier 0"},
            "cluster": {"code": "0.1", "title": "Transport"},
            "core_context": "Balancing ordered byte delivery against tail-latency spikes.",
            "mechanics_and_failures": ["Losing packet #2 stalls packets #3-#5 in SO_RCVBUF."],
            "core_invariant": "Use UDP/QUIC when stale frames are worthless; use TCP when byte order is mandatory.",
            "rules_of_thumb": [
                {"tradeoff": "Order vs Freshness", "decision_rule": "Prefer QUIC for multiplexed RPCs", "production_bound": "BDP = RTT * Bandwidth"}
            ],
            "future_safe_anchors": ["**SO_RCVBUF**: Kernel memory queue staging inbound segments before read()."],
            "highlighted_passages": [{"text": "TCP has no concept of message boundaries.", "paneId": "pane-section-2"}],
        }
        md = NoteDocument.from_dict(payload).to_markdown()
        self.assertIn("## Quick Refresh Anchors", md)
        self.assertIn("**SO_RCVBUF**", md)
        self.assertIn("## Highlighted Passages", md)
        self.assertIn("**[Stage 2]**", md)
        self.assertNotIn("Key Concept", md)


if __name__ == "__main__":
    unittest.main()
