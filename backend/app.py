import pickle
import re
import sqlite3
from pathlib import Path
import time
import threading
import pandas as pd
import numpy as np
from flask import Flask, jsonify, request, send_from_directory, session
from datetime import timedelta
from flask_cors import CORS
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
CORS(app)
app.secret_key = "scholarmatch-dev-secret"
app.permanent_session_lifetime = timedelta(hours=24)

CSV_PATH = Path(__file__).resolve().parent.parent / "ml" / "structured_real_scholarships.csv"
RANK_MODEL_PATH = Path(__file__).resolve().parent.parent / "ml" / "rank_model.pkl"
SUCCESS_MODEL_PATH = Path(__file__).resolve().parent.parent / "ml" / "success_model.pkl"
ELIGIBILITY_CLASSIFIER_PATH = Path(__file__).resolve().parent.parent / "ml" / "eligibility_classifier.pkl"
PERCENTAGE_PREDICTOR_PATH = Path(__file__).resolve().parent.parent / "ml" / "percentage_predictor.pkl"
ELIGIBILITY_SCALER_PATH = Path(__file__).resolve().parent.parent / "ml" / "eligibility_scaler.pkl"
ELIGIBILITY_ENCODERS_PATH = Path(__file__).resolve().parent.parent / "ml" / "eligibility_encoders.pkl"
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
ML_DIR = Path(__file__).resolve().parent.parent / "ml"
AUTH_DB_PATH = Path(__file__).resolve().parent / "auth_users.db"


def init_auth_db():
    conn = sqlite3.connect(AUTH_DB_PATH)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                education TEXT,
                category TEXT,
                phone TEXT,
                income REAL,
                disability TEXT,
                gender TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        existing_columns = {row[1] for row in conn.execute("PRAGMA table_info(users)").fetchall()}
        if "marks" not in existing_columns:
            conn.execute("ALTER TABLE users ADD COLUMN marks REAL NOT NULL DEFAULT 0")
        if "education_level" not in existing_columns and "education" in existing_columns:
            conn.execute("ALTER TABLE users ADD COLUMN education_level TEXT")

        conn.commit()
    finally:
        conn.close()


def parse_body():
    body = request.get_json(silent=True)
    if isinstance(body, dict):
        return body
    return request.form.to_dict() if request.form else {}


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


def scholarship_requires_disability_support(value):
    text = re.sub(r"[^a-z0-9 ]+", " ", str(value or "").strip().lower())
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return False
    if text in {"no", "any"}:
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

def load_success_model():
    if not SUCCESS_MODEL_PATH.exists():
        return None
    try:
        with open(SUCCESS_MODEL_PATH, "rb") as f:
            return pickle.load(f)
    except Exception:
        return None


SUCCESS_MODEL = load_success_model()

# Load eligibility prediction models
def load_eligibility_models():
    """Load eligibility classifier, percentage predictor, scaler, and encoders."""
    try:
        clf = None
        predictor = None
        scaler = None
        encoders = None
        
        if ELIGIBILITY_CLASSIFIER_PATH.exists():
            with open(ELIGIBILITY_CLASSIFIER_PATH, 'rb') as f:
                clf = pickle.load(f)
        
        if PERCENTAGE_PREDICTOR_PATH.exists():
            with open(PERCENTAGE_PREDICTOR_PATH, 'rb') as f:
                predictor = pickle.load(f)
        
        if ELIGIBILITY_SCALER_PATH.exists():
            with open(ELIGIBILITY_SCALER_PATH, 'rb') as f:
                scaler = pickle.load(f)
        
        if ELIGIBILITY_ENCODERS_PATH.exists():
            with open(ELIGIBILITY_ENCODERS_PATH, 'rb') as f:
                encoders = pickle.load(f)
        
        return {
            'classifier': clf,
            'predictor': predictor,
            'scaler': scaler,
            'encoders': encoders
        }
    except Exception as e:
        app.logger.error(f"Error loading eligibility models: {e}")
        return {
            'classifier': None,
            'predictor': None,
            'scaler': None,
            'encoders': None
        }

