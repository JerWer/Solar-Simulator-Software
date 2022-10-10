import sys
import datetime
import time
import os
# import win32com.client
from getmac import get_mac_address as gma
# import socket
from pathlib import Path
# import traceback
# import pandas as pd
import numpy as np
import calendar
from statistics import mean
# from scipy.interpolate import interp1d as interp
import sqlite3
import pickle
import serial
import math
import pyvisa
import socket
#%%######################################################################################################
import matplotlib
# import matplotlib.pyplot as plt
matplotlib.use("Qt5Agg")
#%%######################################################################################################
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5 import QtTest
from PyQt5.QtCore import QThread, pyqtSignal, QSettings
# from PyQt5.QtCore.QElapsedTimer import timer
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QAction, QTableWidgetItem
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
#%%######################################################################################################

version = '1pixel' #'6pixels' , 1pixel
# from PyQt5.uic import loadUiType
if version== '1pixel':
    sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),'GUIfiles'))
    from gui import Ui_MainWindow

from loadingsavingtemplate import LoadParamTemplate, SaveParamTemplate, CreateParamTemplate

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),'KeithleyCode'))
from myKeithleyFunctions import connectToKeithley, prepareVoltage, measureVoltage, prepareCurrent, measureCurrent, openShutter, closeShutter, takeIV, shutdownKeithley,setFrontTerminal,setRearTerminal
from ArduinoComm import ConnectToArduino, Arduino_write_read

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),'Otherfunctions'))
from database_Tables import CreateAllTables
import database_GeneralReading_pyqt as DBreadPack

#%%######################################################################################################
shutteropen=0
RefDiodeChecked=0
Sunintensity=0
STOPMEAS=0
STOPMEASMPP=0
AllDATA={}
lastmeasDATA={}
AlltrackingDATA={}
lastmeastrackingDATA={}
aftermpp=0
ongoingseq=0
latestVmpp=-99
lastJVscansVmpp=[]

def connectPixel(box1, box2, pixelName):
    window.w.ui.textEdit_Keithley.append('Pixel '+pixelName+' connected')
boxCurrent = 'test'
boxVoltage = 'test'
keithleyAddress=['Test']

exedirectory=str(Path(os.path.abspath(__file__)).parent.parent)

loadtempfilepath=''

ArduinoConnected=0
arduino=''
dbchoice=''
Kconnresult=[]

