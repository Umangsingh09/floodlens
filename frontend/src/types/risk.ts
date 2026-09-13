import type { RegionBounds } from './region';

export interface RiskSummary {
  min: number;
  max: number;
  mean: number;
}

export interface RiskAlert {
  level: 'LOW' | 'MODERATE' | 'HIGH' | 'VERY_HIGH' | string;
  threshold: number;
}

/** Real, live regional weather/hydrology context — averaged over the observation area, not a
 *  per-cell value (the source data is coarser than the grid; see RiskSnapshot.note). */
export interface WeatherContext {
  rainfall7dMm: number;
  soilMoistureSurface: number;
}

export interface RiskSnapshot {
  predictionId: string;
  regionId: string;
  hazard: string;
  risk: RiskSummary;
  resolutionMeters: number;
  crs: string;
  bounds: RegionBounds | null;
  satellite: string;
  sourcePassTimestamp: string;
  predictionTimestamp: string;
  processingLagSeconds: number;
  predictionHorizonHours: number;
  modelId: string;
  modelVersion: string;
  alert: RiskAlert;
  rasterUrl: string | null;
  previewUrl: string | null;
  gridUrl: string | null;
  observationWindowScenes: string[] | null;
  gridShape: [number, number] | null;
  weatherContext: WeatherContext | null;
  note: string | null;
}

export interface RiskHistoryPoint {
  predictionId: string;
  predictionTimestamp: string;
  mean: number;
  alertLevel: string;
}

export interface RiskGridCell {
  lat: number;
  lon: number;
  value: number;
}

export interface RiskGrid {
  rows: number;
  cols: number;
  cells: RiskGridCell[];
}
