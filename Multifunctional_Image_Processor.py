import os
import warnings
from PIL import Image, ExifTags,ImageQt, ImageEnhance
import io
#from google.cloud import vision
#import glob
from PyQt6 import QtWidgets
from PyQt6.QtGui import *
from PyQt6.QtCore import *
import sys


#########1
# 忽略特定的警告
warnings.filterwarnings("ignore", category=UserWarning, module="PIL")

def correct_image_orientation(img):
    """
    根據EXIF數據調整圖片方向
    """
    try:
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break

        exif = dict(img._getexif().items())

        if exif[orientation] == 3:
            img = img.rotate(180, expand=True)
        elif exif[orientation] == 6:
            img = img.rotate(270, expand=True)
        elif exif[orientation] == 8:
            img = img.rotate(90, expand=True)
    except (AttributeError, KeyError, IndexError):
        # 沒有EXIF數據或EXIF數據中沒有方向信息
        pass

    return img

def compress_image(input_image_path, output_image_path, quality):
    with Image.open(input_image_path) as img:
        img = correct_image_orientation(img)
        img.save(output_image_path, quality=quality, optimize=True)

def is_size_within_limit(file_path, size_limit_mb):
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    return file_size_mb <= size_limit_mb

def process_images(input_folder, output_folder, initial_quality=85, size_limit_mb=2):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for file_name in os.listdir(input_folder):
        if file_name.lower().endswith(('.png', '.jpg', '.jpeg')):
            input_image_path = os.path.join(input_folder, file_name)
            output_image_path = os.path.join(output_folder, file_name)

            quality = initial_quality
            while quality > 0:
                compress_image(input_image_path, output_image_path, quality)
                if is_size_within_limit(output_image_path, size_limit_mb):
                    print(f"圖片 '{file_name}' 已壓縮並符合大小要求。")
                    break
                quality -= 5

            if quality == 0:
                print(f"警告：無法將 '{file_name}' 壓縮到 {size_limit_mb}MB 以下。")