#%%######################################################################################################
class Main(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        global AllDATA, shutteropen, Kconnresult, keithleyAddress
        QtWidgets.QMainWindow.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.textEdit_Keithley.append(QtCore.QDateTime.currentDateTime().toString()+': starting software')
        
        self.keithleyObject=Kconnresult[1]
        self.ui.textEdit_Keithley.append(QtCore.QDateTime.currentDateTime().toString()+': '+Kconnresult[0])

        self.connecttoDB()
        
        finish = QAction("Quit", self)
        finish.triggered.connect(lambda: self.closeEvent(self.keithleyObject))
        
        #shutter initialization, so that software value corresponds to real value
        if keithleyAddress[0]!='Test':
            self.connecttoarduinoPy()
            
            self.opencloseshutter(self.keithleyObject)
            self.opencloseshutter(self.keithleyObject)
        
        self.fig1 = Figure()
        self.JVgraph = self.fig1.add_subplot(111)
        self.JVgraph.set_xlabel('Voltage (V)')
        self.JVgraph.set_ylabel('Current density (mA/cm'+'\xb2'+')')
        self.JVgraph.axhline(y=0, color='k')
        self.JVgraph.axvline(x=0, color='k')
        self.addmpl(self.fig1,self.ui.gridLayout_MPLwidgetJV, self.ui.MPLwidgetJV)
        
        
        self.fig2 = Figure()
        self.MPPTgraph_JV = self.fig2.add_subplot(221)
        self.MPPTgraph_JV.set_xlabel('Voltage (mV)')
        self.MPPTgraph_JV.set_ylabel('Current density (mA/cm'+'\xb2'+')')
        self.MPPTgraph_TV = self.fig2.add_subplot(222)
        self.MPPTgraph_TV.set_xlabel('Time (s)')
        self.MPPTgraph_TV.set_ylabel('Voltage (mV)')
        self.MPPTgraph_TJ = self.fig2.add_subplot(223)
        self.MPPTgraph_TJ.set_xlabel('Time (s)')
        self.MPPTgraph_TJ.set_ylabel('Current density (mA/cm'+'\xb2'+')')
        self.MPPTgraph_TP = self.fig2.add_subplot(224)
        self.MPPTgraph_TP.set_xlabel('Time (s)')
        self.MPPTgraph_TP.set_ylabel('Power (W/m'+'\xb2'+')')
        self.addmpl(self.fig2, self.ui.gridLayout_MPLwidgetMPPT,self.ui.MPLwidgetMPPT)
        
        self.fig3 = Figure()
        self.DIVgraphlin = self.fig3.add_subplot(121)
        self.DIVgraphlin.set_xlabel('Voltage (mV)')
        self.DIVgraphlin.set_ylabel('Current density (mA/cm'+'\xb2'+')')
        self.DIVgraphlogY = self.fig3.add_subplot(122)
        self.DIVgraphlogY.set_yscale('log')
        self.DIVgraphlogY.set_xlabel('Voltage (mV)')
        self.DIVgraphlogY.set_ylabel('Current density (mA/cm'+'\xb2'+')')
        self.addmpl(self.fig3,self.ui.gridLayout_MPLwidgetDIV,self.ui.MPLwidgetDIV)

        self.fig4 = Figure()
        self.DBgraph = self.fig4.add_subplot(111)
        self.DBgraph.set_xlabel('Date/Time')
        self.DBgraph.set_ylabel('X (-)')
        self.addmpl(self.fig4,self.ui.gridLayout_mplDB, self.ui.widget_DB)

        self.fig6 = Figure()
        self.QSSgraphIV = self.fig6.add_subplot(121)
        self.QSSgraphIV.set_xlabel('Voltage (V)')
        self.QSSgraphIV.set_ylabel('Current density (mA/cm'+'\xb2'+')')
        self.QSSgraphIV.axhline(y=0, color='k')
        self.QSSgraphIV.axvline(x=0, color='k')
        self.QSSgraphStab = self.fig6.add_subplot(122) #step-wise JV vs time
        self.QSSgraphStab.set_xlabel('Time (s)')
        self.QSSgraphStab.set_ylabel('Current density (mA/cm'+'\xb2'+')')
        self.QSSgraphStabbis = self.QSSgraphStab.twinx()
        self.QSSgraphStabbis.set_ylabel('Voltage (mV)')
        self.QSSgraphStabbis.spines['left'].set_color('red')
        self.QSSgraphStabbis.yaxis.label.set_color('red')
        self.QSSgraphStabbis.tick_params(axis='y', colors='red')
        self.addmpl(self.fig6,self.ui.gridLayout_MPLwidgetQSS,self.ui.MPLwidgetQSS)
        
        self.fig7 = Figure()
        self.TimegraphIV = self.fig7.add_subplot(121)
        self.TimegraphIV.set_xlabel('Voltage (V)')
        self.TimegraphIV.set_ylabel('Current density (mA/cm'+'\xb2'+')')
        self.TimegraphIV.axhline(y=0, color='k')
        self.TimegraphIV.axvline(x=0, color='k')
        self.TimegraphStab = self.fig7.add_subplot(122) #step-wise JV vs time
        self.TimegraphStab.set_xlabel('Time (s)')
        self.TimegraphStab.set_ylabel('Current density (mA/cm'+'\xb2'+')')
        self.addmpl(self.fig7,self.ui.gridLayout_MPLwidgetTime,self.ui.MPLwidgetTime)
        
        for item0 in [self.QSSgraphIV, self.QSSgraphStab, self.QSSgraphStabbis, self.DIVgraphlin,self.DIVgraphlogY,self.DBgraph,self.JVgraph,self.MPPTgraph_JV,self.MPPTgraph_TV,self.MPPTgraph_TJ,self.MPPTgraph_TP,self.TimegraphStab, self.TimegraphIV]:
            for item in ([item0.title, item0.xaxis.label, item0.yaxis.label] +
                         item0.get_xticklabels() + item0.get_yticklabels()):
                item.set_fontsize(10)
        
        self.ui.actionLoad_settings.triggered.connect(lambda: LoadParamTemplate(self))
        self.ui.actionSave_settings.triggered.connect(lambda: SaveParamTemplate(self))
        self.ui.actionLoad_lastsession.triggered.connect(self.LoadSession)
        self.ui.actionSave_lastsession.triggered.connect(self.SaveSession)
        
        self.ui.pushButton_OpenCloseShutter.clicked.connect(lambda: self.opencloseshutter(self.keithleyObject))
    
        self.ui.pushButton_StartMeas.clicked.connect(self.InitMeas)
        
        self.ui.pushButton_cleargraph.clicked.connect(lambda: self.ClearGraph('0'))
        
        self.ui.pushButton_stoptracking.clicked.connect(self.stopmeasmpp)
        self.ui.pushButton_StopSequ.clicked.connect(self.stopmeas)
        self.ui.pushButton_StopMeas.clicked.connect(self.stopmeas)
        self.ui.pushButton_StopMppt.clicked.connect(self.stopmeasmpp)
        self.ui.pushButton_upandstart.clicked.connect(self.upandstart)
        
        self.ui.pushButton_MeasureIntensityDiode.clicked.connect(lambda: self.MeasureRefDiode(self.keithleyObject))

        self.ui.pushButton_LoadAllDATAinTable.clicked.connect(lambda: self.UpdateTable(AllDATA))
        
        self.ui.pushButton_PlotfromTable.clicked.connect(self.PlotfromTable)
        
        self.ui.pushButton_exportgraphandfile.clicked.connect(self.Exporttxtplot)
        
        self.ui.comboBox_MeasType.currentTextChanged.connect(self.on_combobox_changed)
        
        self.ui.tabWidget.currentChanged.connect(self.onclickDBtab)
        
        self.ui.comboBox_DBTime.currentTextChanged.connect(self.on_combobox_DBTime_changed)
        self.ui.comboBox_DBTimeYaxis.currentTextChanged.connect(self.SearchAndPlot)
        self.ui.comboBox_DBTime_restrictions.currentTextChanged.connect(self.on_combobox_DBTimeRestrictions_changed)
        self.ui.pushButton_DBTime_Add.clicked.connect(self.Addrestriction)
        self.ui.pushButton_DBTime_remove.clicked.connect(self.Removerestriction)
        self.ui.comboBox_Time_timeplots.currentTextChanged.connect(self.updateRepgraph)
        self.ui.comboBox_Time_IVplots.currentTextChanged.connect(self.updateRepgraph)
        
        self.ui.pushButton_PersoSequence.clicked.connect(lambda: self.LoadStartPersoSequence(self.keithleyObject))
        
        self.ui.doubleSpinBox_MeasuredDiodeCurrent.valueChanged.connect(self.adjustActIntensity)
        
    def closeEvent(self, event):
        """ what happens when close the program"""
        
        close = QMessageBox.question(self,
                                     "QUIT",
                                     "Are you sure?",
                                      QMessageBox.Yes | QMessageBox.No)
        if close == QMessageBox.Yes:
            shutdownKeithley(self.keithleyObject)
            self.theCursor.close()
            self.db_conn.close()
            event.accept()
            app.quit()
        else:
            event.ignore()
        
    def on_combobox_changed(self, value):
        
        if value == 'FixedVoltage':
            self.ui.label_20.setText('Fixed voltage (mV):')
            self.ui.groupBox_MPPTParam.setTitle('FV parameters')
        elif value == 'FixedCurrent':
            self.ui.label_20.setText('Fixed current (mA/cm2):')
            self.ui.groupBox_MPPTParam.setTitle('FC parameters')
        else:
            self.ui.label_20.setText('Start voltage (mV):')
            self.ui.groupBox_MPPTParam.setTitle('MPPT parameters')
                
    def ConnectArduino(self):
        i=5
        connected=1
        while i:
            arduino_ports = [
                p.device
                for p in serial.tools.list_ports.comports()
                if 'Arduino' in p.description
            ]
            
            if not arduino_ports:
                print("No Arduino found")
                self.ui.textEdit_Keithley.append(QtCore.QDateTime.currentDateTime().toString()+': '+'No Arduino found')
                break
                connected=0
            elif len(arduino_ports) > 1:
                print('Multiple Arduinos found - using the first')
                self.ui.textEdit_Keithley.append(QtCore.QDateTime.currentDateTime().toString()+': '+'Multiple Arduinos found - using the first')
                break
                connected=0
            else:
                self.ser = serial.Serial(str(arduino_ports[0]),9600, timeout=.1)
                time.sleep(0.05)
                print("startsendingtoarduino")
                self.ui.textEdit_Keithley.append(QtCore.QDateTime.currentDateTime().toString()+': '+'startsendingtoarduino')
                print("Arduino is connected on ",arduino_ports[0])
                self.ui.textEdit_Keithley.append(QtCore.QDateTime.currentDateTime().toString()+': '+"Arduino is connected on ",arduino_ports[0])
                self.ser.write('L'.encode())
                break
                connected=1
                
        if connected==0:
            print("Connection failed after 5 attempts on all ports")
            self.ui.textEdit_Keithley.append(QtCore.QDateTime.currentDateTime().toString()+': '+'Connection failed after 5 attempts on all ports')
                    
#%%#############
    def loadingtemplate(self):
        templateloading = QMessageBox.question(self,
                                      "Template",
                                      "Do you have a template file to load?",
                                      QMessageBox.Yes | QMessageBox.No)
        if templateloading == QMessageBox.Yes:
            LoadParamTemplate(self)
        else:
            CreateParamTemplate(self)
        
    def SaveSession(self):
        global shutteropen,RefDiodeChecked,Sunintensity,STOPMEAS,STOPMEASMPP,AllDATA,lastmeasDATA,AlltrackingDATA,lastmeastrackingDATA,aftermpp,ongoingseq,latestVmpp
        global boxCurrent,boxVoltage,keithleyAddress,loadtempfilepath
        
        directory=os.path.join(exedirectory,'Database\SessionSaved')
        if not os.path.exists(directory):
            os.makedirs(directory)
            os.chdir(directory)
        else :
            os.chdir(directory)
        
        listofglobalvariables= [shutteropen,RefDiodeChecked,Sunintensity,STOPMEAS,STOPMEASMPP,AllDATA,lastmeasDATA,AlltrackingDATA,lastmeastrackingDATA,aftermpp,ongoingseq,latestVmpp,boxCurrent,boxVoltage,keithleyAddress,loadtempfilepath]
        
        for item in range(len(listofglobalvariables)):
            pickle.dump(listofglobalvariables[item],open(str(item)+'.pkl','wb'), protocol=pickle.HIGHEST_PROTOCOL)
        
        #savesettings
        SaveParamTemplate(self,os.path.join(directory,'GUIsettings.txt'))
        
        #save event log
        datename=QtCore.QDateTime.currentDateTime().toString().replace(' ','-').replace(':','-')
        with open(datename+'_EventsLog.txt','w') as file:
            Text=self.ui.textEdit_Keithley.toPlainText()
            file.write(Text)
        
        self.ui.textEdit_Keithley.append(QtCore.QDateTime.currentDateTime().toString()+': '+'session dumped')
        
    def LoadSession(self):
        global shutteropen,RefDiodeChecked,Sunintensity,STOPMEAS,STOPMEASMPP,AllDATA,lastmeasDATA,AlltrackingDATA,lastmeastrackingDATA,aftermpp,ongoingseq,latestVmpp
        global boxCurrent,boxVoltage,keithleyAddress,loadtempfilepath

        directory=os.path.join(exedirectory,'Database\SessionSaved')
        if os.path.exists(directory):
            os.chdir(directory)
            listofglobalvariables= ["shutteropen","RefDiodeChecked","Sunintensity","STOPMEAS","STOPMEASMPP","AllDATA","lastmeasDATA","AlltrackingDATA","lastmeastrackingDATA","aftermpp","ongoingseq","latestVmpp","boxCurrent","boxVoltage","keithleyAddress","loadtempfilepath"]
            
            for item in range(len(listofglobalvariables)):
                globals()[listofglobalvariables[item]] = pickle.load(open(str(item)+'.pkl','rb'))
            
            #reloadsavedsettings
            LoadParamTemplate(self,os.path.join(directory,'GUIsettings.txt'))
            
            self.ui.doubleSpinBox_NumbSun.setValue(Sunintensity)
            if aftermpp==1:
                self.ui.checkBox_aftermpp.setChecked(True)
            else:
                self.ui.checkBox_aftermpp.setChecked(False)
            
            self.ui.textEdit_Keithley.append(QtCore.QDateTime.currentDateTime().toString()+': '+'session loaded')
        else:
            self.ui.textEdit_Keithley.append(QtCore.QDateTime.currentDateTime().toString()+': '+'no dumped session available')
        
#%%######################################################################################################

    def addmpl(self, fig, whereLayout, whereWidget):
        self.canvas = FigureCanvas(fig)
        whereLayout.addWidget(self.canvas)
        self.canvas.draw()
        self.toolbar = NavigationToolbar(self.canvas, 
                whereWidget, coordinates=True)
        whereLayout.addWidget(self.toolbar)
        
    def opencloseshutter(self,keithleyObject):
        global shutteropen,arduino
        
        if not shutteropen: #if closed, then we open
            openShutter(keithleyObject)
            Arduino_write_read('ON',arduino)
            shutteropen=1
            self.ui.pushButton_OpenCloseShutter.setText('Shutter is open')
        else: #if open, then we close
            closeShutter(keithleyObject)
            Arduino_write_read('OFF',arduino)
            shutteropen=0
            self.ui.pushButton_OpenCloseShutter.setText('Shutter is closed')
            
    def shutter(self,action,keithleyObject):
        global shutteropen,arduino
        
        if action == 'OpenShutter':
            openShutter(keithleyObject)
            Arduino_write_read('ON',arduino)
            shutteropen=1
            self.ui.pushButton_OpenCloseShutter.setText('Shutter is open')
        else:
            closeShutter(keithleyObject)
            Arduino_write_read('OFF',arduino)
            shutteropen=0
            self.ui.pushButton_OpenCloseShutter.setText('Shutter is closed')  
        
#%%######################################################################################################
    def Popup_CheckDiode(self):
        choice = QMessageBox.question(self, 'Do you want to measure the reference diode?',
                                            "Click Ok to measure it\nClick Ignore to assume 1 sun",
                                            QMessageBox.Ok | QMessageBox.Ignore)
        if choice == QMessageBox.Ok:
            self.MeasureRefDiode()
            return 'measuring the ref diode'
        else:
            self.ui.radioButton_Assume1sun.setChecked(True)
            return 'User ignores request for ref meas'
    
    def MeasureRefDiode(self, keithleyObject):
        global RefDiodeChecked, Sunintensity
        if self.ui.doubleSpinBox_DiodeNominalCurrent.value()==0:
                    QMessageBox.information(self,'Norminal current is 0', 'Please enter a Nominal current for the ref. diode.')
        else:
            polar='pin'
            if not self.ui.checkBox_pin.isChecked():
                polar='nip'
    #        self.shutter('OpenShutter',keithleyObject)
            self.opencloseshutter(keithleyObject)
            time.sleep(1)
            # setRearTerminal(keithleyObject)
            # prepareCurrent(keithleyObject, NPLC = 1, currentlimit=1e-2, polarity=polar)
            prepareCurrent(keithleyObject, NPLC = 1, currentlimit=self.ui.doubleSpinBox_RefCellIlimit.value(), polarity=polar)
            dataCurrent = measureCurrent(keithleyObject,voltage=0.0,n=20, polarity = polar)
            self.ui.doubleSpinBox_MeasuredDiodeCurrent.setValue(abs(mean(dataCurrent[:,1])))
            Sunintensity=abs(mean(dataCurrent[:,1]))/self.ui.doubleSpinBox_DiodeNominalCurrent.value()
            self.ui.doubleSpinBox_NumbSun.setValue(Sunintensity)
            self.opencloseshutter(keithleyObject)
            RefDiodeChecked=1
    def adjustActIntensity(self):
        Sunintensity=self.ui.doubleSpinBox_MeasuredDiodeCurrent.value()/self.ui.doubleSpinBox_DiodeNominalCurrent.value()
        self.ui.doubleSpinBox_NumbSun.setValue(Sunintensity)
    def stopmeas(self):
        global STOPMEAS
        STOPMEAS=1
    def stopmeasmpp(self):
        global STOPMEASMPP
        STOPMEASMPP=1
       
    def PlotfromTable(self):
        global AllDATA
        
        rows=list(set(index.row() for index in self.ui.tableWidget.selectedIndexes()))
        sampleselected=[self.ui.tableWidget.item(row,0).text() for row in rows]
        self.ClearGraph('LIV')
        if self.ui.comboBox_JV_ptsorline.currentText() == 'Dots and Line':
            markerJV='o'
        elif self.ui.comboBox_JV_ptsorline.currentText() == 'Line':
            markerJV=''
        for sample in sampleselected:
            direction=AllDATA[sample]['ScanDirection']
            if direction == 'fwd':#forward scan
                self.JVgraph.plot(AllDATA[sample]['Voltage'],AllDATA[sample]['CurrentDensity'],marker=markerJV, linestyle="dashed",label=AllDATA[sample]['SampleNamePix']+'_'+direction)
            elif direction == 'rev':#reverse scan
                self.JVgraph.plot(AllDATA[sample]['Voltage'],AllDATA[sample]['CurrentDensity'],marker=markerJV, linestyle="solid",label=AllDATA[sample]['SampleNamePix']+'_'+direction)
        self.JVgraph.legend()
        self.fig1.canvas.draw_idle()
        self.fig1.canvas.flush_events()
       
    def Exporttxtplot(self):
        global AllDATA
        
        rows=list(set(index.row() for index in self.ui.tableWidget.selectedIndexes()))
        sampleselected=[self.ui.tableWidget.item(row,0).text() for row in rows]
        
        for sample in sampleselected:
            self.Savedata(sample,AllDATA)
    def upandstart(self):
        self.ui.spinBox_pixXnumber.setValue(self.ui.spinBox_pixXnumber.value()+1)
        self.InitMeas()
        
    def InitMeas(self):
        self.ui.label_ongoingmeasurement.setText('The measurement sequence has started...')
        if self.ui.checkBox_threaded.isChecked():
            self.ui.textEdit_Keithley.append(QtCore.QDateTime.currentDateTime().toString()+': '+'threaded')
            self.StartMeasThreaded(self.keithleyObject)
        else:
            self.ui.textEdit_Keithley.append(QtCore.QDateTime.currentDateTime().toString()+': '+'not threaded')
            self.StartMeas(self.keithleyObject)
            
    def LoadStartPersoSequence(self, keithleyObject):
        global STOPMEAS, STOPMEASMPP,Sunintensity
        #ask user to choose file
        directory=os.path.join(str(Path(os.path.abspath(__file__))),'ExamplesTemplateFiles')
        fname = QFileDialog.getOpenFileName(self, 'Choose a Sequence file to load', directory,"Text files (*.txt)")
        if fname[0] =='':
            return
        
        #open and read file
        filetoread = open(fname[0],"r", encoding='ISO-8859-1')
        filerawdata = filetoread.readlines()
        
        #execute the sequence
        Assume1suncheck=0
        if not self.ui.radioButton_Assume1sun.isChecked() and not RefDiodeChecked:
            Assume1suncheck=self.Popup_CheckDiode()
        go=0
        
        if Assume1suncheck =='User ignores request for ref meas' or self.ui.radioButton_Assume1sun.isChecked():
            Sunintensity=1
            go=1
        if go or RefDiodeChecked:
            if RefDiodeChecked and not self.ui.radioButton_Assume1sun.isChecked():
                Sunintensity=self.ui.doubleSpinBox_NumbSun.value()
                
        stepnumb=1
        Rep=0
        pixels=[str(self.ui.spinBox_pixXnumber.value())]
        pixcolorslist=['black']
        
        for row in filerawdata:
            if STOPMEAS==1:
                self.sequence=''
                break
            
            self.ui.spinBox_SequStepNumb.setValue(stepnumb)
            stepnumb+=1
            # print(row)
            
            if row.split('\t')[0] =='LIV':
                self.ui.lineEdit_SequMeasNow.setText('LIV')
                self.ui.Figure_tabWidget.setCurrentIndex(0)
                self.ui.doubleSpinBox_JVminvoltage.setValue(float(row.split('\t')[1]))
                self.ui.doubleSpinBox_JVmaxvoltage.setValue(float(row.split('\t')[2]))
                self.ui.doubleSpinBox_JVstepsize.setValue(float(row.split('\t')[3]))
                self.ui.doubleSpinBox_JVcurrentlimit.setValue(float(row.split('\t')[4]))
                self.ui.doubleSpinBox_JVintegrationtime.setValue(float(row.split('\t')[5]))
                self.ui.doubleSpinBox_JVdelaypoints.setValue(float(row.split('\t')[6]))
                self.ui.doubleSpinBox_JVdelayshutter.setValue(float(row.split('\t')[7]))
                
                if row.split('\t')[9]=='Line':
                    self.ui.comboBox_JV_ptsorline.setCurrentIndex(0)
                # QtTest.QTest.qWait(1000)
                direction=row.split('\t')[8]
                if direction=="Reverse + Forward":
                    self.ui.comboBox_JVscandirection.setCurrentIndex(0)
                    scandirections=[0,1]
                elif direction=="Forward + Reverse":
                    self.ui.comboBox_JVscandirection.setCurrentIndex(1)
                    scandirections=[1,0]
                elif direction=="Reverse":
                    self.ui.comboBox_JVscandirection.setCurrentIndex(2)
                    scandirections=[0]
                elif direction=="Forward":
                    self.ui.comboBox_JVscandirection.setCurrentIndex(3)
                    scandirections=[1]
                    
                self.shutter('OpenShutter',keithleyObject)
                self.ui.checkBox_MPPTlighton.setChecked(True)

                if row.split('\t')[10]=='pin\n':
                    self.ui.checkBox_pin.setChecked(True)
                    # self.ui.radioButton_nip.setChecked(False)
                else:
                    self.ui.checkBox_pin.setChecked(False)
                    # self.ui.radioButton_nip.setChecked(True)
                
                self.PlotIV(keithleyObject, pixels, pixcolorslist, scandirections, Rep)
            elif row.split('\t')[0] =='DIV':
                self.ui.lineEdit_SequMeasNow.setText('DIV')
                self.ui.Figure_tabWidget.setCurrentIndex(2)
                self.ui.doubleSpinBox_JVminvoltage.setValue(float(row.split('\t')[1]))
                self.ui.doubleSpinBox_JVmaxvoltage.setValue(float(row.split('\t')[2]))
                self.ui.doubleSpinBox_JVstepsize.setValue(float(row.split('\t')[3]))
                self.ui.doubleSpinBox_JVcurrentlimit.setValue(float(row.split('\t')[4]))
                self.ui.doubleSpinBox_JVintegrationtime.setValue(float(row.split('\t')[5]))
                self.ui.doubleSpinBox_JVdelaypoints.setValue(float(row.split('\t')[6]))
                self.ui.doubleSpinBox_JVdelayshutter.setValue(float(row.split('\t')[7]))
                
                if row.split('\t')[9]=='Line':
                    self.ui.comboBox_JV_ptsorline.setCurrentIndex(0)
                # QtTest.QTest.qWait(1000)
                direction=row.split('\t')[8]
                if direction=="Reverse + Forward":
                    self.ui.comboBox_JVscandirection.setCurrentIndex(0)
                    scandirections=[0,1]
                elif direction=="Forward + Reverse":
                    self.ui.comboBox_JVscandirection.setCurrentIndex(1)
                    scandirections=[1,0]
                elif direction=="Reverse":
                    self.ui.comboBox_JVscandirection.setCurrentIndex(2)
                    scandirections=[0]
                elif direction=="Forward":
                    self.ui.comboBox_JVscandirection.setCurrentIndex(3)
                    scandirections=[1]
                    
                self.shutter('CloseShutter',keithleyObject)
                self.ui.checkBox_MPPTlighton.setChecked(False)

                if row.split('\t')[10]=='pin\n':
                    self.ui.checkBox_pin.setChecked(True)
                    # self.ui.radioButton_nip.setChecked(False)
                else:
                    self.ui.checkBox_pin.setChecked(False)
                    # self.ui.radioButton_nip.setChecked(True)
                
                self.PlotIV(keithleyObject, pixels, pixcolorslist, scandirections, Rep)
                
            elif row.split('\t')[0] =='WAIT':
                self.ui.lineEdit_SequMeasNow.setText('WAIT ',)
                duration=float(row.split('\t')[1][:-1]) #in seconds
                # print('duration: ',duration)
                if duration<=1:
                    time.sleep(duration)
                    # QtTest.QTest.qWait(duration)
                else:
                    item=0
                    while(item<duration):
                        time.sleep(1)
                        # QtTest.QTest.qWait(1000)
                        if STOPMEAS==1:
                            break
                        self.ui.lineEdit_SequMeasNow.setText('WAIT '+str(item+1))
                        self.fig2.canvas.draw_idle()
                        self.fig2.canvas.flush_events()
                        item+=1
            else:#tracking
                # QtTest.QTest.qWait(1000)
                self.ui.Figure_tabWidget.setCurrentIndex(1)
                if row.split('\t')[1]=='False':
                    self.ui.checkBox_MPPTuseVmpp.setChecked(False)
                else:
                    self.ui.checkBox_MPPTuseVmpp.setChecked(True)
                self.ui.doubleSpinBox_MPPTstartvoltage.setValue(float(row.split('\t')[2]))
                self.ui.spinBox_MPPTstepsize.setValue(float(row.split('\t')[3]))
                self.ui.doubleSpinBox_MPPTvoltagelimit.setValue(float(row.split('\t')[4]))
                self.ui.doubleSpinBox_MPPTdelaypoints.setValue(float(row.split('\t')[5]))
                if row.split('\t')[6]=='ON':
                    self.ui.checkBox_MPPTlighton.setChecked(True)
                    self.shutter('OpenShutter',keithleyObject)
                else:
                    self.shutter('CloseShutter',keithleyObject)
                    self.ui.checkBox_MPPTlighton.setChecked(False)
                if row.split('\t')[7]=='ON':
                    self.ui.checkBox_MPPTlightonafter.setChecked(True)
                else:
                    self.ui.checkBox_MPPTlightonafter.setChecked(False)
                duration= float(row.split('\t')[8])
                
                if row.split('\t')[9]=='pin\n':
                    self.ui.checkBox_pin.setChecked(True)
                    # self.ui.radioButton_nip.setChecked(False)
                else:
                    self.ui.checkBox_pin.setChecked(False)
                    # self.ui.radioButton_nip.setChecked(True)
                    
                if row.split('\t')[0] =='MPPT':
                    self.ui.lineEdit_SequMeasNow.setText('MPPT')
                    self.Tracking(keithleyObject,'MPPT', pixels, pixcolorslist, Rep,duration)

                elif row.split('\t')[0] =='FixedCurrent':
                    self.ui.lineEdit_SequMeasNow.setText('FixedCurrent')
                    QtTest.QTest.qWait(500)
                    self.Tracking(keithleyObject,'FixedCurrent', pixels, pixcolorslist, Rep,duration)

                elif row.split('\t')[0] =='FixedVoltage':
                    self.ui.lineEdit_SequMeasNow.setText('FixedVoltage')
                    QtTest.QTest.qWait(500) 
                    self.Tracking(keithleyObject,'FixedVoltage', pixels, pixcolorslist, Rep,duration)
        
        self.ui.label_ongoingmeasurement.setText('The sequence is finished.')
        self.ui.lineEdit_SequMeasNow.setText('Finished')
            
    def StartMeasThreaded(self, keithleyObject):
        global ongoing,version, aftermpp,boxCurrent, boxVoltage, RefDiodeChecked, STOPMEAS, shutteropen,lastmeastrackingDATA, lastmeasDATA, Sunintensity
        self.ui.pushButton_StartMeas.setEnabled(False)
        self.ui.pushButton_upandstart.setEnabled(False)
        self.ui.pushButton_MeasureIntensityDiode.setEnabled(False)
        STOPMEAS=0
        aftermpp=0
        lastmeasDATA={}
        lastmeastrackingDATA={}
        # self.ClearGraph('All') #clear All
        self.ClearTable()
        
        ########
        Assume1suncheck=0
        if not self.ui.radioButton_Assume1sun.isChecked() and not RefDiodeChecked:
            Assume1suncheck=self.Popup_CheckDiode()
        go=0
        
        if Assume1suncheck =='User ignores request for ref meas' or self.ui.radioButton_Assume1sun.isChecked():
            Sunintensity=1
            go=1
        if go or RefDiodeChecked:
            if RefDiodeChecked and not self.ui.radioButton_Assume1sun.isChecked():
                Sunintensity=self.ui.doubleSpinBox_NumbSun.value()
        
            ########
            
            if self.ui.spinBox_RepNumb.value()>1:
                self.sequence = str(self.ui.comboBox_MeasType.currentText())
                for item in range(self.ui.spinBox_RepNumb.value()-1):
                    self.sequence = self.sequence + '-WAIT-'+str(self.ui.comboBox_MeasType.currentText())
                    
                self.ClearGraph('Rep')
            else:
                self.sequence = str(self.ui.comboBox_MeasType.currentText())
            
            if version != '1pixel': 
                pixels=[]
                pixcolorslist=[]
                Allpixels=['A','B','C','D','E','F']
                allpixcolors=['black','red','blue','green','cyan','magenta']
                if self.ui.radioButton_pixAll.isChecked():
                    pixels=Allpixels
                    pixcolorslist=allpixcolors
                else:
                    checkboxlist=[self.ui.checkBox_pixA.isChecked(),self.ui.checkBox_pixB.isChecked(),
                                  self.ui.checkBox_pixC.isChecked(),self.ui.checkBox_pixD.isChecked(),
                                  self.ui.checkBox_pixE.isChecked(),self.ui.checkBox_pixF.isChecked()]
                    for item in range(6):
                        if checkboxlist[item]:
                            pixels.append(Allpixels[item])
                            pixcolorslist.append(allpixcolors[item])
            else:
                pixels=[str(self.ui.spinBox_pixXnumber.value())]
                pixcolorslist=['black']
                        
            if self.ui.comboBox_JVscandirection.currentText()=="Reverse + Forward":
                scandirections=[0,1]
            elif self.ui.comboBox_JVscandirection.currentText()=="Forward + Reverse":
                scandirections=[1,0]
            elif self.ui.comboBox_JVscandirection.currentText()=="Reverse":
                scandirections=[0]
            elif self.ui.comboBox_JVscandirection.currentText()=="Forward":
                scandirections=[1]
            self.ui.textEdit_Keithley.append(QtCore.QDateTime.currentDateTime().toString()+': launchSequence '+self.sequence)
            self.launchSequence(keithleyObject, pixels, pixcolorslist, scandirections, 0)
                    
    def launchSequence(self, keithleyObject, pixels, pixcolorslist, scandirections, Rep):
        global ongoing, aftermpp,boxCurrent, boxVoltage, RefDiodeChecked, STOPMEAS, shutteropen,lastmeastrackingDATA, lastmeasDATA, Sunintensity, lastJVscansVmpp
        ongoing=1
        
        if self.sequence=='':
            self.ui.label_ongoingmeasurement.setText('The sequence is finished.')
            # QMessageBox.information(self,'Finished', 'The sequence is finished.')
            self.ui.pushButton_StartMeas.setEnabled(True)
            self.ui.pushButton_upandstart.setEnabled(True)
            self.ui.pushButton_MeasureIntensityDiode.setEnabled(True)
            ongoing=0
        elif self.sequence.split('-')[0]=='LIV':
            self.ui.label_ongoingmeasurement.setText('The measurement sequence has started... LIV')
            if self.ui.checkBox_GoToTab.isChecked():
                if str(self.ui.comboBox_MeasType.currentText())=='LIV-QSS-LIV':
                    self.ui.Figure_tabWidget.setCurrentIndex(3)
                else:
                    self.ui.Figure_tabWidget.setCurrentIndex(0)
            # self.sequence=self.sequence[4:]
            self.shutter('OpenShutter',keithleyObject)
            QtTest.QTest.qWait(int(self.ui.doubleSpinBox_JVdelayshutter.value()))
            self.PlotIVThreaded(keithleyObject, pixels, pixcolorslist, scandirections, Rep)

        elif self.sequence.split('-')[0]=='DIV':
            self.ui.label_ongoingmeasurement.setText('The measurement sequence has started... DIV')
            if self.ui.checkBox_GoToTab.isChecked():
                self.ui.Figure_tabWidget.setCurrentIndex(2)
            # self.sequence=self.sequence[4:]
            self.shutter('CloseShutter',keithleyObject)
            self.PlotIVThreaded(keithleyObject, pixels, pixcolorslist, scandirections, Rep)
        
        elif self.sequence.split('-')[0]=='QSS':
            self.ui.label_ongoingmeasurement.setText('The measurement sequence has started... QSS')
            if self.ui.checkBox_GoToTab.isChecked():
                self.ui.Figure_tabWidget.setCurrentIndex(3)
            # self.sequence=self.sequence[4:]
            self.shutter('OpenShutter',keithleyObject)
            QtTest.QTest.qWait(int(self.ui.doubleSpinBox_JVdelayshutter.value()))
            self.PlotQSSThreaded(keithleyObject, pixels, pixcolorslist, scandirections, Rep)
            
        elif self.sequence.split('-')[0]=='MPPT':
            if str(self.ui.comboBox_MeasType.currentText())=='LIV-MPPT-LIV' or str(self.ui.comboBox_MeasType.currentText())=='DIV-LIV-MPPT-LIV'or str(self.ui.comboBox_MeasType.currentText())=='LIV-MPPT':
                if self.ui.checkBox_MPPTuseVmpp.isChecked():
                    voltagefixed=max(lastJVscansVmpp)
                    # voltagefixed=sorted(lastmeasDATA.items(), key=lambda x: x[1]['Vmpp'],reverse=True)[0][1]['Vmpp']
                    self.ui.doubleSpinBox_MPPTstartvoltage.setValue(voltagefixed)
            
            self.ui.label_ongoingmeasurement.setText('The measurement sequence has started... MPPT')
            if self.ui.checkBox_GoToTab.isChecked():
                self.ui.Figure_tabWidget.setCurrentIndex(1)
            self.sequence=self.sequence[5:]
            if self.ui.checkBox_MPPTlighton.isChecked():
                self.shutter('OpenShutter',keithleyObject)
            else:
                self.shutter('CloseShutter',keithleyObject)
            
            if self.ui.comboBox_MPPTopenOrCloseEnd.currentText()=='Open ending':
                self.Tracking(keithleyObject,'MPPT', pixels, pixcolorslist, Rep,-1)
            else:
                # print(self.ui.spinBox_MPPT_duration.value())
                self.Tracking(keithleyObject,'MPPT', pixels, pixcolorslist, Rep,self.ui.spinBox_MPPT_duration.value())
            
            if str(self.ui.comboBox_MeasType.currentText())!='LIV-MPPT-LIV':
                if self.ui.checkBox_MPPTlightonafter.isChecked():
                    self.shutter('OpenShutter',keithleyObject)
                else:
                    self.shutter('CloseShutter',keithleyObject)
            aftermpp=1
            self.ui.checkBox_aftermpp.setChecked(True)
            self.launchSequence(keithleyObject, pixels, pixcolorslist, scandirections, Rep)
        elif self.sequence.split('-')[0]=='FixedVoltage':
            if str(self.ui.comboBox_MeasType.currentText())=='LIV-FixedVoltage':
                if self.ui.checkBox_MPPTuseVmpp.isChecked():
                    voltagefixed=max(lastJVscansVmpp)
                    # voltagefixed=sorted(lastmeasDATA.items(), key=lambda x: x[1]['Vmpp'],reverse=True)[0][1]['Vmpp']
                    self.ui.doubleSpinBox_MPPTstartvoltage.setValue(voltagefixed)
                    
            self.ui.label_ongoingmeasurement.setText('The measurement sequence has started... FV')
            if self.ui.checkBox_GoToTab.isChecked():
                self.ui.Figure_tabWidget.setCurrentIndex(1)
            self.sequence=self.sequence[13:]
            if self.ui.checkBox_MPPTlighton.isChecked():
                self.shutter('OpenShutter',keithleyObject)
            else:
                self.shutter('CloseShutter',keithleyObject)
            
            if self.ui.comboBox_MPPTopenOrCloseEnd.currentText()=='Open ending':
                self.Tracking(keithleyObject,'FixedVoltage', pixels, pixcolorslist, Rep,-1)
            else:
                # print(self.ui.spinBox_MPPT_duration.value())
                self.Tracking(keithleyObject,'FixedVoltage', pixels, pixcolorslist, Rep,self.ui.spinBox_MPPT_duration.value())
            
            if self.ui.checkBox_MPPTlightonafter.isChecked():
                self.shutter('OpenShutter',keithleyObject)
            else:
                self.shutter('CloseShutter',keithleyObject)
            self.launchSequence(keithleyObject, pixels, pixcolorslist, scandirections, Rep)
        elif self.sequence.split('-')[0]=='FixedCurrent':
            self.ui.label_ongoingmeasurement.setText('The measurement sequence has started... FI')
            if self.ui.checkBox_GoToTab.isChecked():
                self.ui.Figure_tabWidget.setCurrentIndex(1)
            self.sequence=self.sequence[13:]
            if self.ui.checkBox_MPPTlighton.isChecked():
                self.shutter('OpenShutter',keithleyObject)
            else:
                self.shutter('CloseShutter',keithleyObject)
                
            if self.ui.comboBox_MPPTopenOrCloseEnd.currentText()=='Open ending':
                self.Tracking(keithleyObject,'FixedCurrent', pixels, pixcolorslist, Rep,-1)
            else:
                # print(self.ui.spinBox_MPPT_duration.value())
                self.Tracking(keithleyObject,'FixedCurrent', pixels, pixcolorslist, Rep,self.ui.spinBox_MPPT_duration.value())
            
            if self.ui.checkBox_MPPTlightonafter.isChecked():
                self.shutter('OpenShutter',keithleyObject)
            else:
                self.shutter('CloseShutter',keithleyObject)
            self.launchSequence(keithleyObject, pixels, pixcolorslist, scandirections, Rep)
        elif self.sequence.split('-')[0]=='bestpixMPPT':
            self.ui.label_ongoingmeasurement.setText('The measurement sequence has started...bestMPPT')
            if self.ui.checkBox_GoToTab.isChecked():
                self.ui.Figure_tabWidget.setCurrentIndex(1)
            self.sequence=self.sequence[12:]
            if self.ui.checkBox_MPPTlighton.isChecked():
                self.shutter('OpenShutter',keithleyObject)
            else:
                self.shutter('CloseShutter',keithleyObject)
            self.Tracking(keithleyObject,'MPPTbest', pixels, pixcolorslist, Rep,-1)
            
            if self.ui.checkBox_MPPTlightonafter.isChecked():
                self.shutter('OpenShutter',keithleyObject)
            else:
                self.shutter('CloseShutter',keithleyObject)
            self.launchSequence(keithleyObject, pixels, pixcolorslist, scandirections, Rep)
        elif self.sequence.split('-')[0]=='LongTermTesting':
            self.ui.label_ongoingmeasurement.setText('The measurement sequence has started...LongTermTesting')
            if self.ui.checkBox_GoToTab.isChecked():
                self.ui.Figure_tabWidget.setCurrentIndex(4)
            self.sequence=self.sequence[16:]
            if self.ui.checkBox_MPPTlighton.isChecked():
                self.shutter('OpenShutter',keithleyObject)
            else:
                self.shutter('CloseShutter',keithleyObject)
            print('doing long term testing')
            if self.ui.checkBox_MPPTlightonafter.isChecked():
                self.shutter('OpenShutter',keithleyObject)
            else:
                self.shutter('CloseShutter',keithleyObject)
            self.launchSequence(keithleyObject, pixels, pixcolorslist, scandirections, Rep)
        elif self.sequence.split('-')[0]=='WAIT':
            self.ui.label_ongoingmeasurement.setText('The measurement sequence has started... wait')
            self.sequence=self.sequence[5:]
            duration=self.ui.spinBox_RepDelay.value()*1000
            if duration<=1000:
                QtTest.QTest.qWait(int(duration))
            else:
                item=0
                while(item<self.ui.spinBox_RepDelay.value()):
                    QtTest.QTest.qWait(1000)
                    if STOPMEAS==1:
                        self.sequence=''
                        if self.ui.checkBox_MPPTlightonafter.isChecked():
                            self.shutter('OpenShutter',keithleyObject)
                        else:
                            self.shutter('CloseShutter',keithleyObject)
                        break
                    item+=1
                self.launchSequence(keithleyObject, pixels, pixcolorslist, scandirections, Rep)
        
    def StartMeas(self, keithleyObject):#if not threaded
        global version, aftermpp,boxCurrent, boxVoltage, RefDiodeChecked, STOPMEAS, shutteropen,lastmeastrackingDATA, lastmeasDATA, Sunintensity
        self.ui.pushButton_StartMeas.setEnabled(False)
        self.ui.pushButton_upandstart.setEnabled(False)
        self.ui.pushButton_MeasureIntensityDiode.setEnabled(True)
        STOPMEAS=0
        lastmeasDATA={}
        lastmeastrackingDATA={}
        # self.ClearGraph('All') #clear All
        self.ClearTable()
        
        ########
        Assume1suncheck=0
        if not self.ui.radioButton_Assume1sun.isChecked() and not RefDiodeChecked:
            Assume1suncheck=self.Popup_CheckDiode()
        go=0
        
        if Assume1suncheck =='User ignores request for ref meas' or self.ui.radioButton_Assume1sun.isChecked():
            Sunintensity=1
            go=1
        if go or RefDiodeChecked:
            if RefDiodeChecked and not self.ui.radioButton_Assume1sun.isChecked():
                Sunintensity=self.ui.doubleSpinBox_NumbSun.value()
        
            ########
            
            for i in range(self.ui.spinBox_RepNumb.value()):
                
                sequence = str(self.ui.comboBox_MeasType.currentText())
                if version != '1pixel': 
                    pixels=[]
                    pixcolorslist=[]
                    Allpixels=['A','B','C','D','E','F']
                    allpixcolors=['black','red','blue','green','cyan','magenta']
                    if self.ui.radioButton_pixAll.isChecked():
                        pixels=Allpixels
                        pixcolorslist=allpixcolors
                    else:
                        checkboxlist=[self.ui.checkBox_pixA.isChecked(),self.ui.checkBox_pixB.isChecked(),
                                      self.ui.checkBox_pixC.isChecked(),self.ui.checkBox_pixD.isChecked(),
                                      self.ui.checkBox_pixE.isChecked(),self.ui.checkBox_pixF.isChecked()]
                        for item in range(6):
                            if checkboxlist[item]:
                                pixels.append(Allpixels[item])
                                pixcolorslist.append(allpixcolors[item])
                else:
                    pixels=[str(self.ui.spinBox_pixXnumber.value())]
                    pixcolorslist=['black']
                            
                if self.ui.comboBox_JVscandirection.currentText()=="Reverse + Forward":
                    scandirections=[0,1]
                elif self.ui.comboBox_JVscandirection.currentText()=="Forward + Reverse":
                    scandirections=[1,0]
                elif self.ui.comboBox_JVscandirection.currentText()=="Reverse":
                    scandirections=[0]
                elif self.ui.comboBox_JVscandirection.currentText()=="Forward":
                    scandirections=[1]
                
                #########################
                if sequence == 'LIV':
                    self.shutter('OpenShutter',keithleyObject)
                    QtTest.QTest.qWait(int(self.ui.doubleSpinBox_JVdelayshutter.value()))
                    self.PlotIV(keithleyObject, pixels, pixcolorslist, scandirections, i)
                    self.shutter('CloseShutter',keithleyObject)
                    
                if sequence == 'DIV':
                    self.shutter('CloseShutter',keithleyObject)
                    self.PlotIV(keithleyObject, pixels, pixcolorslist, scandirections, i)
                    
                if sequence == 'DIV-LIV':
                    self.shutter('CloseShutter',keithleyObject)
                    self.PlotIV(keithleyObject, pixels, pixcolorslist, scandirections, i)
                    self.shutter('OpenShutter',keithleyObject)
                    QtTest.QTest.qWait(int(self.ui.doubleSpinBox_JVdelayshutter.value()))
                    self.PlotIV(keithleyObject, pixels, pixcolorslist, scandirections, i)
                    self.shutter('CloseShutter',keithleyObject)
                    
                if sequence == 'MPPT':
                    if self.ui.checkBox_MPPTlighton.isChecked():
                        self.shutter('OpenShutter',keithleyObject)
                    else:
                        self.shutter('CloseShutter',keithleyObject)
                        
                    self.Tracking(keithleyObject,'MPPT', pixels, pixcolorslist, i,-1)
                    
                    if self.ui.checkBox_MPPTlightonafter.isChecked():
                        self.shutter('OpenShutter',keithleyObject)
                    else:
                        self.shutter('CloseShutter',keithleyObject)
                
                if sequence == 'FixedVoltage':
                    if self.ui.checkBox_MPPTlighton.isChecked():
                        self.shutter('OpenShutter',keithleyObject)
                    else:
                        self.shutter('CloseShutter',keithleyObject)
                    
                    self.Tracking(keithleyObject,'FixedVoltage', pixels, pixcolorslist, i,-1)
                    
                    if self.ui.checkBox_MPPTlightonafter.isChecked():
                        self.shutter('OpenShutter',keithleyObject)
                    else:
                        self.shutter('CloseShutter',keithleyObject)
                    
                if sequence == 'FixedCurrent':
                    if self.ui.checkBox_MPPTlighton.isChecked():
                        self.shutter('OpenShutter',keithleyObject)
                    else:
                        self.shutter('CloseShutter',keithleyObject)
                        
                    self.Tracking(keithleyObject,'FixedCurrent', pixels, pixcolorslist, i,-1)
                    
                    if self.ui.checkBox_MPPTlightonafter.isChecked():
                        self.shutter('OpenShutter',keithleyObject)
                    else:
                        self.shutter('CloseShutter',keithleyObject)
                    
                if sequence == 'LIV-MPPT-LIV':
                    self.shutter('OpenShutter',keithleyObject)
                    STOPMEAS=0
                    QtTest.QTest.qWait(int(self.ui.doubleSpinBox_JVdelayshutter.value()))
                    self.PlotIV(keithleyObject, pixels, pixcolorslist, scandirections, i)
                    
                    if self.ui.checkBox_MPPTlighton.isChecked():
                        self.shutter('OpenShutter',keithleyObject)
                    else:
                        self.shutter('CloseShutter',keithleyObject)
                    STOPMEAS=0    
                    self.Tracking(keithleyObject,'MPPT', pixels, pixcolorslist, i,-1)
                    
                    if self.ui.checkBox_MPPTlightonafter.isChecked():
                        self.shutter('OpenShutter',keithleyObject)
                    else:
                        self.shutter('CloseShutter',keithleyObject)
                    
                    STOPMEAS=0
                    aftermpp=1
                    self.ui.checkBox_aftermpp.setChecked(True)
                    self.PlotIV(keithleyObject, pixels, pixcolorslist, scandirections, i)
                    self.shutter('CloseShutter',keithleyObject)
                    aftermpp=0
                    self.ui.checkBox_aftermpp.setChecked(False)
                    
                if sequence == 'LIV-bestpixMPPT-LIV':
                    self.shutter('OpenShutter',keithleyObject)
                    STOPMEAS=0
                    QtTest.QTest.qWait(int(self.ui.doubleSpinBox_JVdelayshutter.value()))
                    self.PlotIV(keithleyObject, pixels, pixcolorslist, scandirections, i)
                    
                    if self.ui.checkBox_MPPTlighton.isChecked():
                        self.shutter('OpenShutter',keithleyObject)
                    else:
                        self.shutter('CloseShutter',keithleyObject)
                    STOPMEAS=0    
                    self.Tracking(keithleyObject,'MPPTbest', pixels, pixcolorslist, i,-1)
                    
                    if self.ui.checkBox_MPPTlightonafter.isChecked():
                        self.shutter('OpenShutter',keithleyObject)
                    else:
                        self.shutter('CloseShutter',keithleyObject)
                    
                    STOPMEAS=0
                    aftermpp=1
                    self.ui.checkBox_aftermpp.setChecked(True)
                    self.PlotIV(keithleyObject, pixels, pixcolorslist, scandirections, i)
                    
                    self.shutter('CloseShutter',keithleyObject)
                    aftermpp=0
                    self.ui.checkBox_aftermpp.setChecked(False)
                    
                if sequence == 'DIV-LIV-MPPT-LIV':
                    self.shutter('CloseShutter',keithleyObject)
                    STOPMEAS=0
                    self.PlotIV(keithleyObject, pixels, pixcolorslist, scandirections, i)
                    
                    STOPMEAS=0
                    self.shutter('OpenShutter',keithleyObject)
                    QtTest.QTest.qWait(int(self.ui.doubleSpinBox_JVdelayshutter.value()))
                    self.PlotIV(keithleyObject, pixels, pixcolorslist, scandirections, i)
                    
                    if self.ui.checkBox_MPPTlighton.isChecked():
                        self.shutter('OpenShutter',keithleyObject)
                    else:
                        self.shutter('CloseShutter',keithleyObject)
                    STOPMEAS=0    
                    self.Tracking(keithleyObject,'MPPT', pixels, pixcolorslist, i,-1)
                    
                    if self.ui.checkBox_MPPTlightonafter.isChecked():
                        self.shutter('OpenShutter',keithleyObject)
                    else:
                        self.shutter('CloseShutter',keithleyObject)
                        
                    STOPMEAS=0
                    aftermpp=1
                    self.ui.checkBox_aftermpp.setChecked(True)
                    self.PlotIV(keithleyObject, pixels, pixcolorslist, scandirections, i)
                    self.shutter('CloseShutter',keithleyObject)
                    aftermpp=0
                    self.ui.checkBox_aftermpp.setChecked(False)
                    
                if sequence == 'DIV-LIV-bestpixMPPT-LIV':
                    self.shutter('CloseShutter',keithleyObject)
                    STOPMEAS=0
                    self.PlotIV(keithleyObject, pixels, pixcolorslist, scandirections, i)
                    STOPMEAS=0
                    self.shutter('OpenShutter',keithleyObject)
                    QtTest.QTest.qWait(int(self.ui.doubleSpinBox_JVdelayshutter.value()))
                    self.PlotIV(keithleyObject, pixels, pixcolorslist, scandirections, i)
                    
                    if self.ui.checkBox_MPPTlighton.isChecked():
                        self.shutter('OpenShutter',keithleyObject)
                    else:
                        self.shutter('CloseShutter',keithleyObject)
                    STOPMEAS=0
                    self.Tracking(keithleyObject,'MPPTbest', pixels, pixcolorslist, i,-1)
                    
                    if self.ui.checkBox_MPPTlightonafter.isChecked():
                        self.shutter('OpenShutter',keithleyObject)
                    else:
                        self.shutter('CloseShutter',keithleyObject)
                        
                    STOPMEAS=0
                    aftermpp=1
                    self.ui.checkBox_aftermpp.setChecked(True)
                    self.PlotIV(keithleyObject, pixels, pixcolorslist, scandirections, i)
                    self.shutter('CloseShutter',keithleyObject)
                    aftermpp=0
                    self.ui.checkBox_aftermpp.setChecked(False)
                    
                if self.ui.spinBox_RepNumb.value()>1:
                    QtTest.QTest.qWait(int(self.ui.spinBox_RepDelay.value()*1000))
                    
        
        #disconnect from DB
        self.ui.label_ongoingmeasurement.setText('The sequence is finished.')
        self.ui.pushButton_StartMeas.setEnabled(True)
        self.ui.pushButton_upandstart.setEnabled(True)
        self.ui.pushButton_MeasureIntensityDiode.setEnabled(True)
    
     
    def Tracking(self, keithleyObject,trackingtype, pixelslist, pixcolorslist, Rep,duration):
        global STOPMEAS,STOPMEASMPP, AlltrackingDATA,lastmeastrackingDATA, RefDiodeChecked, Sunintensity, shutteropen
        global boxCurrent, boxVoltage, keithleyAddress, lastmeasDATA,exedirectory
        allpixtobemeasured=''
        
        self.SaveSession()
        
        if trackingtype=='MPPTbest':
            pixels=[sorted(lastmeasDATA.items(), key=lambda x: x[1]['Eff'],reverse=True)[0][1]['Pixel']]
        else:
            pixels=pixelslist
        
        for item in range(len(pixels)):
            allpixtobemeasured+=pixels[item]
            allpixtobemeasured+=', '
        allpixtobemeasured=allpixtobemeasured[:-2]
        
        year=str(QtCore.QDate.currentDate().toString(QtCore.Qt.ISODate).split('-')[0])
        month=calendar.month_name[int(QtCore.QDate.currentDate().toString(QtCore.Qt.ISODate).split('-')[1])]
        directory=os.path.join(exedirectory,'SolarSimAllUsersDATA',str(self.ui.lineEdit_UserName.text()),year,month)
        if not os.path.exists(directory):
            os.makedirs(directory)
            os.chdir(directory)
        else :
            os.chdir(directory)
        polar='pin'
        if not self.ui.checkBox_pin.isChecked():
            polar='nip'
        if trackingtype=='FixedCurrent':
            prepareVoltage(keithleyObject, NPLC = 1,voltlimit = 10, polarity=polar)#prepare to apply a current and measure a voltage
        else:
            prepareCurrent(keithleyObject, NPLC = 1, currentlimit=self.ui.doubleSpinBox_JVcurrentlimit.value(), polarity=polar)#prepare to apply a voltage and measure a current

        for item in range(len(pixels)):
            STOPMEASMPP=0
            nMeas = 3
            timelist=[]
            currentlist=[]
            currentdensitylist=[]
            voltagelist=[]
            powerlist=[]
            steplist=[]
            delaylist=[]
            
            initialvoltage=self.ui.doubleSpinBox_MPPTstartvoltage.value()
            initialdelay=self.ui.doubleSpinBox_MPPTdelaypoints.value()
            initialstep=self.ui.spinBox_MPPTstepsize.value()
            connectPixel(boxCurrent, boxVoltage, pixels[item])
            pixcolor=pixcolorslist[item]
            if version != '1pixel': 
                pixarea=eval('self.ui.doubleSpinBox_pix'+pixels[item]+'area.value()')
            else:
                pixarea=window.w.ui.doubleSpinBox_pixXarea.value()
            
            elapsed_timer = QtCore.QElapsedTimer()
            elapsed_timer.start()
            if self.ui.checkBox_MPPTlighton.isChecked():
                self.shutter('OpenShutter',keithleyObject)
            else:
                self.shutter('CloseShutter',keithleyObject)
            
            while True:
                voltagefixed=self.ui.doubleSpinBox_MPPTstartvoltage.value()
                delay=self.ui.doubleSpinBox_MPPTdelaypoints.value()
                step=self.ui.spinBox_MPPTstepsize.value()
                if trackingtype=='FixedVoltage':
                    dataCurrent=measureCurrent(keithleyObject,voltagefixed/1000,nMeas,polarity = polar)
                    currentden=1000*abs(mean(dataCurrent[:,1]))/pixarea #mA/cm2
                    current=abs(mean(dataCurrent[:,1])) #A
                    currentlist.append(float(current))
                    currentdensitylist.append(float(currentden))
                    voltagelist.append(float(voltagefixed))  #mV
                    powerlist.append(float(currentden*voltagefixed/1000)/Sunintensity)
                    timelist.append(float(elapsed_timer.elapsed()/1000))
                    steplist.append(step)
                    delaylist.append(delay)
                    if duration !=-1:
                        if float(elapsed_timer.elapsed()/1000)>duration:
                            STOPMEASMPP=1
                    
                elif trackingtype=='FixedCurrent':
                    dataVoltage=measureVoltage(keithleyObject,pixarea*voltagefixed/1000,nMeas,polarity = polar)#send Ampere values
                    voltage=abs(mean(dataVoltage[:,0]))
                    currentlist.append(voltagefixed*pixarea)
                    currentdensitylist.append(voltagefixed)
                    voltagelist.append(voltage*1000)
                    powerlist.append(voltage*voltagefixed/Sunintensity)
                    timelist.append(float(elapsed_timer.elapsed()/1000))
                    steplist.append(step)
                    delaylist.append(delay)
                    if duration !=-1:
                        if float(elapsed_timer.elapsed()/1000)>duration:
                            STOPMEASMPP=1
                
                elif trackingtype=='MPPT' or trackingtype=='MPPTbest':
                    if trackingtype=='MPPTbest':
                        voltagefixed=sorted(lastmeasDATA.items(), key=lambda x: x[1]['Eff'],reverse=True)[0][1]['Vmpp']
                    dataCurrent=measureCurrent(keithleyObject,voltagefixed/1000,nMeas,polarity = polar)
                    # currentden=1000*abs(mean(dataCurrent[:,1]))/pixarea
                    # current=abs(mean(dataCurrent[:,1]))
#                    currentden=-1000*mean(dataCurrent[:,1])/pixarea
#                    current=mean(dataCurrent[:,1])
                    currentden=1000*abs(mean(dataCurrent[:,1]))/pixarea
                    current=abs(mean(dataCurrent[:,1]))
                    
                    currentlist.append(current)
                    currentdensitylist.append(currentden)
                    voltagelist.append(voltagefixed)#/1000)
                    powerlist.append(currentden*voltagefixed/1000/Sunintensity)
                    timelist.append(float(elapsed_timer.elapsed()/1000))
                    steplist.append(step)
                    delaylist.append(delay)
                    
                    voltagefixed+=step
                    
                    while True:
                        step=self.ui.spinBox_MPPTstepsize.value()
                        delay=self.ui.doubleSpinBox_MPPTdelaypoints.value()
                        # if self.ui.checkBox_MPPTlighton.isChecked():
                        #     self.shutter('OpenShutter',keithleyObject)
                        # else:
                        #     self.shutter('CloseShutter',keithleyObject)
                        
                        
                        dataCurrent=measureCurrent(keithleyObject,voltagefixed/1000,nMeas,polarity = polar)
                        # currentden=1000*abs(mean(dataCurrent[:,1]))/pixarea
                        # current=abs(mean(dataCurrent[:,1]))
#                        currentden=-1000*mean(dataCurrent[:,1])/pixarea
                        currentden=1000*abs(mean(dataCurrent[:,1]))/pixarea
#                        current=mean(dataCurrent[:,1])
                        current=abs(mean(dataCurrent[:,1]))

                        currentlist.append(current)
                        currentdensitylist.append(currentden)
                        voltagelist.append(voltagefixed)#/1000)
                        powerlist.append(currentden*voltagefixed/1000/Sunintensity)
                        
                        timelist.append(float(elapsed_timer.elapsed()/1000))
                        steplist.append(step)
                        delaylist.append(delay)  
                        
                        self.ClearGraph('MPPT')
                        self.MPPTgraph_JV.plot(voltagelist,currentdensitylist, linestyle="solid",color=pixcolor)
                        self.MPPTgraph_TV.plot(timelist,voltagelist, linestyle="solid",color=pixcolor)
                        self.MPPTgraph_TJ.plot(timelist,currentdensitylist, linestyle="solid",color=pixcolor)
                        self.MPPTgraph_TP.plot(timelist,powerlist, linestyle="solid",color=pixcolor)
                        
                        # self.ui.MPPTpcelive.display(powerlist[-1])
                        self.ui.doubleSpinBox_MPPTpcelive.setValue(powerlist[-1])
                        
                        self.fig2.canvas.draw_idle()
                        self.fig2.canvas.flush_events()
                        
                        if abs(voltagefixed)>=abs(self.ui.doubleSpinBox_MPPTvoltagelimit.value()):
                            if voltagefixed>0:
                                voltagefixed-=step
                            else:
                                voltagefixed+=step
                        else:
                            if powerlist[-1]>powerlist[-2]:
                                if voltagelist[-1]>voltagelist[-2]:
                                    voltagefixed+=step
                                else:
                                    voltagefixed-=step
                            else:
                                if voltagelist[-1]>voltagelist[-2]:
                                    voltagefixed-=step
                                else:
                                    voltagefixed+=step
                        
                        QtTest.QTest.qWait(int(delay))
                        if duration !=-1:
                            if float(elapsed_timer.elapsed()/1000)>float(duration):
                                STOPMEASMPP=1
                        if STOPMEASMPP==1:#stops ongoing meas of pixel to pass to the next pixel
                            break
                        if STOPMEAS==1:#will stop all measurement and pass to the next step of sequence
                            break
                self.ClearGraph('MPPT')
                self.MPPTgraph_JV.plot(voltagelist,currentdensitylist, linestyle="solid",color=pixcolor)
                self.MPPTgraph_TV.plot(timelist,voltagelist, linestyle="solid",color=pixcolor)
                self.MPPTgraph_TJ.plot(timelist,currentdensitylist, linestyle="solid",color=pixcolor)
                self.MPPTgraph_TP.plot(timelist,powerlist, linestyle="solid",color=pixcolor)
                
                self.fig2.canvas.draw_idle()
                self.fig2.canvas.flush_events()
                
                QtTest.QTest.qWait(int(delay))
                
                # if keithleyAddress=='Test':
                #     QtTest.QTest.qWait(1000)#to be removed

                
                if STOPMEASMPP==1:#stops ongoing meas of pixel to pass to the next pixel
                    break
                if STOPMEAS==1:#will stop all measurement and pass to the next step of sequence
                    break
            
            if shutteropen:
                illum='lt'
            else:
                illum='dk'
            if self.ui.radioButton_Assume1sun.isChecked():
                radioButton_Assume1sun='True'
            else:
                radioButton_Assume1sun='False'
            timestr = QtCore.QDateTime.currentDateTime().toString(QtCore.Qt.ISODate)
            timestr=timestr.replace(':','').replace('-','')          

            sample=str(self.ui.lineEdit_SampleName.text()) +'_'+  'pX'+pixels[item] +'_'+ trackingtype +'_'+ illum +'_'+ 'lp'+str(Rep) +'_'+ timestr  
            samplename=str(self.ui.lineEdit_SampleName.text()).replace('-','_')
            if '_' in str(self.ui.lineEdit_SampleName.text()):
                Batch=str(self.ui.lineEdit_SampleName.text()).split('_')[0]
                Substrate=str(self.ui.lineEdit_SampleName.text()).split('_')[1]
            else:
                Batch='None'
                Substrate='None' 
            AlltrackingDATA[sample]={'sampleID': sample,'SampleNamePix': str(self.ui.lineEdit_SampleName.text()) +'_'+ pixels[item], 
                                     'linktorawdata':str(os.path.join(str(directory),sample+'.txt')),'SampleName': samplename,'Batch#':Batch,'Substrate#':Substrate,'Pixel':pixels[item],'Allpixs':allpixtobemeasured,
                                     'illum': illum, 'Sunintensity': Sunintensity, 'IsRefDiodeMeasured': RefDiodeChecked, 
                                     'RefDiodeNomCurr':self.ui.doubleSpinBox_DiodeNominalCurrent.value(),
                                     'RefDiodeMeasCurr':self.ui.doubleSpinBox_MeasuredDiodeCurrent.value(),
                                      'datetime': QtCore.QDateTime.currentDateTime(), 'Comment': str(self.ui.lineEdit_Comment.text()),'temperature':self.ui.doubleSpinBox_Temperature.value(),
                                      'UserName': str(self.ui.lineEdit_UserName.text()), 'MeasType': str(self.ui.comboBox_MeasType.currentText()),'MeasNowType': trackingtype,
                                      'RepNumb': Rep,'DelayRep':self.ui.spinBox_RepDelay.value(), 'pixelArea': pixarea,'assume1sun':radioButton_Assume1sun,'ShutterOpen':shutteropen,
                                      'InitialVoltage': initialvoltage, 'initialdelay':initialdelay,'initialstep':initialstep,'trackingtime': max(timelist),
                                      'step':steplist,'delay':delaylist,'Voltage':voltagelist,'Current':currentlist, 'CurrentDensity': currentdensitylist, 'time':timelist,'power':powerlist
                                      }
            lastmeastrackingDATA[sample]=AlltrackingDATA[sample]

            self.Savedata(sample,AlltrackingDATA)
            # self.loadtoDB(sample,AlltrackingDATA)
            
            if STOPMEAS==1:
                self.sequence=''
                break
        self.loadtoDB('MPP',lastmeasDATA,lastmeastrackingDATA) 
    
    # def StabProtocolThreaded(self, keithleyObject, pixels, pixcolorslist, scandirections, Rep):
    #     global STOPMEAS, AllDATA, lastmeasDATA,lastmeastrackingDATA, RefDiodeChecked, Sunintensity, shutteropen
    #     global aftermpp,boxCurrent, boxVoltage, keithleyAddress, exedirectory,latestVmpp
    #     self.pixels=pixels
    #     self.pixcolorslist=pixcolorslist
    #     self.scandirections=scandirections
    #     self.Rep=Rep
    #     latestVmpp=-99
    #     allpixtobemeasured=''
    #     for item in range(len(pixels)):
    #         allpixtobemeasured+=pixels[item]
    #         allpixtobemeasured+=', '
    #     self.allpixtobemeasured=allpixtobemeasured[:-2]
        
    #     year=str(QtCore.QDate.currentDate().toString(QtCore.Qt.ISODate).split('-')[0])
    #     month=calendar.month_name[int(QtCore.QDate.currentDate().toString(QtCore.Qt.ISODate).split('-')[1])]
    #     self.directory=os.path.join(exedirectory,'SolarSimAllUsersDATA',str(self.ui.lineEdit_UserName.text()),year,month)
    #     if not os.path.exists(self.directory):
    #         os.makedirs(self.directory)
    #         os.chdir(self.directory)
    #     else :
    #         os.chdir(self.directory)
    #     QtTest.QTest.qWait(200)
    #     self.keithleyObject=keithleyObject
    #     self.thread = ThreadStabProtocol(pixels,scandirections, keithleyObject)
    #     self.thread.result.connect(self.StabProtocolThreadedUpdategraph)
    #     self.thread.finished.connect(self.StabProtocolThreadedFinished)
    #     self.thread.start()
        
    # def StabProtocolThreadedFinished(self):
    #     global STOPMEAS, AllDATA, lastmeasDATA,lastmeastrackingDATA, RefDiodeChecked, Sunintensity, shutteropen
    #     global aftermpp,boxCurrent, boxVoltage, keithleyAddress
    #     pixels=self.pixels
    #     pixcolorslist=self.pixcolorslist
    #     scandirections=self.scandirections
    #     Rep=self.Rep
    #     directory=self.directory
    #     allpixtobemeasured=self.allpixtobemeasured
    #     keithleyObject=self.keithleyObject
        
    #     print('finished')
        
    #     # update final graph
    #     # compile the report
    #     # export all data, graph and report in one folder
        
        
    #     if  self.sequence=='':
    #         if self.ui.checkBox_MPPTlightonafter.isChecked():
    #             self.shutter('OpenShutter',keithleyObject)
    #         else:
    #             self.shutter('CloseShutter',keithleyObject)
    #     # try:
    #     #     self.loadtoDB('IV',lastmeasDATA,lastmeastrackingDATA)
    #     # except Exception as e: print(e)
        
    #     self.SaveSession()
    #     self.launchSequence(keithleyObject, pixels, pixcolorslist, scandirections, Rep)
        
    # def StabProtocolThreadedUpdategraph(self,data):
    #     global version,STOPMEAS, AllDATA, lastmeasDATA,lastmeastrackingDATA, RefDiodeChecked, Sunintensity, shutteropen
    #     global aftermpp,boxCurrent, boxVoltage, keithleyAddress,latestVmpp
    #     pixels=self.pixels
    #     pixcolorslist=self.pixcolorslist
    #     scandirections=self.scandirections
    #     Rep=self.Rep
    #     directory=self.directory
    #     allpixtobemeasured=self.allpixtobemeasured
    #     keithleyObject=self.keithleyObject
        
    #     direction=data[0]
    #     item=data[1]
    #     data=data[2]
        
    #     pixcolor=pixcolorslist[item]
        
    #     print('update')
    #     # print(data)
    #     if version != '1pixel': 
    #         pixarea=eval('window.w.ui.doubleSpinBox_pix'+pixels[item]+'area.value()')
    #     else:
    #         pixarea=window.w.ui.doubleSpinBox_pixXarea.value()
    #     currentlist=data[:,1]
    #     voltagelist=data[:,0]
    #     currentdenlist=[x*1000/pixarea for x in data[:,1]] #assume 1sun, and assume keithley gives Amperes back 
         
    #     if direction == 1:#forward scan 
    #         directionstr='fwd' 
    #         self.StabGraph1.plot(data[:,0],currentdenlist, linestyle="dashed",color=pixcolor) 
    #     elif direction == 0:#reverse scan 
    #         directionstr='rev' 
    #         self.StabGraph1.plot(data[:,0],currentdenlist, linestyle="solid",color=pixcolor) 
    #     self.fig5.canvas.draw_idle() 
    #     self.fig5.canvas.flush_events()
         
    #     illum='lt'
        
    #     if self.ui.radioButton_Assume1sun.isChecked():
    #         radioButton_Assume1sun='True'
    #     else:
    #         radioButton_Assume1sun='False'
    #     timestr = QtCore.QDateTime.currentDateTime().toString(QtCore.Qt.ISODate)
    #     timestr=timestr.replace(':','').replace('-','')

    #     sample=str(self.ui.lineEdit_SampleName.text()) +'_'+  'pX'+pixels[item] +'_'+ directionstr +'_'+ illum +'_'+ 'lp'+str(Rep) +'_'+ timestr
    #     samplename=str(self.ui.lineEdit_SampleName.text()).replace('-','_')
    #     if '_' in str(self.ui.lineEdit_SampleName.text()):
    #         Batch=str(self.ui.lineEdit_SampleName.text()).split('_')[0]
    #         Substrate=str(self.ui.lineEdit_SampleName.text()).split('_')[1]
    #     else:
    #         Batch='None'
    #         Substrate='None'
        
    #     commenttext=str(self.ui.lineEdit_Comment.text())
    #     if self.ui.checkBox_aftermpp.isChecked():
    #         aftermpp=1
    #     if aftermpp:
    #         if 'aftermpp' not in commenttext:
    #             commenttext+='_aftermpp'
    #     polarity='pin'
    #     if self.ui.radioButton_nip.isChecked():
    #         polarity='nip'
    #     AllDATA[sample]={'sampleID': sample,'SampleNamePix': str(self.ui.lineEdit_SampleName.text()) +'_'+ pixels[item], 
    #                       'linktorawdata':str(os.path.join(str(directory),sample+'.txt')),'SampleName': samplename,'Batch#':Batch,'Substrate#':Substrate, 'Pixel':pixels[item], 'Allpixs':allpixtobemeasured,
    #                       'ScanDirection': directionstr, 'illum': illum, 'Sunintensity': Sunintensity, 'IsRefDiodeMeasured': RefDiodeChecked, 
    #                       'RefDiodeNomCurr':self.ui.doubleSpinBox_DiodeNominalCurrent.value(),'RefDiodeMeasCurr':self.ui.doubleSpinBox_MeasuredDiodeCurrent.value(),
    #                       'datetime': QtCore.QDateTime.currentDateTime(), 'Comment': commenttext,'temperature':self.ui.doubleSpinBox_Temperature.value(),
    #                       'UserName': str(self.ui.lineEdit_UserName.text()), 'MeasType': str(self.ui.comboBox_MeasType.currentText()),'MeasNowType': 'IV',
    #                       'pixcolor':pixcolor,'RepNumb': Rep,'DelayRep':self.ui.spinBox_RepDelay.value(), 'pixelArea': pixarea,'assume1sun':radioButton_Assume1sun,'ShutterOpen':shutteropen,
    #                       'MinVoltage': self.ui.doubleSpinBox_JVminvoltage.value(), 'MaxVoltage': self.ui.doubleSpinBox_JVmaxvoltage.value(),
    #                       'Aftermpp':aftermpp,'StepSize': self.ui.doubleSpinBox_JVstepsize.value(), 'CurrentLimit': self.ui.doubleSpinBox_JVcurrentlimit.value(), 
    #                       'IntegTime': self.ui.doubleSpinBox_JVintegrationtime.value(), 'Delaypts': self.ui.doubleSpinBox_JVdelaypoints.value(), 
    #                       'DelayShutter': self.ui.doubleSpinBox_JVdelayshutter.value(),'polarity':polarity,
    #                       'Voc': -1., 'Jsc': -1., 'Isc': -1., 'FF': -1., 'Eff': -1, 'Pmpp': -1., 'Roc':-1., 'Rsc':-1., 'Jmpp':-1, 'Vmpp':-1,
    #                       'Voltage':voltagelist,'Current':currentlist, 'CurrentDensity': currentdenlist
    #                       }
    #     lastmeasDATA[sample]=AllDATA[sample]
        
    #     self.AnalysisJV(sample)
    #     self.Savedata(sample,AllDATA)
    #     self.UpdateTable(lastmeasDATA)
    #     latestVmpp=lastmeasDATA[sample]['Vmpp']
    #     print('from the resultsupdate function: ', latestVmpp)

    def PlotQSSThreaded(self, keithleyObject, pixels, pixcolorslist, scandirections, Rep):
        global STOPMEAS, AllDATA, lastmeasDATA,lastmeastrackingDATA, RefDiodeChecked, Sunintensity, shutteropen
        global aftermpp,boxCurrent, boxVoltage, keithleyAddress, exedirectory
        self.pixels=pixels
        self.pixcolorslist=pixcolorslist
        self.scandirections=scandirections
        self.Rep=Rep
        
        self.SaveSession()
        
        allpixtobemeasured=''
        for item in range(len(pixels)):
            allpixtobemeasured+=pixels[item]
            allpixtobemeasured+=', '
        self.allpixtobemeasured=allpixtobemeasured[:-2]
        self.ClearGraph('QSS_Stab')
        year=str(QtCore.QDate.currentDate().toString(QtCore.Qt.ISODate).split('-')[0])
        month=calendar.month_name[int(QtCore.QDate.currentDate().toString(QtCore.Qt.ISODate).split('-')[1])]
        self.directory=os.path.join(exedirectory,'SolarSimAllUsersDATA',str(self.ui.lineEdit_UserName.text()),year,month)
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)
            os.chdir(self.directory)
        else :
            os.chdir(self.directory)
        QtTest.QTest.qWait(200)
        self.keithleyObject=keithleyObject
        self.thread = ThreadtakeQSS(pixels,scandirections, keithleyObject)
        # self.thread.result.connect(self.PlotQSSThreadedUpdategraph)
        self.thread.finished.connect(self.PlotQSSThreadedFinished)
        self.thread.start()
        
    def PlotQSSThreadedFinished(self,data):
        global STOPMEAS, AllDATA, lastmeasDATA,lastmeastrackingDATA, RefDiodeChecked, Sunintensity, shutteropen
        global aftermpp,boxCurrent, boxVoltage, keithleyAddress
        pixels=self.pixels
        pixcolorslist=self.pixcolorslist
        scandirections=self.scandirections
        Rep=self.Rep
        directory=self.directory
        allpixtobemeasured=self.allpixtobemeasured
        keithleyObject=self.keithleyObject
        
        direction=data[0]
        item=data[1]
        data=data[2]
        directionstr='rev'
        pixcolor='black'
        pixarea=self.ui.doubleSpinBox_pixXarea.value()
        
        currentlist=data[2]
        currentdenlist=data[1]
        voltagelist=data[0]
        timelist=data[3]
        currentstablist=data[4]
        currentdensitystablist=data[5]
        voltagestablist=data[6]
        powerstablist=data[7]
        notstabilizedlist=data[8]
        illum='lt' 
        
        if self.ui.radioButton_Assume1sun.isChecked():
            radioButton_Assume1sun='True'
        else:
            radioButton_Assume1sun='False'
        timestr = QtCore.QDateTime.currentDateTime().toString(QtCore.Qt.ISODate)
        timestr=timestr.replace(':','').replace('-','')

        sample=str(self.ui.lineEdit_SampleName.text()) +'_'+  'pX'+pixels[item] +'_'+ directionstr +'_'+ illum +'_'+ 'lp'+str(Rep) +'_'+ timestr  
        samplename=str(self.ui.lineEdit_SampleName.text()).replace('-','_')
        if '_' in str(self.ui.lineEdit_SampleName.text()):
            Batch=str(self.ui.lineEdit_SampleName.text()).split('_')[0]
            Substrate=str(self.ui.lineEdit_SampleName.text()).split('_')[1]
        else:
            Batch='None'
            Substrate='None'
            
        commenttext=str(self.ui.lineEdit_Comment.text())
        if self.ui.checkBox_aftermpp.isChecked():
            aftermpp=1
        if aftermpp:
            if 'aftermpp' not in commenttext:
                commenttext+='_aftermpp'
        polarity='pin'
        if not self.ui.checkBox_pin.isChecked():
            polarity='nip'
        AllDATA[sample]={'sampleID': sample,'SampleNamePix': str(self.ui.lineEdit_SampleName.text()) +'_'+ pixels[item], 
                          'linktorawdata':str(os.path.join(str(directory),sample+'.txt')),'SampleName': samplename,'Batch#':Batch,'Substrate#':Substrate, 'Pixel':pixels[item], 'Allpixs':allpixtobemeasured,
                          'ScanDirection': directionstr, 'illum': illum, 'Sunintensity': Sunintensity, 'IsRefDiodeMeasured': RefDiodeChecked, 
                          'RefDiodeNomCurr':self.ui.doubleSpinBox_DiodeNominalCurrent.value(),'RefDiodeMeasCurr':self.ui.doubleSpinBox_MeasuredDiodeCurrent.value(),
                          'datetime': QtCore.QDateTime.currentDateTime(), 'Comment': commenttext,'temperature':self.ui.doubleSpinBox_Temperature.value(),
                          'UserName': str(self.ui.lineEdit_UserName.text()), 'MeasType': str(self.ui.comboBox_MeasType.currentText()),'MeasNowType': 'QSS',
                          'pixcolor':pixcolor,'RepNumb': Rep,'DelayRep':self.ui.spinBox_RepDelay.value(), 'pixelArea': pixarea,'assume1sun':radioButton_Assume1sun,'ShutterOpen':shutteropen,
                          'MinVoltage': self.ui.doubleSpinBox_JVminvoltage.value(), 'MaxVoltage': self.ui.doubleSpinBox_JVmaxvoltage.value(),
                          'Aftermpp':aftermpp,'StepSize': self.ui.doubleSpinBox_JVstepsize.value(), 'CurrentLimit': self.ui.doubleSpinBox_JVcurrentlimit.value(), 
                          'IntegTime': self.ui.doubleSpinBox_JVintegrationtime.value(), 'Delaypts': self.ui.doubleSpinBox_JVdelaypoints.value(), 
                          'DelayShutter': self.ui.doubleSpinBox_JVdelayshutter.value(),'polarity':polarity,
                          'QSSnbpts':self.ui.doubleSpinBox_QSS_Nbpts.value(),'QSSdensity':self.ui.spinBox_QSS_mppptsdensity.value(),
                          'QSSdevcrit':self.ui.doubleSpinBox_QSS_DevCrit.value(),'QSSTdev':self.ui.doubleSpinBox_QSS_TimeDev.value(),
                          'QSSmaxdur':self.ui.doubleSpinBox_QSS_TimeMax4Fail.value(),
                          'Voc': voltagelist[0]*1000, 'Jsc': abs(currentdenlist[-1]), 'Isc': abs(currentlist[-1]), 'FF': -1., 'Eff': -1, 'Pmpp': -1., 'Roc':-1., 'Rsc':-1., 'Jmpp':-1, 'Vmpp':-1,
                          'Voltage':voltagelist,'Current':currentlist, 'CurrentDensity': currentdenlist,
                          'timelist':timelist,'currentstablist':currentstablist, 'currentdensitystablist': currentdensitystablist,
                          'voltagestablist':voltagestablist,'powerstablist':powerstablist, 'notstabilizedlist': notstabilizedlist
                          }
        lastmeasDATA[sample]=AllDATA[sample]
        QtTest.QTest.qWait(200)
        self.AnalysisJV(sample)
        if len(AllDATA[sample]['Voltage'])==len(AllDATA[sample]['CurrentDensity']) and len(AllDATA[sample]['Voltage'])==len(AllDATA[sample]['Current']) and len(AllDATA[sample]['Voltage'])==len(AllDATA[sample]['notstabilizedlist']):
            self.Savedata(sample,AllDATA)
        self.UpdateTable(lastmeasDATA)
        aftermpp=1
        self.ui.checkBox_aftermpp.setChecked(True)
        thissequencestep=self.sequence.split('-')[0]
        self.sequence=self.sequence[4:]
        
        if  self.sequence=='':
            if self.ui.checkBox_MPPTlightonafter.isChecked() and thissequencestep=='LIV':
                self.shutter('OpenShutter',keithleyObject)
            else:
                self.shutter('CloseShutter',keithleyObject)
        try:
            self.loadtoDB('IV',lastmeasDATA,lastmeastrackingDATA)
        except Exception as e: self.ui.textEdit_Keithley.append(QtCore.QDateTime.currentDateTime().toString()+': '+str(e))
        self.SaveSession()
        self.launchSequence(keithleyObject, pixels, pixcolorslist, scandirections, Rep)
        
        
    def PlotIVThreaded(self, keithleyObject, pixels, pixcolorslist, scandirections, Rep):
        global STOPMEAS, AllDATA, lastmeasDATA,lastmeastrackingDATA, RefDiodeChecked, Sunintensity, shutteropen
        global aftermpp,boxCurrent, boxVoltage, keithleyAddress, exedirectory, lastJVscansVmpp
        self.pixels=pixels
        self.pixcolorslist=pixcolorslist
        self.scandirections=scandirections
        self.Rep=Rep
        lastJVscansVmpp=[]
        
        self.SaveSession()
        
        allpixtobemeasured=''
        for item in range(len(pixels)):
            allpixtobemeasured+=pixels[item]
            allpixtobemeasured+=', '
        self.allpixtobemeasured=allpixtobemeasured[:-2]
        if self.sequence.split('-')[0]=='LIV':
            self.ClearGraph('LIV')
            if str(self.ui.comboBox_MeasType.currentText())=='LIV-QSS-LIV' and len(self.sequence.split('-'))==3:
                self.ClearGraph('QSS')
        elif self.sequence.split('-')[0]=='DIV':
            self.ClearGraph('DIV')

        year=str(QtCore.QDate.currentDate().toString(QtCore.Qt.ISODate).split('-')[0])
        month=calendar.month_name[int(QtCore.QDate.currentDate().toString(QtCore.Qt.ISODate).split('-')[1])]
        self.directory=os.path.join(exedirectory,'SolarSimAllUsersDATA',str(self.ui.lineEdit_UserName.text()),year,month)
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)
            os.chdir(self.directory)
        else :
            os.chdir(self.directory)
        QtTest.QTest.qWait(200)
        self.keithleyObject=keithleyObject
        self.thread = ThreadtakeIV(pixels,scandirections, keithleyObject)
        self.thread.result.connect(self.PlotIVThreadedUpdategraph)
        self.thread.finished.connect(self.PlotIVThreadedFinished)
        self.thread.start()
    
    def PlotIVThreadedFinished(self):
        global STOPMEAS, AllDATA, lastmeasDATA,lastmeastrackingDATA, RefDiodeChecked, Sunintensity, shutteropen
        global aftermpp,boxCurrent, boxVoltage, keithleyAddress, lastJVscansVmpp
        pixels=self.pixels
        pixcolorslist=self.pixcolorslist
        scandirections=self.scandirections
        Rep=self.Rep
        directory=self.directory
        allpixtobemeasured=self.allpixtobemeasured
        keithleyObject=self.keithleyObject
        if self.sequence.split('-')[0]=='LIV':
            self.ClearGraph('LIV')
        elif self.sequence.split('-')[0]=='DIV':
            self.ClearGraph('DIV')
        QSSestimatedVmpp=0
        QSSestimatedVoc=0
        QSSestimatedJsc=0
        
        if self.ui.comboBox_JV_ptsorline.currentText() == 'Dots and Line':
            markerJV='o'
        elif self.ui.comboBox_JV_ptsorline.currentText() == 'Line':
            markerJV=''
        for sampleitem in lastmeasDATA.keys():
            if lastmeasDATA[sampleitem]['MeasNowType']!='QSS':
                pixcoloritem=lastmeasDATA[sampleitem]['pixcolor']
                if self.sequence.split('-')[0]=='LIV':
                    if str(self.ui.comboBox_MeasType.currentText())=='LIV-QSS-LIV' and len(self.sequence.split('-'))==3:
                        QSSestimatedVmpp+=lastmeasDATA[sampleitem]['Vmpp']
                        QSSestimatedVoc+=lastmeasDATA[sampleitem]['Voc']
                        QSSestimatedJsc+=lastmeasDATA[sampleitem]['Jsc']
                        if lastmeasDATA[sampleitem]['ScanDirection'] == 'fwd':#forward scan
                            self.QSSgraphIV.plot(lastmeasDATA[sampleitem]['Voltage'],lastmeasDATA[sampleitem]['CurrentDensity'], linestyle="dashed",color='black')
                        elif lastmeasDATA[sampleitem]['ScanDirection'] == 'rev':#reverse scan
                            self.QSSgraphIV.plot(lastmeasDATA[sampleitem]['Voltage'],lastmeasDATA[sampleitem]['CurrentDensity'], linestyle="solid",color='black')
                    if str(self.ui.comboBox_MeasType.currentText())=='LIV-QSS-LIV' and len(self.sequence.split('-'))==1 and lastmeasDATA[sampleitem]['Aftermpp']==0:
                        if lastmeasDATA[sampleitem]['ScanDirection'] == 'fwd':#forward scan
                            self.QSSgraphIV.plot(lastmeasDATA[sampleitem]['Voltage'],lastmeasDATA[sampleitem]['CurrentDensity'], linestyle="dashed",color='black')
                        elif lastmeasDATA[sampleitem]['ScanDirection'] == 'rev':#reverse scan
                            self.QSSgraphIV.plot(lastmeasDATA[sampleitem]['Voltage'],lastmeasDATA[sampleitem]['CurrentDensity'], linestyle="solid",color='black')
                    elif str(self.ui.comboBox_MeasType.currentText())=='LIV-QSS-LIV' and len(self.sequence.split('-'))==1 and lastmeasDATA[sampleitem]['Aftermpp']==1:
                        if lastmeasDATA[sampleitem]['ScanDirection'] == 'fwd':#forward scan
                            self.QSSgraphIV.plot(lastmeasDATA[sampleitem]['Voltage'],lastmeasDATA[sampleitem]['CurrentDensity'], linestyle="dashed",color='grey')
                        elif lastmeasDATA[sampleitem]['ScanDirection'] == 'rev':#reverse scan
                            self.QSSgraphIV.plot(lastmeasDATA[sampleitem]['Voltage'],lastmeasDATA[sampleitem]['CurrentDensity'], linestyle="solid",color='grey')
                    else:
                        if lastmeasDATA[sampleitem]['ScanDirection'] == 'fwd':#forward scan
                            self.JVgraph.plot(lastmeasDATA[sampleitem]['Voltage'],lastmeasDATA[sampleitem]['CurrentDensity'],marker=markerJV, linestyle="dashed",color=pixcoloritem)
                        elif lastmeasDATA[sampleitem]['ScanDirection'] == 'rev':#reverse scan
                            self.JVgraph.plot(lastmeasDATA[sampleitem]['Voltage'],lastmeasDATA[sampleitem]['CurrentDensity'],marker=markerJV, linestyle="solid",color=pixcoloritem)
                        
                        if self.ui.spinBox_RepNumb.value()>1:
                            if self.ui.comboBox_Time_IVplots.currentText()=='J vs V':
                                self.TimegraphIV.set_xlabel('Voltage (V)')
                                self.TimegraphIV.set_ylabel('Current density (mA/cm'+'\xb2'+')')
                                if lastmeasDATA[sampleitem]['ScanDirection'] == 'fwd':#forward scan
                                    self.TimegraphIV.plot(lastmeasDATA[sampleitem]['Voltage'],lastmeasDATA[sampleitem]['CurrentDensity'],marker=markerJV, linestyle="dashed",color=pixcoloritem)
                                elif lastmeasDATA[sampleitem]['ScanDirection'] == 'rev':#reverse scan
                                    self.TimegraphIV.plot(lastmeasDATA[sampleitem]['Voltage'],lastmeasDATA[sampleitem]['CurrentDensity'],marker=markerJV, linestyle="solid",color=pixcoloritem)
                            else:
                                self.TimegraphIV.set_xlabel('Voltage (V)')
                                self.TimegraphIV.set_ylabel('Power density (mW/cm'+'\xb2'+')')
                                if lastmeasDATA[sampleitem]['ScanDirection'] == 'fwd':#forward scan
                                    self.TimegraphIV.plot(lastmeasDATA[sampleitem]['Voltage'],lastmeasDATA[sampleitem]['PowerDensity'],marker=markerJV, linestyle="dashed",color=pixcoloritem)
                                elif lastmeasDATA[sampleitem]['ScanDirection'] == 'rev':#reverse scan
                                    self.TimegraphIV.plot(lastmeasDATA[sampleitem]['Voltage'],lastmeasDATA[sampleitem]['PowerDensity'],marker=markerJV, linestyle="solid",color=pixcoloritem)
                            
                
                # if lastmeasDATA[sampleitem]['illum'] == 'dk':
                elif self.sequence.split('-')[0]=='DIV':
                    if lastmeasDATA[sampleitem]['ScanDirection'] == 'fwd':#forward scan
                        self.DIVgraphlin.plot(lastmeasDATA[sampleitem]['Voltage'],lastmeasDATA[sampleitem]['CurrentDensity'], linestyle="dashed",color=pixcoloritem)
                    elif lastmeasDATA[sampleitem]['ScanDirection'] == 'rev':#reverse scan
                        self.DIVgraphlin.plot(lastmeasDATA[sampleitem]['Voltage'],lastmeasDATA[sampleitem]['CurrentDensity'], linestyle="solid",color=pixcoloritem)
                    ydataabs=list(map(lambda x: abs(x),lastmeasDATA[sampleitem]['CurrentDensity']))
                    if lastmeasDATA[sampleitem]['ScanDirection'] == 'fwd':#forward scan
                        self.DIVgraphlogY.semilogy(lastmeasDATA[sampleitem]['Voltage'],ydataabs, linestyle="dashed",color=pixcoloritem)
                    elif lastmeasDATA[sampleitem]['ScanDirection'] == 'rev':#reverse scan
                        self.DIVgraphlogY.semilogy(lastmeasDATA[sampleitem]['Voltage'],ydataabs, linestyle="solid",color=pixcoloritem)
        if str(self.ui.comboBox_MeasType.currentText())=='LIV-QSS-LIV' and len(self.sequence.split('-'))==1 and lastmeasDATA[sampleitem]['Aftermpp']==1:
            aftermpp=0
            self.ui.checkBox_aftermpp.setChecked(False)
        if str(self.ui.comboBox_MeasType.currentText())=='LIV-QSS-LIV' and len(self.sequence.split('-'))==3:
            QSSestimatedVmpp=QSSestimatedVmpp/len(lastmeasDATA.keys())
            QSSestimatedVoc=QSSestimatedVoc/len(lastmeasDATA.keys())
            QSSestimatedJsc=QSSestimatedJsc/len(lastmeasDATA.keys())
            self.ui.doubleSpinBox_QSS_VmppEstim.setValue(QSSestimatedVmpp)
            self.ui.doubleSpinBox_QSS_VocEstim.setValue(QSSestimatedVoc)
            self.ui.doubleSpinBox_QSS_JscEstim.setValue(QSSestimatedJsc)
            
        thissequencestep=self.sequence.split('-')[0]
        self.JVgraph.relim()
        self.JVgraph.autoscale_view()
        self.fig1.canvas.draw_idle()
        self.fig1.canvas.flush_events()
        self.fig3.canvas.draw_idle()
        self.fig3.canvas.flush_events()
        self.fig6.canvas.draw_idle()
        self.fig6.canvas.flush_events()
        self.fig7.canvas.draw_idle()
        self.fig7.canvas.flush_events()
        self.sequence=self.sequence[4:]
        if  self.sequence=='':
            if self.ui.checkBox_MPPTlightonafter.isChecked() and thissequencestep=='LIV':
                self.shutter('OpenShutter',keithleyObject)
            else:
                self.shutter('CloseShutter',keithleyObject)
        try:
            self.loadtoDB('IV',lastmeasDATA,lastmeastrackingDATA)
        except Exception as e: self.ui.textEdit_Keithley.append(QtCore.QDateTime.currentDateTime().toString()+': '+str(e))
        
        self.SaveSession()
        self.launchSequence(keithleyObject, pixels, pixcolorslist, scandirections, Rep)
        
        
    def PlotIVThreadedUpdategraph(self,data):
        global version,STOPMEAS, AllDATA, lastmeasDATA,lastmeastrackingDATA, RefDiodeChecked, Sunintensity, shutteropen
        global aftermpp,boxCurrent, boxVoltage, keithleyAddress, lastJVscansVmpp
        pixels=self.pixels
        pixcolorslist=self.pixcolorslist
        scandirections=self.scandirections
        Rep=self.Rep
        directory=self.directory
        allpixtobemeasured=self.allpixtobemeasured
        keithleyObject=self.keithleyObject
        
        direction=data[0]
        item=data[1]
        data=data[2]
        illum='lt' 
        
        pixcolor=pixcolorslist[item]
        if direction:
            directionstr='fwd'
        else:
            directionstr='rev'
            
        if version != '1pixel': 
            pixarea=eval('self.ui.doubleSpinBox_pix'+pixels[item]+'area.value()')
        else:
            pixarea=self.ui.doubleSpinBox_pixXarea.value()
        currentlist=data[:,1]
        voltagelist=data[:,0]
        currentdenlist=[x*1000/pixarea for x in data[:,1]] #assume 1sun, and assume keithley gives Amperes back 
        powerdenlist=[voltagelist[x]*currentdenlist[x] for x in range(len(currentdenlist))]

        if self.ui.comboBox_JV_ptsorline.currentText() == 'Dots and Line':
            markerJV='o'
        elif self.ui.comboBox_JV_ptsorline.currentText() == 'Line':
            markerJV=''
        if str(self.ui.comboBox_MeasType.currentText())=='LIV-QSS-LIV' and len(self.sequence.split('-'))==3:
            if direction == 1:#forward scan 
                self.QSSgraphIV.plot(data[:,0],currentdenlist,marker=markerJV, linestyle="dashed",color=pixcolor)
            elif direction == 0:#reverse scan 
                self.QSSgraphIV.plot(data[:,0],currentdenlist,marker=markerJV, linestyle="solid",color=pixcolor)
            self.fig6.canvas.draw_idle() 
            self.fig6.canvas.flush_events()
        else:
            if direction == 1:#forward scan 
                self.JVgraph.plot(data[:,0],currentdenlist,marker=markerJV, linestyle="dashed",color=pixcolor)
            elif direction == 0:#reverse scan 
                self.JVgraph.plot(data[:,0],currentdenlist,marker=markerJV, linestyle="solid",color=pixcolor)
            self.JVgraph.relim()
            self.JVgraph.autoscale_view()
            self.fig1.canvas.draw_idle() 
            self.fig1.canvas.flush_events()
        if self.sequence.split('-')[0]=='LIV':
            illum='lt' 
        elif self.sequence.split('-')[0]=='DIV':
            illum='dk' 
        # if shutteropen: 
        #     illum='lt' 
        # else: 
        #     illum='dk' 
        if illum == 'dk': 
            if direction == 1:#forward scan 
                self.DIVgraphlin.plot(data[:,0],currentdenlist, linestyle="dashed",color=pixcolor) 
            elif direction == 0:#reverse scan 
                self.DIVgraphlin.plot(data[:,0],currentdenlist, linestyle="solid",color=pixcolor) 
            ydataabs=list(map(lambda x: abs(x),currentdenlist)) 
            if direction == 1:#forward scan 
                self.DIVgraphlogY.semilogy(data[:,0],ydataabs, linestyle="dashed",color=pixcolor) 
            elif direction == 0:#reverse scan 
                self.DIVgraphlogY.semilogy(data[:,0],ydataabs, linestyle="solid",color=pixcolor) 
            self.fig3.canvas.draw_idle() 
            self.fig3.canvas.flush_events() 
        
        if self.ui.radioButton_Assume1sun.isChecked():
            radioButton_Assume1sun='True'
        else:
            radioButton_Assume1sun='False'
        timestr = QtCore.QDateTime.currentDateTime().toString(QtCore.Qt.ISODate)
        timestr=timestr.replace(':','').replace('-','')

        sample=str(self.ui.lineEdit_SampleName.text()) +'_'+  'pX'+pixels[item] +'_'+ directionstr +'_'+ illum +'_'+ 'lp'+str(Rep) +'_'+ timestr  
        samplename=str(self.ui.lineEdit_SampleName.text()).replace('-','_')
        if '_' in str(self.ui.lineEdit_SampleName.text()):
            Batch=str(self.ui.lineEdit_SampleName.text()).split('_')[0]
            Substrate=str(self.ui.lineEdit_SampleName.text()).split('_')[1]
        else:
            Batch='None'
            Substrate='None'
        
        commenttext=str(self.ui.lineEdit_Comment.text())
        if self.ui.checkBox_aftermpp.isChecked():
            aftermpp=1
        if aftermpp:
            if 'aftermpp' not in commenttext:
                commenttext+='_aftermpp'
        polarity='pin'
        if not self.ui.checkBox_pin.isChecked():
            polarity='nip'
        AllDATA[sample]={'sampleID': sample,'SampleNamePix': str(self.ui.lineEdit_SampleName.text()) +'_'+ pixels[item], 
                          'linktorawdata':str(os.path.join(str(directory),sample+'.txt')),'SampleName': samplename,'Batch#':Batch,'Substrate#':Substrate, 'Pixel':pixels[item], 'Allpixs':allpixtobemeasured,
                          'ScanDirection': directionstr, 'illum': illum, 'Sunintensity': Sunintensity, 'IsRefDiodeMeasured': RefDiodeChecked, 
                          'RefDiodeNomCurr':self.ui.doubleSpinBox_DiodeNominalCurrent.value(),'RefDiodeMeasCurr':self.ui.doubleSpinBox_MeasuredDiodeCurrent.value(),
                          'datetime': QtCore.QDateTime.currentDateTime(), 'Comment': commenttext,'temperature':self.ui.doubleSpinBox_Temperature.value(),
                          'UserName': str(self.ui.lineEdit_UserName.text()), 'MeasType': str(self.ui.comboBox_MeasType.currentText()),'MeasNowType': 'IV',
                          'pixcolor':pixcolor,'RepNumb': Rep,'DelayRep':self.ui.spinBox_RepDelay.value(), 'pixelArea': pixarea,'assume1sun':radioButton_Assume1sun,'ShutterOpen':shutteropen,
                          'MinVoltage': self.ui.doubleSpinBox_JVminvoltage.value(), 'MaxVoltage': self.ui.doubleSpinBox_JVmaxvoltage.value(),
                          'Aftermpp':aftermpp,'StepSize': self.ui.doubleSpinBox_JVstepsize.value(), 'CurrentLimit': self.ui.doubleSpinBox_JVcurrentlimit.value(), 
                          'IntegTime': self.ui.doubleSpinBox_JVintegrationtime.value(), 'Delaypts': self.ui.doubleSpinBox_JVdelaypoints.value(), 
                          'DelayShutter': self.ui.doubleSpinBox_JVdelayshutter.value(),'polarity':polarity,
                          'Voc': -1., 'Jsc': -1., 'Isc': -1., 'FF': -1., 'Eff': -1, 'Pmpp': -1., 'Roc':-1., 'Rsc':-1., 'Jmpp':-1, 'Vmpp':-1,
                          'Voltage':voltagelist,'Current':currentlist, 'CurrentDensity': currentdenlist, 'PowerDensity':powerdenlist
                          }
        lastmeasDATA[sample]=AllDATA[sample]
        self.AnalysisJV(sample)
        self.Savedata(sample,AllDATA)
        self.UpdateTable(lastmeasDATA)
        
        lastJVscansVmpp.append(AllDATA[sample]['Vmpp'])
        if self.ui.spinBox_RepNumb.value()>1:
            if self.ui.comboBox_Time_timeplots.currentText()=='Eff vs Time':
                self.TimegraphStab.set_xlabel('Time')
                self.TimegraphStab.set_ylabel('Efficiency')
                if AllDATA[sample]['ScanDirection'] == 'fwd':#forward scan
                    self.TimegraphStab.plot(AllDATA[sample]['datetime'].toPyDateTime(),AllDATA[sample]['Eff'],'o',color='black')
                elif lastmeasDATA[sample]['ScanDirection'] == 'rev':#reverse scan
                    self.TimegraphStab.plot(AllDATA[sample]['datetime'].toPyDateTime(),AllDATA[sample]['Eff'],'o',color='gray')#.toString('hh:mm:ss, d/MM')
            elif self.ui.comboBox_Time_timeplots.currentText()=='Voc vs Time':
                self.TimegraphStab.set_xlabel('Time')
                self.TimegraphStab.set_ylabel('Voc')
                if AllDATA[sample]['ScanDirection'] == 'fwd':#forward scan
                    self.TimegraphStab.plot(AllDATA[sample]['datetime'].toPyDateTime(),AllDATA[sample]['Voc'],'o',color='black')
                elif lastmeasDATA[sample]['ScanDirection'] == 'rev':#reverse scan
                    self.TimegraphStab.plot(AllDATA[sample]['datetime'].toPyDateTime(),AllDATA[sample]['Voc'], 'o',color='gray')
            elif self.ui.comboBox_Time_timeplots.currentText()=='Jsc vs Time':
                self.TimegraphStab.set_xlabel('Time')
                self.TimegraphStab.set_ylabel('Jsc')
                if AllDATA[sample]['ScanDirection'] == 'fwd':#forward scan
                    self.TimegraphStab.plot(AllDATA[sample]['datetime'].toPyDateTime(),AllDATA[sample]['Jsc'],'o',color='black')
                elif lastmeasDATA[sample]['ScanDirection'] == 'rev':#reverse scan
                    self.TimegraphStab.plot(AllDATA[sample]['datetime'].toPyDateTime(),AllDATA[sample]['Jsc'],'o',color='gray')
            elif self.ui.comboBox_Time_timeplots.currentText()=='FF vs Time':
                self.TimegraphStab.set_xlabel('Time')
                self.TimegraphStab.set_ylabel('FF')
                if AllDATA[sample]['ScanDirection'] == 'fwd':#forward scan
                    self.TimegraphStab.plot(AllDATA[sample]['datetime'].toPyDateTime(),AllDATA[sample]['FF'],'o',color='black')
                elif lastmeasDATA[sample]['ScanDirection'] == 'rev':#reverse scan
                    self.TimegraphStab.plot(AllDATA[sample]['datetime'].toPyDateTime(),AllDATA[sample]['FF'],'o',color='gray')
        self.fig7.canvas.draw_idle()
        self.fig7.canvas.flush_events()
    
    def updateRepgraph(self):
        global version,STOPMEAS, AllDATA, lastmeasDATA,lastmeastrackingDATA, RefDiodeChecked, Sunintensity, shutteropen
        global aftermpp,boxCurrent, boxVoltage, keithleyAddress, lastJVscansVmpp
        try:        
            self.ClearGraph('Rep')

            if self.ui.comboBox_JV_ptsorline.currentText() == 'Dots and Line':
                markerJV='o'
            elif self.ui.comboBox_JV_ptsorline.currentText() == 'Line':
                markerJV=''
            if self.ui.comboBox_Time_IVplots.currentText()=='J vs V':
                self.TimegraphIV.set_xlabel('Voltage (V)')
                self.TimegraphIV.set_ylabel('Current density (mA/cm'+'\xb2'+')')
                for sample in AllDATA.keys():
                    if AllDATA[sample]['ScanDirection'] == 'fwd':#forward scan
                        self.TimegraphIV.plot(AllDATA[sample]['Voltage'],AllDATA[sample]['CurrentDensity'],marker=markerJV, linestyle="dashed",color=AllDATA[sample]['pixcolor'])
                    elif AllDATA[sample]['ScanDirection'] == 'rev':#reverse scan
                        self.TimegraphIV.plot(AllDATA[sample]['Voltage'],AllDATA[sample]['CurrentDensity'],marker=markerJV, linestyle="solid",color=AllDATA[sample]['pixcolor'])
            else:
                self.TimegraphIV.set_xlabel('Voltage (V)')
                self.TimegraphIV.set_ylabel('Power density (mW/cm'+'\xb2'+')')
                for sample in AllDATA.keys():
                    if AllDATA[sample]['ScanDirection'] == 'fwd':#forward scan
                        self.TimegraphIV.plot(AllDATA[sample]['Voltage'],AllDATA[sample]['PowerDensity'],marker=markerJV, linestyle="dashed",color=AllDATA[sample]['pixcolor'])
                    elif AllDATA[sample]['ScanDirection'] == 'rev':#reverse scan
                        self.TimegraphIV.plot(AllDATA[sample]['Voltage'],AllDATA[sample]['PowerDensity'],marker=markerJV, linestyle="solid",color=AllDATA[sample]['pixcolor'])
    
            
            
            if self.ui.comboBox_Time_timeplots.currentText()=='Eff vs Time':
                self.TimegraphStab.set_xlabel('Time')
                self.TimegraphStab.set_ylabel('Efficiency')
                
                for sample in AllDATA.keys():
                    if AllDATA[sample]['ScanDirection'] == 'fwd':#forward scan
                        self.TimegraphStab.plot(AllDATA[sample]['datetime'].toPyDateTime(),AllDATA[sample]['Eff'],'o',color='black')
                    elif lastmeasDATA[sample]['ScanDirection'] == 'rev':#reverse scan
                        self.TimegraphStab.plot(AllDATA[sample]['datetime'].toPyDateTime(),AllDATA[sample]['Eff'],'o',color='gray')
                        
            elif self.ui.comboBox_Time_timeplots.currentText()=='Voc vs Time':
                self.TimegraphStab.set_xlabel('Time')
                self.TimegraphStab.set_ylabel('Voc')
                for sample in AllDATA.keys():
                    if AllDATA[sample]['ScanDirection'] == 'fwd':#forward scan
                        self.TimegraphStab.plot(AllDATA[sample]['datetime'].toPyDateTime(),AllDATA[sample]['Voc'],'o',color='black')
                    elif lastmeasDATA[sample]['ScanDirection'] == 'rev':#reverse scan
                        self.TimegraphStab.plot(AllDATA[sample]['datetime'].toPyDateTime(),AllDATA[sample]['Voc'], 'o',color='gray')
            elif self.ui.comboBox_Time_timeplots.currentText()=='Jsc vs Time':
                self.TimegraphStab.set_xlabel('Time')
                self.TimegraphStab.set_ylabel('Jsc')
                for sample in AllDATA.keys():
                    if AllDATA[sample]['ScanDirection'] == 'fwd':#forward scan
                        self.TimegraphStab.plot(AllDATA[sample]['datetime'].toPyDateTime(),AllDATA[sample]['Jsc'],'o',color='black')
                    elif lastmeasDATA[sample]['ScanDirection'] == 'rev':#reverse scan
                        self.TimegraphStab.plot(AllDATA[sample]['datetime'].toPyDateTime(),AllDATA[sample]['Jsc'],'o',color='gray')
            elif self.ui.comboBox_Time_timeplots.currentText()=='FF vs Time':
                self.TimegraphStab.set_xlabel('Time')
                self.TimegraphStab.set_ylabel('FF')
                for sample in AllDATA.keys():
                    if AllDATA[sample]['ScanDirection'] == 'fwd':#forward scan
                        self.TimegraphStab.plot(AllDATA[sample]['datetime'].toPyDateTime(),AllDATA[sample]['FF'],'o',color='black')
                    elif lastmeasDATA[sample]['ScanDirection'] == 'rev':#reverse scan
                        self.TimegraphStab.plot(AllDATA[sample]['datetime'].toPyDateTime(),AllDATA[sample]['FF'],'o',color='gray')
            self.fig7.canvas.draw_idle()
            self.fig7.canvas.flush_events()
        except KeyError:
            pass
        
    def PlotIV(self, keithleyObject, pixels, pixcolorslist, scandirections, Rep):
        global STOPMEAS, AllDATA, lastmeasDATA,lastmeastrackingDATA, RefDiodeChecked, Sunintensity, shutteropen
        global aftermpp,boxCurrent, boxVoltage, keithleyAddress,exedirector
        allpixtobemeasured=''
        for item in range(len(pixels)):
            allpixtobemeasured+=pixels[item]
            allpixtobemeasured+=', '
        allpixtobemeasured=allpixtobemeasured[:-2]
        self.allpixtobemeasured=allpixtobemeasured
        
        year=str(QtCore.QDate.currentDate().toString(QtCore.Qt.ISODate).split('-')[0])
        month=calendar.month_name[int(QtCore.QDate.currentDate().toString(QtCore.Qt.ISODate).split('-')[1])]
        directory=os.path.join(exedirectory,'SolarSimAllUsersDATA',str(self.ui.lineEdit_UserName.text()),year,month)
        if not os.path.exists(directory):
            os.makedirs(directory)
            os.chdir(directory)
        else :
            os.chdir(directory)
        integtime=self.ui.doubleSpinBox_JVintegrationtime.value()
        # NPLC of 1 with 60Hz power, new value every 16.67ms
        # integtime=50ms => NPLC = .050*60 = 3
        NPLC=integtime*60/1000
        if NPLC>10:
            NPLC=10
        if NPLC<0.01:
            NPLC=0.01
        polarity='pin'
        if not self.ui.checkBox_pin.isChecked():
            polarity='nip'
        currentlimit=self.ui.doubleSpinBox_JVcurrentlimit.value()
        prepareCurrent(keithleyObject, NPLC,currentlimit,polarity)#prepare to apply a voltage and measure a current

        for item in range(len(pixels)):
            connectPixel(boxCurrent, boxVoltage, pixels[item])
            if version== '1pixel':
                pixarea=self.ui.doubleSpinBox_pixXarea.value()
            elif version== '6pixels':
                pixarea=eval('self.ui.doubleSpinBox_pix'+pixels[item]+'area.value()')
            
            
            pixcolor=pixcolorslist[item]
            
            for direction in scandirections:
                self.direction=direction
                if keithleyAddress[0]=='Test':
                    QtTest.QTest.qWait(0)
                minV=self.ui.doubleSpinBox_JVminvoltage.value()/1000
                maxV=self.ui.doubleSpinBox_JVmaxvoltage.value()/1000
                stepV=self.ui.doubleSpinBox_JVstepsize.value()/1000
                delay=self.ui.doubleSpinBox_JVdelaypoints.value()
                data=takeIV(keithleyObject, minV,maxV,stepV,delay,direction,polarity,NPLC, currentlimit) 
                currentlist=data[:,1]
                voltagelist=data[:,0]
                currentdenlist=[x*1000/pixarea for x in data[:,1]] #assume 1sun, and assume keithley gives Amperes back 
                powerdenlist=[voltagelist[x]*currentdenlist[x] for x in range(len(currentdenlist))]
                 
                if direction == 1:#forward scan 
                    directionstr='fwd' 
                    self.JVgraph.plot(data[:,0],currentdenlist, linestyle="dashed",color=pixcolor) 
                elif direction == 0:#reverse scan 
                    directionstr='rev' 
                    self.JVgraph.plot(data[:,0],currentdenlist, linestyle="solid",color=pixcolor) 
                self.fig1.canvas.draw_idle() 
                 
                if shutteropen: 
                    illum='lt' 
                else: 
                    illum='dk' 
                if illum == 'dk': 
                    if direction == 1:#forward scan 
                        self.DIVgraphlin.plot(data[:,0],currentdenlist, linestyle="dashed",color=pixcolor) 
                    elif direction == 0:#reverse scan 
                        self.DIVgraphlin.plot(data[:,0],currentdenlist, linestyle="solid",color=pixcolor) 
                    ydataabs=list(map(lambda x: abs(x),currentdenlist)) 
                    if direction == 1:#forward scan 
                        self.DIVgraphlogY.semilogy(data[:,0],ydataabs, linestyle="dashed",color=pixcolor) 
                    elif direction == 0:#reverse scan 
                        self.DIVgraphlogY.semilogy(data[:,0],ydataabs, linestyle="solid",color=pixcolor) 
                    self.fig3.canvas.draw_idle() 
                    self.fig3.canvas.flush_events() 
 
                self.fig1.canvas.flush_events() 
                
                if shutteropen:
                    illum='lt'
                    # self.ClearGraph('LIV')
                else:
                    illum='dk'
                    # self.ClearGraph('DIV')
                
                if self.ui.radioButton_Assume1sun.isChecked():
                    radioButton_Assume1sun='True'
                else:
                    radioButton_Assume1sun='False'
                timestr = QtCore.QDateTime.currentDateTime().toString(QtCore.Qt.ISODate)
                timestr=timestr.replace(':','').replace('-','')

                sample=str(self.ui.lineEdit_SampleName.text()) +'_'+  'pX'+pixels[item] +'_'+ directionstr +'_'+ illum +'_'+ 'lp'+str(Rep) +'_'+ timestr  
                samplename=str(self.ui.lineEdit_SampleName.text()).replace('-','_')
                if '_' in str(self.ui.lineEdit_SampleName.text()):
                    Batch=str(self.ui.lineEdit_SampleName.text()).split('_')[0]
                    Substrate=str(self.ui.lineEdit_SampleName.text()).split('_')[1]
                else:
                    Batch='None'
                    Substrate='None'
                
                commenttext=str(self.ui.lineEdit_Comment.text())
                if aftermpp:
                    if 'aftermpp' not in commenttext:
                        commenttext+='_aftermpp'
                
                AllDATA[sample]={'sampleID': sample,'SampleNamePix': str(self.ui.lineEdit_SampleName.text()) +'_'+ pixels[item], 
                                  'linktorawdata':str(os.path.join(str(directory),sample+'.txt')),'SampleName': samplename,'Batch#':Batch,'Substrate#':Substrate, 'Pixel':pixels[item], 'Allpixs':allpixtobemeasured,
                                  'ScanDirection': directionstr, 'illum': illum, 'Sunintensity': Sunintensity, 'IsRefDiodeMeasured': RefDiodeChecked, 
                                  'RefDiodeNomCurr':self.ui.doubleSpinBox_DiodeNominalCurrent.value(),'RefDiodeMeasCurr':self.ui.doubleSpinBox_MeasuredDiodeCurrent.value(),
                                  'datetime': QtCore.QDateTime.currentDateTime(), 'Comment': commenttext,'temperature':self.ui.doubleSpinBox_Temperature.value(),
                                  'UserName': str(self.ui.lineEdit_UserName.text()), 'MeasType': str(self.ui.comboBox_MeasType.currentText()),'MeasNowType': 'IV',
                                  'pixcolor':pixcolor,'RepNumb': Rep,'DelayRep':self.ui.spinBox_RepDelay.value(), 'pixelArea': pixarea,'assume1sun':radioButton_Assume1sun,'ShutterOpen':shutteropen,
                                  'MinVoltage': self.ui.doubleSpinBox_JVminvoltage.value(), 'MaxVoltage': self.ui.doubleSpinBox_JVmaxvoltage.value(),
                                  'Aftermpp':aftermpp,'StepSize': self.ui.doubleSpinBox_JVstepsize.value(), 'CurrentLimit': self.ui.doubleSpinBox_JVcurrentlimit.value(), 
                                  'IntegTime': self.ui.doubleSpinBox_JVintegrationtime.value(), 'Delaypts': self.ui.doubleSpinBox_JVdelaypoints.value(), 
                                  'DelayShutter': self.ui.doubleSpinBox_JVdelayshutter.value(),'polarity':polarity,
                                  'Voc': -1., 'Jsc': -1., 'Isc': -1., 'FF': -1., 'Eff': -1, 'Pmpp': -1., 'Roc':-1., 'Rsc':-1., 'Jmpp':-1, 'Vmpp':-1,
                                  'Voltage':voltagelist,'Current':currentlist, 'CurrentDensity': currentdenlist
                                  }
                lastmeasDATA[sample]=AllDATA[sample]

                self.AnalysisJV(sample)
                self.Savedata(sample,AllDATA)
                self.UpdateTable(lastmeasDATA)
                if STOPMEAS==1:
                    break
            if STOPMEAS==1:
                self.sequence=''
                break
            
        if self.ui.comboBox_MeasType.currentText()=='LIV':
            self.ClearGraph('LIV')
        elif self.ui.comboBox_MeasType.currentText()=='DIV':
            self.ClearGraph('DIV')
        for sampleitem in lastmeasDATA.keys():
            pixcoloritem=lastmeasDATA[sampleitem]['pixcolor']
            if lastmeasDATA[sampleitem]['ScanDirection'] == 'fwd':#forward scan
                self.JVgraph.plot(lastmeasDATA[sampleitem]['Voltage'],lastmeasDATA[sampleitem]['CurrentDensity'], linestyle="dashed",color=pixcoloritem)
            elif lastmeasDATA[sampleitem]['ScanDirection'] == 'rev':#reverse scan
                self.JVgraph.plot(lastmeasDATA[sampleitem]['Voltage'],lastmeasDATA[sampleitem]['CurrentDensity'], linestyle="solid",color=pixcoloritem)
            if lastmeasDATA[sampleitem]['illum'] == 'dk':
                if lastmeasDATA[sampleitem]['ScanDirection'] == 'fwd':#forward scan
                    self.DIVgraphlin.plot(lastmeasDATA[sampleitem]['Voltage'],lastmeasDATA[sampleitem]['CurrentDensity'], linestyle="dashed",color=pixcoloritem)
                elif lastmeasDATA[sampleitem]['ScanDirection'] == 'rev':#reverse scan
                    self.DIVgraphlin.plot(lastmeasDATA[sampleitem]['Voltage'],lastmeasDATA[sampleitem]['CurrentDensity'], linestyle="solid",color=pixcoloritem)
                ydataabs=list(map(lambda x: abs(x),lastmeasDATA[sampleitem]['CurrentDensity']))
                if lastmeasDATA[sampleitem]['ScanDirection'] == 'fwd':#forward scan
                    self.DIVgraphlogY.semilogy(lastmeasDATA[sampleitem]['Voltage'],ydataabs, linestyle="dashed",color=pixcoloritem)
                elif lastmeasDATA[sampleitem]['ScanDirection'] == 'rev':#reverse scan
                    self.DIVgraphlogY.semilogy(lastmeasDATA[sampleitem]['Voltage'],ydataabs, linestyle="solid",color=pixcoloritem)
        
        self.loadtoDB('IV',lastmeasDATA,lastmeastrackingDATA) 
        
    # def PlotIVlive(self, keithleyObject, pixels, pixcolorslist, scandirections, Rep): #live plot point by point, this seems to be slow when using the keithley
    #     global STOPMEAS, AllDATA, lastmeasDATA,lastmeastrackingDATA, RefDiodeChecked, Sunintensity, shutteropen
    #     global aftermpp,boxCurrent, boxVoltage, keithleyAddress,exedirectory
    #     allpixtobemeasured=''
    #     for item in range(len(pixels)):
    #         allpixtobemeasured+=pixels[item]
    #         allpixtobemeasured+=', '
    #     allpixtobemeasured=allpixtobemeasured[:-2]
        
    #     year=str(QtCore.QDate.currentDate().toString(QtCore.Qt.ISODate).split('-')[0])
    #     month=calendar.month_name[int(QtCore.QDate.currentDate().toString(QtCore.Qt.ISODate).split('-')[1])]
    #     directory=os.path.join(exedirectory,'SolarSimAllUsersDATA',str(self.ui.lineEdit_UserName.text()),year,month)
    #     if not os.path.exists(directory):
    #         os.makedirs(directory)
    #         os.chdir(directory)
    #     else :
    #         os.chdir(directory)
    #     integtime=self.ui.doubleSpinBox_JVintegrationtime.value()
    #     # NPLC of 1 with 60Hz power, new value every 16.67ms
    #     # integtime=50ms => NPLC = .050*60 = 3
    #     NPLC=integtime*60/1000
    #     if NPLC>10:
    #         NPLC=10
    #     if NPLC<0.01:
    #         NPLC=0.01
    #     currentlimit=self.ui.doubleSpinBox_JVcurrentlimit.value()
    #     nMeas=2
    #     polar='pin'
    #     if window.w.ui.radioButton_nip.isChecked():
    #         polar='nip'
    #     prepareCurrent(keithleyObject, NPLC,currentlimit,polar)#prepare to apply a voltage and measure a current

    #     for item in range(len(pixels)):
    #         connectPixel(boxCurrent, boxVoltage, pixels[item])
    #         pixarea=eval('self.ui.doubleSpinBox_pix'+pixels[item]+'area.value()')
    #         pixcolor=pixcolorslist[item]
            
    #         for direction in scandirections:
    #             # startIVtime=datetime.datetime.now()
    #             if keithleyAddress[0]=='Test':
    #                 QtTest.QTest.qWait(100)

    #             minV=self.ui.doubleSpinBox_JVminvoltage.value()/1000
    #             maxV=self.ui.doubleSpinBox_JVmaxvoltage.value()/1000
    #             stepV=self.ui.doubleSpinBox_JVstepsize.value()/1000
    #             delay=self.ui.doubleSpinBox_JVdelaypoints.value()
                
    #             if shutteropen:
    #                 illum='lt'
    #                 self.ClearGraph('LIV')
    #             else:
    #                 illum='dk'
    #                 self.ClearGraph('DIV')
    #             # self.fig1.canvas.draw()
    #             # self.fig3.canvas.draw()
    #             # plt.show(block=False)
                
    #             for sampleitem in lastmeasDATA.keys():
    #                 pixcoloritem=lastmeasDATA[sampleitem]['pixcolor']
    #                 if lastmeasDATA[sampleitem]['ScanDirection'] == 'fwd':#forward scan
    #                     self.JVgraph.plot(lastmeasDATA[sampleitem]['Voltage'],lastmeasDATA[sampleitem]['CurrentDensity'], linestyle="dashed",color=pixcoloritem)
    #                 else:#reverse scan
    #                     self.JVgraph.plot(lastmeasDATA[sampleitem]['Voltage'],lastmeasDATA[sampleitem]['CurrentDensity'], linestyle="solid",color=pixcoloritem)
    #                 if lastmeasDATA[sampleitem]['illum'] == 'dk':
    #                     if lastmeasDATA[sampleitem]['ScanDirection'] == 'fwd':#forward scan
    #                         self.DIVgraphlin.plot(lastmeasDATA[sampleitem]['Voltage'],lastmeasDATA[sampleitem]['CurrentDensity'], linestyle="dashed",color=pixcoloritem)
    #                     else:#reverse scan
    #                         self.DIVgraphlin.plot(lastmeasDATA[sampleitem]['Voltage'],lastmeasDATA[sampleitem]['CurrentDensity'], linestyle="solid",color=pixcoloritem)
    #                     ydataabs=list(map(lambda x: abs(x),lastmeasDATA[sampleitem]['CurrentDensity']))
    #                     if lastmeasDATA[sampleitem]['ScanDirection'] == 'fwd':#forward scan
    #                         self.DIVgraphlogY.semilogy(lastmeasDATA[sampleitem]['Voltage'],ydataabs, linestyle="dashed",color=pixcoloritem)
    #                     else:#reverse scan
    #                         self.DIVgraphlogY.semilogy(lastmeasDATA[sampleitem]['Voltage'],ydataabs, linestyle="solid",color=pixcoloritem)
    #             self.fig1.canvas.draw()
    #             self.fig3.canvas.draw()
                
    #             if direction == 1:#forward scan
    #                 directionstr='fwd'
    #                 startV, stopV = minV, maxV
    #             elif direction == 0:#reverse scan
    #                 directionstr='rev'
    #                 startV, stopV = maxV, minV
    #                 stepV *= -1
    #             forw=direction#0=rev, 1=fwd  
                
    #             volts = np.arange(startV, stopV+stepV, stepV)
    #             currentdenlist=[]
    #             currentlist=[]
    #             voltagelist=[]
    #             # lines = []
                
    #             # line, = self.JVgraph.plot([],'o')
    #             # lines.append(line)
                
    #             # for step in volts:
    #             #     starttime=datetime.datetime.now()
    #             #     dataCurrent=measureCurrent(keithleyObject,step,nMeas)
    #             #     currentdenlist.append(1000*mean(dataCurrent[:,1])/pixarea)
    #             #     currentlist.append(mean(dataCurrent[:,1]))
    #             #     voltagelist.append(step)
                    
    #             #     lines[0].set_data(voltagelist,currentdenlist)
    #             #     self.fig1.canvas.draw()
    #             #     self.fig1.canvas.flush_events()
                    
    #             #     # self.JVgraph.plot(voltagelist,currentdenlist, 'o',color=pixcolor)
                    
    #             #     # if illum == 'dk':
    #             #     #     self.DIVgraphlin.plot(voltagelist,currentdenlist, 'o',color=pixcolor)
    #             #     #     ydataabs=list(map(lambda x: abs(x),currentdenlist))
    #             #     #     self.DIVgraphlogY.semilogy(voltagelist,ydataabs, 'o',color=pixcolor)
    #             #     #     # self.fig3.canvas.draw_idle()
    #             #     #     self.fig3.canvas.draw()
    #             #     #     self.fig3.canvas.flush_events()
                    
    #             #     # # self.fig1.canvas.draw_idle() 
    #             #     # self.fig1.canvas.draw()
    #             #     # self.fig1.canvas.flush_events()  
                    
    #             #     # QtTest.QTest.qWait(delay)
    #             #     while (datetime.datetime.now()-starttime).microseconds/1000< (delay+integtime):
    #             #         pass
                
    #             # startIVtime=datetime.datetime.now()
    #             for step in volts:
    #                 starttime=datetime.datetime.now()
    #                 dataCurrent=measureCurrent(keithleyObject,step,nMeas,polarity = polar)
    #                 currentdenlist.append(1000*mean(dataCurrent[:,1])/pixarea)
    #                 currentlist.append(mean(dataCurrent[:,1]))
    #                 voltagelist.append(step)
                    
    #                 self.JVgraph.plot(voltagelist,currentdenlist, 'o',color=pixcolor)
                    
    #                 # if illum == 'dk':
    #                 #     self.DIVgraphlin.plot(voltagelist,currentdenlist, 'o',color=pixcolor)
    #                 #     ydataabs=list(map(lambda x: abs(x),currentdenlist))
    #                 #     self.DIVgraphlogY.semilogy(voltagelist,ydataabs, 'o',color=pixcolor)
    #                 #     # self.fig3.canvas.draw_idle()
    #                 #     self.fig3.canvas.draw()
    #                 #     self.fig3.canvas.flush_events()
                    
    #                 # self.fig1.canvas.draw_idle() 
    #                 self.fig1.canvas.draw()
    #                 self.fig1.canvas.flush_events()  
                    
    #                 # QtTest.QTest.qWait(delay)
    #                 while (datetime.datetime.now()-starttime).microseconds/1000< (delay+integtime):
    #                     pass
    #             # startIVtime=datetime.datetime.now()
    #             if self.ui.radioButton_Assume1sun.isChecked():
    #                 radioButton_Assume1sun='True'
    #             else:
    #                 radioButton_Assume1sun='False'
    #             timestr = QtCore.QDateTime.currentDateTime().toString(QtCore.Qt.ISODate)
    #             timestr=timestr.replace(':','').replace('-','')

    #             sample=str(self.ui.lineEdit_SampleName.text()) +'_'+  'pX'+pixels[item] +'_'+ directionstr +'_'+ illum +'_'+ 'lp'+str(Rep) +'_'+ timestr  
    #             samplename=str(self.ui.lineEdit_SampleName.text()).replace('-','_')
    #             if '_' in str(self.ui.lineEdit_SampleName.text()):
    #                 Batch=str(self.ui.lineEdit_SampleName.text()).split('_')[0]
    #                 Substrate=str(self.ui.lineEdit_SampleName.text()).split('_')[1]
    #             else:
    #                 Batch='None'
    #                 Substrate='None'
                
    #             commenttext=str(self.ui.lineEdit_Comment.text())
    #             if aftermpp:
    #                 if 'aftermpp' not in commenttext:
    #                     commenttext+='_aftermpp'
                
    #             AllDATA[sample]={'sampleID': sample,'SampleNamePix': str(self.ui.lineEdit_SampleName.text()) +'_'+ pixels[item], 
    #                              'linktorawdata':str(os.path.join(str(directory),sample+'.txt')),'SampleName': samplename,'Batch#':Batch,'Substrate#':Substrate, 'Pixel':pixels[item], 'Allpixs':allpixtobemeasured,
    #                              'ScanDirection': directionstr, 'illum': illum, 'Sunintensity': Sunintensity, 'IsRefDiodeMeasured': RefDiodeChecked, 
    #                              'RefDiodeNomCurr':self.ui.doubleSpinBox_DiodeNominalCurrent.value(),'RefDiodeMeasCurr':self.ui.doubleSpinBox_MeasuredDiodeCurrent.value(),
    #                              'datetime': QtCore.QDateTime.currentDateTime(), 'Comment': commenttext,'temperature':self.ui.doubleSpinBox_Temperature.value(),
    #                              'UserName': str(self.ui.lineEdit_UserName.text()), 'MeasType': str(self.ui.comboBox_MeasType.currentText()),'MeasNowType': 'IV',
    #                              'pixcolor':pixcolor,'RepNumb': Rep,'DelayRep':self.ui.spinBox_RepDelay.value(), 'pixelArea': pixarea,'assume1sun':radioButton_Assume1sun,'ShutterOpen':shutteropen,
    #                              'MinVoltage': self.ui.doubleSpinBox_JVminvoltage.value(), 'MaxVoltage': self.ui.doubleSpinBox_JVmaxvoltage.value(),
    #                              'Aftermpp':aftermpp,'StepSize': self.ui.doubleSpinBox_JVstepsize.value(), 'CurrentLimit': self.ui.doubleSpinBox_JVcurrentlimit.value(), 
    #                              'IntegTime': self.ui.doubleSpinBox_JVintegrationtime.value(), 'Delaypts': self.ui.doubleSpinBox_JVdelaypoints.value(), 
    #                              'DelayShutter': self.ui.doubleSpinBox_JVdelayshutter.value(),'polarity':polar,
    #                              'Voc': -1., 'Jsc': -1., 'Isc': -1., 'FF': -1., 'Eff': -1, 'Pmpp': -1., 'Roc':-1., 'Rsc':-1., 'Jmpp':-1, 'Vmpp':-1,
    #                              'Voltage':voltagelist,'Current':currentlist, 'CurrentDensity': currentdenlist
    #                              }
    #             lastmeasDATA[sample]=AllDATA[sample]

    #             self.AnalysisJV(sample)
    #             self.Savedata(sample,AllDATA)
    #             self.UpdateTable(lastmeasDATA)
    #             if STOPMEAS==1:
    #                 break
    #         if STOPMEAS==1:
    #             self.sequence=''
    #             break
            
    #     if self.ui.comboBox_MeasType.currentText()=='LIV':
    #         self.ClearGraph('LIV')
    #     elif self.ui.comboBox_MeasType.currentText()=='DIV':
    #         self.ClearGraph('DIV')
    #     for sampleitem in lastmeasDATA.keys():
    #         pixcoloritem=lastmeasDATA[sampleitem]['pixcolor']
    #         if lastmeasDATA[sampleitem]['ScanDirection'] == 'fwd':#forward scan
    #             self.JVgraph.plot(lastmeasDATA[sampleitem]['Voltage'],lastmeasDATA[sampleitem]['CurrentDensity'], linestyle="dashed",color=pixcoloritem)
    #         elif lastmeasDATA[sampleitem]['ScanDirection'] == 'rev':#reverse scan
    #             self.JVgraph.plot(lastmeasDATA[sampleitem]['Voltage'],lastmeasDATA[sampleitem]['CurrentDensity'], linestyle="solid",color=pixcoloritem)
    #         if lastmeasDATA[sampleitem]['illum'] == 'dk':
    #             if lastmeasDATA[sampleitem]['ScanDirection'] == 'fwd':#forward scan
    #                 self.DIVgraphlin.plot(lastmeasDATA[sampleitem]['Voltage'],lastmeasDATA[sampleitem]['CurrentDensity'], linestyle="dashed",color=pixcoloritem)
    #             elif lastmeasDATA[sampleitem]['ScanDirection'] == 'rev':#reverse scan
    #                 self.DIVgraphlin.plot(lastmeasDATA[sampleitem]['Voltage'],lastmeasDATA[sampleitem]['CurrentDensity'], linestyle="solid",color=pixcoloritem)
    #             ydataabs=list(map(lambda x: abs(x),lastmeasDATA[sampleitem]['CurrentDensity']))
    #             if lastmeasDATA[sampleitem]['ScanDirection'] == 'fwd':#forward scan
    #                 self.DIVgraphlogY.semilogy(lastmeasDATA[sampleitem]['Voltage'],ydataabs, linestyle="dashed",color=pixcoloritem)
    #             elif lastmeasDATA[sampleitem]['ScanDirection'] == 'rev':#reverse scan
    #                 self.DIVgraphlogY.semilogy(lastmeasDATA[sampleitem]['Voltage'],ydataabs, linestyle="solid",color=pixcoloritem)
        
    #     self.loadtoDB('IV',lastmeasDATA,lastmeastrackingDATA)  
    
    def AnalysisJV(self, sample):
        global AllDATA, lastmeasDATA, Sunintensity        
        
        resample_step_size = 0.00001 # Voltage step size to use while resampling JV curve to find Pmax
    
        from scipy.interpolate import interp1d
    
        # Create a dict to store the parameters. Default values are -1 indicating failure to extract parameter
        try:
            # Extract Jsc by interpolating wrt V
            jv_interp_V = interp1d(AllDATA[sample]['Voltage'], AllDATA[sample]['CurrentDensity'], bounds_error=False, fill_value=0.)
            if AllDATA[sample]['MeasNowType']!='QSS':
                Jsc = jv_interp_V(0.)
                AllDATA[sample]['Jsc'] = abs(np.around(Jsc, decimals=8))
                lastmeasDATA[sample]['Jsc']= AllDATA[sample]['Jsc'] 
                AllDATA[sample]['Isc'] = AllDATA[sample]['Jsc']*AllDATA[sample]['pixelArea']
                lastmeasDATA[sample]['Isc'] = AllDATA[sample]['Isc']
                # Extract Voc by interpolating wrt J
                jv_interp_J = interp1d(AllDATA[sample]['CurrentDensity'], AllDATA[sample]['Voltage'], bounds_error=False, fill_value=0.)
                Voc = jv_interp_J(0.)
                AllDATA[sample]['Voc'] = 1000*np.around(Voc, decimals=8) #in mV
                lastmeasDATA[sample]['Voc'] = AllDATA[sample]['Voc'] 
            Voc = AllDATA[sample]['Voc']/1000
            Jsc = -AllDATA[sample]['Jsc']
            # Resample JV curve over standard interval and find Pmax
            Vrange_new = np.arange(0., Voc, resample_step_size)
            jv_resampled = np.zeros((len(Vrange_new), 3))
            jv_resampled[:,0] = np.copy(Vrange_new)
            jv_resampled[:,1] = jv_interp_V(jv_resampled[:,0])
            jv_resampled[:,2] = np.abs(np.multiply(jv_resampled[:,0], jv_resampled[:,1]))
            pmax=np.max(np.abs(np.multiply(jv_resampled[:,0], jv_resampled[:,1])))
            AllDATA[sample]['Pmpp'] = np.around(np.max(np.abs(np.multiply(jv_resampled[:,0], jv_resampled[:,1]))), decimals=4)
            AllDATA[sample]['Eff']=AllDATA[sample]['Pmpp']/Sunintensity #to correct for the actual light intensity measured with the ref diode
            lastmeasDATA[sample]['Pmpp'] = AllDATA[sample]['Pmpp']
            lastmeasDATA[sample]['Eff']=AllDATA[sample]['Eff']
            indPmax=list(jv_resampled[:,2]).index(pmax)
            AllDATA[sample]['Jmpp']=abs(list(jv_resampled[:,1])[indPmax]) 
            lastmeasDATA[sample]['Jmpp']=AllDATA[sample]['Jmpp']
            AllDATA[sample]['Vmpp']=1000*abs(list(jv_resampled[:,0])[indPmax])
            lastmeasDATA[sample]['Vmpp']=AllDATA[sample]['Vmpp']
            # Calculate fill factor
            AllDATA[sample]['FF'] = abs(100*np.around(pmax/(Jsc*Voc), decimals=4))
            lastmeasDATA[sample]['FF'] =AllDATA[sample]['FF']
            
            # Calculate Rsc&Roc 
            x= [x0 for x0,y0 in sorted(zip(AllDATA[sample]['Voltage'],AllDATA[sample]['CurrentDensity']))]
            y= [0.001*y0 for x0,y0 in sorted(zip(AllDATA[sample]['Voltage'],AllDATA[sample]['CurrentDensity']))]
            xSC=[]
            ySC=[]
            for i in range(len(x)):
                if x[i]>=0:
                    xSC.append(x[i-3])
                    xSC.append(x[i-2])
                    xSC.append(x[i-1])
                    xSC.append(x[i])
                    xSC.append(x[i+1])
                    xSC.append(x[i+2])
                    ySC.append(y[i-3])
                    ySC.append(y[i-2])
                    ySC.append(y[i-1])
                    ySC.append(y[i])
                    ySC.append(y[i+1])
                    ySC.append(y[i+2])
                    break
            try:
                xSC=np.array(xSC)
                ySC=np.array(ySC)    
                xy=[xi*yi for xi, yi in zip(xSC,ySC)]
                xSC2=[xi**2 for xi in xSC]
                AllDATA[sample]['Rsc'] =abs( 1/(((sum(xSC)*sum(ySC)) - len(xSC)*sum(xy)) / ((sum(xSC)*sum(xSC)) - len(xSC)*sum(xSC2)))) 
                lastmeasDATA[sample]['Rsc'] =AllDATA[sample]['Rsc']
            except:
                self.ui.textEdit_Keithley.append(QtCore.QDateTime.currentDateTime().toString()+': '+'error for Rsc')
                # print('rsc1')
            if AllDATA[sample]['Jsc']>1:
                xSC=[]
                ySC=[]
                try:
                    for i in range(len(x)):
                        if x[i]>=AllDATA[sample]['Voc']*0.001:
                            xSC.append(x[i-2])
                            xSC.append(x[i-1])
                            xSC.append(x[i])
                            xSC.append(x[i+1])
                            
                            ySC.append(y[i-2])
                            ySC.append(y[i-1])
                            ySC.append(y[i])
                            ySC.append(y[i+1])
                            break
                    xSC=np.array(xSC)
                    ySC=np.array(ySC)
                    
                    xy=[xi*yi for xi, yi in zip(xSC,ySC)]
                    xSC2=[xi**2 for xi in xSC]
                    AllDATA[sample]['Roc'] =abs( 1/(((sum(xSC)*sum(ySC)) - len(xSC)*sum(xy)) / ((sum(xSC)*sum(xSC)) - len(xSC)*sum(xSC2))))
                    lastmeasDATA[sample]['Roc'] =AllDATA[sample]['Roc']
                except:
                    self.ui.textEdit_Keithley.append(QtCore.QDateTime.currentDateTime().toString()+': '+'Error Roc - not enough points around Voc')
                    # print('not enough points around Voc')
            else:
                xSC=x[-3:]
                ySC=y[-3:]
                xSC=np.array(xSC)
                ySC=np.array(ySC)
                xy=[xi*yi for xi, yi in zip(xSC,ySC)]
                xSC2=[xi**2 for xi in xSC]
                AllDATA[sample]['Roc'] = abs( 1/(((sum(xSC)*sum(ySC)) - len(xSC)*sum(xy)) / ((sum(xSC)*sum(xSC)) - len(xSC)*sum(xSC2))))
                lastmeasDATA[sample]['Roc'] =AllDATA[sample]['Roc']
        except:
            self.ui.textEdit_Keithley.append(QtCore.QDateTime.currentDateTime().toString()+': '+'error with fits...')
            # print("error with fits...")
            
