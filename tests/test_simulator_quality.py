#!/usr/bin/env python3
"""
test_simulator_quality.py
Unit & integration tests verifying:
1. Pulling simulator out of rigid AST into direct HTML nodes (SimulatorHtmlNode).
2. Automated pre-flight simulator quality audits (Controls, Failure injection, DOM ID coherence, JS syntax, Telemetry, Log).
"""

import os
import sys
import json
import unittest

# Ensure skills scripts directory is in path
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "skills", "system-design-studio", "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from lesson_builder import LessonDocument, SimulatorHtmlNode, build_simulator_container
import importlib.util

spec = importlib.util.spec_from_file_location("render_lesson", os.path.join(SCRIPTS_DIR, "render-lesson.py"))
render_lesson = importlib.util.module_from_spec(spec)
spec.loader.exec_module(render_lesson)


class TestSimulatorQuality(unittest.TestCase):

    def _build_base_payload(self):
        """Builds a baseline valid lesson dictionary payload."""
        words = "word " * 400
        jargons = "".join([
            f'<span class="jargon-tooltip-wrapper"><span class="jargon-inline-cue">Term{i}</span>'
            f'<span class="jargon-popover-card"><span class="jargon-popover-desc">Definition {i}</span></span></span> '
            for i in range(1, 8)
        ])
        return {
            "LESSON_TITLE": "B-Tree Concurrency & Page Splitting",
            "SECTION_1_TITLE": "The Storage Dilemma: Page Splits vs Concurrent Readers",
            "SECTION_1_BODY": f"<div class=\"callout-box callout-dilemma\">The Core Dilemma</div><p>{words} {jargons}</p>",
            "SECTION_2_TITLE": "B-Tree Architecture & Latch Crabbing",
            "SECTION_2_BODY": f"<p>{words}</p>",
            "SECTION_3_TITLE": "Internal Mechanics: Split Cascades & Failure Injections",
            "SECTION_3_BODY": f"<p>{words}</p>",
            "SECTION_4_TITLE": "Production Invariants & Sizing",
            "SECTION_4_BODY": f"<p>{words}</p>",
            "SECTION_5_TITLE": "Architectural Sign-Off Defense",
            "SECTION_5_BODY": f"<p>{words}</p>",
            "EMBEDDED_JAVASCRIPT": ""
        }

    def test_direct_html_simulator_node_rendering(self):
        """Verifies SimulatorHtmlNode renders bespoke HTML and Markdown trace directly."""
        custom_html = """
        <div id="sim-btree" class="p-4 bg-stone-900 border border-stone-800 rounded-xl">
          <div class="flex gap-2">
            <button id="btn-insert-key" class="px-3 py-1 bg-amber-500 text-stone-900 font-bold">Insert Key 42</button>
            <button id="btn-inject-split-stall" class="px-3 py-1 bg-rose-600 text-white font-bold">Trigger Page Split Stall</button>
            <button id="btn-reset" class="px-3 py-1 bg-stone-800 text-stone-300">Reset</button>
          </div>
          <div id="sim-canvas" class="my-4 p-4 bg-stone-950 font-mono text-xs">Page [10, 20, 30]</div>
          <div class="flex gap-4 text-xs font-mono">
            <div>Stall Delay: <span id="tel-stall">0 ms</span></div>
            <div>Dirty Pages: <span id="tel-dirty">0</span></div>
          </div>
          <div id="sim-log" class="mt-2 text-xs font-mono text-stone-400">Initialized.</div>
        </div>
        """
        custom_js = """
        document.getElementById('btn-insert-key').onclick = function() {
            document.getElementById('tel-dirty').textContent = '1';
            document.getElementById('sim-log').innerHTML += '<br/>Inserted key 42.';
        };
        document.getElementById('btn-inject-split-stall').onclick = function() {
            document.getElementById('tel-stall').textContent = '12 ms';
            document.getElementById('sim-log').innerHTML += '<br/>Page split stall injected.';
        };
        document.getElementById('btn-reset').onclick = function() {
            document.getElementById('tel-stall').textContent = '0 ms';
            document.getElementById('tel-dirty').textContent = '0';
        };
        """
        md_trace = """
        | Stage | Key Inserted | Page Status | Invariant Observed |
        | :--- | :--- | :--- | :--- |
        | Baseline | 42 | Leaf Normal | Zero Stall |
        | Fault | 43 | Split Cascade | Reader Stalled 12ms |
        """

        doc = LessonDocument(topic_id="topic.1.2.b-tree", title="B-Tree Page Split Simulator")
        doc.add_section("Storage Mechanics")
        doc.add_simulator_html(html=custom_html, script=custom_js, markdown_trace=md_trace, title="B-Tree Split Sandbox")

        tabs, panes = doc.to_html_panes()
        self.assertEqual(len(panes), 1)
        self.assertIn('id="sim-btree"', panes[0]["body_html"])
        self.assertIn('btn-inject-split-stall', panes[0]["body_html"])
        self.assertIn('btn-insert-key', panes[0]["body_html"])

        md = doc.to_markdown()
        self.assertIn("| Stage | Key Inserted | Page Status |", md)
        self.assertEqual(doc.embedded_javascript, custom_js.strip())

    def test_valid_simulator_audit_passes(self):
        """Verifies that an agent-crafted direct HTML simulator passes all pre-flight audits."""
        data = self._build_base_payload()
        data["SECTION_3_BODY"] += """
        <div id="sim-container" class="p-4 bg-stone-900 border border-stone-800 rounded-xl">
          <div class="flex gap-2">
            <button id="btn-transmit" class="px-3 py-1 bg-amber-500 font-bold">Transmit 10 Packets</button>
            <button id="btn-inject-drop" class="px-3 py-1 bg-rose-600 font-bold">Inject Packet Drop</button>
            <button id="btn-reset" class="px-3 py-1 bg-stone-800 font-bold">Reset</button>
          </div>
          <div id="sim-canvas" class="my-4 p-4 font-mono">Queue Track</div>
          <div class="flex gap-4">
            <div>Stall Delay: <span id="tel-stall">0 ms</span></div>
            <div>In-Flight: <span id="tel-flight">0 KB</span></div>
          </div>
          <div id="sim-log" class="mt-2 text-xs font-mono">Ready.</div>
        </div>
        """
        data["EMBEDDED_JAVASCRIPT"] = """
        document.getElementById('btn-transmit').onclick = function() {
            document.getElementById('tel-flight').textContent = '10 KB';
            document.getElementById('sim-log').innerHTML += '<br/>Sent 10 packets.';
        };
        document.getElementById('btn-inject-drop').onclick = function() {
            document.getElementById('tel-stall').textContent = '60 ms';
            document.getElementById('sim-log').innerHTML += '<br/>Packet #2 dropped! Kernel buffer stalling.';
        };
        document.getElementById('btn-reset').onclick = function() {
            document.getElementById('tel-stall').textContent = '0 ms';
            document.getElementById('tel-flight').textContent = '0 KB';
        };
        """

        is_valid = render_lesson.audit_lesson_payload(data, topic_id="topic.0.1.tcp-vs-udp")
        self.assertTrue(is_valid)

    def test_degraded_passive_mock_fails(self):
        """Verifies that a static decorative mock with 0 controls is rejected."""
        data = self._build_base_payload()
        # Passive mock without buttons or inputs
        data["SECTION_3_BODY"] += """
        <div id="sim-mock" class="p-4 bg-stone-900 border border-stone-800 rounded-xl">
          <h4>Tactile Mechanics Simulator</h4>
          <div>Sender Queue -> Transit -> Receiver Queue</div>
          <div id="sim-log">Manipulate controls to observe queue dynamics.</div>
        </div>
        """
        is_valid = render_lesson.audit_lesson_payload(data, topic_id="topic.0.1.tcp-vs-udp")
        self.assertFalse(is_valid)

    def test_missing_failure_injection_fails(self):
        """Verifies that a simulator lacking failure injection controls is rejected."""
        data = self._build_base_payload()
        # Contains action trigger and reset, but NO failure injection control
        data["SECTION_3_BODY"] += """
        <div id="sim-canvas">
          <button id="btn-transmit">Transmit Data</button>
          <button id="btn-step">Step Forward</button>
          <button id="btn-reset">Reset</button>
          <div id="sim-log">Log</div>
        </div>
        """
        is_valid = render_lesson.audit_lesson_payload(data, topic_id="topic.0.1.tcp-vs-udp")
        self.assertFalse(is_valid)

    def test_dom_id_mismatch_fails(self):
        """Verifies that JavaScript referencing missing HTML IDs triggers audit failure."""
        data = self._build_base_payload()
        data["SECTION_3_BODY"] += """
        <div id="sim-container">
          <button id="btn-send">Send</button>
          <button id="btn-fail-partition">Sever Network Partition</button>
          <div id="sim-canvas">Cluster Nodes</div>
          <div id="sim-log">Ready</div>
        </div>
        """
        # References non-existent 'tel-missing-metric' and 'btn-unknown'
        data["EMBEDDED_JAVASCRIPT"] = """
        document.getElementById('btn-send').onclick = function() {
            document.getElementById('tel-missing-metric').textContent = 'Failed';
        };
        """
        is_valid = render_lesson.audit_lesson_payload(data, topic_id="topic.2.3.consensus")
        self.assertFalse(is_valid)

    def test_js_syntax_error_fails(self):
        """Verifies that JavaScript with syntax errors fails headless validation."""
        data = self._build_base_payload()
        data["SECTION_3_BODY"] += """
        <div id="sim-container">
          <button id="btn-transmit">Transmit</button>
          <button id="btn-drop">Drop Packet</button>
          <div id="sim-canvas">Track</div>
          <div id="sim-log">Log</div>
        </div>
        """
        # Malformed JavaScript syntax
        data["EMBEDDED_JAVASCRIPT"] = "const broken = ;"

        is_valid = render_lesson.audit_lesson_payload(data, topic_id="topic.0.1.tcp-vs-udp")
        self.assertFalse(is_valid)


if __name__ == "__main__":
    unittest.main()
