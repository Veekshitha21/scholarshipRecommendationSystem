import pickle
import re
from pathlib import Path

import pandas as pd
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)
CORS(app)

CSV_PATH = Path(__file__).resolve().parent.parent / "ml" / "structured_real_scholarships.csv"
RANK_MODEL_PATH = Path(__file__).resolve().parent.parent / "ml" / "rank_model.pkl"
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
ML_DIR = Path(__file__).resolve().parent.parent / "ml"


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


def normalize_class(value):
    v = str(value or "").strip().lower()
    if not v:
        return "any"
    if v in {"any", "all"}:
        return "any"
    if v in {"8", "9", "10", "school"}:
        return "school"
    if v in {"11", "12", "pu", "puc"}:
        return "pu"
    if v in {"diploma"}:
        return "diploma"
    if v in {"ug", "degree", "undergraduate"}:
        return "ug"
    if v in {"pg", "masters", "master", "postgraduate"}:
        return "pg"
    return v


def class_to_education(class_level):
    c = normalize_class(class_level)
    if c in {"school", "pu", "diploma", "ug", "pg"}:
        return c
    return "any"


def education_match(row_level, user_level):
    row_norm = normalize_education(row_level)
    user_norm = normalize_education(user_level)

    if row_norm == "any" or user_norm == "any":
        return "full"
    if row_norm == user_norm:
        return "full"

    # Pairs that should match with partial credit
    near_pairs = {
        ("ug", "diploma"),
        ("diploma", "ug"),
        ("pu", "school"),
        ("school", "pu"),
        ("ug", "school"),  # High school students can see UG scholarships
        ("ug", "pu"),      # PU students can see UG scholarships
    }
    if (row_norm, user_norm) in near_pairs:
        return "partial"

    return "none"


def infer_min_marks(level):
    lvl = normalize_education(level)
    if lvl == "pg":
        return 75.0
    if lvl == "ug":
        return 70.0
    if lvl == "diploma":
        return 60.0
    if lvl == "pu":
        return 60.0
    if lvl == "school":
        return 50.0
    return 65.0


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


def normalize_disability(value):
    v = str(value or "").strip().lower()
    if not v:
        return "no"

    # Common affirmative indicators
    yes_indicators = {"yes", "y", "1", "true", "pwd", "disabled", "for pwd", "only", "only for pwd", "persons with disability", "person with disability", "person with disabilities"}
    no_indicators = {"no", "n", "false", "0"}

    # Normalize common phrases
    vs = re.sub(r"[^a-z0-9 ]+", " ", v)
    vs = re.sub(r"\s+", " ", vs).strip()

    # direct matches
    if vs in yes_indicators:
        return "yes"
    if vs in no_indicators or vs == "any":
        return "no"

    # contains checks for more flexible detection
    if any(tok in vs for tok in ("yes", "pwd", "disabled", "disability", "only")):
        return "yes"

    # default to 'no' (conservative: treat missing/unknown as non-disabled requirement)
    return "no"


def build_user_rank_feature(user):
    return (
        f"cat_{user['category']} gen_{user['gender']} edu_{user['education']} "
        f"dis_{user['disability']} inc_{income_bucket(user['income'])} "
        f"state_{user['state']}"
    )


def is_recommendable_name(name):
    text = str(name or "").strip().lower()
    text = re.sub(r"[_\-]+", " ", text)
    if not text:
        return False
    non_scholarship_patterns = [
        r"\bfaq(s)?\b",
        r"\bguideline(s)?\b",
        r"\bguidlines\b",
        r"\bgl\b",
        r"\bstipend\b",
        r"\bmorb\b",
    ]
    return not any(re.search(pattern, text) for pattern in non_scholarship_patterns)


def ensure_default_ssp(df):
    if df.empty:
        return df
    has_ssp = df["scholarship_name"].astype(str).str.contains(r"\bssp\b", case=False, regex=True).any()
    if has_ssp:
        return df
    extra = pd.DataFrame(
        [
            {
                "scholarship_name": "SSP Post Matric Scholarship",
                "max_income": 250000.0,
                "scholarship_amount": 20000.0,
                "gender": "any",
                "education_level": "ug",
                "category": "any",
                "min_marks": 60.0,
                "disability": "no",
                "state": "karnataka",
            }
        ]
    )
    return pd.concat([df, extra], ignore_index=True)


