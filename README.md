# 概要
このリポジトリは「COATING SEEKER」というアプリケーション開発の一部です。

「COATING SEEKER」は実際に販売されている塗料のリアルな色と質感を手軽に確認できるアプリです。

このリポジトリには塗料の実サンプルの反射特性(BRDF)の計測データから、塗料をコンピュータ上で表現するためのマテリアル(Principled BRDF)を推定するソースコードをアップロードしています。

# 実装工程

## 実サンプルの反射特性(BRDF)の測定
収集した塗料のサンプルに対して、BRDF測定装置(Mini-Diff V2)を用いてBRDFを計測します。収集したサンプルはクレオスのMR.HOBBYシリーズ（44種）です。

![画像1](https://github.com/Bambootree0818/BRDF_Fitting/assets/137160764/e2ea739d-be1e-4450-9edd-1916026b3b67)

計測データは以下のように出力されます。入射方向と出射方向、RGB光源それぞれでの反射率の羅列です。

![brdf出力](https://github.com/Bambootree0818/BRDF_Fitting/assets/137160764/4f8b5ed9-ac3a-4327-9346-e8e2b10c1ad8)

## mitsuba3によるマテリアル(Principled BRDF)の推定
計測したBRDFデータからマテリアルのパラメータを推定するにはmitsuba3という微分可能レンダラーを使用します。

アルゴリズムとしては、以下の画像のように実サンプルの計測BRDFデータと、適当に用意したPrincipled BRDFパラメータから計算したBRDFの差分をとり、その誤差が小さくなるようにPrincipled BRDFパラメータを調整します。このループを誤差の値が収束するまで回します。

![最適化アルゴリズム](https://github.com/Bambootree0818/BRDF_Fitting/assets/137160764/c56e56de-0839-4796-a8f6-fba93ccea252)


以下のgifは赤色の塗料の計測データを使用してループを回している様子です。だんだんと色と質感が変化するのが分かるかと思います。

（gifのため画質が良くないですが実際はもっと階調が豊かです）

![animated_C3_Red_complete](https://github.com/Bambootree0818/BRDF_Fitting/assets/137160764/de6df7b4-674d-4a28-9dde-517025c6f3f2)

## 色補正
先ほどのgifでは赤色の塗料の計測データを使用していると述べましたが、色は赤色になっていません。これは今回使用したBRDF測定装置は質感は概ね再現できましたが色の認識精度が低いためです。

よって分光色差計(NF555)を使用してPricipled BRDFパラメータの色を補正しています

![色差計](https://github.com/Bambootree0818/BRDF_Fitting/assets/137160764/19c5d481-8693-4e82-8770-2df66e6361fe)

## 推定結果
以下は実サンプルと色の補正を行ったマテリアルの比較です。
色と質感が概ね再現できています。

![比較](https://github.com/Bambootree0818/BRDF_Fitting/assets/137160764/b893728e-5e81-45bc-a490-6668133d0106)

推定したPrincipled BRDFパラメータはjsonに保存し、後段のUnreal Engine5で使用しています。

# COATING SEEKER
推定したマテリアルをレンダリングし、手軽に確認できるアプリ(COATING SEEKER)の作成にはUnreal Engine 5を使用しました。jsonに保存したPrincipled BRDFパラメータをUnreal Engine 5のマテリアルシステムに流し込み、確認用の3Dモデルに適用させています。

ユーザーはリストから任意の塗料を選択することで手軽にその色と質感を確認できます。
