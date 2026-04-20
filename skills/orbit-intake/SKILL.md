---
name: orbit-intake
description: "Create customized Asana project plans for new ndMAX implementation clients. Use this skill when someone says 'new client', 'new project assigned', 'add client to my portfolio', 'taking over a client', 'new intake', 'client intake for [name]', 'create project for [name]', or any indication of a new client being assigned. Also use when someone says 'generate project plan for [client]' or 'build tasks for [client]'. This is the AI template builder that replaces GuideCX's rigid project templates — it creates customized task sets based on actual client information from sales data, handoff calls, and planning meetings. Trigger aggressively: any mention of onboarding a new client should invoke this skill."
---

# Orbit Intake — The AI Template Builder

## Overview

The intake skill replaces GuideCX's rigid project templates. Instead of forcing every client into the same cookie-cutter plan, it generates a customized Asana project with tasks tailored to each client's specific situation: their products purchased, firm size, DM status, practice areas, and AI familiarity.

## The Three-Stage Process

Intake is progressive. The project gets smarter with each stage:

| Stage | Trigger | Data source | Output |
|-------|---------|-------------|--------|
| Stage 1: First draft | "New client: [Name]" | Sales win email, Salesforce data, Gainsight | Asana project skeleton with estimated tasks |
| Stage 2: Refinement | "Refine project after handoff call" | Sales handoff call transcript (Teams/Copilot) | Updated tasks based on specific discussions |
| Stage 3: Finalization | "Finalize project after intro call" | Intro/planning call transcript | Final tasks, assignments, custom field values |

The PM/LC can run all three stages sequentially or skip directly to any stage if they have enough information.

## Stage 1: First Draft (from sales data)

### Step 1: Search for client information

```
Search Outlook for:
  - Win notification email (search: "[Client Name] win" or "[Client Name] closed won")
  - Sales handoff email (search: "[Client Name] handoff" or "[Client Name] introduction")
  - Any prior correspondence with client contacts

Search Gainsight/Staircase for:
  - Client health data
  - Any pre-existing relationship data
  - Contract details (ARR, products, dates)

Search Asana for:
  - Verify no existing project for this client
  - Check if client appears in any other projects
```

### Step 2: Extract client profile

From gathered data, build a client profile:

```
CLIENT PROFILE TEMPLATE:

Firm/Company name: [extracted]
Location: [country/city]
Firm size (users): [estimated from contract]
Practice areas: [if known]
ARR / Cash value: [from contract]
Products purchased: [from contract — ndMAX, Legal AI Assistant, Studio Apps, AI Profiling, etc.]
DM implementation status: [from Salesforce/Gainsight]
DM expected go-live: [if available]
Client champion: [from sales contacts]
Champion email: [from sales contacts]
Executive sponsor: [if mentioned]
Key stakeholders: [if mentioned]
AI familiarity: [if mentioned in sales notes — high/medium/low/unknown]
Special considerations: [anything notable — language, timezone, regulatory, etc.]
```

### Step 3: Generate project structure

Using the client profile, generate an Asana project with the five fixed milestone sections. The task content varies based on the profile.

#### Milestone 1: Kickoff & Readiness (always included)

Standard tasks (always present):
- Sales handoff call reviewed
- Kickoff meeting scheduled
- Kickoff meeting held
- Kickoff recap email sent
- AI Readiness Assessment sent
- AI Readiness Assessment completed
- Project team confirmed

Conditional tasks:
- IF DM not yet live → "Monitor DM implementation — go-live expected [date]"
- IF firm size > 200 → "Identify pilot group for phased rollout"
- IF multiple practice areas → "Map practice area representatives for workshops"
- IF international client → "Confirm timezone and language preferences"

#### Milestone 2: Legal AI Assistant Rollout (if purchased)

Standard tasks:
- Legal AI Assistant enabled in environment
- Training format confirmed (live / eLearning / both)
- Assistant training session delivered
- Prompt library customized and shared
- 2-week adoption check-in

Conditional tasks:
- IF pilot approach → "Define pilot group" + "Pilot feedback review" + "Firm-wide rollout decision"
- IF firm-wide approach → "All-hands enablement session" + "Department-specific follow-ups"
- IF firm size > 500 → "Train-the-trainer session for internal champions"
- IF AI familiarity = low → "Change management planning session" + "FAQ document prepared"

#### Milestone 3: Studio Apps Deployment (if purchased)

Standard tasks:
- Studio Apps catalog walkthrough
- Client identifies priority apps (3-5)
- Selected apps imported into environment
- App configuration working session
- App pilot testing with real documents
- Feedback review and customization
- Firm-wide app rollout

Conditional tasks:
- IF specific use cases identified in sales → "Configure [specific app name]" for each
- IF custom app needed → "Custom app requirements gathering" + "Custom app build" + "Custom app testing"
- IF multiple practice groups → separate rollout tasks per practice group

#### Milestone 4: AI Profiling (if purchased)

Standard tasks:
- AI Profiling scope and taxonomy discussed
- Profiling champion assigned by client
- Taxonomy approach confirmed (existing / adapt / build new)
- Document volume estimate confirmed
- Configuration sessions (4-6 week cycle)
- Structured sample validation
- Profiling go-live

Conditional tasks:
- IF existing taxonomy → "Review and map existing taxonomy"
- IF new taxonomy → "Taxonomy design workshop" + "Taxonomy approval from client"
- IF document volume > 50K → "Phased profiling approach planned"
- IF multiple document types → separate configuration tasks per document type

