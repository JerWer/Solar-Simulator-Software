from PyQt5.QtWidgets import QFileDialog
from PyQt5 import QtCore,QtGui
import os
from pathlib import Path
from PyQt5.QtWidgets import QComboBox, QCheckBox, QLineEdit,\
    QRadioButton, QSpinBox, QDoubleSpinBox, QSlider, QListWidget, QTabWidget
from PyQt5.QtCore import QSettings
from distutils.util import strtobool

import inspect
"""
these functions should be replaced by something generic that finds all the widgets of the app by itself
"""

def SaveParamTemplateGeneric(self, ui, settings):
    'generic function'
    handled_types=[QComboBox, QLineEdit, QCheckBox, QRadioButton, QSpinBox, QSlider, QListWidget, QTabWidget]
    
    print(inspect.getmembers(ui))
    
    # for name, obj in inspect.getmembers(ui):
    #     #if type(obj) is QComboBox:  # this works similar to isinstance, but missed some field... not sure why?
    #     if isinstance(obj, QComboBox):
    #         name   = obj.objectName()      # get combobox name
    #         index  = obj.currentIndex()    # get current index from combobox
    #         text   = obj.itemText(index)   # get the text for current index
    #         settings.setValue(name, text)   # save combobox selection to registry

    #     if isinstance(obj, QLineEdit):
    #         name = obj.objectName()
    #         value = obj.text()
    #         settings.setValue(name, value)    # save ui values, so they can be restored next time

    #     if isinstance(obj, QCheckBox):
    #         name = obj.objectName()
    #         state = obj.checkState()
    #         settings.setValue(name, state)

