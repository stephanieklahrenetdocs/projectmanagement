---
name: orbit-kickoff
description: "Generate all kickoff deliverables for ndMAX implementation clients. Use this skill when someone says 'generate kickoff materials', 'kickoff assistant', 'draft kickoff recap email', 'post-meeting email', 'prep for kickoff', 'kickoff deck for [client]', or any request related to preparing or following up from a kickoff meeting. Also triggered by 'here are the meeting notes' after a kickoff call, or 'write the recap' after any client meeting. This skill produces: customized kickoff deck, recap email with AI-extracted action items, and welcome packet. Use proactively when orbit-navigator identifies a client approaching the kickoff milestone."
---

# Orbit Kickoff — The Kickoff Assistant

## Overview

The kickoff assistant handles all deliverables around the ndMAX kickoff meeting — the most important milestone in the implementation. It can produce materials before the call (deck prep) and after the call (recap email, action items). It knows the ndMAX methodology deeply and uses meeting data to generate precise, client-specific follow-ups.

## Capabilities

| Mode | Trigger | Output |
|------|---------|--------|
| Pre-kickoff prep | "Prep kickoff for [Client]" | Customized deck, meeting agenda, prep notes |
| Post-kickoff recap | "Draft kickoff recap for [Client]" | Recap email with action items, updated Asana tasks |
| Post-meeting email | "Post-meeting email for [Client]" | Follow-up email for ANY meeting (not just kickoff) |
| Full kickoff package | "Generate kickoff materials for [Client]" | All of the above |

## Mode 1: Pre-Kickoff Prep

### Step 1: Load client context

From Asana project:
- Client name, products purchased, team members, DM status
- Any notes from sales handoff or intake

From Outlook:
- Prior correspondence with client contacts
- Meeting invite details (attendees, time, duration)

### Step 2: Generate customized deck notes

The kickoff deck template (`ndMAX_Kickoff_Deck_v3_1.pptx`) has placeholder slots. Generate the customization values:

```
DECK CUSTOMIZATION:

Slide 1 (Title):
  [Client Name]: [extracted from Asana project]
  [Date]: [meeting date from calendar]

Slide 3 (ND Team):
  Legal Consultant: [PM/LC name from Asana]
  Solution Design Engineer: [Engineer name from Asana]
  Program Manager: [if assigned, else "Coordination handled by your Legal Consultant"]

Slide 4 (Client Roles):
  Executive Sponsor: [from intake data or "To be confirmed on this call"]
  Champion(s): [from intake data or "To be confirmed"]
  Key Stakeholders: [from intake data or "To be confirmed"]

Slides 6-9 (Phase slides):
  Only include slides for purchased products:
  - Slide 6 (AI Readiness): Always included
  - Slide 7 (Legal AI Assistant): If "Legal AI Assistant" in products
  - Slide 8 (Studio Apps): If "Studio Apps" in products
  - Slide 9 (AI Profiling): If "AI Profiling" in products

Slide 10 (Action Items):
  Pre-populate with standard first actions based on products
```

### Step 3: Generate prep notes for PM/LC

```
KICKOFF PREP NOTES:

Client: [Name]
Date/Time: [from calendar]
Attendees: [from invite]

Products in scope: [list]
ARR: $[amount]
DM Status: [phase] — Go-live: [date if known]

Key questions to ask (from deck speaker notes):
  [Phase-specific questions extracted from deck notes section]

Things to confirm on the call:
  - Project team (executive sponsor, champion, stakeholders)
  - AI Readiness Assessment: who completes it, email or call, timeline
  - Training format preference (live, eLearning, both)
  - [If Studio Apps:] Any use cases already identified
  - [If AI Profiling:] Existing taxonomy? Dedicated champion?

Watch for:
  - [Any concerns from sales notes]
  - [DM dependency issues if DM not live]
  - [Client-specific considerations from intake]
```

## Mode 2: Post-Kickoff Recap Email

This is the primary post-meeting workflow.

### Step 1: Find the meeting recording/transcript

Search for the kickoff call data:

```
Tool: Microsoft 365 chat_message_search or outlook_email_search
Query: "[Client Name] kickoff" or "[Client Name] recording"
Date: meeting date

Also check Teams for Copilot-generated meeting notes
```

### Step 2: Extract action items by topic

Using the meeting transcript/notes, extract action items organized by the same structure as the Kickoff Recap Email Template:

