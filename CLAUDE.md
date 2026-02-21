# Claude Code Instructions

## Project Overview
SignalTrackers is a Python macro financial dashboard providing comprehensive market intelligence for individual investors.

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
- `feature` - Product features from the roadmap
- `bug` - Defects to fix
- `user-story` - Granular user stories within a feature

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

### Collaboration Workflow: PM → Designer → Engineer

This project uses a structured handoff process between roles to ensure clear communication and quality deliverables.

#### Phase 1: Feature Definition (Product Manager)

**PM Responsibilities:**
- Create GitHub issue with feature/user story
- Include user story format: "As a [user], I want [goal], so that [benefit]"
- Define acceptance criteria with checkboxes
- Set priority and assign to milestone
- Tag appropriately (`feature`, `user-story`, `bug`)

**Outputs:**
- GitHub issue with clear requirements
- Acceptance criteria defined
- Priority set

#### Phase 2: Design Specification (UI Designer)

**Designer Responsibilities:**
- Review GitHub issue for design implications
- Ask clarifying questions as issue comments
- Create detailed design specification in `docs/specs/feature-name.md`
- Comment on issue with link to spec file
- Iterate with PM until design is approved

**Design Spec Contains:**
- Detailed wireframes (mobile/tablet/desktop)
- Interaction patterns and behavior
- Component specifications
- Responsive breakpoint behavior
- Design system references
- Implementation notes for engineers
- Accessibility requirements

**Workflow:**
```
1. Designer comments: "Reviewing this feature, will create design spec"
2. Designer asks PM questions if needed (in issue comments)
3. Designer creates docs/specs/feature-name.md
4. Designer comments: "Design spec ready: [link to spec]"
5. PM reviews spec, provides feedback
6. Designer updates spec based on feedback
7. Designer comments: "Spec finalized and ready for engineering"
```

**Outputs:**
- `docs/specs/feature-name.md` with comprehensive design specification
- Issue comment linking to spec file
- PM approval documented in issue

#### Phase 3: Implementation (Engineer)

**Engineer Responsibilities:**
- Implement from design specification
- Follow design system standards ([docs/design-system.md](docs/design-system.md))
- Create PR that references both issue and spec file
- Request design review before merging

**Workflow:**
```
1. Engineer comments: "Starting implementation from [spec file]"
2. Engineer builds according to spec
3. Engineer creates PR:
   - Title describes the change
   - Body includes "Fixes #<number>"
   - Body links to spec file: "Implements [docs/specs/feature-name.md]"
4. Designer reviews PR for design compliance
5. PM validates against acceptance criteria
6. PR merged, issue auto-closes
```

**Outputs:**
- Working implementation matching design spec
- PR with issue and spec references
- Designer and PM approval

#### File Organization

```
docs/
  specs/                           # Design specifications (Designer creates)
    feature-name.md
    component-name-spec.md
  design-system.md                 # Design system reference
  PRODUCT_ROADMAP.md               # Product vision and strategy
  roles/                           # Role-specific context/memory
    pm-context.md
    ui-designer-context.md
```

#### Key Principles

1. **PM owns WHAT and WHY** - Product decisions, priorities, business goals
2. **Designer owns HOW (UX)** - User experience, interaction design, visual design
3. **Engineer owns HOW (Technical)** - Implementation, architecture, code quality
4. **GitHub Issues** - Discussion, questions, decisions, status tracking
5. **Spec Files** - Detailed design documentation, versioned with code
6. **Clear Handoffs** - Each role explicitly signals completion to next role

#### Example Flow

**Scenario: Explorer Mobile Redesign**

1. **PM** creates issue #50: "Explorer page mobile-first redesign"
   - User story with acceptance criteria
   - Priority P1, assigned to current milestone

2. **Designer** reviews and comments:
   - "Will create design spec. Question: Should any stats be above chart?"

3. **PM** responds:
   - "Chart should be primary, all stats can be below/collapsible"

4. **Designer** creates `docs/specs/explorer-mobile-redesign.md`
   - Mobile wireframe with chart prominence
   - Collapsible stats sections
   - Links to design system patterns

5. **Designer** comments on #50:
   - "Design spec ready: docs/specs/explorer-mobile-redesign.md"
   - "@pm please review"

6. **PM** approves:
   - "Design looks great, approved for engineering"

7. **Engineer** implements and creates PR:
   - "Fixes #50"
   - "Implements docs/specs/explorer-mobile-redesign.md"

8. **Designer** reviews PR for design compliance
9. **PM** validates against acceptance criteria
10. PR merged, #50 auto-closes

### Role-Based Collaboration Protocol

This section defines how roles communicate and manage work autonomously in GitHub.

#### Addressing Roles in GitHub

When you need a specific role to review, respond, or take action, use clear role mentions:

**In Issue/PR Comments:**
```
Designer: Please review the mobile layout implementation
PM: Should we include dark mode in this story or defer?
QA: Ready for testing, all acceptance criteria met
Engineer: Implementation question about the API endpoint
```

