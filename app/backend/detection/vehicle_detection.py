"""
detection.py
============

Step 1: Vehicle Detection Module

Uses YOLOv8 (Ultralytics) to detect vehicles in a video file.
Draws bounding boxes with class names and confidence scores.

Supported vehicle classes: car, motorcycle, bus, truck

Usage:
    python -m src.detection
"""

import os
import cv2
from ultralytics import YOLO


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Resolve project root (one level up from src/) so paths work
# regardless of where the script is launched from
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

# Path to input video file
VIDEO_PATH = os.path.join(PROJECT_ROOT, "data", "input_videos", "input.mp4")

# Whether to save the output processed video, and where
SAVE_VIDEO = True
OUTPUT_VIDEO_PATH = os.path.join(PROJECT_ROOT, "data", "processed_videos", "detection_output.mp4")

# YOLOv8 small model — best accuracy/speed tradeoff for vehicle detection
# Options: yolov8n.pt (fastest) | yolov8s.pt (balanced) | yolov8m.pt (heavy)
MODEL_NAME = os.path.join(PROJECT_ROOT, "models", "yolo", "yolov8s.pt")

# COCO class IDs for vehicles we care about
# Reference: https://docs.ultralytics.com/datasets/detect/coco/
VEHICLE_CLASSES = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
}

# Minimum confidence score to keep a detection
# Lower = more detections (may include some false positives)
# Higher = fewer but more confident detections
CONFIDENCE_THRESHOLD = 0.25

# Inference image size — higher = better detection of small/distant vehicles
# but slower processing. Match roughly to your video resolution.
# Options: 640 (fast) | 960 (balanced) | 1280 (best, slow)
INFERENCE_SIZE = 960

# Frame skipping to prevent lag on low-end systems
# 1 = process every frame (high accuracy, very slow)
# 2 = process every 2nd frame (smooth + good accuracy)
# 3 = process every 3rd frame (very fast, no lag)
PROCESS_EVERY_N_FRAMES = 2

# Colors for bounding boxes (BGR format) — one per vehicle type
BOX_COLORS = {
    "car":        (0, 255, 0),    # Green
    "motorcycle": (255, 165, 0),  # Orange
    "bus":        (0, 255, 255),  # Yellow
    "truck":      (0, 0, 255),    # Red
}


# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------

def load_model(model_name: str = MODEL_NAME) -> YOLO:
    """
    Load the YOLOv8 model.

    The model weights are downloaded automatically on first run
    and cached locally for subsequent runs.

    Args:
        model_name: Name of the YOLO model (e.g. 'yolov8n.pt').

    Returns:
        Loaded YOLO model object.
    """
    print(f"[INFO] Loading model: {model_name}")
    model = YOLO(model_name)
    print("[INFO] Model loaded successfully.")
    return model


def detect_vehicles(frame, model: YOLO,
                    confidence_threshold: float = CONFIDENCE_THRESHOLD) -> list:
    """
    Run YOLOv8 inference on a single frame and filter for vehicles only.

    Args:
        frame: Input image (numpy array, BGR format from OpenCV).
        model: Loaded YOLO model.
        confidence_threshold: Minimum confidence to keep a detection.

    Returns:
        List of detections. Each detection is a dict with keys:
            - 'bbox': (x1, y1, x2, y2) as integers
            - 'class_name': e.g. 'car', 'truck'
            - 'confidence': float between 0 and 1
    """
    # Run inference at higher resolution for better small-vehicle detection
    # verbose=False suppresses YOLO's own logging per frame
    results = model(frame, imgsz=INFERENCE_SIZE, verbose=False)[0]

    detections = []

    for box in results.boxes:
        # Get class ID and confidence
        class_id = int(box.cls[0])
        confidence = float(box.conf[0])

        # Skip if not a vehicle class or below threshold
        if class_id not in VEHICLE_CLASSES:
            continue
        if confidence < confidence_threshold:
            continue

        # Extract bounding box coordinates
        x1, y1, x2, y2 = box.xyxy[0]

        detections.append({
            "bbox": (int(x1), int(y1), int(x2), int(y2)),
            "class_name": VEHICLE_CLASSES[class_id],
            "confidence": round(confidence, 2),
        })

    return detections


