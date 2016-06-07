# -*- coding: utf-8 -*-
"""
Created on Fri Oct  2 10:16:23 2015

@author: flehr

ToDo:

"""
__title__ =  'FBGacc'
__about__ = """Hyperion si255 Interrogation Software
            for fbg-acceleration sensors production
            """
__version__ = '0.4.1'
__date__ = '04.03.2016'
__author__ = 'Roman Flehr'
__cp__ = u'\u00a9 2016 Loptek GmbH & Co. KG'

import sys
sys.path.append('../')

from pyqtgraph.Qt import QtGui, QtCore
import plot as pl
import options as opt
import hyperion, time, os
import numpy as np
from scipy.ndimage.interpolation import shift
from qwt_widgets import SlopeMeter
import productionInfo
from tc08usb import TC08USB, USBTC08_TC_TYPE, USBTC08_ERROR#, USBTC08_UNITS
from lmfit.models import GaussianModel


class MainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        
        self.isConnected = False
        self.tempConnected = False
        self.measurementActive = False
        self.si255 = None
        self.tc08usb = None
        self.HyperionIP = '10.0.0.55'
        self.__numChannel = 1
        self.__wavelength = None
        self.__wavelength = np.zeros(20000)
        self.__scaledWavelength = None
        self.__scalePos = None
        self.updateTimer = QtCore.QTimer()
        self.updateTimer.timeout.connect(self.getData)
        self.updateTempTimer = QtCore.QTimer()
        self.updateTempTimer.timeout.connect(self.getTemp)
        self.startTime = None
        
        self.__maxBuffer = 5000
        self.peaks = np.zeros(self.__maxBuffer)
        self.peaksTime = np.zeros(self.__maxBuffer)
        
        self.specFolder = str('../../Spektren')
               
        self.setWindowTitle(__title__ + ' ' + __version__)
        self.resize(900, 600)
        
        self.plotW = pl.Plot()
        self.prodInfo = productionInfo.ProductionInfo()
        self.__vorGrob = 1555.0
        self.__vorFein = 1553.0
        self.waitHeating = False
        self.__heatingTime = 480 # 8min in sec
        self.__heatingStartWl = 1553.2
        self.__heatingStartTime = 0
        self.__activateCooling = False
        self.__finalTemp = 90
        self.cogSpectralWin = 2.5
        
        mainVSplit = QtGui.QSplitter()
        mainVSplit.setOrientation(QtCore.Qt.Vertical)
        mainVSplit.addWidget(self.plotW)
        mainVSplit.addWidget(self.prodInfo)
        
        mainHSplit = QtGui.QSplitter()
        mainHSplit.setOrientation(QtCore.Qt.Horizontal)
        mainHSplit.addWidget(mainVSplit)
        mainHSplit.addWidget(self.createInfoWidget())
        
        self.setCentralWidget(mainHSplit)
        
        self.createMenu()
                
        #self.initDevice()
        #self.connectTemp()
    
        self.plotW.returnSlope.connect(self.setSlope)
        
        self.slopeCh1Dial.setSlope(0)
        self.setActionState()
        self.prodInfo.loadProductionTable()
        
        self.prodInfo.emitSoll.connect(self.chan1SollLabel.setText)
        self.prodInfo.emitProdIds.connect(self.setProdIDs)
        self.prodInfo.buttons.startButton.clicked.connect(self.prodSequenzClicked)


    def initDevice(self):
        try:
            si255Comm = hyperion.HCommTCPSocket(self.HyperionIP, timeout = 5000)
        except hyperion.HyperionError as e:
            print e , ' \thaha'   
        if si255Comm.connected:
            self.si255 = hyperion.Hyperion(comm = si255Comm)
            self.isConnected=True
            self.__wavelength =np.array(self.si255.wavelengths)
            _min = self.minWlSpin.value()
            _max = self.maxWlSpin.value()
            self.__scalePos = np.where((self.__wavelength>=_min) & (self.__wavelength<_max))[0]
            self.__scaledWavelength = self.__wavelength[self.__scalePos]
        else:
            self.isConnected=False
            QtGui.QMessageBox.critical(self,'Connection Error',
                                       'Could not connect to Spectrometer. Please try again')
        self.setActionState()       
         
    def about(self):
        QtGui.QMessageBox.about(self,'About '+__title__,
            self.tr("""<font size=8 color=red>
                        <b><center>{0}</center></b></font>
                   <br><font size=5 color=blue>
                        <b>{1}</b></font>
                    <br><br>Author: {2}<br>
                    Version: {3}<br>
                    Date: {4}<br><br>""".format(__title__, __about__, __author__, __version__, __date__)+__cp__))
                    
    def addActions(self, target, actions):
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)
    
    def calculateLabelColor(self):
        font = QtGui.QFont()
        font.setBold(True)
        font.setPointSize(24)
        tol = self.prodInfo.getTolaranz()
        if not self.chan1SollLabel.text() == '----.---':
            diff = abs(float(self.chan1IsLabel.text())-float(self.chan1SollLabel.text()))
            #print(diff, self.sollGreen[self.prodStep], self.sollGreen[self.prodStep]*3)
            if diff <= tol:
                self.chan1IsLabel.setStyleSheet("color: green")
            elif diff <= tol*3:
                self.chan1IsLabel.setStyleSheet("color: orange")
            else:
                self.chan1IsLabel.setStyleSheet("color: red")
        else:
            self.chan1IsLabel.setStyleSheet("color: black")
            
    def closeEvent(self, event):
        reply = QtGui.QMessageBox.question(self, 'Message',
            "Are you sure to quit?", QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)

        if reply == QtGui.QMessageBox.Yes:
            try:
                if self.si255.comm.connected:
                    self.si255.comm.close()
                if self.tempConnected:
                    self.tc08usb.close_unit()
            except:
                pass
            event.accept()
        else:
            event.ignore()
             
    def connectTemp(self):
        dll_path = os.path.join(os.getenv('ProgramFiles'),'Pico Technology', 'SDK', 'lib')
        try:
            self.tc08usb = TC08USB(dll_path = dll_path)
            if self.tc08usb.open_unit():
                self.tc08usb.set_mains(50)
                self.tc08usb.set_channel(1, USBTC08_TC_TYPE.K)
                self.getTemp()
                self.tempConnected = True
                self.updateTempTimer.start(1000)
            else:
                self.tempConnected = False
                self.connectTempAction.setChecked(False)
                QtGui.QMessageBox.critical(self,'Connection Error',
                                       'Could not connect to TC08-USB. Please try again')
                
        except USBTC08_ERROR as e:
            print(e)
        
        
    def createAction(self, text, slot=None, shortcut=None,
                     icon=None,tip=None,checkable=False,
                     signal='triggered()'):
        action = QtGui.QAction(text, self)
        if icon is not None:
            action.setIcon(QtGui.QIcon('../icons/%s.png' % icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None and not checkable:
            action.triggered.connect(slot)
        elif slot is not None and checkable:
            action.toggled.connect(slot)
        if checkable:
            action.setCheckable(True)
       
        return action
       
    def createIdFrame(self):
        f = QtGui.QGroupBox(self, title='IDs:')
        l = QtGui.QGridLayout(f)
        font = QtGui.QFont()
        font.setBold(False)
        font.setPointSize(16)
        prodIdLabel = QtGui.QLabel(text='Produktion:', font=font) 
        self.proID = QtGui.QLineEdit(font=font)
        self.proID.setAlignment(QtCore.Qt.AlignRight)
        fbgIdLabel = QtGui.QLabel(text='FBG:', font=font) 
        self.fbgID = QtGui.QLineEdit(font=font)
        self.fbgID.setAlignment(QtCore.Qt.AlignRight)
        sensorIdLabel = QtGui.QLabel(text='Sensor:', font=font)
        self.sensorID = QtGui.QLineEdit(font=font)
        self.sensorID.setAlignment(QtCore.Qt.AlignRight)
        
        l.addWidget(prodIdLabel,0,0)
        l.addWidget(self.proID,0,1)
        l.addWidget(fbgIdLabel,1,0)
        l.addWidget(self.fbgID,1,1)
        l.addWidget(sensorIdLabel,2,0)
        l.addWidget(self.sensorID,2,1)
        
        return f
        
    def createInfoWidget(self):
        i = QtGui.QFrame()
        #i.setMaximumWidth(400)
        il = QtGui.QVBoxLayout()
        
        logo = QtGui.QLabel()
        logo.setPixmap(QtGui.QPixmap('../pics/Logo loptek.jpg'))
        logoLay = QtGui.QHBoxLayout()
        logoLay.addStretch()
        logoLay.addWidget(logo)
        
        il.addLayout(logoLay)
        il.addWidget(self.createIdFrame())
        
        font = QtGui.QFont()
        font.setBold(True)
        font.setPointSize(20)
        isLabel = QtGui.QLabel(text='Ist')
        isLabel.setAlignment(QtCore.Qt.AlignCenter)
        isLabel.setFont(font)
        sollLabel= QtGui.QLabel(text='Soll')
        sollLabel.setAlignment(QtCore.Qt.AlignCenter)
        sollLabel.setFont(font)
        self.chan1IsLabel = QtGui.QLabel()
        self.chan1IsLabel.setText('0000.000')
        self.chan1IsLabel.setFont(font)
        self.chan1SollLabel = QtGui.QLabel()
        self.chan1SollLabel.setText('----.---')
        self.chan1SollLabel.setFont(font)
        font.setBold(True)
        font.setPointSize(12)
        self.dispSpin = QtGui.QSpinBox()
        self.dispSpin.setRange(100,self.__maxBuffer)
        self.dispSpin.setValue(500)
        #spinLabel = QtGui.QLabel(text='Points for Regression: ')
        #spinLabel.setFont(font)
        #self.numPointsSpin = QtGui.QSpinBox()
        #self.numPointsSpin.setRange(10,self.__maxBuffer)
        #self.numPointsSpin.setValue(50)
        #self.numPointsSpin.valueChanged.connect(self.plotW.setRegPoints)
        slopeLabel = QtGui.QLabel(text='Slope [pm/s]:')
        slopeLabel.setFont(font)
        dSlopeLabel = QtGui.QLabel(text= u'\u0394Slope [pm/s]:')
        dSlopeLabel.setFont(font)
        self.slopeCh1Label = QtGui.QLabel(text='---')
        self.slopeCh1Label.setFont(font)
        self.dSlopeCh1Label = QtGui.QLabel(text='---')
        self.dSlopeCh1Label.setFont(font)
        self.slopeCh1Dial = SlopeMeter()
        self.tempDisplay = QtGui.QLabel(text=u'-.- \u00b0C')
        font.setBold(True)
        font.setPointSize(16)
        self.tempDisplay.setAlignment(QtCore.Qt.AlignRight)
        self.tempDisplay.setFont(font)
        
        font.setBold(True)
        font.setPointSize(44)
        self.__timeStr = '00:00'        
        self.__timerLabel = QtGui.QLabel(self,text=self.__timeStr)
        self.__timerLabel.setStyleSheet("color: red")
        self.__timerLabel.setFont(font)
        self.__timerLabel.setFrameShape(QtGui.QFrame.StyledPanel)
        self.__timerLabel.setFrameShadow(QtGui.QFrame.Raised)
        
        valLayout = QtGui.QGridLayout()
        valLayout.addWidget(isLabel,0,0)
        valLayout.addWidget(sollLabel,0,1)
        valLayout.addWidget(self.chan1IsLabel,1,0)
        valLayout.addWidget(self.chan1SollLabel,1,1)
        valLayout.addWidget(self.slopeCh1Dial,2,0)
        valLayout.addWidget(self.tempDisplay,2,1)
        #valLayout.addWidget(spinLabel,3,0)
        #valLayout.addWidget(self.numPointsSpin,3,1)
        valLayout.addWidget(self.__timerLabel,3,0)
        
        
        self.slopeCh1Dial.setValue(0.)
        
        il.addLayout(valLayout)
        il.addStretch()
        i.setLayout(il)
        
        return i
        
        
    def createMenu(self):
        
        self.fileMenu = self.menuBar().addMenu('&File')
        self.maesMenu = self.menuBar().addMenu('&Measurement')
        self.helpMenu = self.menuBar().addMenu('&Help')
        waL = QtGui.QWidgetAction(self)
        dispSpinLabel = QtGui.QLabel(text='Points displayed: ')
        waL.setDefaultWidget(dispSpinLabel)
        
        #self.menuBar().addAction(wa)
        self.quitAction = self.createAction('Q&uit',slot=self.close,shortcut='Ctrl+Q',
                                            icon='Button Close',tip='Close App')
        self.connectAction = self.createAction('&Connect', slot=self.initDevice,
                                              tip='Connect Spectrometer', checkable = True,
                                              icon='Button Add')        
        self.connectTempAction = self.createAction('Thermo', slot=self.tempActionToggled, tip='Connect Thermometer',
                                                   checkable=True)
        
        self.startAction = self.createAction('St&art', slot=self.startMeasurement, shortcut='Ctrl+M',
                                             tip='Start Measurement', icon='Button Play')
#         #self.pauseAction = self.createAction('Pa&use', #slot=self.pauseMeasurement, shortcut='Ctrl+U', 
#          #                                    tip='Pause Measurement', icon='Button Pause')
#         
        self.stopAction = self.createAction('St&op', slot=self.stopMeasurement, shortcut='Ctrl+T',
                                        tip='Stop Measurment', icon='Button Stop')
        #self.dBmAction = self.createAction('dBm', tip='Plot logarithmic Data', checkable=True)
        #self.dBmAction.setChecked(True)
        
        self.showTraceAction = self.createAction('Trace', tip='Show Peakwavelength vs. Time', checkable=True)
        self.showTraceAction.setChecked(True)
        self.ptdAction = self.createPointsOfTraceAction()
        self.scalePlotAction = self.createScalePlotAction()
        self.scalePlotAction.setChecked(True)
        
        self.showSpecAction = self.createAction('Spec', slot=self.showPlot, tip='Show Spectrum', checkable=True)
        self.showSpecAction.setChecked(True)
        self.showTraceAction.toggled.connect(self.showPlot)
        
        self.showDBmData = self.createAction('dBm', tip='Plot Spectum as dBm Data', checkable=True)
        self.showDBmData.setChecked(True)
        
        self.fileMenu.addAction(self.quitAction)

        aboutAction = self.createAction('About', slot=self.about)
                                     
        self.helpMenu.addAction(aboutAction)
        
        self.toolbar = self.addToolBar('Measurement')
        
        self.addActions(self.toolbar, (self.connectAction, self.connectTempAction, None, self.startAction, self.stopAction,
                                      None,  self.showTraceAction, self.ptdAction, None, 
                                      self.showSpecAction, self.scalePlotAction, self.showDBmData))#, self.importFileAction, self.importLogAction, self.exportData, None,self.showOptAction,None,self.fitAction, self.showFitAction))
        
    def createPointsOfTraceAction(self):
        wa = QtGui.QWidgetAction(self)
        s = QtGui.QSpinBox()
        s.setRange(100,self.__maxBuffer)
        s.setValue(500)
        sl = QtGui.QLabel(text='Points: ')
        self.plotW.setTracePoints(s.value())
        s.valueChanged.connect(self.plotW.setTracePoints)
        
        l = QtGui.QHBoxLayout()
        l.addWidget(sl)
        l.addWidget(s)
        
        w = QtGui.QWidget()
        w.setLayout(l)
        wa.setDefaultWidget(w)
        
        return wa
        
    def createScalePlotAction(self):
        wa = QtGui.QWidgetAction(self)
        
        self.minWlSpin = QtGui.QDoubleSpinBox()
        self.minWlSpin.setDecimals(3)
        self.minWlSpin.setSuffix(' nm')
        self.minWlSpin.setRange(1460.0,1615.0)
        self.minWlSpin.setValue(1540.0)
        self.minWlSpin.valueChanged.connect(self.scaleInputSpectrum)
        
        self.maxWlSpin = QtGui.QDoubleSpinBox()
        self.maxWlSpin.setDecimals(3)
        self.maxWlSpin.setSuffix(' nm')
        self.maxWlSpin.setRange(1465.0, 1620.0)
        self.maxWlSpin.setValue(1570.0)
        self.maxWlSpin.valueChanged.connect(self.scaleInputSpectrum)
        
        l = QtGui.QHBoxLayout()
        l.addWidget(self.minWlSpin)
        l.addWidget(QtGui.QLabel(text=' - '))
        l.addWidget(self.maxWlSpin)
        
        w = QtGui.QWidget()
        w.setLayout(l)
        wa.setDefaultWidget(w)
        
        return wa
    
    def disconnectTemp(self):
        if self.updateTempTimer.isActive():
            self.updateTempTimer.stop()
        if self.tempConnected:
                    self.tc08usb.close_unit()
        self.tempConnected = False
   
    def getData(self):
        #get spectra
        y = self.getdBmSpec()
        y = y[self.__scalePos]
        wl = self.__scaledWavelength
        if self.showSpecAction.isChecked():
            if not self.showDBmData.isChecked():
                dbmData = np.power(10,y/10)
            else:
                dbmData = y
            self.plotW.plotS(wl,dbmData)
        
        #get peak data
        numVal = self.getPeakData(wl, y)
        if self.showTraceAction.isChecked():
            if numVal:
                self.plotW.plotT(self.peaksTime[:numVal-1], self.peaks[:numVal-1])
            
                   
        now = time.time()
        dt = now - self.lastTime
        if self.fps is None:
             self.fps = 1.0/dt
        else:
             s = np.clip(dt*3., 0, 1)
             self.fps = self.fps * (1-s) + (1.0/dt) * s
        self.statusBar().showMessage('%0.2f Hz' % (self.fps))
        self.lastTime = now
        
    def getdBmSpec(self):
        try:
            dbmData = np.array(self.si255.get_spectrum([1,]), dtype=float)
            
        except hyperion.HyperionError as e:
            print(e)
        
        return dbmData
        
    def getIDs(self):
        pro = self.proID.text()
        fbg = self.fbgID.text()
        sensor = self.sensorID.text()
        er = self.prodInfo.setIDs(pro, fbg, sensor)        
        return er
        
    def getPeakData(self, wl, dbmData):
        peak = self.centerOfGravity(wl, dbmData)
        timestamp = time.clock() - self.startTime
        numVal = np.count_nonzero(self.peaks)
        self.chan1IsLabel.setText(str("{0:.3f}".format(peak)))
        self.calculateLabelColor()
        if self.waitHeating:
            if peak >= self.__heatingStartWl:
                
                self.heatingTimer.start()
                self.waitHeating = False
                self.__heatingStartTime = time.time()
                self.prodInfo.buttons.startButton.setEnabled(False)
                self.prodInfo.buttons.backButton.setEnabled(False)
                self.prodInfo.buttons.stopButton.setEnabled(False)
                
        if numVal < self.__maxBuffer:
            self.peaks[numVal] = peak
            self.peaksTime[numVal] = timestamp
        else:
            self.peaks = shift(self.peaks, -1, cval = peak)
            self.peaksTime = shift(self.peaksTime, -1, cval = timestamp)
            
        return numVal
        
    def getTemp(self):
        self.tc08usb.get_single()
        temp = self.tc08usb[1]
        tempStr = str("{0:.1f}".format(temp)) + u' \u00b0C'
        self.tempDisplay.setText(tempStr)
        
    
    def saveSpectrum(self, x, y):
        if len(x) == 0:
            y = self.getdBmSpec()
            y = y[self.__scalePos]
            x = self.__scaledWavelength
        fname = time.strftime('%Y%m%d_%H%M%S') + self.sensorID.text() + '.spc'
        _file = os.path.join(str(self.specFolder) , str(fname))  
        
        File = open(_file,'w')
        for i in range(len(x)):
            File.write(str("{0:.3f}".format(x[i])) + '\t' + str(y[i]) + '\n')
        File.close()
        return fname
            
    def scaleInputSpectrum(self):
        _min = float(self.minWlSpin.value())
        _max = float(self.maxWlSpin.value())
        if _min > _max:
            _min = _max-1
        if _max < _min:
            _max = _min+1
        self.__scalePos = np.where((self.__wavelength>=_min)&(self.__wavelength<=_max))[0]
        self.__scaledWavelength = self.__wavelength[self.__scalePos]
        
    def setActionState(self):
        if self.isConnected:
            if self.measurementActive:
                self.startAction.setEnabled(False)
                self.stopAction.setEnabled(True)
            else:
                self.startAction.setEnabled(True)
                self.stopAction.setEnabled(False)
        else:
            self.startAction.setEnabled(False)
            self.stopAction.setEnabled(False)
            
    def setProdIDs(self, proID, sensorID):
        self.proID.setText(proID)
        self.fbgID.clear()
        self.sensorID.setText(sensorID)
            
    def setSlope(self, slope, Dslope):
        self.slopeCh1Label.setText(slope)
        self.dSlopeCh1Label.setText(Dslope)  
        self.slopeCh1Dial.setSlope(float(slope))
        
    def setTime(self, sec):
        m, s = divmod(sec, 60)
        timeStr="%02d:%02d" % (m, s)
        self.__timerLabel.setText(timeStr)
        
    def setAutoScale(self, state):
        if state:
            self.minWlSpin.setEnabled(True)
            self.maxWlSpin.setEnabled(True)
            self.plotW.setAutoScaleWavelength(True)
        else:
            self.minWlSpin.setEnabled(False)
            self.maxWlSpin.setEnabled(False)
            self.plotW.setAutoScaleWavelength(False)
        
    def showPlot(self):
        plotT = self.showTraceAction.isChecked()
        plotS = self.showSpecAction.isChecked()
        self.ptdAction.setEnabled(plotT)
        self.scalePlotAction.setEnabled(plotS)
        self.plotW.setShowPlot(plotT, plotS)
        
    def startMeasurement(self):
        self.startTime = time.clock()
        self.lastTime= self.startTime
        self.fps=None
        self.peaks = np.zeros(self.__maxBuffer)
        self.updateTimer.start(100)
        self.measurementActive = True
        self.setActionState()
        
    def stopMeasurement(self):
        self.updateTimer.stop()
        self.measurementActive = False
        self.setActionState()
    

    def testChannelForPeaks(self, Channel = 1):
        i = Channel
        numFBGs = 0
        try:
            peaks = self.si255.get_peaks()
            peakData  = peaks.get_channel(i)
            numFBGs = len(peakData)
            print('Channel ',i,' ',numFBGs,' Gitter')
        except:
            pass
        return numFBGs
                
    def tempActionToggled(self, state):
        if state:
            self.connectTemp()
        else:
            self.disconnectTemp()
            
#### Production
            
    def activateTimer(self):
        self.heatingTimer = QtCore.QTimer()
        self.heatingTimer.setInterval(500)
        self.heatingTimer.timeout.connect(self.updateHeatingTimer)
        self.waitHeating = True
        
    def activateCooling(self):
        self.__activateCooling = True
        
    def updateHeatingTimer(self):
        ht = time.time() - self.__heatingStartTime
        self.setTime(ht)
        if ht >= self.__heatingTime:
            self.heatingTimer.stop()
            peak = self.chan1IsLabel.text()
            self.prodInfo.setPeakWavelength(peak)
            temp = self.tempDisplay.text()
            self.prodInfo.setTemp(temp)
            self.prodInfo.buttons.startButton.setEnabled(True)
            self.prodInfo.buttons.backButton.setEnabled(True)
            self.prodInfo.buttons.stopButton.setEnabled(True)
            self.setTime(0)
                
      
        
    def prodSequenzClicked(self):
        
        if self.prodInfo.buttons.startButton.text() == 'Start':
            print('Start')
            self.prodInfo.startProduction()
        elif self.prodInfo.buttons.startButton.text() == 'Weiter':
            print('Next Step')
            if self.prodInfo.getProStep() < self.prodInfo.proStepNb[-1]-2:
                if self.parseProdCondition():
                    self.parseProdMeas()
                    self.prodInfo.nextProductionStep()
            elif self.prodInfo.getProStep() == self.prodInfo.proStepNb[-1]-2:
                if self.parseProdCondition():
                    self.parseProdMeas()
                    self.prodInfo.buttons.startButton.setText('Neu')
                    self.prodInfo.nextProductionStep()
        elif self.prodInfo.buttons.startButton.text() == 'Neu':
            print('Neu')
            self.prodInfo.startProduction()
        else:
            print('Error Production Sequenz')
            
    def parseProdCondition(self):
        cond = self.prodInfo.getProCondition()
        if cond:
            cond = cond.split(',')
            #print(cond)
            for c in cond:
                c = c.strip()
                if c == 'fbg':
                    if not self.testChannelForPeaks(1):
                        QtGui.QMessageBox.critical(self,'Kein FBG gefunden',
                                       unicode('Konnte keinen Peak detektieren. Bitte überprüfen Sie die angeschlossene Faser', 'utf-8'))
                        return 0
                elif c == 'ids':
                    if not self.proID.text():
                        QtGui.QMessageBox.critical(self,'Keine Produktions ID',
                                       unicode('Bitte geben Sie eine Produktions-Identifikationsnummer ein.', 'utf-8'))
                        return 0
                    if not self.fbgID.text():
                        QtGui.QMessageBox.critical(self,'Keine FBG ID',
                                       unicode('Bitte geben Sie eine FBG-Identifikationsnummer ein.', 'utf-8'))
                        return 0
                    if not self.sensorID.text():
                        QtGui.QMessageBox.critical(self,'Keine Sensor ID',
                                       unicode('Bitte geben Sie eine Sensor -Identifikationsnummer ein.', 'utf-8'))
                        return 0
                    if not self.getIDs():
                        QtGui.QMessageBox.critical(self,'Schreibfehler',
                                       unicode('Konnte Identifikationsnummern nicht in Tabelle schreiben.', 'utf-8'))
                        return 0
                elif c == 'Zielwert':
                    tol = self.prodInfo.getTolaranz()
                    diff = abs(float(self.chan1IsLabel.text())-float(self.chan1SollLabel.text()))
                    if diff > tol:
                        reply = QtGui.QMessageBox.question(self, 'Warnung',
                                    unicode("""Peakwellenlänge entspricht nicht der Vorgabe!
                                    \n\n Wollen Sie wirklich fortfahren""", 'utf-8'), 
                                    QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)

                        if reply == QtGui.QMessageBox.Yes:
                            return 1
                        else:
                            return 0
        return 1
     
    def parseProdMeas(self):
        meas = self.prodInfo.getProMeas()
        x = self.__scaledWavelength
        y = None
        cenFit = 0.
        cenCoG = 0.
        fwhm = 0
        asym = 0.
        peak = 0.
        if meas:
            meas = meas.split(',')
            #print (meas)
            for m in meas:
                m = m.strip()
                if m == 'peak':
                    print('Measure Peak Wavelength')
                    peak = self.chan1IsLabel.text()
                    self.prodInfo.setPeakWavelength(peak)
                elif m == 'spectrum':
                    print('Measure Spectrum')
                    y = self.getdBmSpec()
                    y = y[self.__scalePos]
                    fname = self.saveSpectrum(x,y)
                    self.prodInfo.setSpecFile(fname)
                elif m == 'fwhm':
                    print('Determine FWHM')
                    cenFit, fwhm = self.peakFit(x,y,peak)
                    self.prodInfo.setFWHM(fwhm)
                elif m == 'asymm':
                    print('Determine Asymmety Ratio')
                    cenCoG = self.centerOfGravity(x,y, peak)
                    asym = self.calculateAsym(cenFit, cenCoG)
                    self.prodInfo.setAsymmetrie(asym)
                elif m == 'temp':
                    print('Measure Temperature')
                    temp = self.tempDisplay.text()
                    self.prodInfo.setTemp(temp)
                elif m == 'timer':
                    print('Activate heating Timer.')
                    self.activateTimer()
                elif m == 'cooling':
                    print('Wait for Temprature = 90°C')
                    self.activateCooling()
   
#### calculations
   
    def peakFit(self, x, y, peak=None):
        if len(x) == 0:
            y = self.getdBmSpec()
            y = y[self.__scalePos]
            x = self.__scaledWavelength
        y = np.power(10,y/10)
        mod = GaussianModel()
        pars = mod.guess(y, x=x)
        out  = mod.fit(y, pars, x=x)
        
        print(out.fit_report(min_correl=0.25))
        center = out.best_values['center']
        fwhm = out.best_values['sigma']*2.3548
        
        return center, fwhm#, amp
   
    def centerOfGravity(self, x, y, peak=None):
        if len(x) == 0:
            y = self.getdBmSpec()
            y = y[self.__scalePos]
            x = self.__scaledWavelength
        y = np.power(10,y/10)
        if not peak:
            pos = np.where(y>(np.max(y)*.3))[0]
        else:
            print('CoG spectral Window')
            xmin = float(peak)-float(self.cogSpectralWin)
            xmax = float(peak)+float(self.cogSpectralWin)
            pos = np.where((x>=xmin)&(x<=xmax))[0]
        x = x[pos]
        y = y[pos]
           
        cog = (x*y).sum()/y.sum()
        return cog
   
    def calculateAsym(self, pFit, pCOG):
        if pFit:
            return np.abs(pFit-pCOG)
        else:
            return 0
        
