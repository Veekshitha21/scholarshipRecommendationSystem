import pandas as pd

# -------------------------------
# 1. LOAD DATASET
# -------------------------------
df = pd.read_excel("scholarship_50000_dataset.xlsx")
df = df.drop_duplicates(subset=["name"])

print("Dataset loaded successfully!")
# remove numeric ids from names
df["name"] = df["name"].str.replace(r"\s+\d+$", "", regex=True)

# now remove duplicates
df = df.drop_duplicates(subset=["name"])
# -------------------------------
# 2. CLEAN DATA
# -------------------------------
df.columns = df.columns.str.strip().str.lower()

# Convert numeric columns
df['min_marks'] = pd.to_numeric(df['min_marks'], errors='coerce').fillna(0)
df['max_income'] = pd.to_numeric(df['max_income'], errors='coerce').fillna(0)

# -------------------------------
# 3. USER INPUT
# -------------------------------
print("\n--- USER INPUT ---")

user_marks = float(input("Enter your percentage: "))
user_income = float(input("Enter your income: "))
user_category = input("Enter your category (General/OBC/SC/ST/Minority): ").strip().lower()
user_gender = input("Enter your gender (Male/Female): ").strip().lower()
user_disability = input("Disability (Yes/No): ").strip().lower()

# -------------------------------
# 4. RECOMMENDATION ENGINE
# -------------------------------
results = []

for _, row in df.iterrows():

    score = 0
    eligible = True

    # ---- MARKS ----
    if user_marks >= row['min_marks']:
        score += 30

    elif user_marks >= row['min_marks'] - 10:
        # allow up to 10% relaxation for near matches
        score += 20

    else:
        eligible = False

    # ---- INCOME ----
    if user_income <= row['max_income']:
        score += 30
    else:
        score += (row['max_income'] / (user_income + 1)) * 30
        eligible = False

   # ---- CATEGORY ----
    sch_cat = str(row['category']).lower()

    if (
        user_category in sch_cat
        or sch_cat == "any"
    ):
        score += 15
    else:
        eligible = False

    # ---- GENDER ----
    if row['gender'].lower() == user_gender or row['gender'].lower() == "any":
        score += 10

    # ---- DISABILITY ----
    sch_dis = str(row['disability']).lower()

    if sch_dis == "no":
        score += 5   # open to all

    elif sch_dis == user_disability:
        score += 5

    else:
        eligible = False

    results.append((row['name'], score, eligible))

# -------------------------------
# 5. SORT RESULTS
# -------------------------------
results = sorted(results, key=lambda x: x[1], reverse=True)

# -------------------------------
# 6. OUTPUT
# -------------------------------
print("\n--- TOP RECOMMENDATIONS ---\n")

# keep only fully eligible scholarships
eligible_results = [
    item for item in results
    if item[2] == True
]

if len(eligible_results) == 0:
    print("No scholarships available for this profile.")

else:
    count = 0

    for name, score, eligible in eligible_results:
        print(f"{name} | Score: {round(score,2)} | ✅ Eligible")

        count += 1
        if count == 10:
            break

    pd.DataFrame(
        eligible_results[:10],
        columns=["Scholarship","Score","Eligible"]
    ).to_csv("recommendations.csv", index=False)