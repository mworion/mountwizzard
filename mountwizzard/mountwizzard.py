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
import os
import sys
import logging
import logging.handlers
import datetime
import json
# numerics
import math
import numpy
if platform.system() == 'Windows':
    # application handling
    from winreg import *
# commands to threads
from queue import Queue
# import for the PyQt5 Framework
from PyQt5 import QtCore
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
# matplotlib
from matplotlib import use
use('Qt5Agg')
from matplotlib import pyplot as plt
from matplotlib import figure as figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
# import the UI part, which is done via QT Designer and exported
from baseclasses import widget
from widgets import modelplotWindow
from widgets import imageWindow
from widgets import analyseWindow
from gui import wizzard_main_ui
from environment import environThread
# modeling
from modeling import modelThread
# import mount functions classes
from mount import mountThread
from relays import relays
from remote import remoteThread
from dome import domeThread
from indi import indi_client

if platform.system() == 'Windows':
    from automation import upload_thread
from wakeonlan import wol


class ShowModel(FigureCanvas):

    def __init__(self, parent=None):
        self.fig = figure.Figure(dpi=75, facecolor=(25/256, 25/256, 25/256))
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        FigureCanvas.updateGeometry(self)


class MountWizzardApp(widget.MwWidget):
    logger = logging.getLogger(__name__)

    def __init__(self):
        super(MountWizzardApp, self).__init__()
        # setting up communication queues for inter thread communication
        self.mountCommandQueue = Queue()
        self.modelLogQueue = Queue()
        self.modelCommandQueue = Queue()
        self.messageQueue = Queue()
        self.imageQueue = Queue()
        self.commandDataQueue = Queue()
        self.INDISendCommandQueue = Queue()
        self.INDIDataQueue = Queue()
        # loading config data
        self.config = self.loadConfigData()
        # initializing the gui
        self.ui = wizzard_main_ui.Ui_MainWindow()
        self.ui.setupUi(self)
        # special setups for gui including box for matplotlib. margins to 0
        self.initUI()
        self.setWindowTitle('MountWizzard ' + BUILD_NO)
        self.ui.le_mwWorkingDir.setText(os.getcwd())
        helper = QVBoxLayout(self.ui.model)
        helper.setContentsMargins(0, 0, 0, 0)
        self.modelWidget = ShowModel(self.ui.model)
        # noinspection PyArgumentList
        helper.addWidget(self.modelWidget)
        # instantiating all subclasses and connecting thread signals
        self.relays = relays.Relays(self)
        self.mount = mountThread.Mount(self)
        self.mount.signalMountConnected.connect(self.setMountStatus)
        self.dome = domeThread.Dome(self)
        self.dome.signalDomeConnected.connect(self.setDomeStatus)
        self.INDIworker = indi_client.INDIClient(self)
        self.INDIthread = QThread()
        self.INDIworker.moveToThread(self.INDIthread)
        self.INDIthread.started.connect(self.INDIworker.run)
        self.INDIworker.status.connect(self.setINDIStatus)
        self.environment = environThread.Environment(self)
        if platform.system() == 'Windows':
            self.data = upload_thread.DataUploadToMount(self)
        self.modeling = modelThread.Modeling(self)
        self.analyseWindow = analyseWindow.AnalyseWindow(self)
        self.modelWindow = modelplotWindow.ModelPlotWindow(self)
        self.imageWindow = imageWindow.ImagesWindow(self)
        # starting the threads
        self.mount.start()
        if platform.system() == 'Windows':
            self.checkASCOM()
            self.dome.start()
            self.data.start()
        self.environment.signalEnvironmentConnected.connect(self.setEnvironmentStatus)
        self.environment.start()
        self.modeling.signalModelConnected.connect(self.setCameraPlateStatus)
        self.modeling.start()
        self.remote = remoteThread.Remote(self)
        self.remote.signalRemoteShutdown.connect(self.saveConfigQuit)
        self.enableDisableRemoteAccess()
        self.enableDisableINDI()
        self.initConfig()
        self.mappingFunctions()
        self.checkPlatformDependableMenus()
        # starting loop for cyclic data to gui from threads
        self.mainLoop()

    # noinspection PyArgumentList
    def mappingFunctions(self):
        self.ui.btn_mountQuit.clicked.connect(self.saveConfigQuit)
        self.ui.btn_mountSave.clicked.connect(self.saveConfig)
        self.ui.btn_mountBoot.clicked.connect(self.mountBoot)
        self.ui.btn_mountShutdown.clicked.connect(self.mountShutdown)
        self.ui.btn_mountPark.clicked.connect(lambda: self.mountCommandQueue.put('hP'))
        self.ui.btn_mountUnpark.clicked.connect(lambda: self.mountCommandQueue.put('PO'))
        self.ui.btn_startTracking.clicked.connect(lambda: self.mountCommandQueue.put('AP'))
        self.ui.btn_stopTracking.clicked.connect(lambda: self.mountCommandQueue.put('RT9'))
        self.ui.btn_setTrackingLunar.clicked.connect(lambda: self.mountCommandQueue.put('RT0'))
        self.ui.btn_setTrackingSolar.clicked.connect(lambda: self.mountCommandQueue.put('RT1'))
        self.ui.btn_setTrackingSideral.clicked.connect(lambda: self.mountCommandQueue.put('RT2'))
        self.ui.btn_stop.clicked.connect(lambda: self.mountCommandQueue.put('STOP'))
        self.ui.btn_mountPos1.clicked.connect(self.mountPosition1)
        self.ui.btn_mountPos2.clicked.connect(self.mountPosition2)
        self.ui.btn_mountPos3.clicked.connect(self.mountPosition3)
        self.ui.btn_mountPos4.clicked.connect(self.mountPosition4)
        self.ui.btn_mountPos5.clicked.connect(self.mountPosition5)
        self.ui.btn_mountPos6.clicked.connect(self.mountPosition6)
        self.ui.le_parkPos1Text.textChanged.connect(lambda: self.ui.btn_mountPos1.setText(self.ui.le_parkPos1Text.text()))
        self.ui.le_parkPos2Text.textChanged.connect(lambda: self.ui.btn_mountPos2.setText(self.ui.le_parkPos2Text.text()))
        self.ui.le_parkPos3Text.textChanged.connect(lambda: self.ui.btn_mountPos3.setText(self.ui.le_parkPos3Text.text()))
        self.ui.le_parkPos4Text.textChanged.connect(lambda: self.ui.btn_mountPos4.setText(self.ui.le_parkPos4Text.text()))
        self.ui.le_parkPos5Text.textChanged.connect(lambda: self.ui.btn_mountPos5.setText(self.ui.le_parkPos5Text.text()))
        self.ui.le_parkPos6Text.textChanged.connect(lambda: self.ui.btn_mountPos6.setText(self.ui.le_parkPos6Text.text()))
        self.ui.btn_setHorizonLimitHigh.clicked.connect(self.setHorizonLimitHigh)
        self.ui.btn_setHorizonLimitLow.clicked.connect(self.setHorizonLimitLow)
        self.ui.btn_setSlewRate.clicked.connect(self.setSlewRate)
        self.ui.btn_setDualTracking.clicked.connect(self.setDualTracking)
        self.ui.btn_setUnattendedFlip.clicked.connect(self.setUnattendedFlip)
        if platform.system() == 'Windows':
            self.ui.btn_setupMountDriver.clicked.connect(self.mount.MountAscom.setupDriver)
            self.ui.btn_setupDomeDriver.clicked.connect(lambda: self.dome.setupDriver())
            self.ui.btn_setupAscomEnvironmentDriver.clicked.connect(lambda: self.environment.setupDriver())
        self.ui.btn_setRefractionParameters.clicked.connect(lambda: self.mountCommandQueue.put('SetRefractionParameter'))
        self.ui.btn_runBaseModel.clicked.connect(lambda: self.modelCommandQueue.put('RunBaseModel'))
        self.ui.btn_cancelModel.clicked.connect(self.modeling.cancelModeling)
        self.ui.btn_cancelAnalyseModel.clicked.connect(self.modeling.cancelAnalyseModeling)
        self.ui.btn_runRefinementModel.clicked.connect(lambda: self.modelCommandQueue.put('RunRefinementModel'))
        # self.ui.btn_runBoostModel.clicked.connect(lambda: self.modelCommandQueue.put('RunBoostModel'))
        self.ui.btn_runBatchModel.clicked.connect(lambda: self.modelCommandQueue.put('RunBatchModel'))
        self.ui.btn_clearAlignmentModel.clicked.connect(lambda: self.modelCommandQueue.put('ClearAlignmentModel'))
        self.ui.btn_selectHorizonPointsFileName.clicked.connect(self.modelWindow.selectHorizonPointsFileName)
        self.ui.checkUseMinimumHorizonLine.stateChanged.connect(self.modelWindow.selectHorizonPointsMode)
        self.ui.checkUseFileHorizonLine.stateChanged.connect(self.modelWindow.selectHorizonPointsMode)
        self.ui.altitudeMinimumHorizon.valueChanged.connect(self.modelWindow.selectHorizonPointsMode)
        self.ui.btn_selectModelPointsFileName.clicked.connect(self.selectModelPointsFileName)
        self.ui.btn_selectAnalyseFileName.clicked.connect(self.selectAnalyseFileName)
        self.ui.btn_showActualModel.clicked.connect(lambda: self.mountCommandQueue.put('ShowAlignmentModel'))
        self.ui.checkPolarPlot.clicked.connect(self.setShowAlignmentModelMode)
        self.ui.btn_setRefractionCorrection.clicked.connect(self.setRefractionCorrection)
        self.ui.btn_runTargetRMSAlignment.clicked.connect(lambda: self.mountCommandQueue.put('RunTargetRMSAlignment'))
        self.ui.btn_deleteWorstPoint.clicked.connect(lambda: self.mountCommandQueue.put('DeleteWorstPoint'))
        self.ui.btn_plateSolveSync.clicked.connect(lambda: self.modelCommandQueue.put('PlateSolveSync'))
        self.ui.btn_deletePoints.clicked.connect(lambda: self.modelCommandQueue.put('DeletePoints'))
        self.ui.btn_flipMount.clicked.connect(lambda: self.mountCommandQueue.put('FLIP'))
        self.ui.btn_loadRefinementPoints.clicked.connect(lambda: self.modelCommandQueue.put('LoadRefinementPoints'))
        self.ui.btn_loadBasePoints.clicked.connect(lambda: self.modelCommandQueue.put('LoadBasePoints'))
        self.ui.btn_saveBackupModel.clicked.connect(lambda: self.mountCommandQueue.put('SaveBackupModel'))
        self.ui.btn_loadBackupModel.clicked.connect(lambda: self.mountCommandQueue.put('LoadBackupModel'))
        self.ui.btn_saveSimpleModel.clicked.connect(lambda: self.mountCommandQueue.put('SaveSimpleModel'))
        self.ui.btn_loadSimpleModel.clicked.connect(lambda: self.mountCommandQueue.put('LoadSimpleModel'))
        self.ui.btn_saveRefinementModel.clicked.connect(lambda: self.mountCommandQueue.put('SaveRefinementModel'))
        self.ui.btn_loadRefinementModel.clicked.connect(lambda: self.mountCommandQueue.put('LoadRefinementModel'))
        self.ui.btn_saveBaseModel.clicked.connect(lambda: self.mountCommandQueue.put('SaveBaseModel'))
        self.ui.btn_loadBaseModel.clicked.connect(lambda: self.mountCommandQueue.put('LoadBaseModel'))
        self.ui.btn_saveDSO1Model.clicked.connect(lambda: self.mountCommandQueue.put('SaveDSO1Model'))
        self.ui.btn_loadDSO1Model.clicked.connect(lambda: self.mountCommandQueue.put('LoadDSO1Model'))
        self.ui.btn_saveDSO2Model.clicked.connect(lambda: self.mountCommandQueue.put('SaveDSO2Model'))
        self.ui.btn_loadDSO2Model.clicked.connect(lambda: self.mountCommandQueue.put('LoadDSO2Model'))
        self.ui.btn_generateDSOPoints.clicked.connect(lambda: self.modelCommandQueue.put('GenerateDSOPoints'))
        self.ui.numberHoursDSO.valueChanged.connect(lambda: self.modelCommandQueue.put('GenerateDSOPoints'))
        self.ui.numberPointsDSO.valueChanged.connect(lambda: self.modelCommandQueue.put('GenerateDSOPoints'))
        self.ui.numberHoursPreview.valueChanged.connect(lambda: self.modelCommandQueue.put('GenerateDSOPoints'))
        self.ui.btn_generateDensePoints.clicked.connect(lambda: self.modelCommandQueue.put('GenerateDensePoints'))
        self.ui.btn_generateNormalPoints.clicked.connect(lambda: self.modelCommandQueue.put('GenerateNormalPoints'))
        self.ui.btn_generateGridPoints.clicked.connect(lambda: self.modelCommandQueue.put('GenerateGridPoints'))
        self.ui.numberGridPointsRow.valueChanged.connect(lambda: self.modelCommandQueue.put('GenerateGridPoints'))
        self.ui.numberGridPointsCol.valueChanged.connect(lambda: self.modelCommandQueue.put('GenerateGridPoints'))
        self.ui.altitudeMin.valueChanged.connect(lambda: self.modelCommandQueue.put('GenerateGridPoints'))
        self.ui.altitudeMax.valueChanged.connect(lambda: self.modelCommandQueue.put('GenerateGridPoints'))
        self.ui.btn_generateBasePoints.clicked.connect(lambda: self.modelCommandQueue.put('GenerateBasePoints'))
        self.ui.btn_runCheckModel.clicked.connect(lambda: self.modelCommandQueue.put('RunCheckModel'))
        self.ui.btn_runAllModel.clicked.connect(lambda: self.modelCommandQueue.put('RunAllModel'))
        self.ui.btn_runTimeChangeModel.clicked.connect(lambda: self.modelCommandQueue.put('RunTimeChangeModel'))
        self.ui.btn_runHystereseModel.clicked.connect(lambda: self.modelCommandQueue.put('RunHystereseModel'))
        self.ui.btn_openAnalyseWindow.clicked.connect(self.analyseWindow.showAnalyseWindow)
        self.ui.btn_openModelingPlotWindow.clicked.connect(self.modelWindow.showModelingPlotWindow)
        self.ui.btn_openImageWindow.clicked.connect(self.imageWindow.showImageWindow)
        self.ui.btn_runCheckModel.clicked.connect(lambda: self.modelCommandQueue.put('RunCheckModel'))
        self.ui.checkRemoteAccess.stateChanged.connect(self.enableDisableRemoteAccess)
        self.ui.checkEnableINDI.stateChanged.connect(self.enableDisableINDI)

    def enableDisableRemoteAccess(self):
        if self.ui.checkRemoteAccess.isChecked():
            self.remote.start()
        else:
            self.remote.terminate()

    def enableDisableINDI(self):
        # todo: enable INDI Subsystem as soon as INDI is tested
        # switch on and off INDI subsystem by setting INDICamera available to True (than it will occur in Imaging as well
        if not self.modeling.INDICamera.appAvailable:
            self.ui.checkEnableINDI.setChecked(False)
            self.ui.settingsTabWidget.removeTab(3)
        if self.ui.checkEnableINDI.isChecked():
            self.INDIthread.start()
        else:
            self.INDIworker.stop()
            self.INDIthread.quit()
            self.INDIthread.wait()

    def mountBoot(self):
        wol.send_magic_packet(self.ui.le_mountMAC.text().strip())
        self.messageQueue.put('Send WOL and boot mount !')
        self.logger.debug('Send WOL packet and boot Mount')

    def mountShutdown(self):
        self.mountCommandQueue.put('Shutdown')

    def showModelErrorPolar(self):
        if not self.modeling.modelData:
            return
        data = dict()
        for i in range(0, len(self.modeling.modelData)):
            for (keyData, valueData) in self.modeling.modelData[i].items():
                if keyData == 'azimuth':
                    return
                if keyData in data:
                    data[keyData].append(valueData)
                else:
                    data[keyData] = [valueData]
        self.modelWidget.fig.clf()
        self.modelWidget.axes = self.modelWidget.fig.add_subplot(1, 1, 1, polar=True)
        self.modelWidget.axes.grid(True, color='gray')
        self.modelWidget.fig.subplots_adjust(left=0.025, right=0.975, bottom=0.075, top=0.925)
        self.modelWidget.axes.set_facecolor((32/256, 32/256, 32/256))
        self.modelWidget.axes.tick_params(axis='x', colors='white')
        self.modelWidget.axes.tick_params(axis='y', colors='white')
        self.modelWidget.axes.set_theta_zero_location('N')
        self.modelWidget.axes.set_theta_direction(-1)
        self.modelWidget.axes.set_yticks(range(0, 90, 10))
        yLabel = ['', '80', '', '60', '', '40', '', '20', '', '0']
        self.modelWidget.axes.set_yticklabels(yLabel, color='white')
        azimuth = numpy.asarray(data['Azimuth'])
        altitude = numpy.asarray(data['Altitude'])
        # self.modelWidget.axes.plot(azimuth / 180.0 * math.pi, 90 - altitude, color='black')
        cm = plt.cm.get_cmap('RdYlGn_r')
        colors = numpy.asarray(data['ModelError'])
        # noinspection PyTypeChecker
        scaleError = int(max(colors) / 4 + 1) * 4
        area = [125 if x >= max(colors) else 50 for x in data['ModelError']]
        theta = azimuth / 180.0 * math.pi
        r = 90 - altitude
        scatter = self.modelWidget.axes.scatter(theta, r, c=colors, vmin=0, vmax=scaleError, s=area, cmap=cm)
        scatter.set_alpha(0.75)
        colorbar = self.modelWidget.fig.colorbar(scatter)
        colorbar.set_label('Error [arcsec]', color='white')
        plt.setp(plt.getp(colorbar.ax.axes, 'yticklabels'), color='white')
        self.modelWidget.axes.set_rmax(90)
        self.modelWidget.axes.set_rmin(0)
        self.modelWidget.draw()

    def checkASCOM(self):
        appAvailable, appName, appInstallPath = self.checkRegistrationKeys('ASCOM Platform')
        if appAvailable:
            self.messageQueue.put('Found: {0}'.format(appName))
            self.logger.info('Name: {0}, Path: {1}'.format(appName, appInstallPath))
        else:
            self.logger.warning('Application ASCOM not found on computer')

    def checkRegistrationKeys(self, appSearchName):
        if platform.machine().endswith('64'):
            regPath = 'SOFTWARE\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall'                                # regpath for 64 bit windows
        else:
            regPath = 'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall'                                             # regpath for 32 bit windows
        appInstallPath = ''
        appInstalled = False
        appName = ''
        try:
            key = OpenKey(HKEY_LOCAL_MACHINE, regPath)                                                                      # open registry
            for i in range(0, QueryInfoKey(key)[0]):                                                                        # run through all registry application
                name = EnumKey(key, i)                                                                                      # get registry names of applications
                subkey = OpenKey(key, name)                                                                                 # open subkeys of applications
                for j in range(0, QueryInfoKey(subkey)[1]):                                                                 # run through all subkeys
                    values = EnumValue(subkey, j)
                    if values[0] == 'DisplayName':
                        appName = values[1]
                    if values[0] == 'InstallLocation':
                        appInstallPath = values[1]
                if appSearchName in appName:
                    appInstalled = True
                    CloseKey(subkey)
                    break
                else:
                    CloseKey(subkey)                                                                                        # closing the subkey for later usage
            CloseKey(key)                                                                                                   # closing main key for later usage
            if not appInstalled:
                appInstallPath = ''
                appName = ''
        except Exception as e:
            self.logger.debug('Name: {0}, Path: {1}, error: {2}'.format(appName, appInstallPath, e))
        finally:
            return appInstalled, appName, appInstallPath

    def checkPlatformDependableMenus(self):
        if platform.system() != 'Windows':
            self.ui.settingsTabWidget.removeTab(5)
            self.ui.settingsTabWidget.removeTab(2)

    def initConfig(self):
        try:
            if 'ParkPosText1' in self.config:
                self.ui.le_parkPos1Text.setText(self.config['ParkPosText1'])
                self.ui.btn_mountPos1.setText(self.ui.le_parkPos1Text.text())
            if 'ParkPosAlt1' in self.config:
                self.ui.le_altParkPos1.setText(self.config['ParkPosAlt1'])
            if 'ParkPosAz1' in self.config:
                self.ui.le_azParkPos1.setText(self.config['ParkPosAz1'])
            if 'ParkPosText2' in self.config:
                self.ui.le_parkPos2Text.setText(self.config['ParkPosText2'])
                self.ui.btn_mountPos2.setText(self.ui.le_parkPos2Text.text())
            if 'ParkPosAlt2' in self.config:
                self.ui.le_altParkPos2.setText(self.config['ParkPosAlt2'])
            if 'ParkPosAz2' in self.config:
                self.ui.le_azParkPos2.setText(self.config['ParkPosAz2'])
            if 'ParkPosText3' in self.config:
                self.ui.le_parkPos3Text.setText(self.config['ParkPosText3'])
                self.ui.btn_mountPos3.setText(self.ui.le_parkPos3Text.text())
            if 'ParkPosAlt3' in self.config:
                self.ui.le_altParkPos3.setText(self.config['ParkPosAlt3'])
            if 'ParkPosAz3' in self.config:
                self.ui.le_azParkPos3.setText(self.config['ParkPosAz3'])
            if 'ParkPosText4' in self.config:
                self.ui.le_parkPos4Text.setText(self.config['ParkPosText4'])
                self.ui.btn_mountPos4.setText(self.ui.le_parkPos4Text.text())
            if 'ParkPosAlt4' in self.config:
                self.ui.le_altParkPos4.setText(self.config['ParkPosAlt4'])
            if 'ParkPosAz4' in self.config:
                self.ui.le_azParkPos4.setText(self.config['ParkPosAz4'])
            if 'ParkPosText5' in self.config:
                self.ui.le_parkPos5Text.setText(self.config['ParkPosText5'])
                self.ui.btn_mountPos5.setText(self.ui.le_parkPos5Text.text())
            if 'ParkPosAlt5' in self.config:
                self.ui.le_altParkPos5.setText(self.config['ParkPosAlt5'])
            if 'ParkPosAz5' in self.config:
                self.ui.le_azParkPos5.setText(self.config['ParkPosAz5'])
            if 'ParkPosText6' in self.config:
                self.ui.le_parkPos6Text.setText(self.config['ParkPosText6'])
                self.ui.btn_mountPos6.setText(self.ui.le_parkPos6Text.text())
            if 'ParkPosAlt6' in self.config:
                self.ui.le_altParkPos6.setText(self.config['ParkPosAlt6'])
            if 'ParkPosAz6' in self.config:
                self.ui.le_azParkPos6.setText(self.config['ParkPosAz6'])
            if 'ModelPointsFileName' in self.config:
                self.ui.le_modelPointsFileName.setText(self.config['ModelPointsFileName'])
            if 'CameraBin' in self.config:
                self.ui.cameraBin.setValue(self.config['CameraBin'])
            if 'CameraExposure' in self.config:
                self.ui.cameraExposure.setValue(self.config['CameraExposure'])
            if 'ISOSetting' in self.config:
                self.ui.isoSetting.setValue(self.config['ISOSetting'])
            if 'CheckFastDownload' in self.config:
                self.ui.checkFastDownload.setChecked(self.config['CheckFastDownload'])
            if 'SettlingTime' in self.config:
                self.ui.settlingTime.setValue(self.config['SettlingTime'])
            if 'CheckUseBlindSolve' in self.config:
                self.ui.checkUseBlindSolve.setChecked(self.config['CheckUseBlindSolve'])
            if 'TargetRMS' in self.config:
                self.ui.targetRMS.setValue(self.config['TargetRMS'])
            if 'PixelSize' in self.config:
                self.ui.pixelSize.setValue(self.config['PixelSize'])
            if 'FocalLength' in self.config:
                self.ui.focalLength.setValue(self.config['FocalLength'])
            if 'ScaleSubframe' in self.config:
                self.ui.scaleSubframe.setValue(self.config['ScaleSubframe'])
            if 'CheckDoSubframe' in self.config:
                self.ui.checkDoSubframe.setChecked(self.config['CheckDoSubframe'])
            if 'CheckKeepImages' in self.config:
                self.ui.checkKeepImages.setChecked(self.config['CheckKeepImages'])
            if 'CheckRunTrackingWidget' in self.config:
                self.modelWindow.ui.checkRunTrackingWidget.setChecked(self.config['CheckRunTrackingWidget'])
            if 'CheckClearModelFirst' in self.config:
                self.ui.checkClearModelFirst.setChecked(self.config['CheckClearModelFirst'])
            if 'CheckKeepRefinement' in self.config:
                self.ui.checkKeepRefinement.setChecked(self.config['CheckKeepRefinement'])
            if 'AltitudeBase' in self.config:
                self.ui.altitudeBase.setValue(self.config['AltitudeBase'])
            if 'AzimuthBase' in self.config:
                self.ui.azimuthBase.setValue(self.config['AzimuthBase'])
            if 'NumberGridPointsCol' in self.config:
                self.ui.numberGridPointsCol.setValue(self.config['NumberGridPointsCol'])
            if 'NumberGridPointsRow' in self.config:
                self.ui.numberGridPointsRow.setValue(self.config['NumberGridPointsRow'])
            if 'AltitudeMin' in self.config:
                self.ui.altitudeMin.setValue(self.config['AltitudeMin'])
            if 'AltitudeMax' in self.config:
                self.ui.altitudeMax.setValue(self.config['AltitudeMax'])
            if 'NumberPointsDSO' in self.config:
                self.ui.numberPointsDSO.setValue(self.config['NumberPointsDSO'])
            if 'NumberHoursDSO' in self.config:
                self.ui.numberHoursDSO.setValue(self.config['NumberHoursDSO'])
            if 'AnalyseFileName' in self.config:
                self.ui.le_analyseFileName.setText(self.config['AnalyseFileName'])
            if 'AltitudeTimeChange' in self.config:
                self.ui.altitudeTimeChange.setValue(self.config['AltitudeTimeChange'])
            if 'AzimuthTimeChange' in self.config:
                self.ui.azimuthTimeChange.setValue(self.config['AzimuthTimeChange'])
            if 'NumberRunsTimeChange' in self.config:
                self.ui.numberRunsTimeChange.setValue(self.config['NumberRunsTimeChange'])
            if 'DelayTimeTimeChange' in self.config:
                self.ui.delayTimeTimeChange.setValue(self.config['DelayTimeTimeChange'])
            if 'AltitudeHysterese1' in self.config:
                self.ui.altitudeHysterese1.setValue(self.config['AltitudeHysterese1'])
            if 'AltitudeHysterese2' in self.config:
                self.ui.altitudeHysterese2.setValue(self.config['AltitudeHysterese2'])
            if 'AzimuthHysterese1' in self.config:
                self.ui.azimuthHysterese1.setValue(self.config['AzimuthHysterese1'])
            if 'AzimuthHysterese2' in self.config:
                self.ui.azimuthHysterese2.setValue(self.config['AzimuthHysterese2'])
            if 'NumberRunsHysterese' in self.config:
                self.ui.numberRunsHysterese.setValue(self.config['NumberRunsHysterese'])
            if 'DelayTimeHysterese' in self.config:
                self.ui.delayTimeHysterese.setValue(self.config['DelayTimeHysterese'])
            if 'WindowPositionX' in self.config:
                self.move(self.config['WindowPositionX'], self.config['WindowPositionY'])
            if 'CheckRemoteAccess' in self.config:
                self.ui.checkRemoteAccess.setChecked(self.config['CheckRemoteAccess'])
        except Exception as e:
            self.logger.error('Item in config.cfg not be initialize, error:{0}'.format(e))
        finally:
            pass

    def storeConfig(self):
        self.config['ParkPosText1'] = self.ui.le_parkPos1Text.text()
        self.config['ParkPosAlt1'] = self.ui.le_altParkPos1.text()
        self.config['ParkPosAz1'] = self.ui.le_azParkPos1.text()
        self.config['ParkPosText2'] = self.ui.le_parkPos2Text.text()
        self.config['ParkPosAlt2'] = self.ui.le_altParkPos2.text()
        self.config['ParkPosAz2'] = self.ui.le_azParkPos2.text()
        self.config['ParkPosText3'] = self.ui.le_parkPos3Text.text()
        self.config['ParkPosAlt3'] = self.ui.le_altParkPos3.text()
        self.config['ParkPosAz3'] = self.ui.le_azParkPos3.text()
        self.config['ParkPosText4'] = self.ui.le_parkPos4Text.text()
        self.config['ParkPosAlt4'] = self.ui.le_altParkPos4.text()
        self.config['ParkPosAz4'] = self.ui.le_azParkPos4.text()
        self.config['ParkPosText5'] = self.ui.le_parkPos5Text.text()
        self.config['ParkPosAlt5'] = self.ui.le_altParkPos5.text()
        self.config['ParkPosAz5'] = self.ui.le_azParkPos5.text()
        self.config['ParkPosText6'] = self.ui.le_parkPos6Text.text()
        self.config['ParkPosAlt6'] = self.ui.le_altParkPos6.text()
        self.config['ParkPosAz6'] = self.ui.le_azParkPos6.text()
        self.config['ModelPointsFileName'] = self.ui.le_modelPointsFileName.text()
        self.config['CameraBin'] = self.ui.cameraBin.value()
        self.config['CameraExposure'] = self.ui.cameraExposure.value()
        self.config['CheckFastDownload'] = self.ui.checkFastDownload.isChecked()
        self.config['ISOSetting'] = self.ui.isoSetting.value()
        self.config['SettlingTime'] = self.ui.settlingTime.value()
        self.config['CheckUseBlindSolve'] = self.ui.checkUseBlindSolve.isChecked()
        self.config['TargetRMS'] = self.ui.targetRMS.value()
        self.config['PixelSize'] = self.ui.pixelSize.value()
        self.config['FocalLength'] = self.ui.focalLength.value()
        self.config['ScaleSubframe'] = self.ui.scaleSubframe.value()
        self.config['CheckDoSubframe'] = self.ui.checkDoSubframe.isChecked()
        self.config['CheckKeepImages'] = self.ui.checkKeepImages.isChecked()
        self.config['CheckRunTrackingWidget'] = self.modelWindow.ui.checkRunTrackingWidget.isChecked()
        self.config['AltitudeBase'] = self.ui.altitudeBase.value()
        self.config['AzimuthBase'] = self.ui.azimuthBase.value()
        self.config['NumberGridPointsRow'] = self.ui.numberGridPointsRow.value()
        self.config['NumberGridPointsCol'] = self.ui.numberGridPointsCol.value()
        self.config['AltitudeMin'] = self.ui.altitudeMin.value()
        self.config['AltitudeMax'] = self.ui.altitudeMax.value()
        self.config['NumberPointsDSO'] = self.ui.numberPointsDSO.value()
        self.config['NumberHoursDSO'] = self.ui.numberHoursDSO.value()
        self.config['WindowPositionX'] = self.pos().x()
        self.config['WindowPositionY'] = self.pos().y()
        self.config['AnalyseFileName'] = self.ui.le_analyseFileName.text()
        self.config['AltitudeTimeChange'] = self.ui.altitudeTimeChange.value()
        self.config['AzimuthTimeChange'] = self.ui.azimuthTimeChange.value()
        self.config['NumberRunsTimeChange'] = self.ui.numberRunsTimeChange.value()
        self.config['DelayTimeTimeChange'] = self.ui.delayTimeTimeChange.value()
        self.config['AltitudeHysterese1'] = self.ui.altitudeHysterese1.value()
        self.config['AltitudeHysterese2'] = self.ui.altitudeHysterese2.value()
        self.config['AzimuthHysterese1'] = self.ui.azimuthHysterese1.value()
        self.config['AzimuthHysterese2'] = self.ui.azimuthHysterese2.value()
        self.config['NumberRunsHysterese'] = self.ui.numberRunsHysterese.value()
        self.config['DelayTimeHysterese'] = self.ui.delayTimeHysterese.value()
        self.config['CheckClearModelFirst'] = self.ui.checkClearModelFirst.isChecked()
        self.config['CheckKeepRefinement'] = self.ui.checkKeepRefinement.isChecked()
        self.config['CheckRemoteAccess'] = self.ui.checkRemoteAccess.isChecked()

    def loadConfigData(self):
        try:
            with open('config/config.cfg', 'r') as data_file:
                return json.load(data_file)
        except Exception as e:
            self.messageQueue.put('Config.cfg could not be loaded !')
            self.logger.error('Item in config.cfg not loaded error:{0}'.format(e))
            return {}

    def saveConfigData(self):
        self.storeConfig()
        self.mount.storeConfig()
        self.modeling.storeConfig()
        self.environment.storeConfig()
        if platform.system() == 'Windows':
            self.dome.storeConfig()
            self.data.storeConfig()
        self.modelWindow.storeConfig()
        self.imageWindow.storeConfig()
        self.analyseWindow.storeConfig()
        self.relays.storeConfig()
        self.INDIworker.storeConfig()
        try:
            if not os.path.isdir(os.getcwd() + '/config'):
                os.makedirs(os.getcwd() + '/config')
            with open('config/config.cfg', 'w') as outfile:
                json.dump(self.config, outfile)
            outfile.close()
        except Exception as e:
            self.messageQueue.put('Config.cfg could not be saved !')
            self.logger.error('Item in config.cfg not saved error {0}'.format(e))
            return
        self.mount.saveActualModel()

    def saveConfigQuit(self):
        self.saveConfigData()
        # noinspection PyArgumentList
        QCoreApplication.instance().quit()

    def saveConfig(self):
        self.saveConfigData()
        self.messageQueue.put('Configuration saved.')

    def selectModelPointsFileName(self):
        dlg = QFileDialog()
        dlg.setViewMode(QFileDialog.List)
        dlg.setNameFilter("Text files (*.txt)")
        dlg.setFileMode(QFileDialog.ExistingFile)
        # noinspection PyArgumentList
        a = dlg.getOpenFileName(self, 'Open file', os.getcwd()+'/config', 'Text files (*.txt)')
        if a[0] != '':
            self.ui.le_modelPointsFileName.setText(os.path.basename(a[0]))
        else:
            self.logger.warning('no file selected')

    def selectAnalyseFileName(self):
        dlg = QFileDialog()
        dlg.setViewMode(QFileDialog.List)
        dlg.setNameFilter("Data Files (*.dat)")
        dlg.setFileMode(QFileDialog.AnyFile)
        # noinspection PyArgumentList
        a = dlg.getOpenFileName(self, 'Open file', os.getcwd()+'/analysedata', 'Data Files (*.dat)')
        if a[0] != '':
            self.ui.le_analyseFileName.setText(os.path.basename(a[0]))
        else:
            self.logger.warning('no file selected')

    def setHorizonLimitHigh(self):
        _value = int(self.ui.le_horizonLimitHigh.text())
        if _value < 0:
            _value = 0
        elif _value > 90:
            _value = 90
        self.mountCommandQueue.put('Sh+{0:02d}'.format(_value))

    def setHorizonLimitLow(self):
        _value = int(self.ui.le_horizonLimitLow.text())
        if _value < 0:
            _value = 0
        elif _value > 90:
            _value = 90
        self.mountCommandQueue.put('So+{0:02d}'.format(_value))

    def setDualTracking(self):
        _value = self.ui.le_telescopeDualTrack.text()
        if _value == 'ON':
            _value = 0
            self.ui.le_telescopeDualTrack.setText('OFF')
        else:
            _value = 1
            self.ui.le_telescopeDualTrack.setText('ON')
        self.mountCommandQueue.put('Sdat{0:01d}'.format(_value))

    def setUnattendedFlip(self):
        _value = self.ui.le_telescopeUnattendedFlip.text()
        if _value == 'ON':
            _value = 0
            self.ui.le_telescopeUnattendedFlip.setText('OFF')
        else:
            _value = 1
            self.ui.le_telescopeUnattendedFlip.setText('ON')
        self.mountCommandQueue.put('Suaf{0: 01d}'.format(_value))

    def setSlewRate(self):
        _value = int(self.ui.le_slewRate.text())
        if _value < 1:
            _value = 1
        elif _value > 15:
            _value = 15
        self.mountCommandQueue.put('Sw{0:02d}'.format(_value))

    def setRefractionCorrection(self):
        _value = self.ui.le_refractionStatus.text()
        if _value == 'ON':
            _value = 0
            self.ui.le_refractionStatus.setText('OFF')
        else:
            _value = 1
            self.ui.le_refractionStatus.setText('ON')
        self.mountCommandQueue.put('SREF{0: 01d}'.format(_value))

    def mountPosition1(self):
        self.mountCommandQueue.put('PO')                                                                                         # unpark first
        self.mountCommandQueue.put('Sz{0:03d}*00'.format(int(self.ui.le_azParkPos1.text())))                                     # set az
        self.mountCommandQueue.put('Sa+{0:02d}*00'.format(int(self.ui.le_altParkPos1.text())))                                   # set alt
        self.mountCommandQueue.put('MA')                                                                                         # start Slewing

    def mountPosition2(self):
        self.mountCommandQueue.put('PO')                                                                                         # unpark first
        self.mountCommandQueue.put('Sz{0:03d}*00'.format(int(self.ui.le_azParkPos2.text())))                                     # set az
        self.mountCommandQueue.put('Sa+{0:02d}*00'.format(int(self.ui.le_altParkPos2.text())))                                   # set alt
        self.mountCommandQueue.put('MA')                                                                                         # start Slewing

    def mountPosition3(self):
        self.mountCommandQueue.put('PO')                                                                                         # unpark first
        self.mountCommandQueue.put('Sz{0:03d}*00'.format(int(self.ui.le_azParkPos3.text())))                                     # set az
        self.mountCommandQueue.put('Sa+{0:02d}*00'.format(int(self.ui.le_altParkPos3.text())))                                   # set alt
        self.mountCommandQueue.put('MA')                                                                                         # start Slewing

    def mountPosition4(self):
        self.mountCommandQueue.put('PO')                                                                                         # unpark first
        self.mountCommandQueue.put('Sz{0:03d}*00'.format(int(self.ui.le_azParkPos4.text())))                                     # set az
        self.mountCommandQueue.put('Sa+{0:02d}*00'.format(int(self.ui.le_altParkPos4.text())))                                   # set alt
        self.mountCommandQueue.put('MA')                                                                                         # start Slewing

    def mountPosition5(self):
        self.mountCommandQueue.put('PO')                                                                                         # unpark first
        self.mountCommandQueue.put('Sz{0:03d}*00'.format(int(self.ui.le_azParkPos5.text())))                                     # set az
        self.mountCommandQueue.put('Sa+{0:02d}*00'.format(int(self.ui.le_altParkPos5.text())))                                   # set alt
        self.mountCommandQueue.put('MA')                                                                                         # start Slewing

    def mountPosition6(self):
        self.mountCommandQueue.put('PO')                                                                                         # unpark first
        self.mountCommandQueue.put('Sz{0:03d}*00'.format(int(self.ui.le_azParkPos6.text())))                                     # set az
        self.mountCommandQueue.put('Sa+{0:02d}*00'.format(int(self.ui.le_altParkPos6.text())))                                   # set alt
        self.mountCommandQueue.put('MA')                                                                                         # start Slewing

    @QtCore.Slot(int)
    def setINDIStatus(self, status):
        if status == 0:
            self.ui.le_INDIStatus.setText('UnconnectedState')
        elif status == 1:
            self.ui.le_INDIStatus.setText('HostLookupState')
        elif status == 2:
            self.ui.le_INDIStatus.setText('ConnectingState')
        elif status == 3:
            self.ui.le_INDIStatus.setText('ConnectedState')
        elif status == 6:
            self.ui.le_INDIStatus.setText('ClosingState')
        else:
            self.ui.le_INDIStatus.setText('Error')

    @QtCore.Slot(dict)
    def fillINDIData(self, data):
        if data['Name'] == 'Telescope':
            self.ui.le_INDITelescope.setText(data['value'])
        elif data['Name'] == 'CCD':
            self.ui.le_INDICCD.setText(data['value'])
        elif data['Name'] == 'WEATHER':
            self.ui.le_INDIWeather.setText(data['value'])
        elif data['Name'] == 'CameraStatus':
            self.imageWindow.ui.le_INDICameraStatus.setText(data['value'])

    def setShowAlignmentModelMode(self):
        if self.ui.checkPolarPlot.isChecked():
            self.ui.alignErrorStars.setVisible(False)
        else:
            self.ui.alignErrorStars.setVisible(True)

    @QtCore.Slot(bool)
    def setMountStatus(self, status):
        if status:
            self.ui.btn_driverMountConnected.setStyleSheet('QPushButton {background-color: green;}')
        else:
            self.ui.btn_driverMountConnected.setStyleSheet('QPushButton {background-color: red;}')

    @QtCore.Slot(dict)
    def fillMountData(self):
        for valueName in self.mount.data:
            if valueName == 'Reply':
                pass
            if valueName == 'DualAxisTracking':
                if self.mount.data[valueName] == '1':
                    self.ui.le_telescopeDualTrack.setText('ON')
                else:
                    self.ui.le_telescopeDualTrack.setText('OFF')
            if valueName == 'NumberAlignmentStars':
                self.ui.le_alignNumberStars.setText(str(self.mount.data[valueName]))
            if valueName == 'ModelRMSError':
                self.ui.le_alignErrorRMS.setText(str(self.mount.data[valueName]))
            if valueName == 'ModelErrorPosAngle':
                self.ui.le_alignErrorPosAngle.setText(str(self.mount.data[valueName]))
            if valueName == 'ModelPolarError':
                self.ui.le_alignErrorPolar.setText(str(self.mount.data[valueName]))
            if valueName == 'ModelOrthoError':
                self.ui.le_alignErrorOrtho.setText(str(self.mount.data[valueName]))
            if valueName == 'ModelTerms':
                self.ui.le_alignNumberTerms.setText(str(self.mount.data[valueName]))
            if valueName == 'ModelKnobTurnAz':
                self.ui.le_alignKnobTurnAz.setText(str(self.mount.data[valueName]))
            if valueName == 'ModelKnobTurnAlt':
                self.ui.le_alignKnobTurnAlt.setText(str(self.mount.data[valueName]))
            if valueName == 'ModelErrorAz':
                self.ui.le_alignErrorAz.setText(str(self.mount.data[valueName]))
            if valueName == 'ModelErrorAlt':
                self.ui.le_alignErrorAlt.setText(str(self.mount.data[valueName]))
            if valueName == 'ModelStarError':
                    self.ui.alignErrorStars.setText(self.mount.data[valueName])
            if valueName == 'CurrentHorizonLimitLow':
                self.ui.le_horizonLimitLow.setText(str(self.mount.data[valueName]))
            if valueName == 'CurrentHorizonLimitHigh':
                self.ui.le_horizonLimitHigh.setText(str(self.mount.data[valueName]))
            if valueName == 'CurrentSiteLongitude':
                self.ui.le_siteLongitude.setText(str(self.mount.data[valueName]))
            if valueName == 'CurrentSiteLatitude':
                self.ui.le_siteLatitude.setText(str(self.mount.data[valueName]))
            if valueName == 'CurrentSiteElevation':
                self.ui.le_siteElevation.setText(str(self.mount.data[valueName]))
            if valueName == 'JulianDate':
                self.ui.le_JulianDate.setText(str(self.mount.data[valueName]))
            if valueName == 'LocalSiderealTime':
                self.ui.le_localSiderealTime.setText(str(self.mount.data[valueName]))
            if valueName == 'TelescopeTempDEC':
                self.ui.le_telescopeTempDECMotor.setText(str(self.mount.data[valueName]))
            if valueName == 'RefractionTemperature':
                self.ui.le_refractionTemperature.setText(str(self.mount.data[valueName]))
            if valueName == 'RefractionPressure':
                self.ui.le_refractionPressure.setText(str(self.mount.data[valueName]))
            if valueName == 'RefractionStatus':
                if self.mount.data[valueName] == '1':
                    self.ui.le_refractionStatus.setText('ON')
                else:
                    self.ui.le_refractionStatus.setText('OFF')
            if valueName == 'MountStatus':
                self.ui.le_mountStatus.setText(str(self.mount.statusReference[self.mount.data[valueName]]))
            if valueName == 'TelescopeDEC':
                self.ui.le_telescopeDEC.setText(self.mount.data[valueName])
            if valueName == 'TelescopeRA':
                self.ui.le_telescopeRA.setText(str(self.mount.data[valueName]))
            if valueName == 'TelescopeAltitude':
                self.ui.le_telescopeAltitude.setText(str(self.mount.data[valueName]))
                self.modelWindow.ui.le_telescopeAltitude.setText(str(self.mount.data[valueName]))
            if valueName == 'TelescopeAzimuth':
                self.ui.le_telescopeAzimut.setText(str(self.mount.data[valueName]))
                self.modelWindow.ui.le_telescopeAzimut.setText(str(self.mount.data[valueName]))
            if valueName == 'SlewRate':
                self.ui.le_slewRate.setText(str(self.mount.data[valueName]))
            if valueName == 'MeridianLimitTrack':
                self.ui.le_meridianLimitTrack.setText(str(self.mount.data[valueName]))
            if valueName == 'MeridianLimitSlew':
                self.ui.le_meridianLimitSlew.setText(str(self.mount.data[valueName]))
            if valueName == 'UnattendedFlip':
                if self.mount.data[valueName] == '1':
                    self.ui.le_telescopeUnattendedFlip.setText('ON')
                else:
                    self.ui.le_telescopeUnattendedFlip.setText('OFF')
            if valueName == 'TimeToFlip':
                self.ui.le_timeToFlip.setText(str(self.mount.data[valueName]))
            if valueName == 'TimeToMeridian':
                self.ui.le_timeToMeridian.setText(str(self.mount.data[valueName]))
            if valueName == 'FirmwareProductName':
                self.ui.le_firmwareProductName.setText(str(self.mount.data[valueName]))
            if valueName == 'FirmwareNumber':
                self.ui.le_firmwareNumber.setText(str(self.mount.data[valueName]))
            if valueName == 'FirmwareDate':
                self.ui.le_firmwareDate.setText(str(self.mount.data[valueName]))
            if valueName == 'FirmwareTime':
                self.ui.le_firmwareTime.setText(str(self.mount.data[valueName]))
            if valueName == 'HardwareVersion':
                self.ui.le_hardwareVersion.setText(str(self.mount.data[valueName]))
            if valueName == 'TelescopePierSide':
                self.ui.le_telescopePierSide.setText(str(self.mount.data[valueName]))
            if valueName == 'UTCDataValid':
                if self.mount.data[valueName] == 'V':
                    self.ui.le_UTCDataValid.setText('VALID')
                elif self.mount.data[valueName] == 'E':
                    self.ui.le_UTCDataValid.setText('EXPIRED')
                else:
                    self.ui.le_UTCDataValid.setText('INVALID')
            if valueName == 'UTCDataExpirationDate':
                self.ui.le_UTCDataExpirationDate.setText(str(self.mount.data[valueName]))

    @QtCore.Slot(int)
    def setEnvironmentStatus(self, status):
        if status == 1:
            self.ui.btn_environmentConnected.setStyleSheet('QPushButton {background-color: green;}')
        elif status == 2:
            self.ui.btn_environmentConnected.setStyleSheet('QPushButton {background-color: gray;}')
        else:
            self.ui.btn_environmentConnected.setStyleSheet('QPushButton {background-color: red;}')

    def fillEnvironmentData(self):
        for valueName in self.environment.data:
            if valueName == 'DewPoint':
                self.ui.le_dewPoint.setText('{0:4.1f}'.format(self.environment.data[valueName]))
            elif valueName == 'Temperature':
                self.ui.le_temperature.setText('{0:4.1f}'.format(self.environment.data[valueName]))
            elif valueName == 'Humidity':
                self.ui.le_humidity.setText('{0:4.1f}'.format(self.environment.data[valueName]))
            elif valueName == 'Pressure':
                self.ui.le_pressure.setText('{0:4.1f}'.format(self.environment.data[valueName]))
            elif valueName == 'CloudCover':
                self.ui.le_cloudCover.setText('{0:4.1f}'.format(self.environment.data[valueName]))
            elif valueName == 'RainRate':
                self.ui.le_rainRate.setText('{0:4.1f}'.format(self.environment.data[valueName]))
            elif valueName == 'WindSpeed':
                self.ui.le_windSpeed.setText('{0:4.1f}'.format(self.environment.data[valueName]))
            elif valueName == 'WindDirection':
                self.ui.le_windDirection.setText('{0:4.1f}'.format(self.environment.data[valueName]))
            elif valueName == 'SQR':
                self.ui.le_SQR.setText('{0:4.2f}'.format(self.environment.data[valueName]))
                self.modelWindow.ui.le_SQR.setText('{0:4.2f}'.format(self.environment.data[valueName]))

    @QtCore.Slot(int)
    def setCameraPlateStatus(self, status):
        if status == 3:
            self.ui.btn_camPlateConnected.setStyleSheet('QPushButton {background-color: green;}')
        elif status == 2:
            self.ui.btn_camPlateConnected.setStyleSheet('QPushButton {background-color: yellow;}')
        elif status == 1:
            self.ui.btn_camPlateConnected.setStyleSheet('QPushButton {background-color: red;}')
        else:
            self.ui.btn_camPlateConnected.setStyleSheet('QPushButton {background-color: gray;}')

    @QtCore.Slot(int)
    def setDomeStatus(self, status):
        if status == 1:
            self.ui.btn_domeConnected.setStyleSheet('QPushButton {background-color: green;}')
        elif status == 2:
            self.ui.btn_domeConnected.setStyleSheet('QPushButton {background-color: grey;}')
        else:
            self.ui.btn_domeConnected.setStyleSheet('QPushButton {background-color: red;}')

    def mainLoop(self):
        self.fillMountData()
        self.fillEnvironmentData()
        while not self.INDIDataQueue.empty():
            data = self.INDIDataQueue.get()
            self.fillINDIData(data)
        while not self.messageQueue.empty():
            text = self.messageQueue.get()
            self.ui.errorStatus.setText(self.ui.errorStatus.toPlainText() + text + '\n')
            self.messageQueue.task_done()
            self.ui.errorStatus.moveCursor(QTextCursor.End)
        while not self.imageQueue.empty():
            filename = self.imageQueue.get()
            if self.imageWindow.showStatus:
                self.imageWindow.showFitsImage(filename)
        while not self.modelLogQueue.empty():
            text = self.modelLogQueue.get()
            if text == 'delete':
                self.modelWindow.ui.modellingLog.clear()                                                                    # reset window text
            elif text == 'backspace':
                for i in range(0, 6):
                    self.modelWindow.ui.modellingLog.textCursor().deletePreviousChar()
            elif text.startswith('status'):
                self.modelWindow.ui.le_modelingStatus.setText(text[6:])
            elif text.startswith('percent'):
                self.modelWindow.ui.bar_modelingStatusPercent.setValue(int(1000 * float(text[7:])))
            elif text.startswith('timeleft'):
                self.modelWindow.ui.le_modelingStatusTime.setText(text[8:])
            elif text.startswith('#BW'):
                self.modelWindow.ui.modellingLog.setTextColor(self.COLOR_WHITE)
                self.modelWindow.ui.modellingLog.setFontWeight(QFont.Bold)
                self.modelWindow.ui.modellingLog.insertPlainText(text[3:])
            elif text.startswith('#BG'):
                self.modelWindow.ui.modellingLog.setTextColor(self.COLOR_GREEN)
                self.modelWindow.ui.modellingLog.setFontWeight(QFont.Bold)
                self.modelWindow.ui.modellingLog.insertPlainText(text[3:])
            elif text.startswith('#BY'):
                self.modelWindow.ui.modellingLog.setTextColor(self.COLOR_YELLOW)
                self.modelWindow.ui.modellingLog.setFontWeight(QFont.Bold)
                self.modelWindow.ui.modellingLog.insertPlainText(text[3:])
            else:
                self.modelWindow.ui.modellingLog.setTextColor(self.COLOR_ASTRO)
                self.modelWindow.ui.modellingLog.setFontWeight(QFont.Normal)
                self.modelWindow.ui.modellingLog.insertPlainText(text)                                                      # otherwise add text at the end
            self.modelWindow.ui.modellingLog.moveCursor(QTextCursor.End)                                                    # and move cursor up
            self.modelLogQueue.task_done()
        # noinspection PyCallByClass,PyTypeChecker
        QTimer.singleShot(200, self.mainLoop)                                                                               # 200ms repeat time cyclic


