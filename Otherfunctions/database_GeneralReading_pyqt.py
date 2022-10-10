import os
import sys
from pathlib import Path
import xlsxwriter
import copy
import sqlite3
#%%######################################################################################################
import matplotlib
# import matplotlib.pyplot as plt
matplotlib.use("Qt5Agg")
#%%######################################################################################################
from PyQt5 import QtCore, QtWidgets#, QtGui
# from PyQt5 import QtTest
# from PyQt5.QtCore.QElapsedTimer import timer
from PyQt5.QtWidgets import QFileDialog, QMessageBox#, QAction, QTableWidgetItem
# from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
# from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
# from matplotlib.figure import Figure


#%%######################################################################################################

"""
time evolution graph:
    1) ask which param to check evolution from
    2) ask for restriction parameters
    3) specify the restrictions for those parameters
    4) search and plot graph

box plot graph:
    1) what param for y axis. this should be a numerical one
    2) what for x axis. this should be a non-numerical (or limited number), e.g. samplename, user, or sample area
    3) ask for restriction parameters
    4) specify the restrictions for those parameters
    5) search and plot graph 
    
overall search engine, done already in tkinter, needs to be transfered to pyqt5

"""

parameterList=[]
tablesAndcolnames=[]
SetallcolnamesWOids=[]
criteriaList=[]
criteriaexclusionlist=['JVmeas.commentJV','JVmeas.linktorawdata',
                       'MPPmeas.commentmpp', 'MPPmeas.linktorawdata'] #cannot restrict search from those criteria

dropdowncriteria=['batch.batchname','users.user','samples.samplename','JVmeas.SampleNamePix','JVmeas.MeasurementLongName',
                  'cells.cellname','cells.AllpixSeq','pixelarea.pixel_area',
                  'JVmeas.ScanDirect','JVmeas.MeasType','JVmeas.MeasNowType',
                  'JVmeas.LightDark', 'JVmeas.aftermpp','Refdiode.IsRefDiodeMeasured',
                  'MPPmeas.TrackingAlgo','MPPmeas.MeasType','MPPmeas.MeasNowType',
                  'MPPmeas.LightDark'
                  ]
                  
    

fromtocriteria=['JVmeas.Eff', 'JVmeas.Voc','JVmeas.Jsc', 'JVmeas.Isc','JVmeas.FF',
                'JVmeas.Vmpp', 'JVmeas.Jmpp', 'JVmeas.Pmpp','JVmeas.Roc','JVmeas.Rsc',
                'JVmeas.Delay','JVmeas.DelayShutter','JVmeas.IntegTime',
                'JVmeas.Vmin','JVmeas.Vmax','JVmeas.StepSize','JVmeas.CurrentLimit',
                'JVmeas.IlluminationIntensity', 'Refdiode.RefDiodeNomCurr','Refdiode.RefDiodeMeasCurr','Refdiode.temperature',
                'MPPmeas.TrackingDuration','MPPmeas.Vstart', 'MPPmeas.Vstep', 'MPPmeas.Delay',
                'MPPmeas.IlluminationIntensity','MPPmeas.PowerEnd'
                ]

timecriteria=['JVmeas.DateTimeJV', 'MPPmeas.DateTimeMPP']

criteriaListdetailled=[]
criteriaListdetailled2=[]

listofitems=['item1','item2','item3','item4',]
listofitemsselected=[]

db_conn=0
theCursor=0
numb_for=0

def center(win):
    win.update_idletasks()
    width = win.winfo_width()
    frm_width = win.winfo_rootx() - win.winfo_x()
    win_width = width + 2 * frm_width
    height = win.winfo_height()
    titlebar_height = win.winfo_rooty() - win.winfo_y()
    win_height = height + titlebar_height + frm_width
    x = win.winfo_screenwidth() // 2 - win_width // 2
    y = win.winfo_screenheight() // 2 - win_height // 2
    win.geometry('{}x{}+{}+{}'.format(width, height, x, y))
    win.deiconify()

