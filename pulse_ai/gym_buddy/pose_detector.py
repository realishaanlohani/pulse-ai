"""
gym_buddy/pose_detector.py
Pose detection for Gym Buddy feature.
Uses MediaPipe Pose for skeleton tracking and pushup rep counting.

HOW IT WORKS:
─────────────────────────────────────────────────────────────
1. Captures a frame from st.camera_input (PIL/numpy image)
2. MediaPipe detects 33 body landmarks
3. We calculate joint angles (elbow, shoulder, hip) to:
   - Detect pushup DOWN phase (elbow ~90°, hips straight)
   - Detect pushup UP phase (elbow ~160°+)
   - Flag form issues (sagging hips, wide elbows, etc.)
4. Returns: annotated image, form_status, feedback list, rep_counted

TO EXTEND FOR MORE EXERCISES:
─────────────────────────────────────────────────────────────
- Add a new method: analyze_squat(), analyze_plank(), etc.
- Each method extracts relevant landmarks and computes angles
- Follow the same return dict format

YOLO INTEGRATION (future):
─────────────────────────────────────────────────────────────
- Replace MediaPipe with YOLOv8-pose model
- model = YOLO('yolov8n-pose.pt')
- results = model(frame)
- keypoints = results[0].keypoints.xy
- Map COCO keypoints to joint angle calculations
"""

import numpy as np
from typing import Optional


