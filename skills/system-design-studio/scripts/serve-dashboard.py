#!/usr/bin/env python3
"""
serve-dashboard.py
Interactive Curriculum Studio, Project Workbench & Real-Time Living Cursor for System Design Studio.
- Dual-direction read-write workbench: dashboard updates disk; agents keep data fresh; live sync reflects changes without manual refresh.
- Projects Manager: cards-on-dashboard home view to switch, initialize, and manage learning instances.
- Single Unified Curriculum View: real-time topic status updates (not started, in progress, completed) with collapsible tiers/clusters, inline lessons, notes, and ADR defense.
- Full-Screen Lesson Workbench (Reader Mode): distraction-free lesson-only view supporting interactive HTML simulators and rich Markdown lessons + notes with zero-dependency client-side rendering and built-in highlighting.
- Revision Mode: high-value conceptual understanding distilled from sign-off defenses, failure boundaries, and formulas with Anki-style spaced review intervals.
- Top Navbar design reused directly from the docs site (docs/index.html) with flawless dark and light mode support.
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
import threading
import time
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

try:
    from http.server import ThreadingHTTPServer as StudioHTTPServer
except ImportError:
    from socketserver import ThreadingMixIn
    class StudioHTTPServer(ThreadingMixIn, HTTPServer):
        daemon_threads = True

DEFAULT_PORT = 8420

def find_available_port(start_port=DEFAULT_PORT, max_tries=20):
    for port in range(start_port, start_port + max_tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
    return start_port

def get_local_network_ip():
    """Detects primary LAN IPv4 address for auto-hosting on network."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"

def get_home_dir():
    return os.environ.get("HOME") or os.environ.get("USERPROFILE") or os.path.expanduser("~")

def get_global_studio_dir():
    home = get_home_dir()
    return os.environ.get("SDS_GLOBAL_DIR") or os.path.join(home, ".system-design-studio")

def get_projects_registry_path():
    return os.path.join(get_global_studio_dir(), "projects.json")

