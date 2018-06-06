# -*- coding: utf-8 -*-
"""Hello, Colaboratory

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/notebooks/welcome.ipynb
"""

# !git clone https://github.com/tensorflow/models.git

import os

os.chdir('./src/')

# if not os.path.exists('./protoc-3.3.0-linux-x86_64.zip'):
#     os.system('curl -OL https://github.com/google/protobuf/releases/download/v3.3.0/protoc-3.3.0-linux-x86_64.zip')
#     os.system('unzip protoc-3.3.0-linux-x86_64.zip -d protoc3')
#     os.system('mkdi')
#     os.system('mv protoc3/bin/* ./local/bin/')
#     os.system('mv protoc3/include/* ./local/include/')
#     os.system('protoc object_detection/protos/*.proto --python_out=.')

os.chdir('./object_detection/')

import numpy as np
import os
import six.moves.urllib as urllib
import sys
import tarfile
import tensorflow as tf
import zipfile

from collections import defaultdict
from io import StringIO
# from matplotlib import pyplot as plt
from PIL import Image

# This is needed since the notebook is stored in the object_detection folder.
sys.path.append("..")
from object_detection.utils import ops as utils_ops

if tf.__version__ < '1.4.0':
    os.system('pip install --upgrade tensorflow')
  # raise ImportError('Please upgrade your tensorflow installation to v1.4.* or later!')

# %matplotlib inline
from utils import label_map_util
from utils import visualization_utils as vis_util

os.chdir('../../')

