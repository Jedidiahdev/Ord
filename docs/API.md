# Ord API Reference (Phase 5)

## Orchestrator

### `Orchestrator.route(...)`
Routes a task through selected agents and returns:
- `message`
- `project_id`
- `results`
- `agent_status`
- `reflection`
- `feature_backbone`

### `Orchestrator.voice_first_briefing(command, response_payload)`
Generates a voice-ready executive briefing:
- `narration` (single narrated summary)
- `daa_visuals` (visual blocks for dashboard rendering)

## COO Agent Task API

### `{"type": "welfare_report"}`
Returns fleet health + maintenance predictions + token budget + intelligence compounding.

### `{"type": "intelligence_compound"}`
Compounds current intelligence scores across agents and records a ledger checkpoint.

### `{"type": "town_hall"}`
Returns a Sweet & Loving culture-first town hall script.

## PM Agent Extensions

### Productization Trigger
Any CEO request containing `productize` or `export` routes to one-click productization export.

Response:
- `status: exported`
- `message`
- `export_path`

## Backbone Feature Registry
Use `FeatureBackbone.summary()` to access:
- total features (50)
- priority one feature count (15)
- priority one IDs
