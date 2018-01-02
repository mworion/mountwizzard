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
import math
# import basic stuff
import platform
import threading
import time
# for the sorting
from operator import itemgetter

# import PyQT5 for threading purpose
import PyQt5

if platform.system() == 'Windows':
    # win32com
    import pythoncom
#  mount driver classes
if platform.system() == 'Windows':
    from mount import ascommount
from mount import ipdirect
# astrometry
from astrometry import transform


class Mount(PyQt5.QtCore.QThread):
    logger = logging.getLogger(__name__)                                                                                    # enable logging
    signalMountConnected = PyQt5.QtCore.pyqtSignal([bool], name='mountConnected')                                           # signal for connection status
    signalMountAzAltPointer = PyQt5.QtCore.pyqtSignal([float, float], name='mountAzAltPointer')
    signalMountTrackPreview = PyQt5.QtCore.pyqtSignal(name='mountTrackPreview')

    BLUE = 'background-color: rgb(42, 130, 218)'
    DEFAULT = 'background-color: rgb(32,32,32); color: rgb(192,192,192)'
    BLIND_COMMANDS = ['AP', 'hP', 'PO', 'RT0', 'RT1', 'RT2', 'RT9', 'STOP', 'U2']

    def __init__(self, app):
        super().__init__()                                                                                                  # init of the class parent with super
        self.app = app                                                                                                      # accessing ui object from mount class
        self.data = {}
        if platform.system() == 'Windows':
            self.MountAscom = ascommount.MountAscom(app)                                                                    # set ascom driver class
        self.MountIpDirect = ipdirect.MountIpDirect(app)
        self.mountHandler = self.MountIpDirect
        self.transform = transform.Transform(app)
        self.statusReference = {'0': 'Tracking',
                                '1': 'Stopped after STOP',
                                '2': 'Slewing to park position',
                                '3': 'Unparking',
                                '4': 'Slewing to home position',
                                '5': 'Parked',
                                '6': 'Slewing or going to stop',
                                '7': 'Tracking Off no move',
                                '8': 'Motor low temperature',
                                '9': 'Tracking outside limits',
                                '10': 'Following Satellite',
                                '11': 'User OK Needed',
                                '98': 'Unknown Status',
                                '99': 'Error'
                                }                                                                                           # conversion list Gstat to text
        self.site_lat = '49'                                                                                                # site lat
        self.site_lon = '0'                                                                                                 # site lon
        self.site_height = '0'                                                                                              # site height
        self.sidereal_time = ''                                                                                             # local sidereal time
        self.counter = 0                                                                                                    # counter im main loop
        self.chooserLock = threading.Lock()
        self.initConfig()

    def initConfig(self):
        self.app.ui.pd_chooseMountConnection.addItem('IP Direct Connection')
        if platform.system() == 'Windows':
            self.app.ui.pd_chooseMountConnection.addItem('ASCOM Driver Connection')
        try:
            if platform.system() == 'Windows':
                if 'ASCOMTelescopeDriverName' in self.app.config:
                    self.MountAscom.driverName = self.app.config['ASCOMTelescopeDriverName']
            if 'MountConnection' in self.app.config:
                self.app.ui.pd_chooseMountConnection.setCurrentIndex(int(self.app.config['MountConnection']))
                self.showConfigEntries(int(self.app.config['MountConnection']))
            if 'CheckAutoRefractionCamera' in self.app.config:
                self.app.ui.checkAutoRefractionCamera.setChecked(self.app.config['CheckAutoRefractionCamera'])
            if 'CheckAutoRefractionNotTracking' in self.app.config:
                self.app.ui.checkAutoRefractionNotTracking.setChecked(self.app.config['CheckAutoRefractionNotTracking'])
            if 'MountIP' in self.app.config:
                self.app.ui.le_mountIP.setText(self.app.config['MountIP'])
            if 'MountMAC' in self.app.config:
                self.app.ui.le_mountMAC.setText(self.app.config['MountMAC'])

        except Exception as e:
            self.logger.error('item in config.cfg not be initialize, error:{0}'.format(e))
        finally:
            pass
        self.app.ui.pd_chooseMountConnection.currentIndexChanged.connect(self.chooseMountConn)

    def storeConfig(self):
        if platform.system() == 'Windows':
            self.app.config['ASCOMTelescopeDriverName'] = self.MountAscom.driverName
        self.app.config['MountConnection'] = self.app.ui.pd_chooseMountConnection.currentIndex()
        self.app.config['CheckAutoRefractionCamera'] = self.app.ui.checkAutoRefractionCamera.isChecked()
        self.app.config['CheckAutoRefractionNotTracking'] = self.app.ui.checkAutoRefractionNotTracking.isChecked()
        self.app.config['MountIP'] = self.app.ui.le_mountIP.text()
        self.app.config['MountMAC'] = self.app.ui.le_mountMAC.text()

    def showConfigEntries(self, index):
        if index == 0:
            self.app.ui.le_mountIP.setVisible(True)
            self.app.ui.le_mountIP.setEnabled(True)
            self.app.ui.le_mountMAC.setVisible(True)
            self.app.ui.le_mountMAC.setEnabled(True)
            self.app.ui.label_mountIP.setVisible(True)
            self.app.ui.label_mountMAC.setVisible(True)

            self.app.ui.btn_setupMountDriver.setVisible(False)
            self.app.ui.btn_setupMountDriver.setEnabled(False)
        elif index == 1:
            self.app.ui.le_mountIP.setVisible(False)
            self.app.ui.le_mountIP.setEnabled(False)
            self.app.ui.le_mountMAC.setVisible(False)
            self.app.ui.le_mountMAC.setEnabled(False)
            self.app.ui.label_mountIP.setVisible(False)
            self.app.ui.label_mountMAC.setVisible(False)

            self.app.ui.btn_setupMountDriver.setVisible(True)
            self.app.ui.btn_setupMountDriver.setEnabled(True)

    def chooseMountConn(self):
        self.chooserLock.acquire()
        if self.mountHandler.connected:
            self.mountHandler.connected = False
            self.mountHandler.disconnect()
        if self.app.ui.pd_chooseMountConnection.currentText().startswith('IP Direct Connection'):
            self.mountHandler = self.MountIpDirect
            self.logger.info('actual driver is IpDirect, IP is: {0}'.format(self.MountIpDirect.mountIP()))
        if self.app.ui.pd_chooseMountConnection.currentText().startswith('ASCOM Driver Connection'):
            self.mountHandler = self.MountAscom
            self.logger.info('actual driver is ASCOM')
        self.showConfigEntries(self.app.ui.pd_chooseMountConnection.currentIndex())
        self.chooserLock.release()

    def run(self):
        if platform.system() == 'Windows':
            pythoncom.CoInitialize()
        self.chooseMountConn()
        self.counter = 0
        while True:
            self.signalMountConnected.emit(self.mountHandler.connected)
            if self.mountHandler.connected:
                if not self.app.mountCommandQueue.empty():
                    command = self.app.mountCommandQueue.get()
                    if command == 'ShowAlignmentModel':
                        num = self.numberModelStars()
                        if num == -1:
                            self.app.messageQueue.put('Show Model not available without real mount')
                        else:
                            self.app.ui.btn_showActualModel.setStyleSheet(self.BLUE)
                            self.showAlignmentModel(self.getAlignmentModel())
                            self.app.ui.btn_showActualModel.setStyleSheet(self.DEFAULT)
                    elif command == 'ClearAlign':
                        if self.numberModelStars() == -1:
                            self.app.messageQueue.put('Clear Align not available without real mount')
                        else:
                            self.mountHandler.sendCommand('delalig')
                    elif command == 'RunTargetRMSAlignment':
                        if self.numberModelStars() == -1:
                            self.app.messageQueue.put('Run Optimize not available without real mount')
                        else:
                            self.app.ui.btn_runTargetRMSAlignment.setStyleSheet(self.BLUE)
                            self.runTargetRMSAlignment()
                            self.app.ui.btn_runTargetRMSAlignment.setStyleSheet(self.DEFAULT)
                    elif command == 'DeleteWorstPoint':
                        if self.numberModelStars() == -1:
                            self.app.messageQueue.put('Delete worst point not available without real mount')
                        else:
                            self.app.ui.btn_deleteWorstPoint.setStyleSheet(self.BLUE)
                            self.deleteWorstPoint()
                            self.app.ui.btn_deleteWorstPoint.setStyleSheet(self.DEFAULT)
                    elif command == 'SaveBackupModel':
                        self.app.ui.btn_saveBackupModel.setStyleSheet(self.BLUE)
                        self.saveBackupModel()
                        self.app.ui.btn_saveBackupModel.setStyleSheet(self.DEFAULT)
                    elif command == 'LoadBackupModel':
                        self.app.ui.btn_loadBackupModel.setStyleSheet(self.BLUE)
                        self.loadBackupModel()
                        self.app.ui.btn_loadBackupModel.setStyleSheet(self.DEFAULT)
                    elif command == 'LoadBaseModel':
                        self.app.ui.btn_loadBaseModel.setStyleSheet(self.BLUE)
                        self.loadBaseModel()
                        self.app.ui.btn_loadBaseModel.setStyleSheet(self.DEFAULT)
                    elif command == 'SaveBaseModel':
                        self.app.ui.btn_saveBaseModel.setStyleSheet(self.BLUE)
                        self.saveBaseModel()
                        self.app.ui.btn_saveBaseModel.setStyleSheet(self.DEFAULT)
                    elif command == 'LoadRefinementModel':
                        self.app.ui.btn_loadRefinementModel.setStyleSheet(self.BLUE)
                        self.loadRefinementModel()
                        self.app.ui.btn_loadRefinementModel.setStyleSheet(self.DEFAULT)
                    elif command == 'SaveRefinementModel':
                        self.app.ui.btn_saveRefinementModel.setStyleSheet(self.BLUE)
                        self.saveRefinementModel()
                        self.app.ui.btn_saveRefinementModel.setStyleSheet(self.DEFAULT)
                    elif command == 'LoadSimpleModel':
                        self.app.ui.btn_loadSimpleModel.setStyleSheet(self.BLUE)
                        self.loadSimpleModel()
                        self.app.ui.btn_loadSimpleModel.setStyleSheet(self.DEFAULT)
                    elif command == 'SaveSimpleModel':
                        self.app.ui.btn_saveSimpleModel.setStyleSheet(self.BLUE)
                        self.saveSimpleModel()
                        self.app.ui.btn_saveSimpleModel.setStyleSheet(self.DEFAULT)
                    elif command == 'LoadDSO1Model':
                        self.app.ui.btn_loadDSO1Model.setStyleSheet(self.BLUE)
                        self.loadDSO1Model()
                        self.app.ui.btn_loadDSO1Model.setStyleSheet(self.DEFAULT)
                    elif command == 'SaveDSO1Model':
                        self.app.ui.btn_saveDSO1Model.setStyleSheet(self.BLUE)
                        self.saveDSO1Model()
                        self.app.ui.btn_saveDSO1Model.setStyleSheet(self.DEFAULT)
                    elif command == 'LoadDSO2Model':
                        self.app.ui.btn_loadDSO2Model.setStyleSheet(self.BLUE)
                        self.loadDSO2Model()
                        self.app.ui.btn_loadDSO2Model.setStyleSheet(self.DEFAULT)
                    elif command == 'SaveDSO2Model':
                        self.app.ui.btn_saveDSO2Model.setStyleSheet(self.BLUE)
                        self.saveDSO2Model()
                        self.app.ui.btn_saveDSO2Model.setStyleSheet(self.DEFAULT)
                    elif command == 'SetRefractionParameter':
                        self.setRefractionParameter()
                    elif command == 'FLIP':
                        self.flipMount()
                    elif command == 'SetupAscomDriver':
                        self.MountAscom.setupDriver()
                    elif command == 'Shutdown':
                        self.mountShutdown()
                    else:
                        self.mountHandler.sendCommand(command)
                    self.app.mountCommandQueue.task_done()
                else:
                    if self.counter == 0:
                        self.getStatusOnce()
                    if self.counter % 2 == 0:
                        self.getStatusFast()
                    if self.counter % 15 == 0:
                        self.getStatusMedium()
                    if self.counter % 150 == 0:
                        self.getStatusSlow()
                time.sleep(0.2)
                self.counter += 1
            else:
                self.mountHandler.connect()
                self.counter = 0
                time.sleep(1)
        self.mountHandler.disconnect()
        if platform.system() == 'Windows':
            pythoncom.CoUninitialize()

    def mountShutdown(self):
        reply = self.mountHandler.sendCommand('shutdown')
        if reply != '1':
            self.logger.error('error: {0}'.format(reply))
            self.app.messageQueue.put('Error in mount shutdown !')
        else:
            self.mountHandler.connected = False
            time.sleep(1)
            self.mountHandler.disconnect()
            self.logger.info('Shutdown mount manually')
            self.app.messageQueue.put('Shutting mount down !')

    def flipMount(self):
        reply = self.mountHandler.sendCommand('FLIP').rstrip('#').strip()
        if reply == '0':
            self.app.messageQueue.put('Flip Mount could not be executed !')
            self.logger.error('error: {0}'.format(reply))

    def numberModelStars(self):
        return int(self.mountHandler.sendCommand('getalst'))

    def getAlignmentModelStatus(self, alignModel):
        if self.data['FW'] < 21500:
            return alignModel
        try:
            reply = self.mountHandler.sendCommand('getain')
            # there should be a reply, format string is "ZZZ.ZZZZ,+AA.AAAA,EE.EEEE,PPP.PP,+OO.OOOO,+aa.aa, +bb.bb,NN,RRRRR.R#"
            if reply:
                # if a single 'E' returns, there is a problem, not further parameter will follow
                if reply != 'E':
                    a1, a2, a3, a4, a5, a6, a7, a8, a9 = reply.split(',')
                    # 'E' could be sent if not calculable or no value available
                    if a1 != 'E':
                        alignModel['azimuth'] = float(a1)
                    else:
                        alignModel['azimuth'] = 0
                    if a2 != 'E':
                        alignModel['altitude'] = float(a2)
                    else:
                        alignModel['altitude'] = 0
                    if a3 != 'E':
                        alignModel['polarError'] = float(a3)
                    else:
                        alignModel['polarError'] = 0
                    if a4 != 'E':
                        alignModel['posAngle'] = float(a4)
                    else:
                        alignModel['posAngle'] = 0
                    if a5 != 'E':
                        alignModel['orthoError'] = float(a5)
                    else:
                        alignModel['orthoError'] = 0
                    if a6 != 'E':
                        alignModel['azimuthKnobs'] = float(a6)
                    else:
                        alignModel['azimuthKnobs'] = 0
                    if a7 != 'E':
                        alignModel['altitudeKnobs'] = float(a7)
                    else:
                        alignModel['altitudeKnobs'] = 0
                    if a8 != 'E':
                        alignModel['terms'] = int(float(a8))
                    else:
                        alignModel['terms'] = 0
                    if a9 != 'E':
                        alignModel['RMS'] = float(a9)
                    else:
                        alignModel['RMS'] = 0
        except Exception as e:
            self.logger.error('receive error getain command: {0}'.format(e))
        finally:
            return alignModel

    def getAlignmentModel(self):
        alignModel = {}
        points = []
        alignModel['azimuth'] = 0.0
        alignModel['altitude'] = 0.0
        alignModel['polarError'] = 0.0
        alignModel['posAngle'] = 0.0
        alignModel['orthoError'] = 0.0
        alignModel['azimuthKnobs'] = 0.0
        alignModel['altitudeKnobs'] = 0.0
        alignModel['terms'] = 0
        alignModel['RMS'] = 0.0
        alignModel['points'] = points
        numberStars = self.numberModelStars()
        alignModel['number'] = numberStars
        if numberStars < 1:
            return alignModel
        alignModel = self.getAlignmentModelStatus(alignModel)
        for i in range(1, numberStars + 1):
            reply = self.mountHandler.sendCommand('getalp{0:d}'.format(i)).split(',')
            ha = reply[0].strip().split('.')[0]
            dec = reply[1].strip().split('.')[0]
            errorRMS = float(reply[2].strip())
            errorAngle = reply[3].strip().rstrip('#')
            dec = dec.replace('*', ':')
            ra_J2000 = self.transform.degStringToDecimal(ha)
            dec_J2000 = self.transform.degStringToDecimal(dec)
            az, alt = self.transform.ra_dec_lst_to_az_alt(ra_J2000, dec_J2000)
            # index should start with 0, but numbering in mount starts with 1
            alignModel['points'].append((i-1, ra_J2000, dec_J2000, az, alt, errorRMS, float(errorAngle)))
        return alignModel

    def retrofitMountData(self, data):
        num = self.numberModelStars()
        if num == len(data):
            alignModel = self.getAlignmentModel()
            self.showAlignmentModel(alignModel)
            for i in range(0, alignModel['number']):
                data[i]['ModelError'] = float(alignModel['points'][i][5])
                data[i]['RaError'] = data[i]['ModelError'] * math.sin(math.radians(alignModel['points'][i][6]))
                data[i]['DecError'] = data[i]['ModelError'] * math.cos(math.radians(alignModel['points'][i][6]))
            self.app.modelLogQueue.put('Mount Model and Model Data synced\n')
        else:
            self.logger.warning('size mount modeling {0} and modeling data {1} do not fit !'.format(num, len(data)))
            self.app.modelLogQueue.put('Mount Model and Model Data could not be synced\n')
            self.app.messageQueue.put('Error- Mount Model and Model Data mismatch!\n')
        return data

    def showAlignmentModel(self, alignModel):
        self.data['ModelStarError'] = 'Downloading data\n'
        for i in range(0, alignModel['number']):
            self.data['ModelStarError'] += '#{0:02d}   AZ: {1:3d}   Alt: {2:3d}   Err: {3:4.1f}\x22   PA: {4:3.0f}\xb0\n'.format(i, int(alignModel['points'][i][3]), int(alignModel['points'][i][4]), alignModel['points'][i][5], alignModel['points'][i][6])
        self.data['ModelStarError'] += 'Downloading finished\n'
        self.data['NumberAlignmentStars'] = alignModel['number']
        self.data['ModelRMSError'] = '{0:3.1f}'.format(alignModel['RMS'])
        self.data['ModelErrorPosAngle'] = '{0:3.1f}'.format(alignModel['posAngle'])
        self.data['ModelPolarError'] = '{0}'.format(self.transform.decimalToDegree(alignModel['polarError']))
        self.data['ModelOrthoError'] = '{0}'.format(self.transform.decimalToDegree(alignModel['orthoError']))
        self.data['ModelErrorAz'] = '{0}'.format(self.transform.decimalToDegree(alignModel['azimuthKnobs']))
        self.data['ModelErrorAlt'] = '{0}'.format(self.transform.decimalToDegree(alignModel['altitudeKnobs']))
        self.data['ModelTerms'] = '{0:2d}'.format(alignModel['terms'])
        if alignModel['azimuthKnobs'] > 0:
            value = '{0:2.2f} left'.format(abs(alignModel['azimuthKnobs']))
        else:
            value = '{0:2.2f} right'.format(abs(alignModel['azimuthKnobs']))
        self.data['ModelKnobTurnAz'] = '{0}'.format(value)
        if alignModel['altitudeKnobs'] > 0:
            value = '{0:2.2f} down'.format(abs(alignModel['altitudeKnobs']))
        else:
            value = '{0:2.2f} up'.format(abs(alignModel['altitudeKnobs']))
        self.data['ModelKnobTurnAlt'] = '{0}'.format(value)
        self.app.showModelErrorPolar()
        return

    def runTargetRMSAlignment(self):
        self.data['ModelStarError'] = 'delete'
        alignModel = self.getAlignmentModel()
        if alignModel['number'] < 4:
            return
        while alignModel['RMS'] > float(self.app.ui.targetRMS.value()) and alignModel['number'] > 3:
            alignModel = self.deleteWorstPointRaw(alignModel)

    def deleteWorstPoint(self):
        alignModel = self.getAlignmentModel()
        self.deleteWorstPointRaw(alignModel)

    def deleteWorstPointRaw(self, alignModel):
        if alignModel['number'] < 4:
            return
        if alignModel['number'] > 3:
            # index 0 is the worst star, index starts with 0
            a = sorted(alignModel['points'], key=itemgetter(5), reverse=True)
            index = a[0][0]
            # numbering in mount starts with 1
            reply = self.mountHandler.sendCommand('delalst{0:d}'.format(index + 1))
            if reply == '1':
                alignModel = self.getAlignmentModel()
                self.app.modeling.modelData.pop(index)
                for i in range(0, alignModel['number']):
                    self.app.modeling.modelData[i]['ModelError'] = float(alignModel['points'][i][5])
                    self.app.modeling.modelData[i]['RaError'] = self.app.modeling.modelData[i]['ModelError'] * math.sin(math.radians(float(alignModel['points'][i][6])))
                    self.app.modeling.modelData[i]['DecError'] = self.app.modeling.modelData[i]['ModelError'] * math.cos(math.radians(float(alignModel['points'][i][6])))
                self.showAlignmentModel(alignModel)
            else:
                self.logger.warning('Point {0} could not be deleted').format(index)
        return alignModel

    def saveModel(self, target):
        num = self.numberModelStars()
        if num == -1:
            self.app.messageQueue.put('Save Model not available without real mount')
            return False
        self.mountHandler.sendCommand('modeldel0' + target)
        reply = self.mountHandler.sendCommand('modelsv0' + target)
        if reply == '1':
            self.app.messageQueue.put('Actual Mount Model saved to file {0}'.format(target))
            return True
        else:
            self.logger.warning('Model {0} could not be saved'.format(target))
            return False

    def loadModel(self, target):
        num = self.numberModelStars()
        if num == -1:
            self.app.messageQueue.put('Load Model not available without real mount')
            return False
        reply = self.mountHandler.sendCommand('modelld0' + target)
        if reply == '1':
            self.app.messageQueue.put('Mount Model loaded from file {0}'.format(target))
            return True
        else:
            self.app.messageQueue.put('There is no modeling named {0} or error while loading'.format(target))
            self.logger.warning('Model {0} could not be loaded'.format(target))
            return False

    def saveBackupModel(self):
        if self.saveModel('BACKUP'):
            if self.app.modeling.modelData:
                self.app.analyseWindow.analyse.saveData(self.app.modeling.modelData, 'backup.dat')

    def loadBackupModel(self):
        if self.loadModel('BACKUP'):
            self.app.modeling.modelData = self.app.analyseWindow.analyse.loadDataRaw('backup.dat')
            if not self.app.modeling.modelData:
                self.app.messageQueue.put('No data file for BACKUP')

    def saveBaseModel(self):
        if self.saveModel('BASE'):
            if self.app.modeling.modelData:
                self.app.analyseWindow.analyse.saveData(self.app.modeling.modelData, 'base.dat')
            else:
                self.app.messageQueue.put('No data for BASE')

    def loadBaseModel(self):
        if self.loadModel('BASE'):
            self.app.modeling.modelData = self.app.analyseWindow.analyse.loadDataRaw('base.dat')
            if not self.app.modeling.modelData:
                self.app.messageQueue.put('No data file for BASE')
        else:
            self.app.messageQueue.put('No Model in Mount called BASE')

    def saveRefinementModel(self):
        if self.saveModel('REFINE'):
            if self.app.modeling.modelData:
                self.app.analyseWindow.analyse.saveData(self.app.modeling.modelData, 'refine.dat')
            else:
                self.app.messageQueue.put('No data for REFINE')

    def loadRefinementModel(self):
        if self.loadModel('REFINE'):
            self.app.modeling.modelData = self.app.analyseWindow.analyse.loadDataRaw('refine.dat')
            if not self.app.modeling.modelData:
                self.app.messageQueue.put('No data file for REFINE')

    def saveActualModel(self):
        if self.saveModel('ACTUAL'):
            if self.app.modeling.modelData:
                if 'Index' in self.app.modeling.modelData[0].keys():
                    self.app.analyseWindow.analyse.saveData(self.app.modeling.modelData, 'actual.dat')
            else:
                self.app.messageQueue.put('No data for ACTUAL')

    def loadActualModel(self):
        if self.loadModel('ACTUAL'):
            self.app.modeling.modelData = self.app.analyseWindow.analyse.loadDataRaw('actual.dat')
            if not self.app.modeling.modelData:
                self.app.messageQueue.put('No data file for ACTUAL')

    def saveSimpleModel(self):
        if self.saveModel('SIMPLE'):
            if self.app.modeling.modelData:
                self.app.analyseWindow.analyse.saveData(self.app.modeling.modelData, 'simple.dat')
            else:
                self.app.messageQueue.put('No data file for SIMPLE')

    def loadSimpleModel(self):
        if self.loadModel('SIMPLE'):
            self.app.modeling.modelData = self.app.analyseWindow.analyse.loadDataRaw('simple.dat')
            if not self.app.modeling.modelData:
                self.app.messageQueue.put('No data file for SIMPLE')

    def saveDSO1Model(self):
        if self.saveModel('DSO1'):
            if self.app.modeling.modelData:
                self.app.analyseWindow.analyse.saveData(self.app.modeling.modelData, 'DSO1.dat')
            else:
                self.app.messageQueue.put('No data file for DSO1')

    def loadDSO1Model(self):
        if self.loadModel('DSO1'):
            self.app.modeling.modelData = self.app.analyseWindow.analyse.loadDataRaw('DSO1.dat')
            if not self.app.modeling.modelData:
                self.app.messageQueue.put('No data file for DSO1')

    def saveDSO2Model(self):
        if self.saveModel('DSO2'):
            if self.app.modeling.modelData:
                self.app.analyseWindow.analyse.saveData(self.app.modeling.modelData, 'DSO2.dat')
            else:
                self.app.messageQueue.put('No data file for DSO2')

    def loadDSO2Model(self):
        if self.loadModel('DSO2'):
            self.app.modeling.modelData = self.app.analyseWindow.analyse.loadDataRaw('dso2.dat')
            if not self.app.modeling.modelData:
                self.app.messageQueue.put('No data file for DSO2')

    def setRefractionParameter(self):
        if 'Temperature' in self.app.environment.data and 'Pressure' in self.app.environment.data:
            pressure = self.app.environment.data['Pressure']
            temperature = self.app.environment.data['Temperature']
            if self.app.environment.connected == 1:
                if (900.0 < pressure < 1100.0) and (-40.0 < temperature < 50.0):
                    self.mountHandler.sendCommand('SRPRS{0:04.1f}'.format(pressure))
                    if temperature > 0:
                        self.mountHandler.sendCommand('SRTMP+{0:03.1f}'.format(temperature))
                    else:
                        self.mountHandler.sendCommand('SRTMP-{0:3.1f}'.format(-temperature))
                    self.data['RefractionTemperature'] = self.mountHandler.sendCommand('GRTMP')
                    self.data['RefractionPressure'] = self.mountHandler.sendCommand('GRPRS')
                else:
                    self.logger.warning('parameters out of range ! temperature:{0} pressure:{1}'.format(temperature, pressure))

    def getStatusFast(self):
        reply = self.mountHandler.sendCommand('GS')
        if reply:
            self.data['LocalSiderealTime'] = reply.strip('#')
        reply = self.mountHandler.sendCommand('GR')
        if reply:
            self.data['RaJNow'] = self.transform.degStringToDecimal(reply)
        reply = self.mountHandler.sendCommand('GD')
        if reply:
            self.data['DecJNow'] = self.transform.degStringToDecimal(reply)
        reply = self.mountHandler.sendCommand('Ginfo')
        if reply:
            try:
                reply = reply.rstrip('#').strip().split(',')
            except Exception as e:
                self.logger.error('receive error Ginfo command: {0} reply:{1}'.format(e, reply))
            finally:
                pass
            if len(reply) == 8:
                self.data['RaJNow'] = float(reply[0])
                self.data['DecJNow'] = float(reply[1])
                self.data['Pierside'] = reply[2]
                self.data['Az'] = float(reply[3])
                self.data['Alt'] = float(reply[4])
                # needed for 2.14. firmware
                self.data['JulianDate'] = reply[5].rstrip('#')
                self.data['Status'] = int(reply[6])
                self.data['Slewing'] = (reply[7] == '1')
            else:
                self.logger.warning('Ginfo command delivered wrong number of arguments: {0}'.format(reply))
            self.data['RaJ2000'], self.data['DecJ2000'] = self.transform.transformERFA(self.data['RaJNow'], self.data['DecJNow'], 2)
            self.data['TelescopeRA'] = '{0}'.format(self.transform.decimalToDegree(self.data['RaJ2000'], False, False))
            self.data['TelescopeDEC'] = '{0}'.format(self.transform.decimalToDegree(self.data['DecJ2000'], True, False))
            self.data['TelescopeAltitude'] = '{0:03.2f}'.format(self.data['Alt'])
            self.data['TelescopeAzimuth'] = '{0:03.2f}'.format(self.data['Az'])
            self.data['MountStatus'] = '{0}'.format(self.data['Status'])
            self.data['JulianDate'] = '{0}'.format(self.data['JulianDate'][:13])
            if self.data['Pierside'] == str('W'):
                self.data['TelescopePierSide'] = 'WEST'
            else:
                self.data['TelescopePierSide'] = 'EAST'
            self.signalMountAzAltPointer.emit(self.data['Az'], self.data['Alt'])
            self.data['TimeToFlip'] = int(float(self.mountHandler.sendCommand('Gmte')))
            self.data['MeridianLimitTrack'] = int(float(self.mountHandler.sendCommand('Glmt')))
            self.data['MeridianLimitSlew'] = int(float(self.mountHandler.sendCommand('Glms')))
            self.data['TimeToMeridian'] = int(self.data['TimeToFlip'] - self.data['MeridianLimitTrack'] / 360 * 24 * 60)

    def getStatusMedium(self):
        if self.app.ui.checkAutoRefractionNotTracking.isChecked():
            # if there is no tracking, than updating is good
            if self.data['Status'] != 0:
                self.setRefractionParameter()
        if self.app.ui.checkAutoRefractionCamera.isChecked():
            # the same is good if the camera is not in integrating
            if self.app.modeling.imagingHandler.cameraStatus in ['READY - IDLE', 'DOWNLOADING']:
                self.setRefractionParameter()
        self.data['SlewRate'] = self.mountHandler.sendCommand('GMs')
        self.signalMountTrackPreview.emit()

    def getStatusSlow(self):
        self.data['TimeToTrackingLimit'] = self.mountHandler.sendCommand('Gmte')
        self.data['RefractionTemperature'] = self.mountHandler.sendCommand('GRTMP')
        self.data['RefractionPressure'] = self.mountHandler.sendCommand('GRPRS')
        self.data['TelescopeTempDEC'] = self.mountHandler.sendCommand('GTMP1')
        self.data['RefractionStatus'] = self.mountHandler.sendCommand('GREF')
        self.data['UnattendedFlip'] = self.mountHandler.sendCommand('Guaf')
        self.data['MeridianLimitTrack'] = self.mountHandler.sendCommand('Glmt')
        self.data['MeridianLimitSlew'] = self.mountHandler.sendCommand('Glms')
        self.data['DualAxisTracking'] = self.mountHandler.sendCommand('Gdat')
        self.data['CurrentHorizonLimitHigh'] = self.mountHandler.sendCommand('Gh')
        self.data['CurrentHorizonLimitLow'] = self.mountHandler.sendCommand('Go')
        try:
            if self.data['FW'] >= 21500:
                reply = self.mountHandler.sendCommand('GDUTV')
                if reply:
                    valid, expirationDate = reply.split(',')
                    self.data['UTCDataValid'] = valid
                    self.data['UTCDataExpirationDate'] = expirationDate
        except Exception as e:
            self.logger.error('receive error GDUTV command: {0}'.format(e))
        finally:
            pass

    def getStatusOnce(self):
        # Set high precision mode
        self.mountHandler.sendCommand('U2')
        self.site_height = self.mountHandler.sendCommand('Gev')
        lon1 = self.mountHandler.sendCommand('Gg')
        # due to compatibility to LX200 protocol east is negative
        if lon1[0] == '-':
            self.site_lon = lon1.replace('-', '+')
        else:
            self.site_lon = lon1.replace('+', '-')
        self.site_lat = self.mountHandler.sendCommand('Gt')
        self.data['CurrentSiteElevation'] = self.site_height
        self.data['CurrentSiteLongitude'] = lon1
        self.data['CurrentSiteLatitude'] = self.site_lat
        self.data['FirmwareDate'] = self.mountHandler.sendCommand('GVD')
        self.data['FirmwareNumber'] = self.mountHandler.sendCommand('GVN')
        fw = self.data['FirmwareNumber'].split('.')
        if len(fw) == 3:
            self.data['FW'] = int(float(fw[0]) * 10000 + float(fw[1]) * 100 + float(fw[2]))
        else:
            self.data['FW'] = 0
        self.data['FirmwareProductName'] = self.mountHandler.sendCommand('GVP')
        self.data['FirmwareTime'] = self.mountHandler.sendCommand('GVT')
        self.data['HardwareVersion'] = self.mountHandler.sendCommand('GVZ')
        self.logger.info('FW: {0} Number: {1}'.format(self.mountHandler.sendCommand('GVN'), self.data['FW']))
        self.logger.info('Site Lon:{0}'.format(self.site_lon))
        self.logger.info('Site Lat:{0}'.format(self.site_lat))
        self.logger.info('Site Height:{0}'.format(self.site_height))
        self.loadActualModel()
        alignModel = self.getAlignmentModel()
        if not self.app.modeling.modelData and alignModel['RMS'] > 0:
            self.app.messageQueue.put('Model Data will be reconstructed from Mount Data')
            self.app.modeling.modelData = []
            for i in range(0, alignModel['number']):
                self.app.modeling.modelData.append({'ModelError': float(alignModel['points'][i][5]),
                                                    'RaError': float(alignModel['points'][i][5]) * math.sin(math.radians(alignModel['points'][i][6])),
                                                    'DecError': float(alignModel['points'][i][5]) * math.cos(math.radians(alignModel['points'][i][6])),
                                                    'Azimuth': float(alignModel['points'][i][3]),
                                                    'Altitude': float(alignModel['points'][i][4])})
        self.showAlignmentModel(alignModel)
