#!/usr/bin/env python3
"""
manage-projects.py
Central Multi-Project Registry Manager for System Design Studio.
Manages ~/.system-design-studio/projects.json, supporting default projects
(~/.system-design-studio/projects/<name>) and custom workspaces across disk,
with project-scoped notes tracking and convenient navigation.
"""

import os
import sys
import json
import argparse
import datetime

def get_home_dir():
    home = os.environ.get("HOME") or os.environ.get("USERPROFILE")
    if not home:
        home = os.path.expanduser("~")
    return home

def get_global_studio_dir():
    home = get_home_dir()
    studio_dir = os.environ.get("SDS_GLOBAL_DIR") or os.path.join(home, ".system-design-studio")
    return studio_dir

def get_projects_registry_path():
    return os.path.join(get_global_studio_dir(), "projects.json")

def get_global_config_path():
    return os.path.join(get_global_studio_dir(), "config.json")

def load_registry():
    reg_path = get_projects_registry_path()
    if not os.path.exists(reg_path):
        return {"$schemaVersion": "3.2", "activeProjectId": None, "projects": []}
    try:
        with open(reg_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"$schemaVersion": "3.2", "activeProjectId": None, "projects": []}

def save_registry(data):
    reg_path = get_projects_registry_path()
    os.makedirs(os.path.dirname(reg_path), exist_ok=True)
    temp_path = f"{reg_path}.tmp.{os.getpid()}"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(temp_path, reg_path)

def resolve_project_progress(project_path):
    manifest_path = os.path.join(project_path, ".system-design", "manifest.json")
    if not os.path.exists(manifest_path):
        return {"completed": 0, "total": 0, "activeTopicId": "none", "activeClusterId": "none"}
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            m = json.load(f)
        curriculum = m.get("curriculum", {})
        clusters = curriculum.get("clusters", [])
        total = sum(len(c.get("topics", [])) for c in clusters)
        completed = sum(1 for c in clusters for t in c.get("topics", []) if t.get("status") == "completed")
        active_topic_id = curriculum.get("activeTopicId", "none")
        active_cluster_id = curriculum.get("activeClusterId", "none")
        return {
            "completed": completed,
            "total": total,
            "activeTopicId": active_topic_id,
            "activeClusterId": active_cluster_id
        }
    except Exception:
        return {"completed": 0, "total": 0, "activeTopicId": "none", "activeClusterId": "none"}

def cmd_list(args):
    reg = load_registry()
    projects = reg.get("projects", [])
    active_id = reg.get("activeProjectId")

    if args.json:
        # Refresh progress on the fly
        for p in projects:
            p["progress"] = resolve_project_progress(p.get("projectPath", ""))
        print(json.dumps(reg, indent=2))
        return

    if not projects:
        print("📁 No System Design Studio projects registered yet.")
        print("   Initialize your first project with: init-learning-instance.sh")
        return

    print("=" * 86)
    print("  SYSTEM DESIGN STUDIO — REGISTERED PROJECTS")
    print("=" * 86)
    print(f"{'ACTIVE':<8} {'ID':<30} {'TRACK':<22} {'PROGRESS':<12} {'LOCATION':<10}")
    print("-" * 86)

    for p in projects:
        is_active = "*" if p.get("id") == active_id else " "
        raw_pid = p.get("id", "unknown")
        pid = (raw_pid[:28] + "…") if len(raw_pid) > 29 else raw_pid
        raw_track = p.get("track", "full-mastery")
        track = (raw_track[:20] + "…") if len(raw_track) > 21 else raw_track
        prog = resolve_project_progress(p.get("projectPath", ""))
        prog_str = f"{prog['completed']}/{prog['total']}"
        loc_type = p.get("locationType", "custom")

        print(f"  {is_active:<6} {pid:<30} {track:<22} {prog_str:<12} {loc_type:<10}")
        print(f"         Path:  {p.get('projectPath')}")
        print(f"         Notes: {p.get('notesDir')} ({p.get('notesStructure', 'per-topic')})")
        print("-" * 86)

