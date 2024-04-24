import subprocess
import colour as colour
from colour.models import RGB_COLOURSPACE_BT2020
from colour.models import RGB_COLOURSPACE_sRGB
from colour.models import RGB_COLOURSPACE_ADOBE_RGB1998
import numpy as np

# Lab値を取得
def get_Lab_value(file_path, name):
    with open(file_path, 'r') as file:
        for line in file:
            key, value = line.strip().split(':')
            if key == name:
                # Lab値をカンマで分割してリストとして返す
                return list(map(float, value.split(',')))
    return None

def get_XYZ_value(Lab_value):
    XYZ_value = colour.Lab_to_XYZ(Lab_value)
    XYZ_value_list = XYZ_value.tolist()
    return XYZ_value_list

def get_rgb_value(xyz_value):
    rgb_value = colour.XYZ_to_sRGB(xyz_value)
    rgb_value_list = rgb_value.tolist()
    return rgb_value_list

# 以下の部分は変更なし
file_path = 'sample_Lab_data.txt'
name = input("名前を入力してください (例: C1): ")

Lab_value = get_Lab_value(file_path, name)

XYZ_value = get_XYZ_value(Lab_value)

rgb_value = get_rgb_value(XYZ_value)

if rgb_value:
    print(f"{name} のLav値: {Lab_value}")
    print(f"{name} のXYZ値: {XYZ_value}")
    print(f"{name} のRGB値: {rgb_value}")
else:
    print(f"{name} に対応するRGB値が見つかりませんでした。")


def inverse_gamma_correction(value):
    """Apply inverse gamma correction to a normalized value (0-1 range)."""
    if value <= 0.04045:
        return value / 12.92
    else:
        return ((value + 0.055) / 1.055) ** 2.4


# Normalize and apply inverse gamma correction
linear_rgb = [inverse_gamma_correction(c / 255.0) for c in rgb_value]

print(rgb_value)
