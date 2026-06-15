"""
6_report.py
===========

Step 6: HTML & CSS Dashboard to PDF Converter (Pro Edition)
Generates a stunning, complete HTML dashboard report and PDF.
"""

import os
import cv2
import base64
import importlib
import pandas as pd
import plotly.graph_objects as go
import webbrowser

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None


# ---------------------------------------------------------------------------
# Configuration / Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DATA_PATH = os.path.join(PROJECT_ROOT, "data", "csv", "output.csv")
MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "pkl", "traffic_model.pkl")

INPUT_VIDEO = os.path.join(PROJECT_ROOT, "data", "input.mp4")
TRACKING_VIDEO = os.path.join(PROJECT_ROOT, "data", "processed_videos", "tracking_output.mp4")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "reports", "exports")

# Visual Assets
IMG_PLOT = os.path.join(OUTPUT_DIR, "traffic_plot.png")
IMG_BAR = os.path.join(OUTPUT_DIR, "vehicle_distribution.png")
IMG_INPUT_FRAME = os.path.join(OUTPUT_DIR, "input_frame.png")
IMG_TRACKING_FRAME = os.path.join(OUTPUT_DIR, "tracking_frame.png")
IMG_HEATMAP = os.path.join(OUTPUT_DIR, "traffic_heatmap.png")
IMG_GAUGE = os.path.join(OUTPUT_DIR, "traffic_gauge.png")

# Final Outputs
HTML_REPORT = os.path.join(OUTPUT_DIR, "report.html")
PDF_REPORT = os.path.join(OUTPUT_DIR, "traffic.pdf")

# ---------------------------------------------------------------------------
# Core Logic
# ---------------------------------------------------------------------------

def capture_video_frame(video_path, output_img_path, frame_number=100):
    if not os.path.exists(video_path): return False
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    ret, frame = cap.read()
    if ret:
        cv2.imwrite(output_img_path, frame)
        cap.release()
        return True
    cap.release()
    return False

def generate_predictions(model, df, steps=5):
    df_clean = df.copy()
    if 'total_vehicles_smoothed' not in df_clean.columns:
        df_clean['total_vehicles_smoothed'] = df_clean['total_vehicles'].rolling(window=5).mean()
    df_clean = df_clean.dropna()
    current_features = [
        df_clean['total_vehicles_smoothed'].iloc[-1],
        df_clean['total_vehicles_smoothed'].iloc[-2],
        df_clean['total_vehicles_smoothed'].iloc[-3]
    ]
    predictions = []
    for _ in range(steps):
        pred = max(0, model.predict([current_features])[0])
        predictions.append(pred)
        current_features = [pred, current_features[0], current_features[1]]
    return predictions