def cmd_register(args):
    reg = load_registry()
    projects = reg.get("projects", [])
    
    project_path = os.path.abspath(os.path.expanduser(args.path))
    notes_dir = os.path.abspath(os.path.expanduser(args.notes_dir)) if args.notes_dir else os.path.join(project_path, "notes")
    
    # Check if default path
    studio_dir = get_global_studio_dir()
    default_projects_dir = os.path.join(studio_dir, "projects")
    location_type = "default" if project_path.startswith(default_projects_dir) else "custom"

    existing = next((p for p in projects if p.get("id") == args.id or p.get("projectPath") == project_path), None)
    
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    project_entry = {
        "id": args.id,
        "name": args.name or args.id,
        "locationType": location_type,
        "projectPath": project_path,
        "track": args.track or "full-mastery",
        "notesDir": notes_dir,
        "notesStructure": args.notes_structure or "per-topic",
        "lastActive": now_iso
    }

    if existing:
        existing.update(project_entry)
        print(f"✅ Updated existing project entry for '{args.id}'")
    else:
        project_entry["createdAt"] = now_iso
        projects.append(project_entry)
        print(f"✅ Registered new project '{args.id}' in projects registry")

    reg["projects"] = projects
    if not reg.get("activeProjectId") or args.set_active:
        reg["activeProjectId"] = args.id

    save_registry(reg)

def cmd_unregister(args):
    reg = load_registry()
    projects = reg.get("projects", [])
    before_count = len(projects)
    projects = [p for p in projects if p.get("id") != args.id]
    
    if len(projects) == before_count:
        print(f"⚠️ Project '{args.id}' not found in registry.")
        return

    reg["projects"] = projects
    if reg.get("activeProjectId") == args.id:
        reg["activeProjectId"] = projects[0]["id"] if projects else None

    save_registry(reg)
    print(f"✅ Project '{args.id}' removed from registry (files on disk preserved).")

