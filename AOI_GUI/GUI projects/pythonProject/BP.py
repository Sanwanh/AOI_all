import torch
import cv2
import numpy as np
from model import WaferModel

# 加载模型
BP = WaferModel()

# 加载检查点（你的模型文件）
checkpoint = torch.load(r'pythonProject\epoch=1-val_acc=1.000000.ckpt', map_location='cpu')
BP.load_state_dict(checkpoint['state_dict'], strict=False)

# 设置模型为评估模式
BP.eval()

# 加载输入图片
img = cv2.imread(r'pythonProject\WIN_20240401_18_48_29_Pro.jpg')  # 替换为你的图像文件路径

# BGR 转 RGB，因为 OpenCV 使用 BGR 颜色空间
img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

# 将图像转换为 tensor，并进行归一化
img_tensor = torch.from_numpy(img_rgb).float()
img_tensor = img_tensor.permute(2, 0, 1)  # 将维度从 HWC 转为 CHW
img_tensor /= 255.0  # 归一化到 [0, 1] 范围
img_tensor = img_tensor.unsqueeze(0)  # 增加批次维度

# 推理
with torch.no_grad():
    predictions = BP(img_tensor)

# 获取分类标签和对应的信心度
confidences, predicted_labels = torch.max(predictions, 1)

# 打印预测的类别和对应的信心度
print(f"Predicted Label: {predicted_labels.item()}")
print(f"Confidence: {confidences.item()}")

# 显示处理后的图像
cv2.imshow('Result', img)
cv2.waitKey(0)
cv2.destroyAllWindows()

# 保存输出图像
cv2.imwrite('output_image.jpg', img)
