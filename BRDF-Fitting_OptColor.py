# BRDF マテリアル推定　1月10日　

import mitsuba as mi
import drjit as dr
import numpy as np
import matplotlib.pyplot as plt
import colour as colour
from colour.models import RGB_COLOURSPACE_BT2020

#利用可能なバリアントを表示
variants = mi.variants()
print(variants)

#cudaバリアントをセット
mi.set_variant('cuda_ad_rgb')
print(mi.variant())

# ファイルからデータを読み込み
def read_sample(file_path):
    with open(file_path, 'r') as file:
        data = file.readlines()
    data_list = [line.strip().split(',') for line in data if line.strip()]
    return data_list

file_path = 'TestData.txt' #データパスの指定
sample_data = read_sample(file_path)
#print(data[0][4])

# 最適化対象のBSDFを定義（Principled BRDF）
bsdf = mi.load_dict({
    'type': 'principled',
    'base_color': {
            'type': 'rgb',
            'value': [1.0,1.0,1.0]
    },
    'metallic': 1.0,
    'specular': 1.0,
    'roughness': 1.0,
    'spec_tint': 0.0,
    'anisotropic': 0.0,
    'sheen': 0.0,
    'sheen_tint': 0.0,
    'clearcoat': 1.0,
    'clearcoat_gloss': 1.0,
    'spec_trans': 0.0
})

keys = [
    'metallic.value',
    'roughness.value',
    #'specular',
    'clearcoat.value',
    'clearcoat_gloss.value',    
]
base_color_flag = True
if base_color_flag:
    keys.append('base_color.value')
    
class Samples:

    def __init__(self,samples_data):
        self.samples = samples_data #サンプルの所持
        self.wi_theta = [] #入射光の極角(θ)
        self.wi_phi = [] #入射光の方位角(φ)
        self.wo_theta = [] #反射光の極角
        self.wo_phi = [] #反射光の方位角
        self.rgb_ref_soa= [] #青緑赤の反射
        self.set_parameter() #パラメータをセット
        self.wi_xyz = self.sph_to_dir(self.wi_theta,self.wi_phi) #入射光を球面座標から三次元ベクトルに変換
        self.wo_xyz = self.sph_to_dir(self.wo_theta,self.wo_phi) #反射光を球面座標から三次元ベクトルに変換
        self.specular_xyz = self.calculate_specular_vec(self.wi_xyz)
        #print(self.wi_xyz)

    #パラメータをセット
    def set_parameter(self):
        for row in self.samples:
            self.wi_theta.append(float(row[0]))
            self.wi_phi.append(float(row[1]))
            self.wo_theta.append(float(row[2]))
            self.wo_phi.append(float(row[3]))
            self.rgb_ref_soa.append(float(row[6]))
            self.rgb_ref_soa.append(float(row[5]))
            self.rgb_ref_soa.append(float(row[4]))
        
        self.rgb_ref_soa = dr.unravel(dr.cuda.ad.Array3f, dr.cuda.ad.Float(self.rgb_ref_soa))
        #self.bgr_ref_soa = np.array(self.bgr_ref_soa)

    #球面座標から三次元ベクトルに変換
    def sph_to_dir(self,theta_list,phi_list):
        t = dr.cuda.ad.Float(theta_list)
        p = dr.cuda.ad.Float(phi_list)
        st, ct = dr.sincos(t)
        sp, cp = dr.sincos(p)
            #print(mi.Vector3f(cp * st, sp * st, ct))
            #w.append(mi.Vector3f(cp * st, sp * st, ct))
            #print(w[0][0])
        return mi.Vector3f(cp * st, sp * st, ct)
    
    def calculate_specular_vec(self,wi_xyz, n = np.array([0,0,1])):
        dir = []
        d = dr.dot(n, wi_xyz) 
        for i in range(len(d)):
            h = 2 * n * d[i]
            h_list = h.tolist()
            for j in range(len(h_list)):
                dir.append(h_list[j])
        xyz = dr.unravel(dr.cuda.ad.Array3f, dr.cuda.ad.Float(dir))
        specular_vec = xyz - wi_xyz; 
        return specular_vec
    
    def loss(self,bsdf):
        values = createBRDFSample(bsdf, self.wi_xyz, self.wo_xyz)
        #print(self.rgb_ref_soa)
        #print(values)
        er = dr.sqr(self.rgb_ref_soa[0] - values[0])
        eg = dr.sqr(self.rgb_ref_soa[1] - values[1])
        eb = dr.sqr(self.rgb_ref_soa[2] - values[2])
        loss = dr.sqrt(er + eg + eb)
        return loss
    
