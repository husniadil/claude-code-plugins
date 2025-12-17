---
name: code-review
description: Iterative code review with gap detection and user-controlled fixes. Use for PR reviews ("review my PR", "check my changes") or holistic codebase reviews ("review this codebase", "find gaps in the code"). Supports both diff-based PR review and full codebase analysis.
---

# Code Review - Iterative Review

An iterative, human-in-loop code review skill that identifies gaps, presents them for user selection, and fixes them in cycles until clean.

## When to Use

Use this skill when the user wants to:

- Review a pull request before merging
- Find issues in their current branch changes
- Get their code reviewed iteratively
- Fix code issues systematically
- **Review an entire codebase** for gaps (holistic review)
- Audit code quality across a project

## Review Modes

### 1. PR Review Mode (Default)

Triggered by: "review my PR", "check my changes", "review this branch"

- Analyzes diff against base branch
- Gathers context around changed code (callers, dependencies, types)
- Flags related pre-existing issues that affect the changes

### 2. Holistic Review Mode

Triggered by: "review this codebase", "find gaps in the code", "audit the project"

- Analyzes entire codebase or specified directories/files
- Systematic scan across all gap categories
- Good for initial audits or periodic health checks

## Workflow Overview

```
┌─────────────────────────────────────┐
│  1. Get PR diff (base vs HEAD)      │
└──────────────┬──────────────────────┘
               ▼
┌─────────────────────────────────────┐
│  2. Review: Identify all gaps       │
└──────────────┬──────────────────────┘
               ▼
┌─────────────────────────────────────┐
│  3. Present numbered gap list       │
│     (use AskUserQuestion)           │
└──────────────┬──────────────────────┘
               ▼
┌─────────────────────────────────────┐
│  4. User selects gaps to fix        │
│     or says "done"                  │
└──────────────┬──────────────────────┘
               ▼
      ┌────────┴────────┐
      │                 │
   "done"          selection
      │                 │
      ▼                 ▼
   [EXIT]    ┌──────────────────────┐
             │  5. Fix selected gaps │
             │     (use Task agent)  │
             └──────────┬───────────┘
                        │
                        └──► Loop to step 2
```

## Instructions

### Step 0: Determine Review Mode

First, determine whether this is a **PR Review** or **Holistic Review**:

**PR Review** (user mentions PR, branch, changes, diff):

- Proceed to Step 1 to get the diff
- Focus on changed code + related context

**Holistic Review** (user mentions codebase, audit, project review):

- Skip Step 1 (no diff needed)
- Ask user which directories/files to review, or review entire `src/` by default
- Use Glob to find all relevant files
- Use Task agents to analyze different parts in parallel if codebase is large

For holistic reviews, use this workflow:

```
1. Identify scope (ask user or default to src/)
2. Use Glob to list all files: **/*.{ts,js,py,...}
3. For large codebases, chunk into areas (api/, components/, utils/, etc.)
4. Review each area systematically
5. Present all gaps found
6. Fix selected gaps
7. Re-review affected areas
```

### Step 1: Get the PR Diff (PR Review Mode Only)

First, determine the base branch and get the diff:

```bash
# Get current branch
git branch --show-current

# Get the base branch (usually main or master)
git rev-parse --abbrev-ref HEAD

# Get the diff against base branch
git diff main...HEAD
```

If unsure about the base branch, ask the user.

### Step 2: Review with Context

**IMPORTANT**: Do not blindly review the diff in isolation. Always gather context - both technical AND business logic.

#### 2a. Understand the Business Context

Before diving into code, understand **what this code is supposed to do**:

1. **Read documentation**: Check README, AGENTS.md, inline comments, PR description
2. **Understand the feature**: What user problem does this solve? What's the expected behavior?
3. **Identify business rules**: Are there validation rules, workflows, or domain constraints?
4. **Check edge cases**: What happens with invalid input? Empty states? Concurrent access?

Ask yourself:

- Does this code correctly implement the intended business logic?
- Are there missing business rules or edge cases?
- Would a domain expert find issues with this implementation?

#### 2b. Analyze the Diff

Understand what changed technically:

- New functions/classes added
- Modified logic
- Changed function signatures
- New dependencies

#### 2c. Gather Technical Context

For each changed file, investigate:

1. **Callers**: Who calls this function? Are they passing correct arguments?
2. **Dependencies**: What does this code depend on? Are those contracts met?
3. **Types**: Are type definitions correct? Any missing optional parameters?
4. **Related files**: Are there related files that should be updated together?
5. **Data flow**: How does data flow through this code? Any transformations that could corrupt data?

Use Grep and Read tools to explore:

```bash
# Find callers of a changed function
grep -r "functionName(" --include="*.ts"

# Check type definitions
grep -r "interface.*TypeName" --include="*.ts"

# Find related business logic
grep -r "orderStatus\|paymentState" --include="*.ts"
```

#### 2d. Trace External Integrations (End-to-End)

