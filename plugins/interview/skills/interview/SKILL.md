---
name: interview
description: Deep requirements gathering through probing questions that surface hidden requirements, edge cases, and trade-offs before implementation.
when_to_use: Use when a feature, system, or task needs thorough requirement discovery prior to planning.
---

# Interview

A deep requirements gathering skill that uncovers hidden requirements, edge cases, and trade-offs through thoughtful, in-depth questioning.

## Core Philosophy

**Interviewer, Not Order Taker**

Don't just accept the initial request at face value. Your role is to:

- Uncover requirements the user hasn't explicitly considered
- Surface edge cases and failure modes before they become bugs
- Clarify trade-offs so the user makes informed decisions
- Ensure the implementation plan will actually solve the real problem

Bad pattern: User says "add login", you start implementing login
Good pattern: User says "add login", you ask about session management, OAuth vs password, account recovery, rate limiting, existing auth systems, mobile app integration...

## Workflow: CDEEPER

Follow this 7-phase interview workflow:

### Phase 0: CONTEXTUALIZE (Codebase Exploration)

**BEFORE asking any questions**, explore the codebase to understand existing patterns:

1. **Identify the tech stack**: Use Glob/Grep to find package.json, requirements.txt, go.mod, etc.
2. **Find related code**: Search for similar features or patterns already implemented
3. **Understand conventions**: Look at existing code style, naming, architecture patterns
4. **Check integrations**: Identify databases, APIs, services already in use

This prevents asking obvious questions like "what database should we use?" when PostgreSQL is already used everywhere.

```bash
# Example exploration
Glob: **/package.json, **/requirements.txt
Grep: "database", "prisma", "sequelize", "mongoose"
Read: src/config/, src/lib/
```

**Skip questions about things you can infer from the codebase.** Only ask when there's genuine ambiguity or the new feature requires a different approach than existing patterns.

### Phase 1: DISCOVER

Understand the core intent before asking questions.

**Input Handling:**

1. **Prompt only**: Analyze the request directly
2. **Plan file path provided**: Read the file using Read tool
3. **Both provided**: Plan file takes precedence; prompt provides additional context
4. **File not found**: Inform user and ask them to provide the correct path or describe requirements directly

**If user points to a plan file:**

1. Read the plan file using the Read tool
2. If file doesn't exist or is empty, inform user:
   ```
   I couldn't read the plan file at [path]. Could you:
   - Check the file path is correct, or
   - Describe the requirements here instead?
   ```
3. Understand the scope and objectives
4. Identify gaps in the plan that need clarification

**Analyzing the request:**

1. Identify the core goal (what problem are they solving?)
2. Note what's explicitly stated vs what's assumed
3. Cross-reference with codebase context from Phase 0

**Initial summary** (before questions):

```
I understand you want to: [core goal]

From what you've shared, I see:
- [explicit requirement 1]
- [explicit requirement 2]

I have questions about areas that could significantly impact implementation.
```

### Phase 2: EXPLORE (Technical Implementation)

Ask probing questions about technical aspects. These should NOT be obvious from the prompt.

**Architecture & Data Flow:**

- How does this integrate with existing systems?
- What data needs to flow between components?
- Are there existing patterns in the codebase we should follow or deliberately break from?
- What's the expected data volume/growth rate?

**State Management:**

- Where does state live? Client, server, or both?
- How should state sync across multiple tabs/devices?
- What happens to in-progress state if the user navigates away?

**Dependencies & Integrations:**

- What external services does this touch?
- Are there rate limits, quotas, or SLAs to consider?
- What happens if a dependency is down or slow?

Use `AskUserQuestion` with 1-4 questions per batch. Wait for answers before proceeding.

Example:

```json
{
  "questions": [
    {
      "question": "How should this integrate with the existing authentication system? Does it need to work for logged-out users too?",
      "header": "Auth scope",
      "multiSelect": false,
      "options": [
        {
          "label": "Logged-in only",
          "description": "Require authentication, use existing session"
        },
        {
          "label": "Both",
          "description": "Work for logged-in and anonymous users differently"
        },
        { "label": "Anonymous only", "description": "No authentication needed" }
      ]
    },
    {
      "question": "What's the expected data volume for this feature in the first year?",
      "header": "Scale",
      "multiSelect": false,
      "options": [
        {
          "label": "Low (<1K/day)",
          "description": "Simple storage, no optimization needed"
        },
        {
          "label": "Medium (1K-100K/day)",
          "description": "Need indexes, maybe caching"
        },
        {
          "label": "High (>100K/day)",
          "description": "Need to design for scale from start"
        }
      ]
    }
  ]
}
```

