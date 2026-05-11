from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import math

app = Flask(__name__)
CORS(app)

CSV_PATH = 'structured_real_scholarships.csv'


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
    category = str(body.get('category') or '').strip().lower()
    gender = str(body.get('gender') or '').strip().lower()
    disability = str(body.get('disability') or '').strip().lower()
    education = str(body.get('education_level') or '').strip().lower()

    df = load_scholarships()

    rows = []
    for _, r in df.iterrows():
        # coerce values
        name = str(r.get('scholarship_name') or 'Scholarship')
        try:
            min_marks = float(r.get('min_marks') or r.get('min_marks', 0) or 0)
        except Exception:
            # try infer later
            min_marks = 65.0
        try:
            max_income = float(r.get('max_income') or 0)
        except Exception:
            max_income = 0.0

        score = 0.0
        eligible = True

        # marks
        if marks >= min_marks:
            score += 30
        elif marks >= min_marks - 10:
            score += 20
        else:
            eligible = False

        # income
        if not max_income or income <= max_income:
            score += 30
        else:
            score += (max_income / (income + 1.0)) * 30.0
            eligible = False

        # category
        sch_cat = str(r.get('category') or 'any').lower()
        if sch_cat == 'any' or category in sch_cat:
            score += 15
        else:
            eligible = False

        # gender
        sch_gender = str(r.get('gender') or 'any').lower()
        if sch_gender == 'any' or sch_gender == gender:
            score += 10

        # disability
        sch_dis = str(r.get('disability') or 'no').lower()
        if sch_dis == 'no' or sch_dis == disability:
            score += 5
        else:
            eligible = False

        # education
        row_level = str(r.get('education_level') or '').lower()
        if row_level == 'any' or row_level == education or education == 'any':
            score += 10
        else:
            if (row_level == 'ug' and education == 'diploma') or (row_level == 'diploma' and education == 'ug'):
                score += 5

        rows.append({
            'name': name,
            'score': round(score, 2),
            'eligible': bool(eligible),
            'link': f"https://scholarships.gov.in/?search={name.replace(' ', '+')}",
            'max_income': max_income,
            'scholarship_amount': r.get('scholarship_amount') if 'scholarship_amount' in r else None,
            'education_level': row_level
        })

    rows = sorted(rows, key=lambda x: x['score'], reverse=True)

    return jsonify({'results': rows[:50]})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
