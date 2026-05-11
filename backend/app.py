from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd
from pathlib import Path

app = Flask(__name__)
CORS(app)

CSV_PATH = Path(__file__).resolve().parent.parent / 'ml' / 'structured_real_scholarships.csv'
MODEL_PATH = Path(__file__).resolve().parent.parent / 'ml' / 'eligibility_model.pkl'
FRONTEND_DIR = Path(__file__).resolve().parent.parent / 'frontend'


def normalize_education(value):
    v = str(value or '').strip().lower()
    if not v:
        return 'any'
    if v in {'any', 'all'}:
        return 'any'
    if v in {'degree', 'undergraduate', 'bachelor', 'bachelors', 'ug'}:
        return 'ug'
    if v in {'masters', 'master', 'postgraduate', 'pg'}:
        return 'pg'
    if v in {'diploma', 'polytechnic'}:
        return 'diploma'
    if v in {'1-10th', '10th', 'school', 'secondary', 'high school'}:
        return 'school'
    if v in {'pu', 'puc', 'pre-university', 'pre university', '11th', '12th'}:
        return 'pu'
    return v


def normalize_class(value):
    v = str(value or '').strip().lower()
    if not v:
        return 'any'
    if v in {'any', 'all'}:
        return 'any'
    if v in {'8', '9', '10', 'school'}:
        return 'school'
    if v in {'11', '12', 'pu', 'puc'}:
        return 'pu'
    if v in {'diploma'}:
        return 'diploma'
    if v in {'ug', 'degree', 'undergraduate'}:
        return 'ug'
    if v in {'pg', 'masters', 'master', 'postgraduate'}:
        return 'pg'
    return v


def class_to_education(class_level):
    c = normalize_class(class_level)
    if c in {'school', 'pu', 'diploma', 'ug', 'pg'}:
        return c
    return 'any'


def education_match(row_level, user_level):
    row_norm = normalize_education(row_level)
    user_norm = normalize_education(user_level)

    if row_norm == 'any' or user_norm == 'any':
        return 'full'
    if row_norm == user_norm:
        return 'full'

    near_pairs = {
        ('ug', 'diploma'),
        ('diploma', 'ug'),
        ('pu', 'school'),
        ('school', 'pu')
    }
    if (row_norm, user_norm) in near_pairs:
        return 'partial'

    return 'none'


def load_scholarships():
    try:
        df = pd.read_csv(CSV_PATH)
        # normalize columns
        df.columns = df.columns.str.strip().str.lower()
        # ensure fields exist
        if 'scholarship_name' not in df.columns:
            df.rename(columns={df.columns[0]: 'scholarship_name'}, inplace=True)
        return df
    except Exception:
        return pd.DataFrame([
            {
                'scholarship_name': 'National Merit Grant',
                'max_income': 800000,
                'scholarship_amount': 50000,
                'gender': 'Any',
                'education_level': 'UG',
                'category': 'any',
                'min_marks': 70,
                'disability': 'no'
            },
            {
                'scholarship_name': 'STEM Future Fellowship',
                'max_income': 600000,
                'scholarship_amount': 75000,
                'gender': 'Any',
                'education_level': 'PG',
                'category': 'any',
                'min_marks': 80,
                'disability': 'no'
            }
        ])


@app.route('/api/recommend', methods=['POST'])
def recommend():
    body = request.get_json() or {}
    marks = float(body.get('marks') or 0)
    income = float(body.get('income') or 0)
    class_level = normalize_class(body.get('class_level') or 'any')
    category = str(body.get('category') or '').strip().lower()
    gender = str(body.get('gender') or '').strip().lower()
    disability = str(body.get('disability') or '').strip().lower()
    minority = str(body.get('minority') or 'any').strip().lower()
    state = str(body.get('state') or 'any').strip().lower()
    education = normalize_education(body.get('education_level') or class_to_education(class_level))

    df = load_scholarships()

    # Pure eligibility-based scoring (no ML tricks)
    rows = []
    for _, r in df.iterrows():
        # coerce values
        name = str(r.get('scholarship_name') or 'Scholarship')
        try:
            min_marks = float(r.get('min_marks') or 65.0)
        except Exception:
            min_marks = 65.0
        try:
            max_income = float(r.get('max_income') or 0)
        except Exception:
            max_income = 0.0

        score = 0.0
        eligible = True

        # marks (40 points)
        if marks >= min_marks:
            score += 40
        elif marks >= min_marks - 10:
            score += 25
        else:
            eligible = False

        # income (30 points)
        if not max_income or income <= max_income:
            score += 30
        else:
            score += (max_income / (income + 1.0)) * 30.0
            eligible = False

        # category (15 points)
        sch_cat = str(r.get('category') or 'any').lower()
        if sch_cat == 'any' or category in sch_cat:
            score += 15
        else:
            eligible = False

        # gender (10 points)
        sch_gender = str(r.get('gender') or 'any').lower()
        if sch_gender == 'any' or sch_gender == gender:
            score += 10

        # disability (5 points)
        sch_dis = str(r.get('disability') or 'no').lower()
        if sch_dis == 'no' or sch_dis == disability:
            score += 5
        else:
            eligible = False

        # education (10 points)
        row_level_raw = str(r.get('education_level') or '')
        row_level = normalize_education(row_level_raw)
        edu_result = education_match(row_level, education)
        if edu_result == 'full':
            score += 10
        else:
            if edu_result == 'partial':
                score += 5

        rows.append({
            'name': name,
            'score': round(score, 2),
            'eligible': bool(eligible),
            'link': f"https://scholarships.gov.in/?search={name.replace(' ', '+')}",
            'max_income': max_income,
            'scholarship_amount': r.get('scholarship_amount') if 'scholarship_amount' in r else None,
            'education_level': row_level,
            'gender': sch_gender,
            'category': sch_cat,
            'disability': sch_dis
        })

    # Sort: eligible first, then by score descending
    rows = sorted(rows, key=lambda x: (not x['eligible'], -x['score']))

    return jsonify({'results': rows[:50]})


@app.route('/')
def home():
    return send_from_directory(FRONTEND_DIR, 'index.html')


@app.route('/<path:filename>')
def frontend_files(filename):
    if filename in {'index.html', 'script.js', 'styles.css'}:
        return send_from_directory(FRONTEND_DIR, filename)
    return jsonify({'error': 'Not found'}), 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
