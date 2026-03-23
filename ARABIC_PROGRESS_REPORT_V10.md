# Arabic Progress Report — V10

## What improved in this pass

### 1) Sections now carry a first-class research bundle from tool outputs
I added a backend-generated `source_bundle` for each report section.
This bundle is built directly from structured `tool_result` payloads instead of being inferred from final markdown.

Each section can now carry:
- `queries`
- `toolsUsed`
- `platforms`
- `toolRuns`
- `factCards`
- `citationCards`
- `quoteCards`
- `entityCards`
- `relationCards`
- `interviewCards`
- `questionCards`
- stable `counts` and `displayCounts`

That makes the Step 4 report view much less dependent on prose heuristics.

### 2) Older and in-progress sections now backfill the research bundle automatically
I added log-based aggregation in `ReportManager` so the section research bundle is reconstructed from `agent_log.jsonl` even when:
- the report is still generating,
- the section metadata was created before this pass,
- the section has not been regenerated yet.

So current and older reports can benefit from the new structured UI without requiring a fresh full run.

### 3) Step 4 now renders research inputs separately from written output
`Step4Report.vue` now shows a dedicated **Research inputs** block per section.
It can display:
- queries used
- tools used
- evidence/count chips
- source facts
- source links
- tracked entities
- relation trails
- interview notes
- interview questions
- source quotes

This separates **what the section says** from **what evidence fed that section**, which is especially helpful in Arabic and mixed-language runs.

### 4) Step 5 now falls back to the new structured counts
`Step5Interaction.vue` now uses section `sourceBundle.counts` as a fallback when provenance counts are not present, so deep interaction has more reliable section evidence summaries.

## Files changed
- `backend/app/services/report_ui.py`
- `backend/app/services/report_agent.py`
- `backend/tests/test_report_ui.py`
- `frontend/src/components/Step4Report.vue`
- `frontend/src/components/Step5Interaction.vue`

## Validation completed
- `python -m py_compile backend/app/services/report_ui.py backend/app/services/report_agent.py`
- `python -m py_compile backend/app/api/report.py backend/tests/test_report_ui.py`
- `PYTHONPATH=backend python -m unittest backend.tests.test_report_ui -v`
  - 8 tests passed
- `node --check` on extracted `<script setup>` blocks for:
  - `frontend/src/components/Step4Report.vue`
  - `frontend/src/components/Step5Interaction.vue`

## Main remaining gap
The strongest remaining architectural target is still deeper upstream structuring at generation time:
- explicit JSON for section-level final claims,
- explicit JSON for evidence-to-claim mapping,
- less reliance on any markdown/prose extraction in the final-answer path.

This pass meaningfully reduces that dependency, but it does not remove it completely.
