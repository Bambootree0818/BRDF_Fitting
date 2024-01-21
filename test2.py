import mitsuba as mi
import numpy as np
import matplotlib.pyplot as plt

print(mi.variants())

mi.set_variant('cuda_ad_spectral')
import drjit as dr

# ground truth bsdf
bsdf_gt_dict = {
    'type': 'principled',
    'base_color': {
            'type': 'rgb',
            'value': [1.0, 0.0, 0.0]
    },
    'metallic': 0.1,
    'specular': 1.0,
    'roughness': 0.5,
    'spec_tint': 0.0,
    'anisotropic': 0.0,
    'sheen': 0.0,
    'sheen_tint': 0.0,
    'clearcoat': 0.0,
    'clearcoat_gloss': 1.0,
    'spec_trans': 0.0
}

# bsdf to optimize
bsdf_opt_dict = {
    'type': 'principled',
    'base_color': {
            'type': 'rgb',
            'value': [1.0, 0.0, 0.0]
    },
    'metallic': 1.0,
    'specular': 0.3,
    'roughness': 0.8,
    'spec_tint': 0.0,
    'anisotropic': 0.0,
    'sheen': 0.0,
    'sheen_tint': 0.0,
    'clearcoat': 0.,
    'clearcoat_gloss': 1.0,
    'spec_trans': 0.0
}
keys = {
    #'base_color.value',
    'metallic.value',
    'roughness.value',
    'specular',
    'clearcoat.value'
}

# load the two bsdfs
bsdf_gt = mi.load_dict(bsdf_gt_dict)
bsdf_opt = mi.load_dict(bsdf_opt_dict)
print(bsdf_opt)

params_gt = mi.traverse(bsdf_gt)
params_opt = mi.traverse(bsdf_opt)
print(params_opt)

# set up the optimizer
opt = mi.ad.Adam(lr=5e-2)
# parameter to optimize
for key in keys:
    opt[key] = params_opt[key]
    params_opt[key] = opt[key]

# set up the sampler
sampler = mi.load_dict({
    'type': 'independent',
})

sampler.seed(0, wavefront_size=int(1e7))

# optimization loop
losses = []
for i in range(50):
    params_opt.update()
    sampler.seed(i)
    # dummy surface interaction (we don't have a scene, just a bsdf)
    si = dr.zeros(mi.SurfaceInteraction3f)
    si.wavelengths = [400.0, 500.0, 600.0, 700.0] # ?? visible spectrum
    # get some cosine distributed wi and wo 
    si.wi = mi.warp.square_to_cosine_hemisphere(sampler.next_2d())
    wo = mi.warp.square_to_cosine_hemisphere(sampler.next_2d())
    # eval both bsdfs
    values = bsdf_opt.eval(mi.BSDFContext(), si, wo)
    values_ref = bsdf_gt.eval(mi.BSDFContext(), si, wo)
    # compute the loss (losses are per measurement, is this the correct way??)
    loss = dr.mean(dr.mean(dr.sqr(values- values_ref)))
    losses.append(loss)
    # propagate
    dr.backward(loss)
    opt.step()
    # clamp
    for key in keys:
        opt[key] = dr.clamp(opt[key], 0.0, 1.0)
    # update the values after propagation
    for key in keys:
        params_opt[key] = opt[key]
    # print some info
    print('Iteration:', i)
    print("reflectance:",  opt['metallic.value'])
    print("loss:", loss)
    print()

errors = np.asarray(losses)
print(errors.shape)

# plot a few of the losses (there are 10 million of these!)
plt.plot(errors)
plt.show()

# create a renderable scene using the ground truth bsdf
scene_gt = mi.load_dict({
    'type': 'scene',
    'integrator': {
        'type': 'path'
    },
    'light': {
        'type': 'constant',
        'radiance': 0.99,
    },
    'sphere' : {
        'type': 'sphere',
        'bsdf': bsdf_gt_dict
    },
    'sensor': {
        'type': 'perspective',
        'to_world': mi.ScalarTransform4f.look_at(origin=[0, -5, 5],
                                                 target=[0, 0, 0],
                                                 up=[0, 0, 1]),
    }
})

# creat a renderable scene using the optimized bsdf
scene_opt = mi.load_dict({
    'type': 'scene',
    'integrator': {
        'type': 'path'
    },
    'light': {
        'type': 'constant',
        'radiance': 0.99,
    },
    'sphere' : {
        'type': 'sphere',
        'bsdf': bsdf_opt_dict
    },
    'sensor': {
        'type': 'perspective',
        'to_world': mi.ScalarTransform4f.look_at(origin=[0, -5, 5],
                                                 target=[0, 0, 0],
                                                 up=[0, 0, 1]),
    }
})

print('scene opt:', scene_opt)
print('-------------------')
print('scene  gt:', scene_gt)
# render the two scenes (before the optimization)
img_gt = mi.render(scene_gt, spp=64)
img_opt = mi.render(scene_opt, spp=64)

# udpate scene using the optimized values
scene_params = mi.traverse(scene_opt)
scene_params['sphere.bsdf.reflectance.values'] = opt['reflectance']
scene_params.update()
print('scene opt:', scene_opt)
# render the scene using optimized values
img_opt2 = mi.render(scene_opt, spp=64)

# plot the rendered images
f, axarr = plt.subplots(3,1, figsize=(2,8))
axarr[0].imshow(img_gt ** (1.0/2.2)), axarr[0].set_title('Ground Truth')
axarr[1].imshow(img_opt ** (1.0/2.2)), axarr[1].set_title('UnOptimized')
axarr[2].imshow(img_opt2 ** (1.0/2.2)), axarr[2].set_title('Optimized')
plt.show()