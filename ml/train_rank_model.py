import pickle
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

ROOT = Path(__file__).resolve().parent
CSV_PATH = ROOT / "structured_real_scholarships.csv"
MODEL_PATH = ROOT / "rank_model.pkl"


def normalize_education(value):
    v = str(value or "").strip().lower()
    if not v:
        return "any"
    if v in {"any", "all"}:
        return "any"
    if v in {"degree", "undergraduate", "bachelor", "bachelors", "ug"}:
        return "ug"
    if v in {"masters", "master", "postgraduate", "pg"}:
        return "pg"
    if v in {"diploma", "polytechnic"}:
        return "diploma"
    if v in {"1-10th", "10th", "school", "secondary", "high school"}:
        return "school"
    if v in {"pu", "puc", "pre-university", "pre university", "11th", "12th"}:
        return "pu"
    return v


def income_bucket(amount):
    try:
        x = float(amount or 0)
    except Exception:
        x = 0.0
    if x <= 0:
        return "any"
    if x <= 300000:
        return "low"
    if x <= 600000:
        return "mid"
    return "high"


def build_feature(row):
    category = str(row.get("category") or "any").strip().lower() or "any"
    gender = str(row.get("gender") or "any").strip().lower() or "any"
    disability = str(row.get("disability") or "no").strip().lower() or "no"
    education = normalize_education(row.get("education_level") or "any")
    income = income_bucket(row.get("max_income") or 0)
    # these are placeholders until dataset has these fields
    minority = str(row.get("minority") or "any").strip().lower() or "any"
    state = str(row.get("state") or "any").strip().lower() or "any"

    return f"cat_{category} gen_{gender} edu_{education} dis_{disability} inc_{income} minority_{minority} state_{state}"


def train_and_save():
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {CSV_PATH}")

    df = pd.read_csv(CSV_PATH)
    df.columns = df.columns.str.strip().str.lower()

    if "scholarship_name" not in df.columns:
        df = df.rename(columns={df.columns[0]: "scholarship_name"})

    df["feature_text"] = df.apply(build_feature, axis=1)
    names = df["scholarship_name"].fillna("Scholarship").astype(str).tolist()

    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
    X = vectorizer.fit_transform(df["feature_text"])

    with open(MODEL_PATH, "wb") as f:
        pickle.dump({"vectorizer": vectorizer, "X": X, "names": names}, f)

    print(f"Model trained and saved to: {MODEL_PATH}")
    print(f"Rows trained: {len(df)}")


if __name__ == "__main__":
    train_and_save()