### Phase 3: EDGE (Edge Cases & Boundaries)

Uncover scenarios that break naive implementations.

**Error States:**

- What happens when [critical operation] fails halfway through?
- How do we handle network timeouts? Retry? Show error? Queue?
- What if the user submits the same action twice quickly (double-click)?

**Boundary Conditions:**

- What's the max size/length/count we should support?
- What happens at zero? At the limit? Just over the limit?
- Are there time-based boundaries (midnight, timezones, DST)?

**Concurrent Access:**

- Can multiple users/tabs modify this simultaneously?
- What's the conflict resolution strategy?
- Do we need optimistic or pessimistic locking?

**Data Integrity:**

- What if referenced data is deleted?
- How do we handle orphaned records?
- Is there a soft-delete requirement?

Example:

```json
{
  "questions": [
    {
      "question": "If a user clicks 'Submit' twice quickly before the first request completes, what should happen?",
      "header": "Double-submit",
      "multiSelect": false,
      "options": [
        {
          "label": "Debounce",
          "description": "Ignore second click, first request wins"
        },
        {
          "label": "Idempotent",
          "description": "Both requests safe, server deduplicates"
        },
        { "label": "Queue", "description": "Process both in order" }
      ]
    }
  ]
}
```

### Phase 4: PRIORITIZE (Trade-offs & Constraints)

Clarify what matters most when trade-offs arise.

**Performance vs Simplicity:**

- Is real-time freshness required, or is eventual consistency okay?
- Should we optimize for read speed or write speed?
- Is it worth extra complexity for 10% better performance?

**Flexibility vs Complexity:**

- Do we need to support future variations, or can we hardcode for now?
- Should this be configurable by admins, or is developer config sufficient?
- Build for extensibility or build the minimal thing?

**Time vs Polish:**

- What's the minimum viable version?
- What can be deferred to a fast-follow?
- Are there hard deadlines driving scope decisions?

**Compatibility:**

- What browsers/devices must be supported?
- Are there backward compatibility requirements?
- Can we break existing APIs/behavior?

Example:

```json
{
  "questions": [
    {
      "question": "When this data changes, how quickly must users see the update?",
      "header": "Freshness",
      "multiSelect": false,
      "options": [
        {
          "label": "Real-time",
          "description": "WebSocket/SSE, see changes instantly"
        },
        { "label": "Near real-time", "description": "Poll every 5-30 seconds" },
        {
          "label": "Refresh-based",
          "description": "See updates on next page load"
        }
      ]
    },
    {
      "question": "If we have to choose, which matters more?",
      "header": "Trade-off",
      "multiSelect": false,
      "options": [
        {
          "label": "Ship fast",
          "description": "Minimal viable version, iterate later"
        },
        {
          "label": "Ship complete",
          "description": "Full feature set, even if slower"
        },
        {
          "label": "Ship robust",
          "description": "Handle all edge cases, even if simpler"
        }
      ]
    }
  ]
}
```

### Phase 5: EXPERIENCE (UX/DX Considerations)

Probe the human side of the implementation.

**User Journeys:**

- What's the user doing before they encounter this feature?
- What should they be able to do after?
- What's the happy path? What are the alternate paths?

**Feedback & Affordances:**

- How does the user know something is happening (loading states)?
- How do they know it worked (success states)?
- How do they know it failed and what to do about it?

**Developer Experience:**

- Who will maintain this code after initial implementation?
- Are there conventions in the codebase we should follow?
- Should this be documented? How?

**Accessibility & Internationalization:**

- Are there accessibility requirements (screen readers, keyboard nav)?
- Will this need to support multiple languages?
- Are there locale-specific behaviors (date formats, currencies)?

Example:

```json
{
  "questions": [
    {
      "question": "When this operation takes more than 200ms, what should the user see?",
      "header": "Loading",
      "multiSelect": false,
      "options": [
        {
          "label": "Spinner",
          "description": "Block UI with loading indicator"
        },
        { "label": "Skeleton", "description": "Show placeholder content" },
        {
          "label": "Optimistic",
          "description": "Show success immediately, rollback on error"
        },
        {
          "label": "Background",
          "description": "Let user continue, show toast when done"
        }
      ]
    }
  ]
}
```

### Phase 6: READY (Confirm & Transition)

When you've covered the important areas, summarize and confirm.

**Requirements Summary:**

