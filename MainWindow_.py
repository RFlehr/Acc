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
__version__ = '0.6.0    '
__date__ = '07.07.2016'
__author__ = 'Roman Flehr'
__cp__ = u'\u00a9 2016 Loptek GmbH & Co. KG'

import sys
sys.path.append('../')

from pyqtgraph.Qt import QtGui, QtCore
import plot as pl
import hyperion, time, os, Queue
import numpy as np
from scipy.ndimage.interpolation import shift
from qwt_widgets import SlopeMeter
import productionInfo
from tc08usb import TC08USB, USBTC08_TC_TYPE, USBTC08_ERROR#, USBTC08_UNITS
#from lmfit.models import GaussianModel
from scipy.optimize import curve_fit
from options import OptionDialog
from MyDialogs import NewSensorDialog
from Monitor import MonitorHyperionThread, MonitorTC08USBThread



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
        self.plotW = pl.Plot()
        
        self.loadSettings()
        
        
        
        self.testModus = 0
        
        
        self.updateTimer = QtCore.QTimer()
        self.updateTimer.timeout.connect(self.getData)
        self.updateTempTimer = QtCore.QTimer()
        self.updateTempTimer.timeout.connect(self.getTemp)
        self.startTime = None
        self.heatingTimer = QtCore.QTimer()
        
        self.setWindowTitle(__title__ + ' ' + __version__)
        self.resize(900, 600)
        
        
        self.prodInfo = productionInfo.ProductionInfo()
        self.waitHeating = False
        self.__activateCooling = False
        self.__finalTemp = 90
        self.cogSpectralWin = 2.5
        self.__SpecWinRL = 2
        
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
                
        self.plotW.returnSlope.connect(self.setSlope)
        
        self.slopeCh1Dial.setSlope(0)
        self.setActionState()
        
        self.prodInfo.emitSoll.connect(self.setSollLabel)
        self.prodInfo.emitProdIds.connect(self.setProdIDs)
        self.prodInfo.emitClearIDs.connect(self.clearIDs)
        self.prodInfo.buttons.startButton.clicked.connect(self.prodSequenzClicked)
        self.prodInfo.buttons.backButton.clicked.connect(self.prodSequenzBack)
        
        self.loadSettings()


    
    def initDevice(self):
        if self.isConnected:
            try:
                if self.si255.comm.connected:
                    self.si255.comm.close()
                    self.isConnected = False
                    self.setActionState()
            except:
                pass
        else:
            try:
                si255Comm = hyperion.HCommTCPSocket(self.HyperionIP, timeout = 5000)
            except hyperion.HyperionError as e:
                print e , ' \thaha'   
            if si255Comm.connected:
                self.si255 = hyperion.Hyperion(comm = si255Comm)
                self.isConnected=True
                self.__wavelength =np.array(self.si255.wavelengths)
                self.__scalePos = np.where((self.__wavelength>=self.__minWl) & (self.__wavelength<self.__maxWl))[0]
                self.__scaledWavelength = self.__wavelength[self.__scalePos]
                self.setActionState()   
                return 1
            else:
                self.isConnected=False
                self.printError(5)
                self.setActionState()   
                return 0
         
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
        if self.chan1SollLabel.isVisible():
            tol = self.prodInfo.getTolaranz()
            diff = float(self.chan1IsLabel.text())-float(self.chan1SollLabel.text())
            #print(diff, self.sollGreen[self.prodStep], self.sollGreen[self.prodStep]*3)
            if self.prodInfo.getProdPlanNum() == 2:
                if diff < tol:
                    self.chan1IsLabel.setStyleSheet("color: green")
                elif diff < tol*2:
                    self.chan1IsLabel.setStyleSheet("color: orange")
                else:
                    self.chan1IsLabel.setStyleSheet("color: red")
            else:
                if abs(diff) <= tol:
                    self.chan1IsLabel.setStyleSheet("color: green")
                elif abs(diff) <= tol*3:
                    self.chan1IsLabel.setStyleSheet("color: orange")
                else:
                    self.chan1IsLabel.setStyleSheet("color: red")
        else:
            self.chan1IsLabel.setStyleSheet("color: black")
            
    def clearIDs(self):
        self.proID.clear()
        self.fbgID.clear()
        self.sensorID.clear()
            
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
                self.tempQ = Queue.Queue(100)
                self.tempConnected = True
                self.tempMon = MonitorTC08USBThread(self.tc08usb, self.tempQ)
                self.tempMon.start()
                self.tempConnected = True
                self.updateTempTimer.start(150)
                return 1
            else:
                self.tempConnected = False
                #self.connectTempAction.setChecked(False)
                QtGui.QMessageBox.critical(self,'Verbindungsfehler',
                                       'Konnte keine Verbindung zu TC08-USB herstellen. Bitte nochmal versuchen!')
                return 0
                
        except USBTC08_ERROR as e:
            print(e)
            
        self.setActionState()
        
        
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
        fbgIdLabel = QtGui.QLabel(text='Faser:', font=font) 
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
        self.sollLabel= QtGui.QLabel(text='Soll')
        self.sollLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.sollLabel.setFont(font)
        self.sollLabel.setVisible(False)
        self.chan1IsLabel = QtGui.QLabel()
        self.chan1IsLabel.setText('0.0')
        self.chan1IsLabel.setFont(font)
        self.chan1SollLabel = QtGui.QLabel()
        #self.chan1SollLabel.setText('----.---')
        self.chan1SollLabel.setFont(font)
        self.chan1SollLabel.setAlignment(QtCore.Qt.AlignRight)
        self.chan1SollLabel.setVisible(False)
        font.setBold(True)
        font.setPointSize(12)
        #slopeLabel = QtGui.QLabel(text='Slope [pm/s]:')
        #slopeLabel.setFont(font)
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
        self.__timerLabel.setFont(font)
        self.__timerLabel.setFrameShape(QtGui.QFrame.StyledPanel)
        self.__timerLabel.setFrameShadow(QtGui.QFrame.Raised)
        
        style = "font-size: 16px; font-weight: bold"
        self.openSensorButton = QtGui.QPushButton(text='SensorID laden')
        self.openSensorButton.setStyleSheet(style)
        self.openSensorButton.clicked.connect(self.openSensor)     
        self.openSensorButton.setEnabled(False)
        self.openSensorButton.setVisible(False)
        
        valLayout = QtGui.QGridLayout()
        valLayout.addWidget(isLabel,0,0)
        valLayout.addWidget(self.sollLabel,0,1)
        valLayout.addWidget(self.chan1IsLabel,1,0)
        valLayout.addWidget(self.chan1SollLabel,1,1)
        valLayout.addWidget(self.slopeCh1Dial,3,0)
        valLayout.addWidget(self.tempDisplay,2,1)
        #valLayout.addWidget(self.__timerLabel,4,0)
        #valLayout.addWidget(self.openSensorButton,4,0)
        
        
        self.slopeCh1Dial.setValue(0.)
        bottomL = QtGui.QHBoxLayout()
        bottomL.addStretch()
        bottomL.addWidget(self.__timerLabel)
        bottomL.addWidget(self.openSensorButton)
        bottomL.addStretch()
        
        il.addLayout(valLayout)
        il.addStretch()
        il.addLayout(bottomL)
        i.setLayout(il)
        
        return i
        
        
    def createMenu(self):
        
        self.fileMenu = self.menuBar().addMenu('&Datei')
        self.maesMenu = self.menuBar().addMenu('&Messung')
        self.helpMenu = self.menuBar().addMenu('&Hilfe')
        waL = QtGui.QWidgetAction(self)
        dispSpinLabel = QtGui.QLabel(text='Points displayed: ')
        waL.setDefaultWidget(dispSpinLabel)
        
        #self.menuBar().addAction(wa)
        self.quitAction = self.createAction('Q&uit',slot=self.close,shortcut='Ctrl+Q',
                                            icon='Button Close',tip='Close App')
        self.connectAction = self.createAction('Verbinden', slot=self.initDevice,
                                              tip='Verbinde Spectrometer')        
        self.connectTempAction = self.createAction('Thermo', slot=self.tempActionToggled, tip='Verbinde Thermometer',
                                                   icon='Thermo')
        
        self.startAction = self.createAction('St&art', slot=self.startMeasurement, shortcut='Ctrl+M',
                                             tip='Start Messung', icon='Button Play')
