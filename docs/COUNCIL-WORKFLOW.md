# Council Workflow — Strategic Ideation

**Status:** Design Complete — Ready for Implementation
**Created:** 2026-02-22
**Purpose:** Upstream ideation layer that surfaces new ideas and refinements, funneling approved concepts into the existing Feature Workflow.

---

## Overview

The Council Workflow is an **async ideation layer** that runs on a schedule and feeds approved ideas into the existing Feature Workflow. It does not replace any existing workflow — it adds an upstream stage.

```
Council Workflow (ideation)
        ↓ (approved idea becomes a Feature Issue)
Feature Workflow (definition + spec)
        ↓
User Story Workflow (implementation)
```

### Agents

| Agent | Schedule | Role |
|-------|----------|------|
| Researcher | Daily (8am) | Looks outward — new financial models, competitor gaps, market research, alternative data sources |
| Designer (Council) | Daily (9am) | Looks inward — UX refinements, design debt, interaction improvements |
| Engineer (Council) | Daily (10:30am) | Looks inward — core functionality, algorithms, AI data feed quality, technical debt |
| CEO | Weekly (Monday 10am) | Reads all council inputs, approves or dismisses ideas |
| PM (Council) | Weekly (Monday 11am, after CEO) | Translates CEO-approved ideas into Feature Issues with proper context |

> **Important:** Council modes are separate from Implementation modes. `/work-designer-council` ≠ `/work-designer`. `/work-engineer-council` ≠ `/work-engineer`. Different schedules, different goals.

---

## GitHub Discussions Structure

### Categories

Three categories in GitHub Discussions (Settings → Discussions):

| Category | Purpose | Who Posts |
|----------|---------|-----------|
| **Research** | New opportunities — models, data sources, market insights, transformative ideas | Researcher |
| **Refinements** | UX improvements — design debt, interaction gaps, product polish | Designer |
| **Technical** | Engineering improvements — algorithm quality, AI data feed gaps, core functionality, technical debt | Engineer Council |

### State Machine

State is tracked via **structured comment prefixes** in the discussion thread. This avoids complex GraphQL label mutations and creates a clear audit trail.

```
[Researcher/Designer/Engineer creates Discussion]
         │
         ▼
   OPEN, no CEO decision comment
   → Pending CEO review
         │
         ▼ (CEO weekly run)
    ┌────┴────────────────────┐
    │                         │
APPROVED                DISMISSED            NEEDS-MORE-INFO
    │                         │                     │
CEO posts:              CEO posts:            CEO posts:
"## CEO Decision:       "## CEO Decision:     "## CEO Decision:
APPROVED"               DISMISSED"            NEEDS-MORE-INFO"
Discussion stays OPEN.  CEO closes            Discussion stays OPEN.
    │                   discussion.               │
    ▼                                             ▼ (Researcher/Designer/Engineer daily run)
PM runs (after CEO):                     Agent posts follow-up
Finds open discussions                   research/response
with APPROVED comment,                         │
no "PM: Feature issue                          ▼ (CEO next weekly run)
created" comment.                     CEO makes final APPROVED or
    │                                 DISMISSED decision.
    ▼                                 (Max 2 NEEDS-MORE-INFO cycles;
PM creates Feature Issue              then escalate to human.)
PM comments:
"PM: Feature issue #X created."
PM closes discussion.
```

### Valid Discussion States

| State | Description | Who Acts Next |
|-------|-------------|---------------|
| Open, no CEO comment | New idea, pending review | CEO (weekly) |
| Open, `## CEO Decision: APPROVED` | Approved, awaiting feature creation | PM (weekly, same day as CEO) |
| Open, `## CEO Decision: NEEDS-MORE-INFO` | CEO asked a question | Researcher, Designer, or Engineer Council (next daily run) |
| Closed by CEO | Dismissed, reason in comment | Nobody — done |
| Closed by PM | Feature created, link in comment | Nobody — continues in Feature Workflow |

---

## Agent Responsibilities

### Researcher (Daily)

**Goal:** Surface new opportunities from outside the product.

