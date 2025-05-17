import math
import random

import numpy as np
import torch

from geocalib import GeoCalib


class GeoCalibModel:
    use_samples: int
    model: GeoCalib
    device: str

    def __init__(self, *, device: str, use_samples: int):
        self.device = device
        self.use_samples = use_samples

        self.model = GeoCalib().to(device)

    def infer_fov(self, video: np.array) -> tuple[float, float]:
        frames = len(video)
        height, width, _ = video[0].shape

        idx = list(range(frames))
        random.shuffle(idx)
        idx = idx[:self.use_samples]

        video = np.stack([video[i] for i in idx])

        video = torch.tensor(video).moveaxis(-1, 1).float() / 255

        video = video.to(self.device)

        results = self.model.calibrate(video, shared_intrinsics=True)

        vfov = results["camera"].vfov[0].item()
        hfov = 2 * math.atan(width / height * math.tan(vfov / 2))

        return hfov, vfov
