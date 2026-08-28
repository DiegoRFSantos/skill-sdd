---
id: SPEC-FEAT-CUID
type: spec
feature: catalog-unknown-id
created_at: 2026-08-19
updated_at: 2026-08-19
author: Test
version: 1.0.0
status: draft
---

## 1. Context & Purpose

Minimal spec used only to exercise the catalog_ids_resolve check in isolation.

## 2. Ubiquitous Language

| Term | Definition |
|---|---|
| Widget | A named thing created by a user |

## 3. Actors

| Actor | Type (human/system) | What they need from this capability |
|---|---|---|
| User | human | Create a widget with a name |

## 4. Scope & Non-Goals

### In Scope

Creating a widget with a required name.

### Non-Goals

- Deleting a widget — not needed for this fixture

## 5. Business Rules

### BR-01: Widgets must have a name

**Statement:** Every widget must have a non-empty name.

**Rationale:** Names are how widgets are identified by users.

**Invariant:** name is non-empty whenever a widget is created.

## 6. Acceptance Criteria

### AC-01 (proves BR-01)

```gherkin
Given a user creating a widget
When a name is supplied
Then the widget is accepted
```

## 7. Edge Cases & Failure Modes

### EC-01: Empty name supplied

**Trigger:** A widget is created with an empty name.

**Expected behavior:** The widget is rejected.

**Why it matters:** Prevents unnamed, unidentifiable widgets from existing.

## 8. Success Metrics

| Metric | Baseline | Target |
|---|---|---|
| Widget creation failures | 10 per week | 1 per week |

## 9. Traceability Matrix

| BR/EC id | Covered by AC ids |
|---|---|
| BR-01 | AC-01 |
| EC-01 | AC-01 |

## 10. Open Questions

| Q-NN | Question | Status |
|---|---|---|

## 11. Change Log

| Version | Date | Change | Gate score |
|---|---|---|---|
| 1.0.0 | 2026-08-19 | Initial fixture spec | 1.0 |
