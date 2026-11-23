#!/usr/bin/env python3
"""
test_note_builder_and_calculations.py
Unit and integration tests for NoteDocument AST container, dynamic note synthesis from lesson AST,
and reusable system design calculation functions.
"""

import os
import sys
import json
import tempfile
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "skills", "system-design-studio", "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from lesson_builder import (
    NoteDocument,
    LessonDocument,
    DilemmaNode,
    DefenseChallengeNode,
    ComparisonMatrixNode,
    FormulaNode,
    BreakthroughNode,
    calculate_bdp,
    calculate_quorum,
    calculate_disk_tps,
    calculate_littles_law,
    calculate_consistent_hash_migration,
    calculate_cache_sizing,
    calculate_token_bucket,
    calculate_bloom_filter,
)


class TestNoteDocumentAST(unittest.TestCase):
    def test_01_note_document_initialization_and_serialization(self):
        doc = NoteDocument(
            topic_id="topic.0.1.tcp-vs-udp",
            title="TCP vs UDP Transport Architecture",
            tier={"code": "0", "name": "Tier 0"},
            cluster={"code": "0.1", "title": "Network Transport"},
            hypothesis="Assumed TCP should universally back RPCs for reliability.",
            friction="- Model broke under trans-oceanic loss where HoL blocking stalled head requests.",
            derived_invariant="Packet boundaries must be decoupled from stream serialization.",
        )
        doc.add_rule(
            "Ordering vs Head-of-Line Blocking",
            "Use single-stream TCP for sequential order; switch to QUIC for concurrent multiplexing.",
            "BDP dictates socket buffer sizing.",
        )
        doc.add_formula(
            name="Bandwidth-Delay Product",
            formula=r"BDP = \text{Bandwidth} \times \text{RTT}",
            variables={"RTT": "Round-Trip Time", "Bandwidth": "Bottleneck link capacity"},
            implication="An unscaled 64KB window caps 10Gbps at 50ms RTT to ~10Mbps.",
        )
        doc.add_takeaway("Never assume zero-coordination coexists with monotonic ordering.")

        d = doc.to_dict()
        self.assertEqual(d["topic_id"], "topic.0.1.tcp-vs-udp")
        self.assertEqual(len(d["rules_of_thumb"]), 1)
        self.assertEqual(len(d["formulas"]), 1)
        self.assertEqual(len(d["takeaways"]), 1)

        # Roundtrip from_dict
        restored = NoteDocument.from_dict(d)
        self.assertEqual(restored.title, "TCP vs UDP Transport Architecture")
        self.assertEqual(restored.hypothesis, doc.hypothesis)
        self.assertEqual(len(restored.rules_of_thumb), 1)

    def test_02_note_document_markdown_rendering(self):
        doc = NoteDocument(
            topic_id="topic.0.1.raft",
            title="Raft Distributed Consensus",
            hypothesis="Assumed majority heartbeats alone prevent split-brain.",
            friction="- Asymmetric network partitions isolated the leader with stale leases.",
            derived_invariant="Any two majorities of size Q = floor(N/2) + 1 must overlap by at least one node.",
        )
        doc.add_rule(
            "Quorum Overlap",
            "Require 2Q > N for linearizable commits",
            "F = floor((N-1)/2) failures tolerated",
        )
        doc.add_formula(
            name="Majority Quorum Formula",
            formula=r"Q = \lfloor N/2 \rfloor + 1",
            implication="Even node counts add network cost with zero fault tolerance gain.",
        )
        doc.add_takeaway("Always favor odd node counts (3, 5, 7) for consensus clusters.")

        md = doc.to_markdown()
        self.assertIn("# Raft Distributed Consensus", md)
        self.assertIn("## 1. Initial Intuition & Working Hypothesis", md)
        self.assertIn("## 2. Dialectic & Friction Encountered", md)
        self.assertIn("## 3. Derived Invariant (The 'Aha!' Synthesis)", md)
        self.assertIn("## 4. Personal Rule of Thumb & Sizing Reality", md)
        self.assertIn("| **Quorum Overlap** | Require 2Q > N for linearizable commits |", md)
        self.assertIn("## 5. Mathematical & Physical Invariants", md)
        self.assertIn("### Majority Quorum Formula", md)
        self.assertIn("## 6. Production Takeaways & Heuristics", md)

    def test_03_note_document_dynamic_extraction_from_lesson_ast(self):
        # Build a sample LessonDocument with semantic AST nodes
        lesson = LessonDocument(
            title="Consistent Hashing & Storage Partitioning",
            subtitle="Ring Topology and Minimal Key Migration",
            topic_id="topic.1.2.consistent-hashing",
            tier_badge="Tier 1",
            cluster_badge="Storage Systems",
        )
        lesson.add(DilemmaNode(
            question="Why does hash(key) % N cause catastrophic migration cascades when scaling nodes?",
            concrete_impact="Adding 1 node to a 10-node cluster evicts 90% of cached keys."
        ))
        lesson.add(DefenseChallengeNode(
            title="Node Addition Cascade",
            scenario="Scale-out from 9 to 10 nodes under peak flash sale load",
            prompts=[("Impact", "Database backend overwhelmed by 90% cache eviction spike")]
        ))
        lesson.add(BreakthroughNode(
            title="Ring Locality Invariant",
            content="Mapping both keys and nodes to a circular hash space bounds migration to exactly K / (N + 1) keys."
        ))
        lesson.add(ComparisonMatrixNode(
            title="Modulo Hashing vs. Consistent Hashing",
            columns=["Dimension", "Modulo Hashing", "Consistent Hashing", "Trade-Off", "Production Verdict"],
            rows=[{
                "dimension": "Key Migration on Node Churn",
                "option_a": "O(K) ~ 90-99% keys moved",
                "option_b": "O(K/N) ~ exactly 1/N keys moved",
                "tradeoff": "Consistent hashing requires vnode maintenance",
                "verdict": "Mandatory for dynamic elasticity"
            }]
        ))
        lesson.add(FormulaNode(
            name="Consistent Hash Migration Bound",
            expression=r"\Delta K = \frac{K}{N + 1}",
            variables={"K": "Total active keys", "N": "Initial node count"},
            conclusion="Scaling from 9 to 10 nodes migrates exactly 10% of keys instead of 90%."
        ))

        # Dynamically synthesize NoteDocument from lesson AST
        note_doc = NoteDocument.from_lesson(lesson)

        self.assertEqual(note_doc.title, "Consistent Hashing & Storage Partitioning")
        self.assertIn("evicts 90% of cached keys", note_doc.hypothesis)
        self.assertIn("Scale-out from 9 to 10 nodes", note_doc.friction)
        self.assertIn("bounds migration to exactly K / (N + 1)", note_doc.derived_invariant)
        self.assertEqual(len(note_doc.rules_of_thumb), 1)
        self.assertEqual(len(note_doc.formulas), 1)
        self.assertEqual(note_doc.formulas[0]["name"], "Consistent Hash Migration Bound")

        # Compile to Markdown
        md = note_doc.to_markdown()
        self.assertIn("# Consistent Hashing & Storage Partitioning", md)
        self.assertIn("Key Migration on Node Churn", md)
        self.assertIn("Consistent Hash Migration Bound", md)