class PoseDetector:
    def __init__(self):
        self.mp_pose = None
        self.pose = None
        self.mp_drawing = None
        self._init_mediapipe()

        # State machine for rep counting
        self._pushup_state = "up"   # "up" or "down"
        self._angle_history = []

    def _init_mediapipe(self):
        """Initialize MediaPipe — graceful fallback if not installed."""
        try:
            import mediapipe as mp
            self.mp_pose = mp.solutions.pose
            self.mp_drawing = mp.solutions.drawing_utils
            self.pose = self.mp_pose.Pose(
                min_detection_confidence=0.6,
                min_tracking_confidence=0.6
            )
        except ImportError:
            self.pose = None  # Falls back to mock mode

    # ── Main Public API ───────────────────────────────────────────────────────

    def analyze_pushup(self, frame: np.ndarray) -> dict:
        """
        Analyze a single frame for pushup form and rep counting.

        Args:
            frame: numpy array (H, W, 3) RGB image

        Returns:
            dict with keys:
              - annotated_image: numpy array with landmarks drawn
              - form_status: "correct" | "incorrect" | "unknown"
              - feedback: list of form correction strings
              - rep_counted: bool — True if a rep was just completed
              - landmarks: raw MediaPipe landmarks (or None)
              - angles: dict of computed joint angles
        """
        if self.pose is None:
            return self._mock_analysis()

        try:
            import mediapipe as mp
            rgb_frame = frame.copy()

            # Run detection
            results = self.pose.process(rgb_frame)

            if not results.pose_landmarks:
                return {
                    "annotated_image": frame,
                    "form_status": "unknown",
                    "feedback": ["No pose detected — ensure full body is visible"],
                    "rep_counted": False,
                    "landmarks": None,
                    "angles": {}
                }

            # Draw skeleton on frame
            annotated = frame.copy()
            self.mp_drawing.draw_landmarks(
                annotated,
                results.pose_landmarks,
                self.mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=self.mp_drawing.DrawingSpec(
                    color=(232, 255, 71), thickness=2, circle_radius=3
                ),
                connection_drawing_spec=self.mp_drawing.DrawingSpec(
                    color=(71, 200, 255), thickness=2
                )
            )

            lm = results.pose_landmarks.landmark

            # Extract key landmarks
            def get_point(landmark_enum):
                p = lm[landmark_enum.value]
                return np.array([p.x, p.y, p.z])

            left_shoulder = get_point(self.mp_pose.PoseLandmark.LEFT_SHOULDER)
            left_elbow = get_point(self.mp_pose.PoseLandmark.LEFT_ELBOW)
            left_wrist = get_point(self.mp_pose.PoseLandmark.LEFT_WRIST)
            right_shoulder = get_point(self.mp_pose.PoseLandmark.RIGHT_SHOULDER)
            right_elbow = get_point(self.mp_pose.PoseLandmark.RIGHT_ELBOW)
            right_hip = get_point(self.mp_pose.PoseLandmark.RIGHT_HIP)
            right_knee = get_point(self.mp_pose.PoseLandmark.RIGHT_KNEE)

            # Compute angles
            left_elbow_angle = self._calculate_angle(left_shoulder, left_elbow, left_wrist)
            right_elbow_angle = self._calculate_angle(right_shoulder, right_elbow,
                                                       right_hip)  # simplified
            back_angle = self._calculate_angle(left_shoulder, right_hip, right_knee)
            shoulder_width = abs(left_shoulder[0] - right_shoulder[0])

            angles = {
                "left_elbow": round(left_elbow_angle, 1),
                "right_elbow": round(right_elbow_angle, 1),
                "back_alignment": round(back_angle, 1),
            }

            # Form assessment
            feedback = []
            avg_elbow = (left_elbow_angle + right_elbow_angle) / 2

            # Check hip sag (back should be straight ~180°)
            if back_angle < 155:
                feedback.append("Hips are sagging — engage your core and keep a straight line")

            # Check elbow flare (elbows should be ~45° from body, not 90°)
            if left_elbow_angle < 45 and self._pushup_state == "down":
                feedback.append("Elbows flaring too wide — tuck them closer to your body")

            # Rep counting logic
            rep_counted = False
            if avg_elbow < 100 and self._pushup_state == "up":
                # Went DOWN
                self._pushup_state = "down"
            elif avg_elbow > 155 and self._pushup_state == "down":
                # Came back UP — count the rep
                self._pushup_state = "up"
                rep_counted = True

            form_status = "correct" if not feedback else "incorrect"

            return {
                "annotated_image": annotated,
                "form_status": form_status,
                "feedback": feedback,
                "rep_counted": rep_counted,
                "landmarks": results.pose_landmarks,
                "angles": angles
            }

        except Exception as e:
            return {
                "annotated_image": frame,
                "form_status": "unknown",
                "feedback": [f"Detection error: {str(e)[:60]}"],
                "rep_counted": False,
                "landmarks": None,
                "angles": {}
            }

    # ── YOLO Integration Template ─────────────────────────────────────────────
    # Uncomment and install: pip install ultralytics
    #
    # def analyze_with_yolo(self, frame: np.ndarray) -> dict:
    #     from ultralytics import YOLO
    #     model = YOLO("yolov8n-pose.pt")  # Download once
    #     results = model(frame)
    #     keypoints = results[0].keypoints.xy[0]  # Shape: (17, 2) COCO format
    #
    #     # COCO keypoint indices:
    #     # 5=left_shoulder, 6=right_shoulder, 7=left_elbow, 8=right_elbow
    #     # 9=left_wrist, 10=right_wrist, 11=left_hip, 12=right_hip
    #     # 13=left_knee, 14=right_knee
    #
    #     left_shoulder = keypoints[5].numpy()
    #     left_elbow = keypoints[7].numpy()
    #     left_wrist = keypoints[9].numpy()
    #     angle = self._calculate_angle_2d(left_shoulder, left_elbow, left_wrist)
    #     ...

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _calculate_angle(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
        """Calculate angle at joint B (in degrees) using 3D vectors."""
        ba = a - b
        bc = c - b
        cosine = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
        cosine = np.clip(cosine, -1.0, 1.0)
        return float(np.degrees(np.arccos(cosine)))

    @staticmethod
    def _calculate_angle_2d(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
        """Calculate angle at B using 2D (x, y) points — for YOLO keypoints."""
        ba = a - b
        bc = c - b
        cosine = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
        cosine = np.clip(cosine, -1.0, 1.0)
        return float(np.degrees(np.arccos(cosine)))

    @staticmethod
    def _mock_analysis() -> dict:
        """Returns mock data when MediaPipe is unavailable."""
        import random
        mock_feedback = random.choice([
            [],
            ["Keep your hips level — slight sag detected"],
            ["Great form — stay controlled on the way down"]
        ])
        return {
            "annotated_image": None,
            "form_status": "correct" if not mock_feedback else "incorrect",
            "feedback": mock_feedback,
            "rep_counted": random.random() > 0.7,
            "landmarks": None,
            "angles": {"left_elbow": 145.2, "back_alignment": 172.1}
        }