#%%######################################################################################################            
    def Savedata(self, sample, DATA):
        global exedirectory
        year=str(QtCore.QDate.currentDate().toString(QtCore.Qt.ISODate).split('-')[0])
        month=calendar.month_name[int(QtCore.QDate.currentDate().toString(QtCore.Qt.ISODate).split('-')[1])]
        directory=os.path.join(exedirectory,'SolarSimAllUsersDATA',str(self.ui.lineEdit_UserName.text()),year,month)
        if not os.path.exists(directory):
            os.makedirs(directory)
            os.chdir(directory)
        else :
            os.chdir(directory)
        
        if DATA[sample]['MeasNowType']=='IV':
            text='#Singapore Solar Simulator, Python\n'+\
                '\n'+\
                'DateTime:\t'+	DATA[sample]['datetime'].toString()+'\n'+\
                'UserName:\t'+str(DATA[sample]['UserName']) +'\n'+\
                'SampleName:\t'+str(DATA[sample]['SampleName']) +'\n'+\
                'Comment:\t'+str(DATA[sample]['Comment'])+'\n'+\
                'Meas. type:\t'+str(DATA[sample]['MeasType'])+'\n'+\
                'WhichPixels:\t'+str(DATA[sample]['Allpixs'])+'\n'+\
                'PixelNow:\t'+str(DATA[sample]['Pixel'])+'\n'+\
                'PixArea:\t'+str(DATA[sample]['pixelArea'])+'\n'+\
                '#rep:\t'+str(DATA[sample]['RepNumb'])+'\n'+\
                'DelayRep:\t'+str(DATA[sample]['DelayRep'])+'\n'+\
                'Aftermpp:\t'+str(DATA[sample]['Aftermpp'])+'\n'+\
                '\n'+\
                'WasRefMeasured?:\t'+str(DATA[sample]['IsRefDiodeMeasured'])+'\n'+\
                'Diode nominal current:\t'+str(DATA[sample]['RefDiodeNomCurr'])+'\n'+\
                'Diode measured current:\t'+str(DATA[sample]['RefDiodeMeasCurr'])+'\n'+\
                '#sun:\t'+str(DATA[sample]['Sunintensity'])+'\n'+\
                'temperature:\t'+str(DATA[sample]['temperature'])+'\n'+\
                'assume1sun:\t'+str(DATA[sample]['assume1sun'])+'\n'+\
                '\n'+\
                'Illumination:\t'+str(DATA[sample]['illum'])+'\n'+\
                'ShutterOpen:\t'+str(DATA[sample]['ShutterOpen'])+'\n'+\
                '\n'+\
                '#IV scan Parameters\n'+\
                'minvoltage:\t'+str(DATA[sample]['MinVoltage'])+'\n'+\
                'maxvoltage:\t'+str(DATA[sample]['MaxVoltage'])+'\n'+\
                'JVstepsize:\t'+str(DATA[sample]['StepSize'])+'\n'+\
                'currentlimit:\t'+str(DATA[sample]['CurrentLimit'])+'\n'+\
                'integtime:\t'+str(DATA[sample]['IntegTime'])+'\n'+\
                'delaypoints:\t'+str(DATA[sample]['Delaypts'])+'\n'+\
                'delayshutter:\t'+str(DATA[sample]['DelayShutter'])+'\n'+\
                'scandirection:\t'+str(DATA[sample]['ScanDirection'])+'\n'+\
                'polarity:\t'+str(DATA[sample]['polarity'])+'\n'+\
                '\n'+\
                '#IV results\n'+\
                'Eff\t'+str(DATA[sample]['Eff'])+'\n'+\
                'Voc\t'+str(DATA[sample]['Voc'])+'\n'+\
                'FF\t'+str(DATA[sample]['FF'])+'\n'+\
                'Jsc\t'+str(DATA[sample]['Jsc'])+'\n'+\
                'Isc\t'+str(DATA[sample]['Isc'])+'\n'+\
                'Pmpp\t'+str(DATA[sample]['Pmpp'])+'\n'+\
                'Vmpp\t'+str(DATA[sample]['Vmpp'])+'\n'+\
                'Jmpp\t'+str(DATA[sample]['Jmpp'])+'\n'+\
                'Roc\t'+str(DATA[sample]['Roc'])+'\n'+\
                'Rsc\t'+str(DATA[sample]['Rsc'])+'\n'+\
                '\n'+\
                '#IV data\n'+\
                'Voltage\tCurrentDensity\tCurrent\n'
            for i in range(len(DATA[sample]['Voltage'])):
                text+=str(DATA[sample]['Voltage'][i])+'\t'+str(DATA[sample]['CurrentDensity'][i])+'\t'+str(DATA[sample]['Current'][i])+'\n'
            with open(DATA[sample]['sampleID']+'.txt','w') as file:
                file.write(text)
                
        elif DATA[sample]['MeasNowType']=='QSS':
            stabnotstabstrings=[]
            for item in DATA[sample]['notstabilizedlist']:
                if item:
                    stabnotstabstrings.append('NotStab')
                else:
                    stabnotstabstrings.append('Stab')
            # print(stabnotstabstrings)
            text='#Singapore Solar Simulator, Python\n'+\
                '\n'+\
                'DateTime:\t'+	DATA[sample]['datetime'].toString()+'\n'+\
                'UserName:\t'+str(DATA[sample]['UserName']) +'\n'+\
                'SampleName:\t'+str(DATA[sample]['SampleName']) +'\n'+\
                'Comment:\t'+str(DATA[sample]['Comment'])+'\n'+\
                'Meas. type:\t'+str(DATA[sample]['MeasType'])+'\n'+\
                'WhichPixels:\t'+str(DATA[sample]['Allpixs'])+'\n'+\
                'PixelNow:\t'+str(DATA[sample]['Pixel'])+'\n'+\
                'PixArea:\t'+str(DATA[sample]['pixelArea'])+'\n'+\
                '#rep:\t'+str(DATA[sample]['RepNumb'])+'\n'+\
                'DelayRep:\t'+str(DATA[sample]['DelayRep'])+'\n'+\
                'Aftermpp:\t'+str(DATA[sample]['Aftermpp'])+'\n'+\
                '\n'+\
                'WasRefMeasured?:\t'+str(DATA[sample]['IsRefDiodeMeasured'])+'\n'+\
                'Diode nominal current:\t'+str(DATA[sample]['RefDiodeNomCurr'])+'\n'+\
                'Diode measured current:\t'+str(DATA[sample]['RefDiodeMeasCurr'])+'\n'+\
                '#sun:\t'+str(DATA[sample]['Sunintensity'])+'\n'+\
                'temperature:\t'+str(DATA[sample]['temperature'])+'\n'+\
                'assume1sun:\t'+str(DATA[sample]['assume1sun'])+'\n'+\
                '\n'+\
                'Illumination:\t'+str(DATA[sample]['illum'])+'\n'+\
                'ShutterOpen:\t'+str(DATA[sample]['ShutterOpen'])+'\n'+\
                '\n'+\
                '#IV scan Parameters\n'+\
                'minvoltage:\t'+str(DATA[sample]['MinVoltage'])+'\n'+\
                'maxvoltage:\t'+str(DATA[sample]['MaxVoltage'])+'\n'+\
                'JVstepsize:\t'+str(DATA[sample]['StepSize'])+'\n'+\
                'currentlimit:\t'+str(DATA[sample]['CurrentLimit'])+'\n'+\
                'integtime:\t'+str(DATA[sample]['IntegTime'])+'\n'+\
                'delaypoints:\t'+str(DATA[sample]['Delaypts'])+'\n'+\
                'delayshutter:\t'+str(DATA[sample]['DelayShutter'])+'\n'+\
                'scandirection:\t'+str(DATA[sample]['ScanDirection'])+'\n'+\
                'polarity:\t'+str(DATA[sample]['polarity'])+'\n'+\
                '\n'+\
                '#QSS parameters\n'+\
                'QSSnbpts:\t'+str(DATA[sample]['QSSnbpts'])+'\n'+\
                'QSSdensity:\t'+str(DATA[sample]['QSSdensity'])+'\n'+\
                'QSSdevcrit:\t'+str(DATA[sample]['QSSdevcrit'])+'\n'+\
                'QSSTdev:\t'+str(DATA[sample]['QSSTdev'])+'\n'+\
                'QSSmaxdur:\t'+str(DATA[sample]['QSSmaxdur'])+'\n'+\
                '\n'+\
                '#IV results\n'+\
                'Eff\t'+str(DATA[sample]['Eff'])+'\n'+\
                'Voc\t'+str(DATA[sample]['Voc'])+'\n'+\
                'FF\t'+str(DATA[sample]['FF'])+'\n'+\
                'Jsc\t'+str(DATA[sample]['Jsc'])+'\n'+\
                'Isc\t'+str(DATA[sample]['Isc'])+'\n'+\
                'Pmpp\t'+str(DATA[sample]['Pmpp'])+'\n'+\
                'Vmpp\t'+str(DATA[sample]['Vmpp'])+'\n'+\
                'Jmpp\t'+str(DATA[sample]['Jmpp'])+'\n'+\
                'Roc\t'+str(DATA[sample]['Roc'])+'\n'+\
                'Rsc\t'+str(DATA[sample]['Rsc'])+'\n'+\
                '\n'+\
                '#Quasi-steady-state JV curve data\n'+\
                'Voltage\tCurrentDensity\tCurrent\tIsStabilized?\n'
            # print(len(DATA[sample]['Voltage']))
            # print(len(DATA[sample]['CurrentDensity']))
            # print(len(DATA[sample]['Current']))
            # print(len(stabnotstabstrings))
            for i in range(len(DATA[sample]['Voltage'])):
                text+=str(DATA[sample]['Voltage'][i])+'\t'+str(DATA[sample]['CurrentDensity'][i])+'\t'+str(DATA[sample]['Current'][i])+'\t'+str(stabnotstabstrings[i])+'\n'
            text+='\n'+\
                '#Quasi-steady-state Time stabilization data\n'+\
                'Time\tCurrentDensity\tCurrent\tVoltage\tPower\n'
            for i in range(len(DATA[sample]['timelist'])):
                text+=str(DATA[sample]['timelist'][i])+'\t'+str(DATA[sample]['currentdensitystablist'][i])+'\t'+str(DATA[sample]['currentstablist'][i])+'\t'+str(DATA[sample]['voltagestablist'][i])+'\t'+str(DATA[sample]['powerstablist'][i])+'\n'
                
            with open(DATA[sample]['sampleID']+'.txt','w') as file:
                file.write(text)
        else:
            text='#Singapore Solar Simulator, Python\n'+\
                '\n'+\
                'DateTime:\t'+	DATA[sample]['datetime'].toString()+'\n'+\
                'UserName:\t'+str(DATA[sample]['UserName']) +'\n'+\
                'SampleName:\t'+str(DATA[sample]['SampleName']) +'\n'+\
                'Comment:\t'+str(DATA[sample]['Comment'])+'\n'+\
                'Meas. type:\t'+str(DATA[sample]['MeasType'])+'\n'+\
                'WhichPixels:\t'+str(DATA[sample]['Allpixs'])+'\n'+\
                'PixelNow:\t'+str(DATA[sample]['Pixel'])+'\n'+\
                'PixArea:\t'+str(DATA[sample]['pixelArea'])+'\n'+\
                '#rep:\t'+str(DATA[sample]['RepNumb'])+'\n'+\
                'DelayRep:\t'+str(DATA[sample]['DelayRep'])+'\n'+\
                '\n'+\
                'WasRefMeasured?:\t'+str(DATA[sample]['IsRefDiodeMeasured'])+'\n'+\
                'Diode nominal current:\t'+str(DATA[sample]['RefDiodeNomCurr'])+'\n'+\
                'Diode measured current:\t'+str(DATA[sample]['RefDiodeMeasCurr'])+'\n'+\
                '#sun:\t'+str(DATA[sample]['Sunintensity'])+'\n'+\
                'temperature:\t'+str(DATA[sample]['temperature'])+'\n'+\
                'assume1sun:\t'+str(DATA[sample]['assume1sun'])+'\n'+\
                '\n'+\
                'Illumination:\t'+str(DATA[sample]['illum'])+'\n'+\
                'ShutterOpen:\t'+str(DATA[sample]['ShutterOpen'])+'\n'+\
                '\n'+\
                '#MPPT scan Parameters\n'+\
                'InitialVoltage:\t'+str(DATA[sample]['InitialVoltage'])+'\n'+\
                'initialdelay:\t'+str(DATA[sample]['initialdelay'])+'\n'+\
                'initialstep:\t'+str(DATA[sample]['initialstep'])+'\n'+\
                '\n'+\
                '#MPPT data\n'+\
                'Time\tPower\tVoltage\tCurrentDensity\tCurrent\tStep\tDelay\n'
            for i in range(len(DATA[sample]['Voltage'])):
                text+=str(DATA[sample]['time'][i])+'\t'+str(DATA[sample]['power'][i])+'\t'+str(DATA[sample]['Voltage'][i])+'\t'+str(DATA[sample]['CurrentDensity'][i])+'\t'+str(DATA[sample]['Current'][i])+'\t'+str(DATA[sample]['step'][i])+'\t'+str(DATA[sample]['delay'][i])+'\n'
            with open(DATA[sample]['sampleID']+'.txt','w') as file:
                file.write(text)

