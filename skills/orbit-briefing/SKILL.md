---
name: orbit-briefing
description: "Generate a prioritized daily action plan for ndMAX implementation projects. Use this skill whenever someone says 'morning briefing', 'good morning', 'what should I work on today', 'daily plan', 'briefing', 'my priorities', 'what's urgent', 'show me my clients', or any request to see their project portfolio status. Also triggered by 'what needs attention', 'any fires today', 'catch me up'. This skill pulls live data from Asana, Outlook, Slack, and Gainsight to produce a role-specific prioritized action plan. Use this skill proactively when a team member starts their day or asks about their workload."
---

# Orbit Briefing — The Morning Ritual

## Overview

The morning briefing is the primary daily touchpoint between a team member and Orbit. It synthesizes data from all connected sources into a prioritized, actionable plan for the day. The output adapts based on the user's role (PM/LC, Engineer, Value Engineer, or Manager).

## Prerequisites

Before generating the briefing, call `orbit-sync` for a targeted sync of the user's portfolio. If sync was run within the last 2 hours, skip it and use cached Asana data.

## Step 1: Identify the user and their role

```
Tool: Asana get_user (user_id = "me")
Result: Name, email, GID

Role determination:
  - Match email against known team members (see reference below)
  - If PM/LC: show portfolio view
  - If Engineer: show task-centric view
  - If Manager (Tim Lutero or leadership): show team-wide view
  - If unclear: ask the user which view they prefer
```

### Team member reference

| Name | Email | Role |
|------|-------|------|
| Stephanie Klahre | stephanie.klahre@netdocuments.com | PM/LC |
| Christopher Snead | (confirm) | PM/LC |
| Tim Lutero | (confirm) | PM/LC + Manager |
| Staci VanderPol | (confirm) | PM/LC |
| Amir Mustafa | (confirm) | PM/LC |
| Greg Hartley | (confirm) | Engineer |
| Nikki Patel | (confirm) | Engineer |
| Adam Scott | (confirm) | Engineer |
| Brandon Hill | (confirm) | Engineer |
| Andrew Mecham | (confirm) | Engineer |
| Emilio Campos | (confirm) | Engineer |
| David Kero | (confirm) | Engineer |
| Tyler Graf | (confirm) | Engineer |
| Kyle Kissell | (confirm) | Value Engineer |

## Step 2: Pull portfolio data from Asana

### For PM/LC role:
```
Tool: Asana search_tasks_preview or get_projects
Filter: team = ND Implementations, PM/LC custom field = current user
Fields needed: project name, RAG status, current milestone, engagement velocity,
               ARR, last activity date, engineer assigned, upcoming tasks
```

### For Engineer role:
```
Tool: Asana get_tasks
Filter: assignee = current user, completed = false
Group by: project (client)
Fields needed: task name, due date, project name, section (milestone)
```

### For Manager role:
```
Tool: Asana get_projects
Filter: team = ND Implementations (all projects)
Fields needed: all custom fields, grouped by PM/LC
```

## Step 3: Pull today's calendar

```
Tool: Microsoft 365 outlook_calendar_search
Filter: today's date
Extract: meeting title, time, attendees, client connection
```

For each meeting that involves a client:
- Pull the client's Asana project context
- Check for recent emails/Slack threads about the meeting topic
- Prepare context notes (last status, open items, what to discuss)

## Step 4: Check for urgent items

Scan for items requiring immediate attention:

```
URGENCY SCORING:

Priority 1 — Fires (address now):
  - Client sent email marked urgent/high priority
  - RAG status is Red AND velocity is Stalled or Silent
  - Meeting today with no prep done
  - Task overdue by 7+ days with client waiting

Priority 2 — This week (address today):
  - Unread client email older than 48 hours
  - Task due this week
  - Engagement velocity changed to Slowing
  - Gainsight flagged risk signal

Priority 3 — Monitor (be aware):
  - Projects approaching milestone transition
  - DM go-live dates in next 14 days
  - Clients with no activity in 10-14 days
  - Renewal dates approaching (from ARR data)

Priority 4 — On track (no action needed):
  - Active velocity, tasks progressing, client engaged
```

## Step 5: Compute priority ranking

For each client in the portfolio, compute a priority score:

```
PRIORITY SCORE = (urgency_weight × 0.40) + (arr_weight × 0.30) + (velocity_weight × 0.30)

urgency_weight:
  Priority 1 items present → 1.0
  Priority 2 items present → 0.7
  Priority 3 items present → 0.4
  Priority 4 only → 0.1

arr_weight (normalized):
  Over $100K → 1.0
  $50-100K → 0.7
  $10-50K → 0.4
  Under $10K → 0.2

velocity_weight:
  Silent → 1.0
  Stalled → 0.8
  Slowing → 0.5
  Active → 0.1
```

