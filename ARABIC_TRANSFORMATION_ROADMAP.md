# Arabic transformation roadmap for MiroFish

## What this starter branch already changes

This branch establishes the frontend foundations for an Arabic edition without adding a new i18n dependency. It includes:

- a lightweight locale system in `frontend/src/i18n`
- locale persistence in local storage
- document `lang` and `dir` switching for RTL support
- a shared language switcher component
- a shared app shell header for the main workflow views
- `Accept-Language` propagation from the frontend API client
- localized shell and landing experience for:
  - `frontend/src/views/Home.vue`
  - `frontend/src/components/HistoryDatabase.vue`
  - `frontend/src/components/GraphPanel.vue`
  - `frontend/src/components/Step1GraphBuild.vue`
  - `frontend/src/views/MainView.vue`
  - `frontend/src/views/SimulationView.vue`
  - `frontend/src/views/SimulationRunView.vue`
  - `frontend/src/views/ReportView.vue`
  - `frontend/src/views/InteractionView.vue`

This is intentionally a **starter migration**, not a complete Arabic release. The deep workbench steps and the backend generation pipeline still need a dedicated localization pass.

## Audit snapshot of the original repository

The original repository was heavily Chinese-first.

### Frontend
- 27 text files
- 21 files containing Chinese
- 1,316 lines containing Chinese

Highest-priority frontend files by Chinese density:
1. `frontend/src/components/Step4Report.vue` — 227 lines
2. `frontend/src/components/Step2EnvSetup.vue` — 210 lines
3. `frontend/src/views/Process.vue` — 191 lines
4. `frontend/src/components/HistoryDatabase.vue` — 144 lines
5. `frontend/src/components/GraphPanel.vue` — 91 lines
6. `frontend/src/components/Step5Interaction.vue` — 90 lines
7. `frontend/src/views/Home.vue` — 78 lines
8. `frontend/src/components/Step3Simulation.vue` — 74 lines

### Backend
- 37 text files
- 36 files containing Chinese
- 4,380 lines containing Chinese

Highest-priority backend files by Chinese density:
1. `backend/app/services/report_agent.py` — 670 lines
2. `backend/app/api/simulation.py` — 487 lines
3. `backend/app/services/zep_tools.py` — 461 lines
4. `backend/app/services/simulation_runner.py` — 348 lines
5. `backend/app/services/oasis_profile_generator.py` — 315 lines
6. `backend/scripts/run_parallel_simulation.py` — 306 lines
7. `backend/app/services/simulation_config_generator.py` — 255 lines
8. `backend/app/services/zep_graph_memory_updater.py` — 159 lines

The full machine-readable audit is in `ARABIC_LOCALIZATION_AUDIT.json`.

## Main blockers to a real Arabic edition

### 1) `Step4Report.vue` is coupled to Chinese report text
This file does not only render labels. It parses generated report content with Chinese regex anchors such as:
- `分析问题`
- `预测场景`
- `相关预测事实`
- `涉及实体`
- `### 【关键事实】`

That means a simple text translation is not enough. Arabic output will break the current parser unless the report contract changes.

### 2) The backend still generates Chinese-first prompts and status text
The following files are the critical backend localization surface:
- `backend/app/api/simulation.py`
- `backend/app/api/report.py`
- `backend/app/services/report_agent.py`
- `backend/app/services/simulation_config_generator.py`
- `backend/app/services/oasis_profile_generator.py`
- `backend/app/services/zep_tools.py`

Right now, those files contain hard-coded Chinese prompt fragments, progress messages, field names, and assumptions that leak into the generated outputs.

### 3) There is a stale or duplicate frontend view
`frontend/src/views/Process.vue` appears to be legacy code. The router maps the `Process` route to `MainView.vue`, not to `Process.vue`. This should be cleaned up before doing a wider localization sweep, otherwise effort will be wasted on dead UI.

### 4) The current UI still duplicates shell logic across multiple views
This starter branch partly fixes that by introducing `AppShellHeader.vue`, but deeper workflow components still duplicate labels, statuses, and action text.

### 5) RTL support is started, not finished
Global direction switching is in place, but the following still need visual QA:
- icon direction and arrow semantics
- flex row ordering inside dense panels
- chart and graph detail layouts
- long Arabic labels in badges and narrow controls
- modal and workbench spacing under RTL

## Recommended implementation phases