#%%######################################################################################################    



    def loadtoDB(self, MeasType, ivDATA, mppdata):
        
        if MeasType=='IV':
            DATA=ivDATA
        else:
            DATA=mppdata
        
        for sample in DATA.keys():
            #username in Table users
            self.theCursor.execute("SELECT id FROM users WHERE user=?",(DATA[sample]['UserName'],))
            users_id_exists = self.theCursor.fetchone()
            if users_id_exists==None:
                self.theCursor.execute("INSERT INTO users (user) VALUES (?)",
                                (DATA[sample]['UserName'],))
                users_id_exists=self.theCursor.lastrowid
            else:
                users_id_exists=users_id_exists[0]
                    
            # #batchname in Table batch, with users_id
            self.theCursor.execute("SELECT id FROM batch WHERE batchname =? AND users_id =?",(DATA[sample]['Batch#'],users_id_exists,))
            batch_id_exists = self.theCursor.fetchone()
            if batch_id_exists==None:
                self.theCursor.execute("INSERT INTO batch (batchname,users_id) VALUES (?,?)",
                                (DATA[sample]['Batch#'],users_id_exists,))
                batch_id_exists=self.theCursor.lastrowid
            else:
                batch_id_exists=batch_id_exists[0]
                    
            #samplename in table samples, with batch_id
            self.theCursor.execute("SELECT id FROM samples WHERE samplename =? AND batch_id =?",(DATA[sample]['SampleName'],batch_id_exists,))
            samples_id_exists = self.theCursor.fetchone()
            if samples_id_exists==None:
                self.theCursor.execute("INSERT INTO samples (samplename,batch_id) VALUES (?,?)",
                                (DATA[sample]['SampleName'],batch_id_exists,))
                samples_id_exists=self.theCursor.lastrowid
            else:
                samples_id_exists=samples_id_exists[0]
            
            #sample pixel area
            self.theCursor.execute("SELECT id FROM pixelarea WHERE pixel_area =?",(DATA[sample]['pixelArea'],))
            pixelarea_id_exists = self.theCursor.fetchone()
            if pixelarea_id_exists==None:
                self.theCursor.execute("INSERT INTO pixelarea (pixel_area) VALUES (?)",
                                (DATA[sample]['pixelArea'],))
                pixelarea_id_exists=self.theCursor.lastrowid
            else:
                pixelarea_id_exists=pixelarea_id_exists[0]
            
            #table cells
            self.theCursor.execute("SELECT id FROM cells WHERE cellname =? AND samples_id =? AND batch_id =?",(DATA[sample]['Pixel'],samples_id_exists,batch_id_exists,))
            cells_id_exists = self.theCursor.fetchone()
            if cells_id_exists==None:
                self.theCursor.execute("INSERT INTO cells (cellname,AllpixSeq, pixelarea_id,samples_id,batch_id) VALUES (?,?,?,?,?)",
                                (DATA[sample]['Pixel'],DATA[sample]['Allpixs'],pixelarea_id_exists,samples_id_exists,batch_id_exists,))
                cells_id_exists=self.theCursor.lastrowid
            else:
                cells_id_exists=cells_id_exists[0]
            
            #Table Refdiode
            self.theCursor.execute("INSERT INTO Refdiode (IsRefDiodeMeasured,RefDiodeNomCurr,RefDiodeMeasCurr,temperature) VALUES (?,?,?,?)",
                                (DATA[sample]['IsRefDiodeMeasured'],DATA[sample]['RefDiodeNomCurr'],DATA[sample]['RefDiodeMeasCurr'],DATA[sample]['temperature'],))
            refdiode_id_exists=self.theCursor.lastrowid
            
            
            if DATA[sample]['MeasNowType']=='IV' or DATA[sample]['MeasNowType']=='QSS' :
                #tables JVmeas
                self.theCursor.execute("SELECT id FROM JVmeas WHERE MeasurementLongName =? AND cells_id =? AND samples_id =? AND batch_id =?",(DATA[sample]['sampleID'],cells_id_exists,samples_id_exists,batch_id_exists,))
                JVmeas_id_exists = self.theCursor.fetchone()
                if JVmeas_id_exists==None:
                    self.theCursor.execute("INSERT INTO JVmeas (DateTimeJV, Eff, Voc,Jsc,Isc, FF, Vmpp, Jmpp,Pmpp,Roc,Rsc,ScanDirect,Delay, DelayShutter,IntegTime,Vmin,Vmax,MeasType,MeasNowType,StepSize,CurrentLimit,LightDark,IlluminationIntensity,commentJV,MeasurementLongName,SampleNamePix,linktorawdata,aftermpp,samples_id,batch_id,cells_id,Refdiode_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                                    (DATA[sample]['datetime'].toString(QtCore.Qt.ISODate).replace('T','-').replace(':','-') ,DATA[sample]['Eff'],DATA[sample]['Voc'],DATA[sample]['Jsc'],
                                     DATA[sample]['Isc'],DATA[sample]['FF'],DATA[sample]['Vmpp'],DATA[sample]['Jmpp'],
                                     DATA[sample]['Pmpp'],DATA[sample]['Roc'],DATA[sample]['Rsc'],DATA[sample]['ScanDirection'],
                                     DATA[sample]['Delaypts'],DATA[sample]['DelayShutter'],DATA[sample]['IntegTime'],DATA[sample]['MinVoltage'],
                                     DATA[sample]['MaxVoltage'],DATA[sample]['MeasType'],DATA[sample]['MeasNowType'],DATA[sample]['StepSize'],
                                     DATA[sample]['CurrentLimit'],DATA[sample]['illum'],DATA[sample]['Sunintensity'],DATA[sample]['Comment'],
                                     DATA[sample]['sampleID'],DATA[sample]['SampleNamePix'],DATA[sample]['linktorawdata'],DATA[sample]['Aftermpp'],
                                     samples_id_exists,batch_id_exists,cells_id_exists,refdiode_id_exists,))
                    JVmeas_id_exists=self.theCursor.lastrowid
                else:
                    JVmeas_id_exists=JVmeas_id_exists[0]
            else:
                #tables Mppmeas
                self.theCursor.execute("SELECT id FROM MPPmeas WHERE MeasurementLongName =? AND cells_id =? AND samples_id =? AND batch_id =?",(DATA[sample]['sampleID'],cells_id_exists,samples_id_exists,batch_id_exists,))
                MPPmeas_id_exists = self.theCursor.fetchone()
                if MPPmeas_id_exists==None:
                    self.theCursor.execute("INSERT INTO MPPmeas (DateTimeMPP,TrackingAlgo,MeasType,MeasNowType,TrackingDuration,Vstart,Vstep,Delay,PowerEnd,commentmpp,LightDark,IlluminationIntensity,MeasurementLongName,SampleNamePix,linktorawdata,samples_id,batch_id, cells_id,Refdiode_id,PowerEnd) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                                    (DATA[sample]['datetime'].toString(QtCore.Qt.ISODate).replace('T','-').replace(':','-'),'perturbe&observe',DATA[sample]['MeasType'],DATA[sample]['MeasNowType'],
                                     DATA[sample]['trackingtime'],DATA[sample]['InitialVoltage'],DATA[sample]['initialstep'],DATA[sample]['initialdelay'],
                                     DATA[sample]['power'][-1],DATA[sample]['Comment'],DATA[sample]['illum'],
                                     DATA[sample]['Sunintensity'],DATA[sample]['sampleID'],DATA[sample]['SampleNamePix'],DATA[sample]['linktorawdata'],
                                     samples_id_exists,batch_id_exists,cells_id_exists,refdiode_id_exists,DATA[sample]['power'][-1],))
                    MPPmeas_id_exists=self.theCursor.lastrowid
                else:
                    MPPmeas_id_exists=MPPmeas_id_exists[0]
                    
            self.db_conn.commit()
        
    def connecttoarduinoPy(self):
        global ArduinoConnected, arduino,keithleyAddress
        connectionstrial=0
        while(connectionstrial<2):
            print(connectionstrial)
            ArduinoConnected, arduino = ConnectToArduino('COM8', 115200, .1,0)
            # print('aftercontrial')
            if ArduinoConnected==0:
                if keithleyAddress[0]=='Test':
                    self.ui.textEdit_Keithley.append(QtCore.QDateTime.currentDateTime().toString()+': '+'Failed to connect to the Arduino, but test mode, so pass')
                    break
                else:
                    self.ui.textEdit_Keithley.append(QtCore.QDateTime.currentDateTime().toString()+': '+'Failed to connect to the Arduino')
                    QMessageBox.information(self,'Arduino not connected', 'The Arduino could not be connected. Try to unplug and replug the Arduino.')
                    connectionstrial+=1
            else:
                self.ui.textEdit_Keithley.append(QtCore.QDateTime.currentDateTime().toString()+': Arduino connected as '+str(arduino))
                break
        if connectionstrial>=3:
            self.ui.textEdit_Keithley.append(QtCore.QDateTime.currentDateTime().toString()+': '+'Failed to connect to the Arduino. no shutter control in this session.')
            QMessageBox.information(self,'Arduino not connected', "The Arduino could not be connected. Let's move on without shutter control.")
    def connecttoDB(self):
        global exedirectory,dbchoice
        directory=os.path.join(exedirectory,'Database')
        if not os.path.exists(directory):
            os.makedirs(directory)
            os.chdir(directory)
        else :
            os.chdir(directory)
        listofdbfiles=[]
        #find in this directory all files .db
        for file in os.listdir(directory):
            if file.endswith(".db"):
                listofdbfiles.append(file)
        # print(listofdbfiles)
        #if only one, use it directly
        if len(listofdbfiles)==1:
            path=os.path.join(directory,listofdbfiles[0])
            self.db_conn=sqlite3.connect(path)
            self.theCursor=self.db_conn.cursor()
            CreateAllTables(self.db_conn)
            self.ui.textEdit_Keithley.append(QtCore.QDateTime.currentDateTime().toString()+': '+'connected to DB, '+listofdbfiles[0])
            print(listofdbfiles[0])
        #if multiple, ask the user which one to open by opening window with dropdown box and button
        elif len(listofdbfiles)>1:
            while(True):
                fname = QFileDialog.getOpenFileName(self, 'Several .db files found, choose the correct one', directory,"DB files (*.db)")[0]
                if fname =='':
                    return
                filename, file_extension = os.path.splitext(fname)
                if file_extension=='.db':
                    self.db_conn=sqlite3.connect(fname)
                    self.theCursor=self.db_conn.cursor()
                    CreateAllTables(self.db_conn)
                    self.ui.textEdit_Keithley.append(QtCore.QDateTime.currentDateTime().toString()+': '+'connected to DB, '+filename)
                    print(filename)
                    break
                else:
                    QMessageBox.information(self,'Not correct file', 'This is not a .db file.')
        #if no file, ask user if he wants to select somewhere else a .db file or create a new one automatically
        elif listofdbfiles==[]:
            while(True):#reask the user until he loads a proper file or says that he doesn't have one
                close = QMessageBox.question(self,
                                          "no .db file found in Database folder",
                                          "Do you have a DB file somewhere else?",
                                          QMessageBox.Yes | QMessageBox.No)
                if close == QMessageBox.Yes:
                        fname = QFileDialog.getOpenFileName(self, 'Choose a .db file to load', directory,"DB files (*.db)")[0]
                        if fname =='':
                            return
                        filename, file_extension = os.path.splitext(fname)
                        if file_extension=='.db':
                            self.db_conn=sqlite3.connect(fname)
                            self.theCursor=self.db_conn.cursor()
                            CreateAllTables(self.db_conn)
                            self.ui.textEdit_Keithley.append(QtCore.QDateTime.currentDateTime().toString()+': '+'connected to DB, '+filename)
                            print(filename)
                            break
                        else:
                            QMessageBox.information(self,'Not correct file', 'This is not a .db file.')
                else:#if user says no, then create a default file
                    path=os.path.join(directory,'DefaultDB.db')
                    self.db_conn=sqlite3.connect(path)
                    self.theCursor=self.db_conn.cursor()
                    CreateAllTables(self.db_conn)
                    self.ui.textEdit_Keithley.append(QtCore.QDateTime.currentDateTime().toString()+': '+'connected to DB, '+'DefaultDB.db')
                    print('DefaultDB.db')
                    break
    def onclickDBtab(self,indexoftab):
        if indexoftab:
            self.ui.comboBox_DBTime.clear()
            timecriterialist=DBreadPack.timecriteria
            for i in range(len(timecriterialist)):
                self.ui.comboBox_DBTime.addItem(timecriterialist[i])
                
    def on_combobox_DBTime_changed(self):
        self.ui.comboBox_DBTimeYaxis.clear()
        
        yaxisoptionlist=DBreadPack.fromtocriteria
        for i in range(len(yaxisoptionlist)):
            if 'JV' in self.ui.comboBox_DBTime.currentText():
                if 'MPP' not in yaxisoptionlist[i]:
                    self.ui.comboBox_DBTimeYaxis.addItem(yaxisoptionlist[i])
            elif 'MPP' in self.ui.comboBox_DBTime.currentText():
                if 'JV' not in yaxisoptionlist[i]:
                    self.ui.comboBox_DBTimeYaxis.addItem(yaxisoptionlist[i])
        
        self.ui.comboBox_DBTime_restrictions.clear()
        
        restrictionslist=DBreadPack.fromtocriteria + DBreadPack.dropdowncriteria
            
        for i in range(len(restrictionslist)):
            if 'JV' in self.ui.comboBox_DBTime.currentText():
                if 'MPP' not in restrictionslist[i]:
                    self.ui.comboBox_DBTime_restrictions.addItem(restrictionslist[i])
            elif 'MPP' in self.ui.comboBox_DBTime.currentText():
                if 'JV' not in restrictionslist[i]:
                    self.ui.comboBox_DBTime_restrictions.addItem(restrictionslist[i])

    def on_combobox_DBTimeRestrictions_changed(self):
        try:
            criteria=self.ui.comboBox_DBTime_restrictions.currentText()
            if criteria in DBreadPack.fromtocriteria:
                self.theCursor.execute("SELECT "+criteria.split('.')[1]+" FROM "+criteria.split('.')[0])
                listoptions=list(set([x[0] for x in self.theCursor.fetchall()]))
                minimum=min(listoptions)
                maximum=max(listoptions)
                self.ui.lineEdit_DBTime_From.setText(str(minimum))
                self.ui.lineEdit_DBTime_To.setText(str(maximum))
            elif criteria in DBreadPack.dropdowncriteria:
                self.ui.listWidget_DBTime_Restrictions.clear()
                self.theCursor.execute("SELECT "+criteria.split('.')[1]+" FROM "+criteria.split('.')[0])
                listoptions=list(set([x[0] for x in self.theCursor.fetchall()]))
                for item in listoptions:
                    self.ui.listWidget_DBTime_Restrictions.addItem(str(item))
        except:
            pass
    
    def Addrestriction(self):
        currentrestrictionparam = self.ui.comboBox_DBTime_restrictions.currentText()
        if currentrestrictionparam in DBreadPack.fromtocriteria:
            self.ui.listWidget_DBTime_chosenRestrictions.addItem(currentrestrictionparam+'__'+self.ui.lineEdit_DBTime_From.text()+'__'+self.ui.lineEdit_DBTime_To.text())
        elif currentrestrictionparam in DBreadPack.dropdowncriteria:
            selectedrestparam=self.ui.listWidget_DBTime_Restrictions.selectedItems()
            for i in selectedrestparam:
                self.ui.listWidget_DBTime_chosenRestrictions.addItem(currentrestrictionparam+'__'+i.text())
        self.SearchAndPlot()
        
    def Removerestriction(self):
        self.ui.listWidget_DBTime_chosenRestrictions.takeItem(self.ui.listWidget_DBTime_chosenRestrictions.currentRow())
        self.SearchAndPlot()
        
    def SearchAndPlot(self):
        
        criteria=self.ui.comboBox_DBTimeYaxis.currentText()
        timecrit=self.ui.comboBox_DBTime.currentText()
        # if criteria.split('.')[0]==timecrit.split('.')[0]:#MPP-MPP or JV-JV
        #     self.theCursor.execute("SELECT "+timecrit.split('.')[1]+', ' + criteria.split('.')[1]+" FROM "+criteria.split('.')[0])
        #     results=self.theCursor.fetchall()
        #     date=[datetime.datetime.strptime(x[0],'%Y-%m-%d-%H-%M-%S') for x in results]
        #     ydata=[x[1] for x in results]
        # elif criteria.split('.')[0]=='Refdiode': #JV-Refdiode or MPP-Refdiode
        #     self.theCursor.execute("SELECT "+timecrit +', ' + criteria +" FROM "+criteria.split('.')[0]+', ' + timecrit.split('.')[0] + ' WHERE Refdiode.id = '+ timecrit.split('.')[0]+'.Refdiode_id')
        #     results=self.theCursor.fetchall()
        #     date=[datetime.datetime.strptime(x[0],'%Y-%m-%d-%H-%M-%S') for x in results]
        #     ydata=[x[1] for x in results]
            
        # self.DBgraph.clear()
        # self.DBgraph.plot(date,ydata,'o')
        # self.DBgraph.set_xlabel('Date/Time')
        # self.DBgraph.set_ylabel(criteria.split('.')[1])
        # for tick in self.DBgraph.get_xticklabels():
        #     tick.set_rotation(15)
        # self.fig4.canvas.draw()
        # self.fig4.canvas.flush_events()
        
        
        items = []
        for index in range(self.ui.listWidget_DBTime_chosenRestrictions.count()):
             items.append(self.ui.listWidget_DBTime_chosenRestrictions.item(index).text()) 
             
        criteriaListdetailled=[]
        criteriaListdetailled2=[]
        for item in items:
            if len(item.split('__'))==2:
                criteriaListdetailled.append([item.split('__')[0],[item.split('__')[1]]])
            elif len(item.split('__'))==3:
                criteriaListdetailled2.append([item.split('__')[0],item.split('__')[1],item.split('__')[2]])
        
             
        #get the from
             
        #get where: list of id matches
        #get where: from listbox, blabla = blabli or ...
        #get where: from fromto, (blabla between ll and ll) and ...
        parameterList=[timecrit,criteria]
        parametertables=list(set([x.split('.')[0] for x in parameterList]))
        parametertables=sorted(parametertables, key=lambda s: s.casefold())
        criteriaList=[x.split('__')[0] for x in items]
        tablenames=list(set(["batch","samples"]+[timecrit.split('.')[0],criteria.split('.')[0]]+[x.split('.')[0] for x in criteriaList]))
        
        if criteria.split('.')[0]==timecrit.split('.')[0]:
            SelectInstructions="SELECT "+timecrit +', ' + criteria +" FROM "#+criteria.split('.')[0] + ',samples, batch, cells WHERE '
            for item in tablenames:
                SelectInstructions+=item+', '
            SelectInstructions=SelectInstructions[:-2]+" WHERE "
            wherelist=[criteria.split('.')[0]]
        else:
            SelectInstructions="SELECT "+timecrit +', ' + criteria +" FROM "#+criteria.split('.')[0]+', ' + timecrit.split('.')[0] + ', samples, batch, cells WHERE '
            for item in tablenames:
                SelectInstructions+=item+', '
            SelectInstructions=SelectInstructions[:-2]+" WHERE "
            wherelist=[criteria.split('.')[0]]
             
        items+=[criteria.split('.')[0],timecrit.split('.')[0]]
        # criteriaList=[self.listWidget2.item(i).text() for i in range(self.listWidget2.count())]
        
        # tablenames=list(set(["batch","samples","cells"]+[x.split('.')[0] for x in items]))
        # tablenames=list(set([x.split('.')[0] for x in items]))
        wherelist=["samples.batch_id = batch.id AND "]
        # wherelist=[]
        try:
            for item in tablenames:
                self.theCursor.execute("SELECT * FROM "+item)
                headcol=[x[0] for x in self.theCursor.description]
                headcol=[x[:-3] for x in headcol if '_id' in x]
                for item2 in headcol:
                    if item2 in tablenames:
                        wherelist.append(item+'.'+item2+'_id = '+item2+'.id AND ')
        except:
            pass
        wherelist=list(set(wherelist))
        for item in wherelist:
            SelectInstructions+=item
        for item in criteriaListdetailled:
            SelectInstructions+='('
            for item2 in item[1]:
                SelectInstructions+= item[0]+' = '+"'"+str(item2)+"' OR "
            SelectInstructions=SelectInstructions[:-4]+') AND '
        for item in criteriaListdetailled2:
            SelectInstructions+= '('+item[0] + ' BETWEEN ' + item[1] + ' AND ' + item[2] +') AND '
        
        try:
            self.theCursor.execute(SelectInstructions[:-4])
            data=self.theCursor.fetchall()

            date=[datetime.datetime.strptime(x[0],'%Y-%m-%d-%H-%M-%S') for x in data]
            ydata=[x[1] for x in data]

            self.DBgraph.clear()
            self.DBgraph.plot(date,ydata,'o')
            self.DBgraph.set_xlabel('Date/Time')
            self.DBgraph.set_ylabel(criteria.split('.')[1])
            for tick in self.DBgraph.get_xticklabels():
                tick.set_rotation(15)
            self.fig4.canvas.draw()
            self.fig4.canvas.flush_events()
        except:
            pass

