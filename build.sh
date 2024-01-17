#!/bin/bash
docker build -t gradcam image
# docker run -it --rm --gpus=all --shm-size="64g" -p 3000:3000 --name test_demo gradcam
docker run -it --rm -p 3000:3000 --name test_demo gradcam