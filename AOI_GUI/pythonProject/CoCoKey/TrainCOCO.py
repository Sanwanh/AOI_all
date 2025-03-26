import torch
from torchvision.models.detection import fasterrcnn_resnet50_fpn
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
from torch.utils.data import DataLoader
import CustomDataset


def main():
    # 設置資料集路徑
    dataset_root = "C:\\Users\\puddi\\Desktop\\PythonCode\\Program\\CoCoKey"

    # 建立自定義資料集實例
    dataset = CustomDataset.CustomDataset(root=dataset_root)

    # 將資料集劃分為訓練集和驗證集（這裡簡化為都是訓練集）
    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_dataset, val_dataset = torch.utils.data.random_split(dataset, [train_size, val_size])

    # 設置資料載入器
    train_loader = DataLoader(train_dataset, batch_size=2, shuffle=True, num_workers=4)
    val_loader = DataLoader(val_dataset, batch_size=2, shuffle=False, num_workers=4)

    # 載入預訓練的 Fast R-CNN 模型
    model = fasterrcnn_resnet50_fpn(pretrained=True)

    # 替換模型的預測器以適應資料集的類別數量
    num_classes = 2  # 你的資料集類別數量
    in_features = model.roi_heads.box_predictor.cls_score.in_features
    model.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes)

    # 將模型設置為訓練模式
    model.train()

    # 使用 GPU（如果可用）
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model.to(device)

    # 定義優化器和損失函數
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

    # 訓練模型
    num_epochs = 1
    lr_scheduler = 0.01
    for epoch in range(num_epochs):
        for images, targets in train_loader:
            images = [image.to(device) for image in images]
            targets = [{k: v.to(device) for k, v in t.items()} for t in targets]  # 將每個目標轉換為設備上運行的形式

            loss_dict = model(images, targets)

            # 計算總損失
            losses = sum(loss for loss in loss_dict.values())

            # 反向傳播和優化器更新權重
            optimizer.zero_grad()
            losses.backward()
            optimizer.step()

        # 更新學習率
        lr_scheduler.step()

        # 顯示訓練過程中的損失等信息
        print(f"Epoch {epoch + 1}/{num_epochs}, Loss: {losses.item()}")

    # 保存模型
    torch.save(model.state_dict(), "fast_rcnn_model.pth")
if __name__ == '__main__':
    main()