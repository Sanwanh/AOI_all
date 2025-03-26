import json
import xml.etree.ElementTree as ET


def coco_to_xml(coco_data, xml_filename):
    root = ET.Element("annotations")

    for image_info in coco_data['images']:
        image_id = image_info['id']
        image_filename = image_info['file_name']
        image_width = image_info['width']
        image_height = image_info['height']

        image_element = ET.SubElement(root, "image",
                                      {'id': str(image_id), 'filename': image_filename, 'width': str(image_width),
                                       'height': str(image_height)})

        for annotation_info in coco_data['annotations']:
            if annotation_info['image_id'] == image_id:
                category_id = annotation_info['category_id']
                bbox = annotation_info['bbox']

                annotation_element = ET.SubElement(image_element, "object")
                ET.SubElement(annotation_element, "name").text = str(category_id)
                ET.SubElement(annotation_element, "bndbox").text = ','.join([str(int(i)) for i in bbox])

    tree = ET.ElementTree(root)
    tree.write(xml_filename)


# 讀取COCO JSON檔案
with open('/CoCoKey/annotations/person_keypoints_default.json', 'r') as f:
    coco_data = json.load(f)

# 轉換為XML格式
coco_to_xml(coco_data, 'coco_data.xml')
