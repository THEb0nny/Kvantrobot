#!/usr/bin/env python3

import rospy
import numpy as np
import cv2

from sensor_msgs.msg import Image, CompressedImage
from cv_bridge import CvBridge

import math
import os

from time import sleep
from std_msgs.msg import String

pub_image = rospy.Publisher('sign_image', Image, queue_size = 1)
pub_sign = rospy.Publisher('sign', String, queue_size = 1)
cvBridge = CvBridge()
counter = 1
FLANN_INDEX_KDTREE = 0
index_params = dict(algorithm = FLANN_INDEX_KDTREE, trees = 5)
search_params = dict(checks = 50)
flann = cv2.FlannBasedMatcher(index_params, search_params)

def cbImageProjection(data):
    global kp_ideal, des_ideal, sift, counter, flann

    rospy.loginfo(counter)

    if counter % 3 != 0:
        counter += 1
        return
    else:
        counter = 1
    
    cv_image_original = cvBridge.imgmsg_to_cv2(data, "bgr8")
    cv_image_gray = cv2.cvtColor(cv_image_original, cv2.COLOR_BGR2GRAY)
    kp, des = sift.detectAndCompute(cv_image_gray, None)
    cv_image_original = cv2.drawKeypoints(cv_image_gray, kp, None, (255, 0, 0), 4)
    for i in range(0, 4):
        matches = flann.knnMatch(des, des_ideal[i], k = 2)
        result = compare_matches(kp, kp_ideal[i], matches)
        sign_msg = String()
        if result == True:
            if i == 0:
                sign_msg.data = "stop"
            elif i == 1:
                sign_msg.data = "turn_left"
            elif i == 2:
                sign_msg.data = "turn_right"
            elif i == 3:
                sign_msg.data = "reversal"
            break
        else:
            sign_mgs.data = "none"
        
    print(sign_msg.data)
    pub_sign.publish(sign_msg)
    pub_image.publish(cvBridge.cv2_to_imgmsg(cv_image_original, "rgb8"))
    rospy.loginfo(3)

def compare_matches(kp, kp_ideal, matches):
    MATCHES_ERR = 50000
    MATCHES_DIST_MIN = 7
    good = []
    for m, n in matches:
        if m.distance < 0.7 * n.distance:
            good.append(m)
        
    if len(good) > MATCHES_DIST_MIN:
        src_pts = np.float32([kp[m.queryIdx].pt for m in good])
        dst_pts = np.float32([kp_ideal[m.trainIdx].pt for m in good])
        #sift = cv2.SIFT_create()
        mse_err = find_mse(src_pts, dst_pts)
        print("mse_err: ", mse_err)
        if mse_err < MATCHES_ERR:
            return True
    return False

def find_mse(arr1, arr2):
    err = (arr1 - arr2) ** 2
    sum_err = err.sum()
    suze = arr1.shape[0]
    sum_err = sum_err / size
    return sum_err

def standart_signs():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    dir_path = dir_path.replace('kvantbot_contest/src', 'kvantbot_contest/')
    dir_path += 'data_set/detect_sign/'
    img1 = cv2.imread(dir_path + 'stop.jpg', 0)
    img2 = cv2.imread(dir_path + 'turn_left.jpg', 0)
    img3 = cv2.imread(dir_path + 'turn_right.jpg', 0)
    img4 = cv2.imread(dir_path + 'reversal.jpg', 0)
    sift = cv2.SIFT_create()
    kp1, des1 = sift.detectAndCompute(img1, None)
    kp2, des2 = sift.detectAndCompute(img2, None)
    kp3, des3 = sift.detectAndCompute(img3, None)
    kp4, des4 = sift.detectAndCompute(img4, None)
    kp_ideal = [kp1, kp2, kp3, kp4]
    des_ideal = [des1, des2, des3, des4]
    return kp_ideal, des_ideal, sift

if __name__ == '__main__':
    rospy.init_node('image_projection')
    sum_image = rospy.Subscriber('/usb_cam/image_raw', Image, cbImageProjection, queue_size = 1)
    kp_ideal, des_ideal, sift = standart_signs()
    while not rospy.is_shutdown():
        try:
            rospy.sleep(0.1)
        except KeyboardInterrupt:
            break