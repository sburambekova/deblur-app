import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

// The API runs separately on :8000 during development. The proxy puts it on the same origin as
// the page, as nginx does in production, so the code only ever uses paths like /api/photos.
const api = 'http://localhost:8000';
const proxy = { '/api': api, '/files': api };

export default defineConfig({
  plugins: [react()],
  server: { proxy },
  preview: { proxy },
});
