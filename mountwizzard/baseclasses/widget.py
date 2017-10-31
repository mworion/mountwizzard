############################################################
# -*- coding: utf-8 -*-
#
# Python-based Tool for interaction with the 10micron mounts
# GUI with PyQT5 for python
# Python  v3.5
#
# Michael Würtenberger
# (c) 2016, 2017
#
# Licence APL2.0
#
############################################################
import platform
import logging
import os
import sys

# import for the PyQt5 Framework
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *


class MwWidget(QWidget):

    logger = logging.getLogger(__name__)
    BLUE = 'background-color: rgb(42, 130, 218);'
    RED = 'background-color: red;'
    DEFAULT = 'background-color: rgb(32,32,32); color: rgb(192,192,192)'
    COLOR_ASTRO = QColor(32, 144, 192)  # blue astro color
    COLOR_BLUE = QColor(0, 0, 255)
    COLOR_YELLOW = QColor(192, 192, 0)
    COLOR_GREEN = QColor(0, 255, 0)
    COLOR_GREEN_HORIZON = QColor(0, 64, 0)
    COLOR_GREEN_HORIZON_DARK = QColor(0, 32, 0)
    COLOR_WHITE = QColor(255, 255, 255)
    COLOR_RED = QColor(255, 0, 0)
    COLOR_BLACK = QColor(0, 0, 0)
    COLOR_POINTER = QColor(255, 0, 255)
    COLOR_TRACKWIDGETTEXT = QColor(255, 255, 255)
    COLOR_TRACKWIDGETPOINTS = QColor(128, 128, 128)
    COLOR_WINDOW = QColor(32, 32, 32)
    COLOR_WINDOW_TEXT = QColor(192, 192, 192)
    COLOR_BACKGROUND = QColor(53, 53, 53)
    COLOR_BASE = QColor(25, 25, 25)
    COLOR_ALTERNATE_BASE = QColor(53, 53, 53)
    COLOR_HIGHLIGHT = QColor(42, 130, 218)

    def __init__(self):
        # noinspection PyArgumentList
        super(MwWidget, self).__init__()                                                                                    # Initialize Class for UI
        self.palette = QPalette()                                                                                           # title text
        self.moving = False                                                                                                 # check if window moves with mouse pointer
        self.offset = None                                                                                                  # check offset from mouse pick point to window 0,0 reference point
        self.modifiers = None
        self.showStatus = False
        self.initUI()                                                                                                       # adapt the window to our purpose

    def closeEvent(self, closeEvent):
        self.showStatus = False

    def initUI(self):
        # self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.setWindowFlags((self.windowFlags() | Qt.CustomizeWindowHint) & ~Qt.WindowMaximizeButtonHint)
        self.setMouseTracking(True)
        if platform.system() == 'Windows' or platform.system() == 'Linux':
            darkPalette = QPalette()
            darkPalette.setColor(QPalette.Window, self.COLOR_WINDOW)
            darkPalette.setColor(QPalette.WindowText, self.COLOR_WINDOW_TEXT)
            darkPalette.setColor(QPalette.Base, self.COLOR_BASE)
            darkPalette.setColor(QPalette.AlternateBase, self.COLOR_ALTERNATE_BASE)
            darkPalette.setColor(QPalette.ToolTipBase, self.COLOR_WHITE)
            darkPalette.setColor(QPalette.ToolTipText, self.COLOR_WHITE)
            darkPalette.setColor(QPalette.Text, self.COLOR_ASTRO)
            darkPalette.setColor(QPalette.Button, self.COLOR_BASE)
            darkPalette.setColor(QPalette.ButtonText, self.COLOR_WINDOW_TEXT)
            darkPalette.setColor(QPalette.BrightText, self.COLOR_RED)
            darkPalette.setColor(QPalette.Highlight, self.COLOR_HIGHLIGHT)
            darkPalette.setColor(QPalette.HighlightedText, self.COLOR_BLACK)
            self.setPalette(darkPalette)
            self.palette.setColor(QPalette.Foreground, self.COLOR_ASTRO)
            self.palette.setColor(QPalette.Background, self.COLOR_BACKGROUND)
        # sizing in gui should be fixed, because I have a static layout
        self.setFixedSize(790, 640)
        # set app icon
        if getattr(sys, 'frozen', False):
            # we are running in a bundle
            bundle_dir = sys._MEIPASS
        else:
            # we are running in a normal Python environment
            bundle_dir = os.path.dirname(sys.modules['__main__'].__file__)
        self.setWindowIcon(QIcon(bundle_dir + '\\mw.ico'))
