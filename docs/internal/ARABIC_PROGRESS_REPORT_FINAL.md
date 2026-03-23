# Arabic Finalization Report

This final pass focused on turning the Arabic fork from an advanced prototype into a release-ready handoff.

## Code completed in this pass

### 1) Arabic-first defaults
- Frontend default locale now resolves to Arabic unless the user already saved a preference or explicitly passes `?lang=...`
- Backend default locale now falls back to Arabic
- Root GitHub landing page is now Arabic-first

### 2) Structured evidence references
- Added stable `runId` values for tool runs
- Added stable `evidenceId` values for fact/citation/quote/entity/relation/interview/question cards
- Added `evidenceIndex` to section research bundles
- Added structured claim support fields:
  - `claimId`
  - `supportingRefs`
  - `supportingRefIds`
  - `supportRefCount`
  - `supportLevel`

### 3) Report rollups
- Report-level UI-state now rolls up:
  - `evidenceItems`
  - `evidenceRefs`
  - `supportedClaimRate`
- Added fallback aggregation so older saved bundles without `evidenceIndex` still contribute to rollups

### 4) Step 4 UX polish
- Claim chips now reflect support-reference counts and support level
- Section research chips now include total evidence-item counts
- Report overview chips now include evidence items and linked refs

### 5) Repo polish
- `README.md` is now Arabic-first
- Chinese docs preserved in `README-ZH.md`
- Developer-facing root config/docs files were cleaned up from Chinese-first comments
- Backend debug now defaults to `False`

## Validation completed
- `python -m py_compile` passed for modified backend modules and tests
- `PYTHONPATH=backend python -m unittest backend.tests.test_report_ui -v` passed with 13 tests
- `node --check` passed for:
  - `frontend/src/i18n/index.js`
  - extracted `<script setup>` from `frontend/src/components/Step4Report.vue`

## Not run in this sandbox
- Full Vite production build
- Live Flask/Vite end-to-end session with real credentials
