---
name: orbit-sync
description: "Synchronize ndMAX implementation project data across all connected systems. Use this skill whenever someone says 'sync my projects', 'update orbit', 'pull latest data', 'refresh my portfolio', or any request to update project information from external sources. Also triggered automatically by orbit-briefing and orbit-weekly-notes. This skill reads from Outlook, Slack, Gainsight, and Teams via MCP connectors and writes normalized updates to Asana projects. Use this even for partial syncs like 'check emails for Wiggin and Dana' or 'update RAG for my clients'."
---

# Orbit Sync — The Nervous System

## Overview

Orbit Sync is the data synchronization layer for the ndMAX Orbit project management system. It reads data from external sources (Outlook, Slack, Gainsight, Teams/Copilot) and writes normalized updates to Asana, which serves as the central project database.

## MCP Connectors

| Source | MCP Server URL | Primary data |
|--------|---------------|--------------|
| Asana | `mcp.asana.com/v2/mcp` | Projects, tasks, custom fields, status updates |
| Outlook / M365 | `microsoft365.mcp.claude.com/mcp` | Client emails, calendar, meeting invites |
| Slack | `mcp.slack.com/mcp` | Team channels, DMs, threads about clients |
| Gainsight | `mcp.staircase.ai/mcp` | Health scores, sentiment, risk signals |
| Teams/Copilot | `microsoft365.mcp.claude.com/mcp` | Meeting transcripts, Copilot summaries |

## Asana Workspace Reference

- **Workspace GID**: `1148806218142272` (NetDocuments)
- **Team GID**: `1204685785059509` (ND Implementations)
- **Project naming**: `[RAG emoji] Client Name — ndMAX Implementation`
- **RAG emojis**: 🔴 Red | 🟡 Amber | 🟢 Green

## When This Skill Runs

### Full sync (all sources → Asana)
Triggered by: "sync my projects", "update orbit", "pull latest data"

### Targeted sync (single client)
Triggered by: "sync [Client Name]", "check latest on [Client]", "update [Client]"

### Source-specific sync
Triggered by: "check my emails for client updates", "pull Gainsight scores", "check Slack for [Client]"

### Automatic (called by other skills)
- `orbit-briefing` calls sync before generating the morning plan
- `orbit-weekly-notes` calls sync before drafting Friday updates

## Sync Workflow

### Step 1: Identify scope

Determine which clients to sync:
- **Full sync**: Query Asana for all projects in the ND Implementations team where the PM/LC custom field matches the current user
- **Targeted sync**: Search Asana for the specific client project by name
- **Manager sync**: Query all projects (no PM/LC filter)

```
Tool: Asana search_objects or get_projects
Filter: team = 1204685785059509
```

### Step 2: For each client project, pull external data

#### 2a. Outlook email scan

Search Outlook for emails matching the client name OR client champion email within the last 14 days.

```
Tool: Microsoft 365 outlook_email_search
Query: client name OR champion email
Date range: last 14 days
```

Extract from results:
- **Last email date** → update `Last Activity Date` custom field
- **Unread emails from client** → flag as action items
- **Action items mentioned in emails** → surface in briefing
- **Sentiment signals** → (urgent language, delays mentioned, positive feedback)

#### 2b. Outlook calendar scan

Search calendar for upcoming meetings with client contacts.

```
Tool: Microsoft 365 outlook_calendar_search
Query: client name
Date range: today + 14 days forward
```

Extract:
- **Upcoming meetings** → include in briefing context
- **Recent meetings (past 7 days)** → check for Copilot notes

#### 2c. Slack scan

Search Slack for messages mentioning the client in team channels.

```
Tool: Slack slack_search_public_and_private
Query: client name
```

Extract:
- **Team discussions about client** → capture decisions, blockers, updates
- **Engineer updates** → technical progress on apps, profiling, etc.
- **Mentions of client issues** → flag for attention

#### 2d. Gainsight / Staircase AI scan

Query Gainsight for client health data.

```
Tool: Gainsight staircase_query
Query: "health score and risk signals for [Client Name]"
```

Extract:
- **Health score** → inform RAG recommendation
- **Sentiment trend** → rising/falling/stable
- **Risk signals** → churn risk, disengagement indicators

#### 2e. Teams / Copilot meeting notes

