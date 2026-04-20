"""
02_migrate_gcx.py
ndMAX Orbit — Phase 1, Task 2

Migrates all 82 GuideCX projects to Asana under the ND Implementations team.
For each project it:
  - Detects current milestone from status narrative (keyword matching)
  - Creates the Asana project with RAG emoji prefix
  - Creates the 5 fixed milestone sections
  - Populates all 19 custom fields from GCX data
  - Posts the current status note as the first project status update
  - Creates placeholder tasks in the current milestone section
  - Optionally filters by PM/LC so you can test with just your clients first

Usage:
    # Dry run — see what would be created (safe, no API calls):
    python 02_migrate_gcx.py --dry-run

    # Dry run for Stephanie's clients only:
    python 02_migrate_gcx.py --dry-run --pm "Stephanie Klahre"

    # Live run for Stephanie's clients only (test before all 82):
    python 02_migrate_gcx.py --pm "Stephanie Klahre"

    # Full migration (all 82 projects):
    python 02_migrate_gcx.py

Requirements:
    pip install requests
    ASANA_PAT environment variable set
    orbit-config.json must exist (run 01_create_custom_fields.py first)
"""

import os
import re
import json
import time
import argparse
import requests
from pathlib import Path
from datetime import datetime

# ── Config ─────────────────────────────────────────────────────────────────

GCX_HTML_PATH = Path("C:/Users/Stephanie.Klahre/Documents/GuideCX_Dashboard 4922-4120-6428 v5.html")
CONFIG_FILE   = Path(__file__).parent.parent / "orbit-config.json"
REPORT_FILE   = Path(__file__).parent.parent / "migration-report.json"
API_BASE      = "https://app.asana.com/api/1.0"

RAG_EMOJI = {"Green": "🟢", "Amber": "🟡", "Red": "🔴", "": "⚪"}

# Milestone sections in order
MILESTONE_SECTIONS = [
    "Kickoff & Readiness",
    "Legal AI Assistant Rollout",
    "Studio Apps Deployment",
    "AI Profiling",
    "Hypercare & Closeout",
]

# Placeholder tasks per milestone
MILESTONE_TASKS = {
    "Kickoff & Readiness": [
        "Schedule kickoff call",
        "Send Welcome Packet to client",
        "Confirm DM go-live status",
        "Complete intake form with client details",
        "Kickoff call completed",
    ],
    "Legal AI Assistant Rollout": [
        "System message configuration session",
        "Initial AI testing with client",
        "Feedback review and refinements",
        "Client sign-off on AI Assistant",
        "AI Assistant live",
    ],
    "Studio Apps Deployment": [
        "App selection session with client",
        "Import and configure selected apps",
        "Client UAT session",
        "Refinements based on client feedback",
        "Studio Apps live",
    ],
    "AI Profiling": [
        "Document type review meeting",
        "Taxonomy finalization",
        "Profiling configuration",
        "Testing and validation",
        "AI Profiling live",
    ],
    "Hypercare & Closeout": [
        "30-day check-in call",
        "Adoption review",
        "Final documentation handoff to CSM",
        "Project closure sign-off",
        "Introduce Value Engineering team",
    ],
}

# ── Milestone detection (keyword matching) ─────────────────────────────────

MILESTONE_KEYWORDS = {
    "Kickoff & Readiness": [
        "kickoff", "kick off", "welcome packet", "scheduling", "intake",
        "project created", "new project", "introduced", "introduction",
        "dm go-live", "dm expected", "waiting on dm", "dm not yet",
        "unassigned", "tbd",
    ],
    "Legal AI Assistant Rollout": [
        "ai assistant", "legal ai", "system message", "system prompt",
        "testing", "refinement", "assistant live", "assistant rollout",
        "training", "feedback", "rerunning", "smart answers",
    ],
    "Studio Apps Deployment": [
        "studio app", "studio apps", "app builder", "patternbuilder",
        "pattern builder", "import", "configure", "uat", "app selection",
        "apps live", "apps deployed",
    ],
    "AI Profiling": [
        "profil", "taxonomy", "document type", "profiling",
        "classification", "matter type",
    ],
    "Hypercare & Closeout": [
        "hypercare", "close", "closeout", "handoff", "csm", "adoption",
        "complete", "completed", "project complete", "value team",
    ],
}

