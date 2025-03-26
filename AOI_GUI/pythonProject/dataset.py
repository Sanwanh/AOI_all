import os
import torch
from torch.utils.data import dataset
from torchvision import transforms
from PIL import Image
from matplotlib import pyplot as plt


class RollingShutter:
    def __init__(self, shutter_speed=0.1, direction="horizontal"):
        if direction not in ["horizontal", "vertical", "random"]:
            raise ValueError("direction must be horizontal or vertical")

        self.shutter_speed = torch.rand(1).item() * shutter_speed
        # self.shutter_speed = shutter_speed
        if direction == "random":
            self.direction = "horizontal" if torch.rand(1).item() > 0.5 else "vertical"
        else:
            self.direction = direction

    def __call__(self, image_tensor):
        channels, height, width = image_tensor.shape

        if self.direction == "horizontal":
            offsets = torch.arange(width) * self.shutter_speed
            for i in range(width):
                offset = int(offsets[i])
                image_tensor[:, :, i] = torch.roll(image_tensor[:, :, i], shifts=offset, dims=1)
        elif self.direction == "vertical":
            offsets = torch.arange(height) * self.shutter_speed
            for i in range(height):
                offset = int(offsets[i])
                image_tensor[:, i, :] = torch.roll(image_tensor[:, i, :], shifts=offset, dims=1)

        return image_tensor


class AddNoise:
    def __init__(self, amplitude=0.1):
        self.amplitude = amplitude

    def __call__(self, image_tensor):
        noise = torch.randn_like(image_tensor) * self.amplitude
        return image_tensor + noise


class Crop:
    def __init__(self, percent=0.1):
        self.percent = percent

    def __call__(self, image_tensor):
        channels, height, width = image_tensor.shape
        h = int(height * self.percent)
        w = int(width * self.percent)
        return image_tensor[:, h:height-h, w:width-w]


class WaferDataset(dataset.Dataset):
    def __init__(self, data_path):
        self.data_path = data_path
        self.transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Resize((300, 400),antialias=True),
            transforms.RandomRotation(30),
            RollingShutter(shutter_speed=0.1, direction="random"),
            Crop(percent=0.075),
            transforms.RandomHorizontalFlip(),
            transforms.RandomVerticalFlip(),
            AddNoise(amplitude=0.05)
        ])
        self.category = os.listdir(data_path)
        self.data = []
        for i, data in enumerate(self.category):
            self.data.extend([(os.path.join(self.data_path, data, j), i) for j in os.listdir(os.path.join(data_path, data))])

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        img_path, label = self.data[idx]
        img = Image.open(img_path)
        img = self.transform(img)

        one_hot_label = [0] * len(self.category) #[0,0,1] [0,1,0] [1,0,0]
        one_hot_label[label] = 1
        return img, torch.tensor(one_hot_label, dtype=torch.float32)


if __name__ == "__main__":
    data_set = WaferDataset("data")
    xdd = data_set[1]

    plt.imshow(xdd[0].permute(1, 2, 0))
    plt.show()


