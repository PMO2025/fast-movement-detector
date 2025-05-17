from collections import defaultdict
from itertools import tee
import math

from typing import Iterable
import cv2
from scipy.ndimage import binary_erosion, binary_dilation
import numpy as np

from .depth.vda import VideoDepthAnythingModel
from .segment import SegmentationStream, YoloModel
from .calibrate import GeoCalibModel
from .util import normalize

from ultralytics.utils.plotting import colors


def mask_contour(mask, stroke=5):
    kernel = np.ones((stroke, stroke))
    contour = binary_dilation(mask, kernel)
    contour[mask] = 0
    return contour


def get_pixel_dir_1d(x, rx, fov):
    px = math.sin(fov/2) * (2 * x / rx - 1)
    py = math.cos(fov/2)
    return normalize([px, py])


def get_pixel_dir_2d(x, rx, hfov, y, ry, vfov):
    hx, hy = get_pixel_dir_1d(x, rx, hfov)
    vx, vy = get_pixel_dir_1d(y, ry, vfov)

    return normalize([hx, vy, -vx])


XY_GAIN = 0.4
DIST_GAIN = 0.4
GAIN_3D = 0.4


class Object:
    def __init__(self, hfov, vfov, rx, ry, fps):
        self.initialized = False

        self.hfov = hfov
        self.vfov = vfov
        self.rx = rx
        self.ry = ry
        self.fps = fps

        self.x = None
        self.y = None
        self.dist = None

        self.coord_3d = None
        self.prev_coord = None

    def update(self, x, y, dist):
        if not self.initialized:
            self.x = x
            self.y = y
            self.dist = dist

            dir = get_pixel_dir_2d(
                self.x, self.rx, self.hfov, self.y, self.ry, self.vfov)
            coord_3d = dir * dist

            self.prev_coord = coord_3d
            self.coord_3d = coord_3d

            self.speed = np.array([0, 0, 0])
            self.prev_speed = np.array([0, 0, 0])

            self.initialized = True
        else:
            self.x = (1 - XY_GAIN) * self.x + XY_GAIN * x
            self.y = (1 - XY_GAIN) * self.y + XY_GAIN * y
            self.dist = (1 - DIST_GAIN) * self.dist + DIST_GAIN * dist

            dir = get_pixel_dir_2d(
                self.x, self.rx, self.hfov, self.y, self.ry, self.vfov)
            coord_3d = dir * dist

            self.prev_coord = self.coord_3d
            self.coord_3d = (1 - GAIN_3D) * self.coord_3d + GAIN_3D * coord_3d

            self.prev_speed = self.speed
            speed = (self.coord_3d - self.prev_coord) * self.fps
            self.speed = (1 - GAIN_3D) * self.speed + GAIN_3D * speed

        # if np.linalg.norm(self.prev_speed) > 0:
        #     self.acc = np.linalg.norm(self.speed) / \
        #         np.linalg.norm(self.prev_speed)
        # else:
        #     self.acc = 0
        self.acc = np.linalg.norm(self.speed - self.prev_speed) * self.fps

        # self.rapid = self.acc > 2 and np.linalg.norm(self.speed) > 2
        self.rapid = self.acc > 15


class Model:
    def __init__(self, *, processing_shape):
        self.processing_shape = processing_shape

        self.vda = VideoDepthAnythingModel(device="cuda")
        self.yolo = YoloModel()
        self.geocalib = GeoCalibModel(device="cuda", use_samples=10)

    def infer_advanced(self, video_stream, *, fps, hfov, vfov, depth_stream=None):
        print(hfov / math.pi * 180, vfov / math.pi * 180)

        def resize(frame):
            return cv2.resize(frame, (self.processing_shape[1], self.processing_shape[0]))

        video_stream = map(resize, video_stream)

        if depth_stream is None:
            video_stream, *video_streams = tee(video_stream, 3)
            yolo_stream = self.yolo.create_stream(video_streams[0])
            depth_stream = self.vda.create_stream(video_streams[1])
        else:
            video_stream, *video_streams = tee(video_stream, 2)
            yolo_stream = self.yolo.create_stream(video_streams[0])

        objects = None
        for frame, seg_objects, depth_map in zip(video_stream, yolo_stream, depth_stream):
            height, width, _ = frame.shape

            if objects is None:
                objects = defaultdict(
                    lambda: Object(hfov, vfov, width, height, fps))

            for tid, seg_obj in seg_objects.items():
                mask = binary_erosion(seg_obj.mask, np.ones((7, 7)))

                n_pixels = np.count_nonzero(mask)
                if n_pixels < 5:
                    continue

                dist = np.median(depth_map[mask])

                objects[tid].update(seg_obj.cx, seg_obj.cy, dist)

            yield frame, fps, seg_objects, objects

    def infer(self, video, *, fps, depth_stream=None):
        hfov, vfov = self.geocalib.infer_fov(video)

        return self.infer_advanced(video, fps=fps, hfov=hfov, vfov=vfov, depth_stream=depth_stream)

    def visualize(self, pred_stream):
        heats = {}

        for frame, fps, seg_objects, objects in pred_stream:
            vis = frame.copy()

            for tid in seg_objects.keys():
                seg_obj = seg_objects[tid]
                obj = objects[tid]

                mask = binary_erosion(seg_obj.mask, np.ones((7, 7)))
                contour = mask_contour(mask)

                vis[contour] = np.array(colors(tid, True), dtype=np.uint8)

                px = seg_obj.cx
                py = seg_obj.y

                if not obj.initialized:
                    continue

                text = str(f"{np.linalg.norm(obj.speed):0.4f}, {obj.acc:0.4f}")
                # text = str(f"{obj.acc:0.4f}")
                # text = str(f"{obj.acc > 2}")
                # text = str(f"{avg_dist:0.4f}")

                font = cv2.FONT_HERSHEY_SIMPLEX
                font_size = 0.5
                font_thickness = 1

                pad = 3

                tw, th = cv2.getTextSize(
                    text, font, font_size, font_thickness)[0]

                cv2.rectangle(vis, (int(px-tw/2-pad), int(py-th-2*pad)),
                              (int(px+tw/2+pad), int(py)), (255, 255, 255), -1)

                cv2.putText(vis, text, (int(px-tw/2), int(py-pad)),
                            font, font_size, (0, 0, 0), font_thickness)

                if obj.initialized:
                    cv2.circle(vis, (int(obj.x), int(obj.y)), 3, (255, 0, 0))

                if obj.rapid:
                    heats[tid] = 2

                if tid in heats:
                    heat = min(1, heats[tid])
                    vis[mask] = (255, 0, 0)
                    # vis = np.where(
                    #     np.expand_dims(mask, -1), (1-heat) * vis + heat * np.array([[[255, 0, 0]]]), vis).astype(np.uint8)
                    # print(vis.shape)

            for tid in list(heats.keys()):
                heats[tid] -= 2 / fps
                if heats[tid] <= 0:
                    del heats[tid]

            yield vis
