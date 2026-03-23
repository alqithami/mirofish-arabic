# Arabic progress report — phase 2 improvement pass

This document summarizes what was added **after** the starter Arabic branch.

## What improved in this pass

### Frontend
- `frontend/src/components/Step2EnvSetup.vue`
  - much deeper localization coverage for setup steps, badges, round controls, configuration labels, and runtime logs
  - localized stage mapping for `generating_profiles`, `generating_config`, and `copying_scripts`
  - localized formatting for stance, gender, active-hour ranges, and profile fallbacks

- `frontend/src/components/Step5Interaction.vue`
  - localized report/chat/survey workbench shell
  - localized tool descriptions for Report Agent
  - localized placeholders, empty states, sender names, button text, and results labels
  - localized runtime logs and error strings
  - locale-aware chat-history prompt wrapping for simulated interviews
  - locale-aware time formatting for chat timestamps

- `frontend/src/components/Step4Report.vue`
  - localized shell labels for report generation, metrics, action labels, and next-step CTA
  - much wider language tolerance in the report/tool-output parser
  - parser can now recognize many Chinese, English, and Arabic heading variants instead of only Chinese anchors
  - improved final-answer extraction to recognize Arabic final-answer markers
  - localized many high-visibility tool result labels inside Insight / Panorama / Interview / Quick Search views
  - placeholder detection and question-splitting logic widened to support English and Arabic output patterns

### Backend
- `backend/app/api/simulation.py`
  - interview prompt prefix is now locale-aware based on `Accept-Language`
  - direct interviews, batch interviews, and interview-all flows can prepend an English or Arabic instruction instead of always injecting a Chinese prefix

## What is still not finished

- `frontend/src/components/Step3Simulation.vue` still needs a dedicated localization pass
- `frontend/src/views/Process.vue` should still be audited or removed if it is truly dead code
- `backend/app/services/report_agent.py` and `backend/app/services/zep_tools.py` still generate Chinese-first structures and long-form tool output
- `Step4Report.vue` is now more tolerant, but the best long-term fix is still **structured JSON output** from the backend instead of prose parsing
- a proper `README-AR.md` has not been authored yet
- RTL visual QA is still required for dense panels and graph-heavy screens

## Recommended next step from here

1. Move report/tool outputs toward structured JSON contracts in `backend/app/services/report_agent.py` and `backend/app/api/report.py`
2. Localize `Step3Simulation.vue`
3. Add a small backend locale utility and reuse it across `report.py`, `report_agent.py`, `zep_tools.py`, and `simulation_config_generator.py`
4. Add `README-AR.md` and Arabic screenshots