**Research domains for SignalTrackers:**
- New macroeconomic models or factor models accessible to retail investors
- Alternative data sources (sentiment, positioning, flows, earnings call NLP)
- Gaps in existing financial dashboard products (competitors)
- Academic papers on market signal methodology
- User complaints about financial tools on Reddit, Twitter, forums
- Emerging AI/ML approaches to market analysis

**Each run:**
1. Read `~/.claude/projects/financial/roles/researcher-context.md`
2. **First priority:** Check for open Discussions with `## CEO Decision: NEEDS-MORE-INFO` — answer any outstanding questions before researching new topics
3. **Second priority:** Research 1–2 new topics using web search
4. Before posting, search open Research discussions for similar topics (no duplicates)
5. Post findings as a new Discussion in the **Research** category
6. Update context file: topics covered, date, what was posted

**Discussion post format:**
```
## Summary
[2-3 sentence summary of the finding]

## Why This Matters for SignalTrackers
[Specific relevance to our product and users]

## Evidence
[Links, quotes, data points supporting this]

## Suggested Direction
[What we might do with this — not a prescription, a starting point for CEO]

---
*Posted by Researcher on [date]*
```

---

### Designer — Council Mode (Daily)

**Goal:** Surface UX debt, interaction improvements, and design system gaps based on observing the current product.

**Each run:**
1. Read `~/.claude/projects/financial/roles/ui-designer-context.md`
2. **First priority:** Check for open Discussions with `## CEO Decision: NEEDS-MORE-INFO` addressed to Designer
3. **Second priority:** Review recent design review work and implementation patterns. Identify 1 refinement worth raising.
4. Before posting, check open Refinements discussions to avoid duplicates
5. If a meaningful refinement is found, post to **Refinements** category
6. Update context file

> **Rate limit yourself:** Only post if there's something genuinely worth the CEO's attention. Do not post for the sake of posting. Aim for 2–4 posts per week, not daily.

**Discussion post format:**
```
## Problem
[What is currently wrong or suboptimal — be specific]

## User Impact
[How this affects the user experience]

## Proposed Direction
[What improvement looks like — rough, not a full spec]

## Effort Estimate
[Quick win / Medium / Large]

---
*Posted by Designer on [date]*
```

---

### Engineer — Council Mode (Daily — 10:30am)

**Goal:** Look inward at the application's core functionality — algorithmic correctness, data pipeline health, how data is fed to AI systems, and technical debt.

**Review domains** (rotate — one per session):
- **AI Briefing Data Feed** — Are all metrics and calculations included in briefing inputs? Are new additions reflected?
- **AI Chatbot Tool Coverage** — Does the chatbot's tool set expose all available data?
- **AI Prompt Quality** — Are system prompts and data formatting well-optimized for AI output quality?
- **Algorithm & Calculation Correctness** — Are core calculations (regime engine, divergence gap, market signals) sound?
- **Data Pipeline Reliability** — Is `market_signals.py` handling errors and stale data correctly?
- **Technical Debt** — Is there meaningful duplication or fragility accumulating in core code?

**Each run:**
1. Read `~/.claude/projects/financial/roles/engineer-council-context.md`
2. **First priority:** Check for open Technical discussions with `## CEO Decision: NEEDS-MORE-INFO`
3. **Second priority:** Pick one review domain, investigate by reading relevant source files
4. Before posting, check open Technical discussions and open GitHub issues for duplicates
5. If a meaningful finding is found, post to **Technical** category
6. Update context file: domain reviewed, date, what was posted

> **Rate limit yourself:** Only post if there's something genuinely worth the CEO's attention. Aim for 2–4 posts per week, not daily.

**Discussion post format:**
```
## Problem
[What is currently wrong, missing, or suboptimal — reference specific files]

## Impact
[Effect on AI output quality, reliability, maintainability, or user experience]

## Evidence
[Specific observations from reading the code]

## Proposed Direction
[What a fix looks like — rough direction, not a full spec]

## Effort Estimate
[Quick win / Medium / Large]

---
*Posted by Engineer Council on [date]*
```

---

### CEO (Weekly — Monday)

**Goal:** Read all pending council inputs, make strategic go/no-go decisions, maintain product direction.

