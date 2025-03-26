from PyQt5.QtWidgets import QWidget, QPushButton,QSlider, QToolButton, QLabel, QApplication, QFrame, QLineEdit, QTextEdit, QFileDialog,QVBoxLayout,QHBoxLayout,QDialog,QGraphicsDropShadowEffect
from PyQt5.QtGui import QImage, QPixmap,QIcon,QFont
from PyQt5.QtCore import QThread, pyqtSignal, QTimer, QDateTime, QRect, Qt as QtCore,QSize
# from qt_material import apply_stylesheet
# import qtmodern.styles
# import qtmodern.windows
import cv2
import sys
import threading
import os
#import psutil  # from gpiozero import CPUTemperature
import moonrakerpy as moonpy
import requests,json
import re

import torch
import numpy as np
from model import WaferModel

import platform
import pathlib


Shot_PIC = 0
x,y,x_value,y_value = 0, 0, 0, 0

class MainsailController:
    def __init__(self, mainsail_ip):
        # 使用 mainsail 的 Web/IP 位址實體化 MoonrakerPrinter 物件
        # 將 mainsail 的 IP 透過 moonpy API 來創建 self.printer 變數
        self.printer = moonpy.MoonrakerPrinter(mainsail_ip)

    def send_gcode(self, gcode_command):
        self.printer.send_gcode(gcode_command)  # 向 mainsail 發送 Gcode指令

    def read_gcode_messages(self, count=5):
        # 從 mainsail 的打印機中讀取 Gcode 訊息並將其返回，count => 要讀取的訊息數量
        return self.printer.get_gcode(count)