#%%######################################################################################################    
    def UpdateTable(self, listdata):
        
        self.ui.tableWidget.setRowCount(len(listdata.keys()))
        self.ui.tableWidget.setHorizontalHeaderLabels(
            ['Name','Eff. (%)','FF (%)', 'Voc (mV)', 'Jsc (mA/cm2)','Isc (mA)', 
             'Roc (ohm/cm2)', 'Rsc (ohm/cm2)', 'Pmpp (W/m2)', 'Vmpp (mV)', 'Jmpp (mA/cm2)'])
        i=0
        for key in listdata.keys():
            self.ui.tableWidget.setItem(i,0,QTableWidgetItem(listdata[key]['sampleID']))
            self.ui.tableWidget.setItem(i,1,QTableWidgetItem('%.2f' % listdata[key]['Eff']))
            self.ui.tableWidget.setItem(i,2,QTableWidgetItem('%.2f' % listdata[key]['FF']))
            self.ui.tableWidget.setItem(i,3,QTableWidgetItem('%.2f' % listdata[key]['Voc']))
            self.ui.tableWidget.setItem(i,4,QTableWidgetItem('%.2f' % listdata[key]['Jsc']))
            self.ui.tableWidget.setItem(i,5,QTableWidgetItem('%.2f' % listdata[key]['Isc']))
            self.ui.tableWidget.setItem(i,6,QTableWidgetItem('%.2f' % listdata[key]['Roc']))
            self.ui.tableWidget.setItem(i,7,QTableWidgetItem('%.2f' % listdata[key]['Rsc']))
            self.ui.tableWidget.setItem(i,8,QTableWidgetItem('%.2f' % listdata[key]['Pmpp']))
            self.ui.tableWidget.setItem(i,9,QTableWidgetItem('%.2f' % listdata[key]['Vmpp']))
            self.ui.tableWidget.setItem(i,10,QTableWidgetItem('%.2f' % listdata[key]['Jmpp']))   
            self.ui.tableWidget.setItem(i,11,QTableWidgetItem(listdata[key]['datetime'].toString(QtCore.Qt.ISODate)))
            i+=1
            
    def ClearTable(self):
        self.ui.tableWidget.setRowCount(0)
        
        
    def ClearGraph(self,specificgraph):
        if (self.ui.comboBox_cleargraph.currentText()=='Rep' and specificgraph == '0') or specificgraph == 1 or specificgraph =='Rep':
            self.TimegraphIV.clear()
            self.TimegraphIV.set_xlabel('Voltage (V)')
            self.TimegraphIV.set_ylabel('Current density (mA/cm'+'\xb2'+')')
            self.TimegraphIV.axhline(y=0, color='k')
            self.TimegraphIV.axvline(x=0, color='k')
            self.TimegraphStab.clear()
            self.TimegraphStab.set_xlabel('Time (s)')
            self.TimegraphStab.set_ylabel('Current density (mA/cm'+'\xb2'+')')
            self.fig7.canvas.draw_idle()
            
        if (self.ui.comboBox_cleargraph.currentText()=='LIV' and specificgraph == '0') or specificgraph == 1 or specificgraph =='LIV':
            self.JVgraph.clear()
            self.JVgraph.set_xlabel('Voltage (V)')
            self.JVgraph.set_ylabel('Current density (mA/cm'+'\xb2'+')')
            self.JVgraph.axhline(y=0, color='k')
            self.JVgraph.axvline(x=0, color='k')
            self.fig1.canvas.draw_idle()
        if (self.ui.comboBox_cleargraph.currentText()=='DIV' and specificgraph == '0') or specificgraph == 1 or specificgraph =='DIV':
            self.DIVgraphlin.clear()
            self.DIVgraphlogY.clear()
            self.DIVgraphlin.set_xlabel('Voltage (mV)')
            self.DIVgraphlin.set_ylabel('Current density (mA/cm'+'\xb2'+')')
            self.DIVgraphlogY.set_yscale('log')
            self.DIVgraphlogY.set_xlabel('Voltage (mV)')
            self.DIVgraphlogY.set_ylabel('Current density (mA/cm'+'\xb2'+')')
            self.fig3.canvas.draw_idle()
        if (self.ui.comboBox_cleargraph.currentText()=='QSS' and specificgraph == '0') or specificgraph == 1 or 'QSS' in specificgraph :
            if 'Stab' not in specificgraph:
                self.QSSgraphIV.clear()
                self.QSSgraphIV.set_xlabel('Voltage (V)')
                self.QSSgraphIV.set_ylabel('Current density (mA/cm'+'\xb2'+')')
                self.QSSgraphIV.axhline(y=0, color='k')
                self.QSSgraphIV.axvline(x=0, color='k')
            else:
                self.QSSgraphStab.clear()
                self.QSSgraphStabbis.clear()
                self.QSSgraphStab.set_xlabel('Time (s)')
                self.QSSgraphStab.set_ylabel('Current density (mA/cm'+'\xb2'+')')
                self.QSSgraphStabbis.set_ylabel('Voltage (mV)')
                self.QSSgraphStabbis.spines['left'].set_color('red')
                self.QSSgraphStabbis.yaxis.label.set_color('red')
                self.QSSgraphStabbis.tick_params(axis='y', colors='red')
            self.fig6.canvas.draw_idle()
            if (self.ui.comboBox_cleargraph.currentText()=='QSS' and specificgraph == '0') and 'QSS' not in specificgraph :
                self.QSSgraphStab.clear()
                self.QSSgraphStabbis.clear()
                self.QSSgraphStab.set_xlabel('Time (s)')
                self.QSSgraphStab.set_ylabel('Current density (mA/cm'+'\xb2'+')')
                self.QSSgraphStabbis.set_ylabel('Voltage (mV)')
                self.QSSgraphStabbis.spines['left'].set_color('red')
                self.QSSgraphStabbis.yaxis.label.set_color('red')
                self.QSSgraphStabbis.tick_params(axis='y', colors='red')
                self.fig6.canvas.draw_idle()
        if (self.ui.comboBox_cleargraph.currentText()=='MPPT' and specificgraph == '0') or specificgraph == 1 or specificgraph =='MPPT':
            self.MPPTgraph_JV.clear()
            self.MPPTgraph_JV.set_xlabel('Voltage (mV)')
            self.MPPTgraph_JV.set_ylabel('Current density (mA/cm'+'\xb2'+')')
            self.MPPTgraph_TV.clear()
            self.MPPTgraph_TV.set_xlabel('Time (s)')
            self.MPPTgraph_TV.set_ylabel('Voltage (mV)')
            self.MPPTgraph_TJ.clear()
            self.MPPTgraph_TJ.set_xlabel('Time (s)')
            self.MPPTgraph_TJ.set_ylabel('Current density (mA/cm'+'\xb2'+')')
            self.MPPTgraph_TP.clear()
            self.MPPTgraph_TP.set_xlabel('Time (s)')
            self.MPPTgraph_TP.set_ylabel('Power (W/m'+'\xb2'+')')
            self.fig2.canvas.draw_idle()
        if (self.ui.comboBox_cleargraph.currentText()=='StabPowerCurve' and specificgraph == '0') or specificgraph == 1 or 'StabPower' in specificgraph:
            if 'Graph1' in specificgraph:
                self.StabGraph1.clear()
                self.StabGraph1.set_xlabel('Voltage (mV)')
                self.StabGraph1.set_ylabel('Current density (mA/cm'+'\xb2'+')')
            elif 'Graph2' in specificgraph:
                self.StabGraph2.clear()
                self.StabGraph2bis.clear()
                self.StabGraph2.set_xlabel('Time (s)')
                self.StabGraph2.set_ylabel('Power density (mW/cm'+'\xb2'+')')
                self.StabGraph2bis.set_ylabel('Voltage (mV)')
            elif 'Graph3' in specificgraph:
                self.StabGraph3.clear()
                self.StabGraph3.set_xlabel('Voltage (mV)')
                self.StabGraph3().set_ylabel('Power density (mW/cm'+'\xb2'+')')
            elif 'Graph4' in specificgraph:
                self.StabGraph4.clear()
                self.StabGraph4bis.clear()
                self.StabGraph4.set_xlabel('Time (s)')
                self.StabGraph4.set_ylabel('Power density (mW/cm'+'\xb2'+')')
                self.StabGraph4bis.set_ylabel('Voltage (mV)')

    # def updateJVaftermeas(self,data):
    #     global STOPMEAS, AllDATA, lastmeasDATA,lastmeastrackingDATA, RefDiodeChecked, Sunintensity, shutteropen
    #     global aftermpp,boxCurrent, boxVoltage, keithleyAddress
    #     pixcolor=self.pixcolor
    #     direction=self.direction
    #     pixels=self.pixels
    #     Rep=self.Rep
    #     directory=self.directory
    #     allpixtobemeasured=self.allpixtobemeasured
    #     currentlist=data[:,1]
    #     voltagelist=data[:,0]
    #     currentdenlist=[x*1000/self.pixarea for x in data[:,1]] #assume 1sun, and assume keithley gives Amperes back 
         
    #     if direction == 1:#forward scan 
    #         directionstr='fwd' 
    #         self.JVgraph.plot(data[:,0],currentdenlist, linestyle="dashed",color=pixcolor) 
    #     elif direction == 0:#reverse scan 
    #         directionstr='rev' 
    #         self.JVgraph.plot(data[:,0],currentdenlist, linestyle="solid",color=pixcolor) 
    #     self.fig1.canvas.draw_idle() 
    #     polarity='pin'
    #     if self.ui.radioButton_nip.isChecked():
    #         polarity='nip'
    #     if shutteropen: 
    #         illum='lt' 
    #     else: 
    #         illum='dk' 
    #     if illum == 'dk': 
    #         if direction == 1:#forward scan 
    #             self.DIVgraphlin.plot(data[:,0],currentdenlist, linestyle="dashed",color=pixcolor) 
    #         elif direction == 0:#reverse scan 
    #             self.DIVgraphlin.plot(data[:,0],currentdenlist, linestyle="solid",color=pixcolor) 
    #         ydataabs=list(map(lambda x: abs(x),currentdenlist)) 
    #         if direction == 1:#forward scan 
    #             self.DIVgraphlogY.semilogy(data[:,0],ydataabs, linestyle="dashed",color=pixcolor) 
    #         elif direction == 0:#reverse scan 
    #             self.DIVgraphlogY.semilogy(data[:,0],ydataabs, linestyle="solid",color=pixcolor) 
    #         self.fig3.canvas.draw_idle() 
    #         self.fig3.canvas.flush_events() 
 
    #     self.fig1.canvas.flush_events() 
        
    #     if shutteropen:
    #         illum='lt'
    #         self.ClearGraph('LIV')
    #     else:
    #         illum='dk'
    #         self.ClearGraph('DIV')
        
    #     if self.ui.radioButton_Assume1sun.isChecked():
    #         radioButton_Assume1sun='True'
    #     else:
    #         radioButton_Assume1sun='False'
    #     timestr = QtCore.QDateTime.currentDateTime().toString(QtCore.Qt.ISODate)
    #     timestr=timestr.replace(':','').replace('-','')

    #     sample=str(self.ui.lineEdit_SampleName.text()) +'_'+  'pX'+self.currentpixelmeasured +'_'+ directionstr +'_'+ illum +'_'+ 'lp'+str(Rep) +'_'+ timestr  
    #     samplename=str(self.ui.lineEdit_SampleName.text()).replace('-','_')
    #     if '_' in str(self.ui.lineEdit_SampleName.text()):
    #         Batch=str(self.ui.lineEdit_SampleName.text()).split('_')[0]
    #         Substrate=str(self.ui.lineEdit_SampleName.text()).split('_')[1]
    #     else:
    #         Batch='None'
    #         Substrate='None'
        
    #     commenttext=str(self.ui.lineEdit_Comment.text())
    #     if aftermpp:
    #         if 'aftermpp' not in commenttext:
    #             commenttext+='_aftermpp'
        
    #     AllDATA[sample]={'sampleID': sample,'SampleNamePix': str(self.ui.lineEdit_SampleName.text()) +'_'+ self.currentpixelmeasured, 
    #                      'linktorawdata':str(os.path.join(str(directory),sample+'.txt')),'SampleName': samplename,'Batch#':Batch,'Substrate#':Substrate, 'Pixel':self.currentpixelmeasured, 'Allpixs':allpixtobemeasured,
    #                      'ScanDirection': directionstr, 'illum': illum, 'Sunintensity': Sunintensity, 'IsRefDiodeMeasured': RefDiodeChecked, 
    #                      'RefDiodeNomCurr':self.ui.doubleSpinBox_DiodeNominalCurrent.value(),'RefDiodeMeasCurr':self.ui.doubleSpinBox_MeasuredDiodeCurrent.value(),
    #                      'datetime': QtCore.QDateTime.currentDateTime(), 'Comment': commenttext,'temperature':self.ui.doubleSpinBox_Temperature.value(),
    #                      'UserName': str(self.ui.lineEdit_UserName.text()), 'MeasType': str(self.ui.comboBox_MeasType.currentText()),'MeasNowType': 'IV',
    #                      'pixcolor':pixcolor,'RepNumb': Rep,'DelayRep':self.ui.spinBox_RepDelay.value(), 'pixelArea': self.pixarea,'assume1sun':radioButton_Assume1sun,'ShutterOpen':shutteropen,
    #                      'MinVoltage': self.ui.doubleSpinBox_JVminvoltage.value(), 'MaxVoltage': self.ui.doubleSpinBox_JVmaxvoltage.value(),
    #                      'Aftermpp':aftermpp,'StepSize': self.ui.doubleSpinBox_JVstepsize.value(), 'CurrentLimit': self.ui.doubleSpinBox_JVcurrentlimit.value(), 
    #                      'IntegTime': self.ui.doubleSpinBox_JVintegrationtime.value(), 'Delaypts': self.ui.doubleSpinBox_JVdelaypoints.value(), 
    #                      'DelayShutter': self.ui.doubleSpinBox_JVdelayshutter.value(),'polarity':polarity,
    #                      'Voc': -1., 'Jsc': -1., 'Isc': -1., 'FF': -1., 'Eff': -1, 'Pmpp': -1., 'Roc':-1., 'Rsc':-1., 'Jmpp':-1, 'Vmpp':-1,
    #                      'Voltage':voltagelist,'Current':currentlist, 'CurrentDensity': currentdenlist
    #                      }
    #     lastmeasDATA[sample]=AllDATA[sample]

    #     self.AnalysisJV(sample)
    #     self.Savedata(sample,AllDATA)
    #     self.UpdateTable(lastmeasDATA)

