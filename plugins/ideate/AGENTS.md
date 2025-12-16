# AGENTS.md

Instructions for AI coding agents working on the ideate plugin.

## Overview

The ideate plugin provides a facilitation-first brainstorming skill. The core philosophy is that AI acts as a facilitator to extract and expand the user's own ideas, rather than simply generating ideas for them.

## Structure

```
ideate/
├── .claude-plugin/
│   └── plugin.json       # Plugin metadata
├── CLAUDE.md             # Redirects to AGENTS.md
├── AGENTS.md             # This file
└── skills/
    └── ideate/
        ├── SKILL.md      # Main skill instructions (EECCA workflow)
        └── references/
            ├── techniques.md  # SCAMPER, Six Hats, etc.
            └── prompts.md     # Provocative questions library
```

## Key Concepts

### EECCA Workflow

The skill follows a 5-phase facilitation workflow:

1. **Extract** - Get user's existing ideas before generating anything
2. **Expand** - Build on user's ideas with Yes-And, Combine, Analogize, Extreme
3. **Challenge** - Devil's advocate on promising ideas
4. **Cluster** - Organize ideas into themes
5. **Action** - Concrete next steps for selected ideas

### Anti-Patterns

When modifying this skill, avoid:

- Idea dumping (generating many ideas without extracting first)
- Skipping the challenge phase
- Ignoring user's original ideas
- Over-structuring when user is in flow
- Ending sessions without actionable next steps

## Development Guidelines

- Keep SKILL.md focused on the core workflow
- Reference files should be deep-dives, not required reading
- All changes should reinforce the "facilitator not generator" philosophy
- Test by actually using the skill on real brainstorming problems
