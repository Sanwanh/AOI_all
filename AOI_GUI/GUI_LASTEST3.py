from PyQt5.QtWidgets import QWidget, QPushButton, QToolButton, QLCDNumber, QLabel, QApplication, QFrame, QLineEdit, QTextEdit, QFileDialog,QVBoxLayout,QDialog
from PyQt5.QtGui import QImage, QPixmap,QIcon,QFont
from PyQt5.QtCore import QThread, pyqtSignal, QTimer, QDateTime, QRect, Qt as QtCore,QSize
# from qt_material import apply_stylesheet
import qtmodern.styles
import qtmodern.windows
import cv2
import sys
import threading
import os
#import psutil  # from gpiozero import CPUTemperature
import moonrakerpy as moonpy
import torch
import requests,json

class MainsailController:
    def __init__(self, mainsail_ip):
        # 使用 mainsail 的 Web/IP 位址實體化 MoonrakerPrinter 物件
        self.printer = moonpy.MoonrakerPrinter(mainsail_ip)

    def send_gcode(self, gcode_command):
        self.printer.send_gcode(gcode_command)  # 向 mainsail 發送 Gcode指令

    def read_gcode_messages(self, count=5):
        # 從 mainsail 的打印機中讀取 Gcode 訊息並將其返回，count => 要讀取的訊息數量
        return self.printer.get_gcode(count)

