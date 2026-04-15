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
│ 8. Reply to each comment (cite SHA)   │
└──────────────┬───────────────────────┘
               ▼
┌──────────────────────────────────────┐
│ 9. Resolve threads (carve-out defer)  │
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

### Step 2: Fetch feedback (both review threads AND issue-level reviews)

Reviewers land feedback on a PR through **two different channels**. The skill MUST check both — checking only one class silently misses entire reviews.

| Channel                             | Posted as                                                                                          | Where it lives                                          | How to reply                                               | How to "resolve"                                                          |
| ----------------------------------- | -------------------------------------------------------------------------------------------------- | ------------------------------------------------------- | ---------------------------------------------------------- | ------------------------------------------------------------------------- |
| **A. Line-anchored review threads** | GitHub Review with inline comments                                                                 | `reviewThreads` (GraphQL) / `pulls/:n/comments` (REST)  | `pulls/:n/comments` with `-f in_reply_to=<databaseId>`     | `resolveReviewThread` mutation with thread `id`                           |
| **B. Issue-level PR comments**      | Single comment on the Conversation tab (bot summaries, `@claude` reviews, human free-form reviews) | `issueComments` (GraphQL) / `issues/:n/comments` (REST) | `issues/:n/comments` (new issue comment; no `in_reply_to`) | No resolve state — use a 👍 reaction or mention in PR description instead |

**Always run Step 2a AND Step 2b.** A PR with zero `reviewThreads` is not necessarily "no review" — the reviewer may have posted a structured review as an issue-level comment.

### Step 2a: Fetch unresolved review threads

Use GraphQL in a single call to get both the GraphQL thread `id` (for resolving) and the REST `databaseId` (for replying):

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
    }
  }
}
```

Execute via `gh api graphql -f query=...`.

Filter threads to `isResolved == false`. Whether or not any remain, continue to Step 2b — issue-level reviews can exist independently.

**Pagination note:** `reviewThreads(first: 50)` and `comments(first: 5)` will silently truncate large inputs. If `totalCount > 50` threads or `totalCount > 5` comments on any thread, re-run the query with a `pageInfo { endCursor hasNextPage }` selection and an `after:` argument to paginate until exhaustion. For most PRs the defaults are enough; for round-2 bot discussions or long human threads, paginate.

**Why both IDs**: `databaseId` (integer) is used for REST `in_reply_to` replies (Step 8). `id` (GraphQL node ID) is used for `resolveReviewThread` (Step 9). Both come from the same query — no extra round trip.

### Step 2b: Fetch issue-level PR comments (bot / human review summaries)

```bash
gh api repos/"$OWNER"/"$NAME"/issues/"$PR"/comments \
  --jq '.[] | {id, user: .user.login, created_at, body}'
```

Scan each comment for review-style content. Signals that a comment is a review rather than casual chatter:

- Author matches a known review bot: `claude[bot]`, `coderabbitai[bot]`, `deepsource-autofix[bot]`, `sonarqubecloud[bot]`, `sourcery-ai[bot]`, etc.
- Body contains structured sections: `## Findings`, `### Critical`, severity emojis (🔴 🟠 🟡), `file:line` references, check-lists of tasks, or review verdict language ("Approve", "Request changes", "LGTM", "Blocking", "Nits")
- Body references the PR's diff or cites specific files/lines from it

For each matching comment, **parse findings out of the prose**. Each finding becomes one "virtual thread" in Step 4's table with:

- `Thread`: the issue comment `id` (format it as `issue-<id>` to distinguish from review-thread `#R_...`)
- `File:line`: extracted from the finding text
- `Summary`: the finding description
- `Severity`: inferred from headings/emojis or labelled explicitly

**Replying to an issue-level review** is different from replying to a review thread:

- You cannot use `in_reply_to` — issue comments do not thread.
- Post **one consolidated reply** as a new issue comment that cites each finding and the fix SHA, rather than N per-finding replies. This avoids noise.
- There is no thread to "resolve" — the review stays visible on the Conversation tab. If the bot re-reviews after your push, it will post a fresh comment.

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

For each unresolved review thread:

1. **Read the commented code** — open the file at the commented line range. Use `Read` directly; do not trust the comment's excerpt.
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

