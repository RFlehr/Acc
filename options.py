# -*- coding: utf-8 -*-
"""
Created on Thu Mar 03 12:19:37 2016

@author: Flehr
"""

from pyqtgraph.Qt import QtGui, QtCore
import sys,ntpath

class OptionDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        
        self.__vGrob = 1555.0
        self.__vGTol = 0.3
        self.__vFein = 1553.0
        self.__vFTol = 0.1
        self.__hZeit = 480  
        self.__hDet = .2  ##heating detection
        self.__finalTemp = 90.
        
        self.__paths = ['','','']
        self.__pathLabels = ['Produktionsplan', 'Produktionsdokumentation', 
                  'Spektrenordner']
                  
        self.loadSettings()
                
        self.setWindowTitle('Optionen')
        tab = QtGui.QTabWidget(self)
        
        tab.addTab(self.createProdTab(),'Produktion')
        tab.addTab(self.createPathTab(), 'Dateipfade')
        
        cancel = QtGui.QPushButton(text='Abbrechen')
        cancel.clicked.connect(self.reject)
        ok = QtGui.QPushButton(text='OK')
        ok.clicked.connect(self.accept)
        
        bl = QtGui.QHBoxLayout()
        bl.addWidget(cancel)
        bl.addWidget(ok)
        
        mvl = QtGui.QVBoxLayout(self)
        mvl.addWidget(tab)
        mvl.addLayout(bl)
        
        self.setLayout(mvl)
    
    def accept(self):
        self.saveSettings()
        self.close()
        
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
        
    def createProdTab(self):
        pml = QtGui.QLabel(text='+/-')
        gl = QtGui.QGridLayout()
        vgl = QtGui.QLabel(text='Vorspannung (grob) [nm]')
        spVg = QtGui.QDoubleSpinBox()
        spVg.setAlignment(QtCore.Qt.AlignRight)
        spVg.setRange(1545.,1560.)
        spVg.setValue(self.__vGrob)
        spVg.valueChanged.connect(self.setVorspannGrob)
        spGTol = QtGui.QDoubleSpinBox()
        spGTol.setAlignment(QtCore.Qt.AlignRight)
        spGTol.setRange(0.05,.5)
        spGTol.setValue(self.__vGTol)
        spGTol.valueChanged.connect(self.setVorGrobTol)
        vl = QtGui.QLabel(text='Vorspannung [nm]')
        spV = QtGui.QDoubleSpinBox()
        spV.setAlignment(QtCore.Qt.AlignRight)
        spV.setRange(1545.,1560.)
        spV.setValue(self.__vFein)
        spV.valueChanged.connect(self.setVorspannFein)
        spFTol = QtGui.QDoubleSpinBox()
        spFTol.setAlignment(QtCore.Qt.AlignRight)
        spFTol.setRange(0.05,.5)
        spFTol.setValue(self.__vFTol)
        spFTol.valueChanged.connect(self.setVorFeinTol)
        hl = QtGui.QLabel(text='Heizdauer [min]')
        spHt = QtGui.QSpinBox()
        spHt.setValue(int(self.__hZeit/60))
        spHt.setAlignment(QtCore.Qt.AlignRight)
        spHt.setRange(3,15)
        spHt.valueChanged.connect(self.setHeizzeit)
        hdl = QtGui.QLabel(text=u'Erkennung Heizen [\u0394nm]')
        spHD = QtGui.QDoubleSpinBox()
        spHD.setValue(self.__hDet)
        spHD.setAlignment(QtCore.Qt.AlignRight)
        spHD.setRange(.1,1.)
        spHD.setSingleStep(.05)
        spHD.setDecimals(2)
        spHD.valueChanged.connect(self.setHeizDet)
        templ = QtGui.QLabel(text=u'Temperatur (Messung) \u00b0C')
        spTemp = QtGui.QDoubleSpinBox()
        spTemp.setValue(self.__finalTemp)
        spTemp.setAlignment(QtCore.Qt.AlignRight)
        spTemp.setRange(15,160)
        spTemp.setDecimals(1)
        spTemp.valueChanged.connect(self.setFinalTemp)
        
        
        gl.addWidget(vgl,0,0)
        gl.addWidget(spVg,0,1)
        gl.addWidget(pml,0,2)
        gl.addWidget(spGTol,0,3)
        gl.addWidget(vl, 1,0)
        gl.addWidget(spV,1,1)
        gl.addWidget(pml,1,2)
        gl.addWidget(spFTol,1,3)
        gl.addWidget(hl,2,0)
        gl.addWidget(spHt,2,1)
        gl.addWidget(hdl,3,0)
        gl.addWidget(spHD,3,1)
        gl.addWidget(templ, 4,0)
        gl.addWidget(spTemp,4,1)
        
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
            self.lEdits[bIndex].setText(path)
            self.__paths[bIndex] = path
                
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
        settings.endGroup()
        settings.beginGroup('Dateipfade')
        for i in range(3):
            s = settings.value(self.__pathLabels[i])
            self.__paths[i] = s
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
        settings.endGroup()
        
        settings.beginGroup('Dateipfade')
        for i in range(3):
            settings.setValue(self.__pathLabels[i],self.lEdits[i].text())
        settings.endGroup()
        
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
        
    def transferValues(self):
        return self.__vGrob, self.__vFein, self.__hZeit, self.__hDet, self.__finalTemp
        
        
if __name__ == '__main__':
 app = QtGui.QApplication(sys.argv)
 dia = OptionDialog()
 dia.show()
 #if dia.exec_():
 #    print('ok')
 #dia.close()
 sys.exit(app.exec_())