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
import os
import logging
import time
# PyQt5
import PyQt5
# webservices
import urllib.request as urllib2
# windows automation
from pywinauto import Application, timings, findwindows, application
from pywinauto.controls.win32_controls import ButtonWrapper, EditWrapper


class DataUploadToMount(PyQt5.QtCore.QThread):
    logger = logging.getLogger(__name__)                                                                                    # get logger for  problems

    UTC_1 = 'http://maia.usno.navy.mil/ser7/finals.data'
    UTC_2 = 'http://maia.usno.navy.mil/ser7/tai-utc.dat'
    COMETS = 'http://www.minorplanetcenter.net/iau/MPCORB/CometEls.txt'
    COMETS_START = 102
    COMETS_END = 161
    ASTEROIDS_START = 165
    ASTEROIDS_END = 196
    ASTEROIDS_MPC5000 = 'http://www.ap-i.net/pub/skychart/mpc/mpc5000.dat'
    # ASTEROIDS = 'http://www.minorplanetcenter.net/iau/MPCORB/MPCORB.DAT'
    ASTEROIDS_NEA = 'http://www.minorplanetcenter.net/iau/MPCORB/NEA.txt'
    ASTEROIDS_PHA = 'http://www.minorplanetcenter.net/iau/MPCORB/PHA.txt'
    ASTEROIDS_TNO = 'http://www.minorplanetcenter.net/iau/MPCORB/Distant.txt'
    ASTEROIDS_UNUSAL = 'http://www.minorplanetcenter.net/iau/MPCORB/Unusual.txt'
    SPACESTATIONS = 'http://www.celestrak.com/NORAD/elements/stations.txt'
    SATBRIGHTEST = 'http://www.celestrak.com/NORAD/elements/visual.txt'
    TARGET_DIR = os.getcwd() + '\\'
    COMETS_FILE = 'comets.mpc'
    ASTEROIDS_FILE = 'asteroids.mpc'
    SPACESTATIONS_FILE = 'spacestations.tle'
    SATBRIGHTEST_FILE = 'satbrightest.tle'
    UTC_1_FILE = 'finals.data'
    UTC_2_FILE = 'tai-utc.dat'
    BLUE = 'background-color: rgb(42, 130, 218)'
    RED = 'background-color: red;'
    DEFAULT = 'background-color: rgb(32,32,32); color: rgb(192,192,192)'
    OPENDIALOG = 'Dialog'

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.appAvailable = False
        self.appName = ''
        self.appInstallPath = ''
        self.appExe = 'GmQCIv2.exe'
        self.app.ui.btn_downloadEarthrotation.clicked.connect(lambda: self.app.commandDataQueue.put('EARTHROTATION'))
        self.app.ui.btn_downloadSpacestations.clicked.connect(lambda: self.app.commandDataQueue.put('SPACESTATIONS'))
        self.app.ui.btn_downloadSatbrighest.clicked.connect(lambda: self.app.commandDataQueue.put('SATBRIGHTEST'))
        self.app.ui.btn_downloadAsteroidsMPC5000.clicked.connect(lambda: self.app.commandDataQueue.put('ASTEROIDS_MPC5000'))
        self.app.ui.btn_downloadAsteroidsNEA.clicked.connect(lambda: self.app.commandDataQueue.put('ASTEROIDS_NEA'))
        self.app.ui.btn_downloadAsteroidsPHA.clicked.connect(lambda: self.app.commandDataQueue.put('ASTEROIDS_PHA'))
        self.app.ui.btn_downloadAsteroidsTNO.clicked.connect(lambda: self.app.commandDataQueue.put('ASTEROIDS_TNO'))
        self.app.ui.btn_downloadComets.clicked.connect(lambda: self.app.commandDataQueue.put('COMETS'))
        self.app.ui.btn_downloadAll.clicked.connect(lambda: self.app.commandDataQueue.put('ALL'))
        self.app.ui.btn_uploadMount.clicked.connect(lambda: self.app.commandDataQueue.put('UPLOADMOUNT'))
        self.checkApplication()
        self.TARGET_DIR = self.appInstallPath
        self.initConfig()

    def initConfig(self):
        try:
            if 'FilterExpressionMPC' in self.app.config:
                self.app.ui.le_filterExpressionMPC.setText(self.app.config['FilterExpressionMPC'])
            if 'CheckFilterMPC' in self.app.config:
                self.app.ui.checkFilterMPC.setChecked(self.app.config['CheckFilterMPC'])
        except Exception as e:
            self.logger.error('item in config.cfg not be initialize, error:{0}'.format(e))
        finally:
            pass

    def storeConfig(self):
        self.app.config['CheckFilterMPC'] = self.app.ui.checkFilterMPC.isChecked()
        self.app.config['FilterExpressionMPC'] = self.app.ui.le_filterExpressionMPC.text()

    def checkApplication(self):
        self.appAvailable, self.appName, self.appInstallPath = self.app.checkRegistrationKeys('10micron QCI')
        if self.appAvailable:
            self.app.messageQueue.put('Found: {0}'.format(self.appName))
            self.logger.info('Name: {0}, Path: {1}'.format(self.appName, self.appInstallPath))
        else:
            self.logger.info('Application 10micron Updater  not found on computer')

    def run(self):                                                                                                          # runnable for doing the work
        while True:                                                                                                         # main loop for stick thread
            if not self.app.commandDataQueue.empty():
                command = self.app.commandDataQueue.get()
                if command == 'SPACESTATIONS':
                    self.app.ui.btn_downloadSpacestations.setStyleSheet(self.BLUE)
                    self.downloadFile(self.SPACESTATIONS, self.TARGET_DIR + self.SPACESTATIONS_FILE)
                    self.app.ui.checkSpacestations.setChecked(True)
                    self.app.ui.btn_downloadSpacestations.setStyleSheet(self.DEFAULT)
                elif command == 'SATBRIGHTEST':
                    self.app.ui.btn_downloadSatbrighest.setStyleSheet(self.BLUE)
                    self.downloadFile(self.SATBRIGHTEST, self.TARGET_DIR + self.SATBRIGHTEST_FILE)
                    self.app.ui.checkSatellites.setChecked(True)
                    self.app.ui.btn_downloadSatbrighest.setStyleSheet(self.DEFAULT)
                elif command == 'ASTEROIDS_MPC5000':
                    self.app.ui.btn_downloadAsteroidsMPC5000.setStyleSheet(self.BLUE)
                    self.downloadFile(self.ASTEROIDS_MPC5000, self.TARGET_DIR + self.ASTEROIDS_FILE)
                    self.app.ui.checkAsteroids.setChecked(True)
                    self.app.ui.btn_downloadAsteroidsMPC5000.setStyleSheet(self.DEFAULT)
                elif command == 'ASTEROIDS_NEA':
                    self.app.ui.btn_downloadAsteroidsNEA.setStyleSheet(self.BLUE)
                    self.downloadFile(self.ASTEROIDS_NEA, self.TARGET_DIR + self.ASTEROIDS_FILE)
                    self.app.ui.checkAsteroids.setChecked(True)
                    self.app.ui.btn_downloadAsteroidsNEA.setStyleSheet(self.DEFAULT)
                elif command == 'ASTEROIDS_PHA':
                    self.app.ui.btn_downloadAsteroidsPHA.setStyleSheet(self.BLUE)
                    self.downloadFile(self.ASTEROIDS_PHA, self.TARGET_DIR + self.ASTEROIDS_FILE)
                    self.app.ui.checkAsteroids.setChecked(True)
                    self.app.ui.btn_downloadAsteroidsPHA.setStyleSheet(self.DEFAULT)
                elif command == 'ASTEROIDS_TNO':
                    self.app.ui.btn_downloadAsteroidsTNO.setStyleSheet(self.BLUE)
                    self.downloadFile(self.ASTEROIDS_TNO, self.TARGET_DIR + self.ASTEROIDS_FILE)
                    self.app.ui.checkAsteroids.setChecked(True)
                    self.app.ui.btn_downloadAsteroidsTNO.setStyleSheet(self.DEFAULT)
                elif command == 'ASTEROIDS_UNUSAL':
                    self.app.ui.btn_downloadAsteroidsUNUSAL.setStyleSheet(self.BLUE)
                    self.downloadFile(self.ASTEROIDS_UNUSAL, self.TARGET_DIR + self.ASTEROIDS_FILE)
                    self.app.ui.checkAsteroids.setChecked(True)
                    self.app.ui.btn_downloadAsteroidsUNUSAL.setStyleSheet(self.DEFAULT)
                elif command == 'COMETS':
                    self.app.ui.btn_downloadComets.setStyleSheet(self.BLUE)
                    self.downloadFile(self.COMETS, self.TARGET_DIR + self.COMETS_FILE)
                    self.app.ui.checkComets.setChecked(True)
                    self.app.ui.btn_downloadComets.setStyleSheet(self.DEFAULT)
                elif command == 'EARTHROTATION':
                    self.app.ui.btn_downloadEarthrotation.setStyleSheet(self.BLUE)
                    self.downloadFile(self.UTC_1, self.TARGET_DIR + self.UTC_1_FILE)
                    self.downloadFile(self.UTC_2, self.TARGET_DIR + self.UTC_2_FILE)
                    self.app.ui.checkEarthrotation.setChecked(True)
                    self.app.ui.btn_downloadEarthrotation.setStyleSheet(self.DEFAULT)
                elif command == 'ALL':
                    self.app.ui.btn_downloadAll.setStyleSheet(self.BLUE)
                    self.app.ui.btn_downloadEarthrotation.setStyleSheet(self.BLUE)
                    self.app.ui.btn_downloadSpacestations.setStyleSheet(self.BLUE)
                    self.app.ui.btn_downloadSatbrighest.setStyleSheet(self.BLUE)
                    self.app.ui.btn_downloadAsteroidsMPC5000.setStyleSheet(self.BLUE)
                    self.app.ui.btn_downloadComets.setStyleSheet(self.BLUE)
                    self.downloadFile(self.UTC_1, self.TARGET_DIR + self.UTC_1_FILE)
                    self.downloadFile(self.UTC_2, self.TARGET_DIR + self.UTC_2_FILE)
                    self.app.ui.checkEarthrotation.setChecked(True)
                    self.app.ui.btn_downloadEarthrotation.setStyleSheet(self.DEFAULT)
                    self.downloadFile(self.SPACESTATIONS, self.TARGET_DIR + self.SPACESTATIONS_FILE)
                    self.app.ui.checkTLE.setChecked(True)
                    self.app.ui.btn_downloadSpacestations.setStyleSheet(self.DEFAULT)
                    self.downloadFile(self.SATBRIGHTEST, self.TARGET_DIR + self.SATBRIGHTEST_FILE)
                    self.app.ui.checkTLE.setChecked(True)
                    self.app.ui.btn_downloadSatbrighest.setStyleSheet(self.DEFAULT)
                    self.downloadFile(self.COMETS, self.TARGET_DIR + self.COMETS_FILE)
                    self.app.ui.btn_downloadComets.setStyleSheet(self.DEFAULT)
                    self.app.ui.checkComets.setChecked(True)
                    self.downloadFile(self.ASTEROIDS_MPC5000, self.TARGET_DIR + self.ASTEROIDS_FILE)
                    self.app.ui.btn_downloadAsteroidsMPC5000.setStyleSheet(self.DEFAULT)
                    self.app.ui.checkAsteroids.setChecked(True)
                    self.app.ui.btn_downloadAll.setStyleSheet(self.DEFAULT)
                elif command == 'UPLOADMOUNT':
                    self.app.ui.btn_uploadMount.setStyleSheet(self.BLUE)
                    self.uploadMount()
                    self.app.ui.btn_uploadMount.setStyleSheet(self.DEFAULT)
                else:
                    pass
            time.sleep(0.3)                                                                                                 # wait for the next cycle
        self.terminate()                                                                                                    # closing the thread at the end

    def __del__(self):                                                                                                      # remove thread
        self.wait()

    def filterFileMPC(self, directory, filename, expression, start, end):
        numberEntry = 0
        with open(directory + filename, 'r') as inFile, open(directory + 'filter.mpc', 'w') as outFile:
            for line in inFile:
                searchExp = expression.split(',')
                for exp in searchExp:
                    if line.find(exp, start, end) != -1:
                        outFile.write(line)
                        numberEntry += 1
        if numberEntry == 0:
            return False
        else:
            self.app.messageQueue.put('Found {0} target(s) in MPC file: {1}!'.format(numberEntry, filename))
            self.logger.info('Found {0} target(s) in MPC file: {1}!'.format(numberEntry, filename))
            return True

    def downloadFile(self, url, filename):
        try:
            u = urllib2.urlopen(url)
            with open(filename, 'wb') as f:
                meta = u.info()
                meta_func = meta.getheaders if hasattr(meta, 'getheaders') else meta.get_all
                meta_length = meta_func("Content-Length")
                file_size = None
                if meta_length:
                    file_size = int(meta_length[0])
                self.app.messageQueue.put('{0}'.format(url))
                file_size_dl = 0
                block_sz = 8192
                while True:
                    buffer = u.read(block_sz)
                    if not buffer:
                        break
                    file_size_dl += len(buffer)
                    f.write(buffer)
            self.app.messageQueue.put('Downloaded {0} Bytes'.format(file_size))
        except Exception as e:
            self.logger.error('Download of {0} failed, error{1}'.format(url, e))
            self.app.messageQueue.put('Download Error {0}'.format(e))
        return

    def uploadMount(self):
        actual_work_dir = ''
        try:
            actual_work_dir = os.getcwd()
            os.chdir(os.path.dirname(self.appInstallPath))
            app = Application(backend='win32')
            app.start(self.appInstallPath + self.appExe)
            # timings.Timings.Slow()
        except application.AppStartError:
            self.logger.error('Failed to start updater, please check!')
            self.app.messageQueue.put('Failed to start updater, please check!')
            os.chdir(actual_work_dir)
            return
        try:
            dialog = timings.WaitUntilPasses(2, 0.2, lambda: findwindows.find_windows(title='GmQCIv2', class_name='#32770')[0])
            winOK = app.window_(handle=dialog)
            winOK['OK'].click()
        except timings.TimeoutError as e:
            self.logger.warning('No invalid floating point windows occurred - moving forward')
        except Exception as e:
            self.logger.error('error{0}'.format(e))
        finally:
            pass
        try:
            win = app['10 micron control box update']                                                                       # link handle
            win['next'].click()                                                                                             # accept next
            win['next'].click()                                                                                             # go upload select page
            ButtonWrapper(win['Control box firmware']).UncheckByClick()                                                       # no firmware updates
        except Exception as e:
            self.logger.error('error{0}'.format(e))
            self.app.messageQueue.put('Error in starting 10micron updater, please check!')
            os.chdir(actual_work_dir)
            return
        ButtonWrapper(win['Orbital parameters of comets']).UncheckByClick()
        ButtonWrapper(win['Orbital parameters of asteroids']).UncheckByClick()
        ButtonWrapper(win['Orbital parameters of satellites']).UncheckByClick()
        ButtonWrapper(win['UTC / Earth rotation data']).UncheckByClick()
        try:
            uploadNecessary = False
            if self.app.ui.checkComets.isChecked():
                ButtonWrapper(win['Orbital parameters of comets']).CheckByClick()
                win['Edit...4'].click()
                popup = app['Comet orbits']
                popup['MPC file'].click()
                filedialog = app[self.OPENDIALOG]
                if self.app.ui.checkFilterMPC.isChecked():
                    if self.filterFileMPC(self.TARGET_DIR, self.COMETS_FILE, self.app.ui.le_filterExpressionMPC.text(), self.COMETS_START, self.COMETS_END):
                        uploadNecessary = True
                    EditWrapper(filedialog['Edit13']).SetText(self.TARGET_DIR + 'filter.mpc')                               # filename box
                else:
                    uploadNecessary = True
                    EditWrapper(filedialog['Edit13']).SetText(self.TARGET_DIR + self.COMETS_FILE)                           # filename box
                filedialog['Button16'].click()                                                                              # accept filename selection and proceed
                popup['Close'].click()
            else:
                ButtonWrapper(win['Orbital parameters of comets']).UncheckByClick()
            if self.app.ui.checkAsteroids.isChecked():
                ButtonWrapper(win['Orbital parameters of asteroids']).CheckByClick()
                win['Edit...3'].click()
                popup = app['Asteroid orbits']
                popup['MPC file'].click()
                filedialog = app[self.OPENDIALOG]
                if self.app.ui.checkFilterMPC.isChecked():
                    if self.filterFileMPC(self.TARGET_DIR, self.ASTEROIDS_FILE, self.app.ui.le_filterExpressionMPC.text(), self.ASTEROIDS_START, self.ASTEROIDS_END):
                        uploadNecessary = True
                    EditWrapper(filedialog['Edit13']).SetText(self.TARGET_DIR + 'filter.mpc')
                else:
                    uploadNecessary = True
                    EditWrapper(filedialog['Edit13']).SetText(self.TARGET_DIR + self.ASTEROIDS_FILE)                        # filename box
                filedialog['Button16'].click()                                                                              # accept filename selection and proceed
                popup['Close'].click()
            else:
                ButtonWrapper(win['Orbital parameters of asteroids']).UncheckByClick()
            if self.app.ui.checkTLE.isChecked():
                ButtonWrapper(win['Orbital parameters of satellites']).CheckByClick()
                win['Edit...2'].click()
                popup = app['Satellites orbits']
                popup['Load from file'].click()
                filedialog = app[self.OPENDIALOG]
                EditWrapper(filedialog['Edit13']).SetText(self.TARGET_DIR + self.SATBRIGHTEST_FILE)                         # filename box
                filedialog['Button16'].click()                                                                              # accept filename selection and proceed
                popup['Close'].click()
                uploadNecessary = True
            else:
                ButtonWrapper(win['Orbital parameters of satellites']).UncheckByClick()
            if self.app.ui.checkTLE.isChecked():
                ButtonWrapper(win['Orbital parameters of satellites']).CheckByClick()
                win['Edit...2'].click()
                popup = app['Satellites orbits']
                popup['Load from file'].click()
                filedialog = app[self.OPENDIALOG]
                EditWrapper(filedialog['Edit13']).SetText(self.TARGET_DIR + self.SPACESTATIONS_FILE)                        # filename box
                filedialog['Button16'].click()                                                                              # accept filename selection and proceed
                popup['Close'].click()
                uploadNecessary = True
            else:
                ButtonWrapper(win['Orbital parameters of satellites']).UncheckByClick()
            if self.app.ui.checkEarthrotation.isChecked():
                ButtonWrapper(win['UTC / Earth rotation data']).CheckByClick()
                win['Edit...1'].click()
                popup = app['UTC / Earth rotation data']
                popup['Import files...'].click()
                filedialog = app['Open finals data']
                EditWrapper(filedialog['Edit13']).SetText(self.TARGET_DIR + self.UTC_1_FILE)                                # filename box
                filedialog['Button16'].click()                                                                              # accept filename selection and proceed
                filedialog = app['Open tai-utc.dat']
                EditWrapper(filedialog['Edit13']).SetText(self.TARGET_DIR + self.UTC_2_FILE)                                # filename box
                filedialog['Button16'].click()                                                                              # accept filename selection and proceed
                fileOK = app['UTC data']
                fileOK['OK'].click()
                uploadNecessary = True
            else:
                ButtonWrapper(win['UTC / Earth rotation data']).UncheckByClick()
        except Exception as e:
            self.logger.error('error{0}'.format(e))
            self.app.messageQueue.put('Error in choosing upload files, please check 10micron updater!')
            os.chdir(actual_work_dir)
            return
        if self.app.mount.mountHandler.sendCommand('GVD') == 'Simulation' or not self.app.mount.mountHandler.connected:     # Upload with real mount which is connected
            self.app.messageQueue.put('Upload only possible with real mount !')
            uploadNecessary = False
        if uploadNecessary:
            try:
                win['next'].click()
                win['next'].click()
                win['Update Now'].click()
            except Exception as e:
                self.logger.error('error{0}'.format(e))
                self.app.messageQueue.put('Error in uploading files, please check 10micron updater!')
                os.chdir(actual_work_dir)
                return
            try:
                dialog = timings.WaitUntilPasses(60, 0.5, lambda: findwindows.find_windows(title='Update completed', class_name='#32770')[0])
                winOK = app.window_(handle=dialog)
                winOK['OK'].click()
            except Exception as e:
                self.logger.error('error{0}'.format(e))
                self.app.messageQueue.put('Error in closing 10micron updater, please check!')
                os.chdir(actual_work_dir)
                return
        else:
            try:
                win['Cancel'].click()
                winOK = app['Exit updater']
                winOK['Yes'].click()
            except Exception as e:
                self.logger.error('error{0}'.format(e))
                self.app.messageQueue.put('Error in closing Updater, please check!')
                os.chdir(actual_work_dir)
                return


if __name__ == "__main__":
    pass
