import { BellIcon, GridIcon, SatelliteIcon, ShieldIcon } from '../components/icons/Icons';
import type { HistoricalEvent } from '../types/events';
import type { RegionInfo } from '../types/region';
import type { RiskSnapshot } from '../types/risk';
import styles from './AboutPage.module.css';

interface AboutPageProps {
  region: RegionInfo | null;
  risk: RiskSnapshot | null;
  events: HistoricalEvent[];
}

const FALLBACK_LIMITATION =
  'The current baseline model is trained on a single real historical event ' +
  '(Sentinel-1 + the Global Flood Database reference for DFO 4507, Aug 2017) — treat this ' +
  'as a hackathon proof of pipeline, not a calibrated production forecast. Rainfall and soil ' +
  "moisture are real, live inputs, but with only one historical training instant, the model " +
  "can't yet learn how they affect outcome — that needs training data spanning multiple real " +
  'events with different rainfall conditions.';

export function AboutPage({ region, risk, events }: AboutPageProps) {
  return (
    <div className={styles.wrap}>
      <div className={styles.pageHead}>
        <span className={styles.eyebrow}>Data & methodology</span>
        <h1 className={styles.heading}>What FloodLens actually shows</h1>
        <p className={styles.lede}>
          A geospatial risk map is only useful if you know what's behind it. This page states
          plainly what data feeds the model, how the map is validated, and what isn't built yet —
          nothing here is fabricated to look more finished than it is.
        </p>
      </div>

      <div className={styles.grid}>
        <section className={styles.card}>
          <div className={styles.cardHead}>
            <ShieldIcon />
            <h2>Scope</h2>
          </div>
          <dl className={styles.facts}>
            <div>
              <dt>Hazard</dt>
              <dd>Flood — single hazard, by design</dd>
            </div>
            <div>
              <dt>Region</dt>
              <dd>{region?.aoiName ?? 'not loaded'}</dd>
            </div>
            <div>
              <dt>Prediction horizon</dt>
              <dd>{region ? `${region.predictionHorizonDays} days ahead` : '—'}</dd>
            </div>
          </dl>
        </section>

        <section className={styles.card}>
          <div className={styles.cardHead}>
            <SatelliteIcon />
            <h2>Data source</h2>
          </div>
          <dl className={styles.facts}>
            <div>
              <dt>Satellite</dt>
              <dd>{region?.satelliteCollection ?? 'Sentinel-1 GRD'} via Google Earth Engine</dd>
            </div>
            <div>
              <dt>Grid resolution</dt>
              <dd>{risk ? `${risk.resolutionMeters}m` : '250m (no live prediction yet)'}</dd>
            </div>
            <div>
              <dt>Processing lag</dt>
              <dd>
                {risk
                  ? `documented per prediction (currently ${Math.round(risk.processingLagSeconds / 60)} min)`
                  : 'documented per prediction once one has run'}
              </dd>
            </div>
          </dl>
        </section>

        <section className={styles.card}>
          <div className={styles.cardHead}>
            <GridIcon />
            <h2>Model & validation</h2>
          </div>
          <dl className={styles.facts}>
            <div>
              <dt>Current model</dt>
              <dd>{risk ? `${risk.modelId} · ${risk.modelVersion}` : 'no live prediction yet'}</dd>
            </div>
            <div>
              <dt>Model inputs</dt>
              <dd>
                Sentinel-1 backscatter change, terrain (elevation/slope), plus real-time rainfall
                (NASA GPM) and soil moisture (NASA SMAP)
              </dd>
            </div>
            <div>
              <dt>Validated against</dt>
              <dd>
                {events.length > 0
                  ? `${events.length} real historical event${events.length === 1 ? '' : 's'} (DFO ${events
                      .map((e) => e.dfoId)
                      .join(', ')})`
                  : 'no validated events loaded'}
              </dd>
            </div>
          </dl>
          <div className={styles.formula}>
            <code>flood_reference = flooded == 1 &amp;&amp; permanent_water == 0</code>
          </div>
          <p className={styles.cardNote}>
            Validation reference is satellite-derived (Global Flood Database), not ground survey
            data — it excludes permanent water so the mask represents flood water specifically.
          </p>
        </section>

        <section className={styles.card}>
          <div className={styles.cardHead}>
            <ShieldIcon />
            <h2>Known limitations</h2>
          </div>
          <p className={styles.cardNote}>{risk?.note ?? FALLBACK_LIMITATION}</p>
        </section>
      </div>

      <section className={styles.roadmap}>
        <span className={styles.badge}>
          <BellIcon />
          Coming soon
        </span>
        <h2 className={styles.roadmapHeading}>Threshold-based alerting isn't connected yet</h2>
        <p className={styles.cardNote}>
          No alerts are active, scheduled, or being sent today. Once connected, this will notify
          subscribers when a region's predicted mean risk crosses a configured threshold — the
          same threshold already tracked per prediction (see the alert level shown on Dashboard
          and Risk Map).
        </p>
      </section>
    </div>
  );
}
