import os
import pandas as pd
import joblib

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestClassifier


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CSV_PATH = os.path.join(
    BASE_DIR,
    "Data",
    "Complaint.csv"
)

MODEL_PATH = os.path.join(
    BASE_DIR,
    "risk_model.pkl"
)


# ============================================================
# LOAD DATASET
# ============================================================

print("\n==========================================")
print("CYBERCRIME ML MODEL TRAINING")
print("==========================================")

print("\nReading dataset...")

try:

    data = pd.read_csv(
        CSV_PATH,
        encoding="utf-8",
        on_bad_lines="skip"
    )

except Exception as e:

    print("\nERROR READING CSV:")
    print(e)
    exit()


# ============================================================
# CLEAN COLUMN NAMES
# ============================================================

data.columns = (
    data.columns
    .str.strip()
    .str.lower()
)


print("\nColumns found:")
print(list(data.columns))


# ============================================================
# CHECK REQUIRED COLUMNS
# ============================================================

required_columns = [
    "complaint_id",
    "amount",
    "district",
    "withdrawal_location",
    "risk"
]

missing_columns = [
    column
    for column in required_columns
    if column not in data.columns
]


if missing_columns:

    print("\n==========================================")
    print("CSV COLUMN ERROR")
    print("==========================================")

    print("Missing columns:")
    print(missing_columns)

    print("\nYour CSV must contain:")
    print(required_columns)

    exit()


# ============================================================
# CLEAN DATA
# ============================================================

data["amount"] = pd.to_numeric(
    data["amount"],
    errors="coerce"
)

data["district"] = (
    data["district"]
    .astype(str)
    .str.strip()
)

data["withdrawal_location"] = (
    data["withdrawal_location"]
    .astype(str)
    .str.strip()
)

data["risk"] = (
    data["risk"]
    .astype(str)
    .str.strip()
)


# Remove invalid records

data = data.dropna(
    subset=[
        "amount",
        "district",
        "withdrawal_location",
        "risk"
    ]
)


print("\n==========================================")
print("DATASET INFORMATION")
print("==========================================")

print("Valid records:", len(data))

print("\nFirst 10 records:")

print(
    data[
        [
            "complaint_id",
            "amount",
            "district",
            "withdrawal_location",
            "risk"
        ]
    ].head(10)
)


# ============================================================
# CHECK DATA
# ============================================================

if len(data) < 2:

    print("\nNot enough records for machine learning.")

    exit()


# ============================================================
# FEATURES
# ============================================================

# The model uses:
#
# Transaction Amount
# District selected automatically from map
#
# Target:
# Withdrawal Location

X = data[
    [
        "amount",
        "district"
    ]
]

y_location = data[
    "withdrawal_location"
]


# ============================================================
# PREPROCESSING
# ============================================================

preprocessor = ColumnTransformer(

    transformers=[

        (
            "district",
            OneHotEncoder(
                handle_unknown="ignore"
            ),
            ["district"]
        )

    ],

    remainder="passthrough"
)


# ============================================================
# LOCATION MODEL
# ============================================================

location_model = Pipeline(

    steps=[

        (
            "preprocessor",
            preprocessor
        ),

        (
            "classifier",
            RandomForestClassifier(
                n_estimators=200,
                random_state=42
            )
        )

    ]

)


print("\nTraining withdrawal-location model...")

location_model.fit(
    X,
    y_location
)


# ============================================================
# RISK MODEL
# ============================================================

y_risk = data["risk"]


risk_preprocessor = ColumnTransformer(

    transformers=[

        (
            "district",
            OneHotEncoder(
                handle_unknown="ignore"
            ),
            ["district"]
        )

    ],

    remainder="passthrough"
)


risk_model = Pipeline(

    steps=[

        (
            "preprocessor",
            risk_preprocessor
        ),

        (
            "classifier",
            RandomForestClassifier(
                n_estimators=200,
                random_state=42
            )
        )

    ]

)


print("Training risk model...")

risk_model.fit(
    X,
    y_risk
)


# ============================================================
# SAVE BOTH MODELS
# ============================================================

model_data = {

    "location_model": location_model,

    "risk_model": risk_model

}


joblib.dump(
    model_data,
    MODEL_PATH
)


# ============================================================
# SUCCESS
# ============================================================

print("\n==========================================")
print("ML MODEL TRAINED SUCCESSFULLY")
print("==========================================")

print(
    "Training records:",
    len(data)
)

print(
    "Model saved as:"
)

print(
    MODEL_PATH
)

print("\n==========================================")