def load_projects_registry():
    reg_path = get_projects_registry_path()
    if not os.path.exists(reg_path):
        return {"$schemaVersion": "3.2", "activeProjectId": None, "projects": [], "unregisteredPaths": []}
    try:
        with open(reg_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return {"$schemaVersion": "3.2", "activeProjectId": None, "projects": [], "unregisteredPaths": []}
            if "unregisteredPaths" not in data:
                data["unregisteredPaths"] = []
            return data
    except Exception:
        return {"$schemaVersion": "3.2", "activeProjectId": None, "projects": [], "unregisteredPaths": []}

def save_projects_registry(data):
    reg_path = get_projects_registry_path()
    os.makedirs(os.path.dirname(reg_path), exist_ok=True)
    temp_path = f"{reg_path}.tmp.{os.getpid()}"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(temp_path, reg_path)

def resolve_manifest_metrics(manifest_path, base_dir=None):
    """Parses manifest.json live from disk and returns accurate topics metrics and active topic info."""
    if not manifest_path or not os.path.isfile(manifest_path):
        return None
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        curriculum = manifest.get("curriculum", {})
        clusters = curriculum.get("clusters", [])
        total_topics = sum(len(c.get("topics", [])) for c in clusters)
        verified_topics = sum(1 for c in clusters for t in c.get("topics", []) if t.get("status") in ("completed", "verified"))
        active_topic_id = curriculum.get("activeTopicId", "none")
        active_cluster_id = curriculum.get("activeClusterId", "none")
        active_track = curriculum.get("activeTrackId") or curriculum.get("track") or "full-mastery"

        active_topic_title = "Foundation Initialization"
        for c in clusters:
            for t in c.get("topics", []):
                if t.get("id") == active_topic_id:
                    active_topic_title = t.get("title") or t.get("name") or active_topic_title
                    break

        git_branch = "main"
        if base_dir and os.path.isdir(base_dir):
            git_branch = get_git_info(base_dir).get("branch", "main")

        pct = round((verified_topics / total_topics) * 100) if total_topics > 0 else 0
        return {
            "instanceName": manifest.get("instanceName"),
            "track": active_track,
            "totalTopics": total_topics,
            "verifiedTopics": verified_topics,
            "completed": verified_topics,
            "total": total_topics,
            "percentage": pct,
            "activeTopicId": active_topic_id,
            "activeTopicTitle": active_topic_title,
            "activeClusterId": active_cluster_id,
            "gitBranch": git_branch,
            "lastActive": datetime.datetime.fromtimestamp(os.path.getmtime(manifest_path), tz=datetime.timezone.utc).isoformat()
        }
    except Exception:
        return None

def get_live_projects_registry(current_inst_dir=None, save_back=True):
    """
    Live consumer of disk data:
    1. Loads registered projects from projects.json.
    2. Auto-discovers any learning projects across disk:
       - ~/.system-design-studio/projects/*
       - current server instance directory (current_inst_dir)
       - current working directory (os.getcwd()) and sibling project directories
    3. Re-reads every project's manifest.json live from disk to compute exact topics count,
       active focus topic, and real-time completion percentages.
    4. Persists the synced registry state so all CLI tools and web views share identical data.
    """
    reg = load_projects_registry()
    projects = reg.get("projects", [])
    active_id = reg.get("activeProjectId")
    unregistered = set(reg.get("unregisteredPaths", []))

    seen_paths = {}
    for p in projects:
        pp = os.path.abspath(os.path.expanduser(p.get("projectPath", "")))
        seen_paths[pp] = p

    candidates = []

    # 1. Central studio projects (~/.system-design-studio/projects/*)
    studio_projects_dir = os.path.join(get_global_studio_dir(), "projects")
    if os.path.isdir(studio_projects_dir):
        try:
            for entry in os.listdir(studio_projects_dir):
                cand = os.path.join(studio_projects_dir, entry)
                if os.path.isdir(cand):
                    candidates.append(cand)
        except Exception:
            pass

    # 2. Current server instance directory (if provided)
    if current_inst_dir:
        cand_inst = os.path.abspath(os.path.expanduser(current_inst_dir))
        cand_base = os.path.dirname(cand_inst) if os.path.basename(cand_inst) == ".system-design" else cand_inst
        candidates.append(cand_base)

    # 3. Current working directory and immediate siblings (e.g. ~/Developer/*, only in normal workspace mode)
    if not os.environ.get("SDS_GLOBAL_DIR"):
        cwd = os.path.abspath(os.getcwd())
        candidates.append(cwd)
        parent_cwd = os.path.dirname(cwd)
        if os.path.isdir(parent_cwd) and parent_cwd != cwd:
            try:
                for entry in os.listdir(parent_cwd):
                    cand = os.path.join(parent_cwd, entry)
                    if os.path.isdir(cand):
                        candidates.append(cand)
            except Exception:
                pass

    # Auto-discover candidates that contain .system-design/manifest.json
    for cand_path in candidates:
        cand_path = os.path.abspath(cand_path)
        if cand_path in unregistered:
            continue
        m_path = os.path.join(cand_path, ".system-design", "manifest.json")
        if not os.path.isfile(m_path):
            continue

        if cand_path not in seen_paths:
            metrics = resolve_manifest_metrics(m_path, cand_path)
            folder_name = os.path.basename(cand_path)
            name = (metrics.get("instanceName") if metrics else None) or folder_name
            slug_id = re.sub(r"[^a-zA-Z0-9_-]", "-", name.lower()).strip("-") or folder_name.lower()
            existing_ids = {p.get("id") for p in projects}
            final_id = slug_id
            counter = 1
            while final_id in existing_ids:
                final_id = f"{slug_id}-{counter}"
                counter += 1

            location_type = "default" if cand_path.startswith(studio_projects_dir) else "custom"
            now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
            new_p = {
                "id": final_id,
                "name": name,
                "locationType": location_type,
                "projectPath": cand_path,
                "track": (metrics.get("track") if metrics else None) or "full-mastery",
                "notesDir": os.path.join(cand_path, "notes"),
                "notesStructure": "per-topic",
                "createdAt": now_iso,
                "lastActive": now_iso
            }
            projects.append(new_p)
            seen_paths[cand_path] = new_p

    # Refresh live metrics for EVERY project directly from disk
    refreshed_projects = []
    for p in projects:
        p_path = os.path.abspath(os.path.expanduser(p.get("projectPath", "")))
        m_path = os.path.join(p_path, ".system-design", "manifest.json")
        metrics = resolve_manifest_metrics(m_path, p_path)
        if metrics:
            p["name"] = metrics["instanceName"] or p.get("name")
            p["track"] = metrics["track"] or p.get("track") or "full-mastery"
            p["gitBranch"] = metrics["gitBranch"]
            p["lastActive"] = metrics["lastActive"]
            p["activeTopicTitle"] = metrics["activeTopicTitle"]
            p["progress"] = {
                "totalTopics": metrics["totalTopics"],
                "verifiedTopics": metrics["verifiedTopics"],
                "completed": metrics["completed"],
                "total": metrics["total"],
                "percentage": metrics["percentage"],
                "activeTopicId": metrics["activeTopicId"],
                "activeTopicTitle": metrics["activeTopicTitle"],
                "activeClusterId": metrics["activeClusterId"]
            }
            refreshed_projects.append(p)
        else:
            if os.path.isdir(p_path):
                default_total = 114 if p.get("track") == "interview-sprint" else 354
                p["progress"] = {
                    "totalTopics": default_total,
                    "verifiedTopics": 0,
                    "completed": 0,
                    "total": default_total,
                    "percentage": 0,
                    "activeTopicId": "none",
                    "activeTopicTitle": "Foundation Initialization",
                    "activeClusterId": "none"
                }
                refreshed_projects.append(p)
            else:
                p["missingOnDisk"] = True
                p["progress"] = {
                    "totalTopics": 0,
                    "verifiedTopics": 0,
                    "completed": 0,
                    "total": 0,
                    "percentage": 0
                }
                refreshed_projects.append(p)

    reg["projects"] = refreshed_projects

    if not active_id or not any(p.get("id") == active_id for p in refreshed_projects):
        if refreshed_projects:
            matched = None
            if current_inst_dir:
                c_norm = os.path.abspath(os.path.expanduser(current_inst_dir))
                c_base = os.path.dirname(c_norm) if os.path.basename(c_norm) == ".system-design" else c_norm
                matched = next((p for p in refreshed_projects if os.path.abspath(os.path.expanduser(p.get("projectPath", ""))) == c_base), None)
            reg["activeProjectId"] = matched["id"] if matched else refreshed_projects[0]["id"]

    if save_back:
        try:
            save_projects_registry(reg)
        except Exception:
            pass

    return reg

def resolve_instance_dir(raw_dir=None, project_id=None):
    reg = get_live_projects_registry(save_back=False)
    if project_id:
        for p in reg.get("projects", []):
            if p.get("id") == project_id:
                p_path = os.path.expanduser(p.get("projectPath", ""))
                cand = os.path.join(p_path, ".system-design") if not p_path.endswith(".system-design") else p_path
                if os.path.isdir(cand):
                    return cand

    if raw_dir:
        expanded = os.path.expanduser(raw_dir)
        if os.path.isdir(os.path.join(expanded, ".system-design")):
            return os.path.join(expanded, ".system-design")
        return expanded

    active_id = reg.get("activeProjectId")
    if active_id:
        for p in reg.get("projects", []):
            if p.get("id") == active_id:
                p_path = os.path.expanduser(p.get("projectPath", ""))
                cand = os.path.join(p_path, ".system-design") if not p_path.endswith(".system-design") else p_path
                if os.path.isdir(cand) and os.path.isfile(os.path.join(cand, "manifest.json")):
                    return cand

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

    for p in reg.get("projects", []):
        p_path = os.path.expanduser(p.get("projectPath", ""))
        cand = os.path.join(p_path, ".system-design") if not p_path.endswith(".system-design") else p_path
        if os.path.isdir(cand) and os.path.isfile(os.path.join(cand, "manifest.json")):
            return cand

    return None

def get_git_info(repo_dir):
    info = {"branch": "unknown", "commit": "none", "clean": True, "dirtyCount": 0}
    try:
        res = subprocess.run(["git", "-C", repo_dir, "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, check=False)
        if res.returncode == 0 and res.stdout.strip():
            info["branch"] = res.stdout.strip()

        res2 = subprocess.run(["git", "-C", repo_dir, "log", "-1", "--format=%h %s (%cr)"], capture_output=True, text=True, check=False)
        if res2.returncode == 0 and res2.stdout.strip():
            info["commit"] = res2.stdout.strip()

        res3 = subprocess.run(["git", "-C", repo_dir, "status", "--porcelain"], capture_output=True, text=True, check=False)
        if res3.returncode == 0:
            lines = [l for l in res3.stdout.splitlines() if l.strip()]
            info["dirtyCount"] = len(lines)
            info["clean"] = (len(lines) == 0)
    except Exception:
        pass
    return info

def scan_lessons(inst_dir):
    lessons_dir = os.path.join(inst_dir, "lessons")
    if not os.path.isdir(lessons_dir):
        return []
    items = []
    for f in sorted(os.listdir(lessons_dir)):
        if f.endswith(".html") or f.endswith(".md"):
            fp = os.path.join(lessons_dir, f)
            items.append({
                "filename": f,
                "path": f"lessons/{f}",
                "size": os.path.getsize(fp),
                "modified": datetime.datetime.fromtimestamp(os.path.getmtime(fp), datetime.timezone.utc).isoformat(),
                "format": "markdown" if f.endswith(".md") else "html"
            })
    return items

def scan_notes(base_dir, inst_dir):
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
        for f in files:
            if f.endswith(".md"):
                full_p = os.path.join(root, f)
                rel_p = os.path.relpath(full_p, notes_dir)
                items.append({
                    "filename": f,
                    "relPath": rel_p,
                    "fullPath": full_p,
                    "size": os.path.getsize(full_p),
                    "modified": datetime.datetime.fromtimestamp(os.path.getmtime(full_p), datetime.timezone.utc).isoformat()
                })
    return sorted(items, key=lambda x: x["relPath"])

def get_highlights_candidates(inst_dir, artifact_path):
    clean_p = artifact_path.replace("\\", "/").strip("/")
    candidates = []
    # If it is a note (starts with tier- or notes/ or ends with .md)
    if clean_p.startswith("notes/"):
        slug = clean_p.replace("/", "--")
        candidates.append(os.path.join(inst_dir, "highlights", f"{slug}.json"))
        unprefixed = clean_p[6:]
        candidates.append(os.path.join(inst_dir, "highlights", f"{unprefixed.replace('/', '--')}.json"))
    elif any(clean_p.startswith(pfx) for pfx in ["tier-", "tier_"]):
        candidates.append(os.path.join(inst_dir, "highlights", f"notes--{clean_p.replace('/', '--')}.json"))
        candidates.append(os.path.join(inst_dir, "highlights", f"{clean_p.replace('/', '--')}.json"))
    else:
        candidates.append(os.path.join(inst_dir, "highlights", f"{clean_p.replace('/', '--')}.json"))
    safe_name = os.path.basename(clean_p)
    candidates.append(os.path.join(inst_dir, "highlights", f"{safe_name}.json"))
    # Legacy next to artifact
    candidates.append(os.path.join(inst_dir, clean_p + ".highlights.json"))
    return candidates

def get_highlights_path(inst_dir, artifact_path):
    candidates = get_highlights_candidates(inst_dir, artifact_path)
    for c in candidates:
        if os.path.isfile(c):
            return c
    return candidates[0]

def load_highlights_data(inst_dir, artifact_path):
    candidates = get_highlights_candidates(inst_dir, artifact_path)
    for c in candidates:
        if os.path.isfile(c):
            try:
                with open(c, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
    return []

def save_highlights_data(inst_dir, artifact_path, data):
    p = get_highlights_path(inst_dir, artifact_path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def compute_instance_state_hash(inst_dir, base_dir):
    try:
        files_to_check = [
            os.path.join(inst_dir, "manifest.json") if inst_dir else "",
            os.path.join(inst_dir, "CURSOR.md") if inst_dir else "",
            os.path.join(inst_dir, "DECISIONS.md") if inst_dir else "",
            os.path.join(inst_dir, "settings.json") if inst_dir else "",
            os.path.join(inst_dir, "revisions.json") if inst_dir else "",
            get_projects_registry_path()
        ]
        mtimes = []
        for f in files_to_check:
            if f and os.path.isfile(f):
                mtimes.append(f"{os.path.basename(f)}:{os.path.getmtime(f)}:{os.path.getsize(f)}")

        # Watch central studio projects directory for new/deleted project folders
        studio_projects = os.path.join(get_global_studio_dir(), "projects")
        if os.path.isdir(studio_projects):
            mtimes.append(f"projects_dir:{os.path.getmtime(studio_projects)}:{len(os.listdir(studio_projects))}")

        # Watch lessons and notes directories
        if inst_dir:
            lessons_dir = os.path.join(inst_dir, "lessons")
            if os.path.isdir(lessons_dir):
                mtimes.append(f"lessons:{os.path.getmtime(lessons_dir)}:{len(os.listdir(lessons_dir))}")

        if base_dir:
            notes_dir = os.path.join(base_dir, "notes")
            if os.path.isdir(notes_dir):
                mtimes.append(f"notes:{os.path.getmtime(notes_dir)}:{len(os.listdir(notes_dir))}")

        return "|".join(mtimes)
    except Exception:
        return str(time.time())

CURRENT_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, CURRENT_SCRIPTS_DIR)

try:
    import importlib
    update_revisions_mod = importlib.import_module("update-revisions")
except Exception:
    update_revisions_mod = None

DASHBOARD_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>System Design Studio — Localhost Interactive Workbench</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700;800&family=JetBrains+Mono:wght@500;600;700&display=swap" rel="stylesheet" />
  <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" rel="stylesheet" />
  <style>
    :root {
      --surface: #f5f0e8;
      --surface-container: #eee9e0;
      --surface-container-high: #e8e3da;
      --surface-container-low: #f2ede5;
      --surface-container-lowest: #ffffff;
      --on-surface: #1a1a1a;
      --on-surface-variant: #4a4a4a;
      --primary: #1a1a1a;
      --primary-container: #ffcc00;
      --on-primary-container: #1a1a1a;
      --secondary: #dc2626;
      --tertiary: #0055ff;
      --emerald: #059669;
      --emerald-light: #10b981;
      --border-color: #1a1a1a;
      --shadow-color: #1a1a1a;
      --font-headline: 'Space Grotesk', -apple-system, BlinkMacSystemFont, sans-serif;
      --font-body: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      --font-mono: 'JetBrains Mono', ui-monospace, Menlo, monospace;
    }

    html.dark {
      --surface: #141414;
      --surface-container: #1f1f1f;
      --surface-container-high: #282828;
      --surface-container-low: #181818;
      --surface-container-lowest: #1c1c1c;
      --on-surface: #f5f0e8;
      --on-surface-variant: #a8a398;
      --primary: #f5f0e8;
      --primary-container: #ffcc00;
      --on-primary-container: #1a1a1a;
      --secondary: #dc2626;
      --tertiary: #388bfd;
      --emerald: #10b981;
      --emerald-light: #34d399;
      --border-color: #383838;
      --shadow-color: #000000;
    }

    /* DYNAMIC LIVE READING PRESETS */
    html[data-theme-preset="slate-clean"].dark {
      --surface: #0f172a;
      --surface-container: #1e293b;
      --surface-container-high: #334155;
      --surface-container-low: #090d16;
      --surface-container-lowest: #1e293b;
      --on-surface: #f8fafc;
      --on-surface-variant: #94a3b8;
      --primary: #f8fafc;
      --primary-container: #ffcc00;
      --on-primary-container: #1a1a1a;
      --secondary: #dc2626;
      --tertiary: #38bdf8;
      --border-color: #334155;
      --shadow-color: #000000;
    }

    html[data-theme-preset="cyber-obsidian"].dark,
    html[data-theme-preset="midnight-neon"].dark {
      --surface: #05070c;
      --surface-container: #0d1117;
      --surface-container-high: #161b22;
      --surface-container-low: #020408;
      --surface-container-lowest: #0d1117;
      --on-surface: #f0f6fc;
      --on-surface-variant: #8b949e;
      --primary: #f0f6fc;
      --primary-container: #00e5ff;
      --on-primary-container: #000000;
      --secondary: #ff3366;
      --tertiary: #00e5ff;
      --border-color: #30363d;
      --shadow-color: #000000;
    }

    html[data-theme-preset="nordic-frost"].dark {
      --surface: #242933;
      --surface-container: #2e3440;
      --surface-container-high: #3b4252;
      --surface-container-low: #1e222a;
      --surface-container-lowest: #2e3440;
      --on-surface: #eceff4;
      --on-surface-variant: #d8dee9;
      --primary: #eceff4;
      --primary-container: #88c0d0;
      --on-primary-container: #242933;
      --secondary: #bf616a;
      --tertiary: #81a1c1;
      --border-color: #434c5e;
      --shadow-color: #000000;
    }

    html[data-theme-preset="warm-amber"].dark {
      --surface: #1c1917;
      --surface-container: #292524;
      --surface-container-high: #44403c;
      --surface-container-low: #141210;
      --surface-container-lowest: #292524;
      --on-surface: #fafaf9;
      --on-surface-variant: #a8a29e;
      --primary: #fafaf9;
      --primary-container: #f59e0b;
      --on-primary-container: #1c1917;
      --secondary: #ef4444;
      --tertiary: #fbbf24;
      --border-color: #44403c;
      --shadow-color: #000000;
    }

    html[data-theme-preset="editorial-paper"] {
      --surface: #f5f0e8;
      --surface-container: #eee9e0;
      --surface-container-high: #e8e3da;
      --surface-container-low: #f2ede5;
      --surface-container-lowest: #ffffff;
      --on-surface: #1a1a1a;
      --on-surface-variant: #4a4a4a;
      --primary: #1a1a1a;
      --primary-container: #ffcc00;
      --on-primary-container: #1a1a1a;
      --secondary: #dc2626;
      --tertiary: #0055ff;
      --border-color: #1a1a1a;
      --shadow-color: #1a1a1a;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    .material-symbols-outlined {
      font-family: 'Material Symbols Outlined';
      font-weight: normal;
      font-style: normal;
      font-size: 18px;
      line-height: 1;
      letter-spacing: normal;
      text-transform: none;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      white-space: nowrap;
      word-wrap: normal;
      direction: ltr;
      -webkit-font-feature-settings: 'liga';
      -webkit-font-smoothing: antialiased;
      vertical-align: middle;
      user-select: none;
    }
    body {
      background-color: var(--surface);
      color: var(--on-surface);
      font-family: var(--font-body);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      overflow-x: hidden;
      -webkit-font-smoothing: antialiased;
      transition: background-color 0.15s ease, color 0.15s ease;
    }

    /* TOP NAVBAR (Reused directly from docs/index.html) */
    header.studio-navbar {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      height: 64px;
      background-color: var(--surface);
      border-bottom: 3px solid var(--border-color);
      z-index: 50;
      padding: 0 1.5rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
      transition: background-color 0.15s ease, border-color 0.15s ease;
    }

    .nav-left {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .nav-brand {
      display: flex;
      align-items: center;
      gap: 10px;
      text-decoration: none;
      color: var(--on-surface);
      cursor: pointer;
    }

    .brand-icon-box {
      width: 34px;
      height: 34px;
      background-color: var(--primary-container);
      border: 2px solid var(--border-color);
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 4px;
      box-shadow: 2px 2px 0px var(--shadow-color);
      flex-shrink: 0;
    }

    .brand-title {
      font-family: var(--font-headline);
      font-weight: 800;
      font-size: 17px;
      letter-spacing: -0.02em;
      text-transform: uppercase;
      color: var(--on-surface);
    }

    .active-project-pill {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 4px 10px;
      border: 2px solid var(--border-color);
      background-color: var(--surface-container-low);
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 700;
      box-shadow: 2px 2px 0px var(--shadow-color);
      cursor: pointer;
      max-width: 220px;
      overflow: hidden;
      white-space: nowrap;
      text-overflow: ellipsis;
    }

    .nav-project-dropdown {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 3px 8px 3px 10px;
      border: 2px solid var(--border-color);
      background-color: var(--surface-container-low);
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 700;
      box-shadow: 2px 2px 0px var(--shadow-color);
      position: relative;
      cursor: pointer;
      min-width: 190px;
      max-width: 320px;
      transition: all 0.15s ease;
    }
    .nav-project-dropdown:hover, .nav-project-dropdown:focus-within {
      border-color: var(--primary-container);
      box-shadow: 3px 3px 0px var(--shadow-color);
    }
    .nav-project-select {
      appearance: none;
      -webkit-appearance: none;
      -moz-appearance: none;
      background: transparent;
      border: none;
      outline: none;
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 700;
      color: var(--on-surface);
      cursor: pointer;
      padding-right: 22px;
      text-overflow: ellipsis;
      overflow: hidden;
      white-space: nowrap;
      width: 100%;
    }
    .nav-project-select option {
      background-color: var(--surface-container-high);
      color: var(--on-surface);
      font-family: var(--font-mono);
      font-size: 12px;
    }
    .nav-project-caret {
      position: absolute;
      right: 6px;
      pointer-events: none;
      font-size: 14px;
      color: var(--on-surface-variant);
    }

    .version-tag-pill {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      padding: 3px 8px;
      border: 1.5px solid var(--border-color);
      background: var(--surface-container-low);
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 700;
      color: var(--on-surface-variant);
      cursor: pointer;
      transition: all 0.15s ease;
      box-shadow: 1px 1px 0px var(--shadow-color);
    }
    .version-tag-pill:hover {
      border-color: var(--primary-container);
      color: var(--on-surface);
      background: var(--surface-container-high);
      box-shadow: 2px 2px 0px var(--shadow-color);
    }
    .status-dot.green {
      background-color: var(--emerald-light, #10b981);
    }

    /* INDIVIDUAL HIGHLIGHTS POPOVER MENU */
    .hl-popover-menu {
      position: absolute;
      top: calc(100% + 6px);
      right: 0;
      width: 290px;
      max-height: 280px;
      overflow-y: auto;
      background: var(--surface-container-high);
      border: 2px solid var(--border-color);
      box-shadow: 4px 4px 0px var(--shadow-color);
      padding: 6px;
      z-index: 2000;
      font-family: var(--font-mono);
      font-size: 11px;
    }
    .hl-popover-item {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 5px 6px;
      background: var(--surface-container-lowest);
      border: 1px solid var(--border-color);
      margin-bottom: 4px;
      transition: background 0.15s ease;
    }
    .hl-popover-item:hover {
      background: var(--surface-container-low);
    }
    .hl-popover-text {
      flex: 1;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      color: var(--on-surface);
      font-size: 11px;
    }
    .hl-popover-del-btn {
      background: transparent;
      border: none;
      color: var(--secondary);
      cursor: pointer;
      padding: 2px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 2px;
      transition: all 0.1s ease;
    }
    .hl-popover-del-btn:hover {
      background: var(--secondary);
      color: #fff;
    }

    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background-color: var(--emerald-light);
      display: inline-block;
      flex-shrink: 0;
    }

    .status-dot.pulse {
      animation: pulse-dot 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
    }

    @keyframes pulse-dot {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.5; transform: scale(0.9); }
    }

    /* CENTER NAV TABS */
    .nav-tabs {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .nav-tab-btn {
      padding: 6px 14px;
      font-family: var(--font-headline);
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      border: 2px solid transparent;
      background: transparent;
      color: var(--on-surface-variant);
      cursor: pointer;
      transition: all 0.12s ease;
    }

    .nav-tab-btn:hover {
      color: var(--on-surface);
      background-color: var(--surface-container-high);
    }

    .nav-tab-btn.active {
      background-color: var(--primary-container);
      color: #1a1a1a;
      border: 2px solid var(--border-color);
      box-shadow: 2px 2px 0px var(--shadow-color);
    }

    /* NAV RIGHT ACTIONS */
    .nav-right {
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .sync-micro-badge {
      display: flex;
      align-items: center;
      gap: 6px;
      font-family: var(--font-mono);
      font-size: 11px;
      color: var(--on-surface-variant);
      font-weight: 600;
      padding: 4px 6px;
    }

    .icon-action-btn {
      width: 36px;
      height: 36px;
      border: 2px solid var(--border-color);
      background-color: var(--surface-container-lowest);
      color: var(--on-surface);
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 2px 2px 0px var(--shadow-color);
      cursor: pointer;
      font-family: var(--font-mono);
      font-size: 15px;
      font-weight: bold;
      transition: all 0.1s ease;
    }

    .icon-action-btn:hover {
      background-color: var(--primary-container);
      color: #1a1a1a;
    }

    .icon-action-btn:active {
      transform: translate(1px, 1px);
      box-shadow: 1px 1px 0px var(--shadow-color);
    }

    /* MAIN CONTAINER */
    main.studio-main {
      margin-top: 64px;
      flex: 1;
      width: 100%;
      max-width: 1240px;
      margin-left: auto;
      margin-right: auto;
      padding: 28px 20px 60px 20px;
    }

    /* PANELS */
    .view-panel {
      display: none;
      animation: fadeIn 0.15s ease-out;
    }

    .view-panel.active {
      display: block;
    }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(4px); }
      to { opacity: 1; transform: translateY(0); }
    }

    /* SECTION HEADERS */
    .view-header {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 24px;
      padding-bottom: 16px;
      border-bottom: 2px solid var(--border-color);
    }

    .view-title {
      font-family: var(--font-headline);
      font-size: 26px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: -0.02em;
      color: var(--on-surface);
    }

    .view-subtitle {
      font-family: var(--font-body);
      font-size: 13px;
      color: var(--on-surface-variant);
      margin-top: 4px;
    }

    /* BAUHAUS BUTTONS */
    .btn-primary {
      padding: 8px 16px;
      border: 2px solid var(--border-color);
      background-color: var(--primary-container);
      color: #1a1a1a;
      font-family: var(--font-headline);
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      box-shadow: 3px 3px 0px var(--shadow-color);
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all 0.1s ease;
    }

    .btn-primary:hover {
      background-color: #1a1a1a;
      color: #ffffff;
      border-color: #1a1a1a;
    }

    .btn-primary:active {
      transform: translate(1px, 1px);
      box-shadow: 2px 2px 0px var(--shadow-color);
    }

    .btn-ghost {
      padding: 6px 12px;
      border: 2px solid var(--border-color);
      background-color: var(--surface-container-lowest);
      color: var(--on-surface);
      font-family: var(--font-headline);
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      box-shadow: 2px 2px 0px var(--shadow-color);
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all 0.1s ease;
    }

    .btn-ghost:hover {
      background-color: var(--surface-container-high);
    }

    /* PROJECTS GRID (Cards Home Vibe) */
    .projects-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
      gap: 22px;
      margin-top: 20px;
    }

    .project-card {
      border: 2px solid var(--border-color);
      background-color: var(--surface-container-lowest);
      box-shadow: 4px 4px 0px var(--shadow-color);
      padding: 22px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      min-height: 250px;
      transition: all 0.15s ease;
    }

    .project-card:hover {
      box-shadow: 6px 6px 0px var(--primary-container);
    }

    .project-card.active-card {
      border: 3px solid var(--border-color);
      box-shadow: 5px 5px 0px var(--primary-container);
    }

    .card-top-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 14px;
    }

    .badge-active {
      background-color: var(--primary-container);
      color: #1a1a1a;
      border: 1px solid var(--border-color);
      font-family: var(--font-headline);
      font-size: 10px;
      font-weight: 800;
      text-transform: uppercase;
      padding: 2px 6px;
    }

    .badge-registered {
      background-color: var(--surface-container-high);
      color: var(--on-surface-variant);
      border: 1px solid var(--border-color);
      font-family: var(--font-headline);
      font-size: 10px;
      font-weight: 700;
      text-transform: uppercase;
      padding: 2px 6px;
    }

    .git-branch-tag {
      font-family: var(--font-mono);
      font-size: 11px;
      color: var(--on-surface-variant);
    }

    .project-title {
      font-family: var(--font-headline);
      font-size: 19px;
      font-weight: 700;
      text-transform: uppercase;
      color: var(--on-surface);
      margin-bottom: 4px;
    }

    .project-track {
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 600;
      color: var(--tertiary);
      margin-bottom: 16px;
    }

    .progress-bar-container {
      background-color: var(--surface-container-low);
      border: 1px solid var(--border-color);
      height: 9px;
      width: 100%;
      margin: 10px 0 6px 0;
      overflow: hidden;
    }

    .progress-bar-fill {
      background-color: var(--emerald-light);
      height: 100%;
      transition: width 0.3s ease;
    }

    .progress-metric-text {
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 700;
      color: var(--on-surface);
      display: flex;
      justify-content: space-between;
    }

    .active-topic-snippet {
      font-family: var(--font-mono);
      font-size: 11px;
      color: var(--on-surface-variant);
      margin-top: 14px;
      padding: 8px 10px;
      background-color: var(--surface-container-low);
      border-left: 3px solid var(--primary-container);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .card-footer {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-top: 20px;
      padding-top: 14px;
      border-top: 1px solid var(--surface-container-high);
    }

    .scaffolding-card {
      border: 2px dashed var(--border-color);
      background-color: var(--surface-container-low);
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 24px;
      text-align: center;
      cursor: pointer;
      min-height: 250px;
      transition: all 0.15s ease;
    }

    .scaffolding-card:hover {
      border-color: var(--primary-container);
      background-color: var(--surface-container);
    }

    /* CALM UNIFIED CURRICULUM COMMAND BAR */
    .curriculum-toolbar {
      display: flex;
      flex-direction: column;
      gap: 6px;
      margin-bottom: 12px;
    }

    .toolbar-primary-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      flex-wrap: wrap;
    }

    .toolbar-actions {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }

    .toolbar-select {
      height: 34px;
      padding: 0 10px;
      border: 1px solid var(--border-color);
      background-color: var(--surface-container-lowest);
      color: var(--on-surface);
      font-family: var(--font-headline);
      font-size: 11px;
      font-weight: 700;
      cursor: pointer;
      box-shadow: 1px 1px 0px var(--shadow-color);
      outline: none;
      transition: border-color 0.15s ease;
      border-radius: 2px;
    }

    .toolbar-select:focus {
      border-color: var(--tertiary);
    }

    .search-input-wrapper {
      position: relative;
      display: inline-flex;
      align-items: center;
      flex: 1;
      min-width: 240px;
      max-width: 480px;
    }

    .search-leading-icon {
      position: absolute;
      left: 10px;
      color: var(--on-surface-variant);
      font-size: 16px;
      pointer-events: none;
    }

    .search-input {
      width: 100%;
      height: 34px;
      padding: 0 32px 0 32px;
      border: 1px solid var(--border-color);
      background-color: var(--surface-container-lowest);
      color: var(--on-surface);
      font-family: var(--font-body);
      font-size: 12px;
      box-shadow: 1px 1px 0px var(--shadow-color);
      outline: none;
      transition: all 0.15s ease;
      border-radius: 2px;
    }

    .search-input:focus {
      border-color: var(--tertiary);
      box-shadow: 2px 2px 0px var(--shadow-color);
    }

    .search-hints-row {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 0 2px;
      font-family: var(--font-mono);
      font-size: 10px;
      color: var(--on-surface-variant);
      flex-wrap: wrap;
    }

    .tag-hint-link {
      background: none;
      border: none;
      padding: 1px 4px;
      font-family: var(--font-mono);
      font-size: 10px;
      font-weight: 600;
      color: var(--on-surface-variant);
      cursor: pointer;
      text-decoration: none;
      transition: color 0.1s ease;
      border-radius: 2px;
    }

    .tag-hint-link:hover {
      color: var(--tertiary);
      text-decoration: underline;
    }

    .search-clear-btn {
      position: absolute;
      right: 8px;
      top: 50%;
      transform: translateY(-50%);
      width: 20px;
      height: 20px;
      background: var(--surface-container-high);
      border: 1px solid var(--border-color);
      border-radius: 50%;
      display: none;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      color: var(--on-surface-variant);
      transition: all 0.1s ease;
      padding: 0;
      z-index: 2;
    }
    .search-clear-btn:hover {
      color: var(--on-surface);
      background: var(--surface-container-highest);
      border-color: var(--tertiary);
    }

    .tier-chevron-icon {
      font-size: 18px;
      color: var(--on-surface-variant);
      transition: transform 0.15s ease;
    }

    .tier-accordion {
      margin-bottom: 16px;
      border: 2px solid var(--border-color);
      background-color: var(--surface-container-lowest);
      box-shadow: 3px 3px 0px var(--shadow-color);
    }

    .tier-header {
      padding: 14px 18px;
      background-color: var(--surface-container);
      display: flex;
      align-items: center;
      justify-content: space-between;
      cursor: pointer;
      border-bottom: 2px solid transparent;
      transition: background-color 0.1s ease;
      gap: 12px;
    }

    .tier-accordion.open .tier-header {
      border-bottom-color: var(--border-color);
    }

    .tier-title {
      font-family: var(--font-headline);
      font-size: 14px;
      font-weight: 800;
      text-transform: uppercase;
      color: var(--on-surface);
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .tier-subtitle {
      font-family: var(--font-body);
      font-size: 11px;
      color: var(--on-surface-variant);
      margin-top: 3px;
      text-transform: none;
      line-height: 1.4;
    }

    .tier-level-badge {
      font-family: var(--font-mono);
      font-size: 9px;
      font-weight: 800;
      text-transform: uppercase;
      padding: 2px 7px;
      border: 1px solid var(--border-color, rgba(0, 0, 0, 0.25));
      letter-spacing: 0.06em;
      border-radius: 2px;
      box-shadow: 1px 1px 0px rgba(0, 0, 0, 0.2);
    }

    .tier-badge {
      font-family: var(--font-mono);
      font-size: 10px;
      font-weight: 700;
      padding: 3px 8px;
      background-color: var(--surface-container-lowest);
      border: 1px solid var(--border-color);
      white-space: nowrap;
    }

    .tier-content {
      display: none;
      padding: 14px;
    }

    .tier-accordion.open .tier-content {
      display: block;
    }

    /* TIER QUICK-JUMP NAVIGATION BAR (SEGMENTED STRIP) */
    .tier-jump-bar {
      display: inline-flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 3px;
      padding: 3px;
      margin-bottom: 14px;
      background-color: var(--surface-container-low);
      border: 1px solid var(--border-color);
      box-shadow: 1px 1px 0px var(--shadow-color);
      border-radius: 2px;
      overflow-x: auto;
      scrollbar-width: none;
    }
    .tier-jump-bar::-webkit-scrollbar { display: none; }

    .tier-jump-btn {
      padding: 4px 10px;
      border: 1px solid transparent;
      background-color: transparent;
      color: var(--on-surface-variant);
      font-family: var(--font-headline);
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      cursor: pointer;
      white-space: nowrap;
      display: inline-flex;
      align-items: center;
      gap: 5px;
      transition: all 0.1s ease;
      border-radius: 2px;
    }
    .tier-jump-btn:hover {
      color: var(--on-surface);
      background-color: var(--surface-container-high);
    }
    .tier-jump-btn.active {
      background-color: var(--primary-container);
      color: var(--on-primary-container);
      border-color: var(--border-color);
      font-weight: 800;
      box-shadow: 1px 1px 0px var(--shadow-color);
    }
    .tier-jump-btn:active {
      transform: translate(1px, 1px);
      box-shadow: none;
    }

    .tier-level-dot {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      border: 1px solid rgba(0, 0, 0, 0.2);
      display: inline-block;
      flex-shrink: 0;
    }

    .tier-jump-count {
      font-family: var(--font-mono);
      font-size: 9px;
      opacity: 0.85;
      background: rgba(0, 0, 0, 0.1);
      padding: 1px 4px;
      border-radius: 2px;
    }
    html.dark .tier-jump-count {
      background: rgba(255, 255, 255, 0.15);
    }

    /* CLUSTER CARDS WITH STRUCTURED INDEXING */
    .cluster-box {
      border: 2px solid var(--border-color);
      background-color: var(--surface-container-lowest);
      margin-bottom: 14px;
      box-shadow: 2px 2px 0px var(--shadow-color);
    }

    .cluster-header {
      padding: 12px 16px;
      background-color: var(--surface-container-low);
      border-bottom: 1px solid var(--border-color);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }

    .cluster-code-pill {
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 800;
      padding: 2px 7px;
      background-color: var(--primary);
      color: #ffffff;
      border: 1px solid var(--border-color);
      letter-spacing: 0.03em;
      flex-shrink: 0;
    }
    html.dark .cluster-code-pill {
      background-color: var(--surface-container-highest);
      color: var(--primary-container);
    }

    .cluster-name {
      font-family: var(--font-headline);
      font-size: 13px;
      font-weight: 700;
      text-transform: uppercase;
      color: var(--on-surface);
      letter-spacing: -0.01em;
    }

    .cluster-meta-right {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-shrink: 0;
    }

    .cluster-progress-micro-bar {
      width: 60px;
      height: 6px;
      border: 1px solid var(--border-color);
      background-color: var(--surface-container-high);
      overflow: hidden;
    }

    .cluster-progress-micro-fill {
      height: 100%;
      background-color: var(--emerald-light);
      transition: width 0.3s ease;
    }

    .cluster-stats-pill {
      font-family: var(--font-mono);
      font-size: 10px;
      font-weight: 700;
      color: var(--on-surface-variant);
      white-space: nowrap;
    }

    /* TOPIC INDEX BADGE & COMPACT GRID */
    .topic-index-badge {
      font-family: var(--font-mono);
      font-size: 10px;
      font-weight: 700;
      padding: 2px 6px;
      background-color: var(--surface-container-high);
      color: var(--on-surface-variant);
      border: 1px solid var(--border-color);
      cursor: pointer;
      user-select: none;
      flex-shrink: 0;
      transition: all 0.1s ease;
    }
    .topic-index-badge:hover {
      background-color: var(--primary-container);
      color: #1a1a1a;
      border-color: #1a1a1a;
    }

    .view-mode-toggle {
      display: inline-flex;
      border: 1px solid var(--border-color);
      background-color: var(--surface-container-lowest);
      box-shadow: 1px 1px 0px var(--shadow-color);
      overflow: hidden;
      height: 34px;
      border-radius: 2px;
    }

    .view-mode-btn {
      padding: 0 10px;
      height: 100%;
      font-family: var(--font-headline);
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      background: transparent;
      border: none;
      border-right: 1px solid var(--border-color);
      cursor: pointer;
      color: var(--on-surface-variant);
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 4px;
      transition: all 0.1s ease;
    }
    .view-mode-btn:last-child {
      border-right: none;
    }
    .view-mode-btn:hover {
      background-color: var(--surface-container-high);
      color: var(--on-surface);
    }
    .view-mode-btn.active {
      background-color: var(--primary-container);
      color: #1a1a1a;
      font-weight: 800;
    }

    .compact-grid-mode .tier-content {
      display: grid !important;
      grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
      gap: 14px;
      padding: 14px;
    }
    .compact-grid-mode .cluster-box {
      margin-bottom: 0;
      display: flex;
      flex-direction: column;
    }
    .compact-grid-mode .topic-list-row {
      padding: 8px 12px;
      gap: 8px;
    }
    .compact-grid-mode .topic-title-text {
      font-size: 12px;
    }
    .compact-grid-mode .topic-actions .btn-ghost {
      padding: 2px 6px;
      font-size: 10px;
    }
    .compact-grid-mode .topic-actions .btn-ghost span:last-child {
      display: none;
    }

    .topic-list-row {
      padding: 12px 16px;
      border-bottom: 1px solid var(--surface-container-high);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      transition: background-color 0.1s ease;
    }

    .topic-list-row:last-child {
      border-bottom: none;
    }

    .topic-list-row:hover {
      background-color: var(--surface-container-low);
    }

    .topic-left {
      display: flex;
      align-items: center;
      gap: 12px;
      min-width: 0;
    }

    .topic-title-text {
      font-family: var(--font-body);
      font-size: 13px;
      font-weight: 600;
      color: var(--on-surface);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .topic-actions {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-shrink: 0;
    }

    .status-pill {
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      padding: 3px 8px;
      border: 1.5px solid var(--border-color);
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 5px;
      user-select: none;
      transition: all 0.15s cubic-bezier(0.16, 1, 0.3, 1);
      position: relative;
    }

    .status-pill:hover {
      filter: brightness(1.12);
      box-shadow: 2px 2px 0px var(--shadow-color);
      transform: translateY(-1px);
    }

    .status-caret {
      font-size: 14px;
      opacity: 0.75;
      margin-left: -2px;
      transition: transform 0.15s ease;
    }

    .status-pill:hover .status-caret {
      opacity: 1;
      transform: translateY(1px);
    }

    .status-completed {
      background-color: #ecfdf5;
      color: #065f46;
      border-color: #10b981;
    }
    html.dark .status-completed {
      background-color: #064e3b;
      color: #a7f3d0;
      border-color: #059669;
    }

    .status-active {
      background-color: var(--primary-container);
      color: #1a1a1a;
      border-color: var(--border-color);
    }
    html.dark .status-active {
      background-color: var(--primary-container);
      color: #000000;
      border-color: var(--primary-container);
    }

    .status-unseen {
      background-color: #f1f5f9;
      color: #475569;
      border-color: #cbd5e1;
    }
    html.dark .status-unseen {
      background-color: #1e293b;
      color: #cbd5e1;
      border-color: #475569;
    }

    .status-option-btn {
      width: 100%;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 12px 16px;
      background: var(--surface-container-low);
      color: var(--on-surface) !important;
      border: 1.5px solid var(--border-color);
      cursor: pointer;
      text-align: left;
      transition: all 0.15s ease;
      border-radius: 4px;
    }
    .status-option-btn:hover {
      background: var(--surface-container-high);
      color: var(--on-surface) !important;
      box-shadow: 2px 2px 0px var(--shadow-color);
      transform: translateY(-1px);
    }
    .status-option-btn.selected {
      border: 2px solid var(--primary-container) !important;
      background: var(--surface-container);
      color: var(--on-surface) !important;
      box-shadow: 3px 3px 0px var(--shadow-color);
    }

    .status-option-title {
      font-family: var(--font-headline);
      font-weight: 800;
      font-size: 13.5px;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      display: flex;
      align-items: center;
      gap: 8px;
      background: transparent !important;
    }
    .status-option-title.opt-title-verified {
      color: #059669 !important;
      background: transparent !important;
    }
    html.dark .status-option-title.opt-title-verified {
      color: #34d399 !important;
      background: transparent !important;
    }
    .status-option-title.opt-title-active {
      color: var(--primary-container) !important;
      background: transparent !important;
    }
    .status-option-title.opt-title-not-started {
      color: var(--on-surface) !important;
      background: transparent !important;
    }
    html.dark .status-option-title.opt-title-not-started {
      color: #f0f6fc !important;
      background: transparent !important;
    }

    .status-option-desc {
      font-size: 11.5px;
      color: var(--on-surface-variant) !important;
      font-family: var(--font-mono);
      margin-top: 3px;
      line-height: 1.4;
    }
    html.dark .status-option-desc {
      color: #94a3b8 !important;
    }

    .status-selected-pill {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 3px 8px;
      border-radius: 3px;
      font-family: var(--font-mono);
      font-size: 10px;
      font-weight: 800;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      flex-shrink: 0;
    }

    .status-selected-pill.verified {
      background: rgba(16, 185, 129, 0.18);
      color: #10b981;
      border: 1px solid #10b981;
    }
    html.dark .status-selected-pill.verified {
      background: #064e3b;
      color: #a7f3d0;
      border: 1px solid #059669;
    }

    .status-selected-pill.active {
      background: rgba(255, 204, 0, 0.18);
      color: #b45309;
      border: 1px solid #d97706;
    }
    html.dark .status-selected-pill.active {
      background: rgba(255, 204, 0, 0.2);
      color: var(--primary-container);
      border: 1px solid var(--primary-container);
    }

    .status-selected-pill.not-started {
      background: var(--surface-container-high);
      color: var(--on-surface-variant);
      border: 1px solid var(--border-color);
    }

    /* REVISION FLASHCARD MODE */
    .revision-deck-container {
      max-width: 860px;
      margin: 10px auto;
    }

    .revision-toolbar {
      max-width: 860px;
      margin: 0 auto 16px auto;
      display: flex;
      flex-direction: column;
      gap: 10px;
      padding: 12px 16px;
      background: var(--surface-container-low);
      border: 2px solid var(--border-color);
      box-shadow: 2px 2px 0px var(--shadow-color);
    }

    .revision-search-row {
      display: flex;
      align-items: center;
      gap: 8px;
      width: 100%;
    }

    .revision-search-wrapper {
      flex: 1;
      width: 100%;
      max-width: none;
    }

    .revision-controls-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      flex-wrap: wrap;
    }

    .revision-filter-group {
      display: flex;
      align-items: center;
      gap: 6px;
      flex-wrap: wrap;
    }

    .revision-filter-btn {
      padding: 5px 12px;
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 700;
      background: var(--surface-container);
      color: var(--on-surface);
      border: 2px solid var(--border-color);
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all 0.1s ease;
    }

    .revision-filter-btn:hover {
      background: var(--surface-container-high);
    }

    .revision-filter-btn.active {
      background: var(--primary-container);
      color: #000;
      border-color: #000;
      box-shadow: 2px 2px 0px var(--shadow-color);
    }

    .revision-filter-btn .badge {
      padding: 1px 5px;
      font-size: 10px;
      background: rgba(0,0,0,0.15);
      border-radius: 2px;
    }

    .revision-filter-btn.active .badge {
      background: #000;
      color: #ffcc00;
    }

    .revision-view-toggle {
      display: inline-flex;
      border: 2px solid var(--border-color);
    }

    .revision-view-toggle .view-toggle-btn {
      padding: 5px 10px;
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 700;
      background: var(--surface-container);
      color: var(--on-surface-variant);
      border: none;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 4px;
    }

    .revision-view-toggle .view-toggle-btn.active {
      background: var(--on-surface);
      color: var(--surface);
    }

    .flashcard {
      border: 3px solid var(--border-color);
      background-color: var(--surface-container-lowest);
      box-shadow: 8px 8px 0px var(--shadow-color);
      padding: 18px 24px;
      min-height: 360px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      position: relative;
    }

    .flashcard-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 10px;
      padding-bottom: 8px;
      border-bottom: 2px solid var(--border-color);
      flex-wrap: wrap;
      gap: 8px;
    }

    .flashcard-challenge-pill {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      padding: 3px 8px;
      font-family: var(--font-mono);
      font-size: 10px;
      font-weight: 800;
      background: #00f0ff;
      color: #000;
      border: 2px solid #000;
      letter-spacing: 0.5px;
      text-transform: uppercase;
      box-shadow: 2px 2px 0px #000;
    }

    .flashcard-prompt-text {
      font-family: var(--font-headline);
      font-size: 18px;
      font-weight: 700;
      line-height: 1.35;
      color: var(--on-surface);
      margin: 8px 0 6px 0;
    }

    .flashcard-trap-box {
      background: var(--surface-container-low);
      border: 2px dashed var(--border-color);
      padding: 6px 10px;
      margin: 6px 0 8px 0;
      font-size: 11.5px;
      line-height: 1.4;
    }

    .flashcard-revealed-grid {
      display: grid;
      grid-template-columns: 1fr;
      gap: 8px;
      margin-top: 8px;
    }

    @media (min-width: 768px) {
      .flashcard-revealed-grid {
        grid-template-columns: 1fr 1fr;
      }
    }

    .defense-card-section {
      background: var(--surface-container-low);
      padding: 8px 12px;
      border: 2px solid var(--border-color);
      display: flex;
      flex-direction: column;
      gap: 3px;
    }

    .defense-card-section.invariant-sec {
      border-left: 5px solid #10b981;
    }

    .defense-card-section.failure-sec {
      border-left: 5px solid #ef4444;
    }

    .defense-card-section.formula-sec {
      border-left: 5px solid #3b82f6;
    }

    .defense-card-section.rule-sec {
      border-left: 5px solid #f59e0b;
    }

    .defense-section-label {
      font-family: var(--font-mono);
      font-size: 10px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      display: flex;
      align-items: center;
      gap: 4px;
    }

    .defense-section-body {
      font-family: var(--font-body);
      font-size: 12px;
      line-height: 1.45;
      color: var(--on-surface);
    }

    .defense-section-body.mono {
      font-family: var(--font-mono);
      font-size: 11px;
      background: var(--surface-container-high);
      padding: 4px 6px;
      border-radius: 2px;
      word-break: break-word;
    }

    .flashcard-ratings {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-top: 10px;
      flex-wrap: wrap;
    }

    .flashcard-nav-controls {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-top: 10px;
      padding-top: 8px;
      border-top: 2px solid var(--border-color);
      gap: 8px;
      flex-wrap: wrap;
    }

    /* REVISION GRID VIEW */
    .revision-grid-container {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
      gap: 16px;
      margin-top: 10px;
    }

    .revision-grid-card {
      background: var(--surface-container-lowest);
      border: 2px solid var(--border-color);
      box-shadow: 4px 4px 0px var(--shadow-color);
      padding: 18px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      gap: 12px;
      transition: transform 0.1s ease;
    }

    .revision-grid-card:hover {
      transform: translateY(-2px);
    }

    /* SHARED WORKBENCH DIALOG MODAL BOX (LESSONS & STUDY NOTES) */
    .modal-box.workbench-modal-box,
    .modal-box.note-dialog-box,
    .modal-box.lesson-dialog-box {
      width: 94% !important;
      max-width: 1040px !important;
      height: 86vh !important;
      max-height: 86vh !important;
      background-color: var(--surface-container-lowest);
      border: 3px solid var(--border-color);
      box-shadow: 6px 6px 0px var(--shadow-color);
      display: flex;
      flex-direction: column;
      padding: 20px 24px;
      position: relative;
      transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    }

    .note-dialog-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding-bottom: 14px;
      border-bottom: 2px solid var(--border-color);
      gap: 16px;
      flex-shrink: 0;
    }

    .note-modal-subtitle-row {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
      margin-top: 4px;
    }

    .note-path-badge {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      font-family: var(--font-mono);
      font-size: 11px;
      color: var(--on-surface-variant);
      background: var(--surface-container-high);
      padding: 3px 8px;
      border: 1px solid var(--border-color);
      max-width: 480px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      word-break: keep-all;
    }

    #note-path-text {
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      display: inline-block;
      max-width: 420px;
    }

    .note-stats-badge {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      font-family: var(--font-mono);
      font-size: 11px;
      color: var(--on-surface-variant);
      background: var(--surface-container-high);
      padding: 3px 8px;
      border: 1px solid var(--border-color);
      white-space: nowrap;
    }

    /* NOTION-STYLE NOTE EDITOR WORKBENCH */
    .note-editor-toolbar {
      display: flex;
      align-items: center;
      gap: 4px;
      padding: 6px 10px;
      background: var(--surface-container-high);
      border: 1.5px solid var(--border-color);
      border-bottom: none;
      flex-wrap: wrap;
    }

    .notion-tool-btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      height: 28px;
      min-width: 28px;
      padding: 0 6px;
      background: transparent;
      border: 1px solid transparent;
      color: var(--on-surface-variant);
      cursor: pointer;
      border-radius: 3px;
      font-family: var(--font-headline);
      font-size: 11px;
      font-weight: 700;
      transition: all 0.12s ease;
    }

    .notion-tool-btn:hover {
      background: var(--surface-container-highest);
      color: var(--on-surface);
      border-color: var(--border-color);
    }

    .toolbar-divider {
      width: 1px;
      height: 18px;
      background: var(--border-color);
      margin: 0 4px;
    }

    /* UNIVERSAL SDS HIGHLIGHT SYSTEM */
    .sds-highlight {
      border-radius: 2px;
      padding: 1px 3px;
      cursor: pointer;
      position: relative;
      transition: all 0.15s ease;
      font-weight: 500;
    }
    .sds-highlight:hover {
      filter: brightness(0.95);
      outline: 1px dashed currentColor;
    }
    .sds-hl-yellow {
      background-color: #fef08a !important;
      color: #1a1a1a !important;
      border-bottom: 2px solid #eab308;
    }
    html.dark .sds-hl-yellow, .dark .sds-hl-yellow {
      background-color: rgba(250, 204, 21, 0.35) !important;
      color: #fef08a !important;
      border-bottom: 2px solid #facc15;
    }
    .sds-hl-emerald {
      background-color: #a7f3d0 !important;
      color: #064e3b !important;
      border-bottom: 2px solid #10b981;
    }
    html.dark .sds-hl-emerald, .dark .sds-hl-emerald {
      background-color: rgba(16, 185, 129, 0.3) !important;
      color: #6ee7b7 !important;
      border-bottom: 2px solid #10b981;
    }
    .sds-hl-cyan {
      background-color: #bae6fd !important;
      color: #0369a1 !important;
      border-bottom: 2px solid #0284c7;
    }
    html.dark .sds-hl-cyan, .dark .sds-hl-cyan {
      background-color: rgba(56, 189, 248, 0.3) !important;
      color: #7dd3fc !important;
      border-bottom: 2px solid #38bdf8;
    }

    .highlighter-controls-group {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      padding: 2px 6px;
      background: var(--surface-container-high);
      border: 1px solid var(--border-color);
      border-radius: 3px;
      box-shadow: 1px 1px 0px var(--shadow-color);
    }
    .hl-swatch-btn {
      width: 18px;
      height: 18px;
      border-radius: 50%;
      border: 1.5px solid var(--border-color);
      cursor: pointer;
      padding: 0;
      transition: transform 0.1s ease;
      flex-shrink: 0;
    }
    .hl-swatch-btn:hover {
      transform: scale(1.18);
    }
    .hl-swatch-btn:active {
      transform: scale(0.9);
    }
    .hl-swatch-btn.yellow { background: #facc15; }
    .hl-swatch-btn.emerald { background: #10b981; }
    .hl-swatch-btn.cyan { background: #00e5ff; }

    .note-workbench-layout {
      flex: 1;
      min-height: 0;
      display: flex;
      border: 1.5px solid var(--border-color);
      background: var(--surface);
      position: relative;
      overflow: hidden;
    }

    .note-editor-pane {
      flex: 1;
      height: 100%;
      border: none;
      background: var(--surface-container);
      color: var(--on-surface);
      padding: 16px;
      font-family: var(--font-mono);
      font-size: 12.5px;
      line-height: 1.65;
      resize: none;
      outline: none;
      overflow-y: auto;
      box-sizing: border-box;
    }

    .note-preview-pane {
      flex: 1;
      height: 100%;
      overflow-y: auto;
      padding: 20px 24px;
      background: var(--surface);
      box-sizing: border-box;
      border-left: 1.5px solid var(--border-color);
    }

    .note-view-pane {
      flex: 1;
      height: 100%;
      overflow-y: auto;
      padding: 20px 24px;
      background: var(--surface);
      box-sizing: border-box;
    }

    /* NOTION TABLE & UNIVERSAL MARKDOWN RENDERING */
    .table-responsive-wrapper {
      width: 100%;
      overflow-x: auto;
      margin: 18px 0;
      border: 2px solid var(--border-color);
      box-shadow: 3px 3px 0px var(--shadow-color);
      background: var(--surface-container-lowest);
      -webkit-overflow-scrolling: touch;
    }

    .notion-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
      text-align: left;
      min-width: 520px;
    }

    .notion-table th {
      background-color: var(--surface-container-high);
      font-family: var(--font-headline);
      font-weight: 700;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      padding: 10px 14px;
      border-bottom: 2px solid var(--border-color);
      border-right: 1px solid var(--border-color);
      color: var(--on-surface);
      white-space: nowrap;
    }

    .notion-table td {
      padding: 10px 14px;
      border-bottom: 1px solid var(--border-color);
      border-right: 1px solid var(--border-color);
      color: var(--on-surface);
      line-height: 1.6;
      vertical-align: top;
    }

    .notion-table tr:last-child td {
      border-bottom: none;
    }

    .notion-table th:last-child,
    .notion-table td:last-child {
      border-right: none;
    }

    .notion-table tbody tr:nth-child(even) td {
      background-color: var(--surface-container-low);
    }

    .notion-table tbody tr:hover td {
      background-color: var(--surface-container);
    }

    .notion-task-list {
      list-style: none;
      padding-left: 0;
      margin: 14px 0;
    }

    .notion-task-item {
      display: flex;
      align-items: flex-start;
      gap: 10px;
      padding: 4px 0;
      font-size: 13px;
      line-height: 1.5;
    }

    .notion-task-item.checked span {
      text-decoration: line-through;
      opacity: 0.6;
    }

    .notion-checkbox {
      appearance: none;
      width: 16px;
      height: 16px;
      border: 1.5px solid var(--border-color);
      border-radius: 3px;
      background: var(--surface-container);
      cursor: pointer;
      margin-top: 2px;
      display: inline-grid;
      place-content: center;
      flex-shrink: 0;
    }

    .notion-checkbox:checked {
      background: var(--primary-container);
      border-color: var(--border-color);
    }

    .notion-checkbox:checked::before {
      content: "";
      width: 8px;
      height: 8px;
      clip-path: polygon(14% 44%, 0 65%, 50% 100%, 100% 16%, 80% 0%, 43% 62%);
      background-color: #1a1a1a;
    }

    .notion-inline-code {
      font-family: var(--font-mono);
      font-size: 12px;
      background: var(--surface-container-high);
      color: var(--primary-container);
      padding: 2px 6px;
      border-radius: 3px;
      border: 1px solid var(--border-color);
    }

    .notion-quote {
      border-left: 4px solid var(--primary-container);
      background-color: var(--surface-container-low);
      padding: 12px 18px;
      margin: 18px 0;
      font-size: 13px;
      line-height: 1.65;
    }

    .notion-hr {
      border: none;
      border-top: 2px solid var(--border-color);
      margin: 28px 0;
    }

    .notion-link {
      color: var(--tertiary);
      text-decoration: underline;
      text-underline-offset: 3px;
    }

    .notion-h1 {
      font-family: var(--font-headline);
      font-size: 24px;
      font-weight: 800;
      text-transform: uppercase;
      margin: 24px 0 14px 0;
      padding-bottom: 8px;
      border-bottom: 3px solid var(--primary-container);
      color: var(--on-surface);
    }

    .notion-h2 {
      font-family: var(--font-headline);
      font-size: 18px;
      font-weight: 700;
      text-transform: uppercase;
      margin: 26px 0 12px 0;
      padding-bottom: 6px;
      border-bottom: 2px solid var(--border-color);
      color: var(--on-surface);
    }

    .notion-h3 {
      font-family: var(--font-headline);
      font-size: 15px;
      font-weight: 700;
      text-transform: uppercase;
      margin: 20px 0 10px 0;
      color: var(--on-surface);
    }

    .notion-p {
      margin: 12px 0;
      font-size: 13.5px;
      line-height: 1.75;
      color: var(--on-surface);
    }

    .notion-bullet-list,
    .notion-ordered-list {
      margin: 12px 0;
      padding-left: 24px;
      line-height: 1.7;
      font-size: 13.5px;
    }

    .code-block-container {
      border: 2px solid var(--border-color);
      background-color: #0d1117;
      color: #c9d1d9;
      margin: 20px 0;
      box-shadow: 3px 3px 0px var(--shadow-color);
      overflow: hidden;
    }

    .code-block-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 8px 14px;
      background-color: #161b22;
      border-bottom: 1px solid #30363d;
      font-family: var(--font-headline);
      font-size: 11px;
      font-weight: 700;
      color: var(--primary-container);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .code-copy-btn {
      background: transparent;
      border: 1px solid #30363d;
      color: #8b949e;
      cursor: pointer;
      padding: 3px 6px;
      border-radius: 3px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      transition: all 0.15s ease;
    }

    .code-copy-btn:hover {
      color: #fff;
      background: #30363d;
    }

    .code-block-container pre {
      padding: 16px;
      margin: 0;
      overflow-x: auto;
      font-family: var(--font-mono);
      font-size: 12px;
      line-height: 1.55;
      background: transparent;
      border: none;
      box-shadow: none;
      color: #e6edf3;
    }

    /* LESSON & SIMULATOR DIALOG (MATCHES NOTES MODAL WITH FULLSCREEN SUPPORT) */
    .lesson-dialog-box {
      width: 94%;
      max-width: 1040px;
      height: 86vh;
      max-height: 86vh;
      background-color: var(--surface-container-lowest);
      border: 3px solid var(--border-color);
      box-shadow: 6px 6px 0px var(--shadow-color);
      display: flex;
      flex-direction: column;
      padding: 20px 24px;
      position: relative;
      transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    }

    .lesson-dialog-box.is-fullscreen {
      position: fixed !important;
      inset: 0 !important;
      width: 100vw !important;
      max-width: 100vw !important;
      height: 100vh !important;
      max-height: 100vh !important;
      margin: 0 !important;
      border: none !important;
      box-shadow: none !important;
      padding: 16px 24px !important;
      z-index: 1002;
      background-color: var(--surface);
    }

    .lesson-dialog-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding-bottom: 14px;
      border-bottom: 2px solid var(--border-color);
      gap: 16px;
      flex-shrink: 0;
    }

    .lesson-dialog-body {
      flex: 1;
      min-height: 0;
      display: flex;
      flex-direction: column;
      position: relative;
      margin-top: 14px;
      border: 2px solid var(--border-color);
      background-color: var(--surface);
      overflow: hidden;
    }

    .lesson-iframe {
      width: 100%;
      height: 100%;
      border: none;
      background-color: #ffffff;
      flex: 1;
    }

    .format-pill-group {
      display: inline-flex;
      border: 2px solid var(--border-color);
      background-color: var(--surface-container-low);
      padding: 2px;
      gap: 2px;
    }

    .format-pill-btn {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      padding: 4px 10px;
      font-family: var(--font-headline);
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      border: none;
      background: transparent;
      color: var(--on-surface-variant);
      cursor: pointer;
      transition: all 0.15s ease;
    }

    .format-pill-btn:hover {
      color: var(--on-surface);
      background-color: var(--surface-container-high);
    }

    .format-pill-btn.active {
      background-color: var(--primary-container);
      color: var(--on-primary-container);
      box-shadow: 1px 1px 0px var(--shadow-color);
    }

    /* ARTIFACT-GRADE STYLED MARKDOWN */
    .lesson-artifact-view {
      flex: 1;
      width: 100%;
      height: 100%;
      overflow-y: auto;
      padding: 32px 40px;
      max-width: 900px;
      margin: 0 auto;
      box-sizing: border-box;
      line-height: 1.75;
    }

    .lesson-artifact-view h1 {
      font-family: var(--font-headline);
      font-size: 26px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: -0.01em;
      margin: 0 0 16px 0;
      padding-bottom: 10px;
      border-bottom: 3px solid var(--primary-container);
      color: var(--on-surface);
    }

    .lesson-artifact-view h2 {
      font-family: var(--font-headline);
      font-size: 19px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.02em;
      margin: 32px 0 12px 0;
      padding-bottom: 6px;
      border-bottom: 2px solid var(--border-color);
      color: var(--on-surface);
    }

    .lesson-artifact-view h3 {
      font-family: var(--font-headline);
      font-size: 15px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.03em;
      margin: 24px 0 10px 0;
      color: var(--on-surface);
    }

    .lesson-artifact-view p {
      margin: 14px 0;
      font-size: 14px;
      line-height: 1.8;
      color: var(--on-surface);
    }

    .lesson-artifact-view hr {
      border: none;
      border-top: 2px solid var(--border-color);
      margin: 28px 0;
    }

    .lesson-artifact-view blockquote {
      border-left: 4px solid var(--primary-container);
      background-color: var(--surface-container-low);
      padding: 12px 18px;
      margin: 18px 0;
      font-size: 13px;
      line-height: 1.65;
    }

    .lesson-artifact-view .lead-meta {
      border: 2px solid var(--border-color);
      background-color: var(--surface-container-low);
      border-left: 5px solid var(--primary-container);
      box-shadow: 2px 2px 0px var(--shadow-color);
      padding: 12px 16px;
      margin: 16px 0 24px 0;
      font-family: var(--font-mono);
      font-size: 12px;
      line-height: 1.6;
    }

    .lesson-artifact-view .callout-alert {
      border: 2px solid var(--border-color);
      padding: 14px 18px;
      margin: 20px 0;
      box-shadow: 3px 3px 0px var(--shadow-color);
    }

    .lesson-artifact-view .callout-alert.alert-important {
      border-left: 5px solid var(--secondary);
      background-color: rgba(220, 38, 38, 0.06);
    }

    .lesson-artifact-view .callout-alert.alert-note {
      border-left: 5px solid var(--tertiary);
      background-color: rgba(0, 85, 255, 0.06);
    }

    .lesson-artifact-view .callout-alert.alert-tip,
    .lesson-artifact-view .callout-alert.alert-invariant {
      border-left: 5px solid var(--emerald);
      background-color: rgba(5, 150, 105, 0.06);
    }

    .lesson-artifact-view .callout-alert.alert-warning {
      border-left: 5px solid #f59e0b;
      background-color: rgba(245, 158, 11, 0.06);
    }

    .lesson-artifact-view .callout-header {
      display: flex;
      align-items: center;
      gap: 6px;
      font-family: var(--font-headline);
      font-size: 12px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      margin-bottom: 8px;
    }

    .lesson-artifact-view .diagram-box {
      border: 2px solid var(--border-color);
      background-color: #0d1117;
      color: #c9d1d9;
      margin: 20px 0;
      box-shadow: 3px 3px 0px var(--shadow-color);
      overflow: hidden;
    }

    .lesson-artifact-view .diagram-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 8px 14px;
      background-color: #161b22;
      border-bottom: 1px solid #30363d;
      font-family: var(--font-headline);
      font-size: 11px;
      font-weight: 700;
      color: #ffcc00;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .lesson-artifact-view .diagram-box pre {
      padding: 16px;
      margin: 0;
      overflow-x: auto;
      font-family: var(--font-mono);
      font-size: 12px;
      line-height: 1.55;
      background: transparent;
      border: none;
      box-shadow: none;
      color: #e6edf3;
    }

    .lesson-artifact-view table {
      width: 100%;
      border-collapse: collapse;
      margin: 24px 0;
      border: 2px solid var(--border-color);
      box-shadow: 3px 3px 0px var(--shadow-color);
      font-size: 13px;
    }

    .lesson-artifact-view th {
      background-color: var(--surface-container-high);
      font-family: var(--font-headline);
      font-weight: 700;
      text-transform: uppercase;
      font-size: 11px;
      letter-spacing: 0.05em;
      padding: 10px 14px;
      border: 1px solid var(--border-color);
      color: var(--on-surface);
      text-align: left;
    }

    .lesson-artifact-view td {
      padding: 10px 14px;
      border: 1px solid var(--border-color);
      line-height: 1.55;
    }

    .lesson-artifact-view tr:nth-child(even) td {
      background-color: var(--surface-container-low);
    }

    /* TACTILE BAUHAUS TOAST */
    #studio-toast {
      position: fixed;
      bottom: 24px;
      right: 24px;
      z-index: 9999;
      display: none;
      padding: 10px 18px;
      border: 2px solid var(--border-color);
      background-color: var(--primary-container);
      color: #1a1a1a;
      font-family: var(--font-headline);
      font-size: 12px;
      font-weight: 800;
      text-transform: uppercase;
      box-shadow: 4px 4px 0px var(--shadow-color);
      pointer-events: none;
      transition: opacity 0.2s ease;
    }

    /* MODALS GENERIC WITH TACTILE SCALE TRANSITION */
    .modal-overlay {
      position: fixed;
      inset: 0;
      z-index: 900;
      background-color: rgba(0, 0, 0, 0.72);
      backdrop-filter: blur(2px);
      -webkit-backdrop-filter: blur(2px);
      display: none;
      align-items: center;
      justify-content: center;
      padding: 20px;
      opacity: 0;
      transition: opacity 0.15s cubic-bezier(0.16, 1, 0.3, 1);
    }

    .modal-overlay.active {
      display: flex;
      opacity: 1;
    }

    .modal-box {
      width: 100%;
      max-width: 640px;
      background-color: var(--surface-container-lowest);
      border: 3px solid var(--border-color);
      box-shadow: 6px 6px 0px var(--shadow-color);
      padding: 26px;
      position: relative;
      transform: scale(0.97) translateY(6px);
      transition: transform 0.18s cubic-bezier(0.16, 1, 0.3, 1);
    }

    .modal-overlay.active .modal-box {
      transform: scale(1) translateY(0);
    }

    /* TACTILE PHYSICAL BUTTON PRESS (NEO-BRUTALIST ACTION) */
    .btn-primary:active,
    .btn-ghost:active,
    .format-pill-btn:active,
    .filter-pill:active,
    .icon-action-btn:active,
    .focus-action-btn:active {
      transform: translate(2px, 2px) !important;
      box-shadow: 1px 1px 0px var(--shadow-color) !important;
    }

    /* KEYBOARD SHORTCUTS HUD */
    kbd {
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 700;
      background-color: var(--surface-container-high);
      color: var(--on-surface);
      border: 2px solid var(--border-color);
      box-shadow: 2px 2px 0px var(--shadow-color);
      padding: 2px 7px;
      display: inline-block;
      user-select: none;
    }
    .shortcut-group {
      border: 1px solid var(--border-color);
      background-color: var(--surface-container-low);
      padding: 10px 14px;
      margin-bottom: 8px;
    }
    .shortcut-group:last-child {
      margin-bottom: 0;
    }
    .shortcut-group-title {
      font-family: var(--font-headline);
      font-size: 10px;
      font-weight: 800;
      letter-spacing: 0.08em;
      color: var(--primary-container);
      margin-bottom: 8px;
    }
    html:not(.dark) .shortcut-group-title {
      color: #996500;
    }
    .shortcut-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-size: 12px;
      font-family: var(--font-body);
      color: var(--on-surface);
      padding: 4px 0;
      border-bottom: 1px solid rgba(128, 128, 128, 0.15);
    }
    .shortcut-row:last-child {
      border-bottom: none;
    }

    /* FORWARD-ASSISTED ARCHITECTURAL FOCUS STRIP (CALM & COMPACT) */
    .focus-strip {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 5px 12px;
      background-color: var(--surface-container-low);
      border: 1px solid var(--border-color);
      border-left: 4px solid var(--primary-container);
      box-shadow: 1px 1px 0px var(--shadow-color);
      margin-bottom: 12px;
      flex-wrap: wrap;
      transition: all 0.15s ease;
      border-radius: 2px;
    }
    .focus-strip-left {
      display: flex;
      align-items: center;
      gap: 8px;
      min-width: 0;
      flex: 1;
    }
    .focus-strip-label {
      font-family: var(--font-mono);
      font-size: 10px;
      font-weight: 800;
      letter-spacing: 0.05em;
      color: var(--primary-container);
      white-space: nowrap;
    }
    html:not(.dark) .focus-strip-label {
      color: #92400e;
    }
    .focus-strip-title {
      font-family: var(--font-body);
      font-size: 12px;
      font-weight: 700;
      color: var(--on-surface);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .focus-strip-tag {
      font-family: var(--font-mono);
      font-size: 10px;
      padding: 1px 5px;
      background: var(--surface-container-high);
      border: 1px solid var(--border-color);
      color: var(--on-surface-variant);
      white-space: nowrap;
    }
    .focus-strip-actions {
      display: flex;
      align-items: center;
      gap: 6px;
      flex-shrink: 0;
    }
    .focus-action-btn {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 3px 8px;
      height: 26px;
      font-family: var(--font-headline);
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.03em;
      border: 1px solid var(--border-color);
      box-shadow: 1px 1px 0px var(--shadow-color);
      cursor: pointer;
      transition: all 0.1s ease;
      border-radius: 2px;
    }
    .focus-action-btn.primary {
      background-color: var(--primary-container);
      color: #1a1a1a;
    }
    .focus-action-btn.primary:hover {
      filter: brightness(1.08);
    }
    .focus-action-btn.ghost {
      background-color: var(--surface-container-lowest);
      color: var(--on-surface);
      font-family: var(--font-mono);
      font-size: 10px;
    }
    .focus-action-btn.ghost:hover {
      background-color: var(--surface-container-high);
    }

    /* SEARCH MATCH COUNTER & QUICK TAGS */
    .search-count-badge {
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 700;
      color: var(--on-surface-variant);
      padding: 4px 8px;
      background: var(--surface-container-high);
      border: 1px solid var(--border-color);
      white-space: nowrap;
    }
    .quick-tags-row {
      display: flex;
      align-items: center;
      gap: 6px;
      margin-top: 10px;
      width: 100%;
      flex-wrap: wrap;
    }
    .quick-tag-chip {
      font-family: var(--font-mono);
      font-size: 10px;
      font-weight: 600;
      padding: 2px 7px;
      border: 1px solid var(--border-color);
      background-color: var(--surface-container-lowest);
      color: var(--on-surface-variant);
      cursor: pointer;
      transition: all 0.1s ease;
    }
    .quick-tag-chip:hover {
      background-color: var(--primary-container);
      color: #1a1a1a;
      border-color: var(--border-color);
      box-shadow: 1px 1px 0px var(--shadow-color);
    }
    .empty-search-box {
      border: 2px dashed var(--border-color);
      background-color: var(--surface-container-low);
      padding: 40px 24px;
      text-align: center;
      margin: 20px 0;
      box-shadow: 3px 3px 0px var(--shadow-color);
    }

    /* ACTIVE FOCUS TOPIC ROW PULSE */
    .topic-list-row.active-focus-row {
      border-left: 4px solid var(--primary-container);
      background-color: var(--surface-container);
    }
    .active-focus-pill {
      font-family: var(--font-mono);
      font-size: 9px;
      font-weight: 800;
      background-color: var(--primary-container);
      color: #1a1a1a;
      padding: 1px 6px;
      display: inline-flex;
      align-items: center;
      gap: 4px;
      margin-left: 6px;
      letter-spacing: 0.05em;
    }

    /* REVISION PROGRESS BAR & ANIMATIONS */
    .revision-progress-bar {
      height: 4px;
      width: 100%;
      background-color: var(--surface-container-high);
      border: 1px solid var(--border-color);
      margin-top: 10px;
      overflow: hidden;
    }
    .revision-progress-fill {
      height: 100%;
      background-color: var(--primary-container);
      transition: width 0.25s ease;
    }
    .flashcard-revealed-box {
      animation: flashcard-reveal-in 0.22s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }
    @keyframes flashcard-reveal-in {
      from { opacity: 0; transform: translateY(8px); }
      to { opacity: 1; transform: translateY(0); }
    }

    .modal-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 20px;
      padding-bottom: 12px;
      border-bottom: 2px solid var(--border-color);
    }

    .modal-close-btn {
      background: transparent;
      border: none;
      font-size: 18px;
      font-weight: bold;
      cursor: pointer;
      color: var(--on-surface);
    }

    .form-group {
      margin-bottom: 16px;
    }

    .form-label {
      display: block;
      font-family: var(--font-headline);
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      margin-bottom: 6px;
      color: var(--on-surface);
    }

    .form-input {
      width: 100%;
      padding: 8px 12px;
      border: 2px solid var(--border-color);
      background-color: var(--surface-container-low);
      color: var(--on-surface);
      font-family: var(--font-body);
      font-size: 13px;
      outline: none;
    }

    .form-input:focus {
      border-color: var(--primary-container);
    }

    /* RESPONSIVE BREAKPOINTS (<850px) */
    @media (max-width: 850px) {
      .active-project-pill, .nav-project-dropdown, .version-tag-pill { display: none !important; }
      .studio-header { padding: 0 10px; gap: 8px; }
      .brand-title { display: none; }
      .nav-tabs {
        overflow-x: auto;
        flex: 1;
        white-space: nowrap;
        -webkit-overflow-scrolling: touch;
        scrollbar-width: none;
      }
      .nav-tabs::-webkit-scrollbar { display: none; }
      .nav-tab-btn { padding: 6px 10px; font-size: 11px; }
      .studio-main { padding: 16px 12px 40px 12px; }
      .projects-grid { grid-template-columns: 1fr; }
      .sync-micro-badge span:last-child { display: none; }
    }

    /* TACTILE CONTENT-HUGGING SELECTION (PREVENTS FULL-VIEWPORT HIGHLIGHT SPAN) */
    ::selection {
      background-color: rgba(0, 229, 255, 0.28) !important;
      color: inherit !important;
    }
    html.dark ::selection {
      background-color: rgba(0, 229, 255, 0.32) !important;
      color: inherit !important;
    }
    html::selection,
    html.dark::selection,
    html:not(.dark)::selection,
    body::selection,
    html.dark body::selection,
    html:not(.dark) body::selection,
    main::selection,
    html.dark main::selection,
    html:not(.dark) main::selection,
    section::selection,
    html.dark section::selection,
    html:not(.dark) section::selection,
    article::selection,
    html.dark article::selection,
    html:not(.dark) article::selection,
    header::selection,
    html.dark header::selection,
    html:not(.dark) header::selection,
    footer::selection,
    html.dark footer::selection,
    html:not(.dark) footer::selection {
      background-color: transparent !important;
    }

    /* MARKDOWN & ADR STYLES FOR NOTES, LESSONS & DECISIONS */
    .md-rendered p,
    .md-rendered h1,
    .md-rendered h2,
    .md-rendered h3,
    .md-rendered h4,
    .md-rendered h5,
    .md-rendered h6,
    .md-rendered li,
    .md-rendered blockquote,
    .lesson-artifact-view p,
    .lesson-artifact-view .editorial-lead,
    .lesson-artifact-view h1,
    .lesson-artifact-view h2,
    .lesson-artifact-view h3,
    .lesson-artifact-view h4,
    .lesson-artifact-view li,
    .lesson-artifact-view blockquote,
    .note-view-pane p,
    .note-view-pane h1,
    .note-view-pane h2,
    .note-view-pane h3,
    .note-view-pane h4,
    .note-view-pane li,
    .note-view-pane blockquote,
    .notion-p,
    .notion-h1,
    .notion-h2,
    .notion-h3,
    .notion-quote,
    .notion-callout {
      width: fit-content;
      max-width: 100%;
    }

    .md-rendered h1 { font-family: var(--font-headline); font-size: 26px; font-weight: 800; margin: 24px 0 12px 0; padding-bottom: 8px; border-bottom: 2px solid var(--border-color); }
    .md-rendered h2 { font-family: var(--font-headline); font-size: 20px; font-weight: 700; margin: 20px 0 10px 0; padding-bottom: 6px; border-bottom: 1px solid var(--border-color); }
    .md-rendered h3 { font-family: var(--font-headline); font-size: 16px; font-weight: 700; margin: 16px 0 8px 0; }
    .md-rendered p { margin: 12px 0; font-size: 14px; line-height: 1.7; }
    .md-rendered ul, .md-rendered ol { margin: 12px 0 12px 24px; font-size: 14px; line-height: 1.7; }
    .md-rendered blockquote { border-left: 4px solid var(--primary-container); background: var(--surface-container-low); padding: 10px 16px; margin: 16px 0; font-style: italic; }
    .md-rendered code { font-family: var(--font-mono); font-size: 12px; font-weight: 600; background: var(--surface-container-high); padding: 2px 6px; border: 1px solid var(--border-color); }
    .md-rendered pre { background: var(--primary); color: #ffffff; padding: 14px; border: 2px solid var(--border-color); overflow-x: auto; margin: 16px 0; font-family: var(--font-mono); font-size: 12px; box-shadow: 2px 2px 0px var(--shadow-color); }
    .md-rendered pre code { background: transparent; padding: 0; border: none; color: inherit; }
    .md-rendered table { width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 13px; }
    .md-rendered th, .md-rendered td { border: 1px solid var(--border-color); padding: 8px 12px; text-align: left; }
    .md-rendered th { background-color: var(--surface-container-high); font-family: var(--font-headline); font-weight: 700; }
    .md-rendered tr:nth-child(even) td { background-color: var(--surface-container-low); }
    .md-rendered .lead-meta {
      border: 2px solid var(--border-color);
      background-color: var(--surface-container-low);
      border-left: 5px solid var(--primary-container);
      box-shadow: 2px 2px 0px var(--shadow-color);
      padding: 12px 16px;
      margin: 16px 0 24px 0;
      font-family: var(--font-mono);
      font-size: 12px;
      line-height: 1.6;
    }
    .md-rendered .diagram-box {
      border: 2px solid var(--border-color);
      background-color: #0d1117;
      color: #c9d1d9;
      margin: 20px 0;
      box-shadow: 3px 3px 0px var(--shadow-color);
      overflow: hidden;
    }
    .md-rendered .diagram-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 8px 14px;
      background-color: #161b22;
      border-bottom: 1px solid #30363d;
      font-family: var(--font-headline);
      font-size: 11px;
      font-weight: 700;
      color: #ffcc00;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .md-rendered .diagram-box pre {
      padding: 16px;
      margin: 0;
      overflow-x: auto;
      font-family: var(--font-mono);
      font-size: 12px;
      line-height: 1.55;
      background: transparent;
      border: none;
      box-shadow: none;
      color: #e6edf3;
    }
    .md-rendered .callout-alert {
      border: 2px solid var(--border-color);
      padding: 14px 18px;
      margin: 20px 0;
      box-shadow: 3px 3px 0px var(--shadow-color);
    }
    .md-rendered .callout-alert.alert-important {
      border-left: 5px solid var(--secondary);
      background-color: rgba(220, 38, 38, 0.06);
    }
    .md-rendered .callout-alert.alert-note {
      border-left: 5px solid var(--tertiary);
      background-color: rgba(0, 85, 255, 0.06);
    }
    .md-rendered .callout-alert.alert-tip,
    .md-rendered .callout-alert.alert-invariant {
      border-left: 5px solid var(--emerald);
      background-color: rgba(5, 150, 105, 0.06);
    }
    .md-rendered .callout-alert.alert-warning {
      border-left: 5px solid #f59e0b;
      background-color: rgba(245, 158, 11, 0.06);
    }
    .md-rendered .callout-header {
      display: flex;
      align-items: center;
      gap: 6px;
      font-family: var(--font-headline);
      font-size: 12px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      margin-bottom: 8px;
    }
  </style>
