FROM nvcr.io/nvidia/pytorch:22.09-py3

RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y zip htop screen libgl1-mesa-glx && \
    python -m pip install --upgrade pip setuptools wheel && \
    python -m pip install pyyaml 

RUN pip install Flask gevent grad-cam

# install Yolov5
RUN git clone https://github.com/ultralytics/yolov5.git && \
    cd yolov5  && \
    pip install -U opencv-python && \
    pip install -r requirements.txt && \
    pip install "opencv-python-headless<4.3"


# debug 2025/8/7
RUN pip uninstall -y backports && \
    pip install backports.tarfile || true

ENV CUDA_HOME='/usr/local/cuda'
ARG FORCE_CUDA=1

WORKDIR /workspace/yolov5
ENV HOME=/workspace/yolov5

RUN mkdir -p /workspace/yolov5/output

# data and model
COPY src/img /workspace/yolov5/data/images/img
COPY models/best.pt /workspace/yolov5/models/best.pt
COPY models/yolov5s_arcade.yaml /workspace/yolov5/models/yolov5s_arcade.yaml

# script
COPY src/gradcam_mo.py /workspace/yolov5/gradcam_mo.py
COPY src/app.py /workspace/yolov5/app.py
COPY src/config.py /workspace/yolov5/config.py
COPY src/templates /workspace/yolov5/templates
COPY src/static /workspace/yolov5/static

EXPOSE 3000
CMD ["python", "app.py"]