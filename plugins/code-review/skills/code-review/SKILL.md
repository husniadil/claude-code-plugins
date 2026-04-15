---
name: code-review
description: Iterative, human-in-the-loop code review that detects gaps, presents them for selection, and fixes them in cycles. Supports both diff-based PR review and holistic codebase analysis.
when_to_use: Use when reviewing a pull request, auditing branch changes, or assessing an entire codebase for quality gaps.
argument-hint: "[subagent|no-subagent|auto]"
---

# Code Review - Iterative Review

An iterative, human-in-loop code review skill that identifies gaps, presents them for user selection, and fixes them in cycles until clean.

## Review Modes

Two modes. Pick based on user intent — detail for each mode is covered in **Step 0** below.

- **PR Review Mode** (default): diff-based review against a base branch
- **Holistic Review Mode**: audit an entire codebase or scoped directories

## Subagent Mode (argument)

The skill accepts one optional argument via `$ARGUMENTS` controlling whether scans/fixes delegate to Task subagents:

| `$ARGUMENTS` value | Meaning                                                                                                                                                                 |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `subagent`         | **Always** delegate eligible work to subagents — Explore for read-only scans (Step 0 Holistic, Step 5 re-review), general-purpose for multi-file complex fixes (Step 4) |
| `no-subagent`      | **Never** call the Task tool. Do everything in the main context: Glob + Read + Grep directly, apply fixes directly                                                      |
| `auto`             | **Let the skill decide** based on scope size, codebase breadth, and fix complexity                                                                                      |
| _(empty)_          | Same as `auto`                                                                                                                                                          |

**Default: `auto`.** If `$ARGUMENTS` is empty or not recognized, operate in `auto` mode.

**`auto` decision heuristics:**

- **Holistic scan over >50 files or multiple ecosystem packages** → delegate to Explore subagent
- **Fix touches >2 files or needs cross-cutting refactor** → delegate to general-purpose subagent
- **Small PR diff / single-file scope / known surface** → stay in main context
- **Tight budget / urgency signal from user** → stay in main context

**Respect the argument throughout the session.** Once `subagent` or `no-subagent` is set, apply it consistently across Step 0, Step 4, and Step 5. Do not flip regime mid-run.

**Subagent choice by task type** (for `subagent` and `auto` when delegating):

- **Read-only scans / research** → `Explore` subagent (optimized, read-only)
- **Multi-file fixes / write work** → `general-purpose` subagent (or a domain-specific subagent if one is available)

Validation (Step 2g) **always runs in the main context** regardless of this argument — it directly reads files to confirm agent-reported gaps. `no-subagent` does not disable validation; it disables the upstream delegation that produces the gaps.

## Workflow Overview

```
┌──────────────────────────────────────────────┐
│  1. Gather input                             │
│     PR mode: diff (base vs HEAD)             │
│     Holistic mode: scope from ecosystem      │
└──────────────┬───────────────────────────────┘
               ▼
┌──────────────────────────────────────────────┐
│  2. Review with context → 2a..2g             │
│     (business, diff, tech, integrations,     │
│      dep grounding, identify, validate)      │
└──────────────┬───────────────────────────────┘
               ▼
┌──────────────────────────────────────────────┐
│  3. Present validated gap list               │
│     AskUserQuestion — 2 options:             │
│       · Apply all fixes                      │
│       · Done — looks good                    │
│     (free-form "Other" → selective fix)      │
└──────────────┬───────────────────────────────┘
               ▼
      ┌────────┴─────────────┬──────────────┐
      │                      │              │
   "Done"          "Apply all fixes"    "Other" subset
      │                      │              │
      ▼                      ▼              ▼
   [EXIT]         ┌──────────────────────────────┐
                  │  4. Apply Fixes              │
                  │     Pre-gate checklist       │
                  │     ├─ Tracked Fix Loop      │
                  │     │  (all, or subset ≥3)   │
                  │     └─ Selective Fix         │
                  │        (subset 1-2)          │
                  │     Failure → Retry/Skip/    │
                  │              Abort           │
                  └──────────┬───────────────────┘
                             ▼
                  ┌──────────────────────────────┐
                  │  4.5 Next-Pass Gate          │
                  │      AskUserQuestion:        │
                  │        · Run next pass       │
                  │        · Stop — I'm done     │
                  └────┬─────────────────┬───────┘
                       │                 │
                  "Run next pass"   "Stop"
                       │                 │
                       ▼                 ▼
            ┌──────────────────────┐  ┌────────┐
            │ 5. Re-review → Loop  │  │  EXIT  │
            │    to Step 3         │  │        │
            └──────────────────────┘  └────────┘
```

