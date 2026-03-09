# Council Workflow Redesign — Implementation Plan

**Status:** In Progress
**Created:** 2026-03-08
**Discussion:** #33

## Overview

Adds phase-aware behavior to the Council Workflow:
1. **Phase state** tracked in `PRODUCT_ROADMAP.md` (IDEATING / BUILDING / COMPLETE)
2. **Council pauses** during BUILDING (bash-layer guard, zero tokens)
3. **Human approval gate** — PM Council tags new Feature Issues with `needs-human-approval`; human removes label to unlock implementation
4. **Auto-transition to BUILDING** — `/work-pm` flips phase when it sees approved (unlabeled) features during IDEATING
5. **Phase completion pipeline** — PM detects all stories closed → closes milestone → creates GitHub Release → triggers deploy
6. **Agent awareness** — all council agents read phase state and orient accordingly

---

## Phase 1 — GitHub Setup

- [x] Create `needs-human-approval` label in GitHub
  ```bash
  gh label create "needs-human-approval" --description "Feature awaiting human review before entering implementation pipeline" --color "E4E669"
  ```

---

## Phase 2 — PRODUCT_ROADMAP.md

- [x] Add `## Active Phase` block near the top of `docs/PRODUCT_ROADMAP.md` (after North Star Metric, before Current Release State)
  ```markdown
  ## Active Phase
  **Phase:** Phase 7 — Credit Intelligence & Completion
  **State:** BUILDING
  ```
  > Set to BUILDING immediately — Phase 7 is in active implementation.

---

## Phase 3 — Bash Script Guards (Council Pause)

Add phase guard to each script. Guard checks `## Active Phase` → `**State:**` line. If `BUILDING`, logs and exits before invoking `claude`.

- [x] `scripts/run-researcher-council.sh` — add phase guard
- [x] `scripts/run-designer-council.sh` — add phase guard
- [x] `scripts/run-engineer-council.sh` — add phase guard
- [x] `scripts/run-council-weekly.sh` — add phase guard (skips both CEO and PM Council if BUILDING)

**Guard block to add (after `cd "$REPO_DIR"`):**
```bash
# Phase guard — council pauses during BUILDING
ROADMAP="$REPO_DIR/docs/PRODUCT_ROADMAP.md"
PHASE_STATE=$(grep "^\*\*State:\*\*" "$ROADMAP" | awk '{print $2}')
if [ "$PHASE_STATE" = "BUILDING" ]; then
  echo "Phase is BUILDING — council paused. Exiting." >> "$LOG_FILE"
  exit 0
fi
```

---

## Phase 4 — Agent Instruction Updates

### 4a — Researcher (`work-researcher.md`)
- [x] Add step: Read `## Active Phase` block from `docs/PRODUCT_ROADMAP.md`
- [x] Add IDEATING behavior: Orient research toward gaps relevant to the upcoming phase; check `gh issue list --label needs-human-approval` to avoid proposing duplicates of already-queued ideas
- [x] Add safety note: If state is not IDEATING, do not post — exit early

### 4b — Designer Council (`work-designer-council.md`)
- [x] Add step: Read `## Active Phase` block from `docs/PRODUCT_ROADMAP.md`
- [x] Add IDEATING behavior: Surface UX improvements relevant to the upcoming phase direction; check `needs-human-approval` queue for duplicates
- [x] Add safety note: If state is not IDEATING, do not post — exit early

### 4c — Engineer Council (`work-engineer-council.md`)
- [x] Add step: Read `## Active Phase` block from `docs/PRODUCT_ROADMAP.md`
- [x] Add IDEATING behavior: Surface technical debt and algorithm gaps relevant to next phase; check `needs-human-approval` queue for duplicates
- [x] Add safety note: If state is not IDEATING, do not post — exit early

### 4d — CEO (`work-ceo.md`)
- [x] Add step: Read `## Active Phase` block from `docs/PRODUCT_ROADMAP.md`
- [x] Add step: Check how many features are already queued — `gh issue list --label needs-human-approval --state open` — to calibrate selectivity (avoid overloading the next phase)
- [x] Add approval guidance: When approving ideas, note whether they fit the *next* phase or are Phase N+2 material. Use "defer to future phase" for good-but-not-now ideas rather than full dismissal.