</head>
<body>

  <!-- TOP NAVBAR -->
  <header class="studio-navbar">
    <div class="nav-left">
      <div class="nav-brand" onclick="switchTab('projects')" title="System Design Studio">
        <div class="brand-icon-box" aria-label="Logo">
          <svg viewBox="0 0 256 256" fill="none" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:100%;">
            <path d="M 131 60 A 68 68 0 0 1 131 196" stroke="#1a1a1a" stroke-width="26" stroke-linecap="round"/>
            <path d="M 75 60 L 131 60 L 131 128 L 75 128 L 75 196 L 131 196" stroke="#1a1a1a" stroke-width="26" stroke-linecap="round" stroke-linejoin="round"/>
            <line x1="131" y1="60" x2="131" y2="196" stroke="#1a1a1a" stroke-width="26" stroke-linecap="round"/>
            <circle cx="75" cy="60" r="18" fill="#1a1a1a"/>
            <circle cx="75" cy="196" r="18" fill="#1a1a1a"/>
            <circle cx="165" cy="128" r="20" fill="#dc2626"/>
            <circle cx="131" cy="128" r="14" fill="#ffcc00" stroke="#1a1a1a" stroke-width="8"/>
          </svg>
        </div>
        <span class="brand-title">System Design Studio</span>
      </div>

      <!-- Active Project Dropdown Switcher (Synchronized with Projects Tab) -->
      <div id="nav-project-dropdown-container" class="nav-project-dropdown" title="Active Project (Select to switch workspace)">
        <span class="status-dot"></span>
        <select id="nav-project-select" class="nav-project-select" onchange="handleNavProjectSelect(this.value)" aria-label="Switch active workspace">
          <option value="">Loading workspaces...</option>
        </select>
        <span class="material-symbols-outlined nav-project-caret">unfold_more</span>
      </div>
    </div>

    <!-- Center Nav Tabs -->
    <nav class="nav-tabs">
      <button id="nav-tab-projects" class="nav-tab-btn active" onclick="switchTab('projects')">
        <span class="material-symbols-outlined" style="font-size:15px; margin-right:4px;">dashboard</span>
        <span>Projects</span>
      </button>
      <button id="nav-tab-curriculum" class="nav-tab-btn" onclick="switchTab('curriculum')">
        <span class="material-symbols-outlined" style="font-size:15px; margin-right:4px;">account_tree</span>
        <span>Curriculum Syllabus</span>
      </button>
      <button id="nav-tab-revision" class="nav-tab-btn" onclick="switchTab('revision')">
        <span class="material-symbols-outlined" style="font-size:15px; margin-right:4px;">psychology</span>
        <span>Revision Mode</span>
      </button>
    </nav>

    <!-- Right Actions -->
    <div class="nav-right">
      <div class="sync-micro-badge" title="Real-time disk and Git sync active">
        <span class="status-dot pulse"></span>
        <span>Sync</span>
      </div>

      <!-- Studio Version Badge (Click to check updates) -->
      <button type="button" class="version-tag-pill" id="nav-version-pill" onclick="openSettingsModal('updates')" title="System Design Studio Version (Click to check for updates)">
        <span class="status-dot green" style="width:6px; height:6px;"></span>
        <span id="nav-version-label">v3.7.0</span>
      </button>

      <button aria-label="Refresh data" class="icon-action-btn" onclick="refreshData(true)" type="button" title="Refresh local data">
        <span class="material-symbols-outlined" style="font-size:18px;">refresh</span>
      </button>

      <button aria-label="Keyboard shortcuts guide" class="icon-action-btn" onclick="openShortcutsModal()" type="button" title="Keyboard Shortcuts (?)">
        <span class="material-symbols-outlined" style="font-size:18px;">keyboard</span>
      </button>

      <button aria-label="Toggle dark/light mode" class="icon-action-btn" onclick="toggleTheme()" type="button" title="Toggle Theme">
        <span id="theme-icon" class="material-symbols-outlined" style="font-size:18px;">contrast</span>
      </button>

      <button aria-label="Settings" class="icon-action-btn" onclick="openSettingsModal()" type="button" title="Settings">
        <span class="material-symbols-outlined" style="font-size:18px;">settings</span>
      </button>
    </div>
  </header>

  <!-- EAGER AUTO-UPDATE BANNER (Displayed on page load when update is available) -->
  <div id="eager-update-banner" style="display:none; background:var(--primary-container); color:var(--on-primary-container); padding:8px 16px; border-bottom:2px solid var(--border-color); font-family:var(--font-headline); font-size:12px; font-weight:700; align-items:center; justify-content:space-between; z-index:900;">
    <div style="display:flex; align-items:center; gap:8px;">
      <span class="material-symbols-outlined" style="font-size:18px;">notifications_active</span>
      <span id="eager-update-text">Update available!</span>
    </div>
    <div style="display:flex; align-items:center; gap:8px;">
      <button type="button" class="btn-primary" style="padding:3px 10px; font-size:11px; background:#1a1a1a; color:#ffffff; border-color:#1a1a1a;" onclick="copyUpdateCommand(this)">Copy Update Command</button>
      <button type="button" class="btn-ghost" style="padding:3px 8px; font-size:11px;" onclick="openSettingsModal('updates')">View Details</button>
      <button type="button" class="btn-ghost" style="padding:2px 6px; font-size:14px; border:none;" onclick="dismissUpdateBanner()" title="Dismiss">&times;</button>
    </div>
  </div>

  <!-- MAIN WORKSPACE -->
  <main class="studio-main">

    <!-- PANEL 1: PROJECTS WORKSPACES (CARDS HOME VIEW) -->
    <section id="panel-projects" class="view-panel active">
      <div class="view-header">
        <div>
          <h1 class="view-title">PROJECT WORKSPACES</h1>
          <p class="view-subtitle">Local-first learning instances tracked via Git repositories.</p>
        </div>
        <div style="display:flex; align-items:center; gap:8px;">
          <button class="btn-ghost" onclick="refreshData(true)" title="Rescan disk for workspaces">
            <span class="material-symbols-outlined" style="font-size:16px; margin-right:4px;">sync</span>
            <span>Rescan Disk</span>
          </button>
          <button class="btn-primary" onclick="openNewProjectModal()">
            <span class="material-symbols-outlined" style="font-size:16px;">add</span>
            <span>New Workspace</span>
          </button>
        </div>
      </div>

      <div id="projects-grid" class="projects-grid">
        <!-- Rendered dynamically via loadProjects() -->
      </div>
    </section>

    <!-- PANEL 2: SINGLE UNIFIED CURRICULUM VIEW -->
    <section id="panel-curriculum" class="view-panel">
      <div class="view-header">
        <div>
          <h1 class="view-title" id="curriculum-view-project-title">CURRICULUM SYLLABUS</h1>
          <p class="view-subtitle" id="curriculum-view-meta">Mastery progression, hardware invariants, and interactive lessons.</p>
        </div>
        <div style="display:flex; align-items:center; gap:8px;">
          <button class="btn-ghost" onclick="toggleAllTiers()">
            <span class="material-symbols-outlined" style="font-size:15px;">unfold_more</span>
            <span>Expand / Collapse All</span>
          </button>
          <button class="btn-primary" onclick="openNewNoteModal()">
            <span class="material-symbols-outlined" style="font-size:15px;">post_add</span>
            <span>Quick Note</span>
          </button>
        </div>
      </div>

      <!-- FORWARD-ASSISTED ARCHITECTURAL FOCUS STRIP (CALM & MINIMAL) -->
      <div id="curriculum-focus-strip" class="focus-strip" style="display:none;">
        <div class="focus-strip-left">
          <span class="status-dot pulse" style="background-color:var(--primary-container);"></span>
          <span class="focus-strip-label">ACTIVE FOCUS:</span>
          <span id="focus-strip-topic-title" class="focus-strip-title">Loading active topic...</span>
          <span id="focus-strip-cluster-tag" class="focus-strip-tag"></span>
        </div>
        <div class="focus-strip-actions">
          <button id="btn-focus-open-lesson" class="focus-action-btn primary" title="Open lesson artifact">
            <span class="material-symbols-outlined" style="font-size:14px;">play_arrow</span>
            <span>Open Lesson</span>
          </button>
          <button class="focus-action-btn ghost" onclick="copyAgentCommand('/sds-teach')" title="Copy chat command to deliver lesson">
            <span>/sds-teach</span>
            <span class="material-symbols-outlined copy-icon" style="font-size:11px; opacity:0.6;">content_copy</span>
          </button>
          <button class="focus-action-btn ghost" onclick="copyAgentCommand('/sds-complete')" title="Copy chat command for sign-off verification">
            <span>/sds-complete</span>
            <span class="material-symbols-outlined copy-icon" style="font-size:11px; opacity:0.6;">content_copy</span>
          </button>
        </div>
      </div>

      <!-- CALM UNIFIED CURRICULUM COMMAND BAR -->
      <div class="curriculum-toolbar">
        <div class="toolbar-primary-row">
          <div class="search-input-wrapper">
            <span class="material-symbols-outlined search-leading-icon">search</span>
            <input type="text" id="curriculum-search" class="search-input" placeholder="Search 354 topics, codes (e.g. 0.1.1), or #tags... (Press /)" oninput="handleSearch(this.value)" onkeydown="if(event.key==='Escape'){clearSearch();}" />
            <button id="search-clear-btn" class="search-clear-btn" onclick="clearSearch()" title="Clear search (Esc)">
              <span class="material-symbols-outlined" style="font-size:13px;">close</span>
            </button>
          </div>
          <span id="search-count-badge" class="search-count-badge" style="display:none;"></span>

          <div class="toolbar-actions">
            <!-- Learning Track Filter -->
            <select id="curriculum-track-select" class="toolbar-select" onchange="setTrackFilter(this.value)" title="Filter syllabus by learning track">
              <option value="all">Track: All Syllabus (50 Clusters)</option>
              <option value="interview-sprint">Track: Senior Interview Sprint (15)</option>
              <option value="distributed-core">Track: Distributed Systems (T0 &amp; T2)</option>
              <option value="mobile-offline">Track: Mobile &amp; Offline-First (T0 &amp; T3)</option>
            </select>

            <!-- Topic Completion Status Filter -->
            <select id="curriculum-status-select" class="toolbar-select" onchange="setTopicFilterSelect(this.value)" title="Filter by completion status">
              <option value="all">Status: All Topics</option>
              <option value="active">Status: Active Focus</option>
              <option value="completed">Status: Verified Only</option>
              <option value="unseen">Status: Not Started</option>
            </select>

            <!-- Layout View Mode Switcher -->
            <div class="view-mode-toggle" title="Switch layout">
              <button id="btn-view-standard" class="view-mode-btn active" onclick="setViewMode('standard')" title="Detailed List View">
                <span class="material-symbols-outlined" style="font-size:16px;">view_agenda</span>
              </button>
              <button id="btn-view-compact" class="view-mode-btn" onclick="setViewMode('compact')" title="Compact Index Grid">
                <span class="material-symbols-outlined" style="font-size:16px;">grid_view</span>
              </button>
            </div>
          </div>
        </div>

        <!-- Subtle Inline Quick Tag Links -->
        <div class="search-hints-row" id="search-hints-row">
          <span style="font-weight:700; opacity:0.65;">QUICK TAGS:</span>
          <button class="tag-hint-link" onclick="applySearchTag('transport')">#transport</button>
          <span style="opacity:0.35;">·</span>
          <button class="tag-hint-link" onclick="applySearchTag('database')">#database</button>
          <span style="opacity:0.35;">·</span>
          <button class="tag-hint-link" onclick="applySearchTag('consensus')">#consensus</button>
          <span style="opacity:0.35;">·</span>
          <button class="tag-hint-link" onclick="applySearchTag('cache')">#cache</button>
          <span style="opacity:0.35;">·</span>
          <button class="tag-hint-link" onclick="applySearchTag('mobile')">#mobile</button>
          <span style="opacity:0.35;">·</span>
          <button class="tag-hint-link" onclick="applySearchTag('invariant')">#invariants</button>
          <span style="opacity:0.35;">·</span>
          <button class="tag-hint-link" onclick="applySearchTag('0.1')">#0.1</button>
          <span style="opacity:0.35;">·</span>
          <button class="tag-hint-link" onclick="applySearchTag('2.1')">#2.1</button>
        </div>
      </div>

      <!-- TIER QUICK-JUMP NAVIGATION BAR (SEGMENTED TABS) -->
      <div class="tier-jump-bar" id="tier-jump-bar">
        <button class="tier-jump-btn active" data-tier="all" onclick="setTierFilter('all', this)" title="Show all curriculum tiers">
          <span class="material-symbols-outlined" style="font-size:14px;">apps</span>
          <span>All Tiers</span>
        </button>
        <button class="tier-jump-btn" data-tier="tier.0" onclick="setTierFilter('tier.0', this)" title="Tier 0: HLD Building Blocks">
          <span class="tier-level-dot" style="background:#ffcc00;"></span>
          <span>T0: Primitives</span>
          <span class="tier-jump-count" id="tier-jump-count-0">...</span>
        </button>
        <button class="tier-jump-btn" data-tier="tier.1" onclick="setTierFilter('tier.1', this)" title="Tier 1: Single-Node LLD">
          <span class="tier-level-dot" style="background:#dc2626;"></span>
          <span>T1: In-Process</span>
          <span class="tier-jump-count" id="tier-jump-count-1">...</span>
        </button>
        <button class="tier-jump-btn" data-tier="tier.2" onclick="setTierFilter('tier.2', this)" title="Tier 2: Distributed Systems">
          <span class="tier-level-dot" style="background:#0055ff;"></span>
          <span>T2: Distributed</span>
          <span class="tier-jump-count" id="tier-jump-count-2">...</span>
        </button>
        <button class="tier-jump-btn" data-tier="tier.3" onclick="setTierFilter('tier.3', this)" title="Tier 3: Mobile &amp; Sync">
          <span class="tier-level-dot" style="background:#059669;"></span>
          <span>T3: Mobile &amp; Sync</span>
          <span class="tier-jump-count" id="tier-jump-count-3">...</span>
        </button>
        <button class="tier-jump-btn" data-tier="tier.4" onclick="setTierFilter('tier.4', this)" title="Tier 4: Practice &amp; ADR Defenses">
          <span class="tier-level-dot" style="background:#8b5cf6;"></span>
          <span>T4: Synthesis</span>
          <span class="tier-jump-count" id="tier-jump-count-4">...</span>
        </button>
      </div>

      <!-- Syllabus Tree Accordions -->
      <div id="curriculum-tree-container">
        <!-- Rendered dynamically via renderCurriculum() -->
      </div>
    </section>

    <!-- PANEL 3: REVISION MODE (ACTIVE RECALL FLASHCARDS) -->
    <section id="panel-revision" class="view-panel">
      <div class="view-header" style="flex-wrap:wrap; gap:12px; margin-bottom:12px;">
        <div>
          <h1 class="view-title">INVARIANT REVISION DECK</h1>
          <p class="view-subtitle">Active recall of failure modes, sizing math, and non-negotiable trade-offs derived from accepted ADRs and study notes.</p>
        </div>
        <div id="revision-deck-stats" style="display:flex; align-items:center; gap:8px; font-family:var(--font-mono); font-size:12px; font-weight:700;">
          <span class="badge-status" id="revision-counter">Loading cards...</span>
        </div>
      </div>

      <!-- Revision Deck Controls Toolbar -->
      <div class="revision-toolbar">
        <!-- Top Row: Full-width Search Command Bar -->
        <div class="revision-search-row">
          <div class="search-input-wrapper revision-search-wrapper">
            <span class="material-symbols-outlined search-leading-icon">search</span>
            <input type="text" id="revision-search" class="search-input" placeholder="Search revision cards, formulas, failure modes, invariants... (Press /)" oninput="handleRevisionSearch(this.value)" onkeydown="if(event.key==='Escape'){clearRevisionSearch();}" autocomplete="off">
            <span id="revision-search-count-badge" class="search-count-badge" style="display:none;"></span>
            <button id="revision-search-clear" class="search-clear-btn" onclick="clearRevisionSearch()" title="Clear search (Esc)">
              <span class="material-symbols-outlined" style="font-size:13px;">close</span>
            </button>
          </div>
        </div>

        <!-- Bottom Row: Filter Pills + View Switcher + Shuffle -->
        <div class="revision-controls-row">
          <div class="revision-filter-group">
            <button class="revision-filter-btn active" data-filter="all" onclick="setRevisionFilter('all', this)">ALL <span class="badge" id="rev-count-all">0</span></button>
            <button class="revision-filter-btn" data-filter="due" onclick="setRevisionFilter('due', this)">DUE TODAY <span class="badge" id="rev-count-due">0</span></button>
            <button class="revision-filter-btn" data-filter="needs_review" onclick="setRevisionFilter('needs_review', this)">NEEDS REVIEW <span class="badge" id="rev-count-needs-review">0</span></button>
            <button class="revision-filter-btn" data-filter="learning" onclick="setRevisionFilter('learning', this)">LEARNING <span class="badge" id="rev-count-learning">0</span></button>
            <button class="revision-filter-btn" data-filter="mastered" onclick="setRevisionFilter('mastered', this)">MASTERED <span class="badge" id="rev-count-mastered">0</span></button>
          </div>

          <div style="display:flex; align-items:center; gap:8px;">
            <div class="revision-view-toggle">
              <button id="rev-view-cards" class="view-toggle-btn active" onclick="setRevisionViewMode('card')" title="Card Practice Mode">
                <span class="material-symbols-outlined" style="font-size:15px;">style</span>
                <span>Cards</span>
              </button>
              <button id="rev-view-grid" class="view-toggle-btn" onclick="setRevisionViewMode('grid')" title="Deck Overview Grid">
                <span class="material-symbols-outlined" style="font-size:15px;">grid_view</span>
                <span>Deck Grid</span>
              </button>
            </div>
            <button class="btn-ghost" onclick="shuffleRevisions()" title="Shuffle Cards (🔀)" style="padding:4px 8px; font-size:11px; height:28px;">
              <span class="material-symbols-outlined" style="font-size:15px;">shuffle</span>
            </button>
          </div>
        </div>
      </div>

      <div class="revision-deck-container">
        <div id="revision-card-container">
          <!-- Rendered dynamically via renderRevisionDeck() -->
        </div>
      </div>
    </section>

  </main>

  <!-- TACTILE TOAST NOTIFICATION -->
  <div id="studio-toast">Notification</div>

  <!-- LESSON & SIMULATOR DIALOG MODAL -->
  <div id="lesson-modal" class="modal-overlay">
    <div id="lesson-modal-box" class="modal-box lesson-dialog-box">
      <div class="modal-header lesson-dialog-header">
        <div style="display:flex; align-items:center; gap:10px; min-width:0;">
          <span class="material-symbols-outlined" style="font-size:22px; color:var(--primary-container);">school</span>
          <div style="min-width:0;">
            <h3 id="lesson-modal-title" style="font-family:var(--font-headline); font-size:16px; font-weight:800; text-transform:uppercase; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
              HTML Lesson
            </h3>
            <div id="lesson-modal-subtitle" style="font-family:var(--font-mono); font-size:11px; color:var(--on-surface-variant); margin-top:2px;"></div>
          </div>
        </div>

        <div style="display:flex; align-items:center; gap:8px; flex-shrink:0;">
          <!-- Format Switcher Pill Group -->
          <div id="lesson-format-toggle" class="format-pill-group">
            <button id="btn-format-html" class="format-pill-btn active" onclick="switchLessonFormat('html')" title="Interactive HTML Lesson">
              <span class="material-symbols-outlined" style="font-size:14px;">view_in_ar</span>
              <span>HTML Lesson</span>
            </button>
            <button id="btn-format-md" class="format-pill-btn" onclick="switchLessonFormat('md')" title="Artifact Markdown Document">
              <span class="material-symbols-outlined" style="font-size:14px;">description</span>
              <span>Markdown</span>
            </button>
          </div>

          <!-- Highlighter controls for reader -->
          <div id="lesson-highlighter-controls" class="highlighter-controls-group" style="display:inline-flex; align-items:center; gap:6px; position:relative;">
            <button type="button" class="hl-swatch-btn yellow" onmousedown="event.preventDefault()" onclick="applyHighlight('yellow', 'lesson')" title="Yellow highlight"></button>
            <button type="button" class="hl-swatch-btn emerald" onmousedown="event.preventDefault()" onclick="applyHighlight('emerald', 'lesson')" title="Emerald highlight"></button>
            <button type="button" class="hl-swatch-btn cyan" onmousedown="event.preventDefault()" onclick="applyHighlight('cyan', 'lesson')" title="Cyan highlight"></button>
            <button type="button" id="lesson-hl-list-btn" class="btn-ghost" style="padding:2px 6px; font-size:10px; display:inline-flex; align-items:center; gap:2px;" onclick="toggleHighlightsPopover('lesson')" title="View and remove individual highlights">
              <span class="material-symbols-outlined" style="font-size:12px;">format_ink_highlighter</span>
              <span id="lesson-hl-count">0</span>
              <span class="material-symbols-outlined" style="font-size:11px;">arrow_drop_down</span>
            </button>
            <button type="button" class="btn-ghost" style="padding:2px 6px; font-size:10px;" onclick="clearActiveHighlights('lesson')" title="Clear all highlights in this lesson">Clear All</button>
            <div id="lesson-hl-popover" class="hl-popover-menu" style="display:none;"></div>
          </div>

          <!-- Fullscreen Toggle Button -->
          <button id="lesson-fullscreen-btn" class="icon-action-btn" onclick="toggleLessonFullscreen()" title="Toggle Fullscreen (F)">
            <span class="material-symbols-outlined" id="lesson-fullscreen-icon" style="font-size:18px;">fullscreen</span>
          </button>

          <!-- Close Button -->
          <button class="modal-close-btn" onclick="closeLessonModal()" title="Close (Esc)">
            <span class="material-symbols-outlined" style="font-size:18px;">close</span>
          </button>
        </div>
      </div>

      <div class="lesson-dialog-body">
        <!-- Interactive HTML Simulator -->
        <iframe id="lesson-modal-iframe" class="lesson-iframe" sandbox="allow-scripts allow-same-origin allow-forms" style="display:none;"></iframe>
        
        <!-- Artifact-Grade Markdown Viewer -->
        <div id="lesson-modal-markdown" class="md-rendered lesson-artifact-view" style="display:none;"></div>
      </div>
    </div>
  </div>

  <!-- NOTE VIEWER & EDITOR MODAL -->
  <div id="note-modal" class="modal-overlay">
    <div class="modal-box note-dialog-box">
      <div class="modal-header note-dialog-header">
        <div style="display:flex; align-items:center; gap:10px; min-width:0;">
          <span class="material-symbols-outlined" style="font-size:22px; color:var(--primary-container);">description</span>
          <div style="min-width:0;">
            <h3 id="note-modal-title" style="font-family:var(--font-headline); font-size:16px; font-weight:800; text-transform:uppercase; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
              Study Note
            </h3>
            <div class="note-modal-subtitle-row">
              <span class="note-path-badge" id="note-path-badge" title="Repository file path">
                <span class="material-symbols-outlined" style="font-size:13px;">folder</span>
                <span id="note-path-text">notes/...</span>
              </span>
              <span class="note-stats-badge" id="note-stats-badge">
                <span class="material-symbols-outlined" style="font-size:13px;">schedule</span>
                <span id="note-stats-text">0 words &bull; ~1 min read</span>
              </span>
            </div>
          </div>
        </div>
        <div style="display:flex; align-items:center; gap:8px; flex-shrink:0;">
          <!-- Mode Switcher Pill Group -->
          <div class="format-pill-group">
            <button type="button" id="btn-note-view" class="format-pill-btn active" onclick="setNoteMode('view')" title="Rendered Markdown Preview">
              <span class="material-symbols-outlined" style="font-size:14px;">visibility</span>
              <span>Preview</span>
            </button>
            <button type="button" id="btn-note-split" class="format-pill-btn" onclick="setNoteMode('split')" title="Side-by-side Editor &amp; Live Preview">
              <span class="material-symbols-outlined" style="font-size:14px;">vertical_split</span>
              <span>Split</span>
            </button>
            <button type="button" id="btn-note-edit" class="format-pill-btn" onclick="setNoteMode('edit')" title="Full-screen Markdown Editor">
              <span class="material-symbols-outlined" style="font-size:14px;">edit_note</span>
              <span>Edit</span>
            </button>
          </div>

          <button type="button" id="note-copy-btn" class="btn-ghost" onclick="copyNoteMarkdown()" title="Copy Markdown to Clipboard">
            <span class="material-symbols-outlined" style="font-size:14px;">content_copy</span>
            <span>Copy</span>
          </button>
          <!-- Highlighter controls for Notes -->
          <div id="note-highlighter-controls" class="highlighter-controls-group" style="display:inline-flex; align-items:center; gap:6px; position:relative;">
            <button type="button" class="hl-swatch-btn yellow" onmousedown="event.preventDefault()" onclick="applyHighlight('yellow', 'note')" title="Yellow highlight"></button>
            <button type="button" class="hl-swatch-btn emerald" onmousedown="event.preventDefault()" onclick="applyHighlight('emerald', 'note')" title="Emerald highlight"></button>
            <button type="button" class="hl-swatch-btn cyan" onmousedown="event.preventDefault()" onclick="applyHighlight('cyan', 'note')" title="Cyan highlight"></button>
            <button type="button" id="note-hl-list-btn" class="btn-ghost" style="padding:2px 6px; font-size:10px; display:inline-flex; align-items:center; gap:2px;" onclick="toggleHighlightsPopover('note')" title="View and remove individual highlights">
              <span class="material-symbols-outlined" style="font-size:12px;">format_ink_highlighter</span>
              <span id="note-hl-count">0</span>
              <span class="material-symbols-outlined" style="font-size:11px;">arrow_drop_down</span>
            </button>
            <button type="button" class="btn-ghost" style="padding:2px 6px; font-size:10px;" onclick="clearActiveHighlights('note')" title="Clear all highlights in this note">Clear All</button>
            <div id="note-hl-popover" class="hl-popover-menu" style="display:none;"></div>
          </div>
          <button type="button" id="note-save-btn" class="btn-primary" onclick="saveNoteFromEditor()" style="display:none;" title="Save Note to Disk (⌘S / Ctrl+S)">
            <span class="material-symbols-outlined" style="font-size:14px;">save</span>
            <span>Save</span>
          </button>
          <button type="button" class="modal-close-btn" onclick="closeModal('note-modal')" title="Close (Esc)">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>
      </div>

      <!-- Notion Toolbar (Active in edit / split mode) -->
      <div id="note-editor-toolbar" class="note-editor-toolbar" style="display:none;">
        <button type="button" class="notion-tool-btn" onclick="wrapNoteSelection('**', '**')" title="Bold (⌘B)"><span class="material-symbols-outlined" style="font-size:15px;">format_bold</span></button>
        <button type="button" class="notion-tool-btn" onclick="wrapNoteSelection('*', '*')" title="Italic (⌘I)"><span class="material-symbols-outlined" style="font-size:15px;">format_italic</span></button>
        <button type="button" class="notion-tool-btn" onclick="wrapNoteSelection('~~', '~~')" title="Strikethrough"><span class="material-symbols-outlined" style="font-size:15px;">strikethrough_s</span></button>
        <button type="button" class="notion-tool-btn" onclick="wrapNoteSelection('`', '`')" title="Inline Code"><span class="material-symbols-outlined" style="font-size:15px;">code</span></button>
        <div class="toolbar-divider"></div>
        <button type="button" class="notion-tool-btn" onclick="insertNoteLinePrefix('# ')" title="Heading 1">H1</button>
        <button type="button" class="notion-tool-btn" onclick="insertNoteLinePrefix('## ')" title="Heading 2">H2</button>
        <button type="button" class="notion-tool-btn" onclick="insertNoteLinePrefix('### ')" title="Heading 3">H3</button>
        <div class="toolbar-divider"></div>
        <button type="button" class="notion-tool-btn" onclick="insertNoteLinePrefix('- ')" title="Bullet List"><span class="material-symbols-outlined" style="font-size:15px;">format_list_bulleted</span></button>
        <button type="button" class="notion-tool-btn" onclick="insertNoteLinePrefix('1. ')" title="Numbered List"><span class="material-symbols-outlined" style="font-size:15px;">format_list_numbered</span></button>
        <button type="button" class="notion-tool-btn" onclick="insertNoteLinePrefix('- [ ] ')" title="Task Checklist"><span class="material-symbols-outlined" style="font-size:15px;">check_box</span></button>
        <div class="toolbar-divider"></div>
        <button type="button" class="notion-tool-btn" onclick="insertNoteLinePrefix('> ')" title="Quote"><span class="material-symbols-outlined" style="font-size:15px;">format_quote</span></button>
        <button type="button" class="notion-tool-btn" onclick="insertNoteSnippet('> [!NOTE]\n> ')" title="Callout Alert"><span class="material-symbols-outlined" style="font-size:15px;">crisis_alert</span></button>
        <button type="button" class="notion-tool-btn" onclick="insertNoteTableTemplate()" title="Insert Table"><span class="material-symbols-outlined" style="font-size:15px;">table_chart</span></button>
        <button type="button" class="notion-tool-btn" onclick="insertNoteCodeBlockTemplate()" title="Insert Code Block"><span class="material-symbols-outlined" style="font-size:15px;">terminal</span></button>
        <button type="button" class="notion-tool-btn" onclick="insertNoteSynthesisTemplate()" title="Insert SDS Invariant Template"><span class="material-symbols-outlined" style="font-size:15px;">auto_stories</span></button>
      </div>

      <!-- Workbench Body: View Pane, Editor Pane, and Split Preview Pane -->
      <div class="note-workbench-layout" style="margin-top:12px;">
        <div id="note-view-body" class="md-rendered note-view-pane" style="display:block;"></div>
        <textarea id="note-edit-body" class="note-editor-pane" style="display:none;" placeholder="Write architecture study notes in Notion-grade Markdown..." oninput="handleNoteLiveInput()"></textarea>
        <div id="note-split-preview" class="md-rendered note-preview-pane" style="display:none;"></div>
      </div>
    </div>
  </div>

  <!-- ADR DEFENSE VIEWER MODAL -->
  <div id="adr-modal" class="modal-overlay">
    <div class="modal-box" style="max-width:800px; max-height:90vh; overflow-y:auto;">
      <div class="modal-header">
        <h3 id="adr-modal-title" style="font-family:var(--font-headline); font-size:16px; font-weight:700; text-transform:uppercase;">
          Architecture Decision Records (DECISIONS.md)
        </h3>
        <div style="display:flex; align-items:center; gap:8px;">
          <!-- ADR Highlighter controls -->
          <div id="adr-highlighter-controls" class="highlighter-controls-group" style="display:inline-flex; align-items:center; gap:6px; position:relative;">
            <button type="button" class="hl-swatch-btn yellow" onmousedown="event.preventDefault()" onclick="applyHighlight('yellow', 'adr')" title="Yellow highlight"></button>
            <button type="button" class="hl-swatch-btn emerald" onmousedown="event.preventDefault()" onclick="applyHighlight('emerald', 'adr')" title="Emerald highlight"></button>
            <button type="button" class="hl-swatch-btn cyan" onmousedown="event.preventDefault()" onclick="applyHighlight('cyan', 'adr')" title="Cyan highlight"></button>
            <button type="button" id="adr-hl-list-btn" class="btn-ghost" style="padding:2px 6px; font-size:10px; display:inline-flex; align-items:center; gap:2px;" onclick="toggleHighlightsPopover('adr')" title="View and remove individual highlights">
              <span class="material-symbols-outlined" style="font-size:12px;">format_ink_highlighter</span>
              <span id="adr-hl-count">0</span>
              <span class="material-symbols-outlined" style="font-size:11px;">arrow_drop_down</span>
            </button>
            <button type="button" class="btn-ghost" style="padding:2px 6px; font-size:10px;" onclick="clearActiveHighlights('adr')" title="Clear all highlights in DECISIONS.md">Clear All</button>
            <div id="adr-hl-popover" class="hl-popover-menu" style="display:none;"></div>
          </div>
          <button class="modal-close-btn" onclick="closeModal('adr-modal')">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>
      </div>
      <div id="adr-modal-content" class="md-rendered" style="font-size:13px;">
        Loading decisions...
      </div>
    </div>
  </div>

  <!-- NEW PROJECT WORKSPACE MODAL -->
  <div id="new-project-modal" class="modal-overlay">
    <div class="modal-box">
      <div class="modal-header">
        <h3 style="font-family:var(--font-headline); font-size:16px; font-weight:700; text-transform:uppercase;">
          Initialize New Learning Workspace
        </h3>
        <button class="modal-close-btn" onclick="closeModal('new-project-modal')">
          <span class="material-symbols-outlined">close</span>
        </button>
      </div>
      <form onsubmit="handleCreateProject(event)">
        <div class="form-group">
          <label class="form-label">Workspace Name</label>
          <input type="text" id="new-project-name" class="form-input" placeholder="e.g. Distributed Core Engine" required />
        </div>
        <div class="form-group">
          <label class="form-label">Curriculum Track</label>
          <select id="new-project-track" class="form-input">
            <option value="full-mastery">Full 50-Cluster Mastery Track (354 Topics)</option>
            <option value="interview-sprint">Senior Interview Sprint (Core Distributed Systems)</option>
            <option value="distributed-systems">Distributed Systems & Storage Infrastructure</option>
            <option value="mobile-offline">Mobile & Offline-First Systems</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">Custom Directory Path (Optional, defaults to studio projects)</label>
          <input type="text" id="new-project-path" class="form-input" placeholder="e.g. ~/Developer/distributed-core" />
        </div>
        <div style="display:flex; justify-content:flex-end; gap:8px; margin-top:20px;">
          <button type="button" class="btn-ghost" onclick="closeModal('new-project-modal')">
            <span class="material-symbols-outlined" style="font-size:14px;">close</span>
            <span>Cancel</span>
          </button>
          <button type="submit" class="btn-primary">
            <span class="material-symbols-outlined" style="font-size:15px;">rocket_launch</span>
            <span>Initialize Workspace</span>
          </button>
        </div>
      </form>
    </div>
  </div>

  <!-- TOPIC PROGRESSION STATUS MODAL -->
  <div id="topic-status-modal" class="modal-overlay">
    <div class="modal-box" style="max-width:480px;">
      <div class="modal-header">
        <div style="display:flex; align-items:center; gap:8px;">
          <span class="material-symbols-outlined" style="font-size:22px; color:var(--primary-container);">tune</span>
          <div>
            <h3 style="font-family:var(--font-headline); font-size:16px; font-weight:800; text-transform:uppercase; color:var(--on-surface);">
              Topic Status
            </h3>
            <div id="status-modal-topic-title" style="font-family:var(--font-mono); font-size:11px; color:var(--on-surface-variant); margin-top:2px; word-break:break-word;"></div>
          </div>
        </div>
        <button class="modal-close-btn" onclick="closeModal('topic-status-modal')">
          <span class="material-symbols-outlined">close</span>
        </button>
      </div>
      <div style="padding:16px 0; display:flex; flex-direction:column; gap:12px;">
        <button type="button" class="status-option-btn" id="opt-status-verified" onclick="selectTopicStatus('verified')">
          <div style="display:flex; align-items:center; gap:12px; min-width:0;">
            <span class="material-symbols-outlined" style="color:#10b981; font-size:24px; flex-shrink:0;">check_circle</span>
            <div style="text-align:left; min-width:0;">
              <div class="status-option-title opt-title-verified" style="color:#10b981;">VERIFIED</div>
              <div class="status-option-desc">Invariant defended &amp; recorded in manifest</div>
            </div>
          </div>
          <span class="status-selected-pill verified" id="check-verified" style="display:none;">
            <span class="material-symbols-outlined" style="font-size:13px;">check</span>
            <span>CURRENT</span>
          </span>
        </button>

        <button type="button" class="status-option-btn" id="opt-status-in-progress" onclick="selectTopicStatus('in_progress')">
          <div style="display:flex; align-items:center; gap:12px; min-width:0;">
            <span class="material-symbols-outlined" style="color:var(--primary-container); font-size:24px; flex-shrink:0;">pending</span>
            <div style="text-align:left; min-width:0;">
              <div class="status-option-title opt-title-active" style="color:var(--primary-container);">ACTIVE FOCUS</div>
              <div class="status-option-desc">Currently learning or in active dialectic</div>
            </div>
          </div>
          <span class="status-selected-pill active" id="check-in-progress" style="display:none;">
            <span class="material-symbols-outlined" style="font-size:13px;">check</span>
            <span>CURRENT</span>
          </span>
        </button>

        <button type="button" class="status-option-btn" id="opt-status-not-started" onclick="selectTopicStatus('not_started')">
          <div style="display:flex; align-items:center; gap:12px; min-width:0;">
            <span class="material-symbols-outlined" style="color:var(--on-surface-variant); font-size:24px; flex-shrink:0;">radio_button_unchecked</span>
            <div style="text-align:left; min-width:0;">
              <div class="status-option-title opt-title-not-started" style="color:var(--on-surface);">NOT STARTED</div>
              <div class="status-option-desc">Unseen curriculum topic</div>
            </div>
          </div>
          <span class="status-selected-pill not-started" id="check-not-started" style="display:none;">
            <span class="material-symbols-outlined" style="font-size:13px;">check</span>
            <span>CURRENT</span>
          </span>
        </button>
      </div>

      <div id="status-reset-confirm-box" style="display:none; background:rgba(239,68,68,0.1); border:1.5px solid #ef4444; padding:12px; margin-top:8px;">
        <div style="display:flex; align-items:flex-start; gap:8px;">
          <span class="material-symbols-outlined" style="color:#ef4444; font-size:18px;">warning</span>
          <div style="font-size:12px; line-height:1.4;">
            <strong style="color:var(--on-surface);">Warning: Resetting Verification</strong>
            <p style="margin:4px 0 8px 0; color:var(--on-surface-variant);">This will remove the verification entry for this topic from your repository manifest. Are you sure you want to proceed?</p>
            <div style="display:flex; gap:8px;">
              <button type="button" class="btn-primary" style="background:#ef4444; color:#fff; border-color:#dc2626;" onclick="executeConfirmedStatusChange()">Yes, Update Status</button>
              <button type="button" class="btn-ghost" onclick="cancelStatusConfirmation()">Cancel</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- SETTINGS MODAL -->
  <div id="settings-modal" class="modal-overlay">
    <div class="modal-box">
      <div class="modal-header">
        <h3 style="font-family:var(--font-headline); font-size:16px; font-weight:700; text-transform:uppercase;">
          Studio Settings & Preferences
        </h3>
        <button class="modal-close-btn" onclick="closeModal('settings-modal')">
          <span class="material-symbols-outlined">close</span>
        </button>
      </div>
      <form onsubmit="handleSaveSettings(event)">
        <div class="form-group">
          <label class="form-label">Visual Theme Preset</label>
          <select id="settings-theme-preset" class="form-input" onchange="applyThemePreset(this.value)">
            <option value="slate-clean">Modern Slate (Tech Minimal Dark) [Default]</option>
            <option value="editorial-paper">Clean Editorial (Warm Cream &amp; Ink)</option>
            <option value="cyber-obsidian">Cyber Obsidian (Deep Black)</option>
            <option value="nordic-frost">Nordic Frost (Clean Ice Blue)</option>
            <option value="warm-amber">Warm Amber (Classic Terminal)</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">Artifact Delivery Format</label>
          <div style="font-size:11px; font-family:var(--font-mono); color:var(--on-surface-variant); background:var(--surface-container-high); padding:6px 10px; border:1px solid var(--border-color); border-radius:3px;">
            Dual Delivery Active: HTML (Interactive Simulator) &amp; Markdown (.md) are automatically compiled in sync.
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">Notes Storage Directory</label>
          <input type="text" id="settings-notes-dir" class="form-input" placeholder="notes" />
        </div>
        <div class="form-group" style="display:flex; align-items:center; gap:8px;">
          <input type="checkbox" id="settings-auto-notes" style="width:16px; height:16px;" />
          <label for="settings-auto-notes" style="font-size:12px; font-family:var(--font-body); cursor:pointer;">
            Automatically compile active-learning notes on topic verification
          </label>
        </div>

        <!-- System Design Studio Updates & Maintenance Section -->
        <div id="settings-updates-section" style="margin-top:16px; padding:12px; border:2px solid var(--border-color); background:var(--surface-container-low);">
          <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:6px;">
            <div>
              <div style="font-family:var(--font-headline); font-size:12px; font-weight:800; text-transform:uppercase; letter-spacing:0.02em;">
                Studio Updates &amp; Version
              </div>
              <div style="font-family:var(--font-mono); font-size:11px; color:var(--on-surface-variant); margin-top:2px;">
                Installed Version: <strong id="settings-installed-version" style="color:var(--on-primary-container); background:var(--primary-container); border:1px solid var(--border-color); padding:1px 6px; border-radius:3px; font-weight:700;">v3.7.0</strong>
              </div>
            </div>
            <button type="button" class="btn-ghost" id="btn-check-updates" onclick="checkForUpdates(true)" style="padding:4px 8px; font-size:10px; display:inline-flex; align-items:center; gap:4px;">
              <span class="material-symbols-outlined" id="update-spinner-icon" style="font-size:13px;">sync</span>
              <span>Check for Updates</span>
            </button>
          </div>
          <div id="settings-update-status" style="font-family:var(--font-mono); font-size:11px; color:var(--on-surface-variant); line-height:1.4;">
            Updates are strictly on-demand. All user progress, notes, and ADRs are preserved during updates.
          </div>
          <div id="settings-update-command-box" style="margin-top:8px; display:none;">
            <div style="display:flex; align-items:center; gap:6px; background:var(--surface-container-high); border:1px solid var(--border-color); padding:4px 8px;">
              <code id="settings-update-cmd" style="font-family:var(--font-mono); font-size:10.5px; font-weight:700; color:var(--primary); overflow-x:auto; white-space:nowrap; flex:1; scrollbar-width:none;">curl -fsSL https://raw.githubusercontent.com/alph-a07/system-design-studio/main/update.sh | bash</code>
              <button type="button" class="btn-ghost" style="padding:2px 6px; font-size:10px;" onclick="copyUpdateCommand(this)">Copy</button>
            </div>
          </div>
        </div>
        <div style="display:flex; justify-content:flex-end; gap:8px; margin-top:20px;">
          <button type="button" class="btn-ghost" onclick="closeModal('settings-modal')">
            <span class="material-symbols-outlined" style="font-size:14px;">close</span>
            <span>Cancel</span>
          </button>
          <button type="submit" class="btn-primary">
            <span class="material-symbols-outlined" style="font-size:15px;">save</span>
            <span>Save Settings</span>
          </button>
        </div>
      </form>
    </div>
  </div>

  <!-- KEYBOARD SHORTCUTS HUD MODAL -->
  <div id="shortcuts-modal" class="modal-overlay">
    <div class="modal-box" style="max-width: 580px;">
      <div class="modal-header">
        <div style="display:flex; align-items:center; gap:8px;">
          <span class="material-symbols-outlined" style="font-size:20px; color:var(--primary-container);">keyboard</span>
          <h3 style="font-family:var(--font-headline); font-size:16px; font-weight:700; text-transform:uppercase;">
            Keyboard Shortcuts &amp; Ergonomics
          </h3>
        </div>
        <button class="modal-close-btn" onclick="closeModal('shortcuts-modal')">
          <span class="material-symbols-outlined">close</span>
        </button>
      </div>

      <div style="font-family:var(--font-mono); font-size:11px; color:var(--on-surface-variant); margin-bottom:16px;">
        Tactile keybindings designed for rapid flow and distraction-free study.
      </div>

      <div class="shortcut-group">
        <div class="shortcut-group-title">Global Navigation</div>
        <div class="shortcut-row">
          <span class="shortcut-desc">Open / Close this shortcuts HUD</span>
          <div class="shortcut-keys"><kbd>?</kbd></div>
        </div>
        <div class="shortcut-row">
          <span class="shortcut-desc">Focus curriculum search input</span>
          <div class="shortcut-keys"><kbd>/</kbd></div>
        </div>
        <div class="shortcut-row">
          <span class="shortcut-desc">Switch top-level tabs (Projects / Syllabus / Revision)</span>
          <div class="shortcut-keys"><kbd>1</kbd> <kbd>2</kbd> <kbd>3</kbd></div>
        </div>
        <div class="shortcut-row">
          <span class="shortcut-desc">Dismiss open modal or active dialog</span>
          <div class="shortcut-keys"><kbd>Esc</kbd></div>
        </div>
      </div>

      <div class="shortcut-group">
        <div class="shortcut-group-title">Lesson &amp; Simulator Dialog</div>
        <div class="shortcut-row">
          <span class="shortcut-desc">Toggle borderless theater fullscreen</span>
          <div class="shortcut-keys"><kbd>F</kbd></div>
        </div>
        <div class="shortcut-row">
          <span class="shortcut-desc">Exit lesson dialog back to syllabus</span>
          <div class="shortcut-keys"><kbd>Esc</kbd></div>
        </div>
      </div>

      <div class="shortcut-group" style="margin-bottom:0;">
        <div class="shortcut-group-title">Revision Mode (Spaced Recall)</div>
        <div class="shortcut-row">
          <span class="shortcut-desc">Reveal defended invariant &amp; sizing math</span>
          <div class="shortcut-keys"><kbd>Space</kbd></div>
        </div>
        <div class="shortcut-row">
          <span class="shortcut-desc">Rate retention interval (Needs Review / Good / Mastered)</span>
          <div class="shortcut-keys"><kbd>1</kbd> <kbd>2</kbd> <kbd>3</kbd></div>
        </div>
      </div>
    </div>
  </div>

  <!-- ZERO-DEPENDENCY CLIENT LOGIC -->
  <script>
    let globalStatus = null;
    let projectsData = null;
    let revisionsData = { revisions: [], totalRevisions: 0, dueCount: 0, masteredCount: 0, learningCount: 0, needsReviewCount: 0 };
    let revisionsList = [];
    let currentRevisionIdx = 0;
    let revisionRevealed = false;
    let trapRevealed = false;
    let revisionFilter = 'all';
    let revisionSearchQuery = '';
    let revisionViewMode = 'card';
    let currentTopicFilter = 'all';
    let currentTierFilter = 'all';
    let currentTrackFilter = 'all';
    let currentViewMode = 'standard';
    let currentSearchTerm = '';
    let currentActiveArtifact = '';
    let activeNoteRelPath = '';
    let noteInEditMode = false;

    // Canonical Curriculum Tiers Registry & Track Definitions
    const CANONICAL_TIERS = {
      'tier.0': {
        code: 'T0',
        name: 'Tier 0 — High-Level Design (HLD) Building Blocks',
        subtitle: 'Network transport, database transactions, caching, storage & async worker foundations',
        level: 'PREREQUISITES',
        color: 'var(--primary-container)',
        textColor: 'var(--on-primary-container)'
      },
      'tier.1': {
        code: 'T1',
        name: 'Tier 1 — Low-Level Design (LLD) & In-Process Architecture',
        subtitle: 'Domain entities, ownership, SOLID patterns, concurrency & in-process isolation',
        level: 'SINGLE-NODE LLD',
        color: '#dc2626',
        textColor: '#ffffff'
      },
      'tier.2': {
        code: 'T2',
        name: 'Tier 2 — High-Level Design (HLD) & Distributed Systems',
        subtitle: 'Scalability, partitioning, replication, consensus (Raft/Paxos) & fault tolerance',
        level: 'DISTRIBUTED SCALE',
        color: '#0055ff',
        textColor: '#ffffff'
      },
      'tier.3': {
        code: 'T3',
        name: 'Tier 3 — Mobile & Offline-First Systems',
        subtitle: 'Local-first persistence, delta sync engines, CRDTs, battery & bandwidth invariants',
        level: 'EDGE & OFFLINE',
        color: '#059669',
        textColor: '#ffffff'
      },
      'tier.4': {
        code: 'T4',
        name: 'Tier 4 — Production Architecture Reviews & ADR Defenses',
        subtitle: 'Failure injection, board-level trade-off defense, ADR portfolios & synthesis',
        level: 'SYNTHESIS & DEFENSE',
        color: '#7c3aed',
        textColor: '#ffffff'
      }
    };

    const CANONICAL_TRACKS = {
      'interview-sprint': ['0.1', '0.2', '0.3', '0.4', '0.5', '1.1', '1.2', '1.3', '2.1', '2.2', '2.3', '2.4', '2.5', '2.7', '2.10'],
      'distributed-core': ['tier.0', 'tier.2'],
      'mobile-offline': ['tier.0', 'tier.3']
    };

    function getTierMeta(tierId) {
      if (CANONICAL_TIERS[tierId]) return CANONICAL_TIERS[tierId];
      const numMatch = (tierId || '').match(/\d+/);
      const num = numMatch ? numMatch[0] : '';
      const key = `tier.${num}`;
      if (CANONICAL_TIERS[key]) return CANONICAL_TIERS[key];
      return {
        code: `T${num || '?'}`,
        name: (tierId || 'Tier').replace('tier.', 'Tier ').toUpperCase() + ' — Infrastructure Mechanics',
        subtitle: 'Curriculum learning track tier',
        level: 'CUSTOM TIER',
        color: 'var(--primary-container)',
        textColor: 'var(--on-primary-container)'
      };
    }

    function setTierFilter(tierId, btn) {
      currentTierFilter = tierId;
      document.querySelectorAll('.tier-jump-btn').forEach(b => {
        b.classList.toggle('active', b.getAttribute('data-tier') === tierId);
      });
      if (globalStatus?.manifest) {
        renderCurriculum(globalStatus.manifest);
      }
    }

    function setTrackFilter(trackKey) {
      currentTrackFilter = trackKey;
      if (globalStatus?.manifest) {
        renderCurriculum(globalStatus.manifest);
      }
    }

    function setViewMode(mode) {
      currentViewMode = mode;
      const btnStd = document.getElementById('btn-view-standard');
      const btnCmp = document.getElementById('btn-view-compact');
      const container = document.getElementById('curriculum-tree-container');
      if (btnStd) btnStd.classList.toggle('active', mode === 'standard');
      if (btnCmp) btnCmp.classList.toggle('active', mode === 'compact');
      if (container) container.classList.toggle('compact-grid-mode', mode === 'compact');
      showToast(`View: ${mode === 'compact' ? 'Compact Index Grid' : 'Detailed Syllabus'}`);
    }

    // Tactile Bauhaus Toast
    function showToast(msg, duration = 2400) {
      const t = document.getElementById('studio-toast');
      if (!t) return;
      t.innerHTML = `<span class="material-symbols-outlined" style="font-size:16px; margin-right:6px; color:#1a1a1a;">check_circle</span><span>${msg}</span>`;
      t.style.display = 'inline-flex';
      t.style.alignItems = 'center';
      t.style.opacity = '1';
      clearTimeout(t._timer);
      t._timer = setTimeout(() => {
        t.style.opacity = '0';
        setTimeout(() => { t.style.display = 'none'; }, 200);
      }, duration);
    }

    // Forward-Assisted UX Helpers
    function openShortcutsModal() {
      openModal('shortcuts-modal');
    }

    async function copyAgentCommand(cmd) {
      try {
        if (navigator.clipboard && navigator.clipboard.writeText) {
          await navigator.clipboard.writeText(cmd);
        } else {
          const ta = document.createElement('textarea');
          ta.value = cmd;
          ta.style.position = 'fixed';
          ta.style.opacity = '0';
          document.body.appendChild(ta);
          ta.select();
          document.execCommand('copy');
          document.body.removeChild(ta);
        }
        showToast(`Copied: ${cmd}`);
      } catch (err) {
        showToast(`Command: ${cmd}`);
      }
    }

    async function copyNoteMarkdown() {
      const editBody = document.getElementById('note-edit-body');
      const val = editBody ? editBody.value : '';
      if (!val) {
        showToast('No note content to copy');
        return;
      }
      await copyAgentCommand(val);
      showToast('Note Markdown copied to clipboard');
    }

    function applySearchTag(tag) {
      const inp = document.getElementById('curriculum-search');
      if (inp) {
        inp.value = tag;
        handleSearch(tag);
        inp.focus();
      }
    }

    // Artifact-Grade Client Markdown Renderer (Block-Level Notion Tokenizer)
    function renderMarkdown(md) {
      if (!md) return '';
      let src = md.replace(/\r\n/g, '\n').replace(/\r/g, '\n');

      // 1. Extract Code Blocks first to protect diagrams and code from formatting
      const codeBlocks = [];
      src = src.replace(/```([a-z0-9_-]*)\n([\s\S]*?)```/g, function(match, lang, code) {
        const id = '__CODE_BLOCK_' + codeBlocks.length + '__';
        codeBlocks.push({ lang: (lang || '').trim().toLowerCase(), code: code });
        return id;
      });

      const lines = src.split('\n');
      const out = [];
      let i = 0;

      function formatInline(text) {
        if (!text) return '';
        return text
          .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
          .replace(/`([^`]+)`/g, '<code class="notion-inline-code">$1</code>')
          .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
          .replace(/\*([^*]+)\*/g, '<em>$1</em>')
          .replace(/~~([^~]+)~~/g, '<del>$1</del>')
          .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener" class="notion-link">$1</a>');
      }

      while (i < lines.length) {
        const line = lines[i];
        const trimmed = line.trim();

        // Empty line
        if (!trimmed) {
          i++;
          continue;
        }

        // Code block placeholder
        if (trimmed.startsWith('__CODE_BLOCK_') && trimmed.endsWith('__')) {
          out.push(trimmed);
          i++;
          continue;
        }

        // Horizontal Rule
        if (/^(---|___|\*\*\*)$/.test(trimmed)) {
          out.push('<hr class="notion-hr" />');
          i++;
          continue;
        }

        // Headings
        if (/^#{1,6}\s/.test(trimmed)) {
          const match = trimmed.match(/^(#{1,6})\s+(.*)$/);
          if (match) {
            const level = match[1].length;
            const text = formatInline(match[2]);
            out.push('<h' + level + ' class="notion-h' + level + '">' + text + '</h' + level + '>');
            i++;
            continue;
          }
        }

        // GitHub/Notion Callout Alert: > [!TYPE]
        if (/^>\s*\[!(IMPORTANT|NOTE|WARNING|TIP|CAUTION|DANGER|INVARIANT|MECHANISM|IDEA)\]/i.test(trimmed)) {
          const alertMatch = trimmed.match(/^>\s*\[!(IMPORTANT|NOTE|WARNING|TIP|CAUTION|DANGER|INVARIANT|MECHANISM|IDEA)\]\s*(.*)$/i);
          const alertType = (alertMatch[1] || 'NOTE').toUpperCase();
          let alertContent = alertMatch[2] ? [alertMatch[2]] : [];
          i++;
          while (i < lines.length && /^>/.test(lines[i].trim())) {
            alertContent.push(lines[i].trim().replace(/^>\s?/, ''));
            i++;
          }
          let icon = 'info';
          let cls = 'alert-note';
          if (['IMPORTANT', 'DANGER', 'CAUTION'].includes(alertType)) { icon = 'crisis_alert'; cls = 'alert-important'; }
          else if (alertType === 'WARNING') { icon = 'warning'; cls = 'alert-warning'; }
          else if (['TIP', 'INVARIANT', 'MECHANISM'].includes(alertType)) { icon = 'verified'; cls = 'alert-tip'; }
          else if (alertType === 'IDEA') { icon = 'lightbulb'; cls = 'alert-idea'; }

          out.push('<div class="callout-alert ' + cls + '"><div class="callout-header"><span class="material-symbols-outlined" style="font-size:16px;">' + icon + '</span><span>' + alertType + '</span></div><div class="callout-content" style="font-size:13px; line-height:1.65;">' + alertContent.map(l => formatInline(l)).join('<br />') + '</div></div>');
          continue;
        }

        // Standard Blockquote
        if (/^>/.test(trimmed)) {
          const quoteLines = [];
          while (i < lines.length && /^>/.test(lines[i].trim())) {
            quoteLines.push(lines[i].trim().replace(/^>\s?/, ''));
            i++;
          }
          const formattedQuote = quoteLines.map(l => formatInline(l)).join('<br />');
          const rawJoined = quoteLines.join(' ');
          if (rawJoined.includes('Hierarchy') || rawJoined.includes('Depth') || rawJoined.includes('Format')) {
            out.push('<div class="lead-meta">' + formattedQuote + '</div>');
          } else {
            out.push('<blockquote class="notion-quote">' + formattedQuote + '</blockquote>');
          }
          continue;
        }

        // GFM Table: line contains '|' and next line is delimiter row
        if (line.includes('|') && i + 1 < lines.length && /^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)+\|?\s*$/.test(lines[i + 1])) {
          const headerLine = line;
          const tableRows = [];
          i += 2; // skip header & delimiter
          while (i < lines.length && (lines[i].includes('|') || (tableRows.length > 0 && lines[i].trim() !== '' && !lines[i].trim().startsWith('#') && !lines[i].trim().startsWith('__CODE_BLOCK_') && !lines[i].trim().startsWith('>')))) {
            if (lines[i].includes('|')) {
              tableRows.push(lines[i]);
            } else if (tableRows.length > 0) {
              tableRows[tableRows.length - 1] += ' ' + lines[i].trim();
            }
            i++;
          }

          const parseCols = (l) => {
            let trimmedLine = l.trim();
            if (trimmedLine.startsWith('|')) trimmedLine = trimmedLine.slice(1);
            if (trimmedLine.endsWith('|')) trimmedLine = trimmedLine.slice(0, -1);
            return trimmedLine.split('|').map(c => c.trim());
          };

          const headers = parseCols(headerLine);
          const thHtml = headers.map(h => '<th>' + formatInline(h) + '</th>').join('');
          let tbodyHtml = '';
          tableRows.forEach(r => {
            const cells = parseCols(r);
            while (cells.length < headers.length) {
              cells.push('');
            }
            const tdHtml = cells.map(c => '<td>' + formatInline(c) + '</td>').join('');
            tbodyHtml += '<tr>' + tdHtml + '</tr>';
          });

          out.push('<div class="table-responsive-wrapper"><table class="notion-table"><thead><tr>' + thHtml + '</tr></thead><tbody>' + tbodyHtml + '</tbody></table></div>');
          continue;
        }

        // Task list / Checklist: - [ ] or - [x]
        if (/^-\s+\[([ xX])\]\s+(.*)$/.test(trimmed)) {
          const taskItems = [];
          while (i < lines.length && /^-\s+\[([ xX])\]\s+(.*)$/.test(lines[i].trim())) {
            const m = lines[i].trim().match(/^-\s+\[([ xX])\]\s+(.*)$/);
            const checked = m[1].toLowerCase() === 'x';
            taskItems.push('<li class="notion-task-item ' + (checked ? 'checked' : '') + '"><input type="checkbox" ' + (checked ? 'checked' : '') + ' disabled class="notion-checkbox" /><span>' + formatInline(m[2]) + '</span></li>');
            i++;
          }
          out.push('<ul class="notion-task-list">' + taskItems.join('') + '</ul>');
          continue;
        }

        // Unordered List
        if (/^[-*+]\s+(.*)$/.test(trimmed)) {
          const listItems = [];
          while (i < lines.length && /^[-*+]\s+(.*)$/.test(lines[i].trim()) && !/^-\s+\[[ xX]\]/.test(lines[i].trim())) {
            const m = lines[i].trim().match(/^[-*+]\s+(.*)$/);
            listItems.push('<li>' + formatInline(m[1]) + '</li>');
            i++;
          }
          out.push('<ul class="notion-bullet-list">' + listItems.join('') + '</ul>');
          continue;
        }

        // Ordered List
        if (/^\d+\.\s+(.*)$/.test(trimmed)) {
          const listItems = [];
          while (i < lines.length && /^\d+\.\s+(.*)$/.test(lines[i].trim())) {
            const m = lines[i].trim().match(/^\d+\.\s+(.*)$/);
            listItems.push('<li>' + formatInline(m[1]) + '</li>');
            i++;
          }
          out.push('<ol class="notion-ordered-list">' + listItems.join('') + '</ol>');
          continue;
        }

        // Normal Paragraph (consume lines until blank line or block start)
        const paraLines = [];
        while (
          i < lines.length &&
          lines[i].trim() !== '' &&
          !/^#{1,6}\s/.test(lines[i].trim()) &&
          !lines[i].trim().startsWith('__CODE_BLOCK_') &&
          !/^>/.test(lines[i].trim()) &&
          !/^[-*+]\s/.test(lines[i].trim()) &&
          !/^\d+\.\s/.test(lines[i].trim()) &&
          !(lines[i].includes('|') && i + 1 < lines.length && /^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)+\|?\s*$/.test(lines[i + 1]))
        ) {
          paraLines.push(lines[i].trim());
          i++;
        }
        out.push('<p class="notion-p">' + formatInline(paraLines.join(' ')) + '</p>');
      }

      let finalHtml = out.join('\n');

      // Re-insert Code Blocks with artifact styling
      codeBlocks.forEach((cb, idx) => {
        const id = '__CODE_BLOCK_' + idx + '__';
        let blockHtml = '';
        const safeCode = cb.code.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        if (cb.lang === 'mermaid') {
          blockHtml = `<div class="diagram-box">
            <div class="diagram-header">
              <span style="display:flex; align-items:center; gap:6px;">
                <span class="material-symbols-outlined" style="font-size:14px;">account_tree</span>
                <span>MERMAID PROTOCOL SEQUENCE</span>
              </span>
              <span style="font-size:10px; opacity:0.8;">Zero-JS Diagram</span>
            </div>
            <pre><code>${safeCode.trim()}</code></pre>
          </div>`;
        } else if (cb.lang === 'ascii' || cb.lang === 'diagram' || cb.code.includes('+---') || (cb.lang === 'text' && cb.code.includes('|'))) {
          blockHtml = `<div class="diagram-box">
            <div class="diagram-header">
              <span style="display:flex; align-items:center; gap:6px;">
                <span class="material-symbols-outlined" style="font-size:14px;">memory</span>
                <span>HARDWARE &amp; BUFFER STATE TRACE</span>
              </span>
              <span style="font-size:10px; opacity:0.8;">ASCII Hardware Invariant</span>
            </div>
            <pre><code>${safeCode.trim()}</code></pre>
          </div>`;
        } else {
          blockHtml = `<div class="code-block-container">
            <div class="code-block-header">
              <span style="display:flex; align-items:center; gap:6px;">
                <span class="material-symbols-outlined" style="font-size:14px;">terminal</span>
                <span>${(cb.lang || 'CODE').toUpperCase()}</span>
              </span>
              <button class="code-copy-btn" onclick="navigator.clipboard.writeText(this.closest('.code-block-container').querySelector('code').innerText); showToast('Code copied');" title="Copy code">
                <span class="material-symbols-outlined" style="font-size:13px;">content_copy</span>
              </button>
            </div>
            <pre><code>${safeCode.trim()}</code></pre>
          </div>`;
        }
        finalHtml = finalHtml.replace(id, blockHtml);
      });

      return finalHtml;
    }

    // Modal Control (with Body Scroll Locking to prevent background scroll leaks)
    function openModal(modalId) {
      const el = document.getElementById(modalId);
      if (el) {
        el.classList.add('active');
        document.body.style.overflow = 'hidden';
      }
    }

    function closeModal(modalId) {
      const el = document.getElementById(modalId);
      if (el) {
        el.classList.remove('active');
        if (!document.querySelector('.modal-overlay.active')) {
          document.body.style.overflow = '';
        }
      }
      document.querySelectorAll('.hl-popover-menu').forEach(p => { p.style.display = 'none'; });
    }

    // Theme Management
    function initTheme() {
      const saved = localStorage.getItem('sds_theme') || 'dark';
      const savedPreset = localStorage.getItem('sds_theme_preset') || 'slate-clean';
      document.documentElement.setAttribute('data-theme-preset', savedPreset);
      if (saved === 'dark') {
        document.documentElement.classList.add('dark');
        document.getElementById('theme-icon').innerText = 'light_mode';
      } else {
        document.documentElement.classList.remove('dark');
        document.getElementById('theme-icon').innerText = 'dark_mode';
      }
    }

    function toggleTheme() {
      const isDark = document.documentElement.classList.toggle('dark');
      localStorage.setItem('sds_theme', isDark ? 'dark' : 'light');
      document.getElementById('theme-icon').innerText = isDark ? 'light_mode' : 'dark_mode';
      const preset = localStorage.getItem('sds_theme_preset') || 'slate-clean';

      // Propagate theme change to active iframe lesson
      const iframes = [
        document.getElementById('workbench-iframe'),
        document.getElementById('lesson-modal-iframe')
      ];
      iframes.forEach(iframe => {
        if (iframe && iframe.contentWindow) {
          try {
            iframe.contentWindow.postMessage({ type: 'sds-theme-change', theme: isDark ? 'dark' : 'light', preset: preset }, '*');
          } catch (e) {}
        }
        if (iframe && iframe.contentDocument) {
          try {
            if (isDark) iframe.contentDocument.documentElement.classList.add('dark');
            else iframe.contentDocument.documentElement.classList.remove('dark');
            iframe.contentDocument.documentElement.setAttribute('data-theme-preset', preset);
          } catch (e) {}
        }
      });
      showToast(isDark ? 'Dark theme enabled' : 'Light theme enabled');
    }

    function applyThemePreset(preset) {
      if (!preset) return;
      document.documentElement.setAttribute('data-theme-preset', preset);
      localStorage.setItem('sds_theme_preset', preset);

      if (preset === 'editorial-paper') {
        document.documentElement.classList.remove('dark');
        localStorage.setItem('sds_theme', 'light');
        document.getElementById('theme-icon').innerText = 'dark_mode';
      } else if (preset === 'cyber-obsidian' || preset === 'slate-clean' || preset === 'midnight-neon' || preset === 'nordic-frost' || preset === 'warm-amber') {
        document.documentElement.classList.add('dark');
        localStorage.setItem('sds_theme', 'dark');
        document.getElementById('theme-icon').innerText = 'light_mode';
      }

      const iframes = [
        document.getElementById('workbench-iframe'),
        document.getElementById('lesson-modal-iframe')
      ];
      iframes.forEach(iframe => {
        if (iframe && iframe.contentWindow) {
          try {
            iframe.contentWindow.postMessage({
              type: 'sds-theme-change',
              theme: document.documentElement.classList.contains('dark') ? 'dark' : 'light',
              preset: preset
            }, '*');
          } catch (e) {}
        }
        if (iframe && iframe.contentDocument) {
          try {
            const isDark = document.documentElement.classList.contains('dark');
            if (isDark) iframe.contentDocument.documentElement.classList.add('dark');
            else iframe.contentDocument.documentElement.classList.remove('dark');
            iframe.contentDocument.documentElement.setAttribute('data-theme-preset', preset);
          } catch (e) {}
        }
      });
      showToast(`Visual Preset: ${preset}`);
    }

    // Real-time Data Sync (SSE)
    function setupSSE() {
      if (!window.EventSource) return;
      const es = new EventSource('/api/events');
      es.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data);
          if (data.type === 'update') {
            refreshData(false);
          }
        } catch (err) {}
      };
      es.onerror = () => {};
    }

    // Master Refresh
    async function refreshData(manual = false) {
      try {
        const res = await fetch('/api/status');
        if (!res.ok) return;
        globalStatus = await res.json();

        // Update nav active project label & select
        const m = globalStatus.manifest || {};
        const instName = m.instanceName || 'Project Instance';
        const navNamePill = document.getElementById('nav-active-project-name');
        if (navNamePill) navNamePill.innerText = instName;
        const curProjTitle = document.getElementById('curriculum-view-project-title');
        if (curProjTitle) curProjTitle.innerText = `${instName} — CURRICULUM`;

        // Render curriculum syllabus while preserving open tier state
        renderCurriculum(m);

        // Load projects data
        loadProjects();

        if (manual) {
          showToast('Local data synced');
        }
      } catch (e) {
        console.error('Refresh error:', e);
      }
    }

    // Navigation & Tab Switching
    function switchTab(tabName) {
      const tabs = ['projects', 'curriculum', 'revision'];
      if (!tabs.includes(tabName)) return;

      tabs.forEach(t => {
        const btn = document.getElementById(`nav-tab-${t}`);
        const panel = document.getElementById(`panel-${t}`);
        if (btn) btn.classList.toggle('active', t === tabName);
        if (panel) panel.classList.toggle('active', t === tabName);
      });

      if (tabName === 'projects') {
        loadProjects();
      } else if (tabName === 'revision') {
        loadRevisions();
      } else if (tabName === 'curriculum') {
        if (globalStatus?.manifest) {
          renderCurriculum(globalStatus.manifest);
        }
      }
    }

    // Render Projects (Cards Home Vibe)
    async function loadProjects() {
      try {
        const res = await fetch('/api/projects');
        if (!res.ok) return;
        projectsData = await res.json();
        const grid = document.getElementById('projects-grid');
        grid.innerHTML = '';

        const activeId = projectsData.activeProjectId;
        const projects = projectsData.projects || [];

        projects.forEach(p => {
          const isActive = (p.id === activeId);
          const card = document.createElement('div');
          card.className = `project-card ${isActive ? 'active-card' : ''}`;

          const verified = p.progress?.verifiedTopics ?? p.progress?.completed ?? 0;
          const total = p.progress?.totalTopics ?? p.progress?.total ?? (p.track === 'full-mastery' ? 354 : (p.track === 'interview-sprint' ? 114 : 0));
          const pct = total > 0 ? Math.round((verified / total) * 100) : 0;
          const focusTitle = p.progress?.activeTopicTitle || p.activeTopicTitle || 'Foundation Initialization';

          card.innerHTML = `
            <div>
              <div class="card-top-row">
                <span class="${isActive ? 'badge-active' : 'badge-registered'}">
                  <span class="material-symbols-outlined" style="font-size:12px; margin-right:3px;">${isActive ? 'check_circle' : 'folder'}</span>
                  ${isActive ? 'ACTIVE WORKSPACE' : 'REGISTERED'}
                </span>
                <span class="git-branch-tag">
                  <span class="material-symbols-outlined" style="font-size:13px; margin-right:2px; vertical-align:-2px;">fork_right</span>
                  ${p.gitBranch || 'main'}
                </span>
              </div>
              <h2 class="project-title">${p.name}</h2>
              <div class="project-track">${p.track || 'Distributed Systems & Networking'}</div>
              
              <div class="progress-metric-text">
                <span>PROGRESS</span>
                <span>${verified} / ${total} Topics (${pct}%)</span>
              </div>
              <div class="progress-bar-container">
                <div class="progress-bar-fill" style="width: ${pct}%;"></div>
              </div>

              <div class="active-topic-snippet" title="${focusTitle}">
                <strong>Focus:</strong> ${focusTitle}
              </div>
            </div>

            <div class="card-footer">
              <button class="btn-primary" onclick="handleOpenProject('${p.id}')">
                <span>Open Curriculum</span>
                <span class="material-symbols-outlined" style="font-size:14px; margin-left:4px;">arrow_forward</span>
              </button>
              ${!isActive ? `<button class="btn-ghost" onclick="handleSwitchProject('${p.id}')"><span class="material-symbols-outlined" style="font-size:14px; margin-right:3px;">swap_horiz</span>Switch</button>` : ''}
              <button class="btn-ghost" style="color:var(--secondary);" onclick="handleDeleteProject('${p.id}', '${p.name.replace(/'/g, "\\\\'")}')" title="Delete Workspace">
                <span class="material-symbols-outlined" style="font-size:16px;">delete</span>
              </button>
            </div>
          `;
          grid.appendChild(card);
        });

        // Update Top Navbar Project Select Dropdown
        const navSelect = document.getElementById('nav-project-select');
        if (navSelect && projects.length > 0) {
          navSelect.innerHTML = projects.map(p => `
            <option value="${p.id}" ${p.id === activeId ? 'selected' : ''}>${p.name}</option>
          `).join('');
          navSelect.value = activeId || (projects[0] ? projects[0].id : '');
        }

        // Append "+ Scaffolding Card"
        const scaffoldCard = document.createElement('div');
        scaffoldCard.className = 'scaffolding-card';
        scaffoldCard.onclick = openNewProjectModal;
        scaffoldCard.innerHTML = `
          <span class="material-symbols-outlined" style="font-size:36px; color:var(--primary-container); margin-bottom:8px;">add_circle</span>
          <div style="font-family:var(--font-headline); font-size:14px; font-weight:800; text-transform:uppercase;">
            Initialize New Workspace
          </div>
          <div style="font-family:var(--font-mono); font-size:11px; color:var(--on-surface-variant); margin-top:4px;">
            Create a learning track in this machine
          </div>
        `;
        grid.appendChild(scaffoldCard);
      } catch (e) {
        console.error('Projects load error:', e);
      }
    }

    async function handleOpenProject(projectId) {
      if (projectsData?.activeProjectId !== projectId) {
        await handleSwitchProject(projectId);
      }
      switchTab('curriculum');
    }

    async function handleNavProjectSelect(projectId) {
      if (!projectId || projectId === projectsData?.activeProjectId) return;
      await handleSwitchProject(projectId);
    }

    async function handleSwitchProject(projectId) {
      try {
        const res = await fetch('/api/projects/switch', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ projectId })
        });
        if (res.ok) {
          const navSelect = document.getElementById('nav-project-select');
          if (navSelect) navSelect.value = projectId;
          showToast('Switched active workspace');
          await loadProjects();
          await refreshData();
        }
      } catch (e) {
        console.error('Switch error:', e);
      }
    }

    async function handleDeleteProject(projectId, name) {
      if (!confirm(`Are you sure you want to delete workspace "${name}" from Studio registry? Your local files are kept intact.`)) {
        return;
      }
      try {
        const res = await fetch('/api/projects/delete', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ projectId })
        });
        if (res.ok) {
          showToast('Workspace unregistered');
          refreshData();
        }
      } catch (e) {
        console.error('Delete error:', e);
      }
    }

    function openNewProjectModal() {
      openModal('new-project-modal');
    }

    async function handleCreateProject(event) {
      event.preventDefault();
      const name = document.getElementById('new-project-name').value;
      const track = document.getElementById('new-project-track').value;
      const path = document.getElementById('new-project-path').value;

      try {
        const res = await fetch('/api/projects/create', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, track, path })
        });
        if (res.ok) {
          closeModal('new-project-modal');
          showToast('New workspace initialized');
          refreshData();
        } else {
          alert('Failed to initialize workspace. Please check path and permissions.');
        }
      } catch (e) {
        alert('Failed to initialize workspace');
      }
    }

    // Render Curriculum Syllabus (Single Unified View with State Preservation)
    function renderCurriculum(manifest) {
      const container = document.getElementById('curriculum-tree-container');
      if (!container) return;

      // Preserve opened tiers before clearing
      const existingTiers = document.querySelectorAll('.tier-accordion');
      const wasRenderedBefore = existingTiers.length > 0;
      const openTierIds = new Set(
        Array.from(document.querySelectorAll('.tier-accordion.open')).map(el => el.id)
      );

      container.innerHTML = '';

      const curriculum = manifest.curriculum || {};
      const clusters = curriculum.clusters || [];
      const activeTopicId = curriculum.activeTopicId;

      if (!clusters.length) {
        container.innerHTML = '<div style="padding:40px; text-align:center; font-family:var(--font-mono);">No curriculum clusters loaded yet.</div>';
        return;
      }

      // Compute global tier stats for Tier Jump Navigation Bar
      const globalTierStats = {};
      clusters.forEach(c => {
        const tid = c.tierId || 'tier.0';
        if (!globalTierStats[tid]) globalTierStats[tid] = { verified: 0, total: 0 };
        (c.topics || []).forEach(t => {
          globalTierStats[tid].total++;
          if (t.status === 'completed' || t.status === 'verified') {
            globalTierStats[tid].verified++;
          }
        });
      });

      // Update Tier Jump Bar pills
      ['0', '1', '2', '3', '4'].forEach(n => {
        const el = document.getElementById(`tier-jump-count-${n}`);
        if (el) {
          const stats = globalTierStats[`tier.${n}`] || { verified: 0, total: 0 };
          el.innerText = `${stats.verified}/${stats.total}`;
        }
      });

      // Find active topic for living focus strip
      let activeTopicObj = null;
      let activeClusterObj = null;
      clusters.forEach(c => {
        (c.topics || []).forEach(t => {
          if (t.id === activeTopicId) {
            activeTopicObj = t;
            activeClusterObj = c;
          }
        });
      });

      const focusStrip = document.getElementById('curriculum-focus-strip');
      if (focusStrip) {
        if (activeTopicObj) {
          focusStrip.style.display = 'flex';
          const titleEl = document.getElementById('focus-strip-topic-title');
          const clusterEl = document.getElementById('focus-strip-cluster-tag');
          const openLessonBtn = document.getElementById('btn-focus-open-lesson');
          if (titleEl) titleEl.innerText = activeTopicObj.title || activeTopicObj.id;
          if (clusterEl) {
            const cCode = activeClusterObj?.code || (activeClusterObj?.title?.match(/\[([^\]]+)\]/) || [])[1] || '';
            const cClean = (activeClusterObj?.title || '').replace(/^\d+\.\s*\[[^\]]+\]\s*/, '') || '';
            clusterEl.innerText = cCode ? `[${cCode}] ${cClean}` : (activeClusterObj?.title || '');
          }
          if (openLessonBtn) {
            openLessonBtn.onclick = () => openLessonModal(activeTopicObj.id, activeTopicObj.title, activeTopicObj.lessonArtifact || '');
          }
        } else {
          focusStrip.style.display = 'none';
        }
      }

      // Group clusters into Tiers with Track and Tier filters
      const tiersMap = {};
      clusters.forEach(c => {
        const tierId = c.tierId || 'tier.0';
        const clusterCode = c.code || (c.title?.match(/\[([^\]]+)\]/) || [])[1] || (c.id || '').replace('cluster.', '');

        // Track filter checks
        if (currentTrackFilter === 'interview-sprint') {
          if (!CANONICAL_TRACKS['interview-sprint'].includes(clusterCode)) return;
        } else if (currentTrackFilter === 'distributed-core') {
          if (!CANONICAL_TRACKS['distributed-core'].includes(tierId)) return;
        } else if (currentTrackFilter === 'mobile-offline') {
          if (!CANONICAL_TRACKS['mobile-offline'].includes(tierId)) return;
        }

        // Tier filter checks
        if (currentTierFilter !== 'all' && tierId !== currentTierFilter) {
          return;
        }

        if (!tiersMap[tierId]) {
          const meta = getTierMeta(tierId);
          tiersMap[tierId] = {
            id: tierId,
            meta: meta,
            name: meta.name,
            clusters: []
          };
        }
        tiersMap[tierId].clusters.push(c);
      });

      let totalTopicsCount = 0;
      let totalVerifiedCount = 0;
      let totalMatchingTopics = 0;

      Object.values(tiersMap).forEach((tier, idx) => {
        let tierTopicsCount = 0;
        let tierVerifiedCount = 0;
        let tierHasSearchMatch = false;

        const tierEl = document.createElement('div');
        const tierElId = `tier-acc-${tier.id}`;
        tierEl.id = tierElId;

        let clustersHtml = '';
        tier.clusters.forEach(cluster => {
          let topicsHtml = '';
          const topics = cluster.topics || [];
          const clusterCode = cluster.code || (cluster.title?.match(/\[([^\]]+)\]/) || [])[1] || (cluster.id || '').replace('cluster.', '');
          const cleanTitle = (cluster.title || '').replace(/^\d+\.\s*\[[^\]]+\]\s*/, '').trim();

          let clusterTopicsCount = 0;
          let clusterVerifiedCount = 0;

          topics.forEach((t, topicIdx) => {
            const topicCode = `${clusterCode}.${topicIdx + 1}`;
            tierTopicsCount++;
            totalTopicsCount++;
            clusterTopicsCount++;
            const isCompleted = (t.status === 'completed' || t.status === 'verified');
            const isActive = (t.id === activeTopicId);
            if (isCompleted) {
              tierVerifiedCount++;
              totalVerifiedCount++;
              clusterVerifiedCount++;
            }

            // Apply topic status filters
            let matchesFilter = true;
            if (currentTopicFilter === 'active' && !isActive) matchesFilter = false;
            if (currentTopicFilter === 'completed' && !isCompleted) matchesFilter = false;
            if (currentTopicFilter === 'unseen' && (isCompleted || isActive)) matchesFilter = false;

            if (currentSearchTerm) {
              const fullSearchSpace = (
                t.title + ' ' +
                (t.id || '') + ' ' +
                topicCode + ' ' +
                clusterCode + ' ' +
                cleanTitle + ' ' +
                (cluster.title || '') + ' ' +
                tier.name
              ).toLowerCase();
              if (!fullSearchSpace.includes(currentSearchTerm.toLowerCase())) {
                matchesFilter = false;
              } else {
                tierHasSearchMatch = true;
              }
            }

            if (!matchesFilter) return;
            totalMatchingTopics++;

            let statusBadge = '';
            const safeTitle = (t.title || '').replace(/'/g, "\\'");
            if (isCompleted) {
              statusBadge = `<button type="button" class="status-pill status-completed" onclick="openTopicStatusMenu(event, '${t.id}', 'verified', '${safeTitle}')" title="Status: Verified (Click to change)"><span class="material-symbols-outlined" style="font-size:13px;">check_circle</span><span>VERIFIED</span><span class="material-symbols-outlined status-caret">arrow_drop_down</span></button>`;
            } else if (isActive) {
              statusBadge = `<button type="button" class="status-pill status-active" onclick="openTopicStatusMenu(event, '${t.id}', 'in_progress', '${safeTitle}')" title="Status: Active Focus (Click to change)"><span class="material-symbols-outlined" style="font-size:13px;">pending</span><span>ACTIVE</span><span class="material-symbols-outlined status-caret">arrow_drop_down</span></button>`;
            } else {
              statusBadge = `<button type="button" class="status-pill status-unseen" onclick="openTopicStatusMenu(event, '${t.id}', 'not_started', '${safeTitle}')" title="Status: Unseen (Click to change)"><span class="material-symbols-outlined" style="font-size:13px;">radio_button_unchecked</span><span>UNSEEN</span><span class="material-symbols-outlined status-caret">arrow_drop_down</span></button>`;
            }

            const topicLessonArtifact = t.lessonArtifact || '';

            topicsHtml += `
              <div class="topic-list-row ${isActive ? 'active-focus-row' : ''}">
                <div class="topic-left">
                  <span class="topic-index-badge" onclick="copyAgentCommand('/sds-teach ${t.id}')" title="Topic Code ${topicCode} (Click to copy /sds-teach command)">${topicCode}</span>
                  ${statusBadge}
                  <span class="topic-title-text" title="${t.title}">${t.title}</span>
                  ${isActive ? '<span class="active-focus-pill" style="margin-left:6px;"><span class="material-symbols-outlined" style="font-size:11px;">my_location</span>ACTIVE FOCUS</span>' : ''}
                </div>
                <div class="topic-actions">
                  <button class="btn-ghost" onclick="openLessonModal('${t.id}', '${t.title.replace(/'/g, "\\\\'")}', '${topicLessonArtifact.replace(/'/g, "\\\\'")}')" title="Open Lesson">
                    <span class="material-symbols-outlined" style="font-size:13px;">play_circle</span>
                    <span>Lesson</span>
                  </button>
                  <button class="btn-ghost" onclick="openTopicNote('${cluster.id}', '${t.id}', '${t.title.replace(/'/g, "\\\\'")}')" title="Open Notes">
                    <span class="material-symbols-outlined" style="font-size:13px;">edit_note</span>
                    <span>Notes</span>
                  </button>
                  ${isCompleted ? `<button class="btn-ghost" onclick="openADRModal('${t.id}')" title="View Defended ADR"><span class="material-symbols-outlined" style="font-size:13px;">gavel</span><span>ADR</span></button>` : ''}
                </div>
              </div>
            `;
          });

          if (topicsHtml) {
            const clusterPct = Math.round((clusterVerifiedCount / (clusterTopicsCount || 1)) * 100);
            clustersHtml += `
              <div class="cluster-box">
                <div class="cluster-header">
                  <div style="display:flex; align-items:center; gap:8px; min-width:0;">
                    <span class="cluster-code-pill">${clusterCode}</span>
                    <span class="cluster-name" title="${cleanTitle}">${cleanTitle}</span>
                  </div>
                  <div class="cluster-meta-right">
                    <div class="cluster-progress-micro-bar" title="${clusterVerifiedCount}/${clusterTopicsCount} Verified (${clusterPct}%)">
                      <div class="cluster-progress-micro-fill" style="width: ${clusterPct}%;"></div>
                    </div>
                    <span class="cluster-stats-pill">${clusterVerifiedCount}/${clusterTopicsCount} Verified</span>
                  </div>
                </div>
                <div>${topicsHtml}</div>
              </div>
            `;
          }
        });

        // Determine open state: preserve existing, open on search match, or default open first tier
        const shouldBeOpen = (currentSearchTerm && tierHasSearchMatch) ||
                             (wasRenderedBefore ? openTierIds.has(tierElId) : (idx === 0)) ||
                             (currentTierFilter !== 'all');

        tierEl.className = `tier-accordion ${shouldBeOpen ? 'open' : ''}`;
        const tierPct = Math.round((tierVerifiedCount / (tierTopicsCount || 1)) * 100);
        const meta = tier.meta;

        tierEl.innerHTML = `
          <div class="tier-header" onclick="toggleTier('${tier.id}')">
            <div style="display:flex; align-items:center; gap:12px; min-width:0;">
              <span class="material-symbols-outlined tier-chevron-icon" id="tier-chevron-${tier.id}">${shouldBeOpen ? 'expand_more' : 'chevron_right'}</span>
              <div style="min-width:0;">
                <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
                  <span class="tier-title">${meta.name}</span>
                  <span class="tier-level-badge" style="background-color:${meta.color}; color:${meta.textColor || '#ffffff'};">${meta.level}</span>
                </div>
                <div class="tier-subtitle">${meta.subtitle}</div>
              </div>
            </div>
            <div style="display:flex; align-items:center; gap:8px; flex-shrink:0;">
              <span class="tier-badge">${tierVerifiedCount} / ${tierTopicsCount} Verified (${tierPct}%)</span>
            </div>
          </div>
          <div class="tier-content" id="tier-content-${tier.id}">
            ${clustersHtml || '<div style="font-family:var(--font-mono); font-size:12px; color:var(--on-surface-variant); padding:10px;">No topics matching active filter.</div>'}
          </div>
        `;
        container.appendChild(tierEl);
      });

      // Update Search Count Badge & Empty Search State
      const countBadge = document.getElementById('search-count-badge');
      if (countBadge) {
        if (currentSearchTerm || currentTopicFilter !== 'all' || currentTrackFilter !== 'all' || currentTierFilter !== 'all') {
          countBadge.style.display = 'inline-block';
          countBadge.innerText = `Showing ${totalMatchingTopics} of ${totalTopicsCount} topics`;
        } else {
          countBadge.style.display = 'none';
        }
      }

      if (totalMatchingTopics === 0) {
        container.innerHTML = `
          <div class="empty-search-box">
            <span class="material-symbols-outlined" style="font-size:32px; color:var(--on-surface-variant); margin-bottom:8px;">search_off</span>
            <div style="font-family:var(--font-headline); font-size:14px; font-weight:700; text-transform:uppercase;">No matching topics found</div>
            <div style="font-family:var(--font-body); font-size:12px; color:var(--on-surface-variant); margin-top:4px;">No topics match the current filter query. Try selecting "All Tiers" or a forward tag like #transport, #0.1, or #consensus.</div>
            <button class="btn-ghost" style="margin-top:12px;" onclick="resetCurriculumFilters()"><span class="material-symbols-outlined" style="font-size:14px;">restart_alt</span><span>Reset All Filters</span></button>
          </div>
        `;
      }

      // Update meta text
      const pct = Math.round((totalVerifiedCount / (totalTopicsCount || 1)) * 100);
      document.getElementById('curriculum-view-meta').innerText = `${totalVerifiedCount} of ${totalTopicsCount} Topics Verified (${pct}% Mastery Track). Real-time Git tracked state.`;
    }

    function resetCurriculumFilters() {
      currentTopicFilter = 'all';
      currentTierFilter = 'all';
      currentTrackFilter = 'all';
      currentSearchTerm = '';
      const inp = document.getElementById('curriculum-search');
      if (inp) inp.value = '';
      const trk = document.getElementById('curriculum-track-select');
      if (trk) trk.value = 'all';
      const sts = document.getElementById('curriculum-status-select');
      if (sts) sts.value = 'all';
      document.querySelectorAll('.filter-pill').forEach(b => b.classList.toggle('active', b.getAttribute('data-filter') === 'all'));
      document.querySelectorAll('.tier-jump-btn').forEach(b => b.classList.toggle('active', b.getAttribute('data-tier') === 'all'));
      if (globalStatus?.manifest) {
        renderCurriculum(globalStatus.manifest);
      }
    }

    function toggleTier(tierId) {
      const el = document.getElementById(`tier-acc-${tierId}`);
      if (el) {
        el.classList.toggle('open');
        const chev = document.getElementById(`tier-chevron-${tierId}`);
        if (chev) chev.innerText = el.classList.contains('open') ? 'expand_more' : 'chevron_right';
      }
    }

    function toggleAllTiers() {
      const accordions = document.querySelectorAll('.tier-accordion');
      const anyOpen = Array.from(accordions).some(el => el.classList.contains('open'));
      accordions.forEach(el => {
        if (anyOpen) {
          el.classList.remove('open');
          const ch = el.querySelector('.tier-chevron-icon');
          if (ch) ch.innerText = 'chevron_right';
        } else {
          el.classList.add('open');
          const ch = el.querySelector('.tier-chevron-icon');
          if (ch) ch.innerText = 'expand_more';
        }
      });
    }

    function setTopicFilter(filter, btn) {
      currentTopicFilter = filter;
      const sts = document.getElementById('curriculum-status-select');
      if (sts) sts.value = filter;
      document.querySelectorAll('.filter-pill').forEach(b => b.classList.remove('active'));
      if (btn) btn.classList.add('active');
      if (globalStatus?.manifest) {
        renderCurriculum(globalStatus.manifest);
      }
    }

    function setTopicFilterSelect(val) {
      currentTopicFilter = val;
      document.querySelectorAll('.filter-pill').forEach(b => b.classList.toggle('active', b.getAttribute('data-filter') === val));
      if (globalStatus?.manifest) {
        renderCurriculum(globalStatus.manifest);
      }
    }

    function handleSearch(val) {
      currentSearchTerm = val.trim().replace(/^#/, '');
      const clearBtn = document.getElementById('search-clear-btn');
      if (clearBtn) clearBtn.style.display = val.length > 0 ? 'inline-flex' : 'none';
      if (globalStatus?.manifest) {
        renderCurriculum(globalStatus.manifest);
      }
    }

    function clearSearch() {
      const inp = document.getElementById('curriculum-search');
      if (inp) {
        inp.value = '';
        inp.focus();
      }
      handleSearch('');
    }

    // Interactive Topic Progression Status Menu Engine
    let pendingStatusChange = { topicId: null, targetStatus: null, currentStatus: null };

    function openTopicStatusMenu(event, topicId, currentStatus, topicTitle) {
      if (event) event.stopPropagation();
      pendingStatusChange = { topicId, targetStatus: null, currentStatus };

      const titleEl = document.getElementById('status-modal-topic-title');
      if (titleEl) titleEl.innerText = `${topicId}: ${topicTitle || ''}`;

      const confirmBox = document.getElementById('status-reset-confirm-box');
      if (confirmBox) confirmBox.style.display = 'none';

      ['verified', 'in_progress', 'not_started'].forEach(s => {
        const btn = document.getElementById(`opt-status-${s.replace('_', '-')}`);
        const check = document.getElementById(`check-${s.replace('_', '-')}`);
        if (btn) btn.classList.toggle('selected', s === currentStatus);
        if (check) check.style.display = (s === currentStatus) ? 'inline-flex' : 'none';
      });

      openModal('topic-status-modal');
    }

    async function selectTopicStatus(targetStatus) {
      if (!pendingStatusChange.topicId) return;
      if (targetStatus === pendingStatusChange.currentStatus) {
        closeModal('topic-status-modal');
        return;
      }

      // If un-verifying from verified to not_started or in_progress, ask for confirmation to prevent accidental manifest damage
      if (pendingStatusChange.currentStatus === 'verified' && targetStatus !== 'verified') {
        pendingStatusChange.targetStatus = targetStatus;
        const confirmBox = document.getElementById('status-reset-confirm-box');
        if (confirmBox) confirmBox.style.display = 'block';
        return;
      }

      pendingStatusChange.targetStatus = targetStatus;
      await executeConfirmedStatusChange();
    }

    async function executeConfirmedStatusChange() {
      const { topicId, targetStatus } = pendingStatusChange;
      if (!topicId || !targetStatus) return;

      try {
        const res = await fetch('/api/topic/status', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ topicId, status: targetStatus })
        });
        if (res.ok) {
          showToast(`Topic status updated to ${targetStatus.replace('_', ' ').toUpperCase()}`);
          closeModal('topic-status-modal');
          refreshData();
        } else {
          showToast('Failed to update topic status');
        }
      } catch (e) {
        showToast('Network error updating status');
      }
    }

    function cancelStatusConfirmation() {
      const confirmBox = document.getElementById('status-reset-confirm-box');
      if (confirmBox) confirmBox.style.display = 'none';
      pendingStatusChange.targetStatus = null;
    }

    // Fallback for script compatibility
    async function cycleTopicStatus(topicId, nextStatus) {
      pendingStatusChange = { topicId, targetStatus: nextStatus, currentStatus: null };
      await executeConfirmedStatusChange();
    }

    // Lesson & Simulator Modal Engine
    let currentLessonContext = {
      topicId: null,
      title: '',
      htmlPath: null,
      mdPath: null,
      activeFormat: 'html'
    };

    function toggleLessonFullscreen() {
      const box = document.getElementById('lesson-modal-box');
      const icon = document.getElementById('lesson-fullscreen-icon');
      if (!box) return;
      const isFull = box.classList.toggle('is-fullscreen');
      if (icon) icon.innerText = isFull ? 'fullscreen_exit' : 'fullscreen';
    }

    function closeLessonModal() {
      closeModal('lesson-modal');
      const iframe = document.getElementById('lesson-modal-iframe');
      if (iframe) iframe.src = '';
      const box = document.getElementById('lesson-modal-box');
      if (box) box.classList.remove('is-fullscreen');
      const icon = document.getElementById('lesson-fullscreen-icon');
      if (icon) icon.innerText = 'fullscreen';
    }

    // Aliases for backwards compatibility
    const closeLessonWorkbench = closeLessonModal;

    async function switchLessonFormat(format) {
      currentLessonContext.activeFormat = format;
      const btnHtml = document.getElementById('btn-format-html');
      const btnMd = document.getElementById('btn-format-md');
      const iframe = document.getElementById('lesson-modal-iframe');
      const mdView = document.getElementById('lesson-modal-markdown');
      const highlighters = document.getElementById('lesson-highlighter-controls');

      if (format === 'html' && currentLessonContext.htmlPath) {
        if (btnHtml) btnHtml.classList.add('active');
        if (btnMd) btnMd.classList.remove('active');
        if (highlighters) highlighters.style.display = 'inline-flex';
        mdView.style.display = 'none';
        iframe.style.display = 'block';
        currentActiveArtifact = currentLessonContext.htmlPath;
        const isDark = document.documentElement.classList.contains('dark');
        const activePreset = localStorage.getItem('sds_theme_preset') || 'slate-clean';
        iframe.onload = () => {
          try {
            if (iframe.contentDocument) {
              if (isDark) iframe.contentDocument.documentElement.classList.add('dark');
              else iframe.contentDocument.documentElement.classList.remove('dark');
              iframe.contentDocument.documentElement.setAttribute('data-theme-preset', activePreset);
              injectHighlightStylesIntoDoc(iframe.contentDocument);
              loadAndApplyHighlights(currentLessonContext.htmlPath, iframe.contentDocument.body, 'lesson');
            }
          } catch (e) {}
        };
        iframe.src = `/api/lesson?path=${encodeURIComponent(currentLessonContext.htmlPath)}&theme=${isDark ? 'dark' : 'light'}&preset=${encodeURIComponent(activePreset)}`;
      } else if (format === 'md' && currentLessonContext.mdPath) {
        if (btnMd) btnMd.classList.add('active');
        if (btnHtml) btnHtml.classList.remove('active');
        if (highlighters) highlighters.style.display = 'inline-flex';
        iframe.style.display = 'none';
        mdView.style.display = 'block';
        currentActiveArtifact = currentLessonContext.mdPath;
        mdView.innerHTML = '<div style="font-family:var(--font-mono); font-size:12px; color:var(--on-surface-variant); padding:20px;">Loading artifact markdown lesson...</div>';
        try {
          const res = await fetch(`/api/lesson?path=${encodeURIComponent(currentLessonContext.mdPath)}`);
          if (res.ok) {
            const raw = await res.text();
            mdView.innerHTML = renderMarkdown(raw);
            loadAndApplyHighlights(currentLessonContext.mdPath, mdView, 'lesson');
          } else {
            mdView.innerHTML = '<div style="font-family:var(--font-mono); color:var(--secondary); padding:20px;">Failed to load markdown lesson artifact.</div>';
          }
        } catch (e) {
          mdView.innerHTML = '<div style="font-family:var(--font-mono); color:var(--secondary); padding:20px;">Error loading markdown lesson.</div>';
        }
      }
    }

    async function openLessonModal(topicId, title, explicitArtifact = '') {
      currentLessonContext.topicId = topicId;
      currentLessonContext.title = title;
      currentLessonContext.htmlPath = null;
      currentLessonContext.mdPath = null;

      document.getElementById('lesson-modal-title').innerText = title || topicId;
      document.getElementById('lesson-modal-subtitle').innerText = `TOPIC: ${topicId}`;

      const allLessons = globalStatus?.lessons || [];
      const cleanId = (topicId || '').replace(/^topic\./, '');
      const dashedId = cleanId.replace(/\./g, '-');

      // Check explicit artifact
      if (explicitArtifact) {
        if (explicitArtifact.endsWith('.html')) currentLessonContext.htmlPath = explicitArtifact;
        if (explicitArtifact.endsWith('.md')) currentLessonContext.mdPath = explicitArtifact;
      }

      // Check all lessons in directory
      allLessons.forEach(l => {
        const fname = l.filename || '';
        const lpath = l.path || l.filename;
        if (fname.includes(cleanId) || fname.includes(dashedId)) {
          if (fname.endsWith('.html') && !currentLessonContext.htmlPath) currentLessonContext.htmlPath = lpath;
          if (fname.endsWith('.md') && !currentLessonContext.mdPath) currentLessonContext.mdPath = lpath;
        }
      });

      // Default fallback
      if (!currentLessonContext.htmlPath && !currentLessonContext.mdPath) {
        currentLessonContext.htmlPath = `lessons/${dashedId}.html`;
      }

      const toggleGroup = document.getElementById('lesson-format-toggle');
      const btnHtml = document.getElementById('btn-format-html');
      const btnMd = document.getElementById('btn-format-md');

      // Honor user/manifest outputType preference (markdown vs html)
      const outputPref = (globalStatus?.settings?.outputType || globalStatus?.manifest?.settings?.outputType || '').toLowerCase();
      const preferredFormat = (outputPref === 'markdown' || outputPref === 'md') ? 'md' : 'html';

      if (currentLessonContext.htmlPath && currentLessonContext.mdPath) {
        toggleGroup.style.display = 'inline-flex';
        btnHtml.style.display = 'inline-flex';
        btnMd.style.display = 'inline-flex';
        switchLessonFormat(preferredFormat);
      } else if (currentLessonContext.htmlPath) {
        toggleGroup.style.display = 'none';
        btnHtml.style.display = 'none';
        btnMd.style.display = 'none';
        switchLessonFormat('html');
      } else if (currentLessonContext.mdPath) {
        toggleGroup.style.display = 'none';
        btnHtml.style.display = 'none';
        btnMd.style.display = 'none';
        switchLessonFormat('md');
      } else {
        toggleGroup.style.display = 'none';
        switchLessonFormat('html');
      }

      openModal('lesson-modal');
    }

    // Alias for backward compatibility
    const openLessonWorkbench = (lessonRelPath, title) => {
      openLessonModal(lessonRelPath, title, lessonRelPath);
    };

    // Active Highlights Cache & State per Surface
    const activeHighlightsCache = {
      lesson: { path: '', list: [] },
      note: { path: '', list: [] },
      adr: { path: 'DECISIONS.md', list: [] }
    };

    function updateHighlightCountBadge(surfaceHint) {
      if (!surfaceHint) return;
      const cnt = activeHighlightsCache[surfaceHint]?.list?.length || 0;
      const el = document.getElementById(`${surfaceHint}-hl-count`);
      if (el) el.innerText = cnt;
    }

    function toggleHighlightsPopover(surfaceHint) {
      const popover = document.getElementById(`${surfaceHint}-hl-popover`);
      if (!popover) return;
      const isVisible = (popover.style.display === 'block');

      // Close all highlight popovers first
      document.querySelectorAll('.hl-popover-menu').forEach(p => { p.style.display = 'none'; });

      if (isVisible) return;

      const cache = activeHighlightsCache[surfaceHint] || { list: [], path: '' };
      const list = cache.list || [];

      if (list.length === 0) {
        popover.innerHTML = `
          <div style="padding:10px 8px; text-align:center; color:var(--on-surface-variant); font-size:11px;">
            No active highlights yet.<br/>Select text and click a swatch to add one.
          </div>
        `;
      } else {
        let itemsHtml = `
          <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid var(--border-color); padding-bottom:4px; margin-bottom:6px;">
            <strong style="text-transform:uppercase; font-size:10px; color:var(--on-surface);">Highlights (${list.length})</strong>
            <button type="button" class="btn-ghost" style="padding:1px 4px; font-size:9px; color:var(--secondary);" onclick="clearActiveHighlights('${surfaceHint}')">Clear All</button>
          </div>
        `;
        list.forEach(hl => {
          const color = hl.color || 'yellow';
          const rawText = (hl.text || '').replace(/\s+/g, ' ');
          const previewText = rawText.length > 34 ? rawText.substring(0, 34) + '…' : rawText;
          const escText = rawText.replace(/'/g, "\\'").replace(/"/g, '&quot;');
          itemsHtml += `
            <div class="hl-popover-item" title="${escText}">
              <span class="hl-swatch-btn ${color}" style="width:10px; height:10px; pointer-events:none; flex-shrink:0;"></span>
              <span class="hl-popover-text">"${previewText}"</span>
              <button type="button" class="hl-popover-del-btn" onclick="deleteSingleHighlight('${cache.path}', '${hl.id}', null, '${surfaceHint}')" title="Delete this highlight">
                <span class="material-symbols-outlined" style="font-size:13px;">close</span>
              </button>
            </div>
          `;
        });
        popover.innerHTML = itemsHtml;
      }
      popover.style.display = 'block';
    }

    // Universal Highlighting Engine (DOM TreeWalker & Multi-Surface Persistence)
    function injectHighlightStylesIntoDoc(doc) {
      if (!doc || doc.getElementById('sds-highlight-styles')) return;
      const st = doc.createElement('style');
      st.id = 'sds-highlight-styles';
      st.textContent = `
        ::selection {
          background-color: rgba(0, 229, 255, 0.28) !important;
          color: inherit !important;
        }
        html.dark ::selection {
          background-color: rgba(0, 229, 255, 0.32) !important;
          color: inherit !important;
        }
        html::selection,
        html.dark::selection,
        html:not(.dark)::selection,
        body::selection,
        html.dark body::selection,
        html:not(.dark) body::selection,
        main::selection,
        html.dark main::selection,
        html:not(.dark) main::selection,
        section::selection,
        html.dark section::selection,
        html:not(.dark) section::selection,
        article::selection,
        html.dark article::selection,
        html:not(.dark) article::selection,
        header::selection,
        html.dark header::selection,
        html:not(.dark) header::selection,
        footer::selection,
        html.dark footer::selection,
        html:not(.dark) footer::selection {
          background-color: transparent !important;
        }
        p, .editorial-lead, h1, h2, h3, h4, h5, h6, li, blockquote,
        .notion-p, .notion-h1, .notion-h2, .notion-h3 {
          width: fit-content !important;
          max-width: 100% !important;
        }
        .sds-highlight {
          border-radius: 2px;
          padding: 1px 3px;
          cursor: pointer;
          position: relative;
          transition: all 0.15s ease;
          font-weight: 500;
        }
        .sds-highlight:hover {
          filter: brightness(0.92);
          outline: 1.5px solid #dc2626;
        }
        .sds-highlight::after {
          content: "×";
          position: absolute;
          top: -10px;
          right: -6px;
          background: #dc2626;
          color: #ffffff;
          font-family: monospace;
          font-size: 11px;
          font-weight: 800;
          line-height: 13px;
          width: 14px;
          height: 14px;
          border-radius: 50%;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          opacity: 0;
          pointer-events: auto;
          cursor: pointer;
          transition: opacity 0.15s ease;
          z-index: 50;
          box-shadow: 0 1px 3px rgba(0,0,0,0.4);
        }
        .sds-highlight:hover::after {
          opacity: 1;
        }
        .sds-hl-yellow {
          background-color: #fef08a !important;
          color: #1a1a1a !important;
          border-bottom: 2px solid #eab308;
        }
        html.dark .sds-hl-yellow, .dark .sds-hl-yellow {
          background-color: rgba(250, 204, 21, 0.35) !important;
          color: #fef08a !important;
          border-bottom: 2px solid #facc15;
        }
        .sds-hl-emerald {
          background-color: #a7f3d0 !important;
          color: #064e3b !important;
          border-bottom: 2px solid #10b981;
        }
        html.dark .sds-hl-emerald, .dark .sds-hl-emerald {
          background-color: rgba(16, 185, 129, 0.3) !important;
          color: #6ee7b7 !important;
          border-bottom: 2px solid #10b981;
        }
        .sds-hl-cyan {
          background-color: #bae6fd !important;
          color: #0369a1 !important;
          border-bottom: 2px solid #0284c7;
        }
        html.dark .sds-hl-cyan, .dark .sds-hl-cyan {
          background-color: rgba(56, 189, 248, 0.3) !important;
          color: #7dd3fc !important;
          border-bottom: 2px solid #38bdf8;
        }
      `;
      (doc.head || doc.body).appendChild(st);
    }

    function renderHighlightsInContainer(container, highlights, artifactPath, surfaceHint = null) {
      if (!container || !highlights || !Array.isArray(highlights)) return;
      const doc = container.ownerDocument || document;

      highlights.forEach(hl => {
        const searchText = (hl.text || '').trim();
        if (!searchText) return;

        const walker = doc.createTreeWalker(
          container,
          NodeFilter.SHOW_TEXT,
          {
            acceptNode: function(node) {
              if (!node.nodeValue || !node.nodeValue.includes(searchText)) return NodeFilter.FILTER_REJECT;
              let p = node.parentElement;
              while (p && p !== container) {
                if (p.classList && p.classList.contains('sds-highlight')) return NodeFilter.FILTER_REJECT;
                if (['SCRIPT', 'STYLE', 'TEXTAREA', 'INPUT'].includes(p.tagName)) return NodeFilter.FILTER_REJECT;
                p = p.parentElement;
              }
              return NodeFilter.FILTER_ACCEPT;
            }
          }
        );

        const matchingNodes = [];
        let cur;
        while (cur = walker.nextNode()) {
          matchingNodes.push(cur);
        }

        matchingNodes.forEach(textNode => {
          const val = textNode.nodeValue;
          const idx = val.indexOf(searchText);
          if (idx === -1) return;

          const matchNode = textNode.splitText(idx);
          matchNode.splitText(searchText.length);

          const mark = doc.createElement('mark');
          mark.className = `sds-highlight sds-hl-${hl.color || 'yellow'}`;
          mark.dataset.hlId = hl.id || '';
          mark.title = `Click × to delete highlight (${hl.color || 'yellow'})`;
          mark.onclick = (e) => {
            e.stopPropagation();
            const fn = window.deleteSingleHighlight || window.parent?.deleteSingleHighlight;
            if (typeof fn === 'function') {
              fn(artifactPath, hl.id, mark, surfaceHint);
            }
          };

          if (matchNode.parentNode) {
            matchNode.parentNode.replaceChild(mark, matchNode);
            mark.appendChild(matchNode);
          }
        });
      });

      // Synchronize iframe global functions
      const iframe = document.getElementById('lesson-modal-iframe');
      if (iframe && iframe.contentWindow) {
        iframe.contentWindow.deleteSingleHighlight = deleteSingleHighlight;
        iframe.contentWindow.clearActiveHighlights = clearActiveHighlights;
      }
    }

    async function loadAndApplyHighlights(artifactPath, container, surfaceHint = 'lesson') {
      if (!artifactPath || !container) return;
      if (activeHighlightsCache[surfaceHint]) {
        activeHighlightsCache[surfaceHint].path = artifactPath;
      }
      try {
        const res = await fetch(`/api/highlights?artifact=${encodeURIComponent(artifactPath)}`);
        if (res.ok) {
          const data = await res.json();
          const highlights = Array.isArray(data) ? data : (data.highlights || []);
          if (activeHighlightsCache[surfaceHint]) {
            activeHighlightsCache[surfaceHint].list = highlights;
          }
          updateHighlightCountBadge(surfaceHint);
          renderHighlightsInContainer(container, highlights, artifactPath, surfaceHint);
        }
      } catch (e) {
        console.warn('Failed to load highlights for', artifactPath, e);
      }
    }

    // Alias for backwards compatibility
    async function loadHighlightsForCurrentArtifact() {
      if (!currentActiveArtifact) return;
      const container = document.getElementById('lesson-modal-markdown');
      if (container) loadAndApplyHighlights(currentActiveArtifact, container, 'lesson');
    }

    async function applyHighlight(color, surfaceHint = null) {
      let artifactPath = '';
      let targetContainer = null;
      let targetDoc = document;
      let selectedText = '';
      let selObj = null;

      const adrModal = document.getElementById('adr-modal');
      const noteModal = document.getElementById('note-modal');
      const lessonModal = document.getElementById('lesson-modal');

      if (surfaceHint === 'adr' || (adrModal && adrModal.classList.contains('active'))) {
        surfaceHint = 'adr';
        artifactPath = 'DECISIONS.md';
        targetContainer = document.getElementById('adr-modal-content');
        selObj = window.getSelection();
        selectedText = selObj ? selObj.toString().trim() : '';
      } else if (surfaceHint === 'note' || (noteModal && noteModal.classList.contains('active'))) {
        surfaceHint = 'note';
        artifactPath = activeNoteRelPath;
        targetContainer = (currentNoteMode === 'split') ? document.getElementById('note-split-preview') : document.getElementById('note-view-body');
        selObj = window.getSelection();
        selectedText = selObj ? selObj.toString().trim() : '';
      } else if (surfaceHint === 'lesson' || (lessonModal && lessonModal.classList.contains('active'))) {
        surfaceHint = 'lesson';
        if (currentLessonContext.activeFormat === 'html') {
          artifactPath = currentLessonContext.htmlPath;
          const iframe = document.getElementById('lesson-modal-iframe');
          if (iframe && iframe.contentDocument) {
            targetDoc = iframe.contentDocument;
            targetContainer = iframe.contentDocument.body;
            selObj = iframe.contentWindow ? iframe.contentWindow.getSelection() : null;
            selectedText = selObj ? selObj.toString().trim() : '';
          }
        } else {
          artifactPath = currentLessonContext.mdPath;
          targetContainer = document.getElementById('lesson-modal-markdown');
          selObj = window.getSelection();
          selectedText = selObj ? selObj.toString().trim() : '';
        }
      }

      // Fallback: If no text was captured from primary focus, check iframe selection
      if (!selectedText && lessonModal && lessonModal.classList.contains('active')) {
        const iframe = document.getElementById('lesson-modal-iframe');
        if (iframe && iframe.contentWindow) {
          const ifSel = iframe.contentWindow.getSelection();
          if (ifSel && ifSel.toString().trim()) {
            selectedText = ifSel.toString().trim();
            targetDoc = iframe.contentDocument;
            targetContainer = iframe.contentDocument.body;
            artifactPath = currentLessonContext.htmlPath;
            selObj = ifSel;
            surfaceHint = 'lesson';
          }
        }
      }

      if (!selectedText) {
        showToast('Please select text with your cursor first to highlight');
        return;
      }
      if (!artifactPath) {
        showToast('No active document to highlight');
        return;
      }

      const hlObj = {
        id: `hl_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`,
        color: color,
        text: selectedText
      };

      try {
        const res = await fetch(`/api/highlights?artifact=${encodeURIComponent(artifactPath)}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify([hlObj])
        });
        if (res.ok) {
          if (surfaceHint && activeHighlightsCache[surfaceHint]) {
            activeHighlightsCache[surfaceHint].list.push(hlObj);
            updateHighlightCountBadge(surfaceHint);
          }
          if (targetContainer) {
            renderHighlightsInContainer(targetContainer, [hlObj], artifactPath, surfaceHint);
          }
          if (selObj) {
            selObj.removeAllRanges();
          }
          showToast(`Highlighted in ${color.toUpperCase()}`);
        } else {
          showToast('Failed to save highlight');
        }
      } catch (e) {
        showToast('Network error saving highlight');
      }
    }

    async function deleteSingleHighlight(artifactPath, hlId, markElement, surfaceHint = null) {
      if (!artifactPath || !hlId) return;
      try {
        const res = await fetch(`/api/highlights?artifact=${encodeURIComponent(artifactPath)}&id=${encodeURIComponent(hlId)}`, {
          method: 'DELETE'
        });
        if (res.ok) {
          if (markElement && markElement.parentNode) {
            const parent = markElement.parentNode;
            while (markElement.firstChild) {
              parent.insertBefore(markElement.firstChild, markElement);
            }
            parent.removeChild(markElement);
            parent.normalize();
          } else {
            const unwrapMarks = (rootDoc) => {
              if (!rootDoc) return;
              rootDoc.querySelectorAll(`mark[data-hl-id="${hlId}"]`).forEach(m => {
                const p = m.parentNode;
                if (p) {
                  while (m.firstChild) p.insertBefore(m.firstChild, m);
                  p.removeChild(m);
                  p.normalize();
                }
              });
            };
            unwrapMarks(document);
            const iframe = document.getElementById('lesson-modal-iframe');
            if (iframe && iframe.contentDocument) unwrapMarks(iframe.contentDocument);
          }

          if (surfaceHint && activeHighlightsCache[surfaceHint]) {
            activeHighlightsCache[surfaceHint].list = (activeHighlightsCache[surfaceHint].list || []).filter(h => h.id !== hlId);
            updateHighlightCountBadge(surfaceHint);
            const popover = document.getElementById(`${surfaceHint}-hl-popover`);
            if (popover && popover.style.display === 'block') {
              toggleHighlightsPopover(surfaceHint);
              toggleHighlightsPopover(surfaceHint);
            }
          } else {
            Object.keys(activeHighlightsCache).forEach(s => {
              activeHighlightsCache[s].list = (activeHighlightsCache[s].list || []).filter(h => h.id !== hlId);
              updateHighlightCountBadge(s);
            });
          }
          showToast('Highlight removed');
        }
      } catch (e) {
        showToast('Error removing highlight');
      }
    }

    async function clearActiveHighlights(surfaceHint = null) {
      let artifactPath = '';
      let targetContainer = null;

      const adrModal = document.getElementById('adr-modal');
      const noteModal = document.getElementById('note-modal');
      const lessonModal = document.getElementById('lesson-modal');

      if (surfaceHint === 'adr' || (adrModal && adrModal.classList.contains('active'))) {
        surfaceHint = 'adr';
        artifactPath = 'DECISIONS.md';
        targetContainer = document.getElementById('adr-modal-content');
      } else if (surfaceHint === 'note' || (noteModal && noteModal.classList.contains('active'))) {
        surfaceHint = 'note';
        artifactPath = activeNoteRelPath;
        targetContainer = (currentNoteMode === 'split') ? document.getElementById('note-split-preview') : document.getElementById('note-view-body');
      } else if (surfaceHint === 'lesson' || (lessonModal && lessonModal.classList.contains('active'))) {
        surfaceHint = 'lesson';
        if (currentLessonContext.activeFormat === 'html') {
          artifactPath = currentLessonContext.htmlPath;
          const iframe = document.getElementById('lesson-modal-iframe');
          targetContainer = iframe?.contentDocument?.body;
        } else {
          artifactPath = currentLessonContext.mdPath;
          targetContainer = document.getElementById('lesson-modal-markdown');
        }
      }

      if (!artifactPath && surfaceHint && activeHighlightsCache[surfaceHint]?.path) {
        artifactPath = activeHighlightsCache[surfaceHint].path;
      }

      if (!artifactPath) return;

      try {
        const res = await fetch(`/api/highlights?artifact=${encodeURIComponent(artifactPath)}`, {
          method: 'DELETE'
        });
        if (res.ok) {
          const clearMarks = (cnt) => {
            if (!cnt) return;
            cnt.querySelectorAll('.sds-highlight').forEach(mark => {
              const parent = mark.parentNode;
              if (parent) {
                while (mark.firstChild) parent.insertBefore(mark.firstChild, mark);
                parent.removeChild(mark);
                parent.normalize();
              }
            });
          };

          clearMarks(targetContainer);
          clearMarks(document.getElementById('lesson-modal-markdown'));
          clearMarks(document.getElementById('note-view-body'));
          clearMarks(document.getElementById('note-split-preview'));
          clearMarks(document.getElementById('adr-modal-content'));
          const iframe = document.getElementById('lesson-modal-iframe');
          if (iframe && iframe.contentDocument) clearMarks(iframe.contentDocument.body);

          if (surfaceHint && activeHighlightsCache[surfaceHint]) {
            activeHighlightsCache[surfaceHint].list = [];
            updateHighlightCountBadge(surfaceHint);
            const popover = document.getElementById(`${surfaceHint}-hl-popover`);
            if (popover) popover.style.display = 'none';
          }
          showToast('All highlights cleared');
        }
      } catch (e) {
        showToast('Error clearing highlights');
      }
    }

    // Attach functions globally so iframe click handlers never fail
    window.deleteSingleHighlight = deleteSingleHighlight;
    window.clearActiveHighlights = clearActiveHighlights;

    // Dynamic Notes Resolution (Fixes 404 Bug)
    async function openTopicNote(clusterId, topicId, topicTitle) {
      const cleanSlug = (topicId || '').replace('topic.', '').replace(/\./g, '-');
      const topicLeaf = cleanSlug.split('-').slice(2).join('-') || cleanSlug;
      let resolvedPath = `${clusterId || 'general'}/${cleanSlug || 'note'}.md`;

      // Search globalStatus.notes for existing note matching topic slug or leaf
      if (globalStatus?.notes && Array.isArray(globalStatus.notes)) {
        const matched = globalStatus.notes.find(n => {
          const p = (n.relPath || n.filename || '').toLowerCase();
          return p.includes(cleanSlug.toLowerCase()) ||
                 (topicLeaf && p.includes(topicLeaf.toLowerCase())) ||
                 p.includes(cleanSlug.replace(/-/g, '_'));
        });
        if (matched) {
          resolvedPath = matched.relPath;
        }
      }

      activeNoteRelPath = resolvedPath;
      document.getElementById('note-modal-title').innerText = topicTitle || `Notes: ${topicId}`;
      const pathText = document.getElementById('note-path-text');
      const pathBadge = document.getElementById('note-path-badge');
      const statsText = document.getElementById('note-stats-text');
      if (pathText) pathText.innerText = `notes/${resolvedPath}`;
      if (pathBadge) pathBadge.title = `notes/${resolvedPath}`;
      if (statsText) statsText.innerHTML = `Loading...`;
      setNoteMode('view');
      openModal('note-modal');

      const viewBody = document.getElementById('note-view-body');
      const editBody = document.getElementById('note-edit-body');

      viewBody.innerHTML = '<div style="font-family:var(--font-mono);">Loading note...</div>';
      try {
        const res = await fetch(`/api/note?path=${encodeURIComponent(activeNoteRelPath)}`);
        if (res.ok) {
          const content = await res.text();
          const words = content.trim().split(/\s+/).filter(Boolean).length;
          const readTime = Math.max(1, Math.ceil(words / 200));
          if (statsText) statsText.innerHTML = `${words} words &bull; ~${readTime} min read`;
          viewBody.innerHTML = renderMarkdown(content);
          editBody.value = content;
          loadAndApplyHighlights(activeNoteRelPath, viewBody, 'note');
          if (new URLSearchParams(window.location.search).get('notescroll') === 'bottom') {
            viewBody.scrollTop = viewBody.scrollHeight;
          }
        } else {
          if (statsText) statsText.innerHTML = `New Note`;
          viewBody.innerHTML = '<div style="font-family:var(--font-mono); color:var(--on-surface-variant);">No note recorded yet for this topic. Switch to Edit or Split mode to create one.</div>';
          editBody.value = `# System Architecture Notes: ${topicTitle || topicId}

## Invariant Defended
- Hardware boundary:
- Trade-off derived:
`;
        }
      } catch (e) {
        viewBody.innerText = 'Failed to load note.';
      }
    }

    function openNewNoteModal() {
      openTopicNote('general', `quick-note-${Date.now()}`, 'Quick Note');
    }

    // Notion-Grade Markdown Note Workbench Engine
    let currentNoteMode = 'view'; // 'view' | 'split' | 'edit'

    function setNoteMode(mode) {
      currentNoteMode = mode;
      const viewBody = document.getElementById('note-view-body');
      const editBody = document.getElementById('note-edit-body');
      const splitPreview = document.getElementById('note-split-preview');
      const toolbar = document.getElementById('note-editor-toolbar');
      const saveBtn = document.getElementById('note-save-btn');

      const btnView = document.getElementById('btn-note-view');
      const btnSplit = document.getElementById('btn-note-split');
      const btnEdit = document.getElementById('btn-note-edit');
      const noteHls = document.getElementById('note-highlighter-controls');

      if (btnView) btnView.classList.toggle('active', mode === 'view');
      if (btnSplit) btnSplit.classList.toggle('active', mode === 'split');
      if (btnEdit) btnEdit.classList.toggle('active', mode === 'edit');
      if (noteHls) noteHls.style.display = (mode === 'edit') ? 'none' : 'inline-flex';

      if (mode === 'view') {
        if (toolbar) toolbar.style.display = 'none';
        if (saveBtn) saveBtn.style.display = 'none';
        if (viewBody) {
          viewBody.style.display = 'block';
          viewBody.innerHTML = renderMarkdown(editBody.value);
          loadAndApplyHighlights(activeNoteRelPath, viewBody, 'note');
        }
        if (editBody) editBody.style.display = 'none';
        if (splitPreview) splitPreview.style.display = 'none';
      } else if (mode === 'split') {
        if (toolbar) toolbar.style.display = 'flex';
        if (saveBtn) saveBtn.style.display = 'inline-flex';
        if (viewBody) viewBody.style.display = 'none';
        if (editBody) {
          editBody.style.display = 'block';
          editBody.style.flex = '1';
        }
        if (splitPreview) {
          splitPreview.style.display = 'block';
          splitPreview.style.flex = '1';
          splitPreview.innerHTML = renderMarkdown(editBody.value);
          loadAndApplyHighlights(activeNoteRelPath, splitPreview, 'note');
        }
        editBody.focus();
      } else if (mode === 'edit') {
        if (toolbar) toolbar.style.display = 'flex';
        if (saveBtn) saveBtn.style.display = 'inline-flex';
        if (viewBody) viewBody.style.display = 'none';
        if (splitPreview) splitPreview.style.display = 'none';
        if (editBody) {
          editBody.style.display = 'block';
          editBody.style.flex = '1';
          editBody.focus();
        }
      }
      handleNoteLiveInput();
    }

    function toggleNoteEditMode() {
      if (currentNoteMode === 'view') {
        setNoteMode('split');
      } else {
        setNoteMode('view');
      }
    }

    function handleNoteLiveInput() {
      const editBody = document.getElementById('note-edit-body');
      const splitPreview = document.getElementById('note-split-preview');
      const statsText = document.getElementById('note-stats-text');
      const content = editBody ? editBody.value : '';

      if (currentNoteMode === 'split' && splitPreview) {
        splitPreview.innerHTML = renderMarkdown(content);
      }

      if (statsText) {
        const words = content.trim().split(/\s+/).filter(Boolean).length;
        const readTime = Math.max(1, Math.ceil(words / 200));
        statsText.innerHTML = `${words} words &bull; ~${readTime} min read`;
      }
    }

    function wrapNoteSelection(before, after) {
      const ta = document.getElementById('note-edit-body');
      if (!ta) return;
      const start = ta.selectionStart;
      const end = ta.selectionEnd;
      const text = ta.value;
      const selected = text.slice(start, end) || 'text';
      ta.value = text.slice(0, start) + before + selected + after + text.slice(end);
      ta.selectionStart = start + before.length;
      ta.selectionEnd = start + before.length + selected.length;
      ta.focus();
      handleNoteLiveInput();
    }

    function insertNoteLinePrefix(prefix) {
      const ta = document.getElementById('note-edit-body');
      if (!ta) return;
      const start = ta.selectionStart;
      const text = ta.value;
      const lineStart = text.lastIndexOf('\n', start - 1) + 1;
      ta.value = text.slice(0, lineStart) + prefix + text.slice(lineStart);
      ta.selectionStart = ta.selectionEnd = start + prefix.length;
      ta.focus();
      handleNoteLiveInput();
    }

    function insertNoteSnippet(snippet) {
      const ta = document.getElementById('note-edit-body');
      if (!ta) return;
      const start = ta.selectionStart;
      const end = ta.selectionEnd;
      const text = ta.value;
      ta.value = text.slice(0, start) + snippet + text.slice(end);
      ta.selectionStart = ta.selectionEnd = start + snippet.length;
      ta.focus();
      handleNoteLiveInput();
    }

    function insertNoteTableTemplate() {
      const tpl = `\n| Architectural Trade-Off | Operational Decision Rule | Production Bound / Sizing |\n|:---|:---|:---|\n| Ordering vs. HOL Blocking | QUIC multiplexing when independent | Buffer sizing = BDP (RTT × BW) |\n| Connection Lifecycle | Pre-warm TLS connection pool | Ephemeral port floor (65,535) |\n\n`;
      insertNoteSnippet(tpl);
    }

    function insertNoteCodeBlockTemplate() {
      const tpl = `\n\`\`\`text\n+--------------------+     1 RTT Handshake     +--------------------+\n| Client Application | ----------------------> | Upstream Load Bal. |\n+--------------------+ <---------------------- +--------------------+\n\`\`\`\n\n`;
      insertNoteSnippet(tpl);
    }

    function insertNoteSynthesisTemplate() {
      const tpl = `\n## 1. Ground Truth & First Principles\n- Physical bottleneck:\n- Theoretical limit:\n\n## 2. Active Defense & Invariant Derived\n> [!INVARIANT]\n> Non-negotiable physical or mathematical invariant deduced under dialetical pressure.\n\n## 3. Production Trade-Off & Sizing Matrix\n| Architectural Trade-Off | Decision Rule | Production Sizing Bound |\n|:---|:---|:---|\n| Latency vs. Consistency | Fast-path reads with bounded staleness | Tail SLA < 15ms @ p99 |\n\n`;
      insertNoteSnippet(tpl);
    }

    async function saveNoteFromEditor() {
      const editBody = document.getElementById('note-edit-body');
      const content = editBody ? editBody.value : '';
      try {
        const res = await fetch('/api/note', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ path: activeNoteRelPath, content: content })
        });
        if (res.ok) {
          const viewBody = document.getElementById('note-view-body');
          if (viewBody) viewBody.innerHTML = renderMarkdown(content);
          showToast('Note saved to git repository');
          refreshData();
        } else {
          showToast('Failed to save note');
        }
      } catch (e) {
        showToast('Network error saving note');
      }
    }

    // ADR Decisions Modal (with Topic Filtering)
    async function openADRModal(topicId) {
      openModal('adr-modal');
      const box = document.getElementById('adr-modal-content');
      const titleEl = document.getElementById('adr-modal-title');
      box.innerHTML = '<div style="font-family:var(--font-mono);">Loading DECISIONS.md...</div>';
      try {
        const res = await fetch('/api/decisions');
        const text = await res.text();
        if (topicId) {
          titleEl.innerText = `ADR Defense: ${topicId}`;
          const blocks = text.split(/(?=## ADR-\\d+:)/);
          const matched = blocks.find(b => b.includes(topicId) || b.toLowerCase().includes(topicId.toLowerCase().replace('topic.', '')));
          if (matched) {
            box.innerHTML = `
              <div style="margin-bottom:14px; padding:6px 12px; background:var(--primary-container); border:1px solid var(--border-color); font-family:var(--font-headline); font-size:11px; font-weight:bold; display:flex; justify-content:space-between; align-items:center;">
                <span>Verified Architectural Defense Record</span>
                <button class="btn-ghost" style="padding:2px 6px; font-size:10px;" onclick="openADRModal()">View All ADRs</button>
              </div>
              <div>${renderMarkdown(matched)}</div>
            `;
            loadAndApplyHighlights('DECISIONS.md', box, 'adr');
            return;
          }
        }
        titleEl.innerText = 'Architecture Decision Records (DECISIONS.md)';
        box.innerHTML = renderMarkdown(text);
        loadAndApplyHighlights('DECISIONS.md', box, 'adr');
      } catch (e) {
        box.innerText = 'Failed to load decisions.';
      }
    }

    function escapeHtml(str) {
      if (str === null || str === undefined) return '';
      return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
    }

    // Revision Mode Engine (Spaced Retrieval Practice & Invariant Challenges)
    async function loadRevisions() {
      try {
        const res = await fetch('/api/revisions');
        if (!res.ok) return;
        const data = await res.json();
        revisionsData = data;
        revisionsList = data.revisions || [];
        currentRevisionIdx = 0;
        revisionRevealed = false;
        trapRevealed = false;

        const params = new URLSearchParams(window.location.search);
        if (params.get('reveal') === '1' || params.get('reveal') === 'true') {
          revisionRevealed = true;
        }
        if (params.get('trap') === '1') {
          trapRevealed = true;
        }
        if (params.get('view') === 'grid') {
          revisionViewMode = 'grid';
          const btnCards = document.getElementById('rev-view-cards');
          const btnGrid = document.getElementById('rev-view-grid');
          if (btnCards) btnCards.classList.remove('active');
          if (btnGrid) btnGrid.classList.add('active');
        }
        if (params.get('card')) {
          const cIdx = parseInt(params.get('card'));
          if (!isNaN(cIdx)) currentRevisionIdx = cIdx;
        }

        updateRevisionCounters();
        renderRevisionDeck();
      } catch (e) {
        console.error('Revisions load error:', e);
      }
    }

    function updateRevisionCounters() {
      const allCount = revisionsList.length;
      const dueCount = revisionsList.filter(r => r.isDue).length;
      const needsReviewCount = revisionsList.filter(r => r.masteryStatus === 'needs_review').length;
      const learningCount = revisionsList.filter(r => r.masteryStatus === 'learning' || r.masteryStatus === 'proficient').length;
      const masteredCount = revisionsList.filter(r => r.masteryStatus === 'mastered').length;

      const cAll = document.getElementById('rev-count-all');
      const cDue = document.getElementById('rev-count-due');
      const cNeeds = document.getElementById('rev-count-needs-review');
      const cLearn = document.getElementById('rev-count-learning');
      const cMast = document.getElementById('rev-count-mastered');
      if (cAll) cAll.innerText = allCount;
      if (cDue) cDue.innerText = dueCount;
      if (cNeeds) cNeeds.innerText = needsReviewCount;
      if (cLearn) cLearn.innerText = learningCount;
      if (cMast) cMast.innerText = masteredCount;

      const counter = document.getElementById('revision-counter');
      if (counter) {
        const pct = Math.round((masteredCount / (allCount || 1)) * 100);
        counter.innerHTML = `<span style="color:#10b981;">●</span> ${masteredCount}/${allCount} Mastered (${pct}%) • ${dueCount} Due Today`;
      }
    }

    function getFilteredRevisions() {
      return revisionsList.filter(r => {
        // Status filter
        if (revisionFilter === 'due' && !r.isDue) return false;
        if (revisionFilter === 'needs_review' && r.masteryStatus !== 'needs_review') return false;
        if (revisionFilter === 'learning' && !['learning', 'proficient'].includes(r.masteryStatus)) return false;
        if (revisionFilter === 'mastered' && r.masteryStatus !== 'mastered') return false;

        // Search filter
        if (revisionSearchQuery) {
          const q = revisionSearchQuery;
          const hay = `${r.topicTitle || ''} ${r.realityCheckPrompt || ''} ${r.invariant || ''} ${r.formula || ''} ${r.ruleOfThumb || ''} ${r.clusterTitle || ''}`.toLowerCase();
          if (!hay.includes(q)) return false;
        }

        return true;
      });
    }

    function setRevisionFilter(filter, el) {
      revisionFilter = filter;
      currentRevisionIdx = 0;
      revisionRevealed = false;
      trapRevealed = false;
      document.querySelectorAll('.revision-filter-btn').forEach(btn => btn.classList.remove('active'));
      if (el) el.classList.add('active');
      renderRevisionDeck();
    }

    function handleRevisionSearch(val) {
      revisionSearchQuery = (val || '').trim().toLowerCase();
      currentRevisionIdx = 0;
      revisionRevealed = false;
      trapRevealed = false;
      const clearBtn = document.getElementById('revision-search-clear');
      if (clearBtn) clearBtn.style.display = revisionSearchQuery ? 'inline-flex' : 'none';
      const badge = document.getElementById('revision-search-count-badge');
      const filtered = getFilteredRevisions();
      if (badge) {
        if (revisionSearchQuery) {
          badge.style.display = 'inline-block';
          badge.innerText = `${filtered.length} match${filtered.length === 1 ? '' : 'es'}`;
        } else {
          badge.style.display = 'none';
        }
      }
      renderRevisionDeck();
    }

    function clearRevisionSearch() {
      const inp = document.getElementById('revision-search');
      if (inp) {
        inp.value = '';
        inp.focus();
      }
      handleRevisionSearch('');
    }

    function setRevisionViewMode(mode) {
      revisionViewMode = mode;
      const btnCards = document.getElementById('rev-view-cards');
      const btnGrid = document.getElementById('rev-view-grid');
      if (btnCards) btnCards.classList.toggle('active', mode === 'card');
      if (btnGrid) btnGrid.classList.toggle('active', mode === 'grid');
      renderRevisionDeck();
    }

    function toggleTrap() {
      trapRevealed = !trapRevealed;
      renderRevisionCard();
    }

    function navigateRevision(delta) {
      const filtered = getFilteredRevisions();
      if (!filtered.length) return;
      currentRevisionIdx = (currentRevisionIdx + delta + filtered.length) % filtered.length;
      revisionRevealed = false;
      trapRevealed = false;
      renderRevisionCard();
    }

    function shuffleRevisions() {
      const filtered = getFilteredRevisions();
      if (filtered.length <= 1) return;
      let nextIdx = Math.floor(Math.random() * filtered.length);
      if (nextIdx === currentRevisionIdx) nextIdx = (nextIdx + 1) % filtered.length;
      currentRevisionIdx = nextIdx;
      revisionRevealed = false;
      trapRevealed = false;
      renderRevisionCard();
    }

    function renderRevisionDeck() {
      const container = document.getElementById('revision-card-container');
      if (!container) return;

      if (revisionViewMode === 'grid') {
        renderRevisionGrid();
      } else {
        renderRevisionCard();
      }
    }

    function renderRevisionCard() {
      const container = document.getElementById('revision-card-container');
      if (!container) return;

      const filtered = getFilteredRevisions();

      if (!filtered.length) {
        if (!revisionsList.length) {
          container.innerHTML = `
            <div class="flashcard" style="text-align:center; justify-content:center;">
              <div style="font-family:var(--font-headline); font-size:20px; font-weight:700;">No Revision Cards Yet</div>
              <p style="font-size:13px; color:var(--on-surface-variant); margin-top:8px;">
                Verify topic gates or complete active learning dialectics to populate invariant flashcards.
              </p>
              <div style="margin-top:16px;">
                <button class="btn-primary" onclick="switchTab('curriculum')">
                  <span>Go to Curriculum Syllabus</span>
                  <span class="material-symbols-outlined" style="font-size:14px; margin-left:4px;">arrow_forward</span>
                </button>
              </div>
            </div>
          `;
        } else if (revisionFilter === 'due') {
          container.innerHTML = `
            <div class="flashcard" style="text-align:center; justify-content:center; padding:48px 32px;">
              <div style="width:56px; height:56px; border:3px solid #000; background:#10b981; color:#000; border-radius:50%; display:inline-flex; align-items:center; justify-content:center; margin:0 auto 16px auto; box-shadow:4px 4px 0px #000;">
                <span class="material-symbols-outlined" style="font-size:32px;">verified</span>
              </div>
              <div style="font-family:var(--font-headline); font-size:22px; font-weight:800; letter-spacing:-0.5px;">All Due Cards Reviewed!</div>
              <p style="font-size:14px; color:var(--on-surface-variant); max-width:540px; margin:10px auto; line-height:1.5;">
                You've completed all scheduled retrieval reviews for today. Spaced intervals strengthen structural invariants before the forgetting curve takes hold.
              </p>
              <div style="display:flex; justify-content:center; gap:12px; margin-top:20px; flex-wrap:wrap;">
                <button class="btn-primary" onclick="setRevisionFilter('all', document.querySelector('.revision-filter-btn[data-filter=all]'))">
                  <span class="material-symbols-outlined" style="font-size:16px;">style</span>
                  <span>Review All Deck Cards (${revisionsList.length})</span>
                </button>
                <button class="btn-ghost" onclick="switchTab('curriculum')">
                  <span class="material-symbols-outlined" style="font-size:16px;">arrow_forward</span>
                  <span>Continue Curriculum</span>
                </button>
              </div>
            </div>
          `;
        } else {
          container.innerHTML = `
            <div class="flashcard" style="text-align:center; justify-content:center;">
              <div style="font-family:var(--font-headline); font-size:18px; font-weight:700;">No Matching Cards Found</div>
              <p style="font-size:13px; color:var(--on-surface-variant); margin-top:8px;">
                No flashcards matched your active filter or search query.
              </p>
              <div style="margin-top:16px;">
                <button class="btn-primary" onclick="clearRevisionSearch(); setRevisionFilter('all', document.querySelector('.revision-filter-btn[data-filter=all]'));">
                  <span>Reset Filters</span>
                </button>
              </div>
            </div>
          `;
        }
        return;
      }

      if (currentRevisionIdx >= filtered.length) {
        currentRevisionIdx = 0;
      }

      const rev = filtered[currentRevisionIdx];
      const pct = Math.round(((currentRevisionIdx + 1) / filtered.length) * 100);

      const statusTag = rev.masteryStatus === 'mastered' ?
        '<span style="display:inline-flex; align-items:center; gap:4px; font-family:var(--font-mono); font-size:11px; font-weight:700; color:#10b981; background:rgba(16,185,129,0.12); padding:2px 8px; border:1px solid #10b981;"><span class="material-symbols-outlined" style="font-size:12px;">verified</span> MASTERED</span>' :
        (rev.masteryStatus === 'needs_review' ?
          '<span style="display:inline-flex; align-items:center; gap:4px; font-family:var(--font-mono); font-size:11px; font-weight:700; color:#ef4444; background:rgba(239,68,68,0.12); padding:2px 8px; border:1px solid #ef4444;"><span class="material-symbols-outlined" style="font-size:12px;">replay</span> NEEDS REVIEW</span>' :
          '<span style="display:inline-flex; align-items:center; gap:4px; font-family:var(--font-mono); font-size:11px; font-weight:700; color:#f59e0b; background:rgba(245,158,11,0.12); padding:2px 8px; border:1px solid #f59e0b;"><span class="material-symbols-outlined" style="font-size:12px;">schedule</span> LEARNING</span>');

      container.innerHTML = `
        <div class="flashcard">
          <div class="revision-progress-bar">
            <div class="fill" style="width: ${pct}%;"></div>
          </div>

          <div>
            <div class="flashcard-header">
              <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
                <span class="badge-active">
                  <span class="material-symbols-outlined" style="font-size:12px; margin-right:3px;">school</span>
                  ${escapeHtml(rev.clusterTitle || 'Core Mechanics')}
                </span>
                ${statusTag}
                ${rev.isDue ? '<span style="font-family:var(--font-mono); font-size:10px; font-weight:800; background:#ff5f56; color:#fff; padding:2px 6px; border:1px solid #000;">DUE TODAY</span>' : ''}
              </div>

              <div style="display:flex; align-items:center; gap:8px;">
                <span style="font-family:var(--font-mono); font-size:11px; color:var(--on-surface-variant); font-weight:700;">
                  Card ${currentRevisionIdx + 1} of ${filtered.length}
                </span>
                ${rev.topicId ? `
                  <button class="btn-ghost" style="padding:2px 8px; font-size:10px;" onclick="openLessonModal('${rev.topicId}', '${escapeHtml(rev.topicTitle || '')}')" title="Open Topic Lesson">
                    <span class="material-symbols-outlined" style="font-size:12px;">school</span><span>Lesson</span>
                  </button>
                  <button class="btn-ghost" style="padding:2px 8px; font-size:10px;" onclick="openTopicNote('${rev.clusterId || 'general'}', '${rev.topicId}', '${escapeHtml(rev.topicTitle || '')}')" title="Open Topic Notes">
                    <span class="material-symbols-outlined" style="font-size:12px;">edit_note</span><span>Notes</span>
                  </button>
                ` : ''}
              </div>
            </div>

            <div style="display:flex; align-items:center; gap:8px; margin-top:4px;">
              <span class="flashcard-challenge-pill">
                <span class="material-symbols-outlined" style="font-size:14px;">crisis_alert</span>
                <span>Active Scenario Challenge</span>
              </span>
              <span style="font-family:var(--font-mono); font-size:11px; color:var(--on-surface-variant); font-weight:700;">${escapeHtml(rev.topicTitle || '')}</span>
            </div>

            <div class="flashcard-prompt-text">
              "${escapeHtml(rev.realityCheckPrompt || rev.invariant || 'Defend this architectural invariant under high packet loss.')}"
            </div>

            ${rev.naiveTrap ? `
              <div class="flashcard-trap-box" onclick="toggleTrap()" title="Click to toggle common trap hint">
                <div style="display:flex; align-items:center; justify-content:space-between; cursor:pointer;">
                  <span style="font-family:var(--font-mono); font-size:11px; font-weight:700; color:#f59e0b; display:flex; align-items:center; gap:4px;">
                    <span class="material-symbols-outlined" style="font-size:15px;">warning</span>
                    <span>Naive Intuition Trap (What caught your model?):</span>
                  </span>
                  <span class="material-symbols-outlined" style="font-size:16px; color:var(--on-surface-variant);">${trapRevealed ? 'expand_less' : 'expand_more'}</span>
                </div>
                ${trapRevealed ? `
                  <div style="margin-top:6px; font-family:var(--font-body); font-size:12px; color:var(--on-surface); line-height:1.5;">
                    ${escapeHtml(rev.naiveTrap)}
                  </div>
                ` : `
                  <div style="margin-top:4px; font-family:var(--font-body); font-size:11px; color:var(--on-surface-variant); font-style:italic;">
                    Click to inspect the naive assumption before answering...
                  </div>
                `}
              </div>
            ` : ''}

            ${revisionRevealed ? `
              <div class="flashcard-revealed-grid">
                <div class="defense-card-section invariant-sec">
                  <div class="defense-section-label" style="color:#10b981;">
                    <span class="material-symbols-outlined" style="font-size:15px;">verified</span>
                    <span>Verified Mechanical Invariant</span>
                  </div>
                  <div class="defense-section-body">${escapeHtml(rev.invariant)}</div>
                </div>

                <div class="defense-card-section failure-sec">
                  <div class="defense-section-label" style="color:#ef4444;">
                    <span class="material-symbols-outlined" style="font-size:15px;">dangerous</span>
                    <span>Failure Boundary & Blast Radius</span>
                  </div>
                  <div class="defense-section-body">${escapeHtml(rev.failureBoundary || 'Evaluated failure modes and partition bounds under high load.')}</div>
                </div>

                <div class="defense-card-section formula-sec">
                  <div class="defense-section-label" style="color:#3b82f6;">
                    <span class="material-symbols-outlined" style="font-size:15px;">functions</span>
                    <span>Production Bound & Sizing Math</span>
                  </div>
                  <div class="defense-section-body mono">${escapeHtml(rev.formula || 'Quantitative trade-off defended during sign-off.')}</div>
                </div>

                <div class="defense-card-section rule-sec">
                  <div class="defense-section-label" style="color:#f59e0b;">
                    <span class="material-symbols-outlined" style="font-size:15px;">lightbulb</span>
                    <span>Operational Rule of Thumb</span>
                  </div>
                  <div class="defense-section-body">${escapeHtml(rev.ruleOfThumb || 'Apply deterministic invariants to isolate blast radius.')}</div>
                </div>
              </div>
            ` : ''}
          </div>

          <div>
            ${!revisionRevealed ? `
              <button class="btn-primary" style="width:100%; justify-content:center; padding:13px; font-size:13px;" onclick="revealRevisionCard()">
                <span class="material-symbols-outlined" style="font-size:17px;">visibility</span>
                <span>Reveal Defended Invariant & Sizing Math (Spacebar)</span>
              </button>
            ` : `
              <div>
                <div style="font-family:var(--font-mono); font-size:11px; text-transform:uppercase; font-weight:700; color:var(--on-surface-variant); margin-bottom:8px; display:flex; align-items:center; gap:4px;">
                  <span class="material-symbols-outlined" style="font-size:14px;">psychology</span>
                  <span>Rate Your Recall Precision (Key 1, 2, or 3):</span>
                </div>
                <div class="flashcard-ratings">
                  <button class="btn-ghost" style="flex:1; justify-content:center; color:#ef4444; border-color:#ef4444; padding:10px;" onclick="rateRevision('learning')" title="Key [1]">
                    <span class="material-symbols-outlined" style="font-size:16px;">replay</span>
                    <span>Again (1d)</span>
                    <kbd style="margin-left:4px;">1</kbd>
                  </button>
                  <button class="btn-ghost" style="flex:1; justify-content:center; color:#f59e0b; border-color:#f59e0b; padding:10px;" onclick="rateRevision('proficient')" title="Key [2]">
                    <span class="material-symbols-outlined" style="font-size:16px;">thumb_up</span>
                    <span>Good (3d)</span>
                    <kbd style="margin-left:4px;">2</kbd>
                  </button>
                  <button class="btn-primary" style="flex:1; justify-content:center; background:#10b981; color:#000; border-color:#000; padding:10px;" onclick="rateRevision('mastered')" title="Key [3]">
                    <span class="material-symbols-outlined" style="font-size:16px;">verified</span>
                    <span>Mastered (7d+)</span>
                    <kbd style="margin-left:4px; background:#000; color:#fff; border-color:#000;">3</kbd>
                  </button>
                </div>
              </div>
            `}

            <div class="flashcard-nav-controls">
              <div style="display:flex; align-items:center; gap:8px;">
                <button class="btn-ghost" style="padding:4px 10px; font-size:11px;" onclick="navigateRevision(-1)" title="Previous card (Left Arrow)">
                  <span class="material-symbols-outlined" style="font-size:14px;">arrow_back</span>
                  <span>Prev</span>
                </button>
                <button class="btn-ghost" style="padding:4px 10px; font-size:11px;" onclick="navigateRevision(1)" title="Next card (Right Arrow)">
                  <span>Next</span>
                  <span class="material-symbols-outlined" style="font-size:14px;">arrow_forward</span>
                </button>
                <button class="btn-ghost" style="padding:4px 10px; font-size:11px;" onclick="shuffleRevisions()" title="Shuffle queue order">
                  <span class="material-symbols-outlined" style="font-size:14px;">shuffle</span>
                  <span>Shuffle</span>
                </button>
              </div>

              <div style="font-family:var(--font-mono); font-size:11px; color:var(--on-surface-variant);">
                Next Due: <strong>${rev.nextReviewDate || 'Today'}</strong>
                ${rev.streak ? ` • Streak: <strong>${rev.streak}</strong>` : ''}
              </div>
            </div>
          </div>
        </div>
      `;
    }

    function renderRevisionGrid() {
      const container = document.getElementById('revision-card-container');
      if (!container) return;

      const filtered = getFilteredRevisions();

      if (!filtered.length) {
        container.innerHTML = `
          <div style="text-align:center; padding:48px 24px; border:2px dashed var(--border-color); background:var(--surface-container-lowest);">
            <div style="font-family:var(--font-headline); font-size:18px; font-weight:700;">No Cards Found</div>
            <p style="font-size:13px; color:var(--on-surface-variant); margin-top:8px;">No cards match the active filter or query.</p>
            <button class="btn-primary" style="margin-top:14px;" onclick="clearRevisionSearch(); setRevisionFilter('all', document.querySelector('.revision-filter-btn[data-filter=all]'));">Reset Filters</button>
          </div>
        `;
        return;
      }

      let html = '<div class="revision-grid-container">';
      filtered.forEach((r, idx) => {
        const isMastered = r.masteryStatus === 'mastered';
        const isNeeds = r.masteryStatus === 'needs_review';
        const statusColor = isMastered ? '#10b981' : (isNeeds ? '#ef4444' : '#f59e0b');
        const statusLabel = isMastered ? 'MASTERED' : (isNeeds ? 'NEEDS REVIEW' : 'LEARNING');

        html += `
          <div class="revision-grid-card">
            <div>
              <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:8px; gap:8px;">
                <span style="font-family:var(--font-mono); font-size:10px; font-weight:800; color:${statusColor}; border:1px solid ${statusColor}; padding:1px 6px;">
                  ● ${statusLabel}
                </span>
                <span style="font-family:var(--font-mono); font-size:10px; color:var(--on-surface-variant);">
                  Due: ${r.nextReviewDate || 'Today'}
                </span>
              </div>

              <div style="font-family:var(--font-headline); font-size:15px; font-weight:700; line-height:1.3; color:var(--on-surface); margin-bottom:8px;">
                ${escapeHtml(r.topicTitle || 'Topic')}
              </div>

              <div style="font-size:12px; color:var(--on-surface); line-height:1.45; margin-bottom:10px; font-style:italic;">
                "${escapeHtml((r.realityCheckPrompt || r.invariant || '').slice(0, 140))}${((r.realityCheckPrompt || '').length > 140 ? '...' : '')}"
              </div>

              ${r.formula ? `
                <div style="font-family:var(--font-mono); font-size:11px; background:var(--surface-container-high); padding:4px 8px; border-left:3px solid #3b82f6; margin-bottom:8px; word-break:break-word;">
                  ${escapeHtml(r.formula.slice(0, 100))}
                </div>
              ` : ''}
            </div>

            <div style="display:flex; align-items:center; justify-content:space-between; border-top:1px solid var(--border-color); padding-top:10px; margin-top:8px;">
              <span style="font-family:var(--font-mono); font-size:10px; color:var(--on-surface-variant);">
                Reviewed: ${r.reviewCount || 0} times
              </span>
              <button class="btn-primary" style="padding:4px 10px; font-size:11px;" onclick="practiceCardById('${r.id || r.topicId}')">
                <span class="material-symbols-outlined" style="font-size:13px;">play_arrow</span>
                <span>Practice</span>
              </button>
            </div>
          </div>
        `;
      });
      html += '</div>';
      container.innerHTML = html;
    }

    function practiceCardById(cardId) {
      setRevisionViewMode('card');
      const filtered = getFilteredRevisions();
      const idx = filtered.findIndex(r => r.id === cardId || r.topicId === cardId);
      if (idx !== -1) {
        currentRevisionIdx = idx;
      }
      revisionRevealed = false;
      trapRevealed = false;
      renderRevisionCard();
    }

    function revealRevisionCard() {
      revisionRevealed = true;
      renderRevisionCard();
    }

    async function rateRevision(status) {
      const filtered = getFilteredRevisions();
      if (!filtered.length) return;
      const rev = filtered[currentRevisionIdx];
      try {
        await fetch('/api/revisions/rate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ revisionId: rev.id, masteryStatus: status })
        });
        showToast(`Marked ${status} (scheduled review updated)`);

        // Update local state directly
        rev.masteryStatus = status;
        rev.isDue = false;
        rev.reviewCount = (rev.reviewCount || 0) + 1;
        if (status === 'mastered') {
          rev.streak = (rev.streak || 0) + 1;
        } else {
          rev.streak = 0;
        }
        updateRevisionCounters();
      } catch (e) {}

      // Move to next card
      if (filtered.length > 1) {
        currentRevisionIdx = (currentRevisionIdx + 1) % filtered.length;
      }
      revisionRevealed = false;
      trapRevealed = false;
      renderRevisionDeck();
    }

    // Keyboard navigation (Esc, Space, 1, 2, 3, ?, /)
    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        const revSearchInp = document.getElementById('revision-search');
        if (document.activeElement === revSearchInp) {
          clearRevisionSearch();
          revSearchInp.blur();
          return;
        }
        const curSearchInp = document.getElementById('curriculum-search');
        if (document.activeElement === curSearchInp) {
          clearSearch();
          curSearchInp.blur();
          return;
        }
        closeLessonModal();
        closeModal('note-modal');
        closeModal('adr-modal');
        closeModal('new-project-modal');
        closeModal('settings-modal');
        closeModal('shortcuts-modal');
        closeModal('topic-status-modal');
      } else if (e.key === '?' && !['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) {
        e.preventDefault();
        const scModal = document.getElementById('shortcuts-modal');
        if (scModal && scModal.classList.contains('active')) {
          closeModal('shortcuts-modal');
        } else {
          openShortcutsModal();
        }
      } else if (e.key === '/' && !['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) {
        const curPanel = document.getElementById('panel-curriculum');
        const revPanel = document.getElementById('panel-revision');
        if (curPanel && curPanel.classList.contains('active')) {
          const searchInp = document.getElementById('curriculum-search');
          if (searchInp) {
            e.preventDefault();
            searchInp.focus();
            searchInp.select();
          }
        } else if (revPanel && revPanel.classList.contains('active')) {
          const revSearchInp = document.getElementById('revision-search');
          if (revSearchInp) {
            e.preventDefault();
            revSearchInp.focus();
            revSearchInp.select();
          }
        }
      } else if (e.key === 'f' || e.key === 'F') {
        const lessonModal = document.getElementById('lesson-modal');
        if (lessonModal && lessonModal.classList.contains('active')) {
          if (!['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) {
            toggleLessonFullscreen();
          }
        }
      }

      const isInputFocused = ['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName);
      const anyModalOpen = !!document.querySelector('.modal-overlay.active');
      const revPanel = document.getElementById('panel-revision');
      const isRevActive = revPanel && revPanel.classList.contains('active');

      if (isRevActive) {
        if (e.code === 'Space') {
          e.preventDefault();
          if (!revisionRevealed) {
            revealRevisionCard();
          }
        } else if (e.key === 'ArrowLeft') {
          e.preventDefault();
          navigateRevision(-1);
        } else if (e.key === 'ArrowRight') {
          e.preventDefault();
          navigateRevision(1);
        } else if (e.key === 't' || e.key === 'T') {
          if (!['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) {
            e.preventDefault();
            toggleTrap();
          }
        } else if (revisionRevealed) {
          if (e.key === '1') {
            e.preventDefault();
            rateRevision('learning');
          } else if (e.key === '2') {
            e.preventDefault();
            rateRevision('proficient');
          } else if (e.key === '3') {
            e.preventDefault();
            rateRevision('mastered');
          }
        }
      } else if (!isInputFocused && !anyModalOpen) {
        if (e.key === '1') { switchTab('projects'); }
        else if (e.key === '2') { switchTab('curriculum'); }
        else if (e.key === '3') { switchTab('revision'); }
      }
    });

    // Settings Modal & Updates Engine
    async function openSettingsModal(section = null) {
      openModal('settings-modal');
      const savedPreset = localStorage.getItem('sds_theme_preset') || 'slate-clean';
      document.getElementById('settings-theme-preset').value = savedPreset;
      try {
        const res = await fetch('/api/settings');
        if (res.ok) {
          const data = await res.json();
          const p = data.project || {};
          document.getElementById('settings-notes-dir').value = p.notesDir || 'notes';
          document.getElementById('settings-auto-notes').checked = (p.autoGenerateNotes !== false);
          const fmtEl = document.getElementById('settings-lesson-format');
          if (fmtEl) fmtEl.value = p.outputType || 'html';
        }
      } catch (e) {}
      checkForUpdates(false);
      if (section === 'updates') {
        setTimeout(() => {
          const upSec = document.getElementById('settings-updates-section');
          if (upSec) upSec.scrollIntoView({ behavior: 'smooth' });
        }, 120);
      }
    }

    async function checkForUpdates(force = false) {
      const spinner = document.getElementById('update-spinner-icon');
      const statusEl = document.getElementById('settings-update-status');
      const cmdBox = document.getElementById('settings-update-command-box');
      const verLabel = document.getElementById('nav-version-label');
      const installedEl = document.getElementById('settings-installed-version');

      if (spinner) spinner.style.animation = 'spin 1s linear infinite';
      if (statusEl) statusEl.innerText = 'Checking remote repository for updates...';

      try {
        const res = await fetch(`/api/update?force=${force}`);
        if (res.ok) {
          const data = await res.json();
          const curr = data.currentVersion || 'v3.7.0';
          const remote = data.remoteVersion || curr;
          const isAvail = (data.updateAvailable === true);

          const formattedCurr = curr.startsWith('v') ? curr : `v${curr}`;
          if (verLabel) verLabel.innerText = formattedCurr;
          if (installedEl) installedEl.innerText = formattedCurr;

          if (isAvail) {
            if (statusEl) {
              statusEl.innerHTML = `<span style="color:var(--primary-container); font-weight:bold;">🔔 Update available: v${remote}</span> (Installed: ${formattedCurr}). Run the safe updater below:`;
            }
            if (cmdBox) cmdBox.style.display = 'block';
            showToast(`Update available: v${remote}!`);
          } else {
            if (statusEl) {
              statusEl.innerHTML = `<span style="color:var(--emerald-light); font-weight:bold;">✅ You are on the latest version (${formattedCurr}).</span> All skills up to date.`;
            }
            if (cmdBox) cmdBox.style.display = 'block';
            if (force) showToast(`Studio is up to date (${formattedCurr})`);
          }
        } else {
          if (statusEl) statusEl.innerText = 'Unable to check for updates (offline or network error).';
        }
      } catch (e) {
        if (statusEl) statusEl.innerText = 'Unable to reach update service.';
      } finally {
        if (spinner) spinner.style.animation = 'none';
      }
    }

    async function checkEagerAutoUpdate() {
      try {
        const res = await fetch('/api/update?force=false');
        if (res.ok) {
          const data = await res.json();
          const curr = data.currentVersion || 'v3.7.0';
          const remote = data.remoteVersion || curr;
          const formattedCurr = curr.startsWith('v') ? curr : `v${curr}`;
          const formattedRemote = remote.startsWith('v') ? remote : `v${remote}`;
          const verLabel = document.getElementById('nav-version-label');
          const installedEl = document.getElementById('settings-installed-version');
          if (verLabel) verLabel.innerText = formattedCurr;
          if (installedEl) installedEl.innerText = formattedCurr;

          if (data.updateAvailable === true) {
            const banner = document.getElementById('eager-update-banner');
            const text = document.getElementById('eager-update-text');
            const pill = document.getElementById('nav-version-pill');
            if (text) text.innerHTML = `<span><strong>System Design Studio ${formattedRemote}</strong> is now available (Installed: ${formattedCurr}).</span>`;
            if (banner) banner.style.display = 'flex';
            if (pill) {
              pill.style.borderColor = 'var(--secondary)';
              pill.title = `Update available: ${formattedRemote}! Click to update`;
              const dot = pill.querySelector('.status-dot');
              if (dot) { dot.className = 'status-dot pulse'; dot.style.backgroundColor = '#ef4444'; }
            }
          }
        }
      } catch (e) {
        // Eager background check ignores offline/network error silently
      }
    }

    function dismissUpdateBanner() {
      const banner = document.getElementById('eager-update-banner');
      if (banner) banner.style.display = 'none';
    }

    function copyUpdateCommand(btn = null) {
      const cmd = document.getElementById('settings-update-cmd')?.innerText || 'curl -fsSL https://raw.githubusercontent.com/alph-a07/system-design-studio/main/update.sh | bash';
      if (navigator.clipboard) {
        navigator.clipboard.writeText(cmd).then(() => {
          showToast('Update command copied to clipboard');
          if (btn) {
            const orig = btn.innerText;
            btn.innerText = 'Copied!';
            setTimeout(() => { btn.innerText = orig; }, 1500);
          }
        });
      }
    }

    async function handleSaveSettings(event) {
      event.preventDefault();
      const notesDir = document.getElementById('settings-notes-dir').value;
      const autoNotes = document.getElementById('settings-auto-notes').checked;
      const outputType = document.getElementById('settings-lesson-format')?.value || 'html';
      const themePreset = document.getElementById('settings-theme-preset').value;

      applyThemePreset(themePreset);

      try {
        await fetch('/api/settings', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            notesDir: notesDir,
            autoGenerateNotes: autoNotes,
            outputType: outputType
          })
        });
        closeModal('settings-modal');
        showToast('Settings saved to disk');
        refreshData();
      } catch (e) {
        showToast('Failed to save settings');
      }
    }

    // Boot
    window.addEventListener('DOMContentLoaded', () => {
      initTheme();
      refreshData();
      setupSSE();
      checkEagerAutoUpdate();
      refreshData();
      setupSSE();

      // Notion Markdown Editor Keyboard Shortcuts (Tab indent, Shift+Tab, Cmd+B, Cmd+I, Cmd+S)
      const noteTa = document.getElementById('note-edit-body');
      if (noteTa) {
        noteTa.addEventListener('keydown', (e) => {
          if (e.key === 'Tab') {
            e.preventDefault();
            const start = noteTa.selectionStart;
            const end = noteTa.selectionEnd;
            if (e.shiftKey) {
              const text = noteTa.value;
              const lineStart = text.lastIndexOf('\n', start - 1) + 1;
              if (text.substr(lineStart, 2) === '  ') {
                noteTa.value = text.slice(0, lineStart) + text.slice(lineStart + 2);
                noteTa.selectionStart = noteTa.selectionEnd = Math.max(lineStart, start - 2);
              }
            } else {
              noteTa.value = noteTa.value.substring(0, start) + '  ' + noteTa.value.substring(end);
              noteTa.selectionStart = noteTa.selectionEnd = start + 2;
            }
            handleNoteLiveInput();
          } else if ((e.ctrlKey || e.metaKey) && (e.key === 's' || e.key === 'S')) {
            e.preventDefault();
            saveNoteFromEditor();
          } else if ((e.ctrlKey || e.metaKey) && (e.key === 'b' || e.key === 'B')) {
            e.preventDefault();
            wrapNoteSelection('**', '**');
          } else if ((e.ctrlKey || e.metaKey) && (e.key === 'i' || e.key === 'I')) {
            e.preventDefault();
            wrapNoteSelection('*', '*');
          }
        });
      }

      // Backdrop dismissal on outside click for all dialog modals
      document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', (e) => {
          if (e.target === overlay) {
            if (overlay.id === 'lesson-modal') closeLessonModal();
            else closeModal(overlay.id);
          }
        });
      });

      // Dismiss highlight popovers on click outside
      document.addEventListener('click', (e) => {
        if (!e.target.closest('.highlighter-controls-group')) {
          document.querySelectorAll('.hl-popover-menu').forEach(p => { p.style.display = 'none'; });
        }
      });

      // Initialize update version badge
      checkForUpdates(false);

      // Deep linking via URL query parameters
      const params = new URLSearchParams(window.location.search);
      if (params.get('theme') === 'light') {
        document.documentElement.classList.remove('dark');
        localStorage.setItem('sds_theme', 'light');
        const icon = document.getElementById('theme-icon');
        if (icon) icon.innerText = 'dark_mode';
      } else if (params.get('theme') === 'dark') {
        document.documentElement.classList.add('dark');
        localStorage.setItem('sds_theme', 'dark');
        const icon = document.getElementById('theme-icon');
        if (icon) icon.innerText = 'light_mode';
      }
      if (params.get('preset')) {
        document.documentElement.setAttribute('data-theme-preset', params.get('preset'));
        localStorage.setItem('sds_theme_preset', params.get('preset'));
      }
      if (params.get('modal') === 'settings' || params.get('settings')) {
        setTimeout(() => openSettingsModal('updates'), 150);
      }
      if (params.get('tab')) {
        setTimeout(() => switchTab(params.get('tab')), 100);
      }
      if (params.get('lesson')) {
        setTimeout(() => {
          openLessonModal(params.get('lesson'), params.get('lesson'), params.get('artifact') || '');
          if (params.get('format')) {
            setTimeout(() => switchLessonFormat(params.get('format')), 150);
          }
          if (params.get('fullscreen') === 'true') {
            setTimeout(() => toggleLessonFullscreen(), 200);
          }
        }, 350);
      } else if (params.get('note')) {
        setTimeout(() => {
          openTopicNote(params.get('cluster') || 'cluster.0.1', params.get('note'), params.get('title') || 'Study Note');
          if (params.get('hlmenu')) {
            setTimeout(() => toggleHighlightsPopover('note'), 450);
          }
        }, 350);
      }
      if (params.get('shortcuts') === 'true') {
        setTimeout(() => openShortcutsModal(), 350);
      }
      if (params.get('adr')) {
        openADRModal(params.get('adr') === 'true' ? null : params.get('adr'));
      }
      if (params.get('search')) {
        setTimeout(() => applySearchTag(params.get('search')), 350);
      }
      if (params.get('reveal') === 'true') {
        setTimeout(() => revealRevisionCard(), 350);
      }
      if (params.get('tier')) {
        setTimeout(() => setTierFilter(params.get('tier')), 200);
      }
      if (params.get('track')) {
        setTimeout(() => {
          const sel = document.getElementById('curriculum-track-select');
          if (sel) sel.value = params.get('track');
          setTrackFilter(params.get('track'));
        }, 200);
      }
      if (params.get('status')) {
        setTimeout(() => {
          const sel = document.getElementById('curriculum-status-select');
          if (sel) sel.value = params.get('status');
          setTopicFilterSelect(params.get('status'));
        }, 200);
      }
      if (params.get('view')) {
        setTimeout(() => setViewMode(params.get('view')), 200);
      }
      if (params.get('notemode')) {
        setTimeout(() => setNoteMode(params.get('notemode')), 450);
      }
      if (params.get('notescroll') === 'bottom') {
        setTimeout(() => {
          const view = document.getElementById('note-view-body');
          if (view) view.scrollTop = view.scrollHeight;
        }, 550);
      }
      if (params.get('statusmenu')) {
        setTimeout(() => openTopicStatusMenu(null, params.get('statusmenu'), 'verified', 'TCP vs UDP'), 400);
      }
    });
  </script>
