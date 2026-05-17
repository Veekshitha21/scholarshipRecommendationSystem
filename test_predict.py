import requests
url='http://127.0.0.1:5000/api/predict-eligibility'
payload={'marks':85,'income':200000,'min_marks':70,'max_income':300000,'category':'any','gender':'any','disability':'no','course':'ug'}
try:
    r=requests.post(url,json=payload,timeout=20)
    print('STATUS',r.status_code)
    try:
        print(r.json())
    except Exception:
        print(r.text)
except Exception as e:
    print('ERROR',e)
