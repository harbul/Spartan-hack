/**
 * Types for the VITE_* env vars (values in /.env.example).
 * Owner: P1 (Frontend and UX).
 */
interface ImportMetaEnv {
  readonly VITE_API_URL: string;
  readonly VITE_LOCATION_API_KEY: string;
  readonly VITE_LOCATION_REGION: string;
  readonly VITE_MAPBOX_TOKEN?: string;
  readonly VITE_USE_MOCK?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