def cmd_delete(args):
    reg = load_registry()
    projects = reg.get("projects", [])
    target = next((p for p in projects if p.get("id") == args.id or p.get("name") == args.id), None)

    if not target:
        resolved_path = os.path.abspath(os.path.expanduser(args.id))
        target = next((p for p in projects if os.path.abspath(p.get("projectPath", "")) == resolved_path), None)

    if not target:
        print(f"❌ Error: Project '{args.id}' not found in registry.", file=sys.stderr)
        print("   Use 'manage-projects.py list' to view registered projects.", file=sys.stderr)
        sys.exit(1)

    project_id = target.get("id")
    project_path = target.get("projectPath")
    notes_dir = target.get("notesDir")
    studio_dir = get_global_studio_dir()
    default_projects_dir = os.path.join(studio_dir, "projects")

    dot_sds_dir = os.path.join(project_path, ".system-design") if project_path else None

    is_default_location = (
        project_path and
        os.path.abspath(project_path).startswith(os.path.abspath(default_projects_dir)) and
        os.path.abspath(project_path) != os.path.abspath(default_projects_dir)
    )

    home_dir = os.path.abspath(get_home_dir())
    is_home_or_root = (
        not project_path or
        os.path.abspath(project_path) == home_dir or
        os.path.abspath(project_path) == "/"
    )

    will_delete_entire_dir = is_default_location and not is_home_or_root and (args.purge or not args.keep_project_dir)
    will_delete_notes = args.delete_notes and notes_dir and os.path.exists(notes_dir) and os.path.abspath(notes_dir) != home_dir and os.path.abspath(notes_dir) != "/"

    if args.dry_run:
        print("=" * 76)
        print(f"🔍 DRY RUN — DELETE PROJECT: {project_id}")
        print("=" * 76)
        print(f"   Registry Entry:   Will remove from {get_projects_registry_path()}")
        if dot_sds_dir and os.path.exists(dot_sds_dir):
            print(f"   Learning State:   Will remove {dot_sds_dir}")
        if will_delete_entire_dir:
            print(f"   Project Folder:   Will remove default project dir: {project_path}")
        else:
            print(f"   Workspace Folder: PRESERVED ({project_path})")
        if will_delete_notes:
            print(f"   Study Notes:      Will remove notes dir: {notes_dir}")
        else:
            print(f"   Study Notes:      PRESERVED ({notes_dir})")
        return

    if not args.force:
        print(f"⚠️  Are you sure you want to delete project '{project_id}'?")
        print(f"   • Location: {project_path}")
        if will_delete_entire_dir:
            print(f"   • Action:   Entire default project folder will be removed ({project_path})")
        else:
            print(f"   • Action:   Learning state ({dot_sds_dir}) will be removed; workspace source files kept.")
        if will_delete_notes:
            print(f"   • Notes:    Study notes directory ({notes_dir}) will be DELETED.")
        else:
            print(f"   • Notes:    Study notes ({notes_dir}) will be KEPT.")

        try:
            confirm = input("Type 'yes' or project name to confirm deletion: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAction cancelled.")
            return

        if confirm.lower() != "yes" and confirm != project_id:
            print("Action cancelled. No files or registry entries were changed.")
            return

    import shutil
    deleted_items = []

    if will_delete_entire_dir and os.path.exists(project_path):
        shutil.rmtree(project_path)
        deleted_items.append(f"Project directory ({project_path})")
    elif dot_sds_dir and os.path.exists(dot_sds_dir):
        shutil.rmtree(dot_sds_dir)
        deleted_items.append(f"Instance state ({dot_sds_dir})")

    if will_delete_notes and os.path.exists(notes_dir):
        shutil.rmtree(notes_dir)
        deleted_items.append(f"Notes directory ({notes_dir})")

    projects = [p for p in projects if p.get("id") != project_id]
    reg["projects"] = projects
    if reg.get("activeProjectId") == project_id:
        reg["activeProjectId"] = projects[0]["id"] if projects else None
        if reg["activeProjectId"]:
            print(f"🔄 Active project switched to '{reg['activeProjectId']}'")
        else:
            print("ℹ️  No other registered projects remaining.")

    save_registry(reg)

    print("=" * 76)
    print(f"✅ Successfully deleted project '{project_id}'!")
    for item in deleted_items:
        print(f"   • Removed: {item}")
    if not will_delete_notes and notes_dir and os.path.exists(notes_dir):
        print(f"   • Kept notes at: {notes_dir}")
    if not will_delete_entire_dir and project_path and os.path.exists(project_path):
        print(f"   • Kept workspace at: {project_path}")
    print("=" * 76)