**IMPORTANT**: When code connects to external systems, trace the full integration path.

**Frontend → Backend:**

- Find the API endpoint being called (`fetch`, `axios`, API client)
- Locate the backend route handler
- Verify request/response contracts match
- Check error handling on both sides

```bash
# Find API calls in frontend
grep -r "fetch\|axios\|api\." --include="*.tsx" --include="*.ts"

# Find corresponding backend route
grep -r "router\.\|app\.\(get\|post\|put\|delete\)" --include="*.ts"
```

**Backend → Database:**

- Trace queries to schema definitions
- Verify column names, types, constraints match
- Check for missing migrations

**Backend → External APIs:**

- Verify API contracts (request/response shapes)
- Check authentication/authorization
- Review timeout and retry handling
- Check error responses are handled

**What to Look For in Integrations:**

1. **Contract mismatches**: Frontend expects `userId`, backend sends `user_id`
2. **Missing fields**: Backend added required field, frontend doesn't send it
3. **Type mismatches**: Frontend sends string, backend expects number
4. **Error handling gaps**: Frontend doesn't handle 4xx/5xx responses
5. **Race conditions**: Frontend assumes sync, backend is async
6. **Auth/permissions**: Frontend calls endpoint user doesn't have access to
7. **Pagination mismatches**: Frontend expects array, backend returns paginated object
8. **Validation gaps**: Frontend validates, backend doesn't (or vice versa)

**Example Integration Trace:**

```
Frontend: src/components/OrderForm.tsx
  → calls: POST /api/orders { productId, quantity }

Backend: src/routes/orders.ts
  → handler: createOrder(req.body)
  → validates: productId (required), quantity (number > 0)

Service: src/services/orderService.ts
  → checks: inventory, user balance
  → calls: db.orders.create()

Database: migrations/001_orders.sql
  → schema: orders(id, product_id, quantity, user_id, status)

GAPS FOUND:
- Frontend sends `quantity` as string, backend expects number
- Backend doesn't return created order, frontend expects it
- No error handling in frontend for insufficient inventory
```

#### 2e. Identify Gaps

Look for gaps across ALL categories:

1. **Business Logic** - Missing validations, incorrect workflows, wrong domain rules, edge cases not handled
2. **Integration Issues** - Contract mismatches, missing fields, type mismatches between frontend/backend/database/external APIs
3. **Logic Errors** - Bugs, incorrect conditions, off-by-one errors, race conditions
4. **Security Issues** - Injection vulnerabilities, auth gaps, data exposure
5. **Performance Problems** - N+1 queries, unnecessary loops, memory leaks
6. **Error Handling** - Missing try/catch, unhandled edge cases, silent failures
7. **Code Style** - Inconsistent naming, formatting, patterns
8. **Missing Tests** - Untested code paths, edge cases
9. **Documentation Gaps** - Missing comments for complex logic, outdated docs

**Include related pre-existing issues** if they:

- Affect the correctness of the new changes
- Are in callers that need to be updated (e.g., missing new required parameter)
- Create security/performance issues when combined with new code

For each gap found, note:

- File and line number
- Category
- Brief description
- Severity (high/medium/low)
- Whether it's in the diff or related code

See [references/gap-categories.md](references/gap-categories.md) for detailed definitions.

#### 2f. Validate Gaps Before Presenting

**CRITICAL**: Before presenting any gap to the user, you MUST validate it by reading the actual code.

When using Task agents (Explore or general-purpose) to scan different parts of a codebase in parallel, agents may report false positives or misunderstand context. **Never trust agent claims blindly.**

**Validation Process:**

For each gap reported (by you or by a sub-agent):

1. **Read the actual file** at the reported line number using the Read tool
2. **Verify the issue exists** - confirm the code actually has the problem described
3. **Check the context** - ensure the surrounding code doesn't already handle the case
4. **Confirm line numbers** - agent-reported line numbers may be approximate or outdated

**Discard gaps that:**

- Reference files or lines that don't exist
- Describe code that doesn't match reality when you read it
- Are already handled by surrounding context the agent missed
- Are duplicates of other gaps (same issue, different wording)

**Example Validation:**

```
Agent reports: "[HIGH] src/auth.ts:45 - SQL injection in query"

Validation steps:
1. Read src/auth.ts lines 40-50
2. Check: Is there actually a query at line 45?
3. Check: Does it use string concatenation with user input?
4. Check: Is it already using parameterized queries?

If the code uses parameterized queries → DISCARD the gap
If the code has injection vulnerability → KEEP the gap
```

Only present validated gaps to the user.

### Step 3: Present Gaps to User

Use the `AskUserQuestion` tool to present gaps as a numbered list with selection options.

First, display the gaps found:

```
## PR Review - Iteration 1

Found 4 gaps in your PR:

1. [HIGH] src/auth.ts:45 - Security: SQL injection vulnerability in query
2. [MED] src/api.ts:123 - Error Handling: Missing try/catch around API call
3. [MED] src/utils.ts:67 - Logic: Off-by-one error in loop condition
4. [LOW] src/components/Button.tsx:12 - Style: Inconsistent naming convention
```