#%%######################################################################################################
class OpeningWindow(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        global db_conn, theCursor
        
        self.resize(300, 120)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)
        self.setMinimumSize(QtCore.QSize(200, 90))
        self.gridLayout = QtWidgets.QGridLayout(self)
        self.setWindowTitle("Reading database")
        
        self.pushButton_GlobalReading = QtWidgets.QPushButton("Global Reading", self)
        self.gridLayout.addWidget(self.pushButton_GlobalReading, 3, 0, 1, 2)
        
        self.pushButton_TimeEvol = QtWidgets.QPushButton("Time evolution check", self)
        self.gridLayout.addWidget(self.pushButton_TimeEvol, 2, 0, 1, 2)

        self.pushButton_BoxPlot = QtWidgets.QPushButton("Scatter box plots", self)
        self.gridLayout.addWidget(self.pushButton_BoxPlot, 1, 0, 1, 2)        
        
        self.pushButton_GlobalReading.clicked.connect(self.GlobalReadingstart)   
        self.pushButton_TimeEvol.clicked.connect(self.TimeEvolstart)
        self.pushButton_BoxPlot.clicked.connect(self.BoxPlotstart)
        
        
        directory=os.path.join(str(Path(os.path.abspath(__file__)).parent.parent.parent),'Database')
        path=os.path.join(directory,'CUMcGeheeGeneralDB.db')

        db_conn=sqlite3.connect(path)
        theCursor=db_conn.cursor()
        
        
        self.show()
        
    def GlobalReadingstart(self):   

        self.w = GlobalReading()
        self.w.show()
        self.hide()
    
    def TimeEvolstart(self):   

        self.w = TimeEvol()
        self.w.show()
        self.hide()

    def BoxPlotstart(self):   

        self.w = BoxPlot()
        self.w.show()
        self.hide()
        
#%%######################################################################################################
class GlobalReading(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        global db_conn, theCursor
        global tablesAndcolnames, SetallcolnamesWOids
        
        self.resize(400, 400)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)
        self.setMinimumSize(QtCore.QSize(400, 300))
        self.gridLayout = QtWidgets.QGridLayout(self)
        self.setWindowTitle("Global Reading of database")
        
        theCursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = list(map(lambda x: x[0],theCursor.fetchall()))

        allcolnames=[]
        for item in tables:
            if item != 'sqlite_sequence':
                dat=theCursor.execute('SELECT * FROM '+ item)
                names=list(map(lambda x: item +'.'+ x[0],dat.description))
                tablesAndcolnames.append([item,names])
                allcolnames+=names
        
        Setallcolnames=list(set(allcolnames))
