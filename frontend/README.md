# Deblur frontend

React + TypeScript, built with Vite. Phone first: Home, Adjust, Result and Gallery are separate
screens on a phone; on a screen 960 px or wider, Adjust and Result are one screen with the
spectrum next to the sliders.

## Run locally

Start the backend on port 8000 (see `backend/`), then:

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
```

Vite passes `/api` and `/files` on to `http://localhost:8000`, so the page and the API share one
origin, the same as in production behind nginx.

| Command | What |
|---|---|
| `npm run dev` | Dev server with hot reload |
| `npm run build` | Type check, then the production build in `dist/` |
| `npm run lint` | ESLint |
| `npm test` | Vitest: slider mapping, spectrum overlay, routes |

## Layout

| Path | What |
|---|---|
| `src/api.ts` | Calls to the backend, typed as in `backend/app/schemas` |
| `src/params.ts` | Deblur parameters, the per-method strength slider, labels |
| `src/hooks.ts` | Live preview (debounced, stale answers aborted), job polling |
| `src/spectrum.ts` | Where the kernel's line, marks or ring go over the spectrum |
| `src/upload.ts` | Shrinks photos over 15 MB in the browser before the upload |
| `src/router.ts` | Screens in the URL hash: `#/photo/<id>`, `#/photo/<id>/job/<id>`, `#/gallery` |
| `src/pages/` | Home, Editor (Adjust + Result), Gallery |
| `src/styles.css` | All styles; colours are the variables at the top |
| `public/example/` | The before/after on Home: real output of the backend on synthetic blur |

## Production

`docker compose up -d --build` from the repository root builds this folder into an nginx image
(`Dockerfile`, `nginx.conf`) that serves the site on port 80 and proxies `/api` and `/files` to
the backend container.
