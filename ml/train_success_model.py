import pickle
from pathlib import Path
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

ROOT = Path(__file__).resolve().parent
DATASET_PATH = ROOT.parent / "data" / "scholarship_50000_dataset.xlsx"
MODEL_PATH = ROOT / "success_model.pkl"
PREPROCESSOR_PATH = ROOT / "success_preprocessor.pkl"

def load_data():
    df = pd.read_excel(DATASET_PATH)

    df.columns = df.columns.str.strip().str.lower()

    df = df.rename(columns={
        "max_income": "family_income",
        "min_marks": "marks",
        "course": "education_level"
    })

    df["gender"] = df["gender"].astype(str).str.lower()
    df["category"] = df["category"].astype(str).str.lower()
    df["disability"] = df["disability"].astype(str).str.lower()
    df["education_level"] = df["education_level"].astype(str).str.lower()

    # create target label
    df["selected"] = (
        (
            (df["marks"] >= 75)
            & (df["family_income"] <= 600000)
        )
        |
        (
            (df["category"].isin(["sc", "st", "obc", "minority"]))
            & (df["marks"] >= 65)
        )
        |
        (
            (df["disability"] == "yes")
            & (df["marks"] >= 60)
        )
    ).astype(int)

    return df[[
        "family_income",
        "gender",
        "education_level",
        "category",
        "marks",
        "disability",
        "selected"
    ]]

def train():
    df = load_data()

    X = df.drop("selected", axis=1)
    y = df["selected"]

    categorical = ["gender", "education_level", "category", "disability"]
    numerical = ["family_income", "marks"]

    preprocessor = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical),
        ("num", "passthrough", numerical)
    ])

    model = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", RandomForestClassifier(
            n_estimators=100,
            random_state=42
        ))
    ])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        random_state=42
    )

    model.fit(X_train, y_train)

    preds = model.predict(X_test)

    print("Accuracy:", accuracy_score(y_test, preds))
    print(classification_report(y_test, preds))
    print(confusion_matrix(y_test, preds))

    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)

    print("Success model saved.")

if __name__ == "__main__":
    train()