#!/usr/bin/env python3
"""
test_node_ast_rendering.py — Comprehensive verification suite for the Semantic
Component Node AST and dual-axis (HTML + Markdown) rendering engine.
"""

import os
import sys
import json
import unittest
import tempfile
import subprocess

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "skills", "system-design-studio", "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from lesson_builder import (
    LessonDocument,
    SectionNode,
    SubsectionNode,
    DividerNode,
    EditorialLeadNode,
    ParagraphNode,
    ListNode,
    QuoteNode,
    DilemmaNode,
    CalloutNode,
    AnalogyNode,
    BreakthroughNode,
    StepTraceNode,
    ComparisonMatrixNode,
    FormulaNode,
    CodeBlockNode,
    SimulatorNode,
    DefenseChallengeNode,
    MentalModelNode,
    RawHtmlNode,
    node_from_dict
)


class TestNodeASTRendering(unittest.TestCase):

    def test_01_all_node_types_rendering(self):
        """Verifies both HTML and Markdown compilation across all 18 semantic node types."""
        ctx = {"current_section_glossary": {}, "all_glossary": {}}

        # 1. SectionNode
        sec = SectionNode(title="1. Physical Dilemma", subtitle="Latency vs Safety", badge="Physical Dilemma", section_id="sec-1")
        self.assertEqual(sec.title, "Physical Dilemma")  # Strips numeric prefix
        self.assertIn("## Physical Dilemma", sec.render_markdown(ctx))
        self.assertIn("*Latency vs Safety*", sec.render_markdown(ctx))

        # 2. SubsectionNode
        sub = SubsectionNode(title="Buffer Pool Eviction", level=3)
        self.assertIn("### Buffer Pool Eviction", sub.render_markdown(ctx))
        self.assertIn('<h3 class="text-base font-bold', sub.render_html(ctx))

        # 3. DividerNode
        div = DividerNode()
        self.assertEqual(div.render_markdown(ctx), "\n---\n\n")
        self.assertIn('<hr class="my-6', div.render_html(ctx))

        # 4. EditorialLeadNode
        lead = EditorialLeadNode("Every database engine starts with physics.")
        self.assertIn("> *Every database engine starts with physics.*", lead.render_markdown(ctx))
        self.assertIn('class="editorial-lead"', lead.render_html(ctx))

        # 5. ParagraphNode with inline jargon
        para = ParagraphNode(
            text="When an app executes {{jargon:fsync}}, the OS commits dirty pages.",
            jargons={"fsync": {"term": "fsync()", "category": "POSIX Syscall", "definition": "Flushes dirty pages to non-volatile disk."}}
        )
        md_p = para.render_markdown(ctx)
        html_p = para.render_html(ctx)
        self.assertIn("When an app executes **fsync()**, the OS commits dirty pages.", md_p)
        self.assertIn('class="jargon-tooltip-wrapper"', html_p)
        self.assertIn('onclick="toggleJargonTooltip(this, event)"', html_p)
        self.assertIn("fsync()", ctx["current_section_glossary"])

        # 6. ListNode (unordered and ordered)
        ul = ListNode(["Disk seek: 10ms", "RAM access: 100ns"], ordered=False)
        self.assertIn("- Disk seek: 10ms\n- RAM access: 100ns", ul.render_markdown(ctx))
        self.assertIn("<ul", ul.render_html(ctx))

        ol = ListNode(["Step 1", "Step 2"], ordered=True)
        self.assertIn("1. Step 1\n2. Step 2", ol.render_markdown(ctx))
        self.assertIn("<ol", ol.render_html(ctx))

        # 7. QuoteNode
        q = QuoteNode("Premature optimization is the root of all evil.", author="Donald Knuth", role="Computer Scientist")
        self.assertIn("> \"Premature optimization is the root of all evil.\"", q.render_markdown(ctx))
        self.assertIn("**Donald Knuth**, *Computer Scientist*", q.render_markdown(ctx))
        self.assertIn("border-l-4 border-amber-500", q.render_html(ctx))

        # 8. DilemmaNode
        dil = DilemmaNode(
            title="Write Latency vs Persistence",
            lead="Storage engines face two unacceptable failure modes:",
            extremes=[
                ("Extreme 1: Synchronous Disk Writes", "10ms seek", "100 TPS ceiling"),
                ("Extreme 2: Pure In-Memory Buffering", "0.01ms DRAM", "Catastrophic data loss on power cut")
            ],
            resolution_preview="The Write-Ahead Log unifies persistence and low latency."
        )
        md_dil = dil.render_markdown(ctx)
        html_dil = dil.render_html(ctx)
        self.assertIn("> [!WARNING] ⚡ Write Latency vs Persistence", md_dil)
        self.assertIn("Extreme 1: Synchronous Disk Writes", md_dil)
        self.assertIn("callout-box callout-dilemma", html_dil)

        # 9. CalloutNode variants
        callout_kinds = [
            ("dilemma", "[!WARNING]", "⚡"),
            ("mechanism", "[!NOTE]", "⚙️"),
            ("invariant", "[!IMPORTANT]", "🔒"),
            ("trap", "[!CAUTION]", "⚠️"),
            ("tip", "[!TIP]", "💡")
        ]
        for kind, expected_gfm, expected_icon in callout_kinds:
            c = CalloutNode(kind=kind, title="Test Callout", text="Important invariant statement.")
            self.assertIn(f"> {expected_gfm} {expected_icon} Test Callout", c.render_markdown(ctx))
            self.assertIn(f"callout-{kind}", c.render_html(ctx))

        # 10. AnalogyNode
        an = AnalogyNode(
            title="Restaurant Order Ticket",
            category="Operational Workflow",
            mental_model="Writing the order on paper before cooking mirrors write-ahead logging.",
            mapping=[{"physical": "Order ticket pad", "systems": "WAL append-only log file"}]
        )
        md_an = an.render_markdown(ctx)
        html_an = an.render_html(ctx)
        self.assertIn("> [!TIP] 💡 Intuitive Mental Model: Restaurant Order Ticket", md_an)
        self.assertIn("| Order ticket pad | WAL append-only log file |", md_an)
        self.assertIn('class="analogy-card"', html_an)

        # 11. BreakthroughNode (Aha card)
        aha = BreakthroughNode(title="Sequential Append Dominance", text="Disks write sequential blocks at bus speed.")
        self.assertIn("> [!NOTE] ✨ Breakthrough Realization: Sequential Append Dominance", aha.render_markdown(ctx))
        self.assertIn('class="aha-card"', aha.render_html(ctx))

        # 12. StepTraceNode
        trace = StepTraceNode(
            title="WAL Commit Lifecycle",
            steps=[
                ("T0", "Client App", "Issues INSERT query", "Enters database worker thread"),
                ("T1", "Storage Engine", "Appends to WAL in memory", "Record staged with LSN"),
                ("T2", "Kernel", "Executes fsync()", "Flushed to NVMe non-volatile flash")
            ]
        )
        md_tr = trace.render_markdown(ctx)
        html_tr = trace.render_html(ctx)
        self.assertIn("### ⏱️ Causal Execution Trace: WAL Commit Lifecycle", md_tr)
        self.assertIn("| `T0` | **Client App** | Issues INSERT query | Enters database worker thread |", md_tr)
        self.assertIn('rounded-xl bg-stone-900/90 border border-stone-800', html_tr)

        # 13. ComparisonMatrixNode
        matrix = ComparisonMatrixNode(
            title="B-Tree vs LSM-Tree",
            headers=["Attribute", "B-Tree", "LSM-Tree"],
            rows=[
                ["Write Amplification", "High (Random Pages)", "Low (Sequential Appends)"],
                ["Read Amplification", "Low (Direct O(log N))", "Higher (Multi-SST Compaction)"]
            ]
        )
        md_mat = matrix.render_markdown(ctx)
        html_mat = matrix.render_html(ctx)
        self.assertIn("| Attribute | B-Tree | LSM-Tree |", md_mat)
        self.assertIn("B-Tree vs LSM-Tree", html_mat)
        self.assertIn("border-collapse", html_mat)

        # 14. FormulaNode
        formula = FormulaNode(
            name="Bandwidth-Delay Product (BDP)",
            expression="BDP = Bandwidth (bits/sec) * RTT (sec)",
            variables={"Bandwidth": "Bottleneck link transmission capacity", "RTT": "Round-Trip Time"},
            derivation=["Flight Size = 1 Gbps * 0.050s", "= 50,000,000 bits = 6.25 MB in flight"],
            conclusion="Buffer size must equal BDP to prevent pipeline stall."
        )
        md_form = formula.render_markdown(ctx)
        html_form = formula.render_html(ctx)
        self.assertIn("```math\nBDP = Bandwidth (bits/sec) * RTT (sec)\n```", md_form)
        self.assertIn("- `Bandwidth`: Bottleneck link transmission capacity", md_form)
        self.assertIn('class="font-mono text-sm text-amber-300', html_form)

        # 15. CodeBlockNode
        code = CodeBlockNode(language="python", code="def commit():\n    wal.append()\n    wal.flush()", filename="engine.py", caption="Simple commit")
        md_code = code.render_markdown(ctx)
        html_code = code.render_html(ctx)
        self.assertIn("```python\n// engine.py\ndef commit():", md_code)
        self.assertIn("<pre class=", html_code)
        self.assertIn("<code>def commit():", html_code)

        # 16. SimulatorNode
        sim = SimulatorNode(model="wal_flow", title="Tactile WAL Flow", subtitle="Observe disk head movements.")
        md_sim = sim.render_markdown(ctx)
        html_sim = sim.render_html(ctx)
        self.assertIn("> [!NOTE] 🎮 Interactive Simulation Walkthrough: Tactile WAL Flow", md_sim)
        self.assertIn("Tactile Mechanics Simulator", html_sim)
        self.assertIn("Tactile WAL Flow", html_sim)

        # 17. DefenseChallengeNode
        defense = DefenseChallengeNode(
            title="Power-Cut Recovery Invariant",
            scenario="A replica experiences an abrupt kernel panic midway through a transaction batch.",
            prompts=[
                ("Recovery Sequence", "Trace how WAL replay reconstructs dirty buffer state."),
                ("Torn Pages", "Defend how doublewrite buffers protect against partial page writes.")
            ],
            constraints=["No battery-backed RAM (BBU)", "NVMe write cache enabled"]
        )
        md_def = defense.render_markdown(ctx)
        html_def = defense.render_html(ctx)
        self.assertIn("## 🛡️ Architectural Defense Challenge: Power-Cut Recovery Invariant", md_def)
        self.assertIn("1. **Recovery Sequence:** Trace how WAL replay reconstructs", md_def)
        self.assertIn("ARCHITECTURAL CHALLENGE SCENARIO", html_def)

        # 18. MentalModelNode
        mm = MentalModelNode(
            statement="WAL converts random write latency into sequential append throughput.",
            explanation="By recording intents sequentially first, actual table page writes can be lazily deferred to background flushes."
        )
        md_mm = mm.render_markdown(ctx)
        html_mm = mm.render_html(ctx)
        self.assertIn("> [!IMPORTANT] The Architectural Mental Model", md_mm)
        self.assertIn("WAL converts random write latency into sequential append throughput.", md_mm)
        self.assertIn("The Architectural Mental Model", html_mm)

        # 19. RawHtmlNode
        raw = RawHtmlNode("<div class=\"custom-box\"><p>Custom markup</p></div>")
        self.assertIn("Custom markup", raw.render_markdown(ctx))
        self.assertIn('<div class="custom-box">', raw.render_html(ctx))

    def test_02_content_scaling_and_extremes(self):
        """Verifies graceful handling of small 1-line inputs and large multi-paragraph loads."""
        doc = LessonDocument(topic_id="topic.scale.test", title="Extreme Scaling Test")

        # Small 1-line inputs
        doc.add_section("Mini Section")
        doc.add_lead("Minimal.")
        doc.add_paragraph("Tiny body.")
        doc.add_divider()
        doc.add_mental_model("Short rule.", "Short why.")

        md_small = doc.to_markdown()
        tabs_small, panes_small = doc.to_html_panes()
        self.assertEqual(len(tabs_small), 1)
        self.assertEqual(len(panes_small), 1)
        self.assertIn("Minimal.", md_small)

        # Large scaling inputs
        doc2 = LessonDocument(topic_id="topic.scale.test2", title="Large Volume Test")
        doc2.add_section("Volume Section")
        # 10 large paragraphs
        for i in range(10):
            doc2.add_paragraph(f"Detailed architectural analysis paragraph {i} " * 20)
        # 20-row comparison table
        headers = ["Col A", "Col B", "Col C", "Col D"]
        rows = [[f"Val A{r}", f"Val B{r}", f"Val C{r}", f"Val D{r}"] for r in range(20)]
        doc2.add_comparison_matrix("Massive Matrix", headers, rows)
        # 15-step trace
        steps = [(f"T{s}", f"Worker-{s%4}", f"Action {s}", f"Consequence {s}") for s in range(15)]
        doc2.add_step_trace("Long Step Trace", steps)

        md_large = doc2.to_markdown()
        tabs_large, panes_large = doc2.to_html_components()
        self.assertIn("| Col A | Col B | Col C | Col D |", md_large)
        self.assertIn("| `T14` | **Worker-2** |", md_large)
        self.assertIn("Massive Matrix", panes_large)

    def test_03_arbitrary_section_counts(self):
        """Verifies that the document model handles arbitrary section counts (2, 3, 6 sections)."""
        # 2 Sections
        doc_2sec = LessonDocument(topic_id="topic.two.sec", title="Two Section Lesson")
        doc_2sec.add_section("Opening Dilemma", badge="Dilemma")
        doc_2sec.add_lead("Two sections only.")
        doc_2sec.add_section("Architectural Resolution", badge="Resolution")
        doc_2sec.add_paragraph("All resolved.")

        tabs2, panes2 = doc_2sec.to_html_panes()
        tabs_html2, panes_html2 = doc_2sec.to_html_components()
        self.assertEqual(len(tabs2), 2)
        self.assertEqual(len(panes2), 2)
        self.assertIn('data-target="opening-dilemma"', tabs_html2)
        self.assertIn('data-target="architectural-resolution"', tabs_html2)
        # Verify first pane has Next button to section 2
        self.assertIn("switchSectionTab('architectural-resolution')", panes_html2)
        # Verify second (last) pane has Socratic prompt
        self.assertIn("Ready to defend? Reply in chat to begin Socratic evaluation.", panes_html2)

        # 6 Sections
        doc_6sec = LessonDocument(topic_id="topic.six.sec", title="Six Section Deep-Dive")
        for i in range(1, 7):
            doc_6sec.add_section(f"Phase {i} Invariant", badge=f"Phase {i}")
            doc_6sec.add_paragraph(f"Content for phase {i}.")

        tabs6, panes6 = doc_6sec.to_html_panes()
        tabs_html6, panes_html6 = doc_6sec.to_html_components()
        self.assertEqual(len(tabs6), 6)
        self.assertEqual(len(panes6), 6)
        self.assertIn("<!-- Tab 1 -->", tabs_html6)
        self.assertIn("<!-- Tab 6 -->", tabs_html6)
        self.assertIn("<!-- PANE 1:", panes_html6)
        self.assertIn("<!-- PANE 6:", panes_html6)

    def test_04_e2e_render_lesson_script_with_ast_payload(self):
        """Runs render-lesson.py CLI end-to-end on a JSON file containing semantic AST nodes."""
        doc = LessonDocument(
            topic_id="topic.test.ast-e2e",
            title="E2E AST Document Test",
            subtitle="Testing seamless end-to-end AST compilation",
            tier="Tier 0 · Systems Core",
            cluster="Storage Architecture"
        )
        doc.add_section("The Core Dilemma", badge="Physical Dilemma")
        doc.add_lead("Opening narrative hook explaining physical memory constraints.")
        doc.add_paragraph(
            "When committing transactions, apps invoke {{jargon:fsync}} to persist data.",
            jargons={"fsync": {"term": "fsync()", "category": "POSIX Syscall", "definition": "Forces dirty pages to storage."}}
        )
        doc.add_dilemma(
            "Sync vs Async Writes",
            "A core latency trade-off:",
            [("Sync Writes", "10ms", "Direct disk flushes"), ("Async DRAM", "0.01ms", "Data loss risk")]
        )
        doc.add_section("Internal Mechanics", badge="Mechanics")
        doc.add_step_trace("Commit Trace", [("T0", "Client", "Send insert", "Enters queue"), ("T1", "WAL", "Append record", "Persisted")])
        doc.add_section("Sign-Off Verification", badge="Defense")
        doc.add_defense_challenge(
            "Torn Page Defense",
            "A power cut occurs midway through writing a 16KB page to disk.",
            [("Doublewrite", "Explain how MySQL uses doublewrite buffers to survive partial writes.")]
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            payload_path = os.path.join(tmpdir, "lesson-ast.json")
            with open(payload_path, "w", encoding="utf-8") as f:
                f.write(doc.to_json())

            render_script = os.path.join(SCRIPTS_DIR, "render-lesson.py")
            cmd = [
                sys.executable,
                render_script,
                "--topic-id", "topic.test.ast-e2e",
                "--data-file", payload_path,
                "--output-dir", tmpdir
            ]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertEqual(res.returncode, 0, f"render-lesson.py failed:\n{res.stderr}\n{res.stdout}")

            html_path = os.path.join(tmpdir, "test-ast-e2e.html")
            md_path = os.path.join(tmpdir, "test-ast-e2e.md")

            self.assertTrue(os.path.isfile(html_path), "HTML output artifact missing")
            self.assertFalse(os.path.isfile(md_path), "Markdown lesson file should not be emitted")

            with open(html_path, "r", encoding="utf-8") as hf:
                html_content = hf.read()

            # Verify HTML contains dynamic tabs and panes
            self.assertIn("section-tab-btn active", html_content)
            self.assertIn("data-target=\"the-core-dilemma\"", html_content)
            self.assertIn("pane-the-core-dilemma", html_content)
            self.assertIn("pane-internal-mechanics", html_content)
            self.assertIn("pane-sign-off-verification", html_content)
            self.assertIn("jargon-tooltip-wrapper", html_content)
            self.assertNotIn("{{SECTION_TABS_HTML}}", html_content)
            self.assertNotIn("{{SECTION_PANES_HTML}}", html_content)

            # Verify AST to_markdown compiles clean GFM with alert boxes and section glossary
            doc_md = doc.to_markdown()
            self.assertIn("# E2E AST Document Test", doc_md)
            self.assertIn("> [!WARNING] ⚡ Sync vs Async Writes", doc_md)
            self.assertIn("### ⏱️ Causal Execution Trace: Commit Trace", doc_md)
            self.assertIn("## 🛡️ Architectural Defense Challenge: Torn Page Defense", doc_md)
            self.assertIn("> 💡 **Jargon & Concepts Unpacked in this Section:**", doc_md)
            self.assertIn("> - **fsync()** *(POSIX Syscall)*: Forces dirty pages to storage.", doc_md)
            # Ensure no leaked raw HTML wrappers in Markdown
            self.assertNotIn("jargon-popover-card", doc_md)
            self.assertNotIn("onclick=\"toggleJargonTooltip", doc_md)


if __name__ == "__main__":
    unittest.main()
