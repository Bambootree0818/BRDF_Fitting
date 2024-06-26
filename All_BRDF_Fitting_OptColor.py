# BRDF マテリアル推定　1月10日　

import mitsuba as mi
import drjit as dr
import numpy as np
import matplotlib.pyplot as plt
import colour as colour
from colour.models import RGB_COLOURSPACE_BT2020
import sys
import json

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
    data_list = [line.strip().split(',') for line in data[14:] if line.strip()]
    return data_list

file_name = sys.argv[1]
file_path = 'measures_BRDF/' + file_name + '.astm'  #データパスの指定
sample_data = read_sample(file_path)

measure_rgb_str = sys.argv[2]
measure_rgb_str_list = measure_rgb_str.split(' ')
measure_rgb = list(map(float, measure_rgb_str_list))

# 最適化対象のBSDFを定義（Principled BRDF）
bsdf = mi.load_dict({
    'type': 'principled',
    'base_color': {
            'type': 'rgb',
            'value': [1.0,1.0,1.0]
    },
    'metallic': 0.5,
    'specular': 0.5,
    'roughness': 0.5,
    'spec_tint': 0.0,
    'anisotropic': 0.0,
    'sheen': 0.0,
    'sheen_tint': 0.0,
    'clearcoat': 1.0,
    'clearcoat_gloss': 1.0,
    'spec_trans': 0.0
})

keys = [
    'base_color.value',
    'metallic.value',
    'roughness.value',
    'specular',
    #'spec_tint.value',
    #'anisotropic.value',
    #'sheen.value',
    'clearcoat.value',
    'clearcoat_gloss.value',  
    #'spec_trans.value'  
]
base_color_flag = False
    
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
        return mi.Vector3f(cp * st, sp * st, ct)
    
    #正反射のベクトルを計算
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
    
    #loss関数
    def loss(self, bsdf, all_lossFlag):
        if all_lossFlag == True:
            #print("all")
            return self.all_loss(bsdf)
        else:
            #print("light")
            return self.lightLoss(bsdf)
    
    #rgbloss関数
    def all_loss(self,bsdf):
        values = createBRDFSample(bsdf, self.wi_xyz, self.wo_xyz)
        #print(self.rgb_ref_soa)
        #print(values)
        er = dr.sqr(self.rgb_ref_soa[0] - values[0])
        eg = dr.sqr(self.rgb_ref_soa[1] - values[1])
        eb = dr.sqr(self.rgb_ref_soa[2] - values[2])
        cosWoSpecular = dr.dot(self.wo_xyz, self.specular_xyz)
        loss = dr.sqrt(er + eg + eb) * cosWoSpecular
        return dr.mean(dr.mean(loss))
    
    #loss関数（輝度のみ）
    def lightLoss(self, bsdf):
        values = createBRDFSample(bsdf,self.wi_xyz, self.wo_xyz)
        illuminant_XYZ = np.array([0.31270, 0.32900])
        xyz = colour.RGB_to_XYZ(values,RGB_COLOURSPACE_BT2020,illuminant_XYZ)
        xyz_soa = colour.RGB_to_XYZ(self.rgb_ref_soa,RGB_COLOURSPACE_BT2020,illuminant_XYZ)
        loss = dr.mean(dr.sqr(xyz_soa[1] - xyz[1]))
        return loss
    
#BRDFのサンプルを作成
def createBRDFSample(brdf,wi,wo):
    si = mi.SurfaceInteraction3f()
    si.wi = wi #入射方向を設定
    values = brdf.eval(mi.BSDFContext(),si,wo) #入射方向と出射方向からその反射率を求める
    return values

