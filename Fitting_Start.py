import subprocess

fitting_script = 'All_BRDF_Fitting_OptColor.py'

def load_data(file_path):
    keys = []  # キーを格納するリスト
    data = {}  # キーとRGB値のマッピングを格納する辞書

    # テキストファイルを開いて読み込む
    with open(file_path, 'r') as file:
        for line in file:
            # 各行を":"で分割してキーとRGB値を取得
            key, value = line.strip().split(':')
            # キーをリストに追加
            keys.append(key)
            # RGB値をカンマで分割してリストとして辞書に格納
            data[key] = list(map(int, value.split(',')))

    return keys, data

def get_rgb_value(data, name):
    # 指定された名前に対応するRGB値を辞書から取得
    return data.get(name)

# ファイルパスと名前を指定
file_path = 'sample_rgb_data.txt'  # テキストファイルのパスを指定

# データを読み込み、キーとRGB値のマッピングを取得
keys, data = load_data(file_path)

# キーを表示
print("利用可能なキー:", keys)

#name = input("名前を入力してください (例: C1_White): ")


def inverse_gamma_correction(value):
    """Apply inverse gamma correction to a normalized value (0-1 range)."""
    if value <= 0.04045:
        return value / 12.92
    else:
        return ((value + 0.055) / 1.055) ** 2.4

# Normalize and apply inverse gamma correction


# 各ファイル名についてスクリプト2を実行
for file_name in keys:

    # RGB値を取得
    rgb_value = get_rgb_value(data, file_name)

    if rgb_value:   
        print(f"{file_name} のRGB値: {rgb_value}")
    else:
        print(f"{file_name} に対応するRGB値が見つかりませんでした。")
    
    # Normalize and apply inverse gamma correction
    linear_rgb = [inverse_gamma_correction(c / 255.0) for c in rgb_value]
    print(linear_rgb)

    #文字列に変換
    linear_rgb_str = ' '.join(map(str, linear_rgb))

    # subprocess.runを使用してscript2を実行
    # スクリプト2への入力としてファイル名と追加の引数をコマンドライン引数として渡す
    subprocess.run(['python', fitting_script, file_name, linear_rgb_str])