# class ThreadStabProtocol(QThread):
    
#     result = pyqtSignal(object)
#     finished = pyqtSignal()
    
#     def __init__(self, pixels, scandirections, keithleyObject, parent=None):
#         QThread.__init__(self, parent)
#         self.pixels = pixels
#         self.scandirections=scandirections
#         self.keithleyObject=keithleyObject
        
#     def run(self):
#         global STOPMEAS, AllDATA, lastmeasDATA,lastmeastrackingDATA, RefDiodeChecked, Sunintensity, shutteropen
#         global aftermpp,boxCurrent, boxVoltage, keithleyAddress,latestVmpp
#         print("stab 2")
#         integtime=window.w.ui.doubleSpinBox_JVintegrationtime.value()
#         # NPLC of 1 with 60Hz power, new value every 16.67ms
#         # integtime=50ms => NPLC = .050*60 = 3
#         NPLC=integtime*60/1000
#         if NPLC>10:
#             NPLC=10
#         if NPLC<0.01:
#             NPLC=0.01
#         polarity='pin'
#         if window.w.ui.radioButton_nip.isChecked():
#             polarity='nip'
#         currentlimit=window.w.ui.doubleSpinBox_JVcurrentlimit.value()
#         prepareCurrent(self.keithleyObject, NPLC,currentlimit,polarity)#prepare to apply a voltage and measure a current

