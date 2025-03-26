import json
import os


def coco_to_yolo(coco_json_path, output_dir):
    # 加载 COCO JSON 文件
    with open(coco_json_path, 'r', encoding='utf-8') as f:
        coco_data = json.load(f)

    # 创建一个字典来存储图像的宽高信息
    images = {image['id']: image for image in coco_data['images']}

    # 如果输出目录不存在，则创建它
    os.makedirs(output_dir, exist_ok=True)

    # 初始化文件计数器
    file_counter = 1

    # 处理标注信息
    for annotation in coco_data['annotations']:
        image_id = annotation['image_id']
        image_info = images[image_id]
        img_width = image_info['width']
        img_height = image_info['height']

        # COCO 边界框格式：[左上角 x, 左上角 y, 宽度, 高度]
        x, y, width, height = annotation['bbox']

        # YOLO 边界框格式：[x_center, y_center, width, height]
        x_center = (x + width / 2) / img_width
        y_center = (y + height / 2) / img_height
        width /= img_width
        height /= img_height

        # YOLO 类别（因为 COCO 类别从 1 开始，YOLO 类别从 0 开始，所以减 1）
        category_id = annotation['category_id'] - 1

        # 创建 YOLO 标注字符串
        yolo_annotation = f"{category_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n"

        # 确定输出文件名
        output_file = os.path.join(output_dir, f"annotation_{file_counter}.txt")

        # 写入 YOLO 标注到文件中
        with open(output_file, 'a', encoding='utf-8') as f:
            f.write(yolo_annotation)

        # 增加文件计数器
        file_counter += 1


# COCO JSON 文件路径
coco_json_path = 'CoCoKey/annotations/person_keypoints_default.json'

# YOLO 格式文本文件的输出目录
output_dir = 'YOLOv5Train/labels'

# 转换 COCO 到 YOLO
coco_to_yolo(coco_json_path, output_dir)