def generate_graphs(df, preds):
    """
    Generate report chart PNGs using matplotlib (no kaleido needed).
    Uses the ACTUAL df and preds passed in — always fresh, never cached.
    """
    import matplotlib
    matplotlib.use('Agg')  # non-interactive backend, safe for server use
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker

    # Delete old images first so stale files can never survive a failed write
    for old_path in [IMG_PLOT, IMG_BAR]:
        if os.path.exists(old_path):
            try:
                os.remove(old_path)
            except OSError:
                pass

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # ── 1. Line Graph: actual + predicted traffic ────────────────────────
    df_clean = df.copy()
    actual_frames  = df_clean['frame_number'].tolist()
    actual_traffic = df_clean['total_vehicles'].tolist()

    last_frame   = actual_frames[-1]
    last_val     = actual_traffic[-1]
    pred_frames  = [last_frame] + [last_frame + i + 1 for i in range(len(preds))]
    pred_traffic = [last_val]  + list(preds)

    fig1, ax1 = plt.subplots(figsize=(10, 4))
    fig1.patch.set_facecolor('#0f172a')
    ax1.set_facecolor('#0f172a')

    ax1.plot(actual_frames, actual_traffic, color='#4f46e5', linewidth=1.5, label='Actual Traffic')
    ax1.fill_between(actual_frames, actual_traffic, alpha=0.15, color='#4f46e5')
    ax1.plot(pred_frames, pred_traffic, color='#f97316', linewidth=2,
             linestyle='--', marker='o', markersize=3, label=f'Predicted ({len(preds)} steps)')

    ax1.axhline(y=15, color='#10b981', linestyle=':', linewidth=1, alpha=0.7)
    ax1.axhline(y=25, color='#f59e0b', linestyle=':', linewidth=1, alpha=0.7)
    ax1.axhline(y=35, color='#ef4444', linestyle=':', linewidth=1, alpha=0.7)

    ax1.set_title('Traffic Flow Trend & Forecast', color='white', fontsize=14, pad=10)
    ax1.set_xlabel('Frame Number', color='#8b9bb4')
    ax1.set_ylabel('Vehicles', color='#8b9bb4')
    ax1.tick_params(colors='#8b9bb4')
    ax1.spines[:].set_color('#1e293b')
    ax1.legend(facecolor='#1e293b', edgecolor='#334155', labelcolor='white', fontsize=9)
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: str(int(x))))
    plt.tight_layout()
    fig1.savefig(IMG_PLOT, dpi=120, bbox_inches='tight', facecolor='#0f172a')
    plt.close(fig1)
    print(f"[REPORT] Line graph saved: {IMG_PLOT}")

    # ── 2. Bar Graph: vehicle distribution ──────────────────────────────
    vehicle_labels = ['Cars', 'Motorcycles', 'Buses', 'Trucks']
    vehicle_counts = [
        int(df['count_car'].max()),
        int(df['count_motorcycle'].max()),
        int(df['count_bus'].max()),
        int(df['count_truck'].max())
    ]
    print(f"[REPORT] Bar chart data: {dict(zip(vehicle_labels, vehicle_counts))}")

    bar_colors = ['#3b82f6', '#a855f7', '#22c55e', '#f59e0b']
    fig2, ax2 = plt.subplots(figsize=(10, 4))
    fig2.patch.set_facecolor('#0f172a')
    ax2.set_facecolor('#0f172a')

    bars = ax2.bar(vehicle_labels, vehicle_counts, color=bar_colors, width=0.5, edgecolor='#1e293b', linewidth=0.8)
    for bar, count in zip(bars, vehicle_counts):
        ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(vehicle_counts) * 0.01,
                 f'{count:,}', ha='center', va='bottom', color='white', fontsize=10, fontweight='bold')

    ax2.set_title('Total Vehicle Distribution', color='white', fontsize=14, pad=10)
    ax2.set_xlabel('Vehicle Type', color='#8b9bb4')
    ax2.set_ylabel('Accumulated Count', color='#8b9bb4')
    ax2.tick_params(colors='#8b9bb4')
    ax2.spines[:].set_color('#1e293b')
    ax2.set_ylim(0, max(vehicle_counts) * 1.18 if max(vehicle_counts) > 0 else 10)
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{int(x):,}'))
    plt.tight_layout()
    fig2.savefig(IMG_BAR, dpi=120, bbox_inches='tight', facecolor='#0f172a')
    plt.close(fig2)
    print(f"[REPORT] Bar chart saved: {IMG_BAR}")

    # ── 3. Premium Heatmap Graph ──────────────────────────────────────────
    import numpy as np
    from matplotlib.colors import LinearSegmentedColormap
    heatmap_data = np.array([
        df_clean['count_car'].tolist(),
        df_clean['count_motorcycle'].tolist(),
        df_clean['count_bus'].tolist(),
        df_clean['count_truck'].tolist()
    ])
    
    # Custom traffic-themed colormap: Deep Blue → Cyan → Yellow → Orange → Red
    traffic_cmap = LinearSegmentedColormap.from_list('traffic', [
        '#0a2463', '#00b4d8', '#f0c808', '#f97316', '#e63946'
    ])
    
    # Detect low-activity rows and annotate them
    row_labels = ['Cars', 'Motorcycles', 'Buses', 'Trucks']
    row_maxes = heatmap_data.max(axis=1)
    
    fig3, ax3 = plt.subplots(figsize=(10, 4))
    fig3.patch.set_facecolor('#0f172a')
    ax3.set_facecolor('#0f172a')
    cax = ax3.imshow(heatmap_data, aspect='auto', cmap=traffic_cmap, interpolation='nearest')
    ax3.set_yticks([0, 1, 2, 3])
    ax3.set_yticklabels(row_labels, color='#8b9bb4')
    ax3.set_xlabel('Frame Number', color='#8b9bb4')
    ax3.set_title('Traffic Density Heatmap', color='white', fontsize=14, pad=10)
    ax3.tick_params(colors='#8b9bb4')
    
    # Add "Low Activity" labels on rows with near-zero data
    for i, (label, mx) in enumerate(zip(row_labels, row_maxes)):
        if mx <= 1:
            ax3.text(heatmap_data.shape[1] / 2, i, 'LOW ACTIVITY',
                     ha='center', va='center', color='#4a5568',
                     fontsize=9, fontweight='bold', fontstyle='italic',
                     bbox=dict(boxstyle='round,pad=0.3', facecolor='#0f172a', alpha=0.7, edgecolor='none'))
    
    cbar = fig3.colorbar(cax, ax=ax3)
    cbar.ax.yaxis.set_tick_params(color='#8b9bb4')
    plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='#8b9bb4')
    
    # Add legend labels to colorbar
    cbar.set_label('Vehicle Density', color='#8b9bb4', fontsize=10)
    
    plt.tight_layout()
    fig3.savefig(IMG_HEATMAP, dpi=120, bbox_inches='tight', facecolor='#0f172a')
    plt.close(fig3)
    print(f"[REPORT] Heatmap saved: {IMG_HEATMAP}")

    # ── 4. Premium Traffic Load / Congestion Level Gauge ──────────────
    avg_veh = df_clean['total_vehicles'].mean()
    max_veh_val = df_clean['total_vehicles'].max()
    ceiling = max(40, max_veh_val * 1.5)
    load_pct = min(100, (avg_veh / ceiling) * 100)
    
    # Determine congestion level
    if avg_veh < 10:
        cong_level, cong_color = 'LOW', '#10b981'
    elif avg_veh < 20:
        cong_level, cong_color = 'MEDIUM', '#f59e0b'
    elif avg_veh < 30:
        cong_level, cong_color = 'HIGH', '#f97316'
    else:
        cong_level, cong_color = 'CRITICAL', '#ef4444'
    
    fig4, ax4 = plt.subplots(figsize=(10, 2.5))
    fig4.patch.set_facecolor('#0f172a')
    ax4.set_facecolor('#0f172a')
    
    # Background zones
    zone_colors = [('#10b981', 0, 25), ('#f59e0b', 25, 50), ('#f97316', 50, 75), ('#ef4444', 75, 100)]
    for color, start, end in zone_colors:
        ax4.barh(0, end - start, left=start, color=color, height=0.5, alpha=0.2)
    
    # Filled progress bar
    ax4.barh(0, load_pct, color=cong_color, height=0.5, alpha=0.85,
             edgecolor='white', linewidth=0.5)
    
    # Zone labels
    zone_labels = [('LOW', 12.5), ('MEDIUM', 37.5), ('HIGH', 62.5), ('CRITICAL', 87.5)]
    for label, pos in zone_labels:
        ax4.text(pos, -0.45, label, ha='center', va='top', color='#4a5568',
                 fontsize=7, fontweight='bold')
    
    # Current value marker
    ax4.plot([load_pct, load_pct], [-0.3, 0.3], color='white', linewidth=3, zorder=5)
    ax4.text(load_pct, 0.5, f'{load_pct:.0f}%', color='white', ha='center',
             va='bottom', fontsize=18, fontweight='bold')
    ax4.text(load_pct, 0.85, f'Avg: {avg_veh:.1f} veh/frame', color='#8b9bb4',
             ha='center', va='bottom', fontsize=9)
    
    ax4.set_xlim(0, 100)
    ax4.set_ylim(-0.7, 1.2)
    ax4.axis('off')
    ax4.set_title(f'Traffic Congestion Level: {cong_level}', color=cong_color,
                  fontsize=14, pad=10, fontweight='bold')
    plt.tight_layout()
    fig4.savefig(IMG_GAUGE, dpi=120, bbox_inches='tight', facecolor='#0f172a')
    plt.close(fig4)
    print(f"[REPORT] Congestion gauge saved: {IMG_GAUGE}")

