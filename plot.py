# -*- coding: utf-8 -*-
"""
Created on Tue Feb 02 16:50:13 2016

@author: Roman
"""

import pyqtgraph as pg
import numpy as np
from pyqtgraph.Qt import QtGui, QtCore
from scipy import stats

class Plot(QtGui.QSplitter):
    returnSlope = QtCore.pyqtSignal(float)
    def __init__(self, parent=None):
        QtGui.QSplitter.__init__(self, parent)
        
        self.setOrientation(QtCore.Qt.Vertical)
        
        self.__Spectrum = None
        self.__sCurves = []
        self.__Trace = None
        self.__pCurves = []
        self.__regPoints = 30
        self.__showReg = True
        self.__tracePoints = 1000
        self.lineWidth = 0
        self.specColor = QtGui.QColor(0,0,255)
        self.regColor = QtGui.QColor(255,0,0)
        self.backColor = QtGui.QColor(255,255,255)
        
        
        self.__plotTrace = self.createPlotTrace()
        self.__plotSpec = self.createPlotSpec()
        
        self.addWidget(self.__plotTrace)
        self.addWidget(self.__plotSpec)
        
    def calculateSlope(self, x, y):
        nop = self.__regPoints
        if nop > len(x):
            _x=x
            _y=y
        else:
            _x = x[-nop:]
            _y = y[-nop:]
        slope, intercept, r_value, p_value, std_err = stats.linregress(_x,_y)
        self.returnSlope.emit(slope*1000)
        
         
    def createPlotSpec(self):
        self.__sCurves = []
        p = pg.PlotWidget(title='Spectrum')
        p.setLabel('bottom','Wavelength [nm]')
        p.setLabel('left','Amplitude [dBm]')
        self.__Spectrum = pg.PlotCurveItem(pen=QtGui.QPen(self.specColor,self.lineWidth))
        p.setBackground(pg.mkColor(self.backColor))
        p.addItem(self.__Spectrum)
        self.__sCurves.append(self.__Spectrum)
        return p    

    def createPlotTrace(self):
        self.__pCurves = []
        p = pg.PlotWidget(title='Peak Wavelength')
        p.setLabel('bottom','Time')
        p.setLabel('left','Wavelength [nm]')
        self.__Trace = pg.PlotCurveItem(pen=QtGui.QPen(self.specColor,self.lineWidth))
        p.setBackground(pg.mkColor(self.backColor))
        
        p.addItem(self.__Trace)
        self.__pCurves.append(self.__Trace)
        return p       

    def getSpektrum(self):
       x,y = self.__Spectrum.getData()
       return x,y
       
       
    def plotS(self, x, y):
        self.__Spectrum.setData(x, y)
        
    def plotT(self, x, y):
        nop = len(x)
        if nop >= self.__tracePoints:
            _x = x[-self.__tracePoints:]
            _y = y[-self.__tracePoints:]
        else:
            _x = x
            _y = y
        time = self.setTimeLabel(_x)
        self.__Trace.setData(time, _y)
        if self.__showReg and nop>1:
            self.calculateSlope(_x,_y)
            
    def setRegPoints(self, points):
        self.__regPoints = points
        
    def setShowPlot(self, plotT = True, plotS = True):
        if plotT:
            self.__plotTrace.show()
        else:
            self.__plotTrace.hide()
        if plotS:
            self.__plotSpec.show()
        else:
            self.__plotSpec.hide()
        
    def setTracePoints(self, points):
        self.__tracePoints = points
        
    def setTimeLabel(self, timearray):
        #time in sec
        label = 's'
        times = timearray
        if len(timearray) < 2:
            return times
        lasttime = times[-1]
        if lasttime <= 180:
            label = 's'
        else:
            label = 'min'
            times = times/60.
        self.__plotTrace.setLabel('bottom','Time [' + label + ']')
        return times
        
    def setShowRegression(self, show=True):
        if self.__showReg:
            if not show:
                self.__plotTrace.removeItem(self.__Regres)
                self.__showReg = False
        else:
            if show:
                self.__plotTrace.addItem(self.__Regres)
                self.__showReg = True
        