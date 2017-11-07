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
import threading

import pythoncom
from win32com.client.dynamic import Dispatch

# astrometry
from astrometry import transform


class MountAscom:
    logger = logging.getLogger(__name__)                                                                                    # enable logging

    def __init__(self, app):
        self.app = app
        self.ascom = None                                                                                                   # ascom mount driver entry point
        self.connected = False                                                                                              # init of connection status
        self.driver_real = True
        self.driverName = 'ASCOM.FrejvallGM.Telescope'                                                                      # default driver name is Per's driver
        self.chooser = None                                                                                                 # object space
        self.value_azimuth = 0
        self.value_altitude = 0
        self.sendCommandLock = threading.Lock()

    def connect(self):                                                                                                      # runnable of the thread
        try:
            self.ascom = Dispatch(self.driverName)                                                                          # select win32 driver
            if self.driverName == 'ASCOM.FrejvallGM.Telescope' or self.driverName == 'ASCOM.tenmicron_mount.Telescope':     # identify real telescope against simulator
                self.driver_real = True                                                                                     # set it
            else:
                self.driver_real = False                                                                                    # set it
            self.ascom.connected = True                                                                                     # connect to mount
            self.connected = True                                                                                           # setting connection status from driver
        except Exception as e:                                                                                              # error handling
            self.logger.error('Driver COM Error in dispatchMount: {0}'.format(e))
            self.connected = False                                                                                          # connection broken
        finally:                                                                                                            # we don't stop, but try it again
            pass

    def disconnect(self):
        try:
            self.connected = False
            self.ascom.connected = False                                                                                    # connect to mount
            self.ascom.Quit()
            self.ascom = None
        except Exception as e:                                                                                              # error handling
            self.logger.error('Driver COM Error in dispatchMount: {0}'.format(e))
            self.connected = False                                                                                          # connection broken
        finally:                                                                                                            # we don't stop, but try it again
            pass

    def sendCommand(self, command):                                                                                         # core routine for sending commands to mount
        reply = ''                                                                                                          # reply is empty
        value = '0'
        self.sendCommandLock.acquire()
        if self.driver_real and self.connected:
            try:                                                                                                            # all with error handling
                if command in self.app.mount.BLIND_COMMANDS:                                                                # these are the commands, which do not expect a return value
                    self.ascom.CommandBlind(command)                                                                        # than do blind command
                else:                                                                                                       #
                    reply = self.ascom.CommandString(command)                                                               # with return value do regular command
            except pythoncom.com_error as e:                                                                                # error handling
                self.app.messageQueue.put('Driver COM Error in sendCommand')                                                # gui
                self.logger.error('error: {0} command:{1}  reply:{2} '.format(e, command, reply))
            finally:                                                                                                        # we don't stop
                if len(reply) > 0:                                                                                          # if there is a reply
                    value = reply.rstrip('#').strip()                                                                       # return the value
                    if command == 'CMS':
                        self.logger.info('Return Value Add Model Point: {0}'.format(reply))
                else:                                                                                                       #
                    if command in self.app.mount.BLIND_COMMANDS:                                                            # these are the commands, which do not expect a return value
                        value = ''                                                                                          # nothing
                    else:
                        value = '0'
        else:                                                                                                               # from here we doing the simulation for 10micron mounts commands
            if self.ascom:
                if command == 'Gev':                                                                                            # which are special, but only for the most important for MW to run
                    value = str(self.ascom.SiteElevation)
                elif command == 'Gmte':
                    value = '0125'
                elif command == 'Gt':
                    value = transform.Transform.decimalToDegree(self.ascom.SiteLatitude, True, False)
                elif command == 'Gg':
                    lon = transform.Transform.decimalToDegree(self.ascom.SiteLongitude, True, False)
                    if lon[0] == '-':                                                                                           # due to compatibility to LX200 protocol east is negative
                        lon1 = lon.replace('-', '+')                                                                            # change that
                    else:
                        lon1 = lon.replace('+', '-')                                                                            # and vice versa
                    value = lon1
                elif command.startswith('Sz'):
                    self.value_azimuth = float(command[2:5]) + float(command[6:8]) / 60
                elif command.startswith('Sa'):
                    self.value_altitude = float(command[2:5]) + float(command[6:8]) / 60
                elif command == 'MS':
                    self.ascom.Tracking = False
                    self.ascom.SlewToAltAzAsync(self.value_azimuth, self.value_altitude)
                    self.ascom.Tracking = True
                elif command == 'MA':
                    self.ascom.Tracking = False
                    self.ascom.SlewToAltAzAsync(self.value_azimuth, self.value_altitude)
                    self.ascom.Tracking = False
                elif command == 'GS':
                    value = transform.Transform.decimalToDegree(self.ascom.SiderealTime, False, False)
                elif command == 'GRTMP':
                    value = '10.0'
                elif command == 'Ginfo':
                    raJnow = self.ascom.RightAscension
                    decJnow = self.ascom.Declination
                    az = self.ascom.Azimuth
                    alt = self.ascom.Altitude
                    if self.ascom.Slewing:
                        stat = 6
                    else:
                        if self.ascom.Tracking:
                            stat = 0
                        else:
                            stat = 7
                    jd = self.ascom.SiderealTime + 2440587.5
                    if self.ascom.SideOfPier == 0:
                        pierside = 'E'
                    else:
                        pierside = 'W'
                    if self.ascom.Slewing:
                        slew = 1
                    else:
                        slew = 0
                    value = '{0},{1},{2},{3},{4},{5},{6},{7}#'.format(raJnow, decJnow, pierside, az, alt, jd, stat, slew)
                elif command == 'PO':
                    self.ascom.Unpark()
                elif command == 'hP':
                    self.ascom.Park()
                elif command == 'AP':
                    self.ascom.Tracking = True
                elif command == 'RT9':
                    self.ascom.Tracking = False
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

    def setupDriver(self):
        try:
            if self.ascom:
                self.ascom.connected = False
                self.ascom = None
            self.chooser = Dispatch('ASCOM.Utilities.Chooser')
            self.chooser.DeviceType = 'Telescope'
            self.driverName = self.chooser.Choose(self.driverName)
            self.logger.info('driver chosen:{0}'.format(self.driverName))
            if self.driverName == 'ASCOM.FrejvallGM.Telescope' or self.driverName == 'ASCOM.tenmicron_mount.Telescope':
                self.driver_real = True
            else:
                self.driver_real = False
            self.connected = False                                                                                          # run the driver setup dialog
        except Exception as e:                                                                                              # general exception
            self.app.messageQueue.put('Driver Exception in setupMount')                                                     # write to gui
            self.logger.error('general exception:{0}'.format(e))
            self.connected = False                                                                                          # set to disconnected
        finally:                                                                                                            # won't stop the program, continue
            return
