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
import os
# for the sorting
import operator


class ModelPoints:
    logger = logging.getLogger(__name__)                                                                                    # logging enabling

    def __init__(self, transform):
        self.transform = transform
        self.horizonPoints = []                                                                                             # point out of file for showing the horizon
        self.BasePoints = []                                                                                                # base point out of a file for modeling
        self.RefinementPoints = []                                                                                          # refinement point out of file for modeling

    def loadModelPoints(self, modelPointsFileName, modeltype):                                                              # load modeling point file from MM als list from tuples
        p = []
        number = 0
        msg = None
        if modelPointsFileName.strip() == '':
            msg = 'No Model Points Filename given!'
            self.logger.warning('No Model Points Filename given!')
            return p, msg
        try:                                                                                                                # fault tolerance, if file io fails
            with open('config/' + modelPointsFileName, 'r') as fileHandle:                                                  # run over complete file
                for line in fileHandle:                                                                                     # run over lines
                    if line.startswith('GRID'):                                                                             # if grid, then its a TSX file
                        convertedLine = line.rstrip('\n').split()                                                           # format is TSX format
                        point = (float(convertedLine[2]), float(convertedLine[3]))                                          # take data from line
                        number += 1
                        if modeltype == 'refinement' and number > 3:                                                        # in MM format base and refinement are included
                            p.append(point)                                                                                 # add data to the adequate list
                        elif modeltype == 'base' and number <= 3:
                            p.append(point)                                                                                 # add data to the adequate list
                    else:
                        convertedLine = line.rstrip('\n').split(':')                                                        # format is same as Per's MM
                        point = (int(convertedLine[0]), int(convertedLine[1]))                                              # take data from line
                        if len(convertedLine) == 2 and modeltype == 'refinement':                                           # in MM format base and refinement are included
                            p.append(point)                                                                                 # add data to the adequate list
                        elif len(convertedLine) != 2 and modeltype == 'base':
                            p.append(point)                                                                                 # close file
        except Exception as e:                                                                                              # handle exception
            msg = 'Error loading modeling points from file [{0}] error: {1}!'.format(modelPointsFileName, e)
            self.logger.warning('Error loading modeling points from file [{0}] error: {1}!'.format(modelPointsFileName, e))
        finally:
            return p, msg

    def sortPoints(self, modeltype):                                                                                        # sorting point for performance
        if modeltype == 'base':                                                                                             # check type of sorting
            points = self.BasePoints                                                                                        # starting with point equals base points
        else:                                                                                                               # otherwise
            points = self.RefinementPoints                                                                                  # take the refinement points
        if len(points) == 0:                                                                                                # if no basepoints, than no sort
            self.logger.warning('There are no {0}points to sort'.format(modeltype))
            return
        westSide = []                                                                                                       # split west and east side of pier
        eastSide = []                                                                                                       # and reset them
        a = sorted(points, key=operator.itemgetter(0))                                                                      # first sort for az
        for i in range(0, len(a)):                                                                                          # split flip sides
            if a[i][0] >= 180:                                                                                              # choose the right side
                westSide.append((a[i][0], a[i][1]))                                                                         # add the point tto list
            else:                                                                                                           #
                eastSide.append((a[i][0], a[i][1]))                                                                         #
        westSide = sorted(westSide, key=operator.itemgetter(1))                                                             # sort west flipside
        eastSide = sorted(eastSide, key=operator.itemgetter(1))                                                             # sort east flipside
        if modeltype == 'base':
            self.BasePoints = eastSide + westSide                                                                           # put them together
        else:
            self.RefinementPoints = eastSide + westSide                                                                     # put them together

    def loadHorizonPoints(self, horizonPointsFileName, file_check, line_check, line_value):                                 # load a ModelMaker modeling file, return base & refine points as lists of (az,alt) tuples
        self.horizonPoints = []                                                                                             # clear horizon variable
        hp = []                                                                                                             # clear cache
        msg = None
        minAlt = 0
        if file_check:
            if horizonPointsFileName == '':
                msg = 'No horizon points filename given !'
                return msg
            if not os.path.isfile(os.getcwd() + '/config/' + horizonPointsFileName):
                msg = 'Horizon points file does not exist !'
                self.logger.warning('horizon points file does not exist')
            else:
                try:                                                                                                        # try opening the file
                    with open(os.getcwd() + '/config/' + horizonPointsFileName) as f:                                       # run through file
                        for line in f:                                                                                      # run through lines
                            if ':' in line:
                                m = line.rstrip('\n').split(':')                                                            # model maker format
                            else:
                                m = line.rstrip('\n').split(' ')                                                            # card du ciel format
                            point = (int(m[0]), int(m[1]))                                                                  # get point data
                            hp.append(point)                                                                                # add the point
                    f.close()                                                                                               # close file again
                except Exception as e:                                                                                      # handle exception
                    msg = 'Error loading horizon points: {0}'.format(e)
                    self.logger.error('Error loading horizon points: {0}'.format(e))
                    return msg                                                                                              # stop routine
            hp = sorted(hp, key=operator.itemgetter(0))                                                                     # list should be sorted, but I do it for security anyway
        if line_check:
            minAlt = int(line_value)
            if len(hp) == 0:                                                                                                # there is no file loaded
                hp = [(0, minAlt), (359, minAlt)]
        az_last = 0                                                                                                         # starting azimuth
        alt_last = 0                                                                                                        # starting altitude
        for i in range(0, len(hp)):                                                                                         # run through all points an link them via line
            az_act = hp[i][0]                                                                                               # get az from point of file
            alt_act = hp[i][1]                                                                                              # get alt from point of file
            if az_act > az_last:                                                                                            # if act az is greater than last on, we have to draw a line
                incline = (alt_act - alt_last) / (az_act - az_last)                                                         # calculation the line incline
                for j in range(az_last, az_act):                                                                            # run through the space, where no points are given in the file
                    if line_check:
                        point = (j, max(int(alt_last + incline * (j - az_last)), minAlt))                                    # calculation value of next point
                    else:
                        point = (j, int(alt_last + incline * (j - az_last)))
                    self.horizonPoints.append(point)                                                                        # add the interpolated point to list
            else:                                                                                                           # otherwise no interpolation
                self.horizonPoints.append(hp[i])                                                                            # add the point to list, no interpolation needed
            az_last = az_act                                                                                                # set az value to next point
            alt_last = alt_act                                                                                              # same to alt value
        return msg

    def isAboveHorizonLine(self, point):                                                                                    # check, if point is above horizon list (by horizon file)
        length = len(self.horizonPoints)
        if length > 0 and point[0] < length:                                                                                # check if there are horizon points and fit into list
            if point[1] > self.horizonPoints[int(point[0])][1]:                                                             # simple comparison. important: each Int(az) has value set
                return True                                                                                                 # point is above -> True
            else:                                                                                                           #
                return False                                                                                                # points are below the horizon line -> False
        else:                                                                                                               #
            return True                                                                                                     # if there is no horizon line, all are in

    def deleteBelowHorizonLine(self):                                                                                       # remove points from modeling, if below horizon
        i = 0                                                                                                               # list index
        while i < len(self.RefinementPoints):                                                                               # loop for generating list index of point which is below horizon
            if self.isAboveHorizonLine(self.RefinementPoints[i]):                                                           #
                i += 1                                                                                                      # if ok , keep him
            else:                                                                                                           #
                del self.RefinementPoints[i]                                                                                # otherwise delete point from list

    def deletePoints(self):
        self.BasePoints = []
        self.RefinementPoints = []

    def loadBasePoints(self, filename):
        self.BasePoints, msg = self.loadModelPoints(filename, 'base')

    def loadRefinementPoints(self, filename):
        self.RefinementPoints, msg = self.loadModelPoints(filename, 'refinement')

    def generateDSOPoints(self, hours, numPoints, hoursPrev, ra, dec):                                                      # modeling points along dso path
        self.RefinementPoints = []                                                                                          # clear point list
        for i in range(0, numPoints):                                                                                       # round modeling point from actual az alt position 24 hours
            ra = ra - float(i) * hours / numPoints - hoursPrev
            az, alt = self.transform.transformERFA(ra, dec, 1)                                                             # transform to az alt
            if alt > 0:                                                                                                     # we only take point alt > 0
                self.RefinementPoints.append((az, alt))                                                                     # add point to list

    def generateDensePoints(self):                                                                                          # generate pointcloud in greater circles of sky
        west = []                                                                                                           # no sorting, point will be for west and east prepared
        east = []                                                                                                           #
        for dec in range(-10, 90, 10):                                                                                      # range, actually referenced from european situation
            if dec < 30:                                                                                                    # has to be generalized
                step = -15                                                                                                  # lower dec, more point
            elif dec < 70:
                step = -10
            else:
                step = -30                                                                                                  # higher dec. less point (anyway denser)
            for ha in range(120, -120, step):                                                                               # for complete 24 hourangle
                az, alt = self.transform.transformERFA(ha / 10, dec, 1)                                                    # do the transformation to alt az
                if alt > 0:                                                                                                 # only point with alt > 0 are taken
                    if az > 180:                                                                                            # put to the right list
                        east.append((az, alt))                                                                              # add to east
                    else:
                        west.append((az, alt))                                                                              # add to west
        self.RefinementPoints = west + east

    def generateNormalPoints(self):
        west = []                                                                                                           # no sorting, point will be for west and east prepared
        east = []                                                                                                           #
        for dec in range(-15, 90, 15):                                                                                      # range, actually referenced from european situation
            if dec < 60:                                                                                                    # has to be generalized
                step = -10                                                                                                  # lower dec, more point
            else:
                step = -20                                                                                                  # higher dec. less point (anyway denser)
            for ha in range(120, -120, step):                                                                               # for complete 24 hourangle
                az, alt = self.transform.transformERFA(ha / 10, dec, 1)                                                    # do the transformation to alt az
                if alt > 0:                                                                                                 # only point with alt > 0 are taken
                    if az > 180:                                                                                            # put to the right list
                        east.append((az, alt))                                                                              # add to east
                    else:
                        west.append((az, alt))                                                                              # add to west
        self.RefinementPoints = west + east

    def generateGridPoints(self, row, col, altMin, altMax):                                                                                           # modeling points along dso path
        self.RefinementPoints = []                                                                                          # clear point list
        for az in range(5, 360, int(360 / col)):                                                                            # make point for all azimuth
            for alt in range(altMin, altMax + 1, int((altMax - altMin) / (row - 1))):                                       # make point for all altitudes
                self.RefinementPoints.append((az, alt))                                                                     # add point to list

    def generateBasePoints(self, az, alt):                                                                                           # do base point equally distributed
        self.BasePoints = []
        for i in range(0, 3):                                                                                               # we need 3 basepoints
            azp = i * 120 + az                                                                                              # equal distance of 120 degree in az
            if azp > 360:                                                                                                   # value range 0-360
                azp -= 360                                                                                                  # shift it if necessary
            point = (azp, alt)                                                                                              # generate the point value az,alt
            self.BasePoints.append(point)                                                                                   # put it to list
