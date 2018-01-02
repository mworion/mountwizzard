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
import logging
from baseclasses.camera import MWCamera
import indi.indi_xml as indiXML
import PyQt5


class INDICamera(MWCamera):
    logger = logging.getLogger(__name__)                                                                                    # logging enabling

    def __init__(self, app):
        self.app = app
        self.appRunning = False
        self.cameraConnected = False
        self.cameraStatus = ''
        self.appInstallPath = ''
        self.appAvailable = False
        self.appName = 'INDI Camera'
        self.appExe = ''
        self.tryConnectionCounter = 0
        self.imagingStarted = False
        self.checkAppInstall()

    def checkAppInstall(self):
        self.appAvailable = False

    def checkAppStatus(self):
        if self.app.INDIworker.connected:
            self.tryConnectionCounter = 0
            self.appRunning = True
        else:
            self.tryConnectionCounter += 1
            self.appRunning = False
            self.cameraConnected = False
            if self.tryConnectionCounter < 3:
                self.logger.warning('{0} is not running'.format(self.appName))
            elif self.tryConnectionCounter == 3:
                self.logger.error('No connection to {0} possible - stop logging this connection error'.format(self.appName))

    def connectCamera(self):
        if self.appRunning and self.app.INDIworker.driverNameCCD != '':
            self.app.INDISendCommandQueue.put(indiXML.newSwitchVector([indiXML.oneSwitch('On', indi_attr={'name': 'CONNECT'})], indi_attr={'name': 'CONNECTION', 'device': self.app.INDIworker.driverNameCCD}))

    def disconnectCamera(self):
        if self.cameraConnected:
            self.app.INDISendCommandQueue.put(indiXML.newSwitchVector([indiXML.oneSwitch('Off', indi_attr={'name': 'CONNECT'})], indi_attr={'name': 'CONNECTION', 'device': self.app.INDIworker.driverNameCCD}))

    def getImage(self, modelData):
        binning = int(float(modelData['binning']))
        exposureLength = int(float(modelData['exposure']))
        speed = modelData['speed']
        filename = modelData['file']
        path = modelData['base_dir_images']
        imagePath = path + '/' + filename
        self.app.INDIworker.imagePath = imagePath
        if self.cameraConnected and self.app.INDIworker.driverNameCCD != '':
            self.app.INDIworker.receivedImage = False
            # Enable BLOB mode.
            self.app.INDISendCommandQueue.put(indiXML.enableBLOB('Also', indi_attr={'device': self.app.INDIworker.driverNameCCD}))
            # set to raw - no compression mode
            self.app.INDISendCommandQueue.put(indiXML.newSwitchVector([indiXML.oneSwitch('On', indi_attr={'name': 'CCD_RAW'})], indi_attr={'name': 'CCD_COMPRESSION', 'device': self.app.INDIworker.driverNameCCD}))
            # set frame type
            self.app.INDISendCommandQueue.put(indiXML.newSwitchVector([indiXML.oneSwitch('On', indi_attr={'name': 'FRAME_LIGHT'})], indi_attr={'name': 'CCD_FRAME_TYPE', 'device': self.app.INDIworker.driverNameCCD}))
            # set binning
            self.app.INDISendCommandQueue.put(indiXML.newNumberVector([indiXML.oneNumber(binning, indi_attr={'name': 'HOR_BIN'}), indiXML.oneNumber(binning, indi_attr={'name': 'VER_BIN'})], indi_attr={'name': 'CCD_BINNING', 'device': self.app.INDIworker.driverNameCCD}))
            # Request image.
            self.app.INDISendCommandQueue.put(indiXML.newNumberVector([indiXML.oneNumber(exposureLength, indi_attr={'name': 'CCD_EXPOSURE_VALUE'})], indi_attr={'name': 'CCD_EXPOSURE', 'device': self.app.INDIworker.driverNameCCD}))
            self.imagingStarted = True
            while not self.app.INDIworker.receivedImage:
                PyQt5.QtWidgets.QApplication.processEvents()
        modelData['imagepath'] = self.app.INDIworker.imagePath
        return True, 'OK', modelData

    def solveImage(self, modelData):
        pass

    def getCameraProps(self):
        if self.cameraConnected and self.app.INDIworker.driverNameCCD != '':
            sizeX = self.app.INDIworker.device[self.app.INDIworker.driverNameCCD]['CCD_INFO']['CCD_MAX_X']
            sizeY = self.app.INDIworker.device[self.app.INDIworker.driverNameCCD]['CCD_INFO']['CCD_MAX_Y']
            return True, 'OK', sizeX, sizeY, False, 'High'
        else:
            return False, 'Camera not connected', 0, 0, False, ''

    def getCameraStatus(self):
        if self.appRunning and self.app.INDIworker.driverNameCCD != '':
            if self.app.INDIworker.device[self.app.INDIworker.driverNameCCD]['CONNECTION']['CONNECT'] == 'On':
                self.cameraConnected = True
            else:
                self.cameraConnected = False
                self.cameraStatus = 'DISCONNECTED'
            if self.cameraConnected:
                if float(self.app.INDIworker.device[self.app.INDIworker.driverNameCCD]['CCD_EXPOSURE']['CCD_EXPOSURE_VALUE']):
                    self.cameraStatus = 'INTEGRATING'
                else:
                    self.cameraStatus = 'READY - IDLE'
        else:
            self.cameraStatus = 'ERROR'
            self.cameraConnected = False
        self.app.INDIDataQueue.put({'Name': 'CameraStatus', 'value': self.cameraStatus})