Then use `AskUserQuestion`. **Note**: The examples below are templates - dynamically adjust the numbers and descriptions based on actual gaps found.

```json
{
  "questions": [
    {
      "question": "Which gaps would you like me to fix?",
      "header": "Fix gaps",
      "multiSelect": false,
      "options": [
        {
          "label": "Fix all (1-N)",
          "description": "Fix all N identified gaps"
        },
        {
          "label": "High priority only",
          "description": "Fix only HIGH severity gaps"
        },
        {
          "label": "Select by number",
          "description": "I'll specify which gaps to fix (e.g., 1,3)"
        },
        {
          "label": "Done - looks good",
          "description": "Skip fixes, end the review"
        }
      ]
    }
  ]
}
```

If user selects "Select by number", ask them to specify. The user can type their selection in the "Other" option, or you can provide common combinations based on the actual gaps:

```json
{
  "questions": [
    {
      "question": "Which gap numbers to fix? (e.g., 1,3,4)",
      "header": "Select",
      "multiSelect": false,
      "options": [
        { "label": "All HIGH", "description": "Fix all HIGH severity gaps" },
        {
          "label": "All HIGH + MED",
          "description": "Fix HIGH and MEDIUM gaps"
        },
        { "label": "First few", "description": "Fix gaps 1-3" }
      ]
    }
  ]
}
```

### Step 4: Fix Selected Gaps

For each gap to fix:

1. Read the relevant file
2. Understand the context around the issue
3. Apply the fix using the Edit tool
4. Keep fixes minimal and focused

For complex multi-file fixes, use the Task tool:

```
Task tool parameters:
- subagent_type: "general-purpose"
- description: "Fix SQL injection in auth.ts"
- prompt: "Fix the SQL injection vulnerability in src/auth.ts at line 45.
          Use parameterized queries instead of string concatenation.
          Only modify what's necessary to fix this specific issue."
```

### Step 5: Re-review After Fixes

After applying fixes, re-review based on the mode:

**PR Review Mode:**

1. Run `git diff main...HEAD` again to get updated diff
2. Re-analyze the diff for:
   - Remaining unfixed gaps
   - New issues introduced by fixes
   - Regression in previously clean code
3. Present the updated gap list

**Holistic Review Mode:**

1. Re-read the files that were modified during fixes
2. Re-analyze those files plus any files they interact with
3. Check if fixes introduced new issues or broke related code
4. Present the updated gap list for the affected areas

### Step 6: Iterate or Exit

The review loop continues until:

- **User says "done"**: Respect the user's decision to stop
- **No gaps remain**: Congratulate and summarize changes made
- **User explicitly cancels**: Stop immediately

When exiting, provide a summary:

```
## Review Complete

Iterations: 3
Gaps fixed: 7
Gaps skipped: 2 (user choice)

Changes made:
- src/auth.ts: Fixed SQL injection, added input validation
- src/api.ts: Added error handling
- src/utils.ts: Fixed off-by-one error
```

## Anti-Patterns to Avoid

1. **Blind diff review** - Don't review the diff in isolation. Always gather context: check callers, verify dependencies, trace data flow
2. **Ignoring related issues** - Pre-existing issues that affect the changes ARE in scope. Flag callers missing new parameters, contracts that are now violated, etc.
3. **Over-fixing** - Only fix what user selected
4. **Skipping re-review** - Always re-review after fixes
5. **Silent fixes** - Always explain what was changed and why
6. **Trusting agent claims blindly** - When using Task agents for parallel analysis, ALWAYS validate their reported gaps by reading the actual code before presenting to user. Agents can hallucinate issues or misunderstand context.

## Example Session

```
User: review my PR

Claude: Let me get the PR diff and review it.
[Runs git diff main...HEAD]

Claude: ## PR Review - Iteration 1

Found 3 gaps in your PR:

1. [HIGH] src/auth.ts:45 - Security: Password stored in plain text
2. [MED] src/api.ts:89 - Error Handling: Unhandled promise rejection
3. [LOW] src/utils.ts:12 - Style: Unused import

[Uses AskUserQuestion: "Which gaps would you like me to fix?"]

User: Fix all

Claude: Fixing all 3 gaps...
[Applies fixes using Edit tool]

Claude: ## PR Review - Iteration 2

Re-reviewing after fixes...

Found 1 gap:

1. [LOW] src/auth.ts:48 - Style: Magic number should be a constant

[Uses AskUserQuestion: "Which gaps would you like me to fix?"]

User: Done - looks good

Claude: ## Review Complete

Iterations: 2
Gaps fixed: 3
Gaps skipped: 1 (user choice)

Changes made:
- src/auth.ts: Added password hashing with bcrypt
- src/api.ts: Added try/catch with proper error handling
- src/utils.ts: Removed unused import
```