## Step 6: Generate the briefing output

### PM/LC Briefing Format

Render as an interactive Claude artifact (React component) with these sections:

```
BRIEFING STRUCTURE:

1. HEADER
   Good morning, [Name]. Here's your Orbit briefing for [date].
   Portfolio: [N] active clients | [N] 🔴 | [N] 🟡 | [N] 🟢
   Total ARR under management: $[amount]

2. 🔥 FIRES (Priority 1)
   [For each fire:]
   [RAG emoji] [Client Name] — [one-line issue]
   Action: [specific action to take]
   [Button: "Draft email to [client]" → sendPrompt]
   [Button: "Open in Asana" → link]

3. 📅 TODAY'S MEETINGS
   [For each meeting:]
   [Time] — [Client Name]: [meeting title]
   Context: [2-3 sentence prep summary]
   Open items: [what to discuss]
   [Button: "Prep for this meeting" → sendPrompt]

4. 📋 THIS WEEK'S ACTIONS
   [Sorted by priority score, top 10:]
   [RAG emoji] [Client Name] — [task/action]
   Due: [date] | ARR: $[amount] | Velocity: [status]
   [Button: "Help me advance this" → sendPrompt("Help me advance [Client]")]

5. 🔇 SILENT CLIENTS (no activity 14+ days)
   [For each silent client:]
   [Client Name] — last activity [N] days ago ([source])
   Suggested: [re-engagement action]
   [Button: "Draft re-engagement email" → sendPrompt]

6. 📈 MILESTONE TRANSITIONS (next 2 weeks)
   [Clients approaching phase changes:]
   [Client Name]: [current phase] → [next phase]
   Remaining items: [count] | Blockers: [if any]

7. QUICK ACTIONS (bottom bar)
   [Button: "Refresh priorities ↗"]
   [Button: "Friday GCX updates ↗"]
   [Button: "Find silent clients ↗"]
   [Button: "Sync all projects ↗"]
```

### Engineer Briefing Format

```
ENGINEER BRIEFING:

1. HEADER
   Good morning, [Name]. You have [N] active tasks across [N] clients.

2. 🔧 TASKS NEEDING ATTENTION
   [Grouped by urgency:]
   [Client Name] — [Task name]
   Milestone: [section] | Due: [date] | PM/LC: [name]
   Context: [what the PM/LC needs from you]

3. 📅 TODAY'S MEETINGS
   [Same format as PM/LC]

4. 📊 WORKLOAD OVERVIEW
   Active tasks: [N]
   Due this week: [N]
   Blocked/waiting: [N]
```

### Manager Briefing Format

```
MANAGER BRIEFING:

1. HEADER
   Portfolio overview for [date]
   Total projects: [N] | ARR: $[total]
   🔴 [N] Red | 🟡 [N] Amber | 🟢 [N] Green

2. 🚨 ESCALATIONS
   [Projects needing management attention:]
   [Client] — PM/LC: [name] — Issue: [description]
   Recommended action: [suggestion]

3. 👥 TEAM WORKLOAD
   [For each PM/LC:]
   [Name]: [N] clients | [N]🔴 [N]🟡 [N]🟢 | ARR: $[amount]
   Capacity note: [overloaded/balanced/available]

4. 📊 PORTFOLIO HEALTH TRENDS
   RAG changes this week: [list]
   Velocity changes: [list]
   DM go-lives approaching: [list]

5. 💰 TOP 10 BY ARR
   [Table: Client, PM/LC, Engineer, ARR, RAG, Status]
```

## Behavioral Rules

1. **Keep it scannable** — the briefing should take 60 seconds to read. Details are available via the sendPrompt buttons.
2. **Lead with action** — every item should have a clear "what to do next."
3. **Show data sources** — when surfacing information, note where it came from (email, Slack, Gainsight).
4. **Don't overwhelm** — cap the "This Week's Actions" to top 10 items. Full list available on demand.
5. **Respect the role** — engineers don't need to see ARR data. Managers don't need task-level detail.
6. **Cache the briefing** — if the user asks "show me my briefing again" within 2 hours, regenerate the artifact from the same data (don't re-sync).
7. **Time-aware greetings** — "Good morning" before noon, "Good afternoon" 12-5pm, "Good evening" after 5pm.
8. **Interactive by default** — always render as a Claude artifact with clickable buttons, not as plain text. Each client row should be expandable for detail.
