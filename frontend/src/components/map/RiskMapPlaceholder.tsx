import { MapContainer, TileLayer } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { DEFAULT_MAP_CENTER, DEFAULT_MAP_ZOOM } from '../../lib/constants';
import styles from './RiskMapPlaceholder.module.css';

/**
 * Base map only — no flood-risk layer exists yet.
 * This will be replaced once the AI team's spatial risk output is available.
 */
export function RiskMapPlaceholder() {
  return (
    <div className={styles.wrapper}>
      <div className={styles.banner}>
        Flood-risk overlay not yet available — showing base map of the target
        region only.
      </div>
      <MapContainer
        center={DEFAULT_MAP_CENTER}
        zoom={DEFAULT_MAP_ZOOM}
        scrollWheelZoom={false}
        className={styles.map}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
      </MapContainer>
    </div>
  );
}
