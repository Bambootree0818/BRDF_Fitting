def get_rgb_value(file_path, name):
    with open(file_path, 'r') as file:
        for line in file:
            key, value = line.strip().split(':')
            if key == name:
                # RGB値をカンマで分割してリストとして返す
                return list(map(int, value.split(',')))
    return None

# 以下の部分は変更なし
file_path = 'sample_rgb_data.txt'
name = input("名前を入力してください (例: C1): ")

rgb_value = get_rgb_value(file_path, name)

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


# Normalize and apply inverse gamma correction
linear_rgb = [inverse_gamma_correction(c / 255.0) for c in rgb_value]

print(linear_rgb)
