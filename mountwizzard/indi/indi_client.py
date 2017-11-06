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
# """
#
# A PyQt5 (client) interface to an INDI server. This will only work
# in the context of a PyQt application.
#
# """
import logging
from xml.etree import ElementTree
import PyQt5
from PyQt5 import QtCore, QtNetwork, QtWidgets
import indi.indi_xml as indiXML
import pyfits


class INDIClient(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)
    received = QtCore.pyqtSignal(object)
    status = QtCore.pyqtSignal(int)

    GENERAL_INTERFACE = 0
    TELESCOPE_INTERFACE = (1 << 0)
    CCD_INTERFACE = (1 << 1)
    GUIDER_INTERFACE = (1 << 2)
    FOCUSER_INTERFACE = (1 << 3)
    FILTER_INTERFACE = (1 << 4)
    DOME_INTERFACE = (1 << 5)
    GPS_INTERFACE = (1 << 6)
    WEATHER_INTERFACE = (1 << 7)
    AO_INTERFACE = (1 << 8)
    DUSTCAP_INTERFACE = (1 << 9)
    LIGHTBOX_INTERFACE = (1 << 10)
    DETECTOR_INTERFACE = (1 << 11)
    AUX_INTERFACE = (1 << 15)

    def __init__(self, app):
        super().__init__()

        self.app = app
        self.isRunning = True
        self.device = {}
        self.message_string = ""
        self.socket = None
        self.host = ''
        self.port = 0
        self.driverNameCCD = ''
        self.driverNameTelescope = ''
        self.driverNameWeather = ''
        self.connected = False
        self.receivedImage = False
        self.imagePath = ''
        self.app.ui.le_INDIServerIP.textChanged.connect(self.INDIServerIP)
        self.app.ui.le_INDIServerPort.textChanged.connect(self.INDIServerPort)
        self.received.connect(self.handleReceived)
        self.initConfig()

    def initConfig(self):
        try:
            if 'INDIServerPort' in self.app.config:
                self.app.ui.le_INDIServerPort.setText(self.app.config['INDIServerPort'])
                self.port = int(self.app.config['INDIServerPort'])
            if 'INDIServerIP' in self.app.config:
                self.app.ui.le_INDIServerIP.setText(self.app.config['INDIServerIP'])
                self.host = self.app.config['INDIServerIP']
            if 'CheckEnableINDI' in self.app.config:
                self.app.ui.checkEnableINDI.setChecked(self.app.config['CheckEnableINDI'])
        except Exception as e:
            self.logger.error('item in config.cfg not be initialize, error:{0}'.format(e))
        finally:
            pass

    def storeConfig(self):
        self.app.config['INDIServerPort'] = self.app.ui.le_INDIServerPort.text()
        self.app.config['INDIServerIP'] = self.app.ui.le_INDIServerIP.text()
        self.app.config['CheckEnableINDI'] = self.app.ui.checkEnableINDI.isChecked()

    def INDIServerIP(self):
        if self.app.ui.le_INDIServerIP.text().strip() != '':
            value = self.app.ui.le_INDIServerIP.text().strip().split('.')
            if len(value) != 4:
                self.logger.warning('wrong input value:{0}'.format(value))
                self.app.messageQueue.put('Wrong IP configuration for INDI, please check!')
                return
            v = []
            for i in range(0, 4):
                try:
                    v.append(int(value[i]))
                    ip = '{0:d}.{1:d}.{2:d}.{3:d}'.format(v[0], v[1], v[2], v[3])
                    self.host = ip
                except Exception as e:
                    pass
        else:
            self.logger.warning('empty input value for INDI')
            self.app.messageQueue.put('No INDI IP configured')

    def INDIServerPort(self):
        pass

    def run(self):
        if not self.isRunning:
            self.isRunning = True
        self.socket = QtNetwork.QTcpSocket()
        self.socket.hostFound.connect(self.handleHostFound)
        self.socket.connected.connect(self.handleConnected)
        self.socket.stateChanged.connect(self.handleStateChanged)
        self.socket.disconnected.connect(self.handleDisconnect)
        self.socket.error.connect(self.handleError)
        self.socket.readyRead.connect(self.handleReadyRead)
        self.socket.connectToHost(self.host, self.port)
        while self.isRunning:
            if not self.app.INDISendCommandQueue.empty():
                indi_command = self.app.INDISendCommandQueue.get()
                self.sendMessage(indi_command)
            QtWidgets.QApplication.processEvents()
            if not self.connected and self.socket.state() == 0:
                self.socket.readyRead.connect(self.handleReadyRead)
                self.socket.connectToHost(self.host, self.port)
        # if I leave the loop, I close the connection to remote host
        self.socket.disconnectFromHost()

    def stop(self):
        self.isRunning = False

    def handleHostFound(self):
        pass

    def handleConnected(self):
        self.connected = True
        self.logger.info('INDI Server connected at {}:{}'.format(self.host, self.port))
        self.app.INDISendCommandQueue.put(indiXML.clientGetProperties(indi_attr={'version': '1.0'}))

    def handleError(self, socketError):
        self.logger.error('INDI connection fault: {0}, error: {1}'.format(self.socket.errorString(), socketError))

    def handleStateChanged(self):
        self.logger.info('INDI connection has state: {0}'.format(self.socket.state()))
        self.status.emit(self.socket.state())

    def handleDisconnect(self):
        self.logger.info('INDI connection is disconnected from host')
        self.driverNameCCD = ''
        self.driverNameTelescope = ''
        self.driverNameWeather = ''
        self.connected = False
        self.app.INDIDataQueue.put({'Name': 'WEATHER', 'value': '---'})
        self.app.INDIDataQueue.put({'Name': 'CCD', 'value': '---'})
        self.app.INDIDataQueue.put({'Name': 'Telescope', 'value': '---'})

    def handleReceived(self, message):
        # central dispatcher for data coming from INDI devices. I makes the whole status and data evaluation and fits the
        # data to mountwizzard
        if isinstance(message, indiXML.SetBLOBVector) or isinstance(message, indiXML.DefBLOBVector):
            device = message.attr['device']
            if device == self.driverNameCCD:
                name = message.attr['name']
                if name == 'CCD1':
                    if 'format' in message.getElt(0).attr:
                        if message.getElt(0).attr['format'] == '.fits':
                            imageHDU = pyfits.HDUList.fromstring(message.getElt(0).getValue())
                            imageHDU.writeto(self.imagePath)
                            self.logger.info('image file is in raw fits format')
                        else:
                            self.logger.info('image file is not in raw fits format')
                        self.receivedImage = True

        elif isinstance(message, indiXML.DelProperty):
            device = message.attr['device']
            if device in self.device:
                if 'name' in message.attr:
                    group = message.attr['name']
                    if group in self.device[device]:
                        del self.device[device][group]
        else:
            device = message.attr['device']
            if device not in self.device:
                self.device[device] = {}
            if 'name' in message.attr:
                group = message.attr['name']
                if group not in self.device[device]:
                    self.device[device][group] = {}
                for elt in message.elt_list:
                    self.device[device][group][elt.attr['name']] = elt.getValue()

        if 'name' in message.attr:
            if message.attr['name'] == 'DRIVER_INFO':
                if message.elt_list[3].attr['name'] == 'DRIVER_INTERFACE':
                    if int(message.getElt(3).getValue()) & self.TELESCOPE_INTERFACE:
                        self.driverNameTelescope = message.getElt(0).getValue()
                        self.app.INDIDataQueue.put({'Name': 'Telescope', 'value': message.getElt(0).getValue()})
                    elif int(message.getElt(3).getValue()) & self.CCD_INTERFACE:
                        self.driverNameCCD = message.getElt(0).getValue()
                        self.app.INDIDataQueue.put({'Name': 'CCD', 'value': message.getElt(0).getValue()})
                    elif int(message.getElt(3).getValue()) == self.WEATHER_INTERFACE:
                        self.driverNameWeather = message.getElt(0).getValue()
                        self.app.INDIDataQueue.put({'Name': 'WEATHER', 'value': message.getElt(0).getValue()})

    def handleReadyRead(self):
        # Add starting tag if this is new message.
        if len(self.message_string) == 0:
            self.message_string = "<data>"

        # Get message from socket.
        while self.socket.bytesAvailable():
            # print(self.socket.bytesAvailable())
            tmp = str(self.socket.read(1000000), "ascii")
            self.message_string += tmp

        # Add closing tag.
        self.message_string += "</data>"

        # Try and parse the message.
        try:
            messages = ElementTree.fromstring(self.message_string)
            self.message_string = ""
            for message in messages:
                xml_message = indiXML.parseETree(message)
                self.handleReceived(xml_message)

        # Message is incomplete, remove </data> and wait..
        except ElementTree.ParseError:
            self.message_string = self.message_string[:-7]

    def sendMessage(self, indi_command):
        if self.socket.state() == QtNetwork.QAbstractSocket.ConnectedState:
            self.socket.write(indi_command.toXML() + b'\n')
        else:
            self.logger.warning('Socket not connected')
