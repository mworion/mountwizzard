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
import copy
import datetime
import logging
import math
import os
import random
import shutil
import sys
import time
# PyQt5
import PyQt5
# library for fits file handling
import pyfits


class ModelWorker:
    logger = logging.getLogger(__name__)

    def __init__(self, app):
        # make main sources available
        self.app = app
        self.results = []
        self.modelRun = False

    @staticmethod
    def timeStamp():
        return time.strftime("%H:%M:%S", time.localtime())

    def clearAlignmentModel(self):
        self.app.modeling.modelAnalyseData = []
        self.app.mountCommandQueue.put('ClearAlign')
        time.sleep(4)

    def setupRunningParameters(self):
        settlingTime = int(float(self.app.ui.settlingTime.value()))
        directory = time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime())
        return settlingTime, directory

    def runBaseModel(self):
        if self.app.ui.checkClearModelFirst.isChecked():
            self.app.modelLogQueue.put('Clearing alignment modeling - taking 4 seconds.\n')
            self.clearAlignmentModel()
            self.app.modelLogQueue.put('Model cleared!\n')
        settlingTime, directory = self.setupRunningParameters()
        if len(self.app.modeling.modelPoints.BasePoints) > 0:
            simulation = self.app.ui.checkSimulation.isChecked()
            keepImages = self.app.ui.checkKeepImages.isChecked()
            self.app.modeling.modelData = self.runModel('Base', self.app.modeling.modelPoints.BasePoints, directory, settlingTime, simulation, keepImages)
            self.app.modeling.modelData = self.app.mount.retrofitMountData(self.app.modeling.modelData)
            name = directory + '_base.dat'
            if len(self.app.modeling.modelData) > 0:
                self.app.ui.le_analyseFileName.setText(name)
                self.app.modeling.analyse.saveData(self.app.modeling.modelData, name)
                self.app.mount.saveBaseModel()
        else:
            self.logger.warning('There are no Basepoints for modeling')

    def runRefinementModel(self):
        num = self.app.mount.numberModelStars()
        suc, mes, sizeX, sizeY, canSubframe, gainValue = self.app.modeling.imagingHandler.getCameraProps()
        if sizeX == 800 and sizeY == 600 and suc:
            simulation = True
            self.app.modeling.modelData = []
        else:
            simulation = False
        if num > 2 or simulation:
            settlingTime, directory = self.setupRunningParameters()
            if len(self.app.modeling.modelPoints.RefinementPoints) > 0:
                if self.app.ui.checkKeepRefinement.isChecked():
                    self.app.mount.loadRefinementModel()
                else:
                    self.app.mount.loadBaseModel()
                simulation = self.app.ui.checkSimulation.isChecked()
                keepImages = self.app.ui.checkKeepImages.isChecked()
                refinePoints = self.runModel('Refinement', self.app.modeling.modelPoints.RefinementPoints, directory, settlingTime, simulation, keepImages)
                for i in range(0, len(refinePoints)):
                    refinePoints[i]['Index'] += len(self.app.modeling.modelData)
                self.app.modeling.modelData = self.app.modeling.modelData + refinePoints
                self.app.modeling.modelData = self.app.mount.retrofitMountData(self.app.modeling.modelData)
                name = directory + '_refinement.dat'
                if len(self.app.modeling.modelData) > 0:
                    self.app.ui.le_analyseFileName.setText(name)
                    self.app.modeling.analyse.saveData(self.app.modeling.modelData, name)
                    self.app.mount.saveRefinementModel()
            else:
                self.logger.warning('There are no Refinement Points to modeling')
        else:
            self.app.modelLogQueue.put('Refine stopped, no BASE model available !\n')
            self.app.messageQueue.put('Refine stopped, no BASE model available !\n')

    def runCheckModel(self):
        settlingTime, directory = self.setupRunningParameters()
        points = self.app.modeling.modelPoints.BasePoints + self.app.modeling.modelPoints.RefinementPoints
        if len(points) > 0:
            simulation = self.app.ui.checkSimulation.isChecked()
            keepImages = self.app.ui.checkKeepImages.isChecked()
            self.app.modeling.modelAnalyseData = self.runModel('Check', points, directory, settlingTime, simulation, keepImages)
            name = directory + '_check.dat'
            if len(self.app.modeling.modelAnalyseData) > 0:
                self.app.ui.le_analyseFileName.setText(name)
                self.app.modeling.analyse.saveData(self.app.modeling.modelAnalyseData, name)
        else:
            self.logger.warning('There are no Refinement or Base Points to modeling')

    def runAllModel(self):
        self.runBaseModel()
        self.runRefinementModel()

    def runTimeChangeModel(self):
        settlingTime, directory = self.setupRunningParameters()
        points = []
        for i in range(0, int(float(self.app.ui.numberRunsTimeChange.value()))):
            points.append((int(self.app.ui.azimuthTimeChange.value()), int(self.app.ui.altitudeTimeChange.value()),
                           PyQt5.QtWidgets.QGraphicsTextItem(''), True))
        simulation = self.app.ui.checkSimulation.isChecked()
        keepImages = self.app.ui.checkKeepImages.isChecked()
        self.app.modeling.modelAnalyseData = self.runModel('TimeChange', points, directory, settlingTime, simulation, keepImages)
        name = directory + '_timechange.dat'
        if len(self.app.modeling.modelAnalyseData) > 0:
            self.app.ui.le_analyseFileName.setText(name)
            self.app.modeling.analyse.saveData(self.app.modeling.modelAnalyseData, name)

    def runHystereseModel(self):
        waitingTime, directory = self.setupRunningParameters()
        alt1 = int(float(self.app.ui.altitudeHysterese1.value()))
        alt2 = int(float(self.app.ui.altitudeHysterese2.value()))
        az1 = int(float(self.app.ui.azimuthHysterese1.value()))
        az2 = int(float(self.app.ui.azimuthHysterese2.value()))
        numberRunsHysterese = int(float(self.app.ui.numberRunsHysterese.value()))
        points = []
        for i in range(0, numberRunsHysterese):
            points.append((az1, alt1, PyQt5.QtWidgets.QGraphicsTextItem(''), True))
            points.append((az2, alt2, PyQt5.QtWidgets.QGraphicsTextItem(''), False))
        simulation = self.app.ui.checkSimulation.isChecked()
        keepImages = self.app.ui.checkKeepImages.isChecked()
        self.app.modeling.modelAnalyseData = self.runModel('Hysterese', points, directory, waitingTime, simulation, keepImages)
        name = directory + '_hysterese.dat'
        self.app.ui.le_analyseFileName.setText(name)
        if len(self.app.modeling.modelAnalyseData) > 0:
            self.app.ui.le_analyseFileName.setText(name)
            self.app.modeling.analyse.saveData(self.app.modeling.modelAnalyseData, name)

    def runBatchModel(self):
        nameDataFile = self.app.ui.le_analyseFileName.text()
        self.logger.info('modeling from {0}'.format(nameDataFile))
        data = self.app.modeling.analyse.loadData(nameDataFile)
        if not('RaJNow' in data and 'DecJNow' in data):
            self.logger.warning('RaJNow or DecJNow not in data file')
            self.app.modelLogQueue.put('{0} - mount coordinates missing\n'.format(self.timeStamp()))
            return
        if not('RaJNowSolved' in data and 'DecJNowSolved' in data):
            self.logger.warning('RaJNowSolved or DecJNowSolved not in data file')
            self.app.modelLogQueue.put('{0} - solved data missing\n'.format(self.timeStamp()))
            return
        if not('Pierside' in data and 'LocalSiderealTime' in data):
            self.logger.warning('Pierside and LocalSiderealTime not in data file')
            self.app.modelLogQueue.put('{0} - Time and Pierside missing\n'.format(self.timeStamp()))
            return
        self.app.mount.saveBackupModel()
        self.app.modelLogQueue.put('{0} - Start Batch modeling. Saving Actual modeling to BATCH\n'.format(self.timeStamp()))
        self.app.mount.mountHandler.sendCommand('newalig')
        self.app.modelLogQueue.put('{0} - \tOpening Calculation\n'.format(self.timeStamp()))
        for i in range(0, len(data['Index'])):
            command = 'newalpt{0},{1},{2},{3},{4},{5}'.format(self.app.modeling.transform.decimalToDegree(data['RaJNow'][i], False, True),
                                                              self.app.modeling.transform.decimalToDegree(data['DecJNow'][i], True, False),
                                                              data['Pierside'][i],
                                                              self.app.modeling.transform.decimalToDegree(data['RaJNowSolved'][i], False, True),
                                                              self.app.modeling.transform.decimalToDegree(data['DecJNowSolved'][i], True, False),
                                                              self.app.modeling.transform.decimalToDegree(data['LocalSiderealTimeFloat'][i], False, True))
            reply = self.app.mount.mountHandler.sendCommand(command)
            if reply == 'E':
                self.logger.warning('point {0} could not be added'.format(reply))
                self.app.modelLogQueue.put('{0} - \tPoint could not be added\n'.format(self.timeStamp()))
            else:
                self.app.modelLogQueue.put('{0} - \tAdded point {1} @ Az:{2}, Alt:{3} \n'
                                           .format(self.timeStamp(), reply, int(data['Azimuth'][i]), int(data['Altitude'][i])))
        reply = self.app.mount.mountHandler.sendCommand('endalig')
        if reply == 'V':
            self.app.modelLogQueue.put('{0} - Model successful finished! \n'.format(self.timeStamp()))
            self.logger.info('Model successful finished!')
        else:
            self.app.modelLogQueue.put('{0} - Model could not be calculated with current data! \n'.format(self.timeStamp()))
            self.logger.warning('Model could not be calculated with current data!')

    def slewMountDome(self, az, alt):
        self.app.mountCommandQueue.put('Sz{0:03d}*{1:02d}'.format(int(az), int((az - int(az)) * 60 + 0.5)))
        self.app.mountCommandQueue.put('Sa+{0:02d}*{1:02d}'.format(int(alt), int((alt - int(alt)) * 60 + 0.5)))
        self.app.mountCommandQueue.put('MS')
        self.logger.info('Connected:{0}'.format(self.app.dome.connected))
        break_counter = 0
        while not self.app.mount.data['Slewing']:
            time.sleep(0.1)
            break_counter += 1
            if break_counter == 30:
                break
        if self.app.dome.connected == 1:
            if az >= 360:
                az = 359.9
            elif az < 0.0:
                az = 0.0
            try:
                self.app.dome.ascom.SlewToAzimuth(float(az))
            except Exception as e:
                self.logger.error('value: {0}, error: {1}'.format(az, e))
            self.logger.info('Azimuth:{0}'.format(az))
            while not self.app.mount.data['Slewing']:
                if self.app.modeling.cancel:
                    self.logger.info('Modeling cancelled after mount slewing')
                    break
                time.sleep(0.1)
            while self.app.mount.slewing or self.app.dome.slewing:
                if self.app.modeling.cancel:
                    self.logger.info('Modeling cancelled after dome slewing')
                    break
                time.sleep(0.1)
        else:
            while self.app.mount.data['Slewing']:
                if self.app.modeling.cancel:
                    self.logger.info('Modeling cancelled after mount slewing')
                    break
                time.sleep(0.1)

    def prepareImaging(self, modelData, directory):
        # do all the calculations once
        suc, mes, sizeX, sizeY, canSubframe, gainValue = self.app.modeling.imagingHandler.getCameraProps()
        if suc:
            self.logger.info('camera props: {0}, {1}, {2}'.format(sizeX, sizeY, canSubframe))
        else:
            self.logger.warning('SgGetCameraProps with error: {0}'.format(mes))
            return {}
        if canSubframe and self.app.ui.checkDoSubframe.isChecked():
            scaleSubframe = self.app.ui.scaleSubframe.value() / 100
            modelData['SizeX'] = int(sizeX * scaleSubframe)
            modelData['SizeY'] = int(sizeY * scaleSubframe)
            modelData['OffX'] = int((sizeX - modelData['SizeX']) / 2)
            modelData['OffY'] = int((sizeY - modelData['SizeY']) / 2)
            modelData['CanSubframe'] = True
        else:
            modelData['SizeX'] = 0
            modelData['SizeY'] = 0
            modelData['OffX'] = 0
            modelData['OffY'] = 0
            modelData['CanSubframe'] = False
            self.logger.warning('Camera does not support subframe.')
        modelData['GainValue'] = gainValue
        modelData['BaseDirImages'] = self.app.modeling.IMAGEDIR + '/' + directory
        if self.app.ui.checkFastDownload.isChecked():
            modelData['Speed'] = 'HiSpeed'
        else:
            modelData['Speed'] = 'Normal'
        modelData['Binning'] = int(float(self.app.ui.cameraBin.value()))
        modelData['Exposure'] = int(float(self.app.ui.cameraExposure.value()))
        modelData['Iso'] = int(float(self.app.ui.isoSetting.value()))
        modelData['Blind'] = self.app.ui.checkUseBlindSolve.isChecked()
        modelData['ScaleHint'] = float(self.app.ui.pixelSize.value()) * modelData['Binning'] * 206.6 / float(self.app.ui.focalLength.value())
        if 'Binning' in modelData:
            modelData['SizeX'] = int(modelData['SizeX'] / modelData['Binning'])
            modelData['SizeY'] = int(modelData['SizeY'] / modelData['Binning'])
        return modelData

    def capturingImage(self, modelData, simulation):
        if self.app.modeling.cancel:
            self.logger.info('Modeling cancelled after capturing image')
            return False, 'Cancel modeling pressed', modelData
        LocalSiderealTimeFitsHeader = modelData['LocalSiderealTime'][0:10]
        RaJ2000FitsHeader = self.app.modeling.transform.decimalToDegree(modelData['RaJ2000'], False, False, ' ')
        DecJ2000FitsHeader = self.app.modeling.transform.decimalToDegree(modelData['DecJ2000'], True, False, ' ')
        RaJNowFitsHeader = self.app.modeling.transform.decimalToDegree(modelData['RaJNow'], False, True, ' ')
        DecJNowFitsHeader = self.app.modeling.transform.decimalToDegree(modelData['DecJNow'], True, True, ' ')
        if modelData['Pierside'] == '1':
            pierside_fits_header = 'E'
        else:
            pierside_fits_header = 'W'
        self.logger.info('modelData: {0}'.format(modelData))
        suc, mes, modelData = self.app.modeling.imagingHandler.getImage(modelData)
        if suc:
            if simulation:
                if getattr(sys, 'frozen', False):
                    # we are running in a bundle
                    bundle_dir = sys._MEIPASS
                else:
                    # we are running in a normal Python environment
                    bundle_dir = os.path.dirname(sys.modules['__main__'].__file__)
                shutil.copyfile(bundle_dir + self.app.modeling.REF_PICTURE, modelData['ImagePath'])
            else:
                self.logger.info('suc: {0}, modelData{1}'.format(suc, modelData))
                fitsFileHandle = pyfits.open(modelData['ImagePath'], mode='update')
                fitsHeader = fitsFileHandle[0].header
                if 'FOCALLEN' in fitsHeader and 'XPIXSZ' in fitsHeader:
                    modelData['ScaleHint'] = float(fitsHeader['XPIXSZ']) * 206.6 / float(fitsHeader['FOCALLEN'])
                fitsHeader['DATE-OBS'] = datetime.datetime.now().isoformat()
                fitsHeader['OBJCTRA'] = RaJ2000FitsHeader
                fitsHeader['OBJCTDEC'] = DecJ2000FitsHeader
                fitsHeader['CDELT1'] = str(modelData['ScaleHint'])
                fitsHeader['CDELT2'] = str(modelData['ScaleHint'])
                fitsHeader['PIXSCALE'] = str(modelData['ScaleHint'])
                fitsHeader['SCALE'] = str(modelData['ScaleHint'])
                fitsHeader['MW_MRA'] = RaJNowFitsHeader
                fitsHeader['MW_MDEC'] = DecJNowFitsHeader
                fitsHeader['MW_ST'] = LocalSiderealTimeFitsHeader
                fitsHeader['MW_MSIDE'] = pierside_fits_header
                fitsHeader['MW_EXP'] = modelData['Exposure']
                fitsHeader['MW_AZ'] = modelData['Azimuth']
                fitsHeader['MW_ALT'] = modelData['Altitude']
                self.logger.info('DATE-OBS:{0}, OBJCTRA:{1} OBJTDEC:{2} CDELT1:{3} MW_MRA:{4} '
                                 'MW_MDEC:{5} MW_ST:{6} MW_PIER:{7} MW_EXP:{8} MW_AZ:{9} MW_ALT:{10}'
                                 .format(fitsHeader['DATE-OBS'], fitsHeader['OBJCTRA'], fitsHeader['OBJCTDEC'],
                                         fitsHeader['CDELT1'], fitsHeader['MW_MRA'], fitsHeader['MW_MDEC'],
                                         fitsHeader['MW_ST'], fitsHeader['MW_MSIDE'], fitsHeader['MW_EXP'],
                                         fitsHeader['MW_AZ'], fitsHeader['MW_ALT']))
                fitsFileHandle.flush()
                fitsFileHandle.close()
            self.app.imageQueue.put(modelData['ImagePath'])
            return True, 'OK', modelData
        else:
            return False, mes, modelData

    def addSolveRandomValues(self, modelData):
        modelData['RaJ2000Solved'] = modelData['RaJ2000'] + (2 * random.random() - 1) / 3600
        modelData['DecJ2000Solved'] = modelData['DecJ2000'] + (2 * random.random() - 1) / 360
        modelData['Scale'] = 1.3
        modelData['Angle'] = 90
        modelData['TimeTS'] = 2.5
        ra, dec = self.app.modeling.transform.transformERFA(modelData['RaJ2000Solved'], modelData['DecJ2000Solved'], 3)
        modelData['RaJNowSolved'] = ra
        modelData['DecJNowSolved'] = dec
        modelData['RaError'] = (modelData['RaJ2000Solved'] - modelData['RaJ2000']) * 3600
        modelData['DecError'] = (modelData['DecJ2000Solved'] - modelData['DecJ2000']) * 3600
        modelData['ModelError'] = math.sqrt(modelData['RaError'] * modelData['RaError'] + modelData['DecError'] * modelData['DecError'])
        return modelData

    def solveImage(self, modelData, simulation):
        modelData['UseFitsHeaders'] = True
        suc, mes, modelData = self.app.modeling.imagingHandler.solveImage(modelData)
        self.logger.info('suc:{0} mes:{1}'.format(suc, mes))
        if suc:
            ra_sol_Jnow, dec_sol_Jnow = self.app.modeling.transform.transformERFA(modelData['RaJ2000Solved'], modelData['DecJ2000Solved'], 3)
            modelData['RaJNowSolved'] = ra_sol_Jnow
            modelData['DecJNowSolved'] = dec_sol_Jnow
            modelData['RaError'] = (modelData['RaJ2000Solved'] - modelData['RaJ2000']) * 3600
            modelData['DecError'] = (modelData['DecJ2000Solved'] - modelData['DecJ2000']) * 3600
            modelData['ModelError'] = math.sqrt(modelData['RaError'] * modelData['RaError'] + modelData['DecError'] * modelData['DecError'])
            fitsFileHandle = pyfits.open(modelData['ImagePath'], mode='update')
            fitsHeader = fitsFileHandle[0].header
            fitsHeader['MW_PRA'] = modelData['RaJNowSolved']
            fitsHeader['MW_PDEC'] = modelData['DecJNowSolved']
            fitsHeader['MW_SRA'] = modelData['RaJ2000Solved']
            fitsHeader['MW_SDEC'] = modelData['DecJ2000Solved']
            fitsHeader['MW_PSCAL'] = modelData['Scale']
            fitsHeader['MW_PANGL'] = modelData['Angle']
            fitsHeader['MW_PTS'] = modelData['TimeTS']
            self.logger.info('MW_PRA:{0} MW_PDEC:{1} MW_PSCAL:{2} MW_PANGL:{3} MW_PTS:{4}'.
                             format(fitsHeader['MW_PRA'], fitsHeader['MW_PDEC'], fitsHeader['MW_PSCAL'],
                                    fitsHeader['MW_PANGL'], fitsHeader['MW_PTS']))
            fitsFileHandle.flush()
            fitsFileHandle.close()
            if simulation:
                modelData = self.addSolveRandomValues(modelData)
            return True, mes, modelData
        else:
            return False, mes, modelData

    def addRefinementStar(self, ra, dec):
        self.logger.info('ra:{0} dec:{1}'.format(ra, dec))
        self.app.mount.mountHandler.sendCommand('Sr{0}'.format(ra))
        self.app.mount.mountHandler.sendCommand('Sd{0}'.format(dec))
        starNumber = self.app.mount.numberModelStars()
        reply = self.app.mount.mountHandler.sendCommand('CMS')
        starAdded = self.app.mount.numberModelStars() - starNumber
        if reply == 'E':
            # 'E' says star could not be added
            if starAdded == 1:
                self.logger.error('star added, but return value was E')
                return True
            else:
                self.logger.error('error adding star')
                return False
        else:
            self.logger.info('refinement star added')
            return True

    def syncMountModel(self, ra, dec):
        self.logger.info('ra:{0} dec:{1}'.format(ra, dec))
        self.app.mount.mountHandler.sendCommand('Sr{0}'.format(ra))
        self.app.mount.mountHandler.sendCommand('Sd{0}'.format(dec))
        self.app.mount.mountHandler.sendCommand('CMCFG0')
        # send sync command
        reply = self.app.mount.mountHandler.sendCommand('CM')
        if reply[:5] == 'Coord':
            self.logger.info('mount modeling synced')
            return True
        else:
            self.logger.warning('error in sync mount modeling')
            return False

    def plateSolveSync(self, simulation=False):
        self.app.modelLogQueue.put('delete')
        self.app.modelLogQueue.put('{0} - Start Sync Mount Model\n'.format(self.timeStamp()))
        modelData = {}
        modelData = self.prepareImaging(modelData, '')
        modelData['base_dir_images'] = self.app.modeling.IMAGEDIR + '/platesolvesync'
        self.logger.info('modelData: {0}'.format(modelData))
        self.app.mountCommandQueue.put('PO')
        self.app.mountCommandQueue.put('AP')
        if not os.path.isdir(modelData['BaseDirImages']):
            os.makedirs(modelData['BaseDirImages'])
        modelData['File'] = 'platesolvesync.fit'
        modelData['LocalSiderealTime'] = self.app.mount.data['LocalSiderealTime'][0:9]
        modelData['LocalSiderealTimeFloat'] = self.app.modeling.transform.degStringToDecimal(modelData['LocalSiderealTime'])
        modelData['RaJ2000'] = self.app.mount.data['RaJ2000']
        modelData['DecJ2000'] = self.app.mount.data['DecJ2000']
        modelData['RaJNow'] = self.app.mount.data['RaJNow']
        modelData['DecJNow'] = self.app.mount.data['DecJNow']
        modelData['Pierside'] = self.app.mount.data['Pierside']
        modelData['RefractionTemperature'] = self.app.mount.data['RefractionTemperature']
        modelData['RefractionPressure'] = self.app.mount.data['RefractionPressure']
        modelData['Azimuth'] = 0
        modelData['Altitude'] = 0
        self.app.modelLogQueue.put('{0} -\t Capturing image\n'.format(self.timeStamp()))
        suc, mes, imagepath = self.capturingImage(modelData, simulation)
        self.logger.info('suc:{0} mes:{1}'.format(suc, mes))
        if suc:
            self.app.modelLogQueue.put('{0} -\t Solving Image\n'.format(self.timeStamp()))
            suc, mes, modelData = self.solveImage(modelData, simulation)
            self.app.modelLogQueue.put('{0} -\t Image path: {1}\n'.format(self.timeStamp(), modelData['ImagePath']))
            if suc:
                suc = self.syncMountModel(modelData['RaJNowSolved'], modelData['DecJNowSolved'])
                if suc:
                    self.app.modelLogQueue.put('{0} -\t Mount Model Synced\n'.format(self.timeStamp()))
                else:
                    self.app.modelLogQueue.put(
                        '{0} -\t Mount Model could not be synced - please check!\n'.format(self.timeStamp()))
            else:
                self.app.modelLogQueue.put('{0} -\t Solving error: {1}\n'.format(self.timeStamp(), mes))
        if not self.app.ui.checkKeepImages.isChecked():
            shutil.rmtree(modelData['BaseDirImages'], ignore_errors=True)
        self.app.modelLogQueue.put('{0} - Sync Mount Model finished !\n'.format(self.timeStamp()))

    # noinspection PyUnresolvedReferences
    def runModel(self, modeltype, runPoints, directory, settlingTime, simulation=False, keepImages=False):
        # start clearing the data
        modelData = {}
        results = []
        # preparing the gui outputs
        self.app.modelLogQueue.put('status-- of --')
        self.app.modelLogQueue.put('percent0')
        self.app.modelLogQueue.put('timeleft--:--')
        self.app.modelLogQueue.put('delete')
        self.app.modelLogQueue.put('#BW{0} - Start {1} Model\n'.format(self.timeStamp(), modeltype))
        modelData = self.prepareImaging(modelData, directory)
        if not os.path.isdir(modelData['BaseDirImages']):
            os.makedirs(modelData['BaseDirImages'])
        self.logger.info('modelData: {0}'.format(modelData))
        self.app.mountCommandQueue.put('PO')
        self.app.mountCommandQueue.put('AP')
        # counter and timer for performance estimation
        numCheckPoints = 0
        timeStart = time.time()
        # here starts the real model running cycle
        for i, (p_az, p_alt, p_item, p_solve) in enumerate(runPoints):
            self.app.modeling.modelRun = True
            modelData['Azimuth'] = p_az
            modelData['Altitude'] = p_alt
            if p_item.isVisible():
                # todo: put the code to multi thread modeling
                if self.app.modeling.cancel:
                    self.app.modeling.cancel = False
                    self.app.modelLogQueue.put('#BW{0} -\t {1} Model canceled !\n'.format(self.timeStamp(), modeltype))
                    # tracking should be on after canceling the modeling
                    self.app.mountCommandQueue.put('AP')
                    # clearing the gui
                    self.app.modelLogQueue.put('status-- of --')
                    self.app.modelLogQueue.put('percent0')
                    self.app.modelLogQueue.put('timeleft--:--')
                    self.logger.info('Modeling cancelled in main loop')
                    # finally stopping modeling run
                    break
                self.app.modelLogQueue.put('#BG{0} - Slewing to point {1:2d}  @ Az: {2:3.0f}\xb0 Alt: {3:2.0f}\xb0\n'.format(self.timeStamp(), i+1, p_az, p_alt))
                self.logger.info('point {0:2d}  Az: {1:3.0f} Alt: {2:2.0f}'.format(i+1, p_az, p_alt))
                if modeltype in ['TimeChange']:
                    # in time change there is only slew for the first time, than only track during imaging
                    if i == 0:
                        self.slewMountDome(p_az, p_alt)
                        self.app.mountCommandQueue.put('RT9')
                else:
                    self.slewMountDome(p_az, p_alt)
                self.app.modelLogQueue.put('{0} -\t Wait mount settling / delay time:  {1:02d} sec'.format(self.timeStamp(), settlingTime))
                timeCounter = settlingTime
                while timeCounter > 0:
                    time.sleep(1)
                    timeCounter -= 1
                    self.app.modelLogQueue.put('backspace')
                    self.app.modelLogQueue.put('{0:02d} sec'.format(timeCounter))
                self.app.modelLogQueue.put('\n')
            if p_item.isVisible() and p_solve:
                modelData['File'] = self.app.modeling.CAPTUREFILE + '{0:03d}'.format(i) + '.fit'
                modelData['LocalSiderealTime'] = self.app.mount.data['LocalSiderealTime']
                modelData['LocalSiderealTimeFloat'] = self.app.modeling.transform.degStringToDecimal(self.app.mount.data['LocalSiderealTime'][0:9])
                modelData['RaJ2000'] = self.app.mount.data['RaJ2000']
                modelData['DecJ2000'] = self.app.mount.data['DecJ2000']
                modelData['RaJNow'] = self.app.mount.data['RaJNow']
                modelData['DecJNow'] = self.app.mount.data['DecJNow']
                modelData['Pierside'] = self.app.mount.data['Pierside']
                modelData['Index'] = i
                modelData['RefractionTemperature'] = self.app.mount.data['RefractionTemperature']
                modelData['RefractionPressure'] = self.app.mount.data['RefractionPressure']
                if modeltype in ['TimeChange']:
                    self.app.mountCommandQueue.put('AP')
                self.app.modelLogQueue.put('{0} -\t Capturing image for modeling point {1:2d}\n'.format(self.timeStamp(), i + 1))
                suc, mes, imagepath = self.capturingImage(modelData, simulation)
                if modeltype in ['TimeChange']:
                    self.app.mountCommandQueue.put('RT9')
                self.logger.info('suc:{0} mes:{1}'.format(suc, mes))
                if suc:
                    self.app.modelLogQueue.put('{0} -\t Solving Image\n'.format(self.timeStamp()))
                    suc, mes, modelData = self.solveImage(modelData, simulation)
                    self.app.modelLogQueue.put('{0} -\t Image path: {1}\n'.format(self.timeStamp(), modelData['ImagePath']))
                    if suc:
                        if modeltype in ['Base', 'Refinement', 'All']:
                            suc = self.addRefinementStar(modelData['RaJNowSolved'], modelData['DecJNowSolved'])
                            if suc:
                                self.app.modelLogQueue.put('{0} -\t Point added\n'.format(self.timeStamp()))
                                numCheckPoints += 1
                                results.append(copy.copy(modelData))
                                p_item.setVisible(False)
                            else:
                                self.app.modelLogQueue.put('{0} -\t Point could not be added - please check!\n'.format(self.timeStamp()))
                                self.logger.info('raE:{0} decE:{1} star could not be added'.format(modelData['RaError'], modelData['DecError']))
                        self.app.modelLogQueue.put('{0} -\t RA_diff:  {1:2.1f}    DEC_diff: {2:2.1f}\n'.format(self.timeStamp(), modelData['RaError'], modelData['DecError']))
                        self.logger.info('modelData: {0}'.format(modelData))
                    else:
                        self.app.modelLogQueue.put('{0} -\t Solving error: {1}\n'.format(self.timeStamp(), mes))
                self.app.modelLogQueue.put('status{0} of {1}'.format(i+1, len(runPoints)))
                modelBuildDone = (i + 1) / len(runPoints)
                self.app.modelLogQueue.put('percent{0}'.format(modelBuildDone))
                actualTime = time.time() - timeStart
                timeCalculated = actualTime / (i + 1) * (len(runPoints) - i - 1)
                mm = int(timeCalculated / 60)
                ss = int(timeCalculated - 60 * mm)
                self.app.modelLogQueue.put('timeleft{0:02d}:{1:02d}'.format(mm, ss))
        if not keepImages:
            shutil.rmtree(modelData['BaseDirImages'], ignore_errors=True)
        self.app.modelLogQueue.put('#BW{0} - {1} Model run finished. Number of modeled points: {2:3d}\n\n'.format(self.timeStamp(), modeltype, numCheckPoints))
        self.app.modeling.modelRun = False
        return results
