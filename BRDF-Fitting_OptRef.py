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
mi.set_variant('cuda_ad_spectral')
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
            'type': 'irregular',
            'wavelengths': '460, 525, 630, 700',
            'values': '0.2, 0.2, 0.2, 0.2'
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

keys = {
    'base_color.values',
    'metallic.value',
    'roughness.value',
    'specular',
    'clearcoat.value',
    'clearcoat_gloss.value'
}
    
class Samples:

    def __init__(self,samples_data):
        self.samples = samples_data #サンプルの所持
        self.wi_theta = [] #入射光の極角(θ)
        self.wi_phi = [] #入射光の方位角(φ)
        self.wo_theta = [] #反射光の極角
        self.wo_phi = [] #反射光の方位角
        self.bgr_ref_soa= [] #青緑赤の反射
        self.set_parameter() #パラメータをセット
        self.wi_xyz = self.sph_to_dir(self.wi_theta,self.wi_phi) #入射光を球面座標から三次元ベクトルに変換
        self.wo_xyz = self.sph_to_dir(self.wo_theta,self.wo_phi) #反射光を球面座標から三次元ベクトルに変換

    #パラメータをセット
    def set_parameter(self):
        for row in self.samples:
            self.wi_theta.append(float(row[0]))
            self.wi_phi.append(float(row[1]))
            self.wo_theta.append(float(row[2]))
            self.wo_phi.append(float(row[3]))
            self.bgr_ref_soa.append(float(row[4]))
            self.bgr_ref_soa.append(float(row[5]))
            self.bgr_ref_soa.append(float(row[6]))
            self.bgr_ref_soa.append(float(row[6]))
        
        self.bgr_ref_soa = dr.unravel(mi.cuda_ad_spectral.Spectrum, dr.cuda.ad.Float(self.bgr_ref_soa))
        #self.bgr_ref_soa = np.array(self.bgr_ref_soa)
        #print(self.bgr_ref_soa)

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
    
    def loss(self,bsdf):
        values = createBRDFSample(bsdf, self.wi_xyz, self.wo_xyz)
        #print(self.bgr_ref_soa)
        #print(values)
        #values = np.array(values) #numpy配列に変換
        #values = np.delete(values,3,axis=1) #4列目を削除(測定波長は3つまでのため)
        #values = dr.cuda.ad.Array3f(values) #型を戻す
        loss = dr.mean(dr.mean(dr.sqr(values - self.bgr_ref_soa)))
        #print(type(loss))
        return loss
    
#BRDFのサンプルを作成
def createBRDFSample(brdf,wi,wo):
    si = mi.SurfaceInteraction3f()
    si.wi = wi
    si.wavelengths = [465.0, 525.0, 630.0, 700.0]
    values = brdf.eval(mi.BSDFContext(),si,wo)
    return values

losses = []
def optimize(targetBRDF, measures, steps, keys, lr = 0.01):
    
    #オプティマイザーを定義
    opt = mi.ad.Adam(lr = lr)
    
    param_clamp = True
    
    #シーンをトラバースし、最適化パラメータをリストアップ
    params = mi.traverse(targetBRDF)
    #params_init = dict(params)
    #print(params_init)
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
                else :
                    #opt[key] = dr.clamp(opt[key],0.0,0.1)
                    pass

        
        params.update(opt)
        
        print('Iteration:', step)
        for key in keys:
            print(key,  opt[key])
        print("loss:", loss)
        print()
        
    
    b = []
    for i in range(4):
        b.append(params['base_color.values'][i]) 
    b= dr.unravel(mi.cuda_ad_spectral.Spectrum, dr.cuda.ad.Float(b))
    w = mi.cuda_ad_spectral.Spectrum(465.0, 525.0, 630.0, 700.0)
    #srgb = mi.cuda_ad_spectral.spectrum_to_xyz(values=b,wavelengths=w)
    print(b)
    
            
s = Samples(sample_data)
#a = s.loss(bsdf)
#print((a))
optimize(bsdf, s,1000,keys)


