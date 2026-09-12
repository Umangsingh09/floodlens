# FloodLens — Frontend Design Brief

Use this document as context when prompting an AI (e.g. ChatGPT) to design
the FloodLens frontend. It describes what the product is, who it's for,
what screens/components it needs, and what tone and constraints the design
must respect.

---

## 1. What FloodLens is

FloodLens is a **spatial flood-risk intelligence dashboard** for a specific
flood-prone region of **Bihar, India**. It turns public satellite
observations into a geographically-explicit flood-risk map — showing
*where* risk is elevated across a region, not just a single yes/no or
percentage score for the whole area.

It is a **hackathon / early-stage project**. The current build is a
foundation only: a working app shell and a placeholder map. No AI model,
satellite data, or real predictions are connected yet — the design should
look like a credible, near-finished product, but the content it displays
today must stay honest about what's real vs. placeholder.

## 2. Who it's for

Primary users: disaster-management officials, local authorities, NGOs, and
researchers who need to understand flood risk **spatially** — which
villages/blocks/river stretches are most at risk — rather than a single
generic alert. Secondary users: technical judges/reviewers evaluating the
project, and the internal team.

Design tone: **serious, civic/public-safety, data-forward, trustworthy.**
Not playful, not consumer-app flashy. Think: emergency-management
dashboards, weather-service sites, geospatial analytics tools — clear
hierarchy, calm colors, high legibility, generous whitespace, map as the
centerpiece.

## 3. Core concept the design must communicate

- **One hazard:** flood only.
- **One region:** a specific flood-prone area of Bihar (not all of India).
- **Spatial output:** risk varies by location within the region — the map
  is the primary artifact, not a single big number.
- **Time-awareness:** every prediction is tied to a satellite pass
  timestamp and has a documented lag until the prediction is available.
  This lag should be visible in the UI wherever a prediction is shown.
- **Validated, not speculative:** the product's credibility comes from
  validation against a real historical flood event — this should be
  reflected somewhere (e.g., a "validated against [event]" note).

## 4. Screens / pages needed

### 4.1 Dashboard (home)
- Top-level summary of the current state of the region.
- Space for a few key stat tiles (e.g., current overall risk level, last
  satellite pass time, prediction lag, number of high-risk zones) — **all
  values here today are placeholders and must be visually marked as such**
  until real data exists.
- Prominent entry point into the risk map.

### 4.2 Risk Map (primary screen)
- Full interactive map of the target Bihar region (Leaflet-based).
- Layer toggle concept: base map vs. risk overlay (risk overlay doesn't
  exist yet — design should include an empty/placeholder state for it,
  e.g. "Risk overlay will appear here once the model is connected").
- A legend area for risk levels (low/medium/high) — for future use, styled
  now, not populated with real thresholds yet.
- A way to show metadata for the current view: region name, satellite pass
  timestamp, prediction timestamp, prediction lag.
- Click/hover-on-cell interaction concept for future per-location detail
  (can be a stub for now).

### 4.3 Historical Events
- A list/timeline of past flood events in the region, used for validation.
- Each event: date, brief description, and (later) a link to how the
  model's prediction compared to what actually happened.
- Currently no real event data is wired in — design an empty/placeholder
  state.

### 4.4 Alerts (future)
- Placeholder screen for threshold-based alerting (not built yet).
- Design as "coming soon" / disabled-state screen — should not imply
  alerts are active.

## 5. Global layout / navigation

- Persistent **header**: product name/logo, region label ("Bihar — [AOI
  name]"), and a live backend-connection status indicator (already
  implemented: online/offline/checking).
- Persistent **sidebar navigation**: Dashboard, Risk Map, Historical
  Events, Alerts. Only Dashboard is currently "live"; others should look
  reachable but can be marked as placeholder/in-progress.
- Main content area hosts the active page.
- Responsive: usable on a laptop screen at minimum; a tablet-friendly
  layout is a plus. Not required to be mobile-first.

## 6. Visual/design constraints

- **Map is the hero element** wherever it appears — don't let chrome
  overwhelm it.
- Use a **light and dark mode** aware palette (the current implementation
  already uses CSS variables that swap by `prefers-color-scheme`).
- Favor a **cool, low-saturation palette** (blues/teals/slate grays) that
  reads as calm and analytical, with a clear, distinct accent color
  reserved for risk severity (e.g., amber → high risk cues) — but do not
  hardcode real risk colors/thresholds as if they were final, since the
  risk scale itself hasn't been defined by the model team yet.
- Typography: clean system/sans-serif, strong hierarchy (large page
  titles, muted secondary text for metadata/timestamps).
- Any placeholder or "not yet available" content must be **visually
  distinguishable** (e.g., a muted banner, dashed border, or "placeholder"
  label) — never presented as if it were real data.

## 7. Explicit content rules (must follow)

- Never invent or display fake flood-risk numbers, percentages, or map
  overlays as if they were real predictions.
- Never imply satellite data, AI models, or alerts are live/connected —
  they are not, in the current phase.
- Any example numbers used purely for layout purposes (e.g., in a mockup)
  should be clearly labeled "example" / "placeholder", not realistic-looking
  final values.
- Do not fabricate the exact Bihar sub-region name if unknown — refer to
  it generically ("target region", "the AOI") unless a specific name has
  been confirmed by the team.

## 8. Current technical implementation (for design compatibility)

- **Stack:** React + TypeScript + Vite, CSS Modules, `react-leaflet` for
  the map.
- **Structure already in place:** `layouts/AppLayout` (header + sidebar +
  content), `pages/DashboardPage`, `components/map/RiskMapPlaceholder`
  (renders a real OpenStreetMap base layer centered on Bihar, no risk data),
  `components/layout/Header` and `Sidebar`.
- Designs should be deliverable as component-level mockups/specs
  (colors, spacing, typography, layout) that map cleanly onto this
  existing component structure, rather than a single flat homepage image.

## 9. What a good design deliverable looks like

- A defined color palette (light + dark) with named tokens.
- Header, sidebar, and page-content layout specs.
- Dashboard stat-tile component design (with a clear "placeholder" visual
  treatment).
- Risk map screen layout, including legend and metadata bar placement.
- Empty/placeholder states for: risk overlay, historical events list,
  alerts page.
- Basic responsive behavior notes (what collapses/stacks on a narrower
  screen).
