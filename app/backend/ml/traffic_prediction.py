import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import os
from joblib import dump

def load_and_preprocess(filepath):
    """
    Load dataset and apply preprocessing:
    1. Apply rolling average smoothing (window = 5) on total_vehicles
    2. Create lag features (t-1, t-2, t-3)
    3. Drop missing values
    """
    # 1. Load dataset
    df = pd.read_csv(filepath)
    
    # Ensure total_vehicles exists
    if 'total_vehicles' not in df.columns:
        raise ValueError("Column 'total_vehicles' not found in dataset.")
        
    # 2. Add rolling average smoothing
    # We apply the smoothing directly to 'total_vehicles'
    df['total_vehicles_smoothed'] = df['total_vehicles'].rolling(window=5).mean()
    
    # 3. Feature Engineering: Create lag features based on smoothed total_vehicles
    df['lag_1'] = df['total_vehicles_smoothed'].shift(1)
    df['lag_2'] = df['total_vehicles_smoothed'].shift(2)
    df['lag_3'] = df['total_vehicles_smoothed'].shift(3)
    
    # 4. Drop missing values created by rolling window and lags
    df = df.dropna()
    
    return df

def train_model(df):
    """
    Train Linear Regression using lag features.
    """
    # Define features (X) and target (y)
    # Note: We omit 'avg_speed_px' to allow easy autoregressive future predictions.
    # Predicting future speed without its own lags would overcomplicate the simple pipeline.
    features = ['lag_1', 'lag_2', 'lag_3']
    
    X = df[features]
    y = df['total_vehicles_smoothed']  # Target is the smoothed value
    
    model = LinearRegression()
    # Use .values to train on numpy arrays, preventing feature name warnings during prediction
    model.fit(X.values, y)
    
    return model, features

def predict_future(model, last_known_lags, steps=5):
    """
    Predict next N steps into the future using previous predictions as lags.
    """
    predictions = []
    
    # Copy the current lag feature list
    current_features = list(last_known_lags)
    
    for _ in range(steps):
        # Predict the next step (using 2D array as required by sklearn)
        pred = model.predict([current_features])[0]
        
        # Vehicles cannot be negative
        pred = max(0, pred)
        predictions.append(pred)
        
        # Update lag features for the next prediction:
        # The newly predicted value becomes the new 'lag_1'
        # The old 'lag_1' becomes 'lag_2', and 'lag_2' becomes 'lag_3'
        current_features = [pred, current_features[0], current_features[1]]
        
    return predictions

def determine_traffic_level(avg_pred):
    """
    Determine traffic condition based on average predicted vehicles.
    """
    if avg_pred < 15:
        return "LOW"
    elif avg_pred <= 25:
        return "MEDIUM"
    else:
        return "HIGH"

def main():
    # Base paths: Handle different execution locations safely
    possible_paths = [
        'data/output.csv',       # If running from project root
        '../data/output.csv',    # If running from src/
        os.path.join(os.path.dirname(__file__), '..', 'data', 'output.csv') # Fallback relative to this script
    ]
    
    dataset_path = None
    for path in possible_paths:
        if os.path.exists(path):
            dataset_path = path
            break
            
    if not dataset_path:
        print("Error: Could not find 'output.csv' in the 'data' directory.")
        print("Please make sure you have generated the output dataset from Step 3.")
        return
        
    print(f"Loading data from: {dataset_path} ...")
    
    # Preprocess
    df = load_and_preprocess(dataset_path)
    
    if len(df) < 5:
        print("Error: Dataset is too small or entirely missing after dropping NaNs.")
        print("Ensure you have a sufficiently large video/dataset generating the CSV.")
        return
        
    # Train
    model, features = train_model(df)
    
    # Save the trained model
    # Use PROJECT_ROOT (one level up from src/) to ensure it's saved in traffic-ai/models
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    save_dir = os.path.join(PROJECT_ROOT, "models", "pkl")
    
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
        
    save_path = os.path.join(save_dir, "traffic_model.pkl")
    dump(model, save_path)
    print(f"Model successfully saved to {save_path}")
    

    # Extract the very last known lags to jumpstart the prediction
    # Get the last row in the df
    last_row = df.iloc[-1]
    
    # The last known value becomes our starting 'lag_1', its lag_1 becomes 'lag_2', etc.
    latest_lags = [
        last_row['total_vehicles_smoothed'], # Becomes lag_1
        last_row['lag_1'],                   # Becomes lag_2
        last_row['lag_2']                    # Becomes lag_3
    ]
    
    # Predict next 5 sequences
    predictions = predict_future(model, latest_lags, steps=5)
    
    # Post-processing
    avg_pred = sum(predictions) / len(predictions)
    traffic_level = determine_traffic_level(avg_pred)
    
    # Output results clearly
    print("\n--- TRAFFIC PREDICTION RESULTS ---")
    print(f"Predicting next {len(predictions)} frames/intervals:")
    for i, p in enumerate(predictions, 1):
        print(f"  Step {i}: {p:.1f} vehicles")
        
    print("-" * 34)
    print(f"Average Predicted Traffic: {avg_pred:.1f} vehicles")
    print(f"Predicted Traffic Level:   {traffic_level}")
    print("----------------------------------")

if __name__ == "__main__":
    main()
