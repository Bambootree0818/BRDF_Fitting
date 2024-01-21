import drjit as dr
import mitsuba as mi
import numpy as np
import matplotlib.pyplot as plt
import inspect

# Mitsubaのバリアントを設定（LLVMベースの自動微分とRGBスペクトルをサポート）
mi.set_variant('cuda_ad_rgb')

# 粗い導体のBSDFを定義（GGX分布を使用）
bsdf = mi.load_dict({
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
    'clearcoat': 1.0,
    'clearcoat_gloss': 1.0,
    'spec_trans': 0.0
})

def sph_to_dir(theta, phi):
    """球座標からディレクショナルベクトルへの変換"""
    st, ct = dr.sincos(theta)
    sp, cp = dr.sincos(phi)
    return mi.Vector3f(cp * st, sp * st, ct)

# サーフェスインタラクション（ダミー）を作成
si = dr.zeros(mi.SurfaceInteraction3f)


# 入射方向を45度の仰角で設定
si.wi = sph_to_dir(dr.deg2rad(0.0), 0)
print(si.wi)

# 球面上のグリッドを作成し、それを球面にマッピング
res = 300
theta_o, phi_o = dr.meshgrid(
    dr.linspace(mi.Float, 0,     dr.pi,     res),
    dr.linspace(mi.Float, 0, 2 * dr.pi, 2 * res)
)
wo = sph_to_dir(theta_o, phi_o)

# 配列全体（18000方向）でBSDFを一度に評価
values = bsdf.eval(mi.BSDFContext(), si, wo)
cont = mi.BSDFContext()

#print(cont)

# numpy配列に変換
values_np = np.array(values)

#print(values_np)

# BRDF値の赤色チャネルを抽出し、2Dグリッドに整形
values_r = values_np[:, 0]
values_r = values_r.reshape(2 * res, res).T

# 球座標に対する値をプロット
fig, ax = plt.subplots(figsize=(8, 4))

im = ax.imshow(values_r, extent=[0, 2 * np.pi, np.pi, 0], cmap='jet')

# ラベルと目盛りの設定
ax.set_xlabel(r'$\phi_o$', size=10)
ax.set_xticks([0, dr.pi, dr.two_pi])
ax.set_xticklabels(['0', '$\\pi$', '$2\\pi$'])
ax.set_ylabel(r'$\theta_o$', size=10)
ax.set_yticks([0, dr.pi / 2, dr.pi])
ax.set_yticklabels(['0', '$\\pi/2$', '$\\pi$'])

plt.show()  # 画像を表示
