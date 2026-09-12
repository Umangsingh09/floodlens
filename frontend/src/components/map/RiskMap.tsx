import { CircleMarker, MapContainer, Polygon, TileLayer, Tooltip } from 'react-leaflet';
import type { LatLngBoundsExpression, LatLngTuple } from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { useRiskGrid } from '../../hooks/useRiskGrid';
import { classifyRiskTier, formatPercent, tierColor } from '../../lib/format';
import type { RegionInfo } from '../../types/region';
import type { RiskSnapshot } from '../../types/risk';
import styles from './RiskMap.module.css';

interface RiskMapProps {
  region: RegionInfo;
  risk: RiskSnapshot | null;
}

function toLatLngBounds(bounds: { west: number; south: number; east: number; north: number }): LatLngBoundsExpression {
  return [
    [bounds.south, bounds.west],
    [bounds.north, bounds.east],
  ];
}

export function RiskMap({ region, risk }: RiskMapProps) {
  const grid = useRiskGrid(risk?.gridUrl);
  const aoiPath: LatLngTuple[] = region.geojson.coordinates[0].map(([lon, lat]) => [lat, lon]);
  const overlayBounds = risk?.bounds ? toLatLngBounds(risk.bounds) : null;
  // Fit to the actual observation footprint when one exists — it's a small fraction of the
  // full AOI, so fitting to the whole region would render the risk cells imperceptibly small.
  const mapBounds = overlayBounds ?? toLatLngBounds(region.bounds);
  const boundsOptions = overlayBounds ? { padding: [60, 60] as [number, number] } : undefined;

  const counts = { safe: 0, moderate: 0, high: 0 };
  grid?.cells.forEach((cell) => {
    counts[classifyRiskTier(cell.value)] += 1;
  });

  return (
    <div className={styles.wrap}>
      <MapContainer bounds={mapBounds} boundsOptions={boundsOptions} scrollWheelZoom={false} className={styles.map}>
        <TileLayer
          url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
          attribution="Tiles &copy; Esri &mdash; Source: Esri, Maxar, Earthstar Geographics"
        />
        <Polygon positions={aoiPath} pathOptions={{ color: '#38bdf8', weight: 1.5, fillOpacity: 0.02 }} />
        {grid?.cells.map((cell) => {
          const tier = classifyRiskTier(cell.value);
          return (
            <CircleMarker
              key={`${cell.lat}-${cell.lon}`}
              center={[cell.lat, cell.lon]}
              radius={9}
              pathOptions={{
                color: tierColor(tier),
                fillColor: tierColor(tier),
                fillOpacity: 0.75,
                weight: 1,
                opacity: 0.9,
              }}
            >
              <Tooltip direction="top" offset={[0, -6]} opacity={1}>
                {formatPercent(cell.value)} flood risk
              </Tooltip>
            </CircleMarker>
          );
        })}
      </MapContainer>

      <div className={styles.legend}>
        <span className={styles.legendRow}>
          <span className={styles.dot} style={{ background: tierColor('safe') }} />
          Safer ({counts.safe})
        </span>
        <span className={styles.legendRow}>
          <span className={styles.dot} style={{ background: tierColor('moderate') }} />
          Watch ({counts.moderate})
        </span>
        <span className={styles.legendRow}>
          <span className={styles.dot} style={{ background: tierColor('high') }} />
          Flood risk ({counts.high})
        </span>
      </div>
    </div>
  );
}
