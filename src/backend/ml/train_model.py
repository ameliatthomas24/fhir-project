import os
import pickle
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report, roc_auc_score, confusion_matrix, f1_score
)
from xgboost import XGBClassifier


DATA_PATH = os.getenv("DATA_PATH", "diabetes_prediction_dataset.csv")
MODEL_OUT  = os.getenv("MODEL_OUT",  "model.pkl")
REPORT_OUT = os.getenv("REPORT_OUT", "model_report.txt")
RANDOM_STATE = 42

df = pd.read_csv(DATA_PATH)
df = df[df["gender"] != "Other"].copy()

# Handle outliers 
bmi_cap = df["bmi"].quantile(0.99)
df["bmi"] = df["bmi"].clip(upper=bmi_cap)
age_cap = df["age"].quantile(0.99)
df["age"] = df["age"].clip(upper=age_cap)

# Features 
CATEGORICAL = ["gender", "smoking_history"]
NUMERICAL   = ["age", "bmi", "HbA1c_level", "blood_glucose_level",
                "hypertension", "heart_disease"]

X = df[CATEGORICAL + NUMERICAL]
y = df["diabetes"]

print(f"Class balance: {y.value_counts().to_dict()}")

# Train/test split 

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
)

# Preprocessing Pipeline 
preprocessor = ColumnTransformer(transformers=[
    ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL),
    ("num", StandardScaler(), NUMERICAL),
])

# Logistic regression 
print("\nTraining baseline")
lr_pipeline = Pipeline([
    ("pre", preprocessor),
    ("clf", LogisticRegression(class_weight="balanced", max_iter=1000, random_state=RANDOM_STATE))
])
lr_pipeline.fit(X_train, y_train)
lr_preds = lr_pipeline.predict(X_test)
lr_probs = lr_pipeline.predict_proba(X_test)[:, 1]
lr_auc   = roc_auc_score(y_test, lr_probs)
lr_f1    = f1_score(y_test, lr_preds)
print(f" AUC-ROC: {lr_auc:.4f}, F1: {lr_f1:.4f}")

# XGBoost 
# Handle class imbalance
neg = (y_train == 0).sum()
pos = (y_train == 1).sum()
scale = neg / pos

xgb_pipeline = Pipeline([
    ("pre", preprocessor),
    ("clf", XGBClassifier(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.05,
        scale_pos_weight=scale,   
        eval_metric="logloss",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    ))
])
xgb_pipeline.fit(X_train, y_train)
xgb_preds = xgb_pipeline.predict(X_test)
xgb_probs = xgb_pipeline.predict_proba(X_test)[:, 1]
xgb_auc   = roc_auc_score(y_test, xgb_probs)
xgb_f1    = f1_score(y_test, xgb_preds)
print(f"  AUC-ROC: {xgb_auc:.4f}  |  F1: {xgb_f1:.4f}")

# Feature Importances 
cat_features = list(
    xgb_pipeline.named_steps["pre"]
    .named_transformers_["cat"]
    .get_feature_names_out(CATEGORICAL))
all_features = cat_features + NUMERICAL

importances = xgb_pipeline.named_steps["clf"].feature_importances_
feat_imp = (
    pd.Series(importances, index=all_features)
    .sort_values(ascending=False))

with open(MODEL_OUT, "wb") as f:
    pickle.dump(xgb_pipeline, f)

# Results 
results = f"""
  Total samples : {len(df)}
  Train / Test  : {len(X_train)} / {len(X_test)}
  Diabetic: {y.sum()} ({100*y.mean():.4f}%)
  Non-diabetic  : {(y==0).sum()} ({100*(1-y.mean()):.4f}%)
  Baseline AUC-ROC : {lr_auc:.4f}
  Baseline F1 : {lr_f1:.4f}
  AUC-ROC : {xgb_auc:.4f}
  F1 : {xgb_f1:.4f}
{classification_report(y_test, xgb_preds, target_names=["No Diabetes", "Diabetes"])}
{confusion_matrix(y_test, xgb_preds)}
"""
for feat, score in feat_imp.head(10).items():
    results += f"  {feat:<35} {score:.4f}\n"
print(results)