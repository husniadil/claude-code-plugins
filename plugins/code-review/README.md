# Code Review Plugin

An iterative, human-in-loop code-review toolkit for Claude Code. Bundles two composable skills covering the full PR lifecycle: find gaps before you ship, and respond to comments after reviewers weigh in.

## Skills

### 1. `code-review` — find gaps

Proactively review your own changes. Two modes:

- **PR Review** — diff-based review against the detected base branch (auto-resolves base via `gh`, upstream, or `origin/HEAD`; no hardcoded `main`)
- **Holistic** — audit an entire codebase or scoped directories; detects source roots from ecosystem signals (`package.json`, `pyproject.toml`, `go.mod`, `pom.xml`, `Cargo.toml`, etc.)

Triggers: "review my PR", "audit this codebase", "review the src/api directory".

### 2. `address-pr-review` — respond to comments

React to existing review threads on a GitHub PR (human or bot). For each unresolved comment: validate against the pinned code, classify (Valid / Partially valid / Invalid / Acknowledged-defer / Repeat), fix where valid, reply with reasoning, and resolve the thread.

Trigger: `/address-pr-review [PR_NUMBER] [subagent|no-subagent|auto]`.

## Installation

```bash
claude plugins install ekstend/code-review
```

## What you get

- **Human-gated loop** — `AskUserQuestion` before every destructive action (fix, reply, resolve, push)
- **Tracked fix loop** — batch fixes surface as `TaskCreate`/`TaskUpdate` progress; `completed` = post-fix verified, `deleted` = explicit skip
- **Failure & Resumption Protocol** — on a failed fix: halt, create a blocker task, offer Retry / Skip / Abort
- **Dependency grounding** — library/API claims verified against the exact pinned version in the manifest/lockfile (Node, Python, Go, Java, Kotlin, Rust, Ruby, PHP, Elixir)
- **End-to-end integration tracing** — frontend → backend → database → external APIs
- **GitHub integration** (`address-pr-review`) — fetch unresolved threads via GraphQL, reply via REST (`databaseId`), resolve via GraphQL mutation; never force-pushes
- **Subagent-aware** — `subagent|no-subagent|auto` argument for both skills; default `auto` picks based on scope size and fix complexity

## Gap categories (10)

| #   | Category                     | Example                                            |
| --- | ---------------------------- | -------------------------------------------------- |
| 1   | **Business Logic**           | Order created without stock check                  |
| 2   | **Integration**              | Frontend expects `userId`, backend sends `user_id` |
| 3   | **Dependency Compatibility** | Uses React 18 API in a project pinned to React 17  |
| 4   | Logic Errors                 | Off-by-one errors, race conditions                 |
| 5   | Security                     | SQL injection, hardcoded secrets                   |
| 6   | Performance                  | N+1 queries, missing memoization                   |
| 7   | Error Handling               | Unhandled rejections, empty catches                |
| 8   | Style                        | Inconsistent naming, magic numbers                 |
| 9   | Tests                        | Untested functions, missing edge cases             |
| 10  | Docs                         | Undocumented APIs                                  |

See `skills/code-review/references/gap-categories.md` for full definitions and severity guides.

## Example — `code-review`

```
You: review my PR

[Internal: resolve base, fetch diff, gather context, validate gaps]

Claude: ## PR Review — Iteration 1

Found 3 gaps in your PR:
1. [HIGH] src/auth.ts:45 — Security: Password stored in plain text
2. [MED] src/api.ts:89 — Error Handling: Unhandled promise rejection
3. [LOW] src/utils.ts:12 — Style: Unused import

[AskUserQuestion: "Apply fixes for all 3 validated gaps?"
 Options: Apply all fixes / Done — looks good]

You: Apply all fixes

[TaskCreate × 3 → sequential fix → verify → completed]

[AskUserQuestion: "Run another review pass to check for new or remaining gaps?"
 Options: Run next pass / Stop — I'm done]

You: Stop — I'm done

Claude: ## Review Complete — 3 gaps fixed across 2 iterations
```

## Example — `address-pr-review`

```
You: /address-pr-review 1234

[Internal: resolve repo, fetch 3 unresolved threads, detect stack, validate each]

Claude:

| # | File:line         | Summary                   | Classification | Action                  |
|---|-------------------|---------------------------|----------------|-------------------------|
| 1 | src/auth.ts:45    | Use parameterized query   | Valid          | Fix                     |
| 2 | src/api.ts:89     | Catch should re-throw     | Partially      | Fix (adjusted)          |
| 3 | src/utils.ts:12   | Rename helper for clarity | Invalid        | Reply with reasoning    |

[AskUserQuestion: "Apply the proposed actions for all 3 threads?"]

You: Apply all actions

[Fix #1, #2 → verify → commit abc1234]
[Reply to #1, #2, #3]
[Resolve #1, #2, #3 in one GraphQL mutation]
[git push -u origin HEAD]

Claude: ## Done — 2 fixed, 1 replied as invalid, all resolved, pushed
```

## Composing the two

Typical PR lifecycle using both skills:

1. `review my PR` → find gaps → apply fixes → push
2. Reviewers / bots leave comments
3. `/address-pr-review` → validate each comment → fix valid ones → reply and resolve → push
4. `review my PR` again to catch anything the comment-fixes introduced

## License

MIT
