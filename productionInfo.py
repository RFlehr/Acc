# -*- coding: utf-8 -*-
"""
Created on Wed Feb 10 06:38:58 2016

ToDo:
Doku
- test for last entry
- write data in table

Anweisung:
- zu messende bzw berechnende Größen übergeben bzw anfordern
- IDs
@author: Roman
"""

from PyQt4 import QtGui, QtCore
from openpyxl import load_workbook
from time import strftime
import numpy as np
#print(strftime("%d.%m.%Y"))

class ProductionInfo(QtGui.QWidget):
    emitSoll = QtCore.pyqtSignal(str)
    emitTol = QtCore.pyqtSignal(str)
    emitProdIds = QtCore.pyqtSignal(str, str)
    
    emitGetIDs = QtCore.pyqtSignal()
    emitTestFbg = QtCore.pyqtSignal(int) # int - channel number
    def __init__(self, *args):
        QtGui.QWidget.__init__(self, *args)
        
        self.setMaximumHeight(500)
        self.excelPlan = '..\..\Arbeitsplan_fos4Acc_allV0.4.xlsx'
        self.excel = '..\..\FBGAcc_ProdutionsLog.xlsx'
        
        self.proStepNb = []
        self.proShort = []
        self.proDiscription = []
        self.sollGreen = []
        self.sollArray = []
        self.proMeas = []
        self.proCond = []
        self.__log = None #Excel worksheet for data storage
        self.__logRow = 5 #start row, will set to actual row
        self.__proId = ''
        
        self.__step = 0
        
        self.info = QtGui.QTextEdit()
        self.info.setReadOnly(True)
        self.info.setFontPointSize(20)
        self.info.setAlignment(QtCore.Qt.AlignHCenter)
        _str = unicode('\tDrücken Sie START\n um die Sensorfertigung zu beginnen', 'utf-8')
        self.info.setText(_str)
        self.info.setAlignment(QtCore.Qt.AlignLeft)
        
        hl = QtGui.QHBoxLayout(self)
        hl.addWidget(self.info)
        self.buttons = Buttons()
        hl.addWidget(self.buttons)
        
        #self.buttons.startButton.clicked.connect(self.prodSequenzClicked)
    
    def generateIDs(self):
        id = self.__proId.split('-')
        num = int(id[-1])+1
        proID = str(id[0])+str('-')+str(num).zfill(4)
        sensorID = self.__log['C'+str(self.__logRow-1)].value
        id = sensorID
        num = int(id)+1
        sensorID = str(num).zfill(4)
        self.emitProdIds.emit(proID, sensorID)
        
    def getProCondition(self):
        return self.proCond[self.__step]   
        
    def getProMeas(self):
        return self.proMeas[self.__step]
    
    def getProStep(self):
        return self.__step
        
    def getTolaranz(self):
        return self.sollGreen[self.__step]
        
    def loadProductionTable(self, _file = None):
        print('Load productiontable')
        self.proStepNb = []
        self.proShort = []
        self.proDiscription = []
        self.sollGreen = []
        self.sollArray = []
        self.proMeas = []
        self.proCond = []
        wb = load_workbook(filename=self.excelPlan)
        
        ws = wb['acc_Plan']
        content = True
        row = 2
        while content:
            cell = ws['C'+str(row)].value
            #print cell
            if cell: 
                content = True
            else:
                content = False
                break
            self.proStepNb.append(cell)
            cell = ws['D'+str(row)].value
            self.proShort.append(self.testCell(cell))
            cell = ws['F'+str(row)].value
            self.proDiscription.append(self.testCell(cell))
            cell = ws['G'+str(row)].value
            self.sollArray.append(self.testCellNum(cell))
            cell = ws['H'+str(row)].value
            self.sollGreen.append(self.testCellNum(cell))
            cell = ws['I'+str(row)].value
            self.proMeas.append(self.testCell(cell))
            cell = ws['J'+str(row)].value
            self.proCond.append(self.testCell(cell))
            
            row += 1
        
        self.wb = load_workbook(filename=self.excel)
        self.__log = self.wb['acc_Produktion']
                
        content = True
        while content:
            cell = self.__log['A'+str(self.__logRow)].value
            #print('Zeile ', str(self.__logRow),': ', cell)
            if cell:
                content = True
                self.__proId = cell
                self.__logRow += 1
            else:
                content = False
            
           
        self.generateIDs()
        
    def setIDs(self, pro, fbg, sensor):
        self.__log['A'+str(self.__logRow)].value = str(pro)
        self.__log['B'+str(self.__logRow)].value = str(fbg)
        self.__log['C'+str(self.__logRow)].value = str(sensor)
        self.__log['D'+str(self.__logRow)].value = strftime("%d.%m.%Y")
        self.wb.save(self.excel)
        
        return 1
        
    def setPeakWavelength(self, wavelength):
        if self.proStepNb[self.__step] == 3:
            col = 'E'
        elif  self.proStepNb[self.__step] == 6:
            col = 'J'
        elif  self.proStepNb[self.__step] == 8:
            col = 'L'
        elif self.proStepNb[self.__step] == 9:
            col = 'N'
            
        self.__log[col+str(self.__logRow)].value = float(wavelength)
        self.wb.save(self.excel)
            
    def setSpecFile(self, fname):
        if self.proStepNb[self.__step] == 3:
            col = 'G'
            
        self.__log[col+str(self.__logRow)].value = str(fname)
        self.wb.save(self.excel)
    
    def setTemp(self, temp):
        if self.proStepNb[self.__step] == 3:
            col = 'F'
        elif self.proStepNb[self.__step] == 6:
            col = 'K'
        elif self.proStepNb[self.__step] == 8:
            col = 'M'
        elif self.proStepNb[self.__step] == 9:
            col = 'Q'
        temp = temp.split(' ')
        self.__log[col+str(self.__logRow)].value = float(temp[0])
        self.wb.save(self.excel)
    
    def setFWHM(self, fwhm):
        if self.proStepNb[self.__step] == 3:
            col = 'H'
        
        self.__log[col+str(self.__logRow)].value = float(fwhm)
        self.wb.save(self.excel)
    
    def setAsymmetrie(self,asym):
        if self.proStepNb[self.__step] == 3:
            col = 'I'
             
        self.__log[col+str(self.__logRow)].value = float(asym)
        self.wb.save(self.excel)
            
    def testCell(self,cell): 
        if cell:
             cell = unicode(cell)
        else:
             cell = unicode('')
        return cell
        
    def testCellNum(self,cell): 
        if cell:
             return cell
        else:
             cell = 0.
        return cell

    def makeProTxt(self, num=0):
        step = str(self.proStepNb[num]) + '/'+str(self.proStepNb[-2])+': ' + self.proShort[num]
        discription = self.proDiscription[num]
        goal = 'Zielwert: '
        if self.sollArray[num]:
            goal = goal + str("{0:.3f}".format(self.sollArray[num])) + u' \u00B1 ' + str("{0:.3f}".format(self.sollGreen[num]))
            self.emitSoll.emit(str("{0:.3f}".format(self.sollArray[num])))
        else:
            goal = goal + '---'
            self.emitSoll.emit('----.---')
        
        self.info.clear()
        self.info.setFontUnderline(True)
        self.info.setFontPointSize(12)
        self.info.append(step)
        self.info.setFontUnderline(False)
        self.info.setFontPointSize(11)
        self.info.append('')
        self.info.append(goal)
        self.info.append('')
        
        self.info.append(discription)
        
    def nextProductionStep(self):
        self.__step += 1
        print('Step: ', self.__step)
        if self.__step < self.proStepNb[-1]:
            self.makeProTxt(self.__step)
            #self.chan1SollLabel.setText()
        if self.__step > 0:
            self.buttons.backButton.setEnabled(True)
        
    def startProduction(self):
        self.loadProductionTable()
        
        self.__step = 0
        self.makeProTxt(self.__step)
        self.buttons.startButton.setText('Weiter')
        self.buttons.stopButton.setEnabled(True)
        self.buttons.backButton.setEnabled(False)
        
        
class Buttons(QtGui.QWidget):
    def __init__(self,*args):
        QtGui.QWidget.__init__(self,*args)
        
        style = "font-size: 20px; font-weight: bold"
        self.startButton = QtGui.QPushButton(text='Start')
        self.startButton.setStyleSheet(style)
        self.backButton = QtGui.QPushButton(text=unicode('Zurück', 'utf-8'))
        self.backButton.setStyleSheet(style)
        self.backButton.setEnabled(False)
        self.stopButton = QtGui.QPushButton(text='Abbruch')
        self.stopButton.setStyleSheet(style)
        self.stopButton.setEnabled(False)
        
        bl = QtGui.QVBoxLayout()
        bl.addWidget(self.startButton)
        bl.addWidget(self.backButton)
        bl.addWidget(self.stopButton)
        self.setLayout(bl)
        