## Instructions

### Step 0: Determine Review Mode

First, determine whether this is a **PR Review** or **Holistic Review**:

**PR Review** (user mentions PR, branch, changes, diff):

- Proceed to Step 1 to get the diff
- Focus on changed code + related context

**Holistic Review** (user mentions codebase, audit, project review):

- Skip Step 1 (no diff needed)
- Detect the project's source root from ecosystem signals before defaulting to `src/`:
  - Node/TS: `package.json` → check `main`/`exports`/`workspaces`; fall back to `src/`, `app/`, `packages/*/src/`
  - Python: `pyproject.toml` → `[tool.*]` or `[project].packages`; fall back to top-level package dirs
  - Go: `go.mod` → module root; conventional dirs `cmd/`, `internal/`, `pkg/`
  - Java/Kotlin: `pom.xml` or `build.gradle(.kts)` → `src/main/java`, `src/main/kotlin`
  - Rust: `Cargo.toml` → `src/`, workspace members
  - Monorepo: iterate over workspace members
- If ambiguous, ask the user
- Use **Glob** to enumerate relevant files per ecosystem
- Subagent usage depends on `$ARGUMENTS` (see "Subagent Mode" section above):
  - `subagent` → always delegate area scans to Explore subagents in parallel
  - `no-subagent` → enumerate and read in main context, no Task delegation
  - `auto` (default) → delegate to Explore when scope is large (>50 files or multi-package), otherwise stay in-context

For holistic reviews, use this workflow:

```
1. Detect scope from ecosystem signals (manifest files), or ask user
2. Use Glob to list relevant files per ecosystem
3. For large codebases, chunk into areas (api/, components/, utils/, cmd/, pkg/, etc.)
4. Delegate area scans to Explore subagents in parallel when independent
5. Validate reported gaps (Step 2g) — never trust agent output blindly
6. Present all validated gaps
7. Fix selected gaps
8. Re-review affected areas
```

### Step 1: Get the PR Diff (PR Review Mode Only)

First, detect the current branch, resolve repo metadata, and get the diff. Prefer `gh` when the branch is already pushed as a PR, fall back to raw git otherwise.

**Always re-check the current branch** — do not rely on conversation memory, the branch may have changed:

```bash
git branch --show-current
```

**Resolve repo (when gh is available):**

```bash
REPO=$(gh repo view --json nameWithOwner --jq '.nameWithOwner' 2>/dev/null)
# e.g., "owner/repo" — use for any subsequent gh api calls
```

**If the branch has an open PR, prefer `gh` for changed files and base branch:**

```bash
# PR number for current branch (empty if no PR)
PR=$(gh pr view --json number --jq '.number' 2>/dev/null)

# Base branch from PR metadata
BASE=$(gh pr view --json baseRefName --jq '.baseRefName' 2>/dev/null)

# Changed files (robust in monorepos — first path segment often indicates package/module)
gh pr view "$PR" --json files --jq '.files[].path'
```

**Otherwise, detect base branch from git:**

```bash
# 1. Upstream tracking branch, if set
git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null

# 2. Default branch from remote (origin/HEAD)
git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@'

# 3. Fallback: try common defaults
for b in main master develop trunk; do git show-ref --verify --quiet "refs/heads/$b" && echo "$b" && break; done
```

