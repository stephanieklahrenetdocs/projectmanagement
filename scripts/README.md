# ndMAX Orbit — Scripts

---

## Automating the Hub (orbit_hub.html)

There are two automation levels. Use whichever fits your workflow.

---

### Option A — ⚡ Connect CSV (zero setup, recommended for daily use)

No Python needed. Works entirely in Chrome or Edge.

1. Open `orbit_hub.html` in Chrome or Edge
2. Click **⚡ Connect CSV** → pick your `combined_YYYYMMDD.csv` file
3. Grant permission when asked — **done.**

From now on, every time you open the file, the browser re-reads the CSV from disk automatically. When you export a new CSV **to the same filename/location**, just refresh the page — data updates instantly.

> **Note:** Chrome may ask you to confirm permission again after a browser restart. Just click ⚡ Connect CSV once more — it remembers the file, just needs a re-tap.

---

### Option B — Scheduled Task (fully hands-off, runs at 8am daily)

`refresh_hub.py` embeds the CSV directly into the HTML so it works offline and needs no clicks.

#### Step 1: Run manually first (test it)
```
python scripts\refresh_hub.py
```

This finds your latest `combined_*.csv` in Downloads, embeds it in orbit_hub.html, and keeps a backup.

#### Step 2: Specify a path if auto-detect fails
```
python scripts\refresh_hub.py --csv "C:\Users\Stephanie.Klahre\Downloads\combined_20260414.csv"
```

#### Step 3: Set up Windows Task Scheduler

1. Press **Win + S** → search "Task Scheduler" → Open it
2. Click **Create Basic Task…** (right panel)
3. Name: `Orbit Hub Refresh`
4. Trigger: **Daily**, 8:00 AM
5. Action: **Start a program**
6. Program: `python`
7. Arguments (one line, edit paths to match yours):
   ```
   "C:\Users\Stephanie.Klahre\Documents\PROJECT MANAGEMENT SYSTEM\scripts\refresh_hub.py"
   ```
8. Start in:
   ```
   C:\Users\Stephanie.Klahre\Documents\PROJECT MANAGEMENT SYSTEM
   ```
9. Finish → check **Open Properties** → General tab → check **Run whether user is logged on or not** if you want it to run even when your laptop is locked

Every morning at 8am, the script runs silently, embeds the latest CSV, and orbit_hub.html is ready when you open it.

---

## Prerequisites

1. **Install Python** (3.10+): https://www.python.org/downloads/
2. **Install dependencies**:
   ```
   pip install requests
   ```
3. **Get an Asana Personal Access Token**:
   - Go to https://app.asana.com/0/developer-console
   - Personal access tokens → Create new token
   - Copy and save it somewhere safe

4. **Set your token** (do this before running any script):
   ```
   set ASANA_PAT=your_token_here
   ```

---

## Script 1: Create Custom Fields

`01_create_custom_fields.py` — Creates all 19 workspace-level custom fields in Asana.

### Dry run first (always)
```
python scripts/01_create_custom_fields.py --dry-run
```

This shows what would be created without touching Asana. Review the output, then:

### Create for real
```
python scripts/01_create_custom_fields.py
```

This creates all 19 fields and writes their GIDs to `orbit-config.json`.

**Important:** Run this only once. If you run it twice, you'll get duplicate fields in your workspace. If something goes wrong mid-run, check Asana first before re-running.

---

## Script 2: Migrate GCX Projects

`02_migrate_gcx.py` — Migrates GuideCX projects to Asana Orbit projects.

### Always start with your clients only
```
python scripts/02_migrate_gcx.py --dry-run --pm "Stephanie Klahre"
```

This shows what would be created for your ~16 clients. Review the milestone detection output — if a project is assigned to the wrong milestone, note it so you can correct it after migration.

### Dry run — all 82 projects
```
python scripts/02_migrate_gcx.py --dry-run
```

### Migrate your clients (test batch)
```
python scripts/02_migrate_gcx.py --pm "Stephanie Klahre"
```

Review the Asana projects created. Spot-check 3–4 to make sure data looks right.

### Migrate everyone
```
python scripts/02_migrate_gcx.py
```

### After migration

Check `migration-report.json` in this directory — it shows every project, its detected milestone, and any errors. Fields that need manual attention (Client Location, Client Champion, Champion Email, Products Purchased) are listed per project.

---

## Phase 2: Task-level custom fields

The spec (section 3.4) defines four additional custom fields that apply to **tasks** (not projects). These are NOT created by Script 1, which only creates project-level fields. Add these manually in Asana, or build a `03_create_task_fields.py` script in Phase 2:

| Field | Type | Options |
|-------|------|---------|
| Owner Role | Dropdown | ND Team \| Client \| Shared |
| Task Type | Dropdown | Meeting \| Deliverable \| Decision \| Configuration \| Review |
| Blocked By | Text | Free text |
| Source | Dropdown | AI Generated \| Manual \| Sync |

---

## Velocity algorithm — Phase 1 vs. Phase 3

Script 2 uses a simplified velocity model (single `Last Activity Date` signal) because email and meeting data aren't available until Phase 3 MCP integration. The authoritative velocity algorithm from the spec uses **dual signals**:

```
Silent:  days_since_last_email > 30 AND days_since_last_meeting > 30
Stalled: days_since_last_email > 14 AND days_since_last_meeting > 21
Slowing: days_since_last_email > 8  OR  days_since_last_meeting > 14
Active:  otherwise
```

The `orbit-sync` skill implements the full algorithm once Outlook + Gainsight MCP connectors are wired up in Phase 3.

---

## orbit-config.json

Auto-generated by Script 1. Contains all custom field GIDs that Script 2 needs.

**Do not edit manually** — except the `_comment` field.

---

## Folder structure

```
PROJECT MANAGEMENT SYSTEM/
├── orbit-config.json          ← auto-generated by script 1
├── migration-report.json      ← auto-generated by script 2
├── scripts/
│   ├── README.md              ← this file
│   ├── 01_create_custom_fields.py
│   └── 02_migrate_gcx.py
└── skills/
    ├── orbit-sync/SKILL.md
    ├── orbit-briefing/SKILL.md
    ├── orbit-intake/SKILL.md
    ├── orbit-navigator/SKILL.md
    ├── orbit-weekly-notes/SKILL.md
    └── orbit-kickoff/SKILL.md
```

---

## Deploying the skills

The six SKILL.md files in the `skills/` folder are ready to deploy to Claude Enterprise.

To deploy, copy each SKILL.md into your Claude Enterprise skills directory and register them. The exact path depends on your Claude Enterprise configuration — check with your admin or reference the Claude Enterprise documentation.

Skills communicate with Asana via the Asana MCP connector (mcp.asana.com/v2/mcp), which handles authentication automatically in the Claude Enterprise environment.

---

## Troubleshooting

**`ASANA_PAT` not set error**: Run `set ASANA_PAT=yourtoken` before running scripts.

**`orbit-config.json not found` error**: Run script 1 first before script 2.

**API rate limit errors**: The scripts include `time.sleep()` delays. If you still hit limits, the partial results are in `migration-report.json` — you can resume by filtering to unprocessed clients.

**Wrong milestone detected**: The milestone detection uses keyword matching on the status text. After migration, search your Asana projects for any where the Current Milestone seems wrong and update manually via the Orbit Sync skill.

**Duplicate custom fields**: If you accidentally run script 1 twice, go to Asana workspace settings → Custom Fields and manually delete the duplicates. Then re-run script 1 on a fresh `orbit-config.json`.