#         for item in range(len(self.pixels)):
#             connectPixel(boxCurrent, boxVoltage, self.pixels[item])
            
#             # a) IV sweep loop, extract approximate Vmp
#             estimatedVmpp=self.takeIVquick(item,polarity,NPLC, currentlimit)
            
#             if STOPMEAS==1:
#                 window.w.sequence=''
#                 break
            
#             # b) start fixedvoltage at Vmp, wait that J stabilizes, then perform minor V variations to find real Vmp, wait stabilizes after each variation of V
#             # mppt with stabilized current at each step
#             #     Pmpp1
#             QtTest.QTest.qWait(500)
#             self.trackingStab(estimatedVmpp,item,polarity,NPLC, currentlimit,'black')
            
#             if STOPMEAS==1:
#                 window.w.sequence=''
#                 break
            
#             # c)      change V step-wise towards V=0, wait for J to stabilise at each step. until V=-0.02*Voc
#             self.takeIVstab(item,polarity,NPLC, currentlimit,-1,estimatedVmpp)
#             if STOPMEAS==1:
#                 window.w.sequence=''
#                 break
            
#             # d) back to V=Vmp in one step, check current for comparison with b)
#             #     Pmpp2
#             QtTest.QTest.qWait(500)
#             self.trackingStab(estimatedVmpp,item,polarity,NPLC, currentlimit,'red')
            
#             if STOPMEAS==1:
#                 window.w.sequence=''
#                 break
            
#             # e)      change V step-wise towards V=Voc, with for J to stabilise at each step. until V=1.01*Voc
#             self.takeIVstab(item,polarity,NPLC, currentlimit,1,estimatedVmpp)
#             if STOPMEAS==1:
#                 window.w.sequence=''
#                 break
            
#             # f) back to V=Vmp in one step, check current for comparison with b)
#             #     Pmpp3
#             QtTest.QTest.qWait(500)
#             self.trackingStab(estimatedVmpp,item,polarity,NPLC, currentlimit,'blue')
            
#             if STOPMEAS==1:
#                 window.w.sequence=''
#                 break
            
            
#             # g) repeat b-f to get 2nd IV curve
            
            
#             # h) repeat a) for comparison
#             estimatedVmpp=self.takeIVquick(item,polarity,NPLC, currentlimit)
            
            
#             if STOPMEAS==1:
#                 window.w.sequence=''
#                 break
        
#         QtTest.QTest.qWait(100) # if this is not here, then the finished signal function finishes before the result signal function finishes, causing plotting problems
#         self.finished.emit()
        
#     def takeIVstab(self,item,polarity,NPLC, currentlimit,direction,estimatedVmpp):
#         global STOPMEAS, AllDATA, lastmeasDATA,lastmeastrackingDATA, RefDiodeChecked, Sunintensity, shutteropen
#         global aftermpp,boxCurrent, boxVoltage, keithleyAddress,latestVmpp
#         print('take IV stab')
        
#         stabcurrent=[]
#         stabvoltage=[]
#         stabpower=[]
        
#         #how to make the voltage steps non-linear, more pts towards mpp??
        
#         appliedvoltage=estimatedVmpp
#         # vstepJ=100
#         # vstepV=10
        
#         window.w.ClearGraph('StabPower_Graph2')
            
#         nbpts=window.w.ui.doubleSpinBox_StepJV_NbPts.value()
#         if direction==1:
#             print('towards jsc')
#             vstep=estimatedVmpp/(nbpts-1)
#             elapsed_timer = QtCore.QElapsedTimer()
#             elapsed_timer.start()
#             while(appliedvoltage>=-vstep):
#                 #move to next voltage
#                 #check stability FV
#                 if STOPMEAS==1:
#                     window.w.sequence=''
#                     break
            
#                 stabJVdata=self.FVforJV(appliedvoltage,polarity,elapsed_timer)
                
#                 #get V and J, plot on graph
#                 stabcurrent.append(stabJVdata[2])
#                 stabvoltage.append(stabJVdata[1])
#                 stabpower.append(stabJVdata[0])
                
#                 window.w.StabGraph3.plot(stabJVdata[1],stabJVdata[0], 'ro')
#                 window.w.fig5.canvas.draw_idle()
#                 window.w.fig5.canvas.flush_events()
#                 appliedvoltage-=vstep
                
            
#         elif direction==-1:
#             print('towards Voc')
#             vstep=estimatedVmpp/(0.7*(nbpts-1))
#             #FV for doubleSpinBox_StepJV_timestepJV, unless stable before over doubleSpinBox_StepJV_TimeDev
#             elapsed_timer = QtCore.QElapsedTimer()
#             elapsed_timer.start()
#             while(True):
#                 #move to next voltage
#                 #check stability FV
#                 if STOPMEAS==1:
#                     window.w.sequence=''
#                     break
            
#                 stabJVdata=self.FVforJV(appliedvoltage,polarity,elapsed_timer)
                
#                 #get V and J, plot on graph
#                 stabcurrent.append(stabJVdata[2])
#                 stabvoltage.append(stabJVdata[1])
#                 stabpower.append(stabJVdata[0])
#                 if stabJVdata[8]==1:
#                     window.w.StabGraph3.plot(stabJVdata[1],stabJVdata[0], 'ro')
#                 else:
#                     window.w.StabGraph3.plot(stabJVdata[1],stabJVdata[0], 'go')
#                 window.w.fig5.canvas.draw_idle()
#                 window.w.fig5.canvas.flush_events()
#                 appliedvoltage+=vstep
#                 if len(stabcurrent)>1:
#                     if np.sign(stabcurrent[-2])!=np.sign(stabcurrent[-1]):
#                         break
                
#             #move to next voltage
#             #repeat, until J change of sign
            
            
#     def FVforJV(self,appliedvoltage,polarity,elapsed_timer):
#         global version

#         voltagefixed=appliedvoltage
#         pixarea=window.w.ui.doubleSpinBox_pixXarea.value()
#         nMeas = 2
#         timelist=[]
#         currentlist=[]
#         currentdensitylist=[]
#         voltagelist=[]
#         powerlist=[]
#         timestartingnewFV=float(elapsed_timer.elapsed()/1000)
#         notstabilized=0
#         duration=window.w.ui.doubleSpinBox_StepJV_MaxDur.value()
#         timestablecrit=window.w.ui.doubleSpinBox_StepJV_TimeDev.value()
#         while True:
#             delay=window.w.ui.doubleSpinBox_MPPTdelaypoints.value()
#             dataCurrent=measureCurrent(self.keithleyObject,voltagefixed/1000,nMeas,polarity = polarity)
#             currentden=1000*mean(dataCurrent[:,1])/pixarea #mA/cm2
#             current=mean(dataCurrent[:,1]) #A
#             currentlist.append(float(current))
#             currentdensitylist.append(float(currentden))
#             voltagelist.append(float(voltagefixed)/1000)  #mV
#             powerlist.append(float(currentden*voltagefixed/1000)/Sunintensity)
#             timelist.append(float(elapsed_timer.elapsed()/1000))
#             # plotting
#             window.w.StabGraph2.plot(timelist,powerlist, linestyle="solid",color='black')
#             window.w.StabGraph2bis.plot(timelist,voltagelist, linestyle="solid",color='red')
#             window.w.fig5.canvas.draw_idle()
#             window.w.fig5.canvas.flush_events()
#             QtTest.QTest.qWait(int(delay))
#             #check for deviation criteria over last x seconds
#             if STOPMEAS==1:
#                 window.w.sequence=''
#                 break
#             if float(elapsed_timer.elapsed()/1000)-timestartingnewFV>duration:
#                 notstabilized=1
#                 print('notstabilized')
#                 break
#             if float(elapsed_timer.elapsed()/1000)-timestartingnewFV > timestablecrit:
#                 timeitem=len(timelist)-1
#                 print(timeitem)
#                 print(timelist[timeitem])
#                 powerlistforavg=[]
#                 currentlistforavg=[]
#                 while(timelist[timeitem]-timestartingnewFV>float(elapsed_timer.elapsed()/1000)-timestartingnewFV-timestablecrit):
#                     powerlistforavg.insert(0,powerlist[timeitem])
#                     currentlistforavg.insert(0,currentdensitylist[timeitem])
#                     timeitem-=1
#                 averageofpower=mean(powerlistforavg)
#                 averageofcurrent=mean(currentlistforavg)
#                 stdofpower=np.std(powerlistforavg)
#                 print('avg: '+str(averageofpower)+'; std: '+str(stdofpower))
#                 if 100*stdofpower/averageofpower < window.w.ui.doubleSpinBox_StepJV_DevCrit.value():
#                     # stabavgpowerlist.append(averageofpower)
#                     # stabvoltagelist.append(float(voltagefixed)/1000)
#                     print('criteria fullfilled: '+str(averageofpower))
#                     break
#         return [averageofpower,voltagefixed,averageofcurrent,timelist,currentlist,currentdensitylist,voltagelist,powerlist,notstabilized]
        
#     def takeIVquick(self,item,polarity,NPLC, currentlimit):
#         #to do: data saving
        
#         global STOPMEAS, AllDATA, lastmeasDATA,lastmeastrackingDATA, RefDiodeChecked, Sunintensity, shutteropen
#         global aftermpp,boxCurrent, boxVoltage, keithleyAddress,latestVmpp
#         minV=window.w.ui.doubleSpinBox_JVminvoltage.value()/1000
#         maxV=window.w.ui.doubleSpinBox_JVmaxvoltage.value()/1000
#         stepV=window.w.ui.doubleSpinBox_JVstepsize.value()/1000
#         delay=window.w.ui.doubleSpinBox_JVdelaypoints.value()
#         direction=0#reverse
#         data=takeIV(self.keithleyObject, minV,maxV,stepV,delay,direction,polarity,NPLC, currentlimit)
#         if keithleyAddress[0]=='Test':
#             QtTest.QTest.qWait(200)
        
