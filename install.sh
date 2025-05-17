#!/bin/bash

set -e

rm -rf .venv models

# setup venv
python3.10 -m venv .venv
source ./.venv/bin/activate
python3.10 -m pip install -r requirements.txt

mkdir models
cd models

mkdir yolo

# clone metric depth anything

git clone https://github.com/DepthAnything/Depth-Anything-V2.git depth_anything
cd depth_anything
git reset --hard e5a2732d3ea2cddc081d7bfd708fc0bf09f812f1

cd metric_depth
mkdir checkpoints
cd checkpoints

wget https://huggingface.co/depth-anything/Depth-Anything-V2-Metric-VKITTI-Small/resolve/a49638011c708103f1f0fcbdf138392539558bca/depth_anything_v2_metric_vkitti_vits.pth

cd ../../../..

# git https://huggingface.co/depth-anything/Depth-Anything-V2-Small/resolve/05bbaec5306c04f1fa00a8c376c7dcf4153e7fe8/depth_anything_v2_vits.pth
# python3.10 -m pip install -e "git+https://github.com/cvg/GeoCalib#egg=geocalib"

# av
# pip install -U xformers
