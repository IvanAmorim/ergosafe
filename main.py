import os
import sys
import json
import signal
import time
import logging
import cv2 as cv
import numpy as np
import multiprocessing as mp
from pathlib import Path
from flask import Flask, Response
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import PoseLandmarker, PoseLandmarkerOptions, RunningMode
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# === Logging ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RTSP_Mediapipe")

# === Diretórios ===
BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config" / "cam_config.json"

# === Flask App ===
app = Flask(__name__)
latest_frame = None
frame_lock = mp.Lock()

# === InfluxDB Config ===
INFLUX_URL = "http://10.10.51.61:8086"
INFLUX_TOKEN = "admin"
INFLUX_ORG = "CiTin"
INFLUX_BUCKET = "ergosafe"
influx_client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = influx_client.write_api(write_options=SYNCHRONOUS)

# === PoseLandmarker ===
base_options = BaseOptions(model_asset_path="pose_landmarker_full.task")
options = PoseLandmarkerOptions(
    base_options=base_options,
    running_mode=RunningMode.VIDEO,
    num_poses=1,
    min_pose_detection_confidence=0.5,
    min_pose_presence_confidence=0.5,
    min_tracking_confidence=0.5,
    output_segmentation_masks=False
)
landmarker = PoseLandmarker.create_from_options(options)

# === Shared Queue and Handler ===
frame_queue = mp.Queue(maxsize=5)

display_queue = mp.Queue(maxsize=1)  # última frame anotada


# === Enviar landmarks para InfluxDB ===
def enviar_para_influx(camera_id, landmarks, timestamp_ms):
    for i, lm in enumerate(landmarks):
        point = (
            Point("pose_landmarks")
            .tag("camera_id", camera_id)
            .tag("landmark_id", i)
            .field("x", float(lm.x))
            .field("y", float(lm.y))
            .field("z", float(lm.z))
            .field("visibility", float(lm.visibility))
            .time(timestamp_ms * 1_000_000)
        )
        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)

# === MJPEG Stream ===
@app.route('/video_feed')
def video_feed():
    return Response(generate_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')

def generate_stream():
    global latest_frame
    while True:
        with frame_lock:
            frame = latest_frame.copy() if latest_frame is not None else None
        if frame is not None:
            ret, buffer = cv.imencode('.jpg', frame)
            if ret:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        else:
            time.sleep(0.01)

# === Processar frame da queue ===
def process_frames(frame_id, display_queue):
    while True:
        if not frame_queue.empty():
            jpeg_bytes = frame_queue.get()
            frame = cv.imdecode(np.frombuffer(jpeg_bytes, dtype=np.uint8), cv.IMREAD_COLOR)
            if frame is None:
                continue

            # Pose
            rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            timestamp_ms = int(time.time() * 1000)
            result = landmarker.detect_for_video(mp_image, timestamp_ms)

            if result.pose_landmarks:
                enviar_para_influx(frame_id, result.pose_landmarks[0], timestamp_ms)
                for landmark in result.pose_landmarks[0]:
                    x = int(landmark.x * frame.shape[1])
                    y = int(landmark.y * frame.shape[0])
                    cv.circle(frame, (x, y), 3, (0, 255, 0), -1)

            # Envia para Flask
            success, jpg = cv.imencode('.jpg', frame)
            if success:
                if not display_queue.full():
                    display_queue.put(jpg.tobytes())
        else:
            time.sleep(0.01)

# === Classe para captura da câmara ===
class Video:
    def __init__(self, cam_name, url_cam):
        self.cam_name = cam_name
        self.url_cam = url_cam
        self.cap = self.init_gstreamer_capture()
        self.running = True
        self.crop_width = 1080
        self.crop_height = 1080
        self.width = 1920
        self.height = 1080
        self.mid_x = self.width // 2
        self.mid_y = self.height // 2
        self.cw2 = self.crop_width // 2
        self.ch2 = self.crop_height // 2

    def init_gstreamer_capture(self):
        pipeline = (
            f"rtspsrc location={self.url_cam} latency=0 ! "
            "rtph264depay ! h264parse ! avdec_h264 ! videoconvert ! "
            "video/x-raw,format=BGR ! appsink drop=1 max-buffers=1 sync=false"
        )
        cap = cv.VideoCapture(pipeline, cv.CAP_GSTREAMER)
        return cap if cap.isOpened() else None

    def run(self):
        if not self.cap:
            raise RuntimeError(f"[Video] Erro ao abrir stream: {self.cam_name}")

        logger.info(f"[{self.cam_name}] Câmara iniciada.")
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                logger.warning(f"[{self.cam_name}] Frame não lido")
                time.sleep(0.1)
                continue

            cropped = frame[
                self.mid_y - self.ch2:self.mid_y + self.ch2,
                self.mid_x - self.cw2:self.mid_x + self.cw2
            ]
            success, jpg = cv.imencode('.jpg', cropped)
            if success:
                try:
                    frame_queue.put_nowait(jpg.tobytes())
                except:
                    pass
            time.sleep(0.05)
            
            
def start_flask(display_queue):
    app = Flask(__name__)

    @app.route('/video_feed')
    def video_feed():
        return Response(generate_stream(display_queue), mimetype='multipart/x-mixed-replace; boundary=frame')

    def generate_stream(queue):
        while True:
            if not queue.empty():
                jpeg = queue.get()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpeg + b'\r\n')
            else:
                time.sleep(0.01)

    app.run(host='0.0.0.0', port=5050, threaded=True)

# === Main ===
def main():
    if not CONFIG_PATH.exists():
        logger.error(f"Configuração não encontrada: {CONFIG_PATH}")
        return

    with open(CONFIG_PATH, "r") as fh:
        cameras = json.load(fh)

    cam_name, cam_url = next(iter(cameras.items()))

    # Lançar processos
    capture_proc = mp.Process(target=Video(cam_name, cam_url).run)
    process_proc = mp.Process(target=process_frames, args=(cam_name, display_queue))
    flask_proc = mp.Process(target=start_flask, args=(display_queue,))

    capture_proc.start()
    process_proc.start()
    flask_proc.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Encerrando...")
    finally:
        for p in [capture_proc, process_proc, flask_proc]:
            p.terminate()
            p.join()


if __name__ == "__main__":
    main()