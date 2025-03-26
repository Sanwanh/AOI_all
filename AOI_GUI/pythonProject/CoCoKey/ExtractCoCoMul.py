import os
import json
import shutil
import xml.etree.ElementTree as ET


def coco_to_xml(coco_data, images_folder, output_folder):
    for annotation_info in coco_data['annotations']:
        image_id = annotation_info['image_id']
        image_filename = None
        image_width = None
        image_height = None
        keypoints = None
        bbox = None

        # 找到對應的圖片資訊
        for image_info in coco_data['images']:
            if image_info['id'] == image_id:
                image_filename = image_info['file_name']
                image_width = image_info['width']
                image_height = image_info['height']
                break

        # 找到對應的 keypoints 資訊
        for keypoint_info in coco_data['annotations']:
            if keypoint_info['image_id'] == image_id:
                keypoints = keypoint_info['keypoints']
                break

        # 找到對應的 bbox 資訊
        if 'bbox' in annotation_info:
            bbox = annotation_info['bbox']

        if image_filename is not None:
            # 構造新的圖片檔名
            new_image_filename = f"annotation_{image_id}.jpg"

            # 複製圖片並重新命名
            original_image_path = os.path.join(images_folder, image_filename)
            new_image_path = os.path.join(output_folder, new_image_filename)
            shutil.copyfile(original_image_path, new_image_path)

            # 產生XML檔案
            root = ET.Element("annotation")
            ET.SubElement(root, "filename").text = new_image_filename
            size = ET.SubElement(root, "size")
            ET.SubElement(size, "width").text = str(image_width)
            ET.SubElement(size, "height").text = str(image_height)

            object_element = ET.SubElement(root, "object")
            ET.SubElement(object_element, "name").text = "Solar_energy"  # 假設標記的物體都是人
            ET.SubElement(object_element, "keypoints").text = ','.join([str(keypoint) for keypoint in keypoints])
            if bbox:
                bndbox = ET.SubElement(object_element, "bndbox")
                ET.SubElement(bndbox, "xmin").text = str(int(bbox[0]))
                ET.SubElement(bndbox, "ymin").text = str(int(bbox[1]))
                ET.SubElement(bndbox, "xmax").text = str(int(bbox[0] + bbox[2]))
                ET.SubElement(bndbox, "ymax").text = str(int(bbox[1] + bbox[3]))

            tree = ET.ElementTree(root)
            xml_filename = os.path.join(output_folder, f"annotation_{image_id}.xml")
            tree.write(xml_filename)
            print(f"Saved {xml_filename}")


# 讀取COCO JSON檔案
with open('/CoCoKey/annotations/person_keypoints_default.json', 'r') as f:
    coco_data = json.load(f)

# 指定圖片資料夾和輸出資料夾的路徑
images_folder = "C:\\Users\\puddi\\Desktop\\PythonCode\\Program\\CoCoKey\\images"
output_folder = "C:\\Users\\puddi\\Desktop\\PythonCode\\Program\\CoCoKey\\annotations_and_keypoints"

# 如果輸出資料夾不存在，則創建它
os.makedirs(output_folder, exist_ok=True)

# 轉換為XML格式，同時複製並重新命名圖片
coco_to_xml(coco_data, images_folder, output_folder)
