"""
2_tracking.py
===========

Step 2: Vehicle Tracking Module

Uses Ultralytics' built-in ByteTrack (bundled with the ultralytics package)
to assign unique IDs to detected vehicles and track them across frames.

No extra installation required — ByteTrack ships with ultralytics.

ByteTrack is a state-of-the-art tracker that outperforms SORT, especially
in crowded scenes with partial occlusions.

Supported vehicle classes: car, motorcycle, bus, truck

Usage:
    python -m src.tracking
"""

import os
import cv2
import subprocess
import imageio
import imageio_ffmpeg
import torch
from ultralytics import YOLO
import collections

# Optimize CPU thread allocation to prevent thrashing on low-end processors
torch.set_num_threads(4)

# Global state for trajectory trails (short trails)
track_history = collections.defaultdict(lambda: collections.deque(maxlen=12))
# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Resolve project root (one level up from src/)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

# Path to input video file
VIDEO_PATH = os.path.join(PROJECT_ROOT, "data", "input_videos", "input.mp4")

# Whether to save the output video, and where
SAVE_VIDEO = True
OUTPUT_VIDEO_PATH = os.path.join(PROJECT_ROOT, "data", "processed_videos", "tracking_output.mp4")

# Set to False to run headless (no display window) for faster background processing.
# Useful when you just want the full output .mp4 without watching it live.
SHOW_WINDOW = True

# YOLOv8 Nano — lightest model for CPU, but we compensate for its size
# by feeding it high-resolution frames (800) so it doesn't miss small cars.
MODEL_NAME = os.path.join(PROJECT_ROOT, "models", "yolo", "yolov8n.pt")

# COCO class IDs for vehicles we care about
VEHICLE_CLASS_IDS = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
}

# Lower threshold = catch more cars (especially distant/partially visible ones)
# ByteTrack will filter out ghost detections that don't persist across frames
CONFIDENCE_THRESHOLD = 0.05
# 640 is much faster for CPU while maintaining reasonable accuracy.
INFERENCE_SIZE = 640

# Skip frames to speed up processing (3x faster tracking on CPU)
PROCESS_EVERY_N_FRAMES = 3

# Colors per vehicle class for bounding boxes (BGR)
BOX_COLORS = {
    "car":        (0, 255, 0),    # Green
    "motorcycle": (255, 165, 0),  # Orange
    "bus":        (0, 255, 255),  # Yellow
    "truck":      (0, 0, 255),    # Red
}

DEFAULT_COLOR = (200, 200, 200)  # Fallback grey


# ---------------------------------------------------------------------------
# Model Loading
# ---------------------------------------------------------------------------

def load_model(model_name: str = MODEL_NAME) -> YOLO:
    """
    Load the YOLOv8 model.

    Args:
        model_name: YOLO model filename (e.g. 'yolov8n.pt').

    Returns:
        Loaded YOLO model object.
    """
    print(f"[INFO] Loading model: {model_name}")
    model = YOLO(model_name)
    print("[INFO] Model loaded successfully.")
    return model


# ---------------------------------------------------------------------------
# Tracking (Detection + Tracking in one call via Ultralytics)
# ---------------------------------------------------------------------------

def track_vehicles(frame, model: YOLO) -> list:
    """
    Run YOLOv8 + ByteTrack on a single frame and return tracked vehicles.

    Ultralytics' model.track() runs detection AND tracking in one call.
    ByteTrack is used by default — no extra installation needed.

    Args:
        frame: Input BGR image (numpy array from OpenCV).
        model: Loaded YOLO model.

    Returns:
        List of tracked vehicle dicts, each with:
            - 'track_id':   int — unique stable ID across frames
            - 'bbox':       (x1, y1, x2, y2) as integers
            - 'class_name': e.g. 'car', 'truck'
            - 'confidence': float
    """
    # model.track() runs YOLOv8 detection + ByteTrack tracking in one step.
    # persist=True tells the tracker to maintain state between frames (critical!).
    # verbose=False suppresses per-frame YOLO logging.
    results = model.track(
        frame,
        imgsz=INFERENCE_SIZE,
        conf=CONFIDENCE_THRESHOLD,
        iou=0.4,           # Tighter NMS: reduce duplicate/overlapping boxes
        persist=True,      # Keep tracker state alive across frames
        tracker="bytetrack.yaml",  # Use ByteTrack (bundled with ultralytics)
        classes=list(VEHICLE_CLASS_IDS.keys()),  # Only detect vehicles (skip people/animals → faster)
        max_det=100,       # Cap detections per frame to avoid slowdown in dense scenes
        verbose=False,
    )[0]

    tracked = []

    for box in results.boxes:
        # Skip if tracker hasn't assigned an ID yet (e.g. on first seen frame)
        if box.id is None:
            continue

        class_id = int(box.cls[0])

        # Only keep vehicle classes we care about
        if class_id not in VEHICLE_CLASS_IDS:
            continue

        track_id   = int(box.id[0])
        confidence = float(box.conf[0])
        x1, y1, x2, y2 = box.xyxy[0]

        tracked.append({
            "track_id":   track_id,
            "bbox":       (int(x1), int(y1), int(x2), int(y2)),
            "class_name": VEHICLE_CLASS_IDS[class_id],
            "confidence": round(confidence, 2),
        })

    return tracked


