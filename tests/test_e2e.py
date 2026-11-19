#!/usr/bin/env python3
"""
System Design Studio — Comprehensive End-to-End Test Suite.
Validates the entire product end-to-end across:
1. Multi-agent distribution & CLI generation (Antigravity, Claude, Cursor, Codex, Open Standard)
2. Multi-track project scaffolding (curated tracks + BYO syllabus)
3. Interactive lesson rendering across all 5 themes and dual HTML/Markdown formats
4. Learning lifecycle: topic completion, ADR logging, and cursor advancement
5. Study notes synthesis across all 4 modes (per-topic, per-cluster, per-tier, single-file)
6. Multi-project registry, active context switching, and note discovery
7. Safe project deletion, dry-runs, and workspace/home directory protection
8. Lossless settings migrations across schema versions
9. On-demand skill updater preserving project progress
10. Clean uninstallation strictly preserving user workspaces and notes
"""

import os
import sys
import json
import glob
import shutil
import tempfile
import subprocess
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "skills/system-design-studio/scripts")
RESOURCES_DIR = os.path.join(REPO_ROOT, "skills/system-design-studio/resources")

class SystemDesignStudioE2ETest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sandbox_dir = tempfile.mkdtemp(prefix="sds-e2e-sandbox-")
        cls.fake_home = os.path.join(cls.sandbox_dir, "fake_home")
        os.makedirs(cls.fake_home, exist_ok=True)
        
        cls.env = os.environ.copy()
        cls.env["HOME"] = cls.fake_home
        cls.env["CI"] = "true"
        cls.env["TERM"] = "dumb"

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.sandbox_dir, ignore_errors=True)

    def run_cmd(self, cmd_args, cwd=None, check=True):
        res = subprocess.run(
            cmd_args,
            cwd=cwd or self.sandbox_dir,
            env=self.env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if check and res.returncode != 0:
            raise RuntimeError(f"Command failed (exit {res.returncode}): {' '.join(cmd_args)}\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}")
        return res

    # =========================================================================
    # SUITE 1: Universal Multi-Agent Installer & CLI Verification
    # =========================================================================
    def test_01_installer_multi_agent_distribution(self):
        install_script = os.path.join(REPO_ROOT, "install.sh")
        res = self.run_cmd(["bash", install_script, "--all", "-y"])
        self.assertIn("System Design Studio skill installed across", res.stdout)

        # 1. Verify Google Antigravity, Claude, Cursor, Codex & Studio skills
        for agent_path in [
            os.path.join(self.fake_home, ".gemini/antigravity/skills"),
            os.path.join(self.fake_home, ".gemini/config/skills"),
            os.path.join(self.fake_home, ".agents/skills"),
            os.path.join(self.fake_home, ".claude/skills"),
            os.path.join(self.fake_home, ".cursor/skills"),
            os.path.join(self.fake_home, ".codex/skills"),
            os.path.join(self.fake_home, ".system-design-studio/skills")
        ]:
            self.assertTrue(os.path.isdir(agent_path), f"Missing target: {agent_path}")
            self.assertTrue(os.path.isfile(os.path.join(agent_path, "system-design-studio/SKILL.md")))
            for cmd in ["sds-status", "sds-teach", "sds-discuss", "sds-complete", "sds-notes",
                        "sds-projects", "sds-open", "sds-delete", "sds-curriculum", "sds-config", "sds-update"]:
                cmd_skill = os.path.join(agent_path, cmd, "SKILL.md")
                self.assertTrue(os.path.isfile(cmd_skill), f"Missing companion skill: {cmd_skill}")

        # 2. Verify Claude Code commands and Codex prompts
        for cmd in ["sds-status", "sds-teach", "sds-discuss", "sds-complete", "sds-notes",
                    "sds-projects", "sds-open", "sds-delete", "sds-curriculum", "sds-config", "sds-update"]:
            claude_cmd = os.path.join(self.fake_home, f".claude/commands/{cmd}.md")
            codex_prompt = os.path.join(self.fake_home, f".codex/prompts/{cmd}.md")
            self.assertTrue(os.path.isfile(claude_cmd), f"Missing Claude command: {claude_cmd}")
            self.assertTrue(os.path.isfile(codex_prompt), f"Missing Codex prompt: {codex_prompt}")

        # 3. Verify Subagents Distribution
        expected_subagents = ["sds-lesson-crafter", "sds-pedagogy-auditor", "sds-dialectic-challenger"]
        for agent_dir in [
            os.path.join(self.fake_home, ".gemini/antigravity/agents"),
            os.path.join(self.fake_home, ".gemini/config/agents"),
            os.path.join(self.fake_home, ".agents/agents"),
            os.path.join(self.fake_home, ".claude/agents"),
            os.path.join(self.fake_home, ".cursor/agents"),
            os.path.join(self.fake_home, ".codex/agents"),
            os.path.join(self.fake_home, ".system-design-studio/agents")
        ]:
            self.assertTrue(os.path.isdir(agent_dir), f"Missing agent target: {agent_dir}")
            for subagent in expected_subagents:
                has_md = os.path.isfile(os.path.join(agent_dir, f"{subagent}.md"))
                has_dir = os.path.isfile(os.path.join(agent_dir, subagent, "AGENT.md"))
                self.assertTrue(has_md or has_dir, f"Missing subagent {subagent} in {agent_dir}")

        # 4. Verify CLI wrapper & global config
        cli_bin = os.path.join(self.fake_home, ".system-design-studio/bin/sds")
        global_config = os.path.join(self.fake_home, ".system-design-studio/config.json")
        self.assertTrue(os.path.isfile(cli_bin))
        self.assertTrue(os.access(cli_bin, os.X_OK))
        with open(cli_bin, "r", encoding="utf-8") as f:
            cli_content = f.read()
        self.assertIn("revisions|revision|rev)", cli_content)
        self.assertIn("update-revisions.py", cli_content)
        self.assertTrue(os.path.isfile(global_config))

        # 5. Verify plugin.json manifest
        plugin_file = os.path.join(REPO_ROOT, "plugin.json")
        with open(plugin_file, "r", encoding="utf-8") as f:
            plugin_data = json.load(f)
        self.assertIn("agents", plugin_data)
        self.assertEqual(plugin_data["agents"], "./agents")

    # =========================================================================
    # SUITE 2: Multi-Track Scaffolding & Verification
    # =========================================================================
    def test_02_scaffolding_and_verification(self):
        init_script = os.path.join(SCRIPTS_DIR, "init-learning-instance.sh")
        verify_script = os.path.join(SCRIPTS_DIR, "verify-instance.py")

        # Project 1: interview-sprint
        proj1_dir = os.path.join(self.sandbox_dir, "proj1-interview")
        os.makedirs(proj1_dir, exist_ok=True)
        res1 = self.run_cmd([
            "bash", init_script,
            "--name", "Interview Sprint Lab",
            "--id", "interview-lab",
            "--path", proj1_dir,
            "--track", "interview-sprint",
            "--theme", "nordic-frost",
            "--output", "html",
            "-y"
        ])
        self.assertIn("Project Initialized Successfully!", res1.stdout)
        
        v_res1 = self.run_cmd([sys.executable, verify_script, os.path.join(proj1_dir, ".system-design")])
        self.assertIn("PASSED with 0 errors", v_res1.stdout)
        self.assertIn("15 clusters", v_res1.stdout)

        # Project 2: full-mastery with per-cluster notes
        proj2_dir = os.path.join(self.sandbox_dir, "proj2-mastery")
        os.makedirs(proj2_dir, exist_ok=True)
        res2 = self.run_cmd([
            "bash", init_script,
            "--name", "Full Mastery Core",
            "--id", "full-mastery-core",
            "--path", proj2_dir,
            "--track", "full-mastery",
            "--notes-structure", "per-cluster",
            "--theme", "midnight-neon",
            "-y"
        ])
        self.assertIn("Project Initialized Successfully!", res2.stdout)
        v_res2 = self.run_cmd([sys.executable, verify_script, os.path.join(proj2_dir, ".system-design")])
        self.assertIn("PASSED with 0 errors", v_res2.stdout)
        self.assertIn("50 clusters", v_res2.stdout)

        # Project 3: BYO Custom Syllabus
        proj3_dir = os.path.join(self.sandbox_dir, "proj3-byo")
        os.makedirs(proj3_dir, exist_ok=True)
        custom_md = os.path.join(RESOURCES_DIR, "custom-curriculum-example.md")
        res3 = self.run_cmd([
            "bash", init_script,
            "--name", "Custom Trading Architecture",
            "--id", "trading-byo",
            "--path", proj3_dir,
            "--byo", custom_md,
            "-y"
        ])
        self.assertIn("Project Initialized Successfully!", res3.stdout)
        v_res3 = self.run_cmd([sys.executable, verify_script, os.path.join(proj3_dir, ".system-design")])
        self.assertIn("PASSED with 0 errors", v_res3.stdout)

    # =========================================================================
    # SUITE 3: Interactive Lesson Generation (HTML & Markdown across 5 Themes)
    # =========================================================================
    def test_03_lesson_rendering_themes_and_formats(self):
        render_script = os.path.join(SCRIPTS_DIR, "render-lesson.py")
        proj1_inst = os.path.join(self.sandbox_dir, "proj1-interview/.system-design")

        # 1. Test all 5 themes in HTML mode
        themes = ["slate-clean", "editorial-paper", "midnight-neon", "nordic-frost", "warm-amber"]
        for theme in themes:
            res = self.run_cmd([
                sys.executable, render_script,
                "--topic-id", "topic.0.1.tcp-vs-udp",
                "--instance-dir", proj1_inst,
                "--style", theme,
                "--format", "html"
            ])
            self.assertIn("Lesson rendered to", res.stdout)
            html_file = os.path.join(proj1_inst, "lessons/0-1-tcp-vs-udp.html")
            self.assertTrue(os.path.isfile(html_file))
            with open(html_file, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("<!DOCTYPE html>", content)
            self.assertIn("network-pipe", content)
            self.assertIn("TCP vs UDP", content)
            self.assertIn("--background:", content)

        # 2. Test Markdown mode
        res_md = self.run_cmd([
            sys.executable, render_script,
            "--topic-id", "topic.0.1.tcp-vs-udp",
            "--instance-dir", proj1_inst,
            "--format", "markdown"
        ])
        self.assertIn("Format: Markdown Clean", res_md.stdout)
        md_file = os.path.join(proj1_inst, "lessons/0-1-tcp-vs-udp.md")
        self.assertTrue(os.path.isfile(md_file))
        with open(md_file, "r", encoding="utf-8") as f:
            md_content = f.read()
        self.assertIn("# TCP vs UDP", md_content)
        self.assertIn("```mermaid", md_content)
        self.assertNotIn("<!DOCTYPE html>", md_content)

    # =========================================================================
    # SUITE 4: Learning Lifecycle (Advance Cursor, Sync Status, Notes & ADRs)
    # =========================================================================
    def test_04_learning_lifecycle_advancement(self):
        advance_script = os.path.join(SCRIPTS_DIR, "advance-cursor.py")
        sync_script = os.path.join(SCRIPTS_DIR, "sync-status.py")
        proj1_dir = os.path.join(self.sandbox_dir, "proj1-interview")
        proj1_inst = os.path.join(proj1_dir, ".system-design")

        # 1. Advance Topic 1
        res = self.run_cmd([
            sys.executable, advance_script,
            "--instance-dir", proj1_inst,
            "--complete-topic", "topic.0.1.tcp-vs-udp",
            "--evidence", "Learner proved TCP head-of-line blocking under 5% packet loss cold in chat.",
            "--hypothesis", "Assumed TCP always optimal for critical RPCs regardless of packet loss boundaries.",
            "--discussion-summary", "Evaluated socket buffer HOL blocking under packet drop and derived tail latency multiplier.",
            "--log-example-domain", "Payment Gateway",
            "--log-example-scenario", "Real-time webhook notification retry and backoff",
            "--log-example-tradeoffs", "TCP buffer stalls vs UDP uncoordinated retransmit overhead",
            "--defer-topic", "QUIC 0-RTT replay attack mitigations",
            "--defer-target-cluster", "cluster.0.2",
            "--defer-anchor-note", "Deferred until TLS 1.3 key derivation is studied",
            "--next-topic-id", "topic.0.1.http-1-1-vs-http-2-vs-http-3",
            "--next-action", "Analyze HTTP/2 stream multiplexing and HPACK header compression"
        ])
        self.assertIn("Cursor advanced!", res.stdout)

        # 2. Verify CURRICULUM.md has checkbox marked
        curriculum_file = os.path.join(proj1_inst, "CURRICULUM.md")
        with open(curriculum_file, "r", encoding="utf-8") as f:
            c_text = f.read()
        self.assertIn("- [x]  TCP vs UDP", c_text)

        # 3. Verify CURSOR.md active topic changed and contains anchors
        cursor_file = os.path.join(proj1_inst, "CURSOR.md")
        with open(cursor_file, "r", encoding="utf-8") as f:
            cur_text = f.read()
        self.assertIn("HTTP/1.1 vs HTTP/2 vs HTTP/3", cur_text)
        self.assertIn("Payment Gateway", cur_text)
        self.assertIn("QUIC 0-RTT replay attack mitigations", cur_text)

        # 4. Verify DECISIONS.md has ADR-001
        decisions_file = os.path.join(proj1_inst, "DECISIONS.md")
        self.assertTrue(os.path.isfile(decisions_file))
        with open(decisions_file, "r", encoding="utf-8") as f:
            dec_text = f.read()
        self.assertIn("ADR-001", dec_text)
        self.assertIn("TCP vs UDP Architectural Defense", dec_text)

        # 5. Verify Note was generated in per-topic structure
        matches = glob.glob(os.path.join(proj1_dir, "notes/**/0-1-tcp-vs-udp.md"), recursive=True)
        self.assertTrue(len(matches) > 0, f"Notes file not found under {proj1_dir}/notes")
        notes_file = matches[0]
        with open(notes_file, "r", encoding="utf-8") as f:
            note_text = f.read()
        self.assertIn("TCP vs UDP", note_text)
        self.assertIn("1. Initial Intuition & Working Hypothesis", note_text)
        self.assertIn("2. Dialectic & Friction Encountered", note_text)
        self.assertIn("3. Derived Invariant", note_text)
        self.assertIn("4. Personal Rule of Thumb & Sizing Reality", note_text)

        # 6. Verify sync-status reports correct telemetry
        sync_res = self.run_cmd([sys.executable, sync_script, proj1_inst])
        self.assertIn("SYSTEM DESIGN STUDIO — INSTANCE DIAGNOSTIC", sync_res.stdout)
        self.assertIn("Active Topic:    HTTP/1.1 vs HTTP/2 vs HTTP/3", sync_res.stdout)
        self.assertIn("Overall Progress: 1 / 114 Topics", sync_res.stdout)
        self.assertIn("Payment Gateway", sync_res.stdout)
        self.assertIn("QUIC 0-RTT replay attack mitigations", sync_res.stdout)

        # 7. Test Auto-Advancement within cluster when --next-topic-id is omitted
        auto_adv_res = self.run_cmd([
            sys.executable, advance_script,
            "--instance-dir", proj1_inst,
            "--complete-topic", "topic.0.1.http-1-1-vs-http-2-vs-http-3",
            "--evidence", "Learner proved stream multiplexing benefits cold."
        ])
        self.assertIn("Cursor advanced!", auto_adv_res.stdout)

        with open(os.path.join(proj1_inst, "manifest.json"), "r", encoding="utf-8") as mf:
            m_data = json.load(mf)
        # Next uncompleted topic in cluster 0.1 is topic.0.1.tls-handshake-cost-and-session-resumptio
        self.assertEqual(m_data["curriculum"]["activeTopicId"], "topic.0.1.tls-handshake-cost-and-session-resumptio")
        self.assertEqual(m_data["curriculum"]["activeClusterId"], "cluster.0.1")
        self.assertEqual(m_data["cursor"]["topicFoundationId"], "foundation.0.1.tls-handshake-cost-and-session-resumptio")
        self.assertEqual(m_data["cursor"]["activeMechanismGroupId"], "group.0.1.tls-handshake-cost-and-session-resumptio")

        # Verify CURSOR.md was re-rendered with new active topic
        with open(cursor_file, "r", encoding="utf-8") as f:
            cur_text2 = f.read()
        self.assertIn("**Active Topic**: **TLS handshake cost and session resumption**", cur_text2)
        self.assertIn("`topic.0.1.tls-handshake-cost-and-session-resumptio`", cur_text2)
        self.assertIn("- [x] **TCP vs UDP**", cur_text2)
        self.assertIn("- [x] **HTTP/1.1 vs HTTP/2 vs HTTP/3**", cur_text2)
        self.assertIn("- [ ] **CURRENT** ➔ **TLS handshake cost and session resumption**", cur_text2)

        # 8. Test Auto-Advancement across cluster boundaries when all topics in current cluster complete
        # Complete all remaining topics in cluster 0.1 except the last one
        last_t_id = m_data["curriculum"]["clusters"][0]["topics"][-1]["id"]
        for t in m_data["curriculum"]["clusters"][0]["topics"]:
            if t["id"] != last_t_id:
                t["status"] = "completed"
        with open(os.path.join(proj1_inst, "manifest.json"), "w", encoding="utf-8") as mf:
            json.dump(m_data, mf, indent=2)

        # Complete the final topic of cluster 0.1 without --next-topic-id
        last_t_res = self.run_cmd([
            sys.executable, advance_script,
            "--instance-dir", proj1_inst,
            "--complete-topic", last_t_id
        ])
        self.assertIn("Cursor advanced!", last_t_res.stdout)

        with open(os.path.join(proj1_inst, "manifest.json"), "r", encoding="utf-8") as mf:
            m_data_c02 = json.load(mf)
        # Cluster 0.1 is 100% completed; must advance to cluster 0.2's first topic (b-tree-index)
        self.assertEqual(m_data_c02["curriculum"]["activeClusterId"], "cluster.0.2")
        self.assertEqual(m_data_c02["curriculum"]["activeTopicId"], "topic.0.2.b-tree-index")
        self.assertEqual(m_data_c02["cursor"]["topicFoundationId"], "foundation.0.2.b-tree-index")
        self.assertEqual(m_data_c02["cursor"]["activeMechanismGroupId"], "group.0.2.b-tree-index")

    # =========================================================================
    # SUITE 5: Study Notes Compilation Modes (per-cluster, per-tier, single-file)
    # =========================================================================
    def test_05_notes_structuring_modes(self):
        gen_notes_script = os.path.join(SCRIPTS_DIR, "generate-notes.py")

        # Test per-cluster mode
        proj2_dir = os.path.join(self.sandbox_dir, "proj2-mastery")
        proj2_inst = os.path.join(proj2_dir, ".system-design")
        res_cluster = self.run_cmd([
            sys.executable, gen_notes_script,
            "--instance-dir", proj2_inst,
            "--topic-id", "topic.0.1.tcp-vs-udp",
            "--evidence", "Cold defense proof",
            "--hypothesis", "Naive model hypothesis",
            "--discussion-summary", "Stress testing round"
        ])
        self.assertIn("Study note compiled successfully", res_cluster.stdout)
        c_matches = glob.glob(os.path.join(proj2_dir, "notes/tier-0/cluster-*.md"))
        self.assertTrue(len(c_matches) > 0, "No cluster note found")

        # Test per-tier mode
        settings_file = os.path.join(proj2_inst, "settings.json")
        with open(settings_file, "r", encoding="utf-8") as f:
            s_data = json.load(f)
        s_data["notesStructure"] = "per-tier"
        with open(settings_file, "w", encoding="utf-8") as f:
            json.dump(s_data, f, indent=2)

        res_tier = self.run_cmd([
            sys.executable, gen_notes_script,
            "--instance-dir", proj2_inst,
            "--topic-id", "topic.0.1.tcp-vs-udp",
            "--evidence", "Cold defense tier proof"
        ])
        tier_note = os.path.join(proj2_dir, "notes/tier-0.md")
        self.assertTrue(os.path.isfile(tier_note))

        # Test single-file mode
        s_data["notesStructure"] = "single-file"
        with open(settings_file, "w", encoding="utf-8") as f:
            json.dump(s_data, f, indent=2)

        res_single = self.run_cmd([
            sys.executable, gen_notes_script,
            "--instance-dir", proj2_inst,
            "--topic-id", "topic.0.1.tcp-vs-udp",
            "--evidence", "Master file proof"
        ])
        single_note = os.path.join(proj2_dir, "notes/SYSTEM-DESIGN-NOTES.md")
        self.assertTrue(os.path.isfile(single_note))

    # =========================================================================
    # SUITE 6: Multi-Project Registry, Context Switching & Notes Listing
    # =========================================================================
    def test_06_multi_project_management(self):
        manage_script = os.path.join(SCRIPTS_DIR, "manage-projects.py")

        # 1. List projects
        list_res = self.run_cmd([sys.executable, manage_script, "list"])
        self.assertIn("interview-lab", list_res.stdout)
        self.assertIn("full-mastery-core", list_res.stdout)
        self.assertIn("trading-byo", list_res.stdout)

        # 2a. Switch active project via exact match
        switch_res = self.run_cmd([sys.executable, manage_script, "switch", "interview-lab"])
        self.assertIn("Switched active project to 'interview-lab'", switch_res.stdout)

        active_res = self.run_cmd([sys.executable, manage_script, "active"])
        self.assertIn("interview-lab", active_res.stdout)

        # 2b. Switch active project via case-insensitive ID match
        switch_res2 = self.run_cmd([sys.executable, manage_script, "switch", "FULL-MASTERY-CORE"])
        self.assertIn("Switched active project to 'full-mastery-core'", switch_res2.stdout)

        # 2c. Switch active project via project name
        switch_res3 = self.run_cmd([sys.executable, manage_script, "switch", "Interview Sprint Lab"])
        self.assertIn("Switched active project to 'interview-lab'", switch_res3.stdout)

        # 2d. Switch active project via directory basename
        switch_res4 = self.run_cmd([sys.executable, manage_script, "switch", "proj2-mastery"])
        self.assertIn("Switched active project to 'full-mastery-core'", switch_res4.stdout)

        # Switch back to interview-lab for notes test
        self.run_cmd([sys.executable, manage_script, "switch", "interview-lab"])

        # 3. List notes for active project
        notes_res = self.run_cmd([sys.executable, manage_script, "notes"])
        self.assertIn("0-1-tcp-vs-udp.md", notes_res.stdout)

    # =========================================================================
    # SUITE 7: Safe Deletion, Dry-Run & Home/Workspace Protection Invariants
    # =========================================================================
    def test_07_safe_project_deletion_and_guardrails(self):
        manage_script = os.path.join(SCRIPTS_DIR, "manage-projects.py")
        proj1_dir = os.path.join(self.sandbox_dir, "proj1-interview")
        proj1_notes = os.path.join(proj1_dir, "notes")

        # Create dummy user workspace source files that must NEVER be touched
        user_source_file = os.path.join(proj1_dir, "src/server.go")
        os.makedirs(os.path.dirname(user_source_file), exist_ok=True)
        with open(user_source_file, "w") as f:
            f.write("// Custom user server code")

        # 1. Test Dry Run
        dry_res = self.run_cmd([sys.executable, manage_script, "delete", "--dry-run", "interview-lab"])
        self.assertIn("DRY RUN — DELETE PROJECT: interview-lab", dry_res.stdout)
        self.assertIn(f"Workspace Folder: PRESERVED ({proj1_dir})", dry_res.stdout)
        self.assertIn(f"Study Notes:      PRESERVED ({proj1_notes})", dry_res.stdout)
        self.assertTrue(os.path.isdir(os.path.join(proj1_dir, ".system-design")))

        # 2. Test Deletion preserving workspace & notes by default
        del_res = self.run_cmd([sys.executable, manage_script, "delete", "-f", "interview-lab"])
        self.assertIn("Successfully deleted project 'interview-lab'", del_res.stdout)
        self.assertIn("Active project switched to", del_res.stdout)

        # Verify .system-design is gone
        self.assertFalse(os.path.isdir(os.path.join(proj1_dir, ".system-design")))
        # Invariant: User source files strictly kept
        self.assertTrue(os.path.isfile(user_source_file))
        # Invariant: User notes strictly kept
        self.assertTrue(os.path.isdir(proj1_notes))

        # 3. Test Deletion with --delete-notes on Project 3
        proj3_dir = os.path.join(self.sandbox_dir, "proj3-byo")
        del3_res = self.run_cmd([sys.executable, manage_script, "delete", "-f", "--delete-notes", "trading-byo"])
        self.assertIn("Successfully deleted project 'trading-byo'", del3_res.stdout)
        self.assertFalse(os.path.isdir(os.path.join(proj3_dir, ".system-design")))

    # =========================================================================
    # SUITE 8: Lossless Settings Migration
    # =========================================================================
    def test_08_lossless_settings_migration(self):
        merge_script = os.path.join(SCRIPTS_DIR, "merge-settings.py")
        proj2_inst = os.path.join(self.sandbox_dir, "proj2-mastery/.system-design")
        settings_file = os.path.join(proj2_inst, "settings.json")

        # Set custom settings
        with open(settings_file, "w", encoding="utf-8") as f:
            json.dump({
                "schemaVersion": "1.0.0",
                "artifactStyle": "nordic-frost",
                "customUserKey": "custom-value-preserved"
            }, f, indent=2)

        res = self.run_cmd([
            sys.executable, merge_script,
            "--instance-dir", proj2_inst,
            "--defaults", os.path.join(RESOURCES_DIR, "settings-template.json")
        ])
        self.assertIn("Settings merged successfully", res.stdout)

        with open(settings_file, "r", encoding="utf-8") as f:
            merged = json.load(f)
        # Customizations preserved
        self.assertEqual(merged["artifactStyle"], "nordic-frost")
        self.assertEqual(merged["customUserKey"], "custom-value-preserved")
        # New defaults safely merged
        self.assertIn("outputType", merged)
        self.assertIn("notesStructure", merged)

    # =========================================================================
    # SUITE 8B: Revision Mode Engine & Auto-Sync
    # =========================================================================
    def test_08b_revision_mode_engine(self):
        rev_script = os.path.join(SCRIPTS_DIR, "update-revisions.py")
        proj2_inst = os.path.join(self.sandbox_dir, "proj2-mastery/.system-design")

        # 1. Test compilation and sync of revisions
        res = self.run_cmd([sys.executable, rev_script, "--instance-dir", proj2_inst, "--sync"])
        self.assertIn("SYSTEM DESIGN STUDIO — REVISION MODE SYNC", res.stdout)
        self.assertIn("Total Flashcards:", res.stdout)

        revisions_file = os.path.join(proj2_inst, "revisions.json")
        self.assertTrue(os.path.isfile(revisions_file))
        with open(revisions_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertGreater(data.get("totalRevisions", 0), 0)
        revisions = data.get("revisions", [])
        first_rev = revisions[0]
        self.assertIn("invariant", first_rev)
        self.assertIn("failureBoundary", first_rev)
        self.assertIn("defenseAnswer", first_rev)

        # 2. Test updating mastery status via CLI
        target_id = first_rev["id"]
        res_mastery = self.run_cmd([sys.executable, rev_script, "--instance-dir", proj2_inst, "--update-mastery", target_id, "mastered"])
        self.assertIn(f"Updated {target_id} status to 'mastered'", res_mastery.stdout)

        with open(revisions_file, "r", encoding="utf-8") as f:
            data_updated = json.load(f)
        matching = next((r for r in data_updated.get("revisions", []) if r["id"] == target_id), None)
        self.assertIsNotNone(matching)
        self.assertEqual(matching["masteryStatus"], "mastered")

    # =========================================================================
    # SUITE 8C: Dashboard-First Read-Write Workbench & Local Sync
    # =========================================================================
    def test_08c_dashboard_first_read_write_workbench(self):
        import urllib.request
        import urllib.error
        import time

        dashboard_script = os.path.join(SCRIPTS_DIR, "serve-dashboard.py")
        proj2_dir = os.path.join(self.sandbox_dir, "proj2-mastery")
        proj2_inst = os.path.join(proj2_dir, ".system-design")

        # Find free port
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1', 0))
            test_port = s.getsockname()[1]

        # Launch dashboard in background subprocess
        proc = subprocess.Popen(
            [sys.executable, dashboard_script, "--instance-dir", proj2_inst, "--port", str(test_port), "--no-browser"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        base_url = f"http://127.0.0.1:{test_port}"
        # Wait for server to listen
        ready = False
        for _ in range(30):
            try:
                with urllib.request.urlopen(f"{base_url}/api/status", timeout=1.0) as resp:
                    if resp.status == 200:
                        ready = True
                        break
            except Exception:
                time.sleep(0.15)

        self.assertTrue(ready, "Dashboard server failed to start within timeout")

        try:
            # 1. Test GET / (HTML App)
            with urllib.request.urlopen(f"{base_url}/", timeout=2.0) as resp:
                self.assertEqual(resp.status, 200)
                html = resp.read().decode("utf-8")
                self.assertIn("System Design Studio", html)
                self.assertIn("Revision Mode", html)
                self.assertIn("Curriculum Syllabus", html)

            # 2. Test GET /api/status
            with urllib.request.urlopen(f"{base_url}/api/status", timeout=2.0) as resp:
                self.assertEqual(resp.status, 200)
                status_data = json.loads(resp.read().decode("utf-8"))
                self.assertIn("manifest", status_data)
                self.assertIn("git", status_data)

            # 3. Test GET /api/projects
            with urllib.request.urlopen(f"{base_url}/api/projects", timeout=2.0) as resp:
                self.assertEqual(resp.status, 200)
                proj_data = json.loads(resp.read().decode("utf-8"))
                self.assertIn("projects", proj_data)

            # 4. Test POST /api/topic/status (Read-Write: set topic to in_progress)
            req_data = json.dumps({"topicId": "topic.0.1.tcp-vs-udp", "status": "in_progress"}).encode("utf-8")
            req = urllib.request.Request(f"{base_url}/api/topic/status", data=req_data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                self.assertEqual(resp.status, 200)
                res_json = json.loads(resp.read().decode("utf-8"))
                self.assertEqual(res_json["state"], "in_progress")

            # Verify manifest updated on disk
            manifest_file = os.path.join(proj2_inst, "manifest.json")
            with open(manifest_file, "r", encoding="utf-8") as mf:
                m_disk = json.load(mf)
            self.assertEqual(m_disk["curriculum"]["activeTopicId"], "topic.0.1.tcp-vs-udp")

            # 5. Test POST /api/topic/status (Read-Write: complete topic with ADR defense)
            req_complete = json.dumps({
                "topicId": "topic.0.1.tcp-vs-udp",
                "status": "completed",
                "evidence": "TCP monotonic in-order byte stream verified against HoL blocking cold in chat",
                "hypothesis": "Assumed HTTP/2 multiplexing avoids packet loss delays",
                "discussion_summary": "Evaluated kernel TCP receive buffer stall under 1% loss"
            }).encode("utf-8")
            req = urllib.request.Request(f"{base_url}/api/topic/status", data=req_complete, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                self.assertEqual(resp.status, 200)

            # Verify DECISIONS.md updated on disk
            decisions_file = os.path.join(proj2_inst, "DECISIONS.md")
            with open(decisions_file, "r", encoding="utf-8") as df:
                dec_content = df.read()
            self.assertIn("ADR-001: TCP vs UDP Architectural Defense", dec_content)
            self.assertIn("TCP monotonic in-order byte stream verified against HoL blocking cold in chat", dec_content)

            # 6. Test Notes API (Read & Write)
            new_note = json.dumps({
                "path": "test-cluster/dashboard-note.md",
                "content": "# Live Dashboard Note\n\n- Invariant: Verified without dedicated server\n"
            }).encode("utf-8")
            req = urllib.request.Request(f"{base_url}/api/note", data=new_note, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                self.assertEqual(resp.status, 200)

            note_file = os.path.join(proj2_dir, "notes/test-cluster/dashboard-note.md")
            self.assertTrue(os.path.isfile(note_file))
            with open(note_file, "r", encoding="utf-8") as nf:
                self.assertIn("Live Dashboard Note", nf.read())

            # 7. Test Settings API (Read & Write)
            new_settings = json.dumps({
                "artifactStyle": "cyber-obsidian",
                "notesStructure": "per-cluster",
                "notesDir": "study-notes"
            }).encode("utf-8")
            req = urllib.request.Request(f"{base_url}/api/settings", data=new_settings, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                self.assertEqual(resp.status, 200)

            settings_file = os.path.join(proj2_inst, "settings.json")
            with open(settings_file, "r", encoding="utf-8") as sf:
                s_disk = json.load(sf)
            self.assertEqual(s_disk["artifactStyle"], "cyber-obsidian")
            self.assertEqual(s_disk["notesStructure"], "per-cluster")

            # 8. Test Unified Highlights API (No external server required)
            hl_data = json.dumps([{"id": "hl_1", "color": "yellow", "text": "TCP in-order stream"}]).encode("utf-8")
            req = urllib.request.Request(f"{base_url}/api/highlights?artifact=test-lesson.html", data=hl_data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                self.assertEqual(resp.status, 200)

            with urllib.request.urlopen(f"{base_url}/api/highlights?artifact=test-lesson.html", timeout=2.0) as resp:
                self.assertEqual(resp.status, 200)
                hl_read = json.loads(resp.read().decode("utf-8"))
                self.assertEqual(len(hl_read), 1)
                self.assertEqual(hl_read[0]["text"], "TCP in-order stream")

            # 9. Test Revisions API (GET & POST)
            with urllib.request.urlopen(f"{base_url}/api/revisions", timeout=2.0) as resp:
                self.assertEqual(resp.status, 200)
                revs = json.loads(resp.read().decode("utf-8"))
                self.assertIn("revisions", revs)

        finally:
            proc.terminate()
            try:
                proc.wait(timeout=3.0)
            except Exception:
                proc.kill()
            if proc.stdout: proc.stdout.close()
            if proc.stderr: proc.stderr.close()

    # =========================================================================
    # SUITE 8D: Revamped Docs Landing Page & Contrast Validation
    # =========================================================================
    def test_08d_docs_landing_page_revamp_and_contrast(self):
        index_path = os.path.join(REPO_ROOT, "docs/index.html")
        self.assertTrue(os.path.isfile(index_path))

        with open(index_path, "r", encoding="utf-8") as f:
            html = f.read()

        # 1. Invariant: Internal script leaks are removed from product page
        self.assertNotIn("➔ render-lesson.py", html)
        self.assertNotIn("➔ advance-cursor.py", html)
        self.assertNotIn("➔ sync-status.py", html)
        self.assertNotIn("➔ git-checkpoint.py", html)
        self.assertNotIn("➔ manage-projects.py", html)

        # 2. Invariant: Unintimidating single-command quickstart is prominent
        self.assertIn("curl -fsSL https://raw.githubusercontent.com/alph-a07/system-design-studio/main/install.sh | bash", html)

        # 3. Invariant: High-value features are proudly displayed
        self.assertIn("Live Studio Dashboard", html)
        self.assertIn("Interactive Failure Simulators", html)
        self.assertIn("Revision Mode &amp; Invariants", html)
        self.assertIn("Socratic Trade-Off Defense", html)
        self.assertIn("Study Notes &amp; Live Editor", html)
        self.assertIn("Reader Mode &amp; Highlighting", html)

        # 4. Invariant: Dark & Light mode toggle and flawless contrast principles
        self.assertIn("toggleDarkMode()", html)
        self.assertIn("contrast", html)
        # Ensure yellow containers don't have white text (contrast failure check)
        self.assertNotIn("bg-primary-container text-white", html)
        # Ensure text-surface-dim is not used inside dark cards (WCAG AA contrast fix)
        self.assertNotIn("text-surface-dim", html)

        # 5. Invariant: CSS Secondary token passes >= 4.5:1 WCAG AA contrast for regular text
        styles_path = os.path.join(REPO_ROOT, "docs/styles.css")
        with open(styles_path, "r", encoding="utf-8") as sf:
            styles = sf.read()
        self.assertIn("--secondary: #dc2626;", styles)
        self.assertIn("background-color: #dc2626 !important;", styles)

        # 6. Invariant: Navigation links in curriculum.html are not broken
        curr_html_path = os.path.join(REPO_ROOT, "docs/curriculum.html")
        with open(curr_html_path, "r", encoding="utf-8") as cf:
            curr_html = cf.read()
        self.assertNotIn("#commands", curr_html)
        self.assertNotIn("#themes", curr_html)
        self.assertIn("href=\"index.html#dashboard\"", curr_html)
        self.assertIn("href=\"index.html#features\"", curr_html)

    # =========================================================================
    # SUITE 9: On-Demand Skill Updater
    # =========================================================================
    def test_09_ondemand_updater(self):
        update_script = os.path.join(REPO_ROOT, "update.sh")
        nested_update_script = os.path.join(SCRIPTS_DIR, "update.sh")
        proj2_inst = os.path.join(self.sandbox_dir, "proj2-mastery/.system-design")

        # Test root update.sh with space-separated argument
        res = self.run_cmd(["sh", update_script, "--instance-dir", proj2_inst])
        self.assertIn("System Design Studio updated across", res.stdout)
        self.assertIn("All learning progress and custom user settings were preserved", res.stdout)

        # Test nested update.sh with equals-separated argument
        res2 = self.run_cmd(["sh", nested_update_script, f"--instance-dir={proj2_inst}"])
        self.assertIn("System Design Studio updated across", res2.stdout)

    # =========================================================================
    # SUITE 10: Checkpoint, Rollback & Project-Scoped Curriculum
    # =========================================================================
    def test_10_checkpoint_rollback_and_dashboard(self):
        cp_script = os.path.join(SCRIPTS_DIR, "git-checkpoint.py")
        proj2_dir = os.path.join(self.sandbox_dir, "proj2-mastery")
        proj2_inst = os.path.join(proj2_dir, ".system-design")

        # 1. Test local snapshot creation
        c_res = self.run_cmd([
            sys.executable, cp_script,
            "commit",
            "--instance-dir", proj2_inst,
            "--type", "learn",
            "--subject", "complete 0.1 TCP vs UDP [verified]"
        ])
        self.assertIn("Local snapshot created", c_res.stdout)

        # 2. Test listing checkpoints
        l_res = self.run_cmd([sys.executable, cp_script, "list", "--instance-dir", proj2_inst])
        self.assertIn("sds(learn)", l_res.stdout)
        self.assertIn("complete 0.1 TCP vs UDP [verified]", l_res.stdout)

        # 3. Test rollback
        r_res = self.run_cmd([
            sys.executable, cp_script,
            "rollback",
            "--instance-dir", proj2_inst,
            "--steps", "0"
        ])
        self.assertIn("Successfully restored state to checkpoint", r_res.stdout)

        # 4. Test project-scoped curriculum reconfiguration with progress preservation
        cfg_curric_script = os.path.join(SCRIPTS_DIR, "configure-curriculum.py")
        mut_res = self.run_cmd([
            sys.executable, cfg_curric_script,
            "--instance-dir", proj2_inst,
            "--track", "interview-sprint",
            "--title", "Mutated Mastery Track"
        ])
        self.assertIn("Generated project-scoped curriculum track", mut_res.stdout)
        self.assertIn("completed preserved", mut_res.stdout)

        # 5. Test auto-notes disabled setting
        settings_file = os.path.join(proj2_inst, "settings.json")
        with open(settings_file, "r", encoding="utf-8") as sf:
            s_data = json.load(sf)
        s_data["autoGenerateNotes"] = False
        with open(settings_file, "w", encoding="utf-8") as sf:
            json.dump(s_data, sf, indent=2)

        advance_script = os.path.join(SCRIPTS_DIR, "advance-cursor.py")
        no_notes_res = self.run_cmd([
            sys.executable, advance_script,
            "--instance-dir", proj2_inst,
            "--complete-topic", "topic.0.2.b-tree-index",
            "--evidence", "B-tree index write amplification proven unassisted"
        ])
        self.assertIn("Auto-notes generation is disabled", no_notes_res.stdout)

    # =========================================================================
    # SUITE 11: Clean Uninstallation Engine
    # =========================================================================
    def test_11_clean_uninstaller(self):
        uninstall_script = os.path.join(REPO_ROOT, "uninstall.sh")
        proj2_dir = os.path.join(self.sandbox_dir, "proj2-mastery")

        res = self.run_cmd(["bash", uninstall_script, "-y"])
        self.assertIn("Uninstallation Complete!", res.stdout)

        # Verify all agent skill directories are removed
        for agent_path in [
            os.path.join(self.fake_home, ".gemini/antigravity/skills"),
            os.path.join(self.fake_home, ".claude/skills"),
            os.path.join(self.fake_home, ".cursor/skills"),
            os.path.join(self.fake_home, ".codex/skills")
        ]:
            self.assertFalse(os.path.isdir(os.path.join(agent_path, "system-design-studio")))
            self.assertFalse(os.path.isdir(os.path.join(agent_path, "sds-status")))
            self.assertFalse(os.path.isdir(os.path.join(agent_path, "sds-delete")))

        # Invariant: User learning instance state and study notes are strictly kept
        self.assertTrue(os.path.isdir(os.path.join(proj2_dir, ".system-design")))
        self.assertTrue(os.path.isdir(os.path.join(proj2_dir, "notes")))

    # =========================================================================
    # SUITE 12: Dummy Project & Dashboard Launchers
    # =========================================================================
    def test_12_dummy_project_and_launcher(self):
        dummy_dir = os.path.join(REPO_ROOT, "dummy-project")
        dummy_inst = os.path.join(dummy_dir, ".system-design")
        verify_script = os.path.join(SCRIPTS_DIR, "verify-instance.py")
        launch_script = os.path.join(REPO_ROOT, "launch-dummy-dashboard.sh")
        sds_bin = os.path.join(REPO_ROOT, "bin/sds")

        # 1. Health & Verification of mock project
        self.assertTrue(os.path.isdir(dummy_inst), "Missing dummy-project/.system-design")
        v_res = self.run_cmd([sys.executable, verify_script, dummy_inst])
        self.assertIn("PASSED with 0 errors", v_res.stdout)

        # 2. Verify mock data components
        self.assertTrue(os.path.isfile(os.path.join(dummy_inst, "revisions.json")))
        self.assertTrue(os.path.isfile(os.path.join(dummy_inst, "DECISIONS.md")))
        self.assertTrue(os.path.isfile(os.path.join(dummy_inst, "lessons/0-1-tcp-vs-udp.html.highlights.json")))
        self.assertTrue(os.path.isfile(os.path.join(dummy_inst, "lessons/0-1-http-1-1-vs-http-2-vs-http-3.html.highlights.json")))

        # 3. Test launch-dummy-dashboard.sh script
        self.assertTrue(os.path.isfile(launch_script))
        self.assertTrue(os.access(launch_script, os.X_OK))

        import socket
        import time
        import urllib.request
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1', 0))
            dummy_port = s.getsockname()[1]

        proc = subprocess.Popen(
            [launch_script, "--port", str(dummy_port), "--no-browser"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        try:
            ready = False
            for _ in range(25):
                try:
                    with urllib.request.urlopen(f"http://127.0.0.1:{dummy_port}/api/status", timeout=1.0) as resp:
                        if resp.status == 200:
                            data = json.loads(resp.read().decode("utf-8"))
                            self.assertEqual(data.get("manifest", {}).get("instanceName"), "System Design Dummy Lab")
                            ready = True
                            break
                except Exception:
                    time.sleep(0.15)
            self.assertTrue(ready, "launch-dummy-dashboard.sh failed to start within timeout")
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=2.0)
            except Exception:
                proc.kill()
            if proc.stdout: proc.stdout.close()
            if proc.stderr: proc.stderr.close()

if __name__ == "__main__":
    unittest.main(verbosity=2)
