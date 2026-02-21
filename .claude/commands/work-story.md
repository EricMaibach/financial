# Work User Story Workflow

You are a workflow orchestrator. Given a user story, you will execute 
the following phases sequentially, adopting each role's perspective 
as you go.

## Input
The user stories are in Github, ask the user what user story they would like you to work on before beginning.

## Phase 1: Setup
- Create a feature branch: feature/{story-id}
- Make sure the feature branch is checked out locally so all work is captured in feature branch
- Create a docs/test-plans/{story-id}-workflow-log.md file to be a running log.

## Phase 2: QA Test Planning
Adopt the QA Test Engineer mindset. Read .claude/commands/qa.md for 
your instructions.
- Review the user story and acceptance criteria
- Write a test plan with specific test cases covering: happy path, 
  edge cases, error handling, security considerations
- Save the test plan to the Github issue
- Log: "✅ Phase 1 Complete: Test plan created"

## Phase 3: Implementation
Adopt the Senior Engineer mindset. Read .claude/commands/engineer.md
for your instructions.
- Create a feature branch: feature/{story-id}
- Review the test plan on the user story from Phase 1 so you know what you're building toward
- Review the design spec (if exists) from docs/specs/ to understand visual requirements
- Implement the feature according to the user story and acceptance criteria
- Write unit tests alongside your code
- Log: "✅ Phase 2 Complete: Implementation done"

## Phase 4: Designer Review (UI Changes Only)
**Determine if this story involves UI changes** (templates, CSS, components, layouts).

**If YES - UI changes present:**
- Adopt the UI Designer mindset. Read .claude/commands/ui-designer.md for your instructions.
- Generate screenshots for review:
  - Run Playwright screenshot script: `npx playwright test screenshots.spec.js`
  - Or use existing screenshots from screenshots/ folder
  - View screenshots at mobile (375px), tablet (768px), desktop (1920px)
- Review implementation against design spec (docs/specs/)
- Verify:
  - Visual compliance (colors, spacing, typography match design system)
  - Responsive behavior (mobile/tablet/desktop layouts correct)
  - Interaction patterns (animations, states, progressive disclosure)
  - Accessibility basics (touch targets ≥44px, color contrast, keyboard nav)
  - Design system usage (CSS custom properties, component patterns)
- Comment on Github issue with design review:
  - "✅ Design approved - matches design spec" OR
  - "Changes requested: [specific design issues with spec line references]"
- If changes requested: Return to Phase 3 (Engineer fixes), then re-review
- Log: "✅ Phase 3 Complete: Design review approved"

**If NO - Backend/data changes only:**
- Skip designer review
- Log: "⏭️ Phase 3 Skipped: No UI changes, proceeding to QA"

## Phase 5: QA Verification
Adopt the QA Test Engineer mindset again.
- Review the implementation against the test plan from Phase 1
- Run existing tests and verify they pass
- Write integration/e2e tests for the feature
- Create a review on the Github issue with:
  - PASS/FAIL status for each test case
  - Any bugs or concerns found
  - Overall verdict: APPROVED or CHANGES_REQUESTED
- Log: "✅ Phase 4 Complete: QA review filed"

## Phase 6: Resolution
If QA verdict is APPROVED:
  - Adopt Engineer mindset
  - Create the PR with a summary of changes and test results
  - PR description should include:
    - "Fixes #{story-id}"
    - Link to design spec (if UI changes): "Implements [docs/specs/...]"
    - Summary of changes
    - Test results
  - Log: "✅ Phase 5 Complete: PR created and ready for merge"

If QA verdict is CHANGES_REQUESTED:
  - Adopt Engineer mindset
  - Read the QA review and fix each issue
  - Log what was fixed
  - Return to Phase 5 for re-testing (max 3 cycles, then stop and report remaining issues)

## Rules
- Between phases, briefly state which role you're switching to
- If you hit ambiguity in the user story, stop and ask rather than assuming
- Do not skip phases