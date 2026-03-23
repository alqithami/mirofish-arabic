# Arabic Progress Report — V11

## What improved in this pass

### 1) Claim-to-evidence JSON now exists as a first-class backend contract
I added a new structured `claimBundle` / `claimCards` layer to the report UI pipeline.

It is now emitted for:
- `llm_response` logs
- saved section metadata / section UI payloads
- report-level UI-state summaries

Each claim card can now carry:
- `claim`
- `preview`
- `supportingFacts`
- `supportingQuotes`
- `supportingCitations`
- `supportingEntities`
- `supportingRelations`
- `sourceTools`
- `factCount`
- `citationCount`
- `quoteCount`
- `evidenceCount`
- `hasEvidence`

This is the first pass where Step 4 can show **what the section claims** and **what evidence supports those claims** without relying only on raw markdown or prose parsing.

### 2) The generation loop now carries evidence context forward
Inside `ReportAgent._generate_section_react`, I added per-section structured tool-event accumulation.

That evidence context is now passed into `build_llm_response_ui_payload(...)` while the section is still being generated, so final-answer responses can be normalized against the exact tool outputs already gathered in that section.

I also persisted that evidence context into `agent_log.jsonl` under `llm_response.details.evidence_context`, which improves backward-compatible UI hydration on read.

### 3) Forced-finalization runs are now covered too
There was a real observability gap before this pass: when a section hit the forced-finalization path, the last LLM response was not being logged as a normal `llm_response` event.

I fixed that, so claim/evidence cards are still available even when the section finishes through the max-iteration fallback path.

### 4) Saved sections now persist claim metadata
`ReportManager.save_section()` now computes and stores:
- `source_bundle`
- `claim_bundle`
- a richer `ui_payload`

So saved reports can rehydrate section claims without recomputing everything from scratch.

### 5) Step 4 now renders claim-support cards in the UI
`Step4Report.vue` now shows claim-support blocks in:
- completed section views
- pre-completion section metadata views
- LLM timeline cards

I also added report-level chips for:
- total claims
- supported claims

That makes Step 4 much closer to an analyst-facing evidence review surface instead of only a markdown viewer plus logs.

## Files changed
- `backend/app/services/report_ui.py`
- `backend/app/services/report_agent.py`
- `backend/tests/test_report_ui.py`
- `frontend/src/components/Step4Report.vue`
- `ARABIC_PROGRESS_REPORT_V11.md`

## Validation completed
- `python -m py_compile` passed for:
  - `backend/app/services/report_ui.py`
  - `backend/app/services/report_agent.py`
  - `backend/app/api/report.py`
  - `backend/tests/test_report_ui.py`
- `PYTHONPATH=backend python -m unittest backend.tests.test_report_ui -v`
  - **12 tests passed**
- `node --check` passed for the extracted `<script setup>` block of:
  - `frontend/src/components/Step4Report.vue`

## Main remaining gap
The biggest remaining architectural gap is still deeper upstream structure at write-time:
- explicit section-level JSON for the final research synthesis,
- explicit claim IDs / evidence IDs,
- stable evidence references that survive re-ranking and UI filtering,
- less dependence on heuristic keyword overlap when mapping claims to evidence.

This pass materially improves the contract, but it is still a heuristic claim-evidence mapper built on top of structured tool output, not a fully author-native citation graph yet.
