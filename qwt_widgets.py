# -*- coding: utf-8 -*-
"""
Created on Mon Feb 08 22:16:19 2016

@author: Roman
"""
from PyQt4 import QtGui, QtCore
from PyQt4.Qwt5 import QwtDial, QwtDialSimpleNeedle

class SlopeMeter(QwtDial):

    def __init__(self, *args):
        QwtDial.__init__(self, *args)
        __size = 140
        self.setFixedSize(__size,__size)
        self.__label = 'pm/s'
        self.setWrapping(False)
        self.setReadOnly(True)
        
        self.__min = -2
        self.__max = 2
        self.__inkr = .5

        self.setOrigin(225.0)
        self.setScaleArc(0.0, 270.0)
        self.setRange(self.__min, self.__max)
        self.setScale(self.__min,self.__max,self.__inkr)
        self.setDirection(QwtDial.CounterClockwise)
        self.scale = 2
        self.scaleDraw().setPenWidth(1)
        self.setLineWidth(2)
        self.setFrameShadow(QwtDial.Sunken)

        needle = QwtDialSimpleNeedle(QwtDialSimpleNeedle.Arrow, True, 
                    QtGui.QColor(255,0,0), QtGui.QColor(255,255,255))
        needle.setWidth(7)
        self.setNeedle(needle)

        self.setScaleOptions(QwtDial.ScaleTicks | QwtDial.ScaleLabel)
        self.setScaleTicks(1, 4, 8)

    def drawScaleContents(self, painter, center, radius):
        d = 2*radius
        d2 = 2*d
        xc = center.x()
        #print(xc)
        yc = center.y()
        painter.setPen(QtGui.QColor(220,220,220))
        painter.setBrush(QtGui.QColor(220,220,220))
        painter.drawPie(0,yc-d,d2,d2, -3600, 7200)
        painter.setPen(QtGui.QColor(220,0,0))
        painter.setBrush(QtGui.QColor(220,0,0))
        painter.drawPie(0,yc-d,d2,d2, -2300, 4600)
        painter.setPen(QtGui.QColor(220,220,0))
        painter.setBrush(QtGui.QColor(220,220,0))
        painter.drawPie(0,yc-d,d2,d2, -1400, 2800)
        painter.setPen(QtGui.QColor(0,220,0))
        painter.setBrush(QtGui.QColor(0,220,0))
        painter.drawPie(0,yc-d,d2,d2, -600, 1200)
        
        rect = QtCore.QRect(0, 0, 2 * radius+30, 2 * radius)
        rect.moveCenter(center)
        painter.setPen(self.palette().color(QtGui.QPalette.Text))
        painter.drawText(rect, QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, self.__label)
        
        
    def setSlope(self, slope):
        self.setValue(slope)

    
    
    