Store the resolved base in a variable, then diff. **Do not hardcode `main`**:

```bash
BASE=<detected-base>
git diff "${BASE}...HEAD"
```

If detection is ambiguous or fails, ask the user.

### Step 2: Review with Context

**IMPORTANT**: Do not blindly review the diff in isolation. Always gather context - both technical AND business logic.

#### 2a. Understand the Business & Project Context

Before diving into code, understand **what this code is supposed to do** AND **what conventions it must follow**:

1. **Read documentation**: Check README, AGENTS.md, inline comments, PR description
2. **Read per-package conventions** (monorepos): Each package/service may have its own AGENTS.md, CLAUDE.md, CONTRIBUTING.md — read the one closest to the changed files, not only the repo root
3. **Read linter/formatter configs** before flagging style or convention gaps: `.editorconfig`, `.eslintrc*`, `.prettierrc*`, `ruff.toml` / `[tool.ruff]` in `pyproject.toml`, `.rubocop.yml`, `checkstyle.xml`, `golangci.yml`, `biome.json`, `.swiftlint.yml`, etc. Respect what the project already enforces — do not flag rules the config explicitly disables
4. **Understand the feature**: What user problem does this solve? What's the expected behavior?
5. **Identify business rules**: Are there validation rules, workflows, or domain constraints?
6. **Check edge cases**: What happens with invalid input? Empty states? Concurrent access?

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

**Monorepo / multi-package awareness:**

When the diff touches multiple packages, services, or modules (detected from distinct first-segment paths in the changed-files list, or from workspace members in the manifest), investigate **per-package**. Each package may pin different versions, follow different conventions, and have its own `AGENTS.md` / `CLAUDE.md`. Do not apply global assumptions across packages.

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

When code connects to external systems (frontend ↔ backend ↔ database ↔ third-party APIs), trace the full integration path. Verify contracts, error handling, auth, and pagination match across boundaries — contract drift between tiers is a common source of silent bugs.

See [references/integration-tracing.md](references/integration-tracing.md) for per-boundary checklists (FE→BE, BE→DB, BE→external API), an 8-item watch list (contract/type/auth/pagination mismatches), and a worked trace example.

#### 2e. Dependency & Compatibility Grounding

Internal knowledge about package versions, APIs, and deprecations is often outdated. When the diff touches a dependency manifest, introduces a third-party import, or uses a version-sensitive API, ground against the **exact pinned version** in the manifest/lockfile — not the latest release, not general knowledge.

**Trigger when:** manifest changed, new third-party import, or version-sensitive API usage (deprecated methods, renamed exports, signature changes).

**Workflow (brief):** Read manifest → WebSearch for breaking changes / deprecations / CVEs on that version → WebFetch official changelog or migration guide → cross-check usage against the version's actual API surface.

See [references/dependency-grounding.md](references/dependency-grounding.md) for the stack → manifest lookup table (Node, Python, Go, Java, Kotlin, Rust, Ruby, PHP, Elixir + runtime pinning files), the full grounding workflow, what-to-flag checklist, and an example.

Label findings under the **Dependency Compatibility** category (see Step 2f and [gap-categories.md §3](references/gap-categories.md)).

#### 2f. Identify Gaps

Look for gaps across ALL categories:

1. **Business Logic** - Missing validations, incorrect workflows, wrong domain rules, edge cases not handled
2. **Integration Issues** - Contract mismatches, missing fields, type mismatches between frontend/backend/database/external APIs
3. **Dependency Compatibility** - Usage of APIs not available in pinned version, missed breaking changes on bump, peer-dep mismatches, runtime incompatibility, pinned version with known CVE (see Step 2e)
4. **Logic Errors** - Bugs, incorrect conditions, off-by-one errors, race conditions
5. **Security Issues** - Injection vulnerabilities, auth gaps, data exposure
6. **Performance Problems** - N+1 queries, unnecessary loops, memory leaks
7. **Error Handling** - Missing try/catch, unhandled edge cases, silent failures
8. **Code Style** - Inconsistent naming, formatting, patterns
9. **Missing Tests** - Untested code paths, edge cases
10. **Documentation Gaps** - Missing comments for complex logic, outdated docs

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

