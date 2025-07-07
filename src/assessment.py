import cv2
import time
import queue
import threading
from influxdb_client.client.write_api import SYNCHRONOUS
import numpy as np
from .ergonomicassessments import ErgonomicAssessment
from .yolo_pose_detector import YoloPoseDetector

class AssessmentCore:
    def __init__(self, windowObject, influxDBObject, influxDBBucket):
        self.influxDBObject = influxDBObject
        self.influxDBBucket = influxDBBucket
        self.windowObject = windowObject
        self.isRunning = False
        self.windowAssessmentQueue = queue.Queue(maxsize=1)
        self.pose_detector = YoloPoseDetector()
        self.ergoAssessment = ErgonomicAssessment()

    def Run(self):
        self.t = threading.Thread(target=self.PerformAssessment)
        self.isRunning = True
        self.t.start()

    def Stop(self):
        self.isRunning = False
        if hasattr(self, "videocapture_CameraObject"):
            self.videocapture_CameraObject.release()
        if hasattr(self, "t"):
            self.t.join()
            del self.t

    def GetAdjusmentWeight(self, weight):
        weightInPounds = 2.20462 * float(weight)
        if self.windowObject.assessmentMethod == 1:
            if weightInPounds < 11:
                return 0
            if 11 < weightInPounds < 22:
                return 1
            if weightInPounds > 22:
                return 2
        elif self.windowObject.assessmentMethod == 2:
            if weightInPounds < 4.4:
                return 0
            if 4.4 < weightInPounds < 22:
                return 1
            if weightInPounds > 22:
                return 2
        else:
            return 0

    def GetAssessmentResultFromQueue(self):
        try:
            return True, self.windowAssessmentQueue.get()
        except:
            return False, None

    def PerformAssessment(self):
        self.videocapture_CameraObject = cv2.VideoCapture(int(self.windowObject.cameraIndex), cv2.CAP_V4L2)
        self.videocapture_CameraObject.set(cv2.CAP_PROP_FPS, 60)
        self.videocapture_CameraObject.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))

        while self.isRunning:
            assessmentAdjustmentWeightScore = self.GetAdjusmentWeight(self.windowObject.assessmentAdjustmentWeightScore)
            assessmentAdjustmentActivityScore = self.windowObject.assessmentAdjustmentActivityScore
            assessmentAdjustmentCouplingScore = self.windowObject.assessmentAdjustmentCouplingScore
            ret, cameraFrame = self.videocapture_CameraObject.read()
            result = []
            if ret:
                cameraFrame = cv2.rotate(cameraFrame, cv2.ROTATE_90_COUNTERCLOCKWISE)
                keypoints, annotated_image = self.pose_detector.detect_pose(cameraFrame)

                if keypoints is not None:
                    assessmentAngles = self.ergoAssessment.compute_angles_from_yolo(keypoints)
                    assessmentScore = -9999
                    if self.windowObject.assessmentMethod == 1:
                        listOfScores = self.ergoAssessment.Reba(
                            assessmentAngles,
                            assessmentAdjustmentWeightScore,
                            assessmentAdjustmentCouplingScore
                        )
                        assessmentScore = listOfScores[2]
                    elif self.windowObject.assessmentMethod == 2:
                        listOfScores = self.ergoAssessment.Rula(
                            assessmentAngles,
                            assessmentAdjustmentWeightScore,
                            assessmentAdjustmentActivityScore
                        )
                        assessmentScore = listOfScores[2]
                    else:
                        listOfScores = []

                    result = [annotated_image, assessmentScore, assessmentAngles.tolist()]

                    assessmentMethodDict = {1: "Reba", 2: "Rula"}
                    if self.windowObject.sendScoresToInfluxDB and self.influxDBObject and self.influxDBBucket:
                        try:
                            point_json = {
                                "measurement": "ergosafe",
                                "tags": {
                                    "camera": self.windowObject.influxDBCameraIdentifier,
                                    "operator": self.windowObject.influxDBOperatorIdentifier,
                                    "method": assessmentMethodDict[self.windowObject.assessmentMethod]
                                },
                                "fields": {
                                    "score_a": int(listOfScores[0]),
                                    "score_b": int(listOfScores[1]),
                                    "score_c": int(listOfScores[2]),
                                    "neck": int(listOfScores[3]),
                                    "trunk": int(listOfScores[4]),
                                    "legs": int(listOfScores[5]),
                                    "arm": int(listOfScores[6]),
                                    "forearm": int(listOfScores[7]),
                                    "hand": int(listOfScores[8]),
                                    "twistedhand": int(listOfScores[9]),
                                }
                            }
                            self.influxDBObject.write_api(write_options=SYNCHRONOUS).write(
                                bucket=self.influxDBBucket,
                                record=point_json
                            )
                        except Exception as e:
                            print("Erro ao enviar para InfluxDB:", e)
                else:
                    result = [cameraFrame, -9999, []]

                if not self.windowAssessmentQueue.empty():
                    try:
                        self.windowAssessmentQueue.get_nowait()
                    except queue.Empty:
                        pass
                self.windowAssessmentQueue.put(result)