</body>
</html>
"""

class StudioDashboardHandler(BaseHTTPRequestHandler):
    inst_dir = None
    base_dir = None
    pinned_instance = False

    def log_message(self, format, *args):
        pass

    def send_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_cors()
        self.end_headers()

    def sync_active_instance(self):
        if StudioDashboardHandler.pinned_instance:
            return
        try:
            reg = get_live_projects_registry(current_inst_dir=StudioDashboardHandler.inst_dir)
            active_id = reg.get("activeProjectId")
            if active_id:
                for p in reg.get("projects", []):
                    if p.get("id") == active_id:
                        p_path = os.path.expanduser(p.get("projectPath", ""))
                        expected_inst = os.path.join(p_path, ".system-design") if not p_path.endswith(".system-design") else p_path
                        if os.path.isdir(expected_inst) and os.path.isfile(os.path.join(expected_inst, "manifest.json")):
                            if StudioDashboardHandler.inst_dir != expected_inst:
                                StudioDashboardHandler.inst_dir = expected_inst
                                StudioDashboardHandler.base_dir = os.path.dirname(expected_inst) if os.path.basename(expected_inst) == ".system-design" else expected_inst
                        break
        except Exception:
            pass

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        self.sync_active_instance()

        if path in ["/", "/index.html"]:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_cors()
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

            settings_path = os.path.join(self.inst_dir, "settings.json")
            settings_obj = {}
            if os.path.isfile(settings_path):
                try:
                    with open(settings_path, "r", encoding="utf-8") as sf:
                        settings_obj = json.load(sf)
                except Exception:
                    pass

            payload = {
                "manifest": manifest,
                "settings": settings_obj,
                "git": git_info,
                "lessons": lessons,
                "notes": notes,
                "baseDir": self.base_dir,
                "instanceDir": self.inst_dir,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_cors()
            self.end_headers()
            self.wfile.write(json.dumps(payload).encode("utf-8"))
            return

        elif path == "/api/projects":
            reg = get_live_projects_registry(current_inst_dir=StudioDashboardHandler.inst_dir)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_cors()
            self.end_headers()
            self.wfile.write(json.dumps(reg).encode("utf-8"))
            return

        elif path == "/api/revisions":
            revisions_file = os.path.join(self.inst_dir, "revisions.json")
            data = None
            if os.path.isfile(revisions_file):
                try:
                    with open(revisions_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except Exception:
                    data = None
            if (not data or not isinstance(data.get("revisions"), list)) and update_revisions_mod:
                try:
                    data = update_revisions_mod.sync_revisions(self.inst_dir)
                except Exception:
                    data = {"revisions": []}
            if not data:
                data = {"revisions": []}

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_cors()
            self.end_headers()
            self.wfile.write(json.dumps(data).encode("utf-8"))
            return

        elif path in ["/update", "/api/update"]:
            force_check = query.get("force", ["false"])[0].lower() in ["true", "1"]
            try:
                scripts_dir = os.path.dirname(os.path.abspath(__file__))
                if scripts_dir not in sys.path:
                    sys.path.insert(0, scripts_dir)
                import importlib
                check_mod = importlib.import_module("check-updates")
                update_info = check_mod.check_for_updates(force=force_check, instance_dir=self.inst_dir)
            except Exception as e:
                update_info = {
                    "status": "error",
                    "currentVersion": "3.3.1",
                    "remoteVersion": None,
                    "updateAvailable": False,
                    "error": str(e)
                }
            update_info["updateCommand"] = "curl -fsSL https://raw.githubusercontent.com/alph-a07/system-design-studio/main/update.sh | bash"
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_cors()
            self.end_headers()
            self.wfile.write(json.dumps(update_info).encode("utf-8"))
            return

        elif path == "/api/settings":
            settings_path = os.path.join(self.inst_dir, "settings.json")
            proj_settings = {}
            if os.path.isfile(settings_path):
                try:
                    with open(settings_path, "r", encoding="utf-8") as f:
                        proj_settings = json.load(f)
                except Exception:
                    pass

            global_cfg_path = os.path.join(get_global_studio_dir(), "config.json")
            global_settings = {}
            if os.path.isfile(global_cfg_path):
                try:
                    with open(global_cfg_path, "r", encoding="utf-8") as f:
                        global_settings = json.load(f)
                except Exception:
                    pass

            payload = {"project": proj_settings, "global": global_settings}
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_cors()
            self.end_headers()
            self.wfile.write(json.dumps(payload).encode("utf-8"))
            return

        elif path in ["/highlights", "/api/highlights"]:
            raw_target = query.get("artifact", ["default"])[0]
            clean_rel = raw_target.replace("\\", "/")
            if ".." in clean_rel.split("/") or clean_rel.startswith("/") or "\x00" in clean_rel:
                self.send_response(403)
                self.send_cors()
                self.end_headers()
                self.wfile.write(b"Access denied")
                return
            data = load_highlights_data(self.inst_dir, raw_target)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_cors()
            self.end_headers()
            self.wfile.write(json.dumps(data).encode("utf-8"))
            return

        elif path == "/api/lesson":
            raw_target = query.get("path", [""])[0]
            clean_rel = raw_target.replace("\\", "/")
            if ".." in clean_rel.split("/") or clean_rel.startswith("/") or "\x00" in clean_rel:
                self.send_response(403)
                self.send_cors()
                self.end_headers()
                self.wfile.write(b"Access denied")
                return

            clean_name = os.path.basename(raw_target)
            candidates = [
                os.path.join(self.inst_dir, "lessons", clean_name),
                os.path.join(self.base_dir, "lessons", clean_name),
                os.path.join(self.inst_dir, raw_target.lstrip("/")),
                os.path.join(self.base_dir, raw_target.lstrip("/"))
            ]
            lesson_file = None
            abs_inst = os.path.abspath(self.inst_dir)
            abs_base = os.path.abspath(self.base_dir)
            for c in candidates:
                abs_c = os.path.abspath(c)
                if (abs_c.startswith(abs_inst + os.sep) or abs_c.startswith(abs_base + os.sep) or abs_c == abs_inst or abs_c == abs_base) and os.path.isfile(abs_c):
                    lesson_file = abs_c
                    break

            if lesson_file:
                self.send_response(200)
                is_md = lesson_file.endswith(".md")
                content_type = "text/markdown; charset=utf-8" if is_md else "text/html; charset=utf-8"
                self.send_header("Content-Type", content_type)
                self.send_cors()
                self.end_headers()
                with open(lesson_file, "rb") as f:
                    content_bytes = f.read()

                if not is_md:
                    try:
                        html_str = content_bytes.decode("utf-8")
                        # Strip any legacy baked-in theme CSS variables from artifact so they cannot leak into dashboard rendering
                        html_str = re.sub(r'/\*\s*Custom Theme CSS Variables[^*]*\*/\s*:root\s*\{[^}]*\}', '', html_str, flags=re.DOTALL)
                        html_str = re.sub(r':root\s*\{\s*--background:[^}]*\}', '', html_str, flags=re.DOTALL)
                        theme_param = query.get("theme", ["dark"])[0]
                        preset_param = query.get("preset", ["slate-clean"])[0]
                        theme_injection = f"""<style id="sds-dynamic-theme-vars">
