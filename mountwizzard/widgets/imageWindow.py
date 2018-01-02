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
# standard solutions
import logging
import os
import time

# import for the PyQt5 Framework
import PyQt5.QtWidgets
# numpy
import numpy
# FIT file handling
import pyfits
# matplotlib
from matplotlib import use

from baseclasses import widget
from gui import image_dialog_ui

use('Qt5Agg')
# when using multiple embedded plots in different windows you should use figure instead of pyplot, because the state
# machine from pyplot mixed multiple instances up.
from matplotlib import figure as figure
from matplotlib.colors import LogNorm, SymLogNorm, PowerNorm
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


class ShowImageData(FigureCanvas):

    def __init__(self, parent=None):
        self.fig = figure.Figure(dpi=75, frameon=True, facecolor=(25/256, 25/256, 25/256))
        self.axes = self.fig.add_axes([0., 0., 1., 1.])
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        FigureCanvas.updateGeometry(self)


class ImagesWindow(widget.MwWidget):
    logger = logging.getLogger(__name__)
    BASENAME = 'exposure-'

    def __init__(self, app):
        super(ImagesWindow, self).__init__()
        self.app = app
        self.showStatus = False
        self.sizeX = 10
        self.sizeY = 10
        self.imageVmin = 1
        self.imageVmax = 65535
        self.image = numpy.random.randint(low=5, high=100, size=(20, 20))
        self.cmapColor = 'gray'
        self.ui = image_dialog_ui.Ui_ImageDialog()                                                                          # PyQt5 dialog ui
        self.ui.setupUi(self)                                                                                               # setup the ui
        self.ui.btn_strechLow.setChecked(True)
        self.ui.btn_size100.setChecked(True)
        self.ui.btn_colorGrey.setChecked(True)
        self.initUI()                                                                                                       # adaptions to ui setup
        self.initConfig()
        helper = PyQt5.QtWidgets.QVBoxLayout(self.ui.image)
        self.imageWidget = ShowImageData(self.ui.image)
        helper.addWidget(self.imageWidget)
        self.imageWidget.axes.set_facecolor((25/256, 25/256, 25/256))
        self.imageWidget.axes.set_axis_off()
        self.ui.btn_expose.clicked.connect(self.exposeOnce)
        self.ui.btn_crosshair.clicked.connect(self.crosshairOnOff)
        self.ui.btn_colorGrey.clicked.connect(self.setColor)
        self.ui.btn_colorCool.clicked.connect(self.setColor)
        self.ui.btn_colorRainbow.clicked.connect(self.setColor)
        self.ui.btn_size25.clicked.connect(self.setZoom)
        self.ui.btn_size50.clicked.connect(self.setZoom)
        self.ui.btn_size100.clicked.connect(self.setZoom)
        self.ui.btn_strechLow.clicked.connect(self.setStrech)
        self.ui.btn_strechMid.clicked.connect(self.setStrech)
        self.ui.btn_strechHigh.clicked.connect(self.setStrech)
        # self.show()                                                                                                         # construct the window
        self.setVisible(False)
        self.ui.cross1.setVisible(False)
        self.ui.cross2.setVisible(False)
        self.ui.cross3.setVisible(False)
        self.ui.cross4.setVisible(False)

    def initConfig(self):
        try:
            if 'ImagePopupWindowPositionX' in self.app.config:
                self.move(self.app.config['ImagePopupWindowPositionX'], self.app.config['ImagePopupWindowPositionY'])
            if 'ImagePopupWindowShowStatus' in self.app.config:
                self.showStatus = self.app.config['ImagePopupWindowShowStatus']
        except Exception as e:
            self.logger.error('item in config.cfg not be initialize, error:{0}'.format(e))
        finally:
            pass

    def storeConfig(self):
        self.app.config['ImagePopupWindowPositionX'] = self.pos().x()
        self.app.config['ImagePopupWindowPositionY'] = self.pos().y()
        self.app.config['ImagePopupWindowShowStatus'] = self.showStatus

    def showImageWindow(self):
        self.showStatus = True
        self.setVisible(True)
        self.show()

    def setColor(self):
        if self.ui.btn_colorCool.isChecked():
            self.setColorCool()
        elif self.ui.btn_colorRainbow.isChecked():
            self.setColorRainbow()
        else:
            self.setColorGrey()
        self.setStrech()

    def setColorGrey(self):
        self.cmapColor = 'gray'

    def setColorCool(self):
        self.cmapColor = 'plasma'

    def setColorRainbow(self):
        self.cmapColor = 'rainbow'

    def setStrech(self):
        if self.ui.btn_strechLow.isChecked():
            self.strechLow()
        elif self.ui.btn_strechMid.isChecked():
            self.strechMid()
        else:
            self.strechHigh()

    def strechLow(self):
        image_new = self.loggray(self.image)
        self.imageVmin = numpy.min(image_new)
        self.imageVmax = numpy.max(image_new)
        self.imageWidget.axes.imshow(image_new, cmap=self.cmapColor, vmin=self.imageVmin, vmax=self.imageVmax)
        self.imageWidget.draw()

    def strechMid(self):
        image_new = self.loggray(self.image, a=numpy.min(self.image) * 1.25, b=numpy.max(self.image) * 0.8)
        self.imageVmin = numpy.min(image_new)
        self.imageVmax = numpy.max(image_new)
        self.imageWidget.axes.imshow(image_new, cmap=self.cmapColor, vmin=self.imageVmin, vmax=self.imageVmax)
        self.imageWidget.draw()

    def strechHigh(self):
        image_new = self.loggray(self.image, a=numpy.min(self.image) * 1.5, b=numpy.max(self.image) * 0.66)
        self.imageVmin = numpy.min(image_new)
        self.imageVmax = numpy.max(image_new)
        self.imageWidget.axes.imshow(image_new, cmap=self.cmapColor, vmin=self.imageVmin, vmax=self.imageVmax)
        self.imageWidget.draw()

    def loggray(self, x, a=None, b=None):
        """
        Auxiliary function that specifies the logarithmic gray scale.
        a and b are the cutoffs : if not specified, min and max are used
        """
        if not a:
            a = numpy.min(x)
        if not b:
            b = numpy.max(x)
        linval = 10.0 + 990.0 * (x - float(a)) / (b - a)
        return (numpy.log10(linval) - 1.0) * 0.5 * 255.0

    def setZoom(self):
        if self.ui.btn_size25.isChecked():
            self.zoom25()
        elif self.ui.btn_size50.isChecked():
            self.zoom50()
        else:
            self.zoom100()

    def zoom25(self):
        if self.sizeX:
            minx = int(self.sizeX * 3 / 8)
            maxx = minx + int(self.sizeX / 4)
            miny = int(self.sizeY * 3 / 8)
            maxy = miny + int(self.sizeY / 4)
            self.imageWidget.axes.set_xlim(xmin=minx, xmax=maxx)
            self.imageWidget.axes.set_ylim(ymin=miny, ymax=maxy)
            self.imageWidget.draw()

    def zoom50(self):
        if self.sizeX:
            minx = int(self.sizeX / 4)
            maxx = minx + int(self.sizeX / 2)
            miny = int(self.sizeY / 4)
            maxy = miny + int(self.sizeY / 2)
            self.imageWidget.axes.set_xlim(xmin=minx, xmax=maxx)
            self.imageWidget.axes.set_ylim(ymin=miny, ymax=maxy)
            self.imageWidget.draw()

    def zoom100(self):
        if self.sizeX:
            minx = 0
            maxx = self.sizeX
            miny = 0
            maxy = self.sizeY
            self.imageWidget.axes.set_xlim(xmin=minx, xmax=maxx)
            self.imageWidget.axes.set_ylim(ymin=miny, ymax=maxy)
            self.imageWidget.draw()

    def showFitsImage(self, filename):
        hdulist = pyfits.open(filename)
        self.image = hdulist[0].data
        self.sizeY, self.sizeX = self.image.shape
        self.setStrech()
        self.setZoom()

    def disableExposures(self):
        self.ui.btn_expose.setEnabled(False)
        self.ui.btn_startContExposures.setEnabled(False)
        self.ui.btn_stopContExposures.setEnabled(False)
        self.setWindowTitle('Image Window - Modeling running')

    def enableExposures(self):
        self.ui.btn_expose.setEnabled(True)
        self.ui.btn_startContExposures.setEnabled(True)
        self.ui.btn_stopContExposures.setEnabled(True)
        self.setWindowTitle('Image Window')

    def crosshairOnOff(self):
        if self.ui.cross1.isVisible():
            self.ui.cross1.setVisible(False)
            self.ui.cross2.setVisible(False)
            self.ui.cross3.setVisible(False)
            self.ui.cross4.setVisible(False)
        else:
            self.ui.cross1.setVisible(True)
            self.ui.cross2.setVisible(True)
            self.ui.cross3.setVisible(True)
            self.ui.cross4.setVisible(True)

    def exposeOnce(self):
        param = {'speed': 'HiSpeed',
                 'file': 'test.fit',
                 }
        suc, mes, sizeX, sizeY, canSubframe, gainValue = self.app.modeling.imagingHandler.getCameraProps()
        param['gainValue'] = gainValue
        param['binning'] = self.app.ui.cameraBin.value()
        param['exposure'] = self.app.ui.cameraExposure.value()
        param['iso'] = self.app.ui.isoSetting.value()
        directory = time.strftime("%Y-%m-%d-exposure", time.gmtime())
        param['base_dir_images'] = self.app.modeling.IMAGEDIR + '/' + directory
        if not os.path.isdir(param['base_dir_images']):
            os.makedirs(param['base_dir_images'])
        param = self.app.modeling.prepareCaptureImageSubframes(1, sizeX, sizeY, canSubframe, param)
        number = 0
        while os.path.isfile(param['base_dir_images'] + '/' + self.BASENAME + '{0:04d}.fit'.format(number)):
            number += 1
        param['file'] = self.BASENAME + '{0:04d}.fit'.format(number)
        suc, mes, param = self.app.modeling.imagingHandler.getImage(param)
        self.showFitsImage(param['imagepath'])
        '''
        self.showFitsImage('c:/temp/t2.fit')
        '''

    def exposeContinuous(self):
        pass

