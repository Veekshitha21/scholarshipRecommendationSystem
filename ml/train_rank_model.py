import pickle
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT.parent / "data"
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


def normalize_gender(value):
    v = str(value or "").strip().lower()
    if not v or v in {"any", "all"}:
        return "any"
    if v in {"f", "female", "girl", "women", "woman"}:
        return "female"
    if v in {"m", "male", "boy", "men", "man"}:
        return "male"
    return "any"


def normalize_category(value):
    v = str(value or "").strip().lower()
    if not v or v in {"any", "all", "general"}:
        return "any"
    if "obc" in v:
        return "obc"
    if v in {"sc", "scheduled caste"}:
        return "sc"
    if v in {"st", "scheduled tribe"}:
        return "st"
    if "minority" in v:
        return "minority"
    return "any"


def normalize_disability(value):
    v = str(value or "").strip().lower()
    if v in {"yes", "y", "1", "true", "pwd", "disabled"}:
        return "yes"
    return "no"


def scholarship_requires_disability_support(value):
    text = str(value or "").strip().lower()
    text = " ".join(text.split())
    if not text or text in {"no", "any"}:
        return False
    required_tokens = {
        "yes",
        "required",
        "only",
        "only for pwd",
        "pwd",
        "disabled",
        "persons with disability",
        "person with disability",
        "person with disabilities",
        "for pwd",
    }
    return text in required_tokens or any(token in text for token in ("pwd", "disabled", "disability", "required", "only"))


def normalize_name(value):
    return str(value or "").strip()


def normalize_state(value):
    v = str(value or "").strip().lower()
    if not v or v in {"india", "all", "any"}:
        return "any"
    return v


def candidate_scholarship_names(df):
    names = set()
    for col in df.columns:
        key = str(col).strip().lower()
        if key == "name" or key.startswith("scholarship"):
            series = df[col].dropna().astype(str).str.strip()
            for name in series.unique():
                if name and name.lower() not in {"nan", "none"}:
                    names.add(name)
    return sorted(names)


def pick_mode(series, normalizer, default):
    if series is None or series.empty:
        return default
    normalized = series.dropna().astype(str).map(normalizer)
    if normalized.empty:
        return default
    counts = normalized.value_counts()
    if counts.empty:
        return default
    return str(counts.index[0] or default)


def build_rows_from_profile_sheet(df):
    cols = {str(c).strip().lower(): c for c in df.columns}
    names = candidate_scholarship_names(df)
    if not names:
        return []

    outcome_col = cols.get("outcome")
    income_col = cols.get("income")
    marks_col = cols.get("annual-percentage")
    gender_col = cols.get("gender")
    category_col = cols.get("community")
    disability_col = cols.get("disability")
    education_col = cols.get("education qualification")
    state_col = cols.get("india") or cols.get("state")

    base_df = df
    if outcome_col is not None:
        out = pd.to_numeric(df[outcome_col], errors="coerce").fillna(0)
        positives = df[out > 0]
        if not positives.empty:
            base_df = positives

    max_income = 0.0
    if income_col is not None:
        income_vals = pd.to_numeric(base_df[income_col], errors="coerce").dropna()
        if not income_vals.empty:
            max_income = float(income_vals.quantile(0.95))

    min_marks = 65.0
    if marks_col is not None:
        marks_vals = pd.to_numeric(base_df[marks_col], errors="coerce").dropna()
        if not marks_vals.empty:
            min_marks = float(marks_vals.quantile(0.10))

    gender = pick_mode(base_df[gender_col], normalize_gender, "any") if gender_col else "any"
    category = pick_mode(base_df[category_col], normalize_category, "any") if category_col else "any"
    disability = (
        pick_mode(base_df[disability_col], normalize_disability, "no") if disability_col else "no"
    )
    education_level = (
        pick_mode(base_df[education_col], normalize_education, "any") if education_col else "any"
    )
    state = pick_mode(base_df[state_col], normalize_state, "any") if state_col else "any"

    rows = []
    for scholarship_name in names:
        rows.append(
            {
                "scholarship_name": normalize_name(scholarship_name),
                "max_income": max_income,
                "gender": gender,
                "education_level": education_level,
                "scholarship_amount": 0.0,
                "category": category,
                "min_marks": min_marks,
                "disability": disability,
                "state": state,
            }
        )
    return rows


def build_rows_from_structured_sheet(df):
    df.columns = [str(c).strip().lower() for c in df.columns]
    required = {"name", "min_marks", "max_income", "category", "gender", "disability", "course"}
    if not required.issubset(set(df.columns)):
        return []

    out_df = pd.DataFrame()
    out_df["scholarship_name"] = df["name"].fillna("Scholarship").astype(str).str.strip()
    out_df["max_income"] = pd.to_numeric(df["max_income"], errors="coerce").fillna(0.0)
    out_df["gender"] = df["gender"].fillna("Any").astype(str).map(normalize_gender)
    out_df["education_level"] = df["course"].fillna("Any").astype(str).map(normalize_education)
    out_df["scholarship_amount"] = 0.0
    out_df["category"] = df["category"].fillna("any").astype(str).map(normalize_category)
    out_df["min_marks"] = pd.to_numeric(df["min_marks"], errors="coerce").fillna(65.0)
    out_df["disability"] = df["disability"].fillna("no").astype(str).map(normalize_disability)
    if "state" in df.columns:
        out_df["state"] = df["state"].fillna("any").astype(str).map(normalize_state)
    else:
        out_df["state"] = "any"
    out_df = out_df.drop_duplicates(subset=["scholarship_name"], keep="first")
    return out_df.to_dict(orient="records")


def rebuild_structured_dataset_from_data():
    if not DATA_DIR.exists():
        raise FileNotFoundError(f"Data folder not found: {DATA_DIR}")

    rows = []
    source_files = sorted(DATA_DIR.glob("*.xlsx"))
    if not source_files:
        raise FileNotFoundError(f"No .xlsx files found in: {DATA_DIR}")

    for file_path in source_files:
        try:
            df = pd.read_excel(file_path)
            structured_rows = build_rows_from_structured_sheet(df)
            if not structured_rows:
                structured_rows = build_rows_from_profile_sheet(df)
            rows.extend(structured_rows)
            print(f"Loaded {file_path.name}: +{len(structured_rows)} rows")
        except Exception as exc:
            print(f"Skipped {file_path.name}: {exc}")

    if not rows:
        raise ValueError("No rows could be extracted from data files.")

    merged = pd.DataFrame(rows)
    merged = merged.dropna(subset=["scholarship_name"])
    merged["scholarship_name"] = merged["scholarship_name"].astype(str).str.strip()
    merged = merged[merged["scholarship_name"] != ""]
    merged = merged.drop_duplicates(subset=["scholarship_name"], keep="first")
    merged.to_csv(CSV_PATH, index=False)
    print(f"Structured dataset saved to: {CSV_PATH}")
    print(f"Total unique scholarships: {len(merged)}")


def build_feature(row):
    category = str(row.get("category") or "any").strip().lower() or "any"
    gender = str(row.get("gender") or "any").strip().lower() or "any"
    disability = str(row.get("disability") or "no").strip().lower() or "no"
    if scholarship_requires_disability_support(disability):
        disability = "yes"
    education = normalize_education(row.get("education_level") or "any")
    income = income_bucket(row.get("max_income") or 0)
    state = normalize_state(row.get("state") or "any")

    return f"cat_{category} gen_{gender} edu_{education} dis_{disability} inc_{income} state_{state}"


def train_and_save():
    rebuild_structured_dataset_from_data()

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
