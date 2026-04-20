"""
01_create_custom_fields.py
ndMAX Orbit — Phase 1, Task 1

Creates all 19 workspace-level custom fields in Asana and saves their GIDs
to orbit-config.json so other scripts can reference them.

Usage:
    # Set your token first:
    set ASANA_PAT=your_personal_access_token_here

    # Dry run (shows what would be created, no API calls):
    python 01_create_custom_fields.py --dry-run

    # Actually create the fields:
    python 01_create_custom_fields.py

Requirements:
    pip install requests
"""

import os
import json
import time
import argparse
import requests
from pathlib import Path

# ── Config ─────────────────────────────────────────────────────────────────

WORKSPACE_GID = "1148806218142272"
API_BASE      = "https://app.asana.com/api/1.0"
CONFIG_FILE   = Path(__file__).parent.parent / "orbit-config.json"

# ── Field definitions ───────────────────────────────────────────────────────

CUSTOM_FIELDS = [
    {
        "name": "RAG Status",
        "resource_subtype": "enum",
        "enum_options": [
            {"name": "Green", "color": "green"},
            {"name": "Amber", "color": "yellow"},
            {"name": "Red",   "color": "red"},
        ],
    },
    {
        "name": "PM/LC",
        "resource_subtype": "enum",
        "enum_options": [
            {"name": "Stephanie Klahre", "color": "aqua"},
            {"name": "Christopher Snead", "color": "blue"},
            {"name": "Tim Lutero",        "color": "purple"},
            {"name": "Staci VanderPol",   "color": "pink"},
            {"name": "Amir Mustafa",      "color": "orange"},
        ],
    },
    {
        "name": "Engineer",
        "resource_subtype": "enum",
        "enum_options": [
            {"name": "Greg Hartley",   "color": "aqua"},
            {"name": "Nikki Patel",    "color": "blue"},
            {"name": "Adam Scott",     "color": "green"},
            {"name": "Brandon Hill",   "color": "yellow"},
            {"name": "Andrew Mecham",  "color": "orange"},
            {"name": "Emilio Campos",  "color": "red"},
            {"name": "David Kero",     "color": "purple"},
            {"name": "Tyler Graf",     "color": "pink"},
        ],
    },
    {
        "name": "Value Engineer",
        "resource_subtype": "enum",
        "enum_options": [
            {"name": "Kyle Kissell", "color": "aqua"},
        ],
    },
    {
        "name": "ARR / Cash Value",
        "resource_subtype": "number",
        "precision": 0,
        "format": "currency",
        "currency_code": "USD",
    },
    {
        "name": "Cash Bucket",
        "resource_subtype": "enum",
        "enum_options": [
            {"name": "Under $10K",  "color": "yellow"},
            {"name": "$10-50K",     "color": "green"},
            {"name": "$50-100K",    "color": "blue"},
            {"name": "Over $100K",  "color": "purple"},
        ],
    },
    {
        "name": "Start Quarter",
        "resource_subtype": "enum",
        "enum_options": [
            {"name": "2025 Q1", "color": "aqua"},
            {"name": "2025 Q2", "color": "aqua"},
            {"name": "2025 Q3", "color": "aqua"},
            {"name": "2025 Q4", "color": "aqua"},
            {"name": "2026 Q1", "color": "blue"},
            {"name": "2026 Q2", "color": "blue"},
            {"name": "2026 Q3", "color": "blue"},
            {"name": "2026 Q4", "color": "blue"},
            {"name": "2027 Q1", "color": "purple"},
            {"name": "2027 Q2", "color": "purple"},
            {"name": "2027 Q3", "color": "purple"},
            {"name": "2027 Q4", "color": "purple"},
        ],
    },
    {
        "name": "GCX Status",
        "resource_subtype": "enum",
        "enum_options": [
            {"name": "On Time", "color": "green"},
            {"name": "Late",    "color": "red"},
            {"name": "On Hold", "color": "yellow"},
        ],
    },
    {
        "name": "Current Milestone",
        "resource_subtype": "enum",
        "enum_options": [
            {"name": "Kickoff",    "color": "aqua"},
            {"name": "Assistant",  "color": "blue"},
            {"name": "Studio Apps","color": "purple"},
            {"name": "Profiling",  "color": "orange"},
            {"name": "Hypercare",  "color": "green"},
        ],
    },
    {
        "name": "DM Implementation Phase",
        "resource_subtype": "enum",
        "enum_options": [
            {"name": "SOW Pending",            "color": "yellow"},
            {"name": "Initiation",             "color": "aqua"},
            {"name": "Design and Build",       "color": "blue"},
            {"name": "Test and Acceptance",    "color": "orange"},
            {"name": "Production Rollout",     "color": "purple"},
            {"name": "Post-Rollout Support",   "color": "green"},
            {"name": "Project Complete",       "color": "green"},
            {"name": "Cancelled",              "color": "red"},
        ],
    },
    {
        "name": "DM Expected Go-Live",
        "resource_subtype": "date",
    },
    {
        "name": "DM Actual Go-Live",
        "resource_subtype": "date",
    },
    {
        "name": "Products Purchased",
        "resource_subtype": "multi_enum",
        "enum_options": [
            {"name": "Legal AI Assistant", "color": "blue"},
            {"name": "Studio Apps",        "color": "purple"},
            {"name": "AI Profiling",       "color": "orange"},
            {"name": "Smart Answers",      "color": "aqua"},
            {"name": "PatternBuilder",     "color": "green"},
            {"name": "Custom App",         "color": "pink"},
            {"name": "ndMAX",              "color": "yellow"},
        ],
    },
    {
        "name": "Client Location",
        "resource_subtype": "text",
    },
    {
        "name": "Client Champion",
        "resource_subtype": "text",
    },
    {
        "name": "Champion Email",
        "resource_subtype": "text",
    },
    {
        "name": "Last Activity Date",
        "resource_subtype": "date",
    },
    {
        "name": "Engagement Velocity",
        "resource_subtype": "enum",
        "enum_options": [
            {"name": "Active",   "color": "green"},
            {"name": "Slowing",  "color": "yellow"},
            {"name": "Stalled",  "color": "orange"},
            {"name": "Silent",   "color": "red"},
        ],
    },
    {
        "name": "Projected End Date",
        "resource_subtype": "date",
    },
]

