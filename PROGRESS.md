# FloodLens Project Progress

Last updated: 2026-09-13

## Executive summary

FloodLens is progressing from data-pipeline validation into real-data verification. The core logic for the Bihar + southern Nepal study area, Sentinel-1 preprocessing, temporal feature generation, and future-flood dataset assembly has been implemented and partially verified with real Earth Engine data. The main issue that was resolved was a zero-filled / no-overlap Sentinel-1 temporal-selection bug, which caused invalid scenes to be treated as usable historical observations.

The project is currently in validation/fix mode, not in model-training mode.

---

## Completed work

### 1. Project configuration and AOI definition
- Finalized the study-region configuration for the Bihar + southern Nepal corridor.
- Established the project-level Earth Engine target and explicit study window.
- Centralized key settings in the AI config layer.

### 2. Sentinel-1 preprocessing foundation
- Implemented explicit reference-projection logic for Sentinel-1 scenes.
- Added UTM-based regridding/alignment to a common training grid.
- Added support for polarizations and real-data alignment checks.

### 3. Temporal feature generation
- Implemented temporal feature logic for:
  - vv_t, vh_t
  - vv_t_1, vh_t_1
  - vv_t_2, vh_t_2
  - delta_vv, delta_vh
  - water_current, water_previous, water_baseline
  - DEM and slope-derived support features
- Added feature-stack construction and water-mask logic.

### 4. Real Earth Engine sampling and diagnostics
- Implemented small, leakage-safe sample construction for real GEE validation.
- Added checks to reject scenes with no real SAR signal instead of silently treating them as valid zeros.
- Added explicit temporal diagnostics for t, t-1, and t-2 scene selection.
- Added verification that temporal observations are selected only on or before the observation timestamp.

### 5. Historical-label and dataset logic
- Implemented the future-flood dataset construction contract.
- Ensured that the GFD target is treated as the 7-day future label relative to the observation timestamp.
- Ensured permanent-water masking is excluded from the positive label condition.
- Added deterministic temporal dataset splitting and quality checks.

### 6. Regression coverage for the real bug
- Added regression tests proving that zero-filled or no-overlap scenes are rejected from temporal roles.
- Verified temporal-selection uniqueness (same-day duplicates collapse correctly).
- Verified temporal selection rejects future scenes and invalid missing-signal inputs.

### 7. Verified evidence collected
- Regression test result: 8 passed in 0.20s
- The zero-filled/no-overlap rejection logic is covered by tests and passes.

---

## Known issue resolved

The main known issue was real-data contamination from zero-filled or no-overlap Sentinel-1 scenes:
- those scenes were being accepted as valid temporal observations,
- and this silently collapsed previous/baseline features toward zero.

This has been fixed by rejecting scenes with no real SAR signal before they are admitted into the temporal stack.

---

## What remains to finish

### Immediate next tasks
1. Run the full pytest suite for the project.
2. Run python -m pip check.
3. Re-run the real GEE smoke validation with a small, valid ROI that stays below Earth Engine sample-size limits.
4. Validate final raw -> preprocessed -> aggregated VV/VH ranges for all selected scenes.
5. Confirm real label classes are present in the smoke sample: specifically both 0 and 1 labels.
6. Confirm alignment and spatial dimensions between feature arrays and GFD label grid.
7. Confirm the final sample remains causally valid: all Sentinel-1 inputs are at or before the observation time while the target remains exactly t + 7 days.

### Remaining engineering gaps
- Full project-wide real-data verification still needs to be finalized.
- The pipeline is not yet considered training-ready until the real smoke validation passes completely and the full project checks are green.
- The FE remains intentionally untouched as requested.

---

## Current status

### Status: In validation / close to pipeline-ready

Confirmed:
- AOI and data contract are defined.
- Sentinel-1 preprocessing and temporal feature logic are implemented.
- Zero-filled/no-overlap temporal bug has been fixed and covered with tests.
- Focused regression checks are green.

Not yet fully confirmed:
- complete project-wide pytest run
- pip dependency validation
- final real Earth Engine smoke sample with all required value-range diagnostics
- final training-readiness decision

---

## Recommended next milestone

The next milestone should be a final validation pass focused only on real data and project checks:
- full pytest
- pip check
- small ROI GEE smoke validation with actual selected scene IDs/timestamps and VV/VH ranges
- final training-readiness verdict

Once those are all green, the pipeline can be declared training-ready for the next phase.
