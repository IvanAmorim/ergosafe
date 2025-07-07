import cv2
import time
import numpy as np
from flask import Flask, Response
from multiprocessing import Process, Queue
import logging

# === Configuração das Câmaras ===
CAMS = {
    "cam1": "rtsp://admin:c1t1nPass@10.10.99.10:554/Streaming/Channels/1",
    "cam2": "rtsp://admin:c1t1nPass@10.10.99.8:554/Streaming/Channels/1"
}

# === Parâmetros Globais ===
FPS = 20
FRAME_SIZE = (720, 720)
QUEUE_SIZE = 10

# === Logging ===
logging.basicConfig(level=logging.INFO)


# === Captura RTSP ===
def capture_rtsp(cam_name, rtsp_url, output_queue):
    logging.info(f"[{cam_name}] A iniciar captura de {rtsp_url}")
    pipeline = (
        f"rtspsrc location={rtsp_url} latency=0 ! "
        "rtph264depay ! h264parse ! avdec_h264 ! videoconvert ! "
        "video/x-raw,format=BGR ! appsink drop=1 max-buffers=1 sync=false"
    )
    cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
    if not cap.isOpened():
        logging.error(f"[{cam_name}] Erro ao abrir RTSP")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            logging.warning(f"[{cam_name}] Frame não lido")
            time.sleep(0.1)
            continue
        frame = cv2.rotate(frame,cv2.ROTATE_90_CLOCKWISE)
        success, jpg = cv2.imencode('.jpg', frame)
        if success and not output_queue.full():
            output_queue.put(jpg.tobytes())

        time.sleep(1.0 / FPS)


# === Servidor Web ===
def start_web_stream(queues):
    app = Flask(__name__)

    def make_stream(queue):
        while True:
            if not queue.empty():
                jpeg = queue.get()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpeg + b'\r\n')
            else:
                time.sleep(0.01)

    @app.route('/cam1_feed')
    def cam1_feed():
        return Response(make_stream(queues["cam1"]),
                        mimetype='multipart/x-mixed-replace; boundary=frame')

    @app.route('/cam2_feed')
    def cam2_feed():
        return Response(make_stream(queues["cam2"]),
                        mimetype='multipart/x-mixed-replace; boundary=frame')

    app.run(host="0.0.0.0", port=5050, threaded=True)


# === Main ===
if __name__ == "__main__":
    queues = {
        "cam1": Queue(QUEUE_SIZE),
        "cam2": Queue(QUEUE_SIZE),
        "cam1_view": Queue(QUEUE_SIZE),
        "cam2_view": Queue(QUEUE_SIZE)
    }

    processes = [
        Process(target=capture_rtsp, args=("cam1", CAMS["cam1"], queues["cam1"])),
        Process(target=capture_rtsp, args=("cam2", CAMS["cam2"], queues["cam2"])),
        Process(target=start_web_stream, args=({
            "cam1": queues["cam1"],
            "cam2": queues["cam2"]
        },))
    ]

    # # Redirecionar frames para gravação e visualização
    # def forward_frames(src_queue, dest_queue):
    #     while True:
    #         if not src_queue.empty() and not dest_queue.full():
    #             dest_queue.put(src_queue.get())
    #         else:
    #             time.sleep(0.005)

    # processes.append(Process(target=forward_frames, args=(queues["cam1"], queues["cam1_view"])))
    # processes.append(Process(target=forward_frames, args=(queues["cam2"], queues["cam2_view"])))

    for p in processes:
        p.start()

    try:
        for p in processes:
            p.join()
    except KeyboardInterrupt:
        for p in processes:
            p.terminate()
            p.join()