#         #self.pauseAction = self.createAction('Pa&use', #slot=self.pauseMeasurement, shortcut='Ctrl+U', 
#          #                                    tip='Pause Measurement', icon='Button Pause')
#         
        self.stopAction = self.createAction('St&op', slot=self.stopMeasurement, shortcut='Ctrl+T',
                                        tip='Stop Messung', icon='Button Stop')
        
        self.buildAction = self.createAction('Aufbau', checkable=True)
        self.siliconAction = self.createAction('Silikon', checkable=True)
        self.terminationAction = self.createAction('Faserterminierung', checkable=True)
        
        self.buildAction.setChecked(True)
        self.buildAction.toggled.connect(self.setBuildAction)
        self.siliconAction.toggled.connect(self.setSiliconAction)
        self.terminationAction.toggled.connect(self.setTerminationAction)
        
        
        self.fileMenu.addAction(self.quitAction)

        aboutAction = self.createAction('About', slot=self.about)
        
        optionAction = self.createAction('O&ptionen', tip='Optionsdialog', slot=self.openOptionsDialog)
                                     
        self.helpMenu.addAction(aboutAction)
        self.helpMenu.addAction(optionAction)
        
        self.toolbar = self.addToolBar('Measurement')
        
        self.addActions(self.toolbar, (self.connectAction, self.connectTempAction, None, self.startAction, self.stopAction, None,
                                       self.buildAction, self.siliconAction, self.terminationAction))#, self.importFileAction, self.importLogAction, self.exportData, None,self.showOptAction,None,self.fitAction, self.showFitAction))
    
    def setBuildAction(self):
        if self.buildAction.isChecked():
            self.siliconAction.setChecked(False)
            self.terminationAction.setChecked(False)
            self.clearIDs()
            
            self.prodInfo.changeProdPlan(0)
                        
            
    def setSiliconAction(self):
        if self.siliconAction.isChecked():
            self.buildAction.setChecked(False)
            self.terminationAction.setChecked(False)
            self.clearIDs()
            
            self.prodInfo.changeProdPlan(1)
            self.__timerLabel.setVisible(False)
                        
    def setTerminationAction(self):
        if self.terminationAction.isChecked():
            self.buildAction.setChecked(False)
            self.siliconAction.setChecked(False)
            self.clearIDs()
            
            self.prodInfo.changeProdPlan(2)
            
            
    def disconnectTemp(self):
        if self.updateTempTimer.isActive():
            self.updateTempTimer.stop()
        if self.tempMon:
            if self.tempMon.alive.isSet():
                self.tempMon.join()
        self.tempMon = None
        self.tc08usb.close_unit()
        self.tc08usb = None
        self.tempConnected = False
        self.tempDisplay = QtGui.QLabel(text=u'-.- \u00b0C')
        
    def getAllFromQueue(self, Q):
        """ Generator to yield one after the others all items 
            currently in the queue Q, without any waiting.
        """
        try:
            while True:
                yield Q.get_nowait( )
        except Queue.Empty:
            raise StopIteration
   
    def getData(self):
        #get spectra
        data, timestamp, success  = self.readDataFromQ()
        if not success: 
            return None
        
        self.dbmData = data[0]
        actualTime = timestamp-self.startTime
        
        wl = self.__scaledWavelength
        self.plotW.plotS(wl,self.dbmData)
        if self.prodInfo.getProdPlanNum() == 2:
            rl = self.calcReturnloss()
            self.chan1IsLabel.setText(str("{0:.1f}".format(rl)))
            self.calculateLabelColor()
        else:
        #get peak data
            numVal = self.getPeakData(wl, self.dbmData, actualTime)
            self.plotW.plotT(self.peaksTime[:numVal-1], self.peaks[:numVal-1])
                
    def readDataFromQ(self):
        qData = list(list(self.getAllFromQueue(self.dataQ)))
        timestamp = 0
        d = None
        if len(qData) > 0:
            d = np.array(qData[-1][0])
            timestamp = qData[-1][1]
            d = d[:,self.__scalePos]
            return d, timestamp , 1
        else:
            return 0,0,0
        
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
        
    def getPeakData(self, wl, dbmData, timestamp):
        peak = self.peakFit(wl, dbmData)
        numVal = np.count_nonzero(self.peaks)
        self.chan1IsLabel.setText(str("{0:.3f}".format(peak)))
        self.calculateLabelColor()
        if self.waitHeating:
            if peak >= self.__heatingStartWl:
                self.heatingTimer.start()
                self.waitHeating = False
                self.prodInfo.buttons.startButton.setEnabled(True)
                self.prodInfo.buttons.backButton.setEnabled(False)
                self.prodInfo.buttons.stopButton.setEnabled(False)
                self.__heatingStartTime = time.time()

                
        if numVal < self.__maxBuffer:
            self.peaks[numVal] = peak
            self.peaksTime[numVal] = timestamp
        else:
            self.peaks = shift(self.peaks, -1, cval = peak)
            self.peaksTime = shift(self.peaksTime, -1, cval = timestamp)
            
        return numVal
        
    def getTemp(self):
        try: 
            temp = self.tempQ.get(True, 0.01)
            
        except Queue.Empty:
            return None
        tempStr = str("{0:.1f}".format(temp)) + u' \u00b0C'
        self.tempDisplay.setText(tempStr)

    def loadSettings(self):
        print('Lade Einstellungen Hauptfenster')
        self.__Vorsp = []
        self.__VorspTol = []
        settings = QtCore.QSettings('test.ini',QtCore.QSettings.IniFormat)
        settings.beginGroup('Produktion')
        self.__heatingTime = settings.value('Heizdauer').toInt()[0]
        vorSp = settings.value('VorspannFein').toFloat()[0]
        deltaHeating = settings.value('HeizDetekt').toFloat()[0]
        self.__SpecWinRL = settings.value('windowRL').toFloat()[0]
        settings.endGroup()
        
        settings.beginGroup('Dateipfade')
        self.specFolder = str(settings.value('Spektrenordner').toString())
        settings.endGroup()
        self.__heatingStartWl = vorSp + deltaHeating
        
        settings.beginGroup('Plot')
        self.__maxBuffer = settings.value('Buffer').toInt()[0]
        self.plotW.setTracePoints(settings.value('TracePunkte').toInt()[0])
        showTrace = settings.value('ShowTrace').toInt()[0]
        showSpec = settings.value('ShowSpec').toInt()[0]
        minWl = settings.value('MinWl').toFloat()[0]
        maxWl = settings.value('MaxWl').toFloat()[0]
        regPoints = settings.value('RegPoints').toInt()[0]
        settings.endGroup()
        self.showPlot(showTrace,showSpec)
        self.scaleInputSpectrum(minWl,maxWl)
        self.setBuffer()
        self.plotW.setRegPoints(regPoints)
        print('Einstellungen Hauptfenster wurden geladen')
        
    
    def openOptionsDialog(self):
        passW, ok = QtGui.QInputDialog.getText(self,"Optionen", "Bitte Password eingeben")
        if ok and passW == 'Test':
            option = OptionDialog()
            if option.exec_():
                self.prodInfo.loadSettings()
                self.loadSettings()

    def openSensor(self):
        ids = self.prodInfo.getSensorIDs() 
        newDia = NewSensorDialog(ids)
        index = 0
        if newDia.exec_():
            index = newDia.setSensor()
            self.setIDbyIndex(index)
            
    def setIDbyIndex(self, index =-1):
        pro, fbg, sens = self.prodInfo.getIDbyIndex(index)
        self.proID.setText(pro)
        self.fbgID.setText(fbg)
        self.sensorID.setText(sens)
        
    def saveSpectrum(self, x, y):
        if len(x) == 0:
            y = self.dbmData
            x = self.__scaledWavelength
        fname = time.strftime('%Y%m%d_%H%M%S') + self.sensorID.text() + '.spc'
        _file = os.path.join(str(self.specFolder) , str(fname))  
        
        File = open(_file,'w')
        for i in range(len(x)):
            File.write(str("{0:.3f}".format(x[i])) + '\t' + str(y[i]) + '\n')
        File.close()
        return fname
            
    def scaleInputSpectrum(self,_min,_max):
        self.__minWl = _min
        self.__maxWl = _max
        self.__scalePos = np.where((self.__wavelength>=self.__minWl)&(self.__wavelength<=self.__maxWl))[0]
        self.__scaledWavelength = self.__wavelength[self.__scalePos]
        
    def setActionState(self):
        if self.isConnected:
            self.connectAction.setIcon(QtGui.QIcon('../icons/Button Delete.png'))
            if self.measurementActive:
                self.connectAction.setEnabled(False)
                self.connectTempAction.setEnabled(False)
                self.startAction.setEnabled(False)
                self.stopAction.setEnabled(True)
            else:
                self.connectAction.setEnabled(True)
                self.connectTempAction.setEnabled(True)
                self.startAction.setEnabled(True)
                self.stopAction.setEnabled(False)
        else:
            self.connectAction.setIcon(QtGui.QIcon('../icons/Button Add.png'))
            self.startAction.setEnabled(False)
            self.stopAction.setEnabled(False)
        if self.tempConnected:
            self.connectTempAction.setIcon(QtGui.QIcon('../icons/Thermo.png'))
        else:
            self.connectTempAction.setIcon(QtGui.QIcon('../icons/NoThermo.png'))
            
    def setBuffer(self):
        self.peaks = np.zeros(self.__maxBuffer)
        self.peaksTime = np.zeros(self.__maxBuffer)
            
    def setProdIDs(self, proID, sensorID):
        self.proID.setText(proID)
        self.fbgID.clear()
        self.sensorID.setText(sensorID)
            
    def setSlope(self, slope):
        self.slopeCh1Dial.setSlope(slope)
        
    def setSollLabel(self, text):
        if text:
            self.sollLabel.setVisible(True)
            self.chan1SollLabel.setVisible(True)
            self.chan1SollLabel.setText(text)
        else:
            self.sollLabel.setVisible(False)
            self.chan1SollLabel.setVisible(False)
            
            
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
        
    def showPlot(self,plotT, plotS):
        self.plotW.setShowPlot(plotT, plotS)
        
    def startMeasurement(self):
        self.setBuffer()
        self.startTime = time.time()
        #initialize Queue
        self.dataQ = Queue.Queue(100)
        #self.initTempArray()
        self.Monitor = MonitorHyperionThread(self.dataQ, self.si255, 
                                         channelList=[1,], specDevider=1)
        self.Monitor.start()
        self.updateTimer.start(100)
        self.measurementActive = True
        self.setActionState()
        
    def stopMeasurement(self):
        self.updateTimer.stop()
        try:
            self.Monitor.join(0.1)
        except:
            pass
        self.Monitor = None
        self.si255.disable_spectrum_streaming()
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
        
    def testSpectrometer(self):
        print('Test for Spectrometer')
        try:
            if self.si255:
                if self.si255.comm.connected:
                    return 1
                else:
                    return self.initDevice()
            else:
                return self.initDevice()
        except:
            pass
            
    def testThermometer(self):
        print('Test for Thermometer')
        try:
            if not self.tempConnected:
                self.connectTemp()
        except:
            pass
        if self.tempConnected:
            return 1
        else:
            self.printError(6)
            return 0
                
    def tempActionToggled(self, state):
        if not self.tempConnected:
            self.connectTemp()
        else:
            self.disconnectTemp()
        self.setActionState()
            
