from ultralytics import YOLO
import numpy as np
import cv2
import torch
import math

class YoloPoseSkeleton:
    def __init__(self, model_path="yolov8n-pose.pt", device=None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = YOLO(model_path)

    def detect_and_compute_angles(self, frame):
        results = self.model.predict(frame, device=self.device, verbose=False)
        annotated = results[0].plot()

        angles_per_person = []

        if not results or not results[0].keypoints:
            return [], annotated

        keypoints_all = results[0].keypoints.data.cpu().numpy()  # shape: (n, 17, 3)

        for kp in keypoints_all:
            # Converter para lista (x, y, score)
            keypoints = [(x, y, c) for x, y, c in kp]

            # Preencher a lista de 33 pontos como MediaPipe para compatibilidade
            landmarks = np.zeros((33, 3), dtype=np.float32)
            index_map = {
                0: 0,   # nose
                5: 11,  # left_shoulder
                6: 12,  # right_shoulder
                7: 13,  # left_elbow
                8: 14,  # right_elbow
                9: 15,  # left_wrist
                10: 16, # right_wrist
                11: 23, # left_hip
                12: 24, # right_hip
                13: 25, # left_knee
                14: 26, # right_knee
                15: 27, # left_ankle
                16: 28, # right_ankle
            }

            for yolo_idx, mp_idx in index_map.items():
                x, y, c = keypoints[yolo_idx]
                landmarks[mp_idx] = [x / frame.shape[1], y / frame.shape[0], 0.0]

            angles = self.compute_angles(landmarks)
            angles_per_person.append(angles)

        return angles_per_person, annotated

    def compute_angles(self, l):
        angles = np.zeros((15, 1))
        shoulder_dist = 0.3

        def eq(p1, p2, p3, inv=False):
            x1, y1, _ = p1
            x2, y2, _ = p2
            x3, y3, _ = p3
            slope1 = (y2 - y1) / (x2 - x1 + 1e-6)
            slope2 = (y3 - y2) / (x3 - x2 + 1e-6)
            angle = abs(math.atan(slope1) - math.atan(slope2))
            deg = math.degrees(angle)
            if not inv:
                if slope1 > slope2: deg = 180 - deg
            else:
                if slope1 < slope2: deg = 180 - deg
            return deg

        def eq3d(p1, p2, p3):
            v1 = np.array(p2) - np.array(p1)
            v2 = np.array(p3) - np.array(p2)
            dot = np.dot(v1, v2)
            norm = np.linalg.norm(v1) * np.linalg.norm(v2)
            if norm == 0: return 0
            angle = math.acos(np.clip(dot / norm, -1.0, 1.0))
            return math.degrees(angle)

        try:
            angles[0] = 180 - eq(l[11], l[13], l[15])  # left elbow
            angles[1] = eq(l[12], l[14], l[16])        # right elbow
            angles[2] = 0  # no hand landmark
            angles[3] = 0
            angles[4] = eq(l[13], l[11], l[23]) - 15
            angles[5] = eq(l[14], l[12], l[24], inv=True) - 15
            angles[6] = eq(l[11], l[23], l[25], inv=True)
            angles[7] = eq(l[12], l[24], l[26])
            angles[8] = eq(l[23], l[25], l[27])
            angles[9] = 180 - eq(l[24], l[26], l[28])
            mid_shoulder = (l[11] + l[12]) / 2
            mid_hip = (l[23] + l[24]) / 2
            neck_base = (mid_shoulder + mid_hip) / 2
            angles[10] = abs(eq3d(l[0], mid_shoulder, neck_base) - 80)
            angles[11] = eq3d(l[0], mid_shoulder, neck_base)
            angles[12] = abs(eq(mid_shoulder, mid_hip, (l[25]+l[26])/2) - 15)
            angles[13] = 0
            twisted_trunk = math.dist(l[11], l[12])
            angles[14] = 60 if twisted_trunk / shoulder_dist > 1.5 else twisted_trunk
        except Exception:
            angles = np.zeros((15, 1))  # fallback em caso de erro

        return angles
