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