def draw_detections(frame, detections: list):
    """
    Draw bounding boxes, class names, and confidence scores on the frame.

    Args:
        frame: Input image (numpy array, modified in-place).
        detections: List of detection dicts from detect_vehicles().

    Returns:
        Annotated frame with bounding boxes drawn.
    """
    for det in detections:
        x1, y1, x2, y2 = det["bbox"]
        label = det["class_name"]
        conf = det["confidence"]
        color = BOX_COLORS.get(label, (255, 255, 255))

        # Draw the bounding box rectangle
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

        # Prepare label text: "car 0.87"
        text = f"{label} {conf:.2f}"

        # Calculate text size for the background rectangle
        (text_w, text_h), baseline = cv2.getTextSize(
            text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1
        )

        # Draw filled rectangle behind text for readability
        cv2.rectangle(
            frame,
            (x1, y1 - text_h - baseline - 4),
            (x1 + text_w, y1),
            color,
            cv2.FILLED,
        )

        # Draw the label text (black text on colored background)
        cv2.putText(
            frame, text,
            (x1, y1 - baseline - 2),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6,
            (0, 0, 0), 1, cv2.LINE_AA,
        )

    return frame


def process_video(video_path: str = VIDEO_PATH, model: YOLO = None):
    """
    Main function — processes a video file frame-by-frame:
      1. Read each frame
      2. Detect vehicles
      3. Draw bounding boxes
      4. Display in a window
      5. Press 'q' to quit

    Args:
        video_path: Path to the input video file.
        model: Pre-loaded YOLO model (loaded automatically if None).
    """
    # Load model if not provided
    if model is None:
        model = load_model()

    # Open the video file
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print(f"[ERROR] Cannot open video: {video_path}")
        print("[HINT]  Place your traffic video at 'data/input.mp4'")
        return

    # Get video properties for display
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    print(f"[INFO] Video opened: {video_path}")
    print(f"[INFO] Resolution: {width}x{height} | FPS: {fps:.1f} | Frames: {total_frames}")
    print("[INFO] Press 'q' to quit the video window.")

    # Initialize VideoWriter if saving
    out_video = None
    if SAVE_VIDEO:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v') # Codec for .mp4
        out_video = cv2.VideoWriter(OUTPUT_VIDEO_PATH, fourcc, fps, (width, height))
        print(f"[INFO] Saving output video to: {OUTPUT_VIDEO_PATH}")

    frame_count = 0
    last_detections = []

    while True:
        # Read the next frame
        ret, frame = cap.read()

        # End of video
        if not ret:
            print("[INFO] End of video reached.")
            break

        frame_count += 1

        # --- Step 1: Detect vehicles (or use previous detections) ---
        # We only run YOLO inference every N frames. On skipped frames,
        # we reuse the previous bounding boxes. This keeps the video smooth!
        if frame_count % PROCESS_EVERY_N_FRAMES == 1 or PROCESS_EVERY_N_FRAMES == 1:
            detections = detect_vehicles(frame, model)
            last_detections = detections
        else:
            detections = last_detections

        # --- Step 2: Draw bounding boxes on the frame ---
        annotated_frame = draw_detections(frame, detections)

        # --- Step 3: Add frame info overlay (top-left corner) ---
        info_text = f"Frame: {frame_count}/{total_frames} | Vehicles: {len(detections)}"
        cv2.putText(
            annotated_frame, info_text,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.8,
            (255, 255, 255), 2, cv2.LINE_AA,
        )

        # --- Step 4: Show the frame in a window ---
        cv2.imshow("Traffic Detection - YOLOv8", annotated_frame)

        # --- Step 4.5: Save video frame if enabled ---
        if out_video is not None:
            out_video.write(annotated_frame)

        # --- Step 5: Wait for key press (1ms = real-time speed) ---
        # Press 'q' to quit early
        if cv2.waitKey(1) & 0xFF == ord("q"):
            print("[INFO] User pressed 'q' — exiting.")
            break

    # Cleanup
    cap.release()
    if out_video is not None:
        out_video.release()
    cv2.destroyAllWindows()
    print(f"[INFO] Processed {frame_count} frames.")


# ---------------------------------------------------------------------------
# Entry point — run this file directly to test detection
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    process_video()
