import mitsuba as mi  # Mitsuba 3D rendering frameworkをインポート
import drjit as dr  # 数値計算と自動微分をサポートするDr.Jitをインポート
import matplotlib.pyplot as plt  # グラフや画像表示用のmatplotlibをインポート
import numpy as np

sv = mi.variants()  # 利用可能なMitsubaのバリアントを表示
print(sv)

mi.set_variant("cuda_ad_rgb")  # CUDAを使った自動微分とRGB色空間をサポートするバリアントを設定

scene = mi.load_file("C:/Users/sasaki_takaya/Documents/mitsuba/scenes/cbox.xml", res=512, integrator='prb')
# XMLファイルからシーンをロード。解像度と積分器を設定
#scene = mi.load_file("scene.xml")

# 参照用の画像をレンダリング（samples per pixel = 512）
bitmap_ref = mi.Bitmap('basecolor_ref/C3_Red_ref.jpg').convert(mi.Bitmap.PixelFormat.RGB, mi.Struct.Type.Float32, srgb_gamma=False)
#image_ref = np.array(bitmap_ref)
image_ref = mi.TensorXf(bitmap_ref)

params=  mi.traverse(scene)  # シーンの全パラメータを取得s

#key = "bsdf-diffuse.reflectance.value"  # 最適化するパラメータを指定
key = 'red.reflectance.value'
params.keep(key)
params.update()

param_ref = mi.Color3f(params[key])  # 最適化前のパラメータ値を保持

# パラメータの初期値を設定し、シーンに反映
params[key] = mi.Color3f(0.01,0.0,0.9)
params.update()

opt = mi.ad.Adam(lr=0.05)  # Adam最適化アルゴリズムを使用
opt[key] = params[key]  # 最適化するパラメータを最適化器に設定
params.update(opt)  # 最適化器の変更をシーンに反映

# 初期パラメータでのシーンのレンダリング
image_init=  mi.render(scene,spp = 512)

def mse(image):
    """画像と参照画像との間の平均二乗誤差を計算する関数"""
    print(dr.mean(dr.sqr(image - image_ref)))
    return dr.mean(dr.sqr(image - image_ref))

iteration_count = 50  # 最適化の繰り返し回数を設定

errors = []
for it in range(iteration_count):  # 最適化ループ開始

    image = mi.render(scene, params, spp=4)  # 現在のパラメータでシーンをレンダリング

    loss = mse(image)  # 損失関数（MSE）の計算
    #print(type(loss))
    dr.backward(loss)  # 自動微分を用いた勾配の計算

    opt.step()  # 勾配降下法によるパラメータの更新

    opt[key] = dr.clamp(opt[key], 0.0, 1.0)  # パラメータの値を合法的な範囲に制限

    params.update(opt)  # 最適化されたパラメータをシーンに反映

    err_ref = dr.sum(dr.sqr(param_ref - params[key]))  # 真のパラメータ値との誤差を計算

    #print(f"Iteration {it:02d}: parameter error = {err_ref[0]:6f}", end='\r')  # 進行状況を表示

    errors.append(err_ref)  # 誤差を記録

print('\nOptimization complete.')  # 最適化の完了を表示

# 最適化後のシーンをレンダリングし、ビットマップに変換
image_final = mi.render(scene, spp=512)
mi.util.convert_to_bitmap(image_final)

# matplotlibの設定と画像表示
plt.axis("off")  # 軸を非表示
plt.imshow(image_final ** (1.0 / 2.2))  # 画像を表示（sRGBトーンマッピングを近似）
plt.show()  # 画像を表示

#mi.util.write_bitmap("Fitting_Results/C4_Yellow.png", image)
