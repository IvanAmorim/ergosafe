# src/stream_manager.py

import time
import cv2
import logging
import numpy as np
from threading import Thread
from queue import Queue
from ergosafe.crud import get_camera_by_id
from fastapi.responses import StreamingResponse
from ergosafe.inference import YoloPoseSkeleton


logger = logging.getLogger("StreamManager")

# Guarda threads de aquisição
acquisition_threads = {}
queues = {}
running_flags = {}


def start_acquisition(camera_id: int):
    camera = get_camera_by_id(camera_id)
    if not camera:
        logger.error(f"Câmara com ID {camera_id} não encontrada.")
        return

    if camera_id in acquisition_threads:
        logger.info(f"Câmara {camera_id} já está a ser adquirida.")
        return

    frame_queue = Queue(maxsize=2)
    queues[camera_id] = frame_queue
    running_flags[camera_id] = True

    def capture_loop():
        logger.info(f"[cam_{camera_id}] Início da aquisição")
        pipeline = (
            f"rtspsrc location={camera.url} latency=0 ! "
            "rtph264depay ! h264parse ! avdec_h264 ! videoconvert ! "
            "video/x-raw,format=BGR ! appsink drop=1 max-buffers=1 sync=false"
            )
        cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
        if not cap.isOpened():
            logger.error(f"[cam_{camera_id}] Erro ao abrir o stream - URL: {camera.url}")
            return

        while running_flags[camera_id]:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.1)
                continue
            if not frame_queue.full():
                frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
                frame_queue.put(frame)
            time.sleep(0.05)  # ~20 FPS

        cap.release()
        logger.info(f"[cam_{camera_id}] Aquisição terminada")

    thread = Thread(target=capture_loop, daemon=True)
    thread.start()
    acquisition_threads[camera_id] = thread


def stop_camera_stream(camera_id: int):
    running_flags[camera_id] = False
    if camera_id in acquisition_threads:
        acquisition_threads[camera_id].join()
        del acquisition_threads[camera_id]
        del queues[camera_id]
        del running_flags[camera_id]

def get_stream(camera_id: int):
    if camera_id not in queues:
        start_acquisition(camera_id)
        time.sleep(1)

    # === Obter operador associado à câmara ===
    camera = get_camera_by_id(camera_id)
    operator = f"user_{camera.user_id}" if camera and camera.user_id else "default"

    def generate():
        pose_detector = YoloPoseSkeleton(cam_id=camera_id, operator=operator)

        while True:
            if camera_id not in queues:
                break

            if not queues[camera_id].empty():
                frame = queues[camera_id].get()
                angles_list, annotated = pose_detector.detect_and_compute_angles(frame)

                # for idx, angles in enumerate(angles_list):
                #     for i, angle in enumerate(angles):
                #         cv2.putText(annotated, f"A{i+1}: {angle[0]:.1f}", (10, 20 + 20*i + idx*300),
                #                     cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)

                ret, jpeg = cv2.imencode(".jpg", annotated)

                if ret:
                    yield (b"--frame\r\n"
                           b"Content-Type: image/jpeg\r\n\r\n" + jpeg.tobytes() + b"\r\n")
            else:
                time.sleep(0.01)

    return StreamingResponse(generate(), media_type="multipart/x-mixed-replace; boundary=frame")