if __name__ == "__main__":
    import traceback
    import warnings

    def except_hook(typeException, valueException, tbackException):                                                         # manage unhandled exception here
        logging.error(traceback.format_exception(typeException, valueException, tbackException))
        sys.__excepthook__(typeException, valueException, tbackException)                                                   # then call the default handler

    BUILD_NO = '2.5.26 beta'

    warnings.filterwarnings("ignore")
    name = 'mount.{0}.log'.format(datetime.datetime.now().strftime("%Y-%m-%d"))
    handler = logging.handlers.RotatingFileHandler(name, backupCount=3)
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s [%(levelname)7s][%(filename)20s][%(lineno)5s][%(thread)5d][%(funcName)20s] - %(message)s',
                        handlers=[handler], datefmt='%Y-%m-%d %H:%M:%S')

    if not os.path.isdir(os.getcwd() + '/analysedata'):
        os.makedirs(os.getcwd() + '/analysedata')
    if not os.path.isdir(os.getcwd() + '/images'):
        os.makedirs(os.getcwd() + '/images')
    if not os.path.isdir(os.getcwd() + '/config'):
        os.makedirs(os.getcwd() + '/config')

    logging.info('-----------------------------------------')
    logging.info('MountWizzard v ' + BUILD_NO + ' started !')
    logging.info('-----------------------------------------')
    logging.info('Platform: ' + platform.system())
    logging.info('Release: ' + platform.release())
    logging.info('Version: ' + platform.version())
    logging.info('Machine: ' + platform.machine())

    logging.info('working directory: {0}'.format(os.getcwd()))
    if not os.access(os.getcwd(), os.W_OK):
        logging.error('no write access to workdir')
    if not os.access(os.getcwd() + '/images', os.W_OK):
        logging.error('no write access to /images')
    if not os.access(os.getcwd() + '/config', os.W_OK):
        logging.error('no write access to /config')
    if not os.access(os.getcwd() + '/analysedata', os.W_OK):
        logging.error('no write access to /analysedata')

    app = QApplication(sys.argv)

    sys.excepthook = except_hook
    # noinspection PyCallByClass,PyTypeChecker,PyArgumentList
    app.setStyle(QStyleFactory.create('Fusion'))
    app.setWindowIcon(QIcon('mw.ico'))

    mountApp = MountWizzardApp()
    if mountApp.modelWindow.showStatus:
        mountApp.modelWindow.redrawModelingWindow()
        mountApp.modelWindow.showModelingPlotWindow()
    if mountApp.imageWindow.showStatus:
        mountApp.imageWindow.showImageWindow()
    if mountApp.analyseWindow.showStatus:
        mountApp.analyseWindow.showAnalyseWindow()
    mountApp.show()
    sys.exit(app.exec_())