def LoadParamTemplate(self, selectedpath=1):
    
    if selectedpath==1:
        directory=os.path.join(str(Path(os.path.abspath(__file__)).parent.parent),'ExamplesTemplateFiles')
        
        fname = QFileDialog.getOpenFileName(self, 'Choose a template file to load', directory,"Text files (*.txt)")[0]
        
    else:
        fname=selectedpath
    if fname =='':
        return
    # print(fname)
    with open(fname,'r') as file:
        for line in file:
            # print(line)
            if 'UserName' in line:
                self.ui.lineEdit_UserName.setText(line.split('\t')[1][:-1])
            elif 'SampleName' in line:
                self.ui.lineEdit_SampleName.setText(line.split('\t')[1][:-1])
            elif 'Comment' in line:
                self.ui.lineEdit_Comment.setText(line.split('\t')[1][:-1])
            elif 'aftermppt' in line:
                self.ui.checkBox_aftermpp.setChecked(eval(line.split('\t')[1]))
            elif 'Meas. type' in line:
                index = self.ui.comboBox_MeasType.findText(line.split('\t')[1][:-1], QtCore.Qt.MatchFixedString)
                if index >= 0:
                     self.ui.comboBox_MeasType.setCurrentIndex(index)
            elif '#rep' in line:
                self.ui.spinBox_RepNumb.setValue(float(line.split('\t')[1]))
            elif 'DelayRep' in line:
                self.ui.spinBox_RepDelay.setValue(float(line.split('\t')[1]))
            elif 'threaded' in line:
                self.ui.checkBox_threaded.setChecked(eval(line.split('\t')[1]))
            elif 'Diode1sun' in line:
                self.ui.doubleSpinBox_DiodeNominalCurrent.setValue(float(line.split('\t')[1]))
            elif 'Refcurrentlimit' in line:
                self.ui.doubleSpinBox_RefCellIlimit.setValue(float(line.split('\t')[1]))
            elif 'temperature' in line:
                self.ui.doubleSpinBox_Temperature.setValue(float(line.split('\t')[1]))
            elif 'assume1sun' in line:
                self.ui.radioButton_Assume1sun.setChecked(eval(line.split('\t')[1]))
            elif 'minvoltage' in line:
                self.ui.doubleSpinBox_JVminvoltage.setValue(float(line.split('\t')[1]))
            elif 'maxvoltage' in line:
                self.ui.doubleSpinBox_JVmaxvoltage.setValue(float(line.split('\t')[1]))
            elif 'JVstepsize' in line:
                self.ui.doubleSpinBox_JVstepsize.setValue(float(line.split('\t')[1]))
            elif 'currentlimit' in line:
                self.ui.doubleSpinBox_JVcurrentlimit.setValue(float(line.split('\t')[1]))
            elif 'integtime' in line:
                self.ui.doubleSpinBox_JVintegrationtime.setValue(float(line.split('\t')[1]))
            elif 'JVdelaypoints' in line:
                self.ui.doubleSpinBox_JVdelaypoints.setValue(float(line.split('\t')[1]))
                # print(float(line.split('\t')[1]))
            elif 'delayshutter' in line:
                self.ui.doubleSpinBox_JVdelayshutter.setValue(float(line.split('\t')[1]))
            elif 'scandirection' in line:
                index = self.ui.comboBox_JVscandirection.findText(line.split('\t')[1][:-1], QtCore.Qt.MatchFixedString)
                if index >= 0:
                     self.ui.comboBox_JVscandirection.setCurrentIndex(index)
            elif 'polarity' in line:
                if line.split('\t')[1]=='nip':
                    # self.ui.radioButton_nip.setChecked(True)
                    self.ui.checkBox_pin.setChecked(False)
                else:
                    # self.ui.radioButton_nip.setChecked(False)
                    self.ui.checkBox_pin.setChecked(True)
            # elif 'Vmpestimation' in line:
            #     self.ui.doubleSpinBox_StepJV_VmpEstim.setValue(float(line.split('\t')[1]))
            # elif 'stepJVtimestepJV' in line:
            #     self.ui.doubleSpinBox_StepJV_timestepJV.setValue(float(line.split('\t')[1]))
            # elif 'stepJVmaxDurTotal' in line:
            #     self.ui.doubleSpinBox_StepJV_MaxDurTotal.setValue(float(line.split('\t')[1]))
            # elif 'stepJVnbpts' in line:
            #     self.ui.doubleSpinBox_StepJV_NbPts.setValue(float(line.split('\t')[1]))
            # elif 'maxduration' in line:
            #     self.ui.doubleSpinBox_StepJV_MaxDur.setValue(float(line.split('\t')[1]))
            # elif 'deviationcrit' in line:
            #     self.ui.doubleSpinBox_StepJV_DevCrit.setValue(float(line.split('\t')[1]))
            # elif 'timeunderdev' in line:
            #     self.ui.doubleSpinBox_StepJV_TimeDev.setValue(float(line.split('\t')[1]))
            elif 'QSSNbpts' in line:
                self.ui.doubleSpinBox_QSS_Nbpts.setValue(float(line.split('\t')[1]))
            elif 'QSSmppptsdensity' in line:
                self.ui.spinBox_QSS_mppptsdensity.setValue(float(line.split('\t')[1]))
            elif 'QSSDevCrit' in line:
                self.ui.doubleSpinBox_QSS_DevCrit.setValue(float(line.split('\t')[1]))
            elif 'QSSTimeDev' in line:
                self.ui.doubleSpinBox_QSS_TimeDev.setValue(float(line.split('\t')[1]))
            elif 'QSSTimeMax4Fail' in line:
                self.ui.doubleSpinBox_QSS_TimeMax4Fail.setValue(float(line.split('\t')[1]))
            elif 'useVmpp' in line:
                self.ui.checkBox_MPPTuseVmpp.setChecked(eval(line.split('\t')[1]))
            elif 'startvoltage' in line:
                self.ui.doubleSpinBox_MPPTstartvoltage.setValue(float(line.split('\t')[1]))
            elif 'MPPTstepsize' in line:
                self.ui.spinBox_MPPTstepsize.setValue(float(line.split('\t')[1]))
            elif 'voltagelimit' in line:
                self.ui.doubleSpinBox_MPPTvoltagelimit.setValue(float(line.split('\t')[1]))
            elif 'delaypointsmpp' in line:
                self.ui.doubleSpinBox_MPPTdelaypoints.setValue(float(line.split('\t')[1]))
            elif 'lighton' in line:
                self.ui.checkBox_MPPTlighton.setChecked(eval(line.split('\t')[1]))
            elif 'keeplightafter' in line:
                self.ui.checkBox_MPPTlightonafter.setChecked(eval(line.split('\t')[1]))
            elif 'PixelA' in line:
                self.ui.checkBox_pixA.setChecked(eval(line.split('\t')[1]))
            elif 'PixelB' in line:
                self.ui.checkBox_pixB.setChecked(eval(line.split('\t')[1]))
            elif 'PixelC' in line:
                self.ui.checkBox_pixC.setChecked(eval(line.split('\t')[1]))
            elif 'PixelD' in line:
                self.ui.checkBox_pixD.setChecked(eval(line.split('\t')[1]))
            elif 'PixelE' in line:
                self.ui.checkBox_pixE.setChecked(eval(line.split('\t')[1]))
            elif 'PixelF' in line:
                self.ui.checkBox_pixF.setChecked(eval(line.split('\t')[1]))
            elif 'A-area' in line:
                self.ui.doubleSpinBox_pixAarea.setValue(float(line.split('\t')[1]))
            elif 'B-area' in line:
                self.ui.doubleSpinBox_pixBarea.setValue(float(line.split('\t')[1]))
            elif 'C-area' in line:
                self.ui.doubleSpinBox_pixCarea.setValue(float(line.split('\t')[1]))
            elif 'D-area' in line:
                self.ui.doubleSpinBox_pixDarea.setValue(float(line.split('\t')[1]))
            elif 'E-area' in line:
                self.ui.doubleSpinBox_pixEarea.setValue(float(line.split('\t')[1]))
            elif 'F-area' in line:
                self.ui.doubleSpinBox_pixFarea.setValue(float(line.split('\t')[1]))
            elif 'Allpix' in line:
                self.ui.radioButton_pixAll.setChecked(eval(line.split('\t')[1]))
            elif 'PixelX' in line:
                # print('pixelX, ', int(line.split('\t')[1]))
                self.ui.spinBox_pixXnumber.setValue(int(line.split('\t')[1]))
            if 'PixelArea' in line:
                # print('pixelarea, ', float(line.split('\t')[1]))
                self.ui.doubleSpinBox_pixXarea.setValue(float(line.split('\t')[1]))
            if 'CurrentTab' in line:
                self.ui.Figure_tabWidget.setCurrentIndex(float(line.split('\t')[1]))


    return fname

