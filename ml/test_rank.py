import pickle
from sklearn.metrics.pairwise import cosine_similarity

with open("rank_model.pkl", "rb") as f:
    model = pickle.load(f)

vectorizer = model["vectorizer"]
X = model["X"]
names = model["names"]

student_profile = "cat_obc gen_female edu_ug dis_no inc_low state_karnataka"

query = vectorizer.transform([student_profile])

scores = cosine_similarity(query, X)[0]

top_indices = scores.argsort()[::-1][:10]

print("Top Recommended Scholarships:")
for idx in top_indices:
    print(names[idx], "-", scores[idx])