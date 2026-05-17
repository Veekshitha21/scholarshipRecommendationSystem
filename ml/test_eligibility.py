import pickle

with open("eligibility_model.pkl", "rb") as f:
    model = pickle.load(f)

student = {
    "income": 250000,
    "marks": 85,
    "gender": "female",
    "education_level": "ug",
    "category": "obc",
    "disability": "no"
}

matches = []

for i in range(model["count"]):
    if (
        student["income"] <= model["max_incomes"][i]
        and student["marks"] >= model["min_marks"][i]
    ):
        matches.append(model["scholarships"][i])

print("Eligible Scholarships:")
print(matches[:10])