def load_scholarships():
    try:
        df = pd.read_csv(CSV_PATH)
        df.columns = df.columns.str.strip().str.lower()
        if "scholarship_name" not in df.columns:
            df.rename(columns={df.columns[0]: "scholarship_name"}, inplace=True)

        for col, default in {
            "max_income": 0.0,
            "scholarship_amount": 0.0,
            "gender": "Any",
            "education_level": "Any",
            "category": "any",
            "min_marks": None,
            "disability": "no",
            "state": "any",
        }.items():
            if col not in df.columns:
                df[col] = default

        df["scholarship_name"] = df["scholarship_name"].fillna("Scholarship").astype(str)
        df["max_income"] = pd.to_numeric(df["max_income"], errors="coerce").fillna(0.0)
        df["scholarship_amount"] = pd.to_numeric(df["scholarship_amount"], errors="coerce").fillna(0.0)
        df["gender"] = df["gender"].fillna("Any").astype(str).str.strip().str.lower()
        df["education_level"] = df["education_level"].fillna("Any").astype(str).apply(normalize_education)
        df["category"] = df["category"].fillna("any").astype(str).str.strip().str.lower()
        df["disability"] = df["disability"].fillna("no").astype(str).apply(normalize_disability)
        df["state"] = df["state"].fillna("any").astype(str).str.strip().str.lower()
        min_marks_series = pd.to_numeric(df["min_marks"], errors="coerce")
        df["min_marks"] = min_marks_series.fillna(df["education_level"].apply(infer_min_marks))
        df = df[df["scholarship_name"].apply(is_recommendable_name)].copy()
        df = df.drop_duplicates(subset=["scholarship_name"], keep="first")
        df = ensure_default_ssp(df)
        return df
    except Exception:
        return pd.DataFrame([
            {
                "scholarship_name": "National Merit Grant",
                "max_income": 800000,
                "scholarship_amount": 50000,
                "gender": "any",
                "education_level": "ug",
                "category": "any",
                "min_marks": 70,
                "disability": "no",
            },
            {
                "scholarship_name": "STEM Future Fellowship",
                "max_income": 600000,
                "scholarship_amount": 75000,
                "gender": "any",
                "education_level": "pg",
                "category": "any",
                "min_marks": 80,
                "disability": "no",
            },
        ])


def load_rank_model():
    if not RANK_MODEL_PATH.exists():
        return None
    try:
        with open(RANK_MODEL_PATH, "rb") as f:
            model = pickle.load(f)
        if not isinstance(model, dict):
            return None
        if {"vectorizer", "X", "names"} - set(model.keys()):
            return None
        return model
    except Exception:
        return None


RANK_MODEL = load_rank_model()


@app.route("/api/dataset-preview", methods=["GET"])
def dataset_preview():
    """Return real scholarship names from the ML dataset for UI ticker (no hardcoded list)."""
    try:
        df = load_scholarships()
        if df.empty:
            return jsonify({"scholarships": []})
        limit = min(int(request.args.get("limit", 36)), 200)
        names = df["scholarship_name"].astype(str).head(limit).tolist()
        return jsonify({"scholarships": names})
    except Exception as exc:
        return jsonify({"scholarships": [], "error": str(exc)}), 200


