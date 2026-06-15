import os
import re
import time
import importlib
import threading
from flask import Flask, request, jsonify, send_from_directory, send_file, Response
from werkzeug.utils import secure_filename
import pandas as pd
from flask_cors import CORS
import imageio

app = Flask(__name__, static_folder="app/frontend", static_url_path="/")
CORS(app)

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "outputs")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

INPUT_VIDEO_PATH = os.path.join(DATA_DIR, "input.mp4")
PREVIEW_VIDEO_PATH = os.path.join(DATA_DIR, "input_preview.mp4")
OUTPUT_VIDEO_PATH = os.path.join(DATA_DIR, "processed_videos", "tracking_output.mp4")
DATA_CSV_PATH = os.path.join(DATA_DIR, "csv", "output.csv")
PDF_REPORT_PATH = os.path.join(PROJECT_ROOT, "reports", "exports", "traffic.pdf")

# Global state to track background processing
analysis_status = {
    "is_running": False,
    "progress": 0,
    "message": "Idle",
    "completed": False,
    "results": None,
    "error": None
}

def load_module(module_name):
    """Import and FORCE reload a module so stale cache never affects results."""
    import sys
    mod = importlib.import_module(module_name)
    importlib.reload(mod)
    return mod

def generate_preview_video(input_path, output_path, max_frames=300):
    try:
        reader = imageio.get_reader(input_path)
        meta = reader.get_meta_data()
        fps = meta.get('fps', 30)
        writer = imageio.get_writer(output_path, fps=fps, codec='libx264', quality=6)
        for i, frame in enumerate(reader):
            writer.append_data(frame)
            if i >= max_frames: break
        writer.close()
        reader.close()
        return True
    except Exception as e:
        print(f"Preview generation failed: {e}")
        return False

