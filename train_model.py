import pandas as pd
from xgboost import XGBClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report
import joblib

# 1. Load Data (Preprocessed)
print("Loading data...")
X_train = pd.read_csv('X_train_processed.csv')
y_train = pd.read_csv('y_train_processed.csv').values.ravel()
X_test = pd.read_csv('X_test_processed.csv')
y_test = pd.read_csv('y_test_processed.csv').values.ravel()

# --- CRITICAL CHANGE FOR R2L/U2R ---
# Instead of selecting "Top 20", we use ALL features.
# R2L and U2R rely on rare features like 'root_shell' or 'num_failed_logins'
# which get deleted in a "Top 20" selection.
selected_features = X_train.columns.tolist() 

print(f"Training on ALL {len(selected_features)} features to capture R2L/U2R patterns...")

X_train_selected = X_train[selected_features]
X_test_selected = X_test[selected_features]

# 2. Encode Labels (Required for XGBoost)
le = LabelEncoder()
y_train_enc = le.fit_transform(y_train)
y_test_enc = le.transform(y_test)

# 3. Train XGBoost
print("Training XGBoost (this might take 10-20 seconds)...")
model = XGBClassifier(
    n_estimators=100, 
    eval_metric='mlogloss',
)
model.fit(X_train_selected, y_train_enc)

# 4. Evaluate
print("Evaluating...")
y_pred = model.predict(X_test_selected)
acc = accuracy_score(y_test_enc, y_pred)
print(f"Test Accuracy: {acc:.4f}")
print("\nClassification Report:")
print(classification_report(y_test_enc, y_pred, target_names=le.classes_))

# 5. Save Everything
print("Saving artifacts...")

# We save it as 'xgboost_model.pkl' 
joblib.dump(model, 'models/xgboost_model.pkl') 

# Save the encoder (needed to turn 0,1,2 back into 'DoS', 'Normal')
joblib.dump(le, 'models/label_encoder.pkl')

# Save the feature list (which is now ALL features)
joblib.dump(selected_features, 'models/selected_features.pkl')

print("Done! Ready for Live Demo.")