#        Setallcolnames.remove('id')
        SetallcolnamesWOids=[]
        for item in Setallcolnames:
            if "id" not in item:
                SetallcolnamesWOids.append(item)
        SetallcolnamesWOids=sorted(SetallcolnamesWOids) 
        
        
        self.listWidget = QtWidgets.QListWidget()
        self.listWidget.setGeometry(QtCore.QRect(10, 10, 211, 291))
        for i in SetallcolnamesWOids:
            item = QtWidgets.QListWidgetItem(i)
            self.listWidget.addItem(item)
        self.listWidget.itemClicked.connect(self.selectitem)
        self.gridLayout.addWidget(self.listWidget)
        
        self.pushButton1 = QtWidgets.QPushButton("Add the usuals", self)
        self.gridLayout.addWidget(self.pushButton1)
        self.pushButton2 = QtWidgets.QPushButton("Add all", self)
        self.gridLayout.addWidget(self.pushButton2)
       
        self.listWidget2 = QtWidgets.QListWidget()
        self.listWidget2.setGeometry(QtCore.QRect(10, 10, 211, 291))
        self.listWidget2.itemClicked.connect(self.deleteitem)
        self.gridLayout.addWidget(self.listWidget2)   
        
        self.pushButton3 = QtWidgets.QPushButton("Validate", self)
        self.gridLayout.addWidget(self.pushButton3)
        self.pushButton4 = QtWidgets.QPushButton("Cancel", self)
        self.gridLayout.addWidget(self.pushButton4)

        
        self.pushButton1.clicked.connect(self.Addusuals)
        self.pushButton2.clicked.connect(self.AddAll)
        self.pushButton3.clicked.connect(self.validate)
        self.setLayout(self.gridLayout)
        
        
    def selectitem(self): 
        elemalreadythere=[self.listWidget2.item(i).text() for i in range(self.listWidget2.count())]
        if self.listWidget.selectedItems()[0].text() not in elemalreadythere:
            self.listWidget2.addItem(self.listWidget.selectedItems()[0].text())
            self.listWidget.takeItem(self.listWidget.row(self.listWidget.selectedItems()[0]))
        
    def deleteitem(self):
        elemalreadythere=[self.listWidget.item(i).text() for i in range(self.listWidget.count())]
        if self.listWidget2.selectedItems()[0].text() not in elemalreadythere:
            self.listWidget.addItem(self.listWidget2.selectedItems()[0].text())
            self.listWidget2.takeItem(self.listWidget2.row(self.listWidget2.selectedItems()[0]))
        
     
    def Addusuals(self):
        elemtobeadded=['samples.samplename','users.user','pixelarea.pixel_area','JVmeas.DateTimeJV',
                    'JVmeas.Eff', 'JVmeas.FF','JVmeas.Jsc','JVmeas.Voc',]
        
        elemalreadythere=[self.listWidget2.item(i).text() for i in range(self.listWidget2.count())]
        for i in elemtobeadded:
            if i not in elemalreadythere:
                self.listWidget2.addItem(i)
        
        elemalreadythere=[self.listWidget.item(i) for i in range(self.listWidget.count())]
        for i in elemtobeadded:
            for j in elemalreadythere:
                if i==j.text():
                    self.listWidget.takeItem(self.listWidget.row(j))
    
    def AddAll(self):
        elemtobeadded=[self.listWidget.item(i).text() for i in range(self.listWidget.count())]
        elemalreadythere=[self.listWidget2.item(i).text() for i in range(self.listWidget2.count())]
        for i in elemtobeadded:
            if i not in elemalreadythere:
                self.listWidget2.addItem(i)
        
        elemalreadythere=[self.listWidget.item(i) for i in range(self.listWidget.count())]
        for i in elemtobeadded:
            for j in elemalreadythere:
                if i==j.text():
                    self.listWidget.takeItem(self.listWidget.row(j))
    
    def validate(self):
        global parameterList
        
        parameterList=[self.listWidget2.item(i).text() for i in range(self.listWidget2.count())]
        
        # print(parameterList)   
        self.w = RestrictionCriteriawindow()
        self.w.show()
        self.hide()
        # self.hide()
        

class RestrictionCriteriawindow(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        global db_conn, theCursor, numb_for
        global tablesAndcolnames, SetallcolnamesWOids, criteriaList, criteriaexclusionlist
        
        self.resize(400, 400)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)
        self.setMinimumSize(QtCore.QSize(400, 300))
        self.gridLayout = QtWidgets.QGridLayout(self)
        self.setWindowTitle("Selection of restriction criteria")
        
        colnamesnew=[item for item in SetallcolnamesWOids if item not in criteriaexclusionlist]
        self.listWidget = QtWidgets.QListWidget()
        self.listWidget.setGeometry(QtCore.QRect(10, 10, 211, 291))
        for i in colnamesnew:
            item = QtWidgets.QListWidgetItem(i)
            self.listWidget.addItem(item)
        self.listWidget.itemClicked.connect(self.selectitem)
        self.gridLayout.addWidget(self.listWidget)
       
        self.listWidget2 = QtWidgets.QListWidget()
        self.listWidget2.setGeometry(QtCore.QRect(10, 10, 211, 291))
        self.listWidget2.itemClicked.connect(self.deleteitem)
        self.gridLayout.addWidget(self.listWidget2)   
        
        self.pushButton3 = QtWidgets.QPushButton("Validate", self)
        self.gridLayout.addWidget(self.pushButton3)
        self.pushButton4 = QtWidgets.QPushButton("Cancel", self)
        self.gridLayout.addWidget(self.pushButton4)

        self.pushButton3.clicked.connect(self.validate)
        self.setLayout(self.gridLayout)
        
        numb_for=0

    def selectitem(self): 
        elemalreadythere=[self.listWidget2.item(i).text() for i in range(self.listWidget2.count())]
        if self.listWidget.selectedItems()[0].text() not in elemalreadythere:
            self.listWidget2.addItem(self.listWidget.selectedItems()[0].text())
            self.listWidget.takeItem(self.listWidget.row(self.listWidget.selectedItems()[0]))
        
    def deleteitem(self):
        elemalreadythere=[self.listWidget.item(i).text() for i in range(self.listWidget.count())]
        if self.listWidget2.selectedItems()[0].text() not in elemalreadythere:
            self.listWidget.addItem(self.listWidget2.selectedItems()[0].text())
            self.listWidget2.takeItem(self.listWidget2.row(self.listWidget2.selectedItems()[0]))

    def validate(self):
        global criteriaList
        
        criteriaList=[self.listWidget2.item(i).text() for i in range(self.listWidget2.count())]
                
        if criteriaList!=[]:
            detaillingcriteriaList()
            # print(criteriaList)
            self.hide() 
        else:
            QMessageBox.information(self,'', 'at least one criteria should be selected') 