**Each run:**
1. Read `~/.claude/projects/financial/roles/ceo-context.md`
2. Read `docs/PRODUCT_ROADMAP.md` for current strategy
3. Fetch open issue titles (`gh issue list --state open --json number,title`) for backlog awareness
4. Process all open Discussions with no CEO decision comment:
   - Research category discussions
   - Refinements category discussions
   - Technical category discussions
5. For each unreviewed discussion, post one of three structured decisions (see formats below)
6. Update context file: key decisions made, dismissed directions, strategic priorities

**APPROVED format:**
```
## CEO Decision: APPROVED

This aligns with our direction because [reason].

PM: Please create a feature issue for "[working title]".
- Suggested milestone: [milestone]
- Priority: [P0/P1/P2/P3]
- Key outcome to achieve: [one sentence]
```

**DISMISSED format:**
```
## CEO Decision: DISMISSED

Not pursuing this. Reason: [one of: out of scope / timing / already covered by #X / low ROI / strategic conflict]

[Optional: what would change this decision]
```

**NEEDS-MORE-INFO format:**
```
## CEO Decision: NEEDS-MORE-INFO

Before deciding, I need to understand: [specific question]

[Researcher/Designer]: Please investigate and post follow-up findings here.

*(Cycle 1 of max 2)*
```

> **Escalation rule:** If a discussion has already received 2 NEEDS-MORE-INFO comments, do not ask again. Instead, post: `## CEO Decision: ESCALATE — This needs a human decision. Tagging for review.` and leave the discussion open.

**After processing discussions:**
7. Close the repository: `git pull` to ensure you have the latest roadmap
8. If strategic direction has meaningfully shifted, update `docs/PRODUCT_ROADMAP.md` and commit to main

---

### PM — Council Mode (Weekly — Monday, after CEO)

**Goal:** Translate CEO-approved ideas into well-formed Feature Issues that enter the existing Feature Workflow.

**Each run:**
1. Read `~/.claude/projects/financial/roles/pm-context.md`
2. Find all open Discussions with `## CEO Decision: APPROVED` that do NOT have a `PM: Feature issue created` comment
3. For each approved discussion:
   a. Check for an existing similar feature: `gh issue list --label feature --state open`
   b. If a near-identical feature already exists, comment: `PM: Duplicate of #X. No new issue created.` and close the discussion.
   c. Otherwise, create a Feature Issue (see format below)
   d. Add to project board and set priority per CEO guidance
   e. Comment on the Discussion: `PM: Feature issue #[number] created. [link]`
   f. Close the Discussion
4. Update `~/.claude/projects/financial/roles/pm-context.md`

**Feature Issue format (council-originated):**
```bash
gh issue create \
  --title "[Feature title]" \
  --label "feature" \
  --milestone "<milestone>" \
  --body "## Feature

[Description of what we're building and why]

## Origin
Originated from Council Discussion: [discussion link]
CEO approved on: [date]
CEO rationale: [paste CEO rationale from decision comment]

## Target Outcome
[One sentence — what success looks like]

## Acceptance Criteria
- [ ] [Observable outcome 1]
- [ ] [Observable outcome 2]

## Notes for PM
[Any implementation constraints or considerations from the council discussion]"
```

> **Note:** The PM does NOT break this into user stories here. That happens in the existing Feature Workflow when the `/work-pm` command processes `needs-design-spec` or `ready-for-stories` labels.

---

## Information Flow (End-to-End Example)

**Day 1 (Monday):**
- Researcher (8am): Researches "alternative economic nowcasting models" and posts to Research Discussions
- Designer Council (9am): Notices mobile dashboard cards have inconsistent tap targets; posts to Refinements

**Day 1 (Monday):**
- CEO (10am): Reviews both posts. Approves the nowcasting model idea with P1 priority. Dismisses the tap target issue as too small for a feature (adds it to their context notes as design debt to fix in any upcoming UI story).
- PM Council (11am): Reads CEO's APPROVED decision. Checks no existing feature covers this. Creates Feature Issue #102 "Integrate economic nowcasting signals." Links back to discussion. Closes the discussion.

**Day 2 (Tuesday):**
- Feature Issue #102 now appears in `gh issue list --label feature`. PM's existing `/work-pm` flow will pick it up on next run.