#### Production
            
    def activateTimer(self):
        self.heatingTimer = QtCore.QTimer()
        self.heatingTimer.setInterval(500)
        self.heatingTimer.timeout.connect(self.updateHeatingTimer)
        self.waitHeating = True
        self.prodInfo.buttons.startButton.setEnabled(False)
        self.__timerLabel.setStyleSheet("color: black")
        
    def activateCooling(self):
        self.__activateCooling = True
        
    def activateOpenSensor(self):
        
        if self.prodInfo.getProdPlanNum():
            self.__timerLabel.setVisible(False)
            self.openSensorButton.setVisible(True)
            if self.prodInfo.getProStep() == 0:
                self.clearIDs()
                self.openSensorButton.setEnabled(True)
            else:
                self.openSensorButton.setEnabled(False)
        else:
            self.__timerLabel.setVisible(True)
            self.openSensorButton.setVisible(False)
        
        
    def updateHeatingTimer(self):
        ht = time.time() - self.__heatingStartTime
        self.setTime(ht)
        if ht >= self.__heatingTime:
            self.heatingTimer.stop()
            self.__timerLabel.setStyleSheet("color: green")
#==============================================================================
#             peak = self.chan1IsLabel.text()
#             self.prodInfo.setPeakWavelength(peak)
#             temp = self.tempDisplay.text()
#             self.prodInfo.setTemp(temp)
#             self.prodInfo.buttons.startButton.setEnabled(True)
#             self.prodInfo.buttons.backButton.setEnabled(True)
#             self.prodInfo.buttons.stopButton.setEnabled(True)
#             self.setTime(0)
#==============================================================================
                
    def startProductionSequence(self):
        if not self.testModus:
            if not self.testThermometer(): 
                return 0
            if not self.testSpectrometer(): 
                return 0
            if not self.measurementActive:
                self.startMeasurement()
        print('Starte neue Produktionssequenz')
        self.prodInfo.startProduction()
        
        
    def prodSequenzClicked(self):
        if self.prodInfo.buttons.startButton.text() == 'Start':
            self.startProductionSequence()
            
        elif self.prodInfo.buttons.startButton.text() == 'Weiter':
            print('Next Step')
            if self.prodInfo.getProStep() < self.prodInfo.proStepNb[-1]-2:
                self.prodInfo.buttons.setEnabled(False)
                if self.parseProdCondition():
                    self.parseProdMeas()
                    self.prodInfo.nextProductionStep()
                self.prodInfo.buttons.setEnabled(True)
                
            elif self.prodInfo.getProStep() == self.prodInfo.proStepNb[-1]-2:
                if self.parseProdCondition():
                    self.parseProdMeas()
                    self.prodInfo.buttons.startButton.setText('Neu')
                    self.prodInfo.nextProductionStep()
        elif self.prodInfo.buttons.startButton.text() == 'Neu':
            self.prodInfo.productionSequenzCancel(0)
            
        else:
            print('Error Production Sequenz')
        self.activateOpenSensor()
        #self.prodInfo.buttons.startButton.setFocus()
        
            
    def prodSequenzBack(self):
        if self.prodInfo.getProStep() > 0:
            self.prodInfo.productionSequenzBack()
        self.activateOpenSensor()
            
    def parseProdCondition(self):
        cond = self.prodInfo.getProCondition()
        if cond:
            cond = cond.split(',')
            #print(cond)
            for c in cond:
                c = c.strip()
                if c == 'fbg':
                    if not self.testModus:
                        if not self.testChannelForPeaks(1):
                            self.printError(0)
                            return 0
                elif c == 'ids':
                    print('Test for IDs')
                    if not self.testModus:
                        if self.prodInfo.getProdPlanNum() == 0:
                            text = self.proID.text()
                            if not text:
                                self.printError(1)
                                self.proID.setFocus()
                                return 0
                            if not self.prodInfo.testID(0,text):
                                self.printError(9)
                                self.proID.clear()
                                self.proID.setFocus()
                                return 0
                                
                            text = self.fbgID.text()
                            if not text:
                                self.printError(2)
                                self.fbgID.setFocus()
                                return 0
                            if not self.prodInfo.testID(1,text):
                                self.printError(10)
                                self.fbgID.clear()
                                self.fbgID.setFocus()
                                return 0
                                
                            text = self.sensorID.text()
                            if not text:
                                self.printError(3)
                                self.sensorID.setFocus()
                                return 0
                            if not self.prodInfo.testID(2,text):
                                self.printError(11)
                                self.sensorID.clear()
                                self.sensorID.setFocus()
                                return 0
                        else:
                            if not self.proID.text():
                                self.printError(7)
                                return 0
                        
                elif c == 'Zielwert':
                    tol = self.prodInfo.getTolaranz()
                    diff = float(self.chan1IsLabel.text())-float(self.chan1SollLabel.text())
                    msgWl = unicode("""Peakwellenlänge entspricht nicht der Vorgabe!
                                    \n\n Wollen Sie wirklich fortfahren""", 'utf-8')
                    msgRl = unicode("""Rückstreuung entspricht nicht der Vorgabe!
                                    \n\n Wollen Sie wirklich fortfahren""", 'utf-8')
                    if self.prodInfo.getProdPlanNum() == 2:
                        isTol = diff <tol
                        msg = msgRl
                    else:
                        isTol = abs(diff) < tol
                        msg = msgWl
                    if not isTol:
                        reply = QtGui.QMessageBox.question(self, 'Warnung', msg, 
                                    QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)

                        if reply == QtGui.QMessageBox.Yes:
                            return 1
                        else:
                            return 0
        return 1
     
    def parseProdMeas(self):
        if not self.testModus:
            meas = self.prodInfo.getProMeas()
            x = self.__scaledWavelength
            y = self.dbmData
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
                    if m == 'ids':
                        print('Write ids')
                        if not self.testModus:
                            if not self.getIDs():
                                self.printError(4)
                                return 0
                            
                    elif m == 'date':
                        print('Write date')
                        if not self.testModus:
                            self.prodInfo.setDate()
                    elif m == 'peak':
                        print('Measure Peak Wavelength')
                        if not self.testModus:
                            peak = self.chan1IsLabel.text()
                            self.prodInfo.setPeakWavelength(peak)
                    elif m == 'spectrum':
                        print('Measure Spectrum')
                        if not self.testModus:
                            fname = self.saveSpectrum(x,y)
                            self.prodInfo.setSpecFile(fname)
                    elif m == 'fwhm':
                        print('Determine FWHM')
                        if not self.testModus:
                            cenFit = self.peakFit(x,y)
                            fwhm = self.calcFWHM(x,y)
                            self.prodInfo.setFWHM(fwhm)
                    elif m == 'asymm':
                        print('Determine Asymmety Ratio')
                        if not self.testModus:
                            cenCoG = self.centerOfGravity(x,y, peak)
                            asym = self.calculateAsym(cenFit, cenCoG)
                            self.prodInfo.setAsymmetrie(asym)
                    elif m == 'temp':
                        print('Measure Temperature')
                        if not self.testModus:
                            temp = self.tempDisplay.text()
                            self.prodInfo.setTemp(temp)
                    elif m == 'timer':
                        print('Activate heating Timer.')
                        if not self.testModus:
                            if self.heatingTimer.isActive():
                                self.printError(8)
                                self.prodSequenzBack()
                            else:
                                self.activateTimer()
                    elif m == 'cooling':
                        print('Wait for Temprature = 90°C')
                        if not self.testModus:
                            self.activateCooling()
   