class dropdowncriteriaRefinement(QtWidgets.QDialog):
    def __init__(self,criterianame='',listoptions=['']):
        super().__init__()
        global db_conn, theCursor, numb_for
        global tablesAndcolnames, SetallcolnamesWOids, criteriaList, criteriaexclusionlist
        
        self.resize(300, 200)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)
        self.setMinimumSize(QtCore.QSize(400, 200))
        self.gridLayout = QtWidgets.QGridLayout(self)
        self.setWindowTitle("Select for: "+criterianame+" (multiple choice possible)")

        self.listWidget = QtWidgets.QListWidget()
        self.listWidget.setGeometry(QtCore.QRect(10, 10, 211, 291))
        for i in listoptions:
            item = QtWidgets.QListWidgetItem(i)
            self.listWidget.addItem(item)
        self.gridLayout.addWidget(self.listWidget)
        
        self.pushButton3 = QtWidgets.QPushButton("Validate", self)
        self.gridLayout.addWidget(self.pushButton3)
        self.pushButton3.clicked.connect(lambda: self.validate(criterianame))
    
    def validate(self,criterianame):
        global criteriaListdetailled
        values=[i.text() for i in self.listWidget.selectedItems()]

        if values!=[]:
            criteriaListdetailled.append([copy.deepcopy(criterianame),values])
            detaillingcriteriaList()
            self.hide()
        else:
            QMessageBox.information(self,'', 'you must pick at least one') 
        
class minmaxcriteriaRefinement(QtWidgets.QDialog):
    def __init__(self,criterianame, minimum, maximum):
        super().__init__()
        global db_conn, theCursor, numb_for
        global tablesAndcolnames, SetallcolnamesWOids, criteriaList, criteriaexclusionlist
        
        self.resize(300, 200)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)
        self.setMinimumSize(QtCore.QSize(300, 200))
        self.gridLayout = QtWidgets.QGridLayout(self)
        self.setWindowTitle("Select for: "+criterianame+" (default values are min and max in DB)")
        
        self.label = QtWidgets.QLabel()
        self.label.setText('from')
        self.gridLayout.addWidget(self.label)
        
        self.lineEdit1 = QtWidgets.QLineEdit()
        self.lineEdit1.setText(str(minimum))
        self.gridLayout.addWidget(self.lineEdit1)
        
        self.label = QtWidgets.QLabel()
        self.label.setText('to')
        self.gridLayout.addWidget(self.label)
        
        self.lineEdit2 = QtWidgets.QLineEdit()
        self.lineEdit2.setText(str(maximum))
        self.gridLayout.addWidget(self.lineEdit2)
        
        self.pushButton3 = QtWidgets.QPushButton("Validate", self)
        self.gridLayout.addWidget(self.pushButton3)
        self.pushButton3.clicked.connect(lambda: self.validate(criterianame))
        
    def validate(self,criterianame):
        global criteriaListdetailled2
        
        criteriaListdetailled2.append([criterianame,self.lineEdit1.text(),self.lineEdit2.text()])
        detaillingcriteriaList()
        self.hide()

