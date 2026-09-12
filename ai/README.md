# FloodLens AI Workspace

This directory contains the AI and geospatial pipeline for the FloodLens project.
The initial Phase 1 implementation focuses on real Sentinel-1 GRD discovery for the
Bihar + southern Nepal flood corridor and does not yet include model training or
inference.

## Study region and AOI

The configured AOI is a project-defined study-region polygon for the Bihar +
southern Nepal flood corridor. It is not an official legal boundary file; it is a
specific operational geometry intended to capture Bihar and the adjacent Nepal
Terai reach immediately upstream of the Bihar floodplain. The default polygon is
narrower than the earlier broad bounding box and is designed to avoid overly large
areas outside the study corridor.

Approximate extents of the configured polygon: longitude 83.55°E to 88.35°E,
latitude 25.10°N to 28.90°N. This captures the core Bihar area and the relevant
southern Nepal Terai segment without using a generic oversized rectangle.

## Sentinel-1 source

FloodLens uses real public Sentinel-1 Ground Range Detected (GRD) imagery from
Google Earth Engine:

- collection: `COPERNICUS/S1_GRD`
- platform: Sentinel-1 A/B
- mode: `IW`
- polarizations: `VV`, `VH` when available
- source: Google Earth Engine public Copernicus archive

This is a discovery-only pipeline in Phase 1; it does not download a large archive
for model training. It reports matching scenes and metadata only.

## Spatial resolution and revisit characteristics

Sentinel-1 GRD typically provides a spatial resolution on the order of 10 meters
for the relevant acquisition mode, with a revisit cycle that varies by orbital geometry
and scene coverage. The system records the actual discovered scene metadata and does
not assume a fixed warning window. The prediction horizon is configured separately in
AI config and is not hardcoded from the nominal revisit period.

## Historical validation reference: DFO 4507

The project has a confirmed historical flood-validation reference from the Global
Flood Database / Dartmouth Flood Observatory dataset:

- Dataset: `GLOBAL_FLOOD_DB/MODIS_EVENTS/V1`
- Event: DFO 4507
- Image ID: `DFO_4507_From_20170810_to_20170826`
- Event dates: 2017-08-10 through 2017-08-26
- Primary country: India
- Countries metadata: China, India, Pakistan, Nepal, Bangladesh
- Reference type: remotely sensed historical reference
- Not a ground-truth label in the strict sense; it is a satellite-derived MODIS/GFD flood product.

The historical flood reference is defined explicitly as:

```python
flood_reference = flooded == 1 AND jrc_perm_water == 0
```

This intentionally excludes permanent water so the mask represents flood water,
not chronic standing water. The Earth Engine dataset is a 250-meter MODIS-based
reference and should be used for historical validation only, not as the final
training target for the model pipeline.

The official public dataset source is the Google Earth Engine Data Catalog entry for
`GLOBAL_FLOOD_DB/MODIS_EVENTS/V1`, published by Cloud to Street / Dartmouth Flood
Observatory. The public source material cites the Global Flood Database and its
associated research; the dataset licensing should be referenced as CC BY-NC 4.0 when
used in project documentation or downstream research artifacts.

## Discovery workflow

The discovery command is available from the repository root:

```bash
python -m ai.preprocessing.sentinel1 --discover
```

Optional overrides are supported for date range and GEE project:

```bash
python -m ai.preprocessing.sentinel1 --discover --start-date 2017-01-01 --end-date 2018-12-31 --project-id floodlens-508418
```

## Authentication and configuration

The Google Earth Engine project ID is configurable via environment variables or the
project `.env` file. Supported keys include:

- `EARTH_ENGINE_PROJECT=floodlens-508418`
- `EARTHENGINE_PROJECT=floodlens-508418`
- `SATELLITE_COLLECTION=COPERNICUS/S1_GRD`
- `SENTINEL1_INSTRUMENT_MODE=IW`
- `SENTINEL1_POLARIZATIONS=VV,VH`
- `START_DATE=2016-01-01`
- `END_DATE=2024-12-31`

Authentication steps:

```bash
python -m pip install earthengine-api
earthengine authenticate
```

Then re-run discovery. Credentials are never committed or hardcoded into source files.

## Real data vs. tests

- Real data: Google Earth Engine Sentinel-1 GRD scenes
- Test data: small synthetic fixtures and mocked metadata used only in unit tests
- No synthetic satellite scenes are used for discovery or pipeline execution

## Future flood-risk dataset semantics

The next dataset stage is a future-flood prediction setup, not a current-water classification.
The learning target is defined as:

- observation window: t-2, t-1, t
- feature set X(t): Sentinel-1 temporal features derived from the observation window only
- target Y(t+7): flood-reference occurrence 7 days in the future
- prediction horizon: 7 days, configured in the AI settings

The observation timestamp is the source of the input features. The target timestamp is always
exactly 7 days later and is used only to align the future flood reference. No features from after
that target timestamp may appear in X(t).

This is intentionally distinct from the real-time water detection problem. The feature stack uses
VV, VH, previous VV/VH, delta VV, delta VH, water persistence/change/trend, and DEM-derived
slope/elevation when available. These are all generated from the 10-meter Sentinel-1 grid and
aligned to the target reference grid before training set construction.

The historical train/validation reference uses the GFD flood mask with the explicit rule:

```python
flood_reference = flooded == 1 AND jrc_perm_water == 0
```

This is not ground truth. It is a 250-meter MODIS-derived historically validated reference for
flood occurrence. It can support target generation for temporal learning, but it must be treated
as a coarser, proxy label than Sentinel-1 imagery.

## Common grid and leakage prevention

To avoid spatial leakage and resolution mismatches, the project uses a documented common training
grid. Sentinel-1 features are aggregated or resampled to a deterministic grid that matches the
reference label grid before training data are assembled. The label and feature arrays must share
one CRS and grid definition, and the reference cell size is preserved as 250 m to avoid pretending
that the MODIS flood mask is 10 m ground truth.

The dataset builder enforces:

- X(t) uses only observations from the observation window and earlier
- Y(t+7) is computed from the future flood reference at the target time
- temporal train/validation/test splits are chronological and not random pixel splits
- feature and label shapes and CRS/grid metadata are checked before training
- NaN/Inf values, invalid label classes, and permanent-water exclusions are validated

## Current phase status

This implementation provides the real discovery layer, historical flood-reference semantics,
and the future-flood dataset builder for the Bihar + southern Nepal corridor. Model training,
raster export, and inference remain future phases, and the dataset remains intentionally untrained
until leakage-safe feature/label alignment is verified.