#### 2g. Validate Gaps Before Presenting

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

Use the **AskUserQuestion** tool to present gaps as a numbered list with selection options. **Invoke the tool verbatim** — do not paraphrase the question as prose in chat. The structured panel must appear; a plain-text question is a bug, not an alternative.

First, display the gaps found:

```
## PR Review - Iteration 1

Found 4 gaps in your PR:

1. [HIGH] src/auth.ts:45 - Security: SQL injection vulnerability in query
2. [MED] src/api.ts:123 - Error Handling: Missing try/catch around API call
3. [MED] src/utils.ts:67 - Logic: Off-by-one error in loop condition
4. [LOW] src/components/Button.tsx:12 - Style: Inconsistent naming convention
```

Then call the **AskUserQuestion** tool with **only two options**. The "Other" free-form box is provided automatically by the tool and is the fallback for any subset or filter the user wants. Do not substitute a chat prompt for this tool call.

**Pluralization at runtime** — substitute `N` with the actual count and adjust wording for singular vs plural:

| Count | Question                                   | "Apply all fixes" description                                    |
| ----- | ------------------------------------------ | ---------------------------------------------------------------- |
| N = 1 | `"Apply the fix for the 1 validated gap?"` | `"Fix the gap, verify, track progress"`                          |
| N ≥ 2 | `"Apply fixes for all N validated gaps?"`  | `"Fix all N gaps sequentially, track progress, stop on failure"` |

Template below uses the N ≥ 2 form. Adjust wording for N = 1 before calling the tool.

```json
{
  "questions": [
    {
      "question": "Apply fixes for all N validated gaps?",
      "header": "Fix gaps",
      "multiSelect": false,
      "options": [
        {
          "label": "Apply all fixes",
          "description": "Fix all N gaps sequentially, track progress, stop on failure"
        },
        {
          "label": "Done — looks good",
          "description": "Exit without fixing"
        }
      ]
    }
  ]
}
```

#### Fallback: Interpreting free-form input

When the user types into the **"Other"** box instead of picking an option, parse the intent:

| User input pattern             | Interpretation                                             |
| ------------------------------ | ---------------------------------------------------------- |
| `1,3,5` / `1 3 5`              | Selective fix: gaps #1, #3, #5                             |
| `1-3`                          | Selective fix: gaps #1 through #3                          |
| `only HIGH` / `HIGH only`      | Selective fix: filter by severity HIGH                     |
| `HIGH + MED` / `HIGH and MED`  | Selective fix: HIGH and MEDIUM                             |
| `skip #N` / `all except #N`    | Apply all fixes minus #N                                   |
| `first N`                      | Selective fix: gaps #1..#N                                 |
| `not now` / `later` / `cancel` | Treat as "Done"                                            |
| Anything ambiguous             | **Do not guess** — confirm with a short follow-up question |

Any subset interpretation routes to the **selective fix** path in Step 4. Only the clean "Apply all fixes" choice enters the **tracked fix loop**.

### Step 4: Apply Fixes

Step 4 has **two execution paths** depending on the Step 3 outcome:

- **Tracked fix loop** (primary) — user picked **"Apply all fixes"**
- **Selective fix** (fallback) — user typed a subset/filter in "Other"

Both paths share the pre-gate checklist below.

#### Pre-gate Checklist

Before any edit, verify all of the following. If any item fails, **do not start**; surface the problem to the user and wait.

