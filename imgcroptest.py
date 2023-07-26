import time
import keyboard
import pyautogui
import ctypes
import os
import cv2
import numpy as np
from PIL import Image

PATH = "./pic/screenshot.png"

def attackPattern(threshold):
    img = cv2.imread(PATH)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    redMask = (np.array([0,150,150]),np.array([20,255,255]),np.array([160,150,150]),np.array([180,255,255]))
    mask1 = cv2.inRange(hsv, redMask[0], redMask[1])
    mask2 = cv2.inRange(hsv, redMask[2], redMask[3])
    mask = mask1 + mask2
    maskedImg = cv2.bitwise_and(img, img, mask=mask)
    cv2.imwrite("./pic/cropped.png", maskedImg)
    targetImg = cv2.imread("./model/basebombing.png")
    height, width, channel = targetImg.shape
    result = cv2.matchTemplate(maskedImg, targetImg, cv2.TM_CCORR_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    print("bombing run\t" + str(max_val))
    ul = cv2.minMaxLoc(result)[3]
    lr = (ul[0] + width, ul[1] + height)
    show = Image.open(PATH)
    show = show.crop((ul[0], ul[1], lr[0], lr[1]))
    show.save("./pic/target.png")
    """
    
    
    "start matching"
    
    
    if max_val > threshold:
        print("yo")
        ul = cv2.minMaxLoc(result)[2]
        lr = (ul[0] + width, ul[1] + height)
        center = (int((ul[0] + lr[0]) / 2), int((ul[1] + lr[1]) / 2))
    """


attackPattern(0.85)

if __name__ == '__main__':
    print("yay")