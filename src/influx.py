from influxdb_client import Point
from src.influx_conf.influx_client import write_api
from src.influx_conf.influx_config import INFLUX_BUCKET
import time


def send_pose_data(camera_id: str, keypoints: list, angles: list, reba_score=None, rula_score=None, operator="default"):
    timestamp = int(time.time() * 1e9)
    camera_tag = f"camera_{camera_id}"

    # === Enviar keypoints ===
    for idx, (x, y, c) in enumerate(keypoints):
        point = (
            Point("keypoint")
            .tag("camera", camera_tag)
            .tag("operator", operator)
            .tag("index", idx)
            .field("x", float(x))
            .field("y", float(y))
            .field("confidence", float(c))
            .time(timestamp)
        )
        write_api.write(bucket=INFLUX_BUCKET, record=point)

    # === Enviar ângulos ===
    for i, a in enumerate(angles):
        point = (
            Point("angle")
            .tag("camera", camera_tag)
            .tag("operator", operator)
            .tag("angle_index", i)
            .field("value", float(a))
            .time(timestamp)
        )
        write_api.write(bucket=INFLUX_BUCKET, record=point)

    # === Enviar scores RULA/REBA (se disponíveis) ===
    if reba_score is not None or rula_score is not None:
        score_point = (
            Point("score")
            .tag("camera", camera_tag)
            .tag("operator", operator)
            .time(timestamp)
        )
        if reba_score is not None:
            score_point = score_point.field("reba_score", float(reba_score))
        if rula_score is not None:
            score_point = score_point.field("rula_score", float(rula_score))

        write_api.write(bucket=INFLUX_BUCKET, record=score_point)

def send_reba_table(camera_id: str, table: dict, operator="default"):
    timestamp = int(time.time() * 1e9)
    camera_tag = f"camera_{camera_id}"
    for label, value in table.items():
        point = (
            Point("reba_table")
            .tag("camera", camera_tag)
            .tag("operator", operator)
            .tag("label", label)
            .field("value", float(value))
            .time(timestamp)
        )
        write_api.write(bucket=INFLUX_BUCKET, record=point)


def send_rula_table(camera_id: str, table: dict, operator="default"):
    timestamp = int(time.time() * 1e9)
    camera_tag = f"camera_{camera_id}"
    for label, value in table.items():
        point = (
            Point("rula_table")
            .tag("camera", camera_tag)
            .tag("operator", operator)
            .tag("label", label)
            .field("value", float(value))
            .time(timestamp)
        )
        write_api.write(bucket=INFLUX_BUCKET, record=point)