#### calculations
   
    def peakFit(self, x, y):
        p0 = [x[np.argmax(y)], 30, .2, -60]
        #y = np.power(10,y/10)
        popt, pcov = curve_fit(self.gauss, x, y, p0)
        #self.plotW.plotS(x,self.gauss(x, popt[0],popt[1],popt[2],popt[3]))
        #print(popt)
        return popt[0]
        
    def calcFWHM(self, x,y):
        hmdB = np.max(y) - 3
        maxX = x[np.argmax(y)]
        hmX = x[np.where((y> hmdB-.5) & (y< hmdB+.5) )[0]]
        hm1 = np.mean(hmX[np.where(hmX < maxX)[0]])
        hm2 = np.mean(hmX[np.where(hmX > maxX)[0]])
        fwhm = abs(hm2-hm1)
        print('FWHM: %s'% fwhm)
        return fwhm
   
    def centerOfGravity(self, x, y, peak=None):
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
    
    def calcReturnloss(self):
        x = self.__scaledWavelength
        y = self.dbmData
        maxX = x[np.argmax(y)]
        xmin = float(maxX)-float(self.__SpecWinRL)
        xmax = float(maxX)+float(self.__SpecWinRL)
        pos = np.where((x<=xmin)|(x>=xmax))[0]
        return np.mean(y[pos])
                  
    def gauss(self,x, center, amp, sig, off):
        up = x - center
        up2 = up*up
        down = 2*sig*sig
        frac = up2/down * -1
        _exp = np.exp(frac)
        
        return amp*_exp + off
            
    def printError(self, errorCode):
        errorHeader = ['Kein FBG gefunden',     #0
                       'Keine Produktions ID',  #1
                       'Keine Faser ID',          #2
                       'Keine Sensor ID',       #3
                       'Schreibfehler',         #4
                       'Kein Spektrometer',     #5
                       'Kein Thermometer',      #6
                       'Kein Sensor geladen',    #7
                       'Timer aktiv',           #8
                       'Produktions ID bereits vorhanden',  #9
                       'Faser ID bereits vorhanden',        #10
                       'Sensor ID bereits vorhanden']       #11
                       
        errorMessage = [unicode('Konnte keinen Peak detektieren. Bitte überprüfen Sie die angeschlossene Faser', 'utf-8'),
                        unicode('Bitte geben Sie eine Produktions-Identifikationsnummer ein.', 'utf-8'),
                        unicode('Bitte geben Sie eine Faser-Identifikationsnummer ein.', 'utf-8'),
                        unicode('Bitte geben Sie eine Sensor-Identifikationsnummer ein.', 'utf-8'),
                        unicode('Konnte Identifikationsnummern nicht in Tabelle schreiben.', 'utf-8'),
                        unicode('Bitte überprüfen Sie ob das Spektrometer angeschaltet bzw. angeschlossen ist.', 'utf-8'),
                        unicode('Bitte überprüfen Sie ob das Thermometer angeschaltet bzw. angeschlossen ist.', 'utf-8'),
                        unicode('Bitte SensorID laden.','utf-8'),
                        unicode('Bitte warten bis die aktuelle Heizperiode beendet ist.','utf-8'),
                        unicode('Die gewählte Produktions ID ist bereits vorhanden.\nBitte geben Sie eine neue ID ein.','utf-8'),
                        unicode('Die gewählte Faser ID ist bereits vorhanden.\nBitte geben Sie eine neue ID ein.','utf-8'),
                        unicode('Die gewählte Sensor ID ist bereits vorhanden.\nBitte geben Sie eine neue ID ein.','utf-8')]
        
        QtGui.QMessageBox.critical(self,errorHeader[errorCode],errorMessage[errorCode])
        

        
        