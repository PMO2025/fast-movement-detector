import os  # noqa
os.environ["YOLO_VERBOSE"] = "False"  # noqa

from dataclasses import dataclass
from typing import Iterable

import numpy as np
from ultralytics import YOLO


@dataclass
class SegmentationObject:
    tid: int
    x: int
    y: int
    cx: int
    cy: int
    width: int
    height: int
    klass: int
    mask: np.array


SegmentationStream = Iterable[dict[int, SegmentationObject]]


class YoloModel:
    def create_stream(self, video_stream: Iterable[np.array]) -> SegmentationStream:
        model = YOLO("./models/yolo/yolo11n-seg.pt")

        for frame in video_stream:
            res = model.track(frame, persist=True)[0]

            if res.boxes is None or res.masks is None:
                continue

            tids = res.boxes.id.int().cpu().tolist()
            boxes = res.boxes.data.cpu().tolist()
            classes = res.boxes.cls.cpu().tolist()
            masks = res.masks.data.cpu().numpy()

            objects = {}
            for tid, box, klass, mask in zip(tids, boxes, classes, masks):
                if klass != 0:
                    continue

                x0, y0, x1, y1, *_ = box
                objects[tid] = SegmentationObject(
                    tid=int(tid),
                    x=int(x0),
                    y=int(y0),
                    cx=int((x0 + x1)/2),
                    cy=int((y0 + y1)/2),
                    width=int(x1 - x0),
                    height=int(y1 - y0),
                    klass=int(klass),
                    mask=mask,
                )

            yield objects
