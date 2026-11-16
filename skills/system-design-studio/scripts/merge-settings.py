#!/usr/bin/env python3
"""
merge-settings.py
Deep-merges user settings.json with the latest settings-template.json.
Guarantees that user preferences (such as chosen artifactStyle, custom themes,
and directory save preferences for cursor, lessons, and instance updates) are
strictly preserved across skill updates while incorporating new default styles
and configuration keys.
"""

import os
import sys
import json
import argparse

def merge_settings(current_settings, template_settings):
    """
    Merges template settings into current settings without overwriting user choices.
    """
    merged = dict(template_settings)

    # 1. Preserve user-chosen active artifactStyle, format, notes and project identity
    for id_key in ["projectId", "projectName", "track", "artifactStyle", "outputType", "autoGenerateNotes", "notesStructure"]:
        if id_key in current_settings:
            merged[id_key] = current_settings[id_key]

    # 2. Preserve directory paths preferences (paths object & top-level aliases)
    if "paths" in current_settings and isinstance(current_settings["paths"], dict):
        merged_paths = dict(template_settings.get("paths", {}))
        merged_paths.update(current_settings["paths"])
        merged["paths"] = merged_paths
    elif "paths" in template_settings:
        merged["paths"] = dict(template_settings["paths"])

    for dir_key in ["instanceDir", "cursorDir", "lessonsDir", "notesDir"]:
        if dir_key in current_settings:
            merged[dir_key] = current_settings[dir_key]
        elif "paths" in merged and dir_key in merged["paths"]:
            merged[dir_key] = merged["paths"][dir_key]

    # 3. Preserve user deliveryMode and inlineDiscussions if explicitly configured
    for key in ["deliveryMode", "inlineDiscussions", "inlineFollowups"]:
        if key in current_settings:
            merged[key] = current_settings[key]

    # 4. Merge availableStyles list
    template_styles = template_settings.get("availableStyles", [])
    current_styles = current_settings.get("availableStyles", [])

    # Index template styles by id
    style_map = {s["id"]: dict(s) for s in template_styles if "id" in s}

    # Overlay user custom styles or modified style descriptions
    for user_style in current_styles:
        sid = user_style.get("id")
        if not sid:
            continue
        if sid in style_map:
            # Update while preserving user custom fields
            style_map[sid].update(user_style)
        else:
            # User defined a brand-new custom theme
            style_map[sid] = user_style

    merged["availableStyles"] = list(style_map.values())

    # 5. Copy over any additional user-defined custom keys
    for k, v in current_settings.items():
        if k not in merged:
            merged[k] = v

    return merged

def main():
    parser = argparse.ArgumentParser(description="Merge or update System Design Studio settings while preserving user preferences.")
    parser.add_argument("--current", "--settings", "--instance-dir", dest="current", help="Path to current settings.json or .system-design directory")
    parser.add_argument("--template", "--defaults", dest="template", help="Path to settings-template.json or settings-defaults.json")
    parser.add_argument("--key", help="Specific setting key to update (e.g. artifactStyle, outputType, notesStructure)")
    parser.add_argument("--value", help="Value to set for --key")
    parser.add_argument("--output", help="Path to output merged settings.json (defaults to --current)")

    args = parser.parse_args()

    if not args.current:
        print("❌ Error: --current or --settings path is required.", file=sys.stderr)
        sys.exit(1)

    target_path = args.current
    if os.path.isdir(target_path):
        candidate = os.path.join(target_path, "settings.json")
        if not os.path.exists(candidate) and os.path.isdir(os.path.join(target_path, ".system-design")):
            candidate = os.path.join(target_path, ".system-design", "settings.json")
        target_path = candidate

    out_path = args.output or target_path

    # If updating a single key
    if args.key and args.value is not None:
        data = {}
        if os.path.exists(target_path):
            with open(target_path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except Exception:
                    data = {}

        # Handle boolean conversion
        val = args.value
        if val.lower() == "true":
            val = True
        elif val.lower() == "false":
            val = False

        # Support nested key paths (e.g., paths.notesDir)
        if "." in args.key:
            parts = args.key.split(".")
            curr = data
            for p in parts[:-1]:
                if p not in curr or not isinstance(curr[p], dict):
                    curr[p] = {}
                curr = curr[p]
            curr[parts[-1]] = val
        else:
            data[args.key] = val

        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.write("\n")

        print(f"✅ Setting updated in '{out_path}': {args.key} = {val}")
        return

    if not args.template:
        print("❌ Error: Either (--key and --value) or --template is required.", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(args.template):
        print(f"❌ Error: Template settings file not found: {args.template}", file=sys.stderr)
        sys.exit(1)

    with open(args.template) as tf:
        try:
            template_data = json.load(tf)
        except json.JSONDecodeError as e:
            print(f"❌ Error decoding template settings JSON: {e}", file=sys.stderr)
            sys.exit(1)

    current_data = {}
    if os.path.exists(target_path):
        try:
            with open(target_path) as cf:
                current_data = json.load(cf)
        except Exception as e:
            print(f"⚠️ Warning: Could not read current settings JSON ({e}); using template defaults.", file=sys.stderr)

    merged = merge_settings(current_data, template_data)

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w") as out_f:
        json.dump(merged, out_f, indent=2)
        out_f.write("\n")

    preserved_style = merged.get("artifactStyle", "slate-clean")
    lessons_dir = merged.get("paths", {}).get("lessonsDir") or merged.get("lessonsDir", ".system-design/lessons")
    cursor_dir = merged.get("paths", {}).get("cursorDir") or merged.get("cursorDir", ".system-design")

    print(f"✅ Settings merged successfully to '{out_path}'")
    print(f"   - Style:      '{preserved_style}'")
    print(f"   - Cursor Dir: '{cursor_dir}'")
    print(f"   - Lessons:    '{lessons_dir}'")

if __name__ == "__main__":
    main()
