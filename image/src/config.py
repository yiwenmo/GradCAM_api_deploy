# utils.py
import base64
import re
from PIL import Image
from io import BytesIO

UPLOAD_FOLDER = '/workspace/yolov5/data'
OUTPUT_FOLDER = '/workspace/yolov5/output'


def base64_to_image(img_base64):
    # decode base64 image
    img_data = re.sub('^data:image/.+;base64,', '', img_base64)
    # img_data = base64.b64decode(base64_str.split(',')[1])
    
    # turn base64 to PIL
    img = Image.open(BytesIO(base64.b64decode(img_data)))
    
    return img