```
## Interview Summary

Based on our discussion, here's what I understand:

### Core Requirements
- [requirement 1]
- [requirement 2]

### Technical Decisions
- [decision 1]: [chosen option] because [reason from user]
- [decision 2]: [chosen option] because [reason from user]

### Edge Cases Handled
- [edge case 1]: [how we'll handle it]
- [edge case 2]: [how we'll handle it]

### Trade-offs Accepted
- [trade-off]: Chose [option] over [alternative]

### Out of Scope (for now)
- [deferred item 1]
- [deferred item 2]
```

**Final confirmation:**

```json
{
  "questions": [
    {
      "question": "Does this summary capture the requirements correctly? Any gaps?",
      "header": "Complete?",
      "multiSelect": false,
      "options": [
        {
          "label": "Looks complete",
          "description": "Ready to move to planning"
        },
        { "label": "Minor tweaks", "description": "I'll clarify a few things" },
        {
          "label": "Missing area",
          "description": "We need to discuss [topic] more"
        }
      ]
    }
  ]
}
```

**Offer plan mode:**

If user confirms completeness:

```json
{
  "questions": [
    {
      "question": "Would you like me to create an implementation plan based on these requirements?",
      "header": "Next step",
      "multiSelect": false,
      "options": [
        {
          "label": "Enter plan mode",
          "description": "I'll design the implementation approach for your review"
        },
        {
          "label": "Start implementing",
          "description": "Skip planning, start coding now"
        },
        {
          "label": "Save requirements",
          "description": "Save this summary to a file, decide later"
        }
      ]
    }
  ]
}
```

If user chooses "Enter plan mode", use the `EnterPlanMode` tool.

## Phase Completion Criteria

Each phase has specific completion signals. Move to the next phase when criteria are met:

| Phase                | Complete When                                                                                                            |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| **0. Contextualize** | Tech stack identified, related patterns found, conventions understood (typically 1-2 minutes of exploration)             |
| **1. Discover**      | Core goal articulated, user confirms understanding is correct                                                            |
| **2. Explore**       | Key architectural decisions made (data flow, integrations, state management) OR user indicates "enough technical detail" |
| **3. Edge**          | At least 3 edge cases discussed OR user says "I'll handle edge cases as they come up"                                    |
| **4. Prioritize**    | Primary trade-off direction chosen (speed vs completeness vs robustness)                                                 |
| **5. Experience**    | Happy path UX defined, error handling approach chosen                                                                    |
| **6. Ready**         | User confirms summary is accurate, chooses next action                                                                   |

**Signals to move on:**

- User provides clear, confident answers (not "I don't know" or "maybe")
- User explicitly says "let's move on", "that's enough", "next topic"
- You've asked 2-3 questions in a category with no new information surfacing
- User's answers reveal they've already thought deeply about this area

**Signals to dig deeper:**

- User says "I haven't thought about that"
- Answers are vague or contradictory
- User asks clarifying questions back (indicates uncertainty)
- Critical area (security, data integrity) not yet covered

## Skip-to-Summary Flow

After **each question batch** (starting from Phase 2, after Discover completes), offer the user a choice to continue or skip:

```json
{
  "questions": [
    {
      "question": "How would you like to proceed?",
      "header": "Continue?",
      "multiSelect": false,
      "options": [
        {
          "label": "Continue",
          "description": "Ask more questions in this phase"
        },
        { "label": "Next phase", "description": "Move to the next phase" },
        {
          "label": "Skip to summary",
          "description": "Jump to requirements summary now"
        }
      ]
    }
  ]
}
```

**When user chooses "Skip to summary":**

First, ask their preferred summary style:

```json
{
  "questions": [
    {
      "question": "What level of summary would you like?",
      "header": "Summary style",
      "multiSelect": false,
      "options": [
        {
          "label": "Minimal",
          "description": "List what was discussed, mark rest as 'not covered'"
        },
        {
          "label": "Inferred",
          "description": "Make reasonable assumptions based on codebase + answers"
        },
        {
          "label": "Critical first",
          "description": "Ask 2-3 critical questions (security, data integrity), then summarize"
        }
      ]
    }
  ]
}
```

**Early skip warning:**

If user tries to skip before Phase 2 (during Contextualize or Discover):

```
⚠️ Warning: We haven't gathered enough requirements yet.

So far I only know:
- [what little we've discovered]

Skipping now means I'll have to make many assumptions. Are you sure?
```

Then proceed with summary style choice if they confirm.

## Question Tracking

Track all questions asked to avoid redundancy and enable confidence scoring:

**Mental tracking format:**

| Phase | Topic       | Question        | Answer              | Confidence |
| ----- | ----------- | --------------- | ------------------- | ---------- |
| 0     | Tech stack  | (explored)      | Next.js, PostgreSQL | 100%       |
| 1     | Core goal   | What problem?   | User auth flow      | 95%        |
| 2     | Auth scope  | Logged-in only? | Yes                 | 90%        |
| 2     | Data volume | Expected scale? | Medium              | 75%        |