def SaveParamTemplate(self, selectedpath=1):
    if self.ui.checkBox_MPPTlighton.isChecked():
        checkBox_MPPTlighton='True'
    else:
        checkBox_MPPTlighton='False'
    if self.ui.checkBox_aftermpp.isChecked():
        checkBox_aftermpp='True'
    else:
        checkBox_aftermpp='False'
    if self.ui.checkBox_threaded.isChecked():
        checkBox_threaded='True'
    else:
        checkBox_threaded='False'
    if self.ui.checkBox_MPPTlightonafter.isChecked():
        checkBox_MPPTlightonafter='True'
    else:
        checkBox_MPPTlightonafter='False'
    if self.ui.checkBox_MPPTuseVmpp.isChecked():
        useVmpp='True'
    else:
        useVmpp='False'
    if self.ui.checkBox_pixA.isChecked():
        checkBox_pixA='True'
    else:
        checkBox_pixA='False'
    if self.ui.checkBox_pixB.isChecked():
        checkBox_pixB='True'
    else:
        checkBox_pixB='False'
    if self.ui.checkBox_pixC.isChecked():
        checkBox_pixC='True'
    else:
        checkBox_pixC='False'
    if self.ui.checkBox_pixD.isChecked():
        checkBox_pixD='True'
    else:
        checkBox_pixD='False'
    if self.ui.checkBox_pixE.isChecked():
        checkBox_pixE='True'
    else:
        checkBox_pixE='False'
    if self.ui.checkBox_pixF.isChecked():
        checkBox_pixF='True'
    else:
        checkBox_pixF='False'
    if self.ui.radioButton_pixAll.isChecked():
        radioButton_pixAll='True'
    else:
        radioButton_pixAll='False'
    if self.ui.radioButton_Assume1sun.isChecked():
        radioButton_Assume1sun='True'
    else:
        radioButton_Assume1sun='False'
    if self.ui.checkBox_pin.isChecked():
        polarity='pin'
    else:
        polarity='nip'
        
    if selectedpath==1:
        directory=os.path.join(str(Path(os.path.abspath(__file__)).parent.parent),'ExamplesTemplateFiles')
        # print(str(self.ui.doubleSpinBox_JVdelaypoints.value()))
        fname = QFileDialog.getSaveFileName(self, 'Save file', directory,"Text files (*.txt)")[0]
    else:
        fname=selectedpath
    try:
        with open(fname,'w') as file:
            text='UserName\t'+ str(self.ui.lineEdit_UserName.text())+'\n'+\
                'SampleName\t'+ str(self.ui.lineEdit_SampleName.text())+'\n'+\
                'Comment\t'+str(self.ui.lineEdit_Comment.text())+'\n'+\
                'aftermppt\t'+ checkBox_aftermpp +'\n'+\
                'Meas. type\t'+ str(self.ui.comboBox_MeasType.currentText())+'\n'+\
                '#rep\t'+ str(self.ui.spinBox_RepNumb.value())+'\n'+\
                'DelayRep\t'+ str(self.ui.spinBox_RepDelay.value())+'\n'+\
                'threaded\t'+ checkBox_threaded +'\n'+\
                '\n'+\
                'Diode1sun\t'+ str(self.ui.doubleSpinBox_DiodeNominalCurrent.value())+'\n'+\
                'Refcurrentlimit\t'+ str(self.ui.doubleSpinBox_RefCellIlimit.value())+'\n'+\
                'temperature\t'+ str(self.ui.doubleSpinBox_Temperature.value())+'\n'+\
                'assume1sun\t'+ radioButton_Assume1sun +'\n'+\
                '\n'+\
                'minvoltage\t'+ str(self.ui.doubleSpinBox_JVminvoltage.value())+'\n'+\
                'maxvoltage\t'+ str(self.ui.doubleSpinBox_JVmaxvoltage.value())+'\n'+\
                'JVstepsize\t'+ str(self.ui.doubleSpinBox_JVstepsize.value())+'\n'+\
                'currentlimit\t'+ str(self.ui.doubleSpinBox_JVcurrentlimit.value())+'\n'+\
                'integtime\t'+ str(self.ui.doubleSpinBox_JVintegrationtime.value())+'\n'+\
                'JVdelaypoints\t'+ str(self.ui.doubleSpinBox_JVdelaypoints.value())+'\n'+\
                'delayshutter\t'+ str(self.ui.doubleSpinBox_JVdelayshutter.value())+'\n'+\
                'scandirection\t'+ str(self.ui.comboBox_JVscandirection.currentText())+'\n'+\
                'polarity\t'+ polarity+'\n'+\
                '\n'+\
                'QSSNbpts\t'+ str(self.ui.doubleSpinBox_QSS_Nbpts.value())+'\n'+\
                'QSSmppptsdensity\t'+ str(self.ui.spinBox_QSS_mppptsdensity.value())+'\n'+\
                'QSSDevCrit\t'+ str(self.ui.doubleSpinBox_QSS_DevCrit.value())+'\n'+\
                'QSSTimeDev\t'+ str(self.ui.doubleSpinBox_QSS_TimeDev.value())+'\n'+\
                'QSSTimeMax4Fail\t'+ str(self.ui.doubleSpinBox_QSS_TimeMax4Fail.value())+'\n'+\
                '\n'+\
                'useVmpp\t'+ useVmpp+'\n'+\
                'startvoltage\t'+ str(self.ui.doubleSpinBox_MPPTstartvoltage.value())+'\n'+\
                'MPPTstepsize\t'+ str(self.ui.spinBox_MPPTstepsize.value())+'\n'+\
                'voltagelimit\t'+ str(self.ui.doubleSpinBox_MPPTvoltagelimit.value())+'\n'+\
                'delaypointsmpp\t'+ str(self.ui.doubleSpinBox_MPPTdelaypoints.value())+'\n'+\
                'lighton\t'+checkBox_MPPTlighton +'\n'+\
                'keeplightafter\t'+checkBox_MPPTlightonafter +'\n'+\
                '\n'+\
                'PixelA\t'+checkBox_pixA +'\n'+\
                'PixelB\t'+checkBox_pixB +'\n'+\
                'PixelC\t'+checkBox_pixC +'\n'+\
                'PixelD\t'+checkBox_pixD +'\n'+\
                'PixelE\t'+checkBox_pixE +'\n'+\
                'PixelF\t'+checkBox_pixF +'\n'+\
                'A-area\t'+ str(self.ui.doubleSpinBox_pixAarea.value())+'\n'+\
                'B-area\t'+ str(self.ui.doubleSpinBox_pixBarea.value())+'\n'+\
                'C-area\t'+ str(self.ui.doubleSpinBox_pixCarea.value())+'\n'+\
                'D-area\t'+ str(self.ui.doubleSpinBox_pixDarea.value())+'\n'+\
                'E-area\t'+ str(self.ui.doubleSpinBox_pixEarea.value())+'\n'+\
                'F-area\t'+ str(self.ui.doubleSpinBox_pixFarea.value())+'\n'+\
                'Allpix\t'+ radioButton_pixAll+'\n'+\
                '\n'+\
                'PixelX\t'+ str(self.ui.spinBox_pixXnumber.value())+'\n'+\
                'PixelArea\t'+ str(self.ui.doubleSpinBox_pixXarea.value())+'\n'\
                '\n'+\
                'CurrentTab\t'+str(self.ui.Figure_tabWidget.currentIndex())+'\n'
                # 'Vmpestimation\t'+ str(self.ui.doubleSpinBox_StepJV_VmpEstim.value())+'\n'+\
                # 'stepJVmaxDurTotal\t'+ str(self.ui.doubleSpinBox_StepJV_MaxDurTotal.value())+'\n'+\
                # 'stepJVnbpts\t'+ str(self.ui.doubleSpinBox_StepJV_NbPts.value())+'\n'+\
                # 'maxduration\t'+ str(self.ui.doubleSpinBox_StepJV_MaxDur.value())+'\n'+\
                # 'deviationcrit\t'+ str(self.ui.doubleSpinBox_StepJV_DevCrit.value())+'\n'+\
                # 'timeunderdev\t'+ str(self.ui.doubleSpinBox_StepJV_TimeDev.value())+'\n'+\
            file.write(text)
    except FileNotFoundError:
        pass
    return fname

