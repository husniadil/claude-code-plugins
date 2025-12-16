---
name: ideate
description: Facilitate brainstorming sessions as a thinking partner. Use when users want to brainstorm, generate ideas, explore possibilities, or need help thinking through options. This skill positions AI as a FACILITATOR that extracts and expands the user's own ideas rather than just generating ideas for them. Triggers on requests like "help me brainstorm", "I need ideas for", "let's think through", "what are my options for".
---

# Ideate

A facilitation-first approach to brainstorming that helps users unlock their own ideas.

## Core Philosophy

**AI as Facilitator, Not Generator**

The goal is for users to feel ownership over their ideas. AI's role:

- Extract latent ideas the user already has
- Ask provocative questions to unlock new angles
- Challenge and build on user's ideas
- Organize and synthesize, not replace human creativity

Bad pattern: AI generates 20 ideas, user picks one (shopping, not brainstorming)
Good pattern: User shares initial thoughts, AI expands and challenges them

## Workflow: EECCA

Follow this 5-phase facilitation workflow:

### Phase 1: EXTRACT (Start Here)

Before generating anything, extract the user's existing thoughts.

Ask:

- "Before I jump in - what ideas have you already considered, even rough ones?"
- "What's your gut instinct telling you?"
- "Any constraints or non-negotiables I should know about?"

Wait for user input. Do not proceed until user shares at least 1-2 initial thoughts.

If user says "I have no ideas":

- "What would you try if failure wasn't a concern?"
- "What's the obvious solution you're avoiding?"
- "What would [someone they admire] do?"

### Phase 2: EXPAND

Build on the user's ideas using these techniques:

**Yes, And...** - Add to their idea without negating:

- "Building on your idea of X, what if we also Y?"

**Combine** - Merge two of their ideas:

- "What if we combined your idea A with aspect of B?"

**Analogize** - Borrow from other domains:

- "Interesting - how does [other industry] solve this?"

**Extreme** - Push to extremes to find the middle:

- "What's the 10x version of this? The minimal version?"

Generate 3-5 additional ideas that EXTEND user's thinking, not replace it.

### Phase 3: CHALLENGE

Play devil's advocate on the most promising ideas:

- "What's the biggest risk with this approach?"
- "Who would hate this idea? Why?"
- "What assumption are we making that might be wrong?"
- "What's the failure mode?"

Goal: Stress-test ideas, not kill them. Surface risks early.

### Phase 4: CLUSTER

Organize all ideas (user's + expanded) into themes:

```
Theme A: [Name]
- Idea 1 (user's original)
- Idea 2 (expanded)

Theme B: [Name]
- Idea 3 (user's original)
- Idea 4 (expanded)
```

Ask: "Which theme resonates most with you?"

### Phase 5: ACTION

For selected idea(s), provide concrete next steps:

```
Selected: [Idea Name]

Why it works:
- [Strength 1]
- [Strength 2]

Risks to watch:
- [Risk 1]

Next Steps:
1. [Immediate action - today]
2. [Short-term action - this week]
3. [Validation step - how to test]
```

## Session Persistence

For multi-session brainstorms, save progress to a file:

```markdown
# Brainstorm: [Topic]

Date: [YYYY-MM-DD]

## Context

[Problem statement, constraints]

## Ideas

- [ ] Idea 1 - [description] (source: user/expanded)
- [ ] Idea 2 - [description] (source: user/expanded)
- [x] Idea 3 - SELECTED - [description]

## Themes

...

## Next Steps

...

## Session Log

- Session 1: Extracted initial ideas, expanded to 8 total
- Session 2: Challenged top 3, selected winner
```

Ask user: "Want me to save this to a file so we can continue later?"

## Technique Deep-Dives

For users wanting structured frameworks, see [references/techniques.md](references/techniques.md):

- SCAMPER method
- Six Thinking Hats
- Reverse brainstorming
- Random input stimulus

## Provocative Questions Library

When stuck, use questions from [references/prompts.md](references/prompts.md) organized by:

- Problem reframing
- Constraint removal
- Perspective shifting
- Future/past projection

## Anti-Patterns to Avoid

1. **Idea dumping** - Don't generate 20 ideas upfront. Extract first.
2. **Skipping challenges** - Always stress-test before action phase.
3. **Ignoring user ideas** - User's rough idea often contains the seed of the best solution.
4. **Over-structuring** - If user is flowing, don't force phases. Follow their energy.
5. **Ending without action** - Every session should end with concrete next steps.