/* System Design Studio - Dynamic Live Theme Injection */
:root,
html:not(.dark),
html[data-theme-preset="editorial-paper"] {{
  --background: #fbfbfa !important;
  --foreground: #18181b !important;
  --card: #ffffff !important;
  --card-border: #e4e4e7 !important;
  --border: #e4e4e7 !important;
  --muted-foreground: #71717a !important;
  --primary: #2563eb !important;
  --primary-hover: #1d4ed8 !important;
  --accent-badge: #eff6ff !important;
  --accent-badge-text: #1d4ed8 !important;
  color-scheme: light;
}}

html.dark,
html.dark[data-theme-preset="slate-clean"] {{
  --background: #0f172a !important;
  --foreground: #f8fafc !important;
  --card: #1e293b !important;
  --card-border: #334155 !important;
  --border: #334155 !important;
  --muted-foreground: #94a3b8 !important;
  --primary: #3b82f6 !important;
  --primary-hover: #2563eb !important;
  --accent-badge: #1e3a8a !important;
  --accent-badge-text: #93c5fd !important;
  color-scheme: dark;
}}

html.dark[data-theme-preset="cyber-obsidian"],
html.dark[data-theme-preset="midnight-neon"] {{
  --background: #05070c !important;
  --foreground: #f1f5f9 !important;
  --card: #0d1117 !important;
  --card-border: #21262d !important;
  --border: #21262d !important;
  --muted-foreground: #8b949e !important;
  --primary: #06b6d4 !important;
  --primary-hover: #0891b2 !important;
  --accent-badge: #083344 !important;
  --accent-badge-text: #67e8f9 !important;
  color-scheme: dark;
}}