class bydeffunction(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        global db_conn, theCursor, numb_for
        global tablesAndcolnames, SetallcolnamesWOids, criteriaList, criteriaexclusionlist
        
        self.resize(100, 100)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)
        self.setMinimumSize(QtCore.QSize(100, 100))
        self.gridLayout = QtWidgets.QGridLayout(self)
        self.setWindowTitle("Selection of Search Parameters)")
        
        self.pushButton3 = QtWidgets.QPushButton("Ok", self)
        self.gridLayout.addWidget(self.pushButton3)
        self.pushButton3.clicked.connect(self.validate)
        
    def validate(self):
        detaillingcriteriaList()
        self.hide
        
def detaillingcriteriaList():
    """
    now it iterates through the selected criteria and propose all possibilities existing in the DB
    in the future, it should restrict the possibilities after each criteria definition, in order to limit directly the search and not end up with 0 results after having set all criteria
    
    """
    global parameterList, criteriaList, criteriaexclusionlist, dropdowncriteria, fromtocriteria, timecriteria, criteriaListdetailled, criteriaListdetailled2
    global numb_for
    
    # print(len(criteriaList))
    # print(numb_for)
    
    if numb_for < len(criteriaList):
        
        if criteriaList[numb_for] in dropdowncriteria:
            theCursor.execute("SELECT "+criteriaList[numb_for].split('.')[1]+" FROM "+criteriaList[numb_for].split('.')[0])
            listoptions=list(set([x[0] for x in theCursor.fetchall()]))
            w=dropdowncriteriaRefinement(criteriaList[numb_for],listoptions)
            w.show()
#                print(criteriaList[self.numb_for])
        elif criteriaList[numb_for] in fromtocriteria:
            theCursor.execute("SELECT "+criteriaList[numb_for].split('.')[1]+" FROM "+criteriaList[numb_for].split('.')[0])
            listoptions=list(set([x[0] for x in theCursor.fetchall()]))
            minimum=min(listoptions)
            maximum=max(listoptions)
            w=minmaxcriteriaRefinement(criteriaList[numb_for],minimum,maximum)
            w.show()
#                print(criteriaList[self.numb_for])
        elif criteriaList[numb_for] in timecriteria:
            theCursor.execute("SELECT "+criteriaList[numb_for].split('.')[1]+" FROM "+criteriaList[numb_for].split('.')[0])
            listoptions=list(set([x[0] for x in theCursor.fetchall()]))      
            datemin=min(listoptions)
            datemax=max(listoptions)
            w=minmaxcriteriaRefinement(criteriaList[numb_for],datemin,datemax)
            w.show()
#                print(criteriaList[self.numb_for])
        else:
            w=bydeffunction()
            w.show()
        
        numb_for+=1
    else:   
        # print(criteriaList)
        SearchingAndExporting()        
        

