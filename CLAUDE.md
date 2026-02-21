# Claude Code Instructions

## Project Overview
SignalTrackers is a Python macro financial dashboard providing comprehensive market intelligence for individual investors.

## Workflows Overview

This project uses **two distinct async workflows**. Choose based on the type of work:

### Feature Workflow (New Features)

Use when adding new functionality. If the feature requires UI changes, include the design spec step. If backend-only, skip directly to breaking into user stories.

**UI feature path:**
```
PM creates feature → Designer creates spec → PM approves → PM creates user stories → stories completed → PM closes feature
```

**Backend-only path:**
```
PM creates feature → PM creates user stories directly → stories completed → PM closes feature
```

| Step | Who | Label Transition |
|------|-----|-----------------|
| Create feature issue | PM | `feature` |
| *If UI changes:* add to design queue | PM | + `needs-design-spec` |
| Create design spec in `docs/specs/` | Designer | → `needs-pm-approval` |
| Review and approve spec | PM | → `ready-for-stories` |
| *If backend-only:* skip design steps | PM | — |
| Break into user stories | PM | remove `ready-for-stories` (if set); each story → `user-story + needs-test-plan` |
| Stories in progress | — | no feature label; GitHub sub-issue progress shows status |
| All stories merged | PM (auto-detects on next `/work-pm` run) | close feature issue |

### User Story Workflow (Implementation Pipeline)

Use when implementing user stories, fixing bugs, or any code changes.

**WIP Limit: 1 story at a time in the implementation pipeline.**

```
QA creates test plan → Engineer implements → Designer reviews → QA tests → Engineer creates PR → Human merges
```

| Step | Who | Label Transition |
|------|-----|-----------------|
| Create test plan | QA | `needs-test-plan` → `ready-for-implementation` |
| Implement on `feature/US-X.X.X` branch | Engineer | → `needs-design-review` (UI) or `needs-qa-testing` |
| Review implementation | Designer | → `needs-qa-testing` or `needs-design-changes` |
| Fix design issues | Engineer | → back to `needs-design-review` |
| Test against test plan | QA | → `ready-for-pr` or `needs-fixes` |
| Fix QA bugs | Engineer | → back to `needs-qa-testing` |
| Create PR (do NOT merge) | Engineer | PR created |
| Review and merge | **Human** | Issue auto-closes |

### Quick Reference

| Situation | Workflow |
|-----------|----------|
| New feature with UI changes | Feature Workflow → User Story Workflow |
| Backend-only new feature | Create issue → User Story Workflow |
| Bug fix | User Story Workflow (skip to `needs-test-plan`) |
| Design spec update | Feature Workflow (Designer commits to `main`) |
| Documentation update | Direct commit to `main` |

---

## Roles Overview

| Role | Command | Mode | When to Use |
|------|---------|------|-------------|
| Product Manager | `/pm` | Interactive | Strategy discussions, writing user stories, product decisions |
| UI/UX Designer | `/ui-designer` | Interactive | Design discussions, spec review, UI feedback |
| Engineer | `/engineer` | Interactive | Code questions, architecture decisions, implementation help |
| QA | `/qa` | Interactive | Testing strategy, bug triage, quality questions |
| PM (autonomous) | `/work-pm` | Autonomous | Process PM queue: approve specs, break features into stories, close completed features |
| Designer (autonomous) | `/work-designer` | Autonomous | Process design queue: create specs, review implementations |
| Engineer (autonomous) | `/work-engineer` | Autonomous | Process engineering queue: implement stories, create PRs |
| QA (autonomous) | `/work-qa` | Autonomous | Process QA queue: create test plans, verify implementations |

### Interactive vs Autonomous

- **Interactive** (`/pm`, `/ui-designer`, `/engineer`, `/qa`) — Discuss, advise, answer questions. **Does NOT autonomously check for or pick up work from GitHub queues.**
- **Autonomous** (`/work-pm`, `/work-designer`, `/work-engineer`, `/work-qa`) — Check GitHub label queues, pick up work, process it, and move the pipeline forward.

---

## Memory Management

All roles store context **outside the repo** to prevent git conflicts.

### Context File Locations

```
~/.claude/projects/financial/roles/
├── pm-context.md           # Roadmap, active work, key decisions
├── ui-designer-context.md  # Design system, active features, design decisions
├── engineer-context.md     # Architecture, patterns, tech debt
└── qa-context.md           # Test coverage, known issues, test decisions
```

These are working notes — **never committed to git**.

### Rules for All Roles

- Keep context files under 300 lines
- Read your context file at the start of every session
- Update your context file at the end of every session with key decisions
- Archive old resolved items — keep only a one-line summary
- Prioritize recent, actionable information over historical detail

---

## Project Management

This project uses GitHub for work management. Always check GitHub for open work and update issues as you complete tasks.