######2
def watermark_position(img, icon, position):
    """ 計算浮水印的位置 """
    img_width, img_height = img.size
    icon_width, icon_height = icon.size

    positions = {
        '1': (0, 0),
        '2': ((img_width - icon_width) // 2, 0),  
        '3': (img_width - icon_width, 0), 
        '4': (0, (img_height - icon_height) // 2), 
        '5': ((img_width - icon_width) // 2, (img_height - icon_height) // 2), 
        '6': (img_width - icon_width, (img_height - icon_height) // 2),  
        '7': (0, img_height - icon_height),  
        '8': ((img_width - icon_width) // 2, img_height - icon_height), 
        '9': (img_width - icon_width, img_height - icon_height)  
    }

    return positions.get(position, (0, 0))  # 如果輸入無效，默認為左上角

########4
def split_image_into_four(input_image_path, output_folder):
    """
    將圖片切割成四等分（左上、右上、左下、右下）。
    """
    with Image.open(input_image_path) as img:
        width, height = img.size

        # 計算切割點
        mid_width, mid_height = width // 2, height // 2

        # 定義四個區域
        boxes = [
            (0, 0, mid_width, mid_height),                      # 左上
            (mid_width, 0, width, mid_height),                 # 右上
            (0, mid_height, mid_width, height),                # 左下
            (mid_width, mid_height, width, height)             # 右下
        ]

        # 切割並保存每個區域
        for i, box in enumerate(boxes):
            part = img.crop(box)
            part.save(f"{output_folder}/part_{i+1}.jpg")
            print(f"部分 {i+1} 已保存")


#######5
class MyWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('GUI.studio')
        self.resize(540, 360)
        self.setUpdatesEnabled(True)
        self.img = False    # 建立一個變數儲存圖片
        self.ui()
        self.adjustUi()

    # 主要按鈕和文字標籤
    def ui(self):
        self.canvas = QPixmap(360,360)         # 建立畫布元件
        self.canvas.fill(QColor('#ffffff'))    # 預設填滿白色
        self.label = QtWidgets.QLabel(self)    # 建立 QLabel 元件，作為顯示圖片使用
        self.label.setGeometry(0, 0, 360, 360) # 設定位置和尺寸
        self.label.setPixmap(self.canvas)      # 放入畫布元件

        self.mbox = QtWidgets.QMessageBox(self)        # 建立對話視窗元件

        self.btn_open = QtWidgets.QPushButton(self)    # 開啟圖片按鈕
        self.btn_open.setText('開啟圖片')
        self.btn_open.setGeometry(400, 10, 100, 30)
        self.btn_open.clicked.connect(self.newFile)

        self.btn_save = QtWidgets.QPushButton(self)    # 另存圖片按鈕
        self.btn_save.setText('另存圖片')
        self.btn_save.setGeometry(400, 40, 100, 30)
        self.btn_save.clicked.connect(self.saveFile)

        self.btn_reset = QtWidgets.QPushButton(self)    # 重設數值按鈕
        self.btn_reset.setText('重設數值')
        self.btn_reset.setGeometry(400, 290, 100, 30)
        self.btn_reset.clicked.connect(self.resetVal)

        self.btn_close = QtWidgets.QPushButton(self)    # 關閉視窗按鈕
        self.btn_close.setText('關閉')
        self.btn_close.setGeometry(400, 320, 100, 30)
        self.btn_close.clicked.connect(self.closeFile)

    # 調整數值滑桿
    def adjustUi(self):
        self.label_adj_1 = QtWidgets.QLabel(self)       # 調整亮度說明文字
        self.label_adj_1.setGeometry(400, 80, 100, 30)
        self.label_adj_1.setText('調整亮度')
        self.label_adj_1.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label_val_1 = QtWidgets.QLabel(self)       # 調整亮度數值
        self.label_val_1.setGeometry(500, 100, 40, 30)
        self.label_val_1.setText('0')
        self.label_val_1.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.slider_1 = QtWidgets.QSlider(self)         # 調整亮度滑桿
        self.slider_1.setOrientation(Qt.Orientation.Horizontal)
        self.slider_1.setGeometry(400,100,100,30)
        self.slider_1.setRange(-100, 100)
        self.slider_1.setValue(0)
        self.slider_1.valueChanged.connect(self.showImage)

        self.label_adj_2 = QtWidgets.QLabel(self)       # 調整對比說明文字
        self.label_adj_2.setGeometry(400, 130, 100, 30)
        self.label_adj_2.setText('調整對比')
        self.label_adj_2.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label_val_2 = QtWidgets.QLabel(self)       # 調整對比數值
        self.label_val_2.setGeometry(500, 150, 40, 30)
        self.label_val_2.setText('0')
        self.label_val_2.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.slider_2 = QtWidgets.QSlider(self)         # 調整對比滑桿
        self.slider_2.setOrientation(Qt.Orientation.Horizontal)
        self.slider_2.setGeometry(400,150,100,30)
        self.slider_2.setRange(-100, 100)
        self.slider_2.setValue(0)
        self.slider_2.valueChanged.connect(self.showImage)

        self.label_adj_3 = QtWidgets.QLabel(self)       # 調整飽和度說明文字
        self.label_adj_3.setGeometry(400, 180, 100, 30)
        self.label_adj_3.setText('調整飽和度')
        self.label_adj_3.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label_val_3 = QtWidgets.QLabel(self)       # 調整飽和度數值
        self.label_val_3.setGeometry(500, 200, 40, 30)
        self.label_val_3.setText('0')
        self.label_val_3.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.slider_3 = QtWidgets.QSlider(self)         # 調整飽和度滑桿
        self.slider_3.setOrientation(Qt.Orientation.Horizontal)
        self.slider_3.setGeometry(400,200,100,30)
        self.slider_3.setRange(-100, 100)
        self.slider_3.setValue(0)
        self.slider_3.valueChanged.connect(self.showImage)

        self.label_adj_4 = QtWidgets.QLabel(self)       # 調整銳利度說明文字
        self.label_adj_4.setGeometry(400, 230, 100, 30)
        self.label_adj_4.setText('調整銳利度')
        self.label_adj_4.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label_val_4 = QtWidgets.QLabel(self)       # 調整銳利度數值
        self.label_val_4.setGeometry(500, 250, 40, 30)
        self.label_val_4.setText('0')

        self.slider_4 = QtWidgets.QSlider(self)         # 調整銳利度滑桿
        self.slider_4.setOrientation(Qt.Orientation.Horizontal)
        self.slider_4.setGeometry(400,250,100,30)
        self.slider_4.setRange(-100, 100)
        self.slider_4.setValue(0)
        self.slider_4.valueChanged.connect(self.showImage)

    # 開新圖片
    def newFile(self):
        global output      # 建立一個全域變數，在不同視窗之間傳遞圖片資訊
        filePath , filetype = QtWidgets.QFileDialog.getOpenFileName(filter='IMAGE(*.jpg *.png *.gif)')
        if filePath:
            # 如果選擇檔案，彈出視窗詢問是否開啟
            ret = self.mbox.question(self, 'question', '確定開新檔案？')
            # 如果確定開啟
            if ret == self.mbox.StandardButton.Yes:
                self.img = Image.open(filePath)                 # 使用 Pillow Image 開啟
                output = self.img                               # 紀錄圖片資訊
                qimg = ImageQt.toqimage(self.img)               # 轉換成 Qpixmap 格式
                self.canvas = QPixmap(360,360).fromImage(qimg)  # 顯示在畫布中
                self.label.setPixmap(self.canvas)               # 重設畫布內容
                self.update()                                   # 更新視窗
            else:
                return

    # 關閉
    def closeFile(self):
        ret = self.mbox.question(self, 'question', '確定關閉視窗？')
        if ret == self.mbox.StandardButton.Yes:
            app.quit()            # 如果點擊 yes，關閉視窗
        else:
            return

    # 重設
    def resetVal(self):
        self.slider_1.setValue(0)        # 滑桿預設值 0
        self.slider_2.setValue(0)        # 滑桿預設值 0
        self.slider_3.setValue(0)        # 滑桿預設值 0
        self.slider_4.setValue(0)        # 滑桿預設值 0
        self.label_val_1.setText('0')    # 滑桿數值顯示 0
        self.label_val_2.setText('0')    # 滑桿數值顯示 0
        self.label_val_3.setText('0')    # 滑桿數值顯示 0
        self.label_val_4.setText('0')    # 滑桿數值顯示 0
        qimg = ImageQt.toqimage(self.img)               # 圖片顯示 self.img 內容
        self.canvas = QPixmap(360,360).fromImage(qimg)  # 更新畫布內容
        self.label.setPixmap(self.canvas)               # 重設畫布
        self.update()                                   # 更新視窗

    # 調整並顯示圖片
    def showImage(self):
        global output
        # 如果已經開啟圖片
        if self.img != False:
            val1 = self.slider_1.value()         # 取得滑桿數值
            val2 = self.slider_2.value()         # 取得滑桿數值
            val3 = self.slider_3.value()         # 取得滑桿數值
            val4 = self.slider_4.value()         # 取得滑桿數值
            self.label_val_1.setText(str(val1))  # 顯示滑桿數值
            self.label_val_2.setText(str(val2))  # 顯示滑桿數值
            self.label_val_3.setText(str(val3))  # 顯示滑桿數值
            self.label_val_4.setText(str(val4))  # 顯示滑桿數值
            output = self.img.copy()                        # 複製 img 圖片 ( 避免更動原始圖片 )
            brightness = ImageEnhance.Brightness(output)    # 調整亮度
            output = brightness.enhance(1+int(val1)/100)    # 讀取滑桿數值並轉換成調整的數值
            contrast = ImageEnhance.Contrast(output)        # 調整對比
            output = contrast.enhance(1+int(val2)/100)      # 讀取滑桿數值並轉換成調整的數值
            color = ImageEnhance.Color(output)              # 調整飽和度
            output = color.enhance(1+int(val3)/100)         # 讀取滑桿數值並轉換成調整的數值
            sharpness = ImageEnhance.Sharpness(output)      # 調整銳利度
            output = sharpness.enhance(1+int(val4)/10)      # 讀取滑桿數值並轉換成調整的數值

            qimg = ImageQt.toqimage(output)                 # 圖片顯示 self.img 內容
            self.canvas = QPixmap(360,360).fromImage(qimg)  # 更新畫布內容
            self.label.setPixmap(self.canvas)               # 重設畫布
            self.update()                                   # 更新視窗

    def saveFile(self):
        self.nw = saveWindow()      # 連接新視窗
        self.nw.show()              # 顯示新視窗

class saveWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('選擇存檔格式')    # 新視窗標題
        self.resize(300, 180)                # 新視窗尺寸
        self.ui()

    def ui(self):
        self.label_size = QtWidgets.QLabel(self)     # 顯示尺寸縮放比例說明文字
        self.label_size.setGeometry(15, 10, 80, 30)
        self.label_size.setText('尺寸改變')

        self.imgsize =100                            # 預設圖片尺寸縮放比例

        self.box_size = QtWidgets.QSpinBox(self)     # 尺寸縮放調整元件
        self.box_size.setGeometry(15, 40, 60, 30)
        self.box_size.setRange(0,200)
        self.box_size.setValue(self.imgsize)
        self.box_size.valueChanged.connect(self.changeSize) # 串連調整函式

        self.label_format = QtWidgets.QLabel(self)   # 存檔格式說明文字
        self.label_format.setGeometry(100, 10, 100, 30)
        self.label_format.setText('儲存格式')

        self.format = 'JPG'                          # 預設格式

        self.box_format  = QtWidgets.QComboBox(self) # 下拉選單元件
        self.box_format.addItems(['JPG','PNG'])      # 兩個選項
        self.box_format.setGeometry(90,40,100,30)
        self.box_format.currentIndexChanged.connect(self.changeFormat) # 串連改變時的程式

        self.label_jpg = QtWidgets.QLabel(self)      # 壓縮品質說明文字
        self.label_jpg.setGeometry(100, 70, 100, 30)
        self.label_jpg.setText('JPG 壓縮品質')

        self.val = 75                                # 預設 JPG 壓縮品質

        self.label_jpg_val = QtWidgets.QLabel(self)  # 壓縮品質數值
        self.label_jpg_val.setGeometry(190, 100, 100, 30)
        self.label_jpg_val.setText(str(self.val))

        self.slider = QtWidgets.QSlider(self)        # 壓縮品質調整滑桿
        self.slider.setOrientation(Qt.Orientation.Horizontal)                # 水平顯示
        self.slider.setGeometry(100,100,80,30)
        self.slider.setRange(0, 100)                 # 數值範圍
        self.slider.setValue(self.val)               # 預設值
        self.slider.valueChanged.connect(self.changeVal)  # 串連改變時的函式

        self.btn_ok = QtWidgets.QPushButton(self)    # 確定儲存按鈕
        self.btn_ok.setText('確定儲存')
        self.btn_ok.setGeometry(200, 10, 90, 30)
        self.btn_ok.clicked.connect(self.saveImage)  # 串連儲存函式

        self.btn_cancel = QtWidgets.QPushButton(self)  # 取消儲存按鈕
        self.btn_cancel.setText('取消')
        self.btn_cancel.setGeometry(200, 40, 90, 30)
        self.btn_cancel.clicked.connect(self.closeWindow)  # 串連關閉視窗函式

    # 改變尺寸
    def changeSize(self):
        self.imgsize = self.box_size.value()         # 取得改變的數值

    # 改變格式
    def changeFormat(self):
        self.format = self.box_format.currentText()  # 顯示目前格式
        if self.format == 'JPG':
            self.label_jpg.setDisabled(False)        # 如果是 JPG，啟用 JPG 壓縮品質調整相關元件
            self.label_jpg_val.setDisabled(False)
            self.slider.setDisabled(False)
        else:
            self.label_jpg.setDisabled(True)        # 如果是 JPG，停用 JPG 壓縮品質調整相關元件
            self.label_jpg_val.setDisabled(True)
            self.slider.setDisabled(True)

    # 改變數值
    def changeVal(self):
        self.val = self.slider.value()              # 取得滑桿數值
        self.label_jpg_val.setText(str(self.slider.value()))

    # 存檔
    def saveImage(self):
        global output
        if self.format == 'JPG':
            filePath, filterType = QtWidgets.QFileDialog.getSaveFileName(filter='JPG(*.jpg)')
            if filePath:
                nw = int ( output.size[0] * self.imgsize/100 )    # 根據縮放比例調整大小
                nh = int ( output.size[1] * self.imgsize/100 )
                img2 = output.resize((nw, nh))                    # 調整大小
                img2.save(filePath, quality=self.val, subsampling=0)  # JPG 存檔
                self.close()
        else:
            filePath, filterType = QtWidgets.QFileDialog.getSaveFileName(filter='PNG(*.png)')
            if filePath:
                nw = int ( output.size[0] * self.imgsize/100 )    # 根據縮放比例調整大小
                nh = int ( output.size[1] * self.imgsize/100 )
                img2 = output.resize((nw, nh))                    # 調整大小
                img2.save(filePath, 'png')                        # PNG 存檔
                self.close()

    def closeWindow(self):
        self.close()

# 主程式開始
while True:
    print()
    print("(1)批量壓縮圖片")  
    print("(2)加入浮水印")
    print("(3)反向搜圖")
    print("(4)圖片切割成四等分")
    print("(5)色彩調整")
    print()
    func = input("請輸入要執行的功能:")

    # 批量壓縮圖片
    if func == '1':
        input_folder = 'C:\\Users\\USER\\Desktop\\side_project\\compress_pictures'  
        output_folder = 'C:\\Users\\USER\\Desktop\\side_project\\compress_pictures2'
        size_limit_mb = float(input("要壓縮成幾mb以下?")) 

        process_images(input_folder, output_folder, size_limit_mb=size_limit_mb)

    elif func == "2":
        while True:
            # 開啟圖片和浮水印
            img = Image.open("C:\\Users\\USER\\Desktop\\side_project\\Final_project\\watermark-photo.jpg")
            icon = Image.open("C:\\Users\\USER\\Desktop\\side_project\\Final_project\\watermark-icon.png")

            # 讓使用者選擇浮水印的位置
            position = input("請選擇浮水印的放置位置 (1左上, 2中上, 3右上, 4中左, 5中間, 6中右, 7左下, 8中下, 9右下): ")

            # 計算浮水印位置並將其貼上
            pos = watermark_position(img, icon, position)
            img.paste(icon, pos, icon)

            # 顯示圖片
            img.show()

            #使用者若滿意再儲存
            OK_OR_not = input("儲存或是重新添加浮水印(1:儲存/任意鍵:重新添加)")
            if OK_OR_not == "1":
                save_path = 'C:\\Users\\USER\\Desktop\\side_project\\compress_pictures2\\saved_image.png'
                img.save( save_path, format='PNG')
                print("成功儲存")
                break

    # #反向搜尋
    # elif func == "3":
    #     # API
    #     os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "C:\\Users\\USER\\Desktop\\side_project\\Final_project\\dht11-a6a14-494f2d021ac0.json"

    #     # 初始化客戶端
    #     client = vision.ImageAnnotatorClient()

    #     # 載入圖片
    #     file_name = "C:\\Users\\USER\\Desktop\\side_project\\Final_project\\button_Resize Image_Resize Image.png"
    #     with io.open(file_name, 'rb') as image_file:
    #         content = image_file.read()

    #     image = vision.Image(content=content)

    #     # 執行反向圖片搜索
    #     response = client.web_detection(image=image)
    #     web_detection = response.web_detection

    #     if web_detection.pages_with_matching_images:
    #         print('找到匹配的網頁：')
    #         for page in web_detection.pages_with_matching_images:
    #             print(page.url)

    #切割四等分
    
    elif func == "4":
        input_image_path = "C:\\Users\\USER\\Desktop\\side_project\\Final_project\\watermark-photo.jpg"
        output_folder = 'C:\\Users\\USER\\Desktop\\side_project\\compress_pictures2'
        split_image_into_four(input_image_path, output_folder)

    #色彩調整
    elif func == "5":
        if __name__ == '__main__':
            app = QtWidgets.QApplication(sys.argv)
            Form = MyWidget()
            Form.show()
            sys.exit(app.exec())