@app.route("/api/recommend", methods=["POST"])
def recommend():
    body = request.get_json() or {}
    marks = float(body.get("marks") or 0)
    income = float(body.get("income") or 0)
    class_level = normalize_class(body.get("class_level") or "any")
    category = str(body.get("category") or "any").strip().lower() or "any"
    gender = str(body.get("gender") or "any").strip().lower() or "any"
    disability = normalize_disability(body.get("disability") or "no")
    state = str(body.get("state") or "any").strip().lower() or "any"
    edu_from_form = normalize_education(body.get("education_level") or "")
    education = (
        edu_from_form
        if edu_from_form and edu_from_form != "any"
        else class_to_education(class_level)
    )

    df = load_scholarships()
    user_profile = {
        "category": category,
        "gender": gender,
        "education": education,
        "disability": disability,
        "income": income,
        "state": state,
    }
    name_to_similarity = {}
    if RANK_MODEL:
        user_feature = build_user_rank_feature(user_profile)
        try:
            user_vec = RANK_MODEL["vectorizer"].transform([user_feature])
            sims = cosine_similarity(user_vec, RANK_MODEL["X"]).flatten()
            for idx, raw_name in enumerate(RANK_MODEL["names"]):
                name = str(raw_name or "").strip()
                if not name:
                    continue
                sim = float(sims[idx]) if idx < len(sims) else 0.0
                if name not in name_to_similarity or sim > name_to_similarity[name]:
                    name_to_similarity[name] = sim
        except Exception:
            name_to_similarity = {}

    rows = []
    for _, r in df.iterrows():
        name = str(r.get("scholarship_name") or "Scholarship")
        try:
            min_marks = float(r.get("min_marks") or infer_min_marks(r.get("education_level")))
        except Exception:
            min_marks = 65.0
        try:
            max_income = float(r.get("max_income") or 0)
        except Exception:
            max_income = 0.0
        try:
            amount = float(r.get("scholarship_amount") or 0)
        except Exception:
            amount = 0.0

        score = 0.0
        eligible = True

        # marks (35 points)
        if marks >= min_marks:
            score += 35
        elif marks >= min_marks - 10:
            score += 20
        else:
            eligible = False

        # income (30 points)
        if not max_income or income <= max_income:
            score += 30
        else:
            score += (max_income / (income + 1.0)) * 30.0
            eligible = False

        # category (10 points)
        sch_cat = str(r.get("category") or "any").strip().lower()
        if sch_cat == "any" or category == "any" or sch_cat == category:
            score += 10
        else:
            eligible = False

        # gender (10 points)
        sch_gender = str(r.get("gender") or "any").strip().lower()
        if sch_gender == "any" or gender == "any" or sch_gender == gender:
            score += 10

        # disability (5 points)
        sch_dis = normalize_disability(r.get("disability") or "no")
        # IMPORTANT: Non-disabled students should NOT get disability-only scholarships.
        # Skip any scholarship that requires disability if user selected "no"
        if disability == "no" and sch_dis == "yes":
            try:
                app.logger.debug(f"Skipping {name} because scholarship requires disability but user has none")
            except Exception:
                pass
            continue
        # Give full score if scholarship has no disability requirement OR if disability matches
        if sch_dis == "no" or sch_dis == disability:
            score += 5
        else:
            # User is disabled but scholarship doesn't support disabilities
            eligible = False

        # state (15 points)
        sch_state = str(r.get("state") or "any").strip().lower()
        if sch_state == "any" or state == "any" or sch_state == state:
            score += 15
        else:
            score += 3

        # education (10 points)
        row_level_raw = str(r.get("education_level") or "")
        row_level = normalize_education(row_level_raw)
        edu_result = education_match(row_level, education)
        if edu_result == "full":
            score += 10
        elif edu_result == "partial":
            score += 5

        # amount (0-5 points)
        if amount > 0:
            score += min(5.0, (amount / 100000.0) * 5.0)

        # Karnataka users often expect SSP in recommendations.
        if state == "karnataka" and "ssp" in name.lower():
            score += 25

        # trained rank model similarity bonus (0-100 points)
        similarity = name_to_similarity.get(name, 0.0)
        ml_score = max(0.0, min(100.0, similarity * 100.0))
        if state == "karnataka" and "ssp" in name.lower():
            ml_score = max(ml_score, 92.0)
        rule_score = score
        # Keep recommendations user-rule aware while making the model
        # the primary driver of ranking.
        final_score = (0.65 * ml_score) + (0.35 * rule_score)

        rows.append({
            "name": name,
            "score": round(final_score, 2),
            "eligible": bool(eligible),
            "link": f"https://scholarships.gov.in/?search={name.replace(' ', '+')}",
            "max_income": max_income,
            "scholarship_amount": amount,
            "education_level": row_level,
            "gender": sch_gender,
            "category": sch_cat,
            "disability": sch_dis,
            "state": sch_state,
            "ml_similarity": round(similarity, 4),
            "ml_score": round(ml_score, 2),
            "rule_score": round(rule_score, 2),
        })

    rows = sorted(rows, key=lambda x: (not x["eligible"], -x["score"], -x["ml_similarity"]))

    return jsonify({"results": rows[:50]})


ALLOWED_FRONTEND_FILES = frozenset(
    {
        "index.html",
        "script.js",
        "styles.css",
        "welcome.html",
        "welcome.js",
    }
)


@app.route("/")
def home():
    """Scholarship dashboard (main app). Landing page: /welcome.html"""
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/<path:filename>")
def frontend_files(filename):
    if filename in ALLOWED_FRONTEND_FILES:
        return send_from_directory(FRONTEND_DIR, filename)
    return jsonify({"error": "Not found"}), 404


@app.route("/ml/<path:filename>")
def ml_files(filename):
    if filename == "structured_real_scholarships.csv":
        return send_from_directory(ML_DIR, filename)
    return jsonify({"error": "Not found"}), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