#         data=[direction,item,data]
#         self.result.emit(data)
#         #estimate Vmpp
#         QtTest.QTest.qWait(500)
#         print('Vmpp reverse: ', latestVmpp)
#         Vmppreverse=latestVmpp

#         direction=1#forward
#         data=takeIV(self.keithleyObject, minV,maxV,stepV,delay,direction,polarity,NPLC, currentlimit)
#         if keithleyAddress[0]=='Test':
#             QtTest.QTest.qWait(200)
        
#         data=[direction,item,data]
#         self.result.emit(data)
#         #estimate Vmpp
#         QtTest.QTest.qWait(500)
#         print('Vmpp forward: ', latestVmpp)
#         Vmppforward=latestVmpp

#         estimatedVmpp=(Vmppreverse+Vmppforward)/2 #take the average
#         return estimatedVmpp
        
#     def trackingStab(self,estimVmpp,item,polarity,NPLC, currentlimit, pixcolor):
#         #todo: data saving
        
        
#         print('\ntrackingStab: ',estimVmpp)
#         global STOPMEAS,STOPMEASMPP,version
#         STOPMEASMPP=0
#         nMeas = 2
#         timelist=[]
#         currentlist=[]
#         currentdensitylist=[]
#         voltagelist=[]
#         powerlist=[]
#         stabavgpowerlist=[]
#         stabvoltagelist=[]
#         steplist=[]
#         delaylist=[]
        
#         totalduration=window.w.ui.doubleSpinBox_StepJV_MaxDurTotal.value()
#         duration=window.w.ui.doubleSpinBox_StepJV_MaxDur.value()
#         timestablecrit=window.w.ui.doubleSpinBox_StepJV_TimeDev.value()
        
#         # initialvoltage=self.ui.doubleSpinBox_MPPTstartvoltage.value()
#         # initialdelay=self.ui.doubleSpinBox_MPPTdelaypoints.value()
#         # initialstep=self.ui.spinBox_MPPTstepsize.value()
#         if version != '1pixel': 
#             pixarea=eval('window.w.ui.doubleSpinBox_pix'+self.pixels[item]+'area.value()')
#         else:
#             pixarea=window.w.ui.doubleSpinBox_pixXarea.value()
        

#         elapsed_timer = QtCore.QElapsedTimer()
#         elapsed_timer.start()
#         if window.w.ui.checkBox_MPPTlighton.isChecked():
#             window.w.shutter('OpenShutter',self.keithleyObject)
#         else:
#             window.w.shutter('CloseShutter',self.keithleyObject)
            
#         voltagefixed=estimVmpp
#         delay=window.w.ui.doubleSpinBox_MPPTdelaypoints.value()
#         step=window.w.ui.spinBox_MPPTstepsize.value()
        
#         # FV at estimated Vmpp, 
#         # if stable within limits for time criteria, then compare power and decide if + or - vstep,
#         # if unstable, put data in red, and keep same V, repeat
#         # plot power vs time live
#         # colored scheme to show if stabilized or not: green data
        
        
#         dataCurrent=measureCurrent(self.keithleyObject,voltagefixed/1000,nMeas,polarity = polarity)
#         # currentden=1000*abs(mean(dataCurrent[:,1]))/pixarea
#         # current=abs(mean(dataCurrent[:,1]))
#         currentden=1000*mean(dataCurrent[:,1])/pixarea
#         current=mean(dataCurrent[:,1])
        
#         currentlist.append(current)
#         currentdensitylist.append(currentden)
#         voltagelist.append(voltagefixed)
#         powerlist.append(currentden*voltagefixed/1000/Sunintensity)
#         stabavgpowerlist.append(currentden*voltagefixed/1000/Sunintensity)
#         stabvoltagelist.append(voltagefixed)
#         timelist.append(float(elapsed_timer.elapsed()/1000))
#         steplist.append(step)
#         delaylist.append(delay)
        
#         # voltagefixed+=step
                    
#         while True:
#             print('starting loop, V=',voltagefixed)
#             step=window.w.ui.spinBox_MPPTstepsize.value()
            
#             timestartingnewFV=float(elapsed_timer.elapsed()/1000)
#             notstabilized=0
            
#             while True:
#                 delay=window.w.ui.doubleSpinBox_MPPTdelaypoints.value()
#                 dataCurrent=measureCurrent(self.keithleyObject,voltagefixed/1000,nMeas,polarity = polarity)
#                 currentden=1000*mean(dataCurrent[:,1])/pixarea #mA/cm2
#                 current=mean(dataCurrent[:,1]) #A
#                 currentlist.append(float(current))
#                 currentdensitylist.append(float(currentden))
#                 voltagelist.append(float(voltagefixed))#/1000))  #mV
#                 powerlist.append(float(currentden*voltagefixed/1000)/Sunintensity)
#                 timelist.append(float(elapsed_timer.elapsed()/1000))
#                 steplist.append(step)
#                 delaylist.append(delay)
#                 # plotting
#                 window.w.ClearGraph('StabPower_Graph4')
#                 window.w.StabGraph4.plot(timelist,powerlist, linestyle="solid",color=pixcolor)
#                 window.w.StabGraph4bis.plot(timelist,voltagelist, linestyle="dashed",color=pixcolor)
#                 window.w.fig5.canvas.draw_idle()
#                 window.w.fig5.canvas.flush_events()
#                 QtTest.QTest.qWait(int(delay))
#                 #check for deviation criteria over last x seconds
#                 if float(elapsed_timer.elapsed()/1000)-duration > timestartingnewFV:
#                     notstabilized=1
#                     print('notstabilized')
#                     break
#                 if float(elapsed_timer.elapsed()/1000) > totalduration or STOPMEASMPP==1 or STOPMEAS==1:
#                     print('overtime')
#                     break
#                 if float(elapsed_timer.elapsed()/1000)-timestablecrit >= timestartingnewFV:
#                     timeitem=len(timelist)-1
#                     powerlistforavg=[]
#                     while(timelist[timeitem]>float(elapsed_timer.elapsed()/1000)-timestablecrit):
#                         powerlistforavg.insert(0,powerlist[timeitem])
#                         timeitem-=1
#                     averageofpower=mean(powerlistforavg)
#                     stdofpower=np.std(powerlistforavg)
#                     print('avg: '+str(averageofpower)+'; std: '+str(stdofpower))
#                     if 100*stdofpower/averageofpower < window.w.ui.doubleSpinBox_StepJV_DevCrit.value():
#                         stabavgpowerlist.append(averageofpower)
#                         stabvoltagelist.append(float(voltagefixed))
#                         print('criteria fullfilled: '+str(stabavgpowerlist[-1]))
#                         break
#             # check how the power varied and decide if voltagefixed + or - step
#             if notstabilized:
#                 voltagefixed=voltagefixed #if not stabilized, then status quo: we keep it going at same V
#             elif abs(voltagefixed)>=abs(window.w.ui.doubleSpinBox_MPPTvoltagelimit.value()):
#                 if voltagefixed>0:
#                     voltagefixed-=step
#                 else:
#                     voltagefixed+=step
#             else:
#                 try:
#                     if stabavgpowerlist[-1]>stabavgpowerlist[-2]:
#                         if stabvoltagelist[-1]>stabvoltagelist[-2]:
#                             voltagefixed+=step
#                         else:
#                             voltagefixed-=step
#                     else:
#                         if stabvoltagelist[-1]>stabvoltagelist[-2]:
#                             voltagefixed-=step
#                         else:
#                             voltagefixed+=step
#                 except IndexError:
#                     pass
            
#             QtTest.QTest.qWait(int(delay))
#             print('elapsedtime= ',float(elapsed_timer.elapsed()/1000))
#             if float(elapsed_timer.elapsed()/1000)>totalduration:
#                 STOPMEASMPP=1
#             if STOPMEASMPP==1:#stops ongoing meas of pixel to pass to the next pixel
#                 break
#             if STOPMEAS==1:#will stop all measurement and pass to the next step of sequence
#                 window.w.sequence=''
#                 break
                    
#         #saving data
        
        
#         if len(stabavgpowerlist)>1:
#             estimatedVmpp=stabavgpowerlist[-1]
#         else:
#             estimatedVmpp=-1 #we cannot estimate the Vmpp, as the cell never stabilized within criteria
        
#         return estimatedVmpp
        
class ThreadtakeLongTermTesting(QThread):
    
    result = pyqtSignal(object)
    finished = pyqtSignal(object)
    
    def __init__(self, pixels, scandirections, keithleyObject, parent=None):
        QThread.__init__(self, parent)
        self.pixels = pixels
        self.scandirections=scandirections
        self.keithleyObject=keithleyObject
        
    def run(self):
        global STOPMEAS, AllDATA, lastmeasDATA,lastmeastrackingDATA, RefDiodeChecked, Sunintensity, shutteropen
        global aftermpp,boxCurrent, boxVoltage, keithleyAddress
        
        """
        if JV scans check, then start with JV scan and determine vmpp. time tracking is then the interval.
        if no JV scan, vmpp assumed to be equal to spec bias for the start. time tracking is then open ended. 
        
        mppt: start with either vmpp or vspec
        if Vmpp is not defined because no JV, then Vmpp = Vspec. and 'Vbias at Vmpp' and 'Vbias at specified' are the same
        
        
        """
        
    
class ThreadtakeQSS(QThread):
    
    result = pyqtSignal(object)
    finished = pyqtSignal(object)
    
    def __init__(self, pixels, scandirections, keithleyObject, parent=None):
        QThread.__init__(self, parent)
        self.pixels = pixels
        self.scandirections=scandirections
        self.keithleyObject=keithleyObject
        
    def run(self):
        global STOPMEAS, AllDATA, lastmeasDATA,lastmeastrackingDATA, RefDiodeChecked, Sunintensity, shutteropen
        global aftermpp,boxCurrent, boxVoltage, keithleyAddress
        integtime=window.w.ui.doubleSpinBox_JVintegrationtime.value()
        # NPLC of 1 with 60Hz power, new value every 16.67ms
        # integtime=50ms => NPLC = .050*60 = 3
        NPLC=integtime*60/1000
        if NPLC>10:
            NPLC=10
        if NPLC<0.01:
            NPLC=0.01
        polarity='pin'
        if not window.w.ui.checkBox_pin.isChecked():
            polarity='nip'
        
        item=0
        connectPixel(boxCurrent, boxVoltage, self.pixels[item])
        STOPMEAS=0
        STOPMEASMPP=0
        nMeas = 2
        timelist=[]
        currentlist=[]
        currentdensitylist=[]
        voltagelist=[]
        voltagestablist=[]
        powerstablist=[]
        notstabilizedlist=[]
        steplist=[]
        delaylist=[]
        
        stabcurrentdensity=[]
        stabpower=[]
        nbpts=window.w.ui.doubleSpinBox_QSS_Nbpts.value()
        Voc=window.w.ui.doubleSpinBox_QSS_VocEstim.value()
        print('voc1: ',Voc)
        #tracking Voc
        prepareVoltage(self.keithleyObject, NPLC = 1,voltlimit = 10, polarity=polarity)#prepare to apply a current and measure a voltage
        elapsed_timer = QtCore.QElapsedTimer()
        elapsed_timer.start()
        duration=window.w.ui.doubleSpinBox_QSS_TimeMax4Fail.value()
        timestablecrit=window.w.ui.doubleSpinBox_QSS_TimeDev.value()
        # print('tracking Voc 1')
        while True:
            delay=window.w.ui.doubleSpinBox_MPPTdelaypoints.value()
            if delay<200:
                delay=200
                window.w.ui.doubleSpinBox_MPPTdelaypoints.setValue(200)
            dataVoltage=measureVoltage(self.keithleyObject,0,nMeas,polarity = polarity)
            voltage=abs(mean(dataVoltage[:,0]))
            voltagestablist.append(voltage*1000)
            # print(voltage)
            currentdensitylist.append(0)
            currentlist.append(0)
            powerstablist.append(0)
            timelist.append(float(elapsed_timer.elapsed()/1000))
            # print(timelist[-1])
            window.w.QSSgraphStab.plot(timelist,currentdensitylist, linestyle="solid",color='black')
            window.w.QSSgraphStabbis.plot(timelist,voltagestablist, linestyle="solid",color='red')
            window.w.fig6.canvas.draw_idle()
            window.w.fig6.canvas.flush_events()
            
            QtTest.QTest.qWait(int(delay))
            
            if STOPMEAS==1 or STOPMEASMPP==1:
                print('tracking Voc 2')
                window.w.sequence=''
                notstabilized=1
                notstabilizedlist.append(1)
                # Voc=0
                break
            if float(elapsed_timer.elapsed()/1000)>duration:
                print('tracking Voc 3')
                notstabilized=1
                window.w.ui.textEdit_Keithley.append(QtCore.QDateTime.currentDateTime().toString()+': '+'notstabilized')
                # print('notstabilized')
                notstabilizedlist.append(1)
                # Voc=0
                timeitem=len(timelist)-1
                voltagelistforavg=[]
                while(timelist[timeitem]>float(elapsed_timer.elapsed()/1000)-timestablecrit):
                    voltagelistforavg.insert(0,voltagestablist[timeitem])
                    timeitem-=1
                averageofvoltage=mean(voltagelistforavg)
                stdofvoltage=mean(voltagelistforavg)
                break
            if float(elapsed_timer.elapsed()/1000)> timestablecrit:
                print('tracking Voc 4')
                timeitem=len(timelist)-1
                voltagelistforavg=[]
                # print(timelist)
                timeelapsednow=float(elapsed_timer.elapsed()/1000)-timestablecrit
                # print(timeelapsednow)
                if timeelapsednow <0: 
                    timeelapsednow=0
                while(timelist[timeitem]>timeelapsednow and timeitem>0):
                    # print(timeitem)
                    # print(timelist[timeitem])
                    voltagelistforavg.insert(0,voltagestablist[timeitem])
                    timeitem-=1
                    
                averageofvoltage=mean(voltagelistforavg)
                stdofvoltage=np.std(voltagelistforavg)
                if 100*stdofvoltage/averageofvoltage < window.w.ui.doubleSpinBox_QSS_DevCrit.value():
                    window.w.ui.textEdit_Keithley.append(QtCore.QDateTime.currentDateTime().toString()+': '+'criteria fullfilled: '+str(averageofvoltage))
                    print('criteria fullfilled: '+str(averageofvoltage))
                    Voc=averageofvoltage
                    notstabilized=0
                    notstabilizedlist.append(0)
                    break
        if notstabilized:
            window.w.QSSgraphIV.plot(Voc/1000,0, 'ro')#Voc is still the same as the origina estimate
            window.w.fig6.canvas.draw_idle()
            window.w.fig6.canvas.flush_events()
        else:
            window.w.QSSgraphIV.plot(Voc/1000,0, 'go')#Voc is the new stabilized Voc
            window.w.fig6.canvas.draw_idle()
            window.w.fig6.canvas.flush_events()
        #then use the stab Voc to calculate the distribution of points
        currentlimit=window.w.ui.doubleSpinBox_JVcurrentlimit.value()
        prepareCurrent(self.keithleyObject, NPLC,currentlimit,polarity)#prepare to apply a voltage and measure a current
        # a=3
        # b=0.1
        # c=10
        # f = lambda x: a*x**3 +b*x**2 + c*x
        
        # voltagelist=[f(i) for i in range(-int(0.6667*nbpts),int(0.3333*nbpts)+1,1)]
        # voltagelist=[voltagelist[i]+abs(voltagelist[0]) for i in range(len(voltagelist))]
        # voltagelist=[Voc*voltagelist[i]/voltagelist[-1] for i in range(len(voltagelist))]
        # voltagelist=sorted(voltagelist[:-1],reverse=True)#need to be chosen by user. now by default it's reverse
        print('voc2: ',Voc)
        Vocestimate=Voc
        Vmppestimate=window.w.ui.doubleSpinBox_QSS_VmppEstim.value()
        # Vocestimate=1200
        # Vmppestimate=1100
        if nbpts<5:
            voltagelist=[0,Vmppestimate,Vocestimate]
        elif nbpts==5:
            voltagelist=[0,2.5*Vmppestimate-(Vocestimate/2),Vmppestimate,(Vocestimate-Vmppestimate)/2,Vocestimate]
        else:
            voltagelist=[0,2.5*Vmppestimate-(Vocestimate/2),Vmppestimate,(Vocestimate-Vmppestimate)/2,Vocestimate]
            density=window.w.ui.spinBox_QSS_mppptsdensity.value()
            firstinterval=int(math.floor(nbpts/(2+density)))
            firstintervallist=[0]
            thirdinterval=int(math.floor(nbpts/(2+density)))
            thirdintervallist=[Vocestimate]
            secondinterval=int(nbpts-firstinterval-thirdinterval)
            secondintervallist=[1.5*Vmppestimate-(Vocestimate/2),Vmppestimate,(Vocestimate+Vmppestimate)/2]
            
            #1st and last intervals: add n-1 pts
            for item0 in range(1,firstinterval,1):
                firstintervallist.append(firstintervallist[0]+item0*secondintervallist[0]/firstinterval)
            for item0 in range(1,thirdinterval,1):
                thirdintervallist.append(thirdintervallist[0]-item0*(thirdintervallist[0]-secondintervallist[-1])/thirdinterval)
            if secondinterval>3:
                secondintervallist1=[]
                for item0 in range(0,secondinterval,1):
                    secondintervallist1.append(secondintervallist[0]+item0*(secondintervallist[2]-secondintervallist[0])/(secondinterval-1))
                secondintervallist=secondintervallist1
            voltagelist=firstintervallist+secondintervallist+thirdintervallist
        
        if window.w.ui.comboBox_QSS_ScanDir.currentText()=='Reverse':
            voltagelist=sorted(voltagelist,reverse=True)[1:]
        # elapsed_timer = QtCore.QElapsedTimer()
        # elapsed_timer.start()
        for appliedvoltage in voltagelist:
            if STOPMEAS==1:
                window.w.sequence=''
                break
            #[averageofpower,voltagefixed,-averageofcurrent,timelist,currentlist,currentdensitylist,voltagelist,powerlist,notstabilized]
            stabJVdata=self.FVforJV(appliedvoltage,polarity,elapsed_timer)#appliedvoltage given in mV
            
            #get V and J, plot on graph
            stabcurrentdensity.append(stabJVdata[2])
            stabpower.append(stabJVdata[0])
            timelist+=stabJVdata[3]
            currentlist+=stabJVdata[4]
            currentdensitylist+=stabJVdata[5]
            voltagestablist+=stabJVdata[6]
            powerstablist+=stabJVdata[7]
            notstabilizedlist.append(stabJVdata[8])
            
            if stabJVdata[8]:
                window.w.QSSgraphIV.plot(stabJVdata[1]/1000,stabJVdata[2], 'ro')#plot in V and mA/cm2
                window.w.fig6.canvas.draw_idle()
                window.w.fig6.canvas.flush_events()
            else:
                window.w.QSSgraphIV.plot(stabJVdata[1]/1000,stabJVdata[2], 'go')
                window.w.fig6.canvas.draw_idle()
                window.w.fig6.canvas.flush_events()
        voltagelist=voltagelist[:len(notstabilizedlist)-1]
        voltagelist=[Voc]+voltagelist
        voltagelist=[x/1000 for x in voltagelist]
        stabcurrent=[x*window.w.ui.doubleSpinBox_pixXarea.value() for x in stabcurrentdensity]
        data=[voltagelist,[0]+stabcurrentdensity,[0]+stabcurrent,timelist,currentlist,currentdensitylist,voltagestablist,powerstablist,notstabilizedlist]
        QtTest.QTest.qWait(100) # if this is not here, then the finished signal function finishes before the result signal function finishes, causing plotting problems
        direction=self.scandirections[0]
        data=[direction,0,data]
        self.finished.emit(data)
        
    def FVforJV(self,appliedvoltage,polarity,elapsed_timer):

        voltagefixed=appliedvoltage
        pixarea=window.w.ui.doubleSpinBox_pixXarea.value()
        nMeas = 2
        timelist=[]
        currentlist=[]
        currentdensitylist=[]
        voltagelist=[]
        powerlist=[]
        timestartingnewFV=float(elapsed_timer.elapsed()/1000)
        notstabilized=0
        duration=window.w.ui.doubleSpinBox_QSS_TimeMax4Fail.value()
        timestablecrit=window.w.ui.doubleSpinBox_QSS_TimeDev.value()
        while True:
            delay=window.w.ui.doubleSpinBox_MPPTdelaypoints.value()
            if delay<200:
                delay=200
                window.w.ui.doubleSpinBox_MPPTdelaypoints.setValue(200)
            dataCurrent=measureCurrent(self.keithleyObject,voltagefixed/1000,nMeas,polarity = polarity)
            currentden=1000*mean(dataCurrent[:,1])/pixarea #mA/cm2
            current=mean(dataCurrent[:,1]) #A
            currentlist.append(float(current))
            currentdensitylist.append(float(currentden))
            voltagelist.append(float(voltagefixed))  #mV
            powerlist.append(float(currentden*voltagefixed/1000)/Sunintensity)
            timelist.append(float(elapsed_timer.elapsed()/1000))
            # plotting
            window.w.QSSgraphStab.plot(timelist,currentdensitylist, linestyle="solid",color='black')
            window.w.QSSgraphStabbis.plot(timelist,voltagelist, linestyle="solid",color='red')
            window.w.fig6.canvas.draw_idle()
            window.w.fig6.canvas.flush_events()
            QtTest.QTest.qWait(int(delay))
            #check for deviation criteria over last x seconds
            if STOPMEAS==1:
                window.w.sequence=''
                notstabilized=1
                return [0,voltagefixed,0,timelist,currentlist,currentdensitylist,voltagelist,powerlist,notstabilized]
            if float(elapsed_timer.elapsed()/1000)-timestartingnewFV>duration:
                notstabilized=1
                window.w.ui.textEdit_Keithley.append(QtCore.QDateTime.currentDateTime().toString()+': '+'notstabilized')
                # print('notstabilized')
                timeitem=len(timelist)-1
                powerlistforavg=[]
                currentlistforavg=[]
                while(timelist[timeitem]-timestartingnewFV>float(elapsed_timer.elapsed()/1000)-timestartingnewFV-timestablecrit):
                    powerlistforavg.insert(0,powerlist[timeitem])
                    currentlistforavg.insert(0,currentdensitylist[timeitem])
                    timeitem-=1
                averageofpower=mean(powerlistforavg)
                averageofcurrent=mean(currentlistforavg)
                return [averageofpower,voltagefixed,-averageofcurrent,timelist,currentlist,currentdensitylist,voltagelist,powerlist,notstabilized]
            if float(elapsed_timer.elapsed()/1000)-timestartingnewFV > timestablecrit:
                timeitem=len(timelist)-1
                powerlistforavg=[]
                currentlistforavg=[]
                while(timelist[timeitem]-timestartingnewFV>float(elapsed_timer.elapsed()/1000)-timestartingnewFV-timestablecrit and timeitem>0):
                    powerlistforavg.insert(0,powerlist[timeitem])
                    currentlistforavg.insert(0,currentdensitylist[timeitem])
                    timeitem-=1
                averageofpower=mean(powerlistforavg)
                averageofcurrent=mean(currentlistforavg)
                # stdofpower=np.std(powerlistforavg)
                stdofcurrent=np.std(currentlistforavg)
                if 100*stdofcurrent/averageofcurrent < window.w.ui.doubleSpinBox_QSS_DevCrit.value():
                    # stabavgpowerlist.append(averageofpower)
                    # stabvoltagelist.append(float(voltagefixed)/1000)
                    window.w.ui.textEdit_Keithley.append(QtCore.QDateTime.currentDateTime().toString()+': '+'criteria fullfilled: '+str(averageofcurrent))
                    # print('criteria fullfilled: '+str(averageofcurrent))
                    break
        return [averageofpower,voltagefixed,-averageofcurrent,timelist,currentlist,currentdensitylist,voltagelist,powerlist,notstabilized]

        
    
class ThreadtakeIV(QThread):
    
    result = pyqtSignal(object)
    finished = pyqtSignal()
    
    def __init__(self, pixels, scandirections, keithleyObject, parent=None):
        QThread.__init__(self, parent)
        self.pixels = pixels
        self.scandirections=scandirections
        self.keithleyObject=keithleyObject
        
    def run(self):
        global STOPMEAS, AllDATA, lastmeasDATA,lastmeastrackingDATA, RefDiodeChecked, Sunintensity, shutteropen
        global aftermpp,boxCurrent, boxVoltage, keithleyAddress
        integtime=window.w.ui.doubleSpinBox_JVintegrationtime.value()
        # NPLC of 1 with 60Hz power, new value every 16.67ms
        # integtime=50ms => NPLC = .050*60 = 3
        NPLC=integtime*60/1000
        if NPLC>10:
            NPLC=10
        if NPLC<0.01:
            NPLC=0.01
        polarity='pin'
        if not window.w.ui.checkBox_pin.isChecked():
            polarity='nip'
        currentlimit=window.w.ui.doubleSpinBox_JVcurrentlimit.value()
        prepareCurrent(self.keithleyObject, NPLC,currentlimit,polarity)#prepare to apply a voltage and measure a current

        for item in range(len(self.pixels)):
            connectPixel(boxCurrent, boxVoltage, self.pixels[item])
            
            for direction in self.scandirections:
                minV=window.w.ui.doubleSpinBox_JVminvoltage.value()/1000
                maxV=window.w.ui.doubleSpinBox_JVmaxvoltage.value()/1000
                stepV=window.w.ui.doubleSpinBox_JVstepsize.value()/1000
                delay=window.w.ui.doubleSpinBox_JVdelaypoints.value()
                data=takeIV(self.keithleyObject, minV,maxV,stepV,delay,direction,polarity,NPLC, currentlimit)

                if keithleyAddress[0]=='Test':
                    QtTest.QTest.qWait(500)
                
                data=[direction,item,data]
                self.result.emit(data)
                                
                if STOPMEAS==1:
                    break
            if STOPMEAS==1:
                break
            
        
        QtTest.QTest.qWait(100) # if this is not here, then the finished signal function finishes before the result signal function finishes, causing plotting problems
        self.finished.emit()
        

#%%######################################################################################################
class Window(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        
        self.resize(150, 100)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)
        self.setMinimumSize(QtCore.QSize(430, 92))
        self.gridLayout = QtWidgets.QGridLayout(self)
        self.setWindowTitle("Simulation or Reality?")
        self.pushButton_Simulation = QtWidgets.QPushButton("Simulation mode", self)
        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.ButtonText, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.ButtonText, brush)
        brush = QtGui.QBrush(QtGui.QColor(120, 120, 120))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.ButtonText, brush)
        self.pushButton_Simulation.setPalette(palette)
        self.pushButton_Simulation.setObjectName("pushButton_Simulation")
        self.gridLayout.addWidget(self.pushButton_Simulation, 3, 0, 1, 2)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 4, 0, 1, 1)
        self.pushButton_Reality = QtWidgets.QPushButton("With keithley", self)
        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(255, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.ButtonText, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.ButtonText, brush)
        brush = QtGui.QBrush(QtGui.QColor(120, 120, 120))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.ButtonText, brush)
        self.pushButton_Reality.setPalette(palette)
        self.pushButton_Reality.setObjectName("pushButton_Reality")
        self.gridLayout.addWidget(self.pushButton_Reality, 2, 0, 1, 2)
        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem1, 1, 0, 1, 1)

        
        self.pushButton_Reality.clicked.connect(self.MainReal)   
        self.pushButton_Simulation.clicked.connect(self.MainSimul)

        self.show()

    def MainReal(self): 
        global keithleyAddress, usbflashdriveaddress, Kconnresult
        if version== '6pixels':
            global boxCurrent, boxVoltage, connectPixel
            sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),'AdvantechCode'))
            from pixelControl import connectPixel 
            sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),'AdvantechCode'))
            import pyDAQNavi as pDN
            boxCurrent = pDN.DeviceObject('USB-4761,BID#0')
            boxVoltage = pDN.DeviceObject('USB-4761,BID#1')
            
        rm = pyvisa.ResourceManager(r'C:\WINDOWS\system32\visa32.dll')
        print(list(rm.list_resources('?*')))
        
        keithleyAddress =list(dict.fromkeys(list(rm.list_resources('?*'))+['GPIB0::22::INSTR','GPIB0::23::INSTR','ASRL1::INSTR','ASRL2::INSTR','ASRL3::INSTR','ASRL4::INSTR','ASRL5::INSTR','ASRL6::INSTR','ASRL7::INSTR','ASRL8::INSTR']))
        Kconnresult=connectToKeithley(keithleyAddress)

        print('')
        print(Kconnresult)
        print('')
        if Kconnresult!=None:
            self.w = Main()
            self.w.show()
            self.hide()
        else:
            QMessageBox.information(self,'No connection', 'Check connection with Keithley')
            
    def MainSimul(self):
        global keithleyAddress, usbflashdriveaddress, Kconnresult

        keithleyAddress=['Test']
        Kconnresult=connectToKeithley(keithleyAddress)
        
        if Kconnresult!=None:
            self.w = Main()
            self.w.show()
            self.hide()
    
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = Window()
    sys.exit(app.exec())
