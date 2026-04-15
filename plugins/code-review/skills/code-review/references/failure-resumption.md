# Failure & Resumption Protocol

Handling for fixes that can't complete inside the Tracked Fix Loop (Step 4 of `code-review`): Edit fails, post-fix verification fails, unexpected state, or a delegated subagent returns an error.

## Core rules

- Never silently skip a failed fix.
- Never mark an unverified fix `completed`.
- `completed` = the post-fix check confirmed the change took effect.
- `deleted` (with a reason in `description`) = explicit user-approved skip, because the fix did not land.

## Protocol

When a fix can't complete:

1. **Keep the current task at `in_progress`.** Do not mark `completed`. Do not `deleted` yet — the user hasn't decided.
2. **`TaskCreate` a blocker task** describing the symptom:
   - `subject`: `Blocker on gap #N: <brief symptom>`
   - Use `TaskUpdate addBlockedBy` to link subsequent gap tasks to this blocker so the dependency is visible.
3. **Halt the loop.** Remaining gap tasks stay `pending`.
4. **Surface to the user** with enough context to decide: which gap, what was attempted, what failed, the minimum relevant output/stack/trace.
5. **Ask (via `AskUserQuestion`) how to proceed:**
   - **Retry** — attempt the fix again (possibly after the user adjusts context, stages files, fixes environment, etc.)
   - **Skip this gap, continue** — `TaskUpdate status=deleted` on the stuck task; update `description` to note the skip reason (`"skipped: <reason>"`). Resume the loop from the next gap. Rationale: `deleted` — not `completed` — because the fix did not actually land.
   - **Abort** — exit Step 4 entirely. Pending tasks stay `pending` so the review can be resumed later by re-entering the skill.

## When to use this protocol

- Edit tool returned an error (e.g., `old_string` not found, permission denied)
- Post-fix verification failed (re-read shows the change didn't take effect, or type/compile check errored)
- Delegated subagent returned a failure or a result that doesn't address the gap
- Unexpected state encountered mid-fix (file moved, branch changed, conflicting edit, etc.)

## What NOT to do

- Do not mark the stuck task `completed` "with a note" — `completed` has a specific meaning (verified fix applied).
- Do not silently move on to the next gap and hope the user notices later.
- Do not retry automatically without user approval — the cause of failure may require environment changes they must make first.
- Do not delete the audit trail. `deleted` tasks stay in the list as a record of the decision.