### Structure
- **Project**: SignalTrackers Product Roadmap (https://github.com/users/EricMaibach/projects/1)
- **Milestones**: Group work by release phase (run `gh api repos/:owner/:repo/milestones` to see current milestones)
- **Issues**: Features (`feature` label), bugs (`bug` label), and tasks with full detail

### Workflow
1. **Starting a session**: Run `gh issue list` to see open work
2. **Before starting work**: Check issue details with `gh issue view <number>`
3. **When work is complete**: Create a PR with `Fixes #<number>` in the description - issue auto-closes on merge
4. **Discovered new work**: Create issues with `gh issue create` and assign to appropriate milestone

### Creating User Stories for Features
When breaking down a feature into implementable work:
1. Review the feature issue to understand requirements
2. Create user stories with the `user-story` label, each containing:
   - User story format: "As a [user], I want [goal], so that [benefit]"
   - Acceptance criteria with checkboxes
   - Implementation notes (files to modify, code patterns to follow)
   - Testing requirements
3. Add each user story to the project board
4. Set priority (P0-P3) based on dependencies and importance
5. Add user stories as sub-issues of the parent feature
6. Order by implementation sequence (dependencies first)

### Issue Labels

#### Type Labels (Issue Classification)
- `feature` - Strategic work requiring PM + Designer definition
- `user-story` - Implementation work for QA → Engineer → Designer → QA pipeline
- `bug` - Defects to fix

#### Feature Workflow States
| Label | Meaning | Who Acts |
|-------|---------|----------|
| `needs-design-spec` | Feature needs design specification created | Designer |
| `needs-pm-approval` | Designer completed spec — PM review needed | PM |
| `ready-for-stories` | PM approved spec — break into user stories | PM |
| *(no label)* | Stories in progress (or complete — PM auto-detects on next `/work-pm` run) | PM (auto) |

#### User Story Workflow States
| Label | Meaning | Who Acts |
|-------|---------|----------|
| `needs-test-plan` | QA must create a test plan | QA |
| `ready-for-implementation` | Test plan done — Engineer can pick up (if no WIP) | Engineer |
| `needs-design-review` | Implementation ready — Designer reviews | Designer |
| `needs-design-changes` | Designer requested changes — Engineer fixes | Engineer |
| `needs-qa-testing` | Ready for QA verification | QA |
| `needs-fixes` | QA found bugs — Engineer fixes before re-test | Engineer |
| `ready-for-pr` | QA approved — Engineer creates PR (do not merge) | Engineer |

#### Blocking / Meta States
| Label | Meaning | Who Acts |
|-------|---------|----------|
| `blocked` | Work is blocked, needs human intervention | Human |
| `needs-clarification` | Requirements unclear, needs PM or human input | PM / Human |
| `needs-human-decision` | Escalated — requires human decision to proceed | Human |

### Priority
All bugs and user stories should be assigned a priority in the project board:
- **P0 - Critical**: Drop everything, fix immediately
- **P1 - High**: Next up, important work
- **P2 - Medium**: Standard priority
- **P3 - Low**: Nice to have, when time permits

### Issue Hierarchy
Features should have user stories as **sub-issues** (not just references):
- Create the feature issue first with `feature` label
- Create user stories with `user-story` label
- Add user stories as sub-issues of the feature (see commands below)
- When user stories are closed, the feature shows progress

### Branch Strategy

| Work Type | Branch | Who Commits | Push Strategy |
|-----------|--------|-------------|---------------|
| Feature specs | `main` | Designer only | Direct push to main |
| Product roadmap | `main` | PM (rare) | Direct push to main |
| Design system | `main` | Designer | Direct push to main |
| User story | `feature/US-X.X.X` | Engineer, Designer, QA | Shared branch, all push |
| Bug fixes | `fix/bug-description` | Engineer | Same as user story |

#### Two Branch Patterns

**1. Feature Documentation (main branch)**
- WHO: Designer creates specs, PM updates roadmap (rarely)
- BRANCH: `main`
- PROCESS: Create/update file → commit directly to main → push
- RATIONALE: Low-risk documentation, enables fast iteration without PR overhead

**2. User Story Implementation (feature branch)**
- WHO: Engineer creates branch, all agents contribute
- BRANCH: `feature/US-X.X.X`
- PROCESS: Engineer creates branch → Designer reviews/tweaks → QA tests → Engineer creates PR → Human merges
- RATIONALE: All work for one story in one reviewable unit, with human approval gate

#### Branch Workflow Steps

1. **Engineer** creates `feature/US-X.X.X` from main, implements, pushes to origin
2. **Designer** fetches, checks out the branch, reviews implementation, optionally commits spec clarifications, pushes
3. **QA** fetches, checks out the branch, tests, optionally commits test files, pushes
4. **Engineer** creates a single PR containing all commits from all agents
5. **Human** reviews and merges the entire branch — issue auto-closes via "Fixes #X"

See `docs/ASYNC-WORKFLOW-IMPLEMENTATION-PLAN.md` for detailed examples of both patterns.

### Documentation Split

| What | Where | Purpose |
|------|-------|---------|
| **Strategy & Vision** | `docs/PRODUCT_ROADMAP.md` | Product vision, success metrics, what we're NOT building, backlog |
| **Active Work** | GitHub Issues & Milestones | Features, bugs, tasks with full implementation detail |

- **PRODUCT_ROADMAP.md** answers "What is this product and where is it going?"
- **GitHub Issues** answer "What exactly are we building and how?"

When adding new features:
1. If it's a new strategic direction or vision change → Update PRODUCT_ROADMAP.md
2. If it's actionable work to implement → Create a GitHub Issue

### Role Communication

#### Addressing Roles in Issue/PR Comments

When you need a specific role to act, prefix your comment with their role name — this makes it searchable:

```
Designer: Please review the mobile layout implementation
PM: Should we include dark mode in this story or defer?
QA: Ready for testing, all acceptance criteria met
Engineer: Implementation question about the API endpoint
```

#### Key Principles

1. **PM owns WHAT and WHY** — Product decisions, priorities, business goals
2. **Designer owns HOW (UX)** — User experience, interaction design, visual design
3. **Engineer owns HOW (Technical)** — Implementation, architecture, code quality
4. **QA owns QUALITY** — Test plans, verification, bug reporting
5. **GitHub Issues** — Discussion, questions, decisions, status tracking
6. **Spec Files** — Detailed design documentation, versioned with code

#### Repository Organization

```
docs/
  specs/                    # Design specifications (Designer creates, on main)
  design-system.md          # Design system reference
  PRODUCT_ROADMAP.md        # Product vision and strategy
signaltrackers/             # Application code (Engineer)
tests/                      # Test files (QA)
```

Agent context files live **outside the repo** at `~/.claude/projects/financial/roles/` — see Memory Management above.

## GitHub Commands

Authoritative command reference. Role command files reference this section.

### Issues

```bash
# List open issues
gh issue list

# List by label (use for queue processing)
gh issue list --label needs-design-spec --state open
gh issue list --label ready-for-implementation --state open
gh issue list --label needs-qa-testing --state open

# View issue details
gh issue view <number>

# Create a new issue
gh issue create --title "Title" --label "feature" --milestone "<milestone-name>"

# Add/remove labels
gh issue edit <number> --add-label needs-design-review
gh issue edit <number> --remove-label needs-test-plan --add-label ready-for-implementation

# Comment on an issue
gh issue comment <number> --body "Comment text here"

# Close an issue
gh issue close <number> --comment "Completed by..."
```

### Pull Requests

```bash
# Create a PR that auto-closes an issue on merge
gh pr create \
  --title "US-X.X.X: Story title" \
  --base main \
  --body "Fixes #<number>

## Summary
...

## Testing
- ✅ All tests passing
- ✅ Design review approved
- ✅ QA verification complete"

# View PR
gh pr view <number>

# List open PRs
gh pr list
```

### Project Board

```bash
# List milestones
gh api repos/:owner/:repo/milestones | jq -r '.[].title'

# Add issue to project board
gh project item-add 1 --owner @me --url <issue-url>

# Set priority on a project item
# Step 1 — get item ID:
gh project item-list 1 --owner @me --format json | jq '.items[] | select(.content.number == <issue-number>)'
# Step 2 — set priority (option IDs: P0=feb8faa0, P1=2d29e952, P2=5a6e367a, P3=76b63ab5):
gh project item-edit --project-id PVT_kwHOAFS-6M4BO0V5 --id <item-id> --field-id PVTSSF_lAHOAFS-6M4BO0V5zg9c5n0 --single-select-option-id <option-id>
```

### Sub-Issues (Feature → User Story Hierarchy)

```bash
# Step 1 — get issue node IDs:
gh api graphql -f query='{ repository(owner: "EricMaibach", name: "financial") { issue(number: <num>) { id } } }'

# Step 2 — add user story as sub-issue of a feature:
gh api graphql -f query='mutation { addSubIssue(input: { issueId: "<parent-id>", subIssueId: "<child-id>" }) { issue { id } } }'
```

### Labels

```bash
# List all labels
gh label list

# Create a label
gh label create "label-name" --description "What it means" --color "RRGGBB"
```

## Technical Notes

### Running the Application
```bash
docker compose up
```

### Key Directories
- `signaltrackers/` - Main application code
- `signaltrackers/templates/` - Jinja2 HTML templates
- `signaltrackers/static/` - CSS, JS, images
- `signaltrackers/data/` - CSV data files for metrics
- `docs/` - Documentation and specifications

### Data Collection
```bash
python signaltrackers/market_signals.py
```

### Environment Configuration (.env file)
**CRITICAL RULE**: **NEVER EDIT THE `.env` FILE - EVER**

The `.env` file contains sensitive, production configuration that is excluded from git (no backup exists).

**When adding new environment variables:**
1. **ONLY edit `.env.example`** - Add new variables with placeholder values and comments
2. **Ask the user** to manually add the variable to their `.env` file
3. **Document the new variable** in the .env.example comments

**You may ONLY:**
- Read `.env` to understand current configuration
- Edit `.env.example` to document new variables

**You may NEVER:**
- Write to `.env`
- Edit `.env`
- Modify `.env` in any way
- Run `git add .env` or add `.env` to git in any way
- Commit `.env` to git (it's in .gitignore for a reason)

If you need to add environment configuration, update `.env.example` and inform the user to update their `.env` file manually.

**The .env file contains sensitive credentials and must NEVER be committed to git.**