For any meetings in the past 7 days, check for Copilot-generated summaries.

```
Tool: Microsoft 365 chat_message_search or read_resource
Query: meeting recap for [Client Name]
```

Extract:
- **Action items from meetings** → create/update Asana tasks
- **Decisions made** → include in status notes
- **Client commitments** → track in project

### Step 3: Compute engagement velocity

Using the data gathered, compute the engagement velocity for each client:

```
VELOCITY ALGORITHM:

Inputs:
  days_since_last_client_email = today - last email FROM client
  days_since_last_meeting = today - last meeting WITH client
  tasks_completed_14d = count of tasks completed in trailing 14 days
  gainsight_trend = rising | stable | falling

Rules (evaluated in order, first match wins):
  IF days_since_last_client_email > 30 AND days_since_last_meeting > 30:
    velocity = "Silent"
  
  IF days_since_last_client_email > 14 AND days_since_last_meeting > 21:
    velocity = "Stalled"
  
  IF days_since_last_client_email > 8 OR days_since_last_meeting > 14:
    velocity = "Slowing"
  
  ELSE:
    velocity = "Active"

  # Gainsight override: if health is critically low, escalate one level
  IF gainsight_trend == "falling" AND velocity != "Silent":
    velocity = escalate_one_level(velocity)
```

### Step 4: Compute RAG recommendation

Based on all gathered data, recommend a RAG status:

```
RAG RECOMMENDATION ALGORITHM:

RED conditions (any one triggers Red):
  - Engagement velocity = "Silent" for 30+ days
  - Client explicitly expressed dissatisfaction
  - Gainsight health score critically low
  - Project blocked with no workaround for 21+ days
  - Client mentioned churn or non-renewal

AMBER conditions (any one triggers Amber):
  - Engagement velocity = "Stalled"
  - Project is more than 4 weeks behind expected milestone pace
  - Key dependency blocked (e.g., DM not live, access issues)
  - Client engagement declining (was Active, now Slowing)
  - Gainsight sentiment trend falling

GREEN conditions (default when no Red/Amber triggers):
  - Engagement velocity = "Active" or "Slowing" with recent progress
  - Tasks completing at expected pace
  - Client responsive and engaged
  - No blocking issues
```

### Step 5: Write updates to Asana

For each client project, update the following:

```
Custom field updates:
  - Last Activity Date → most recent client interaction date
  - Engagement Velocity → computed velocity
  - RAG Status → ONLY if sync is in "recommend" mode (user confirms changes)

Task updates:
  - Mark tasks complete if evidence shows they're done
  - Add new tasks for action items discovered in emails/meetings
  - Update task descriptions with latest context

Status note (if significant changes found):
  - Draft a brief status note summarizing what changed since last sync
  - Store as Asana project status update (draft, not published)
```

### Step 6: Report sync results

Present a summary to the user:

```
SYNC SUMMARY FORMAT:

📊 Orbit Sync Complete — [date] [time]
Sources checked: Outlook ✓ | Slack ✓ | Gainsight ✓ | Teams ✓

[For each client with changes:]
  [RAG emoji] Client Name
    Last activity: [date] ([source])
    Velocity: [status] [→ change if different]
    Changes found: [brief description]
    [If RAG recommendation differs from current:]
      ⚠️ RAG recommendation: [current] → [recommended] — [reason]

[Summary stats:]
  Clients synced: N
  Updates written: N
  RAG changes recommended: N
  Action items found: N
```

## Error Handling

- If a source is unavailable (MCP connector not responding), skip it and note in the summary
- Never overwrite Asana data with empty/null values from a failed source query
- If Asana write fails, report the error and retry once
- Always show the user what was found BEFORE writing any RAG status changes

## Important Behavioral Rules

1. **Never auto-change RAG status** without user confirmation. Always present recommendations and let the PM/LC approve.
2. **Respect data freshness** — if Asana data is newer than what we found externally, keep the Asana data.
3. **Attribute sources** — always note where data came from (email, Slack, Gainsight, meeting notes).
4. **Degrade gracefully** — if only 2 of 4 sources respond, sync what we can and note the gaps.
5. **Rate limit awareness** — when syncing a full portfolio (15+ clients), batch external queries and pause between batches to avoid MCP rate limits.