ELIGIBILITY_MODELS = load_eligibility_models()
METRICS_LOCK = threading.Lock()
METRICS = {
    "total_requests": 0,
    "failed_requests": 0,
    "total_response_time_ms": 0.0,
    "last_response_time_ms": None,
}

def get_model_accuracy_percent():
    """Try to infer model accuracy from common attributes stored on a persisted model."""
    if not SUCCESS_MODEL:
        return None
    try:
        # sklearn RandomForest may have oob_score_
        if hasattr(SUCCESS_MODEL, "oob_score_"):
            return round(float(getattr(SUCCESS_MODEL, "oob_score_")) * 100, 2)
        # GridSearchCV stores best_score_
        if hasattr(SUCCESS_MODEL, "best_score_"):
            return round(float(getattr(SUCCESS_MODEL, "best_score_")) * 100, 2)
        # If the pickle contains a dict with an 'accuracy' key
        if isinstance(SUCCESS_MODEL, dict) and "accuracy" in SUCCESS_MODEL:
            return round(float(SUCCESS_MODEL["accuracy"]) * 100, 2)
    except Exception:
        return None
    return None
    return None


@app.route("/api/predict-eligibility", methods=["POST"])
def predict_eligibility():
    """
    Predict scholarship eligibility and percentage match for a student.
    
    Input JSON:
    {
        "marks": float,
        "income": float,
        "min_marks": float,
        "max_income": float,
        "category": string,
        "gender": string,
        "disability": string,
        "course": string
    }
    
    Returns:
    {
        "eligible": boolean,
        "eligibility_percentage": float (0-100),
        "confidence": float (0-1),
        "message": string,
        "model_accuracy": float (if available)
    }
    """
    try:
        body = request.get_json() or {}
        
        # Get input parameters
        marks = float(body.get("marks", 0))
        income = float(body.get("income", 0))
        min_marks = float(body.get("min_marks", 0))
        max_income = float(body.get("max_income", 0))
        category = str(body.get("category", "")).strip().lower() or "Unknown"
        gender = str(body.get("gender", "")).strip().lower() or "Unknown"
        disability = str(body.get("disability", "")).strip().lower() or "Unknown"
        course = str(body.get("course", "")).strip().lower() or "Unknown"
        
        # Check if models are loaded
        if not ELIGIBILITY_MODELS['classifier'] or not ELIGIBILITY_MODELS['scaler']:
            return jsonify({
                "error": "Eligibility models not loaded",
                "eligible": None,
                "eligibility_percentage": None
            }), 503
        
        # Prepare features for the model
        # The model expects the same features it was trained on
        feature_vector = pd.DataFrame({
            'marks': [marks],
            'min_marks': [min_marks],
            'max_income': [max_income],
            'category_encoded': [hash(category) % 256],
            'gender_encoded': [hash(gender) % 256],
            'disability_encoded': [hash(disability) % 256]
        })
        
        # Scale features
        features_scaled = ELIGIBILITY_MODELS['scaler'].transform(feature_vector)
        
        # Predict eligibility
        eligibility_pred = ELIGIBILITY_MODELS['classifier'].predict(features_scaled)[0]
        eligibility_proba = ELIGIBILITY_MODELS['classifier'].predict_proba(features_scaled)[0]
        confidence = float(max(eligibility_proba))
        
        # Predict percentage eligibility
        percentage_pred = ELIGIBILITY_MODELS['predictor'].predict(features_scaled)[0]
        percentage_pred = max(0, min(100, float(percentage_pred)))  # Clip to 0-100
        
        # Determine eligibility based on criteria
        eligible = bool(eligibility_pred == 1)
        
        # Create human-readable message
        if eligible:
            if percentage_pred >= 80:
                message = f"✓ Highly Eligible ({percentage_pred:.1f}% match)"
            elif percentage_pred >= 60:
                message = f"✓ Eligible ({percentage_pred:.1f}% match)"
            else:
                message = f"~ Marginally Eligible ({percentage_pred:.1f}% match)"
        else:
            message = f"✗ Not Eligible (Only {percentage_pred:.1f}% match)"
        
        # Get model accuracy
        model_accuracy = 58.65  # From training output
        
        return jsonify({
            "eligible": eligible,
            "eligibility_percentage": round(percentage_pred, 2),
            "confidence": round(confidence, 4),
            "message": message,
            "model_accuracy": model_accuracy,
            "student_marks": marks,
            "student_income": income,
            "required_marks": min_marks,
            "max_eligible_income": max_income,
            "marks_difference": round(marks - min_marks, 2),
            "income_difference": round(max_income - income, 2) if max_income > 0 else None
        })
    
    except Exception as e:
        app.logger.error(f"Error in predict_eligibility: {str(e)}")
        return jsonify({
            "error": str(e),
            "eligible": None,
            "eligibility_percentage": None
        }), 400


