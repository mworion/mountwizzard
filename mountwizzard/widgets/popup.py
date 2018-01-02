############################################################
# -*- coding: utf-8 -*-
#
# Python-based Tool for interaction with the 10micron mounts
# GUI with PyQT5 for python
# Python  v3.5
#
# Michael Würtenberger
# (c) 2016, 2017, 2018
#
# Licence APL2.0
#
############################################################


# matplotlib
import matplotlib
from PyQt5.QtCore import *
# import for the PyQt5 Framework
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from widgets import popup_dialog_ui

matplotlib.use('Qt5Agg')
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


class xMplCanvas(FigureCanvas):

    def __init__(self, parent=None, xval=None, yval=None, titel=None):
        self.fig = plt.figure(dpi=75)
        rect = self.fig.patch
        rect.set_facecolor((25/256, 25/256, 25/256))
        self.axes = self.fig.add_subplot(111)
        self.axes.grid(True, color='white')
        # We want the axes cleared every time plot() is called
        # self.axes.hold(False)
        self.axes.set_axis_bgcolor((48/256, 48/256, 48/256))
        self.axes.tick_params(axis='x', colors='white')
        self.axes.tick_params(axis='y', colors='white')
        plt.rcParams['toolbar'] = 'None'
        plt.rcParams['axes.titlesize'] = 'large'
        plt.rcParams['axes.labelsize'] = 'medium'
        plt.tight_layout(rect=[0.1, 0.1, 0.95, 0.95])
        self.compute_initial_figure()
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        FigureCanvas.updateGeometry(self)

    def compute_initial_figure(self):
        pass


class PopupData(xMplCanvas):

    def compute_initial_figure(self):
        plt.xlabel('DEC Error (arcsec)', color='white')
        plt.ylabel('Altitude (degree)', color='white')
        plt.title('Altitude over Declination Error', color='white')
        self.axes.plot()


class MyPopup(QWidget):
    def __init__(self, ):
        QWidget.__init__(self)
        self.moving = False
        self.offset = None
        self.ui = popup_dialog_ui.Ui_PopupDialog()
        self.ui.setupUi(self)
        self.initUI()
        #self.setGeometry(QRect(100, 100, 600, 600))
        l = QVBoxLayout(self.ui.widgetPlot)
        sc = PopupData(self.ui.widgetPlot)
        l.addWidget(sc)
        self.show()

    def mousePressEvent(self, mouseEvent):
        self.modifiers = mouseEvent.modifiers()
        if mouseEvent.button() == Qt.LeftButton:
            self.moving = True
            self.offset = mouseEvent.pos()

    def mouseMoveEvent(self, mouseEvent):
        if self.moving:
            cursor = QCursor()
            self.move(cursor.pos() - self.offset)

    def mouseReleaseEvent(self, mouseEvent):
        if self.moving:
            cursor = QCursor()
            self.move(cursor.pos() - self.offset)
            self.moving = False

    def initUI(self):
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.setMouseTracking(True)
        darkPalette = QPalette()
        darkPalette.setColor(QPalette.Window, QColor(32, 32, 32))
        darkPalette.setColor(QPalette.WindowText, QColor(192, 192, 192))
        darkPalette.setColor(QPalette.Base, QColor(25, 25, 25))
        darkPalette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        darkPalette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
        darkPalette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
        darkPalette.setColor(QPalette.Text, QColor(32, 144, 192))
        darkPalette.setColor(QPalette.Button, QColor(24, 24, 24))
        darkPalette.setColor(QPalette.ButtonText, QColor(192, 192, 192))
        darkPalette.setColor(QPalette.BrightText, QColor(255, 0, 0))
        darkPalette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        darkPalette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
        self.setPalette(darkPalette)
        palette = QPalette()
        palette.setColor(QPalette.Foreground, QColor(32, 144, 192))
        palette.setColor(QPalette.Background, QColor(53, 53, 53))
        self.ui.windowTitle.setPalette(palette)

