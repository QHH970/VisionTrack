# -*- coding: utf-8 -*-
# 本程序用于视频中车辆行人等多目标检测跟踪（基于 YOLOv8）

import cv2
import numpy as np
from ultralytics import YOLO
from sort import Sort  # Sort 算法用于多目标追踪


class Detector:
    def __init__(self, model_path=None):
        self.filter_confidence = 0.5  # 筛除置信度过低的检测结果
        self.tracker = Sort()  # 初始化 Sort 跟踪器

        # 加载 YOLOv8 模型
        if model_path is None:
            model_path = "./yolov8n.pt"  # 默认权重文件路径（YOLOv8n 模型）
        try:
            self.model = YOLO(model_path)  # 加载 YOLOv8 模型
            print("模型加载成功！")
        except Exception as e:
            print(f"模型加载失败：{e}")

    def run(self, frame):
        frame_in = frame.copy()
        (H, W) = frame_in.shape[:2]

        # 使用 YOLOv8 进行目标检测
        results = self.model.predict(frame_in, conf=self.filter_confidence, verbose=False)

        # 提取检测结果
        dets = []
        for result in results[0].boxes:
            x1, y1, x2, y2 = result.xyxy[0]  # 检测框坐标
            conf = result.conf[0]  # 置信度
            cls_id = int(result.cls[0])  # 类别 ID
            dets.append([x1, y1, x2, y2, conf, cls_id])

        dets = np.array(dets)

        # 使用 Sort 算法进行跟踪
        tracks = self.tracker.update(dets)
        boxes = []  # 跟踪到的标记框
        indexIDs = []  # 跟踪到的 ID
        cls_IDs = []  # 跟踪到的类别 ID

        for track in tracks:
            boxes.append([track[0], track[1], track[2], track[3]])
            indexIDs.append(int(track[4]))
            cls_IDs.append(int(track[5]))

        return dets, boxes, indexIDs, cls_IDs