html.dark[data-theme-preset="nordic-frost"] {{
  --background: #242933 !important;
  --foreground: #eceff4 !important;
  --card: #2e3440 !important;
  --card-border: #434c5e !important;
  --border: #434c5e !important;
  --muted-foreground: #d8dee9 !important;
  --primary: #88c0d0 !important;
  --primary-hover: #81a1c1 !important;
  --accent-badge: #434c5e !important;
  --accent-badge-text: #88c0d0 !important;
  color-scheme: dark;
}}

html.dark[data-theme-preset="warm-amber"] {{
  --background: #1c1917 !important;
  --foreground: #fafaf9 !important;
  --card: #292524 !important;
  --card-border: #44403c !important;
  --border: #44403c !important;
  --muted-foreground: #a8a29e !important;
  --primary: #f59e0b !important;
  --primary-hover: #d97706 !important;
  --accent-badge: #451a03 !important;
  --accent-badge-text: #fcd34d !important;
  color-scheme: dark;
}}

body {{
  background-color: var(--background) !important;
  color: var(--foreground) !important;
  transition: background-color 0.2s cubic-bezier(0.16, 1, 0.3, 1), color 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}}

/* Light mode component & container adaptations */
html:not(.dark) .bg-\\[var\\(--card\\)\\],
html:not(.dark) .bg-\\[var\\(--background\\)\\] {{
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}}

