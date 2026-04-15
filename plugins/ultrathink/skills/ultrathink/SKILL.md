---
name: ultrathink
description: Sequential thinking tool for multi-step problem solving with structured reasoning, confidence tracking, and assumption management.
when_to_use: Use when breaking down complex problems into steps, planning implementations, debugging multi-layered issues, or when explicit step-by-step reasoning is beneficial.
---

# UltraThink - Sequential Thinking CLI

A tool for dynamic and reflective problem-solving through structured, sequential thoughts.

## When to Use

Use this skill for:

- Breaking down complex problems (>3 reasoning steps)
- Planning and design with room for revision
- Architecture decisions with multiple trade-offs
- Algorithm design and optimization
- Debugging multi-layered issues
- Analysis that might need course correction

Do NOT use for:

- Simple one-step answers
- Straightforward code edits
- Basic file operations
- Simple factual questions

## Instructions

1. Start a session with initial thought and estimated total
2. Continue session using `session_id` from response
3. Use `--confidence` to track uncertainty (0.0-1.0)
4. Revise thoughts with `--is-revision --revises <num>`
5. Branch to explore alternatives with `--branch-from <num> --branch-id <name>`
6. Track assumptions with `--assumptions`, `--depends-on`, `--invalidates`
7. Monitor `risky_assumptions` in response
8. Continue until `next_thought_needed` is false

## Quick Start

```bash
# Start new session
uv run ${CLAUDE_PLUGIN_ROOT}/skills/ultrathink/scripts/ultrathink.py -t "Analyzing the problem..." -n 5

# Continue session
uv run ${CLAUDE_PLUGIN_ROOT}/skills/ultrathink/scripts/ultrathink.py -t "Next step..." -n 5 -s <session-id>

# With confidence
uv run ${CLAUDE_PLUGIN_ROOT}/skills/ultrathink/scripts/ultrathink.py -t "I believe X is correct" -n 3 -c 0.8

# With assumption
uv run ${CLAUDE_PLUGIN_ROOT}/skills/ultrathink/scripts/ultrathink.py -t "Assuming Redis available" -n 3 \
  --assumptions '[{"id":"A1","text":"Redis is available"}]'
```

## Example Session

```
Thought 1 (confidence: 0.6): "Analyzing access patterns for caching strategy..."
Thought 2 (confidence: 0.7): "Two approaches: LRU or LFU..."
Thought 3 (revision of 2): "Should also consider TTL-based expiration..."
Thought 4 (branch from 2): "Exploring hybrid LRU+TTL approach..."
Thought 5 (confidence: 0.95): "Hybrid approach recommended."
```

## Reference

For complete documentation including all CLI options, response schema, and advanced examples, see [references/REFERENCE.md](references/REFERENCE.md).
