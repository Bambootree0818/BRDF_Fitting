import mitsuba as mi
import drjit as dr
import numpy as np

#利用可能なバリアントを表示
variants = mi.variants()
print(variants)

#cudaバリアントをセット
mi.set_variant('cuda_ad_rgb')
print(mi.variant())

# 粗い導体のBSDFを定義（GGX分布を使用）
bsdf = mi.load_dict({
    'type': 'principled',
    'base_color': {
            'type': 'rgb',
            'value': [1.0, 1.0, 1.0]
    },
    'metallic': 0.0,
    'specular': 1.0,
    'roughness': 0.5,
    'spec_tint': 0.0,
    'anisotropic': 0.0,
    'sheen': 0.0,
    'sheen_tint': 0.0,
    'clearcoat': 1.00,
    'clearcoat_gloss': 1.0,
    'spec_trans': 0.0
})

keys = {
    'basecolor.value'
    'metallic.value'
    'roughness.value'
    'specular.value'
}

#球座標からディレクショナルベクトルへの変換
def sph_to_dir(theta, phi):
    st, ct = dr.sincos(theta)
    sp, cp = dr.sincos(phi)
    return mi.Vector3f(cp * st, sp * st, ct)

# サーフェスインタラクション（ダミー）を作成
si = mi.SurfaceInteraction3f()
#si.wavelengths = [465.0, 525.0, 630.0, 700.0]


# 入射方向を45度の仰角で設定
si.wi = sph_to_dir(dr.deg2rad(0.0), 0)

# 球面上のグリッドを作成し、それを球面にマッピング
res = 300
theta_o, phi_o = dr.meshgrid(
    dr.linspace(mi.Float, 0,     dr.pi,     res),
    dr.linspace(mi.Float, 0, 2 * dr.pi, 2 * res)
)
wo = sph_to_dir(theta_o, phi_o)

# 配列全体（18000方向）でBSDFを一度に評価
values = bsdf.eval(mi.BSDFContext(), si, wo)
#values = np.array(values)
#values = np.delete(values,3,axis=1)
#values = dr.cuda.Array3f(values)
print(values)