# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'analyse_dialog_ui.ui'
#
# Created by: PyQt5 UI code generator 5.8.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_AnalyseDialog(object):
    def setupUi(self, AnalyseDialog):
        AnalyseDialog.setObjectName("AnalyseDialog")
        AnalyseDialog.resize(791, 670)
        self.windowTitle = QtWidgets.QLabel(AnalyseDialog)
        self.windowTitle.setGeometry(QtCore.QRect(0, 0, 791, 31))
        font = QtGui.QFont()
        font.setFamily("MS Shell Dlg 2")
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.windowTitle.setFont(font)
        self.windowTitle.setAutoFillBackground(True)
        self.windowTitle.setAlignment(QtCore.Qt.AlignCenter)
        self.windowTitle.setObjectName("windowTitle")
        self.plot = QtWidgets.QWidget(AnalyseDialog)
        self.plot.setGeometry(QtCore.QRect(0, 170, 791, 501))
        self.plot.setObjectName("plot")
        self.btn_selectDecError = QtWidgets.QPushButton(AnalyseDialog)
        self.btn_selectDecError.setGeometry(QtCore.QRect(10, 50, 121, 31))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.btn_selectDecError.setFont(font)
        self.btn_selectDecError.setObjectName("btn_selectDecError")
        self.btn_selectRaError = QtWidgets.QPushButton(AnalyseDialog)
        self.btn_selectRaError.setGeometry(QtCore.QRect(140, 50, 121, 31))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.btn_selectRaError.setFont(font)
        self.btn_selectRaError.setObjectName("btn_selectRaError")
        self.btn_selectDecErrorAltitude = QtWidgets.QPushButton(AnalyseDialog)
        self.btn_selectDecErrorAltitude.setGeometry(QtCore.QRect(270, 50, 121, 31))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.btn_selectDecErrorAltitude.setFont(font)
        self.btn_selectDecErrorAltitude.setObjectName("btn_selectDecErrorAltitude")
        self.btn_selectRaErrorAltitude = QtWidgets.QPushButton(AnalyseDialog)
        self.btn_selectRaErrorAltitude.setGeometry(QtCore.QRect(400, 50, 121, 31))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.btn_selectRaErrorAltitude.setFont(font)
        self.btn_selectRaErrorAltitude.setObjectName("btn_selectRaErrorAltitude")
        self.btn_selectModelPointPolar = QtWidgets.QPushButton(AnalyseDialog)
        self.btn_selectModelPointPolar.setGeometry(QtCore.QRect(530, 50, 121, 31))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.btn_selectModelPointPolar.setFont(font)
        self.btn_selectModelPointPolar.setObjectName("btn_selectModelPointPolar")
        self.btn_selectDecErrorAzimuth = QtWidgets.QPushButton(AnalyseDialog)
        self.btn_selectDecErrorAzimuth.setGeometry(QtCore.QRect(270, 90, 121, 31))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.btn_selectDecErrorAzimuth.setFont(font)
        self.btn_selectDecErrorAzimuth.setObjectName("btn_selectDecErrorAzimuth")
        self.btn_selectClose = QtWidgets.QPushButton(AnalyseDialog)
        self.btn_selectClose.setGeometry(QtCore.QRect(760, 0, 31, 31))
        font = QtGui.QFont()
        font.setFamily("MS Shell Dlg 2")
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.btn_selectClose.setFont(font)
        self.btn_selectClose.setObjectName("btn_selectClose")
        self.btn_selectModelPointErrorPolar = QtWidgets.QPushButton(AnalyseDialog)
        self.btn_selectModelPointErrorPolar.setGeometry(QtCore.QRect(530, 90, 121, 31))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.btn_selectModelPointErrorPolar.setFont(font)
        self.btn_selectModelPointErrorPolar.setObjectName("btn_selectModelPointErrorPolar")
        self.btn_selectRaErrorDeviation = QtWidgets.QPushButton(AnalyseDialog)
        self.btn_selectRaErrorDeviation.setGeometry(QtCore.QRect(140, 90, 121, 31))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.btn_selectRaErrorDeviation.setFont(font)
        self.btn_selectRaErrorDeviation.setObjectName("btn_selectRaErrorDeviation")
        self.btn_selectRaErrorAzimuth = QtWidgets.QPushButton(AnalyseDialog)
        self.btn_selectRaErrorAzimuth.setGeometry(QtCore.QRect(400, 90, 121, 31))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.btn_selectRaErrorAzimuth.setFont(font)
        self.btn_selectRaErrorAzimuth.setObjectName("btn_selectRaErrorAzimuth")
        self.label_93 = QtWidgets.QLabel(AnalyseDialog)
        self.label_93.setGeometry(QtCore.QRect(140, 140, 61, 21))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_93.setFont(font)
        self.label_93.setObjectName("label_93")
        self.label_113 = QtWidgets.QLabel(AnalyseDialog)
        self.label_113.setGeometry(QtCore.QRect(240, 140, 21, 20))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_113.setFont(font)
        self.label_113.setAlignment(QtCore.Qt.AlignCenter)
        self.label_113.setWordWrap(False)
        self.label_113.setObjectName("label_113")
        self.scalePlotRA = QtWidgets.QDoubleSpinBox(AnalyseDialog)
        self.scalePlotRA.setGeometry(QtCore.QRect(200, 140, 41, 22))
        self.scalePlotRA.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.scalePlotRA.setDecimals(0)
        self.scalePlotRA.setMinimum(5.0)
        self.scalePlotRA.setMaximum(100.0)
        self.scalePlotRA.setSingleStep(5.0)
        self.scalePlotRA.setProperty("value", 20.0)
        self.scalePlotRA.setObjectName("scalePlotRA")
        self.label_94 = QtWidgets.QLabel(AnalyseDialog)
        self.label_94.setGeometry(QtCore.QRect(10, 140, 71, 21))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_94.setFont(font)
        self.label_94.setObjectName("label_94")
        self.scalePlotDEC = QtWidgets.QDoubleSpinBox(AnalyseDialog)
        self.scalePlotDEC.setGeometry(QtCore.QRect(80, 140, 41, 22))
        self.scalePlotDEC.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.scalePlotDEC.setDecimals(0)
        self.scalePlotDEC.setMinimum(5.0)
        self.scalePlotDEC.setMaximum(100.0)
        self.scalePlotDEC.setSingleStep(5.0)
        self.scalePlotDEC.setProperty("value", 20.0)
        self.scalePlotDEC.setObjectName("scalePlotDEC")
        self.label_114 = QtWidgets.QLabel(AnalyseDialog)
        self.label_114.setGeometry(QtCore.QRect(120, 140, 21, 20))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_114.setFont(font)
        self.label_114.setAlignment(QtCore.Qt.AlignCenter)
        self.label_114.setWordWrap(False)
        self.label_114.setObjectName("label_114")
        self.label_95 = QtWidgets.QLabel(AnalyseDialog)
        self.label_95.setGeometry(QtCore.QRect(270, 140, 71, 21))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_95.setFont(font)
        self.label_95.setObjectName("label_95")
        self.label_115 = QtWidgets.QLabel(AnalyseDialog)
        self.label_115.setGeometry(QtCore.QRect(380, 140, 51, 20))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_115.setFont(font)
        self.label_115.setAlignment(QtCore.Qt.AlignCenter)
        self.label_115.setWordWrap(False)
        self.label_115.setObjectName("label_115")
        self.scalePlotError = QtWidgets.QDoubleSpinBox(AnalyseDialog)
        self.scalePlotError.setGeometry(QtCore.QRect(340, 140, 41, 22))
        self.scalePlotError.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.scalePlotError.setDecimals(0)
        self.scalePlotError.setMinimum(5.0)
        self.scalePlotError.setMaximum(50.0)
        self.scalePlotError.setSingleStep(5.0)
        self.scalePlotError.setProperty("value", 10.0)
        self.scalePlotError.setObjectName("scalePlotError")
        self.btn_selectDecErrorDeviation = QtWidgets.QPushButton(AnalyseDialog)
        self.btn_selectDecErrorDeviation.setGeometry(QtCore.QRect(10, 90, 121, 31))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.btn_selectDecErrorDeviation.setFont(font)
        self.btn_selectDecErrorDeviation.setObjectName("btn_selectDecErrorDeviation")
        self.btn_selectAnalyseFileName_11 = QtWidgets.QPushButton(AnalyseDialog)
        self.btn_selectAnalyseFileName_11.setGeometry(QtCore.QRect(660, 50, 121, 31))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.btn_selectAnalyseFileName_11.setFont(font)
        self.btn_selectAnalyseFileName_11.setObjectName("btn_selectAnalyseFileName_11")
        self.btn_selectAnalyseFileName_12 = QtWidgets.QPushButton(AnalyseDialog)
        self.btn_selectAnalyseFileName_12.setGeometry(QtCore.QRect(660, 90, 121, 31))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.btn_selectAnalyseFileName_12.setFont(font)
        self.btn_selectAnalyseFileName_12.setObjectName("btn_selectAnalyseFileName_12")
        self.btn_selectMinimize = QtWidgets.QPushButton(AnalyseDialog)
        self.btn_selectMinimize.setGeometry(QtCore.QRect(730, 0, 31, 31))
        font = QtGui.QFont()
        font.setFamily("MS Shell Dlg 2")
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.btn_selectMinimize.setFont(font)
        self.btn_selectMinimize.setObjectName("btn_selectMinimize")

        self.retranslateUi(AnalyseDialog)
        QtCore.QMetaObject.connectSlotsByName(AnalyseDialog)

    def retranslateUi(self, AnalyseDialog):
        _translate = QtCore.QCoreApplication.translate
        AnalyseDialog.setWindowTitle(_translate("AnalyseDialog", "Analyse Window"))
        self.windowTitle.setText(_translate("AnalyseDialog", "Analyse"))
        self.btn_selectDecError.setToolTip(_translate("AnalyseDialog", "<html><head/><body><p>Show Dec Error in arc sec from modeling file</p></body></html>"))
        self.btn_selectDecError.setText(_translate("AnalyseDialog", "Dec Error"))
        self.btn_selectRaError.setToolTip(_translate("AnalyseDialog", "<html><head/><body><p>Show Ra Error in arc sec from modeling file.</p></body></html>"))
        self.btn_selectRaError.setText(_translate("AnalyseDialog", "Ra Error"))
        self.btn_selectDecErrorAltitude.setToolTip(_translate("AnalyseDialog", "<html><head/><body><p>Show Dec Error in arc sec from modeling file over Altitude.</p></body></html>"))
        self.btn_selectDecErrorAltitude.setText(_translate("AnalyseDialog", "Dec Error over Alt"))
        self.btn_selectRaErrorAltitude.setToolTip(_translate("AnalyseDialog", "<html><head/><body><p>Show Ra Error in arc sec from modeling file over Altitude.</p></body></html>"))
        self.btn_selectRaErrorAltitude.setText(_translate("AnalyseDialog", "Ra Error over Alt"))
        self.btn_selectModelPointPolar.setToolTip(_translate("AnalyseDialog", "<html><head/><body><p>Show model points in colors over altitude and azimuth in polar diagram. blue: points west, green: points east.</p></body></html>"))
        self.btn_selectModelPointPolar.setText(_translate("AnalyseDialog", "Modeling Points Polar"))
        self.btn_selectDecErrorAzimuth.setToolTip(_translate("AnalyseDialog", "<html><head/><body><p>Show Dec Error in arc sec from modeling file over Azimuth.</p></body></html>"))
        self.btn_selectDecErrorAzimuth.setText(_translate("AnalyseDialog", "Dec Error over Az"))
        self.btn_selectClose.setToolTip(_translate("AnalyseDialog", "Sets dual tracking on / off"))
        self.btn_selectClose.setText(_translate("AnalyseDialog", "X"))
        self.btn_selectModelPointErrorPolar.setToolTip(_translate("AnalyseDialog", "<html><head/><body><p>Show total error in colors over altitude and azimuth in polar diagram. blue: points west, green: points east.</p></body></html>"))
        self.btn_selectModelPointErrorPolar.setText(_translate("AnalyseDialog", "Modeling Error Polar"))
        self.btn_selectRaErrorDeviation.setToolTip(_translate("AnalyseDialog", "<html><head/><body><p>Show Ra Error in arc sec from modeling file with respect to the first model point.</p></body></html>"))
        self.btn_selectRaErrorDeviation.setText(_translate("AnalyseDialog", "RA Error Flexure"))
        self.btn_selectRaErrorAzimuth.setToolTip(_translate("AnalyseDialog", "<html><head/><body><p>Show Ra Error in arc sec from modeling file over Azimuth.</p></body></html>"))
        self.btn_selectRaErrorAzimuth.setText(_translate("AnalyseDialog", "Ra Error over Az"))
        self.label_93.setText(_translate("AnalyseDialog", "Scale RA"))
        self.label_113.setText(_translate("AnalyseDialog", "°"))
        self.scalePlotRA.setToolTip(_translate("AnalyseDialog", "resulting focal length - please think of reducers etc."))
        self.label_94.setText(_translate("AnalyseDialog", "Scale DEC"))
        self.scalePlotDEC.setToolTip(_translate("AnalyseDialog", "resulting focal length - please think of reducers etc."))
        self.label_114.setText(_translate("AnalyseDialog", "°"))
        self.label_95.setText(_translate("AnalyseDialog", "Scale Error"))
        self.label_115.setText(_translate("AnalyseDialog", "arcsec"))
        self.scalePlotError.setToolTip(_translate("AnalyseDialog", "resulting focal length - please think of reducers etc."))
        self.btn_selectDecErrorDeviation.setToolTip(_translate("AnalyseDialog", "<html><head/><body><p>Show Dec Error in arc sec from modeling file with respect to the first model point.</p></body></html>"))
        self.btn_selectDecErrorDeviation.setText(_translate("AnalyseDialog", "DEC Error Flexure"))
        self.btn_selectAnalyseFileName_11.setToolTip(_translate("AnalyseDialog", "Sets dual tracking on / off"))
        self.btn_selectAnalyseFileName_11.setText(_translate("AnalyseDialog", "..."))
        self.btn_selectAnalyseFileName_12.setToolTip(_translate("AnalyseDialog", "Sets dual tracking on / off"))
        self.btn_selectAnalyseFileName_12.setText(_translate("AnalyseDialog", "..."))
        self.btn_selectMinimize.setToolTip(_translate("AnalyseDialog", "Sets dual tracking on / off"))
        self.btn_selectMinimize.setText(_translate("AnalyseDialog", "-"))