# 創建照片視窗
class ImageDialog(QDialog):
    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("圖片查看器")
        self.setGeometry(100, 100, 800, 600)
        
        # 儲存目前圖片路徑和所有圖片文件
        self.current_file_path = file_path
        self.dir_path = os.path.dirname(file_path) # 從 file_path 中提取出目錄路徑（即檔案所在的資料夾路徑）
        self.image_files = self.get_image_files(self.dir_path) # 用於獲取指定目錄（self.dir_path）中的所有圖片檔案的路徑。
        self.current_index = self.image_files.index(file_path) if file_path in self.image_files else 0 
        # 如果 file_path 在列表中，則使用 index() 方法獲取其索引，並將其賦值給 self.current_index
        # 如果 file_path 不在列表中（例如，檔案被刪除或移動），則將 self.current_index 設置為 0（即列表中的第一個圖片）
        
        # 創建主要布局
        layout = QVBoxLayout(self)
        
        # 圖片顯示區域
        self.img_frame = QFrame(self)
        self.img_frame.setMinimumHeight(500)
        img_layout = QVBoxLayout(self.img_frame)
        
        # 圖片顯示標籤
        self.label = QLabel(self)
        self.label.setAlignment(QtCore.AlignCenter)
        # 不使用setScaledContents，改为手动控制缩放比例
        # self.label.setScaledContents(True)
        
        img_layout.addWidget(self.label)
        
        # 導航按钮
        button_layout = QVBoxLayout()
        nav_layout = QHBoxLayout()
        
        self.prev_button = QPushButton("上一張", self)
        self.prev_button.setFixedSize(100, 40)
        self.prev_button.clicked.connect(self.load_prev_image)
        self.prev_button.setStyleSheet("""
            QPushButton {
                background-color: #2C2C2C;
                border: none;
                border-radius: 5px;
                color: white;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3C3C3C;
            }
            QPushButton:pressed {
                background-color: #1C1C1C;
            }
        """)
        
        self.next_button = QPushButton("下一張", self)
        self.next_button.setFixedSize(100, 40)
        self.next_button.clicked.connect(self.load_next_image)
        self.next_button.setStyleSheet("""
            QPushButton {
                background-color: #2C2C2C;
                border: none;
                border-radius: 5px;
                color: white;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3C3C3C;
            }
            QPushButton:pressed {
                background-color: #1C1C1C;
            }
        """)
        
        # 文件名稱標籤
        self.filename_label = QLabel(self)
        self.filename_label.setAlignment(QtCore.AlignCenter)
        self.filename_label.setStyleSheet("font-size: 16px; color: #333; font-family:Arial;")
        
        # 計數圖片標籤 (例如: 1/10)
        self.count_label = QLabel(self)
        self.count_label.setAlignment(QtCore.AlignCenter)
        self.count_label.setStyleSheet("font-size: 16px; color: #333; font-family:Arial;")
        
        # 水平至中的按鈕布局
        nav_layout.addStretch() # 在佈局中的控件之間或邊緣創建可伸縮的空白區域
        nav_layout.addWidget(self.prev_button)
        nav_layout.addSpacing(200)  # 按鈕之間的間距
        nav_layout.addWidget(self.next_button)
        nav_layout.addStretch()
        
        # 添加檔案名稱、圖片計數標籤和按鈕到布局
        button_layout.addLayout(nav_layout)
        button_layout.addWidget(self.filename_label)
        button_layout.addWidget(self.count_label)
        
        # 添加所有元素到主布局
        layout.addWidget(self.img_frame)
        layout.addLayout(button_layout)
        
        # 存储原始图像以便后续调整大小
        self.original_pixmap = None
        
        # 在窗口显示后才加载图片，确保大小正确
        QTimer.singleShot(100, lambda: self.load_image(self.current_file_path))
        self.update_ui_state()
    
    def get_image_files(self, directory):
        """获取目录中所有图片文件"""
        # 支持的图片格式
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff']
        image_files = []
        
        # 遍历目录中的所有文件
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path):
                # 检查文件扩展名
                ext = os.path.splitext(filename)[1].lower()
                if ext in image_extensions:
                    image_files.append(file_path)
        
            # 使用自然排序（按文件名中的数字排序）
        def natural_sort_key(s):
            return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', os.path.basename(s))]

        return sorted(image_files, key=natural_sort_key)
        
    def load_image(self, file_path):
        """加载并显示图片"""
        if not os.path.exists(file_path):
            self.label.setText("找不到图片文件")
            return
        
        # 存储原始图像
        self.original_pixmap = QPixmap(file_path)
        if self.original_pixmap.isNull():
            self.label.setText("无法加载图片")
            return
        
        # 调整图片大小以适应标签框架
        self.scale_image()
        
        # 更新当前文件路径和索引
        self.current_file_path = file_path
        if file_path in self.image_files:
            self.current_index = self.image_files.index(file_path)
        
        # 更新文件名标签
        filename = os.path.basename(file_path)
        self.filename_label.setText(filename)
        
        # 更新计数标签
        self.count_label.setText(f"{self.current_index + 1}/{len(self.image_files)}")
    
    def scale_image(self):
        """根据当前显示区域调整图片大小"""
        if self.original_pixmap is None:
            return
            
        # 获取显示区域的尺寸
        frame_width = self.img_frame.width() - 20  # 减去一些边距
        frame_height = self.img_frame.height() - 20
        
        if frame_width <= 0 or frame_height <= 0:
            frame_width = 760  # 默认值，如果框架尚未正确调整大小
            frame_height = 480
        
        # 调整图片大小，保持纵横比
        scaled_pixmap = self.original_pixmap.scaled(
            frame_width, 
            frame_height,
            QtCore.KeepAspectRatio, 
            QtCore.SmoothTransformation
        )
        
        self.label.setPixmap(scaled_pixmap)
    
    def load_next_image(self):
        """加载下一张图片"""
        if not self.image_files:
            return
            
        next_index = (self.current_index + 1) % len(self.image_files)
        self.current_index = next_index
        self.load_image(self.image_files[next_index])
        self.update_ui_state()
    
    def load_prev_image(self):
        """加载上一张图片"""
        if not self.image_files:
            return
            
        prev_index = (self.current_index - 1) % len(self.image_files)
        self.current_index = prev_index
        self.load_image(self.image_files[prev_index])
        self.update_ui_state()
    
    def update_ui_state(self):
        """更新UI状态，如果只有一张图片则禁用按钮"""
        has_multiple_images = len(self.image_files) > 1
        self.prev_button.setEnabled(has_multiple_images)
        self.next_button.setEnabled(has_multiple_images)
    
    def resizeEvent(self, event):
        """窗口大小改变时重新缩放当前图片以适应新大小"""
        super().resizeEvent(event)
        self.scale_image()
    
    def showEvent(self, event):
        """窗口显示时确保图片正确加载"""
        super().showEvent(event)
        # 延迟加载，确保窗口已经完全显示并且尺寸已确定
        QTimer.singleShot(50, self.scale_image)

