# API server for ScholarMatch

This repository includes a Flask API at `backend/app.py` that exposes `/api/recommend` for frontend integration and serves the frontend from the same host.

Requirements
- Python 3.8+
- Install dependencies:

```powershell
cd C:\Users\USER\Desktop\programming\scholarshipRecommmendation
python -m venv venv_api
venv_api\Scripts\activate
pip install -r backend\requirements.txt
```

Run server

```powershell
python backend\app.py
```

The API listens on http://0.0.0.0:5000 by default and serves the frontend files (`index.html`, `script.js`, `styles.css`) directly.

Notes
- `backend/app.py` uses `ml/structured_real_scholarships.csv` as the data source.
- If available, `ml/rank_model.pkl` is used to improve ranking with trained similarity signals.
- The endpoint returns JSON with `results` sorted from most recommended to least recommended.