1. **Validation gate** — every selected gap has passed Step 2g (Validate Gaps). Never fix an un-validated gap.
2. **File existence** — every referenced `file:line` exists in the current working tree. Drop or re-validate any that don't.
3. **Working tree clean (or explicitly approved)** — run `git status`. If dirty with unrelated changes, invoke the **AskUserQuestion** tool (verbatim — not prose) with three options: `Stash unrelated changes`, `Commit unrelated changes first`, `Abort`. Do not silently mix unrelated work into review fixes.
4. **Working context confirmed**:
   - PR mode: `git branch --show-current` still matches the branch being reviewed
   - Holistic mode: the intended scope path is still the one to edit

#### Tracked Fix Loop (primary path)

Triggered when the user picks **"Apply all fixes"**. This path guarantees:

- **Exhaustive** — every validated gap gets fixed, no re-prompt per item
- **Sequential** — one gap at a time, finish + verify before moving to the next
- **Tracked** — every gap becomes a visible task the user can watch
- **Verified** — a task is marked `completed` only after a post-fix check confirms the change took effect
- **Fail-stop** — on failure, the loop halts; nothing is silently skipped

**Protocol:**

1. **Create tasks up front.** Before applying any edit, `TaskCreate` one task per selected gap:
   - `subject`: `Fix [SEVERITY] <file:line> — <category>`
   - `activeForm`: `Fixing <file:line>`
2. **Process sequentially.** For each gap, in the order presented:
   1. `TaskUpdate status=in_progress`
   2. Read the file around the reported location
   3. Apply the fix using the Edit tool (or delegate a complex multi-file fix to a Task subagent — see below)
   4. **Post-fix verify** — re-read the edited region and confirm the change actually addresses the gap. For type/compile-sensitive edits, run a quick check if available (`tsc --noEmit`, `go build`, `python -m py_compile`, linter, etc.).
   5. Only on successful verification: `TaskUpdate status=completed`
3. **On failure** — apply the Failure & Resumption Protocol below. Do not continue to the next gap.
4. **After the loop** — summarize fixes made, then go to the Next-Pass Gate below before running Step 5.

**Delegating complex fixes** — subject to `$ARGUMENTS` (see "Subagent Mode"):

- `subagent` → delegate any multi-file or complex fix to `general-purpose`
- `no-subagent` → apply all fixes directly in main context with Read + Edit
- `auto` (default) → delegate only when the fix touches >2 files or requires cross-cutting refactor

When delegating, the Task call happens inside step 2.3 above; the outer task bookkeeping (create → in_progress → verify → completed) still applies:

```
Task tool parameters:
- subagent_type: "general-purpose"
- description: "Fix SQL injection in auth.ts"
- prompt: "Fix the SQL injection vulnerability in src/auth.ts at line 45.
          Use parameterized queries instead of string concatenation.
          Only modify what's necessary to fix this specific issue."
```

#### Selective Fix (fallback path)

Triggered when the user typed a subset/filter into "Other" (e.g. `1,3`, `only HIGH`, `skip #2`).

- **If the resolved subset has ≥3 gaps** — run the same Tracked Fix Loop above, scoped to the subset.
- **If the subset has 1–2 gaps** — lightweight loop: pre-gate → Read → Edit → verify → summarize. No `TaskCreate` overhead.

Otherwise the rules are identical: pre-gated, sequentially applied, verified before marking done, and fail-stop on error.

#### Failure & Resumption Protocol

If a fix can't complete (Edit fails, verification fails, unexpected state, subagent error): **halt the loop**, `TaskCreate` a blocker task, surface the failure to the user, and ask via `AskUserQuestion` to **Retry / Skip / Abort**.

Core rules: never silently skip a failure; `completed` means verified; use `deleted` (with a reason) for explicit skips.

See [references/failure-resumption.md](references/failure-resumption.md) for the full protocol (when to trigger, task-state transitions, anti-patterns).

### Step 4.5: Next-Pass Gate

After fixes land, do NOT auto-run Step 5. Ask the user first whether to spend another review pass. A second pass often surfaces new gaps (regressions, issues revealed by the fix, adjacent code the fix touched) — but it's not always wanted. Let the user decide.

