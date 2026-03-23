# Post-release roadmap for the Arabic fork

## P0 — Release hardening
- Run real end-to-end simulation/report generation with Arabic prompts
- Build frontend in production mode
- Validate upload, simulation, report, and chat flows against a real backend
- Smoke test locale switching among Arabic, English, and Chinese

## P1 — Deployment hardening
- Replace dev-mode Docker startup with a production entrypoint
- Serve the built frontend as static assets or behind a reverse proxy
- Add environment-specific logging and secrets handling
- Add health checks and startup validation for required API keys

## P2 — Report pipeline quality
- Emit author-native evidence IDs directly from tool/generation steps
- Reduce the remaining keyword-overlap heuristics in claim matching
- Add section-level confidence summaries and evidence density indicators
- Add regression fixtures for Arabic reports with mixed-language source material

## P3 — Product polish
- Add an onboarding preset for Arabic demo scenarios
- Add Arabic screenshots/video references in the docs
- Add a localization QA checklist for every new UI component
- Add optional locale-aware typography and spacing refinements for RTL layouts

## P4 — Developer ergonomics
- Add CI for Python unit tests and frontend syntax/build checks
- Add snapshot fixtures for report UI-state payloads
- Add typed schemas for section/source/claim payloads
- Document the report data contract for contributors
