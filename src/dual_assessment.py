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
        angles_front, _ = self.front_detector.detect_and_compute_angles(front_frame)
        angles_side, _ = self.side_detector.detect_and_compute_angles(side_frame)

        if not angles_front or not angles_side:
            return front_frame, None, None

        combined = (angles_front[0] + angles_side[0]) / 2.0
        angle_dict = self.front_detector.convert_angles_to_dict(combined)

        reba_score, reba_table = compute_reba_score(angle_dict)
        rula_score, rula_table = compute_rula_score(angle_dict)

        self.front_detector._send_data_async([], combined, reba_table, rula_table, reba_score, rula_score)

        return front_frame, reba_score, rula_score
