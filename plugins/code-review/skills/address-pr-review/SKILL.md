---
name: address-pr-review
description: Address reviewer and bot comments on a GitHub pull request — validate each comment, apply fixes where valid, reply with reasoning, and resolve threads.
when_to_use: Use when responding to review comments on a GitHub pull request (human reviewer or bot such as Coderabbit, DeepSource), after feedback has been left and needs iteration.
argument-hint: "[PR_NUMBER] [subagent|no-subagent|auto]"
---

# Address PR Review

Work through unresolved review comments on a GitHub pull request: fetch each thread, validate the claim against the pinned code, apply fixes where valid, reply with technical reasoning, and resolve the thread.

This skill is a companion to `code-review`. `code-review` finds gaps proactively from the diff; `address-pr-review` reacts to comments already on the PR.

## Subagent Mode (argument)

Second `$ARGUMENTS` slot controls subagent delegation:

| Value         | Meaning                                                                                 |
| ------------- | --------------------------------------------------------------------------------------- |
| `subagent`    | Delegate comment validation research and multi-file fixes to Task subagents in parallel |
| `no-subagent` | Stay in main context — no Task delegation                                               |
| `auto`        | Decide per comment: research-heavy or multi-file → delegate; simple → stay in-context   |
| _(empty)_     | Same as `auto`                                                                          |

**Default: `auto`.** Validation re-reads always run in main context regardless of this mode.

## Arguments

`$ARGUMENTS` is `[PR_NUMBER] [subagent|no-subagent|auto]`. Either slot may be omitted.

- `$1` — PR number. If omitted, infer from the current branch.
- `$2` — subagent mode (see above).

Resolution rules:

- If `$1` is a number → treat as PR number.
- If `$1` is one of `subagent`/`no-subagent`/`auto` → treat as subagent mode; infer PR from branch.
- If `$1` is empty → infer PR from branch. If on main/master with no PR, ask the user.

## Workflow Overview

```
┌──────────────────────────────────────┐
│ 1. Resolve PR number + repo          │
└──────────────┬───────────────────────┘
               ▼
┌──────────────────────────────────────┐
│ 2. Fetch unresolved review threads   │
│    via GraphQL                       │
└──────────────┬───────────────────────┘
               ▼
┌──────────────────────────────────────┐
│ 3. Detect stack + dependency versions │
│    (per-package in monorepos)         │
└──────────────┬───────────────────────┘
               ▼
┌──────────────────────────────────────┐
│ 4. Validate each comment              │
│    → valid / partial / invalid /      │
│      defer / repeat                   │
└──────────────┬───────────────────────┘
               ▼
┌──────────────────────────────────────┐
│ 5. Present summary → AskUserQuestion  │
│    (Apply / Done — free-form Other)   │
└──────────────┬───────────────────────┘
               ▼
┌──────────────────────────────────────┐
│ 6. Apply fixes (tracked fix loop)     │
└──────────────┬───────────────────────┘
               ▼
┌──────────────────────────────────────┐
│ 7. Push (commits live on origin)      │
└──────────────┬───────────────────────┘
               ▼
┌──────────────────────────────────────┐
│ 8. Reply to each item (cite live SHA) │
│    8a inline · 8b issue / body        │
└──────────────┬───────────────────────┘
               ▼
┌──────────────────────────────────────┐
│ 9. Resolve inline threads             │
│    (carve-out defer)                  │
└──────────────┬───────────────────────┘
               ▼
┌──────────────────────────────────────┐
│ 10. Update PR description (optional)  │
└──────────────────────────────────────┘
```

## Instructions

### Step 1: Resolve PR number and repo

**Always re-check the current branch first.** Do not rely on conversation memory.

```bash
git branch --show-current
```

Resolve the repo:

```bash
REPO=$(gh repo view --json nameWithOwner --jq '.nameWithOwner')
OWNER=${REPO%/*}
NAME=${REPO#*/}
```

Resolve PR:

- If `$1` is a number → `PR=$1`.
- Else infer from current branch: `PR=$(gh pr view --json number --jq '.number' 2>/dev/null)`.
- If empty (not a PR branch) → ask the user for the PR number.

### Step 2: Fetch unresolved review threads, issue comments, and review bodies

GitHub PRs carry feedback in **three distinct surfaces**, and this skill must address all of them:

