#!/bin/bash
docker build -t mo_gradcam:test0102 .
docker run -it --rm --gpus=all --shm-size="64g" --name test mo_gradcam:test0102