### Phase 0 — foundation
Status: **done in this starter branch**

Delivered:
- locale store
- language switcher
- shared workflow header
- RTL document direction
- Arabic-ready landing page and shell
- `Accept-Language` header propagation

### Phase 1 — finish the static frontend migration
Target files:
- `frontend/src/components/Step2EnvSetup.vue`
- `frontend/src/components/Step3Simulation.vue`
- `frontend/src/components/Step4Report.vue` (static labels only, before parser refactor)
- `frontend/src/components/Step5Interaction.vue`

Goal:
- move every visible string into locale messages
- remove hard-coded Chinese status badges, placeholders, button labels, tool descriptions, and empty states
- keep all current behavior unchanged

Deliverable:
- a fully localized frontend shell where Arabic, English, and Chinese can all render the static UI consistently

### Phase 2 — replace free-text parsing with structured report data
This is the most important architecture change.

Current problem:
- frontend report rendering depends on parsing generated prose

Recommended fix:
- make the backend return structured JSON sections for the report, for example:
  - summary
  - scenario
  - stats
  - facts
  - entities
  - relations
  - interviews
  - tool outputs
  - progress state

Target files:
- `backend/app/api/report.py`
- `backend/app/services/report_agent.py`
- `frontend/src/components/Step4Report.vue`
- `frontend/src/components/Step5Interaction.vue`

Result:
- Arabic, English, and Chinese all become first-class output languages
- frontend becomes less brittle
- test coverage becomes possible

### Phase 3 — backend locale awareness
Introduce a small locale service in the backend.

Recommended capabilities:
- parse `Accept-Language`
- store `request_locale`
- expose locale helpers to prompt builders and serializers
- centralize translated progress/status messages
- choose output language explicitly in every LLM prompt

Suggested new files:
- `backend/app/utils/locale.py`
- `backend/app/prompts/` for language-specific templates

Suggested refactor targets:
- `simulation.py`
- `report.py`
- `report_agent.py`
- `simulation_config_generator.py`
- `oasis_profile_generator.py`
- `zep_tools.py`

### Phase 4 — Arabic UX and RTL QA
Target:
- make Arabic feel native, not merely translated

Work items:
- check all workbench layouts in RTL
- widen or reflow narrow button clusters
- verify graph detail panels with long Arabic text
- verify form placeholders, monospace labels, and mixed Arabic/Latin strings
- choose final Arabic-friendly font stack and fallback behavior

### Phase 5 — docs and release packaging
Deliverables:
- `README-AR.md`
- Arabic screenshots or GIFs
- Docker and `.env` setup instructions in Arabic
- release notes explaining Arabic support
- contributor notes describing how to add more locales safely

### Phase 6 — hardening and product improvements
These are not strictly localization tasks, but they will make the Arabic branch much better.

#### Product and architecture
- remove or archive unused `Process.vue`
- centralize repeated workflow status logic
- define stable response schemas for graph, simulation, and report payloads
- consider moving the frontend toward TypeScript for safer large refactors
- replace repeated polling logic with a unified polling or streaming layer

#### Security and deployment
- turn off development defaults for production images
- review Flask debug exposure and traceback returns
- validate upload file types consistently between frontend and backend
- add request limits and safer error handling around long-running report generation

#### Quality
- add locale snapshot tests for UI strings
- add smoke tests for the full flow: Home → Graph → Simulation → Report → Interaction
- add contract tests for report JSON payloads
- add prompt evaluation checks to confirm Arabic output stays Arabic

## Suggested next PR sequence

### PR 1
Finish `Step2EnvSetup.vue` and `Step3Simulation.vue` static localization.

### PR 2
Refactor `Step4Report.vue` to stop depending on Chinese regex parsing.

### PR 3
Add backend locale helpers and wire `Accept-Language` through `report_agent.py` and `simulation.py`.

### PR 4
Localize `Step5Interaction.vue` and interview/report chat surfaces.

### PR 5
Add `README-AR.md` and Arabic screenshots.

### PR 6
Delete or archive `frontend/src/views/Process.vue`, then clean up route-related duplication.

## Practical recommendation

Do **not** translate backend prompts and report prose line-by-line on top of the current parser.  
The correct order is:

1. finish the static frontend pass
2. switch report rendering to structured data
3. make backend prompts locale-aware
4. then ship Arabic as a first-class output language

That order will save rework and keep the Arabic branch maintainable.