```
EXTRACTION FRAMEWORK:

For each topic below, ONLY include if it was actually discussed on the call.
Do NOT include placeholder sections for topics that weren't covered.

1. PROJECT TEAM
   - Confirmed stakeholders and roles
   - Any internal alignment the client needs to do
   - Names mentioned for each role

2. AI READINESS HEALTH CHECK
   - Who will complete the assessment
   - Delivery method agreed (email or call)
   - Timeline for completion
   - Who joins the debrief

3. LEGAL AI ASSISTANT
   - Training format confirmed
   - Rollout scope (pilot or firm-wide)
   - If pilot: who is in the pilot group
   - Any blockers to enablement

4. STUDIO APPS
   - Use cases identified on the call
   - Whether client has browsed the catalog
   - Import/demo session planning
   - Who should attend training

5. AI PROFILING
   - Taxonomy approach (existing/adapt/new)
   - Estimated document volume
   - Point of contact for configuration
   - Proof of concept scope
```

### Step 3: Generate the recap email

Follow the exact format from `Kickoff_Recap_Email_Template.docx`:

```
EMAIL FORMAT:

Subject: ndMAX Kickoff Recap — [Client Name] | [Date]

Hello,

Thank you for participating in today's ndMAX Kickoff Meeting. It was great to 
bring everyone together and officially launch the project.

Here [recording link placeholder] is the recording of the call and attached 
you will find the deck shared during the session for your reference.

As a reminder, here are the action items we discussed:

[Below is a summary of next steps organized by topic.]

[TOPIC SECTIONS — only include topics that were discussed:]

**Project Team**
[2-4 sentences/bullets with specific action items, owners, and deadlines]

**AI Readiness Health Check**  
[2-4 sentences/bullets]
[Include link: AI Readiness Survey: https://aireadysurvey.netlify.app/]

**Legal AI Assistant**
[2-4 sentences/bullets]

**Studio Apps**
[2-4 sentences/bullets]
[Include link if relevant: Studio Apps catalog: https://studio.netdocuments.com/]

**AI Profiling**
[2-4 sentences/bullets]

We are looking forward to working with your team on the next steps in the 
implementation process.

Best regards,

**[PM/LC Name]**
Legal Consultant | NetDocuments AI Professional Services
```

### Step 4: Generate the email using the message_compose tool

Use the `message_compose_v1` tool to present the email in a sendable format. If there are multiple possible tones, present 1-2 variants.

### Step 5: Update Asana

After the email is approved:
- Mark "Kickoff meeting held" task as complete
- Mark "Kickoff recap email sent" task as complete (after PM/LC sends it)
- Create new tasks for any action items extracted from the call
- Update custom fields (project team names, champion, etc.)
- Set "AI Readiness Assessment sent" task due date based on agreed timeline

## Mode 3: Post-Meeting Email (any meeting)

This mode works for ANY client meeting, not just kickoffs. It follows the same extraction process but with a more flexible email format.

### Step 1: Identify the meeting

```
"Post-meeting email for [Client]"
→ Search calendar for most recent meeting with this client
→ Find Copilot notes/transcript for that meeting
```

### Step 2: Extract content

Use the same topic-based extraction, but don't limit to kickoff topics. Include whatever was discussed: app demo feedback, profiling progress, adoption review, etc.

### Step 3: Draft follow-up email

Use the post-meeting-email user skill format if available, otherwise:

```
Subject: [Meeting topic] Follow-Up — [Client Name] | [Date]

Hi [Client contacts],

Thank you for your time today. Here's a summary of what we covered and the 
next steps we agreed on.

[Topic-organized sections with action items]

[Inline resource links where relevant]

Please let me know if I missed anything or if you have questions.

Best regards,
[PM/LC Name]
```

## Deliverable Quality Standards

- **Use the client's actual names** throughout (not "your firm" or "the client")
- **Be specific about dates and owners** ("Adrian will complete the assessment by April 18" not "the assessment will be completed soon")
- **Include links inline** where discussed (AI Readiness Survey, Studio Apps catalog, recording link)
- **Professional but warm tone** — direct, no filler phrases, ready to send as-is
- **Don't include sections for undiscussed topics** — this is the most important quality signal. If AI Profiling wasn't mentioned, don't add a boilerplate section about it.

## Behavioral Rules

1. **Meeting data is essential** — if no transcript/notes are available, ask the PM/LC to summarize what was discussed rather than guessing
2. **Present the email before sending** — always use message_compose for review
3. **Include the deck and welcome packet** — remind the PM/LC to attach these files
4. **Update Asana automatically** — after the email is sent, update the relevant tasks and custom fields
5. **Remember this client's context** — reference prior conversations and specific details from intake
6. **One email per meeting** — don't batch multiple meetings into one email
