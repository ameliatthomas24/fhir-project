import pickle
import pandas as pd
from pathlib import Path
from pydantic import BaseModel
import os


# Feature names 
CATEGORICAL_COLUMNS = ["gender", "smoking_history"]
NUMERICAL_COLUMNS   = ["age", "bmi", "HbA1c_level", "blood_glucose_level",
                       "hypertension", "heart_disease"]

# Schemas 
class PatientProfile(BaseModel):
    gender: str                     
    smoking_history: str          
    age: float
    bmi: float
    HbA1c_level: float
    blood_glucose_level: float
    hypertension: int               
    heart_disease: int               

class DiabetesPrediction(BaseModel):
    risk_score: float                
    risk_label: str                 
    top_factors: list[dict]        

# Inference 
# Score a single patient and return their diabetes risk
def generate_risk_assessment(patient_profile: PatientProfile, pipeline) -> DiabetesPrediction:
    patient_input_data = pd.DataFrame([{
        "gender":              patient_profile.gender,
        "smoking_history":     patient_profile.smoking_history,
        "age":                 patient_profile.age,
        "bmi":                 patient_profile.bmi,
        "HbA1c_level":         patient_profile.HbA1c_level,
        "blood_glucose_level": patient_profile.blood_glucose_level,
        "hypertension":        patient_profile.hypertension,
        "heart_disease":       patient_profile.heart_disease,
    }])

    # Risk probability
    probability_score = float(pipeline.predict_proba(patient_input_data)[0][1])

    # Thresholds tuned for a managed-diabetes patient population where HbA1c
    # values cluster between 5.3-7.6% and the model outputs skewed probabilities.
    if probability_score < 0.15:
        risk_level = "Low"
    elif probability_score < 0.45:
        risk_level = "Moderate"
    else:
        risk_level = "High"

    # Per-patient feature contributions
    feature_processor = pipeline.named_steps["pre"]
    trained_classifier = pipeline.named_steps["clf"]

    processed_categorical_names = list(
        feature_processor.named_transformers_["cat"]
        .get_feature_names_out(CATEGORICAL_COLUMNS)
    )
    combined_feature_names = processed_categorical_names + NUMERICAL_COLUMNS

    # Weight this patient's preprocessed values by global importances
    preprocessed_values = feature_processor.transform(patient_input_data)[0]
    feature_importances = trained_classifier.feature_importances_
    contributions = [abs(float(v) * float(w)) for v, w in zip(preprocessed_values, feature_importances)]
    total = sum(contributions) or 1.0

    top_series = (
        pd.Series(contributions, index=combined_feature_names)
        .sort_values(ascending=False)
        .head(5)
    )
    key_risk_drivers = [
        {"feature": name, "importance": round(val / total, 4)}
        for name, val in top_series.items()
    ]

    return DiabetesPrediction(
        risk_score=round(probability_score, 4),
        risk_label=risk_level,
        top_factors=key_risk_drivers,
    )

if __name__ == "__main__":
    test_patient = PatientProfile(
        gender="Female",
        smoking_history="never",
        age=55.0,
        bmi=29.5,
        HbA1c_level=6.8,
        blood_glucose_level=140.0,
        hypertension=1,
        heart_disease=0
    )

    result = generate_risk_assessment(test_patient)

    print(f"Risk Score: {result.risk_score}")
    print(f"Risk Label: {result.risk_label}")
    print("Top Risk Factors:")
    for factor in result.top_factors:
        print(f"  {factor['feature']:<30} {factor['importance']:.4f}")