class ImageDialog(QDialog):
    def __init__(self, save_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("圖片查看器")
        self.setGeometry(100, 100, 800, 600)

        self.label = QLabel(self)
        self.label.setGeometry(10, 10, 780, 580)

        self.load_image(save_path)

    def load_image(self, save_path):
        pixmap = QPixmap(save_path)
        if pixmap.isNull():
            self.label.setText("無法加載圖片")
        else:
            self.label.setPixmap(pixmap)
            self.label.setScaledContents(True)


class mainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.window_w, self.window_h = 1280, 720 # 1500,900
        self.setWindowTitle('AOI')
        self.resize(self.window_w, self.window_h)
        self.setStyleSheet('background:')

        self.ui()

        #self.mainsail_controller = MainsailController('http://192.168.50.136')
        self.photo_number = 1  # 照片檔名從1開始
        self.ocv = True
        self.video = threading.Thread(target=self.opencv)
        self.video.start()

        '''self.resource_usage = boardInfoClass()
        self.resource_usage.start()
        self.resource_usage.cpu.connect(self.handle_cpu_signal)
        self.resource_usage.ram.connect(self.handle_ram_signal)'''

        # # QTimer
        # self.lcd_timer = QTimer()
        # self.lcd_timer.timeout.connect(self.clock)
        # self.lcd_timer.start()

        # self.timer = QTimer(self)
        # self.timer.timeout.connect(self.updateMotorPosition)
        # self.timer.start(1000)  # 每1000毫秒（1秒）更新一次

        # Replace 'COM' with your Arduino's port
        # self.serial_port = serial.Serial('COM4', 9600)
        # time.sleep(2)

        # Gcode
        self.gcode_command1 = ''
        self.gcode_command2 = ''
        self.gcode_command3 = ''
        self.gcode_command4 = ''

    '''def getMotorPosition(self):
        try:
            res = requests.get(
                'http://192.168.50.136/printer/objects/query?gcode_move=position')
            js = json.loads(res.content)
            x, y = js['result']['status']['gcode_move']['position'][0:2]
            print(x, y)
            return x, y
        except Exception as e:
            print(f"Error: {e}")
            return None, None

    def updateMotorPosition(self):
        x, y = self.getMotorPosition()
        self.btn20.setText(f'X : {x:.2f} , Y : {y:.2f}')'''

    def ui(self):

        # self.frame = QFrame(self)
        # self.frame.setGeometry(QRect(840, 80, 600, 221))
        # #self.frame.setFrameShape(QFrame.StyledPanel)
        # #self.frame.setFrameShadow(QFrame.Raised)
        # #self.frame.setStyleSheet('border: 2px solid black')
        # self.frame.setObjectName("frame")

        # # X軸 Label
        # x_label = QLabel("X", self)
        # x_label.setGeometry(920, 330, 20, 50)
        # font = x_label.font()
        # font.setPointSize(16)  # Adjust font size as needed
        # x_label.setFont(font)
        #
        # # Y軸 Label
        # x_label = QLabel("Y", self)
        # x_label.setGeometry(920, 400, 20, 50)
        # font = x_label.font()
        # font.setPointSize(16)  # Adjust font size as needed
        # x_label.setFont(font)

        # 相機畫面 Label
        camera_label = QLabel('相機畫面',self)
        camera_label.setGeometry(50,50,200,50)
        camera_label.setFont(QFont("SimHei",16)) 
        # # Set text
        # font = QFont('Arial', 11)
        # font.setBold(True)
        # camera_label.setFont(font)
        # # camera_label.setLayoutDirection(QtCore.LeftToRight)

        # 代碼輸入 Label
        x_label = QLabel("G-Code Command", self)
        x_label.setGeometry(850, 500, 250, 50)
        x_label.setFont(QFont("Arial", 16))

        # X軸
        # self.display_box1 = QLineEdit(self)  # 創建單行顯示框
        # self.display_box1.setGeometry(950, 330, 200, 50)
        # # self.display_box.setReadOnly(True)  # 設置讀取，防止用戶輸入
        # layout = QVBoxLayout()
        # self.display_box1.setStyleSheet("background-color: white")  # 背景顏色
        # self.display_box1.returnPressed.connect(self.handle_btn17_click)

        # Y軸
        # self.display_box2 = QLineEdit(self)  # 創建單行顯示框
        # self.display_box2.setGeometry(950, 400, 200, 50)
        # # self.display_box.setReadOnly(True)  # 設置讀取，防止用戶輸入
        # layout = QVBoxLayout()
        # self.display_box2.setStyleSheet("background-color: white")
        # self.display_box2.returnPressed.connect(self.handle_btn18_click)

        # 輸入代碼
        # Create QLineEdit
        self.display_box5 = QLineEdit(self)  # 創建單行顯示框
        self.display_box5.setGeometry(850, 550, 280, 50)
        self.display_box5.setPlaceholderText("Enter G-Code...")
        layout = QVBoxLayout()
        self.display_box5.setStyleSheet("""
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
        #Set font
        font = QFont("Arial",12)
        self.display_box5.setFont(font)
        self.display_box5.returnPressed.connect(self.handle_btn19_click)

        # X軸多行顯示框上
        # x_label = QLabel( "X", self)
        # x_label.setGeometry(900, 510, 20, 50)
        # font = x_label.font()
        # font.setPointSize(13)  # Adjust font size as needed
        # x_label.setFont(font)

        # X軸多行顯示框
        # self.display_box3 = QTextEdit(self)      # 創建多行顯示框
        # self.display_box3.setGeometry(900, 550, 100, 200)
        # self.display_box3.setReadOnly(True)
        # self.display_box3.setStyleSheet("background-color: white")

        # Y軸多行顯示框上
        # x_label = QLabel("Y", self)
        # x_label.setGeometry(1100, 510, 20, 50)
        # font = x_label.font()
        # font.setPointSize(13)  # Adjust font size as needed
        # x_label.setFont(font)

        # Y軸多行顯示框
        # self.display_box4 = QTextEdit(self)      # 創建多行顯示框
        # self.display_box4.setGeometry(1100, 550, 100, 200)
        # self.display_box4.setReadOnly(True)
        # self.display_box4.setStyleSheet("background-color: white")

        # # G軸多行顯示框上
        # x_label = QLabel("G", self)
        # x_label.setGeometry(1300, 510, 20, 50)
        # font = x_label.font()
        # font.setPointSize(13)  # Adjust font size as needed
        # x_label.setFont(font)'''

        # '''# G軸多行顯示框
        # self.display_box6 = QTextEdit(self)      # 創建多行顯示框
        # self.display_box6.setGeometry(1300, 550, 100, 200)
        # self.display_box6.setReadOnly(True)
        # self.display_box6.setStyleSheet("background-color: white")

        # 列表
        #self.display_box7 = 

        self.label = QLabel(self)
        self.label.setGeometry(10, 120, 800, 500)

        self.cpu_label = QLabel(self)  
        self.cpu_label.setGeometry(940, 20, 120, 50)
        self.set_font_size(self.cpu_label, 12)

        self.ram_label = QLabel(self)
        self.ram_label.setGeometry(1060, 20, 120, 50)
        self.set_font_size(self.ram_label, 12)

        # self.lcd_label = QLCDNumber(self)
        # self.lcd_label.setGeometry(1300, 20, 120, 50)
        # self.lcd_label.setFrameStyle(QFrame.NoFrame)
        # self.lcd_label.setDigitCount(8)
        # self.lcd_label.show()

        # Create the btn1
        btn1 = QPushButton(self)
        # btn1.setArrowType(QtCore.UpArrow)
        # btn1.setText('上')
        btn1.setGeometry(1000, 35, 60, 45)
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
        # Set icon
        btn1.setIcon(QIcon('E:\python GUI\qypt project\icons8-up-arrow-25.png')) # icons8-up-arrow-25.png
        btn1.setIconSize(btn1.size()*1)
        # Set text
        font = QFont('Arial', 11)
        font.setBold(True)
        btn1.setFont(font)
        btn1.setLayoutDirection(QtCore.LeftToRight)   

        # Create the btn2
        btn2 = QPushButton(self)
        # btn2.setArrowType(QtCore.UpArrow)
        # btn2.setText('下')
        btn2.setGeometry(1000, 145, 60, 45)
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
        # Set icon
        btn2.setIcon(QIcon('E:\python GUI\qypt project\icons8-down-arrow-24.png')) # icons8-up-arrow-25.png
        btn2.setIconSize(btn2.size()*1)
        # Set text
        font = QFont('Arial', 11)
        font.setBold(True)
        btn2.setFont(font)
        btn2.setLayoutDirection(QtCore.LeftToRight)  

        # Create the btn3
        btn3 = QPushButton(self)
        # btn3.setArrowType(QtCore.UpArrow)
        # btn3.setText('左')
        btn3.setGeometry(930, 90, 60, 45)
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
        # Set icon
        btn3.setIcon(QIcon('E:\python GUI\qypt project\icons8-left-48.png'))
        btn3.setIconSize(btn3.size()*0.5)
        # Set text
        font = QFont('Arial', 11)
        font.setBold(True)
        btn3.setFont(font)
        btn3.setLayoutDirection(QtCore.LeftToRight)

        # btn3 = QPushButton(self) # btn3 = QToolButton(self.frame)
        # btn3.setArrowType(QtCore.LeftArrow)
        # btn3.setText('左')
        # btn3.setGeometry(30, 90, 50, 50)
        # btn3.setStyleSheet('color:black;background:#FFFFFF')

        # Create the btn4
        btn4 = QPushButton(self)
        # btn4.setArrowType(QtCore.UpArrow)
        # btn4.setText('右')
        btn4.setGeometry(1070, 90, 60, 45)
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
        # Set icon
        btn4.setIcon(QIcon('E:\python GUI\qypt project\icons8-right-arrow-48.png'))
        btn4.setIconSize(btn4.size()*0.5)
        # Set text
        font = QFont('Arial', 11)
        font.setBold(True)
        btn4.setFont(font)
        btn4.setLayoutDirection(QtCore.LeftToRight)

        # Create the btn5
        btn5 = QPushButton(self)
        btn5.setGeometry(120, 640, 150, 40) # btn5.setGeometry(120, 640, 100, 50)
        btn5.setStyleSheet("""
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
        # Set icon
        btn5.setIcon(QIcon('E:\python GUI\qypt project\camera_icon.png'))
        btn5.setIconSize(btn5.size()*1)
        # Set text
        font = QFont('Arial', 11)
        font.setBold(True)
        btn5.setFont(font)
        btn5.setText('  Shoot')
        btn5.setLayoutDirection(QtCore.LeftToRight)
    
        # Create the btn6
        btn6 = QPushButton(self)
        btn6.setGeometry(1000, 90, 60, 45) # btn6.setGeometry(120, 640, 100, 50)
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
        # Set icon
        btn6.setIcon(QIcon('E:\python GUI\qypt project\icons8-home-50.png'))
        btn6.setIconSize(btn5.size()*0.5)
        # Set text
        font = QFont('Arial', 11)
        font.setBold(True)
        btn6.setFont(font)
        btn6.setLayoutDirection(QtCore.LeftToRight)
        
        # Create the btn7       
        btn7 = QPushButton(self)
        btn7.setGeometry(320, 640, 150, 40)
        btn7.setStyleSheet("""
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
        # Set icon
        btn7.setIcon(QIcon('E:\\python GUI\\qypt project\\file_icon.png'))
        btn7.setIconSize(btn7.size()*1)        
        # Set text
        font = QFont('Arial', 11)
        font.setBold(True)
        btn7.setFont(font)
        btn7.setText('  File')
        btn7.setLayoutDirection(QtCore.LeftToRight)

        # Create the btn8
        btn8 = QPushButton(self)
        btn8.setGeometry(530, 640, 150, 40)
        btn8.setStyleSheet("""
            QPushButton {
                background-color: #FF3B30;
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
        # Set icon
        btn8.setIcon(QIcon('E:\python GUI\qypt project\square_icon.png'))
        btn8.setIconSize(btn8.size()*1)        
        # Set text
        font = QFont('Arial', 11)
        font.setBold(True)
        btn8.setFont(font)
        btn8.setText('  Stop')
        btn8.setLayoutDirection(QtCore.LeftToRight) 

        # Create the btn9
        btn9 = QPushButton(self)
        btn9.setGeometry(800, 300, 60, 50)
        # btn9.setStyleSheet('background:#FFFFFF')
        btn9.setStyleSheet("""
                QPushButton {
                    background-color: #2C2C2C;
                    border: none;
                    border-radius: 5px;
                    color: white;                                
                    padding: 5px 10px;
                    
                }
                QPushButton:checked {
                    background-color: #3C3C3C;
                }
            """)
        btn9.setCheckable(True)
        btn9.setAutoExclusive(True)

        # Set text
        font = QFont('Arial', 11)
        font.setBold(True)
        btn9.setFont(font)
        btn9.setText('0.1')
        btn9.setLayoutDirection(QtCore.LeftToRight)         

        # Create the btn10
        btn10 = QPushButton(self)
        btn10.setGeometry(870, 300, 60, 50)
        # btn9.setStyleSheet('background:#FFFFFF')
        btn10.setStyleSheet("""
                QPushButton {
                    background-color: #2C2C2C;
                    border: none;
                    border-radius: 5px;
                    color: white;                                
                    padding: 5px 10px;
                    
                }
                QPushButton:checked {
                    background-color: #3C3C3C;
                }
            """)
        btn10.setCheckable(True)
        btn10.setAutoExclusive(True)

        # Set text
        font = QFont('Arial', 11)
        font.setBold(True)
        btn10.setFont(font)
        btn10.setText('1')
        btn10.setLayoutDirection(QtCore.LeftToRight)

        # Create the btn11
        btn11 = QPushButton(self)
        btn11.setGeometry(940, 300, 60, 50)
        # btn11.setStyleSheet('background:#FFFFFF')
        btn11.setStyleSheet("""
                QPushButton {
                    background-color: #2C2C2C;
                    border: none;
                    border-radius: 5px;
                    color: white;                                
                    padding: 5px 10px;
                    
                }
                QPushButton:checked {
                    background-color: #3C3C3C;
                }
            """)
        btn11.setCheckable(True)
        btn11.setAutoExclusive(True)

        # Set text
        font = QFont('Arial', 11)
        font.setBold(True)
        btn11.setFont(font)
        btn11.setText('10')
        btn11.setLayoutDirection(QtCore.LeftToRight)

        # Create the btn12
        btn12 = QPushButton(self)
        btn12.setGeometry(1010, 300, 60, 50)
        # btn12.setStyleSheet('background:#FFFFFF')
        btn12.setStyleSheet("""
                QPushButton {
                    background-color: #2C2C2C;
                    border: none;
                    border-radius: 5px;
                    color: white;                                
                    padding: 5px 10px;
                    
                }
                QPushButton:checked {
                    background-color: #3C3C3C;
                }
            """)
        btn12.setCheckable(True)
        btn12.setAutoExclusive(True)

        # Set text
        font = QFont('Arial', 11)
        font.setBold(True)
        btn12.setFont(font)
        btn12.setText('25')
        btn12.setLayoutDirection(QtCore.LeftToRight)

        # Create the btn13
        btn13 = QPushButton(self)
        btn13.setGeometry(1080, 300, 60, 50)
        # btn13.setStyleSheet('background:#FFFFFF')
        btn13.setStyleSheet("""
                QPushButton {
                    background-color: #2C2C2C;
                    border: none;
                    border-radius: 5px;
                    color: white;                                
                    padding: 5px 10px;
                    
                }
                QPushButton:checked {
                    background-color: #3C3C3C;
                }
            """)
        btn13.setCheckable(True)
        btn13.setAutoExclusive(True)

        # Set text
        font = QFont('Arial', 11)
        font.setBold(True)
        btn13.setFont(font)
        btn13.setText('50')
        btn13.setLayoutDirection(QtCore.LeftToRight)

        # Create the btn14
        btn14 = QPushButton(self)
        btn14.setGeometry(1150, 300, 60, 50)
        # btn14.setStyleSheet('background:#FFFFFF')
        btn14.setStyleSheet("""
                QPushButton {
                    background-color: #2C2C2C;
                    border: none;
                    border-radius: 5px;
                    color: white;                                
                    padding: 5px 10px;
                    
                }
                QPushButton:checked {
                    background-color: #3C3C3C;
                }
            """)
        btn14.setCheckable(True)
        btn14.setAutoExclusive(True)

        # Set text
        font = QFont('Arial', 11)
        font.setBold(True)
        btn14.setFont(font)
        btn14.setText('100')
        btn14.setLayoutDirection(QtCore.LeftToRight)

        '''btn15 = QPushButton(self)
        btn15.setText('位置')
        btn15.setGeometry(840, 330, 60, 50)
        btn15.setStyleSheet('background:#FFFFFF; color:black')'''

        '''btn16 = QPushButton(self)
        btn16.setText('清除')
        btn16.setGeometry(840, 400, 60, 50)
        btn16.setStyleSheet('background:#FFFFFF; color:black')'''

        # X軸輸入
        # btn17 = QPushButton(self)
        # btn17.setText('加入')
        # btn17.setGeometry(1200, 330, 60, 50)
        # btn17.setStyleSheet('background:#FFFFFF;color:black')
        # btn17.clicked.connect(self.handle_btn17_click)

        # Y軸加入
        # btn18 = QPushButton(self)
        # btn18.setText('加入')
        # btn18.setGeometry(1200, 400, 60, 50)
        # btn18.setStyleSheet('background:#FFFFFF; color:black')
        # btn18.clicked.connect(self.handle_btn18_click)

        # 代碼確認
        # Create the btn19
        btn19 = QPushButton(self)
        btn19.setGeometry(1150, 550, 60, 50)
        btn19.setStyleSheet("""
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
        # Set text
        font = QFont('Arial', 11)
        font.setBold(True)
        btn19.setFont(font)
        btn19.setText('Send')
        btn19.setLayoutDirection(QtCore.LeftToRight)

        # btn20 = QPushButton(self.frame)
        # btn20.setText('Auto')
        # btn20.setGeometry(140, 10, 100, 50)
        # btn20.setStyleSheet(
        #     'font-size:22px;font-weight:bold;background:#FFFFFF')

        # self.btn20 = QLabel(self)
        # self.btn20.setGeometry(0, 0, 400, 50)
        # self.btn20.setStyleSheet(
        #     'font-size:22px; font-weight:bold; background:#FFFFFF; color: black')
        # # Ensure btn20 is updated initially
        # self.updateMotorPosition()

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
        btn11.clicked.connect(self.handle_btn11_click)
        btn12.clicked.connect(self.handle_btn12_click)
        btn13.clicked.connect(self.handle_btn13_click)
        btn14.clicked.connect(self.handle_btn14_click)
        #btn15.clicked.connect(self.handle_btn15_click)
        #btn16.clicked.connect(self.handle_btn16_click)
        # btn17.clicked.connect(self.handle_btn17_click)
        # btn18.clicked.connect(self.handle_btn18_click)
        btn19.clicked.connect(self.handle_btn19_click)
        # btn20.clicked.connect(self.handle_btn20_click)

    def set_font_size(self, widget, size):
        font = widget.font()  # 取得 widget 元件的字體
        font.setPointSize(size)  # 設定字體大小
        widget.setFont(font)  # 設定 widget 元件的字體

    # def handle_cpu_signal(self, cpu_usage):
    #     self.cpu_label.setText(f'CPU: {cpu_usage}%')
    #
    # def handle_ram_signal(self, ram_info):
    #     used_percentage = ram_info[2]  # 獲取RAM%
    #     self.ram_label.setText(f'RAM: {used_percentage}% Used')

    # 存檔時使用順序名稱的函式
    def rename(self):
        name = str(self.photo_number)  # 使用目前的照片編號作為檔名
        self.photo_number += 1  # 照片編號加一，準備下一張照片的檔名
        return name

    photo = False

    def takephoto(self):  # 按下拍照的動作
        self.photo = True

    def opencv(self):
        #cap = cv2.VideoCapture('http://192.168.50.136//webcam//?action=stream')
        cap = cv2.VideoCapture(0)
        #device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model = torch.hub.load(r"E:\python GUI\pythonProject", 'custom',
                               path=r"E:\python GUI\pythonProject\runs\train\exp8\weights\best1.pt", source='local')

        if not cap.isOpened():
            print("Cannot open camera ")
            exit()
        while self.ocv:
            position = [None,None,None,None,None,None]
            index = len(position)
            step = 0
            '''x, y = self.getMotorPosition()'''
            ret, frame = cap.read()
            frame = cv2.flip(frame, 1)  # 鏡頭翻轉           
            if not ret:
                print("Cannot receive frame")
                break

            file_path = "E:\python GUI\qypt project\FILE"
            frame = cv2.resize(frame, (640, 480))   # 改變尺寸和視窗相同

            if self.photo == True:
                self.photo = False
                name = self.rename()
                save_path = os.path.join(file_path, f'{name}.jpg')  # 合併路徑和檔案名稱
                cv2.imwrite(save_path, frame)  # 儲存圖片

            results = model(frame)
            detections = results.pandas().xyxy[0]
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            for index, row in detections.iterrows():
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

                modedImg = frame[y1:y1+w,x1:x1+h]

            height, width, channel = frame.shape
            byterPerline = channel * width
            img = QImage(frame, width, height,
                         byterPerline, QImage.Format_RGB888)
            self.label.setPixmap(QPixmap.fromImage(img))

    # def openFiles(self):
    #     save_path = 'D:\python GUI\qypt project\FILE'
    #     self.filePath, self.filterType = QFileDialog.getOpenFileNames(self, 'Open Files', save_path)  # 選取多個檔案


    def handle_btn1_click(self):
        self.mainsail_controller.send_gcode('G91')
        self.mainsail_controller.send_gcode(self.gcode_command3)
        print("up")

    def handle_btn2_click(self):
        self.mainsail_controller.send_gcode('G91')
        self.mainsail_controller.send_gcode(self.gcode_command4)
        print("down")

    def handle_btn3_click(self):
        self.mainsail_controller.send_gcode('G91')
        self.mainsail_controller.send_gcode(self.gcode_command2)
        # self.serial_port.write(b'a')  # Send 'a' to Arduino
        print("left")

    def handle_btn4_click(self):
        self.mainsail_controller.send_gcode('G91')
        self.mainsail_controller.send_gcode(self.gcode_command1)
        # self.serial_port.write(b'b')  # Send 'b' to Arduino
        print("right")

    def handle_btn5_click(self):
        self.photo = True
        print("Shoot")

    def handle_btn6_click(self):
        self.mainsail_controller.send_gcode('XY_HOME')
        print("Align")

    def handle_btn7_click(self):
        save_path = 'E:\python GUI\qypt project\FILE'
        self.filePath, self.filterType = QFileDialog.getOpenFileNames(
            self, 'Open Files', save_path, "Images (*.png *.xpm *.jpg *.jpeg *.bmp);;All Files (*)")  # 選取多個檔案
        
        if self.filePath:
            self.open_image_dialog(self.filePath[0])  # 加載第一個選中的圖片

    def open_image_dialog(self, save_path):
        self.image_dialog = ImageDialog(save_path, self)
        self.image_dialog.show()

        # self.hide()
        # self.window2 = screen2()
        # self.window2.show()
        print("download")

    def handle_btn8_click(self):
        self.mainsail_controller.send_gcode('M112')
        print(" STOP ")

    def handle_btn9_click(self):
        self.gcode_command1 = 'G1 X0.1 '
        self.gcode_command2 = 'G1 X-0.1 '
        self.gcode_command3 = 'G1 Y0.1 '
        self.gcode_command4 = 'G1 Y-0.1 '
        # self.serial_port.write(b'a')  # Send 'a' to Arduino
        print("0.1")

    def handle_btn10_click(self):
        self.gcode_command1 = 'G1 X1 '
        self.gcode_command2 = 'G1 X-1 '
        self.gcode_command3 = 'G1 Y1 '
        self.gcode_command4 = 'G1 Y-1 '
        print("1")

    def handle_btn11_click(self):
        self.gcode_command1 = 'G1 X10 '
        self.gcode_command2 = 'G1 X-10 '
        self.gcode_command3 = 'G1 Y10 '
        self.gcode_command4 = 'G1 Y-10 '
        print("10")

    def handle_btn12_click(self):
        self.gcode_command1 = 'G1 X25 '
        self.gcode_command2 = 'G1 X-25 '
        self.gcode_command3 = 'G1 Y25 '
        self.gcode_command4 = 'G1 Y-25 '
        print("25")

    def handle_btn13_click(self):
        self.gcode_command1 = 'G1 X50 '
        self.gcode_command2 = 'G1 X-50 '
        self.gcode_command3 = 'G1 Y50 '
        self.gcode_command4 = 'G1 Y-50 '
        print("50")

    def handle_btn14_click(self):
        self.gcode_command1 = 'G1 X100 '
        self.gcode_command2 = 'G1 X-100 '
        self.gcode_command3 = 'G1 Y100'
        self.gcode_command4 = 'G1 Y-100 '
        print("100")

    def handle_btn15_click(self):
        self.display_box3.setText("座標")

    def handle_btn16_click(self):
        self.display_box3.clear()
        self.display_box4.clear()
        self.display_box6.clear()

    def handle_btn17_click(self):
        value = self.display_box1.text()  # 從文本框中獲取用戶輸入的數值
        text = f'{value}'  # 顯示 "X" 與用戶輸入的數值
        self.display_box3.setAlignment(QtCore.AlignTop)  # 對齊
        self.display_box3.append(text)  # 將文本添加到第二顯示框上
        self.display_box1.clear()
        gcode_command = f'G1 X{value}'  # 在 Gcode 指令中添加 'X' 和用戶輸入的數值
        # self.mainsail_controller.send_gcode(gcode_command)

    def handle_btn18_click(self):
        value = self.display_box2.text()  # 从文本框中获取 Gcode 指令
        text = f'{value}'
        self.display_box4.setAlignment(QtCore.AlignTop)  # 对齐
        self.display_box4.append(text)      # 将文本添加到第三显示框上
        self.display_box2.clear()
        gcode_command = f'G1 Y{value}'
        # self.mainsail_controller.send_gcode(gcode_command)

    def handle_btn19_click(self):
        gcode_command = self.display_box5.text()  # 从文本框中获取 Gcode 指令
        '''if gcode_command in ['G90','G91']:
            self.coordinate_mode = gcode_command
            self.mainsail_controller.send_gcode(gcode_command)
            self.display_box6.append(f"切換到{gcode_command}模式")
        
        else:
            # 處理XY座標輸入
            commands = gcode_command.split()
            full_command = f"{self.coordinate_mode}"
        for command in commands:
            if command.startswith('X') or command.startswith('Y'):
                full_command += f" {command}"                       

        self.display_box5.clear() '''
        self.mainsail_controller.send_gcode(gcode_command)
        text = self.display_box5.text()
        self.display_box6.setAlignment(QtCore.AlignTop)  # 对齐
        self.display_box6.append(text)      # 将文本添加到第二显示框上
        self.display_box5.clear()

    # def handle_btn20_click(self):
    #     pass

    '''def clock(self):
        self.DateTime = QDateTime.currentDateTime()
        formatted_time = self.DateTime.toString('hh:mm:ss')
        self.lcd_label.display(formatted_time)'''

    def closeEvent(self, event):
        self.ocv = False
        self.video.join()
        event.accept()

    def start_thread(self, thread):
        thread.start()

'''class boardInfoClass(QThread):
    cpu = pyqtSignal(float)
    ram = pyqtSignal(tuple)

    def getCPU(self):
        return psutil.cpu_percent(interval=1)

    def getRAM(self):
        return psutil.virtual_memory()

    def run(self):
        self.ThreadActive = True
        while self.ThreadActive:
            cpu = self.getCPU()
            ram = self.getRAM()
            self.cpu.emit(cpu)
            self.ram.emit(ram)

    def stop(self):
        self.ThreadActive = False
        self.quit()'''


# class screen2(QWidget):
#     def __init__(self):
#         super().__init__()
#         self.window_w, self.window_h = 1250, 800
#         self.setWindowTitle('page2')
#         self.resize(self.window_w, self.window_h)
#         self.setStyleSheet('background:')

#         self.ui2()

#     def ui2(self):
#         btn1 = QPushButton(self)
#         btn1.setText('Back')
#         btn1.setGeometry(20, 20, 100, 50)
#         btn1.setStyleSheet('background:#FFFFFF')
#         btn1.clicked.connect(self.Back)

#     def Back(self):
#         self.hide()
#         self.window1 = mainWindow()
#         self.window1.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = mainWindow()

    #qtmodern.styles.dark(app)
    #main_window = qtmodern.windows.ModernWindow(main_window)
    # apply_stylesheet(app, theme='dark_teal.xml')

    main_window.show()
    sys.exit(app.exec_())
