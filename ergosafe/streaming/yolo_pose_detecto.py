import cv2
import numpy as np
import torch
from ultralytics import YOLO

class YoloPoseDetector:
    def __init__(self, model_path='yolov8n-pose.pt'):
        self.model = YOLO(model_path)
        self.model.to('cuda' if torch.cuda.is_available() else 'cpu')

    def detect_pose(self, image):
        results = self.model(image, verbose=False)
        keypoints = None
        annotated_image = image.copy()

        for result in results:
            if result.keypoints is not None:
                kpts = result.keypoints.xy.cpu().numpy()[0]  # (17, 2)
                keypoints = kpts
                for x, y in kpts:
                    cv2.circle(annotated_image, (int(x), int(y)), 3, (0, 255, 0), -1)
                break  # Apenas o primeiro detetado

        return keypoints, annotated_image