def detect_milestone(status_text: str, dm_phase: str) -> str:
    """Return the most likely current milestone based on status narrative."""
    text_lower = (status_text or "").lower()

    # Check DM phase — if DM isn't complete, likely in Kickoff
    if dm_phase in ("SOW Pending", "Initiation", "Design and Build", "Test and Acceptance"):
        return "Kickoff & Readiness"

    # Score each milestone by keyword matches
    scores = {m: 0 for m in MILESTONE_KEYWORDS}
    for milestone, keywords in MILESTONE_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                scores[milestone] += 1

    best = max(scores, key=lambda m: scores[m])
    return best if scores[best] > 0 else "Kickoff & Readiness"

# ── Data mapping ────────────────────────────────────────────────────────────

CASH_BUCKET_MAP = {
    "1: under $10k":  "Under $10K",
    "under $10k":     "Under $10K",
    "1":              "Under $10K",
    "2: $10-50k":     "$10-50K",
    "$10-50k":        "$10-50K",
    "2":              "$10-50K",
    "3: $50-100k":    "$50-100K",
    "$50-100k":       "$50-100K",
    "3":              "$50-100K",
    "4: over $100k":  "Over $100K",
    "over $100k":     "Over $100K",
    "4":              "Over $100K",
}

DM_PHASE_MAP = {
    "sow pending":          "SOW Pending",
    "initiation":           "Initiation",
    "design and build":     "Design and Build",
    "test and acceptance":  "Test and Acceptance",
    "production rollout":   "Production Rollout",
    "post-rollout support": "Post-Rollout Support",
    "project complete":     "Project Complete",
    "cancelled":            "Cancelled",
    "canceled":             "Cancelled",
}