**Deduplication rules:**

- Before asking a question, check if a similar topic was already covered
- If covered, reference the previous answer: "Earlier you mentioned [X], building on that..."
- Don't re-ask the same question in different words
- If user's answer revealed new information, follow up on that instead of asking unrelated questions

## Confidence Scoring

Assign a confidence percentage to each gathered requirement:

| Confidence | When to Assign                                                       |
| ---------- | -------------------------------------------------------------------- |
| 90-100%    | User gave explicit, unambiguous answer                               |
| 70-89%     | User answered with some uncertainty ("probably", "I think", "maybe") |
| 50-69%     | Inferred from codebase patterns + partial user confirmation          |
| 30-49%     | Assumed based on codebase only, user didn't explicitly confirm       |
| <30%       | Pure assumption, no supporting evidence                              |

**Display in summary:**

```markdown
### Core Requirements

- User authentication via OAuth (95%)
- Support for multiple providers (80%)
- Session management with Redis (60% - inferred from existing patterns)
- Rate limiting on auth endpoints (40% - ASSUMED, not discussed)
```

Requirements below 50% should be flagged as needing verification before implementation.

## Question Ordering Strategy

Use a hybrid approach: start with domain-appropriate questions, then adapt based on answers.

**Domain Detection (Phase 0):**

Based on codebase exploration, classify the task domain:

| Domain         | Indicators                         | Question Priority                          |
| -------------- | ---------------------------------- | ------------------------------------------ |
| Frontend-heavy | React/Vue/Angular, components, CSS | UX → State → Components → API              |
| Backend-heavy  | API routes, database, services     | Data → API → Integrations → Scale          |
| Full-stack     | Both frontend and backend changes  | API contract → Data → UX → Integration     |
| Infrastructure | Deployment, Docker, CI/CD          | Security → Scale → Deployment → Monitoring |
| Data/Analytics | Queries, reports, dashboards       | Data flow → Performance → Accuracy → UX    |

**Adaptive Reordering Triggers:**

Adjust question priority based on user answers:

| User Mentions          | Prioritize Next                   |
| ---------------------- | --------------------------------- |
| Security concern       | Security & auth questions         |
| Performance worry      | Scale & optimization questions    |
| Tight deadline         | MVP scope & trade-off questions   |
| "I don't know"         | Skip that category, revisit later |
| Integration complexity | External service questions        |
| Data sensitivity       | Compliance & audit questions      |

**Example adaptation:**

```
Initial plan (Backend-heavy): Data → API → Integrations → Scale

User says: "This handles payment data"

Adapted plan: Data → Security → Compliance → API → Integrations
```

## Adaptive Questioning

Adapt your questions based on the domain:

**Frontend-focused:**

- Component architecture, state management, styling approach
- Responsive design, animations, accessibility
- Bundle size, code splitting, lazy loading

**Backend-focused:**

- API design, data modeling, migrations
- Caching strategy, background jobs, queues
- Logging, monitoring, alerting

**Infrastructure-focused:**

- Deployment strategy, rollback procedures
- Scaling approach, cost considerations
- Security hardening, compliance requirements

**Full-stack:**

- API contracts between frontend and backend
- Shared types/validation
- End-to-end testing strategy

## Question Techniques

See [references/question-categories.md](references/question-categories.md) for detailed question templates organized by:

- Technical deep-dives
- Edge case discovery
- Trade-off clarification
- UX/DX considerations
- Security & operations

## Handling Early Exit

Users may want to skip ahead. Handle gracefully:

**When user says "just implement it" or "let's skip ahead":**

```json
{
  "questions": [
    {
      "question": "I have a few more questions that could prevent issues later. How would you like to proceed?",
      "header": "Continue?",
      "multiSelect": false,
      "options": [
        {
          "label": "Quick finish",
          "description": "Ask only critical questions (security, data integrity), then plan"
        },
        {
          "label": "Skip to plan",
          "description": "I'll make reasonable assumptions and note them in the plan"
        },
        {
          "label": "Continue interview",
          "description": "Let's keep going, I have time"
        }
      ]
    }
  ]
}
```

**If user chooses "Skip to plan":**

1. Summarize what you DO know from the conversation
2. List assumptions you'll make (mark as "ASSUMPTION - verify before implementing")
3. Proceed to plan mode with explicit assumption markers

**Partial Requirements Summary:**

