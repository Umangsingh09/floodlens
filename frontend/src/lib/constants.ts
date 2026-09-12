export const API_BASE_URL: string =
  import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export const FLOODLENS_STUDY_REGION_LABEL = 'FloodLens study region';

export const FLOODLENS_STUDY_REGION_BOUNDS: [[number, number], [number, number]] = [
  [23.6, 82.8],
  [28.0, 88.6],
];

/**
 * Initial viewport centered on the Bihar–southern Nepal flood corridor.
 * This is a project study region, not an official administrative boundary.
 */
export const DEFAULT_MAP_CENTER: [number, number] = [26.25, 85.7];
export const DEFAULT_MAP_ZOOM = 7;
