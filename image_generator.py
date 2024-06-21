import cv2
import numpy as np
 
#ブランク画像
height = 512
width = 512
blank = np.zeros((height, width, 3))
blank += [144,41,6][::-1] #RGBで青指定

file_name = input('file name : ')
 
cv2.imwrite('basecolor_ref_another/' + file_name,blank)