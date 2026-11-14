#!/usr/bin/env python3
"""
merge-settings.py
Deep-merges user settings.json with the latest settings-template.json.
Guarantees that user preferences (such as chosen artifactStyle, custom themes,
and overrides) are preserved across skill updates while incorporating new default styles
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

    # 1. Preserve user-chosen active artifactStyle
    if "artifactStyle" in current_settings:
        merged["artifactStyle"] = current_settings["artifactStyle"]

    # 2. Preserve user deliveryMode and inlineDiscussions if explicitly configured
    for key in ["deliveryMode", "inlineDiscussions", "inlineFollowups"]:
        if key in current_settings:
            merged[key] = current_settings[key]

    # 3. Merge availableStyles list
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

    # 4. Copy over any additional user-defined custom keys
    for k, v in current_settings.items():
        if k not in merged:
            merged[k] = v

    return merged

def main():
    parser = argparse.ArgumentParser(description="Merge System Design Studio settings while preserving user preferences.")
    parser.add_argument("--current", required=True, help="Path to current settings.json")
    parser.add_argument("--template", required=True, help="Path to settings-template.json")
    parser.add_argument("--output", help="Path to output merged settings.json (defaults to --current)")

    args = parser.parse_args()
    out_path = args.output or args.current

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
    if os.path.exists(args.current):
        try:
            with open(args.current) as cf:
                current_data = json.load(cf)
        except Exception as e:
            print(f"⚠️ Warning: Could not read current settings JSON ({e}); using template defaults.", file=sys.stderr)

    merged = merge_settings(current_data, template_data)

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w") as out_f:
        json.dump(merged, out_f, indent=2)
        out_f.write("\n")

    preserved_style = merged.get("artifactStyle", "slate-clean")
    print(f"✅ Settings merged successfully to '{out_path}' (Active style preserved: '{preserved_style}')")

if __name__ == "__main__":
    main()
