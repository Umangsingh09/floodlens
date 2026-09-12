export interface RegionBounds {
  west: number;
  south: number;
  east: number;
  north: number;
}

export interface RegionInfo {
  regionId: string;
  aoiName: string;
  geojson: {
    type: string;
    coordinates: number[][][];
  };
  bounds: RegionBounds;
  satelliteCollection: string;
  predictionHorizonDays: number;
}
