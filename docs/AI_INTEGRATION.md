# AI ↔ Backend Integration Contract (Proposed)

> **Status: proposed, not final.** This document describes the shape of
> output the eventual AI pipeline is expected to produce so the
> backend/frontend can be built against a stable interface. It will be
> revised once the AI/geospatial team finalizes the model and data
> pipeline. No model exists yet — nothing below is implemented.

## Why this exists

The AI/geospatial work and the backend/frontend work are being done by
different people in parallel. This contract lets backend/frontend
scaffolding proceed without waiting for the model, and gives the AI team a
concrete target for their output format.

## Required output fields

A single flood-risk prediction "product" (e.g., one file or one API
response) must include:

| Field | Description | Notes |
|---|---|---|
| `regionId` / `aoi` | Identifier and/or geometry (bounding box or polygon) of the area of interest | Must match the finalized Bihar AOI |
| `spatialOutput` | The risk surface itself: a grid/raster (e.g., GeoTIFF) or a vector of cells/polygons, each with a risk value | Must be spatial, not a single scalar |
| `riskValue` | Per-cell/per-polygon risk probability or score | Scale (e.g., 0–1) must be documented when finalized |
| `resolution` | Spatial resolution of the output (e.g., pixel size in meters, or grid cell size) | |
| `crs` | Coordinate reference system of the spatial output | e.g., EPSG code |
| `sourcePassTimestamp` | Timestamp(s) of the satellite observation(s) the prediction is derived from | Required for lag reporting |
| `predictionTimestamp` | Timestamp the prediction was generated | |
| `predictionLag` | Derived or explicit: `predictionTimestamp − sourcePassTimestamp` | Must be surfaced to the user, not hidden |
| `predictionHorizon` | How far ahead (if at all) the prediction is forecasting, vs. nowcasting the latest pass | |
| `modelId` / `modelVersion` | Identifier of the model and version that produced the output | For traceability/reproducibility |
| `dataSources` | Which satellite product(s)/bands (and any secondary data source) were used | |

## Historical reference note (validated)

The project has verified a real historical flood-validation reference from the
Global Flood Database / Dartmouth Flood Observatory:

- Dataset: `GLOBAL_FLOOD_DB/MODIS_EVENTS/V1`
- Event: DFO 4507
- Dates: 2017-08-10 to 2017-08-26
- Primary country: India
- Reference class: remotely sensed historical reference
- Not ground truth: this is a MODIS-derived satellite reference, not a field-verified
  flood measurement.

The flood-reference mask is defined as:

```python
flood_reference = flooded == 1 AND jrc_perm_water == 0
```

This is used for historical validation only. It remains separate from model training
and is not used to create the training set for the current pipeline. The official
source is the Google Earth Engine Data Catalog entry for the Global Flood Database
v1, published by Cloud to Street / Dartmouth Flood Observatory; the dataset is
catalogued under the CC BY-NC 4.0 terms referenced by the project source materials.

## Non-requirements (explicitly out of scope for this contract)

- The internal model architecture.
- The training/evaluation methodology.
- Alert thresholding logic (will be layered on top of `riskValue` once the
  core contract is stable).

## How the backend will consume this (future)

Once the AI pipeline produces output matching this contract, the backend
will expose it via a prediction endpoint (not yet built) that the frontend
map layer will render. Until then, the frontend's map component displays a
base map only, explicitly labeled as having no risk overlay.