# ---------------------------------------------------------------------------
# Drawing
# ---------------------------------------------------------------------------

def draw_tracked_vehicles(frame, tracked_vehicles: list):
    """
    Draw bounding boxes and vehicle IDs on the frame.

    Each vehicle is annotated with:
      - Colored bounding box (per class)
      - Label: "<class_name>  ID: <id>" on a filled background

    Args:
        frame: BGR image (numpy array), drawn on in-place.
        tracked_vehicles: List of dicts from track_vehicles().

    Returns:
        Annotated frame.
    """
    for vehicle in tracked_vehicles:
        x1, y1, x2, y2 = vehicle["bbox"]
        track_id   = vehicle["track_id"]
        class_name = vehicle["class_name"]
        color      = BOX_COLORS.get(class_name, DEFAULT_COLOR)

        # ── Trajectory Trail ──
        cx = int((x1 + x2) / 2)
        cy = int((y1 + y2) / 2)
        track_history[track_id].append((cx, cy))

        pts = list(track_history[track_id])
        for i in range(1, len(pts)):
            # Tapering thickness for comet tail effect
            thickness = int(max(1, (i / len(pts)) * 6))
            # Trail color explicitly set to Blue (BGR: 255, 0, 0)
            cv2.line(frame, pts[i - 1], pts[i], (255, 0, 0), thickness, cv2.LINE_AA)

        # Draw bounding box
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

        # Build label: "car  ID: 5"
        label = f"{class_name}  ID: {track_id}"

        # Measure text for background rectangle sizing
        (text_w, text_h), baseline = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1
        )

        # Draw filled background rectangle above the box
        cv2.rectangle(
            frame,
            (x1, y1 - text_h - baseline - 4),
            (x1 + text_w, y1),
            color,
            cv2.FILLED,
        )

        # Draw label in black text over the colored background
        cv2.putText(
            frame, label,
            (x1, y1 - baseline - 2),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6,
            (0, 0, 0), 1, cv2.LINE_AA,
        )

    return frame


# ---------------------------------------------------------------------------
# Main Video Processing Loop
# ---------------------------------------------------------------------------

