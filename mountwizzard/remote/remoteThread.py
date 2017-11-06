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
import PyQt5
import socket


class Remote(PyQt5.QtCore.QThread):
    logger = logging.getLogger(__name__)                                                                                    # get logger for  problems
    signalRemoteConnected = PyQt5.QtCore.pyqtSignal(bool, name='RemoteConnected')
    signalRemoteShutdown = PyQt5.QtCore.pyqtSignal(bool, name='RemoteShutdown')
    TCP_IP = '127.0.0.1'
    BUFFER_SIZE = 20                                                                                                        # Normally 1024, but we want fast response

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.connected = 0
        self.remotePort = 0
        self.initConfig()
        self.app.ui.le_remotePort.textChanged.connect(self.setRemotePort)

    def initConfig(self):
        try:
            if 'RemotePort' in self.app.config:
                self.app.ui.le_remotePort.setText(self.app.config['RemotePort'])
        except Exception as e:
            self.logger.error('item in config.cfg not be initialize, error:{0}'.format(e))
        finally:
            self.setRemotePort()

    def storeConfig(self):
        self.app.config['RemotePort'] = self.app.ui.le_remotePort.Text()

    def setRemotePort(self):
        if self.app.ui.le_remotePort.text().strip() != '':
            self.remotePort = int(self.app.ui.le_remotePort.text())
        else:
            self.logger.warning('empty input value for remote port')
            self.app.messageQueue.put('No remote port configured')

    def run(self):                                                                                                          # runnable for doing the work
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = s.connect_ex((self.TCP_IP, self.remotePort))
        except Exception as e1:
            self.logger.warning('Error in socket {0}'.format(e1))
        finally:
            s.close()
            if result == 0:
                portFree = False
            else:
                portFree = True
        if portFree:
            # there is no listening socket
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind((self.TCP_IP, self.remotePort))
            s.listen(1)
            self.logger.info('MountWizzard started listening on port {0}'.format(self.remotePort))
            while True:
                conn, addr = s.accept()
                self.logger.info('connection to MountWizzard from {0}'.format(addr))
                while True:
                    try:
                        data = conn.recv(self.BUFFER_SIZE)
                        if not data:
                            break
                        else:
                            if data.decode().strip() == 'shutdown':
                                self.logger.info('shutdown MountWizzard from {0}'.format(addr))
                                self.signalRemoteShutdown.emit(True)
                    except Exception as e:
                        self.logger.error('error {0}'.format(e))
                        break
                conn.close()
        else:
            self.logger.warning('port {0} is already in use'.format(self.remotePort))
        self.terminate()                                                                                                    # closing the thread at the end

    def __del__(self):                                                                                                      # remove thread
        self.wait()
