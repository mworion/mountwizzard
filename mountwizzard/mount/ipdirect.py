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

# import basic stuff
import logging
import threading
import socket


class MountIpDirect:
    logger = logging.getLogger(__name__)
    PORT = 3492

    def __init__(self, app):
        self.app = app
        self.connected = False
        self.socket = None
        self.value_azimuth = 0
        self.value_altitude = 0
        self.tryConnectionCounter = 0
        self.sendCommandLock = threading.Lock()

    def mountIP(self):
        value = self.app.ui.le_mountIP.text().split('.')
        if len(value) != 4:
            self.logger.warning('wrong input value:{0}'.format(value))
            self.app.messageQueue.put('Wrong IP configuration for mount, please check!')
            return
        v = []
        for i in range(0, 4):
            v.append(int(value[i]))
        ip = '{0:d}.{1:d}.{2:d}.{3:d}'.format(v[0], v[1], v[2], v[3])
        return ip

    def connect(self):
        try:
            if self.socket is None:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(60)
            self.socket.connect((self.mountIP(), self.PORT))
            self.connected = True
            self.tryConnectionCounter = 0
        except ConnectionRefusedError:
            pass
        # except IOError:
        #     pass
        except Exception as e:
            self.tryConnectionCounter += 1
            if self.tryConnectionCounter < 3:
                self.logger.warning('Direct mount connection is broken')
            elif self.tryConnectionCounter == 3:
                self.logger.error('No connection to Mount possible - stop logging this connection error')
            else:
                pass
            self.socket = None
            self.connected = False
        finally:
            pass

    def disconnect(self):
        try:
            self.connected = False
            if self.socket:
                self.socket.shutdown(1)
                self.socket.close()
                self.socket = None
        except ConnectionRefusedError:
            pass
        # except IOError:
        #    pass
        except Exception as e:
            self.logger.error('Socket disconnect error: {0}'.format(e))
            self.connected = False
        finally:
            pass

    def commandBlind(self, command):
        totalSent = 0
        command = (':' + command + '#').encode()
        try:
            while totalSent < len(command):
                sent = self.socket.send(command[totalSent:])
                if sent == 0:
                    raise RuntimeError("Socket connection broken")
                totalSent = totalSent + sent
        except Exception as e:
            self.logger.error('Socket send error: {0}'.format(e))
            self.disconnect()
        finally:
            pass

    def commandString(self, command):
        self.commandBlind(command)
        try:
            chunks = []
            while True:
                chunk = self.socket.recv(1024)
                if chunk == b'':
                    raise RuntimeError('Socket connection broken')
                chunk = chunk.decode()
                chunks.append(chunk)
                # for some reasons there are existing command return values not ended with '#'
                if chunk[len(chunk)-1] == '#' or len(chunk) == 1:
                    break
        except RuntimeError as e:
            self.logger.error('Socket connection broken')
            self.disconnect()
        except Exception as e:
            self.logger.error('Socket receive error: {0}'.format(e))
        finally:
            # noinspection PyUnboundLocalVariable
            value = ''.join(chunks)
            return value

    def sendCommand(self, command):
        reply = ''
        self.sendCommandLock.acquire()
        if self.connected:
            try:
                # these are the commands, which do not expect a return value
                if command in self.app.mount.BLIND_COMMANDS:
                    self.commandBlind(command)
                else:
                    reply = self.commandString(command)
            except Exception as e:
                self.app.messageQueue.put('TCP error in sendCommand')
                self.logger.error('error: {0} command:{1}  reply:{2} '.format(e, command, reply))
            finally:
                if len(reply) > 0:
                    value = reply.rstrip('#').strip()
                    if command == 'CMS':
                        self.logger.info('Return Value Add Model Point: {0}'.format(reply))
                else:
                    if command in self.app.mount.BLIND_COMMANDS:
                        value = ''
                    else:
                        value = '0'
        else:
            if command == 'Gev':
                value = '01234.1'
            elif command == 'Gmte':
                value = '0125'
            elif command == 'Gt':
                value = '00:00:00'
            elif command == 'Gg':
                value = '00:00:00'
            elif command == 'GS':
                value = '00:00:00'
            elif command == 'GRTMP':
                value = '10.0'
            elif command == 'Ginfo':
                value = '0, 0, E, 0, 0, 0, 0'
            elif command == 'GTMP1':
                value = '10.0'
            elif command == 'GRPRS':
                value = '990.0'
            elif command == 'Guaf':
                value = '0'
            elif command == 'GMs':
                value = '15'
            elif command == 'Gh':
                value = '90'
            elif command == 'Go':
                value = '00'
            elif command == 'Gdat':
                value = '0'
            elif command in ['GVD', 'GVN', 'GVP', 'GVT', 'GVZ']:
                value = 'Simulation'
            elif command == 'GREF':
                value = '1'
            elif command == 'CMS':
                value = 'V'
            elif command == 'getalst':
                value = '-1'
            elif command == 'GDUTV':
                value = '1,1'
            else:
                value = '0'
        self.sendCommandLock.release()
        return value


if __name__ == "__main__":

    a = MountIpDirect(None)
    a.connect()
    b = a.commandString('Guaf')
    a.disconnect()
