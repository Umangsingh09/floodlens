export const API_BASE_URL: string =
  import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

/**
 * Approximate center/zoom for the target Bihar flood-prone region.
 * Placeholder framing only — the exact AOI will be finalized with the AI/data team.
 */
export const DEFAULT_MAP_CENTER: [number, number] = [25.6, 85.1];
export const DEFAULT_MAP_ZOOM = 7;