Present a summary table to the user. The `Thread` column identifies the source — `#R_xxx` for a review thread, `issue-<id>` for a finding parsed out of an issue-level review.

```
| # | Thread      | File:line | Severity | Summary | Classification | Proposed action |
|---|-------------|-----------|----------|---------|----------------|-----------------|
| 1 | #R_aaa      | ...       | ...      | ...     | ...            | ...             |
| 2 | issue-1234  | ...       | ...      | ...     | ...            | ...             |
```

### Step 5: Present and ask

Invoke the **AskUserQuestion** tool with two options (verbatim — the structured panel must render; do not substitute a prose question). The "Other" free-form box the tool provides automatically is the fallback for any subset.

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

**Why push before reply?** Replies cite a commit SHA (`Fixed in abc1234`). If the SHA is not live on origin when the reviewer clicks it, GitHub returns 404. Always land the commit remotely before advertising it.

### Step 8: Reply to each comment

Branch on the thread source:

**Review threads (`#R_xxx`)** — per-finding reply via REST, using the **`databaseId`** captured in Step 2a:

```bash
gh api repos/"$OWNER"/"$NAME"/pulls/"$PR"/comments \
  -X POST \
  -f in_reply_to="$DATABASE_ID" \
  -f body="<reply>"
```

**Reply templates** (keep concise, cite the commit where applicable):

| Classification          | Reply                                                                                                                          |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| Valid + fixed           | `Valid. <brief explanation>. Fixed in <sha>.`                                                                                  |
| Partially valid + fixed | `Partially valid. <what was right, what was adjusted>. Fixed in <sha>.`                                                        |
| Invalid                 | `Invalid — <technical reasoning with evidence, cite file/line or version>.`                                                    |
| Acknowledged, defer     | `Acknowledged. Out of scope for this PR — <reason, link backlog/issue if applicable>. Leaving this thread open for your call.` |
| Repeat                  | `Already addressed in this PR. See <Design Decisions section / prior thread>.`                                                 |

Never reply before the fix has been verified, committed, **and pushed** (for valid cases) — the `sha` must be live on origin.

**Issue-level reviews (`issue-<id>`)** — post **one consolidated reply** as a new issue comment summarizing all findings from that review:

```bash
gh api repos/"$OWNER"/"$NAME"/issues/"$PR"/comments \
  -X POST \
  -f body="<consolidated reply>"
```

Recommended body structure:

```
Thanks for the review! Addressed as follows:

- Finding 1 (<brief>): Valid. <fix>. Fixed in <sha>.
- Finding 2 (<brief>): Partially valid. <adjustment>. Fixed in <sha>.
- Finding 3 (<brief>): Invalid — <reasoning>.
- Finding 4 (<brief>): Acknowledged, deferred — <reason>.
```

Do **not** try to use `in_reply_to` for an issue comment; that field is only valid for review-thread comments.

### Step 9: Resolve threads

Resolve threads that were **Valid**, **Partially valid**, **Invalid**, or **Repeat** — using the **GraphQL node `id`** from Step 2.

**Do NOT resolve threads classified "Acknowledged, defer".** The reviewer left a valid-but-out-of-scope observation; auto-resolving their thread reads as dismissal. Leave it open so the reviewer can acknowledge themselves or convert it to a follow-up issue.

**Issue-level reviews have no resolve state.** Skip this step for any `issue-<id>` entries — they don't live in `reviewThreads`. The consolidated reply from Step 8 is the resolution record.

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
12. **Checking only review threads** — bots (Claude, CodeRabbit, DeepSource, etc.) and humans often post full reviews as a single **issue-level comment** on the Conversation tab. If Step 2a returns zero threads, Step 2b is still mandatory. Concluding "no review to address" based solely on `reviewThreads` is the exact bug this skill was built to prevent.
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

[git push -u origin HEAD]  ← push BEFORE reply so SHA is live

[Reply to #1: "Valid. Switched to parameterized query. Fixed in abc1234."]
[Reply to #2: "Partially valid. Re-throw after logging preserves the stack. Fixed in def5678."]
[Reply to #3: "Invalid — the helper name matches the domain term used in docs/GLOSSARY.md and other callers."]

[Resolve threads #1, #2, #3 in one batched mutation]

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