# ---------------------------------------------------------------------------
# HTML Template
# ---------------------------------------------------------------------------

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>AI Traffic Flow Analytics Dashboard</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        :root {{
            --primary: #4f46e5;
            --primary-light: #e0e7ff;
            --bg-body: #f8fafc;
            --bg-card: #ffffff;
            --text-main: #0f172a;
            --text-muted: #64748b;
            --border: #e2e8f0;
            --success: #10b981;
            --success-bg: #dcfce7;
            --warning: #f59e0b;
            --warning-bg: #fef3c7;
            --danger: #ef4444;
            --danger-bg: #fee2e2;
        }}

        body {{
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-body);
            color: var(--text-main);
            margin: 0;
            padding: 40px;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1050px;
            margin: 0 auto;
        }}
        
        /* Typography */
        h1 {{ font-size: 36px; font-weight: 700; color: var(--text-main); margin: 0; letter-spacing: -1px; }}
        h2 {{ font-size: 22px; font-weight: 700; color: var(--text-main); margin-bottom: 20px; margin-top: 40px; border-bottom: 2px solid var(--border); padding-bottom: 8px; }}
        h3 {{ font-size: 16px; font-weight: 600; color: var(--text-muted); margin-top: 0; margin-bottom: 15px; text-transform: uppercase; letter-spacing: 0.5px; }}
        p {{ margin: 0 0 10px 0; color: var(--text-main); }}

        /* Components */
        .card {{
            background: var(--bg-card);
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05), 0 1px 3px rgba(0,0,0,0.03);
            border: 1px solid rgba(226, 232, 240, 0.8);
            margin-bottom: 24px;
        }}
        
        .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }}
        .grid-4 {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }}
        
        /* Header Section */
        .header {{
            text-align: center;
            margin-bottom: 40px;
        }}
        .header p {{ color: var(--text-muted); font-size: 18px; margin-top: 8px; }}
        
        /* Exec Summary & Overview */
        .summary-text {{ font-size: 15px; color: var(--text-main); }}
        .flow-diagram {{
            background: var(--primary-light);
            color: var(--primary);
            padding: 12px 20px;
            border-radius: 8px;
            font-weight: 600;
            text-align: center;
            font-size: 14px;
            letter-spacing: 1px;
            margin-top: 15px;
        }}
        
        ul.insights-list {{ margin: 0; padding-left: 20px; font-size: 15px; }}
        ul.insights-list li {{ margin-bottom: 8px; }}

        /* KPI Stats */
        .stat-box {{
            background: var(--bg-body);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 16px;
            text-align: center;
        }}
        .stat-box .title {{ font-size: 13px; color: var(--text-muted); font-weight: 600; text-transform: uppercase; }}
        .stat-box .value {{ font-size: 28px; font-weight: 700; color: var(--primary); margin-top: 8px; }}

        /* Visuals Segment */
        .visual-container {{ text-align: center; }}
        .visual-container img {{
            width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            border: 1px solid var(--border);
        }}
        .visual-container p {{ margin-top: 12px; font-weight: 600; color: var(--text-muted); font-size: 14px; }}

        /* Predictions Segment */
        .pred-grid {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: var(--bg-body);
            padding: 20px;
            border-radius: 8px;
            border: 1px solid var(--border);
        }}
        .pred-item {{ text-align: center; }}
        .pred-item .label {{ font-size: 13px; color: var(--text-muted); font-weight: 600; text-transform: uppercase; }}
        .pred-item .val {{ font-size: 20px; font-weight: 700; margin-top: 5px; color: var(--text-main); }}
        
        .badge {{
            padding: 6px 14px;
            border-radius: 20px;
            font-weight: 700;
            font-size: 15px;
        }}

        /* Data Table */
        .dataframe {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
            text-align: left;
        }}
        .dataframe th {{ background: var(--bg-body); border-bottom: 2px solid var(--border); padding: 12px 8px; color: var(--text-muted); text-transform: uppercase; font-size: 12px; }}
        .dataframe td {{ padding: 10px 8px; border-bottom: 1px solid var(--border); color: var(--text-main); }}

        /* Graph Segment */
        .graph-wrapper {{ text-align: center; }}
        .graph-wrapper img {{ max-width: 100%; height: auto; }}
        
        .footer {{ text-align: center; margin-top: 60px; color: var(--text-muted); font-size: 14px; padding-bottom: 20px; border-top: 1px solid var(--border); padding-top: 20px; }}

        /* ========================================= */
        /* PRINT / PDF PAGINATION REFINEMENTS        */
        /* ========================================= */
        @media print {{
            .page-break {{
                page-break-before: always;
            }}
            img, tr {{
                page-break-inside: avoid;
                break-inside: avoid;
            }}
            thead {{
                display: table-header-group;
            }}
            h1, h2, h3 {{
                page-break-after: avoid;
                break-after: avoid;
            }}
            img {{
                max-width: 100%;
                max-height: 350px;
                object-fit: contain;
                height: auto;
            }}
            body {{
                padding: 0;
                margin: 0;
            }}
            .container {{
                padding: 15px;
            }}
            .card {{
                margin-bottom: 15px;
                padding: 16px;
                border-radius: 8px;
            }}
            h2 {{
                margin-top: 25px;
                margin-bottom: 10px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        
        <!-- =================== PAGE 1 =================== -->
        <div>
            <!-- HEADER -->
            <div class="header">
                <h1>AI Traffic Flow Prediction Report</h1>
                <p>Comprehensive telemetry, forecasting, and tracking analytics</p>
            </div>

            <!-- ROW 1: EXEC SUMMARY & INSIGHTS -->
            <div class="grid-2">
                <div class="card">
                    <h3>Executive Summary</h3>
                    <p class="summary-text">
                        This report compiles the latest tracking telemetry obtained via our YOLOv8 and ByteTrack pipeline. The system accurately monitors real-time traffic volume across four distinct vehicle classes. 
                        Using embedded autoregressive Machine Learning, the system forecasts future structural loads to preemptively flag congestion.
                    </p>
                    <div class="flow-diagram">VIDEO &rarr; YOLOv8 &rarr; BYTE TRACK &rarr; ML FORECASTING</div>
                </div>
                <div class="card">
                    <h3>Key Automated Insights</h3>
                    <ul class="insights-list">
                        <li><b>Peak Traffic Hit:</b> A maximum volume of {max_veh} vehicles was detected in a single frame.</li>
                        <li><b>Traffic Trend:</b> The recent segment shows a <b>{trend_direction}</b> momentum in traffic density.</li>
                        <li><b>Primary Demographic:</b> {top_vehicle_class} dominate the current roadway usage.</li>
                        <li><b>Overall Forecast:</b> Traffic is expected to stabilize at <b>{level_text}</b> volumes in the immediate future.</li>
                    </ul>
                </div>
            </div>

            <!-- TELEMETRY STATS -->
            <h2>Telemetry Analytics & Forecasting</h2>
            <div class="card">
                <h3>Current System Load Statistics</h3>
                <div class="grid-4">
                    <div class="stat-box">
                        <div class="title">Frames Analyzed</div>
                        <div class="value">{total_frames}</div>
                    </div>
                    <div class="stat-box">
                        <div class="title">Avg Vehicles/Frame</div>
                        <div class="value">{avg_veh:.1f}</div>
                    </div>
                    <div class="stat-box">
                        <div class="title">Max Traffic Local</div>
                        <div class="value">{max_veh}</div>
                    </div>
                    <div class="stat-box">
                        <div class="title">Risk Score / 100</div>
                        <div class="value" style="color: {risk_color};">{risk_score}</div>
                        <div style="font-size: 10px; font-weight: bold; color: {risk_color}; margin-top: 5px;">{risk_label}</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- =================== PAGE 2 =================== -->
        <div class="page-break">
            <div class="card">
                <h3>AI Future Predictions</h3>
                <div class="pred-grid">
                    <div class="pred-item">
                        <div class="label">Next 5 Step Outputs</div>
                        <div class="val">[{pred_raw}]</div>
                    </div>
                    <div class="pred-item">
                        <div class="label">Forecasted Avg Volume</div>
                        <div class="val" style="color: var(--primary);">{pred_avg:.1f}</div>
                    </div>
                    <div class="pred-item">
                        <div class="label">Determined Target Level</div>
                        <div class="val" style="margin-top: 8px;">
                            <span class="badge" style="background: {level_bg}; color: {level_fg};">{level_text}</span>
                        </div>
                    </div>
                </div>
                <p style="margin-top: 15px; font-size: 14px; text-align: center; color: var(--text-muted);">
                    <b>Conclusion & Recommendation:</b> Based on the ML forecast, traffic is expected to remain stable at <b>{level_text}</b> levels. Normal procedures apply.
                </p>
            </div>

            <!-- SYSTEM VISUALS -->
            <h2>System Visuals Context</h2>
            <div class="grid-2">
                <div class="card visual-container">
                    <img src="{img_input}" alt="Raw Input Video Frame">
                    <p>Raw Input Video Context</p>
                </div>
                <div class="card visual-container">
                    <img src="{img_track}" alt="Tracked AI Output">
                    <p>YOLOv8 Active Tracked Outputs</p>
                </div>
            </div>
        </div>

        <!-- =================== PAGE 3 =================== -->
        <div class="page-break">
            <h2>Raw Data Snapshot</h2>
            <div class="card" style="overflow-x: auto;">
                <h3>Dataset (First 5 Rows)</h3>
                {html_table}
            </div>
            
            <div class="card" style="overflow-x: auto;">
                <h3>Dataset Summary Statistics</h3>
                {summary_table}
            </div>
        </div>

        <!-- =================== PAGE 4 =================== -->
        <div class="page-break">
            <h2>Detailed Analytical Graphs</h2>
            <div class="card graph-wrapper">
                <img src="{img_plot}" alt="Plot Graph">
            </div>
            <div class="card graph-wrapper">
                <img src="{img_bar}" alt="Bar Graph">
            </div>
            <div class="card graph-wrapper">
                <img src="{img_heatmap}" alt="Traffic Density Heatmap">
            </div>
            <div class="card graph-wrapper">
                <img src="{img_gauge}" alt="Traffic Congestion Level">
            </div>
            
            <div class="footer">
                Generated by AI Traffic Flow Prediction System &bull; Confidential Dashboard Report
            </div>
        </div>
    </div>
</body>
</html>
"""

def build_report():
    import time
    print("[REPORT] Loading dataset from:", DATA_PATH)
    print(f"[REPORT] CSV last modified   : {time.ctime(os.path.getmtime(DATA_PATH)) if os.path.exists(DATA_PATH) else 'FILE NOT FOUND'}")

    df = pd.read_csv(DATA_PATH)
    total_frames = len(df)
    print(f"[REPORT] CSV rows loaded     : {total_frames}")
    print(f"[REPORT] Vehicle maxes       : cars={int(df['count_car'].max())}  motos={int(df['count_motorcycle'].max())}  buses={int(df['count_bus'].max())}  trucks={int(df['count_truck'].max())}")

    # --- ALWAYS retrain the model fresh from current CSV (no stale .pkl) ---
    try:
        ml_mod = importlib.import_module("app.backend.ml.traffic_prediction")
    except ImportError:
        ml_mod = importlib.import_module("app.backend.ml.traffic_prediction")

    df_ml = ml_mod.load_and_preprocess(DATA_PATH)
    pred_steps = 200
    print(f"[REPORT] Pred steps          : {pred_steps}  (rows after preprocess={len(df_ml)})")

    if len(df_ml) < 5:
        # Flatline fallback
        last_val = float(df['total_vehicles'].iloc[-1]) if total_frames > 0 else 0
        preds = [last_val] * pred_steps
        print(f"[REPORT] Using flatline fallback: {last_val:.1f}")
        # Build a trivial model stub for generate_graphs
        from sklearn.linear_model import LinearRegression
        import numpy as np
        model = LinearRegression()
        model.fit(np.array([[0,0,0]]), np.array([last_val]))
    else:
        model, _ = ml_mod.train_model(df_ml)
        last_row = df_ml.iloc[-1]
        latest_lags = [last_row['total_vehicles_smoothed'], last_row['lag_1'], last_row['lag_2']]
        preds = ml_mod.predict_future(model, latest_lags, steps=pred_steps)
        print(f"[REPORT] Predictions         : {[round(p,1) for p in preds]}")

    # Process basic metrics
    avg_veh = df['total_vehicles'].mean()
    max_veh = int(df['total_vehicles'].max())
    min_veh = int(df['total_vehicles'].min())

    # Calculate Risk Score
    max_capacity_threshold = 80
    risk_score = int(min(100, max(0, (avg_veh / max_capacity_threshold) * 100)))
    if risk_score < 40:
        risk_label = "LOW RISK"
        risk_color = "var(--success)"
    elif risk_score < 70:
        risk_label = "MEDIUM RISK"
        risk_color = "var(--warning)"
    elif risk_score < 85:
        risk_label = "HIGH RISK"
        risk_color = "var(--danger)"
    else:
        risk_label = "CRITICAL"
        risk_color = "#ff0000"

    # Auto-Insights Generation
    trend_val = df['total_vehicles'].tail(5).mean() - df['total_vehicles'].head(5).mean()
    if trend_val > 5: trend_direction = "Sharply Increasing"
    elif trend_val > 0: trend_direction = "Slowly Increasing"
    elif trend_val < -5: trend_direction = "Sharply Decreasing"
    else: trend_direction = "Stable"

    class_sums = {
        'Cars': int(df['count_car'].sum()),
        'Motorcycles': int(df['count_motorcycle'].sum()),
        'Buses': int(df['count_bus'].sum()),
        'Trucks': int(df['count_truck'].sum())
    }
    top_vehicle_class = max(class_sums, key=class_sums.get)

    # Process predictions
    pred_raw = ", ".join([f"{p:.0f}" for p in preds[:5]])
    pred_avg = sum(preds) / len(preds)

    if pred_avg < 15:
        level_text = "LOW"
        level_bg = "var(--success-bg)"
        level_fg = "var(--success)"
    elif pred_avg <= 25:
        level_text = "MEDIUM"
        level_bg = "var(--warning-bg)"
        level_fg = "var(--warning)"
    else:
        level_text = "HIGH"
        level_bg = "var(--danger-bg)"
        level_fg = "var(--danger)"

    print("[REPORT] Generating visual assets...")
    generate_graphs(df, preds)   # pass predictions list, not model
    capture_video_frame(INPUT_VIDEO, IMG_INPUT_FRAME, 50)
    capture_video_frame(TRACKING_VIDEO, IMG_TRACKING_FRAME, 50)
    
    def make_url(path):
        return "file:///" + os.path.abspath(path).replace('\\', '/')
    
    def img_to_data_uri(path):
        """Embed image as base64 data URI so Playwright PDF can render it."""
        if not os.path.exists(path):
            return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        with open(path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode('utf-8')
        ext = os.path.splitext(path)[1].lower().lstrip('.')
        mime = 'jpeg' if ext in ('jpg', 'jpeg') else 'png'
        return f"data:image/{mime};base64,{encoded}"

    # Generate HTML Table snippet
    html_table = df.head(5).to_html(index=False, classes="")
    summary_table = df.describe().to_html(classes="")
    
    print("[INFO] Injecting data into Dashboard Template...")
    html_content = HTML_TEMPLATE.format(
        total_frames=total_frames,
        avg_veh=avg_veh,
        max_veh=max_veh,
        min_veh=min_veh,
        trend_direction=trend_direction,
        top_vehicle_class=top_vehicle_class,
        pred_raw=pred_raw,
        pred_avg=pred_avg,
        level_text=level_text,
        level_bg=level_bg,
        level_fg=level_fg,
        risk_score=risk_score,
        risk_label=risk_label,
        risk_color=risk_color,
        html_table=html_table,
        summary_table=summary_table,
        img_input=img_to_data_uri(IMG_INPUT_FRAME),
        img_track=img_to_data_uri(IMG_TRACKING_FRAME),
        img_plot=img_to_data_uri(IMG_PLOT),
        img_bar=img_to_data_uri(IMG_BAR),
        img_heatmap=img_to_data_uri(IMG_HEATMAP),
        img_gauge=img_to_data_uri(IMG_GAUGE)
    )
    
    with open(HTML_REPORT, 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    print(f"[INFO] 10/10 Pro HTML Dashboard compiled: {HTML_REPORT}")
    
    print("\n[INFO] Attempting to compile into PDF using Playwright...")
    if sync_playwright is None:
        print("[WARN] 'playwright' library is not installed. PDF was not generated.")
    else:
        try:
            with sync_playwright() as p:
                print("[INFO] Launching headless browser...")
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                # Use absolute local path with file:/// protocol for Chromium
                url = make_url(HTML_REPORT)
                print(f"[INFO] Rendering: {url}")
                
                page.goto(url, wait_until="networkidle")
                
                # Generate PDF with pro options
                page.pdf(
                    path=PDF_REPORT,
                    format="A4",
                    print_background=True,
                    margin={"top": "0in", "right": "0in", "bottom": "0in", "left": "0in"},
                    display_header_footer=False
                )
                browser.close()
                
            if os.path.exists(PDF_REPORT):
                print(f"[SUCCESS] High-fidelity PDF Generated at: {PDF_REPORT}")
            else:
                print("[ERROR] PDF file was not created by Playwright.")
                
        except Exception as e:
            print(f"[ERROR] Playwright PDF Generation failed: {e}")
                
    print("[INFO] HTML Dashboard generation complete.")
    # webbrowser.open(make_url(HTML_REPORT))  # Removed to prevent unwanted popups during API calls


def generate_pdf_report():
    """
    Public entry point called by app.py /api/report route.
    Delegates to build_report() which generates the HTML and PDF.
    """
    build_report()


if __name__ == "__main__":
    build_report()
