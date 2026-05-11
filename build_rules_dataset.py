from datasets import load_dataset
import pandas as pd

ds = load_dataset("NetraVerse/indian-govt-scholarships")

df = ds["train"].to_pandas()

print(df.head())

df.to_csv("real_scholarships_raw.csv", index=False)