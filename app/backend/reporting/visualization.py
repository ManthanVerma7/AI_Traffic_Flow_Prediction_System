"""
5_visualization.py
==================

Step 5: Visualization
Reads dataset and ML model to create an interactive Plotly dashboard,
featuring a time-series line graph and a categorical bar chart.
"""

import os
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from joblib import load

# ---------------------------------------------------------------------------
# Configuration / Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DATA_PATH = os.path.join(PROJECT_ROOT, "data", "csv", "output.csv")
MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "pkl", "traffic_model.pkl")


# ---------------------------------------------------------------------------
# Data Loading & Preparation
# ---------------------------------------------------------------------------

def load_and_prepare_data():
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"[ERROR] Could not find {DATA_PATH}")
        
    df = pd.read_csv(DATA_PATH)
    df['total_vehicles_smoothed'] = df['total_vehicles'].rolling(window=5).mean()
    df = df.dropna()
    
    return df


# ---------------------------------------------------------------------------
# Prediction Generation
# ---------------------------------------------------------------------------

def generate_predictions(model, df, steps=5):
    current_features = [
        df['total_vehicles_smoothed'].iloc[-1],
        df['total_vehicles_smoothed'].iloc[-2],
        df['total_vehicles_smoothed'].iloc[-3]
    ]
    
    predictions = []
    
    for _ in range(steps):
        pred = model.predict([current_features])[0]
        pred = max(0, pred)
        predictions.append(pred)
        current_features = [pred, current_features[0], current_features[1]]
        
    return predictions


# ---------------------------------------------------------------------------
# Visualization Core
# ---------------------------------------------------------------------------

