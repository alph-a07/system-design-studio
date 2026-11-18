#!/usr/bin/env python3
"""
serve-dashboard.py
Read-Only Curriculum Progress Tracker & Artifact Studio on Localhost for System Design Studio.
- In live sync with Git & local files (auto-polls /api/status).
- Showcases Curriculum Syllabus with completion status, living Cursor, interactive Lessons (HTML simulators),
  Active Study Notes (styled Markdown reader), and Architecture Decision Records (ADRs).
- Matches the Bauhaus Neo-Brutalist brand identity of the docs site.
- Built strictly with Python 3 standard library (zero external dependencies).
"""

import os
import sys
import json
import re
import socket
import argparse
import datetime
import webbrowser
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

DEFAULT_PORT = 8420

def find_available_port(start_port=DEFAULT_PORT, max_tries=20):
    for port in range(start_port, start_port + max_tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
    return start_port

def resolve_instance_dir(raw_dir=None, project_id=None):
    if project_id:
        reg_path = os.path.expanduser("~/.system-design-studio/projects.json")
        if os.path.isfile(reg_path):
            try:
                with open(reg_path, "r", encoding="utf-8") as f:
                    reg = json.load(f)
                for p in reg.get("projects", []):
                    if p.get("id") == project_id:
                        p_path = os.path.expanduser(p.get("projectPath", ""))
                        return os.path.join(p_path, ".system-design") if not p_path.endswith(".system-design") else p_path
            except Exception:
                pass

    if raw_dir:
        expanded = os.path.expanduser(raw_dir)
        if os.path.isdir(os.path.join(expanded, ".system-design")):
            return os.path.join(expanded, ".system-design")
        return expanded

    cwd_inst = os.path.abspath(".system-design")
    if os.path.isdir(cwd_inst) and os.path.isfile(os.path.join(cwd_inst, "manifest.json")):
        return cwd_inst

    curr = os.getcwd()
    while True:
        candidate = os.path.join(curr, ".system-design")
        if os.path.isdir(candidate) and os.path.isfile(os.path.join(candidate, "manifest.json")):
            return candidate
        parent = os.path.dirname(curr)
        if parent == curr:
            break
        curr = parent

    reg_path = os.path.expanduser("~/.system-design-studio/projects.json")
    if os.path.isfile(reg_path):
        try:
            with open(reg_path, "r", encoding="utf-8") as f:
                reg = json.load(f)
            active_id = reg.get("activeProjectId")
            for p in reg.get("projects", []):
                if p.get("id") == active_id:
                    cand = os.path.join(os.path.expanduser(p.get("projectPath", "")), ".system-design")
                    if os.path.isdir(cand) and os.path.isfile(os.path.join(cand, "manifest.json")):
                        return cand
        except Exception:
            pass

    return os.path.abspath(".system-design")

def get_git_info(base_dir):
    try:
        b_res = subprocess.run(["git", "-C", base_dir, "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, check=False)
        branch = b_res.stdout.strip() if b_res.returncode == 0 else "none"

        c_res = subprocess.run(["git", "-C", base_dir, "log", "-1", "--format=%h %s (%cr)"], capture_output=True, text=True, check=False)
        commit = c_res.stdout.strip() if c_res.returncode == 0 else "none"

        d_res = subprocess.run(["git", "-C", base_dir, "status", "--porcelain", ".system-design"], capture_output=True, text=True, check=False)
        dirty = bool(d_res.stdout.strip()) if d_res.returncode == 0 else False

        return {"is_git": True, "branch": branch, "commit": commit, "dirty": dirty}
    except Exception:
        return {"is_git": False, "branch": "none", "commit": "none", "dirty": False}

def scan_lessons(inst_dir):
    lessons_dir = os.path.join(inst_dir, "lessons")
    if not os.path.isdir(lessons_dir):
        return []
    items = []
    for f in sorted(os.listdir(lessons_dir)):
        if f.endswith(".html"):
            fpath = os.path.join(lessons_dir, f)
            size = os.path.getsize(fpath)
            mtime = datetime.datetime.fromtimestamp(os.path.getmtime(fpath)).strftime("%Y-%m-%d %H:%M")
            title = f.replace(".html", "").replace("-", " ").title()
            items.append({
                "filename": f,
                "title": title,
                "size_kb": round(size / 1024, 1),
                "mtime": mtime
            })
    return items

def scan_notes(base_dir, inst_dir):
    # Check settings for notesDir
    notes_dir_rel = "notes"
    settings_path = os.path.join(inst_dir, "settings.json")
    if os.path.isfile(settings_path):
        try:
            with open(settings_path, "r", encoding="utf-8") as sf:
                s = json.load(sf)
                notes_dir_rel = s.get("paths", {}).get("notesDir") or s.get("notesDir") or "notes"
        except Exception:
            pass

    notes_dir = notes_dir_rel if os.path.isabs(notes_dir_rel) else os.path.join(base_dir, notes_dir_rel)
    if not os.path.isdir(notes_dir):
        return []

    items = []
    for root, _, files in os.walk(notes_dir):
        for f in sorted(files):
            if f.endswith(".md"):
                fpath = os.path.join(root, f)
                rel_path = os.path.relpath(fpath, notes_dir)
                size = os.path.getsize(fpath)
                mtime = datetime.datetime.fromtimestamp(os.path.getmtime(fpath)).strftime("%Y-%m-%d %H:%M")
                items.append({
                    "rel_path": rel_path,
                    "filename": f,
                    "size_kb": round(size / 1024, 1),
                    "mtime": mtime
                })
    return items

DASHBOARD_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>System Design Studio — Local Curriculum & Progress Tracker</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@600;700;800&family=JetBrains+Mono:wght@500;600;700&display=swap" rel="stylesheet" />
  <style>
    :root {
      --surface-paper: #f5f0e8;
      --surface-card: #ffffff;
      --surface-card-high: #eae5dc;
      --surface-void: #141414;
      --surface-dark-card: #1c1d22;
      --ink: #1a1a1a;
      --ink-dim: #5c5852;
      --yellow: #ffcc00;
      --red: #e63b2e;
      --emerald: #10b981;
      --cobalt: #0047d4;
      --border-hard: 3px solid #1a1a1a;
      --shadow-hard: 4px 4px 0px #1a1a1a;
      --shadow-yellow: 4px 4px 0px #ffcc00;
      --shadow-red: 4px 4px 0px #e63b2e;
      --font-headline: 'Space Grotesk', -apple-system, sans-serif;
      --font-body: 'Inter', -apple-system, sans-serif;
      --font-mono: 'JetBrains Mono', ui-monospace, Menlo, monospace;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: var(--surface-paper);
      color: var(--ink);
      font-family: var(--font-body);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      overflow-x: hidden;
      -webkit-font-smoothing: antialiased;
    }

    /* Top Navbar */
    header {
      background: var(--surface-void);
      color: #f5f0e8;
      border-bottom: 3px solid var(--ink);
      padding: 12px 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      position: sticky;
      top: 0;
      z-index: 100;
    }

    .brand-lockup {
      display: flex;
      align-items: center;
      gap: 12px;
      text-decoration: none;
      color: #f5f0e8;
    }

    .brand-badge {
      width: 28px;
      height: 28px;
      background: var(--yellow);
      border: 2px solid #ffffff;
      box-shadow: 2px 2px 0px #000;
      display: flex;
      align-items: center;
      justify-content: center;
      font-family: var(--font-headline);
      font-weight: 800;
      color: #000;
      font-size: 14px;
    }

    .brand-title {
      font-family: var(--font-headline);
      font-weight: 800;
      font-size: 18px;
      letter-spacing: -0.5px;
      text-transform: uppercase;
    }

    .brand-subtitle {
      font-family: var(--font-mono);
      font-size: 11px;
      color: var(--yellow);
      background: rgba(255, 204, 0, 0.15);
      border: 1px solid var(--yellow);
      padding: 2px 8px;
      font-weight: 700;
    }

    .header-right {
      display: flex;
      align-items: center;
      gap: 14px;
    }

    .sync-status {
      display: flex;
      align-items: center;
      gap: 8px;
      font-family: var(--font-mono);
      font-size: 11px;
      color: #d6d1c9;
      background: #202228;
      padding: 4px 10px;
      border: 1.5px solid #444;
    }

    .sync-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--emerald);
      box-shadow: 0 0 6px var(--emerald);
      animation: pulse-dot 2s infinite;
    }
    @keyframes pulse-dot {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.4; }
    }

    /* Layout: Sidebar + Main Area */
    .dashboard-layout {
      display: grid;
      grid-template-columns: 320px 1fr;
      flex: 1;
      min-height: calc(100vh - 58px);
    }

    /* Sidebar */
    aside {
      background: var(--surface-card-high);
      border-right: 3px solid var(--ink);
      padding: 24px 20px;
      display: flex;
      flex-direction: column;
      gap: 24px;
      overflow-y: auto;
    }

    .sidebar-section-title {
      font-family: var(--font-headline);
      font-size: 11px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--ink-dim);
      margin-bottom: 8px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .project-card {
      background: var(--surface-card);
      border: var(--border-hard);
      box-shadow: 3px 3px 0px var(--ink);
      padding: 14px;
    }

    .project-name {
      font-family: var(--font-headline);
      font-weight: 800;
      font-size: 16px;
      text-transform: uppercase;
      margin-bottom: 4px;
    }

    .project-track {
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 700;
      color: var(--cobalt);
    }

    /* Progress Widget */
    .progress-widget {
      background: var(--surface-card);
      border: var(--border-hard);
      box-shadow: 3px 3px 0px var(--ink);
      padding: 14px;
    }

    .progress-numbers {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      margin-bottom: 6px;
    }

    .progress-large {
      font-family: var(--font-headline);
      font-weight: 800;
      font-size: 28px;
    }

    .progress-bar-bg {
      width: 100%;
      height: 12px;
      background: #e0dbd0;
      border: 2px solid var(--ink);
      overflow: hidden;
      margin-bottom: 6px;
    }

    .progress-bar-fill {
      height: 100%;
      background: var(--emerald);
      width: 0%;
      transition: width 0.3s ease;
    }

    /* Navigation Pills */
    .nav-list {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    .nav-btn {
      background: var(--surface-card);
      color: var(--ink);
      border: 2px solid var(--ink);
      box-shadow: 2px 2px 0px var(--ink);
      padding: 10px 14px;
      font-family: var(--font-mono);
      font-size: 12px;
      font-weight: 700;
      text-align: left;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: space-between;
      transition: all 0.1s ease;
    }

    .nav-btn:hover, .nav-btn.active {
      background: var(--yellow);
      transform: translate(-1px, -1px);
      box-shadow: 3px 3px 0px var(--ink);
    }

    .nav-badge {
      background: var(--surface-void);
      color: #fff;
      font-size: 10px;
      padding: 2px 6px;
      border-radius: 2px;
    }

    /* Git Status Card */
    .git-card {
      background: var(--surface-void);
      color: #f5f0e8;
      border: 2px solid var(--ink);
      padding: 12px;
      font-family: var(--font-mono);
      font-size: 11px;
      line-height: 1.5;
    }

    .git-title {
      font-weight: 800;
      color: var(--yellow);
      margin-bottom: 4px;
      text-transform: uppercase;
      font-size: 10px;
    }

    /* Main Content Area */
    main {
      padding: 32px 36px;
      overflow-y: auto;
    }

    .view-panel {
      display: none;
      flex-direction: column;
      gap: 24px;
      max-width: 1180px;
    }

    .view-panel.active {
      display: flex;
    }

    .panel-header {
      border-bottom: 3px solid var(--ink);
      padding-bottom: 16px;
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
      flex-wrap: wrap;
      gap: 12px;
    }

    .panel-title {
      font-family: var(--font-headline);
      font-size: 32px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: -0.5px;
    }

    .panel-desc {
      font-family: var(--font-body);
      color: var(--ink-dim);
      font-size: 14px;
      margin-top: 4px;
    }

    /* Active Focus View */
    .focus-grid {
      display: grid;
      grid-template-columns: 1.4fr 1fr;
      gap: 24px;
    }

    .focus-card-hero {
      background: var(--surface-card);
      border: var(--border-hard);
      box-shadow: var(--shadow-hard);
      padding: 24px;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

    .focus-tag {
      background: var(--yellow);
      border: 2px solid var(--ink);
      padding: 3px 8px;
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 800;
      text-transform: uppercase;
      display: inline-block;
      width: fit-content;
    }

    .focus-topic-name {
      font-family: var(--font-headline);
      font-size: 26px;
      font-weight: 800;
      line-height: 1.2;
    }

    .focus-cluster-line {
      font-family: var(--font-mono);
      font-size: 13px;
      color: var(--cobalt);
      font-weight: 700;
    }

    .reality-check-box {
      background: #faf7f2;
      border: 2px solid var(--ink);
      padding: 14px 16px;
      font-family: var(--font-mono);
      font-size: 12px;
      line-height: 1.6;
    }

    .reality-check-title {
      font-weight: 800;
      color: var(--red);
      margin-bottom: 6px;
      text-transform: uppercase;
      font-size: 11px;
    }

    .lineage-card {
      background: var(--surface-card);
      border: var(--border-hard);
      box-shadow: var(--shadow-hard);
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 14px;
    }

    .lineage-block {
      border-left: 3px solid var(--cobalt);
      padding-left: 12px;
    }

    .lineage-label {
      font-family: var(--font-mono);
      font-size: 10px;
      font-weight: 800;
      text-transform: uppercase;
      color: var(--ink-dim);
      margin-bottom: 2px;
    }

    .lineage-text {
      font-size: 13px;
      line-height: 1.5;
    }

    /* Curriculum View */
    .filter-bar {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      align-items: center;
      margin-bottom: 8px;
    }

    .filter-btn {
      background: var(--surface-card);
      border: 2px solid var(--ink);
      padding: 6px 12px;
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 700;
      cursor: pointer;
    }

    .filter-btn.active {
      background: var(--yellow);
      box-shadow: 2px 2px 0px var(--ink);
    }

    .curriculum-tier-box {
      background: var(--surface-card);
      border: var(--border-hard);
      box-shadow: var(--shadow-hard);
      margin-bottom: 20px;
      overflow: hidden;
    }

    .tier-header {
      background: #141414;
      color: #fff;
      padding: 12px 18px;
      font-family: var(--font-headline);
      font-weight: 800;
      font-size: 16px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .cluster-item {
      border-bottom: 1.5px solid #e0dbd0;
      padding: 14px 18px;
    }

    .cluster-item:last-child {
      border-bottom: none;
    }

    .cluster-top {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
    }

    .cluster-title {
      font-family: var(--font-headline);
      font-weight: 700;
      font-size: 14px;
    }

    .cluster-progress-badge {
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 700;
      background: var(--surface-card-high);
      border: 1px solid var(--ink);
      padding: 2px 8px;
    }

    .topics-list {
      display: flex;
      flex-direction: column;
      gap: 4px;
      padding-left: 8px;
    }

    .topic-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 4px 6px;
      font-family: var(--font-mono);
      font-size: 12px;
      border-radius: 2px;
    }

    .topic-row.completed {
      color: var(--emerald);
      font-weight: 600;
    }

    .topic-row.current {
      background: var(--yellow);
      color: var(--ink);
      font-weight: 800;
      border: 1.5px solid var(--ink);
    }

    .topic-links {
      display: flex;
      gap: 6px;
    }

    .mini-link {
      background: #ffffff;
      border: 1px solid var(--ink);
      padding: 2px 6px;
      font-size: 10px;
      text-decoration: none;
      color: var(--ink);
      font-weight: 700;
      cursor: pointer;
    }
    .mini-link:hover {
      background: var(--cobalt);
      color: #fff;
    }

    /* Lessons & Notes Grid */
    .items-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
      gap: 16px;
    }

    .item-card {
      background: var(--surface-card);
      border: var(--border-hard);
      box-shadow: var(--shadow-hard);
      padding: 16px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      gap: 12px;
    }

    .item-card-title {
      font-family: var(--font-headline);
      font-weight: 800;
      font-size: 15px;
      line-height: 1.3;
    }

    .item-card-meta {
      font-family: var(--font-mono);
      font-size: 11px;
      color: var(--ink-dim);
      display: flex;
      justify-content: space-between;
    }

    .item-card-action {
      background: var(--yellow);
      border: 2px solid var(--ink);
      padding: 6px 12px;
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 800;
      cursor: pointer;
      text-align: center;
      text-transform: uppercase;
      text-decoration: none;
      color: var(--ink);
      display: block;
    }
    .item-card-action:hover {
      background: var(--ink);
      color: #fff;
    }

    /* Preview Modal for Lessons / Notes */
    .preview-modal {
      display: none;
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(0, 0, 0, 0.75);
      z-index: 1000;
      padding: 30px;
      align-items: center;
      justify-content: center;
    }

    .preview-modal.active {
      display: flex;
    }

    .preview-window {
      background: #ffffff;
      width: 100%;
      max-width: 1100px;
      height: 90vh;
      border: 4px solid var(--ink);
      box-shadow: 10px 10px 0px #000;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    .preview-header {
      background: var(--surface-void);
      color: #fff;
      padding: 10px 18px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-family: var(--font-mono);
      font-size: 12px;
      font-weight: 700;
    }

    .close-btn {
      background: var(--red);
      color: #fff;
      border: 1.5px solid #fff;
      padding: 4px 10px;
      cursor: pointer;
      font-weight: 800;
    }

    .preview-body {
      flex: 1;
      width: 100%;
      height: 100%;
      border: none;
      overflow: auto;
      background: #faf7f2;
      padding: 24px;
    }

    /* Markdown note container */
    .markdown-content {
      max-width: 800px;
      margin: 0 auto;
      line-height: 1.7;
      font-size: 14px;
    }
    .markdown-content h1, .markdown-content h2, .markdown-content h3 {
      font-family: var(--font-headline);
      margin: 20px 0 10px;
      font-weight: 800;
      text-transform: uppercase;
    }
    .markdown-content pre {
      background: #141414;
      color: #fff;
      padding: 14px;
      border: 2px solid var(--ink);
      overflow-x: auto;
      margin: 14px 0;
      font-family: var(--font-mono);
      font-size: 12px;
    }
    .markdown-content blockquote {
      border-left: 4px solid var(--yellow);
      background: #fff;
      padding: 10px 14px;
      margin: 14px 0;
      font-weight: 500;
    }
  </style>
</head>
<body>

  <!-- Top Navbar -->
  <header>
    <a class="brand-lockup" href="#">
      <div class="brand-badge">S</div>
      <div>
        <div class="brand-title">System Design Studio</div>
      </div>
    </a>
    <span class="brand-subtitle" id="top-project-title">LOCAL WORKBENCH</span>
    <div class="header-right">
      <div class="sync-status">
        <div class="sync-dot"></div>
        <span id="sync-text">SYNCED WITH GIT</span>
      </div>
      <button onclick="refreshData()" class="filter-btn" style="background:var(--yellow);">⟳ REFRESH</button>
    </div>
  </header>

  <!-- Dashboard Layout -->
  <div class="dashboard-layout">
    
    <!-- Sidebar -->
    <aside>
      <div>
        <div class="sidebar-section-title">ACTIVE PROJECT</div>
        <div class="project-card">
          <div class="project-name" id="sb-project-name">Loading...</div>
          <div class="project-track" id="sb-project-track">Full Systems Mastery</div>
        </div>
      </div>

      <div>
        <div class="sidebar-section-title">CURRICULUM MASTERY</div>
        <div class="progress-widget">
          <div class="progress-numbers">
            <span class="progress-large" id="sb-progress-pct">0.0%</span>
            <span id="sb-progress-counts" style="font-family:var(--font-mono); font-size:12px; font-weight:700;">0/354</span>
          </div>
          <div class="progress-bar-bg">
            <div class="progress-bar-fill" id="sb-progress-bar"></div>
          </div>
          <div style="font-family:var(--font-mono); font-size:11px; color:var(--ink-dim); text-align:right;">
            <span id="sb-completed-count">0</span> Verified Topics
          </div>
        </div>
      </div>

      <div>
        <div class="sidebar-section-title">NAVIGATION</div>
        <div class="nav-list">
          <button class="nav-btn active" onclick="switchTab('focus')">
            <span>📌 Active Focus</span>
            <span class="nav-badge" id="nav-badge-focus">CURRENT</span>
          </button>
          <button class="nav-btn" onclick="switchTab('curriculum')">
            <span>🗺️ Curriculum Syllabus</span>
            <span class="nav-badge" id="nav-badge-clusters">50 Clusters</span>
          </button>
          <button class="nav-btn" onclick="switchTab('lessons')">
            <span>🧪 Interactive Lessons</span>
            <span class="nav-badge" id="nav-badge-lessons">0 HTML</span>
          </button>
          <button class="nav-btn" onclick="switchTab('notes')">
            <span>📝 Active Notes</span>
            <span class="nav-badge" id="nav-badge-notes">0 Notes</span>
          </button>
          <button class="nav-btn" onclick="switchTab('decisions')">
            <span>📋 Architecture ADRs</span>
            <span class="nav-badge" id="nav-badge-adrs">ADRs</span>
          </button>
        </div>
      </div>

      <div style="margin-top:auto;">
        <div class="sidebar-section-title">GIT TRACKING STATUS</div>
        <div class="git-card">
          <div class="git-title" id="sb-git-branch">BRANCH: MAIN</div>
          <div id="sb-git-commit" style="color:#d6d1c9; font-size:10px;">Checking status...</div>
        </div>
      </div>
    </aside>

    <!-- Main Content Panels -->
    <main>
      
      <!-- TAB 1: ACTIVE FOCUS -->
      <div id="panel-focus" class="view-panel active">
        <div class="panel-header">
          <div>
            <div class="panel-title">Active Pedagogical Focus</div>
            <div class="panel-desc">Immediate teaching horizon and causal grounding anchored in CURSOR.md.</div>
          </div>
        </div>

        <div class="focus-grid">
          <div class="focus-card-hero">
            <span class="focus-tag" id="fc-tier">Tier 0 — Transport</span>
            <div class="focus-cluster-line" id="fc-cluster">Cluster 0.1: TCP vs UDP</div>
            <div class="focus-topic-name" id="fc-topic">TCP Monotonic Stream vs UDP Datagram Boundaries</div>

            <div class="reality-check-box">
              <div class="reality-check-title">⚠️ Cluster Reality Check Defense Prompt</div>
              <div id="fc-reality-checks">
                1. "Explain the core invariant and causal failure boundary cold without notes."<br/>
                2. "Derive the quantitative trade-off or latency impact when the primary assumption fails."
              </div>
            </div>

            <div style="font-family:var(--font-mono); font-size:12px; color:var(--ink-dim); border-top:1.5px solid #eee; padding-top:12px;">
              <strong>Next Teaching Action:</strong> <span id="fc-next-action">Review mechanics and verify invariants</span>
            </div>
          </div>

          <div class="lineage-card">
            <div style="font-family:var(--font-headline); font-weight:800; font-size:16px; text-transform:uppercase; margin-bottom:4px;">
              Cognitive Lineage & Anchors
            </div>

            <div class="lineage-block">
              <div class="lineage-label">Backward Anchor (Where We Came From)</div>
              <div class="lineage-text" id="fc-backward">Grounding in physical network realities and kernel socket limits.</div>
            </div>

            <div class="lineage-block" style="border-color:var(--emerald);">
              <div class="lineage-label">Forward Hook (Where This Leads)</div>
              <div class="lineage-text" id="fc-forward">Connecting socket buffering to application-level multiplexing and HTTP/2.</div>
            </div>

            <div class="lineage-block" style="border-color:var(--yellow);">
              <div class="lineage-label">Examples Taken & Analogies</div>
              <div class="lineage-text" id="fc-examples">None logged yet.</div>
            </div>
          </div>
        </div>
      </div>

      <!-- TAB 2: CURRICULUM SYLLABUS -->
      <div id="panel-curriculum" class="view-panel">
        <div class="panel-header">
          <div>
            <div class="panel-title">Curriculum Syllabus</div>
            <div class="panel-desc">Master topic checklist, verified completion ticks, and cluster distribution.</div>
          </div>
          <div class="filter-bar">
            <button class="filter-btn active" onclick="filterTopics('all')">All</button>
            <button class="filter-btn" onclick="filterTopics('completed')">Completed</button>
            <button class="filter-btn" onclick="filterTopics('unseen')">Remaining</button>
          </div>
        </div>

        <div id="curriculum-container">
          <!-- Populated dynamically via JS -->
        </div>
      </div>

      <!-- TAB 3: INTERACTIVE LESSONS -->
      <div id="panel-lessons" class="view-panel">
        <div class="panel-header">
          <div>
            <div class="panel-title">Interactive HTML Lessons</div>
            <div class="panel-desc">Zero-dependency interactive simulations compiled into .system-design/lessons/.</div>
          </div>
        </div>

        <div class="items-grid" id="lessons-grid">
          <!-- Populated dynamically -->
        </div>
      </div>

      <!-- TAB 4: ACTIVE NOTES -->
      <div id="panel-notes" class="view-panel">
        <div class="panel-header">
          <div>
            <div class="panel-title">Active-Learning Study Notes</div>
            <div class="panel-desc">Structured Markdown study notes generated from defended invariants.</div>
          </div>
        </div>

        <div class="items-grid" id="notes-grid">
          <!-- Populated dynamically -->
        </div>
      </div>

      <!-- TAB 5: ARCHITECTURE ADRs -->
      <div id="panel-decisions" class="view-panel">
        <div class="panel-header">
          <div>
            <div class="panel-title">Architecture Decision Records</div>
            <div class="panel-desc">Persistent trade-off defenses logged into DECISIONS.md during sign-off gates.</div>
          </div>
        </div>

        <div id="adrs-content" class="markdown-content" style="background:#fff; border:3px solid var(--ink); padding:24px; box-shadow:4px 4px 0px var(--ink);">
          Loading decisions...
        </div>
      </div>

    </main>
  </div>

  <!-- Preview Modal for HTML Lessons / Markdown Notes -->
  <div id="preview-modal" class="preview-modal">
    <div class="preview-window">
      <div class="preview-header">
        <span id="preview-title">Document Preview</span>
        <button class="close-btn" onclick="closeModal()">✕ CLOSE</button>
      </div>
      <iframe id="preview-iframe" class="preview-body" style="display:none;"></iframe>
      <div id="preview-markdown" class="preview-body markdown-content" style="display:none;"></div>
    </div>
  </div>

  <script>
    let currentData = null;
    let activeFilter = 'all';

    function switchTab(tabId) {
      document.querySelectorAll('.view-panel').forEach(p => p.classList.remove('active'));
      document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));

      const target = document.getElementById(`panel-${tabId}`);
      if (target) target.classList.add('active');

      const btnIndex = ['focus', 'curriculum', 'lessons', 'notes', 'decisions'].indexOf(tabId);
      if (btnIndex >= 0) {
        document.querySelectorAll('.nav-btn')[btnIndex].classList.add('active');
      }

      if (tabId === 'decisions') loadDecisions();
    }

    async function refreshData() {
      try {
        const res = await fetch('/api/status');
        if (!res.ok) throw new Error('API failed');
        currentData = await res.json();
        renderDashboard(currentData);
      } catch (e) {
        console.error('Fetch error:', e);
        document.getElementById('sync-text').innerText = 'OFFLINE / DISCONNECTED';
      }
    }

    function renderDashboard(data) {
      // Sidebar stats
      const manifest = data.manifest || {};
      const curriculum = manifest.curriculum || {};
      const cursor = manifest.cursor || {};
      const clusters = curriculum.clusters || [];

      document.getElementById('top-project-title').innerText = manifest.instanceName || 'SYSTEM DESIGN STUDIO';
      document.getElementById('sb-project-name').innerText = manifest.instanceName || 'Current Project';
      document.getElementById('sb-project-track').innerText = curriculum.title || 'Mastery Track';

      let totalTopics = 0;
      let completedTopics = 0;
      clusters.forEach(c => {
        (c.topics || []).forEach(t => {
          totalTopics++;
          if (t.status === 'completed') completedTopics++;
        });
      });

      const pct = totalTopics > 0 ? ((completedTopics / totalTopics) * 100).toFixed(1) : '0.0';
      document.getElementById('sb-progress-pct').innerText = `${pct}%`;
      document.getElementById('sb-progress-counts').innerText = `${completedTopics}/${totalTopics}`;
      document.getElementById('sb-progress-bar').style.width = `${pct}%`;
      document.getElementById('sb-completed-count').innerText = completedTopics;

      // Git status
      const git = data.git || {};
      document.getElementById('sb-git-branch').innerText = `BRANCH: ${git.branch || 'MAIN'}`;
      document.getElementById('sb-git-commit').innerText = git.commit || 'No commits';

      // Active Focus
      document.getElementById('fc-tier').innerText = cursor.activeTier || 'Tier 0';
      document.getElementById('fc-cluster').innerText = cursor.activeClusterName || 'Cluster';
      document.getElementById('fc-topic').innerText = cursor.activeTopic || 'Active Topic';
      document.getElementById('fc-next-action').innerText = cursor.nextTeachingAction || 'Review next mechanics';
      document.getElementById('fc-backward').innerText = cursor.backwardAnchor || 'None';
      document.getElementById('fc-forward').innerText = cursor.forwardHook || 'None';

      const examples = (manifest.runningContext && manifest.runningContext.examplesTaken) || [];
      if (examples.length > 0) {
        document.getElementById('fc-examples').innerHTML = examples.map(e => `• <strong>${e.domain}</strong>: ${e.scenario}`).join('<br/>');
      } else {
        document.getElementById('fc-examples').innerText = 'None logged yet.';
      }

      // Counts
      document.getElementById('nav-badge-clusters').innerText = `${clusters.length} Clusters`;
      document.getElementById('nav-badge-lessons').innerText = `${(data.lessons || []).length} HTML`;
      document.getElementById('nav-badge-notes').innerText = `${(data.notes || []).length} Notes`;

      renderCurriculum(clusters, cursor);
      renderLessons(data.lessons || []);
      renderNotes(data.notes || []);
    }

    function renderCurriculum(clusters, cursor) {
      const cont = document.getElementById('curriculum-container');
      cont.innerHTML = '';

      // Group clusters by tier
      const tiers = {};
      clusters.forEach(c => {
        const tId = c.tierId || 'tier.0';
        if (!tiers[tId]) tiers[tId] = [];
        tiers[tId].push(c);
      });

      Object.keys(tiers).forEach(tId => {
        const tierClusters = tiers[tId];
        const tierBox = document.createElement('div');
        tierBox.className = 'curriculum-tier-box';

        const tierName = tId.replace('tier.', 'Tier ');
        tierBox.innerHTML = `
          <div class="tier-header">
            <span>${tierName}</span>
            <span style="font-family:var(--font-mono); font-size:11px; font-weight:700;">${tierClusters.length} Clusters</span>
          </div>
        `;

        tierClusters.forEach(c => {
          const cTopics = c.topics || [];
          const cCompleted = cTopics.filter(t => t.status === 'completed').length;
          const cDiv = document.createElement('div');
          cDiv.className = 'cluster-item';

          let topicsHtml = '';
          cTopics.forEach(t => {
            const isCompleted = t.status === 'completed';
            const isCurrent = t.id === cursor.activeTopicId || t.title === cursor.activeTopic;
            
            if (activeFilter === 'completed' && !isCompleted) return;
            if (activeFilter === 'unseen' && isCompleted) return;

            let rowClass = 'topic-row';
            if (isCompleted) rowClass += ' completed';
            if (isCurrent) rowClass += ' current';

            let check = isCompleted ? '✓' : (isCurrent ? '➔' : '○');
            let actions = '';
            if (t.lessonArtifact) {
              actions += `<button class="mini-link" onclick="openLesson('${t.lessonArtifact}')">SIMULATOR</button>`;
            }

            topicsHtml += `
              <div class="${rowClass}">
                <span>${check} ${t.title}</span>
                <div class="topic-links">${actions}</div>
              </div>
            `;
          });

          cDiv.innerHTML = `
            <div class="cluster-top">
              <span class="cluster-title">${c.title}</span>
              <span class="cluster-progress-badge">${cCompleted}/${cTopics.length}</span>
            </div>
            <div class="topics-list">${topicsHtml}</div>
          `;
          tierBox.appendChild(cDiv);
        });

        cont.appendChild(tierBox);
      });
    }

    function renderLessons(lessons) {
      const grid = document.getElementById('lessons-grid');
      grid.innerHTML = '';
      if (lessons.length === 0) {
        grid.innerHTML = '<div style="font-family:var(--font-mono); padding:20px;">No lesson artifacts generated yet. Run /sds-teach to generate interactive simulators.</div>';
        return;
      }

      lessons.forEach(l => {
        const card = document.createElement('div');
        card.className = 'item-card';
        card.innerHTML = `
          <div>
            <div class="focus-tag" style="background:var(--emerald); color:#000; margin-bottom:8px;">HTML SIMULATOR</div>
            <div class="item-card-title">${l.title}</div>
          </div>
          <div>
            <div class="item-card-meta">
              <span>${l.size_kb} KB</span>
              <span>${l.mtime}</span>
            </div>
            <button class="item-card-action" style="margin-top:10px; width:100%;" onclick="openLesson('lessons/${l.filename}')">Open Interactive Simulator ➔</button>
          </div>
        `;
        grid.appendChild(card);
      });
    }

    function renderNotes(notes) {
      const grid = document.getElementById('notes-grid');
      grid.innerHTML = '';
      if (notes.length === 0) {
        grid.innerHTML = '<div style="font-family:var(--font-mono); padding:20px;">No study notes compiled yet. Notes compile automatically upon topic sign-off (/sds-complete).</div>';
        return;
      }

      notes.forEach(n => {
        const card = document.createElement('div');
        card.className = 'item-card';
        card.innerHTML = `
          <div>
            <div class="focus-tag" style="background:var(--yellow); margin-bottom:8px;">STUDY NOTE</div>
            <div class="item-card-title">${n.rel_path}</div>
          </div>
          <div>
            <div class="item-card-meta">
              <span>${n.size_kb} KB</span>
              <span>${n.mtime}</span>
            </div>
            <button class="item-card-action" style="margin-top:10px; width:100%;" onclick="openNote('${n.rel_path}')">Read Note ➔</button>
          </div>
        `;
        grid.appendChild(card);
      });
    }

    async function loadDecisions() {
      try {
        const res = await fetch('/api/decisions');
        const text = await res.text();
        document.getElementById('adrs-content').innerHTML = `<pre style="white-space:pre-wrap; background:#fff; color:#1a1a1a; border:none; padding:0;">${escapeHtml(text)}</pre>`;
      } catch (e) {
        document.getElementById('adrs-content').innerText = 'Failed to load DECISIONS.md';
      }
    }

    function openLesson(relPath) {
      const modal = document.getElementById('preview-modal');
      const iframe = document.getElementById('preview-iframe');
      const mdDiv = document.getElementById('preview-markdown');
      
      iframe.style.display = 'block';
      mdDiv.style.display = 'none';
      iframe.src = `/api/lesson?path=${encodeURIComponent(relPath)}`;
      document.getElementById('preview-title').innerText = `Simulator: ${relPath}`;
      modal.classList.add('active');
    }

    async function openNote(relPath) {
      const modal = document.getElementById('preview-modal');
      const iframe = document.getElementById('preview-iframe');
      const mdDiv = document.getElementById('preview-markdown');
      
      iframe.style.display = 'none';
      mdDiv.style.display = 'block';
      document.getElementById('preview-title').innerText = `Study Note: ${relPath}`;
      modal.classList.add('active');

      try {
        const res = await fetch(`/api/note?path=${encodeURIComponent(relPath)}`);
        const text = await res.text();
        mdDiv.innerHTML = `<pre style="white-space:pre-wrap; font-family:var(--font-mono); font-size:13px; line-height:1.6; background:transparent; border:none; color:var(--ink);">${escapeHtml(text)}</pre>`;
      } catch (e) {
        mdDiv.innerText = 'Failed to load note content.';
      }
    }

    function closeModal() {
      document.getElementById('preview-modal').classList.remove('active');
      document.getElementById('preview-iframe').src = '';
    }

    function filterTopics(type) {
      activeFilter = type;
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      event.target.classList.add('active');
      if (currentData && currentData.manifest) {
        renderCurriculum(currentData.manifest.curriculum.clusters || [], currentData.manifest.cursor || {});
      }
    }

    function escapeHtml(text) {
      return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }

    // Auto-poll status every 3 seconds for live git sync
    setInterval(refreshData, 3000);
    window.addEventListener('DOMContentLoaded', refreshData);
  </script>
