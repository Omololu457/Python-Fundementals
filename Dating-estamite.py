import json
import os
import pickle
import math
import numpy as np
from datetime import datetime
from sklearn.linear_model import LogisticRegression

# =========================================================
# LOAD PEOPLE DATABASE
# =========================================================

with open("people.json", "r") as f:
    PEOPLE_DB = json.load(f)

FEEDBACK_FILE = "feedback.jsonl"
MODEL_FILE = "model.pkl"

# =========================================================
# YOUR PROFILE
# =========================================================

def calculate_age():
    birth = datetime(2007, 11, 19)
    today = datetime.today()
    age = today.year - birth.year
    if (today.month, today.day) < (birth.month, birth.day):
        age -= 1
    return age


MY_PROFILE = {
    "frc": 75,
    "sps": 55,
    "usv": 70,
    "emotional": 60,
    "adventure": 65,
    "age": calculate_age()
}

MY_PREFS = {
    "skin_tone": 80,
    "softness": 90,
    "facial_harmony": 85,
    "eye_expressiveness": 95,
    "lip_fullness": 85,
    "hair_volume": 75,
    "body_balance": 90,
    "presence": 88
}

# =========================================================
# CORE SCORING FUNCTIONS
# =========================================================

def similarity(a, b):
    return 100 - abs(a - b)

def polarity(a, b):
    diff = abs(a - b)
    return max(0, 100 - (diff - 40) ** 2 / 20)


def aesthetic_score(me_prefs, them):
    if "aesthetic" not in them:
        return 50

    weights = {
        "skin_tone": 0.15,
        "softness": 0.20,
        "facial_harmony": 0.15,
        "eye_expressiveness": 0.15,
        "lip_fullness": 0.10,
        "hair_volume": 0.10,
        "body_balance": 0.10,
        "presence": 0.05
    }

    score = 0
    for k, w in weights.items():
        score += (100 - abs(me_prefs[k] - them["aesthetic"].get(k, 50))) * w

    return score


def lifestyle_penalty(me, them):
    penalty = 0

    if abs(me["age"] - them["age"]) > 7:
        penalty += 10

    if them.get("lifestyle_conflict", False):
        penalty += 15

    if them.get("value_mismatch", 0) > 50:
        penalty += 20

    return penalty

# =========================================================
# FEATURE VECTOR (THIS IS WHAT THE ML MODEL LEARNS FROM)
# =========================================================

def build_features(me, them):
    return [
        similarity(me["frc"], them["frc"]),
        similarity(me["emotional"], them["emotional"]),
        polarity(me["usv"], them["usv"]),
        polarity(me["adventure"], them["adventure"]),
        aesthetic_score(MY_PREFS, them),
        abs(me["age"] - them["age"]),
        lifestyle_penalty(me, them),
        them.get("usv", 50) / 100,
        them.get("sps", 50) / 100
    ]

# =========================================================
# MODEL LOADING / TRAINING
# =========================================================

def load_model():
    if os.path.exists(MODEL_FILE):
        with open(MODEL_FILE, "rb") as f:
            return pickle.load(f)
    return LogisticRegression()


def train_model():
    model = load_model()

    if not os.path.exists(FEEDBACK_FILE):
        return model

    X, y = [], []

    with open(FEEDBACK_FILE, "r") as f:
        for line in f:
            data = json.loads(line)
            X.append(data["features"])
            y.append(data["label"])

    if len(X) > 5:
        model.fit(X, y)
        with open(MODEL_FILE, "wb") as f:
            pickle.dump(model, f)

    return model


def predict_score(features):
    model = train_model()
    features = np.array(features).reshape(1, -1)
    return model.predict_proba(features)[0][1]

# =========================================================
# FEEDBACK SYSTEM (SELF-TUNING LOOP)
# =========================================================

def log_feedback(features, label):
    with open(FEEDBACK_FILE, "a") as f:
        f.write(json.dumps({
            "features": features,
            "label": label
        }) + "\n")

# =========================================================
# MAIN ANALYSIS FUNCTION
# =========================================================

def analyze_person(name):
    if name not in PEOPLE_DB:
        return None

    them = PEOPLE_DB[name]
    features = build_features(MY_PROFILE, them)

    score = predict_score(features) * 100

    return {
        "name": name,
        "age_you": MY_PROFILE["age"],
        "age_them": them["age"],
        "compatibility_score": round(score, 2),
        "features": features
    }

# =========================================================
# CLI INTERFACE
# =========================================================

def main():
    print("\n=== MATCH ENGINE ===\n")

    while True:
        cmd = input("\nEnter command (match / feedback / exit): ").strip().lower()

        if cmd == "exit":
            break

        elif cmd == "match":
            name = input("Enter name: ")

            result = analyze_person(name)

            if not result:
                print("Person not found.")
                continue

            print("\n--- RESULT ---")
            print(f"Name: {result['name']}")
            print(f"Age You: {result['age_you']}")
            print(f"Age Them: {result['age_them']}")
            print(f"Compatibility Score: {result['compatibility_score']}%")

            # store last features for feedback step
            global LAST_FEATURES
            LAST_FEATURES = result["features"]

        elif cmd == "feedback":
            if "LAST_FEATURES" not in globals():
                print("Run a match first.")
                continue

            label = int(input("Was it a good match? (1=yes / 0=no): "))
            log_feedback(LAST_FEATURES, label)

            print("Feedback saved. Model will improve.")

        else:
            print("Unknown command.")

# =========================================================

if __name__ == "__main__":
    main()