```
## Interview Summary (Partial)

Completed phases: Contextualize, Discover, Explore (partial)
Skipped phases: Edge, Prioritize, Experience

### What We Covered
- [covered requirement 1]
- [covered requirement 2]

### Assumptions Made (Verify Before Implementing)
- ASSUMPTION: [assumption 1] - defaulting to [choice] because [reason]
- ASSUMPTION: [assumption 2] - using existing pattern from [file]

### Not Discussed (May Need Revisiting)
- Edge case handling
- Trade-off priorities
- UX details
```

## Anti-Patterns to Avoid

1. **Obvious questions** - Don't ask what the user already stated. If they said "add login with Google OAuth", don't ask "should we use OAuth?"

2. **Yes/no questions** - Prefer scenario-based or option-based questions that surface hidden requirements.

3. **Question overload** - Batch 1-4 questions at a time. Let user answer before asking more.

4. **Skipping to planning** - Don't rush to plan mode. Incomplete requirements lead to rework.

5. **Ignoring answers** - Build on previous answers. Reference what the user said.

6. **Generic questions** - Tailor questions to the specific feature and codebase context.

7. **Missing the real problem** - Sometimes users ask for a solution when they have a problem. Understand the underlying need.

8. **Ignoring impatience** - If user wants to move faster, respect that. Use early exit flow above.

## Session Persistence

For multi-session interviews, save progress with explicit phase tracking:

```markdown
# Interview: [Feature Name]

Created: [YYYY-MM-DD]
Last Updated: [YYYY-MM-DD HH:MM]
Status: [In Progress / Complete / Skipped at Phase N]
Current Phase: [0-6] - [Phase Name]
Detected Domain: [Frontend-heavy / Backend-heavy / Full-stack / Infrastructure]

## Progress Tracker

- [x] Phase 0: Contextualize - COMPLETE
- [x] Phase 1: Discover - COMPLETE
- [ ] Phase 2: Explore - IN PROGRESS (2/4 questions answered)
- [ ] Phase 3: Edge
- [ ] Phase 4: Prioritize
- [ ] Phase 5: Experience
- [ ] Phase 6: Ready

## Questions Asked

| Phase | Topic       | Question                      | Answer                     | Confidence |
| ----- | ----------- | ----------------------------- | -------------------------- | ---------- |
| 0     | Tech stack  | (explored)                    | Next.js, PostgreSQL, Redis | 100%       |
| 1     | Core goal   | What problem are you solving? | User authentication flow   | 95%        |
| 2     | Auth scope  | Logged-in users only?         | Yes, require auth          | 90%        |
| 2     | Data volume | Expected scale?               | Medium (1K-100K/day)       | 75%        |

## Context

**Original Request:**
[Original request]

**Codebase Context (Phase 0):**

- Tech stack: [e.g., Next.js, PostgreSQL, Redis]
- Related patterns: [e.g., existing auth uses NextAuth]
- Conventions: [e.g., uses repository pattern, Zod for validation]
- Detected domain: [Frontend-heavy / Backend-heavy / etc.]

## Discoveries

### Phase 1: Discover

- Core goal: [what they're trying to achieve]
- Explicit requirements: [what they stated]
- Implicit requirements: [what we inferred]

### Phase 2: Explore

- [Q]: [question asked]
- [A]: [user's answer]
- [Decision]: [resulting decision]
- [Confidence]: [percentage]

### Phase 3: Edge

- [edge case]: [how to handle] ([confidence]%)

### Phase 4: Prioritize

- [trade-off]: [chosen direction] ([confidence]%)

### Phase 5: Experience

- [UX decision]: [choice made] ([confidence]%)

## Requirements Summary

### High Confidence (90-100%)

- [requirement] (95%)

### Medium Confidence (50-89%)

- [requirement] (70%)

### Low Confidence / Assumed (<50%)

- [requirement] (40% - ASSUMED, needs verification)

## Open Questions

- [ ] [question still to be answered]
- [ ] [another pending question]

## Skip History (if applicable)

- Skipped at: Phase [N] - [Phase Name]
- Summary style chosen: [Minimal / Inferred / Critical first]
- Phases not covered: [list]

## Resume Instructions

To continue this interview:

1. Read this file to restore context
2. Resume at Phase [N]: [Phase Name]
3. Next question to ask: [specific question]
4. Topics already covered: [list from Questions Asked table]
```

**When resuming a session:**

1. Read the interview file if user mentions "continue interview" or provides a file path
2. Check the "Current Phase" and "Progress Tracker"
3. Review "Questions Asked" table to avoid re-asking
4. Resume from the exact point (don't re-ask answered questions)
5. Reference previous answers: "Earlier you mentioned [X], building on that..."

Ask user: "Want me to save this interview progress to a file?"