**Day 5 (Friday):**
- Researcher: Finds a paper on yield curve factor models. Before posting, sees a NEEDS-MORE-INFO question from CEO in an existing discussion. Researches the answer. Posts follow-up comment.

**Following Monday:**
- CEO: Reads the Researcher's follow-up. Now has enough context. Posts APPROVED decision. Cycle completes.

---

## Context Files

New files needed (follow the same rules as existing role context files):

```
~/.claude/projects/financial/roles/
├── researcher-context.md         # Topics researched, dates, findings log
├── ceo-context.md                # Strategic priorities, recent decisions, dismissed directions
├── engineer-council-context.md   # Domains reviewed, findings posted, recently covered domains
├── pm-context.md                 # Existing — also updated by PM council runs
└── ui-designer-context.md        # Existing — also updated by Designer council runs
```

### researcher-context.md starter template
```markdown
# Researcher Context

## Research Domains
- Macroeconomic models and factor models
- Alternative data sources
- Competitor product gaps
- Academic signal methodology
- User pain points in retail investing
- AI/ML approaches to market analysis

## Recently Covered Topics
(add entries as: [date] — [topic] — [discussion #])

## Open CEO Questions
(add entries as: [date] — [question] — [discussion #])

## Notes
```

### ceo-context.md starter template
```markdown
# CEO Context

## Strategic Priorities (current)
(updated each run)

## Recent Decisions
(add entries as: [date] — [Approved/Dismissed] — [topic] — [discussion #])

## Dismissed Directions (do not re-approve without new evidence)
(add entries as: [direction] — [reason] — [date])

## Notes
```

---

## Working Directories

Council agents require far less filesystem access than implementation agents. None of them branch. They never run simultaneously. There are no conflicts.

| Agent | Repo Needed | Working Directory | Commits? |
|-------|-------------|-------------------|----------|
| Researcher | Read-only | `~/projects/financial-pm/` — reads `PRODUCT_ROADMAP.md` to avoid proposing already-planned work | Never |
| Designer Council | Read-only | `~/projects/financial-pm/` — reads `docs/design-system.md`, `docs/specs/`, and templates to identify real gaps | Never |
| Engineer Council | Read-only | `~/projects/financial-pm/` — reads source files in `signaltrackers/` and `data/` to audit AI data feed coverage, algorithms, and technical debt | Never |
| CEO | Read + write | `~/projects/financial-pm/` — reads roadmap, may update `PRODUCT_ROADMAP.md` on main | Rarely (roadmap only) |
| PM Council | Read-only | `~/projects/financial-pm/` — `gh` CLI only, no file changes | Never |

**All four council agents share the existing PM checkout.** All stay on `main`. None branch. CEO is the only one that ever commits (roadmap updates only). No new checkouts needed.

Compare to implementation agents (Engineer, Designer impl, QA) who each need their own checkout because they work on different feature branches potentially in parallel.

---

## Scripts

### scripts/run-researcher-council.sh
Runs daily at 8am. Invokes the `/work-researcher` command.

### scripts/run-designer-council.sh
Runs daily at 9am. Invokes the `/work-designer-council` command.

### scripts/run-engineer-council.sh
Runs daily at 10:30am. Invokes the `/work-engineer-council` command.

### scripts/run-council-weekly.sh
Runs weekly (Monday at 10am). Invokes CEO then PM sequentially — order is critical.

### scripts/setup-council-cron.sh
One-time setup: installs the cron jobs for all council agents.

Script contents are defined in the Implementation Plan below and created during implementation.

---

## Command Files Needed

```
.claude/commands/
├── work-researcher.md         # Researcher autonomous mode
├── work-ceo.md                # CEO autonomous mode
├── work-designer-council.md   # Designer council mode (separate from work-designer.md)
├── work-engineer-council.md   # Engineer council mode (separate from work-engineer.md)
└── work-pm-council.md         # PM council mode (separate from work-pm.md)
```

---

## Guardrails and Edge Cases

