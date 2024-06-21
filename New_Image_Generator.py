import os
import json
from PIL import Image

def create_single_color_image(color, size=(100, 100)):
    """ Create a single color image with the specified RGB color and size. """
    image = Image.new("RGBA", size, (color[0] , color[1], color[2] , 255))
    return image

def convert_rgb(rgb_0_to_1):
    gamma = 2.2
    # 0〜1の範囲にクリップする
    rgb_0_to_1 = [min(max(value, 0), 1) for value in rgb_0_to_1]
    # ガンマ補正を適用
    rgb_corrected = [max(value ** (1/gamma), 0) for value in rgb_0_to_1]
    # 0~255にスケーリング
    rgb_255 = [int(value * 255) for value in rgb_corrected]
    return rgb_255

def process_json_files(input_folder, output_folder):
    """ Process all JSON files in the specified folder to extract name and base_color.value, then create and save images. """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    for filename in os.listdir(input_folder):
        file_path = os.path.join(input_folder, filename)
        if os.path.isfile(file_path):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    name = data["name"]
                    base_color = data["base_color.value"]
                    base_color = convert_rgb(base_color)
                    image = create_single_color_image(base_color)
                    image.save(os.path.join(output_folder, f"{name}.png"))
            except json.JSONDecodeError:
                # If the file is not a valid JSON, skip it
                print(f"Skipping non-JSON file: {filename}")

# フォルダパスを指定してください
input_folder = "Result_json"
output_folder = "basecolor_ref_another"
process_json_files(input_folder, output_folder)
