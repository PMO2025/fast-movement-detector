from itertools import chain, tee
from typing import Iterator

import numpy as np

import cv2

import torch
from torchvision.transforms import Compose
import torch.nn.functional as F

from models.video_depth_anything.video_depth_anything.video_depth import VideoDepthAnything
from models.video_depth_anything.utils.util import compute_scale_and_shift, get_interpolate_frames
from models.video_depth_anything.video_depth_anything.util.transform import Resize, NormalizeImage, PrepareForNet

INFER_LEN = 32
OVERLAP = 10
KEYFRAMES = [0, 12, 24, 25, 26, 27, 28, 29, 30, 31]
INTERP_LEN = 8


def _sliding_windows(x, win_size: int, hop: int):
    data = []

    for sample in x:
        data.append(sample)
        if len(data) >= win_size:
            yield data.copy()
            data = data[hop:]

    if len(data) > 0:
        while len(data) < win_size:
            data.append(data[-1])

        yield data


def _create_window_stream(vda, frames, input_size=518, device="cuda", fp32=False):
    first_frame = next(frames)

    frame_height, frame_width = first_frame.shape[:2]
    ratio = max(frame_height, frame_width) / min(frame_height, frame_width)
    if ratio > 1.78:
        input_size = int(input_size * 1.777 / ratio)
        input_size = round(input_size / 14) * 14

    print(input_size)

    transform = Compose([
        Resize(
            width=input_size,
            height=input_size,
            resize_target=False,
            keep_aspect_ratio=True,
            ensure_multiple_of=14,
            resize_method='lower_bound',
            image_interpolation_method=cv2.INTER_CUBIC,
        ),
        NormalizeImage(mean=[0.485, 0.456, 0.406],
                       std=[0.229, 0.224, 0.225]),
        PrepareForNet(),
    ])

    def transform_frame(frame):
        image = frame.astype(np.float32) / 255.0
        image = torch.from_numpy(transform(dict(image=image))["image"])
        return image.unsqueeze(0).unsqueeze(0)

    frames = map(transform_frame, chain([first_frame], frames))

    pre_input = None
    for win in _sliding_windows(frames, INFER_LEN, INFER_LEN - OVERLAP):
        cur_input = torch.cat(win, dim=1).to(device)
        if pre_input is not None:
            cur_input[:, :OVERLAP, ...] = pre_input[:, KEYFRAMES, ...]

        with torch.no_grad():
            with torch.autocast(device_type=device, enabled=(not fp32)):
                depth = vda.forward(cur_input)

        depth = depth.to(cur_input.dtype)
        depth = F.interpolate(depth.flatten(0, 1).unsqueeze(1), size=(
            frame_height, frame_width), mode='bilinear', align_corners=True)

        print(depth)

        yield [
            depth[i][0].cpu().numpy()
            for i in range(depth.shape[0])
        ]

        pre_input = cur_input


def _create_depth_stream(vda, frames, input_size=518, device='cuda', fp32=False):
    aligned = []
    ref_align = []
    align_len = OVERLAP - INTERP_LEN

    kf_align_list = KEYFRAMES[:align_len]

    first = True
    for depth_frame in _create_window_stream(vda, frames, input_size, device, fp32):
        if first:
            aligned += depth_frame

            yield from aligned[:-INTERP_LEN]
            aligned = aligned[-INTERP_LEN:]

            for kf_id in kf_align_list:
                ref_align.append(depth_frame[kf_id])

            first = False
            continue

        curr_align = []
        for i in range(len(kf_align_list)):
            curr_align.append(depth_frame[i])

        scale, shift = compute_scale_and_shift(
            np.concatenate(curr_align),
            np.concatenate(ref_align),
            np.concatenate(np.ones_like(ref_align) == 1)
        )

        pre_depth_list = aligned[-INTERP_LEN:]
        post_depth_list = depth_frame[align_len:OVERLAP]

        for i in range(len(post_depth_list)):
            post_depth_list[i] = post_depth_list[i] * scale + shift
            post_depth_list[i][post_depth_list[i] < 0] = 0

        aligned[-INTERP_LEN:] = get_interpolate_frames(
            pre_depth_list, post_depth_list)

        for i in range(OVERLAP, INFER_LEN):
            new_depth = depth_frame[i] * scale + shift
            new_depth[new_depth < 0] = 0
            aligned.append(new_depth)

        yield from aligned[:-INTERP_LEN]
        aligned = aligned[-INTERP_LEN:]

        ref_align = ref_align[:1]
        for kf_id in kf_align_list[1:]:
            new_depth = depth_frame[kf_id] * scale + shift
            new_depth[new_depth < 0] = 0
            ref_align.append(new_depth)

    yield from aligned


def _infer_video_depth(vda, frames, input_size=518, device='cuda', fp32=False):
    frames = tee(frames)
    depth = _create_depth_stream(vda, frames[0], input_size, device, fp32)

    for _, depth in zip(frames[1], depth):
        yield depth


class VideoDepthAnythingModel:
    device: str

    def __init__(self, *, device: str):
        self.device = device

        self.model = VideoDepthAnything(
            encoder="vits",
            features=64,
            out_channels=[48, 96, 192, 384]
        )

        self.model.load_state_dict(torch.load(
            "./models/video_depth_anything/checkpoints/video_depth_anything_vits.pth", map_location="cpu"), strict=True)

        self.model.to(device)
        self.model.eval()

    def create_stream(self, video_stream: Iterator[np.array]) -> Iterator[np.array]:
        return _infer_video_depth(self.model, video_stream)
