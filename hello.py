import mitsuba as mi
import matplotlib.pyplot as plt

mi.set_variant("cuda_ad_rgb")

scene = mi.load_file("scene.xml")

image = mi.render(scene, spp=516)
mi.util.convert_to_bitmap(image)

plt.axis("off")
plt.imshow(image ** (1.0 / 2.2)); # approximate sRGB tonemapping
plt.show() 