### 4e — PM Council (`work-pm-council.md`)
- [x] Add `--label "needs-human-approval"` to all `gh issue create` commands
- [x] Update feature issue body template to note: "Human must remove `needs-human-approval` label before this enters the implementation pipeline"
- [x] Update Discussion close comment to: "PM: Feature issue #X created. Awaiting human approval (`needs-human-approval` label) before entering implementation pipeline."

### 4f — PM (`work-pm.md`)
- [x] Add session-start step: Read `## Active Phase` block from `docs/PRODUCT_ROADMAP.md`
- [x] Add IDEATING logic:
  - Check for features without `needs-human-approval`: `gh issue list --label feature --state open` then cross-check
  - If any exist: flip `**State:**` in `PRODUCT_ROADMAP.md` from `IDEATING` to `BUILDING`, commit to main, push
  - Proceed with normal queue processing
- [x] Add BUILDING logic: Skip any feature with `needs-human-approval` label
- [x] Add COMPLETE detection:
  - When all sub-issues of all active features are closed, detect phase complete
  - Close the GitHub milestone
  - Create a GitHub Release tagged `phase-N-complete`
  - Flip `**State:**` to `IDEATING` in `PRODUCT_ROADMAP.md`, commit, push
  - Comment on closed milestone: "Phase complete. GitHub Release created. Deployment triggered."

---

## Phase 5 — Deployment Pipeline

**Already complete.** No changes needed.

- [x] `.github/workflows/docker-publish.yml` already exists and handles the full pipeline:
  - Triggers on `release: published`
  - Builds multi-arch Docker image (amd64 + arm64)
  - Pushes `ghcr.io/ericmaibach/financial:latest` to GHCR using built-in `GITHUB_TOKEN`
  - Watchtower (running in Portainer) polls GHCR and auto-pulls the new image

When `/work-pm` creates a GitHub Release via `gh release create "phase-N-complete" ...`, this workflow fires automatically. No webhook, no additional secrets, no further configuration required.

---

## Phase 6 — Documentation Updates

- [x] Update `docs/COUNCIL-WORKFLOW.md`
  - Add phase state model section (IDEATING / BUILDING / COMPLETE)
  - Add council pause behavior
  - Add human approval gate
  - Add phase completion → deploy pipeline
  - Update state machine diagram

- [x] Update `CLAUDE.md`
  - Add phase state to Workflows Overview
  - Add `needs-human-approval` to Issue Labels table
  - Add council pause behavior to Council Workflow section
  - Add deploy pipeline to Technical Notes

---

## Phase 7 — Validation

- [x] Verify phase guard: Confirmed `run-researcher-council.sh` logs "Phase is BUILDING — council paused. Exiting." and exits before invoking `claude`. **Note:** Required `git pull` in the `financial-pm` checkout — scripts use that path and it was behind main.
- [x] Verify `needs-human-approval` label flow: Label confirmed live in GitHub (`#E4E669`). Command files verified to include `--label "feature,needs-human-approval"` in `gh issue create`.
- [x] Verify `/work-pm` BUILDING skip: Simulated the exact jq filter from `work-pm.md` against live issues — correctly returns 5 existing Phase 7 features (all without the label, all grandfathered in). 0 features have `needs-human-approval`.
- [x] Verify IDEATING → BUILDING flip: Simulated detection query — 5 features without `needs-human-approval` would trigger the BUILDING flip. Logic confirmed correct. Full agent run not executed (would process live queues).
- [x] Verify deploy workflow: `docker-publish.yml` confirmed to trigger on `release: [published]`. Existing workflow already handles build + push to `ghcr.io/ericmaibach/financial:latest` → Watchtower auto-deploys.

---

## Implementation Notes

**Current state for Phase 7 transition:**
- Set Active Phase to `BUILDING` immediately (step 2 above)
- Existing features #218, #219, #220 are grandfathered — created before the gate existed, no retroactive label needed
- Council pauses immediately once scripts are updated

**Phase 8 scope:**
- Not defined yet — intentional
- Council will surface Phase 8 ideas during the next IDEATING window (after Phase 7 ships)

**IDEATING → BUILDING trigger (by whom):**
- Human removes `needs-human-approval` from features they want to build
- `/work-pm` detects unlabeled features during IDEATING → auto-flips to BUILDING
- This keeps human firmly in control of scope commitment while automating the state transition

**BUILDING → COMPLETE trigger:**
- PM detects all sub-issues closed on next `/work-pm` run
- Auto: closes milestone, creates GitHub Release, flips to IDEATING