def parse_date(date_str: str) -> str:
    """Convert various date formats to YYYY-MM-DD or empty string."""
    if not date_str:
        return ""
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%m/%d/%Y %I:%M %p", "%m/%d/%Y"):
        try:
            return datetime.strptime(date_str.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return ""

def clean_project_name(raw_name: str) -> str:
    """Strip GCX suffix patterns from project name."""
    name = raw_name
    for suffix in [" AI PS Onboarding", " PS Onboarding", " Onboarding"]:
        if name.endswith(suffix):
            name = name[: -len(suffix)]
    return name.strip()

# ── API helpers ─────────────────────────────────────────────────────────────

def headers(pat: str) -> dict:
    return {
        "Authorization": f"Bearer {pat}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

def api_post(pat: str, path: str, payload: dict, dry_run: bool, label: str = "") -> dict:
    if dry_run:
        return {"gid": f"DRY_{label}", "name": label}
    resp = requests.post(f"{API_BASE}{path}", headers=headers(pat), json=payload, timeout=30)
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"POST {path} failed {resp.status_code}: {resp.text[:300]}")
    time.sleep(0.4)  # rate limit: ~150 req/min
    return resp.json()["data"]

def api_get(pat: str, path: str) -> dict:
    resp = requests.get(f"{API_BASE}{path}", headers=headers(pat), timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"GET {path} failed {resp.status_code}: {resp.text[:300]}")
    return resp.json()["data"]

# ── GCX data extraction ─────────────────────────────────────────────────────

def extract_gcx_data(html_path: Path) -> list:
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()
    match = re.search(r"const DATA\s*=\s*(\[.*?\]);", content, re.DOTALL)
    if not match:
        raise RuntimeError("Could not find 'const DATA = [...]' in the GCX HTML file.")
    return json.loads(match.group(1))

# ── Project creation ────────────────────────────────────────────────────────

def build_custom_field_values(row: dict, config: dict) -> dict:
    """Map GCX row fields to Asana custom field GIDs and values."""
    cf_config = config["custom_fields"]
    values = {}

    def enum_gid(field_name: str, option_name: str) -> str:
        opts = cf_config.get(field_name, {}).get("enum_options", {})
        return opts.get(option_name, "")

    def field_gid(field_name: str) -> str:
        return cf_config.get(field_name, {}).get("gid", "")

    # RAG Status
    rag = row.get("RAG Status", "Green")
    if fg := field_gid("RAG Status"):
        values[fg] = enum_gid("RAG Status", rag) or None

    # PM/LC
    pm = row.get("PM/LC", "")
    if pm and (fg := field_gid("PM/LC")):
        values[fg] = enum_gid("PM/LC", pm) or None

    # Engineer
    eng = row.get("Engineer", "")
    if eng and (fg := field_gid("Engineer")):
        values[fg] = enum_gid("Engineer", eng) or None

    # ARR / Cash Value
    cash_str = row.get("Cash Value", "")
    if cash_str:
        try:
            cash_val = float(cash_str)
            if fg := field_gid("ARR / Cash Value"):
                values[fg] = cash_val
        except ValueError:
            pass

    # Cash Bucket
    bucket_raw = row.get("Cash Value Bucket", "").lower()
    bucket_mapped = CASH_BUCKET_MAP.get(bucket_raw, "")
    if bucket_mapped and (fg := field_gid("Cash Bucket")):
        values[fg] = enum_gid("Cash Bucket", bucket_mapped) or None

    # Start Quarter
    sq = row.get("Start Quarter", "")
    if sq and (fg := field_gid("Start Quarter")):
        values[fg] = enum_gid("Start Quarter", sq) or None

    # GCX Status
    gcx_status = row.get("Status", "")
    if gcx_status and (fg := field_gid("GCX Status")):
        values[fg] = enum_gid("GCX Status", gcx_status) or None

    # DM Implementation Phase
    dm_phase_raw = row.get("DM Case: Implementation Phase", "").lower().strip()
    dm_phase = DM_PHASE_MAP.get(dm_phase_raw, "")
    if dm_phase and (fg := field_gid("DM Implementation Phase")):
        values[fg] = enum_gid("DM Implementation Phase", dm_phase) or None

    # DM Expected Go-Live
    dm_expected = parse_date(row.get("DM Case: Expected Go-Live Date", ""))
    if dm_expected and (fg := field_gid("DM Expected Go-Live")):
        values[fg] = {"date": dm_expected}

    # DM Actual Go-Live
    dm_actual = parse_date(row.get("DM Case: Actual Go-Live Date", ""))
    if dm_actual and (fg := field_gid("DM Actual Go-Live")):
        values[fg] = {"date": dm_actual}

    # Last Activity Date
    last_updated = parse_date(row.get("Last Updated", ""))
    if last_updated and (fg := field_gid("Last Activity Date")):
        values[fg] = {"date": last_updated}

    # Projected End Date
    projected_end = parse_date(row.get("Projected End Date", ""))
    if projected_end and (fg := field_gid("Projected End Date")):
        values[fg] = {"date": projected_end}

    # Remove None values — Asana rejects null enum GIDs
    return {k: v for k, v in values.items() if v is not None and v != ""}

def migrate_project(pat: str, row: dict, config: dict, dry_run: bool) -> dict:
    """Create one Asana project from a GCX row. Returns a result record."""
    team_gid  = config["team_gid"]
    workspace = config["workspace_gid"]

    raw_name   = row.get("Project Name", "Unknown")
    clean_name = clean_project_name(raw_name)
    rag        = row.get("RAG Status", "Green")
    emoji      = RAG_EMOJI.get(rag, "⚪")
    project_name = f"{emoji} {clean_name} — ndMAX Implementation"

    status_text = row.get("Current Project Status", "")
    dm_phase    = DM_PHASE_MAP.get(
        row.get("DM Case: Implementation Phase", "").lower().strip(), ""
    )
    current_milestone = detect_milestone(status_text, dm_phase)

    # Collect unmapped data for report
    unmapped = {}
    if not row.get("PM/LC"):
        unmapped["PM/LC"] = "empty"
    if not row.get("Engineer"):
        unmapped["Engineer"] = "empty (will need manual assignment)"

    result = {
        "gcx_name":          raw_name,
        "asana_name":        project_name,
        "pm_lc":             row.get("PM/LC", ""),
        "rag":               rag,
        "detected_milestone": current_milestone,
        "status":            "dry_run" if dry_run else "pending",
        "asana_project_gid": None,
        "unmapped":          unmapped,
        "errors":            [],
    }

    if dry_run:
        print(f"  [DRY RUN] {project_name}")
        print(f"            PM/LC: {row.get('PM/LC','—')}  |  "
              f"RAG: {rag}  |  Milestone: {current_milestone}")
        print(f"            Status: {status_text[:80]}{'...' if len(status_text) > 80 else ''}")
        return result

    try:
        # 1. Create project
        start_date = parse_date(row.get("Start Date", ""))
        due_date   = parse_date(row.get("Due Date", ""))

        proj_payload = {
            "data": {
                "name":      project_name,
                "team":      team_gid,
                "workspace": workspace,
                "notes":     f"Migrated from GuideCX on {datetime.today().strftime('%Y-%m-%d')}",
            }
        }
        if start_date:
            proj_payload["data"]["start_on"] = start_date
        if due_date:
            proj_payload["data"]["due_on"] = due_date

        proj = api_post(pat, "/projects", proj_payload, dry_run=False, label=project_name)
        project_gid = proj["gid"]
        result["asana_project_gid"] = project_gid
        print(f"  Created project: {project_name} (GID: {project_gid})")

        # 2. Create milestone sections
        section_gids = {}
        for section_name in MILESTONE_SECTIONS:
            sec = api_post(
                pat, f"/projects/{project_gid}/sections",
                {"data": {"name": section_name}},
                dry_run=False, label=section_name,
            )
            section_gids[section_name] = sec["gid"]

        print(f"  Created {len(section_gids)} sections")

        # 3. Add custom field settings to project
        cf_config = config["custom_fields"]
        for field_name, field_info in cf_config.items():
            fg = field_info.get("gid", "")
            if fg and not fg.startswith("DRY_RUN"):
                try:
                    api_post(
                        pat, f"/projects/{project_gid}/addCustomFieldSetting",
                        {"data": {"custom_field": fg, "is_important": False}},
                        dry_run=False, label=field_name,
                    )
                except Exception as e:
                    # Non-fatal — field may already be on the project
                    result["errors"].append(f"addCustomFieldSetting {field_name}: {e}")

        # 4. Set custom field values on the project via project update
        cf_values = build_custom_field_values(row, config)
        if cf_values:
            try:
                resp = requests.put(
                    f"{API_BASE}/projects/{project_gid}",
                    headers=headers(pat),
                    json={"data": {"custom_fields": cf_values}},
                    timeout=30,
                )
                if resp.status_code != 200:
                    result["errors"].append(f"custom field update: {resp.status_code} {resp.text[:200]}")
                time.sleep(0.4)
            except Exception as e:
                result["errors"].append(f"custom field update exception: {e}")

        # 5. Set Current Milestone field
        cm_gid = cf_config.get("Current Milestone", {}).get("gid", "")
        cm_opts = cf_config.get("Current Milestone", {}).get("enum_options", {})
        if cm_gid and current_milestone in cm_opts:
            try:
                resp = requests.put(
                    f"{API_BASE}/projects/{project_gid}",
                    headers=headers(pat),
                    json={"data": {"custom_fields": {cm_gid: cm_opts[current_milestone]}}},
                    timeout=30,
                )
                time.sleep(0.3)
            except Exception as e:
                result["errors"].append(f"set current milestone: {e}")

        # 6. Create status update (first project status note)
        if status_text:
            try:
                today = datetime.today().strftime("%Y-%m-%d")
                api_post(
                    pat, "/project_statuses",
                    {
                        "data": {
                            "project": project_gid,
                            "title":  f"Migrated from GuideCX — {today}",
                            "text":   status_text,
                            "color":  rag.lower() if rag.lower() in ("green", "red") else "yellow",
                        }
                    },
                    dry_run=False, label="status",
                )
            except Exception as e:
                result["errors"].append(f"status update: {e}")

        # 7. Create placeholder tasks in current milestone section
        current_section_gid = section_gids.get(current_milestone)
        if current_section_gid:
            task_names = MILESTONE_TASKS.get(current_milestone, [])
            for task_name in task_names:
                try:
                    api_post(
                        pat, "/tasks",
                        {
                            "data": {
                                "name":      task_name,
                                "projects":  [project_gid],
                                "memberships": [
                                    {"project": project_gid, "section": current_section_gid}
                                ],
                            }
                        },
                        dry_run=False, label=task_name,
                    )
                except Exception as e:
                    result["errors"].append(f"task '{task_name}': {e}")

        result["status"] = "success" if not result["errors"] else "partial"
        print(f"  Status: {result['status']} | Tasks: {len(MILESTONE_TASKS.get(current_milestone,[]))}")

    except Exception as e:
        result["status"] = "error"
        result["errors"].append(str(e))
        print(f"  ERROR: {e}")

    return result

# ── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Migrate GuideCX projects to Asana")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview without creating anything in Asana")
    parser.add_argument("--pm", type=str, default="",
                        help="Filter to one PM/LC (e.g. 'Stephanie Klahre')")
    args = parser.parse_args()

    pat = os.environ.get("ASANA_PAT", "")
    if not pat and not args.dry_run:
        print("ERROR: Set ASANA_PAT before running.")
        print("       set ASANA_PAT=your_token_here")
        raise SystemExit(1)

    # Load config
    if not CONFIG_FILE.exists():
        print(f"ERROR: {CONFIG_FILE} not found.")
        print("       Run 01_create_custom_fields.py first.")
        raise SystemExit(1)

    with open(CONFIG_FILE, encoding="utf-8") as f:
        config = json.load(f)

    # Load GCX data
    if not GCX_HTML_PATH.exists():
        print(f"ERROR: GCX HTML not found at:\n  {GCX_HTML_PATH}")
        raise SystemExit(1)

    all_projects = extract_gcx_data(GCX_HTML_PATH)

    # Filter
    projects = all_projects
    if args.pm:
        projects = [p for p in all_projects if args.pm.lower() in p.get("PM/LC", "").lower()]

    mode    = "DRY RUN" if args.dry_run else "LIVE"
    filter_ = f" | Filter: PM/LC = '{args.pm}'" if args.pm else ""
    print(f"\n{'='*60}")
    print(f"  ndMAX Orbit — GCX Migration [{mode}]{filter_}")
    print(f"  Total in GCX: {len(all_projects)}  |  To migrate: {len(projects)}")
    print(f"{'='*60}\n")

    results  = []
    success  = 0
    partial  = 0
    errors   = 0
    dry_runs = 0

    for i, row in enumerate(projects, 1):
        name = row.get("Project Name", "Unknown")
        pm   = row.get("PM/LC", "—")
        print(f"\n[{i:02d}/{len(projects)}] {name}  (PM: {pm})")

        result = migrate_project(pat, row, config, args.dry_run)
        results.append(result)

        s = result["status"]
        if s == "success":  success  += 1
        if s == "partial":  partial  += 1
        if s == "error":    errors   += 1
        if s == "dry_run":  dry_runs += 1

        if not args.dry_run:
            time.sleep(0.5)

    # ── Write report ────────────────────────────────────────────────────────

    report = {
        "run_date":   datetime.today().isoformat(),
        "dry_run":    args.dry_run,
        "pm_filter":  args.pm,
        "summary": {
            "total":   len(projects),
            "success": success,
            "partial": partial,
            "errors":  errors,
            "dry_run": dry_runs,
        },
        "projects": results,
    }

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\n{'='*60}")
    print(f"  Migration Summary")
    print(f"{'='*60}")
    if args.dry_run:
        print(f"  Would migrate:  {dry_runs} projects")
        print(f"  This was a DRY RUN — nothing was created in Asana.")
        print(f"  Review the report, then run without --dry-run.")
    else:
        print(f"  Success:  {success}")
        print(f"  Partial:  {partial}  (created but some fields may be missing)")
        print(f"  Errors:   {errors}")

    print(f"  Report:   {REPORT_FILE}\n")

    if not args.dry_run and errors > 0:
        print("  Projects with errors:")
        for r in results:
            if r["status"] == "error":
                print(f"    - {r['gcx_name']}: {r['errors']}")

if __name__ == "__main__":
    main()