class TestSystemDesignCalculations(unittest.TestCase):
    def test_01_calculate_bdp(self):
        # 10 Gbps at 50ms RTT
        res = calculate_bdp(10000.0, 50.0)
        self.assertEqual(res["bdp_bytes"], 62500000)
        self.assertEqual(res["bdp_mb"], 59.6)
        self.assertTrue(res["window_scaling_required"])
        self.assertEqual(res["standard_tcp_window_cap_mbps"], 10.49)
        self.assertEqual(res["standard_window_efficiency_pct"], 0.1)

        # Low bandwidth / low RTT (no scaling needed)
        res_small = calculate_bdp(10.0, 10.0)
        self.assertFalse(res_small["window_scaling_required"])
        self.assertEqual(res_small["standard_tcp_window_cap_mbps"], 10.0)

    def test_02_calculate_quorum(self):
        # Odd node count: 5 nodes
        q5 = calculate_quorum(5)
        self.assertEqual(q5["majority_quorum"], 3)
        self.assertEqual(q5["fault_tolerance"], 2)
        self.assertFalse(q5["is_even"])
        self.assertEqual(q5["warning"], "")

        # Even node count: 4 nodes
        q4 = calculate_quorum(4)
        self.assertEqual(q4["majority_quorum"], 3)
        self.assertEqual(q4["fault_tolerance"], 1)
        self.assertTrue(q4["is_even"])
        self.assertIn("provides F=1 fault tolerance, which is identical to N=3 nodes", q4["warning"])

    def test_03_calculate_disk_tps(self):
        # HDD ~8ms seek + 4ms rotational
        hdd = calculate_disk_tps(seek_time_ms=8.0, rotational_latency_ms=4.16, transfer_time_ms=0.1)
        self.assertTrue(75 <= hdd["random_iops_ceiling"] <= 85)
        self.assertTrue(hdd["group_commit_50x_tps"] > 3500)

        # SSD ~0.1ms
        ssd = calculate_disk_tps(seek_time_ms=0.08, transfer_time_ms=0.02)
        self.assertEqual(ssd["random_iops_ceiling"], 10000)

    def test_04_calculate_littles_law(self):
        # 5,000 RPS at 20ms service time -> L = 5000 * 0.02 = 100 in-flight
        res = calculate_littles_law(5000.0, 20.0)
        self.assertEqual(res["concurrent_in_flight_requests"], 100.0)
        self.assertEqual(res["spike_scenarios"]["10x_latency"]["concurrent_requests"], 1000.0)
        self.assertEqual(res["spike_scenarios"]["50x_latency"]["concurrent_requests"], 5000.0)

    def test_05_calculate_consistent_hash_migration(self):
        # 1,000,000 keys across 9 nodes scaling to 10
        res = calculate_consistent_hash_migration(1000000, 9)
        self.assertEqual(res["consistent_hashing_keys_migrated"], 100000)
        self.assertEqual(res["consistent_hashing_pct_moved"], 10.0)
        self.assertEqual(res["modulo_hashing_keys_migrated"], 900000)
        self.assertEqual(res["modulo_hashing_pct_moved"], 90.0)
        self.assertEqual(res["unnecessary_migrations_prevented"], 800000)

    def test_06_calculate_cache_sizing(self):
        # 10M DAU, 20 reads/user, 10KB avg object size, 20% hot data
        res = calculate_cache_sizing(10000000, 20, 10.0, 0.2)
        self.assertEqual(res["total_daily_reads"], 200000000)
        self.assertTrue(2300 < res["avg_qps"] < 2320)
        self.assertTrue(res["working_set_ram_gb"] > 350)
        self.assertTrue(res["peak_egress_bandwidth_gbps"] > 0.3)

    def test_07_calculate_token_bucket(self):
        # 1000 capacity, 100 refill rate, 2 sec burst
        res = calculate_token_bucket(1000, 100.0, 2.0)
        self.assertEqual(res["max_burst_requests"], 1200)
        self.assertEqual(res["time_to_refill_from_empty_sec"], 10.0)

    def test_08_calculate_bloom_filter(self):
        # 1,000,000 items, 1% false positive
        res = calculate_bloom_filter(1000000, 0.01)
        self.assertEqual(res["optimal_hash_functions_k"], 7)
        self.assertTrue(9.5 < res["bits_per_item"] < 9.7)
        self.assertTrue(1.1 < res["memory_mb"] < 1.3)


class TestGenerateNotesScriptIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.instance_dir = os.path.join(self.temp_dir, ".system-design")
        os.makedirs(os.path.join(self.instance_dir, "lessons"), exist_ok=True)
        os.makedirs(os.path.join(self.temp_dir, "notes"), exist_ok=True)

        # Write sample manifest
        manifest = {
            "curriculum": {
                "clusters": [{
                    "id": "cluster.0.1",
                    "code": "0.1",
                    "title": "Network Transport",
                    "topics": [{
                        "id": "topic.0.1.tcp-vs-udp",
                        "title": "TCP vs UDP Transport",
                        "status": "delivered",
                        "lessonArtifact": "lessons/0-1-tcp-vs-udp.html"
                    }]
                }]
            }
        }
        with open(os.path.join(self.instance_dir, "manifest.json"), "w", encoding="utf-8") as f:
            json.dump(manifest, f)

    def test_01_generate_notes_cli_with_data_file(self):
        import subprocess

        # Author a sample note JSON
        note_doc = NoteDocument(
            topic_id="topic.0.1.tcp-vs-udp",
            title="TCP vs UDP Transport",
            hypothesis="Assumed TCP universally optimal for low-latency gaming and RPCs.",
            friction="- Discovered 1% packet loss triggers 500ms HOL blocking freeze.",
            derived_invariant="Multiplexed streams over UDP isolate loss domains completely.",
        )
        note_doc.add_rule(
            "Loss Recovery vs Head-of-Line Blocking",
            "Use QUIC/UDP when independent streams share link.",
            "BDP determines socket buffer allocation.",
        )
        data_path = os.path.join(self.temp_dir, "custom_note.json")
        note_doc.save(data_path)

        cmd = [
            sys.executable,
            os.path.join(SCRIPTS_DIR, "generate-notes.py"),
            "--instance-dir", self.instance_dir,
            "--topic-id", "topic.0.1.tcp-vs-udp",
            "--data-file", data_path,
            "--notes-dir", os.path.join(self.temp_dir, "notes"),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Error: {res.stderr}")
        self.assertIn("Study note compiled successfully", res.stdout)

        # Verify compiled note on disk
        expected_note = os.path.join(
            self.temp_dir, "notes", "tier-0", "cluster-0-1-network-transport", "0-1-tcp-vs-udp.md"
        )
        self.assertTrue(os.path.isfile(expected_note), f"File not found: {expected_note}")
        with open(expected_note, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("Assumed TCP universally optimal", content)
        self.assertIn("Loss Recovery vs Head-of-Line Blocking", content)

    def test_02_generate_notes_cli_auto_extract_from_lesson_on_disk(self):
        import subprocess

        # Save a lesson AST in .system-design/lessons/.generated-0-1-tcp-vs-udp.json
        lesson = LessonDocument(
            title="TCP vs UDP Transport",
            topic_id="topic.0.1.tcp-vs-udp",
            tier_badge="Tier 0",
            cluster_badge="Network Transport",
        )
        lesson.add(DilemmaNode(
            question="Why does standard TCP freeze all streams under packet loss?",
            concrete_impact="A single lost packet stalls all independent application requests."
        ))
        lesson.add(BreakthroughNode(
            title="Loss Domain Decoupling",
            content="QUIC maps byte offsets per stream, isolating loss recovery."
        ))
        lesson_file = os.path.join(self.instance_dir, "lessons", ".generated-0-1-tcp-vs-udp.json")
        lesson.save(lesson_file)

        # Run generate-notes WITHOUT --data-file: should auto-detect the lesson file
        cmd = [
            sys.executable,
            os.path.join(SCRIPTS_DIR, "generate-notes.py"),
            "--instance-dir", self.instance_dir,
            "--topic-id", "topic.0.1.tcp-vs-udp",
            "--notes-dir", os.path.join(self.temp_dir, "notes"),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Error: {res.stderr}")

        expected_note = os.path.join(
            self.temp_dir, "notes", "tier-0", "cluster-0-1-network-transport", "0-1-tcp-vs-udp.md"
        )
        with open(expected_note, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("A single lost packet stalls all independent application requests", content)
        self.assertIn("QUIC maps byte offsets per stream", content)


if __name__ == "__main__":
    unittest.main()
