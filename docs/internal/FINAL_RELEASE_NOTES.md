# MiroFish Arabic Edition — Final Release Notes

This package is the finalized Arabic-first fork produced from the upstream repository and the earlier Arabic localization passes.

## What is now finished

### Arabic-first product behavior
- Default UI locale is now **Arabic** unless the user explicitly switches language or passes `?lang=en` / `?lang=zh`.
- Backend locale fallback is now **Arabic**, so report generation and interaction endpoints default to Arabic when no locale is supplied.
- The GitHub landing page (`README.md`) is now Arabic-first.
- Chinese documentation was preserved in `README-ZH.md`.

### Structured report intelligence
- Section research bundles now emit stable **tool run IDs** and **evidence IDs**.
- Claims now carry structured:
  - `claimId`
  - `supportingRefs`
  - `supportingRefIds`
  - `supportRefCount`
  - `supportLevel`
- Report UI state now rolls up:
  - total evidence items
  - linked evidence references
  - supported-claim totals
  - supported-claim rate

### Step 4 report UX
- Step 4 now shows richer claim-support chips based on structured references instead of only prose-derived matches.
- Section research chips now include total evidence-item counts.
- Report-level evidence chips now include:
  - evidence items
  - linked refs
  - supported claims

### Repo and developer polish
- Root docs were reorganized for an Arabic-first fork:
  - `README.md` → Arabic-first
  - `README-EN.md` → English
  - `README-ZH.md` → preserved Chinese doc
- Root operational/config files were cleaned up from Chinese-first comments into neutral developer-facing English:
  - `.env.example`
  - `Dockerfile`
  - `docker-compose.yml`
  - `package.json`
  - `backend/pyproject.toml`
  - `backend/requirements.txt`
  - `backend/run.py`
  - `backend/app/config.py`
- Safer backend default:
  - `FLASK_DEBUG` now defaults to `False`

## Validation completed
- `python -m py_compile` passed for the modified backend modules and tests
- `PYTHONPATH=backend python -m unittest backend.tests.test_report_ui -v` passed with **13 tests**
- `node --check` passed for:
  - `frontend/src/i18n/index.js`
  - extracted `<script setup>` from `frontend/src/components/Step4Report.vue`

## Remaining optional work after this final package
None of the following are blockers for release, but they are the best next upgrades if you keep evolving the fork:
1. run a full frontend production build in a network-enabled environment
2. run the full Flask + Vite stack end-to-end with real LLM/Zep credentials
3. replace the remaining prose heuristics in the generation loop with author-native structured IDs emitted at generation time
4. add production deployment mode instead of the current development-style Docker entrypoint

## Recommended branch name
`arabic-final`