</body>
</html>
"""

class StudioDashboardHandler(BaseHTTPRequestHandler):
    inst_dir = None
    base_dir = None

    def log_message(self, format, *args):
        # Suppress normal polling logs to keep terminal quiet
        pass

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(DASHBOARD_HTML_TEMPLATE.encode("utf-8"))
            return

        elif path == "/api/status":
            manifest_path = os.path.join(self.inst_dir, "manifest.json")
            manifest = {}
            if os.path.isfile(manifest_path):
                try:
                    with open(manifest_path, "r", encoding="utf-8") as f:
                        manifest = json.load(f)
                except Exception as e:
                    manifest = {"error": str(e)}

            git_info = get_git_info(self.base_dir)
            lessons = scan_lessons(self.inst_dir)
            notes = scan_notes(self.base_dir, self.inst_dir)

            payload = {
                "manifest": manifest,
                "git": git_info,
                "lessons": lessons,
                "notes": notes,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(payload).encode("utf-8"))
            return

        elif path == "/api/lesson":
            raw_target = query.get("path", [""])[0]
            clean_name = os.path.basename(raw_target)
            lesson_file = os.path.join(self.inst_dir, "lessons", clean_name)
            if os.path.isfile(lesson_file):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                with open(lesson_file, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"Lesson file not found")
            return

        elif path == "/api/note":
            rel_path = query.get("path", [""])[0]
            # Safety check against path traversal
            norm_rel = os.path.normpath(rel_path).lstrip("/\\")
            if ".." in norm_rel:
                self.send_response(403)
                self.end_headers()
                self.wfile.write(b"Access denied")
                return

            notes_dir_rel = "notes"
            settings_path = os.path.join(self.inst_dir, "settings.json")
            if os.path.isfile(settings_path):
                try:
                    with open(settings_path, "r", encoding="utf-8") as sf:
                        s = json.load(sf)
                        notes_dir_rel = s.get("paths", {}).get("notesDir") or s.get("notesDir") or "notes"
                except Exception:
                    pass

            notes_dir = notes_dir_rel if os.path.isabs(notes_dir_rel) else os.path.join(self.base_dir, notes_dir_rel)
            target = os.path.join(notes_dir, norm_rel)
            if os.path.isfile(target):
                self.send_response(200)
                self.send_header("Content-Type", "text/markdown; charset=utf-8")
                self.end_headers()
                with open(target, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"Note not found")
            return

        elif path == "/api/decisions":
            dec_file = os.path.join(self.inst_dir, "DECISIONS.md")
            if os.path.isfile(dec_file):
                self.send_response(200)
                self.send_header("Content-Type", "text/markdown; charset=utf-8")
                self.end_headers()
                with open(dec_file, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"No DECISIONS.md found yet.")
            return

        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not found")

def main():
    try:
        from pathlib import Path
        _ensure_script = Path(__file__).resolve().parent / 'ensure-highlight-server.py'
        if _ensure_script.is_file():
            import subprocess, sys
            subprocess.run([sys.executable, str(_ensure_script)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1.0)
    except Exception:
        pass
    
    parser = argparse.ArgumentParser(description="System Design Studio Live Localhost Curriculum & Progress Tracker")
    parser.add_argument("--instance-dir", help="Path to .system-design directory")
    parser.add_argument("--project", help="Target project ID from multi-project registry")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"HTTP port (default {DEFAULT_PORT})")
    parser.add_argument("--no-browser", action="store_true", help="Do not automatically open web browser")

    args = parser.parse_args()

    inst_dir = resolve_instance_dir(args.instance_dir, args.project)
    if not os.path.isdir(inst_dir):
        print(f"❌ Error: .system-design instance directory not found at '{inst_dir}'.", file=sys.stderr)
        sys.exit(1)

    abs_inst = os.path.abspath(inst_dir)
    base_dir = os.path.dirname(abs_inst) if os.path.basename(abs_inst) == ".system-design" else abs_inst

    port = find_available_port(args.port)

    StudioDashboardHandler.inst_dir = abs_inst
    StudioDashboardHandler.base_dir = base_dir

    server = HTTPServer(("127.0.0.1", port), StudioDashboardHandler)
    url = f"http://localhost:{port}"

    print("=" * 76)
    print("  SYSTEM DESIGN STUDIO — LOCAL CURRICULUM TRACKER & WORKBENCH")
    print("=" * 76)
    print(f"🌐 Running live on: {url}")
    print(f"📂 Project Root:   {base_dir}")
    print(f"📁 Instance State: {abs_inst}")
    print("⚡ Real-time Git & Disk Sync: Active (polled every 3s)")
    print("Press Ctrl+C to stop the dashboard.")
    print("=" * 76)

    if not args.no_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Dashboard server stopped gracefully.")
        server.server_close()

if __name__ == "__main__":
    main()