#### Milestone 5: Hypercare & Closeout (always included)

Standard tasks:
- Hypercare kickoff — weekly cadence established
- Week 1 check-in
- Week 2 check-in
- Week 3 check-in
- Adoption metrics review
- Closeout and handoff meeting
- Project closed in Asana

Conditional tasks:
- IF value engineering handoff planned → "Value Engineering transition meeting"
- IF renewal within 6 months → "Renewal preparation — document ROI and value delivered"

### Step 4: Set custom fields

```
Asana custom fields to set:

RAG Status: Green (new projects start green)
PM/LC: [current user]
Engineer: [TBD or assigned if known]
Value Engineer: [TBD]
ARR / Cash Value: [from contract]
Cash Bucket: [computed from ARR]
Start Quarter: [current quarter]
GCX Status: N/A (new project)
Current Milestone: Kickoff
DM Implementation Phase: [from Salesforce data]
DM Expected Go-Live: [if available]
Products Purchased: [from contract]
Client Location: [from profile]
Client Champion: [from profile]
Champion Email: [from profile]
Engagement Velocity: Active (new project)
```

### Step 5: Present for review

Use the `Asana:create_project_preview` tool to show the PM/LC the complete project structure before creating it. The preview should include all sections, tasks, assignments, and dates.

```
PRESENT TO USER:

"Here's the draft project for [Client Name] based on [data sources used].
I've created [N] tasks across [N] milestones based on:
- Products: [list]
- Firm size: [N] users
- DM status: [status]
- Special considerations: [any]

Please review and edit before I create this in Asana.
[Asana project preview widget]

Things I wasn't sure about:
- [List any assumptions or gaps]
- [Questions for the PM/LC to answer]"
```

## Stage 2: Refinement (after handoff call)

Triggered by: "Refine project after handoff call" or "Update [Client] from handoff notes"

### Process:
1. Search Teams/Copilot for the handoff call transcript
2. Extract specific details discussed:
   - Client priorities and pain points
   - Specific use cases mentioned
   - Timeline expectations
   - Stakeholder names and roles
   - Technical environment details
   - Any concerns or blockers raised
3. Update existing Asana project:
   - Add tasks for specific use cases discussed
   - Remove tasks for products/features not in scope
   - Adjust priorities based on client's stated priorities
   - Update custom fields with confirmed information
4. Present changes to PM/LC for approval

## Stage 3: Finalization (after intro/planning call)

Triggered by: "Finalize project after intro call" or "Update [Client] from planning call"

### Process:
1. Search for intro/planning call transcript
2. Extract finalized details:
   - Confirmed project team (executive sponsor, champions, stakeholders)
   - Agreed timeline and workshop schedule
   - Confirmed training format preferences
   - Studio App shortlist
   - AI Profiling scope decisions
   - Any client commitments (assessment timeline, champion assignment, etc.)
3. Finalize Asana project:
   - Set task assignments (PM/LC vs. Engineer tasks)
   - Set date ranges on tasks based on agreed timeline
   - Update all custom fields to confirmed values
   - Create calendar holds for scheduled sessions
4. Present final version for PM/LC approval
5. Once approved, the project is officially live

## Migration Mode

When migrating from GuideCX, the intake skill operates differently:

Triggered by: "Migrate [Client] from GCX" or "Import GCX data for [Client]"

### Process:
1. Read the GCX data for this client (from the exported JSON/HTML)
2. Create Asana project with:
   - Current GCX status → GCX Status custom field
   - Current GCX RAG → RAG Status custom field
   - Current Project Status narrative → first status update note
   - All mapped fields from the GCX export
3. Determine current milestone based on the status narrative:
   - Keywords like "kickoff", "readiness", "survey" → Milestone 1
   - Keywords like "assistant", "training", "enablement" → Milestone 2
   - Keywords like "studio", "apps", "import", "configure" → Milestone 3
   - Keywords like "profiling", "taxonomy", "metadata" → Milestone 4
   - Keywords like "hypercare", "closeout", "handoff" → Milestone 5
4. Generate appropriate remaining tasks for the current phase
5. Mark previous milestone tasks as complete based on status narrative
6. Present for PM/LC review before creating

## Knowledge Base Reference

The intake skill should reference these documents for implementation methodology:
- `ndMAX_Welcome_Packet.pdf` — Roles, best practices, success criteria
- `ndMAX_Kickoff_Deck_v3_1.pptx` — Kickoff structure, questions to ask per phase
- `Kickoff_Recap_Email_Template.docx` — Email format and Copilot prompt

## Behavioral Rules

1. **Never create a project without PM/LC review** — always present the preview first
2. **Start Green** — all new projects begin with Green RAG status
3. **Be transparent about data gaps** — clearly list what you couldn't find and what you assumed
4. **Customize aggressively** — the whole point is that no two projects look alike. Use every signal available to tailor the task set.
5. **Keep milestone sections fixed** — the five sections never change (Power BI depends on them). Only the tasks inside vary.
6. **Date ranges, not deadlines** — set start/due date ranges on tasks for timeline visibility, but don't create artificial urgency. Dates are planning tools, not enforcement mechanisms.
7. **Include the client's language** — if specific use cases, app names, or workflows were mentioned, use those exact words in task names so the PM/LC recognizes them.