#マテリアルプレビュー
def material_preview(opt_bsdf, scene_params,step):
    for key in keys:
        if 'metallic' in key:
            scene_params["bsdf-matpreview.metallic.value"] = opt_bsdf[key]
        elif 'roughness' in key:
            scene_params["bsdf-matpreview.roughness.value"] = opt_bsdf[key]
        elif 'clearcoat.value' in key:
            scene_params["bsdf-matpreview.clearcoat.value"] = opt_bsdf[key]
        elif 'clearcoat_gloss.value' in key:
            scene_params["bsdf-matpreview.clearcoat_gloss.value"] = opt_bsdf[key]
        elif 'specular' in key:
            scene_params["bsdf-matpreview.specular"] = opt_bsdf[key]
        elif 'base_color' in key:
            scene_params["bsdf-matpreview.base_color.value"] = measure_rgb
        #mtParams["bsdf-matpreview." + key] = opt_bsdf[key]
        
    scene_params.update()
    material_image = mi.render(scene,scene_params,spp = 516)
    #print(scene_params)
    mi.util.convert_to_bitmap(material_image)
    mi.util.write_bitmap("Fitting_Results/" + file_name + ".png", material_image)
    
    # matplotlibの設定と画像表示
    #plt.axis("off")  # 軸を非表示
    #plt.imshow(material_image ** (1.0 / 2.2))  # 画像を表示（sRGBトーンマッピングを近似）
    #plt.show()  # 画像を表示

def optimize(targetBRDF, measures, scene_params, steps, keys, lr = 0.001):
    
    #オプティマイザーを定義
    opt = mi.ad.Adam(lr = lr)
    
    param_clamp = True
    
    #シーンをトラバースし、最適化パラメータをリストアップ
    params = mi.traverse(targetBRDF)
    print(params)
    for key in keys:
        opt[key] = params[key]
    
    #初期値のセット
    params.update(opt)
    
    #最適化スタート
    for step in range(steps):
        
        #loss関数を計算
        loss= 0.
        #print(base_color_flag)
        loss = measures.loss(targetBRDF,base_color_flag)

        
        penalty = 0
        for key in keys:
            penalty += dr.sqr(opt[key] - 0.3824)
        loss = loss + penalty
        #print(loss)
        
        dr.backward(loss)
        
        opt.step()
        if param_clamp:
            for key in keys:
                if 'metallic' in key:
                    opt[key] = dr.clamp(opt[key],0.0,1.0)
                    pass
                elif 'roughness' in key:
                    opt[key] = dr.clamp(opt[key],0.0,1.0)
                    pass
                elif 'clearcoat' in key:
                    opt[key] = dr.clamp(opt[key],0.0,1.0)
                    pass
                elif 'specular' in key:
                    opt[key] = dr.clamp(opt[key],0.0,1.0)
                    #pass
                elif 'base_color' in key:
                    opt[key] = dr.clamp(opt[key],0.0,1.0)
                    #pass
                else:
                    opt[key] = dr.clamp(opt[key],0.0,1.0)

        params.update(opt)
        
        print('Iteration:', step)
        for key in keys:
            print(key,  opt[key])
        print("loss:", loss)
        print()

    material_preview(params, scene_params, step)
        
    #セーブするデータを登録
    data_to_save = {'name': file_name}
    for key in keys:
        data_to_save[key] = params[key]
        if type(data_to_save[key]) == mi.cuda_ad_rgb.Color3f:
            data_to_save[key] = measure_rgb
        if type(data_to_save[key]) == mi.cuda_ad_rgb.Float:
            data_to_save[key] = float(data_to_save[key][0])
    
    #メタリック塗料フラグ
    data_to_save["matallic_type"] = 0
    
    #jsonfileに書き込み
    with open('Result_json/' + file_name, 'w') as json_file:
        json.dump(data_to_save, json_file, indent=4) 

scene = mi.load_file("Scene/Material-Ball.xml")
#シーンをトラバースし、最適化パラメータをリストアップ
scene_params = mi.traverse(scene)

#測定データクラスのインスタンスを作成
s = Samples(sample_data)

base_color_flag = True
optimize(bsdf, s, scene_params,3000,keys)