def display_dashboard():
    print("[INFO] Loading data...")
    df = load_and_prepare_data()
    
    print("[INFO] Loading trained model...")
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"[ERROR] Could not find {MODEL_PATH}")
    model = load(MODEL_PATH)
    
    print("[INFO] Generating predictions for next 5 frames...")
    predictions = generate_predictions(model, df, steps=5)
    
    # -----------------------------------------------------------------------
    # Part 1: Data Aggregation & Prep
    # -----------------------------------------------------------------------
    
    # Line Graph Data
    actual_frames = df['frame_number'].tolist()
    actual_traffic = df['total_vehicles_smoothed'].tolist()
    
    last_known_frame = actual_frames[-1]
    pred_frames = [last_known_frame + i + 1 for i in range(len(predictions))]
    pred_frames_continuous = [last_known_frame] + pred_frames
    pred_traffic_continuous = [actual_traffic[-1]] + predictions
    
    # Bar Chart Data (Aggregate Totals)
    total_cars = df['count_car'].sum()
    total_motos = df['count_motorcycle'].sum()
    total_buses = df['count_bus'].sum()
    total_trucks = df['count_truck'].sum()
    
    vehicle_types = ['Cars', 'Motorcycles', 'Buses', 'Trucks']
    vehicle_counts = [total_cars, total_motos, total_buses, total_trucks]
    
    print("[INFO] Starting Plotly visualization...")
    
    # -----------------------------------------------------------------------
    # Part 2: Build Subplots
    # -----------------------------------------------------------------------
    # Create 1 row, 2 columns subplot layout
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=(
            "Traffic Flow Over Time", 
            "Vehicle Type Distribution"
        ),
        column_widths=[0.65, 0.35], # Give line graph more space
        horizontal_spacing=0.1
    )
    
    # --- Subplot 1: Line Graph (Actual Data) ---
    fig.add_trace(go.Scatter(
        x=actual_frames,
        y=actual_traffic,
        mode='lines',
        name='Actual Traffic',
        line=dict(color='#00d4ff', width=1), # Reduced thickness
        fill='tozeroy',
        fillcolor='rgba(0, 212, 255, 0.1)',
        hovertemplate='<b>Frame %{x}</b><br>Vehicles: %{y:.1f}<extra></extra>'
    ), row=1, col=1)
    
    # --- Subplot 1: Line Graph (Predicted Data) ---
    fig.add_trace(go.Scatter(
        x=pred_frames_continuous,
        y=pred_traffic_continuous,
        mode='lines+markers',
        name='Predicted Traffic',
        line=dict(color='#ff9100', width=2, dash='dot'), # Reduced thickness
        marker=dict(size=8, symbol='diamond', color='#ff9100', line=dict(color='white', width=1)),
        fill='tozeroy',
        fillcolor='rgba(255, 145, 0, 0.15)',
        hovertemplate='<b>Future Step</b><br>Frame: %{x}<br>Predicted: %{y:.1f}<extra></extra>'
    ), row=1, col=1)
    
    # --- Subplot 2: Bar Graph (Vehicle Distribution) ---
    fig.add_trace(go.Bar(
        x=vehicle_types,
        y=vehicle_counts,
        name='Vehicle Distribution',
        marker_color=['#00d4ff', '#ff9100', '#00ff88', '#ff3333'], # Consistent vibrant colors
        marker_line=dict(color='white', width=1),
        hovertemplate='<b>%{x}</b><br>Total Aggregated: %{y}<extra></extra>'
    ), row=1, col=2)
    
    # -----------------------------------------------------------------------
    # Part 3: Styling and Layout Adjustments
    # -----------------------------------------------------------------------
    
    # Traffic Level Horizontal Lines overlaying Subplot 1
    # Adding LOW traffic indicator line
    fig.add_hline(y=10, line_color="#00ff88", line_width=1.5, line_dash="dash",
                  annotation_text="Traffic Level: LOW (<15)", annotation_position="top left",
                  annotation_font_color="#00ff88", row=1, col=1)
                  
    # Adding MEDIUM traffic indicator line
    fig.add_hline(y=20, line_color="#ffdd00", line_width=1.5, line_dash="dash",
                  annotation_text="Traffic Level: MEDIUM (15-25)", annotation_position="top left",
                  annotation_font_color="#ffdd00", row=1, col=1)
                  
    # Adding HIGH traffic indicator line
    fig.add_hline(y=30, line_color="#ff3333", line_width=1.5, line_dash="dash",
                  annotation_text="Traffic Level: HIGH (>25)", annotation_position="top left",
                  annotation_font_color="#ff3333", row=1, col=1)
                  
    fig.update_layout(
        title=dict(
            text='AI Traffic Flow Dashboard',
            font=dict(size=28, color='#ffffff', family="Arial, sans-serif"),
            x=0.5, xanchor='center'
        ),
        paper_bgcolor='#111111',
        plot_bgcolor='#111111',
        template='plotly_dark',
        hovermode='x unified',
        width=1400, # Increased width for side-by-side
        height=700,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.15, # Move legend below graphs
            xanchor="center",
            x=0.5,
            font=dict(color='#ffffff')
        ),
        margin=dict(l=60, r=60, t=120, b=80)
    )
    
    # Update axes styling to ensure it applies to both subplots cleanly
    fig.update_xaxes(title_text='Frame Sequence', gridcolor='#333333', zerolinecolor='#333333', tickfont=dict(color='#888888'), row=1, col=1)
    fig.update_yaxes(title_text='Vehicles (Smoothed)', gridcolor='#333333', zerolinecolor='#333333', tickfont=dict(color='#888888'), row=1, col=1)
    
    fig.update_xaxes(title_text='Vehicle Type', gridcolor='#333333', zerolinecolor='#333333', tickfont=dict(color='#888888'), row=1, col=2)
    fig.update_yaxes(title_text='Counts', gridcolor='#333333', zerolinecolor='#333333', tickfont=dict(color='#888888'), row=1, col=2)
    
    # Make subplot titles stand out
    for annotation in fig['layout']['annotations']: 
        if annotation['text'] in ("Traffic Flow Over Time", "Vehicle Type Distribution"):
            annotation['font'] = dict(size=20, color='#aaaaaa')
            
    # Launch in browser more reliably
    output_dir = os.path.join(PROJECT_ROOT, "reports", "exports")
    os.makedirs(output_dir, exist_ok=True)
    html_path = os.path.join(output_dir, "dashboard.html")
    
    # Using CDN makes the file tiny and prevents the browser from 
    # lagging/hanging when trying to load local massive JS files.
    fig.write_html(html_path, include_plotlyjs='cdn')
    
    print(f"\n[INFO] Dashboard successfully generated!")
    print(f"[INFO] Saved to: {html_path}")
    
    import webbrowser
    webbrowser.open(f"file://{html_path}")
if __name__ == "__main__":
    display_dashboard()
