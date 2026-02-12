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

If you need to add environment configuration, update `.env.example` and inform the user to update their `.env` file manually.
