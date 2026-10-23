/**
 * Vite config: React + Tailwind plugins. Reads env from the repo root .env
 * (see /.env.example) so the whole team shares one file.
 *
 * Implements: PLAN.md §9 (frontend stack). Owner: P1 (Frontend and UX).
 */
import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [react(), tailwindcss()],
  envDir: '..',
});
