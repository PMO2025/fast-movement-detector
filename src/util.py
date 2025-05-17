import av
import cv2
import numpy as np


# def read_video(path, width, height):
#     cap = cv2.VideoCapture(path)
#     fps = cap.get(cv2.CAP_PROP_FPS)
#     frames = []

#     while cap.isOpened():
#         succ, frame = cap.read()
#         if not succ:
#             break

#         frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#         frame = cv2.resize(frame, (width, height))
#         frames.append(frame)

#     cap.release()
#     return np.stack(frames, axis=0), fps


# def write_video(path, frames, fps, codec=None):
#     height, width, *_ = frames[0].shape

#     if frames[0].dtype != np.uint8:
#         norm = max(frame.max() for frame in frames)

#     if codec is not None:
#         if type(codec) is str:
#             codec = cv2.VideoWriter_fourcc(*codec)

#     out = cv2.VideoWriter(path, codec, fps, (width, height))

#     for frame in frames:
#         if frame.dtype != np.uint8:
#             frame = (frame / norm * 255).astype(np.uint8)
#             # frame = (frame * 255).astype(np.uint8)

#         if len(frame.shape) == 2:
#             frame = cv2.applyColorMap(frame, cv2.COLORMAP_JET)

#         out.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

#     out.release()

class VideoWriter:
    def __init__(self, path, format, fps):
        if format != "webm":
            raise ValueError("unknown format")

        self.container = av.open(path, mode="w")
        self.stream = None
        self.format = format
        self.fps = fps

    def write(self, frame):
        if self.stream is None and self.format == "webm":
            self.stream = self.container.add_stream("libvpx", rate=self.fps)
            self.stream.width = frame.shape[1]
            self.stream.height = frame.shape[0]
            self.stream.pix_fmt = "yuv420p"
            self.stream.bit_rate = 7642888

        frame = av.VideoFrame.from_ndarray(frame, format="rgb24")

        for packet in self.stream.encode(frame):
            self.container.mux(packet)

    def close(self):
        for packet in self.stream.encode():
            self.container.mux(packet)

        self.container.close()


def stream_video(path):
    container = av.open(path)

    fps = container.streams[0].average_rate

    def gen():
        # print(container.bit_rate)
        for frame in container.decode(video=0):
            yield np.asarray(frame.to_image())

    return gen(), fps


def read_video(path):
    stream, fps = stream_video(path)
    return list(stream), fps


def fmt_number(number, digits=3):
    return str(int(number * (10**digits)) / (10**digits))


def normalize(x):
    if type(x) != np.array:
        x = np.array(x)

    return x / np.linalg.norm(x)


class Stream:
    def __init__(self, iter):
        self._iter = iter
        self._started = False
        self._id = 0

    def use(self):
        if self._started:
            raise "???"

        self._id += 1


class StreamIter:
    def __init__(self, stream, id):
        self._stream = stream
        self._id = id

    def __iter__(self):
        return self

    def __next__(self):
        return self._stream._next(self._id)

    def __len__(self):
        return self._stream._next(self._id)
