import cv2
import numpy as np
 
#ブランク画像
height = 512
width = 512
blank = np.zeros((height, width, 3))
blank += [158,2,6][::-1] #RGBで青指定
 
cv2.imwrite('basecolor_ref_another/C3_Red_ref.png',blank)