def run_analysis_pipeline():
    global analysis_status
    analysis_status["is_running"] = True
    analysis_status["progress"] = 10
    analysis_status["message"] = "Starting analysis..."
    analysis_status["completed"] = False
    analysis_status["error"] = None
    
    start_time = time.time()
    
    try:
        # Step 2: Tracking
        analysis_status["message"] = "Initializing object detection model..."
        analysis_status["progress"] = 5
        tracking_mod = load_module("app.backend.tracking.vehicle_tracking")

        # DEBUG: Log video metadata
        video_name = os.path.basename(INPUT_VIDEO_PATH)
        app.logger.info("[PIPELINE] ── Starting analysis ──────────────────")
        app.logger.info(f"[PIPELINE] Input video     : {INPUT_VIDEO_PATH}")
        app.logger.info(f"[PIPELINE] Video exists    : {os.path.exists(INPUT_VIDEO_PATH)}")

        def update_progress(msg, pct):
            analysis_status["message"] = msg
            analysis_status["progress"] = 5 + int(pct * 0.8)  # scale up to 85%

        track_info = tracking_mod.process_video(video_path=INPUT_VIDEO_PATH, show_window=False, progress_callback=update_progress)
        video_total_frames = track_info["real_total_frames"]  # real frame count of the video file
        processed_frames   = track_info["processed_frames"]   # frames actually analysed (≤1000)
        app.logger.info(f"[PIPELINE] Video total frames : {video_total_frames}")
        app.logger.info(f"[PIPELINE] Processed frames   : {processed_frames}  (cap=1000)")
        
        # Step 4: ML Prediction
        analysis_status["message"] = "Running ML predictions..."
        analysis_status["progress"] = 86
        ml_mod = load_module("app.backend.ml.traffic_prediction")

        # Get frame counts from the video file via OpenCV (fallback if track_info is None)
        if track_info is None:
            import cv2 as _cv2
            _cap = _cv2.VideoCapture(INPUT_VIDEO_PATH)
            video_total_frames = int(_cap.get(_cv2.CAP_PROP_FRAME_COUNT))
            _cap.release()
            processed_frames = len(pd.read_csv(DATA_CSV_PATH))

        # Always reload the FRESH CSV just written by the tracker
        df_raw = pd.read_csv(DATA_CSV_PATH)
        app.logger.info(f"[PIPELINE] CSV rows           : {len(df_raw)}")
        app.logger.info(f"[PIPELINE] Vehicle counts     : cars={int(df_raw['count_car'].sum())}  motos={int(df_raw['count_motorcycle'].sum())}  buses={int(df_raw['count_bus'].sum())}  trucks={int(df_raw['count_truck'].sum())}")
        app.logger.info(f"[PIPELINE] Avg vehicles/frame : {df_raw['total_vehicles'].mean():.2f}")

        # Prediction horizon: fixed 200 steps always
        pred_steps = 200
        app.logger.info(f"[PIPELINE] Pred steps      : {pred_steps}")

        df_ml = ml_mod.load_and_preprocess(DATA_CSV_PATH)

        if len(df_ml) < 5:
            last_val = float(df_raw['total_vehicles'].iloc[-1]) if processed_frames > 0 else 0
            predictions = [last_val] * pred_steps
            app.logger.warning(f"[PIPELINE] Short video fallback: {len(df_ml)} clean rows, flatline at {last_val:.1f}")
        else:
            model_ml, features_ml = ml_mod.train_model(df_ml)
            last_row = df_ml.iloc[-1]
            latest_lags = [last_row['total_vehicles_smoothed'], last_row['lag_1'], last_row['lag_2']]
            app.logger.info(f"[PIPELINE] ML lags input   : {[round(v, 2) for v in latest_lags]}")
            predictions = ml_mod.predict_future(model_ml, latest_lags, steps=pred_steps)
            app.logger.info(f"[PIPELINE] Predictions out : {len(predictions)} steps, first5={[round(p,1) for p in predictions[:5]]}")

        avg_pred = sum(predictions) / len(predictions) if predictions else 0
        traffic_level = ml_mod.determine_traffic_level(avg_pred)

        # Use the fresh df_raw for all result calculations
        avg_veh = df_raw["total_vehicles"].mean()
        max_veh = int(df_raw["total_vehicles"].max())

        # Chart data - actual trace
        actual_frames = df_raw["frame_number"].tolist()
        actual_traffic = df_raw["total_vehicles"].tolist()

        # Prediction trace - BRIDGE: start from the last actual frame/value
        last_frame = actual_frames[-1] if actual_frames else 0
        last_traffic_val = actual_traffic[-1] if actual_traffic else 0
        pred_frames = [last_frame] + list(range(last_frame + 1, last_frame + 1 + len(predictions)))
        pred_traffic_bridged = [last_traffic_val] + [round(p, 1) for p in predictions]

        # Distribution - lowercase keys to match frontend lookup
        vehicle_counts = {
            "cars":        int(df_raw["count_car"].max()),
            "motorcycles": int(df_raw["count_motorcycle"].max()),
            "buses":       int(df_raw["count_bus"].max()),
            "trucks":      int(df_raw["count_truck"].max())
        }
        app.logger.info(f"[PIPELINE] Distribution    : {vehicle_counts}")
        app.logger.info(f"[PIPELINE] Traffic level   : {traffic_level}")

        processing_time = time.time() - start_time
        app.logger.info(f"[PIPELINE] Processing time : {processing_time:.1f}s")

        analysis_status["results"] = {
            "video_name":          video_name,
            "video_total_frames":  video_total_frames,
            "processed_frames":    processed_frames,
            "total_frames":        video_total_frames,
            "avg_veh":             round(avg_veh, 1),
            "max_veh":             max_veh,
            "traffic_level":       traffic_level,
            "processing_time":     round(processing_time, 2),
            "avg_pred":            round(avg_pred, 1),
            "pred_steps":          pred_steps,
            "graph_data": {
                "frames":       actual_frames,
                "traffic":      actual_traffic,
                "pred_frames":  pred_frames,
                "pred_traffic": pred_traffic_bridged,
                "distribution": vehicle_counts,
                "cars_traffic": df_raw['count_car'].tolist(),
                "motorcycles_traffic": df_raw['count_motorcycle'].tolist(),
                "buses_traffic": df_raw['count_bus'].tolist(),
                "trucks_traffic": df_raw['count_truck'].tolist()
            }
        }
        
        analysis_status["message"] = "Analysis complete!"
        analysis_status["progress"] = 100
        analysis_status["completed"] = True
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        app.logger.error(f"Analysis Pipeline Error: {error_trace}")
        analysis_status["error"] = str(e)
        analysis_status["message"] = f"Pipeline Crashed: {str(e)}"
        
    finally:
        analysis_status["is_running"] = False


# ROUTES
@app.route("/")
def index():
    return app.send_static_file("index.html")

@app.route("/api/upload", methods=["POST"])
def upload_video():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
        
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
        
    try:
        import imageio_ffmpeg
        import subprocess
        import uuid
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        
        temp_filename = f"temp_upload_{uuid.uuid4().hex}{os.path.splitext(file.filename)[1]}"
        temp_path = os.path.join(DATA_DIR, temp_filename)
        file.save(temp_path)
        
        subprocess.run([
            ffmpeg_path, '-y', '-i', temp_path, 
            '-frames:v', '1000',
            '-vf', 'scale=960:-2',
            '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '28',
            '-pix_fmt', 'yuv420p',
            INPUT_VIDEO_PATH
        ], check=True)
        
        try:
            os.remove(temp_path)
        except Exception as remove_e:
            app.logger.warning(f"Could not remove temp file {temp_path}: {remove_e}")
        
        return jsonify({"message": "Upload and Transcode successful", "preview_url": "/api/preview"})
    except Exception as e:
        app.logger.error(f"Transcode failed: {e}")
        return jsonify({"error": f"Transcode failed: {str(e)}"}), 500

