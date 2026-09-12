"""Real Earth Engine probe for the future-flood training sample contract.

Runs `build_real_training_sample` against the DFO 4507 (Aug 2017) historical
flood window with a small ROI and prints the full sampling diagnostics:
VV/VH ranges, label classes, spatial alignment, and causal validity. This
hits live Earth Engine — it is a diagnostic script, not a unit test.
"""

import json
from dataclasses import asdict

import ee

from ai.config import get_settings
from ai.preprocessing.real_gee_sampling import GridSpec, build_real_training_sample

settings = get_settings()
ee.Initialize(project=settings.earthengine_project)

aoi_geometry = json.loads(settings.aoi_geojson)
sample_region = ee.Geometry.BBox(85.77, 26.18, 85.81, 26.22)

feature_grid, label_arr, extra = build_real_training_sample(
    aoi_geometry,
    "2017-08-21T00:00:00",
    settings=settings,
    sample_region=sample_region,
    grid_spec=GridSpec(),
    min_scene_count=3,
    max_lookback_days=30,
)

diagnostics = extra["diagnostics"]
print(json.dumps(asdict(diagnostics), indent=2, default=str))

print("\n--- Checklist ---")
print("Both label classes present (0 and 1):", set(diagnostics.label_unique_values) == {0, 1})
print("Feature/label spatial alignment confirmed:", diagnostics.spatial_alignment_confirmed)
print("Feature dims == label dims:", diagnostics.feature_dimensions == diagnostics.label_dimensions)
print("NaN count:", diagnostics.nan_count, "| Inf count:", diagnostics.inf_count)
print("Observation timestamp:", diagnostics.observation_timestamp)
print("Target timestamp (obs + 7d):", diagnostics.target_timestamp)
