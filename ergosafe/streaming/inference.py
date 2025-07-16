from ultralytics import YOLO
import numpy as np
import cv2
import torch
import math
from ergosafe.influx.influx import (
    send_pose_data,
    send_reba_table,
    send_rula_table,
)
from ergosafe.scoring.reba_score import compute_reba_score
from ergosafe.scoring.rula_score import compute_rula_score
from datetime import datetime
import threading

class YoloPoseSkeleton:
    def __init__(self, model_path="yolov8n-pose.pt", device=None, cam_id=1, operator="default"):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = YOLO(model_path)
        self.cam_id = cam_id
        self.operator = operator
        self.batch_cnt = 0
        self.reba_scores = []
        self.reba_tables = []
        self.rula_scores = []
        self.rula_tables = []
        
    def _send_data_async(self, keypoints, angles, reba_table, rula_table, reba_score, rula_score):
        def send():
            send_reba_table(self.cam_id, reba_table, operator=self.operator)
            send_rula_table(self.cam_id, rula_table, operator=self.operator)
            send_pose_data(f"{self.cam_id}", keypoints, angles, reba_score, rula_score, operator=self.operator)
        threading.Thread(target=send, daemon=True).start()


    def detect_and_compute_angles(self, frame):
        results = self.model.predict(frame, device=self.device, verbose=False)
        if not results or not hasattr(results[0], 'keypoints') or results[0].keypoints is None:
            return [], frame  # Nenhum esqueleto detetado

        if results[0].keypoints.conf is None:
            return [], frame  # Confiança ausente (possível erro no modelo ou frame inválido)

        keypoints_all = results[0].keypoints.data.cpu().numpy()  # shape: (n, 17, 3)
        conf_tensor = results[0].keypoints.conf.cpu().numpy()    # (n, 17)

        # # Filtrar e selecionar pessoa mais centrada com confiança >= 0.7
        candidatos = []
        for idx, kp in enumerate(keypoints_all):
            conf = conf_tensor[idx].mean()
            if conf >= 0.7:
                x_center = kp[:, 0].mean()
                y_center = kp[:, 1].mean()
                dist_center = math.hypot(x_center - frame.shape[1] / 2, y_center - frame.shape[0] / 2)
                candidatos.append((dist_center, idx, conf))

        if not candidatos:
            return [], frame  # nenhum candidato com confiança suficiente

        candidatos.sort(key=lambda x: x[0])
        _, best_idx, best_conf = candidatos[0]


        kp = keypoints_all[best_idx]
        keypoints = [(x, y, c) for x, y, c in kp]

        # Inicializar landmarks compatíveis com MediaPipe
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

        # === Desenhar keypoints e traços ===
        annotated = frame.copy()
        for x, y, c in keypoints:
            if c > 0.7:
                cv2.circle(annotated, (int(x), int(y)), 4, (0, 255, 0), -1)

        # Definir pares de ligação (YOLOPose skeleton)
        edges = [
            (5, 7), (7, 9), (6, 8), (8, 10),  # braços
            (11, 13), (13, 15), (12, 14), (14, 16),  # pernas
            (5, 6), (5, 11), (6, 12),  # tronco
        ]

        for p1, p2 in edges:
            if keypoints[p1][2] > 0.7 and keypoints[p2][2] > 0.7:
                x1, y1 = int(keypoints[p1][0]), int(keypoints[p1][1])
                x2, y2 = int(keypoints[p2][0]), int(keypoints[p2][1])
                cv2.line(annotated, (x1, y1), (x2, y2), (255, 0, 0), 2)

        # === Calcular ângulos ===

        angles = self.compute_angles(landmarks)
        # Enviar só o primeiro utilizador com confiança > 0.7
        angle_dict = self.convert_angles_to_dict(angles)
        
        if keypoints[0][2] > 0.7:
            reba_score, reba_table = compute_reba_score(angle_dict)
            rula_score, rula_table = compute_rula_score(angle_dict)

            self.reba_scores.append(reba_score)
            self.reba_tables.append(reba_table)
            self.rula_scores.append(rula_score)
            self.rula_tables.append(rula_table)
            self.batch_cnt += 1

            if self.batch_cnt >= 20:
                # Mediana REBA e última tabela
                median_reba = float(np.median(self.reba_scores))
                latest_reba_table = self.reba_tables[-1]

                # Mediana RULA e última tabela
                median_rula = float(np.median(self.rula_scores))
                latest_rula_table = self.rula_tables[-1]

                # send_reba_table(self.cam_id, latest_reba_table, operator=self.operator)
                # send_rula_table(self.cam_id, latest_rula_table, operator=self.operator)
                # send_pose_data(f"{self.cam_id}", keypoints, angles, median_reba, median_rula, operator=self.operator)
                self._send_data_async(keypoints, angles, latest_reba_table, latest_rula_table, median_reba, median_rula)

                # Reiniciar buffers
                self.reba_scores.clear()
                self.reba_tables.clear()
                self.rula_scores.clear()
                self.rula_tables.clear()
                self.batch_cnt = 0

        return [angles], annotated
    
    
    def convert_angles_to_dict(self, angles):
        return {
            "upper_arm_angle": max(angles[4][0], angles[5][0]),
            "lower_arm_angle": max(angles[0][0], angles[1][0]),
            "wrist_angle": max(angles[2][0], angles[3][0]),
            "neck_angle": angles[11][0],
            "trunk_angle": angles[10][0],
            "carga_peso": 0,  # podes ajustar ou inferir noutro local
            "ajustes": {
                "shoulder_raised": False,
                "abducted": False,
                "leaning": False,
                "wrist_twisted": False,
                "wrist_bent": False,
                "midline": False,
                "neck_twisted": False,
                "neck_side": False,
                "trunk_twisted": angles[14][0] > 30,
                "trunk_side": False,
                "feet_supported": True,
                "static_posture": False,
                "repetitive": False
            }
        }
    
    

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