def process_video(video_path: str = VIDEO_PATH, model: YOLO = None, show_window: bool = SHOW_WINDOW, progress_callback=None):
    """
    Main entry point — processes a video file frame-by-frame:
      1. Detect + track vehicles using YOLOv8 + ByteTrack
      2. Draw bounding boxes and unique vehicle IDs
      3. Display live window | save output video | press 'q' to quit

    Args:
        video_path: Path to input video file.
        model: Pre-loaded YOLO model (auto-loaded if None).
        show_window: Whether to display the live tracking window.
        progress_callback: Function to call with live logs
    """
    if model is None:
        model = load_model(MODEL_NAME)

    # Step 3: Data extractor — collects per-frame stats and saves CSV at the end
    # Try both import styles: module (python -m src.2_tracking) and direct (python 2_tracking.py)
    import importlib
    try:
        data_ext = importlib.import_module("app.backend.utils.data_extraction")
    except ImportError:
        data_ext = importlib.import_module("app.backend.utils.data_extraction")
    extractor = data_ext.DataExtractor()

    # Open the video file
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"[ERROR] Cannot open video: {video_path}")
        print("[HINT]  Place your traffic video at 'data/input.mp4'")
        return

    # Read video properties
    fps          = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width        = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height       = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    print(f"[INFO] Video: {video_path}")
    print(f"[INFO] Resolution: {width}x{height} | FPS: {fps:.1f} | Frames: {total_frames}")
    print("[INFO] Press 'q' to quit the window.")

    # Set up VideoWriter if saving is enabled
    out_video = None
    TEMP_VIDEO_PATH = OUTPUT_VIDEO_PATH + ".raw.mp4"
    if SAVE_VIDEO:
        os.makedirs(os.path.dirname(OUTPUT_VIDEO_PATH), exist_ok=True)
        # Write raw frames first to a temp file; we will re-encode with faststart afterwards
        out_video = imageio.get_writer(TEMP_VIDEO_PATH, fps=fps, codec='libx264', quality=8)
        print(f"[INFO] Output will be saved to (H.264): {OUTPUT_VIDEO_PATH}")


    frame_count      = 0
    last_tracked     = []   # Cache tracked results for skipped frames

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[INFO] End of video reached.")
            break

        frame_count += 1

        # Processing cap — stop at 1000 frames for performance
        # (real total is preserved in total_frames for reporting)
        if frame_count > 1000:
            print("[INFO] Reached 1000 frames limit. Stopping video processing.")
            break

        # ----------------------------------------------------------------
        # Step 1+2 — Detection + Tracking (skipped on intermediate frames)
        # ----------------------------------------------------------------
        # On skipped frames we reuse the last result. The tracker's internal
        # Kalman filter state is preserved via persist=True, so IDs stay stable.
        if frame_count % PROCESS_EVERY_N_FRAMES == 1 or PROCESS_EVERY_N_FRAMES == 1:
            last_tracked = track_vehicles(frame, model)

        tracked_vehicles = last_tracked

        # ----------------------------------------------------------------
        # Step 3 — Extract data for this frame (speed + class counts)
        # ----------------------------------------------------------------
        extractor.update(frame_count, tracked_vehicles)

        # ----------------------------------------------------------------
        # Step 4 — Draw tracked vehicles on the frame
        # ----------------------------------------------------------------
        annotated_frame = draw_tracked_vehicles(frame, tracked_vehicles)

        # ----------------------------------------------------------------
        # Step 4 — Info overlay (top-left corner)
        # ----------------------------------------------------------------
        info_text = (
            f"Frame: {frame_count}/{total_frames}  |  "
            f"Tracked vehicles: {len(tracked_vehicles)}"
        )
        cv2.putText(
            annotated_frame, info_text,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.8,
            (255, 255, 255), 2, cv2.LINE_AA,
        )

        # ----------------------------------------------------------------
        # Step 5 — Save frame to output video
        # ----------------------------------------------------------------
        if out_video is not None:
            # OpenCV is BGR, but imageio expects RGB for correct colors
            rgb_frame = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
            out_video.append_data(rgb_frame)


        # ----------------------------------------------------------------
        # Step 6 — Display window (only if show_window = True)
        # ----------------------------------------------------------------
        if show_window:
            cv2.imshow("Traffic Tracking - ByteTrack + YOLOv8", annotated_frame)

            # FPS-locked wait: cap display speed to match the video's natural FPS.
            # waitKey(1) causes uncapped speed — user quits early thinking video ended.
            # Using 1000/fps (e.g. 100ms for a 10 FPS video) fixes this.
            wait_ms = max(1, int(1000 / fps))
            if cv2.waitKey(wait_ms) & 0xFF == ord("q"):
                print("[INFO] User pressed 'q' — exiting.")
                break

        # ----------------------------------------------------------------
        # Step 7 — Terminal progress (every 50 frames)
        # Report progress against the CAPPED limit (1000), not total_frames,
        # so the UI progress bar reaches 100% when processing finishes.
        # ----------------------------------------------------------------
        cap_limit = min(total_frames, 1000)
        if frame_count % 50 == 0 or frame_count == cap_limit:
            pct = min((frame_count / cap_limit) * 100, 100.0)
            log_msg = f"Progress: {frame_count}/{cap_limit} frames analysed ({pct:.1f}%) | Vehicles: {len(tracked_vehicles)}"
            print(f"[INFO] {log_msg}")
            if progress_callback:
                progress_callback(log_msg, pct)

    # Save extracted data to CSV before releasing resources
    extractor.save()

    # Release resources
    cap.release()
    if out_video is not None:
        out_video.close()
        
        # Re-encode with faststart so the browser can stream without downloading entire file first
        try:
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            print("[INFO] Re-encoding output video for browser compatibility (faststart)...")
            subprocess.run([
                ffmpeg_exe, '-y', '-i', TEMP_VIDEO_PATH,
                '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '23',
                '-pix_fmt', 'yuv420p',
                '-movflags', '+faststart',
                OUTPUT_VIDEO_PATH
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            os.remove(TEMP_VIDEO_PATH)
            print(f"[INFO] Web-compatible output saved: {OUTPUT_VIDEO_PATH}")
        except Exception as e:
            print(f"[WARN] faststart re-encode failed ({e}), using raw temp file.")
            if os.path.exists(TEMP_VIDEO_PATH):
                import shutil
                shutil.move(TEMP_VIDEO_PATH, OUTPUT_VIDEO_PATH)

    cv2.destroyAllWindows()

    print(f"[INFO] Finished. Processed {frame_count} frames out of {total_frames} total.")
    if SAVE_VIDEO:
        print(f"[INFO] Saved output to: {OUTPUT_VIDEO_PATH}")

    # Return metadata so app.py can use it without re-opening the video file
    return {
        "real_total_frames": total_frames,    # actual frame count of the video file
        "processed_frames":  frame_count,     # how many frames were actually analysed
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    process_video()