def SearchingAndExporting():
    global parameterList, criteriaList, criteriaexclusionlist, dropdowncriteria, fromtocriteria, timecriteria
    global criteriaListdetailled, criteriaListdetailled2, tablesAndcolnames, SetallcolnamesWOids
           
    directory=os.path.join(str(Path(os.path.abspath(__file__)).parent.parent),'ExamplesTemplateFiles')

    path = QFileDialog.getSaveFileName(caption = 'Select where to save the extracted data', directory = directory)
    print(path)

    parametertables=list(set([x.split('.')[0] for x in parameterList]))
    dictparam={}
    for item in parametertables:
        dictparam[item]=[]
    for item in parameterList:
        dictparam[item.split('.')[0]].append(item)
        
    print(parametertables)
    ####################
    workbook = xlsxwriter.Workbook(str(path[0]))
    worksheet1 = workbook.add_worksheet("DB info")
    
    theCursor.execute("SELECT COUNT(*) FROM batch") # * means everything
    numbbatch = theCursor.fetchall()[0][0]
    worksheet1.write(0,0,"number of batch")
    worksheet1.write(0,1,numbbatch)
    #print(numbbatch)
    theCursor.execute("SELECT COUNT(*) FROM samples") # * means everything
    numbsamples = theCursor.fetchall()[0][0]
    worksheet1.write(1,0,"number of samples")
    worksheet1.write(1,1,numbsamples)
    #print(numbsamples)
    theCursor.execute("SELECT COUNT(*) FROM cells") # * means everything
    numbcells = theCursor.fetchall()[0][0]
    worksheet1.write(2,0,"number of cells")
    worksheet1.write(2,1,numbcells)
    #print(numbcells)
    theCursor.execute("SELECT COUNT(*) FROM JVmeas") # * means everything
    numbJVmeas = theCursor.fetchall()[0][0]
    worksheet1.write(3,0,"number of JV scans")
    worksheet1.write(3,1,numbJVmeas)
    #print(numbJVmeas)
    worksheet1.write(6,0,"highest efficiency")
    theCursor.execute("SELECT Eff FROM JVmeas") # * means everything
    numbJVmeas = theCursor.fetchall()
    #print(max(numbJVmeas)[0])
    worksheet1.write(6,1,max(numbJVmeas)[0])
    theCursor.execute("""SELECT batchname, users.user
                      FROM batch
                      INNER JOIN JVmeas ON batch.id = JVmeas.batch_id
                      INNER JOIN users ON batch.users_id = users.id
                      WHERE JVmeas.Eff=?""", (max(numbJVmeas)[0],))
    numbJVmeas = theCursor.fetchall()[0]
    #print(numbJVmeas)
    worksheet1.write(6,2,numbJVmeas[0])
    worksheet1.write(6,3,numbJVmeas[1])
    worksheet1.write(7,0,"highest Voc")
    theCursor.execute("SELECT Voc FROM JVmeas") # * means everything
    numbJVmeas = theCursor.fetchall()
    #print(max(numbJVmeas)[0])
    worksheet1.write(7,1,max(numbJVmeas)[0])
    theCursor.execute("""SELECT batchname, users.user
                      FROM batch
                      INNER JOIN JVmeas ON batch.id = JVmeas.batch_id
                      INNER JOIN users ON batch.users_id = users.id
                      WHERE JVmeas.Voc=?""", (max(numbJVmeas)[0],))
    numbJVmeas = theCursor.fetchall()[0]
    #print(numbJVmeas)
    worksheet1.write(7,2,numbJVmeas[0])
    worksheet1.write(7,3,numbJVmeas[1])      
    worksheet1.write(8,0,"highest Jsc")
    theCursor.execute("SELECT Jsc FROM JVmeas") # * means everything
    numbJVmeas = theCursor.fetchall()
    #print(max(numbJVmeas)[0])
    worksheet1.write(8,1,max(numbJVmeas)[0])
    theCursor.execute("""SELECT batchname, users.user
                      FROM batch
                      INNER JOIN JVmeas ON batch.id = JVmeas.batch_id
                      INNER JOIN users ON batch.users_id = users.id
                      WHERE JVmeas.Jsc=?""", (max(numbJVmeas)[0],))
    numbJVmeas = theCursor.fetchall()[0]
    #print(numbJVmeas)
    worksheet1.write(8,2,numbJVmeas[0])
    worksheet1.write(8,3,numbJVmeas[1])        
    worksheet1.write(9,0,"highest FF")
    theCursor.execute("SELECT FF FROM JVmeas") # * means everything
    numbJVmeas = theCursor.fetchall()
    #print(max(numbJVmeas)[0])
    worksheet1.write(9,1,max(numbJVmeas)[0])
    theCursor.execute("""SELECT batchname, users.user
                      FROM batch
                      INNER JOIN JVmeas ON batch.id = JVmeas.batch_id
                      INNER JOIN users ON batch.users_id = users.id
                      WHERE JVmeas.FF=?""", (max(numbJVmeas)[0],))
    numbJVmeas = theCursor.fetchall()[0]
    #print(numbJVmeas)
    worksheet1.write(9,2,numbJVmeas[0])
    worksheet1.write(9,3,numbJVmeas[1])
    
    worksheet1.write(14,0,"List of search criteria:")
    critlist=criteriaListdetailled+criteriaListdetailled2
    #print(critlist)
    for item in range(len(critlist)):
        for item0 in range(len(critlist[item])):
            if type(critlist[item][item0])!=list:
                worksheet1.write(item+15,item0,critlist[item][item0])
            else:
                for item1 in range(len(critlist[item][item0])):
                    worksheet1.write(item+15,item0+item1,critlist[item][item0][item1])

    ####################
    parametertables=sorted(parametertables, key=lambda s: s.casefold())
    print(parametertables)

    for item1 in parametertables:
        print("\n"+item1)
        tablenames=list(set(["batch","samples"]+[x.split('.')[0] for x in criteriaList+[item1]]))
