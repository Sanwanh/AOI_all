from PyQt5.QtWidgets import QWidget, QPushButton,QSlider, QToolButton, QLabel, QApplication, QFrame, QLineEdit, QTextEdit, QFileDialog,QVBoxLayout,QDialog,QGraphicsDropShadowEffect
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
# import torch
import requests,json

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
    def __init__(self, save_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("圖片查看器") # 圖片視窗
        self.setGeometry(100, 100, 800, 600)

        self.label = QLabel(self) # 圖片本身
        self.label.setGeometry(10, 10, 780, 580)
        self.load_image(save_path)

    def load_image(self, save_path): # 從指定的路徑加載圖片並在標籤（QLabel）中顯示
        pixmap = QPixmap(save_path) # QPixmap 用於加載和處理圖片
        if pixmap.isNull():
            self.label.setText("無法加載圖片")
        else:
            self.label.setPixmap(pixmap) # 將圖片設置為標籤label的內容
            self.label.setScaledContents(True) # 讓圖片自適應視窗大小

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

        self.mainsail_controller = MainsailController('http://192.168.50.136')
        self.photo_number = 1  # 照片檔名從1開始
        self.ocv = True
        self.video = threading.Thread(target=self.opencv)
        self.video.start()

        # Gcode
        self.gcode_command1 = ''
        self.gcode_command2 = ''
        self.gcode_command3 = ''
        self.gcode_command4 = ''

        # 新增一個計時器，每 500 毫秒更新一次座標
        self.position_timer = QTimer(self)
        self.position_timer.timeout.connect(self.updateMotorPosition)
        self.position_timer.start(500)  # 每500毫秒更新一次

    def getMotorPosition(self):
        try:
            res = requests.get(
                'http://192.168.50.136/printer/objects/query?gcode_move=position',timeout=1) # 添加逾時設定
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
        else:
        # 當無法獲取座標時顯示錯誤訊息
            self.motorX_label.setText('無法獲取座標')

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

        btn1.clicked.connect(self.handle_btn1_click)
        btn2.clicked.connect(self.handle_btn2_click)
        btn3.clicked.connect(self.handle_btn3_click)
        btn4.clicked.connect(self.handle_btn4_click)
        btn5.clicked.connect(self.handle_btn5_click)
        btn6.clicked.connect(self.handle_btn6_click)
        btn7.clicked.connect(self.handle_btn7_click)
        btn8.clicked.connect(self.handle_btn8_click)
        btn9.clicked.connect(self.handle_btn9_click)

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

    def takephoto(self):  # 按下拍照的動作
        self.photo = True

    def opencv(self):
        cap = cv2.VideoCapture('http://192.168.50.136//webcam//?action=stream')
        #cap = cv2.VideoCapture(0)
        #device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        '''model = torch.hub.load(r"E:\python GUI\pythonProject", 'custom',
                               path=r"E:\python GUI\pythonProject\runs\train\exp8\weights\best1.pt", source='local')'''

        if not cap.isOpened():
            print("Cannot open camera")
            exit() # 終止程式執行
        while self.ocv: # 因為 PyQt5 的視窗本身是「迴圈」，所以需要使用 threading 將 OpenCV 讀取影像的功能，放在另外的執行緒執行。
            position = [None,None,None,None,None,None]
            index = len(position)
            step = 0
            # x, y = self.getMotorPosition()
            ret, frame = cap.read()
            frame = cv2.flip(frame, 1)  # 鏡頭翻轉           
            if not ret:
                print("Cannot receive frame")
                break

            file_path = "FILE"
            frame = cv2.resize(frame, (640, 480))   # 改變尺寸和視窗相同

            if self.photo == True:
                self.photo = False
                name = self.rename()
                save_path = os.path.join(file_path, f'{name}.jpg')  # 合併路徑和檔案名稱
                cv2.imwrite(save_path, frame)  # 儲存圖片

            '''results = model(frame)
            detections = results.pandas().xyxy[0]'''
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            '''for index, row in detections.iterrows():
                # Extract bounding box coordinates and dimensions
                x1, y1, x2, y2 = int(row['xmin']), int(row['ymin']), int(row['xmax']), int(row['ymax'])
                w = x2 - x1
                h = y2 - y1
                # text1 = str("{:1.2f}".format(row['confidence']))
                # text2 = row['name']
                # # Draw the bounding box on the frame
                # cv2.putText(frame, text2, (x1 + 100, y1), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 3, cv2.LINE_AA)
                # cv2.putText(frame, text1, (x1, y1), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 3, cv2.LINE_AA)
                # cv2.rectangle(frame, (x1 - 10, y1 - 10), (x2 + 10, y2 + 10), (255, 0, 0), 2)

                # confident = row['confidence'] #0.4
                # if confident > 0.35:
                #     try:
                #         res = requests.get('http://192.168.50.136/printer/objects/query?gcode_move=position')
                #         js = json.loads(res.content)
                #         x, y = js['result']['status']['gcode_move']['position'][0:2]
                #         x1, y1 = x, y
                #         if position[step] is None or 
                #             position[step] = [x1,y1]
                #             step = step + 1
                #     except Exception as e:
                #         print(f"Error: {e}")
                #         return None, None

                modedImg = frame[y1:y1+w,x1:x1+h]'''

            height, width, channel = frame.shape
            byterPerline = channel * width
            img = QImage(frame, width, height,
                         byterPerline, QImage.Format_RGB888)
            self.label.setPixmap(QPixmap.fromImage(img))

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

    def closeEvent(self, event):
        self.ocv = False
        self.video.join()
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

    # qtmodern.styles.dark(app)
    # main_window = qtmodern.windows.ModernWindow(main_window)
    # apply_stylesheet(app, theme='dark_teal.xml')
    main_window.show()
    sys.exit(app.exec_())