Invoke the **AskUserQuestion** tool (verbatim — must appear as a structured panel, not a prose question):

```json
{
  "questions": [
    {
      "question": "Run another review pass to check for new or remaining gaps?",
      "header": "Next pass",
      "multiSelect": false,
      "options": [
        {
          "label": "Run next pass",
          "description": "Re-review the changed code (Step 5) and surface any new gaps"
        },
        {
          "label": "Stop — I'm done",
          "description": "Exit the review with a summary of what was fixed"
        }
      ]
    }
  ]
}
```

Routing:

- **Run next pass** → proceed to Step 5 (Re-review)
- **Stop — I'm done** → proceed to Step 6 (Exit) with summary
- **Free-form in "Other"** — parse intent: "once more" / "yes" → Run; "enough" / "no" / "that's fine" → Stop; anything ambiguous → confirm with a short follow-up

Also skip the gate and go straight to Step 6 when:

- **No fixes were applied** in Step 4 (user picked "Done" earlier, or subset resolved to empty) — there's nothing new to re-review
- **All gaps were `deleted`** via the Failure & Resumption Skip option and nothing actually landed

### Step 5: Re-review After Fixes

**Task list handling across iterations:**

- Leave tasks from the previous iteration intact as an audit trail (`completed`, `deleted`, and any `in_progress` blockers). Do not delete completed tasks between iterations.
- For each new gap found in this iteration, create a **new** task via `TaskCreate`. Do not reuse or relabel previous tasks.
- If a new iteration re-surfaces a gap that was `deleted` (skipped) earlier, treat it as a new task and let the user decide again.

After applying fixes, re-review based on the mode:

**PR Review Mode:**

1. Run `git diff "${BASE}...HEAD"` again (using the base detected in Step 1) to get the updated diff
2. Re-analyze the diff for:
   - Remaining unfixed gaps
   - New issues introduced by fixes
   - Regression in previously clean code
3. Present the updated gap list

**Holistic Review Mode:**

1. Re-read the files that were modified during fixes
2. Re-analyze those files plus any files they interact with. Delegation follows `$ARGUMENTS` (see "Subagent Mode"): `subagent` → Explore for re-scan; `no-subagent` → read directly; `auto` → Explore only when the re-scan is large, direct reads otherwise
3. Check if fixes introduced new issues or broke related code
4. Re-validate any agent-reported gaps (Step 2g) before presenting
5. Present the updated gap list for the affected areas

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

## Output Behavior

- **Do not narrate workflow steps** to the user. Avoid "Step 1: ...", "Step 2: ..." announcements. Work like a colleague reviewing code, not a robot reading a checklist.
- **First user-visible output should be the gap list**, not chatter about fetching the diff, resolving the base branch, or detecting the stack. Keep internal plumbing silent.
- Only surface results, decisions, and questions that need user input.

## Anti-Patterns to Avoid

