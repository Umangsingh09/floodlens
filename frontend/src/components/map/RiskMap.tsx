import { useState } from 'react';
import { CircleMarker, MapContainer, Polygon, TileLayer, Tooltip } from 'react-leaflet';
import type { LatLngBoundsExpression, LatLngTuple } from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { useRiskGrid } from '../../hooks/useRiskGrid';
import { classifyRiskTier, formatPercent, tierColor, tierEmoji, tierLabel, type RiskTier } from '../../lib/format';
import type { RegionInfo } from '../../types/region';
import type { RiskGridCell, RiskSnapshot } from '../../types/risk';
import { GridCellDetail } from './GridCellDetail';
import styles from './RiskMap.module.css';

interface RiskMapProps {
  region: RegionInfo;
  risk: RiskSnapshot | null;
  /** 'compact' fits inline in a dashboard panel; 'full' fills a dedicated map page. */
  variant?: 'compact' | 'full';
}

const TIERS: RiskTier[] = ['low', 'moderate', 'high', 'critical'];

function toLatLngBounds(bounds: { west: number; south: number; east: number; north: number }): LatLngBoundsExpression {
  return [
    [bounds.south, bounds.west],
    [bounds.north, bounds.east],
  ];
}

export function RiskMap({ region, risk, variant = 'compact' }: RiskMapProps) {
  const grid = useRiskGrid(risk?.gridUrl);
  const [selectedCell, setSelectedCell] = useState<RiskGridCell | null>(null);
  const aoiPath: LatLngTuple[] = region.geojson.coordinates[0].map(([lon, lat]) => [lat, lon]);
  const overlayBounds = risk?.bounds ? toLatLngBounds(risk.bounds) : null;
  // Fit to the actual observation footprint when one exists — it's a small fraction of the
  // full AOI, so fitting to the whole region would render the risk cells imperceptibly small.
  const mapBounds = overlayBounds ?? toLatLngBounds(region.bounds);
  const boundsOptions = overlayBounds ? { padding: [60, 60] as [number, number] } : undefined;

  const counts: Record<RiskTier, number> = { low: 0, moderate: 0, high: 0, critical: 0 };
  grid?.cells.forEach((cell) => {
    counts[classifyRiskTier(cell.value)] += 1;
  });

  return (
    <div className={styles.wrap} data-variant={variant} data-detail-open={selectedCell ? 'true' : 'false'}>
      <MapContainer bounds={mapBounds} boundsOptions={boundsOptions} scrollWheelZoom={variant === 'full'} className={styles.map}>
        <TileLayer
          url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
          attribution="Tiles &copy; Esri &mdash; Source: Esri, Maxar, Earthstar Geographics"
        />
        <Polygon positions={aoiPath} pathOptions={{ color: '#38bdf8', weight: 1.5, fillOpacity: 0.02 }} />
        {grid?.cells.map((cell) => {
          const tier = classifyRiskTier(cell.value);
          const isSelected = selectedCell?.lat === cell.lat && selectedCell?.lon === cell.lon;
          return (
            <CircleMarker
              key={`${cell.lat}-${cell.lon}`}
              center={[cell.lat, cell.lon]}
              radius={isSelected ? 11 : 9}
              pathOptions={{
                // A neutral halo ring keeps a cell legible against the varied satellite
                // basemap underneath, instead of relying on the fill hue alone.
                color: isSelected ? tierColor(tier) : '#f8fafc',
                weight: isSelected ? 2.5 : 1.25,
                fillColor: tierColor(tier),
                fillOpacity: 0.8,
                opacity: 0.95,
              }}
              eventHandlers={{
                click: () => setSelectedCell(isSelected ? null : cell),
              }}
            >
              <Tooltip direction="top" offset={[0, -6]} opacity={1}>
                {tierEmoji(tier)} {formatPercent(cell.value)} flood risk — click for detail
              </Tooltip>
            </CircleMarker>
          );
        })}
      </MapContainer>

      <div className={styles.legend}>
        <span className={styles.legendTitle}>Flood risk</span>
        {TIERS.map((tier) => (
          <span key={tier} className={styles.legendRow}>
            <span className={styles.dot} style={{ background: tierColor(tier) }} />
            {tierEmoji(tier)} {tierLabel(tier)} ({counts[tier]})
          </span>
        ))}
      </div>

      {selectedCell && risk && (
        <GridCellDetail cell={selectedCell} risk={risk} onClose={() => setSelectedCell(null)} />
      )}
    </div>
  );
}
