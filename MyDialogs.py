# -*- coding: utf-8 -*-
"""
Created on Thu Feb 18 21:48:10 2016

@author: Roman
"""
from PyQt4 import QtGui

class TimerDialog(QtGui.QProgressDialog):
    def __init__(self, *args):
        QtGui.QProgressDialog.__init__(self, *args)
        
        self.setWindowTitle('Timer')
        font = QtGui.QFont()
        font.setBold(True)
        font.setPointSize(44)
        self.__timeStr = '0:00'        
        self.__timerLabel = QtGui.QLabel(self,text=self.__timeStr)
        self.__timerLabel.setStyleSheet("color: red")
        self.__timerLabel.setFont(font)
        self.__timerLabel.setFrameShape(QtGui.QFrame.StyledPanel)
        self.__timerLabel.setFrameShadow(QtGui.QFrame.Raised)
        
        self.setRange(0,560)
        
        lay = QtGui.QVBoxLayout(self)
        lay.addWidget(self.__timerLabel)
        
    def setTime(self, sec):
        m, s = divmod(sec, 60)
        timeStr="%02d:%02d" % (m, s)
        self.__timerLabel.setText(timeStr)
        
class NewSensorDialog(QtGui.QDialog):
    def __init__(self, ids=None, *args):
        QtGui.QDialog.__init__(self, *args) 
        
        self.index = 0
        self.setWindowTitle('Sensorauswahl')
        self.setMinimumWidth(200)
        self.idCombo = QtGui.QComboBox()
        self.idCombo.addItems(ids)    
        lay = QtGui.QVBoxLayout()
        ok = QtGui.QPushButton(text='OK')
        ok.clicked.connect(self.accept)
        lay.addWidget(self.idCombo)
        lay.addWidget(ok)
        self.setLayout(lay)
        
        self.idCombo.currentIndexChanged.connect(self.setIndex)
        
    def setIndex(self, index):
        self.index = index
        #print(self.index)
            
    def setSensor(self):
        return self.index
        
        
        