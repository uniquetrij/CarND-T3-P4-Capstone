import os
import numpy as np
import os
import cv2
import rospy
import six.moves.urllib as urllib
import sys
import tarfile
import tensorflow as tf
import zipfile

from collections import defaultdict
from io import StringIO
from matplotlib import pyplot as plt
from PIL import Image
from styx_msgs.msg import TrafficLight

import time

rospy.logerr(os.getcwd())
sys.path.append('..')
from object_detection.tl_classifier import classifier



class TLClassifier(object):
    def __init__(self):
        #TODO load classifier
        self.cl = classifier()
        self.t = 0.0
        self.tl = TrafficLight.UNKNOWN
        pass

    def get_classification(self, image, light=TrafficLight.UNKNOWN):
        """Determines the color of the traffic light in the image

        Args:
            image (cv::Mat): image containing the traffic light

        Returns:
            int: ID of traffic light color (specified in styx_msgs/TrafficLight)

        """
        #TODO implement light color prediction

        if time.time() - self.t > 10 :
            self.t = time.time()
            image = Image.fromarray(image)
            tl = self.cl.detect(image)
            if tl:
                self.tl = tl
            rospy.loginfo(tl)

        return self.tl

        # return light
        # return TrafficLight.UNKNOWN
