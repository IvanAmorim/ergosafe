from typing import Tuple
import cv2
from .inference import YoloPoseSkeleton
from .reba_score import compute_reba_score
from .rula_score import compute_rula_score

class DualCameraAssessment:
    """Combine two camera views (front and side) for ergonomic assessment."""
    def __init__(self, front_cam_id: int, side_cam_id: int, operator: str = "default"):
        self.front_detector = YoloPoseSkeleton(cam_id=front_cam_id, operator=operator)
        self.side_detector = YoloPoseSkeleton(cam_id=side_cam_id, operator=operator)

    def process(self, front_frame, side_frame) -> Tuple[cv2.Mat, float, float]:
        """Process frames from both cameras and compute combined scores.

        The front camera is responsible for elbow flexion and shoulder
        abduction angles while the side camera provides the remaining
        posture information. The resulting angle vector is sent for REBA
        and RULA scoring.
        """

        angles_front, annotated_front = self.front_detector.detect_and_compute_angles(front_frame)
        angles_side, _ = self.side_detector.detect_and_compute_angles(side_frame)

        if not angles_front or not angles_side:
            return front_frame, None, None

        # Use side view as base and overwrite specific angles from the front
        combined = angles_side[0].copy()
        combined[0] = angles_front[0][0]  # left elbow flexion
        combined[1] = angles_front[1][0]  # right elbow flexion
        combined[4] = angles_front[4][0]  # left shoulder abduction
        combined[5] = angles_front[5][0]  # right shoulder abduction

        angle_dict = self.front_detector.convert_angles_to_dict(combined)

        reba_score, reba_table = compute_reba_score(angle_dict)
        rula_score, rula_table = compute_rula_score(angle_dict)

        self.front_detector._send_data_async([], combined, reba_table, rula_table, reba_score, rula_score)

        return annotated_front, reba_score, rula_score