def CreateParamTemplate(self):

    checkBox_MPPTlighton='True'
    checkBox_aftermpp='False'
    checkBox_threaded='True'
    checkBox_MPPTlightonafter='True'
    useVmpp='True'
    checkBox_pixA='False'
    checkBox_pixB='False'
    checkBox_pixC='False'
    checkBox_pixD='False'
    checkBox_pixE='False'
    checkBox_pixF='False'
    radioButton_pixAll='False'
    radioButton_Assume1sun='True'
    polarity='pin'
        
    directory=str(Path(os.path.abspath(__file__)).parent.parent)
    fname = QFileDialog.getSaveFileName(self, 'Save file', directory,"Text files (*.txt)")[0]
        
    with open(fname+'.txt','w') as file:
        text='UserName\t'+ 'YourName'+'\n'+\
            'SampleName\t'+ 'batch#_sample#'+'\n'+\
            'Comment\t'+str(self.ui.lineEdit_Comment.text())+'\n'+\
            'aftermppt\t'+ checkBox_aftermpp +'\n'+\
            'Meas. type\t'+ str(self.ui.comboBox_MeasType.currentText())+'\n'+\
            '#rep\t'+ str(self.ui.spinBox_RepNumb.value())+'\n'+\
            'DelayRep\t'+ str(self.ui.spinBox_RepDelay.value())+'\n'+\
            'threaded\t'+ checkBox_threaded +'\n'+\
            '\n'+\
            'Diode1sun\t'+ str(self.ui.doubleSpinBox_DiodeNominalCurrent.value())+'\n'+\
            'Refcurrentlimit\t'+ str(self.ui.doubleSpinBox_RefCellIlimit.value())+'\n'+\
            'temperature\t'+ str(self.ui.doubleSpinBox_Temperature.value())+'\n'+\
            'assume1sun\t'+ radioButton_Assume1sun +'\n'+\
            '\n'+\
            'minvoltage\t'+ str(self.ui.doubleSpinBox_JVminvoltage.value())+'\n'+\
            'maxvoltage\t'+ str(self.ui.doubleSpinBox_JVmaxvoltage.value())+'\n'+\
            'JVstepsize\t'+ str(self.ui.doubleSpinBox_JVstepsize.value())+'\n'+\
            'currentlimit\t'+ str(self.ui.doubleSpinBox_JVcurrentlimit.value())+'\n'+\
            'integtime\t'+ str(self.ui.doubleSpinBox_JVintegrationtime.value())+'\n'+\
            'JVdelaypoints\t'+ str(self.ui.doubleSpinBox_JVdelaypoints.value())+'\n'+\
            'delayshutter\t'+ str(self.ui.doubleSpinBox_JVdelayshutter.value())+'\n'+\
            'scandirection\t'+ str(self.ui.comboBox_JVscandirection.currentText())+'\n'+\
            'polarity\t'+ polarity+'\n'+\
            '\n'+\
            'Vmpestimation\t'+ str(self.ui.doubleSpinBox_StepJV_VmpEstim.value())+'\n'+\
            'stepJVtimestepJV\t'+ str(self.ui.doubleSpinBox_StepJV_timestepJV.value())+'\n'+\
            'stepJVmaxDurTotal\t'+ str(self.ui.doubleSpinBox_StepJV_MaxDurTotal.value())+'\n'+\
            'stepJVnbpts\t'+ str(self.ui.doubleSpinBox_StepJV_NbPts.value())+'\n'+\
            'maxduration\t'+ str(self.ui.doubleSpinBox_StepJV_MaxDur.value())+'\n'+\
            'deviationcrit\t'+ str(self.ui.doubleSpinBox_StepJV_DevCrit.value())+'\n'+\
            'timeunderdev\t'+ str(self.ui.doubleSpinBox_StepJV_TimeDev.value())+'\n'+\
            '\n'+\
            'useVmpp\t'+ useVmpp+'\n'+\
            'startvoltage\t'+ str(self.ui.doubleSpinBox_MPPTstartvoltage.value())+'\n'+\
            'MPPTstepsize\t'+ str(self.ui.spinBox_MPPTstepsize.value())+'\n'+\
            'voltagelimit\t'+ str(self.ui.doubleSpinBox_MPPTvoltagelimit.value())+'\n'+\
            'delaypointsmpp\t'+ str(self.ui.doubleSpinBox_MPPTdelaypoints.value())+'\n'+\
            'lighton\t'+checkBox_MPPTlighton +'\n'+\
            'keeplightafter\t'+checkBox_MPPTlightonafter +'\n'+\
            '\n'+\
            'PixelA\t'+checkBox_pixA +'\n'+\
            'PixelB\t'+checkBox_pixB +'\n'+\
            'PixelC\t'+checkBox_pixC +'\n'+\
            'PixelD\t'+checkBox_pixD +'\n'+\
            'PixelE\t'+checkBox_pixE +'\n'+\
            'PixelF\t'+checkBox_pixF +'\n'+\
            'A-area\t'+ str(self.ui.doubleSpinBox_pixAarea.value())+'\n'+\
            'B-area\t'+ str(self.ui.doubleSpinBox_pixBarea.value())+'\n'+\
            'C-area\t'+ str(self.ui.doubleSpinBox_pixCarea.value())+'\n'+\
            'D-area\t'+ str(self.ui.doubleSpinBox_pixDarea.value())+'\n'+\
            'E-area\t'+ str(self.ui.doubleSpinBox_pixEarea.value())+'\n'+\
            'F-area\t'+ str(self.ui.doubleSpinBox_pixFarea.value())+'\n'+\
            'Allpix\t'+ radioButton_pixAll+'\n'+\
            '\n'+\
            'PixelX\t'+ str(self.ui.spinBox_pixXnumber.value())+'\n'+\
            'PixelArea\t'+ str(self.ui.doubleSpinBox_pixXarea.value())+'\n'\
            '\n'+\
            'CurrentTab\t'+str(self.ui.Figure_tabWidget.CurrentIndex())+'\n'
        
        file.write(text)
    return fname