html:not(.dark) .bg-stone-900,
html:not(.dark) .bg-stone-900\\/80,
html:not(.dark) .bg-stone-950 {{
  background-color: #f8fafc !important;
  color: #0f172a !important;
  border-color: #e2e8f0 !important;
}}

html:not(.dark) .bg-stone-800 {{
  background-color: #f1f5f9 !important;
  color: #334155 !important;
  border-color: #cbd5e1 !important;
}}

html:not(.dark) .border-stone-800,
html:not(.dark) .border-stone-700 {{
  border-color: #e2e8f0 !important;
}}

html:not(.dark) .text-stone-300,
html:not(.dark) .text-stone-400 {{
  color: #475569 !important;
}}

html:not(.dark) .text-stone-500 {{
  color: #64748b !important;
}}

html:not(.dark) .text-amber-300 {{
  color: #b45309 !important;
}}

html:not(.dark) .text-amber-200 {{
  color: #92400e !important;
}}

html:not(.dark) .jargon-card {{
  background: #fffbeb !important;
  border-color: #fcd34d !important;
}}

html:not(.dark) .jargon-title {{
  color: #b45309 !important;
}}

html:not(.dark) .jargon-pill {{
  background: #fef3c7 !important;
  color: #92400e !important;
}}

html:not(.dark) .bg-blue-950,
html:not(.dark) .bg-blue-950\\/80 {{
  background-color: #eff6ff !important;
  border-color: #bfdbfe !important;
  color: #1e40af !important;
}}

