# Ord Internal Developer Guide

## Phase 5 Focus
This phase emphasizes:
1. Culture consistency in every response.
2. Reflection after each task.
3. Intelligence compounding tracked by COO.
4. Priority implementation of top 10–15 backbone features.
5. Production readiness through tests and CI/CD.

## Architecture Additions
- `core/feature_backbone.py`: canonical 50-feature roadmap with top-15 priorities.
- `core/resilience.py`: retry/self-healing helper.
- `core/reflection.py`: structured reflection payload.
- `integrations/voice/briefing.py`: voice-first executive briefing composer.
- `integrations/productization/exporter.py`: one-click productization scaffold.

## Testing Strategy
- Unit tests for:
  - culture + reflection wrapper behavior
  - COO intelligence compounding
  - feature backbone summary
  - voice briefing output shape
  - productization exporter file generation

## CI/CD
Workflow file: `.github/workflows/ci-cd.yml`
- Runs lint-like checks via `python -m compileall`
- Runs `pytest`
- Builds the dashboard app (`npm run build`)