**Using GitHub Labels for Workflow States:**
- `needs-design-spec` - Feature needs design specification created
- `needs-design-review` - Implementation/PR ready for designer approval
- `needs-pm-review` - Awaiting PM decision or approval
- `needs-qa-testing` - Ready for QA verification

**Why This Works:**
- Text mentions are searchable in GitHub (search for "Designer:" in comments)
- Labels are filterable in GitHub UI and API (`gh issue list --label needs-design-review`)
- Clear and unambiguous - no special syntax to remember
- Works with existing GitHub features

#### Autonomous Role Behavior

When a role is invoked via their skill command (e.g., `/ui-designer`, `/pm`, `/qa`), they should:

1. **Check for active workflow context first**
   - If there's a specific user story or feature being discussed in recent messages
   - If the conversation is clearly focused on one task
   - → **FOCUSED MODE**: Work only on that specific task, don't search for other work

2. **If no specific context (starting fresh)**
   - User invoked the role command without ongoing work
   - → **AUTONOMOUS MODE**: Check for pending work assigned to that role and proactively address it

**IMPORTANT:** When a role is invoked as part of a workflow command (e.g., `/work-story`), the role should focus ONLY on the specific task in the workflow context, not autonomously search for other work.

#### Role-Specific Autonomous Checklists

**UI Designer** (when in autonomous mode):
1. Check for new features needing design specs (`gh issue list --label feature,needs-design-spec`)
2. Check for comments addressed to designer (search for "Designer:" in recent issues)
3. Check for new user stories under features already designed (tracked in `docs/roles/ui-designer-context.md`)
4. Check for PRs ready for design review (`gh pr list --label needs-design-review`)

**Product Manager** (when in autonomous mode):
1. Check for features awaiting PM approval (`gh issue list --label needs-pm-review`)
2. Check for comments addressed to PM (search for "PM:" in recent issues)
3. Review and prioritize new feature requests
4. Check for completed features needing product validation

**QA** (when in autonomous mode):
1. Check for user stories ready for testing (`gh issue list --label user-story,needs-qa-testing`)
2. Check for comments addressed to QA (search for "QA:" in recent issues)
3. Check for PRs ready for QA validation
4. Review test plan coverage for new features

**Engineer** (when in autonomous mode):
1. Check for user stories ready for implementation (approved design specs, not in progress)
2. Check for comments addressed to Engineer (search for "Engineer:" in recent issues)
3. Check for PRs needing engineering review
4. Address technical debt and bug fixes

#### Example Autonomous Session

**Scenario:** User invokes `/ui-designer` with no specific context

Designer should:
```
1. Check for new features needing design specs
   → gh issue list --label feature,needs-design-spec --state open
   → If found: Review feature, create design spec, comment on issue

2. Check for comments addressed to designer
   → Search recent comments on open issues for "Designer:"
   → If found: Respond to questions with design guidance

3. Check active features (from docs/roles/ui-designer-context.md)
   → For each feature I've designed: Check for new user stories or PRs
   → Review user stories for design compliance
   → Review PRs for design implementation quality

4. Check for PRs needing design review
   → gh pr list --label needs-design-review --state open
   → Review screenshots, provide approval or request changes

5. Update role context with completed work
   → Update docs/roles/ui-designer-context.md with progress
```

## Common Commands

```bash
# List open issues
gh issue list

# View issue details
gh issue view <number>

# Close an issue when done
gh issue close <number> --comment "Fixed by..."

# Create a new issue (use --milestone to assign to a milestone)
gh issue create --title "Title" --label "bug" --milestone "<milestone-name>"

# Create PR that auto-closes issue on merge
gh pr create --title "Title" --body "Fixes #<number>"

# List milestones
gh api repos/:owner/:repo/milestones | jq -r '.[].title'

# Add issue to project
gh project item-add 1 --owner @me --url <issue-url>

# Set priority on a project item (requires item ID and option ID)
# First get item ID: gh project item-list 1 --owner @me --format json | jq '.items[] | select(.content.number == <issue-number>)'
# Priority option IDs: P0=feb8faa0, P1=2d29e952, P2=5a6e367a, P3=76b63ab5
gh project item-edit --project-id PVT_kwHOAFS-6M4BO0V5 --id <item-id> --field-id PVTSSF_lAHOAFS-6M4BO0V5zg9c5n0 --single-select-option-id <option-id>

# Add sub-issue to a parent feature (requires issue node IDs)
# First get issue IDs: gh api graphql -f query='{ repository(owner: "EricMaibach", name: "financial") { issue(number: <num>) { id } } }'
gh api graphql -f query='mutation { addSubIssue(input: { issueId: "<parent-id>", subIssueId: "<child-id>" }) { issue { id } } }'
```

## Technical Notes

### Running the Application
```bash
cd signaltrackers
python dashboard.py
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
