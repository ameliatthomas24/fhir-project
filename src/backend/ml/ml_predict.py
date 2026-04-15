import pickle
import pandas as pd
from pathlib import Path
from pydantic import BaseModel

MODEL_FILE_PATH = os.path.join("/app", "ml", "model.pkl")

# Load model 
try:
    with open(MODEL_FILE_PATH, "rb") as model_file:
        prediction_pipeline = pickle.load(model_file)
except FileNotFoundError:
    prediction_pipeline = None
    print(f"Model file missing")
except Exception as error:
    prediction_pipeline = None
    print(f"Failed to load model")

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
def generate_risk_assessment(patient_profile: PatientProfile) -> DiabetesPrediction:
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
    probability_score = float(prediction_pipeline.predict_proba(patient_input_data)[0][1])

    # Risk label
    if probability_score < 0.3:
        risk_level = "Low"
    elif probability_score < 0.6:
        risk_level = "Moderate"
    else:
        risk_level = "High"

    # Top features 
    feature_processor = prediction_pipeline.named_steps["pre"]
    trained_classifier = prediction_pipeline.named_steps["clf"]

    processed_categorical_names = list(
        feature_processor.named_transformers_["cat"]
        .get_feature_names_out(CATEGORICAL_COLUMNS)
    )
    combined_feature_names = processed_categorical_names + NUMERICAL_COLUMNS
    influence_rankings = trained_classifier.feature_importances_

    key_risk_drivers = (
        pd.Series(influence_rankings, index=combined_feature_names)
        .sort_values(ascending=False)
        .head(5)
        .reset_index()
        .rename(columns={"index": "feature", 0: "importance"})
        .to_dict(orient="records")
    )

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