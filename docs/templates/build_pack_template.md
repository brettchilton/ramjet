# Build Pack Template

## Purpose

This template defines how to create a **Build Pack** — a structured set of planning documents that an agent (or developer) can use to implement a feature or initiative. A Build Pack lives under `docs/plans/<initiative_name>/` and consists of:

1. **MASTER_PLAN.md** — The what and why: executive summary, architecture, scope
2. **ORCHESTRATION.md** — The how and when: phase sequencing, handoffs, testing gates
3. **phases/PHASE_N_*.md** — Implementation specs for each phase
4. **PROMPTS.md** — Ready-to-use agent prompts for each phase (optional but recommended)
5. **handovers/** — Phase completion handover documents (created by agents during implementation)

**Reference implementations**:
- (No reference implementations yet — the first Build Pack created will serve as the canonical example)

---

## Agent Instructions

When you receive this template, you are being asked to **create a new Build Pack** for an initiative. Follow these steps:

1. **Read the project context** — Start with `docs/project-overview.md` and `docs/conventions.md`
2. **Use the reference** — Study `docs/plans/report_4_overhaul/` to understand structure and depth
3. **Create the folder** — `docs/plans/<initiative_name>/` with `phases/` subfolder
4. **Fill in the sections below** — Replace all `{{placeholders}}` with concrete content
5. **Tailor depth** — Some initiatives need less detail (e.g. config-only changes); others need full schemas and code sketches. Match the reference level to complexity.

---

## Folder Structure

```
docs/plans/<initiative_name>/
├── MASTER_PLAN.md
├── ORCHESTRATION.md
├── PROMPTS.md              # Agent prompts (create if using agent-driven execution)
├── phases/
│   ├── PHASE_1_<FOCUS>.md
│   ├── PHASE_2_<FOCUS>.md
│   └── ...
└── handovers/              # Created by agents; handover-phase-N.md after each phase
    ├── handover-phase-1.md
    ├── handover-phase-2.md
    └── ...
```

---

## 1. MASTER_PLAN.md

Copy and fill in the following structure. Remove sections that don't apply.

```markdown
# {{Initiative Name}} - Master Plan

## 1. Executive Summary

Brief description of the initiative.

### Current State
- {{What exists today}}
- {{Pain points or constraints}}

### Target State
- {{What we're building towards}}
- {{Key outcomes}}

---

## 2. Architecture Overview

[Include an ASCII diagram or description of the flow. Example:]

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   STEP 1     │───▶│   STEP 2     │───▶│   STEP 3     │
│   ...        │    │   ...        │    │   ...        │
└──────────────┘    └──────────────┘    └──────────────┘
```

---

## 3. {{Domain-Specific Section}}

[Add sections that matter for this initiative, e.g.:]
- Data Source Mapping
- API Contracts
- User Flow
- Data Models

---

## 4. Technical Components

### 4.1 New/Modified Database Models
[If applicable — schema sketches or pseudocode]

### 4.2 New Service Layer
```
backend/app/services/
├── {{service_name}}/
│   └── ...
```

### 4.3 New API Endpoints
```
POST   /api/v1/{{resource}}/...
GET    /api/v1/{{resource}}/...
```

### 4.4 Background Tasks (if Celery)
[Task names and purposes]

---

## 5. User Flow

### 5.1 Happy Path
[Numbered steps or flowchart]

### 5.2 Fallback Paths
| Scenario | Fallback |
|----------|----------|
| {{scenario}} | {{fallback}} |

---

## 6. Privacy & Security
[If applicable — data handling, scopes, consent]

---

## 7. Success Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| {{metric}} | {{value}} | {{value}} | {{how}} |

---

## 8. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| {{risk}} | {{H/M/L}} | {{H/M/L}} | {{action}} |

---

## 9. Dependencies

### External Dependencies
- {{External service, API, credentials}}

### Internal Dependencies
- {{Existing feature, model, service}}

---

## 10. Phase Overview

| Phase | Focus | Dependencies | Deliverables |
|-------|-------|---------------|---------------|
| **Phase 1** | {{focus}} | {{deps}} | {{deliverables}} |
| **Phase 2** | {{focus}} | Phase 1 | {{deliverables}} |
| ... | | | |

See `ORCHESTRATION.md` for detailed sequencing and handoffs.

---

## 11. Out of Scope

- {{Explicitly excluded items}}

---

## 12. References

- {{Related docs}}
- {{External documentation}}

---

*Document created: {{YYYY-MM-DD}}*
*Status: Planning*
```

---

## 2. ORCHESTRATION.md

Copy and fill in. This coordinates phase execution.

```markdown
# {{Initiative Name}} - Orchestration Guide

## 1. Purpose

This document coordinates the execution of all phases, defining:
- Phase sequencing and dependencies
- Parallel work opportunities
- Handoff criteria between phases
- Testing gates
- {{Feature flag / migration strategy if applicable}}

---

## 2. Phase Dependency Graph

```
[ASCII diagram showing Phase 1 → Phase 2 → ... and any parallels]

Example:
                    ┌─────────────────────┐
                    │      PHASE 1        │
                    └─────────┬───────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
    ┌─────────────────┐ ┌─────────────────┐ ...
```

### Dependency Matrix

| Phase | Depends On | Can Start After | Blocks |
|-------|------------|-----------------|--------|
| Phase 1 | - | Immediately | Phase 2, 3 |
| Phase 2 | Phase 1 | Phase 1 complete | Phase 4 |
| ... | | | |

---

## 3. Parallel Work Opportunities

[Describe which phases or tracks can run in parallel]

---

## 4. Phase Handoff Criteria

### Phase N → Phase N+1

**Exit Criteria for Phase N:**
- [ ] {{Concrete deliverable}}
- [ ] {{Test passing}}
- [ ] ...

**Handoff Artifacts:**
- {{Model, service, endpoint, etc.}}

---

## 5. Testing Strategy

### Unit Tests (Per Phase)
| Phase | Test Focus |
|-------|-------------|
| 1 | {{focus}} |

### Integration Tests
| Test | Phases | Description |
|------|--------|-------------|
| {{name}} | {{phases}} | {{description}} |

---

## 6. Feature Flag Strategy (if applicable)

[Flags, rollout stages, A/B metrics]

---

## 7. Migration Strategy (if applicable)

[In-progress handling, data migration, rollback plan]

---

## 8. Handover Document Template

Include this section so phase prompts can reference it. Each phase produces a handover at `handovers/handover-phase-N.md`:

```markdown
# Phase N Handover: [Phase Name]

## Completion Status
- Date completed: YYYY-MM-DD
- All exit criteria met: Yes / No (list exceptions)

## What Was Built
- [List of files created/modified with brief description]

## Key Implementation Details
- [Important patterns or decisions made during implementation]
- [Anything that deviated from the phase doc and why]

## State of the Codebase
- [What works]
- [Known issues or technical debt introduced]

## For the Next Phase
- [Specific context the next phase agent needs]
- [Any prerequisites that should be verified before starting]

## Test Results
- [What was tested and outcomes]
```

---

## 9. Success Criteria (Overall)

### Must Have
- [ ] {{criterion}}

### Should Have
- [ ] {{criterion}}

---

*Document created: {{YYYY-MM-DD}}*
*Status: Planning*
```

---

## 3. Phase Document (phases/PHASE_N_*.md)

Each phase gets its own file. Use this structure.

```markdown
# Phase N: {{Phase Title}}

## 1. Overview

**Objective**: {{One sentence goal}}

**Scope**:
- {{In-scope item 1}}
- {{In-scope item 2}}

**Does NOT include**:
- {{Out-of-scope item}}

**Dependencies**: {{Prior phases}}

---

## 2. {{Technical Section 1}}

[Database schema, service code, API routes — use concrete sketches where helpful]

### 2.1 {{Subsection}}
[Code blocks, pseudocode, tables]

---

## 3. {{Technical Section 2}}

---

## 4. File Structure

```
backend/app/
├── ...
frontend/src/
├── ...
```

---

## 5. Environment Variables

[If new env vars are needed]

---

## 6. Testing Requirements

### Unit Tests
[Test descriptions or examples]

### Integration Tests
[Test descriptions]

---

## 7. Exit Criteria

- [ ] {{Deliverable}}
- [ ] {{Test passing}}
- [ ] ...

---

## 8. Handoff to Phase N+1

**Artifacts provided:**
- {{List}}

**Phase N+1 will:**
- {{How it uses these artifacts}}

---

*Document created: {{YYYY-MM-DD}}*
*Status: Planning*
```

---

## 4. PROMPTS.md (Optional)

If you want agents to implement phases (rather than humans), create `PROMPTS.md` with ready-to-use prompts. **Reference**: `docs/plans/unified-chat-engine/PROMPTS.md`

### Structure

```markdown
# {{Initiative Name}} - Agent Prompts

## Purpose

Ready-to-use prompts for each implementation phase. Copy-paste the relevant prompt to start a new agent session for that phase.

Each prompt tells the agent to:
1. Read the master plan and orchestration guide
2. Read the phase-specific document
3. Read the previous phase's handover document (if not Phase 1)
4. Implement the phase following exit criteria
5. Create a handover document when done

---

## Phase N: {{Phase Title}}

Each phase prompt is a fenced code block. **Study `docs/plans/unified-chat-engine/PROMPTS.md` for the exact format.** Each prompt should include:

| Section | Content |
|---------|---------|
| **Opening** | "You are implementing Phase N of {{Initiative}}... Do NOT enter plan mode." |
| **Context** | Numbered reading order: MASTER → ORCHESTRATION → phase doc → previous handover (Phase 2+) |
| **Reference files** | Specific paths to existing code the agent must read |
| **Task** | Key deliverables with file paths |
| **Closing** | "Create handover at handovers/handover-phase-N.md. Use ORCHESTRATION section 8." |

---

## Usage Notes

1. **Start each session fresh.** Each prompt is self-contained — the agent reads the docs, not memory.
2. **Handover documents are critical.** They're the bridge between phases. Each agent must create one.
3. **Exit criteria are the definition of done.** Don't mark complete until all boxes are checked.
4. **Read the reference files.** Point to specific files that contain patterns to follow or replace.
5. **Note parallel opportunities.** If Phase N can run alongside Phase M, say so in the prompt.
```

### Tips for Writing Phase Prompts

| Element | Why it matters |
|---------|----------------|
| **Explicit "Do NOT enter plan mode"** | Agents may default to planning; you want them to execute |
| **Numbered reading order** | Ensures context before implementation |
| **Specific reference file paths** | Agents need to see existing patterns |
| **Concrete deliverables with paths** | "Create X at path Y" beats "implement X" |
| **Handover instruction at end** | Reminds agent to bridge to next phase |

---

## 5. Handover Document — What Makes a Good One

The handover template (in ORCHESTRATION section 8) defines the structure. This section shows **what makes a handover effective** for the next phase's agent.

### Example: Effective Handover (Condensed)

```markdown
# Phase 1 Handover: Backend Chat Engine

## Completion Status
- Date completed: 2026-02-12
- All exit criteria met: Yes
```
↑ **Explicit confirmation** — next agent knows the phase is truly done.

```markdown
## What Was Built

| File | Purpose |
|------|---------|
| `backend/app/core/chat_engine/engine.py` | ChatEngine — agentic loop |
| `backend/app/core/chat_engine/streaming.py` | SSEStreamGenerator, create_sse_response() |
| ... | ... |
```
↑ **Specific paths + one-line purpose** — next agent knows exactly what exists and where.

```markdown
## Key Implementation Details

- **ChatMessage.raw_content field**: Added to preserve Anthropic SDK content blocks for
  re-sending in the agentic loop. Critical for assistant messages with tool_use blocks.
- **No deviations from phase doc**: Implementation follows PHASE_1 exactly.
```
↑ **Non-obvious decisions + deviations** — next agent won't repeat work or be surprised.

```markdown
## For the Next Phase

Phase 2 (General Mentor migration) should:

1. **Import from** `app.core.chat_engine`: ChatEngine, ToolRegistry, EngineConfig, create_sse_response
2. **Register General Mentor's 3 tools** as ToolDefinition instances
3. **Key config values** (from services/chat/agent.py): model=claude-sonnet-4-5, max_tokens=2048, max_iterations=5
```
↑ **Actionable, numbered steps** — next agent can start immediately without re-reading Phase 1.

```markdown
## Test Results
34 passed. (HistoryManager: 7, ToolRegistry: 6, ChatEngine: 6, ...)
```
↑ **Evidence of done** — confidence the phase actually works.
```

### Qualities of a Good Handover

| Quality | Bad | Good |
|---------|-----|------|
| **Completeness** | "Built the engine" | Table of files with paths and purpose |
| **Next-phase guidance** | "Phase 2 will use this" | Numbered steps: "1. Import X from Y. 2. Register Z..." |
| **Deviations** | (omitted) | "Phase doc said A but we used B because C" |
| **Known issues** | (omitted) | "None" or "Type X in file Y — deferred to Phase N" |
| **Exit criteria** | Vague | Explicit checkbox list matching phase doc |

---

## Checklist for Agent

Before considering the Build Pack complete:

- [ ] All `{{placeholders}}` replaced with real content
- [ ] Phase dependency graph matches phase documents
- [ ] Each phase has clear exit criteria and handoff artifacts
- [ ] ORCHESTRATION includes Handover Document Template (section 8)
- [ ] PROMPTS.md created if using agent-driven execution (one prompt per phase, reference files listed)
- [ ] handovers/ folder exists (empty until agents run)
- [ ] Naming follows project conventions (API routes, URL patterns, JSON field casing, etc.)
- [ ] References to existing docs/architecture are accurate
- [ ] Out of scope is explicitly stated
- [ ] Document dates and status are set

---

## Quick Reference

| Document | Key Content | Where to Study |
|----------|-------------|----------------|
| **MASTER_PLAN** | Exec summary, architecture diagram, tech components, user flow, phase table, out of scope | First Build Pack will be reference |
| **ORCHESTRATION** | Dependency graph, handoff criteria, handover template (section 8), testing, feature flags | First Build Pack will be reference |
| **PHASE_N** | Overview, technical specs, file structure, exit criteria, handoff artifacts | First Build Pack will be reference |
| **PROMPTS** | Per-phase copy-paste prompts, context reading order, reference files, handover instruction | First Build Pack will be reference |
| **Handover** | Completion status, what was built, key details, for-next-phase guidance | First Build Pack will be reference |

Reference paths will be updated once the first Build Pack is created in `docs/plans/`.
