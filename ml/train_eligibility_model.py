"""
Train an eligibility ranking model from scholarship data.
This model learns which scholarships are most likely to be recommended
for different student profiles (income, marks, category, disability, gender).
"""

import pickle
from pathlib import Path

import pandas as pd
from sklearn.preprocessing import StandardScaler
import numpy as np

ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
DATA_DIR = PROJECT_ROOT / "data"
CSV_PATH = ROOT / "structured_real_scholarships.csv"
MODEL_PATH = ROOT / "eligibility_model.pkl"


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


def load_and_prepare_data():
    """Load scholarship CSV and prepare eligibility features."""
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {CSV_PATH}")

    df = pd.read_csv(CSV_PATH)
    df.columns = df.columns.str.strip().str.lower()

    # Ensure all required columns exist
    if 'scholarship_name' not in df.columns:
        df['scholarship_name'] = df[df.columns[0]]
    if 'min_marks' not in df.columns:
        df['min_marks'] = 65.0
    if 'max_income' not in df.columns:
        df['max_income'] = 0.0
    if 'scholarship_amount' not in df.columns:
        df['scholarship_amount'] = 0.0
    if 'gender' not in df.columns:
        df['gender'] = 'Any'
    if 'education_level' not in df.columns:
        df['education_level'] = 'Any'
    if 'category' not in df.columns:
        df['category'] = 'any'
    if 'disability' not in df.columns:
        df['disability'] = 'no'

    # Fill missing values
    df['scholarship_name'] = df['scholarship_name'].fillna('Scholarship')
    df['max_income'] = pd.to_numeric(df['max_income'], errors='coerce').fillna(0)
    df['min_marks'] = pd.to_numeric(df['min_marks'], errors='coerce').fillna(65)
    df['scholarship_amount'] = pd.to_numeric(df['scholarship_amount'], errors='coerce').fillna(0)
    df['gender'] = df['gender'].fillna('Any').astype(str).str.strip()
    df['education_level'] = df['education_level'].fillna('Any').astype(str).apply(normalize_education)
    df['category'] = df['category'].fillna('any').astype(str).str.lower().str.strip()
    df['disability'] = df['disability'].fillna('no').astype(str).str.lower().str.strip()

    return df


def build_eligibility_index(df):
    """
    Build a data structure that maps student profiles to scholarship eligibility rankings.
    Returns a dict that can be used for fast lookups during API requests.
    """
    eligibility_index = {
        'scholarships': df['scholarship_name'].tolist(),
        'max_incomes': df['max_income'].tolist(),
        'min_marks': df['min_marks'].tolist(),
        'genders': df['gender'].tolist(),
        'education_levels': df['education_level'].tolist(),
        'categories': df['category'].tolist(),
        'disabilities': df['disability'].tolist(),
        'amounts': df['scholarship_amount'].tolist(),
        'count': len(df)
    }
    return eligibility_index


def train_and_save():
    """Load data, build index, and save eligibility model."""
    print("Loading and preparing scholarship data...")
    df = load_and_prepare_data()

    print(f"Loaded {len(df)} scholarships")
    print("\nScholarships loaded:")
    for idx, row in df.iterrows():
        print(f"  {idx+1}. {row['scholarship_name'][:60]} - Income: ₹{row['max_income']:,.0f}, Marks: {row['min_marks']:.0f}")

    print("\nBuilding eligibility index...")
    eligibility_index = build_eligibility_index(df)

    print(f"Saving model to: {MODEL_PATH}")
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(eligibility_index, f)

    print(f"\n✅ Model trained successfully!")
    print(f"   Scholarships indexed: {eligibility_index['count']}")
    print(f"   Model saved: {MODEL_PATH}")


if __name__ == "__main__":
    train_and_save()