1. **Blind diff review** - Don't review the diff in isolation. Always gather context: check callers, verify dependencies, trace data flow
2. **Ignoring related issues** - Pre-existing issues that affect the changes ARE in scope. Flag callers missing new parameters, contracts that are now violated, etc.
3. **Over-fixing** - Do not exceed the scope the user approved — either all gaps (from "Apply all fixes") or the subset parsed from their free-form input. Never fold in adjacent cleanups, related refactors, or new issues noticed mid-fix unless the user approves them.
4. **Skipping the Next-Pass Gate** - Never auto-run Step 5 (Re-review) after fixes land. Always ask the user first via the Next-Pass Gate whether to spend another pass. If they say stop, stop.
5. **Silent fixes** - Always explain what was changed and why
6. **Trusting agent claims blindly** - When using Task agents for parallel analysis, ALWAYS validate their reported gaps by reading the actual code before presenting to user. Agents can hallucinate issues or misunderstand context.
7. **Grounding against latest instead of pinned version** - Never assume library behavior from the latest release or general knowledge. Always verify against the exact version resolved in the manifest/lockfile for the specific package being reviewed. Behavior in v5.x may not exist in v4.x.
8. **Applying global assumptions in a monorepo** - Different packages can pin different versions and enforce different conventions. Ground per-package, not per-repo.
9. **Mixing unrelated work into review fixes** - If `git status` is dirty with unrelated changes, resolve that first. Don't commit review fixes alongside in-flight work.
10. **Silent batch fixes** - For batch work (Tracked Fix Loop, or any selective run ≥3 gaps), always surface progress via `TaskCreate`/`TaskUpdate`. No invisible mass edits.
11. **Marking a task completed before verification** - `completed` requires a post-fix check confirming the change addresses the gap. Edit tool success alone is not completion.
12. **Silently skipping a failed fix** - Failures route through the Failure & Resumption Protocol. Never drop a gap without the user deciding Retry / Skip / Abort.
13. **Starting fix work without the pre-gate checklist** - Validation gate, file existence, clean working tree, and confirmed working context must all pass before any edit.
14. **Paraphrasing AskUserQuestion as a prose question** - Wherever this skill says to present choices (Step 3 fix menu, Step 4 dirty-tree pre-gate, Step 4.5 Next-Pass Gate, Failure & Resumption Retry/Skip/Abort), **invoke the AskUserQuestion tool verbatim** so the structured panel renders. A natural-language `"Apply all fixes or done?"` in chat is a bug — the user should see the panel, not plain text.

## Example Session

```
User: review my PR

[Internal: resolve base branch, fetch diff, gather context, validate gaps]

Claude: ## PR Review - Iteration 1

Found 3 gaps in your PR:

1. [HIGH] src/auth.ts:45 - Security: Password stored in plain text
2. [MED] src/api.ts:89 - Error Handling: Unhandled promise rejection
3. [LOW] src/utils.ts:12 - Style: Unused import

[AskUserQuestion: "Apply fixes for all 3 validated gaps?"
 Options: Apply all fixes / Done — looks good]

User: Apply all fixes

[Internal pre-gate: ✓ validated, ✓ files exist, ✓ clean tree, ✓ branch confirmed]

[TaskCreate × 3]
  #1 pending  — Fix [HIGH] src/auth.ts:45 — Security
  #2 pending  — Fix [MED] src/api.ts:89 — Error Handling
  #3 pending  — Fix [LOW] src/utils.ts:12 — Style

[#1 in_progress → Read → Edit → verify (re-read confirms bcrypt hashing) → completed]
[#2 in_progress → Read → Edit → verify (try/catch wraps await) → completed]
[#3 in_progress → Read → Edit → verify (import removed) → completed]

Claude: Fixed 3/3 gaps.

[AskUserQuestion: "Run another review pass to check for new or remaining gaps?"
 Options: Run next pass / Stop — I'm done]

User: Run next pass

[Internal: re-run diff, re-validate]

Claude: ## PR Review - Iteration 2

Found 1 gap:

1. [LOW] src/auth.ts:48 - Style: Magic number should be a constant

[AskUserQuestion: "Apply the fix for the 1 validated gap?"
 Options: Apply all fixes / Done — looks good]

User: Done — looks good

Claude: ## Review Complete

Iterations: 2
Gaps fixed: 3
Gaps skipped: 1 (user choice)

Changes made:
- src/auth.ts: Added password hashing with bcrypt
- src/api.ts: Added try/catch with proper error handling
- src/utils.ts: Removed unused import
```

**Variant — free-form subset via "Other":**

```
[AskUserQuestion: "Apply fixes for all 3 validated gaps?"]

User (types in Other): skip #3

Claude: Interpreted as: fix gaps #1 and #2, skip #3.

[Selective fix — 2 gaps, below ≥3 threshold, lightweight loop]
[#1 Read → Edit → verify]
[#2 Read → Edit → verify]

Claude: Fixed 2/3 gaps (skipped #3 per your request). Re-reviewing...
```
