# Ramjet Stock Tracking — Orchestration

**Last Updated:** February 11, 2026
**Current Phase:** Phase 1 is next

---

## Phase Progress

| Phase | Name | Status | Agent Session | Date |
|-------|------|--------|---------------|------|
| 1 | Database Model & Product CRUD | NOT STARTED | — | — |
| 2 | QR Code Generation & Label Printing | NOT STARTED | — | — |
| 3 | Stock-In Scanning (Production → Warehouse) | NOT STARTED | — | — |
| 4 | Stock-Out Scanning & Partial Boxes | NOT STARTED | — | — |
| 5 | Stock Dashboard, Search & Thresholds | NOT STARTED | — | — |
| 6 | Stocktake Verification | NOT STARTED | — | — |
| 7 | Raw Materials Inventory | NOT STARTED | — | — |
| 8 | Reports & Data Export | NOT STARTED | — | — |

**Status values:** `NOT STARTED` → `IN PROGRESS` → `COMPLETE` (or `BLOCKED`)

---

## Phase Dependencies

```
Phase 1 (DB & Product CRUD) ──► Phase 2 (QR Labels) ──► Phase 3 (Stock In) ──► Phase 4 (Stock Out)
       │                                                         │
       │                                                         ▼
       │                                                  Phase 5 (Dashboard)──► Phase 6 (Stocktake)
       │                                                                                │
       └──► Phase 7 (Raw Materials)                                                     │
                    │                                                                    │
                    └────────────────────────────► Phase 8 (Reports) ◄───────────────────┘
```

Phase 7 (Raw Materials) can be built in parallel with Phases 3-6 since it has no dependency beyond Phase 1.

---

## Key Decisions Log

| Date | Phase | Decision | Rationale |
|------|-------|----------|-----------|
| — | — | — | — |

---

## Known Issues

| Date | Phase | Issue | Status | Resolution |
|------|-------|-------|--------|------------|
| — | — | — | — | — |

---

## Files Created / Modified

### Phase 1
_(not started)_

### Phase 2
_(not started)_

### Phase 3
_(not started)_

### Phase 4
_(not started)_

### Phase 5
_(not started)_

### Phase 6
_(not started)_

### Phase 7
_(not started)_

### Phase 8
_(not started)_

---

## Environment / Config Changes

| Phase | Change | Notes |
|-------|--------|-------|
| — | — | — |

---

## How to Update This Document

At the **end of every agent session**:

1. Update the Phase Progress table (status + date)
2. Log any key decisions in the Decisions Log
3. Log any known issues
4. Add files created/modified under the relevant phase
5. Note any new env vars or dependency changes
6. Update "Last Updated" date and "Current Phase" at the top