def cmd_switch(args):
    reg = load_registry()
    projects = reg.get("projects", [])
    target = next((p for p in projects if p.get("id") == args.id or p.get("name") == args.id), None)
    
    if not target:
        print(f"❌ Error: Project '{args.id}' not found in registry.", file=sys.stderr)
        sys.exit(1)

    target["lastActive"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    reg["activeProjectId"] = target["id"]
    save_registry(reg)
    print(f"✅ Switched active project to '{target['id']}' ({target['projectPath']})")

def cmd_active(args):
    reg = load_registry()
    active_id = reg.get("activeProjectId")
    projects = reg.get("projects", [])
    active_proj = next((p for p in projects if p.get("id") == active_id), None)

    if not active_proj:
        if args.json:
            print(json.dumps({"activeProject": None}))
        else:
            print("No active project currently set.")
        return

    prog = resolve_project_progress(active_proj.get("projectPath", ""))
    active_proj["progress"] = prog

    if args.json:
        print(json.dumps(active_proj, indent=2))
    else:
        print(f"Active Project: {active_proj['id']} ({active_proj.get('name')})")
        print(f"Path:           {active_proj['projectPath']}")
        print(f"Track:          {active_proj['track']}")
        print(f"Notes:          {active_proj['notesDir']} ({active_proj.get('notesStructure', 'per-topic')})")
        print(f"Progress:       {prog['completed']}/{prog['total']} topics completed")

def cmd_notes(args):
    reg = load_registry()
    projects = reg.get("projects", [])
    target_id = args.id or reg.get("activeProjectId")
    target_proj = next((p for p in projects if p.get("id") == target_id), None)

    # Fallback to current directory if not found in registry
    if not target_proj and os.path.exists(".system-design/settings.json"):
        with open(".system-design/settings.json") as sf:
            s = json.load(sf)
        target_proj = {
            "id": s.get("projectId", "local"),
            "name": s.get("projectName", "Local Project"),
            "projectPath": os.getcwd(),
            "notesDir": s.get("paths", {}).get("notesDir", "notes"),
            "notesStructure": s.get("notesStructure", "per-topic")
        }

    if not target_proj:
        print(f"❌ Error: No registered or local project found.", file=sys.stderr)
        sys.exit(1)

    notes_dir = target_proj.get("notesDir", "notes")
    if not os.path.isabs(notes_dir):
        notes_dir = os.path.normpath(os.path.join(target_proj.get("projectPath", os.getcwd()), notes_dir))

    print("=" * 76)
    print(f"📝 STUDY NOTES FOR PROJECT: {target_proj.get('name')} ({target_proj.get('id')})")
    print(f"   Directory: {notes_dir}")
    print(f"   Structure: {target_proj.get('notesStructure', 'per-topic')}")
    print("=" * 76)

    if not os.path.exists(notes_dir):
        print(f"   (No notes directory found at {notes_dir}. Notes will be generated as topics complete).")
        return

    note_files = []
    for root, _, files in os.walk(notes_dir):
        for f in files:
            if f.endswith(".md"):
                rel_path = os.path.relpath(os.path.join(root, f), notes_dir)
                abs_path = os.path.join(root, f)
                note_files.append((rel_path, abs_path))

    if not note_files:
        print("   No study notes generated yet. Topics sign-off will automatically synthesize notes here.")
        return

    for rel, abs_p in sorted(note_files):
        print(f"   • {rel}  ➔  file://{abs_p}")

def cmd_rollback(args):
    import subprocess
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cp_script = os.path.join(script_dir, "git-checkpoint.py")
    if not os.path.exists(cp_script):
        print("❌ Error: git-checkpoint.py not found.", file=sys.stderr)
        sys.exit(1)
    cmd = [sys.executable, cp_script, "rollback"]
    if getattr(args, "target_id", None):
        cmd.extend(["--id", args.target_id])
    if getattr(args, "steps", None):
        cmd.extend(["--steps", str(args.steps)])
    if getattr(args, "dry_run", False):
        cmd.append("--dry-run")
    if getattr(args, "instance_dir", None):
        cmd.extend(["--instance-dir", args.instance_dir])
    subprocess.run(cmd)

def cmd_dashboard(args):
    import subprocess
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dash_script = os.path.join(script_dir, "serve-dashboard.py")
    if not os.path.exists(dash_script):
        print("❌ Error: serve-dashboard.py not found.", file=sys.stderr)
        sys.exit(1)
    cmd = [sys.executable, dash_script]
    if getattr(args, "port", None):
        cmd.extend(["--port", str(args.port)])
    if getattr(args, "project", None):
        cmd.extend(["--project", args.project])
    if getattr(args, "instance_dir", None):
        cmd.extend(["--instance-dir", args.instance_dir])
    if getattr(args, "no_browser", False):
        cmd.append("--no-browser")
    subprocess.run(cmd)

def main():
    parser = argparse.ArgumentParser(description="Manage System Design Studio multi-project registry")
    subparsers = parser.add_subparsers(dest="command")

    # list
    p_list = subparsers.add_parser("list", help="List all registered projects")
    p_list.add_argument("--json", action="store_true", help="Output as JSON")

    # register
    p_reg = subparsers.add_parser("register", help="Register a project")
    p_reg.add_argument("--id", required=True, help="Project unique identifier")
    p_reg.add_argument("--name", help="Display name")
    p_reg.add_argument("--path", required=True, help="Project filesystem path")
    p_reg.add_argument("--track", default="full-mastery", help="Curriculum track")
    p_reg.add_argument("--notes-dir", help="Project notes directory path")
    p_reg.add_argument("--notes-structure", default="per-topic", choices=["per-topic", "per-cluster", "per-tier", "single-file"], help="Notes structuring strategy")
    p_reg.add_argument("--set-active", action="store_true", help="Set this project as active")

    # unregister
    p_unreg = subparsers.add_parser("unregister", help="Unregister a project")
    p_unreg.add_argument("id", help="Project identifier")

    # switch
    p_switch = subparsers.add_parser("switch", help="Switch active project")
    p_switch.add_argument("id", help="Project identifier or name")

    # active
    p_act = subparsers.add_parser("active", help="Show active project")
    p_act.add_argument("--json", action="store_true", help="Output as JSON")

    # notes
    p_notes = subparsers.add_parser("notes", help="List notes for a project")
    p_notes.add_argument("id", nargs="?", help="Project identifier (defaults to active)")

    # delete
    p_del = subparsers.add_parser("delete", aliases=["rm", "remove"], help="Safely delete a project learning instance")
    p_del.add_argument("id", help="Project identifier, display name, or path")
    p_del.add_argument("-f", "--force", action="store_true", help="Skip confirmation prompt")
    p_del.add_argument("--delete-notes", action="store_true", help="Also delete the generated study notes directory")
    p_del.add_argument("--purge", action="store_true", help="Purge entire project folder if default location")
    p_del.add_argument("--keep-project-dir", action="store_true", help="Keep project folder even if default location")
    p_del.add_argument("--dry-run", action="store_true", help="Show what would be removed without touching disk")

    # rollback
    p_roll = subparsers.add_parser("rollback", aliases=["restore", "undo"], help="Roll back state to a previous checkpoint")
    p_roll.add_argument("--id", dest="target_id", help="Target checkpoint ID")
    p_roll.add_argument("--steps", type=int, default=1, help="Number of checkpoints to roll back (default 1)")
    p_roll.add_argument("--dry-run", action="store_true", help="Preview rollback without modifying files")
    p_roll.add_argument("--instance-dir", help="Target .system-design directory")

    # dashboard
    p_dash = subparsers.add_parser("dashboard", aliases=["serve", "tracker"], help="Launch localhost curriculum tracker")
    p_dash.add_argument("--port", type=int, default=8420, help="HTTP port (default 8420)")
    p_dash.add_argument("--project", help="Target project ID")
    p_dash.add_argument("--instance-dir", help="Target .system-design directory")
    p_dash.add_argument("--no-browser", action="store_true", help="Do not open browser automatically")

    args = parser.parse_args()
    if args.command == "list" or not args.command:
        cmd_list(args if args.command else argparse.Namespace(json=False))
    elif args.command == "register":
        cmd_register(args)
    elif args.command == "unregister":
        cmd_unregister(args)
    elif args.command in ("delete", "rm", "remove"):
        cmd_delete(args)
    elif args.command == "switch":
        cmd_switch(args)
    elif args.command == "active":
        cmd_active(args)
    elif args.command == "notes":
        cmd_notes(args)
    elif args.command in ("rollback", "restore", "undo"):
        cmd_rollback(args)
    elif args.command in ("dashboard", "serve", "tracker"):
        cmd_dashboard(args)

if __name__ == "__main__":
    main()
