#!/usr/bin/env python3
"""
test_adversarial_qa.py
Rigorous QA & Chaos Adversarial Testing Suite for System Design Studio.
Tests negative conditions, boundary values, intentional sabotage, path traversals,
data hazard prevention (zero git rollback on unverify), and edge cases.
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

class AdversarialQATestCase(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="sds-qa-")
        self.sandbox_home = os.path.join(self.temp_dir, "fakehome")
        os.makedirs(self.sandbox_home, exist_ok=True)
        self.orig_env = os.environ.copy()
        os.environ["HOME"] = self.sandbox_home
        os.environ["USERPROFILE"] = self.sandbox_home
        os.environ["SDS_GLOBAL_DIR"] = os.path.join(self.sandbox_home, ".system-design-studio")

        # Create a git-backed test project instance
        self.project_dir = os.path.join(self.temp_dir, "qa-project")
        os.makedirs(self.project_dir, exist_ok=True)
        subprocess.run(["git", "init", self.project_dir], capture_output=True, check=True)
        subprocess.run(["git", "-C", self.project_dir, "config", "user.name", "QA Bot"], check=True)
        subprocess.run(["git", "-C", self.project_dir, "config", "user.email", "qa@example.com"], check=True)

        init_script = os.path.join(SCRIPTS_DIR, "init-learning-instance.sh")
        res = subprocess.run([
            "bash", init_script,
            "--name", "QA Lab",
            "--id", "qa-lab",
            "--path", self.project_dir,
            "--track", "interview-sprint",
            "-y"
        ], capture_output=True, text=True, check=True)

        self.inst_dir = os.path.join(self.project_dir, ".system-design")

        # Initial commit in project
        subprocess.run(["git", "-C", self.project_dir, "add", "."], check=True)
        subprocess.run(["git", "-C", self.project_dir, "commit", "-m", "chore: init instance"], check=True)

        # Launch dashboard on a free port
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
        self.assertTrue(ready, "Dashboard failed to start in QA setup")

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
    # QA 1: CRITICAL DATA HAZARD PREVENTION (Zero Blind Git Rollback on Unverify)
    # =========================================================================
    def test_qa_01_unverify_topic_no_git_rollback(self):
        """Verify that cycling a topic to not_started does NOT roll back git history."""
        advance_script = os.path.join(SCRIPTS_DIR, "advance-cursor.py")

        # 1. Complete Topic 1 (TCP vs UDP)
        subprocess.run([
            sys.executable, advance_script,
            "--instance-dir", self.inst_dir,
            "--complete-topic", "topic.0.1.tcp-vs-udp",
            "--evidence", "Defended TCP backpressure cold in chat"
        ], check=True)

        # 2. Complete Topic 2 (HTTP/1 vs HTTP/2)
        subprocess.run([
            sys.executable, advance_script,
            "--instance-dir", self.inst_dir,
            "--complete-topic", "topic.0.1.http-1-1-vs-http-2-vs-http-3",
            "--evidence", "Derived HoL blocking in HTTP/2 under 1% loss"
        ], check=True)

        # Record commit count and top commit hash
        log_res = subprocess.run(["git", "-C", self.project_dir, "log", "--oneline"], capture_output=True, text=True, check=True)
        commits_before = [l for l in log_res.stdout.splitlines() if l.strip()]
        self.assertGreaterEqual(len(commits_before), 3, "Expected at least 3 commits")
        latest_commit_before = commits_before[0]
        self.assertIn("http-1-1-vs-http-2-vs-http-3", latest_commit_before)

        # 3. Trigger Unverify on Topic 1 via Dashboard API
        req_unverify = json.dumps({"topicId": "topic.0.1.tcp-vs-udp", "status": "not_started"}).encode("utf-8")
        req = urllib.request.Request(f"{self.base_url}/api/topic/status", data=req_unverify, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            self.assertEqual(resp.status, 200)

        # 4. Verify manifest.json state
        manifest_file = os.path.join(self.inst_dir, "manifest.json")
        with open(manifest_file, "r", encoding="utf-8") as mf:
            m = json.load(mf)

        t1_status = None
        t2_status = None
        for c in m["curriculum"]["clusters"]:
            for t in c["topics"]:
                if t["id"] == "topic.0.1.tcp-vs-udp": t1_status = t["status"]
                if t["id"] == "topic.0.1.http-1-1-vs-http-2-vs-http-3": t2_status = t["status"]

        self.assertEqual(t1_status, "unseen", "Topic 1 should be reset to unseen")
        self.assertEqual(t2_status, "completed", "Topic 2 MUST remain completed")

        # 5. INVARIANT: Git history MUST NOT be rolled back
        log_after = subprocess.run(["git", "-C", self.project_dir, "log", "--oneline"], capture_output=True, text=True, check=True)
        commits_after = [l for l in log_after.stdout.splitlines() if l.strip()]
        self.assertEqual(len(commits_before), len(commits_after), "Git commits count must remain identical (zero rollback)")
        self.assertEqual(commits_before[0], commits_after[0], "HEAD commit must not change")

        # 6. Verify CURRICULUM.md tickbox
        curric_file = os.path.join(self.inst_dir, "CURRICULUM.md")
        with open(curric_file, "r", encoding="utf-8") as cf:
            c_text = cf.read()
        self.assertTrue(re.search(r"-\s*\[\s*\]\s*TCP vs UDP", c_text), "TCP vs UDP must be unchecked in CURRICULUM.md")
        self.assertTrue(re.search(r"-\s*\[x\]\s*HTTP/1\.1 vs HTTP/2 vs HTTP/3", c_text), "HTTP/1.1 vs HTTP/2 vs HTTP/3 must remain checked in CURRICULUM.md")

    # =========================================================================
    # QA 2: PATH TRAVERSAL & MALICIOUS INPUT DEFENSE
    # =========================================================================
    def test_qa_02_path_traversal_rejection(self):
        """Ensure /api/note and /api/lesson strictly reject directory traversal attacks."""
        for malicious_path in [
            "../../etc/passwd",
            "../secret.md",
            "..\\..\\system.ini",
            "notes/../../../outside.txt"
        ]:
            # POST /api/note
            req_data = json.dumps({"path": malicious_path, "content": "malicious"}).encode("utf-8")
            req = urllib.request.Request(f"{self.base_url}/api/note", data=req_data, headers={"Content-Type": "application/json"})
            try:
                urllib.request.urlopen(req, timeout=2.0)
                self.fail(f"POST /api/note path traversal succeeded for {malicious_path}")
            except urllib.error.HTTPError as e:
                self.assertEqual(e.code, 403, f"Expected 403 for {malicious_path}, got {e.code}")

            # GET /api/note
            encoded_p = urllib.parse.quote(malicious_path)
            try:
                urllib.request.urlopen(f"{self.base_url}/api/note?path={encoded_p}", timeout=2.0)
                self.fail(f"GET /api/note path traversal succeeded for {malicious_path}")
            except urllib.error.HTTPError as e:
                self.assertEqual(e.code, 403, f"Expected 403 for {malicious_path}, got {e.code}")

            # GET /api/lesson
            try:
                urllib.request.urlopen(f"{self.base_url}/api/lesson?path={encoded_p}", timeout=2.0)
                self.fail(f"GET /api/lesson path traversal succeeded for {malicious_path}")
            except urllib.error.HTTPError as e:
                self.assertEqual(e.code, 403, f"Expected 403 for {malicious_path}, got {e.code}")

    # =========================================================================
    # QA 3: COMPLEX MARKDOWN & UNICODE PRESERVATION IN NOTES
    # =========================================================================
    def test_qa_03_markdown_pipe_tables_and_unicode_notes(self):
        """Verify notes API accurately persists pipe tables, math, quotes, and unicode."""
        complex_content = (
            "# Advanced Distributed Notes: Raft Consensus\n\n"
            "> **Invariant**: A leader will never overwrite or truncate its own log.\n\n"
            "| State | Term | Commit Index | Match Index |\n"
            "| :--- | :--- | :--- | :--- |\n"
            "| Leader | 4 | 1,024 | 1,024 |\n"
            "| Follower | 4 | 1,020 | 1,018 |\n\n"
            "- Formula: $\\text{Quorum} = \\lfloor N / 2 \\rfloor + 1$\n"
            "- Chinese glyphs: 系統設計, Japanese: システム設計, Emoji: 🛡⚡\n"
        )
        safe_rel_path = "tier-0/cluster-0-1/raft-notes.md"
        req_data = json.dumps({"path": safe_rel_path, "content": complex_content}).encode("utf-8")
        req = urllib.request.Request(f"{self.base_url}/api/note", data=req_data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            self.assertEqual(resp.status, 200)

        # Read back via GET /api/note
        encoded_p = urllib.parse.quote(safe_rel_path)
        with urllib.request.urlopen(f"{self.base_url}/api/note?path={encoded_p}", timeout=2.0) as resp:
            self.assertEqual(resp.status, 200)
            retrieved = resp.read().decode("utf-8")
            self.assertEqual(retrieved, complex_content)

    # =========================================================================
    # QA 4: SETTINGS KEYS & THEME PRESET SYNCHRONIZATION
    # =========================================================================
    def test_qa_04_settings_keys_harmonization(self):
        """Ensure settings API updates outputType and artifactStyle without schema mismatch."""
        new_cfg = {
            "outputType": "markdown",
            "artifactStyle": "obsidian",
            "notesDir": "custom-study-notes",
            "autoGenerateNotes": False
        }
        req_data = json.dumps(new_cfg).encode("utf-8")
        req = urllib.request.Request(f"{self.base_url}/api/settings", data=req_data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            self.assertEqual(resp.status, 200)

        # Verify on disk in settings.json
        settings_file = os.path.join(self.inst_dir, "settings.json")
        with open(settings_file, "r", encoding="utf-8") as sf:
            s_disk = json.load(sf)

        self.assertEqual(s_disk.get("outputType"), "markdown")
        self.assertEqual(s_disk.get("artifactStyle"), "obsidian")
        self.assertEqual(s_disk.get("notesDir"), "custom-study-notes")
        self.assertFalse(s_disk.get("autoGenerateNotes"))

        # Verify via GET /api/settings
        with urllib.request.urlopen(f"{self.base_url}/api/settings", timeout=2.0) as resp:
            self.assertEqual(resp.status, 200)
            payload = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(payload["project"]["outputType"], "markdown")
            self.assertEqual(payload["project"]["artifactStyle"], "obsidian")

    # =========================================================================
    # QA 5: ANKI-STYLE SPACED REPETITION SCHEDULING IN REVISIONS
    # =========================================================================
    def test_qa_05_revisions_rate_spaced_scheduling(self):
        """Verify /api/revisions/rate calculates review intervals (1d, 3d, 7d)."""
        revisions_file = os.path.join(self.inst_dir, "revisions.json")
        sample_revs = {
            "$schemaVersion": "1.0",
            "revisions": [
                {
                    "id": "rev.0.1.tcp",
                    "topicId": "topic.0.1.tcp-vs-udp",
                    "topicTitle": "TCP vs UDP",
                    "invariant": "Defended byte stream ordering",
                    "masteryStatus": "learning"
                }
            ]
        }
        with open(revisions_file, "w", encoding="utf-8") as rf:
            json.dump(sample_revs, rf, indent=2)

        # 1. Rate proficient (+3d)
        req_data = json.dumps({"revisionId": "rev.0.1.tcp", "masteryStatus": "proficient"}).encode("utf-8")
        req = urllib.request.Request(f"{self.base_url}/api/revisions/rate", data=req_data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            self.assertEqual(resp.status, 200)

        with open(revisions_file, "r", encoding="utf-8") as rf:
            r_after = json.load(rf)

        rev_item = r_after["revisions"][0]
        self.assertEqual(rev_item["masteryStatus"], "proficient")
        self.assertEqual(rev_item["reviewCount"], 1)

        today = datetime.date.today()
        expected_due = (today + datetime.timedelta(days=3)).strftime("%Y-%m-%d")
        self.assertEqual(rev_item["nextReviewDate"], expected_due)

    # =========================================================================
    # QA 6: ACTIVE PROJECT DELETION IN-MEMORY STALENESS PREVENTION
    # =========================================================================
    def test_qa_06_active_project_delete_in_memory_switch(self):
        """Ensure deleting the active project updates in-memory handler to next registered project."""
        reg_file = os.path.join(os.environ["SDS_GLOBAL_DIR"], "projects.json")

        # Register a second project
        proj_b_dir = os.path.join(self.temp_dir, "proj-b")
        os.makedirs(proj_b_dir, exist_ok=True)
        init_script = os.path.join(SCRIPTS_DIR, "init-learning-instance.sh")
        subprocess.run(["bash", init_script, "--name", "Project B", "--id", "proj-b", "--path", proj_b_dir, "-y"], check=True)

        with open(reg_file, "r", encoding="utf-8") as rf:
            reg_before = json.load(rf)
        self.assertEqual(len(reg_before["projects"]), 2)

        # Delete active project "qa-lab"
        req_data = json.dumps({"projectId": "qa-lab"}).encode("utf-8")
        req = urllib.request.Request(f"{self.base_url}/api/projects/delete", data=req_data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            self.assertEqual(resp.status, 200)

        with open(reg_file, "r", encoding="utf-8") as rf:
            reg_after = json.load(rf)

        self.assertEqual(len(reg_after["projects"]), 1)
        self.assertEqual(reg_after["activeProjectId"], "proj-b")

        # Verify /api/status now reports Project B without server restart
        with urllib.request.urlopen(f"{self.base_url}/api/status", timeout=2.0) as resp:
            self.assertEqual(resp.status, 200)
            status_data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(status_data["manifest"]["instanceName"], "Project B")

if __name__ == "__main__":
    unittest.main(verbosity=2)