#BRDFのサンプルを作成
def createBRDFSample(brdf,wi,wo):
    si = mi.SurfaceInteraction3f()
    si.wi = wi
    values = brdf.eval(mi.BSDFContext(),si,wo)
    return values

#マテリアルプレビュー
def material_preview(opt_bsdf):
    scene = mi.load_file("scene.xml")
    mtParams = mi.traverse(scene)
    for key in keys:
        if 'metallic' in key:
            mtParams["bsdf-matpreview.metallic.value"] = opt_bsdf[key]
        elif 'roughness' in key:
            mtParams["bsdf-matpreview.roughness.value"] = opt_bsdf[key]
        elif 'clearcoat.value' in key:
            mtParams["bsdf-matpreview.clearcoat.value"] = opt_bsdf[key]
        elif 'clearcoat_gloss.value' in key:
            mtParams["bsdf-matpreview.clearcoat_gloss.value"] = opt_bsdf[key]
        elif 'specular' in key:
            mtParams["bsdf-matpreview.specular"] = opt_bsdf[key]
        elif 'base_color' in key:
            mtParams["bsdf-matpreview.base_color.value"] = opt_bsdf[key]
        
    mtParams.update()
    material_image = mi.render(scene,spp = 516)
    mi.util.convert_to_bitmap(material_image)

    # matplotlibの設定と画像表示
    plt.axis("off")  # 軸を非表示
    plt.imshow(material_image ** (1.0 / 2.2))  # 画像を表示（sRGBトーンマッピングを近似）
    plt.show()  # 画像を表示

losses = []
def optimize(targetBRDF, measures, steps, keys, lr = 0.01):
    
    #オプティマイザーを定義
    opt = mi.ad.Adam(lr = lr)
    
    param_clamp = True
    
    #シーンをトラバースし、最適化パラメータをリストアップ
    params = mi.traverse(targetBRDF)
    #params_init = dict(params)
    print(params)
    for key in keys:
        opt[key] = params[key]
    
    #初期値のセット
    params.update(opt)
    
    #最適化スタート
    for step in range(steps):
        
        #loss関数を計算
        loss = measures.loss(targetBRDF)
        losses.append(loss)
        
        dr.backward(loss)
        
        opt.step()
        if param_clamp:
            for key in keys:
                if 'metallic' in key:
                    opt[key] = dr.clamp(opt[key],0.0,0.1)
                elif 'roughness' in key:
                    opt[key] = dr.clamp(opt[key],0.0,0.1)
                elif 'clearcoat' in key:
                    opt[key] = dr.clamp(opt[key],0.0,0.1)
                elif 'specular' in key:
                    opt[key] = dr.clamp(opt[key],0.0,0.1)
                elif 'base_color' in key:
                    pass
                else:
                    opt[key] = dr.clamp(opt[key],0.0,0.1)

        
        params.update(opt)
        
        print('Iteration:', step)
        for key in keys:
            print(key,  opt[key])
        print("loss:", loss)
        print()

    material_preview(params)
    
    #b = []
    #for i in range(4):
    #    b.append(params['base_color.value'][i]) 
    #b= dr.unravel(mi.cuda_ad_spectral.Spectrum, dr.cuda.ad.Float(b))
    #w = mi.cuda_ad_spectral.Spectrum(465.0, 525.0, 630.0, 700.0)
    #srgb = mi.cuda_ad_spectral.spectrum_to_xyz(values=b,wavelengths=w)
    #print(b)
    
            
s = Samples(sample_data)
a = s.wi_xyz
b = s.specular_xyz
print(a)
print(b)
#optimize(bsdf, s,1000,keys)
base_color_flag = True






