import json

import numpy as np

import ee

from ai.config import get_settings
from ai.preprocessing.temporal_features import build_feature_stack
from ai.preprocessing.water_mask import compute_water_mask


settings = get_settings()
ee.Initialize(project='floodlens-508418')
geometry = ee.Geometry(json.loads(settings.aoi_geojson))
sample_region = ee.Geometry.BBox(84.5, 25.8, 85.2, 26.5)
collection = (
    ee.ImageCollection(settings.satellite_collection)
    .filterBounds(geometry)
    .filterDate('2024-09-01', '2024-09-30')
    .filter(ee.Filter.eq('instrumentMode', settings.instrument_mode))
    .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
    .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH'))
    .sort('system:time_start')
)
scene_count = int(collection.size().getInfo())
print('scene_count', scene_count)
items = collection.limit(2).toList(2)
current = ee.Image(items.get(0))
previous = ee.Image(items.get(1))

vv_t = np.asarray(current.select('VV').sampleRectangle(sample_region).get('VV').getInfo(), dtype=np.float32)
vh_t = np.asarray(current.select('VH').sampleRectangle(sample_region).get('VH').getInfo(), dtype=np.float32)
vv_t_1 = np.asarray(previous.select('VV').sampleRectangle(sample_region).get('VV').getInfo(), dtype=np.float32)
vh_t_1 = np.asarray(previous.select('VH').sampleRectangle(sample_region).get('VH').getInfo(), dtype=np.float32)
print('vv_t_shape', vv_t.shape)
print('vh_t_shape', vh_t.shape)

water_current = compute_water_mask(vv_t, threshold=settings.water_threshold_db)
water_previous = compute_water_mask(vv_t_1, threshold=settings.water_threshold_db)
water_baseline = np.zeros_like(water_current, dtype=bool)
print('water_current_unique', np.unique(water_current)[:10])


dem = ee.Image(settings.dem_dataset).select('elevation')
slope = ee.Terrain.slope(dem)
elevation = np.asarray(dem.sampleRectangle(sample_region).get('elevation').getInfo(), dtype=np.float32)
slope_arr = np.asarray(slope.sampleRectangle(sample_region).get('slope').getInfo(), dtype=np.float32)
print('elevation_shape', elevation.shape)
print('slope_shape', slope_arr.shape)
features = build_feature_stack(
    vv_t,
    vh_t,
    vv_t_1,
    vh_t_1,
    water_current=water_current.astype(np.float32),
    water_previous=water_previous.astype(np.float32),
    water_baseline=water_baseline.astype(np.float32),
    elevation=elevation,
    slope=slope_arr,
    fill_value=0.0,
)
print('core_keys', sorted(features.keys()))
print('finite_delta_vv', bool(np.isfinite(features['delta_vv']).all()))
print('finite_delta_vh', bool(np.isfinite(features['delta_vh']).all()))
print('finite_elevation', bool(np.isfinite(features['elevation']).all()))
print('finite_slope', bool(np.isfinite(features['slope']).all()))
print('dem_dataset', settings.dem_dataset)
