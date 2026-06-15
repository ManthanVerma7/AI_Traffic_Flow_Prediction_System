"""
step3_data_extraction.py
==================

Step 3: Data Extraction & CSV Generation

Processes per-frame tracking output to extract structured traffic data
and saves it as a consistent, high-quality CSV dataset.

Fixes Applied:
1. Unique Vehicle Count: Uses a historical set of all seen IDs.
2. Vehicle Type Counts: Properly tracks and counts classes (car, motorcycle, bus, truck).
3. Average Speed: Tracks centroids using previous_positions dict and skips zeroes safely.
4. Consistency: Ensures clean numeric output in a standardized CSV format.

Usage logic:
    extractor = DataExtractor()
    extractor.update(frame_number, tracked_vehicles)
    extractor.save()
"""

import os
import math
import pandas as pd


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
CSV_OUTPUT_PATH = os.path.join(PROJECT_ROOT, "data", "csv", "output.csv")


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def get_centroid(bbox: tuple) -> tuple:
    """
    Compute the center point (cx, cy) of a bounding box.
    bbox format is (x1, y1, x2, y2).
    """
    x1, y1, x2, y2 = bbox
    cx = (x1 + x2) / 2.0
    cy = (y1 + y2) / 2.0
    return (cx, cy)


def euclidean_distance(p1: tuple, p2: tuple) -> float:
    """
    Calculate straight-line distance between two 2D points (pixels).
    """
    return math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)


# ---------------------------------------------------------------------------
# Core Class: DataExtractor
# ---------------------------------------------------------------------------

class DataExtractor:
    """
    Maintains the state required for generating an accurate dataset.
    - previous_positions: {id: (cx, cy)} for calculating speed.
    - all_seen_ids: set() to track unique vehicles over the entire video.
    """

    def __init__(self):
        # Stores the final rows that will become the CSV
        self.dataset = []
        
        # State trackers for critical fixes
        self.previous_positions = {}  # Dictionary to track previous frame's center points {id: (cx, cy)}
        self.all_seen_ids       = set() # Global set of all unique tracking IDs seen across all frames
        self.last_valid_speed   = 0.0   # To handle zero-speed due to skipped frames

    def update(self, frame_number: int, tracked_vehicles: list):
        """
        Process a single frame and extract all required data points.
        
        Args:
            frame_number: The current frame index.
            tracked_vehicles: List of dicts. Each dict MUST have:
                              'track_id', 'bbox', 'class_name', 'confidence'.
        """
        # --- 1. Vehicle Type Counts ---
        count_car        = 0
        count_motorcycle = 0
        count_bus        = 0
        count_truck      = 0

        # --- 2. Speed Tracking ---
        current_positions = {}
        speeds_this_frame = []

        for vehicle in tracked_vehicles:
            track_id   = vehicle["track_id"]
            class_name = vehicle["class_name"].lower() # Ensure consistency
            bbox       = vehicle["bbox"]

            # Fix: Update global unique seen vehicles
            self.all_seen_ids.add(track_id)

            # Fix: Correctly count vehicles per class
            if class_name == "car":
                count_car += 1
            elif class_name == "motorcycle":
                count_motorcycle += 1
            elif class_name == "bus":
                count_bus += 1
            elif class_name == "truck":
                count_truck += 1

            # Fix: Compute pixel displacement for Average Speed
            cx, cy = get_centroid(bbox)
            current_positions[track_id] = (cx, cy)

            if track_id in self.previous_positions:
                prev_cx, prev_cy = self.previous_positions[track_id]
                distance = euclidean_distance((prev_cx, prev_cy), (cx, cy))
                speeds_this_frame.append(distance)

        # Update previous_positions dictionary for the next frame
        self.previous_positions = current_positions

        # Compute average speed for this frame
        if len(speeds_this_frame) > 0:
            avg_speed_px = sum(speeds_this_frame) / len(speeds_this_frame)
            
            # Handle frame-skipping artifacts (where distance is instantly 0.0)
            if avg_speed_px == 0.0 and self.last_valid_speed > 0.0:
                avg_speed_px = self.last_valid_speed
            else:
                self.last_valid_speed = avg_speed_px
        else:
            avg_speed_px = 0.0

        # --- 3. Compile Frame Data ---
        # Data Consistency: ensuring all values are numeric
        frame_data = {
            "frame_number":     int(frame_number),
            "total_vehicles":   int(len(tracked_vehicles)),
            "unique_vehicles":  int(len(self.all_seen_ids)),
            "count_car":        int(count_car),
            "count_motorcycle": int(count_motorcycle),
            "count_bus":        int(count_bus),
            "count_truck":      int(count_truck),
            "avg_speed_px":     round(float(avg_speed_px), 2),
        }

        self.dataset.append(frame_data)


    # -----------------------------------------------------------------------
    # CSV Export
    # -----------------------------------------------------------------------

    def save(self, output_path: str = CSV_OUTPUT_PATH):
        """
        Convert the accumulated dataset to a Pandas DataFrame and save to CSV.
        """
        if not self.dataset:
            print("[WARN] No data was extracted. Dataset is empty.")
            return

        # Ensure consistent column ordering as requested
        cols = [
            "frame_number",
            "total_vehicles",
            "unique_vehicles",
            "count_car",
            "count_motorcycle",
            "count_bus",
            "count_truck",
            "avg_speed_px"
        ]
        
        df = pd.DataFrame(self.dataset)
        df = df[cols]

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        
        print("\n" + "="*50)
        print(f"[INFO] DATA EXTRACTION COMPLETE")
        print(f"[INFO] Dataset saved to: {output_path}")
        print(f"[INFO] Total frames recorded : {len(df)}")
        print(f"[INFO] Total unique vehicles : {df['unique_vehicles'].iloc[-1]}")
        print("="*50 + "\n")
        
        return df


# ---------------------------------------------------------------------------
# Simple Test Block
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("[INFO] Testing Data Extraction logic...")
    extractor = DataExtractor()
    
    # Mock Frame 1
    extractor.update(1, [
        {"track_id": 1, "class_name": "car", "bbox": (10, 10, 20, 20), "confidence": 0.9},
        {"track_id": 2, "class_name": "bus", "bbox": (100, 100, 150, 150), "confidence": 0.8}
    ])
    
    # Mock Frame 2 (Vehicles moved by 10 pixels roughly)
    extractor.update(2, [
        {"track_id": 1, "class_name": "car", "bbox": (18, 18, 28, 28), "confidence": 0.9},
        {"track_id": 2, "class_name": "bus", "bbox": (110, 110, 160, 160), "confidence": 0.8},
        {"track_id": 3, "class_name": "motorcycle", "bbox": (50, 50, 60, 60), "confidence": 0.7}
    ])
    
    df = extractor.save()
    print(df.head())
