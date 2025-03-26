import os
import shutil


def rename_images(input_dir, output_dir):
    # 获取输入目录中的所有图像文件
    image_files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]

    # 按文件名排序
    image_files.sort()

    # 如果输出目录不存在，则创建它
    os.makedirs(output_dir, exist_ok=True)

    # 初始化文件计数器
    file_counter = 1

    # 遍历图像文件并重新命名
    for image_file in image_files:
        # 构建新的文件名
        new_file_name = f"annotation_{file_counter}.jpg"

        # 构建源文件路径和目标文件路径
        src_file = os.path.join(input_dir, image_file)
        dest_file = os.path.join(output_dir, new_file_name)

        # 复制并重命名文件
        shutil.copy(src_file, dest_file)

        # 增加文件计数器
        file_counter += 1


# 输入目录路径（包含图像文件的文件夹）
input_dir = 'CoCoKey/images'

# 输出目录路径（重命名后的图像文件将被保存到这里）
output_dir = 'YOLOv5Train/images'

# 重新命名图像文件并输出到新的目录
rename_images(input_dir, output_dir)
