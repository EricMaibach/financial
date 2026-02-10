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
3. **When work is complete**: Close the issue with `gh issue close <number> --comment "Description of what was done"`
4. **Discovered new work**: Create issues with `gh issue create` and assign to appropriate milestone

### Issue Labels
- `feature` - Product features from the roadmap
- `bug` - Defects to fix
- `user-story` - Granular user stories within a feature

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

# List milestones
gh api repos/:owner/:repo/milestones | jq -r '.[].title'

# Add issue to project
gh project item-add 1 --owner @me --url <issue-url>
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
