FROM nvcr.io/nvidia/pytorch:22.09-py3

RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y zip htop screen libgl1-mesa-glx && \
    python -m pip install pyyaml 

RUN pip install Flask gevent


# install pytorch-grad-cam
RUN pip install grad-cam

# install Yolov5
RUN git clone https://github.com/ultralytics/yolov5.git && \
    cd yolov5  && \
    pip install -U opencv-python && \
    pip install -r requirements.txt && \
    pip install "opencv-python-headless<4.3"


ENV CUDA_HOME='/usr/local/cuda'
ARG FORCE_CUDA=1

WORKDIR /workspace/yolov5
ENV HOME=/workspace/yolov5

COPY src/static /workspace/Mask2Former/static