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
from PyQt5 import QtCore
import socket


class Remote(QtCore.QThread):
    logger = logging.getLogger(__name__)                                                                                    # get logger for  problems
    signalRemoteConnected = QtCore.pyqtSignal(bool, name='RemoteConnected')
    signalRemoteShutdown = QtCore.pyqtSignal(bool, name='RemoteShutdown')
    TCP_IP = '127.0.0.1'
    TCP_PORT = 3495
    BUFFER_SIZE = 20                                                                                                        # Normally 1024, but we want fast response

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.connected = 0

        self.initConfig()

    def initConfig(self):
        try:
            pass
        except Exception as e:
            self.logger.error('initConfig -> item in config.cfg not be initialize, error:{0}'.format(e))
        finally:
            pass

    def storeConfig(self):
        pass

    def run(self):                                                                                                          # runnable for doing the work
        self.connected = 0                                                                                                  # set connection flag for stick itself
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.TCP_IP, self.TCP_PORT))
        s.listen(1)
        while True:
            conn, addr = s.accept()
            while True:
                try:
                    data = conn.recv(self.BUFFER_SIZE)
                    if not data:
                        break
                    else:
                        if data.decode().strip() == 'shutdown':
                            print('Mountwizzard will be stopped !')
                            self.signalRemoteShutdown.emit(True)
                except Exception as e:
                    print(e)
                    break
            conn.close()

        self.terminate()                                                                                                    # closing the thread at the end

    def __del__(self):                                                                                                      # remove thread
        self.wait()