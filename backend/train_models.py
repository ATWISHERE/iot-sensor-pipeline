import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import LabelEncoder
import joblib
import os

print("1. Training Crop Recommendation Model...")
crop_df = pd.read_csv("Dataset/Crop_recommendation.csv")

# Sklearn can handle string targets automatically, so no need for a manual dictionary mapping
X_crop = crop_df[['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall']]
y_crop = crop_df['label'] 

crop_model = DecisionTreeClassifier(random_state=42)
crop_model.fit(X_crop, y_crop)

# Save the trained model to a file
joblib.dump(crop_model, "crop_model.pkl")
print("--> Saved crop_model.pkl")

print("\n2. Training Fertilizer Recommendation Model...")
fert_df = pd.read_csv("Dataset/Fertilizer Prediction.csv")

# Initialize encoders for categorical columns
soil_enc = LabelEncoder()
crop_type_enc = LabelEncoder()

# Encode strings to numbers
fert_df['Soil Type'] = soil_enc.fit_transform(fert_df['Soil Type'])
fert_df['Crop Type'] = crop_type_enc.fit_transform(fert_df['Crop Type'])

# Notice the exact column names from your dataset (Temparature, Humidity )
X_fert = fert_df[['Temparature', 'Humidity ', 'Moisture', 'Soil Type', 'Crop Type', 'Nitrogen', 'Potassium', 'Phosphorous']]
y_fert = fert_df['Fertilizer Name']

fert_model = DecisionTreeClassifier(random_state=42)
fert_model.fit(X_fert, y_fert)

# Save the model and the encoders (we need the encoders later to translate live dashboard inputs)
joblib.dump(fert_model, "fert_model.pkl")
joblib.dump(soil_enc, "soil_encoder.pkl")
joblib.dump(crop_type_enc, "crop_type_encoder.pkl")
print("--> Saved fert_model.pkl and encoders")

print("\nAll models trained and ready for the IoT backend!")
