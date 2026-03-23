# Arabic Improvement Pass — Progress Report V2

## What changed in this pass

### 1) Backend locale pipeline is now much stronger

The backend can now carry request locale more consistently into report generation and simulation preparation.

Updated files:
- `backend/app/utils/locale.py`
- `backend/app/api/report.py`
- `backend/app/api/simulation.py`
- `backend/app/services/simulation_manager.py`
- `backend/app/services/oasis_profile_generator.py`
- `backend/app/services/simulation_config_generator.py`
- `backend/app/services/report_agent.py`

Key improvements:
- Added a shared locale helper module.
- `Accept-Language` is now used in more report and simulation flows.
- Interview prompts are no longer hardcoded to Chinese only.
- Profile generation and simulation config generation now receive locale-aware language hints.
- Report generation and chat now explicitly carry locale.
- Report agent tool calls now record **structured results** in addition to raw text.
- The section-writing prompt no longer contains a Chinese-only language rule; it now targets the requested report language.

### 2) Step 4 became less dependent on Chinese prose parsing

Updated file:
- `frontend/src/components/Step4Report.vue`

Key improvements:
- Step 4 can now read `result_structured` from backend tool logs when available.
- Structured payload support was added for:
  - `insight_forge`
  - `panorama_search`
  - `quick_search`
  - `interview_agents`
- Legacy regex parsing remains as fallback, but the UI is no longer blocked by Chinese-only text in the same way as before.
- The interview parser was expanded to tolerate Chinese, English, and Arabic section variants more reliably.
- Additional visible strings in the report tool displays were localized more thoroughly, including count formatting and interview headers.

### 3) Step 3 simulation view is now substantially localized

Updated file:
- `frontend/src/components/Step3Simulation.vue`

Key improvements:
- Added locale-aware labels for the platform cards, counters, report button, waiting states, and monitor header.
- Localized visible action labels and tooltip labels.
- Localized action badges used in the timeline.
- Localized high-visibility activity text inside timeline cards.
- Localized runtime log messages emitted by the screen itself.
- Switched action timestamp formatting to use the current UI locale instead of always using `en-US`.

### 4) Arabic documentation now exists in the repo

Added file:
- `README-AR.md`

Updated files:
- `README.md`
- `README-EN.md`

Key improvements:
- Added an Arabic README covering overview, workflow, setup, Docker, and Arabic-branch notes.
- Added Arabic language links in the existing Chinese and English READMEs.

## Validation run in this pass

### Python validation

Successfully compiled:
- `backend/app/utils/locale.py`
- `backend/app/api/report.py`
- `backend/app/api/simulation.py`
- `backend/app/services/simulation_manager.py`
- `backend/app/services/oasis_profile_generator.py`
- `backend/app/services/simulation_config_generator.py`
- `backend/app/services/report_agent.py`

Command used:

```bash
python -m py_compile \
  backend/app/utils/locale.py \
  backend/app/api/report.py \
  backend/app/api/simulation.py \
  backend/app/services/simulation_manager.py \
  backend/app/services/oasis_profile_generator.py \
  backend/app/services/simulation_config_generator.py \
  backend/app/services/report_agent.py
```

### Frontend syntax validation

Extracted and checked the `<script setup>` blocks of:
- `frontend/src/components/Step3Simulation.vue`
- `frontend/src/components/Step4Report.vue`

Command used:

```bash
node --check /tmp/step3_check.js
node --check /tmp/step4_check.js
```

Both passed.

## Remaining highest-priority roadmap

### Priority A — Finish backend-native Arabic output

Still needed:
- make `zep_tools.py` return locale-aware user-facing text where plain-text fallbacks are still used,
- ensure all report/tool/chat outputs are naturally Arabic rather than only tolerated by the frontend parser,
- localize additional report API error/status messages beyond the paths already covered.

### Priority B — Remove fragile prose contracts entirely

Still needed:
- replace remaining prose-dependent parsing in report views with structured JSON contracts,
- align report sections, tool logs, and interaction flows around stable schemas.

This is the most important long-term architectural improvement.

### Priority C — Complete Arabic coverage across the remaining app

Still needed:
- audit all remaining visible Chinese/English strings in the app,
- localize any secondary report and interaction surfaces,
- improve RTL-specific spacing/alignment on small screens.

### Priority D — Production hardening

Still needed:
- add automated tests for locale propagation,
- add frontend snapshot or component checks for Arabic + RTL,
- review production defaults, security settings, and deployment readiness.

## Recommended next implementation pass

If continuing from this branch, the most valuable next pass is:

1. make backend tool outputs fully locale-aware,
2. convert more report UI parsing to structured payloads only,
3. finish a full visual RTL polish pass,
4. then add tests so Arabic support stops regressing.