@app.route("/api/preview")
def get_preview():
    if not os.path.exists(INPUT_VIDEO_PATH):
        return jsonify({"error": "No video found"}), 404
    
    file_size = os.path.getsize(INPUT_VIDEO_PATH)
    range_header = request.headers.get('Range', None)
    
    if range_header:
        byte_start, byte_end = 0, None
        match = re.search(r'bytes=(\d+)-(\d*)', range_header)
        if match:
            byte_start = int(match.group(1))
            byte_end = int(match.group(2)) if match.group(2) else file_size - 1
        
        length = byte_end - byte_start + 1
        with open(INPUT_VIDEO_PATH, 'rb') as f:
            f.seek(byte_start)
            data = f.read(length)
        
        rv = Response(data, 206, mimetype='video/mp4', direct_passthrough=True)
        rv.headers.add('Content-Range', f'bytes {byte_start}-{byte_end}/{file_size}')
        rv.headers.add('Accept-Ranges', 'bytes')
        rv.headers.add('Content-Length', str(length))
        return rv
    else:
        rv = send_file(INPUT_VIDEO_PATH, mimetype='video/mp4')
        rv.headers.add('Accept-Ranges', 'bytes')
        rv.headers.add('Content-Length', str(file_size))
        return rv

@app.route("/api/output_video")
def get_output_video():
    if not os.path.exists(OUTPUT_VIDEO_PATH):
        return jsonify({"error": "Output video not found"}), 404
    
    file_size = os.path.getsize(OUTPUT_VIDEO_PATH)
    range_header = request.headers.get('Range', None)
    
    if range_header:
        byte_start, byte_end = 0, None
        match = re.search(r'bytes=(\d+)-(\d*)', range_header)
        if match:
            byte_start = int(match.group(1))
            byte_end = int(match.group(2)) if match.group(2) else file_size - 1
        length = byte_end - byte_start + 1
        with open(OUTPUT_VIDEO_PATH, 'rb') as f:
            f.seek(byte_start)
            data = f.read(length)
        rv = Response(data, 206, mimetype='video/mp4', direct_passthrough=True)
        rv.headers.add('Content-Range', f'bytes {byte_start}-{byte_end}/{file_size}')
        rv.headers.add('Accept-Ranges', 'bytes')
        rv.headers.add('Content-Length', str(length))
        return rv
    else:
        rv = send_file(OUTPUT_VIDEO_PATH, mimetype='video/mp4')
        rv.headers.add('Accept-Ranges', 'bytes')
        rv.headers.add('Content-Length', str(file_size))
        return rv

@app.route("/api/analyze", methods=["POST"])
def analyze_video():
    if analysis_status["is_running"]:
        return jsonify({"error": "Analysis already in progress"}), 400
        
    thread = threading.Thread(target=run_analysis_pipeline)
    thread.daemon = True
    thread.start()
    
    return jsonify({"message": "Analysis started"})

@app.route("/api/status", methods=["GET"])
def get_status():
    return jsonify(analysis_status)

@app.route("/api/report", methods=["POST", "GET"])
def get_report():
    try:
        report_mod = load_module("app.backend.reporting.report_generator")
        report_mod.generate_pdf_report()
    except Exception as e:
        import traceback
        app.logger.error(f"Report generation error: {traceback.format_exc()}")
        return jsonify({"error": f"Report generation failed: {str(e)}"}), 500
    
    if os.path.exists(PDF_REPORT_PATH):
        return send_file(PDF_REPORT_PATH, as_attachment=True, download_name="traffic_report.pdf")
    return jsonify({"error": "PDF not found after generation. Check server logs."}), 404

@app.route("/api/send_report", methods=["POST"])
def send_report():
    data = request.json
    email = data.get("email")
    if not email:
        return jsonify({"error": "No email provided"}), 400
        
    try:
        report_mod = load_module("app.backend.reporting.report_generator")
        report_mod.generate_pdf_report()
        
        send_mod = load_module("app.api.email.email_sender")
        send_mod.dispatch_email(target_receiver_email=email)
        return jsonify({"message": f"Report successfully sent to {email}"})
    except Exception as e:
        app.logger.error(f"Send Report Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# --- RAG Chat Backend Instance ---
import importlib
rag_chat_mod = importlib.import_module("app.backend.rag.rag_chat")
rag_engine = rag_chat_mod.SimpleRAG()

@app.route("/api/chat", methods=["POST"])
def chat_bot():
    data = request.json
    if not data or "message" not in data:
        return jsonify({"error": "No message provided"}), 400
        
    query = data["message"]
    
    if analysis_status.get("completed") and "results" in analysis_status:
        rag_engine.build_knowledge_base(analysis_status["results"])
        
    response = rag_engine.answer_query(query)
    return jsonify({"reply": response})

if __name__ == "__main__":
    app.run(debug=False, port=5000)
