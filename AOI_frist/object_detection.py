import os
import json
from PIL import Image, ImageDraw
import matplotlib.pyplot as plt

# 指定 JSON 文件和圖片文件夾的路徑
json_path = r'C:\Users\SAN\Documents\pyCharm\AOI_frist\data\annotations\person_keypoints_default.json'
image_folder = r'C:\Users\SAN\Documents\pyCharm\AOI_frist\data\images'

# 載入 JSON 數據
with open(json_path, 'r') as f:
    data = json.load(f)

# 建立圖片 ID 到文件名的映射
id_to_filename = {img['id']: img['file_name'] for img in data['images']}
id_to_annotations = {ann['image_id']: ann for ann in data['annotations']}
skeleton = data['categories'][0]['skeleton']  # 假設所有圖片都適用相同的關鍵點結構

# 設定輸出圖片的數量
max_images = 10
image_count = 0

# 根據圖片 ID 排序並顯示每一張圖片及其關鍵點
for image_id in sorted(id_to_filename.keys()):
    if image_count >= max_images:
        break
    image_name = id_to_filename[image_id]
    image_path = os.path.join(image_folder, image_name)
    image = Image.open(image_path)
    annotation = id_to_annotations[image_id]
    keypoints = annotation['keypoints']

    # 繪製關鍵點和連線
    draw = ImageDraw.Draw(image)
    x_visible = []
    y_visible = []
    for link in skeleton:
        start_index = (link[0] - 1) * 3  # -1 因為 skeleton 通常是從 1 開始編號的
        end_index = (link[1] - 1) * 3
        if keypoints[start_index+2] != 0 and keypoints[end_index+2] != 0:  # Beide Punkte müssen sichtbar sein
            start = (keypoints[start_index], keypoints[start_index+1])
            end = (keypoints[end_index], keypoints[end_index+1])
            draw.line([start, end], fill='red', width=10)
            x_visible.extend([start[0], end[0]])
            y_visible.extend([start[1], end[1]])

    # 如果存在可見關鍵點，裁切圖片
    if x_visible:
        padding = 50  # 添加一些邊界
        x_min = max(min(x_visible) - padding, 0)
        y_min = max(min(y_visible) - padding, 0)
        x_max = min(max(x_visible) + padding, image.width)
        y_max = min(max(y_visible) + padding, image.height)
        cropped_image = image.crop((x_min, y_min, x_max, y_max))
        plt.imshow(cropped_image)
    else:
        plt.imshow(image)

    plt.title(image_name)
    plt.show()
    image_count += 1
