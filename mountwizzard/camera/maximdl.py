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
import time
import PyQt5
# windows automation
from pywinauto import findwindows
# import .NET / COM Handling
from win32com.client.dynamic import Dispatch
# base for cameras
from baseclasses.camera import MWCamera


class MaximDLCamera(MWCamera):
    logger = logging.getLogger(__name__)

    def __init__(self, app):
        super(MaximDLCamera, self).__init__(app)
        self.driverNameCamera = 'MaxIm.CCDCamera'                                                                           # driver object name
        self.driverNameDocument = 'MaxIm.Document'                                                                          # driver object name
        self.maximCamera = None                                                                                             # placeholder for ascom driver object
        self.maximDocument = None                                                                                           # placeholder for ascom driver object
        self.cameraStatus = ''
        self.appExe = 'MaxIm_DL.exe'
        self.checkAppInstall()

    def checkAppInstall(self):
        self.appAvailable, self.appName, self.appInstallPath = self.app.checkRegistrationKeys('MaxIm DL')
        if self.appAvailable:
            self.app.messageQueue.put('Found: {0}'.format(self.appName))
            self.logger.info('Name: {0}, Path: {1}'.format(self.appName, self.appInstallPath))
        else:
            self.logger.info('Application MaxIm DL not found on computer')

    def checkAppStatus(self):
        try:
            a = findwindows.find_windows(title_re='^(.*?)(\\bMaxIm DL Pro\\b)(.*)$')
            if len(a) == 0:
                self.appRunning = False
            else:
                self.appRunning = True
                self.connectCamera()
        except Exception as e:
            self.logger.error('error{0}'.format(e))
        finally:
            pass

    def connectCamera(self):
        if self.appRunning:
            try:
                if not self.cameraConnected:
                    if not self.maximCamera:
                        self.maximCamera = Dispatch(self.driverNameCamera)
                    if not self.maximDocument:
                        self.maximDocument = Dispatch(self.driverNameDocument)
                    if not self.maximCamera.LinkEnabled:
                        self.maximCamera.LinkEnabled = True
                    self.cameraConnected = True
            except Exception as e:
                self.cameraConnected = False
                self.logger.error('error: {0}'.format(e))
            finally:
                pass

    def disconnectCamera(self):
        if self.appRunning:
            try:
                self.maximCamera.LinkEnabled = False
            except Exception as e:
                self.logger.error('error: {0}'.format(e))
            finally:
                self.cameraConnected = False
                self.maximCamera = None
                self.maximDocument = None

    def getImage(self, modelData):
        suc = False
        mes = ''
        if self.maximCamera:
            try:
                self.maximCamera.BinX = int(modelData['Binning'])
                self.maximCamera.BinY = int(modelData['Binning'])
                self.maximCamera.NumX = int(modelData['SizeX'])
                self.maximCamera.NumY = int(modelData['SizeY'])
                self.maximCamera.StartX = int(modelData['OffX'])
                self.maximCamera.StartY = int(modelData['OffY'])
                if modelData['Speed'] == 'HiSpeed':
                    self.maximCamera.FastReadout = True
                else:
                    self.maximCamera.FastReadout = False
                suc = self.maximCamera.Expose(modelData['Exposure'], 1)
                if not suc:
                    self.logger.error('could not start exposure')
                while not self.maximCamera.ImageReady:
                    time.sleep(0.5)
                modelData['ImagePath'] = modelData['BaseDirImages'] + '/' + modelData['File']
                self.maximCamera.SaveImage(modelData['ImagePath'])
                suc = True
                mes = 'Image integrated'
            except Exception as e:
                self.logger.error('error: {0}'.format(e))
                suc = False
            finally:
                return suc, mes, modelData
        else:
            return False, 'Camera not Connected', modelData

    def getCameraProps(self):
        suc = True
        mes = 'OK'
        canSubframe = False
        gains = ''
        sizeX = 1
        sizeY = 1
        try:
            sizeX = self.maximCamera.CameraXSize
            sizeY = self.maximCamera.CameraYSize
            canSubframe = True
            gains = ['Not Set']
        except Exception as e:
            self.logger.error('error: {0}'.format(e))
            suc = False
            mes = '{0}'.format(e)
        finally:
            return suc, mes, sizeX, sizeY, canSubframe, gains

    def getCameraStatus(self):
        if self.appRunning:
            try:
                if self.maximCamera:
                    if self.maximCamera.LinkEnabled:
                        value = self.maximCamera.CameraStatus
                        self.cameraConnected = True
                    else:
                        value = 0
                    if value == 0:
                        self.cameraStatus = 'DISCONNECTED'
                    elif value == 2:
                        self.cameraStatus = 'READY - IDLE'
                    elif value == 3:
                        self.cameraStatus = 'INTEGRATING'
                    elif value == 4 or value == 5:
                        self.cameraStatus = 'DOWNLOADING'
                    else:
                        self.cameraStatus = 'ERROR'
                        self.cameraConnected = False
            except Exception as e:
                self.cameraStatus = 'ERROR'
                self.cameraConnected = False
                self.logger.error('error: {0}'.format(e))
            finally:
                pass

    def solveImage(self, modelData):
        startTime = time.time()                                                                                             # start timer for plate solve
        mes = ''
        self.maximDocument.OpenFile(modelData['ImagePath'].replace('/', '\\'))                                              # open the fits file
        ra = self.app.mount.transform.degStringToDecimal(self.maximDocument.GetFITSKey('OBJCTRA'), ' ')                     # get ra
        dec = self.app.mount.transform.degStringToDecimal(self.maximDocument.GetFITSKey('OBJCTDEC'), ' ')                   # get dec
        hint = self.maximDocument.GetFITSKey('CDELT1')
        if not hint:
            xpixsz = self.maximDocument.GetFITSKey('XPIXSZ')
            focallen = self.maximDocument.GetFITSKey('FOCALLEN')
            hint = float(xpixsz) * 206.6 / float(focallen)
        else:
            hint = float(hint)
        self.logger.info('solving pinpoint with ra:{0}, dec:{1}, hint:{2}'.format(ra, dec, hint))
        self.maximDocument.PinPointSolve(ra, dec, hint, hint)                                                               # start solving with FITS Header data
        while True:
            try:
                status = self.maximDocument.PinPointStatus
                if status != 3:                                                                                             # 3 means solving
                    break
            except Exception as e:                                                                                          # the request throws exception for reason of failing plate solve
                if e.excepinfo[2] == 'The time limit for plate solving has expired':
                    self.logger.warning('time limit from pinpoint has expired')
                    mes = 'The time limit for plate solving has expired'
                    self.logger.warning('solving message: {0}'.format(e))
                else:
                    self.logger.error('error: {0}'.format(e))
            finally:
                pass
            time.sleep(0.25)
        if status == 1:
            self.logger.info('no start {0}'.format(status))
            suc = self.maximDocument.Close
            if not suc:
                self.logger.error('document {0} could not be closed'.format(modelData['ImagePath']))
                return False, 'Problem closing document in MaximDL', modelData
            else:
                return False, mes, modelData

        stopTime = time.time()
        timeTS = (stopTime - startTime) / 1000
        if status == 2:
            modelData['RaJ2000Solved'] = self.maximDocument.CenterRA
            modelData['DecJ2000Solved'] = self.maximDocument.CenterDec
            modelData['Scale'] = self.maximDocument.ImageScale
            modelData['Angle'] = self.maximDocument.PositionAngle
            modelData['TimeTS'] = timeTS
            self.logger.info('modelData {0}'.format(modelData))
            return True, 'Solved', modelData


if __name__ == "__main__":
    max = 10
    cam = MaximDLCamera(MWCamera)
    cam.appRunning = True
    cam.connectApplication()
    print(cam.getCameraProps())
    value = {'Binning': 1, 'Exposure': 1, 'Iso': 100,
             'GainValue': 'Not Set', 'Speed': 'HiSpeed',
             'File': 'test.fit', 'BaseDirImages': 'c:/temp',
             'CanSubframe': True, 'OffX': 0, 'OffY': 0,
             'SizeX': 3388, 'SizeY': 2712}
    t_start = time.time()
    for i in range(0, max):
        print(i)
        cam.getImage(value)
    t_stop = time.time()
    print((t_stop - t_start - max) / max)
