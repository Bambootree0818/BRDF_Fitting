def get_rgb_value(file_path, name):
    # テキストファイルを開いて読み込む
    with open(file_path, 'r') as file:
        for line in file:
            # 各行を":"で分割して名前とRGB値を取得
            key, value = line.strip().split(':')
            print(key)
            # 指定された名前が見つかった場合、RGB値を返す
            if key == name:
                # RGB値をカンマで分割してタプルとして返す
                return tuple(map(int, value.split(',')))
    # 指定された名前が見つからない場合、Noneを返す
    return None

# ファイルパスと名前を指定
file_path = 'sample_rgb_data.txt'  # テキストファイルのパスを指定
name = input("名前を入力してください (例: C1): ")

# RGB値を取得
rgb_value = get_rgb_value(file_path, name)
#print(key)

if rgb_value:
    print(f"{name} のRGB値: {rgb_value}")
else:
    print(f"{name} に対応するRGB値が見つかりませんでした。")


def inverse_gamma_correction(value):
    """Apply inverse gamma correction to a normalized value (0-1 range)."""
    if value <= 0.04045:
        return value / 12.92
    else:
        return ((value + 0.055) / 1.055) ** 2.4

# RGB values in the range 0-255
#rgb = (144,41,6)

# Normalize and apply inverse gamma correction
linear_rgb = [inverse_gamma_correction(c / 255.0) for c in rgb_value]

print(linear_rgb)
