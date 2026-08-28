---
id: TESTS-FEAT-CUID
type: test-catalog
feature: catalog-unknown-id
spec_ref: SPEC-FEAT-CUID
design_ref: DESIGN-FEAT-CUID
created_at: 2026-08-19
updated_at: 2026-08-19
author: Test
status: draft
---

## 1. Coverage Summary

Fixture with one test case covering a spec id that does not exist.

## 2. Test Cases

| TC | Covers | Level | Scenario | Status |
|---|---|---|---|---|
| TC-01 | AC-01, BR-01 | unit | widget created with a valid name is accepted | `[ ]` |
| TC-02 | AC-99 | unit | fixture case referencing a spec id that does not exist | `[ ]` |

## 3. Deliberate Gaps

| Spec id | Why no TC row | Recorded by |
|---|---|---|
| EC-01 | Not covered in this fixture | Test |
