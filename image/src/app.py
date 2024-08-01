# Flask
from flask import Flask, request, render_template, jsonify
from gevent.pywsgi import WSGIServer

# Some utilites
import os
import base64
import logging
from config import UPLOAD_FOLDER, base64_to_image
from gradcam_mo import initialize_model

# Declare a flask app
app = Flask(__name__, template_folder='templates', static_folder='static')

# add log file
logging.basicConfig(level=logging.INFO)


@app.route('/', methods=['GET'])
def index():
    # Main page
    app.logger.info("Main page done")
    return render_template('index.html')


@app.route('/predict', methods=['POST'])
def upload_image():
    try:
        if request.method == 'POST':              
            img = base64_to_image(request.json)

            # save the uploaded file
            image_path = os.path.join(UPLOAD_FOLDER, 'uploaded_image.png')
            img.save(image_path)

            # prediction
            model = initialize_model()
            model(image_path, '/workspace/yolov5/output')


            # Convert prediction result image to Base64
            with open('output/output.png', 'rb') as result_img_file:
                encoded_result_image = base64.b64encode(result_img_file.read()).decode('utf-8')

            # Convert img to url
            image_data_url = f"data:image/png;base64,{encoded_result_image}"

            # Prepare response data with image in Base64 format
            response_data = {
                'image':image_data_url,
            }

            # Return response with JSON format containing Base64 image data
            return jsonify(response_data), 200
        else:
            return jsonify({'error': 'File not found'}), 300

    except Exception as e:
        app.logger.error(f'Failed to process image: {str(e)}')
        return jsonify({'error': 'Failed to process the image'}), 500

    return jsonify({'message': 'Image processed successfully'}), 200



if __name__ == '__main__':

    # Serve the app with gevent
    http_server = WSGIServer(('0.0.0.0', 3000), app)
    print('Serving on http://127.0.0.1:3000')
    http_server.serve_forever()


