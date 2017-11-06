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

import logging
import socket
import errno


class MWCamera:
    logger = logging.getLogger(__name__)                                                                                    # logging enabling

    def __init__(self, app):
        self.app = app
        self.appRunning = False
        self.cameraConnected = False
        self.cameraStatus = ''
        self.appInstallPath = ''
        self.appAvailable = False
        self.appName = ''
        self.appExe = ''
        self.tryConnectionCounter = 0
        self.host = ''
        self.port = 0

    def checkAppInstall(self):
        pass

    def checkAppStatus(self):
        try:
            checkSocket = socket.socket()
            checkSocket.connect((self.host, self.port))
            checkSocket.close()
            self.tryConnectionCounter = 0
            self.appRunning = True
        except socket.error as e:
            if e.errno == errno.ECONNREFUSED:
                self.tryConnectionCounter += 1
                self.appRunning = False
                self.cameraConnected = False
                if self.tryConnectionCounter < 3:
                    self.logger.warning('{0} is not running'.format(self.appName))
                elif self.tryConnectionCounter == 3:
                    self.logger.error('No connection to {0} possible - stop logging this connection error'.format(self.appName))
        except Exception as e:
            self.cameraConnected = False
            self.appRunning = False
            self.logger.error('error: {0}'.format(e))
        finally:
            pass

    def connectCamera(self):
        pass

    def disconnectCamera(self):
        pass

    def getImage(self, modelData):
        pass

    def solveImage(self, modelData):
        pass

    def getCameraProps(self):
        pass

    def getCameraStatus(self):
        pass