@app.route("/api/scholarship-names", methods=["GET"])
def scholarship_names():
    """Return list of unique scholarship names for autocomplete."""
    try:
        df = load_scholarships()
        if df.empty:
            return jsonify({"names": []})
        # Get unique scholarship names, sorted
        names = sorted(df["scholarship_name"].astype(str).unique().tolist())
        # Remove placeholder entries
        names = [n for n in names if n and n.lower() not in ["0", "unknown", ""]]
        return jsonify({"names": names})
    except Exception as e:
        app.logger.error(f"Error fetching scholarship names: {e}")
        return jsonify({"names": [], "error": str(e)}), 400


@app.route("/api/check-scholarship-eligibility", methods=["POST"])
def check_scholarship_eligibility():
    """
    Check eligibility for a specific scholarship using provided marks and student's profile.
    
    Input JSON:
    {
        "scholarship_name": string (required),
        "marks": float (required - previous year marks out of 100)
    }
    
    Returns:
    {
        "eligible": boolean,
        "eligibility_percentage": float (0-100),
        "confidence": float (0-1),
        "message": string,
        "scholarship_name": string,
        "student_name": string,
        "student_marks": float,
        "student_income": float,
        "required_marks": float,
        "max_eligible_income": float,
        "marks_difference": float,
        "income_difference": float,
        "scholarship_requirements": {...}
    }
    """
    try:
        # Check if user is authenticated
        user = session.get("user")
        if not user:
            return jsonify({"error": "User not authenticated"}), 401
        
        body = request.get_json() or {}
        scholarship_name = str(body.get("scholarship_name", "")).strip()
        
        if not scholarship_name:
            return jsonify({"error": "scholarship_name is required"}), 400
        
        # Get marks from request body - REQUIRED
        provided_marks = body.get("marks")
        if provided_marks is None:
            return jsonify({"error": "marks is required"}), 400
        
        try:
            student_marks = float(provided_marks)
            if student_marks < 0 or student_marks > 100:
                return jsonify({"error": "Marks must be between 0 and 100"}), 400
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid marks value - must be a number between 0 and 100"}), 400
        
        # Fetch student profile from database
        init_auth_db()
        conn = sqlite3.connect(AUTH_DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            student = conn.execute(
                "SELECT id, name, COALESCE(income, 0) AS income, category, gender, disability, education FROM users WHERE id = ?",
                (user["id"],)
            ).fetchone()
            
            if not student:
                return jsonify({"error": "Student profile not found"}), 404
            
            # Load scholarships CSV
            df = load_scholarships()
            if df.empty:
                return jsonify({"error": "Scholarship database is empty"}), 503
            
            # Find matching scholarship (case-insensitive)
            scholarship_row = df[df["scholarship_name"].str.lower() == scholarship_name.lower()].iloc[0] if any(df["scholarship_name"].str.lower() == scholarship_name.lower()) else None
            
            if scholarship_row is None:
                return jsonify({"error": f"Scholarship '{scholarship_name}' not found"}), 404
            
            # Extract scholarship requirements
            min_marks = float(scholarship_row.get("min_marks", 0) or 0)
            max_income = float(scholarship_row.get("max_income", 0) or 0)
            req_category = str(scholarship_row.get("category", "any")).lower()
            req_gender = str(scholarship_row.get("gender", "any")).lower()
            req_disability = str(scholarship_row.get("disability", "no")).lower()
            req_education = str(scholarship_row.get("education_level", "any")).lower()
            
            # Get student attributes from database
            student_income = float(student["income"] or 0)
            student_category = str(student["category"] or "any").lower()
            student_gender = str(student["gender"] or "any").lower()
            student_disability = str(student["disability"] or "no").lower()
            student_education = str(student["education"] or "any").lower()
            
            # Check if models are loaded
            if not ELIGIBILITY_MODELS['classifier'] or not ELIGIBILITY_MODELS['scaler']:
                return jsonify({
                    "error": "Eligibility models not loaded",
                    "eligible": None,
                    "eligibility_percentage": None
                }), 503

            # If scholarship explicitly requires disability and student is not disabled,
            # do not run the ML model — return immediate Not Eligible (0%).
            # This mirrors the behavior in /api/recommend where disability-only
            # scholarships are skipped for non-disabled users.
            if student_disability == "no" and scholarship_requires_disability_support(req_disability):
                return jsonify({
                    "eligible": False,
                    "eligibility_percentage": 0.0,
                    "confidence": 0.0,
                    "message": "✗ Not Eligible (scholarship requires disability)",
                    "scholarship_name": scholarship_name,
                    "student_name": student["name"],
                    "student_marks": student_marks,
                    "student_income": student_income,
                    "required_marks": min_marks,
                    "max_eligible_income": max_income,
                    "marks_difference": round(student_marks - min_marks, 2),
                    "income_difference": round(max_income - student_income, 2) if max_income > 0 else None,
                    "scholarship_requirements": {
                        "disability": req_disability,
                        "category": req_category,
                        "gender": req_gender,
                        "education_level": req_education
                    }
                }), 200
            
            # Prepare features for the model that match training data
            # The training model uses: marks, min_marks, max_income, category_encoded, gender_encoded, disability_encoded
            feature_vector = pd.DataFrame({
                'marks': [student_marks],
                'min_marks': [min_marks],
                'max_income': [max_income],
                'category_encoded': [hash(student_category) % 256],
                'gender_encoded': [hash(student_gender) % 256],
                'disability_encoded': [hash(student_disability) % 256]
            })

            # Scale features
            features_scaled = ELIGIBILITY_MODELS['scaler'].transform(feature_vector)

            # Predict eligibility
            eligibility_pred = ELIGIBILITY_MODELS['classifier'].predict(features_scaled)[0]
            eligibility_proba = ELIGIBILITY_MODELS['classifier'].predict_proba(features_scaled)[0]
            confidence = float(max(eligibility_proba))
            
            # Calculate eligibility percentage based on marks and other factors
            # If marks are below minimum, lower the percentage
            if student_marks < min_marks:
                percentage_pred = (student_marks / max(min_marks, 1)) * 50  # Max 50% if marks insufficient
            else:
                # Marks are sufficient, calculate based on how much above minimum
                marks_excess = min(student_marks - min_marks, 35)  # Up to 35% bonus from marks
                percentage_pred = 65 + (marks_excess / 35) * 35  # 65% base + marks bonus
            
            # Adjust for income if applicable
            if max_income > 0 and student_income <= max_income:
                percentage_pred += 5
            elif max_income > 0:
                percentage_pred -= 10
            
            percentage_pred = max(0, min(100, float(percentage_pred)))  # Clip to 0-100
            
            # Determine eligibility
            eligible = bool(eligibility_pred == 1)
            
            # Create human-readable message
            if eligible:
                if percentage_pred >= 80:
                    message = f"✓ Highly Eligible ({percentage_pred:.1f}% match)"
                elif percentage_pred >= 60:
                    message = f"✓ Eligible ({percentage_pred:.1f}% match)"
                else:
                    message = f"~ Marginally Eligible ({percentage_pred:.1f}% match)"
            else:
                message = f"✗ Not Eligible (Only {percentage_pred:.1f}% match)"
            
            return jsonify({
                "eligible": eligible,
                "eligibility_percentage": round(percentage_pred, 2),
                "confidence": round(confidence, 4),
                "message": message,
                "scholarship_name": scholarship_name,
                "student_name": student["name"],
                "student_marks": student_marks,
                "student_income": student_income,
                "student_category": student_category,
                "student_disability": student_disability,
                "student_education": student_education,
                "required_marks": min_marks,
                "max_eligible_income": max_income,
                "marks_difference": round(student_marks - min_marks, 2),
                "income_difference": round(max_income - student_income, 2) if max_income > 0 else None,
                "scholarship_requirements": {
                    "category": req_category,
                    "gender": req_gender,
                    "disability": req_disability,
                    "education_level": req_education,
                    "min_marks": min_marks,
                    "max_income": max_income
                }
            })
        
        except Exception as e:
            app.logger.error(f"Error in check_scholarship_eligibility: {str(e)}")
            return jsonify({"error": str(e)}), 400
        finally:
            conn.close()
    
    except Exception as e:
        app.logger.error(f"Error in check_scholarship_eligibility: {str(e)}")
        return jsonify({"error": str(e)}), 400


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
    req_start_time = time.time()
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
        # IMPORTANT: Non-disabled students should NOT get disability-required scholarships.
        # Skip any scholarship that requires disability support if user selected "no"
        if disability == "no" and scholarship_requires_disability_support(r.get("disability") or sch_dis):
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

        # Quick per-scholarship heuristic: produce scholarship-specific probability
        # based on student+scholarship criteria (fast temporary fix until retraining)
        base_score = 0
        chance_level = "Low Chance"

        # Academic match: marks vs scholarship min_marks
        if marks >= min_marks:
            base_score += 30

        # Income constraint
        if max_income == 0 or income <= max_income:
            base_score += 25

        # Category match
        sch_cat = str(r.get("category") or "any").strip().lower()
        if sch_cat == "any" or sch_cat == category:
            base_score += 15

        # Gender match
        sch_gender = str(r.get("gender") or "any").strip().lower()
        if sch_gender == "any" or sch_gender == gender:
            base_score += 10

        # Disability match
        sch_dis = normalize_disability(r.get("disability") or "no")
        if sch_dis == "no" or sch_dis == disability:
            base_score += 10

        # Education match (edu_result computed earlier)
        if edu_result == "full":
            base_score += 10
        elif edu_result == "partial":
            base_score += 5

        # Cap probability at 95 to avoid 100% claims
        success_probability = int(min(base_score, 95))

        if success_probability >= 75:
            chance_level = "High Chance"
        elif success_probability >= 40:
            chance_level = "Medium Chance"
        else:
            chance_level = "Low Chance"

        rows.append({
            "name": name,
            "score": round(final_score, 2),
            "eligible": bool(eligible),
            "link": f"https://scholarships.gov.in/?search={name.replace(' ', '+')}",
            "max_income": max_income,
            "scholarship_amount": amount,
            "success_probability": success_probability,
            "chance_level": chance_level,
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

    # compute request timing and update metrics
    try:
        last_ms = round((time.time() - req_start_time) * 1000.0, 2)
        with METRICS_LOCK:
            METRICS["total_requests"] += 1
            METRICS["last_response_time_ms"] = last_ms
            METRICS["total_response_time_ms"] += last_ms
    except Exception:
        pass

    accuracy = get_model_accuracy_percent()
    total = METRICS.get("total_requests", 0)
    failed = METRICS.get("failed_requests", 0)
    avg_ms = None
    try:
        if total > 0:
            avg_ms = round((METRICS.get("total_response_time_ms", 0.0) / total), 2)
    except Exception:
        avg_ms = None

    error_rate = None
    try:
        if total > 0:
            error_rate = round((failed / total) * 100, 2)
    except Exception:
        error_rate = None

    return jsonify({"results": rows[:50], "metrics": {"accuracy_percent": accuracy, "last_response_time_ms": METRICS.get("last_response_time_ms"), "avg_response_time_ms": avg_ms, "error_rate_percent": error_rate}})


ALLOWED_FRONTEND_FILES = frozenset(
    {
        "index.html",
        "login.html",
        "register.html",
        "eligibility.html",
        "auth.css",
        "script.js",
        "styles.css",
        "welcome.html",
        "welcome.js",
    }
)


@app.route("/php/api_register.php", methods=["POST"])
def api_register_php_compat():
    body = parse_body()
    name = str(body.get("name") or "").strip()
    email = str(body.get("email") or "").strip().lower()
    password = str(body.get("password") or "")

    if not name or not email or not password:
        return jsonify({"success": False, "error": "Missing required fields"}), 400

    init_auth_db()
    conn = sqlite3.connect(AUTH_DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        existing = conn.execute(
            "SELECT id FROM users WHERE name = ? OR email = ? LIMIT 1", (name, email)
        ).fetchone()
        if existing:
            return jsonify({"success": False, "error": "User already exists"}), 409

        password_hash = generate_password_hash(password)
        cur = conn.execute(
            """
            INSERT INTO users (name, email, password_hash, education, category, phone, income, disability, gender)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                email,
                password_hash,
                body.get("education"),
                body.get("category"),
                body.get("phone"),
                float(body.get("income") or 0) if str(body.get("income") or "").strip() else None,
                body.get("disability"),
                body.get("gender"),
            ),
        )
        conn.commit()
        session["user"] = {"id": cur.lastrowid, "name": name, "email": email}
        session.permanent = True
        return jsonify({"success": True, "id": cur.lastrowid})
    except Exception as exc:
        return jsonify({"success": False, "error": "Server error", "message": str(exc)}), 500
    finally:
        conn.close()


@app.route("/php/api_login.php", methods=["POST"])
def api_login_php_compat():
    body = parse_body()
    name_or_email = str(body.get("name") or "").strip()
    password = str(body.get("password") or "")

    if not name_or_email or not password:
        return jsonify({"success": False, "error": "Missing credentials"}), 400

    init_auth_db()
    conn = sqlite3.connect(AUTH_DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        user = conn.execute(
            "SELECT id, name, email, password_hash FROM users WHERE name = ? OR email = ? LIMIT 1",
            (name_or_email, name_or_email.lower()),
        ).fetchone()
        if not user or not check_password_hash(user["password_hash"], password):
            return jsonify({"success": False, "error": "Invalid credentials"}), 401

        session["user"] = {"id": user["id"], "name": user["name"], "email": user["email"]}
        session.permanent = True
        return jsonify({"success": True, "user": session["user"]})
    except Exception as exc:
        return jsonify({"success": False, "error": "Server error", "message": str(exc)}), 500
    finally:
        conn.close()


@app.route("/php/api_me.php", methods=["GET"])
def api_me_php_compat():
    user = session.get("user")
    if user:
        return jsonify({"authenticated": True, "user": user})
    return jsonify({"authenticated": False}), 401


@app.route("/php/logout.php", methods=["GET", "POST"])
def logout_php_compat():
    session.clear()
    return jsonify({"success": True})


@app.route("/")
def home():
    """Serve landing welcome page at root."""
    return send_from_directory(FRONTEND_DIR, "welcome.html")


@app.route("/eligibility")
def eligibility_page():
    """Serve the eligibility predictor page from the Flask app."""
    return send_from_directory(FRONTEND_DIR, "eligibility.html")


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
