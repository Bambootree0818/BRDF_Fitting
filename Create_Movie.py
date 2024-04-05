# Since we need to load all C3_Red images from the folder, let's identify all the images dynamically

import os
from PIL import Image
import numpy as np
from moviepy.editor import ImageSequenceClip

# The path to the directory containing the images
directory_path = 'gifs/'

# Get all the image paths
all_image_paths = [os.path.join(directory_path, f) for f in os.listdir(directory_path) if f.startswith('C3_Red') and f.endswith('.png')]

# Sort the images by their number to maintain the sequence
all_image_paths.sort(key=lambda x: int(x.split('C3_Red')[1].split('.png')[0]))

# Load the images and convert them to numpy arrays
all_images = [np.array(Image.open(image_path)) for image_path in all_image_paths]

# Create the clip
clip = ImageSequenceClip(all_images, fps=24)  # fps is the number of frames per second

# Write out the video file
clip.write_videofile("output_video.mp4", fps=24)


# Save as a GIF
#animated_gif_path = 'gifs/animated_C3_Red_complete.gif'
#all_images[0].save(animated_gif_path, save_all=True, append_images=all_images[1:], optimize=False, duration=100, loop=0)