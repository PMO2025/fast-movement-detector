from typing import Iterator

import numpy as np
import torch

from models.depth_anything.metric_depth.depth_anything_v2.dpt import DepthAnythingV2


class DepthAnythingModel:
    device: str

    def __init__(self, *, device: str):
        self.device = device

        self.model = DepthAnythingV2(
            encoder="vits",
            features=64,
            out_channels=[48, 96, 192, 384],
            max_depth=80
        )

        self.model.load_state_dict(torch.load(
            "./models/depth_anything/metric_depth/checkpoints/depth_anything_v2_metric_vkitti_vits.pth", map_location="cpu"))

        self.model.to(device)
        self.model.eval()

    def create_stream(self, video_stream: Iterator[np.array]) -> Iterator[np.array]:
        for frame in video_stream:
            yield self.model.infer_image(frame)
