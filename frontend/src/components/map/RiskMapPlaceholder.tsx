import { MapContainer, TileLayer } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import {
  DEFAULT_MAP_CENTER,
  DEFAULT_MAP_ZOOM,
  FLOODLENS_STUDY_REGION_BOUNDS,
  FLOODLENS_STUDY_REGION_LABEL,
} from '../../lib/constants';
import styles from './RiskMapPlaceholder.module.css';

export function RiskMapPlaceholder() {
  const baseMap = (
    <TileLayer
      attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
    />
  );

  const studyRegionLayer = null;
  const futureRiskLayer = null;

  return (
    <div className={styles.wrapper}>
      <div className={styles.statusBar}>Risk layer: awaiting backend prediction</div>

      <div className={styles.mapFrame}>
        <div className={styles.studyRegionChip}>{FLOODLENS_STUDY_REGION_LABEL}</div>

        <MapContainer
          bounds={FLOODLENS_STUDY_REGION_BOUNDS}
          center={DEFAULT_MAP_CENTER}
          zoom={DEFAULT_MAP_ZOOM}
          scrollWheelZoom={false}
          className={styles.map}
          maxZoom={12}
          minZoom={5}
        >
          {baseMap}
          {studyRegionLayer}
          {futureRiskLayer}
        </MapContainer>
      </div>

      <div className={styles.legend} aria-label="Risk legend">
        <div className={styles.legendItem}>
          <span className={`${styles.swatch} ${styles.low}`} />
          <span>Low</span>
        </div>
        <div className={styles.legendItem}>
          <span className={`${styles.swatch} ${styles.moderate}`} />
          <span>Moderate</span>
        </div>
        <div className={styles.legendItem}>
          <span className={`${styles.swatch} ${styles.high}`} />
          <span>High</span>
        </div>
        <div className={styles.legendItem}>
          <span className={`${styles.swatch} ${styles.critical}`} />
          <span>Critical</span>
        </div>
      </div>
    </div>
  );
}
