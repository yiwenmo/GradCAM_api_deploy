docker build -t gradcam image

# docker run -it --rm --gpus=all --shm-size="64g" -p 3000:3000 --name demo gradcam # use GPU
docker run -it --rm -p 3000:3000 --name demo gradcam # use CPU