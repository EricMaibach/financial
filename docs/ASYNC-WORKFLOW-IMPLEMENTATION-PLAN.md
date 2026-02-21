# Async Multi-Agent Workflow Implementation Plan

**Status:** Planning Complete - Ready for Implementation
**Created:** 2026-02-21
**Last Updated:** 2026-02-21
**Purpose:** Document the redesign from synchronous to asynchronous multi-agent workflow

**Recent Updates:**
- Added Decision 8: Branch Strategy (feature docs on main, user stories on shared feature branches)
- Added Decision 9: File Permissions (agent boundaries and enforcement)
- Added Phase 2.5: Branch Strategy Documentation
- Added Phase 5.5: File Permissions in Role Commands
- Added Phase 9.5: Git Pre-Commit Hooks (optional technical enforcement)
- Enhanced examples with detailed branch workflow demonstrations

---

## Executive Summary

### Current State
- Synchronous `/work-story` workflow (single session, linear path)
- PM ↔ Designer async workflow (documented in CLAUDE.md)
- Agent context files in repo (causing conflicts)
- Single working directory (agents conflict on branches/files)

### Target State
- **Asynchronous multi-agent workflow** with GitHub issues as state machine
- **Dual mode agents**: Interactive (discussion) + Autonomous (work processing)
- **Multiple repo checkouts** - one per agent to prevent file conflicts
- **Agent context outside repo** - eliminates most concurrency issues
- **Human-in-the-loop** - agents create PRs, humans merge code
- **WIP limit of 1** - one user story in implementation pipeline at a time (initially)

### Key Benefits
- ✅ Realistic team simulation (mirrors professional development)
- ✅ Scalable (multiple stories can be in different phases)
- ✅ Resumable (work persists across sessions)
- ✅ Safe (human approval for code merges)
- ✅ Debuggable (GitHub issues are source of truth)

---

## Architecture Decisions

### Decision 1: Asynchronous Workflow
**Choice:** Async multi-agent over synchronous single-session
**Rationale:**
- More realistic (real teams work asynchronously)
- Scalable (many stories in flight in different phases)
- Resumable (work across multiple sessions)
- Flexible (agents work when ready, not all at once)

