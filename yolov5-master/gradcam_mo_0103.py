import warnings
warnings.filterwarnings('ignore')
warnings.simplefilter('ignore')
import torch, yaml, cv2, os, shutil
import numpy as np

np.random.seed(0)
import matplotlib.pyplot as plt
from tqdm import trange
from PIL import Image
from models.yolo import Model
from utils.general import intersect_dicts
from utils.augmentations import letterbox
from utils.general import xywh2xyxy

from pytorch_grad_cam import GradCAMPlusPlus, GradCAM, XGradCAM
from pytorch_grad_cam.utils.image import show_cam_on_image
from pytorch_grad_cam.activations_and_gradients import ActivationsAndGradients

class yolov5_heatmap:
    # load model and weight
    def __init__(self, weight, cfg, device, method, layer, backward_type, conf_threshold, genCAMNum):
        device = torch.device(device)
        ckpt = torch.load(weight)
        model_names = ckpt['model'].names
        csd = ckpt['model'].float().state_dict()  # checkpoint state_dict as FP32
        model = Model(cfg, ch=3, nc=len(model_names)).to(device)
        csd = intersect_dicts(csd, model.state_dict(), exclude=['anchor'])  # intersect
        model.load_state_dict(csd, strict=False)  # load
        model.eval()
        print(f'Transferred {len(csd)}/{len(model.state_dict())} items')

        # target layers
        target_layers = [eval(layer)]
        # self.target_layers = layers
        method = eval(method)

        colors = np.random.uniform(0, 255, size=(len(model_names), 3)).astype(np.int)
        self.__dict__.update(locals())

    def post_process(self, result):
        logits_ = result[..., 4:]
        boxes_ = result[..., :4]
        sorted, indices = torch.sort(logits_[..., 0], descending=True)
        return logits_[0][indices[0]], xywh2xyxy(boxes_[0][indices[0]]).cpu().detach().numpy()

    def draw_detections(self, box, color, name, img):
        xmin, ymin, xmax, ymax = list(map(int, list(box)))
        cv2.rectangle(img, (xmin, ymin), (xmax, ymax), tuple(int(x) for x in color), 2)
        cv2.putText(img, str(name), (xmin, ymin - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.8, tuple(int(x) for x in color), 2,
                    lineType=cv2.LINE_AA)
        return img
    
    def __call__(self, img_path, save_path, output_filename='output'):
        # remove dir if exist
        if os.path.exists(save_path):
            shutil.rmtree(save_path)
        # make dir if not exist
        os.makedirs(save_path, exist_ok=True)

        # img process
        img = cv2.imread(img_path)
        img = letterbox(img)[0]
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = np.float32(img) / 255.0
        tensor = torch.from_numpy(np.transpose(img, axes=[2, 0, 1])).unsqueeze(0).to(self.device) 

        # init ActivationsAndGradients
        grads = ActivationsAndGradients(self.model, self.target_layers, reshape_transform=None)

        # get ActivationsAndResult
        result = grads(tensor)
        activations = grads.activations[0].cpu().detach().numpy()

        # postprocess to yolo output
        post_result, post_boxes = self.post_process(result[0])
                                                   

        for i in trange(self.genCAMNum):
            if post_result[i][0] < self.conf_threshold:
                break

            self.model.zero_grad()
            if self.backward_type == 'conf':
                post_result[i, 0].backward(retain_graph=True)
            else:
                # get max probability for this prediction
                score = post_result[i, 1:].max()
                score.backward(retain_graph=True)

            # process heatmap
            gradients = grads.gradients[0]
            b, k, u, v = gradients.size()
            weights = self.method.get_cam_weights(self.method, None, None, None, activations,
                                                  gradients.detach().numpy())
            weights = weights.reshape((b, k, 1, 1))
            saliency_map = np.sum(weights * activations, axis=1)
            saliency_map = np.squeeze(np.maximum(saliency_map, 0))
            saliency_map = cv2.resize(saliency_map, (tensor.size(3), tensor.size(2)))
            saliency_map_min, saliency_map_max = saliency_map.min(), saliency_map.max()
            if (saliency_map_max - saliency_map_min) == 0:
                continue
            saliency_map = (saliency_map - saliency_map_min) / (saliency_map_max - saliency_map_min)
            
            # # add arcade_bbox_image
            # arcade_bbox_img = cv2.imread(arcade_bbox_image_path)
            # arcade_bbox_img = np.float32(arcade_bbox_img) / 255.0
            # blended_image = show_cam_on_image(arcade_bbox_img.copy(), saliency_map, use_rgb=False)

            # # save blend_img
            # blended_image_path = os.path.join(save_path, f'{output_filename}_blended.png')
            # cv2.imwrite(blended_image_path, blended_image)

            # add heatmap to image
            cam_image = show_cam_on_image(img.copy(), saliency_map, use_rgb=True)
            # cam_image = self.draw_detections(post_boxes[i], self.colors[int(post_result[i, 1:].argmax())],
            #                                  f'{self.model_names[int(post_result[i, 1:].argmax())]} {post_result[i][0]-0.01:.2f}',
            #                                  cam_image)
            cam_image = Image.fromarray(cam_image)
            cam_image.save(f'{save_path}/{output_filename}.png')


def get_params():
    params = {
        'weight': 'yolov5-master/models/best.pt',  # 訓練權重檔案.pt
        'cfg': 'yolov5-master/models/yolov5s_arcade.yaml',  # yaml存取模型架構
        'device': 'cpu',  # cuda:0 or cpu : 在本機端選cuda會出錯
        'method': 'GradCAM',  # Gradcam選擇
        'layer': 'model.model[23]',  # target layers
        'backward_type': 'conf',  # class or conf
        'conf_threshold': 0.6, 
        'genCAMNum': 5
    }
    return params

# process for one img
model = yolov5_heatmap(**get_params())
model("yolov5-master/data/images/test.png", 'yolov5-master/output')
print("Script execution finished!")


# # process for one img
# if __name__ == '__main__':
#     model = yolov5_heatmap(**get_params())
#     model("yolov5-master/data/images/test.png", 'yolov5-master/output')
#     print("Script execution finished!")


### Original Code
# process multiple img
# if __name__ == '__main__':
#     model = yolov5_heatmap(**get_params())
    
#     # Folder containing input images (with filenames like 'o7klq_tNY07Ud_HFRulR-A$a$4.31_gsv.png')
#     input_folder = 'data/images/img/test'
    
#     # Folder containing arcade bbox images (with filenames like 'o7klq_tNY07Ud_HFRulR-A$a$4.31_result.png')
#     arcade_bbox_folder = 'data/images/img/test'
    
#     # Output folder for saving heatmaps
#     output_folder = 'result'
    
#     # Iterate through input images
#     for input_filename in os.listdir(input_folder):
#         if input_filename.endswith('_gsv.png'):  # Check if it's an input image
#             input_image_path = os.path.join(input_folder, input_filename)
            
#             # Generate filename pattern for the corresponding arcade bbox image
#             arcade_bbox_filename = input_filename.replace('_gsv.png', '_result.png')
#             arcade_bbox_image_path = os.path.join(arcade_bbox_folder, arcade_bbox_filename)
            
#             if os.path.exists(arcade_bbox_image_path):  # Check if corresponding arcade bbox image exists
#                 # Get the desired layer index [2] from the model.layer string
#                 layer_idx = int(model.layer.split('[')[-1].split(']')[0])

#                 # Generate heatmap for each image and include the original image's name in the output file name
#                 output_filename = f'{os.path.splitext(input_filename)[0]}_{layer_idx}'
#                 # create new folder to save img
#                 model(input_image_path, os.path.join(output_folder, output_filename), arcade_bbox_image_path)
#                 print("Script execution finished!")
