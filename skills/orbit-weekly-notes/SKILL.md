---
name: orbit-weekly-notes
description: "Generate weekly status update notes for all clients in a PM/LC's portfolio. Use this skill when someone says 'Friday updates', 'weekly notes', 'generate my status updates', 'draft my status notes', 'GCX updates', 'time for updates', 'weekly status', or any request related to producing end-of-week client status summaries. This skill sweeps all data sources (Outlook, Slack, Gainsight, Teams), drafts per-client notes, proposes RAG changes, and presents everything for review before publishing to Asana. Trigger this even for partial requests like 'update notes for my red clients' or 'what changed this week for [Client]'."
---

# Orbit Weekly Notes — The Friday Automation

## Overview

Every Friday, PM/LCs need to update the status of all their clients. In GuideCX, this was a painful manual process. Orbit automates 90% of it: the skill sweeps all data sources, drafts status notes for every client, proposes RAG changes with reasoning, and presents everything for review. The PM/LC edits what needs editing and approves.

## Prerequisites

1. Call `orbit-sync` for a full portfolio sync before generating notes
2. Identify the current user and their portfolio from Asana

## Step 1: Load portfolio

```
Query Asana for all projects where:
  - Team = ND Implementations
  - PM/LC custom field = current user (or specified PM/LC)
  - Project is not archived

For each project, load:
  - All custom fields (RAG, velocity, milestone, ARR, DM status, etc.)
  - Last 2 status update notes (for comparison / continuity)
  - Incomplete tasks (to assess progress)
  - Recently completed tasks (this week)
```

## Step 2: For each client, gather this week's data

### Email activity
```
Tool: Microsoft 365 outlook_email_search
Query: [client name] OR [champion email]
Date range: Monday of this week to today
Extract: key topics discussed, action items, sentiment
```

### Slack activity
```
Tool: Slack slack_search_public_and_private  
Query: [client name]
Date range: this week
Extract: team discussions, engineer updates, decisions
```

### Meeting activity
```
Tool: Microsoft 365 outlook_calendar_search
Query: [client name]
Date range: Monday to today
For each meeting found, check for Copilot transcript/notes
Extract: what was discussed, decisions made, action items
```

### Gainsight signals
```
Tool: Gainsight staircase_query
Query: "[client name] health and risk signals"
Extract: health score change, sentiment, alerts
```

### Asana task changes
```
Compare task states from start of week to now:
- Tasks completed this week
- Tasks added this week
- Tasks that became overdue
- Custom field changes (RAG, velocity, milestone)
```

## Step 3: Draft the status note

For each client, generate a note following this format:

```
NOTE FORMAT:

[date] - [Summary sentence]. [Detail sentence if applicable]. [Next step if clear]. - [PM/LC initials]

EXAMPLES:
"4/11/26 - Scheduled Studio App Configuration working session with Chel and Mary for April 7 at 4pm ET with Nikki. Apps imported, setup underway. - SK"

"4/11/26 - No change since last update. Customer paused ndMAX implementation with minimal PS hours used (~5/24). Expected to re-engage when ready. - SK"

"4/11/26 - Client raised concerns about AI Profiling limitations. Call with Kyle Kissell and Steve Yates scheduled to discuss workarounds. Emilio sent profiling plan. - SK"
```

### Note generation rules:

1. **Match the PM/LC's voice** — study the last 2 status notes to match tone, abbreviation style, and level of detail. Stephanie writes concisely with dates and initials. Match that.

2. **Only report real changes** — if nothing happened this week, write "No change since last update. [Brief reminder of current state]. - [initials]"

3. **Lead with action** — start with what happened or what's happening next, not background.

4. **Include dates** — specific dates for meetings, deadlines, and events.

5. **Name names** — mention specific people involved (client contacts, engineers, CSMs).

6. **Keep it under 3 sentences** — these notes need to be scannable across 20+ clients.

7. **Use the client's exact status language** — if the client said "we'll start in April," use that phrasing.

## Step 4: RAG assessment

For each client, evaluate whether the RAG status should change:

```
RAG CHANGE ASSESSMENT:

For each client, compare:
  - Current RAG status (from Asana custom field)
  - Recommended RAG (from orbit-sync velocity algorithm)
  - This week's events (positive or negative signals)

Propose a change ONLY if:
  - Clear evidence supports it (not just a gut feeling)
  - The change is justified by specific events this week
  - The PM/LC hasn't recently overridden the recommendation

Format:
  ⚠️ RAG change recommended: [Current] → [Proposed]
  Reason: [specific evidence]
```

## Step 5: Present for review

Show all drafted notes in a single, reviewable interface:

```
OUTPUT FORMAT:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 Weekly Notes — [Date]
Portfolio: [Name] | Clients: [N]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Group by RAG status: Red first, then Amber, then Green]

🔴 RED CLIENTS ([N])
─────────────────────

[Client Name] | ARR: $[amount] | Milestone: [phase]
Current note: "[drafted note text]"
[If RAG change:] ⚠️ Recommend: 🔴→🟡 — [reason]
[Button: "Edit note"] [Button: "Approve ✓"]

─────────────────────

[Repeat for each red client]

🟡 AMBER CLIENTS ([N])
─────────────────────

[Same format for each amber client]

🟢 GREEN CLIENTS ([N])  
─────────────────────

[Same format for each green client]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SUMMARY
  Notes drafted: [N]
  RAG changes proposed: [N]
  Clients with no changes: [N]

[Button: "Approve all notes"]
[Button: "Approve all + RAG changes"]
[Button: "Edit specific notes"]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Step 6: Publish approved notes

Once the PM/LC approves (all or individually):

1. Write each approved note as an Asana status update on the corresponding project
2. Update the "Last Updated" / "Last Activity Date" custom field to today
3. Apply any approved RAG status changes
4. Update engagement velocity if changed

```
For each approved note:
  Tool: Asana add_comment or create_project_status_update
  Project: [client project GID]
  Content: [approved note text]
  
  Tool: Asana update_tasks (for custom field updates)
  Fields: Last Activity Date = today, RAG Status = [if changed]
```

## Partial modes

### Single client
"Update notes for Wiggin and Dana only" → runs the full pipeline for just that client

### RAG filter
"Update my red clients" → only processes clients with Red RAG status

### Specific date range
"What happened with my clients since Monday?" → adjusts the data gathering window

### Comparison mode
"Show me what changed since last week's notes" → highlights differences between last week's notes and this week's draft

## Integration with GCX (transition period)

During the parallel operation period, the weekly notes skill can also:
- Format notes in the exact GCX status update format
- Copy-paste ready output for manual entry into GCX
- Track which clients have been updated in both systems

## Behavioral Rules

1. **Never publish without approval** — always present drafts first
2. **Match the PM/LC's writing style** — study their historical notes and mirror the tone
3. **Be honest about "no change"** — don't manufacture updates when nothing happened
4. **Prioritize Red > Amber > Green** — present in order of urgency
5. **Show your sources** — for each note, the PM/LC should be able to see what data informed the draft
6. **Handle the full portfolio** — even if a PM/LC has 20 clients, draft notes for all of them in one pass
7. **Remember context** — reference what happened last week when it's relevant (e.g., "Still waiting on client response since last week's email")
8. **Respect overrides** — if the PM/LC edited a note last week, don't overwrite their language this week. Build on it.
