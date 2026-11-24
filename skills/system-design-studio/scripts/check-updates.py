#!/usr/bin/env python3
"""
check-updates.py
Checks for available updates to System Design Studio against the remote GitHub repository.
Uses raw plugin.json to avoid GitHub API rate limits.
Caches check results for 12 hours to prevent redundant network requests.
"""

import os
import sys
import json
import time
import argparse
import urllib.request
import re

REMOTE_PLUGIN_URL = "https://raw.githubusercontent.com/alph-a07/system-design-studio/main/plugin.json"
CACHE_TTL_SECONDS = 12 * 3600  # 12 hours

def parse_semver(v_str):
    """Parses a version string into a tuple of ints (major, minor, patch)."""
    clean = re.sub(r"^[^\d]*", "", str(v_str).strip())
    parts = []
    for piece in clean.split("."):
        m = re.match(r"^(\d+)", piece)
        parts.append(int(m.group(1)) if m else 0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])

def get_local_version(script_dir):
    """Resolves local version by scanning candidate files and returning the highest valid semver found."""
    candidates = [
        os.path.join(script_dir, "..", "SKILL.md"),
        os.path.join(script_dir, "SKILL.md"),
        os.path.join(script_dir, "..", "..", "SKILL.md"),
        os.path.join(script_dir, "..", "..", "..", "plugin.json"),
        os.path.join(os.path.expanduser("~"), ".system-design-studio", "plugin.json"),
        os.path.join(os.path.expanduser("~"), ".system-design-studio", "skills", "system-design-studio", "SKILL.md"),
    ]

    found_versions = []
    for p in candidates:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    content = f.read()
                if p.endswith(".json"):
                    data = json.loads(content)
                    if "version" in data and data["version"]:
                        found_versions.append(str(data["version"]).strip())
                elif "version:" in content:
                    m = re.search(r"version:\s*[\"']?([0-9\.]+)[\"']?", content)
                    if m:
                        found_versions.append(m.group(1).strip())
            except Exception:
                pass

    if found_versions:
        # Sort by semver tuple and return the maximum detected version
        found_versions.sort(key=lambda v: parse_semver(v), reverse=True)
        return found_versions[0]

    return "4.2.1"

def get_cache_path(instance_dir=None):
    if instance_dir and os.path.isdir(instance_dir):
        return os.path.join(instance_dir, ".update-check.json")
    home = os.path.expanduser("~")
    return os.path.join(home, ".system-design-studio-update.json")

def check_for_updates(force=False, instance_dir=".system-design"):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    current_version = get_local_version(script_dir)
    cache_path = get_cache_path(instance_dir)

    now = time.time()
    if not force and os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as cf:
                cache = json.load(cf)
            if now - cache.get("timestamp", 0) < CACHE_TTL_SECONDS:
                cached_res = cache.get("result", {})
                cached_remote = cached_res.get("remoteVersion")
                curr_tuple = parse_semver(current_version)
                remote_tuple = parse_semver(cached_remote) if cached_remote else curr_tuple
                update_available = remote_tuple > curr_tuple
                live_res = {
                    "status": cached_res.get("status", "ok"),
                    "currentVersion": current_version,
                    "remoteVersion": cached_remote,
                    "updateAvailable": update_available
                }
                return live_res
        except Exception:
            pass

    # Query remote
    remote_version = None
    try:
        req = urllib.request.Request(
            REMOTE_PLUGIN_URL,
            headers={"User-Agent": "SystemDesignStudio-UpdateCheck"}
        )
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            remote_version = data.get("version")
    except Exception as e:
        result = {
            "status": "offline_or_error",
            "currentVersion": current_version,
            "remoteVersion": None,
            "updateAvailable": False,
            "error": str(e)
        }
        return result

    curr_tuple = parse_semver(current_version)
    remote_tuple = parse_semver(remote_version) if remote_version else curr_tuple
    update_available = remote_tuple > curr_tuple

    result = {
        "status": "ok",
        "currentVersion": current_version,
        "remoteVersion": remote_version,
        "updateAvailable": update_available
    }

    try:
        with open(cache_path, "w") as cf:
            json.dump({"timestamp": now, "result": result}, cf)
    except Exception:
        pass

    return result

def main():
    parser = argparse.ArgumentParser(description="Check for System Design Studio updates.")
    parser.add_argument("--force", action="store_true", help="Bypass cached check")
    parser.add_argument("--instance-dir", default=".system-design", help="Instance directory")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    parser.add_argument("--prompt", action="store_true", help="Output user-facing prompt alert if update available")

    args = parser.parse_args()
    res = check_for_updates(force=args.force, instance_dir=args.instance_dir)

    if args.json:
        print(json.dumps(res, indent=2))
        return

    curr = res.get("currentVersion", "unknown")
    remote = res.get("remoteVersion")

    if res.get("updateAvailable"):
        if args.prompt:
            print(f"""
🔔 **System Design Studio Update Available!**
A newer version (`v{remote}`) is available (you are currently on `v{curr}`).
To update while safely preserving all your progress, notes, and custom settings:
```bash
curl -fsSL https://raw.githubusercontent.com/alph-a07/system-design-studio/main/update.sh | bash
```
""")
        else:
            print(f"🔔 Update available: v{remote} (current: v{curr})")
            print("   Run: curl -fsSL https://raw.githubusercontent.com/alph-a07/system-design-studio/main/update.sh | bash")
    else:
        if not args.prompt:
            if res.get("status") == "ok":
                print(f"✅ System Design Studio is up to date (v{curr}).")
            else:
                print(f"ℹ️ System Design Studio (v{curr}) — update check skipped ({res.get('error', 'offline')}).")

if __name__ == "__main__":
    main()
