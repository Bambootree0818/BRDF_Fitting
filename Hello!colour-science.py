import colour as colour
from colour.models import RGB_COLOURSPACE_BT2020
from colour.models import RGB_COLOURSPACE_sRGB
from colour.models import RGB_COLOURSPACE_ADOBE_RGB1998
import numpy as np

# 反射率データ
reflectance = {
    465 : 0.0133401652290821,
    525 : 0.015336792652988,
    630 : 0.209678081325707
}

# 光源D65のスペクトルデータ（近似値）
# 実際の計算ではもっと細かい波長でのデータが必要ですが、
# ここでは与えられた3つの波長のみを使用します。
D65_spectrum = {
    465: 0.9817,  
    525: 1.0624,  
    630: 0.8329
}

# 等色関数の値
color_matching_functions = {
    465: (0.2219781, 0.1060145, 1.42844),
    525: (0.1268468, 0.7946448, 0.03751912),
    630: (0.6924717, 0.2980865, 0.0)
}

#定数
K = 100 / 10*sum(D65_spectrum[λ] * color_matching_functions[λ][1] for λ in reflectance)

# XYZ色空間の値を計算
X = 10 * sum(reflectance[λ] * D65_spectrum[λ] * color_matching_functions[λ][0] for λ in reflectance) * K
Y = 10 * sum(reflectance[λ] * D65_spectrum[λ] * color_matching_functions[λ][1] for λ in reflectance) * K
Z = 10 * sum(reflectance[λ] * D65_spectrum[λ] * color_matching_functions[λ][2] for λ in reflectance) * K

#print(Y)
#print(X,Y,Z)

value = np.array([18.99/100,9.54/100,0.9/100])

illuminant_RGB = np.array([0.31270, 0.32900])
illuminant_XYZ = np.array([0.31270, 0.32900])
chromatic_adaptation_transform = 'Bradford'
matrix_RGB_to_XYZ = np.array([[0.41240000, 0.35760000, 0.18050000],
                              [0.21260000, 0.71520000, 0.07220000],
                              [0.01930000, 0.11920000, 0.95050000]])

#xyz = colour.RGB_to_XYZ(value,illuminant_RGB, illuminant_XYZ, matrix_RGB_to_XYZ)
xyz = colour.RGB_to_XYZ(value,RGB_COLOURSPACE_BT2020,illuminant_XYZ)
rgb_s = colour.XYZ_to_RGB(value,RGB_COLOURSPACE_sRGB,illuminant_XYZ)
rgb_a = colour.XYZ_to_RGB(value,RGB_COLOURSPACE_ADOBE_RGB1998,illuminant_XYZ)
rgb_bt = colour.XYZ_to_RGB(value,RGB_COLOURSPACE_BT2020,illuminant_XYZ)

print(K)
print(rgb_s[0],rgb_s[1],rgb_s[2])
print(rgb_a[0],rgb_a[1],rgb_a[2])
print(rgb_bt[0],rgb_bt[1],rgb_bt[2])