# API server for ScholarMatch (minimal)

This repository includes a small Flask API at `app.py` that exposes `/api/recommend` for frontend integration.

Requirements
- Python 3.8+
- Install dependencies:

```powershell
cd C:\Users\USER\Desktop\programming\scholarshipRecommmendation
python -m venv venv_api
venv_api\Scripts\activate
pip install -r requirements.txt
```

Run server

```powershell
python app.py
```

The API will listen on http://0.0.0.0:5000 by default. When open the frontend via a static server (e.g. `python -m http.server 8000`), the frontend will POST to `/api/recommend` (same origin) when both are served on the same host or when using a proxy.

If you serve the frontend from the same Flask host, run a simple static file route or use a production server.

Notes
- `app.py` uses `structured_real_scholarships.csv` as the data source. If the CSV cannot be read, a small built-in fallback list is used.
- The endpoint returns JSON with `results` (array of {name, score, eligible, link}).
