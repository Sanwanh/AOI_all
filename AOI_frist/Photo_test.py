import torch
from torchvision import transforms
from PIL import Image
import matplotlib.pyplot as plt

from dataset import Crop, AddNoise, RollingShutter
from model import WaferModel
from pl_module import PLWaferModule

# 初始化模型
model = WaferModel()

# 載入模型權重
model_checkpoint_path = "C:\\Users\\SAN\\Documents\\pyCharm\\AOI_frist\\saves\\epoch=1-val_acc=1.000000.ckpt"

# 忽略不匹配的參數
checkpoint = torch.load(model_checkpoint_path, map_location=torch.device('cpu'))

# 手動加載匹配的參數
model_dict = model.state_dict()
pretrained_dict = {k: v for k, v in checkpoint['state_dict'].items() if k in model_dict and model_dict[k].shape == v.shape}
model_dict.update(pretrained_dict)
model.load_state_dict(model_dict)
model.eval()

# 準備圖像並進行預測
# image_path = r'C:\Users\SAN\Documents\pyCharm\AOI_frist\data\Bad\extracted_320.jpg'
#image_path = r'C:\Users\SAN\Documents\pyCharm\AOI_frist\data\CutTest\bad\extracted_3.jpg'
image_path = r'C:\Users\SAN\Documents\pyCharm\AOI_frist\data\CutTest\good\extracted_8.jpg'
image = Image.open(image_path)

# 將圖像轉換為 Tensor 並進行預處理
preprocess = transforms.Compose([
    transforms.ToTensor(),
    transforms.Resize((300, 400), antialias=True),
    transforms.RandomRotation(30),
    RollingShutter(shutter_speed=0.1, direction="random"),
    Crop(percent=0.075),
    transforms.RandomHorizontalFlip(),
    transforms.RandomVerticalFlip(),
    AddNoise(amplitude=0.05)
])

# 使用預處理步驟處理圖像
input_image = preprocess(image).unsqueeze(0)  # 添加批次維度

# 使用模型進行預測
output = model(input_image)

# 打印模型輸出
print(output)

# 得到預測結果的索引
_, predicted = torch.max(output, 1)
prediction = predicted.item()  # 獲取預測的類別索引

plt.imshow(image)

# 定義二元類別標籤
binary_labels = ["Good", "Bad"]

# 將多類別預測映射到二元類別
if prediction == 0:
    binary_prediction = 0  # "Good"
else:
    binary_prediction = 1  # "Bad"

plt.title(f'Predicted class: {binary_labels[binary_prediction]}')  # 將預測類別添加到標題中

# 獲取預測的概率
softmax_probs = torch.nn.functional.softmax(output, dim=1)
predicted_prob = softmax_probs[0, prediction].item()

# 將準確度添加到圖像上
#plt.text(0.5, -0.1, f'Probability: {predicted_prob:.2%}', horizontalalignment='center', verticalalignment='center',
         #transform=plt.gca().transAxes, fontsize=10, color='red')

plt.axis('off')
plt.show()

# 打印預測的類別和準確度
print(f"Predicted class: {binary_labels[binary_prediction]}")
print(f"Probability: {predicted_prob:.2%}")
