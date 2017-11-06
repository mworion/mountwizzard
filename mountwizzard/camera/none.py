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

# import basic stuff
import logging

from baseclasses.camera import MWCamera


class NoneCamera(MWCamera):
    logger = logging.getLogger(__name__)

    def __init__(self, app):
        super(NoneCamera, self).__init__(app)
        self.checkAppInstall()

    def checkAppInstall(self):
        self.appAvailable = True

    def checkAppStatus(self):
        self.appRunning = False
        self.cameraConnected = False

    def getImage(self, modelData):
        return False, 'DISCONNECTED', modelData

    def getCameraProps(self):
        suc = True
        mes = 'OK'
        canSubframe = False
        gains = ''
        sizeX = 1
        sizeY = 1
        return suc, mes, sizeX, sizeY, canSubframe, gains

    def getCameraStatus(self):
        self.cameraStatus = 'DISCONNECTED'

    def solveImage(self, modelData):
        return False, 'ERROR', modelData
