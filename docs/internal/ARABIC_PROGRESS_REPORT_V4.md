# Arabic Transformation Progress Report — V4

## What changed in this pass

This round focused on the biggest remaining localization bottleneck in **Step 4**: the report timeline still depended too heavily on raw backend shapes and prose parsing.

### 1) Added a backend-side Step 4 UI contract
New file:
- `backend/app/services/report_ui.py`

What it does:
- normalizes `insight_forge`, `panorama_search`, `quick_search`, and `interview_agents` results into a **frontend-stable UI payload**;
- extracts platform-separated interview answers (`twitter` / `reddit`) for richer display;
- derives LLM response metadata such as extracted final-answer preview;
- backfills older log entries at read-time, so previously generated logs also benefit when possible.

### 2) Upgraded the report agent log payloads
Updated:
- `backend/app/services/report_agent.py`

What changed:
- `tool_result` logs can now include `ui_payload`;
- `llm_response` logs can now include `ui_payload` with final-answer preview;
- tool execution now returns both `structured_result` and a normalized UI payload;
- `ReportManager.get_agent_log()` now normalizes log entries before sending them to the frontend.

### 3) Made the report log API locale-aware during normalization
Updated:
- `backend/app/api/report.py`

What changed:
- `Accept-Language` is now passed into the agent-log endpoints, so the normalization layer can respect the active UI locale.

### 4) Improved Step 4 Arabic UX directly in the frontend
Updated:
- `frontend/src/components/Step4Report.vue`

What changed:
- Step 4 now prefers `details.ui_payload` over brittle raw/prose fallbacks;
- interview cards can consume split platform answers when available;
- a large set of remaining hard-coded UI strings are now localized:
  - iteration / tools / final badges,
  - show/hide params,
  - raw output / structured view,
  - show/hide response,
  - waiting state,
  - console header,
  - final answer hint,
  - report completion banner;
- time display now follows the active locale instead of forcing `en-US`;
- added mixed-direction text support with `unicode-bidi: plaintext` for Arabic + English content in the same blocks;
- added a final-answer preview card in the timeline when the backend provides one.

## Validation performed

### Backend
- `python -m py_compile backend/app/services/report_ui.py`
- `python -m py_compile backend/app/services/report_agent.py`
- `python -m py_compile backend/app/api/report.py`

### Frontend
- extracted the `<script setup>` block from `Step4Report.vue`
- `node --check` passed on the extracted script

## What is better now

The Step 4 report timeline is now substantially less dependent on raw backend object shapes and prose parsing. The strongest improvement is for interview results and LLM responses:
- interview outputs can now be rendered with richer per-platform structure,
- final-answer previews are exposed directly from the backend log contract,
- old logs can be upgraded on read without regenerating the report.

## What still remains

### Highest-value next step
Move report **section generation metadata** into a dedicated structured contract as well, not just tool/log payloads.

That would mean:
- explicit section summaries/previews,
- explicit tool evidence references per section,
- less dependence on raw markdown parsing in the report timeline.

### Other remaining work
- some large internal prompt templates in `report_agent.py` are still authored in Chinese even though output language control is stronger now;
- console-log text itself is still not fully locale-normalized;
- I did not run a full Vite production build or a live Flask app boot in this sandbox.

## Recommended next pass

1. add structured section metadata files alongside `section_XX.md`;
2. make Step 4 consume that section metadata directly;
3. convert the remaining Chinese-authored prompt scaffolding in `report_agent.py` to neutral English instructions with locale-driven output;
4. add deployment hardening and a production Docker path.
