from datasets import load_dataset
import pandas as pd
import re

ds = load_dataset("NetraVerse/indian-govt-scholarships")
df = ds["train"].to_pandas()


# Extract income like "8 lakh"
def extract_income(text):
    m = re.search(r'(\d+)\s*lakh', str(text).lower())
    if m:
        return int(m.group(1)) * 100000
    return None


# Detect female-only
def extract_gender(text):
    t = str(text).lower()
    if "only female students are eligible" in t:
        return "Female"
    return "Any"


# Detect education level
def extract_level(text):
    t = str(text).lower()
    if "diploma" in t:
        return "Diploma"
    if "degree" in t:
        return "UG"
    if "post-graduate" in t:
        return "PG"
    return "Any"


# Extract amount like Rs 50,000
def extract_amount(text):

    t = str(text).lower()

    # specifically find amounts like Rs 50,000
    m = re.search(r'rs\.?\s*([0-9,]{4,})', t)

    if m:
        try:
            return int(m.group(1).replace(",", ""))
        except:
            return None

    return None

# Build structured fields
df["max_income"] = df["text"].apply(extract_income)
df["gender"] = df["text"].apply(extract_gender)
df["education_level"] = df["text"].apply(extract_level)
df["scholarship_amount"] = df["text"].apply(extract_amount)

# rename
df["scholarship_name"] = df["label"]

# save structured dataset
final_df = df[[
    "scholarship_name",
    "max_income",
    "gender",
    "education_level",
    "scholarship_amount"
]]

print(final_df)

final_df.to_csv("structured_real_scholarships.csv", index=False)