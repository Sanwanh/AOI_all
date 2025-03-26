import os

from torch import nn
from torch.nn import functional as F


class WaferModel(nn.Module):
    def __init__(self, data_path= r'pythonProject\data' ):
        super().__init__()
        self.seq_1 = nn.Sequential(
            nn.Conv2d(3, 16, kernel_size=3),
            nn.BatchNorm2d(16),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(16, 32, kernel_size=3),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, kernel_size=3),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(64, 64, kernel_size=3),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(64, 64, kernel_size=3),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Dropout(0.5)  # 添加 Dropout 層
        )
        self.seq_2 = nn.Sequential(
            nn.Linear(115072, 256), #1536
            nn.ReLU(),
            nn.Linear(256, len(os.listdir(data_path))),
            nn.Softmax(dim=1)
        )


    def forward(self, x):
        x = self.seq_1(x)
        x = x.view(x.size(0), -1)
        x = self.seq_2(x)
        return x