| Situation | Handling |
|-----------|----------|
| Researcher wants to post a duplicate idea | Check open discussions for similar topics before posting. If similar exists, add a comment to the existing thread instead of creating a new one. |
| CEO asked NEEDS-MORE-INFO twice with no resolution | On third encounter, post ESCALATE comment and leave for human |
| PM finds approved discussion but similar feature already exists | Comment "PM: Duplicate of #X" on discussion, close discussion, no new issue |
| Designer has nothing worth posting | Skip posting entirely. Do not post for the sake of posting. |
| Council Discussion has no CEO decision for 2+ weeks | CEO context file tracks stale items; CEO processes oldest-first each weekly run |
| CEO approves something already in the backlog | PM detects the duplicate and closes the discussion with a reference to the existing issue |
| PM crashes after creating issue but before closing discussion | Next week PM sees APPROVED + no "PM: Feature issue created" comment → runs again → checks for duplicate → finds existing issue → comments and closes |

---

## Relationship to Existing Workflows

```
Council Workflow                    Existing Workflows
──────────────────                  ──────────────────
Researcher (daily)  ─┐
Designer Council    ─┤
(daily)              ├→ Discussion → CEO approves → PM creates Feature Issue
Engineer Council    ─┘                                      │
(daily)                                                     ▼
                                              Feature Workflow (/work-pm, /work-designer)
                                                            │
                                                            ▼
                                              User Story Workflow (/work-engineer, /work-qa)
```

The Council Workflow only outputs **Feature Issues**. Everything downstream is unchanged.

---

## Implementation Plan

### Phase 1 — GitHub Setup
- [x] Create "Research" Discussion category in GitHub (Settings → Discussions → New category)
- [x] Create "Refinements" Discussion category in GitHub
- [x] Create "Technical" Discussion category in GitHub
- [x] Verify gh CLI can list and create Discussions via GraphQL (`gh api graphql`)
- [x] Get repository node ID: `R_kgDORDsXzA`
- [x] Get category IDs:
  - Research: `DIC_kwDORXrB_s4C3HGH`
  - Refinements: `DIC_kwDORXrB_s4C3HGA`
  - Technical: `DIC_kwDORXrB_s4C3Oge`
- [x] Record repo ID and category IDs in `~/.claude/projects/financial/council-config.md`

### Phase 2 — Context Files
- [x] Create `~/.claude/projects/financial/roles/researcher-context.md` using starter template above
- [x] Create `~/.claude/projects/financial/roles/ceo-context.md` using starter template above

### Phase 3 — Command Files
- [x] Create `.claude/commands/work-researcher.md`
- [x] Create `.claude/commands/work-ceo.md`
- [x] Create `.claude/commands/work-designer-council.md`
- [x] Create `.claude/commands/work-engineer-council.md`
- [x] Create `.claude/commands/work-pm-council.md`

### Phase 4 — Scripts
- [x] Create `scripts/run-researcher-council.sh`
- [x] Create `scripts/run-designer-council.sh`
- [x] Create `scripts/run-engineer-council.sh`
- [x] Create `scripts/run-council-weekly.sh` (runs CEO then PM in sequence)
- [x] Create `scripts/setup-council-cron.sh`
- [x] Make all scripts executable (`chmod +x`)

### Phase 5 — Update CLAUDE.md
- [x] Add council roles to the Roles Overview table
- [x] Add council scripts to the running/scheduling section
- [x] Add council workflow summary to Workflows Overview

### Phase 6 — Validation
- [ ] Manual test: Run `/work-researcher` in interactive mode, verify it posts a Discussion to Research category
- [ ] Manual test: Run `/work-ceo` in interactive mode, verify it reads the discussion and posts a structured decision
- [ ] Manual test: Run `/work-pm-council` in interactive mode, verify it creates a Feature Issue and closes the discussion
- [ ] Verify the resulting Feature Issue is picked up correctly by the existing `/work-pm` flow
- [ ] End-to-end test: Full cycle from Researcher post → CEO approval → PM feature issue → confirm it enters Feature Workflow queue

### Phase 7 — Cron Activation
- [ ] Run `scripts/setup-council-cron.sh` to install cron jobs
- [ ] Verify cron jobs are listed: `crontab -l`
- [ ] Monitor first automated runs and check Discussion board for output
