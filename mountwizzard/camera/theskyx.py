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
import platform
import json
import logging
import socket
import timeit
from baseclasses.camera import MWCamera


class TheSkyX(MWCamera):
    logger = logging.getLogger(__name__)

    def __init__(self, app):
        super(TheSkyX, self).__init__(app)
        self.host = '127.0.0.1'
        self.port = 3040
        self.responseSuccess = '|No error. Error = 0.'
        self.appExe = 'TheSkyX.exe'
        self.checkAppInstall()

    def checkAppInstall(self):
        if platform.system() == 'Windows':
            self.appAvailable, self.appName, self.appInstallPath = self.app.checkRegistrationKeys('TheSkyX')
        else:
            self.appAvailable = True
            self.appName = 'TheSkyX'
            self.appInstallPath = ''
        if self.appAvailable:
            self.app.messageQueue.put('Found: {0}'.format(self.appName))
            self.logger.info('Name: {0}, Path: {1}'.format(self.appName, self.appInstallPath))
        else:
            self.logger.info('Application TheSkyX not found on computer')

    def connectCamera(self):
        if self.appRunning:
            try:
                tsxSocket = socket.socket()
                tsxSocket.connect((self.host, self.port))
                command = '/* Java Script */ '
                command += 'ccdsoftCamera.Connect();'
                self.cameraConnected, response = self.sendCommand(command)
            except Exception as e:
                self.logger.error('error: {0}'.format(e))
                self.cameraConnected = False
            finally:
                # noinspection PyUnboundLocalVariable
                tsxSocket.close()

    def disconnectCamera(self):
        if self.appRunning:
            try:
                tsxSocket = socket.socket()
                tsxSocket.connect((self.host, self.port))
                command = '/* Java Script */ '
                command += 'ccdsoftCamera.Disconnect();'
                self.sendCommand(command)
                self.cameraConnected = False
            except Exception as e:
                self.logger.error('error: {0}'.format(e))
            finally:
                # noinspection PyUnboundLocalVariable
                tsxSocket.close()

    def sendCommand(self, command):
        try:
            tsxSocket = socket.socket()
            tsxSocket.connect((self.host, self.port))
            tsxSocket.send(command.encode())
            response = str(tsxSocket.recv(1024).decode())

            if response.endswith(self.responseSuccess):
                response = response.replace(self.responseSuccess, '')
                return True, response
            else:
                return False, response
        except Exception as e:
            self.logger.error('error: {0}'.format(e))
            return False, format(e)
        finally:
            # noinspection PyUnboundLocalVariable
            tsxSocket.close()

    def solveImage(self, modelData):
        if modelData['Blind']:
            self.logger.warning('Blind mode is not supported. TheSkyX allows to switch to All Sky Image Link by scripting. Please, enable All Sky Image Link manually in TheSkyX')

        try:
            command = '/* Java Script */'
            command += 'ccdsoftCamera.Asynchronous=0;'
            command += 'ImageLink.pathToFITS="' + str(modelData['ImagePath']).replace('\\', '/') + '";'
            if modelData['ScaleHint']:
                command += 'ImageLink.unknownScale=0;'
                command += 'ImageLink.scale=' + str(modelData['ScaleHint']) + ';'
            else:
                command += 'ImageLink.unknownScale=1;'
                command += 'ImageLink.scale=2;'
            command += 'ImageLink.execute();'
            command += 'Out=String(\'{"succeeded":"\'+ImageLinkResults.succeeded+\'","imageCenterRAJ2000":"\'+ImageLinkResults.imageCenterRAJ2000+\'","imageCenterDecJ2000":"\'+ImageLinkResults.imageCenterDecJ2000+\'","imageScale":"\'+ImageLinkResults.imageScale+\'","imagePositionAngle":"\'+ImageLinkResults.imagePositionAngle+\'"}\');'

            startTime = timeit.default_timer()
            success, response = self.sendCommand(command)
            solveTime = timeit.default_timer() - startTime

            if success:
                captureResponse = json.loads(response)

                if captureResponse['succeeded'] == '1':
                    modelData['RaJ2000Solved'] = float(captureResponse['imageCenterRAJ2000'])
                    modelData['DecJ2000Solved'] = float(captureResponse['imageCenterDecJ2000'])
                    modelData['Scale'] = float(captureResponse['imageScale'])
                    modelData['Angle'] = float(captureResponse['imagePositionAngle'])
                    modelData['TimeTS'] = solveTime
                    return True, 'Solved', modelData
                else:
                    return False, 'Unsolved', modelData
            else:
                return False, 'Request failed', modelData
        except Exception as e:
            self.logger.error('error: {0}'.format(e))
            return False, 'Request failed', modelData

    def getImage(self, modelData):
        # TODO: how is TSX dealing with ISO settings for DSLR?

        try:
            command = '/* Java Script */'
            command += 'ccdsoftCamera.Asynchronous=0;'
            if modelData['CanSubframe']:
                command += 'ccdsoftCamera.Subframe=1;'
                command += 'ccdsoftCamera.SubframeLeft=' + str(modelData['OffX']) + ';'
                command += 'ccdsoftCamera.SubframeTop=' + str(modelData['OffY']) + ';'
                command += 'ccdsoftCamera.SubframeRight=' + str(modelData['OffX'] + modelData['SizeX']) + ';'
                command += 'ccdsoftCamera.SubframeBottom=' + str(modelData['OffY'] + modelData['SizeY']) + ';'
            else:
                command += 'ccdsoftCamera.Subframe=0;'

            if modelData['Speed'] == 'HiSpeed':
                command += 'ccdsoftCamera.setPropStr("m_csExCameraMode", "Fast Image Download");'
            else:
                command += 'ccdsoftCamera.setPropStr("m_csExCameraMode", "High Image Quality");'

            command += 'ccdsoftCamera.BinX='+str(modelData['Binning'])+';'
            command += 'ccdsoftCamera.BinY='+str(modelData['Binning'])+';'
            command += 'ccdsoftCamera.ExposureTime='+str(modelData['Exposure'])+';'
            command += 'ccdsoftCamera.AutoSavePath="'+str(modelData['BaseDirImages'])+'";'
            command += 'ccdsoftCamera.AutoSaveOn=1;'
            command += 'ccdsoftCamera.Frame="cdLight";'
            command += 'ccdsoftCamera.TakeImage();'
            command += 'var Out = "";'
            command += 'Out=ccdsoftCamera.LastImageFileName;'
            success, response = self.sendCommand(command)

            modelData['ImagePath'] = response

            return success, response, modelData
        except Exception as e:
            self.logger.error('error: {0}'.format(e))
            return False, 'Request failed', ''

    def getCameraStatus(self):
        if self.appRunning:
            try:
                command = '/* Java Script */'
                command += 'var Out = "";'
                command += 'ccdsoftCamera.Asynchronous=0;'
                command += 'Out=ccdsoftCamera.ExposureStatus;'
                success, response = self.sendCommand(command)
                self.cameraConnected = True
                if response == 'Not Connected':
                    response = 'DISCONNECTED'
                    self.cameraConnected = False
                elif response == 'Ready':
                    response = 'READY - IDLE'
                elif 'Exposing' in response:
                    response = 'INTEGRATING'
                self.cameraStatus = response
            except Exception as e:
                self.logger.error('error: {0}'.format(e))
            finally:
                pass

    def getCameraProps(self):
        # TODO: Get the chance to implement subframe on / off if a camera doesn't support this
        # TODO: Gain setting in CMOS Cameras necessary ?
        try:
            command = '/* Java Script */'
            command += 'var Out = "";'
            command += 'ccdsoftCamera.Asynchronous=0;'
            command += 'Out=String(\'{"WidthInPixels":"\'+ccdsoftCamera.WidthInPixels+\'","HeightInPixels":"\'+ccdsoftCamera.HeightInPixels+\'"}\');'
            success, response = self.sendCommand(command)
            captureResponse = json.loads(response)
            return success, '', int(captureResponse['WidthInPixels']), int(captureResponse['HeightInPixels']), True, 'Not Set'
        except Exception as e:
            self.logger.error('error: {0}'.format(e))
            return False, 'Request failed', '', '', '', ''
