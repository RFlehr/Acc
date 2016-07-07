# -*- coding: utf-8 -*-
"""
Created on Thu Mar 03 12:19:37 2016

@author: Flehr
"""

from pyqtgraph.Qt import QtGui, QtCore
import os

pm = u'\u00B1'

class OptionDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        
        #production
        self.__vGrob = 1555.0
        self.__vGTol = 0.3
        self.__vFein = 1553.0
        self.__vFTol = 0.1
        self.__hZeit = 480  
        self.__hDet = .2  ##heating detection
        self.__finalTemp = 90.
        self.__wavelengthSi = 1550.3
        self.__deltaSi = 0.1
        self.__returnLossMin = -50 #dBm
        self.__returnLoss = -55 #dBm
        self.__windowRL = 2 # nm
        
        
        #files
        self.__paths = ['','','']
        self.__pathLabels = ['Produktionsplan', 'Produktionsdokumentation', 
                  'Spektrenordner']

         #plot
        self.__maxBuffer = 5000
        self.__showTrace = True
        self.__tracePoints = 500
        self.__showSpec = True
        self.__minWl = 1540.
        self.__maxWl = 1570.

        self.loadSettings()
                
        self.setWindowTitle('Optionen')
        tab = QtGui.QTabWidget(self)
        
        tab.addTab(self.createProdTab(),'Produktion')
        tab.addTab(self.createPathTab(), 'Dateipfade')
        tab.addTab(self.createPlotTab(), 'Plot')
        
        cancel = QtGui.QPushButton(text='Abbrechen')
        cancel.clicked.connect(self.reject)
        ok = QtGui.QPushButton(text='OK')
        ok.clicked.connect(self._accept)
        
        bl = QtGui.QHBoxLayout()
        bl.addWidget(cancel)
        bl.addWidget(ok)
        
        mvl = QtGui.QVBoxLayout(self)
        mvl.addWidget(tab)
        mvl.addLayout(bl)
        
        self.setLayout(mvl)
    
    def _accept(self):
        self.saveSettings()
        self.accept()
        #self.close()
        
    def createPathTab(self):
        pathW  = QtGui.QWidget()
        gl = QtGui.QGridLayout()
        pathW.setLayout(gl)
        
        self.lEdits = []
        self.pathButtons = []
        
        for i, label in enumerate(self.__pathLabels):
            l = QtGui.QLabel(text=label+':')
            e = QtGui.QLineEdit()
            e.setText(self.__paths[i])
            self.lEdits.append(e)
            b = QtGui.QPushButton(text= unicode('Öffnen', 'utf-8'))
            b.clicked.connect(self.openFile)
            self.pathButtons.append(b)
            gl.addWidget(l,2*i+0,0)      
            gl.addWidget(e,2*i+1,0)
            gl.addWidget(b,2*i+1,2)
       
        return pathW
        
    def createPlotTab(self):
        plotW  = QtGui.QWidget()
        gl = QtGui.QGridLayout()
        plotW.setLayout(gl)
        
        line = 0        
        ##Trace
        trL = QtGui.QLabel(text='Trace:')
        gl.addWidget(trL,line,0)
        line+=1
        
        trSTL = QtGui.QLabel(text='Zeige Trace:')
        chST = QtGui.QCheckBox()
        chST.setChecked(self.__showTrace)
        chST.stateChanged.connect(self.setShowTrace)
        gl.addWidget(trSTL,line,0)
        gl.addWidget(chST,line,2)   
        line+=1
        
        
        bufferL = QtGui.QLabel(text=unicode('Größe Buffer:', 'utf-8'))
        spB = QtGui.QSpinBox()
        spB.setAlignment(QtCore.Qt.AlignRight)
        spB.setRange(100,10000)
        spB.setValue(self.__maxBuffer)  
        spB.valueChanged.connect(self.setBuffer)
        gl.addWidget(bufferL,line,0)
        gl.addWidget(spB,line,2)
        line+=1
        
        trPL = QtGui.QLabel(text='Anzahl Punkte:')
        spTr = QtGui.QSpinBox()
        spTr.setAlignment(QtCore.Qt.AlignRight)
        spTr.setRange(100,self.__maxBuffer)
        spTr.setValue(self.__tracePoints)
        spTr.valueChanged.connect(self.setTracePoints)
        gl.addWidget(trPL,line,0)
        gl.addWidget(spTr,line,2)
        line+=1
        
        ##Spectrum
        SpL = QtGui.QLabel(text='Spektrum:')
        gl.addWidget(SpL,line,0)
        line+=1
        
        trSSL = QtGui.QLabel(text='Zeige Spektrum:')
        chSS = QtGui.QCheckBox()
        chSS.setChecked(self.__showSpec)
        chSS.stateChanged.connect(self.setShowSpec)
        gl.addWidget(trSSL,line,0)
        gl.addWidget(chSS,line,2)   
        line+=1
        
        minWlL  = QtGui.QLabel(text=unicode('Wellenlänge min', 'utf-8'))
        self.minWlSpin = QtGui.QDoubleSpinBox()
        self.minWlSpin.setAlignment(QtCore.Qt.AlignRight)
        self.minWlSpin.setDecimals(3)
        self.minWlSpin.setSuffix(' nm')
        self.minWlSpin.setRange(1460.0,1615.0)
        self.minWlSpin.setValue(self.__minWl)
        self.minWlSpin.valueChanged.connect(self.setWlScale)
        line+=1
        gl.addWidget(minWlL,line,0)
        gl.addWidget(self.minWlSpin,line,2)  
        
        minWlL  = QtGui.QLabel(text=unicode('Wellenlänge max', 'utf-8'))        
        self.maxWlSpin = QtGui.QDoubleSpinBox()
        self.maxWlSpin.setAlignment(QtCore.Qt.AlignRight)
        self.maxWlSpin.setDecimals(3)
        self.maxWlSpin.setSuffix(' nm')
        self.maxWlSpin.setRange(1465.0, 1620.0)
        self.maxWlSpin.setValue(self.__maxWl)
        self.maxWlSpin.valueChanged.connect(self.setWlScale)
        line+=1
        gl.addWidget(minWlL,line,0)
        gl.addWidget(self.maxWlSpin,line,2)  
        
        return plotW
        
        
    def createProdTab(self):
        gl = QtGui.QGridLayout()
        
        vgl = QtGui.QLabel(text='Vorspannung (grob) [nm]')
        gl.addWidget(vgl,0,0)
        
        spVg = QtGui.QDoubleSpinBox()
        spVg.setAlignment(QtCore.Qt.AlignRight)
        spVg.setRange(1545.,1560.)
        spVg.setValue(self.__vGrob)
        spVg.valueChanged.connect(self.setVorspannGrob)
        gl.addWidget(spVg,0,1)
        
        spGTol = QtGui.QDoubleSpinBox()
        spGTol.setAlignment(QtCore.Qt.AlignRight)
        spGTol.setRange(0.05,.5)
        spGTol.setValue(self.__vGTol)
        spGTol.valueChanged.connect(self.setVorGrobTol)
        gl.addWidget(QtGui.QLabel(text=pm),0,2)
        gl.addWidget(spGTol,0,3)
        
        
        vl = QtGui.QLabel(text='Vorspannung [nm]')
        gl.addWidget(vl, 1,0)
        
        spV = QtGui.QDoubleSpinBox()
        spV.setAlignment(QtCore.Qt.AlignRight)
        spV.setRange(1545.,1560.)
        spV.setValue(self.__vFein)
        spV.valueChanged.connect(self.setVorspannFein)
        gl.addWidget(spV,1,1)
        
        spFTol = QtGui.QDoubleSpinBox()
        spFTol.setAlignment(QtCore.Qt.AlignRight)
        spFTol.setRange(0.05,.5)
        spFTol.setValue(self.__vFTol)
        spFTol.valueChanged.connect(self.setVorFeinTol)
        gl.addWidget(QtGui.QLabel(text=pm),1,2)
        gl.addWidget(spFTol,1,3)
        
        
        hl = QtGui.QLabel(text='Heizdauer [min]')
        gl.addWidget(hl,2,0)
        
        spHt = QtGui.QSpinBox()
        spHt.setValue(int(self.__hZeit/60))
        spHt.setAlignment(QtCore.Qt.AlignRight)
        spHt.setRange(3,15)
        spHt.valueChanged.connect(self.setHeizzeit)
        gl.addWidget(spHt,2,1)
        
        
        hdl = QtGui.QLabel(text=u'Erkennung Heizen [\u0394nm]')
        gl.addWidget(hdl,3,0)
        
        spHD = QtGui.QDoubleSpinBox()
        spHD.setValue(self.__hDet)
        spHD.setAlignment(QtCore.Qt.AlignRight)
        spHD.setRange(.1,1.)
        spHD.setSingleStep(.05)
        spHD.setDecimals(2)
        spHD.valueChanged.connect(self.setHeizDet)
        gl.addWidget(spHD,3,1)
        
        
        templ = QtGui.QLabel(text=u'Temperatur (Messung) \u00b0C')
        gl.addWidget(templ, 4,0)
        
        spTemp = QtGui.QDoubleSpinBox()
        spTemp.setValue(self.__finalTemp)
        spTemp.setAlignment(QtCore.Qt.AlignRight)
        spTemp.setRange(15,160)
        spTemp.setDecimals(1)
        spTemp.valueChanged.connect(self.setFinalTemp)
        gl.addWidget(spTemp,4,1)
        
            
        siL = QtGui.QLabel(text=u'\u03BB Silikonverklebung [nm]')
        gl.addWidget(siL,5,0)
        spSi = QtGui.QDoubleSpinBox()
        spSi.setAlignment(QtCore.Qt.AlignRight)
        spSi.setRange(1545.,1560.)
        spSi.setValue(self.__wavelengthSi)
        spSi.valueChanged.connect(self.setSiWl)
        gl.addWidget(spSi,5,1)
        
        spDSi = QtGui.QDoubleSpinBox()
        spDSi.setAlignment(QtCore.Qt.AlignRight)
        spDSi.setRange(0.05,1.)
        spDSi.setValue(self.__deltaSi)
        spDSi.valueChanged.connect(self.setDSiWl)
        gl.addWidget(QtGui.QLabel(text=pm),5,2)
        gl.addWidget(spDSi,5,3)
        
        rlml = QtGui.QLabel(text='Return Loss Min [dBm]')
        gl.addWidget(rlml,6,0)
        
        spRlM = QtGui.QSpinBox()
        spRlM.setAlignment(QtCore.Qt.AlignRight)
        spRlM.setRange(-60,-50)
        spRlM.setValue(self.__returnLossMin)
        spRlM.valueChanged.connect(self.setReturnLossMin)
        gl.addWidget(spRlM,6,1)
        
        rll = QtGui.QLabel(text='Return Loss [dBm]')
        gl.addWidget(rll,7,0)
        
        spRl = QtGui.QSpinBox()
        spRl.setAlignment(QtCore.Qt.AlignRight)
        spRl.setRange(-60,-50)
        spRl.setValue(self.__returnLoss)
        spRl.valueChanged.connect(self.setReturnLoss)
        gl.addWidget(spRl,7,1)
                
        
        wrll = QtGui.QLabel(text='Window RL [nm]')
        gl.addWidget(wrll, 8,0)
        
        spWRL = QtGui.QDoubleSpinBox()
        spWRL.setRange(.5,5)
        spWRL.setValue(self.__windowRL)
        spWRL.setAlignment(QtCore.Qt.AlignRight)
        spWRL.setDecimals(1)
        spWRL.valueChanged.connect(self.setWindowRL)
        gl.addWidget(spWRL,8,1)
        
        
        proW = QtGui.QWidget()
        proW.setLayout(gl)
        
        return proW
        
      
        
    def openFile(self):
        bIndex = self.pathButtons.index(self.sender())
        if bIndex < 2:
            _str = 'Bitte ' + self.__pathLabels[bIndex] + unicode(' Datei auswählen','utf8')
            path = QtGui.QFileDialog.getOpenFileName(self,caption=_str)
        else:
            path = QtGui.QFileDialog.getExistingDirectory(self, caption=unicode('Bitte den Ordner auswählen','utf8'))
        if path:
            self.lEdits[bIndex].setText(os.path.normpath(path))
            self.__paths[bIndex] = os.path.normpath(path)
                
    def loadSettings(self):
        settings = QtCore.QSettings('test.ini',QtCore.QSettings.IniFormat)
        settings.beginGroup('Produktion')
        self.__vGrob = float(settings.value('VorspannGrob', self.__vGrob))
        self.__vGTol = float(settings.value('VorGrobTol', self.__vGTol))
        self.__vFein = float(settings.value('VorspannFein', self.__vFein))
        self.__vFTol = float(settings.value('VorFeinTol', self.__vFTol))
        self.__hZeit = int(settings.value('Heizdauer',self.__hZeit))
        self.__hDet = float(settings.value('HeizDetekt', self.__hDet))
        self.__finalTemp = float(settings.value('Endtemp', self.__finalTemp))
        self.__wavelengthSi = float(settings.value('SiVerklebung', self.__wavelengthSi))
        self.__deltaSi = float(settings.value('DeltaSiVerklebung', self.__deltaSi))
        self.__returnLossMin = int(settings.value('returnLossMin', self.__returnLossMin))
        self.__returnLoss = int(settings.value('returnLoss', self.__returnLoss))
        self.__windowRL = float(settings.value('windowRL', self.__windowRL))
        settings.endGroup()
        
        settings.beginGroup('Dateipfade')
        for i in range(3):
            s = settings.value(self.__pathLabels[i])
            self.__paths[i] = s
        settings.endGroup()
        
        settings.beginGroup('Plot')
        self.__maxBuffer = int(settings.value('Buffer', self.__maxBuffer))
        self.__tracePoints = int(settings.value('TracePunkte', self.__tracePoints))
        self.__showTrace = int(settings.value('ShowTrace', self.__showTrace))
        self.__showSpec = int(settings.value('ShowSpec', self.__showSpec))
        self.__minWl = float(settings.value('MinWl', self.__minWl))
        self.__maxWl = float(settings.value('MaxWl', self.__maxWl))
        settings.endGroup()
        
    def saveSettings(self):
        settings = QtCore.QSettings('test.ini',QtCore.QSettings.IniFormat)
        settings.beginGroup('Produktion')
        settings.setValue('VorspannGrob', self.__vGrob)
        settings.setValue('VorGrobTol', self.__vGTol)
        settings.setValue('VorspannFein', self.__vFein)
        settings.setValue('VorFeinTol', self.__vFTol)
        settings.setValue('Heizdauer',self.__hZeit)
        settings.setValue('HeizDetekt', self.__hDet)
        settings.setValue('Endtemp', self.__finalTemp)
        settings.setValue('SiVerklebung', self.__wavelengthSi)
        settings.setValue('DeltaSiVerklebung', self.__deltaSi)
        settings.setValue('returnLossMin', self.__returnLossMin)
        settings.setValue('returnLoss', self.__returnLoss)
        settings.setValue('windowRL', self.__windowRL)
        settings.endGroup()
        
        settings.beginGroup('Dateipfade')
        for i in range(3):
            settings.setValue(self.__pathLabels[i],self.lEdits[i].text())
        settings.endGroup()
        
        settings.beginGroup('Plot')
        settings.setValue('Buffer', self.__maxBuffer)
        settings.setValue('TracePunkte', self.__tracePoints)
        settings.setValue('ShowTrace', self.__showTrace)
        settings.setValue('ShowSpec', self.__showSpec)
        settings.setValue('MinWl', self.__minWl)
        settings.setValue('MaxWl', self.__maxWl)
        settings.endGroup()
        
    def setBuffer(self, val):
        self.__maxBuffer = val
        
    def setShowTrace(self, val):
        self.__showTrace = val
        
    def setShowSpec(self, val):
        self.__showSpec = val
        
    def setTracePoints(self, val):
        self.__tracePoints = val
        
    def setVorspannGrob(self, val):
        self.__vGrob = val
        
    def setVorGrobTol(self, val):
        self.__vGTol = val
    
    def setVorspannFein(self, val):
        self.__vFein = val
        
    def setVorFeinTol(self, val):
        self.__vFTol = val
        
    def setHeizzeit(self, time):
        self.__hZeit = time*60
        
    def setHeizDet(self, val):
        self.__hDet = val
        
    def setFinalTemp(self, val):
        self.__finalTemp = val
        
    def setSiWl(self, val):
        self.__wavelengthSi = val
        
    def setDSiWl(self, val):
        self.__deltaSi = val
        
    def setReturnLossMin(self, val):
        self.__returnLossMin = val
        
    def setReturnLoss(self, val):
        self.__returnLoss = val
        
    def setWindowRL(self, val):
        self.__windowRL = val
    
    def setWlScale(self):    
        _min = float(self.minWlSpin.value())
        _max = float(self.maxWlSpin.value())
        if _min > _max:
            _min = _max-1
        if _max < _min:
            _max = _min+1
        self.__minWl = _min
        self.__maxWl = _max
       
        
#==============================================================================
# if __name__ == '__main__':
#  app = QtGui.QApplication(sys.argv)
#  dia = OptionDialog()
#  dia.show()
#  #if dia.exec_():
#  #    print('ok')
#  #dia.close()
#  sys.exit(app.exec_())
#==============================================================================
