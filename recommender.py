import pandas as pd
import pickle
from sklearn.metrics.pairwise import cosine_similarity


# 1 Load dataset FIRST
data = pd.read_excel("dataset_combined.xlsx")


# 2 Create features
data["features"] = (
    data["Community"].astype(str) + " " +
    data["Gender"].astype(str) + " " +
    data["Education Qualification"].astype(str) + " " +
    data["Disability"].astype(str)
)


# 3 Load trained model
vectorizer = pickle.load(open("model.pkl","rb"))

X = vectorizer.transform(data["features"])


# 4 User input example
student = ["General Male Undergraduate No"]

student_vec = vectorizer.transform(student)

similarity = cosine_similarity(student_vec, X)


# 5 Create results
results = []

for i in range(len(data)):
    score = similarity[0][i] * 100
    results.append(
        (data.iloc[i]["Scholarship Name"], score)
    )


# 6 Filter recommendations
top_matches = sorted(results, key=lambda x: x[1], reverse=True)

THRESHOLD = 70

valid_matches = [
    item for item in top_matches
    if item[1] >= THRESHOLD
]

print("\n--- TOP RECOMMENDATIONS ---")

if len(valid_matches) == 0:
    print("No scholarships available for this profile.")
else:
    for name, score in valid_matches[:10]:
        print(f"{name} | Score: {score:.2f} | ✅ Match")