### Decision 2: Separate Workflows for Features vs User Stories
**Choice:** Two distinct workflows
**Rationale:**
- Features = Strategic work (PM ↔ Designer only)
- User Stories = Implementation work (QA → Engineer → Designer → QA)
- Prevents confusion (Engineer won't pick up Features by mistake)

**Feature Workflow:**
```
1. feature + needs-design-spec     → Designer creates spec
2. feature + needs-pm-approval     → PM reviews/approves
3. feature + ready-for-stories     → PM creates user stories
```

**User Story Workflow:**
```
1. user-story + needs-test-plan            → QA creates test plan
2. user-story + ready-for-implementation   → Engineer implements
3. user-story + needs-design-review        → Designer reviews (if UI)
4. user-story + needs-qa-testing          → QA tests
5. user-story + ready-for-pr              → Engineer creates PR
6. [Human reviews and merges PR]
7. Issue auto-closes
```

### Decision 3: Multiple Repo Checkouts
**Choice:** 4 separate working directories (one per agent)
**Rationale:**
- Prevents Git conflicts (each agent has own working directory)
- Allows concurrent work (Designer updates spec while Engineer switches branches)
- Simple to understand (just clone 4 times)
- Disk space is not a constraint

**Structure:**
```
~/projects/financial-pm/        # PM workspace
~/projects/financial-designer/  # Designer workspace
~/projects/financial-engineer/  # Engineer workspace
~/projects/financial-qa/        # QA workspace
```

### Decision 4: Agent Context Outside Repo
**Choice:** Move agent memory to `~/.claude/projects/financial/`
**Rationale:**
- Agent memory is working notes, not product deliverable
- Eliminates context file conflicts
- Keeps repo focused on product artifacts (code, specs, docs)
- Can be backed up separately if needed

**Structure:**
```
~/.claude/projects/financial/
├── roles/
│   ├── pm-context.md
│   ├── ui-designer-context.md
│   ├── engineer-context.md
│   └── qa-context.md
└── logs/
    └── [optional workflow logs]
```

### Decision 5: Dual Mode Agents
**Choice:** Separate commands for Interactive vs Autonomous
**Rationale:**
- Explicit and unambiguous (no guessing mode from context)
- User controls behavior by command choice
- Easy to invoke from cron (autonomous) or CLI (interactive)

**Commands:**
- `/pm`, `/ui-designer`, `/engineer`, `/qa` → Interactive (discussion)
- `/work-pm`, `/work-designer`, `/work-engineer`, `/work-qa` → Autonomous (process work)

### Decision 6: Human-in-the-Loop for Code Merges
**Choice:** Agents create PRs, humans merge
**Rationale:**
- Safety control (prevents agents from breaking production)
- Industry best practice (even advanced systems require approval)
- Learning opportunity (human reviews agent work)
- Compliance/audit (some orgs require human sign-off)

**Exception:** Agents CAN commit documentation (design specs, etc.) directly

### Decision 7: WIP Limit of 1 (Initially)
**Choice:** Only one user story in implementation pipeline at a time
**Rationale:**
- Easier debugging (know where things broke)
- Prevents PR pile-up (don't overwhelm human reviewer)
- Learn the workflow before scaling
- Can relax later (increase to 3, 5, etc.)

**Enforcement:** Engineer checks for in-flight stories before picking up new work

### Decision 8: Branch Strategy
**Choice:** Different branch strategies for feature docs vs user story work
**Rationale:**
- Feature documentation is low-risk, can go direct to main
- User story work needs review, uses feature branches
- All agents contribute to shared feature branch for cohesive PR

**Strategy:**

| Work Type | Branch | Who Commits | Push Strategy |
|-----------|--------|-------------|---------------|
| Feature specs | `main` | Designer only | Direct push to main |
| Product roadmap | `main` | PM (rare) | Direct push to main |
| Design system | `main` | Designer | Direct push to main |
| User story | `feature/US-X.X.X` | Engineer, Designer, QA | Shared branch, all push |
| Bug fixes | `fix/bug-description` | Engineer | Same as user story |

**Workflow:**
1. **Engineer** creates `feature/US-X.X.X` branch, implements, pushes
2. **Designer** fetches, checks out branch, reviews/tweaks, pushes
3. **QA** fetches, checks out branch, tests, optionally commits test files, pushes
4. **Engineer** creates single PR with all commits from all agents
5. **Human** reviews and merges entire branch

### Decision 9: File Permissions (Agent Boundaries)
**Choice:** Behavioral instructions + optional technical enforcement
**Rationale:**
- Agents should stay in their domain (Designer doesn't write code)
- Behavioral instructions are simple and flexible
- Git hooks provide technical enforcement if needed
- Prevents accidental violations

**Permissions Matrix:**

| Agent | Can Modify | Cannot Modify |
|-------|------------|---------------|
| **PM** | `docs/PRODUCT_ROADMAP.md` (rare) | Code, specs, config, tests |
| **Designer** | `docs/specs/`, `docs/design-system.md`, `static/css/` | Code, templates, config, tests |
| **Engineer** | Code, templates, tests, deps | `docs/PRODUCT_ROADMAP.md`, `.env` |
| **QA** | `tests/`, `*_test.py` | Code (non-test), specs, config |

**Enforcement:**
1. **Tier 1 (Now):** Behavioral instructions in role commands
2. **Tier 2 (Later):** Git pre-commit hooks if violations occur
3. **Tier 3 (Future):** Claude Code approval policies

---

## Workflow Design

### Feature Workflow (PM ↔ Designer)

```
┌─────────────────────────────────────────────────┐
│            FEATURE WORKFLOW                      │
│        (Strategic/Design Definition)             │
└─────────────────────────────────────────────────┘

1. PM creates feature issue
   - Label: feature
   - Contains: User story format, context, goals
   - Determines if UI work needed

2. If UI work:
   - PM adds label: needs-design-spec
   - Designer picks up, creates spec in docs/specs/
   - Designer commits spec, comments on issue
   - Designer adds label: needs-pm-approval

3. PM reviews design spec
   - Approves: Adds label ready-for-stories
   - Requests changes: Comments, keeps needs-pm-approval

4. PM breaks feature into user stories
   - Creates user-story issues
   - Adds as sub-issues of feature
   - Each story gets label: needs-test-plan
   - Feature remains open until all stories complete
```

### User Story Workflow (QA → Engineer → Designer → QA)

```
┌─────────────────────────────────────────────────┐
│          USER STORY WORKFLOW                     │
│         (Implementation Pipeline)                │
└─────────────────────────────────────────────────┘

BACKLOG (Multiple stories OK)
├─ QA creates test plans for stories
├─ Stories move to: ready-for-implementation
└─ Queue builds up (ready for Engineer)

IMPLEMENTATION (WIP Limit: 1 story)
│
├─ 1. Engineer checks: Any story in progress?
│     → YES: Wait for PR merge
│     → NO: Pick ONE from ready-for-implementation
│
├─ 2. Engineer implements
│     - Creates feature/US-X.X.X branch
│     - Implements per spec and acceptance criteria
│     - Adds label: needs-design-review (if UI) or needs-qa-testing (if no UI)
│
├─ 3. Designer reviews (if UI)
│     - Checks out branch, reviews implementation
│     - Approves: Adds label needs-qa-testing
│     - Requests changes: Adds label needs-design-changes
│
├─ 4. Engineer fixes (if design changes requested)
│     - Makes changes
│     - Adds label: needs-design-review (back to step 3)
│
├─ 5. QA tests
│     - Verifies against test plan
│     - Approves: Adds label ready-for-pr
│     - Finds bugs: Adds label needs-fixes
│
├─ 6. Engineer fixes bugs (if needed)
│     - Fixes issues
│     - Adds label: needs-qa-testing (back to step 5)
│
└─ 7. Engineer creates PR
      - Title: "US-X.X.X: [Story title]"
      - Body: "Fixes #X" + summary + test results
      - Does NOT merge
      - Comments: "✅ PR created, ready for human review"

HUMAN REVIEW
└─ Human reviews PR
   └─ Approves and merges (or requests changes)
      └─ Issue auto-closes (via "Fixes #X")
         └─ Pipeline is clear, next story can start
```

---

## File Structure Changes

### Current Structure (to be changed)
```
~/projects/financial/                    # Single working directory
├── docs/
│   ├── roles/                          # ❌ Agent context in repo (conflicts)
│   │   ├── pm-context.md
│   │   └── ...
│   └── specs/                          # ✅ Keep (design specs)
├── .claude/
│   └── commands/
│       ├── pm.md                       # ❌ Mixed interactive/autonomous
│       ├── ui-designer.md              # ❌ Mixed interactive/autonomous
│       ├── engineer.md                 # ❌ Mixed interactive/autonomous
│       ├── qa.md                       # ❌ Mixed interactive/autonomous
│       └── work-story.md               # ❌ Remove (replaced by async)
└── CLAUDE.md                           # ⚠️ Needs reorganization
```

### Target Structure
```
# Multiple working directories (one per agent)
~/projects/
├── financial-pm/                       # PM workspace (main branch)
├── financial-designer/                 # Designer workspace (main/design branch)
├── financial-engineer/                 # Engineer workspace (feature branches)
└── financial-qa/                       # QA workspace (review branches)

# Each contains:
~/projects/financial-*/
├── docs/
│   ├── specs/                          # ✅ Design specs (in repo)
│   ├── design-system.md                # ✅ Design system (in repo)
│   └── PRODUCT_ROADMAP.md              # ✅ Product vision (in repo)
├── .claude/
│   └── commands/
│       ├── pm.md                       # ✅ Interactive PM
│       ├── ui-designer.md              # ✅ Interactive Designer
│       ├── engineer.md                 # ✅ Interactive Engineer
│       ├── qa.md                       # ✅ Interactive QA
│       ├── work-pm.md                  # ✅ NEW: Autonomous PM
│       ├── work-designer.md            # ✅ NEW: Autonomous Designer
│       ├── work-engineer.md            # ✅ NEW: Autonomous Engineer
│       └── work-qa.md                  # ✅ NEW: Autonomous QA
├── signaltrackers/                     # Code
└── CLAUDE.md                           # ✅ Reorganized

# Agent context (outside repo)
~/.claude/projects/financial/
├── roles/
│   ├── pm-context.md                   # Agent working memory
│   ├── ui-designer-context.md
│   ├── engineer-context.md
│   └── qa-context.md
└── logs/                               # Optional workflow logs
```

---

## GitHub Label System

### Type Labels (Issue Classification)
```yaml
feature           # Strategic work (PM + Designer)
user-story        # Implementation work (QA + Engineer + Designer)
bug              # Defects
```

### Feature Workflow States
```yaml
needs-design-spec      # Designer: create design specification
needs-pm-approval      # PM: review and approve design spec
ready-for-stories      # PM: break into user stories
```

### User Story Workflow States
```yaml
needs-test-plan            # QA: create test plan
ready-for-implementation   # Engineer: implement story (if no WIP)
needs-design-review        # Designer: review implementation
needs-design-changes       # Engineer: fix design issues (iteration)
needs-qa-testing          # QA: verify implementation
needs-fixes               # Engineer: fix bugs (iteration)
ready-for-pr              # Engineer: create PR (don't merge)
```

### Blocking/Meta States
```yaml
blocked                # Blocked, needs intervention
needs-clarification    # Unclear requirements
needs-human-decision   # Escalate to human for decision
```

---

## Implementation Steps

### Phase 1: Planning & Documentation ✅
- [x] Review current workflow and identify issues
- [x] Design async multi-agent architecture
- [x] Document decisions and rationale
- [x] Create implementation plan (this document)

### Phase 2: Repository Setup
- [x] **2.1** Create multiple repo checkouts
  ```bash
  cd ~/projects
  git clone git@github.com:EricMaibach/financial.git financial-pm
  git clone git@github.com:EricMaibach/financial.git financial-designer
  git clone git@github.com:EricMaibach/financial.git financial-engineer
  git clone git@github.com:EricMaibach/financial.git financial-qa
  ```

- [x] **2.2** Create agent context directory structure
  ```bash
  mkdir -p ~/.claude/projects/financial/roles
  mkdir -p ~/.claude/projects/financial/logs
  ```

- [x] **2.3** Move existing context files (if any)
  ```bash
  mv ~/projects/financial/docs/roles/*.md ~/.claude/projects/financial/roles/ 2>/dev/null || true
  ```

- [x] **2.4** Update .gitignore in all repos
  ```bash
  # Add to .gitignore
  docs/roles/
  docs/test-plans/
  ```

### Phase 2.5: Branch Strategy Documentation ✅
- [x] **2.5.1** Document branch strategy in CLAUDE.md
  - Feature documentation: `main` branch, direct push (Designer)
  - User story work: `feature/US-X.X.X` shared branch (all agents)
  - Bug fixes: `fix/description` branch (Engineer)
  - Include branch strategy table

- [x] **2.5.2** Add branch workflow to role commands
  - **Designer:** When to commit to `main` (specs) vs `feature/US-X.X.X` (review tweaks)
  - **Engineer:** Always create `feature/US-X.X.X` for user stories, commit implementation
  - **QA:** Check out `feature/US-X.X.X` to test, optionally commit test files
  - **PM:** Rarely commits, stays on `main` if needed

- [x] **2.5.3** Create branch workflow examples
  - Example: Designer creates spec on main
  - Example: Engineer creates feature branch, Designer/QA contribute, PR created
  - Examples already in this plan (Examples 1, 2, 3); condensed version added to CLAUDE.md

### Phase 3: GitHub Label Setup ✅
- [x] **3.1** Create workflow state labels in GitHub
  - Type labels: `feature`, `user-story`, `bug`
  - Feature states: `needs-design-spec`, `needs-pm-approval`, `ready-for-stories`
  - User story states: `needs-test-plan`, `ready-for-implementation`, `needs-design-review`, `needs-design-changes`, `needs-qa-testing`, `needs-fixes`, `ready-for-pr`
  - Meta states: `blocked`, `needs-clarification`, `needs-human-decision`

- [x] **3.2** Document label system in CLAUDE.md

### Phase 4: Update CLAUDE.md ✅
- [x] **4.1** Add "Workflows Overview" section
  - Feature Workflow (PM → Designer → PM → stories) with label transition table
  - User Story Workflow (QA → Engineer → Designer → QA → PR → Human) with label transition table
  - Quick reference table for "which workflow?"

- [x] **4.2** Add "Roles Overview" section
  - Table of all 8 commands (4 interactive + 4 autonomous)
  - Interactive vs Autonomous explanation

- [x] **4.3** Consolidate "Memory Management" section
  - Centralized section with context file locations
  - Rules for all roles (read/update each session, 300 line limit)
  - Context files live outside repo at ~/.claude/projects/financial/roles/

- [x] **4.4** Consolidate "GitHub Commands" section
  - Renamed to "## GitHub Commands" — authoritative reference
  - Organized by: Issues, Pull Requests, Project Board, Sub-Issues, Labels

- [x] **4.5** Update "Collaboration Workflow" section
  - Removed old PM → Designer → Engineer 3-phase section
  - Replaced with slim "Role Communication" section (role tagging + key principles + repo org)
  - Full workflow detail lives in Workflows Overview section (4.1)

- [x] **4.6** Remove/archive "Role-Based Autonomous" section
  - Removed autonomous checklists and example autonomous session from CLAUDE.md
  - These will live in work-* command files (Phase 6)

- [x] **4.7** Update ".env Rules" (keep centralized)
  - Already well-documented under Technical Notes — no changes needed

### Phase 5: Create Interactive Role Commands ✅
- [x] **5.1** Update `pm.md`
  - Added "# Product Manager — Interactive Mode" header
  - Added "Do NOT autonomously check for work" statement
  - Updated context path to ~/.claude/projects/financial/roles/pm-context.md
  - Replaced inline memory rules with reference to CLAUDE.md Memory Management
  - Kept user story writing guidelines

- [x] **5.2** Update `ui-designer.md`
  - Added "# UI/UX Designer — Interactive Mode" header
  - Removed entire "## Invocation Context" section (Focused/Autonomous Mode content)
  - Added "Do NOT autonomously check for work" statement
  - Updated context path to ~/.claude/projects/financial/roles/ui-designer-context.md
  - Replaced inline memory rules with reference to CLAUDE.md Memory Management
  - Kept all design principles, guidelines, and Branch Workflow

- [x] **5.3** Update `engineer.md`
  - Added "# Engineer — Interactive Mode" header
  - Added "Do NOT autonomously check for work" statement
  - Updated context path to ~/.claude/projects/financial/roles/engineer-context.md
  - Fixed memory management section (was incorrectly referencing qa-context.md)
  - Replaced inline memory rules with reference to CLAUDE.md Memory Management
  - Cleaned up formatting in Branch Workflow section
  - Kept all code quality and security guidelines

- [x] **5.4** Update `qa.md`
  - Added "# QA Test Engineer — Interactive Mode" header
  - Added "Do NOT autonomously check for work" statement
  - Updated context path to ~/.claude/projects/financial/roles/qa-context.md
  - Replaced inline memory rules with reference to CLAUDE.md Memory Management
  - Added proper markdown formatting throughout
  - Fixed Session Wrap-Up to reference correct outside-repo context path
  - Kept all test strategy guidelines

### Phase 5.5: Add File Permissions to Role Commands ✅
- [x] **5.5.1** Added file permissions section to `pm.md`
  - Can commit: docs/PRODUCT_ROADMAP.md only (rare)
  - Cannot commit: code, specs, config, tests

- [x] **5.5.2** Added file permissions section to `ui-designer.md`
  - Can modify: docs/specs/, docs/design-system.md, static/css/
  - Cannot modify: Python code, HTML templates, config, tests

- [x] **5.5.3** Added file permissions section to `engineer.md`
  - Can modify: signaltrackers/, templates/, static/js/, tests/, requirements.txt
  - Coordinate: docs/specs/, design-system.md, static/css/
  - Cannot modify: PRODUCT_ROADMAP.md, .env

- [x] **5.5.4** Added file permissions section to `qa.md`
  - Can modify: tests/, docs/test-plans/, *_test.py
  - Cannot modify: non-test code, templates, specs, config

### Phase 6: Create Autonomous Work Commands ✅
- [x] **6.1** Create `work-pm.md`
  - "# Product Manager — Autonomous Mode" header
  - Working directory: ~/projects/financial-pm/
  - Queue 1: needs-pm-approval → review spec → approve (ready-for-stories) or request changes
  - Queue 2: ready-for-stories → break into user stories with sub-issue links
  - Queue 3: needs-clarification → resolve or escalate
  - Error handling table

- [x] **6.2** Create `work-designer.md`
  - "# UI/UX Designer — Autonomous Mode" header
  - Working directory: ~/projects/financial-designer/
  - Queue 1 (priority): needs-design-review → checkout feature branch, review, approve or request changes
  - Queue 2: needs-design-spec → checkout main, create spec, push, update label
  - Queue 3: respond to "Designer:" comments
  - Design spec template included
  - 3-iteration limit with needs-human-decision escalation
  - Error handling table

- [x] **6.3** Create `work-engineer.md`
  - "# Engineer — Autonomous Mode" header
  - Working directory: ~/projects/financial-engineer/
  - WIP limit check command (jq query) before any new story pickup
  - Queue 1: needs-design-changes → fix design issues, back to needs-design-review
  - Queue 2: needs-fixes → fix QA bugs, back to needs-qa-testing
  - Queue 3: ready-for-pr → pull all commits, create PR (DO NOT MERGE)
  - Queue 4: ready-for-implementation → only if no WIP, implement, push, route to review
  - Error handling table

- [x] **6.4** Create `work-qa.md`
  - "# QA Test Engineer — Autonomous Mode" header
  - Working directory: ~/projects/financial-qa/
  - Queue 1 (priority): needs-qa-testing → checkout branch, run tests, approve (ready-for-pr) or file bugs (needs-fixes)
  - Queue 2: needs-test-plan → create test plan as issue comment, advance to ready-for-implementation
  - Queue 3: triage new bug reports
  - Bug creation template included
  - Error handling table

### Phase 7: Remove Synchronous Workflow ✅
- [x] **7.1** Archive or delete `work-story.md`
  - Archived to `docs/archive/work-story.md` for reference

- [x] **7.2** Update skills list if work-story was registered
  - Removed by deleting `.claude/commands/work-story.md` (skills auto-discovered from commands/)

### Phase 8: Testing & Validation
- [ ] **8.1** Test Feature Workflow
  - PM creates feature
  - Designer creates spec
  - PM approves
  - Verify labels update correctly

- [ ] **8.2** Test User Story Workflow (Happy Path)
  - QA creates test plan
  - Engineer implements
  - Designer reviews (if UI)
  - QA tests
  - Engineer creates PR
  - Human merges
  - Issue auto-closes

- [ ] **8.3** Test User Story Workflow (Iteration)
  - Designer requests changes
  - Engineer fixes
  - Back to design review
  - Verify loop works

- [ ] **8.4** Test WIP Limit Enforcement
  - Start story A
  - Try to start story B (should be blocked)
  - Merge story A
  - Verify story B can now start

- [ ] **8.5** Test Interactive Mode
  - Invoke /ui-designer
  - Ask questions
  - Verify it doesn't autonomously check for work

- [ ] **8.6** Test Autonomous Mode
  - Invoke /work-designer
  - Verify it checks queues and processes work

### Phase 9: Cron Job Setup (Optional)
- [ ] **9.1** Create cron jobs for autonomous agents
  ```bash
  # Example crontab (every 2 hours)
  0 */2 * * * cd ~/projects/financial-pm && /usr/local/bin/claude /work-pm >> ~/logs/claude-pm.log 2>&1
  0 */2 * * * cd ~/projects/financial-designer && /usr/local/bin/claude /work-designer >> ~/logs/claude-designer.log 2>&1
  0 */2 * * * cd ~/projects/financial-engineer && /usr/local/bin/claude /work-engineer >> ~/logs/claude-engineer.log 2>&1
  0 */2 * * * cd ~/projects/financial-qa && /usr/local/bin/claude /work-qa >> ~/logs/claude-qa.log 2>&1
  ```

- [ ] **9.2** Create log directories
  ```bash
  mkdir -p ~/logs
  ```

### Phase 9.5: Git Pre-Commit Hooks (Optional - Only if Needed)
**Note:** Only implement this phase if agents violate file permissions during testing.
Start with behavioral instructions (Phase 5.5). Add technical enforcement only if needed.

- [ ] **9.5.1** Create pre-commit hook for Designer
  ```bash
  cat > ~/projects/financial-designer/.git/hooks/pre-commit << 'EOF'
  #!/bin/bash
  # Designer permission enforcement

  STAGED_FILES=$(git diff --cached --name-only)

  for FILE in $STAGED_FILES; do
    # Allow design specs, design system, CSS
    if [[ $FILE =~ ^docs/specs/ ]] || \
       [[ $FILE =~ ^docs/design-system.md$ ]] || \
       [[ $FILE =~ ^static/css/ ]]; then
      continue
    fi

    # Block everything else
    echo "❌ ERROR: Designer agent cannot modify $FILE"
    echo ""
    echo "Designer is only authorized to modify:"
    echo "  - docs/specs/ (design specifications)"
    echo "  - docs/design-system.md"
    echo "  - static/css/ (stylesheets)"
    echo ""
    echo "If you need code changes, document them in the issue"
    echo "and update the label. Engineer will implement."
    exit 1
  done
  EOF

  chmod +x ~/projects/financial-designer/.git/hooks/pre-commit
  ```

- [ ] **9.5.2** Create pre-commit hook for PM
  ```bash
  cat > ~/projects/financial-pm/.git/hooks/pre-commit << 'EOF'
  #!/bin/bash
  # PM permission enforcement

  STAGED_FILES=$(git diff --cached --name-only)

  for FILE in $STAGED_FILES; do
    if [[ ! $FILE =~ ^docs/PRODUCT_ROADMAP.md$ ]]; then
      echo "❌ ERROR: PM agent should not commit files directly"
      echo ""
      echo "PM creates GitHub issues, does not commit code"
      echo "Only docs/PRODUCT_ROADMAP.md is allowed (rare)"
      exit 1
    fi
  done
  EOF

  chmod +x ~/projects/financial-pm/.git/hooks/pre-commit
  ```

- [ ] **9.5.3** Create pre-commit hook for Engineer (warnings only)
  ```bash
  cat > ~/projects/financial-engineer/.git/hooks/pre-commit << 'EOF'
  #!/bin/bash
  # Engineer warnings (not blocking)

  STAGED_FILES=$(git diff --cached --name-only)

  for FILE in $STAGED_FILES; do
    if [[ $FILE =~ ^docs/specs/ ]]; then
      echo "⚠️  WARNING: Engineer modifying design spec: $FILE"
      echo "Consider asking Designer to update instead"
    fi

    if [[ $FILE =~ ^\.env$ ]]; then
      echo "❌ ERROR: NEVER modify .env file"
      echo "See CLAUDE.md for .env rules"
      exit 1
    fi
  done
  EOF

  chmod +x ~/projects/financial-engineer/.git/hooks/pre-commit
  ```

- [ ] **9.5.4** Create pre-commit hook for QA
  ```bash
  cat > ~/projects/financial-qa/.git/hooks/pre-commit << 'EOF'
  #!/bin/bash
  # QA permission enforcement

  STAGED_FILES=$(git diff --cached --name-only)

  for FILE in $STAGED_FILES; do
    if [[ $FILE =~ ^tests/ ]] || \
       [[ $FILE =~ ^docs/test-plans/ ]] || \
       [[ $FILE =~ _test\.py$ ]]; then
      continue
    fi

    echo "❌ ERROR: QA agent cannot modify $FILE"
    echo ""
    echo "QA is only authorized to modify:"
    echo "  - tests/ (test files)"
    echo "  - docs/test-plans/ (test documentation)"
    echo "  - *_test.py (test files)"
    exit 1
  done
  EOF

  chmod +x ~/projects/financial-qa/.git/hooks/pre-commit
  ```

- [ ] **9.5.5** Test hooks don't block legitimate work
  - Designer: Can commit to docs/specs/
  - Engineer: Can commit code
  - QA: Can commit tests
  - Verify violations are caught

### Phase 10: Documentation & Polish
- [ ] **10.1** Create workflow visualization diagram
  - ASCII art showing Feature → User Story flow
  - Add to CLAUDE.md

- [ ] **10.2** Create quick start guide in CLAUDE.md
  - New feature with UI? → /pm, /ui-designer, then user stories
  - Backend work? → Create issue, /work-story
  - Reviewing work? → /ui-designer, /qa, /engineer

- [ ] **10.3** Document error handling
  - What to do if story is blocked
  - Escalation paths
  - Manual intervention

- [ ] **10.4** Update README (if applicable)

### Phase 11: Migration & Cleanup
- [ ] **11.1** Migrate existing open issues to new label system
  - Review open issues
  - Add appropriate labels
  - Update to match new workflow

- [ ] **11.2** Commit all changes
  - Update CLAUDE.md
  - Update role commands
  - Add new autonomous commands
  - Remove work-story.md

- [ ] **11.3** Create PR for workflow changes
  - Title: "Implement async multi-agent workflow"
  - Body: Link to this implementation plan
  - Get human approval before merging

---

## Examples

### Branch Strategy Summary

**Two distinct branch patterns:**

1. **Feature Documentation (main branch)**
   - WHO: Designer creates design specs
   - BRANCH: `main`
   - PROCESS: Create spec → commit directly to main → push
   - RATIONALE: Low-risk documentation, fast iteration
   - EXAMPLE: See Example 1 below

2. **User Story Implementation (feature branch)**
   - WHO: Engineer creates branch, all agents contribute
   - BRANCH: `feature/US-X.X.X`
   - PROCESS: Engineer creates branch → Designer reviews/tweaks → QA tests → Engineer creates PR → Human merges
   - RATIONALE: All work for one story in one reviewable unit
   - EXAMPLE: See Example 2 below

---

### Example 1: Feature Workflow (Design Spec on Main Branch)

**PM creates feature:**
```bash
gh issue create \
  --title "Portfolio tracking page" \
  --label feature,needs-design-spec \
  --body "As an investor, I want to track my portfolio performance..."
# Creates issue #60
```

**Designer picks up work (autonomous):**
```bash
cd ~/projects/financial-designer
/work-designer

# Finds issue #60 (needs-design-spec)
# Works on main branch (specs go directly to main)

git checkout main
git pull origin main

# Creates design spec
vim docs/specs/portfolio-tracking.md
# ... creates comprehensive spec ...

# Commits directly to main (low-risk documentation)
git add docs/specs/portfolio-tracking.md
git commit -m "Add portfolio tracking design spec for #60"
git push origin main

# Updates GitHub issue
gh issue comment 60 --body "Design spec ready: docs/specs/portfolio-tracking.md"
gh issue edit 60 --remove-label needs-design-spec --add-label needs-pm-approval

# Reports completion
# "✅ Design spec created for #60. Awaiting PM approval."
```

**PM reviews (interactive or autonomous):**
```bash
/pm
# Reviews spec
# Approves
# Updates label: ready-for-stories
# Breaks into user stories:
#   - US-4.1.1: Portfolio summary dashboard
#   - US-4.1.2: Individual stock performance tracking
#   - US-4.1.3: Portfolio charts and visualizations
# Each story labeled: user-story, needs-test-plan
# Each story is sub-issue of #60
```

### Example 2: User Story Workflow - Shared Feature Branch (Happy Path)

**Story created:**
```
#61: US-4.1.1 - Portfolio summary dashboard
Labels: user-story, needs-test-plan
Parent: #60 (Portfolio tracking page)
```

**QA creates test plan (autonomous):**
```bash
cd ~/projects/financial-qa
/work-qa
# Finds #61
# Creates test plan in issue comment
# Updates label: ready-for-implementation
```

**Engineer implements (autonomous):**
```bash
cd ~/projects/financial-engineer
/work-engineer

# Checks WIP limit
gh issue list --label user-story --state open --json number,labels | jq '...'
# Result: No stories in progress ✅

# Finds #61 in ready-for-implementation queue
# Reads design spec: docs/specs/portfolio-tracking.md

# Creates feature branch (shared branch for all agents)
git checkout main
git pull origin main
git checkout -b feature/US-4.1.1

# Implements per spec
vim signaltrackers/portfolio.py
vim signaltrackers/templates/portfolio.html
# ... implementation work ...

# Commits implementation
git add signaltrackers/
git commit -m "Implement portfolio summary dashboard

- Add Portfolio model and data layer
- Create portfolio summary template
- Add route for /portfolio

Implements #61 per design spec."

# Pushes feature branch to origin (other agents will use this)
git push origin feature/US-4.1.1

# Updates GitHub issue
gh issue comment 61 --body "✅ Implementation complete. Ready for design review."
gh issue edit 61 --remove-label ready-for-implementation --add-label needs-design-review

# Reports completion
# "✅ Implemented #61. Pushed to feature/US-4.1.1. Awaiting design review."
```

**Designer reviews (autonomous):**
```bash
cd ~/projects/financial-designer
/work-designer

# Finds #61 needs-design-review
# Fetches latest from origin
git fetch origin

# Checks out Engineer's feature branch (shared branch)
git checkout feature/US-4.1.1

# Generates screenshots for review
docker compose up -d
sleep 8
node screenshots.spec.js
docker compose down

# Reviews screenshots against design spec (docs/specs/portfolio-tracking.md)
# Finds minor issue: Need to clarify responsive breakpoint in spec

# Updates spec for clarity (commits to same branch)
vim docs/specs/portfolio-tracking.md
# Add clarification about tablet breakpoint

git add docs/specs/portfolio-tracking.md
git commit -m "Clarify tablet breakpoint in portfolio spec

Minor spec update based on implementation review."

git push origin feature/US-4.1.1

# Updates GitHub issue
gh issue comment 61 --body "✅ Design review complete. Implementation matches spec.

Minor spec clarification added to feature branch. Approved for QA testing."

gh issue edit 61 --remove-label needs-design-review --add-label needs-qa-testing

# Reports completion
# "✅ Design review approved for #61. Spec clarification committed to feature/US-4.1.1."
```

**QA tests (autonomous):**
```bash
cd ~/projects/financial-qa
/work-qa

# Finds #61 needs-qa-testing
# Fetches latest from origin
git fetch origin

# Checks out feature branch (now has Engineer + Designer commits)
git checkout feature/US-4.1.1
git pull origin feature/US-4.1.1

# Runs tests against test plan
python -m pytest signaltrackers/tests/test_portfolio.py -v
# All tests pass ✅

# Optionally adds test files to branch
vim signaltrackers/tests/test_portfolio_integration.py
git add signaltrackers/tests/test_portfolio_integration.py
git commit -m "Add integration tests for portfolio dashboard"
git push origin feature/US-4.1.1

# Updates GitHub issue
gh issue comment 61 --body "✅ QA verification complete. All tests pass.

Test results:
- Unit tests: 12/12 passed
- Integration tests: 5/5 passed
- Manual testing: No issues found

Ready for PR creation."

gh issue edit 61 --remove-label needs-qa-testing --add-label ready-for-pr

# Reports completion
# "✅ QA approved for #61. All tests passing. Ready for PR."
```

**Engineer creates PR (autonomous):**
```bash
cd ~/projects/financial-engineer
/work-engineer

# Finds #61 ready-for-pr
# Checks out feature branch and pulls latest (has all commits from all agents)
git checkout feature/US-4.1.1
git pull origin feature/US-4.1.1

# Views all commits in this branch
git log main..HEAD
# Shows:
#   - Engineer: Implementation
#   - Designer: Spec clarification
#   - QA: Integration tests

# Creates PR with all work from all agents
gh pr create \
  --title "US-4.1.1: Portfolio summary dashboard" \
  --body "Fixes #61

## Summary
Implemented portfolio summary dashboard per design spec.

## Changes
- Portfolio data model and business logic (Engineer)
- Portfolio summary template with responsive layout (Engineer)
- Design spec clarification for tablet breakpoint (Designer)
- Integration test coverage (QA)

## Testing
- ✅ All unit tests passing (12/12)
- ✅ All integration tests passing (5/5)
- ✅ Design review approved
- ✅ Manual QA verification complete

## Screenshots
See design review comment on #61

Ready for human review and merge."

# Does NOT call gh pr merge (human must approve)

# Updates GitHub issue
gh issue comment 61 --body "✅ PR #92 created and ready for human review.

All agent reviews complete:
- Engineer: Implementation ✅
- Designer: Design compliance ✅
- QA: Test verification ✅

Awaiting human approval to merge."

# Reports completion
# "✅ PR #92 created for #61. All agent work complete. Awaiting human merge."
# "Pipeline will remain blocked until PR #92 is merged (WIP limit: 1)"
```

**Human reviews and merges:**
```bash
gh pr view 92
gh pr merge 92
# Issue #61 auto-closes
# Pipeline is now clear for next story
```

### Example 3: User Story with Iteration (Design Changes Loop)

**Story in progress:**
```
#62: US-4.1.2 - Individual stock performance tracking
Current state: needs-design-review
Branch: feature/US-4.1.2 (already created by Engineer)
```

**Designer finds issues (autonomous):**
```bash
cd ~/projects/financial-designer
/work-designer

# Finds #62 needs-design-review
git fetch origin
git checkout feature/US-4.1.2

# Reviews implementation
# Generates screenshots
# Compares against design spec

# Finds design issues:
#   - Touch targets too small (32px, should be 44px)
#   - Color contrast insufficient (3.2:1, should be 4.5:1)
#   - Layout doesn't match spec (stats should be collapsible)

# Comments on GitHub with detailed feedback
gh issue comment 62 --body "Design review: Changes needed

Issues found:
1. Touch targets too small
   - Current: 32px buttons
   - Required: 44px minimum per design system
   - Files: templates/stock-performance.html

2. Color contrast insufficient
   - Current: #777 on #fff (3.2:1)
   - Required: 4.5:1 minimum
   - Use design system color: var(--text-secondary)

3. Stats layout
   - Should be collapsible sections per spec
   - Currently all expanded

Please fix and update label to needs-design-review when ready."

# Updates label (back to Engineer)
gh issue edit 62 --remove-label needs-design-review --add-label needs-design-changes

# Reports completion
# "🔄 Design review found issues for #62. Feedback provided, awaiting fixes."
```

**Engineer fixes (autonomous):**
```bash
cd ~/projects/financial-engineer
/work-engineer

# Checks WIP limit
# Story #62 still in flight, but I created it, so I can continue working on it

# Finds #62 needs-design-changes
git checkout feature/US-4.1.2
git pull origin feature/US-4.1.2  # Get any Designer commits

# Reads Designer's feedback from issue comments
gh issue view 62

# Makes fixes
vim signaltrackers/templates/stock-performance.html
# Fix 1: Increase button sizes to 44px
# Fix 2: Use design system color variables
# Fix 3: Add collapsible sections for stats

# Commits fixes to same branch
git add signaltrackers/templates/
git commit -m "Fix design issues per review feedback

- Increase touch targets to 44px (accessibility)
- Use design system color variables for proper contrast
- Make stats sections collapsible per spec

Addresses design review feedback on #62"

git push origin feature/US-4.1.2

# Updates GitHub
gh issue comment 62 --body "✅ Design issues fixed:
- Touch targets increased to 44px
- Color contrast now meets 4.5:1 standard
- Stats sections now collapsible

Ready for re-review."

gh issue edit 62 --remove-label needs-design-changes --add-label needs-design-review

# Reports completion
# "✅ Fixed design issues for #62. Re-submitted for design review."
```

**Designer re-reviews:**
```bash
cd ~/projects/financial-designer
/work-designer

# Finds #62 needs-design-review (round 2)
git checkout feature/US-4.1.2
git pull origin feature/US-4.1.2  # Get Engineer's fixes

# Generates new screenshots
docker compose up -d && sleep 8 && node screenshots.spec.js && docker compose down

# Reviews fixes
# All issues resolved ✅

gh issue comment 62 --body "✅ Design re-review complete. All issues resolved.

Verified:
- Touch targets: 44px ✅
- Color contrast: 4.5:1 ✅
- Collapsible stats: Working as specified ✅

Approved for QA testing."

gh issue edit 62 --remove-label needs-design-review --add-label needs-qa-testing

# Reports completion
# "✅ Design approved for #62 after iteration. Proceeding to QA."
```

**Then QA tests, Engineer creates PR (same as Example 2)**

---

## Migration Notes

### For Existing Open Issues
1. Review each open issue
2. Determine if it's a `feature` or `user-story`
3. Add appropriate workflow state label
4. Add to correct phase of pipeline

### For Existing Context Files
1. Move from `docs/roles/` to `~/.claude/projects/financial/roles/`
2. Update any absolute path references
3. Git ignore `docs/roles/` to prevent future commits

### For Existing Branches
1. Clean up old feature branches if not needed
2. Ensure main is up to date in all checkouts

---

## Error Handling

### Blocked Stories
If a story is blocked:
1. Add label: `blocked`
2. Comment explaining blocker
3. Optionally add: `needs-human-decision` if needs escalation
4. Human reviews and resolves

### Infinite Loops
If Designer/Engineer loop more than 3 times:
1. Add label: `needs-escalation`
2. Comment: "Design/implementation iterations exceeded 3. Needs PM decision."
3. PM reviews and provides direction

### Agent Failures
If an autonomous agent fails mid-task:
1. Issue remains in current state (label unchanged)
2. Next agent run will find it and retry
3. If fails 3 times, add `blocked` label

---

## Future Enhancements

### After Initial Rollout
- [ ] Add observability dashboard (what's in flight, what's blocked)
- [ ] Add `/status` command (show workflow pipeline state)
- [ ] Add cost tracking (API usage per agent)
- [ ] Add workflow metrics (time in each state, iteration counts)

### Scaling
- [ ] Increase WIP limit from 1 to 3 stories
- [ ] Consider database-backed state if labels insufficient
- [ ] Add agent-to-agent direct communication
- [ ] Parallel story implementation (multiple engineers)

### Advanced Features
- [ ] Auto-merge for low-risk changes (docs, tests)
- [ ] Automated regression testing before PR creation
- [ ] Integration with CI/CD for automated testing
- [ ] Slack/Discord notifications for workflow events

---

## Success Metrics

### Phase 1 (First 10 Stories)
- [ ] All stories follow the workflow correctly
- [ ] No major blockers or infinite loops
- [ ] Human review time < 15 minutes per PR
- [ ] Agents correctly enforce WIP limit

### Phase 2 (Stories 11-50)
- [ ] Workflow feels smooth and natural
- [ ] Iteration loops (design/QA) resolve within 2 cycles
- [ ] No lost work or major conflicts
- [ ] Ready to increase WIP limit

### Long-term
- [ ] Higher throughput than previous synchronous workflow
- [ ] Lower human cognitive load (agents handle coordination)
- [ ] Better code quality (thorough review at each stage)
- [ ] Clear audit trail (GitHub issues show full history)

---

## Rollback Plan

If this doesn't work:
1. Keep the multiple checkouts (still useful)
2. Revert to synchronous `/work-story` command
3. Keep context files outside repo (still useful)
4. Document lessons learned
5. Try alternative approach (e.g., simpler state machine)

---

## Questions & Decisions Log

### 2026-02-21: Initial Planning
**Q:** Should we use one async workflow or keep sync as option?
**A:** One async workflow. Sync adds complexity without clear benefit.

**Q:** How to handle file conflicts with concurrent agents?
**A:** Multiple repo checkouts (one per agent).

**Q:** Where to store agent context?
**A:** Outside repo (~/.claude/projects/financial/roles/).

**Q:** Should agents auto-merge code?
**A:** No. Agents create PRs, humans merge. Exception for docs.

**Q:** How many stories in flight initially?
**A:** WIP limit of 1. Can increase later.

**Q:** How to control autonomous vs interactive mode?
**A:** Separate commands (/ui-designer vs /work-designer).

---

## Appendix: Command Reference

### Interactive Commands (Discussion)
- `/pm` - Product Manager (discuss strategy, answer questions)
- `/ui-designer` - UI/UX Designer (discuss design, review specific work)
- `/engineer` - Engineer (discuss code, answer questions)
- `/qa` - QA Tester (discuss testing, answer questions)

### Autonomous Commands (Work Processing)
- `/work-pm` - Check PM queue, review/approve specs
- `/work-designer` - Check design queue, create specs or review implementations
- `/work-engineer` - Check engineering queue, implement stories
- `/work-qa` - Check QA queue, create test plans or verify implementations

### Utility Commands (Future)
- `/status` - Show workflow pipeline state
- `/check-work` - List pending work without processing

---

**End of Implementation Plan**