1. **Inline review threads** (`reviewThreads`) — comments pinned to a diff line; can be resolved.
2. **Issue-level comments** (`comments`) — free-form PR conversation (bots like Coderabbit's summary, human chat). Cannot be "resolved"; handled via reply.
3. **Review bodies** (`reviews.body`) — top-level summary text a reviewer writes when submitting a review. Cannot be replied-to inline; acknowledged via an issue comment.

Fetch all three in one GraphQL call:

```graphql
{
  repository(owner: "<OWNER>", name: "<NAME>") {
    pullRequest(number: <PR>) {
      reviewThreads(first: 50) {
        nodes {
          id
          isResolved
          comments(first: 5) {
            nodes { id databaseId body author { login } createdAt }
          }
        }
      }
      comments(first: 50) {
        nodes { id databaseId body author { login } createdAt }
      }
      reviews(first: 50) {
        nodes { id databaseId body state author { login } submittedAt }
      }
    }
  }
}
```

Execute via `gh api graphql -f query=...`.

**Filtering**:

- `reviewThreads` → keep `isResolved == false`.
- `comments` (issue-level) → keep ones authored after the last push by the PR author, or that contain actionable feedback (bots often post a summary + suggestions here). Skip your own prior replies and pure acknowledgements.
- `reviews` → keep `state` in (`CHANGES_REQUESTED`, `COMMENTED`) with non-empty `body`. Skip `APPROVED` unless the body contains actionable notes.

If all three surfaces are empty, report "No unresolved feedback" and stop.

**Pagination note:** `reviewThreads(first: 50)`, `comments(first: 50)`, `reviews(first: 50)`, and `comments(first: 5)` per thread will silently truncate large inputs. Add a `totalCount` selection to each; if any overflow, re-run with `pageInfo { endCursor hasNextPage }` and an `after:` cursor until exhaustion.

**ID usage**:

- Inline thread reply → REST `in_reply_to` with comment `databaseId` (Step 8a).
- Inline thread resolve → GraphQL thread node `id` (Step 9).
- Issue comment reply → new issue comment via `gh pr comment` or REST `POST /issues/:n/comments` (Step 8b). No threading, no resolve.
- Review body acknowledgement → same as issue comment (Step 8b). No resolve.

### Step 3: Detect stack and dependency versions

Get changed files in this PR:

```bash
gh pr view "$PR" --json files --jq '.files[].path'
```

Group changed paths by package/service (first path segment in monorepos; repo root for single-package repos). For each affected package, read:

- The relevant dependency manifest / lockfile (see the stack → manifest table in [../code-review/references/dependency-grounding.md](../code-review/references/dependency-grounding.md))
- Any runtime pinning file present: `.tool-versions`, `.nvmrc`, `.python-version`, `.ruby-version`
- The package-level `AGENTS.md` / `CLAUDE.md` / `CONTRIBUTING.md` closest to the changed files

**Multi-package awareness**: different packages may pin different versions, enforce different conventions, and require different compile/check commands. Track all affected packages. Validation in Step 4 and checks in Step 6 must cover all of them — no global assumptions.

### Step 4: Validate each comment

Process **all three surfaces** uniformly: inline threads, issue comments, and review bodies. For items without a file:line anchor (issue comments, review bodies), extract file/line references from the body text itself — bots often embed them as `path/to/file.ts:42` or Markdown links.

For each item:

1. **Read the commented code** — open the file at the commented/referenced line range. Use `Read` directly; do not trust the comment's excerpt. If the item has no file anchor and references nothing, treat it as a general remark (design, scope, acknowledgement).
2. **Understand the claim** — is it a bug, a style preference, a factual assertion about library behavior, a broader design concern?
3. **Ground the claim**:
   - Library behavior → verify against the **exact pinned version** using [../code-review/references/dependency-grounding.md](../code-review/references/dependency-grounding.md). Do not reason from latest-release knowledge.
   - Pattern claim ("this is how we do X here") → Grep the codebase for counter-examples or confirming examples
   - Style / convention → check the project's linter/formatter configs and the nearest `AGENTS.md`. If the config explicitly disables a rule, the comment may be invalid
   - Cross-stack integration → trace per [../code-review/references/integration-tracing.md](../code-review/references/integration-tracing.md)
   - Repeat of a previously-addressed point → check the PR description's **Design Decisions** section (or equivalent); bots often lack memory across rounds
4. **Classify** the comment:
   - **Valid** — the issue exists; will apply a fix
   - **Partially valid** — the premise is right but the proposed fix isn't; will apply a modified fix
   - **Invalid** — wrong premise; will reply with technical reasoning
   - **Acknowledged, defer** — fair observation but out of scope for this PR
   - **Repeat** — already addressed in a previous round or in the PR description

**Subagent usage** (per Subagent Mode): for research-heavy validation (cross-repo pattern search, deep library source inspection, changelog reading), delegate to subagents where appropriate. Keep the actual `Read` to confirm the commented code in the main context.

Present a summary table to the user. Include a **Source** column so the user sees where each item lives (resolve-capable or not):

```
| # | Source       | Ref        | File:line        | Severity | Summary | Classification | Proposed action |
|---|--------------|------------|------------------|----------|---------|----------------|-----------------|
| 1 | inline       | #R_aaa     | src/auth.ts:45   | HIGH     | ...     | Valid          | Fix + resolve   |
| 2 | issue-comment| #IC_123    | (none)           | MED      | ...     | Valid          | Fix + reply     |
| 3 | review-body  | #RV_456    | src/api.ts:89    | LOW      | ...     | Invalid        | Reply only      |
```

`Source` values: `inline` (reviewThread), `issue-comment`, `review-body`.

### Step 5: Present and ask

Use `AskUserQuestion` with two options. Fallback via "Other" for any subset.

```json
{
  "questions": [
    {
      "question": "Apply the proposed actions for all N threads?",
      "header": "Address comments",
      "multiSelect": false,
      "options": [
        {
          "label": "Apply all actions",
          "description": "Fix valid/partial, reply to all, resolve all threads"
        },
        {
          "label": "Done — not now",
          "description": "Exit without changes"
        }
      ]
    }
  ]
}
```

**Pluralization**: for N = 1 use `"Apply the proposed action for the 1 thread?"`.

Free-form "Other" parses the same way as in `code-review` (see its Step 3): `1,3,5` / `only valid` / `skip #2` / etc. Ambiguous input → confirm, do not guess.

### Step 6: Apply fixes (tracked fix loop)

For threads classified **Valid** or **Partially valid** in the approved set.

**Pre-gate checklist** (same as `code-review` Step 4):

1. Working tree clean, or user explicitly approved mixing
2. Current branch still matches the PR branch (`git branch --show-current`)
3. Every referenced `file:line` still exists

**Tracked fix loop:**

1. `TaskCreate` one task per thread to fix:
   - `subject`: `Fix thread #N — <file:line> — <classification>`
   - `activeForm`: `Fixing thread #N`
2. For each thread sequentially:
   1. `TaskUpdate status=in_progress`
   2. Read the file region
   3. Apply the fix (Edit, or delegate multi-file to a `general-purpose` subagent per Subagent Mode)
   4. **Post-fix verify** — re-read to confirm change took effect. For type/compile-sensitive edits run the project's own check (e.g. `tsc --noEmit`, `go build`, `pytest --collect-only`, linter). Use whatever the project already uses; do not introduce new tools.
   5. `TaskUpdate status=completed` only on successful verification
3. **On failure** → apply the Failure & Resumption Protocol from [../code-review/references/failure-resumption.md](../code-review/references/failure-resumption.md). Halt, create blocker, surface to user with Retry / Skip / Abort.
4. **Stage and commit**:

   ```bash
   git add <modified files>
   git commit -m "<message>"
   ```

   Commit message format:

   ```
   fix: address review comment <brief>

   Thread: <thread-id or quoted comment summary>
   Why: <short reason>
   ```

   Never use `--no-verify`. Let hooks run. If a hook fails, fix the underlying issue, re-stage, create a **new** commit — do not `--amend` unless the user explicitly asks.

### Step 7: Push

```bash
git push -u origin HEAD
```

`-u origin HEAD` avoids the "no upstream branch" error on first push. **Do not force push.** If push fails because of remote changes, pull/rebase first and reconcile — ask the user if conflicts arise.

**Why push before reply?** Replies cite commit SHAs (`Fixed in abc1234`). If the SHA is not live on origin when the reviewer clicks it, GitHub returns 404. Always land the commits remotely before advertising them.

### Step 8: Reply to each item

Every processed item gets a reply (including invalid/deferred/repeat). The endpoint depends on the **Source**:

#### Step 8a: Inline review threads

Reply threaded to the original inline comment using its REST `databaseId`. Use `-f` (typed) not `-F` (raw string) so the integer `in_reply_to` is coerced correctly — GitHub's REST API rejects a string here with 422:

```bash
gh api repos/"$OWNER"/"$NAME"/pulls/"$PR"/comments \
  -X POST \
  -f in_reply_to="$DATABASE_ID" \
  -f body="<reply>"
```

#### Step 8b: Issue comments and review bodies

These have no thread anchor. Post a new PR issue comment that **quotes or references** the original so the reply is attributable. Mention the reviewer's handle to re-notify them.

```bash
gh pr comment "$PR" --body "<reply>"
```

Or via REST for scripted batching:

```bash
gh api repos/"$OWNER"/"$NAME"/issues/"$PR"/comments \
  -X POST \
  -f body="<reply>"
```

Reply body template for issue-comment / review-body items:

```
@<reviewer> re: <short quote or link to original comment>

<classification reply from the table below>
```

Link syntax for referencing a specific comment: `https://github.com/<OWNER>/<NAME>/pull/<PR>#issuecomment-<databaseId>` (issue comment) or `#pullrequestreview-<databaseId>` (review body).

**Reply templates** (keep concise, cite the commit where applicable):

| Classification          | Reply                                                                                                                          |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| Valid + fixed           | `Valid. <brief explanation>. Fixed in <sha>.`                                                                                  |
| Partially valid + fixed | `Partially valid. <what was right, what was adjusted>. Fixed in <sha>.`                                                        |
| Invalid                 | `Invalid — <technical reasoning with evidence, cite file/line or version>.`                                                    |
| Acknowledged, defer     | `Acknowledged. Out of scope for this PR — <reason, link backlog/issue if applicable>. Leaving this thread open for your call.` |
| Repeat                  | `Already addressed in this PR. See <Design Decisions section / prior thread>.`                                                 |

Never reply before the fix has been verified, committed, **and pushed** (for valid cases) — the `sha` must be live on origin.

### Step 9: Resolve threads

Applies to **inline review threads only**. Issue comments and review bodies have no resolve mechanism on GitHub — the reply in Step 8b is the full closure.

Resolve threads classified **Valid**, **Partially valid**, **Invalid**, or **Repeat** — using the **GraphQL node `id`** from Step 2.

**Do NOT resolve threads classified "Acknowledged, defer".** The reviewer left a valid-but-out-of-scope observation; auto-resolving their thread reads as dismissal. Leave it open so the reviewer can close it themselves or convert it to a follow-up issue.

Batch into a single GraphQL mutation when possible using aliases:

```graphql
mutation {
  r1: resolveReviewThread(input: { threadId: "<NODE_ID_1>" }) {
    thread {
      isResolved
    }
  }
  r2: resolveReviewThread(input: { threadId: "<NODE_ID_2>" }) {
    thread {
      isResolved
    }
  }
  # ...
}
```

Execute via `gh api graphql -f query=...`.

### Step 10: Update PR description (optional)

If any comments were classified **Acknowledged, defer** or **Invalid with important reasoning**, consider adding/updating a **Design Decisions** section in the PR description. Bots typically cannot see prior thread replies — only the PR body and latest diff. Documenting there prevents repeat comments in the next round.

Only update if there is new information not already captured. Do not rewrite sections unrelated to review outcomes.

## Output Behavior

- Do not narrate workflow steps to the user. No "Step 1: ...".
- First user-visible output should be the **summary table** (Step 4), not progress chatter about fetching threads or detecting the stack.
- Surface only: summary table, pre-gate failures, fix progress (via TaskCreate/TaskUpdate), reply/resolve confirmations, and the final push result.

## Anti-Patterns

1. **Trusting comments blindly** — bots and humans both hallucinate or misread. Always re-read the actual code before accepting or rejecting a claim.
2. **Grounding against latest instead of pinned version** — verify library claims against the exact version pinned in the manifest.
3. **Global assumptions in a monorepo** — different packages may pin different versions and conventions. Validate per-package.
4. **Replying before verifying the fix** — never cite a `sha` that isn't real or a fix that wasn't verified.
5. **Skipping hooks** — no `--no-verify` unless the user explicitly asks. Pre-commit hooks exist for a reason.
6. **Force push to address comments** — never. Create new commits. If upstream moved, pull/rebase and reconcile.
7. **Resolving without replying** — every processed thread gets a reply, even invalid/deferred. Resolving silently is rude.
8. **Silent skips on failure** — failed fixes route through the Failure & Resumption Protocol. Never drop a thread without a decision.
9. **Amending someone else's commit** — create a new commit. Only amend your own HEAD and only when the user explicitly asks.
10. **Auto-running the next round** — if the bot re-reviews after your push, this skill does not auto-handle the next round. Let the user re-invoke.
11. **Paraphrasing AskUserQuestion as a prose question** — Step 5 presents choices via the AskUserQuestion tool. Invoke it verbatim so the structured panel renders. A natural-language question in chat is a bug, not an alternative.
12. **Checking only one feedback surface** — GitHub PRs carry feedback across three surfaces (`reviewThreads`, issue-level `comments`, and `reviews.body`). Skipping any of them silently misses entire reviews. Bots like `claude[bot]` post to issue comments; CodeRabbit often posts to `reviews.body`; humans use all three. Step 2 is mandatory in full.
13. **Replying to SHAs that aren't on origin yet** — push before reply. A reviewer clicking `abc1234` before the push completes sees a 404.

## Example Session

```
User: /address-pr-review 1234

[Internal: resolve repo, fetch unresolved threads (3), detect stack, validate each]

Claude:

| # | Thread     | File:line            | Severity | Summary                          | Classification | Action                 |
|---|------------|----------------------|----------|----------------------------------|----------------|------------------------|
| 1 | #R_aaa     | src/auth.ts:45       | HIGH     | Use parameterized query          | Valid          | Fix                    |
| 2 | #R_bbb     | src/api.ts:89        | MED      | Catch should re-throw            | Partially      | Fix (adjusted)         |
| 3 | #R_ccc     | src/utils.ts:12      | LOW      | Rename helper for clarity        | Invalid        | Reply with reasoning   |

[AskUserQuestion: "Apply the proposed actions for all 3 threads?"
 Options: Apply all actions / Done — not now]

User: Apply all actions

[Pre-gate: ✓ clean tree, ✓ branch, ✓ files exist]

[TaskCreate × 2 (for threads 1 and 2 — thread 3 is Invalid, reply only)]

[#1 in_progress → Read → Edit (parameterize query) → verify (re-read) → completed]
[git add src/auth.ts; git commit -m "fix: address review comment on parameterized query

Thread: #R_aaa
Why: prevent SQL injection on user-provided id"]

[#2 in_progress → Read → Edit (throw after log) → verify → completed]
[git add src/api.ts; git commit -m "fix: address review comment on catch re-throw

Thread: #R_bbb
Why: preserve stack; logging alone swallowed the original error"]

[git push -u origin HEAD]  ← push BEFORE reply so SHAs are live

[Reply to #1 (8a): "Valid. Switched to parameterized query. Fixed in abc1234."]
[Reply to #2 (8a): "Partially valid. Re-throw after logging preserves the stack. Fixed in def5678."]
[Reply to #3 (8a): "Invalid — the helper name matches the domain term used in docs/GLOSSARY.md and other callers."]

[Resolve threads #1, #2, #3 in one batched mutation (defer carve-out: none deferred here)]

Claude: ## Done
- 2 threads fixed (commits abc1234, def5678), 1 replied as invalid
- All 3 threads resolved
- Pushed to origin/<branch>
```

## References

- [../code-review/references/dependency-grounding.md](../code-review/references/dependency-grounding.md) — grounding library claims against pinned versions
- [../code-review/references/integration-tracing.md](../code-review/references/integration-tracing.md) — tracing FE ↔ BE ↔ DB ↔ external API when a comment spans tiers
- [../code-review/references/failure-resumption.md](../code-review/references/failure-resumption.md) — failure protocol for the tracked fix loop
- [../code-review/references/gap-categories.md](../code-review/references/gap-categories.md) — gap category definitions (useful when classifying comments)
