import cv2
import time
import logging
import numpy as np
from common.crud import get_camera_by_id

logger = logging.getLogger("CameraDriver")

class CameraDriver:
    def __init__(self, cam_name, rtsp_url, frame_size=(720, 720), fps=20):
        self.cam_name = cam_name
        self.rtsp_url = rtsp_url
        self.frame_size = frame_size
        self.fps = fps
        self.pipeline = (
            f"rtspsrc location={self.rtsp_url} latency=0 ! "
            "rtph264depay ! h264parse ! avdec_h264 ! videoconvert ! "
            "video/x-raw,format=BGR ! appsink drop=1 max-buffers=1 sync=false"
        )
        self.cap = cv2.VideoCapture(self.pipeline, cv2.CAP_GSTREAMER)
        if not self.cap.isOpened():
            logger.error(f"[{self.cam_name}] Erro ao abrir RTSP")
            self.cap = None

    def read_frame(self):
        if self.cap is None or not self.cap.isOpened():
            return None

        ret, frame = self.cap.read()
        if not ret:
            logger.warning(f"[{self.cam_name}] Frame não lido")
            return None

        frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        resized = cv2.resize(frame, self.frame_size)
        return resized

    def stream_loop(self, output_queue):
        logger.info(f"[{self.cam_name}] Captura iniciada")
        interval = 1.0 / self.fps
        while True:
            frame = self.read_frame()
            if frame is not None:
                success, jpg = cv2.imencode('.jpg', frame)
                if success and not output_queue.full():
                    output_queue.put(jpg.tobytes())
            time.sleep(interval)

    def release(self):
        if self.cap:
            self.cap.release()
            logger.info(f"[{self.cam_name}] RTSP encerrado")



    def video_stream(camera_id: int):
        camera = get_camera_by_id(camera_id)
        if not camera:
            return {"error": "Câmara não encontrada"}

        def stream_generator():
            # Usa GStreamer para baixo atraso
            pipeline = (
                f"rtspsrc location={camera.url} latency=0 ! "
                "rtph264depay ! h264parse ! avdec_h264 ! videoconvert ! "
                "video/x-raw,format=BGR ! appsink drop=1 max-buffers=1 sync=false"
            )
            cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
            if not cap.isOpened():
                yield b""
                return

            while True:
                ret, frame = cap.read()
                if not ret:
                    time.sleep(0.1)
                    continue
                
                frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
                _, jpeg = cv2.imencode('.jpg', frame)
                frame_bytes = jpeg.tobytes()

                yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

        return StreamingResponse(stream_generator(), media_type="multipart/x-mixed-replace; boundary=frame")
