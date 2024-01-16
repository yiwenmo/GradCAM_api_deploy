#!/bin/bash
docker build -t mo_gradcam:test0103 .
# docker run -it --rm --gpus=all --shm-size="64g" --name test mo_gradcam:test0102
docker run -it --gpus=all --shm-size="64g" --name test_demo mo_gradcam:test0103