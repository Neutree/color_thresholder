#
# =======================================================
# color threshold picker
# @author neucrack
# @license MIT
# @date 2020.06.13
#
# =======================================================
#

from PyQt5.QtCore import pyqtSignal,Qt, QLibraryInfo
from PyQt5.QtWidgets import (QApplication, QWidget,QToolTip,QPushButton,QMessageBox,QDesktopWidget,QMainWindow,
                             QVBoxLayout,QHBoxLayout,QGridLayout,QTextEdit,QLabel,QRadioButton,QCheckBox,
                             QLineEdit,QGroupBox,QSplitter,QFileDialog, QScrollArea, QSlider, QFrame)
from PyQt5.QtGui import QIcon,QFont,QTextCursor,QPixmap, QImage
import sys, os
import re
import cv2
import numpy as np
import ctypes

os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = QLibraryInfo.location(
    QLibraryInfo.PluginsPath
)


class MainWindow(QMainWindow):
    DataPath = os.path.abspath(os.path.dirname(__file__))
    app = None

    def __init__(self,app):
        super().__init__()
        self.app = app
        self.loadConfig()
        self.DataPath = os.path.abspath(os.path.join(os.path.dirname(__file__), "assets"))
        self.labValueEventSet = False
        self.imgs = []
        self.imgsWidgets = []
        self.initWindow()
        self.initEvent()

    def loadConfig(self):
        self.picWidth = 320
        self.picHeight = 240

    def initWindow(self):
        # main layout
        frameWidget = QWidget()
        frameLayout = QHBoxLayout()
        scroll = QScrollArea()
        self.picWiget = QFrame(scroll)
        self.picLayout = QGridLayout()
        self.picWiget.setLayout(self.picLayout)
        scroll.setWidget(self.picWiget)
        scroll.setWidgetResizable(True)
        controlLayout = QVBoxLayout()
        self.picShowSize = QLineEdit("320, 240")
        self.folderPath = QLineEdit()
        self.folderSelectBtn = QPushButton("Select folder")
        self.labSlider = []
        controlLayout.addWidget(self.picShowSize)
        controlLayout.addWidget(self.folderPath)
        controlLayout.addWidget(self.folderSelectBtn)
        checkBoxsLayout = QHBoxLayout()
        controlLayout.addLayout(checkBoxsLayout)
        self.slideApplyCheckbox = QCheckBox("Slide Apply")
        self.slideApplyCheckbox.setChecked(True)
        checkBoxsLayout.addWidget(self.slideApplyCheckbox)
        self.labSliderLimit = ( (0, 100), (0, 100), (-128, 127), (-128, 127), (-128, 127), (-128, 127))
        for i in range(6):
            slider = QSlider(Qt.Horizontal)
            controlLayout.addWidget(slider)
            slider.setMinimum(self.labSliderLimit[i][0])
            slider.setMaximum(self.labSliderLimit[i][1])
            if i%2 == 0:
                slider.setValue(self.labSliderLimit[i][0])
            else:
                slider.setValue(self.labSliderLimit[i][1])
            slider.setTickPosition(QSlider.TicksBelow)
            self.labSlider.append(slider)
        self.labValue = QLineEdit("(0, 100, -128, 127, -128, 127)")
        controlLayout.addWidget(self.labValue)
        self.showOriginalBtn = QPushButton("Show original")
        controlLayout.addWidget(self.showOriginalBtn)
        frameLayout.addWidget(scroll)
        frameLayout.addLayout(controlLayout)
        frameWidget.setLayout(frameLayout)
        self.setCentralWidget(frameWidget)

        frameLayout.setStretch(0,5)
        frameLayout.setStretch(1, 3)

        self.resize(1600, 900)
        self.show()

    def initEvent(self):
        for i in range(6):
            self.labSlider[i].valueChanged.connect(self.onSliderChangedBySlide)
            self.labSlider[i].sliderReleased.connect(self.onSliderChangedByMouseRelease)
        self.setLabValueEvent(True)
        self.folderSelectBtn.clicked.connect(self.onSlectFolder)

        self.picShowSize.textChanged.connect(self.onPicShowSizeChanged)
        self.showOriginalBtn.pressed.connect(self.showOriginal)
        self.showOriginalBtn.released.connect(self.showLab)

    def setLabValueEvent(self, enable):
        if not enable:
            if self.labValueEventSet:
                self.labValue.textChanged.disconnect(self.onLabValueChanged)
                self.labValueEventSet = False
        else:
            if not self.labValueEventSet:
                self.labValueEventSet = True
                self.labValue.textChanged.connect(self.onLabValueChanged)
    def onPicShowSizeChanged(self):
        text = self.picShowSize.text()
        v = re.findall(r'[-+]?\d+', text)
        if len(v) == 2:
            self.picWidth  = int(v[0])
            self.picHeight = int(v[1])

    def onSliderChanged(self):
        if not self.labValueEventSet: # label is editing
            return
        v = []
        for i in range(6):
            v.append(self.labSlider[i].value())
        self.setLabValueEvent(False)
        self.labValue.setText("({}, {}, {}, {}, {}, {})".format(v[0], v[1], v[2], v[3], v[4], v[5]))
        self.updateImgs()
        self.setLabValueEvent(True)
    
    def onSliderChangedBySlide(self):
        if self.slideApplyCheckbox.isChecked():
            self.onSliderChanged()
    
    def onSliderChangedByMouseRelease(self):
        if not self.slideApplyCheckbox.isChecked():
            self.onSliderChanged()

    def onLabValueChanged(self):
        text = self.labValue.text()
        v = re.findall(r'[-+]?\d+', text)
        self.setLabValueEvent(False)
        if len(v) == 6:
            for i in range(6):
                try:
                    v[i] = int(v[i])
                except Exception:
                    break
                if v[i] < self.labSliderLimit[i][0]:
                    v[i] = self.labSliderLimit[i][0]
                elif v[i] > self.labSliderLimit[i][1]:
                    v[i] = self.labSliderLimit[i][1]
                self.labSlider[i].setValue(v[i])
        self.updateImgs()
        self.setLabValueEvent(True)
    
    def onSlectFolder(self):
        oldPath = self.folderPath.text()
        if not os.path.isdir(oldPath):
            oldPath = None
        directory = QFileDialog.getExistingDirectory(self,  
                            "SelectFolder",
                            oldPath)
        if os.path.isdir(directory):
            self.folderPath.setText(directory)
            files = os.listdir(directory)
            # for i in range(self.picLayout.count()):
            #     w = self.picLayout.itemAt(i).widget()
            for w in self.imgsWidgets:
                w.setParent(None)
            count = 0
            self.imgs = []
            self.imgsWidgets = []
            for f in files:
                f_path = os.path.join(directory, f)
                if os.path.isfile(f_path) and (f.endswith(".jpg") or f.endswith(".jpeg") or f.endswith(".png") or f.endswith(".bmp")):
                    img = cv2.imdecode(np.fromfile(f_path,dtype=np.uint8),cv2.IMREAD_COLOR)
                    img = cv2.resize(img, (self.picWidth, self.picHeight))
                    self.imgs.append(img)
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    qtImg = QImage( img.data, 
                                    img.shape[1], 
                                    img.shape[0],
                                    img.shape[1]*3,
                                    QImage.Format_RGB888)
                    pixmap = QPixmap(QPixmap.fromImage(qtImg))
                    label = QLabel()
                    label.setPixmap(pixmap)
                    self.picLayout.addWidget(label, count/3, count%3, 1, 1 )
                    self.imgsWidgets.append(label)
                    count += 1

    def updateImgs(self):
        text = self.labValue.text()
        v = re.findall(r'[-+]?\d+', text)
        if len(v) == 6:
            for i, img in enumerate(self.imgs):
                ## way 1
                l_range = [int(v[0])*255//100, int(v[1])*255//100]
                a_range = [int(v[2])+128, int(v[3])+128]
                b_range = [int(v[4])+128, int(v[5])+128]
                lab = cv2.cvtColor(img,cv2.COLOR_BGR2LAB)
                l, a, b = cv2.split(lab)
                out = np.ndarray([img.shape[0]*img.shape[1]], dtype=np.uint8)
                thresholds = np.array([l_range[0], l_range[1], a_range[0], a_range[1], b_range[0], b_range[1]], dtype=np.uint8)
                # for y in range(lab.shape[0]):
                #     for x in range(lab.shape[1]):
                #         lmin_ok = l[y][x] >= min(l_range[0], l_range[1])
                #         lmax_ok = l[y][x] <= max(l_range[0], l_range[1])
                #         amin_ok = a[y][x] >= min(a_range[0], a_range[1])
                #         amax_ok = a[y][x] <= max(a_range[0], a_range[1])
                #         bmin_ok = b[y][x] >= min(b_range[0], b_range[1])
                #         bmax_ok = b[y][x] <= max(b_range[0], b_range[1])
                #         ok = (lmin_ok and lmax_ok and amin_ok and amax_ok and bmin_ok and bmax_ok) ^ 0
                #         out[y][x] = 0xff if ok else 0x00
                l = np.ravel(l)
                a = np.ravel(a)
                b = np.ravel(b)
                c_uint8_p = ctypes.POINTER(ctypes.c_uint8)
                out_p = out.ctypes.data_as(c_uint8_p)
                l_p = l.ctypes.data_as(c_uint8_p)
                a_p = a.ctypes.data_as(c_uint8_p)
                b_p = b.ctypes.data_as(c_uint8_p)
                b_p = b.ctypes.data_as(c_uint8_p)
                ths_p = thresholds.ctypes.data_as(c_uint8_p)
                if sys.platform == 'win32':
                    dl_path = "c_lib_win.so"
                elif sys.platform == "linux":
                    dl_path = "c_lib.so"
                else:
                    print("platform not support")
                    break
                lib = ctypes.cdll.LoadLibrary(os.path.join(os.path.dirname(os.path.abspath(__file__)), dl_path))
                ret = lib.lab_threshold(l_p, a_p, b_p, out_p, img.shape[1], img.shape[0], ths_p, ctypes.c_bool(False))
                img = out.reshape((img.shape[0], img.shape[1]))
                qtImg = QImage( img.data, 
                                img.shape[1], 
                                img.shape[0],
                                img.shape[1],
                                QImage.Format_Grayscale8)
                pixmap = QPixmap(QPixmap.fromImage(qtImg))
                self.imgsWidgets[i].setPixmap(pixmap)
    
    def showOriginal(self):
        for i, img in enumerate(self.imgs):
            img = cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
            qtImg = QImage( img.data, 
                            img.shape[1], 
                            img.shape[0],
                            img.shape[1]*3,
                            QImage.Format_RGB888)
            pixmap = QPixmap(QPixmap.fromImage(qtImg))
            self.imgsWidgets[i].setPixmap(pixmap)

    def showLab(self):
        self.onLabValueChanged()



def main():
    app = QApplication(sys.argv)
    mainWindow = MainWindow(app)
    file = open(mainWindow.DataPath + '/qss/style-dark.qss', "r")
    qss = file.read().replace("$DataPath",mainWindow.DataPath)
    app.setStyleSheet(qss)
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

