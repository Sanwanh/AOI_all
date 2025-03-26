import torch
import torchvision.models.detection.faster_rcnn
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
from torchvision.datasets import CocoDetection
from torchvision.transforms import ToTensor
from torch.utils.data import DataLoader
from torchvision.models.detection.faster_rcnn import FasterRCNN_ResNet50_FPN_Weights
from tqdm import tqdm  # 导入tqdm来显示进度条

if __name__ == "__main__":
    train_dataset = CocoDetection("WaferBad-1/train",
                                  "C:\\Users\\SAN\\Documents\\pyCharm\\AOI_frist\\WaferBad-1\\train\\_annotations.coco.json",
                                  transform=ToTensor())
    train_dataloader = DataLoader(train_dataset, batch_size=1, shuffle=True, num_workers=4)

    valid_dataset = CocoDetection("WaferBad-1/valid",
                                  "C:\\Users\\SAN\\Documents\\pyCharm\\AOI_frist\\WaferBad-1\\valid\\_annotations.coco.json",
                                  transform=ToTensor())
    valid_dataloader = DataLoader(valid_dataset, batch_size=1, shuffle=False, num_workers=4)

    device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')

    model = torchvision.models.detection.fasterrcnn_resnet50_fpn(weights=FasterRCNN_ResNet50_FPN_Weights.DEFAULT)

    num_classes = 2

    in_features = model.roi_heads.box_predictor.cls_score.in_features
    model.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes)

    params = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.SGD(params, lr=0.005, momentum=0.9, weight_decay=0.0005)
    lr_scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=3, gamma=0.1)

    num_epochs = 20
    for epoch in range(num_epochs):
        model.train()
        total_loss = 0  # 初始化总损失
        with tqdm(total=len(train_dataloader)) as pbar:  # 初始化进度条
            for images, targets in train_dataloader:
                images = list(image for image in images)
                new_targets = []
                for target in targets:
                    x_min, y_min, width, height = target["bbox"]
                    x_max = width + x_min
                    y_max = height + y_min

                    frcnn_bbox = [float(x_min), float(y_min), float(x_max), float(y_max)]

                    new_target = {
                        "boxes": torch.tensor([frcnn_bbox]),
                        "labels": target["category_id"],
                    }

                    new_targets.append(new_target)

                loss_dicts = model(images, new_targets)

                # 计算总损失并更新进度条
                total_loss += sum(loss.item() for loss in loss_dicts.values())
                pbar.set_description(f'Epoch {epoch + 1}/{num_epochs}, Total Loss: {total_loss:.4f}')
                pbar.update(1)

                optimizer.zero_grad()
                # total_loss.backward()
                optimizer.step()

        # 运行验证
        model.eval()
        with torch.no_grad():
            total_valid_loss = 0
            validation_results = []  # 用于存储验证结果的字典列表
            with tqdm(total=len(valid_dataloader)) as pbar_valid:  # 验证进度条
                for images, targets in valid_dataloader:
                    images = list(image for image in images)
                    new_targets = []
                    for target in targets:
                        x_min, y_min, width, height = target["bbox"]
                        x_max = width + x_min
                        y_max = height + y_min

                        frcnn_bbox = [float(x_min), float(y_min), float(x_max), float(y_max)]

                        new_target = {
                            "boxes": torch.tensor([frcnn_bbox]),
                            "labels": target["category_id"],
                        }

                        new_targets.append(new_target)

                    loss_dicts = model(images, new_targets)

                    # 计算验证集的总损失
                    total_loss = sum(loss_dict["loss_dicts"] for loss_dict in loss_dicts)
                    total_valid_loss += total_loss.item()  # 将张量转换为标量并累加

                    validation_results.append({
                        "epoch": epoch + 1,
                        "validation_loss": total_valid_loss,
                        "loss_dicts": loss_dicts
                    })

                    pbar_valid.set_description(
                        f'Epoch {epoch + 1}/{num_epochs}, Validation Loss: {total_valid_loss:.4f}')
                    pbar_valid.update(1)

        lr_scheduler.step()

    torch.save(model.state_dict(), "faster_rcnn_model.pth")
