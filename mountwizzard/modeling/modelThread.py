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
import copy
import logging
import os
import platform
import time
# threading
import threading
# queuing
from queue import Queue
# PyQt5
import PyQt5
# for data storing
from analyse.analysedata import Analyse
# cameras
from camera import none
from camera import indicamera
if platform.system() == 'Windows':
    from camera import maximdl
    from camera import sgpro
    import pythoncom
if platform.system() == 'Windows' or platform.system() == 'Darwin':
    from camera import theskyx
# modelPoints
from modeling import modelPoints
# workers
from modeling import modelWorker


class Modeling(PyQt5.QtCore.QThread):
    logger = logging.getLogger(__name__)
    signalModelConnected = PyQt5.QtCore.pyqtSignal(int, name='ModelConnected')
    signalModelRedraw = PyQt5.QtCore.pyqtSignal(bool, name='ModelRedrawPoints')

    BLUE = 'background-color: rgb(42, 130, 218)'
    RED = 'background-color: red;'
    DEFAULT = 'background-color: rgb(32,32,32); color: rgb(192,192,192)'
    REF_PICTURE = '/model001.fit'
    IMAGEDIR = os.getcwd().replace('\\', '/') + '/images'
    CAPTUREFILE = 'modeling'
    CYCLESTATUSFAST = 1000

    def __init__(self, app):
        super(PyQt5.QtCore.QThread, self).__init__()
        # make main sources available
        self.app = app
        self.isRunning = True
        # make windows imaging applications available
        if platform.system() == 'Windows':
            self.SGPro = sgpro.SGPro(self.app)
            self.MaximDL = maximdl.MaximDLCamera(self.app)
        if platform.system() == 'Windows' or platform.system() == 'Darwin':
            self.TheSkyX = theskyx.TheSkyX(self.app)
        # make non windows applications available
        self.NoneCam = none.NoneCamera(self.app)
        self.INDICamera = indicamera.INDICamera(self.app)
        # select default application
        self.imagingHandler = self.NoneCam
        # assign support classes
        self.analyse = Analyse(self.app)
        self.transform = self.app.mount.transform
        self.modelPoints = modelPoints.ModelPoints(self.transform)
        self.modelWorker = modelWorker.ModelWorker(self.app)
        # counter for thread timing
        self.counter = 0
        self.chooserLock = threading.Lock()
        # finally initialize the class configuration
        self.cancel = False
        self.modelRun = False
        self.modelAnalyseData = []
        self.modelData = {}
        self.counter = 0
        # setting the config up
        self.initConfig()

    def initConfig(self):
        if self.NoneCam.appAvailable:
            self.app.ui.pd_chooseImagingApp.addItem('No Application')
        if self.INDICamera.appAvailable:
            self.app.ui.pd_chooseImagingApp.addItem('INDI Camera')
        if platform.system() == 'Windows':
            if self.SGPro.appAvailable:
                self.app.ui.pd_chooseImagingApp.addItem('SGPro - ' + self.SGPro.appName)
            if self.MaximDL.appAvailable:
                self.app.ui.pd_chooseImagingApp.addItem('MaximDL - ' + self.MaximDL.appName)
        if platform.system() == 'Windows' or platform.system() == 'Darwin':
            if self.TheSkyX.appAvailable:
                self.app.ui.pd_chooseImagingApp.addItem('TheSkyX - ' + self.TheSkyX.appName)
        try:
            if 'ImagingApplication' in self.app.config:
                self.app.ui.pd_chooseImagingApp.setCurrentIndex(int(self.app.config['ImagingApplication']))
            if 'CheckSortPoints' in self.app.config:
                self.app.ui.checkSortPoints.setChecked(self.app.config['CheckSortPoints'])
            if 'CheckDeletePointsHorizonMask' in self.app.config:
                self.app.ui.checkDeletePointsHorizonMask.setChecked(self.app.config['CheckDeletePointsHorizonMask'])
            if 'CheckSimulation' in self.app.config:
                self.app.ui.checkSimulation.setChecked(self.app.config['CheckSimulation'])
        except Exception as e:
            self.logger.error('item in config.cfg not be initialize, error:{0}'.format(e))
        finally:
            pass

    def storeConfig(self):
        self.app.config['ImagingApplication'] = self.app.ui.pd_chooseImagingApp.currentIndex()
        self.app.config['CheckSortPoints'] = self.app.ui.checkSortPoints.isChecked()
        self.app.config['CheckDeletePointsHorizonMask'] = self.app.ui.checkDeletePointsHorizonMask.isChecked()
        self.app.config['CheckSimulation'] = self.app.ui.checkSimulation.isChecked()

    def chooseImagingApp(self):
        self.chooserLock.acquire()
        if self.imagingHandler.cameraConnected:
            self.imagingHandler.disconnectCamera()
        if self.app.ui.pd_chooseImagingApp.currentText().startswith('No Application'):
            self.imagingHandler = self.NoneCam
            self.logger.info('actual camera / plate solver is None')
        elif self.app.ui.pd_chooseImagingApp.currentText().startswith('INDI Camera'):
            self.imagingHandler = self.INDICamera
            self.logger.info('actual camera / plate solver is INDI Camera')
        elif self.app.ui.pd_chooseImagingApp.currentText().startswith('SGPro'):
            self.imagingHandler = self.SGPro
            self.logger.info('actual camera / plate solver is SGPro')
        elif self.app.ui.pd_chooseImagingApp.currentText().startswith('TheSkyX'):
            self.imagingHandler = self.TheSkyX
            self.logger.info('actual camera / plate solver is TheSkyX')
        elif self.app.ui.pd_chooseImagingApp.currentText().startswith('MaximDL'):
            self.imagingHandler = self.MaximDL
            self.logger.info('actual camera / plate solver is MaximDL')
        self.imagingHandler.checkAppStatus()
        self.imagingHandler.connectCamera()
        self.chooserLock.release()

    def run(self):
        if platform.system() == 'Windows':
            pythoncom.CoInitialize()
        # run it first, to set all imaging applications up
        self.chooseImagingApp()
        # connect change in imaging app to the subroutine of setting it up
        self.app.ui.pd_chooseImagingApp.currentIndexChanged.connect(self.chooseImagingApp)
        # start first time the loop for status updates
        self.getStatusFast()
        while self.isRunning:
            if not self.app.modelCommandQueue.empty():
                command = self.app.modelCommandQueue.get()
            else:
                command = ''
            if self.app.mount.mountHandler.connected:
                if self.imagingHandler.cameraConnected:
                    if command == 'RunBaseModel':
                        self.app.imageWindow.disableExposures()
                        self.app.ui.btn_runBaseModel.setStyleSheet(self.BLUE)
                        self.modelWorker.runBaseModel()
                        self.app.ui.btn_runBaseModel.setStyleSheet(self.DEFAULT)
                        self.app.ui.btn_cancelModel.setStyleSheet(self.DEFAULT)
                        self.app.imageWindow.enableExposures()
                    elif command == 'RunRefinementModel':
                        self.app.imageWindow.disableExposures()
                        self.app.ui.btn_runRefinementModel.setStyleSheet(self.BLUE)
                        self.modelWorker.runRefinementModel()
                        self.app.ui.btn_runRefinementModel.setStyleSheet(self.DEFAULT)
                        self.app.ui.btn_cancelModel.setStyleSheet(self.DEFAULT)
                        self.app.imageWindow.enableExposures()
                    elif command == 'RunBoostModel':
                        self.app.imageWindow.disableExposures()
                        self.app.ui.btn_runBoostModel.setStyleSheet(self.BLUE)
                        simulation = self.app.ui.checkSimulation.isChecked()
                        self.runBoostModeling(simulation)
                        self.app.ui.btn_runBoostModel.setStyleSheet(self.DEFAULT)
                        self.app.ui.btn_cancelModel.setStyleSheet(self.DEFAULT)
                        self.app.imageWindow.enableExposures()
                    elif command == 'PlateSolveSync':
                        self.app.imageWindow.disableExposures()
                        self.app.ui.btn_plateSolveSync.setStyleSheet(self.BLUE)
                        simulation = self.app.ui.checkSimulation.isChecked()
                        self.modelWorker.plateSolveSync(simulation)
                        self.app.ui.btn_plateSolveSync.setStyleSheet(self.DEFAULT)
                        self.app.imageWindow.enableExposures()
                    elif command == 'RunBatchModel':
                        self.app.ui.btn_runBatchModel.setStyleSheet(self.BLUE)
                        self.modelWorker.runBatchModel()
                        self.app.ui.btn_runBatchModel.setStyleSheet(self.DEFAULT)
                    elif command == 'RunCheckModel':
                        self.app.imageWindow.disableExposures()
                        self.app.ui.btn_runCheckModel.setStyleSheet(self.BLUE)
                        num = self.app.mount.numberModelStars()
                        if num > 2:
                            self.modelWorker.runCheckModel()
                        else:
                            self.app.modelLogQueue.put('Run Analyse stopped, not BASE modeling available !\n')
                            self.app.messageQueue.put('Run Analyse stopped, not BASE modeling available !\n')
                        self.app.ui.btn_runCheckModel.setStyleSheet(self.DEFAULT)
                        self.app.ui.btn_cancelModel.setStyleSheet(self.DEFAULT)
                        self.app.imageWindow.enableExposures()
                    elif command == 'RunAllModel':
                        self.app.imageWindow.disableExposures()
                        self.app.ui.btn_runAllModel.setStyleSheet(self.BLUE)
                        self.modelWorker.runAllModel()
                        self.app.ui.btn_runAllModel.setStyleSheet(self.DEFAULT)
                        self.app.ui.btn_cancelModel.setStyleSheet(self.DEFAULT)
                        self.app.imageWindow.enableExposures()
                    elif command == 'RunTimeChangeModel':
                        self.app.imageWindow.disableExposures()
                        self.app.ui.btn_runTimeChangeModel.setStyleSheet(self.BLUE)
                        self.modelWorker.runTimeChangeModel()
                        self.app.ui.btn_runTimeChangeModel.setStyleSheet(self.DEFAULT)
                        self.app.ui.btn_cancelAnalyseModel.setStyleSheet(self.DEFAULT)
                        self.app.imageWindow.enableExposures()
                    elif command == 'RunHystereseModel':
                        self.app.imageWindow.disableExposures()
                        self.app.ui.btn_runHystereseModel.setStyleSheet(self.BLUE)
                        self.modelWorker.runHystereseModel()
                        self.app.ui.btn_runHystereseModel.setStyleSheet(self.DEFAULT)
                        self.app.ui.btn_cancelAnalyseModel.setStyleSheet(self.DEFAULT)
                        self.app.imageWindow.enableExposures()
                    elif command == 'ClearAlignmentModel':
                        self.app.ui.btn_clearAlignmentModel.setStyleSheet(self.BLUE)
                        self.app.modelLogQueue.put('Clearing alignment modeling - taking 4 seconds.\n')
                        self.modelWorker.clearAlignmentModel()
                        self.app.modelLogQueue.put('Model cleared!\n')
                        self.app.ui.btn_clearAlignmentModel.setStyleSheet(self.DEFAULT)
                if command == 'GenerateDSOPoints':
                    self.app.ui.btn_generateDSOPoints.setStyleSheet(self.BLUE)
                    self.modelPoints.generateDSOPoints(int(float(self.app.ui.numberHoursDSO.value())),
                                                       int(float(self.app.ui.numberPointsDSO.value())),
                                                       int(float(self.app.ui.numberHoursPreview.value())),
                                                       copy.copy(self.app.mount.data['RaJNow']),
                                                       copy.copy(self.app.mount.data['DecJNow']))
                    if self.app.ui.checkSortPoints.isChecked():
                        self.modelPoints.sortPoints('refinement')
                    if self.app.ui.checkDeletePointsHorizonMask.isChecked():
                        self.modelPoints.deleteBelowHorizonLine()
                    self.signalModelRedraw.emit(True)
                    self.app.ui.btn_generateDSOPoints.setStyleSheet(self.DEFAULT)
                elif command == 'GenerateDensePoints':
                    self.app.ui.btn_generateDensePoints.setStyleSheet(self.BLUE)
                    self.modelPoints.generateDensePoints()
                    if self.app.ui.checkSortPoints.isChecked():
                        self.modelPoints.sortPoints('refinement')
                    if self.app.ui.checkDeletePointsHorizonMask.isChecked():
                        self.modelPoints.deleteBelowHorizonLine()
                    self.signalModelRedraw.emit(True)
                    self.app.ui.btn_generateDensePoints.setStyleSheet(self.DEFAULT)
                elif command == 'GenerateNormalPoints':
                    self.app.ui.btn_generateNormalPoints.setStyleSheet(self.BLUE)
                    self.modelPoints.generateNormalPoints()
                    if self.app.ui.checkSortPoints.isChecked():
                        self.modelPoints.sortPoints('refinement')
                    if self.app.ui.checkDeletePointsHorizonMask.isChecked():
                        self.modelPoints.deleteBelowHorizonLine()
                    self.signalModelRedraw.emit(True)
                    self.app.ui.btn_generateNormalPoints.setStyleSheet(self.DEFAULT)
                else:
                    pass
            if command == 'LoadBasePoints':
                self.modelPoints.loadBasePoints(self.app.ui.le_modelPointsFileName.text())
                self.signalModelRedraw.emit(True)
            elif command == 'LoadRefinementPoints':
                self.modelPoints.loadRefinementPoints(self.app.ui.le_modelPointsFileName.text())
                if self.app.ui.checkSortPoints.isChecked():
                    self.modelPoints.sortPoints('refinement')
                if self.app.ui.checkDeletePointsHorizonMask.isChecked():
                    self.modelPoints.deleteBelowHorizonLine()
                self.signalModelRedraw.emit(True)
            elif command == 'GenerateGridPoints':
                self.app.ui.btn_generateGridPoints.setStyleSheet(self.BLUE)
                self.modelPoints.generateGridPoints(int(float(self.app.ui.numberGridPointsRow.value())),
                                                    int(float(self.app.ui.numberGridPointsCol.value())),
                                                    int(float(self.app.ui.altitudeMin.value())),
                                                    int(float(self.app.ui.altitudeMax.value())))
                if self.app.ui.checkSortPoints.isChecked():
                    self.modelPoints.sortPoints('refinement')
                if self.app.ui.checkDeletePointsHorizonMask.isChecked():
                    self.modelPoints.deleteBelowHorizonLine()
                self.signalModelRedraw.emit(True)
                self.app.ui.btn_generateGridPoints.setStyleSheet(self.DEFAULT)
            elif command == 'GenerateBasePoints':
                self.modelPoints.generateBasePoints(float(self.app.ui.azimuthBase.value()),
                                                    float(self.app.ui.altitudeBase.value()))
                self.signalModelRedraw.emit(True)
            elif command == 'DeletePoints':
                self.modelPoints.deletePoints()
                self.signalModelRedraw.emit(True)
            self.counter += 1
            if self.counter % 5 == 0:
                self.getStatusFast()
            time.sleep(0.2)
            PyQt5.QtWidgets.QApplication.processEvents()

    def stop(self):
        if platform.system() == 'Windows':
            pythoncom.CoUninitialize()
        self.isRunning = False

    def cancelModeling(self):
        if self.modelRun:
            self.app.ui.btn_cancelModel.setStyleSheet(self.RED)
            self.logger.info('User canceled modeling with cancel any model run')
            self.cancel = True

    def cancelAnalyseModeling(self):
        if self.modelRun:
            self.app.ui.btn_cancelAnalyseModel.setStyleSheet(self.RED)
            self.logger.info('User canceled modeling with cancel analyse run')
            self.cancel = True

    def getStatusFast(self):
        self.imagingHandler.checkAppStatus()
        self.imagingHandler.getCameraStatus()
        self.signalModelConnected.emit(1)
        if self.imagingHandler.appRunning:
            self.signalModelConnected.emit(2)
        if self.imagingHandler.cameraConnected:
            self.signalModelConnected.emit(3)

    def runBoostModeling(self, simulation):
        # loading test data
        for i in range(1, 10):
            self.workerSlewpoint.queuePoint.put(i)
        # start process
        self.workerSlewpoint.signalSlewing.emit()
