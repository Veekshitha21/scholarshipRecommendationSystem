"""
Train an eligibility ranking model from scholarship data.
This model learns which scholarships are most likely to be recommended
for different student profiles (income, marks, category, disability, gender).
"""

import pickle
from pathlib import Path

import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
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


def rule_based_eligible(user, scholarship):
    """
    Heuristic eligibility check. Returns True if student likely eligible for scholarship.
    Used for labeling training data.
    """
    # Marks check
    if user['marks'] < scholarship['min_marks']:
        return False
    
    # Income check
    if scholarship['max_income'] > 0 and user['income'] > scholarship['max_income']:
        return False
    
    # Category match
    if scholarship['category'] not in ['any', 'open']:
        if scholarship['category'] != user['category']:
            return False
    
    # Gender match
    if scholarship['gender'] not in ['any', 'both']:
        if scholarship['gender'] != user['gender']:
            return False
    
    # Disability match
    if scholarship['disability'] not in ['no', 'any']:
        if scholarship['disability'] != user['disability']:
            return False
    
    return True


def build_training_examples(df, samples_per_sch=6):
    """
    Generate synthetic student profiles from scholarship criteria.
    Returns X (feature vectors) and y (labels) for training.
    """
    X = []
    y = []
    
    for _, scholarship in df.iterrows():
        min_marks = float(scholarship['min_marks'])
        max_income = float(scholarship['max_income'])
        
        # Generate samples_per_sch examples per scholarship
        for _ in range(samples_per_sch):
            # Eligible examples: marks above min, income below max
            marks = np.random.uniform(min_marks, 100)
            income = np.random.uniform(0, max(max_income * 1.5, 100000)) if max_income > 0 else np.random.uniform(0, 500000)
            
            user = {
                'marks': marks,
                'income': income,
                'category': np.random.choice(['general', 'obc', 'sc', 'st']),
                'gender': np.random.choice(['male', 'female']),
                'disability': np.random.choice(['no', 'yes'])
            }
            
            # Build 5-feature vector
            marks_diff = user['marks'] - min_marks
            income_margin = max(max_income - user['income'], 0) if max_income > 0 else 0
            cat_match = 1 if scholarship['category'] in ['any', 'open'] or scholarship['category'] == user['category'] else 0
            gen_match = 1 if scholarship['gender'] in ['any', 'both'] or scholarship['gender'] == user['gender'] else 0
            dis_match = 1 if scholarship['disability'] in ['no', 'any'] or scholarship['disability'] == user['disability'] else 0
            
            features = [marks_diff, income_margin, cat_match, gen_match, dis_match]
            label = 1 if rule_based_eligible(user, scholarship) else 0
            
            X.append(features)
            y.append(label)
    
    return np.array(X), np.array(y)


def train_and_save():
    """Load data, train ML classifier, and save eligibility model."""
    print("Loading and preparing scholarship data...")
    df = load_and_prepare_data()

    print(f"Loaded {len(df)} scholarships")
    print("\nScholarships loaded:")
    for idx, row in df.iterrows():
        print(f"  {idx+1}. {row['scholarship_name'][:60]} - Income: ₹{row['max_income']:,.0f}, Marks: {row['min_marks']:.0f}")

    print("\nGenerating training data from scholarships...")
    X, y = build_training_examples(df, samples_per_sch=6)
    print(f"Generated {len(X)} training examples")
    print(f"  Eligible: {(y == 1).sum()}, Not Eligible: {(y == 0).sum()}")
    
    # Train logistic regression
    print("\nTraining Logistic Regression classifier...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    clf = LogisticRegression(max_iter=200, class_weight='balanced', random_state=42)
    clf.fit(X_train_scaled, y_train)
    
    train_acc = clf.score(X_train_scaled, y_train)
    test_acc = clf.score(X_test_scaled, y_test)
    
    print(f"  Train accuracy: {train_acc:.4f}")
    print(f"  Test accuracy: {test_acc:.4f}")
    
    # Save model and scaler
    model_data = {
        'clf': clf,
        'scaler': scaler
    }

    print(f"\nSaving ML model to: {MODEL_PATH}")
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model_data, f)

    print(f"\n✅ Model trained successfully!")
    print(f"   Classifier trained on {len(X)} examples")
    print(f"   Test accuracy: {test_acc:.2%}")
    print(f"   Model saved: {MODEL_PATH}")


if __name__ == "__main__":
    train_and_save()
