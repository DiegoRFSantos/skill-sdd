---
id: TESTS-FEAT-CCG
type: test-catalog
feature: catalog-coverage-gap
spec_ref: SPEC-FEAT-CCG
design_ref: DESIGN-FEAT-CCG
created_at: 2026-08-19
updated_at: 2026-08-19
author: Test
status: draft
---

## 1. Coverage Summary

Fixture where AC-02 has neither a test case nor a Deliberate Gaps entry, to
exercise the catalog_coverage_prompt review-severity nudge.

## 2. Test Cases

| TC | Covers | Level | Scenario | Status |
|---|---|---|---|---|
| TC-01 | AC-01, EC-01 | unit | widget created with a valid, non-whitespace name is accepted | `[ ]` |

## 3. Deliberate Gaps

| Spec id | Why no TC row | Recorded by |
|---|---|---|