html:not(.dark) .bg-emerald-950,
html:not(.dark) .bg-emerald-950\\/80 {{
  background-color: #ecfdf5 !important;
  border-color: #a7f3d0 !important;
  color: #065f46 !important;
}}

html:not(.dark) .bg-amber-950,
html:not(.dark) .bg-amber-950\\/80 {{
  background-color: #fffbeb !important;
  border-color: #fde68a !important;
  color: #92400e !important;
}}

html:not(.dark) .bg-rose-950,
html:not(.dark) .bg-rose-950\\/80 {{
  background-color: #fff1f2 !important;
  border-color: #fecdd3 !important;
  color: #9f1239 !important;
}}

html:not(.dark) .text-emerald-400 {{
  color: #059669 !important;
}}

html:not(.dark) .text-blue-400 {{
  color: #2563eb !important;
}}

html:not(.dark) .text-rose-400 {{
  color: #e11d48 !important;
}}

html:not(.dark) ::-webkit-scrollbar-track {{
  background: var(--background) !important;
}}
html:not(.dark) ::-webkit-scrollbar-thumb {{
  background: #cbd5e1 !important;
}}

/* Clean, content-hugging text selection inside lessons */
::selection {{
  background-color: rgba(0, 229, 255, 0.28) !important;
  color: inherit !important;
}}
html.dark ::selection {{
  background-color: rgba(0, 229, 255, 0.32) !important;
  color: inherit !important;
}}
html::selection,
html.dark::selection,
html:not(.dark)::selection,
body::selection,
html.dark body::selection,
html:not(.dark) body::selection,
main::selection,
html.dark main::selection,
html:not(.dark) main::selection,
section::selection,
html.dark section::selection,
html:not(.dark) section::selection,
article::selection,
html.dark article::selection,
html:not(.dark) article::selection,
header::selection,
html.dark header::selection,
html:not(.dark) header::selection,
footer::selection,
html.dark footer::selection,
html:not(.dark) footer::selection {{
  background-color: transparent !important;
}}
p, .editorial-lead, h1, h2, h3, h4, h5, h6, li, blockquote,
.notion-p, .notion-h1, .notion-h2, .notion-h3 {{
  width: fit-content !important;
  max-width: 100% !important;
}}
</style>
<script id="sds-theme-listener">
(function() {{
  function applyTheme(theme, preset) {{
    const isDark = (theme === 'dark');
    if (isDark) {{
      document.documentElement.classList.add('dark');
    }} else {{
      document.documentElement.classList.remove('dark');
    }}
    if (preset) {{
      document.documentElement.setAttribute('data-theme-preset', preset);
    }}
  }}

  const initialTheme = '{theme_param}';
  const initialPreset = '{preset_param}';
  applyTheme(initialTheme, initialPreset);

  window.addEventListener('message', function(e) {{
    if (e.data && e.data.type === 'sds-theme-change') {{
      applyTheme(e.data.theme, e.data.preset);
    }}
  }});
}})();
</script>"""
                        if "</head>" in html_str:
                            html_str = html_str.replace("</head>", theme_injection + "</head>", 1)
                        else:
                            html_str = theme_injection + html_str
                        content_bytes = html_str.encode("utf-8")
                    except Exception:
                        pass

                self.wfile.write(content_bytes)
            else:
                self.send_response(404)
                self.send_cors()
                self.end_headers()
                self.wfile.write(b"Lesson file not found")
            return

        elif path == "/api/note":
            rel_path = query.get("path", [""])[0]
            clean_rel = rel_path.replace("\\", "/")
            if ".." in clean_rel.split("/") or clean_rel.startswith("/") or "\x00" in clean_rel:
                self.send_response(403)
                self.send_cors()
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
            norm_rel = os.path.normpath(clean_rel).lstrip("/")
            target = os.path.abspath(os.path.join(notes_dir, norm_rel))
            abs_notes = os.path.abspath(notes_dir)
            if not (target == abs_notes or target.startswith(abs_notes + os.sep)):
                self.send_response(403)
                self.send_cors()
                self.end_headers()
                self.wfile.write(b"Access denied")
                return

            if os.path.isfile(target):
                self.send_response(200)
                self.send_header("Content-Type", "text/markdown; charset=utf-8")
                self.send_cors()
                self.end_headers()
                with open(target, "rb") as f:
                    self.wfile.write(f.read())
            else:
                # Recursive fallback search inside notes_dir
                fallback_target = None
                target_base = os.path.basename(norm_rel)
                target_stem = target_base.replace(".md", "")
                if os.path.isdir(notes_dir):
                    for root, _, files in os.walk(notes_dir):
                        if target_base in files:
                            fallback_target = os.path.join(root, target_base)
                            break
                        for f in files:
                            if f.endswith(".md") and (target_stem in f or f.replace(".md", "") in target_stem):
                                fallback_target = os.path.join(root, f)
                                break
                        if fallback_target:
                            break

                if fallback_target and os.path.isfile(fallback_target):
                    self.send_response(200)
                    self.send_header("Content-Type", "text/markdown; charset=utf-8")
                    self.send_cors()
                    self.end_headers()
                    with open(fallback_target, "rb") as f:
                        self.wfile.write(f.read())
                else:
                    self.send_response(404)
                    self.send_cors()
                    self.end_headers()
                    self.wfile.write(b"Note not found")
            return

        elif path == "/api/decisions":
            dec_file = os.path.join(self.inst_dir, "DECISIONS.md")
            if os.path.isfile(dec_file):
                self.send_response(200)
                self.send_header("Content-Type", "text/markdown; charset=utf-8")
                self.send_cors()
                self.end_headers()
                with open(dec_file, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_cors()
                self.end_headers()
                self.wfile.write(b"No DECISIONS.md found yet.")
            return

        elif path == "/api/events":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_cors()
            self.end_headers()

            initial_hash = compute_instance_state_hash(self.inst_dir, self.base_dir)
            try:
                self.wfile.write(b": connected\n\n")
                self.wfile.flush()
                while True:
                    time.sleep(1.2)
                    current_hash = compute_instance_state_hash(self.inst_dir, self.base_dir)
                    if current_hash != initial_hash:
                        initial_hash = current_hash
                        msg = f"data: {json.dumps({'type': 'update', 'timestamp': time.time()})}\n\n"
                        self.wfile.write(msg.encode("utf-8"))
                        self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, Exception):
                pass
            return

        else:
            self.send_response(404)
            self.send_cors()
            self.end_headers()
            self.wfile.write(b"Not found")

    def do_POST(self):
        self.sync_active_instance()
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length > 0 else b"{}"
        try:
            payload = json.loads(body.decode("utf-8")) if body else {}
        except Exception:
            payload = {}

        if path == "/api/topic/status":
            topic_id = payload.get("topicId")
            status = payload.get("status", "completed")
            if status == "verified":
                status = "completed"
            evidence = payload.get("evidence", "")
            hypothesis = payload.get("hypothesis", "")
            discussion = payload.get("discussion_summary", "")

            # 1. Topic Status Reset (Zero Git Rollback Data Hazard)
            if status == "not_started":
                manifest_path = os.path.join(self.inst_dir, "manifest.json")
                if os.path.isfile(manifest_path):
                    try:
                        with open(manifest_path, "r", encoding="utf-8") as mf:
                            m_data = json.load(mf)

                        # Find topic and reset status to unseen
                        topic_title = None
                        for c in m_data.get("curriculum", {}).get("clusters", []):
                            for t in c.get("topics", []):
                                if t.get("id") == topic_id:
                                    t["status"] = "unseen"
                                    topic_title = t.get("title")
                                    break

                        m_data["lastUpdated"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
                        with open(manifest_path, "w", encoding="utf-8") as mf:
                            json.dump(m_data, mf, indent=2)

                        # Update CURRICULUM.md tickbox
                        curric_path = os.path.join(self.inst_dir, "CURRICULUM.md")
                        if os.path.isfile(curric_path):
                            with open(curric_path, "r", encoding="utf-8") as cf:
                                c_lines = cf.readlines()
                            new_lines = []
                            clean_id = topic_id.replace("topic.", "")
                            for line in c_lines:
                                if (topic_title and re.search(r"-\s*\[x\]\s*" + re.escape(topic_title), line)) or f"`{clean_id}`" in line or f"`{topic_id}`" in line:
                                    new_lines.append(re.sub(r"-\s*\[x\]", "- [ ]", line, count=1))
                                else:
                                    new_lines.append(line)
                            with open(curric_path, "w", encoding="utf-8") as cf:
                                cf.write("".join(new_lines))

                    except Exception as e:
                        print(f"Error resetting topic {topic_id}: {e}")

            # 2. Advance or Activate Topic
            else:
                advance_script = os.path.join(CURRENT_SCRIPTS_DIR, "advance-cursor.py")
                if os.path.isfile(advance_script):
                    cmd = [sys.executable, advance_script, "--instance-dir", self.inst_dir]
                    if status == "completed":
                        cmd.extend(["--complete-topic", topic_id])
                        if evidence: cmd.extend(["--evidence", evidence])
                        if hypothesis: cmd.extend(["--hypothesis", hypothesis])
                        if discussion: cmd.extend(["--discussion-summary", discussion])
                    elif status == "in_progress":
                        cmd.extend(["--next-topic-id", topic_id])

                    subprocess.run(cmd, check=False)

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_cors()
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "topicId": topic_id, "state": status}).encode("utf-8"))
            return

        elif path == "/api/projects/switch":
            StudioDashboardHandler.pinned_instance = False
            project_id = payload.get("projectId")
            reg = get_live_projects_registry(current_inst_dir=StudioDashboardHandler.inst_dir)
            for p in reg.get("projects", []):
                if p.get("id") == project_id:
                    reg["activeProjectId"] = project_id
                    save_projects_registry(reg)
                    new_inst = resolve_instance_dir(project_id=project_id)
                    if os.path.isdir(new_inst):
                        StudioDashboardHandler.inst_dir = new_inst
                        StudioDashboardHandler.base_dir = os.path.dirname(new_inst) if os.path.basename(new_inst) == ".system-design" else new_inst
                    break

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_cors()
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "activeProjectId": project_id}).encode("utf-8"))
            return

        elif path == "/api/projects/create":
            name = payload.get("name", "New Studio Project")
            custom_path = payload.get("path", "").strip()
            track = payload.get("track", "full-mastery")

            init_script = os.path.join(CURRENT_SCRIPTS_DIR, "init-learning-instance.sh")
            proj_id = re.sub(r"[^a-zA-Z0-9_-]", "-", name.lower()).strip("-")
            
            # Default to isolated ~/.system-design-studio/projects/<slug> if custom path is blank
            if not custom_path:
                target_dir = os.path.join(get_global_studio_dir(), "projects", proj_id)
            else:
                target_dir = os.path.abspath(os.path.expanduser(custom_path))

            cmd = ["bash", init_script, "--name", name, "--id", proj_id, "--track", track, "--path", target_dir, "-y"]
            res = subprocess.run(cmd, capture_output=True, text=True, check=False)

            if res.returncode == 0:
                # Remove from unregisteredPaths if previously deleted
                reg = load_projects_registry()
                unreg = set(reg.get("unregisteredPaths", []))
                norm_target = os.path.abspath(target_dir)
                if norm_target in unreg:
                    unreg.remove(norm_target)
                    reg["unregisteredPaths"] = list(unreg)
                    save_projects_registry(reg)

                # Re-sync live projects
                reg = get_live_projects_registry(current_inst_dir=StudioDashboardHandler.inst_dir)
                reg["activeProjectId"] = proj_id
                save_projects_registry(reg)

                new_inst = resolve_instance_dir(project_id=proj_id)
                if new_inst and os.path.isdir(new_inst):
                    StudioDashboardHandler.inst_dir = new_inst
                    StudioDashboardHandler.base_dir = os.path.dirname(new_inst) if os.path.basename(new_inst) == ".system-design" else new_inst
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_cors()
                self.end_headers()
                self.wfile.write(json.dumps({"status": "created", "projectId": proj_id, "path": target_dir}).encode("utf-8"))
            else:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_cors()
                self.end_headers()
                self.wfile.write(json.dumps({"error": res.stderr or "Initialization failed"}).encode("utf-8"))
            return

        elif path == "/api/projects/delete":
            project_id = payload.get("projectId")
            reg = load_projects_registry()
            before_len = len(reg.get("projects", []))

            # Check if this project is currently served by this handler instance
            was_current = (reg.get("activeProjectId") == project_id)
            deleted_proj = next((p for p in reg.get("projects", []) if p.get("id") == project_id), None)
            if deleted_proj and self.inst_dir:
                d_path = os.path.abspath(os.path.expanduser(deleted_proj.get("projectPath", "")))
                curr_path = os.path.abspath(self.inst_dir)
                if curr_path == d_path or curr_path.startswith(d_path + os.sep) or d_path.startswith(curr_path):
                    was_current = True

            # Record in unregisteredPaths so auto-discovery does not immediately resurrect it
            if deleted_proj and deleted_proj.get("projectPath"):
                del_p = os.path.abspath(os.path.expanduser(deleted_proj.get("projectPath")))
                unreg = set(reg.get("unregisteredPaths", []))
                unreg.add(del_p)
                reg["unregisteredPaths"] = list(unreg)

            reg["projects"] = [p for p in reg.get("projects", []) if p.get("id") != project_id]
            if was_current or reg.get("activeProjectId") == project_id:
                reg["activeProjectId"] = reg["projects"][0]["id"] if reg["projects"] else None

            if len(reg.get("projects", [])) < before_len or "unregisteredPaths" in reg:
                save_projects_registry(reg)

            # Update in-memory handler if the active or current project was deleted
            if was_current and reg.get("activeProjectId"):
                StudioDashboardHandler.pinned_instance = False
                new_active_inst = resolve_instance_dir(project_id=reg["activeProjectId"])
                if new_active_inst and os.path.isdir(new_active_inst):
                    StudioDashboardHandler.inst_dir = new_active_inst
                    StudioDashboardHandler.base_dir = os.path.dirname(new_active_inst) if os.path.basename(new_active_inst) == ".system-design" else new_active_inst

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_cors()
            self.end_headers()
            self.wfile.write(json.dumps({"status": "deleted", "projectId": project_id}).encode("utf-8"))
            return

        elif path == "/api/note":
            rel_path = payload.get("path", "").strip()
            content = payload.get("content", "")
            if not rel_path:
                self.send_response(400)
                self.send_cors()
                self.end_headers()
                self.wfile.write(b"Missing path")
                return

            clean_rel = rel_path.replace("\\", "/")
            if ".." in clean_rel.split("/") or clean_rel.startswith("/") or "\x00" in clean_rel:
                self.send_response(403)
                self.send_cors()
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
            norm_rel = os.path.normpath(clean_rel).lstrip("/")
            target = os.path.abspath(os.path.join(notes_dir, norm_rel))
            abs_notes = os.path.abspath(notes_dir)
            if not (target == abs_notes or target.startswith(abs_notes + os.sep)):
                self.send_response(403)
                self.send_cors()
                self.end_headers()
                self.wfile.write(b"Access denied")
                return

            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "w", encoding="utf-8") as f:
                f.write(content)

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_cors()
            self.end_headers()
            self.wfile.write(json.dumps({"status": "saved", "path": rel_path}).encode("utf-8"))
            return

        elif path in ["/highlights", "/api/highlights"]:
            raw_target = query.get("artifact", ["default"])[0]
            clean_rel = raw_target.replace("\\", "/")
            if ".." in clean_rel.split("/") or clean_rel.startswith("/") or "\x00" in clean_rel:
                self.send_response(403)
                self.send_cors()
                self.end_headers()
                self.wfile.write(b"Access denied")
                return
            existing = load_highlights_data(self.inst_dir, raw_target)
            if isinstance(payload, list):
                for item in payload:
                    existing.append(item)
            elif isinstance(payload, dict) and payload:
                existing.append(payload)

            save_highlights_data(self.inst_dir, raw_target, existing)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_cors()
            self.end_headers()
            self.wfile.write(json.dumps(existing).encode("utf-8"))
            return

        elif path == "/api/settings":
            settings_path = os.path.join(self.inst_dir, "settings.json")
            data = {}
            if os.path.isfile(settings_path):
                try:
                    with open(settings_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except Exception:
                    pass

            for k, v in payload.items():
                data[k] = v

            with open(settings_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            # Also update global config defaults
            global_cfg_path = os.path.join(get_global_studio_dir(), "config.json")
            if os.path.isfile(global_cfg_path):
                try:
                    with open(global_cfg_path, "r", encoding="utf-8") as gf:
                        g_data = json.load(gf)
                    if "artifactStyle" in payload: g_data["artifactStyle"] = payload["artifactStyle"]
                    if "outputType" in payload: g_data["outputType"] = payload["outputType"]
                    with open(global_cfg_path, "w", encoding="utf-8") as gf:
                        json.dump(g_data, gf, indent=2)
                except Exception:
                    pass

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_cors()
            self.end_headers()
            self.wfile.write(json.dumps({"status": "updated"}).encode("utf-8"))
            return

        elif path == "/api/revisions/rate":
            rev_id = payload.get("revisionId")
            status = payload.get("masteryStatus", "proficient")
            revisions_file = os.path.join(self.inst_dir, "revisions.json")
            if os.path.isfile(revisions_file):
                try:
                    with open(revisions_file, "r", encoding="utf-8") as f:
                        r_data = json.load(f)

                    # Anki-Style Spaced Repetition Scheduling
                    interval_days = 1 if status in ["learning", "needs_review"] else (3 if status == "proficient" else 7)
                    today = datetime.date.today()
                    next_dt = today + datetime.timedelta(days=interval_days)

                    for r in r_data.get("revisions", []):
                        if r.get("id") == rev_id or r.get("topicId") == rev_id:
                            r["masteryStatus"] = status
                            r["lastReviewed"] = today.strftime("%Y-%m-%d")
                            r["nextReviewDate"] = next_dt.strftime("%Y-%m-%d")
                            r["reviewCount"] = r.get("reviewCount", 0) + 1
                            r["streak"] = (r.get("streak", 0) + 1) if status == "mastered" else 0
                            r["isDue"] = False
                            break

                    with open(revisions_file, "w", encoding="utf-8") as f:
                        json.dump(r_data, f, indent=2)
                except Exception:
                    pass

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_cors()
            self.end_headers()
            self.wfile.write(json.dumps({"status": "rated", "masteryStatus": status}).encode("utf-8"))
            return

        else:
            self.send_response(404)
            self.send_cors()
            self.end_headers()
            self.wfile.write(b"Not found")

    def do_DELETE(self):
        self.sync_active_instance()
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path in ["/highlights", "/api/highlights"]:
            raw_target = query.get("artifact", ["default"])[0]
            clean_rel = raw_target.replace("\\", "/")
            if ".." in clean_rel.split("/") or clean_rel.startswith("/") or "\x00" in clean_rel:
                self.send_response(403)
                self.send_cors()
                self.end_headers()
                self.wfile.write(b"Access denied")
                return
            hl_id = query.get("id", [None])[0]
            if hl_id:
                existing = load_highlights_data(self.inst_dir, raw_target)
                filtered = [h for h in existing if (h.get("id") if isinstance(h, dict) else None) != hl_id]
                save_highlights_data(self.inst_dir, raw_target, filtered)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_cors()
                self.end_headers()
                self.wfile.write(json.dumps({"status": "deleted", "id": hl_id}).encode("utf-8"))
                return
            for c in get_highlights_candidates(self.inst_dir, raw_target):
                if os.path.isfile(c):
                    try:
                        os.remove(c)
                    except Exception:
                        pass
            save_highlights_data(self.inst_dir, raw_target, [])
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_cors()
            self.end_headers()
            self.wfile.write(json.dumps({"status": "cleared"}).encode("utf-8"))
            return

        self.send_response(404)
        self.send_cors()
        self.end_headers()
        self.wfile.write(b"Not found")

def main():
    parser = argparse.ArgumentParser(description="System Design Studio Localhost Interactive Workbench")
    parser.add_argument("--instance-dir", default=None, help="Path to .system-design directory")
    parser.add_argument("--project-id", default=None, help="Target registered project ID")
    parser.add_argument("--port", type=int, default=None, help="Port to serve dashboard on")
    parser.add_argument("--no-browser", action="store_true", help="Do not open browser automatically")
    parser.add_argument("--network", action="store_true", help="Expose dashboard on local network (binds to 0.0.0.0)")
    args = parser.parse_args()

    inst_dir = resolve_instance_dir(raw_dir=args.instance_dir, project_id=args.project_id)
    if not inst_dir or not os.path.isdir(inst_dir):
        print("[!] Error: No valid System Design Studio learning instance found.")
        print("Run 'sds init' in your project root or pass '--instance-dir <path>'.")
        sys.exit(1)

    base_dir = os.path.dirname(inst_dir) if os.path.basename(inst_dir) == ".system-design" else inst_dir
    port = args.port or find_available_port(DEFAULT_PORT)

    StudioDashboardHandler.inst_dir = inst_dir
    StudioDashboardHandler.base_dir = base_dir
    StudioDashboardHandler.pinned_instance = bool(args.instance_dir or args.project_id)

    host = "0.0.0.0" if args.network else "127.0.0.1"
    server = StudioHTTPServer((host, port), StudioDashboardHandler)
    server.daemon_threads = True
    url = f"http://127.0.0.1:{port}"

    print(f"[*] System Design Studio Dashboard active at: {url}")
    if args.network:
        lan_ip = get_local_network_ip()
        network_url = f"http://{lan_ip}:{port}"
        print(f"[+] Network access:                           {network_url}")
    print(f"[-] Instance Directory: {inst_dir}")
    print(f"[-] Workspace Directory: {base_dir}")
    print("Press Ctrl+C to stop.")

    if not args.no_browser:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping dashboard server...")
        server.server_close()

if __name__ == "__main__":
    main()
