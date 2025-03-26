import cv2
from ultralytics import YOLO
import torch
import os

# 加載YOLO模型
model = torch.hub.load(r"C:\Users\puddi\Desktop\PythonCode\YOLO\pythonProject", 'custom', path="runs/train/exp3/weights/best.pt", source='local')

# 設定圖片來源資料夾和保存資料夾
image_folder = "Test/bad"
output_folder = "CutTest/bad"
os.makedirs(output_folder, exist_ok=True)

# 讀取資料夾中所有的圖片
image_files = [f for f in os.listdir(image_folder) if os.path.isfile(os.path.join(image_folder, f))]

count = 0

for image_file in image_files:
    image_path = os.path.join(image_folder, image_file)
    frame = cv2.imread(image_path)

    if frame is None:
        continue

    # 進行物體辨識
    results = model(frame)

    # 轉換結果為可迭代格式
    detections = results.pandas().xyxy[0]

    # 遍歷偵測到的物體
    for index, row in detections.iterrows():
        # 提取邊界框座標和尺寸
        x1, y1, x2, y2 = int(row['xmin']), int(row['ymin']), int(row['xmax']), int(row['ymax'])
        w = x2 - x1
        h = y2 - y1

        # 擷取物體的部分圖像
        modelImg = frame[y1:y2, x1:x2]

        # 將BGR轉為RGB
        #modelImg_rgb = cv2.cvtColor(modelImg, cv2.COLOR_BGR2BGR)

        # 保存擷取的圖片
        output_path = os.path.join(output_folder, f"extracted_{count}.jpg")
        cv2.imwrite(output_path, modelImg)
        count += 1

    print(f"Processed {image_file}, detected {len(detections)} objects.")

print("Processing complete.")
