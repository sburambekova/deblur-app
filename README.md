# Deblur

A website that sharpens photos blurred by camera shake or bad focus, using classical
deconvolution (Tikhonov, total variation, Richardson–Lucy) instead of neural networks. You find
the blur with sliders and a live preview, then get the full-size result.

Live: http://34.154.57.202/

Software Engineering course project, Fall 2026, by Danial Baizak and Sandugash Burambekova.

## Layout

| Folder | What |
|---|---|
| `backend/` | Python, FastAPI, NumPy, SciPy: the deblurring engine and the HTTP API |
| `frontend/` | TypeScript, React, Vite: the website, served by nginx in production |
| `docker-compose.yml` | Runs both on one server |

## Run

```bash
docker compose up -d --build
```

Then open http://localhost/. The API is also on port 8000, with its docs at
http://localhost:8000/docs.

## Develop

```bash
cd backend
python -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/uvicorn app.main:app --reload --port 8000
.venv/bin/pytest -q
```

For the frontend, see [frontend/README.md](frontend/README.md).