# ── API helpers ─────────────────────────────────────────────────────────────

def get_headers(pat: str) -> dict:
    return {
        "Authorization": f"Bearer {pat}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

def create_custom_field(pat: str, field_def: dict, dry_run: bool) -> dict:
    """Create one custom field. Returns the created field data (or a mock)."""
    payload = {
        "data": {
            "workspace": WORKSPACE_GID,
            "name": field_def["name"],
            "resource_subtype": field_def["resource_subtype"],
            "is_global_to_workspace": True,
        }
    }

    # Add type-specific attributes
    subtype = field_def["resource_subtype"]
    if subtype in ("enum", "multi_enum") and "enum_options" in field_def:
        payload["data"]["enum_options"] = field_def["enum_options"]

    if subtype == "number":
        payload["data"]["precision"] = field_def.get("precision", 0)
        if "format" in field_def:
            payload["data"]["format"] = field_def["format"]
        if "currency_code" in field_def:
            payload["data"]["currency_code"] = field_def["currency_code"]

    if dry_run:
        print(f"  [DRY RUN] Would create: {field_def['name']} ({subtype})")
        if subtype in ("enum", "multi_enum"):
            opts = [o["name"] for o in field_def.get("enum_options", [])]
            print(f"            Options: {', '.join(opts)}")
        return {"gid": f"DRY_RUN_{field_def['name'].replace(' ', '_').upper()}", "name": field_def["name"]}

    resp = requests.post(
        f"{API_BASE}/custom_fields",
        headers=get_headers(pat),
        json=payload,
        timeout=30,
    )

    if resp.status_code != 201:
        raise RuntimeError(
            f"Failed to create field '{field_def['name']}': "
            f"{resp.status_code} {resp.text}"
        )

    return resp.json()["data"]

# ── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Create ndMAX Orbit custom fields in Asana")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be created without API calls")
    args = parser.parse_args()

    pat = os.environ.get("ASANA_PAT", "")
    if not pat and not args.dry_run:
        print("ERROR: Set the ASANA_PAT environment variable before running.")
        print("       set ASANA_PAT=your_token_here")
        raise SystemExit(1)

    mode = "DRY RUN" if args.dry_run else "LIVE"
    print(f"\n{'='*60}")
    print(f"  ndMAX Orbit — Create Custom Fields [{mode}]")
    print(f"  Workspace GID: {WORKSPACE_GID}")
    print(f"  Fields to create: {len(CUSTOM_FIELDS)}")
    print(f"{'='*60}\n")

    created = {}
    errors  = []

    for i, field in enumerate(CUSTOM_FIELDS, 1):
        print(f"[{i:02d}/{len(CUSTOM_FIELDS)}] {field['name']} ({field['resource_subtype']})")
        try:
            result = create_custom_field(pat, field, args.dry_run)
            created[field["name"]] = {
                "gid": result["gid"],
                "resource_subtype": field["resource_subtype"],
            }

            if not args.dry_run:
                print(f"  OK  GID: {result['gid']}")

                # Build enum option lookup for later use in migration script
                if field["resource_subtype"] in ("enum", "multi_enum"):
                    # Fetch the field back to get option GIDs
                    time.sleep(0.3)  # rate limit courtesy
                    r = requests.get(
                        f"{API_BASE}/custom_fields/{result['gid']}",
                        headers=get_headers(pat),
                        timeout=30,
                    )
                    if r.status_code == 200:
                        opts = r.json()["data"].get("enum_options", [])
                        created[field["name"]]["enum_options"] = {
                            o["name"]: o["gid"] for o in opts
                        }

            if not args.dry_run:
                time.sleep(0.5)  # respect Asana rate limit (150 req/min)

        except Exception as e:
            print(f"  ERROR: {e}")
            errors.append({"field": field["name"], "error": str(e)})

    # ── Write config file ───────────────────────────────────────────────────

    config = {
        "workspace_gid": WORKSPACE_GID,
        "team_gid": "1204685785059509",
        "my_user_gid": "1211028599268999",
        "custom_fields": created,
        "milestone_sections": [
            "Kickoff & Readiness",
            "Legal AI Assistant Rollout",
            "Studio Apps Deployment",
            "AI Profiling",
            "Hypercare & Closeout",
        ],
        "dry_run": args.dry_run,
    }

    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    print(f"\n{'='*60}")
    print(f"  Results")
    print(f"{'='*60}")
    print(f"  Created: {len(created)}")
    print(f"  Errors:  {len(errors)}")
    print(f"  Config written to: {CONFIG_FILE}")

    if errors:
        print(f"\n  Failed fields:")
        for e in errors:
            print(f"    - {e['field']}: {e['error']}")

    if args.dry_run:
        print(f"\n  This was a DRY RUN. No fields were created in Asana.")
        print(f"  Re-run without --dry-run to create them for real.")

    print()

if __name__ == "__main__":
    main()
