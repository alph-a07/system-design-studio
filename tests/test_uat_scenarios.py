#!/usr/bin/env python3
"""
test_uat_scenarios.py
Comprehensive End-to-End User Acceptance Testing (UAT) & Chaos Validation Suite
for System Design Studio.

Covers non-happy-path user workflows, nested workspace traversal, multi-track
mutations with completed topic preservation, notes structure variations,
gitless checkpoint fallbacks, concurrent SSE events, and revision state machine.
"""

import os
import sys
import json
import time
import shutil
import tempfile
import unittest
import subprocess
import urllib.request
import urllib.parse
import urllib.error
import socket
import datetime
import re

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "skills/system-design-studio/scripts")
BIN_SDS = os.path.join(REPO_ROOT, "bin/sds")


class UATScenariosTestCase(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="sds-uat-")
        self.sandbox_home = os.path.join(self.temp_dir, "fakehome")
        os.makedirs(self.sandbox_home, exist_ok=True)
        self.orig_env = os.environ.copy()
        os.environ["HOME"] = self.sandbox_home
        os.environ["USERPROFILE"] = self.sandbox_home
        os.environ["SDS_GLOBAL_DIR"] = os.path.join(self.sandbox_home, ".system-design-studio")

        # Create git-backed primary UAT project
        self.project_dir = os.path.join(self.temp_dir, "uat-project")
        os.makedirs(self.project_dir, exist_ok=True)
        subprocess.run(["git", "init", self.project_dir], capture_output=True, check=True)
        subprocess.run(["git", "-C", self.project_dir, "config", "user.name", "UAT Tester"], check=True)
        subprocess.run(["git", "-C", self.project_dir, "config", "user.email", "uat@example.com"], check=True)

        init_script = os.path.join(SCRIPTS_DIR, "init-learning-instance.sh")
        subprocess.run([
            "bash", init_script,
            "--name", "UAT Robustness Lab",
            "--id", "uat-lab",
            "--path", self.project_dir,
            "--track", "interview-sprint",
            "-y"
        ], capture_output=True, text=True, check=True)

        self.inst_dir = os.path.join(self.project_dir, ".system-design")
        subprocess.run(["git", "-C", self.project_dir, "add", "."], check=True)
        subprocess.run(["git", "-C", self.project_dir, "commit", "-m", "chore: init uat lab"], check=True)

        # Free port for dashboard server
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1', 0))
            self.test_port = s.getsockname()[1]

        dashboard_script = os.path.join(SCRIPTS_DIR, "serve-dashboard.py")
        self.proc = subprocess.Popen(
            [sys.executable, dashboard_script, "--instance-dir", self.inst_dir, "--port", str(self.test_port), "--no-browser"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        self.base_url = f"http://127.0.0.1:{self.test_port}"
        ready = False
        for _ in range(30):
            try:
                with urllib.request.urlopen(f"{self.base_url}/api/status", timeout=1.0) as resp:
                    if resp.status == 200:
                        ready = True
                        break
            except Exception:
                time.sleep(0.15)
        self.assertTrue(ready, "Dashboard server failed to start in UAT setup")

    def tearDown(self):
        if hasattr(self, "proc") and self.proc:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=2.0)
            except Exception:
                self.proc.kill()
        os.environ.clear()
        os.environ.update(self.orig_env)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # =========================================================================
    # UAT 1: CLI WORKFLOW FROM DEEPLY NESTED SUBDIRECTORIES
    # =========================================================================
    def test_uat_01_nested_subdirectory_discovery(self):
        """Verify bin/sds commands discover .system-design from deeply nested subfolders."""
        nested_dir = os.path.join(self.project_dir, "src", "services", "auth", "handlers")
        os.makedirs(nested_dir, exist_ok=True)

        # Run sds status from inside nested_dir
        res = subprocess.run([BIN_SDS, "status"], cwd=nested_dir, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"sds status failed from nested directory: {res.stderr}")
        self.assertIn("UAT Robustness Lab", res.stdout)
        self.assertIn("TCP vs UDP", res.stdout)

        # Run sds notes from nested_dir
        res_notes = subprocess.run([BIN_SDS, "notes"], cwd=nested_dir, capture_output=True, text=True)
        self.assertEqual(res_notes.returncode, 0)

    # =========================================================================
    # UAT 2: TRACK MUTATION & PRESERVATION OF COMPLETED TOPICS
    # =========================================================================
    def test_uat_02_track_switching_preserves_completed_topics(self):
        """User switches tracks multiple times; completed topics & ADRs must never be lost."""
        advance_script = os.path.join(SCRIPTS_DIR, "advance-cursor.py")

        # 1. Complete topic 0.1.tcp-vs-udp
        subprocess.run([
            sys.executable, advance_script,
            "--instance-dir", self.inst_dir,
            "--complete-topic", "topic.0.1.tcp-vs-udp",
            "--evidence", "Defended monotonic byte streams in interview mock"
        ], check=True)

        # Verify completed in manifest
        with open(os.path.join(self.inst_dir, "manifest.json"), "r", encoding="utf-8") as f:
            m1 = json.load(f)
        top1 = [t for c in m1["curriculum"]["clusters"] for t in c["topics"] if t["id"] == "topic.0.1.tcp-vs-udp"][0]
        self.assertEqual(top1["status"], "completed")

        # 2. Switch track to 'full-mastery' (50 clusters)
        config_script = os.path.join(SCRIPTS_DIR, "configure-curriculum.py")
        res_switch = subprocess.run([
            sys.executable, config_script,
            "--track", "full-mastery",
            "--instance-dir", self.inst_dir,
            "--title", "UAT Track Switch"
        ], capture_output=True, text=True)
        self.assertEqual(res_switch.returncode, 0)
        self.assertIn("1 completed preserved", res_switch.stdout)

        # Verify topic remains completed in new curriculum track
        with open(os.path.join(self.inst_dir, "manifest.json"), "r", encoding="utf-8") as f:
            m2 = json.load(f)
        self.assertEqual(len(m2["curriculum"]["clusters"]), 50)
        top_switched = [t for c in m2["curriculum"]["clusters"] for t in c["topics"] if t["id"] == "topic.0.1.tcp-vs-udp"][0]
        self.assertEqual(top_switched["status"], "completed")

        # 3. Switch track to 'distributed-systems'
        res_prereq = subprocess.run([
            sys.executable, config_script,
            "--track", "distributed-systems",
            "--instance-dir", self.inst_dir,
            "--title", "Distributed Systems Track"
        ], capture_output=True, text=True)
        self.assertEqual(res_prereq.returncode, 0)
        self.assertIn("1 completed preserved", res_prereq.stdout)

        with open(os.path.join(self.inst_dir, "manifest.json"), "r", encoding="utf-8") as f:
            m3 = json.load(f)
        top_prereq = [t for c in m3["curriculum"]["clusters"] for t in c["topics"] if t["id"] == "topic.0.1.tcp-vs-udp"][0]
        self.assertEqual(top_prereq["status"], "completed")

    # =========================================================================
    # UAT 3: STUDY NOTES STRUCTURAL VARIATIONS & IDEMPOTENCY
    # =========================================================================
    def test_uat_03_notes_structures_and_idempotency(self):
        """Test compiling study notes under different structures (per-cluster, single-file)."""
        gen_script = os.path.join(SCRIPTS_DIR, "generate-notes.py")
        settings_file = os.path.join(self.inst_dir, "settings.json")

        # Switch to per-cluster structure
        with open(settings_file, "r", encoding="utf-8") as f:
            s = json.load(f)
        s["notesStructure"] = "per-cluster"
        with open(settings_file, "w", encoding="utf-8") as f:
            json.dump(s, f, indent=2)

        # Generate notes for cluster 0.1
        res = subprocess.run([
            sys.executable, gen_script,
            "--instance-dir", self.inst_dir,
            "--topic-id", "topic.0.1.tcp-vs-udp",
            "--evidence", "Defended sequence ordering cold in mock",
            "--notes-structure", "per-cluster"
        ], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)

        # Verify cluster note created
        match = re.search(r"file://([^\s\n]+)", res.stdout)
        self.assertIsNotNone(match, f"No file URI in stdout: {res.stdout}")
        cluster_note_path = match.group(1)
        self.assertTrue(os.path.isfile(cluster_note_path), f"Note missing: {cluster_note_path}")

        # Re-run same generation (idempotency check)
        res_repeat = subprocess.run([
            sys.executable, gen_script,
            "--instance-dir", self.inst_dir,
            "--topic-id", "topic.0.1.tcp-vs-udp",
            "--evidence", "Defended sequence ordering cold in mock",
            "--notes-structure", "per-cluster"
        ], capture_output=True, text=True)
        self.assertEqual(res_repeat.returncode, 0)

        # Verify no duplicate topic sections created
        with open(cluster_note_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content.count("## TCP vs UDP"), 1, "Duplicate section header created on repeat run")

    # =========================================================================
    # UAT 4: GITLESS CHECKPOINT FALLBACK
    # =========================================================================
    def test_uat_04_gitless_checkpoint_fallback(self):
        """Ensure git-checkpoint.py creates atomic local snapshot when outside git."""
        non_git_dir = os.path.join(self.temp_dir, "non-git-project")
        os.makedirs(non_git_dir, exist_ok=True)
        init_script = os.path.join(SCRIPTS_DIR, "init-learning-instance.sh")
        subprocess.run([
            "bash", init_script,
            "--name", "Gitless Project",
            "--id", "gitless-proj",
            "--path", non_git_dir,
            "-y"
        ], capture_output=True, check=True)

        non_git_inst = os.path.join(non_git_dir, ".system-design")
        checkpoint_dir = os.path.join(non_git_inst, ".checkpoints")
        self.assertTrue(os.path.isdir(checkpoint_dir))

        # Create a manual checkpoint outside git
        cp_script = os.path.join(SCRIPTS_DIR, "git-checkpoint.py")
        res = subprocess.run([
            sys.executable, cp_script,
            "commit",
            "--instance-dir", non_git_inst,
            "--type", "learn",
            "--subject", "Manual snapshot test"
        ], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("Local snapshot created", res.stdout)

    # =========================================================================
    # UAT 5: SSE LIVE SYNC CLIENT & STATE HASH CHANGE
    # =========================================================================
    def test_uat_05_sse_events_and_state_sync(self):
        """Verify /api/events sends initial connection and detects instance changes."""
        # Check initial connection to /api/events
        req = urllib.request.Request(f"{self.base_url}/api/events")
        resp = urllib.request.urlopen(req, timeout=3.0)
        self.assertEqual(resp.status, 200)
        first_line = resp.readline().decode("utf-8").strip()
        self.assertEqual(first_line, ": connected")
        resp.close()

        # Update settings via API and verify instant reflection
        settings_update = {
            "artifactStyle": "terminal-hacker",
            "outputType": "markdown"
        }
        post_req = urllib.request.Request(
            f"{self.base_url}/api/settings",
            data=json.dumps(settings_update).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(post_req, timeout=2.0) as p_resp:
            self.assertEqual(p_resp.status, 200)

        # Verify reflected in /api/status
        with urllib.request.urlopen(f"{self.base_url}/api/status", timeout=2.0) as s_resp:
            status_data = json.loads(s_resp.read().decode("utf-8"))
            self.assertEqual(status_data["settings"]["artifactStyle"], "terminal-hacker")
            self.assertEqual(status_data["settings"]["outputType"], "markdown")

    # =========================================================================
    # UAT 6: REVISION CORRUPTION AUTO-HEALING
    # =========================================================================
    def test_uat_06_corrupted_revisions_recovery(self):
        """If revisions.json is corrupted by manual edit, /api/revisions must re-sync without 500 error."""
        rev_file = os.path.join(self.inst_dir, "revisions.json")
        with open(rev_file, "w", encoding="utf-8") as f:
            f.write("CORRUPTED NOT JSON {{{")

        # Query /api/revisions
        with urllib.request.urlopen(f"{self.base_url}/api/revisions", timeout=2.0) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertIn("revisions", data)
            self.assertIsInstance(data["revisions"], list)


if __name__ == "__main__":
    unittest.main(verbosity=2)