class CustomSlider(QSlider):
    # 自訂義信號，用於發送實際值
    valueChangedCustom = pyqtSignal(float) # 定義了一個名為 valueChangedCustom 的 PyQt 信號，用來傳遞浮點數值

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.values = [0.1, 1, 10, 25, 50, 100] #  定義滑動條的自訂義值列表，包含 6 個浮點數（例如 0.1、1、10 等）
        self.setMinimum(0) # 對應self.values 的第一個值
        self.setMaximum(len(self.values) - 1) # len長度有6個，self.values 列表從0開始數，100是在第len-1個 
        #self.setSingleStep(1) # 設置較小的步數，相當於按下鍵盤上的上下鍵
        self.setPageStep(1) # 設置較大的步數，相當於按下鍵盤上的PageUp、PageDown
        self.valueChanged.connect(self.emitCustomValue) # 運用 valueChanged.connect(fn) 方法，就能在調整數值時，執行特定的函式

    def emitCustomValue(self, index):
        # index 是滑動條的當前值，對應 self.values 的索引。
        # 根據索引值從 self.values 中取出對應的浮點數，並通過 valueChangedCustom 信號發送。
        self.valueChangedCustom.emit(self.values[index])

class mainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.window_w, self.window_h = 1280, 720 # 1500,900
        self.setWindowTitle('AOI')
        self.resize(self.window_w, self.window_h) # 只關心大小用 resize()，需同時設定位置和大小用 setGeometry()

        self.ui()

        self.mainsail_controller = MainsailController('http://192.168.50.190')
        self.photo_number = 1  # 照片檔名從1開始
        self.ocv = True
        # self.video = threading.Thread(target=self.opencv)
        # self.video.start()

        # Gcode
        self.gcode_command1 = ''
        self.gcode_command2 = ''
        self.gcode_command3 = ''
        self.gcode_command4 = ''

        # 新增一個計時器，每 500 毫秒更新一次座標
        self.position_timer = QTimer(self)
        self.position_timer.timeout.connect(self.updateMotorPosition)
        self.position_timer.start(1000)  # 每500毫秒更新一次

    def getMotorPosition(self):
        try:
            res = requests.get(
                'http://192.168.50.190/printer/objects/query?gcode_move=position',timeout=1) # 添加逾時設定
            if res.status_code == 200:
                js = json.loads(res.content)
                x, y = js['result']['status']['gcode_move']['position'][0:2]
                print(f"目前位置: X={x}, Y={y}")
                return x, y
            else:
                print(f"請求錯誤，狀態碼: {res.status_code}")
                return None, None   
        except requests.exceptions.RequestException as e:
            print(f"網路請求錯誤: {e}")
            return None, None
        except Exception as e:
            print(f"其他錯誤: {e}")
            return None, None

    def updateMotorPosition(self):
        x, y = self.getMotorPosition()
        if x is not None and y is not None:
            self.motorX_label.setText(f'X : {x:.2f} , Y : {y:.2f}')
            return x, y
        else:
        # 當無法獲取座標時顯示錯誤訊息
            self.motorX_label.setText('無法獲取座標')
            return None, None

    #自動化
    def automatic(self):
        gcode = "some_value"
        # 讀取 G-code 文件
        with open('AOI Gcode.txt', 'r') as file:
            gcode_lines = file.readlines()
        # 發送 G-code 指令並根據需要拍照
        for idx, line in enumerate(gcode_lines):            
            gcode = line.strip()
            self.mainsail_controller.send_gcode(gcode)
            x_value, y_value = self.extract_X_Y_values(gcode)
            if x_value is not None:
                x_value = int(float(x_value))  # 先轉換為浮點數再轉換為整數
            if y_value is not None:
                y_value = int(float(y_value))  # 先轉換為浮點數再轉換為整數 
            #print('Sending G-code:', gcode)
            print('x_value:', x_value, 'y_value', y_value)
            #print('x:', x, 'y:', y)
            x, y = self.getMotorPosition()
            x, y = self.updateMotorPosition()
            #只在基數行後拍照
            print('idx=', idx)
            if x_value == x and y_value == y:
            # 拍照
                Shot_PIC += 1
                self.photo = True
                print('shoot')
        self.mainsail_controller.send_gcode('XY_HOME')
    
    #擷取txt中X,Y值
    def extract_X_Y_values(self, gcode):
        x_value = re.search(r'X(-?\d+\.?\d*)', gcode)
        y_value = re.search(r'Y(-?\d+\.?\d*)', gcode)
    
        if x_value:
            x_value = x_value.group(1)
        else:
            x_value = None

        if y_value:
            y_value = y_value.group(1)
        else:
            y_value = None
        
        return x_value,y_value
    
    def ui(self):

        # 背景畫面 bg_Label
        self.bg_label = QLabel(self)
        self.bg_label.resize(1280,720)
        self.bg_label.setStyleSheet("""
            QWidget {
                background-color: white; 
                border-radius: 10px; 
                margin:10px;
            }
            """)
        
        # # creating a QGraphicsDropShadowEffect object 
        # self.shadow = QGraphicsDropShadowEffect(self) 

        # # 陰影偏移    
        # self.shadow.setOffset(0,0)
        
        # # setting blur radius 
        # self.shadow.setBlurRadius(30) 
  
        # # shadow color
        # self.shadow.setColor(QtCore.gray)

        # # adding shadow to the label 
        # self.bg_label.setGraphicsEffect(self.shadow)         

        # 相機畫面 camera_label
        self.camera_label = QLabel('相機畫面',self)
        self.camera_label.setFont(QFont('Microsoft YaHei',18))
        self.camera_label.setGeometry(50,30,200,50)

        # 方向控制 control_label
        self.control_label = QLabel('方向控制',self)
        self.control_label.setFont(QFont('Microsoft YaHei',18))
        self.control_label.setGeometry(800,30,200,50)

        # 步進大小 step0_label
        self.step0_label = QLabel('步進大小',self)
        self.step0_label.setFont(QFont('Microsoft YaHei',16))
        self.step0_label.setGeometry(800,280,200,50)

        # 當前位置 position_label
        self.position_label = QLabel('當前位置',self)
        self.position_label.setFont(QFont('Microsoft YaHei',16))
        self.position_label.setGeometry(800,430,200,50)

        # 馬達X位置 motorX_label
        self.motorX_label = QLabel(self)
        self.motorX_label.setFont(QFont('Arial'))
        self.motorX_label.setGeometry(800,500,200,50)
        self.updateMotorPosition()
        self.motorX_label.setStyleSheet("""
            QLabel {
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px;
                font-size: 14px;
                background-color: white;
            }
        """)

        # G-Code 指令 gcode_label
        self.gcode_label = QLabel("G-Code 指令", self)
        self.gcode_label.setGeometry(800, 580, 250, 50)
        self.gcode_label.setFont(QFont("Microsoft YaHei", 16))

        # 輸入代碼
        # Create QLineEdit
        self.display_box = QLineEdit(self)  # 創建單行顯示框
        self.display_box.setFont(QFont("Arial"))
        self.display_box.setGeometry(800, 630, 280, 50)
        self.display_box.setPlaceholderText("Enter G-Code...")
        self.display_box.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px;
                font-size: 14px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #4a90e2;
            }
        """)
        self.display_box.returnPressed.connect(self.handle_btn9_click)

        # 列表
        #self.display_box7 = 
        
        # 相機影像位置
        self.label = QLabel(self)
        self.label.setGeometry(20, 120, 800, 500)

        # Create slider
        self.slider = CustomSlider(QtCore.Horizontal,self)
        #self.slider.setOrientation(1)
        #self.slider.setTickPosition(QSlider.TicksBelow)
        #self.slider.setTickInterval(1)
        self.slider.setGeometry(800, 320, 400, 50)
        self.slider.setStyleSheet('''
            QSlider {
                border-radius: 10px;
            }
            QSlider::groove:horizontal {
                height: 5px;
                background: #000;
            }
            QSlider::handle:horizontal{
                background: #f00;
                width: 16px;
                height: 16px;
                margin:-6px 0;
                border-radius:8px;
            }
            QSlider::sub-page:horizontal{
                background:#f90;
            }
        ''')

        # Create the step label
        self.step_label = QLabel('步進大小: 0.1 步', self)
        self.step_label.setFont(QFont('Microsoft YaHei',10))
        self.step_label.setGeometry(950,320,120,100)

        #連接自訂訊號到更新標籤的槽函數
        self.slider.valueChangedCustom.connect(self.updateLabel)

        # 上鍵
        btn1 = QPushButton(self)
        # btn1.setArrowType(QtCore.UpArrow)
        btn1.setIcon(QIcon('img\icons8-up-arrow-25.png')) # icons8-up-arrow-25.png
        btn1.setIconSize(btn1.size()*1) 
        btn1.setGeometry(1000, 100, 60, 45)
        btn1.setStyleSheet("""
            QPushButton {
                background-color: #2C2C2C;
                border: none;   
                border-radius: 5px;
                color: white;   
                padding: 5px 10px;
            }
            QPushButton:hover {     
                background-color: #3C3C3C;
            }
            QPushButton:pressed {
                background-color: #1C1C1C;
            }
        """)

        # 下鍵
        btn2 = QPushButton(self)
        # btn2.setArrowType(QtCore.UpArrow)
        btn2.setIcon(QIcon('img\icons8-down-arrow-24.png')) # icons8-up-arrow-24.png
        btn2.setIconSize(btn2.size()*1)
        btn2.setGeometry(1000, 210, 60, 45)
        btn2.setStyleSheet("""
            QPushButton {
                background-color: #2C2C2C;
                border: none;   
                border-radius: 5px;
                color: white;   
                padding: 5px 10px;
            }
            QPushButton:hover {     
                background-color: #3C3C3C;
            }
            QPushButton:pressed {
                background-color: #1C1C1C;
            }
        """)
        
        # 左鍵
        btn3 = QPushButton(self)
        # btn3.setArrowType(QtCore.UpArrow)
        btn3.setIcon(QIcon('img\icons8-left-48.png'))
        btn3.setIconSize(btn3.size()*1)
        btn3.setGeometry(930, 155, 60, 45)
        btn3.setStyleSheet("""
            QPushButton {
                background-color: #2C2C2C;
                border: none;   
                border-radius: 5px;
                color: white;   
                padding: 5px 10px;
            }
            QPushButton:hover {     
                background-color: #3C3C3C;
            }
            QPushButton:pressed {
                background-color: #1C1C1C;
            }
        """)

        # 右鍵
        btn4 = QPushButton(self)
        # btn4.setArrowType(QtCore.UpArrow)
        btn4.setIcon(QIcon('img\icons8-right-arrow-48.png'))
        btn4.setIconSize(btn4.size()*1)
        btn4.setGeometry(1070, 155, 60, 45)
        btn4.setStyleSheet("""
            QPushButton {
                background-color: #2C2C2C;
                border: none;   
                border-radius: 5px;
                color: white;   
                padding: 5px 10px;
            }
            QPushButton:hover {     
                background-color: #3C3C3C;
            }
            QPushButton:pressed {
                background-color: #1C1C1C;
            }
        """)

        # Shoot鍵
        btn5 = QPushButton(self)
        btn5.setFont(QFont('Arial',11))
        btn5.setText(' Shoot')
        btn5.setIcon(QIcon('img\camera_icon.png'))
        btn5.setIconSize(btn5.size()*1)
        btn5.setGeometry(60, 640, 150, 40) # btn5.setGeometry(120, 640, 100, 50)
        btn5.setStyleSheet("""
            QPushButton {
                background-color: #2C2C2C;
                border: none;
                border-radius: 5px;
                color: white;
                padding: 5px 10px;
                font-weight:bold;
            }
            QPushButton:hover {
                background-color: #3C3C3C;
            }
            QPushButton:pressed {
                background-color: #1C1C1C;
            }
        """)
    
        # Home鍵
        btn6 = QPushButton(self)
        btn6.setIcon(QIcon('img\icons8-home-50.png'))
        btn6.setIconSize(btn5.size()*0.5)
        btn6.setGeometry(1000, 155, 60, 45) # btn6.setGeometry(120, 640, 100, 50)
        btn6.setStyleSheet("""
            QPushButton {
                background-color: #2C2C2C;
                border: none;
                border-radius: 5px;
                color: white;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #3C3C3C;
            }
            QPushButton:pressed {
                background-color: #1C1C1C;
            }
        """)
        
        # File鍵       
        btn7 = QPushButton(self)
        btn7.setFont(QFont('Arial', 11))
        btn7.setText('  File')
        btn7.setIcon(QIcon('img\\file_icon.png'))
        btn7.setIconSize(btn7.size()*1) 
        btn7.setGeometry(260, 640, 150, 40)
        btn7.setStyleSheet("""
            QPushButton {
                background-color: #2C2C2C;
                border: none;
                border-radius: 5px;
                color: white;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3C3C3C;
            }
            QPushButton:pressed {
                background-color: #1C1C1C;
            }
        """)

        # 終止鍵
        btn8 = QPushButton(self)
        btn8.setFont(QFont('Arial', 11))
        btn8.setText('  Stop')      
        btn8.setIcon(QIcon('img\square_icon.png'))
        btn8.setIconSize(btn8.size()*1) 
        btn8.setGeometry(460, 640, 150, 40)
        btn8.setStyleSheet("""
            QPushButton {
                background-color: #FF3B30;
                border: none;
                border-radius: 5px;
                color: white;
                padding: 5px 10px;
                font-weight:bold;
            }
            QPushButton:hover {
                background-color: #3C3C3C;
            }
            QPushButton:pressed {
                background-color: #1C1C1C;
            }
        """)

        # Send鍵
        btn9 = QPushButton(self)
        btn9.setFont(QFont('Arial',11))
        btn9.setText('Send')
        btn9.setGeometry(1100, 630, 60, 50)
        btn9.setStyleSheet("""
            QPushButton {
                background-color: #2C2C2C;
                border: none;
                border-radius: 5px;
                color: white;
                padding: 5px 10px;
                font-weight:bold;
            }
            QPushButton:hover {
                background-color: #3C3C3C;
            }
            QPushButton:pressed {
                background-color: #1C1C1C;
            }
        """)
        btn10 = QPushButton(self)
        btn10.setGeometry(1000, 500, 60, 45)

        btn1.clicked.connect(self.handle_btn1_click)
        btn2.clicked.connect(self.handle_btn2_click)
        btn3.clicked.connect(self.handle_btn3_click)
        btn4.clicked.connect(self.handle_btn4_click)
        btn5.clicked.connect(self.handle_btn5_click)
        btn6.clicked.connect(self.handle_btn6_click)
        btn7.clicked.connect(self.handle_btn7_click)
        btn8.clicked.connect(self.handle_btn8_click)
        btn9.clicked.connect(self.handle_btn9_click)
        btn10.clicked.connect(self.handle_btn10_click)
    def updateLabel(self, value):
        self.step_label.setText(f'步進大小: {value} 步')

        # Assign G-code commands based on the current slider value
        if value == 0.1:
            self.gcode_command1 = 'G1 X0.1'
            self.gcode_command2 = 'G1 X-0.1'
            self.gcode_command3 = 'G1 Y0.1'
            self.gcode_command4 = 'G1 Y-0.1'
        elif value == 1:
            self.gcode_command1 = 'G1 X1'
            self.gcode_command2 = 'G1 X-1'
            self.gcode_command3 = 'G1 Y1'
            self.gcode_command4 = 'G1 Y-1'
        elif value == 10:
            self.gcode_command1 = 'G1 X10'
            self.gcode_command2 = 'G1 X-10'
            self.gcode_command3 = 'G1 Y10'
            self.gcode_command4 = 'G1 Y-10'
        elif value == 25:
            self.gcode_command1 = 'G1 X25'
            self.gcode_command2 = 'G1 X-25'
            self.gcode_command3 = 'G1 Y25'
            self.gcode_command4 = 'G1 Y-25'
        elif value == 50:
            self.gcode_command1 = 'G1 X50'
            self.gcode_command2 = 'G1 X-50'
            self.gcode_command3 = 'G1 Y50'
            self.gcode_command4 = 'G1 Y-50'
        elif value == 100:
            self.gcode_command1 = 'G1 X100'
            self.gcode_command2 = 'G1 X-100'
            self.gcode_command3 = 'G1 Y100'
            self.gcode_command4 = 'G1 Y-100'
        # Add additional conditions for other values if needed
        else:
            # Default or extended values
            pass

        # Optionally: print or log the commands for debugging
        print(self.gcode_command1, self.gcode_command2, self.gcode_command3, self.gcode_command4)

    # 存檔時使用順序名稱的函式
    def rename(self):
        name = str(self.photo_number)  # 使用目前的照片編號作為檔名
        self.photo_number += 1  # 照片編號加一，準備下一張照片的檔名
        return name

    photo = False

    def takephoto(self):
        """按下拍照按鈕時，開啟相機、拍照，然後關閉相機"""
        cap = cv2.VideoCapture(0)  # 開啟相機
        if not cap.isOpened():
            print("無法開啟相機")
            return

        ret, frame = cap.read()  # 讀取畫面
        cap.release()  # 立即關閉相機，避免持續運行

        if not ret:
            print("無法獲取影像")
            return

        frame = cv2.flip(frame, 1)  # 鏡像翻轉
        file_path = "FILE"
        name = self.rename()
        save_path = os.path.join(file_path, f'{name}.jpg')
        cv2.imwrite(save_path, frame)  # 儲存圖片
        print(f'已拍照並儲存: {save_path}')

    
    def load_model():
    # 加载 YOLOv5 模型
        yolo_model = torch.hub.load(r"E:\python GUI\pythonProject", 'custom', 
                                    path=r"E:\python GUI\pythonProject\runs\train\exp8\weights\best1.pt", 
                                    source='local')
        # 加载 CNN 模型
        BP = WaferModel()  # 你的 CNN 类
        checkpoint = torch.load(r'pythonProject\epoch=1-val_acc=1.000000.ckpt', map_location='cpu')
        BP.load_state_dict(checkpoint['state_dict'], strict=False)
        BP.eval()
        
        return yolo_model, BP

    # CNN 图像预处理
    def preprocess_image(img):
        transform = transforms.Compose([
            transforms.Resize((64, 64)),
            transforms.ToTensor(),
            transforms.Normalize([0.5], [0.5])  # 标准化
        ])
        return transform(img).unsqueeze(0)

    # YOLOv5 进行目标检测 & CNN 分类
    def detect_and_classify(yolo_model, BP, image_folder, output_folder):
        if Shot_PIC == 20:
            os.makedirs(output_folder, exist_ok=True)
            confidences_list = []

            # 获取文件夹中的图片
            image_files = [f for f in os.listdir(image_folder) if f.endswith('.jpg')]

            count = 0
            
            for image_file in image_files:
                image_path = os.path.join(image_folder, image_file)
                frame = cv2.imread(image_path)

                if frame is None:
                    continue

                # YOLOv5 目标检测
                results = yolo_model(frame)
                detections = results.pandas().xyxy[0]  # YOLO的结果

                # 遍历检测到的物体，裁剪目标区域
                for _, row in detections.iterrows():
                    x1, y1, x2, y2 = int(row['xmin']), int(row['ymin']), int(row['xmax']), int(row['ymax'])
                    cropped_img = frame[y1:y2, x1:x2]

                    # 保存裁剪图像
                    output_path = os.path.join(output_folder, f"cut_{count}.jpg")
                    cv2.imwrite(output_path, cropped_img)
                    count += 1

                    # 只保存 20 张裁切图
                    if count >= 20:
                        return


    # CNN 分类裁剪后的图片
    def classify_with_cnn(BP, cropped_image_folder):
        confidences_list = []
        # 获取切割后的图片
        cut_images = [f for f in os.listdir(cropped_image_folder) if f.endswith('.jpg')]
        for img_file in cut_images:
            img_path = os.path.join(cropped_image_folder, img_file)
            img = Image.open(img_path).convert('RGB')
            img_tensor = preprocess_image(img)
            # CNN 分类
            with torch.no_grad():
                prediction = BP(img_tensor)
                confidence, predicted_label = torch.max(prediction, 1)
                confidences_list.append(confidence.item())
                
        return confidences_list
    


    '''def openFiles(self):
         save_path = 'D:\python GUI\pyqt project\FILE'
         self.filePath, self.filterType = QFileDialog.getOpenFileNames(self, 'Open Files', save_path)  # 選取多個檔案'''

    def handle_btn1_click(self):
        self.mainsail_controller.send_gcode('G91')
        self.mainsail_controller.send_gcode(self.gcode_command3)
        print("Up")
        QTimer.singleShot(200, self.updateMotorPosition)

    def handle_btn2_click(self):
        self.mainsail_controller.send_gcode('G91')
        self.mainsail_controller.send_gcode(self.gcode_command4)
        print("Down")
        QTimer.singleShot(200, self.updateMotorPosition)

    def handle_btn3_click(self):
        self.mainsail_controller.send_gcode('G91')
        self.mainsail_controller.send_gcode(self.gcode_command2)
        # self.serial_port.write(b'a')  # Send 'a' to Arduino
        print("Left")
        QTimer.singleShot(200, self.updateMotorPosition)

    def handle_btn4_click(self):
        self.mainsail_controller.send_gcode('G91')
        self.mainsail_controller.send_gcode(self.gcode_command1)
        # self.serial_port.write(b'b')  # Send 'b' to Arduino
        print("Right")
        QTimer.singleShot(200, self.updateMotorPosition)

    def handle_btn5_click(self):
        self.photo = True
        print("Shoot")

    def handle_btn6_click(self):
        self.mainsail_controller.send_gcode('XY_HOME')
        print("HOME")
        QTimer.singleShot(200, self.updateMotorPosition)

    def handle_btn7_click(self):
        save_path = 'FILE'
        self.filePath, self.filterType = QFileDialog.getOpenFileNames(
            self, 'Open Files', save_path, "Images (*.png *.xpm *.jpg *.jpeg *.bmp);;All Files (*)")  # 選取多個檔案
        
        if self.filePath:
            self.open_image_dialog(self.filePath[0])  # 加載第一個選中的圖片

    def open_image_dialog(self, save_path):
        self.image_dialog = ImageDialog(save_path, self)
        self.image_dialog.show()
        print("Download")

    def handle_btn8_click(self):
        self.mainsail_controller.send_gcode('M112')
        print(" STOP ")

    def handle_btn9_click(self):
        gcode_command = self.display_box.text().strip()  # 從文本框中獲取Gcode指令並移除多餘空格
    
        if not gcode_command:  # 如果輸入為空，直接返回
            return
    
        # 檢查是否包含座標模式指令(G90/G91)
        if 'G90' in gcode_command or 'G91' in gcode_command:
            # 分解指令
            commands = gcode_command.split()
            mode = None
            x_value = None
            y_value = None
        
            # 解析各部分指令
            for cmd in commands:
                if cmd == 'G90' or cmd == 'G91':
                    mode = cmd
                elif cmd.startswith('X'):
                    x_value = cmd
                elif cmd.startswith('Y'):
                    y_value = cmd
        
            # 首先發送座標模式指令
            if mode:
                self.mainsail_controller.send_gcode(mode)
                print(f"發送座標模式: {mode}")
        
            # 然後發送移動指令(如果有)
        if x_value or y_value:
            move_cmd = "G1"
            if x_value:
                move_cmd += f" {x_value}"
            if y_value:
                move_cmd += f" {y_value}"
            
            self.mainsail_controller.send_gcode(move_cmd)
            print(f"發送移動指令: {move_cmd}")
        else:
            # 如果沒有指定座標模式，則直接發送原始指令
            self.mainsail_controller.send_gcode(gcode_command)
            print(f"發送原始指令: {gcode_command}")
    
        # 清空輸入框
        self.display_box.clear()
        QTimer.singleShot(200, self.updateMotorPosition)

    def handle_btn10_click(self):
        def background_task():
            self.mainsail_controller.send_gcode('XY_HOME')
            x, y = self.getMotorPosition()  # 在迴圈外取得位置
            if x is None or y is None:
                print("無法取得座標")
                return
            while not (-1 < x < 1 and -1 < y < 1):  # 確保正確比較方式
                self.mainsail_controller.send_gcode('XY_HOME')
                x, y = self.getMotorPosition()
                self.updateMotorPosition()
            
            self.mainsail_controller.send_gcode('G90')
            self.mainsail_controller.send_gcode('G4 P5000')
            self.automatic()

            x, y = self.getMotorPosition()  # 重新取得位置
            if x is None or y is None:
                print("無法取得座標")
        
            while not (-1 < x < 1 and -1 < y < 1):  # 確保正確比較方式
                self.mainsail_controller.send_gcode('XY_HOME')
                x, y = self.getMotorPosition()
                self.updateMotorPosition()

        thread = threading.Thread(target=background_task)
        thread.start()

    def closeEvent(self, event):
        self.ocv = False
        # self.video.join()
        event.accept()

    def start_thread(self, thread):
        thread.start()

    # def paintEvent(self, event):
    #     # 繪製圓角背景
    #     painter = QPainter(self)
    #     painter.setRenderHint(QPainter.Antialiasing)
    #     brush = QBrush(QColor(255, 255, 0))  # 白色背景
    #     painter.setBrush(brush)
    #     painter.setPen(QtCore.NoPen)
    #     rect = self.rect()
    #     painter.drawRoundedRect(rect, 100, 100)  # 圓角半徑 20px

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = mainWindow()

    # ✅ 使用多執行緒，防止 GUI 卡死
    from threading import Thread

    def run_detection():
        yolo_model, BP = load_model()

        # 設定資料夾路徑
        image_folder = r"Test/bad"
        output_folder = r"CutTest/bad"

        # ✅ 執行 YOLOv5 裁切 + CNN 辨識
        confidences = detect_and_classify(yolo_model, BP, image_folder, output_folder)
        print("Confidences:", confidences)

    # ✅ 啟動一個新執行緒運行 YOLO + CNN，避免 PyQt 界面卡死
    detection_thread = Thread(target=run_detection)
    detection_thread.start()

    # ✅ 啟動 PyQt GUI
    main_window.show()
    sys.exit(app.exec_())
