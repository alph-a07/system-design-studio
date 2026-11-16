#!/usr/bin/env python3
"""
git-checkpoint.py
Atomic Git Checkpoint, History Tracking, and Reversible Rollback Engine for System Design Studio.
Provides:
1. Tractable, structured commit messages:
   - sds(learn): complete <topic-id> - <topic-title> [verified]
   - sds(adr): record <adr-id> - <topic-title>
   - sds(curriculum): mutate track '<name>' (<N> clusters, <M> topics)
   - sds(notes): generate active-learning notes for <topic-title>
   - sds(config): update <key> to <value>
   - sds(rollback): revert state to <checkpoint-id>
2. Local backup snapshots in .system-design/.checkpoints/ for 100% safety even outside Git.
3. Clean rollback and restore command with --dry-run and step selection.
"""

import os
import sys
import json
import shutil
import argparse
import datetime
import subprocess

MAX_LOCAL_CHECKPOINTS = 30

def is_git_repo(directory):
    try:
        res = subprocess.run(
            ["git", "-C", directory, "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            check=False
        )
        return res.returncode == 0 and res.stdout.strip() == "true"
    except Exception:
        return False

def get_git_status_summary(directory):
    if not is_git_repo(directory):
        return {"is_git": False}
    try:
        branch_res = subprocess.run(
            ["git", "-C", directory, "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=False
        )
        branch = branch_res.stdout.strip() or "HEAD"

        commit_res = subprocess.run(
            ["git", "-C", directory, "log", "-1", "--format=%h %s"],
            capture_output=True,
            text=True,
            check=False
        )
        last_commit = commit_res.stdout.strip() or "none"

        status_res = subprocess.run(
            ["git", "-C", directory, "status", "--porcelain", ".system-design"],
            capture_output=True,
            text=True,
            check=False
        )
        dirty = bool(status_res.stdout.strip())

        return {
            "is_git": True,
            "branch": branch,
            "last_commit": last_commit,
            "dirty": dirty
        }
    except Exception as e:
        return {"is_git": True, "error": str(e)}

def create_local_snapshot(inst_dir, action_type, description):
    checkpoints_dir = os.path.join(inst_dir, ".checkpoints")
    os.makedirs(checkpoints_dir, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_desc = "".join(c if c.isalnum() or c in "-_" else "_" for c in description)[:30]
    snap_id = f"{timestamp}_{action_type}_{clean_desc}"
    snap_dir = os.path.join(checkpoints_dir, snap_id)
    os.makedirs(snap_dir, exist_ok=True)

    # Files to snapshot
    core_files = ["manifest.json", "CURSOR.md", "CURRICULUM.md", "DECISIONS.md", "settings.json"]
    copied = []
    for f in core_files:
        src = os.path.join(inst_dir, f)
        if os.path.isfile(src):
            shutil.copy2(src, os.path.join(snap_dir, f))
            copied.append(f)

    meta = {
        "id": snap_id,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "actionType": action_type,
        "description": description,
        "files": copied
    }
    with open(os.path.join(snap_dir, "meta.json"), "w", encoding="utf-8") as mf:
        json.dump(meta, mf, indent=2)

    # Prune oldest if exceeding MAX_LOCAL_CHECKPOINTS
    existing = sorted([d for d in os.listdir(checkpoints_dir) if os.path.isdir(os.path.join(checkpoints_dir, d))])
    if len(existing) > MAX_LOCAL_CHECKPOINTS:
        for old in existing[:-MAX_LOCAL_CHECKPOINTS]:
            shutil.rmtree(os.path.join(checkpoints_dir, old), ignore_errors=True)

    return snap_id

def commit_git_checkpoint(inst_dir, action_type, subject, additional_files=None):
    """
    Creates local snapshot and atomic Git commit if inside a Git repository.
    """
    abs_inst = os.path.abspath(inst_dir)
    repo_root = os.path.dirname(abs_inst) if os.path.basename(abs_inst) == ".system-design" else abs_inst

    # Always create local snapshot
    snap_id = create_local_snapshot(abs_inst, action_type, subject)

    if not is_git_repo(repo_root):
        print(f"📦 Local snapshot created: {snap_id} (Git repository not detected)")
        return {"snapshot_id": snap_id, "git_committed": False}

    # Format tractable commit message
    commit_msg = f"sds({action_type}): {subject}"

    try:
        # Check if git user is configured
        user_check = subprocess.run(
            ["git", "-C", repo_root, "config", "user.name"],
            capture_output=True,
            text=True,
            check=False
        )
        if not user_check.stdout.strip():
            # Set local fallback author if not configured
            subprocess.run(["git", "-C", repo_root, "config", "--local", "user.name", "System Design Studio"], check=False)
            subprocess.run(["git", "-C", repo_root, "config", "--local", "user.email", "studio@systemdesign.local"], check=False)

        # Stage .system-design files (excluding .checkpoints)
        files_to_stage = [
            os.path.join(abs_inst, "manifest.json"),
            os.path.join(abs_inst, "CURSOR.md"),
            os.path.join(abs_inst, "CURRICULUM.md"),
            os.path.join(abs_inst, "DECISIONS.md"),
            os.path.join(abs_inst, "settings.json")
        ]
        if additional_files:
            for af in additional_files:
                if af and os.path.exists(af):
                    files_to_stage.append(af)

        existing_stage = [f for f in files_to_stage if os.path.exists(f)]
        if existing_stage:
            subprocess.run(["git", "-C", repo_root, "add"] + existing_stage, check=False)

        # Check if staged changes exist
        diff_res = subprocess.run(
            ["git", "-C", repo_root, "diff", "--cached", "--quiet"],
            check=False
        )
        if diff_res.returncode != 0:
            # Changes are staged, commit
            c_res = subprocess.run(
                ["git", "-C", repo_root, "commit", "-m", commit_msg],
                capture_output=True,
                text=True,
                check=False
            )
            if c_res.returncode == 0:
                print(f"🔒 Git commit recorded: '{commit_msg}'")
                return {"snapshot_id": snap_id, "git_committed": True, "commit_msg": commit_msg}
            else:
                print(f"⚠️ Git commit warning: {c_res.stderr.strip() or c_res.stdout.strip()}")
        else:
            print("ℹ️ No state changes to commit to Git.")

    except Exception as e:
        print(f"⚠️ Git commit exception: {e}")

    return {"snapshot_id": snap_id, "git_committed": False}

def list_checkpoints(inst_dir):
    abs_inst = os.path.abspath(inst_dir)
    checkpoints_dir = os.path.join(abs_inst, ".checkpoints")
    results = []

    if os.path.isdir(checkpoints_dir):
        for snap_name in sorted(os.listdir(checkpoints_dir), reverse=True):
            snap_path = os.path.join(checkpoints_dir, snap_name)
            meta_file = os.path.join(snap_path, "meta.json")
            if os.path.isfile(meta_file):
                try:
                    with open(meta_file, "r", encoding="utf-8") as mf:
                        meta = json.load(mf)
                        results.append(meta)
                except Exception:
                    pass

    return results

def rollback_checkpoint(inst_dir, steps=1, target_id=None, dry_run=False):
    abs_inst = os.path.abspath(inst_dir)
    checkpoints = list_checkpoints(abs_inst)

    if not checkpoints:
        print("❌ Error: No local checkpoints found in .system-design/.checkpoints/", file=sys.stderr)
        return False

    selected = None
    if target_id:
        for c in checkpoints:
            if c["id"] == target_id or target_id in c["id"]:
                selected = c
                break
        if not selected:
            print(f"❌ Error: Checkpoint '{target_id}' not found.", file=sys.stderr)
            return False
    else:
        idx = min(steps, len(checkpoints) - 1)
        selected = checkpoints[idx]

    snap_dir = os.path.join(abs_inst, ".checkpoints", selected["id"])
    print("=" * 72)
    print("  SYSTEM DESIGN STUDIO — RESTORE & ROLLBACK CHECKPOINT")
    print("=" * 72)
    print(f"🎯 Target Checkpoint: {selected['id']}")
    print(f"   Date:        {selected.get('timestamp')}")
    print(f"   Action:      {selected.get('actionType')}")
    print(f"   Description: {selected.get('description')}")
    print(f"   Files:       {', '.join(selected.get('files', []))}")
    print("-" * 72)

    if dry_run:
        print("🔍 [DRY RUN]: No changes written to disk.")
        return True

    # Backup current state before restoring
    pre_rollback_snap = create_local_snapshot(abs_inst, "pre-rollback", f"Backup prior to reverting to {selected['id']}")

    # Restore files
    for fname in selected.get("files", []):
        src = os.path.join(snap_dir, fname)
        dst = os.path.join(abs_inst, fname)
        if os.path.isfile(src):
            shutil.copy2(src, dst)
            print(f"   • Restored: {fname}")

    print(f"✅ Successfully restored state to checkpoint: {selected['id']}")
    print(f"   (Safety snapshot created: {pre_rollback_snap})")

    # If in git repo, record atomic rollback commit
    repo_root = os.path.dirname(abs_inst) if os.path.basename(abs_inst) == ".system-design" else abs_inst
    if is_git_repo(repo_root):
        msg = f"revert state to {selected['id']} ({selected.get('description', '')})"
        commit_git_checkpoint(abs_inst, "rollback", msg)

    return True

def main():
    parser = argparse.ArgumentParser(description="Git checkpoint and state rollback engine for System Design Studio")
    subparsers = parser.add_subparsers(dest="subcommand", help="Action to perform")

    # commit subcommand
    c_p = subparsers.add_parser("commit", help="Create an atomic checkpoint and Git commit")
    c_p.add_argument("--instance-dir", default=".system-design", help="Path to .system-design directory")
    c_p.add_argument("--type", required=True, choices=["learn", "adr", "curriculum", "notes", "config", "rollback"], help="Action type")
    c_p.add_argument("--subject", required=True, help="Tractable commit message subject")
    c_p.add_argument("--files", nargs="*", default=[], help="Additional files to include in commit")

    # list subcommand
    l_p = subparsers.add_parser("list", help="List available checkpoints")
    l_p.add_argument("--instance-dir", default=".system-design", help="Path to .system-design directory")

    # rollback subcommand
    r_p = subparsers.add_parser("rollback", help="Roll back state to a previous checkpoint")
    r_p.add_argument("--instance-dir", default=".system-design", help="Path to .system-design directory")
    r_p.add_argument("--steps", type=int, default=1, help="Number of checkpoints to roll back (default 1)")
    r_p.add_argument("--id", dest="target_id", help="Specific checkpoint ID to restore")
    r_p.add_argument("--dry-run", action="store_true", help="Preview rollback without modifying files")

    # status subcommand
    s_p = subparsers.add_parser("status", help="Get git and checkpoint status")
    s_p.add_argument("--instance-dir", default=".system-design", help="Path to .system-design directory")

    args = parser.parse_args()

    if not args.subcommand:
        parser.print_help()
        sys.exit(0)

    if args.subcommand == "commit":
        commit_git_checkpoint(args.instance_dir, args.type, args.subject, args.files)
    elif args.subcommand == "list":
        cps = list_checkpoints(args.instance_dir)
        print("=" * 76)
        print("  SYSTEM DESIGN STUDIO — STATE CHECKPOINTS & AUDIT TRAIL")
        print("=" * 76)
        if not cps:
            print("  (No checkpoints recorded yet)")
        for i, c in enumerate(cps):
            print(f"[{i:02d}] {c['id']}")
            print(f"     Time:   {c.get('timestamp')}")
            print(f"     Action: sds({c.get('actionType', 'state')})")
            print(f"     Desc:   {c.get('description')}")
            print("-" * 76)
    elif args.subcommand == "rollback":
        rollback_checkpoint(args.instance_dir, args.steps, args.target_id, args.dry_run)
    elif args.subcommand == "status":
        info = get_git_status_summary(args.instance_dir)
        print(json.dumps(info, indent=2))

if __name__ == "__main__":
    main()
