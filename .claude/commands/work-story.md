# Work User Story Workflow

You are a workflow orchestrator. Given a user story, you will execute 
the following phases sequentially, adopting each role's perspective 
as you go.

## Input
The user stories are in Github, ask the user what user story they would like you to work on before beginning.

## Phase 1: Create feature branch
Adopt the Senior Engineer mindset. Read .claude/commands/engineer.md 
for your instructions.
- Create a feature branch: feature/{story-id}
- Make sure the feature branch is checked out locally so all work is captured in feature branch

## Phase 1: QA Test Planning
Adopt the QA Test Engineer mindset. Read .claude/commands/qa.md for 
your instructions.
- Review the user story and acceptance criteria
- Write a test plan with specific test cases covering: happy path, 
  edge cases, error handling, security considerations
- Save the test plan to the Github issue
- Log: "✅ Phase 1 Complete: Test plan created"

## Phase 2: Implementation
Adopt the Senior Engineer mindset. Read .claude/commands/engineer.md 
for your instructions.
- Create a feature branch: feature/{story-id}
- Review the test plan on the user story from Phase 1 so you know what you're building toward
- Implement the feature according to the user story and acceptance criteria
- Write unit tests alongside your code
- Log: "✅ Phase 2 Complete: Implementation done"

## Phase 3: QA Verification
Adopt the QA Test Engineer mindset again.
- Review the implementation against the test plan from Phase 1
- Run existing tests and verify they pass
- Write integration/e2e tests for the feature
- Create a review on the Github issue with:
  - PASS/FAIL status for each test case
  - Any bugs or concerns found
  - Overall verdict: APPROVED or CHANGES_REQUESTED
- Log: "✅ Phase 3 Complete: QA review filed"

## Phase 4: Resolution
If QA verdict is APPROVED:
  - Adopt Engineer mindset
  - Create the PR with a summary of changes and test results
  - Log: "✅ Phase 4 Complete: PR created"

If QA verdict is CHANGES_REQUESTED:
  - Adopt Engineer mindset
  - Read the QA review and fix each issue
  - Log what was fixed
  - Return to Phase 3 (max 3 cycles, then stop and report remaining issues)

## Rules
- Between phases, briefly state which role you're switching to
- Keep a running log in docs/test-plans/{story-id}-workflow-log.md
- If you hit ambiguity in the user story, stop and ask rather than assuming
- Do not skip phases