#            print(tablenames)
        wherelist=["samples.batch_id = batch.id AND "]
        for item in tablenames:
            theCursor.execute("SELECT * FROM "+item)
            headcol=[x[0] for x in theCursor.description]  
            headcol=[x[:-3] for x in headcol if '_id' in x]  
            for item2 in headcol:
                if item2 in tablenames:
                    wherelist.append(item+'.'+item2+'_id = '+item2+'.id AND ')
        wherelist=list(set(wherelist))
#            print(wherelist)
        listwosamplename=["batch", "users"]
        if item1 in listwosamplename:
            SelectInstructions="SELECT batch.batchname, "
            heads=["batchname"]
            for item in dictparam[item1]:
                if item != "batch.batchname":
                    SelectInstructions+=item+', '
                    heads.append(item.split('.')[1])
        else:
            SelectInstructions="SELECT samples.samplename, "
            heads=["samplename"]
            for item in dictparam[item1]:
                if item != "samples.samplename":
                    SelectInstructions+=item+', '
                    heads.append(item.split('.')[1])
        
        SelectInstructions=SelectInstructions[:-2]+' FROM '
        for item in tablenames:
            SelectInstructions+=item+', '
        SelectInstructions=SelectInstructions[:-2]+" WHERE "
        for item in wherelist:
            SelectInstructions+=item
        for item in criteriaListdetailled:
            SelectInstructions+='('
            for item2 in item[1]:
                SelectInstructions+= item[0]+' = '+"'"+str(item2)+"' OR "
            SelectInstructions=SelectInstructions[:-4]+') AND '
        for item in criteriaListdetailled2:
            SelectInstructions+= '('+item[0] + ' BETWEEN ' + item[1] + ' AND ' + item[2] +') AND '
        theCursor.execute(SelectInstructions[:-4]+"ORDER BY samples.samplename ASC")
        data=list(set(theCursor.fetchall()))
        data=sorted(data, key=lambda x: str(x[0]))
        if data!=[]:
            data=[tuple(heads)]+data
            worksheetx = workbook.add_worksheet(item1)
            for item in range(len(data)):
                for item0 in range(len(data[item])):
                    worksheetx.write(item,item0,data[item][item0])
        if item1=="samples":
            length=len(data)-1
    
    worksheet1.write(12,0,length)
    worksheet1.write(12,1,"samples found")
    
    workbook.close() 
    
    parameterList=[]
    tablesAndcolnames=[]
    SetallcolnamesWOids=[]
    criteriaList=[]
    criteriaListdetailled=[]
    criteriaListdetailled2=[]    
    
    theCursor.close()
    db_conn.close()
    
#        self.master.destroy()
#        print(len(data))
    # QMessageBox.information('#results', str(length)+" samples found") 

    # messagebox.showinfo("#results", str(length)+" samples found")
#        self.backtomain()
    os.startfile(str(path[0]))#opens the just created excel file
    
    w=OpeningWindow()
    w.show()
    

 #%%######################################################################################################
class TimeEvol(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        
        self.resize(607, 151)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)
        self.setMinimumSize(QtCore.QSize(430, 92))
        self.gridLayout = QtWidgets.QGridLayout(self)
        self.setWindowTitle("Time Evolution Reading of database")
        
#%%######################################################################################################
class BoxPlot(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        
        self.resize(607, 151)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)
        self.setMinimumSize(QtCore.QSize(430, 92))
        self.gridLayout = QtWidgets.QGridLayout(self)
        self.setWindowTitle("Box Plots Reading of database")

###############################################################################        
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = OpeningWindow()
    sys.exit(app.exec())


