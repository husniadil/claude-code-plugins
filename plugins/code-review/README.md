# Code Review Plugin

An iterative, human-in-loop code review skill for Claude Code that reviews code, identifies gaps (including business logic issues), and fixes them in cycles until clean.

## Features

- **Two Review Modes**: PR diff review or holistic codebase audit
- **Business Logic Awareness**: Understands domain rules, not just code correctness
- **Context-Aware**: Gathers surrounding context (callers, dependencies, types) before flagging issues
- **Iterative Loop**: Review → Fix → Re-review until clean
- **Human-in-Loop**: User approves every iteration and selects which gaps to fix
- **9 Gap Categories**: Business logic, integrations, code logic, security, performance, error handling, style, tests, docs
- **End-to-End Integration Tracing**: Traces frontend → backend → database → external APIs

## Installation

```bash
claude plugins install ekstend/code-review
```

## Usage

### PR Review Mode

Review changes in your current branch:

```
review my PR
check my changes
review this branch against main
```

### Holistic Review Mode

Review entire codebase or specific areas:

```
review this codebase
audit the project for gaps
review the src/api directory
```

## Workflow

1. **Determine Mode**: PR review vs holistic codebase review
2. **Understand Business Context**: Read docs, understand feature intent
3. **Gather Technical Context**: Check callers, dependencies, data flow
4. **Identify Gaps**: Find issues across all 8 categories
5. **Present**: Shows numbered list of gaps with severity
6. **Select**: You choose which gaps to fix (or skip)
7. **Fix**: Claude fixes selected gaps
8. **Loop**: Re-reviews and repeats until you're satisfied

## Gap Categories

| #   | Category           | Description                          | Example                                            |
| --- | ------------------ | ------------------------------------ | -------------------------------------------------- |
| 1   | **Business Logic** | Missing validations, wrong workflows | Order created without stock check                  |
| 2   | **Integration**    | Contract mismatches between systems  | Frontend expects `userId`, backend sends `user_id` |
| 3   | Logic Errors       | Technical bugs, conditions           | Off-by-one errors                                  |
| 4   | Security           | Vulnerabilities                      | SQL injection                                      |
| 5   | Performance        | Slowdowns, memory issues             | N+1 queries                                        |
| 6   | Error Handling     | Missing try/catch                    | Unhandled rejections                               |
| 7   | Style              | Inconsistent patterns                | Magic numbers                                      |
| 8   | Tests              | Missing coverage                     | Untested functions                                 |
| 9   | Docs               | Missing documentation                | Undocumented APIs                                  |

## Context-Aware Review

The skill doesn't blindly check the diff. For each change, it:

1. **Understands the business intent** - What is this code supposed to do?
2. **Checks callers** - Are they passing correct arguments?
3. **Verifies dependencies** - Are contracts being met?
4. **Traces data flow** - Can data get corrupted?
5. **Flags related issues** - Pre-existing problems that affect new code
6. **Traces integrations end-to-end** - Frontend → API → Backend → Database

### Integration Tracing Example

```
Frontend: src/components/OrderForm.tsx
  → calls: POST /api/orders { productId, quantity }

Backend: src/routes/orders.ts
  → handler: createOrder(req.body)
  → validates: productId, quantity

Service: src/services/orderService.ts
  → checks: inventory
  → calls: db.orders.create()

GAPS FOUND:
- Frontend sends quantity as string, backend expects number
- No error handling for insufficient inventory response
```

## Example Session

```
You: review my PR

Claude: Let me understand the context first...
[Reads AGENTS.md, checks related files, traces callers]

Found 4 gaps in your PR:

1. [HIGH] src/orders.ts:45 - Business Logic: Order created without checking stock
2. [HIGH] src/auth.ts:23 - Security: Password stored in plain text
3. [MED] src/api.ts:89 - Error Handling: Unhandled promise rejection
4. [LOW] src/utils.ts:12 - Style: Unused import

Which gaps would you like me to fix?
> Fix all

Claude: Fixing all 4 gaps...
[Applies fixes, also updates 2 callers that needed changes]

Re-reviewing after fixes...

Found 0 gaps. Your PR looks good!

Review Complete!
- Iterations: 2
- Gaps fixed: 4
- Related files updated: 2
```

## License

MIT
