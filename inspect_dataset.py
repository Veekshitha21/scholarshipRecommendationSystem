from datasets import load_dataset

ds = load_dataset("NetraVerse/indian-govt-scholarships")

print(ds)
print(ds["train"][0])