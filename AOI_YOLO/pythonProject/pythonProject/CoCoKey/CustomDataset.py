import os
import torch
from torchvision.datasets import VisionDataset
from torchvision.io import read_image
from xml.etree import ElementTree as ET

class CustomDataset(VisionDataset):
    def __init__(self, root, transform=None, target_transform=None):
        super().__init__(root, transform=transform, target_transform=target_transform)
        self.image_files = [os.path.join(root, file) for file in os.listdir(root) if file.endswith('.jpg')]

    def __len__(self):
        return len(self.image_files)

    def __getitem__(self, idx):
        image_path = self.image_files[idx]
        image = read_image(image_path)
        annotation_path = image_path.replace('.jpg', '.xml')
        target = self.parse_annotation(annotation_path)
        return image, target

    def parse_annotation(self, annotation_path):
        tree = ET.parse(annotation_path)
        root = tree.getroot()

        boxes = []
        labels = []

        # 創建類別名稱到索引的映射字典
        label_map = {'Solar_energy': 0, 'Background': 1}  # 這裡需要根據你的類別名稱進行修改

        for obj in root.findall('object'):
            box = obj.find('bndbox')
            xmin = int(box.find('xmin').text)
            ymin = int(box.find('ymin').text)
            xmax = int(box.find('xmax').text)
            ymax = int(box.find('ymax').text)
            boxes.append([xmin, ymin, xmax, ymax])

            # 使用字典映射來獲取類別索引
            label = obj.find('name').text
            labels.append(label_map[label])

        target = {}
        target['boxes'] = torch.tensor(boxes, dtype=torch.float32)
        target['labels'] = torch.tensor(labels, dtype=torch.int64)
        return target