class classifier:
    # What model to download.
    MODEL_NAME = 'ssd_mobilenet_v1_coco_2017_11_17'
    MODEL_FILE = MODEL_NAME + '.tar.gz'
    DOWNLOAD_BASE = 'http://download.tensorflow.org/models/object_detection/'
    # Path to frozen detection graph. This is the actual model that is used for the object detection.
    PATH_TO_CKPT = MODEL_NAME + '/frozen_inference_graph.pb'
    # List of the strings that is used to add correct label for each box.
    PATH_TO_LABELS = os.path.join('./src/object_detection/data', 'mscoco_label_map.pbtxt')

    NUM_CLASSES = 90

    # Size, in inches, of the output images.
    IMAGE_SIZE = (12, 8)

    def __init__(self):
        # os.popen("protoc ./src/object_detection/protos/*.proto --python_out=.")
        # sys.path.append("..")
        if tf.__version__ < '1.4.0':
            raise ImportError('Please upgrade your tensorflow installation to v1.4.* or later!')

        # opener = urllib.request.URLopener()
        # opener.retrieve(self.DOWNLOAD_BASE + self.MODEL_FILE, self.MODEL_FILE)
        # tar_file = tarfile.open(self.MODEL_FILE)
        # for file in tar_file.getmembers():
        #   file_name = os.path.basename(file.name)
        #   if 'frozen_inference_graph.pb' in file_name:
        #     tar_file.extract(file, os.getcwd())

        self.detection_graph = tf.Graph()
        with self.detection_graph.as_default():
          od_graph_def = tf.GraphDef()
          with tf.gfile.GFile(self.PATH_TO_CKPT, 'rb') as fid:
            serialized_graph = fid.read()
            od_graph_def.ParseFromString(serialized_graph)
            tf.import_graph_def(od_graph_def, name='')

        label_map = label_map_util.load_labelmap(self.PATH_TO_LABELS)
        categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=self.NUM_CLASSES, use_display_name=True)
        category_index = label_map_util.create_category_index(categories)

    def load_image_into_numpy_array(self, image):
      (im_width, im_height) = image.size
      return np.array(image.getdata()).reshape(
          (im_height, im_width, 3)).astype(np.uint8)

    def run_inference_for_single_image(self, image, graph):
      with graph.as_default():
        with tf.Session() as sess:
          # Get handles to input and output tensors
          ops = tf.get_default_graph().get_operations()
          all_tensor_names = {output.name for op in ops for output in op.outputs}
          tensor_dict = {}
          for key in [
              'num_detections', 'detection_boxes', 'detection_scores',
              'detection_classes', 'detection_masks'
          ]:
            tensor_name = key + ':0'
            if tensor_name in all_tensor_names:
              tensor_dict[key] = tf.get_default_graph().get_tensor_by_name(
                  tensor_name)
          if 'detection_masks' in tensor_dict:
            # The following processing is only for single image
            detection_boxes = tf.squeeze(tensor_dict['detection_boxes'], [0])
            detection_masks = tf.squeeze(tensor_dict['detection_masks'], [0])
            # Reframe is required to translate mask from box coordinates to image coordinates and fit the image size.
            real_num_detection = tf.cast(tensor_dict['num_detections'][0], tf.int32)
            detection_boxes = tf.slice(detection_boxes, [0, 0], [real_num_detection, -1])
            detection_masks = tf.slice(detection_masks, [0, 0, 0], [real_num_detection, -1, -1])
            detection_masks_reframed = utils_ops.reframe_box_masks_to_image_masks(
                detection_masks, detection_boxes, image.shape[0], image.shape[1])
            detection_masks_reframed = tf.cast(
                tf.greater(detection_masks_reframed, 0.5), tf.uint8)
            # Follow the convention by adding back the batch dimension
            tensor_dict['detection_masks'] = tf.expand_dims(
                detection_masks_reframed, 0)
          image_tensor = tf.get_default_graph().get_tensor_by_name('image_tensor:0')

          # Run inference
          output_dict = sess.run(tensor_dict,
                                 feed_dict={image_tensor: np.expand_dims(image, 0)})

          # all outputs are float32 numpy arrays, so convert types as appropriate
          output_dict['num_detections'] = int(output_dict['num_detections'][0])
          output_dict['detection_classes'] = output_dict[
              'detection_classes'][0].astype(np.uint8)
          output_dict['detection_boxes'] = output_dict['detection_boxes'][0]
          output_dict['detection_scores'] = output_dict['detection_scores'][0]
          if 'detection_masks' in output_dict:
            output_dict['detection_masks'] = output_dict['detection_masks'][0]
      return output_dict

    def detect(self, image):
      # the array based representation of the image will be used later in order to prepare the
      # result image with boxes and labels on it.
      image_np = self.load_image_into_numpy_array(image)
      # Expand dimensions since the model expects images to have shape: [1, None, None, 3]
      image_np_expanded = np.expand_dims(image_np, axis=0)
      # Actual detection.
      output_dict = self.run_inference_for_single_image(image_np, self.detection_graph)
      # Visualization of the results of a detection.

      boxes = output_dict['detection_scores'] > 0.5
      boxes = [i for i, x in enumerate(boxes) if x]
      boxes = output_dict['detection_boxes'][boxes]

      ymin = boxes[0,0]
      xmin = boxes[0,1]
      ymax = boxes[0,2]
      xmax = boxes[0,3]

      (im_width, im_height) = image.size
      (xminn, xmaxx, yminn, ymaxx) = (xmin * im_width, xmax * im_width, ymin * im_height, ymax * im_height)
      cropped_image = tf.image.crop_to_bounding_box(image_np, int(yminn), int(xminn),int(ymaxx - yminn), int(xmaxx - xminn))
      sess = tf.Session()
      img_data = sess.run(cropped_image)
      sess.close()

      # plt.figure(figsize=self.IMAGE_SIZE)
      # plt.imshow(img_data)

      r = img_data[:, :, 0] > 200
      g = img_data[:, :, 1] > 200
      y = r & g
      print('R',sum(sum(r)))
      print('Y',sum(sum(y)))
      print('G',sum(sum(g)))

# !wget https://cdn-images-1.medium.com/max/800/1*rfsKlnTf3pkN8C0i79O8SQ.jpeg -O ./test_images/traffic_g.jpg
# !wget https://cdn-images-1.medium.com/max/800/1*lHCzOcapHKRqfwd-O1dcLw.jpeg -O ./test_images/traffic_y.jpg
# !wget https://cdn-images-1.medium.com/max/800/1*AcigwfSCTELcCOp912IV2w.jpeg -O ./test_images/traffic_r.jpg

cf = classifier()

cf.detect(Image.open('./src/object_detection/test_images/traffic_r.jpeg'))

cf.detect(Image.open('./src/object_detection/test_images/traffic_g.jpeg'))
#
cf.detect(Image.open('./src/object_detection/test_images/traffic_y.jpeg'))