import os
from pathlib import Path
import xlsxwriter
import copy
import sqlite3
#%%######################################################################################################
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use("Qt5Agg")
#%%######################################################################################################
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5 import QtTest
# from PyQt5.QtCore.QElapsedTimer import timer
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QAction, QTableWidgetItem
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

import tkinter as tk
from tkinter import messagebox, Entry, Button, Toplevel, OptionMenu, Frame, StringVar, Listbox
from tkinter import filedialog

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
criteriaexclusionlist=['JVmeas.commentJV','JVmeas.linktorawdata','JVmeas.SampleNamePix','JVmeas.MeasurementLongName',
                       'MPPmeas.commentmpp', 'MPPmeas.linktorawdata'] #cannot restrict search from those criteria

dropdowncriteria=['batch.batchname','users.user','samples.samplename',
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
class DBReadingapp(Toplevel):

    def __init__(self, *args, **kwargs):
        
        Toplevel.__init__(self, *args, **kwargs)
        Toplevel.wm_title(self, "DBReadingapp")
        Toplevel.config(self,background="white")
        self.wm_geometry("300x150")
        center(self)
        self.initUI()

    def initUI(self):
        self.master.withdraw()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.canvas0 = tk.Canvas(self, borderwidth=0, background="#ffffff")
        self.canvas0.pack(side="left", fill="both", expand=True)
        
        Button(self.canvas0, text="Welcome to the\nUltimate Database Reading System",
               command = self.on_start, width=100).pack(expand=1)


    def on_start(self):
        directory=os.path.join(str(Path(os.path.abspath(__file__)).parent.parent.parent),'Database')

        path=os.path.join(directory,'CUMcGeheeGeneralDB.db')

        self.db_conn=sqlite3.connect(path)
        self.theCursor=self.db_conn.cursor()
        self.SELECTwindow()
            
    def on_closing(self):        
        #if messagebox.askokcancel("Quit", "Do you want to quit?"):
        self.destroy()
        self.master.deiconify()
    
    class Drag_and_Drop_Listbox(tk.Listbox):
        #A tk listbox with drag'n'drop reordering of entries.
        def __init__(self, master, **kw):
            #kw['selectmode'] = tk.MULTIPLE
            kw['selectmode'] = tk.SINGLE
            kw['activestyle'] = 'none'
            tk.Listbox.__init__(self, master, kw)
            self.bind('<Button-1>', self.getState, add='+')
            self.bind('<Button-1>', self.setCurrent, add='+')
            self.bind('<B1-Motion>', self.shiftSelection)
            self.curIndex = None
            self.curState = None
        def setCurrent(self, event):
            ''' gets the current index of the clicked item in the listbox '''
            self.curIndex = self.nearest(event.y)
        def getState(self, event):
            ''' checks if the clicked item in listbox is selected '''
            #i = self.nearest(event.y)
            #self.curState = self.selection_includes(i)
            self.curState = 1
        def shiftSelection(self, event):
            ''' shifts item up or down in listbox '''
            i = self.nearest(event.y)
            if self.curState == 1:
              self.selection_set(self.curIndex)
            else:
              self.selection_clear(self.curIndex)
            if i < self.curIndex:
              # Moves up
              x = self.get(i)
              selected = self.selection_includes(i)
              self.delete(i)
              self.insert(i+1, x)
              if selected:
                self.selection_set(i+1)
              self.curIndex = i
            elif i > self.curIndex:
              # Moves down
              x = self.get(i)
              selected = self.selection_includes(i)
              self.delete(i)
              self.insert(i-1, x)
              if selected:
                self.selection_set(i-1)
              self.curIndex = i

################################################################################
################################################################################        
#select which parameter we want to see in the final report (head of columns of the report table)
        
    def SELECTwindow(self):
        global tablesAndcolnames, SetallcolnamesWOids
        
        self.withdraw()
        self.selectionwindow = tk.Toplevel()
        center(self.selectionwindow)
        self.selectionwindow.protocol("WM_DELETE_WINDOW", self.backtomain)
        self.selectionwindow.wm_geometry("350x200")
        self.selectionwindow.wm_title("Selection of Search Parameters")
        
        
        self.theCursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = list(map(lambda x: x[0],self.theCursor.fetchall()))

        allcolnames=[]
        for item in tables:
            if item != 'sqlite_sequence':
                dat=self.theCursor.execute('SELECT * FROM '+ item)
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
#        print(SetallcolnamesWOids)     
        frame1=Frame(self.selectionwindow,borderwidth=0,  bg="white")
        frame1.pack(fill=tk.BOTH)
        
        self.parameterlist=SetallcolnamesWOids
        self.parameterChoice=StringVar()
        self.parameterChoice.set(self.parameterlist[0])
        self.dropMenuFrame = OptionMenu(frame1, self.parameterChoice, *self.parameterlist, command=self.addparametertolist)
        self.dropMenuFrame.pack(side="left")
        
        Button(frame1, text="Add the usuals",
               command = self.addtheusualparameters).pack(side="left")
        Button(frame1, text="Add all",
               command = self.addallparameters).pack(side="left")
      
        frame=Frame(self.selectionwindow,borderwidth=0,  bg="white")
        frame.pack(fill=tk.BOTH, expand=1)
        
#        self.listboxsamples=Listbox(frame,width=20, height=5, selectmode=tk.EXTENDED)
#        self.listboxsamples.pack(side="left", fill=tk.BOTH, expand=1)
#        scrollbar = tk.Scrollbar(frame, orient="vertical")
#        scrollbar.config(command=self.listboxsamples.yview)
#        scrollbar.pack(side="right", fill="y")
#        self.listboxsamples.config(yscrollcommand=scrollbar.set)
        
        self.listboxsamples = self.Drag_and_Drop_Listbox(frame)
        self.listboxsamples.pack(fill=tk.BOTH, expand=True)
        scrollbar = tk.Scrollbar(self.listboxsamples, orient="vertical")
        scrollbar.config(command=self.listboxsamples.yview)
        scrollbar.pack(side="right", fill="y")
        self.listboxsamples.config(yscrollcommand=scrollbar.set)
        
        frame3=Frame(self.selectionwindow,borderwidth=0,  bg="white")
        frame3.pack()
        Button(frame3, text="DeleteParam",
               command = self.deleteparameterfromlist).pack(side="left", fill=tk.BOTH,expand=1)
        Button(frame3, text="Validate",
               command = self.validateparameters).pack(side="left", fill=tk.BOTH,expand=1)
        Button(frame3, text="Cancel",
               command = self.backtomain).pack(side="left", fill=tk.BOTH,expand=1)
   
    def addallparameters(self):
        global parameterList, SetallcolnamesWOids
               
        for item in SetallcolnamesWOids:
            if item not in parameterList:
                parameterList.append(item)
                self.listboxsamples.insert(tk.END, item)
                
    def addtheusualparameters(self):
        global parameterList, SetallcolnamesWOids
        
        usualparam=['samples.samplename','users.user','pixelarea.pixel_area','JVmeas.DateTimeJV',
                    'JVmeas.Eff', 'JVmeas.FF','JVmeas.Jsc','JVmeas.Voc',]
        
        for item in usualparam:
            if item not in parameterList:
                parameterList.append(item)
                self.listboxsamples.insert(tk.END, item)
           
    def addparametertolist(self,a):
        global parameterList
        
        #cannot select twice the same parameter
        if self.parameterChoice.get() in parameterList:
            messagebox.showinfo("", "parameter already selected in the list")
        else:#add parameter to list
            parameterList.append(self.parameterChoice.get())
        
            #show it in the listbox        
            self.listboxsamples.insert(tk.END, self.parameterChoice.get())
        
    def deleteparameterfromlist(self):
        global parameterList
                
        selection = self.listboxsamples.curselection()
        
        pos = 0
        for i in selection :
            idx = int(i) - pos
            value=self.listboxsamples.get(i)
            ind = parameterList.index(value)
            del(parameterList[ind])
            self.listboxsamples.delete( idx,idx )
            pos = pos + 1
            
    def validateparameters(self):
        global parameterList
        
        if parameterList != []:
            parameterList=list(self.listboxsamples.get(0,tk.END))
#            print(parameterList)
            self.RestrictionCriteriawindow()
        else:
            messagebox.showinfo("", "at least one parameter should be selected")

    
################################################################################
################################################################################                       
#define here restriction criteria, to limit the search to specific samples...
            
    def RestrictionCriteriawindow(self):
        global tablesAndcolnames, SetallcolnamesWOids, criteriaList, criteriaexclusionlist
        
        self.withdraw()
        self.selectionwindow.destroy()
        self.criteriawindow = tk.Toplevel()
        center(self.criteriawindow)
        self.criteriawindow.protocol("WM_DELETE_WINDOW", self.backtomain)
        self.criteriawindow.wm_geometry("350x200")
        self.criteriawindow.wm_title("Selection of restriction criteria")        
        
#        tk.Label(self.criteriawindow, text="if no criteria are selected, the search will be done without\nrestriction, which can potentially generate a very large output file.", bg="black",fg="white").pack()

        colnamesnew=[item for item in SetallcolnamesWOids if item not in criteriaexclusionlist]
        frame1=Frame(self.criteriawindow,borderwidth=0,  bg="white")
        frame1.pack(fill=tk.BOTH, expand=1)        
        self.criterialist=colnamesnew
        self.parameterChoice=StringVar()
        self.parameterChoice.set(self.parameterlist[0])
        self.dropMenuFrame = OptionMenu(frame1, self.parameterChoice, *self.criterialist, command=self.addcriteriatolist)
        self.dropMenuFrame.pack(side="left")
#        Button(frame1, text="Add all to list",
#               command = self.addallcriteria).pack(side="left")
        
        frame=Frame(self.criteriawindow,borderwidth=0,  bg="white")
        frame.pack(fill=tk.BOTH, expand=1)
        
        self.listboxsamples=Listbox(frame,width=20, height=5, selectmode=tk.EXTENDED)
        self.listboxsamples.pack(side="left", fill=tk.BOTH, expand=1)
        scrollbar = tk.Scrollbar(frame, orient="vertical")
        scrollbar.config(command=self.listboxsamples.yview)
        scrollbar.pack(side="right", fill="y")
        self.listboxsamples.config(yscrollcommand=scrollbar.set)
        
        frame3=Frame(self.criteriawindow,borderwidth=0,  bg="white")
        frame3.pack()
        Button(frame3, text="DeleteCriteria",
               command = self.deletecriteriafromlist).pack(side="left", fill=tk.BOTH,expand=1)
        Button(frame3, text="Validate",
               command = self.validatecriteria).pack(side="left", fill=tk.BOTH,expand=1)
        Button(frame3, text="Cancel",
               command = self.backtomain).pack(side="left", fill=tk.BOTH,expand=1)
        self.numb_for=0
    
    def addallcriteria(self):
        global criteriaList, SetallcolnamesWOids, criteriaexclusionlist
                
        colnamesnew=[item for item in SetallcolnamesWOids if item not in criteriaexclusionlist]

        for item in colnamesnew:
            if item not in criteriaList:
                criteriaList.append(item)
                self.listboxsamples.insert(tk.END, item)
                
    def addcriteriatolist(self,a):
        global criteriaList, criteriaexclusionlist
        
        #cannot select twice the same criteria
        if self.parameterChoice.get() in criteriaList:
            messagebox.showinfo("", "criteria already selected in the list")
        else:#add criteria to list
            criteriaList.append(self.parameterChoice.get())
        
            #show it in the listbox        
            self.listboxsamples.insert(tk.END, self.parameterChoice.get())
    
    def deletecriteriafromlist(self):
        global criteriaList
                
        selection = self.listboxsamples.curselection()
        
        pos = 0
        for i in selection :
            idx = int(i) - pos
            value=self.listboxsamples.get(i)
            ind = criteriaList.index(value)
            del(criteriaList[ind])
            self.listboxsamples.delete( idx,idx )
            pos = pos + 1
    def validatecriteria(self):
        global criteriaList, SetallcolnamesWOids, criteriaexclusionlist
        
        if criteriaList!=[]:
            self.detaillingcriteriaList()
        else:
            messagebox.showinfo("", "at least one criteria should be selected")

        
        
################################################################################
################################################################################            
#generate popup windows to 

    
    def dropdowncriteriaRefinement(self,criterianame,listoptions):

        self.dropdownwindow = tk.Toplevel()
        center(self.dropdownwindow)
        self.dropdownwindow.protocol("WM_DELETE_WINDOW", self.backtomain)
        self.dropdownwindow.wm_geometry("400x200")
        self.dropdownwindow.wm_title("Select for: "+criterianame+" (multiple choice possible)")

        self.critname=criterianame
        
        frame2=Frame(self.dropdownwindow,borderwidth=0,  bg="white")
        frame2.pack(fill=tk.BOTH, expand=1)

        self.listboxsamples=Listbox(frame2,width=20, height=5, selectmode=tk.EXTENDED)
        self.listboxsamples.pack(side="left", fill=tk.BOTH, expand=1)
        scrollbar = tk.Scrollbar(frame2, orient="vertical")
        scrollbar.config(command=self.listboxsamples.yview)
        scrollbar.pack(side="right", fill="y")
        self.listboxsamples.config(yscrollcommand=scrollbar.set)
        
        for item in listoptions:
            self.listboxsamples.insert(tk.END, item)
        
        frame=Frame(self.dropdownwindow,borderwidth=0,  bg="white")
        frame.pack()
        self.buttondropdown=Button(frame, text="done",
               command = self.dropdownfinished).pack(side="left", fill=tk.BOTH,expand=1)

    def dropdownfinished(self):
        global criteriaListdetailled
        
        values = [self.listboxsamples.get(idx) for idx in self.listboxsamples.curselection()]
       
        if values!=[]:
            criteriaListdetailled.append([copy.deepcopy(self.critname),values])
            self.dropdownwindow.destroy()
            self.detaillingcriteriaList()
        else:
            messagebox.showinfo("", "you must pick at least one")

        
        
    def minmaxcriteriaRefinement(self, criterianame, minimum, maximum):
        
        self.minmaxwindow = tk.Toplevel()
        center(self.minmaxwindow)
        self.minmaxwindow.protocol("WM_DELETE_WINDOW", self.backtomain)
        self.minmaxwindow.wm_geometry("500x60")
        self.minmaxwindow.wm_title("Select for: "+criterianame+" (default values are min and max in DB)")
        
        self.critname=criterianame
        
        frame=Frame(self.minmaxwindow,borderwidth=0,  bg="white")
        frame.pack()
        tk.Label(frame, text="from", font=("Verdana", 10)).pack(side="left",fill=tk.BOTH,expand=1)
        self.min = tk.StringVar()
        self.entry1=Entry(frame, textvariable=self.min,width=20)
        self.entry1.pack(side="left",fill=tk.BOTH,expand=1)
        self.min.set(str(minimum))
        tk.Label(frame, text="to", font=("Verdana", 10)).pack(side="left",fill=tk.BOTH,expand=1)
        self.max = tk.StringVar()
        self.entry1=Entry(frame, textvariable=self.max,width=20)
        self.entry1.pack(side="left",fill=tk.BOTH,expand=1)
        self.max.set(str(maximum))
        
        Button(self.minmaxwindow, text="done",
               command = self.minmaxfinished).pack(side="left", fill=tk.BOTH,expand=1)
        
    def minmaxfinished(self):
        global criteriaListdetailled2
        
        criteriaListdetailled2.append([self.critname,self.min.get(),self.max.get()])
        
        self.minmaxwindow.destroy()
        self.detaillingcriteriaList()

    def bydeffunction(self):
        self.criteriawindow = tk.Toplevel()
        center(self.criteriawindow)
        self.criteriawindow.protocol("WM_DELETE_WINDOW", self.backtomain)
        self.criteriawindow.wm_geometry("100x100")
        self.criteriawindow.wm_title("Selection of Search Parameters")
        
        Button(self.criteriawindow, text="Ok",
               command = self.detaillingcriteriaList).pack(side="left", fill=tk.BOTH,expand=1)
        
        
#        self.detaillingcriteriaList()

    def detaillingcriteriaList(self):
        """
        now it iterates through the selected criteria and propose all possibilities existing in the DB
        in the future, it should restrict the possibilities after each criteria definition, in order to limit directly the search and not end up with 0 results after having set all criteria
        
        """
        global parameterList, criteriaList, criteriaexclusionlist, dropdowncriteria, fromtocriteria, timecriteria, criteriaListdetailled, criteriaListdetailled2
        try:
            self.criteriawindow.destroy()
        except: pass
    

#        print(len(criteriaList))
#        print(self.numb_for)
        
        if self.numb_for < len(criteriaList):
            
            if criteriaList[self.numb_for] in dropdowncriteria:
                self.theCursor.execute("SELECT "+criteriaList[self.numb_for].split('.')[1]+" FROM "+criteriaList[self.numb_for].split('.')[0])
                listoptions=list(set([x[0] for x in self.theCursor.fetchall()]))
                self.dropdowncriteriaRefinement(criteriaList[self.numb_for],listoptions)
#                print(criteriaList[self.numb_for])
            elif criteriaList[self.numb_for] in fromtocriteria:
                self.theCursor.execute("SELECT "+criteriaList[self.numb_for].split('.')[1]+" FROM "+criteriaList[self.numb_for].split('.')[0])
                listoptions=list(set([x[0] for x in self.theCursor.fetchall()]))
                minimum=min(listoptions)
                maximum=max(listoptions)
                self.minmaxcriteriaRefinement(criteriaList[self.numb_for],minimum,maximum)
#                print(criteriaList[self.numb_for])
            elif criteriaList[self.numb_for] in timecriteria:
                self.theCursor.execute("SELECT "+criteriaList[self.numb_for].split('.')[1]+" FROM "+criteriaList[self.numb_for].split('.')[0])
                listoptions=list(set([x[0].split(" ")[0] for x in self.theCursor.fetchall()]))
                datemin=min(listoptions)
                datemax=max(listoptions)
                self.minmaxcriteriaRefinement(criteriaList[self.numb_for],datemin,datemax)
#                print(criteriaList[self.numb_for])
            else:
                self.bydeffunction()
            
#            print(self.numb_for)
            self.numb_for+=1
#            print("")
        else:
#            print("finished")
#            print(parameterList)
#            print(criteriaList)
#            print(criteriaListdetailled)
#            print(criteriaListdetailled2)
            
            self.SearchingAndExporting()

################################################################################
################################################################################             

    def SearchingAndExporting(self):
        global parameterList, criteriaList, criteriaexclusionlist, dropdowncriteria, fromtocriteria, timecriteria
        global criteriaListdetailled, criteriaListdetailled2, tablesAndcolnames, SetallcolnamesWOids
        
        path = filedialog.asksaveasfilename(title="Select where to save the extracted data",defaultextension=".xlsx")
        
        try:
            self.dropdownwindow.destroy()
        except: pass
        try:
            self.minmaxwindow.destroy()
        except: pass
    
        parametertables=list(set([x.split('.')[0] for x in parameterList]))
        dictparam={}
        for item in parametertables:
            dictparam[item]=[]
        for item in parameterList:
            dictparam[item.split('.')[0]].append(item)
    
        ####################
        workbook = xlsxwriter.Workbook(path)
        worksheet1 = workbook.add_worksheet("DB info")
        
        self.theCursor.execute("SELECT COUNT(*) FROM batch") # * means everything
        numbbatch = self.theCursor.fetchall()[0][0]
        worksheet1.write(0,0,"number of batch")
        worksheet1.write(0,1,numbbatch)
        #print(numbbatch)
        self.theCursor.execute("SELECT COUNT(*) FROM samples") # * means everything
        numbsamples = self.theCursor.fetchall()[0][0]
        worksheet1.write(1,0,"number of samples")
        worksheet1.write(1,1,numbsamples)
        #print(numbsamples)
        self.theCursor.execute("SELECT COUNT(*) FROM cells") # * means everything
        numbcells = self.theCursor.fetchall()[0][0]
        worksheet1.write(2,0,"number of cells")
        worksheet1.write(2,1,numbcells)
        #print(numbcells)
        self.theCursor.execute("SELECT COUNT(*) FROM JVmeas") # * means everything
        numbJVmeas = self.theCursor.fetchall()[0][0]
        worksheet1.write(3,0,"number of JV scans")
        worksheet1.write(3,1,numbJVmeas)
        #print(numbJVmeas)
        worksheet1.write(6,0,"highest efficiency")
        self.theCursor.execute("SELECT Eff FROM JVmeas") # * means everything
        numbJVmeas = self.theCursor.fetchall()
        #print(max(numbJVmeas)[0])
        worksheet1.write(6,1,max(numbJVmeas)[0])
        self.theCursor.execute("""SELECT batchname, users.user
                          FROM batch
                          INNER JOIN JVmeas ON batch.id = JVmeas.batch_id
                          INNER JOIN users ON batch.users_id = users.id
                          WHERE JVmeas.Eff=?""", (max(numbJVmeas)[0],))
        numbJVmeas = self.theCursor.fetchall()[0]
        #print(numbJVmeas)
        worksheet1.write(6,2,numbJVmeas[0])
        worksheet1.write(6,3,numbJVmeas[1])
        worksheet1.write(7,0,"highest Voc")
        self.theCursor.execute("SELECT Voc FROM JVmeas") # * means everything
        numbJVmeas = self.theCursor.fetchall()
        #print(max(numbJVmeas)[0])
        worksheet1.write(7,1,max(numbJVmeas)[0])
        self.theCursor.execute("""SELECT batchname, users.user
                          FROM batch
                          INNER JOIN JVmeas ON batch.id = JVmeas.batch_id
                          INNER JOIN users ON batch.users_id = users.id
                          WHERE JVmeas.Voc=?""", (max(numbJVmeas)[0],))
        numbJVmeas = self.theCursor.fetchall()[0]
        #print(numbJVmeas)
        worksheet1.write(7,2,numbJVmeas[0])
        worksheet1.write(7,3,numbJVmeas[1])      
        worksheet1.write(8,0,"highest Jsc")
        self.theCursor.execute("SELECT Jsc FROM JVmeas") # * means everything
        numbJVmeas = self.theCursor.fetchall()
        #print(max(numbJVmeas)[0])
        worksheet1.write(8,1,max(numbJVmeas)[0])
        self.theCursor.execute("""SELECT batchname, users.user
                          FROM batch
                          INNER JOIN JVmeas ON batch.id = JVmeas.batch_id
                          INNER JOIN users ON batch.users_id = users.id
                          WHERE JVmeas.Jsc=?""", (max(numbJVmeas)[0],))
        numbJVmeas = self.theCursor.fetchall()[0]
        #print(numbJVmeas)
        worksheet1.write(8,2,numbJVmeas[0])
        worksheet1.write(8,3,numbJVmeas[1])        
        worksheet1.write(9,0,"highest FF")
        self.theCursor.execute("SELECT FF FROM JVmeas") # * means everything
        numbJVmeas = self.theCursor.fetchall()
        #print(max(numbJVmeas)[0])
        worksheet1.write(9,1,max(numbJVmeas)[0])
        self.theCursor.execute("""SELECT batchname, users.user
                          FROM batch
                          INNER JOIN JVmeas ON batch.id = JVmeas.batch_id
                          INNER JOIN users ON batch.users_id = users.id
                          WHERE JVmeas.FF=?""", (max(numbJVmeas)[0],))
        numbJVmeas = self.theCursor.fetchall()[0]
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

        for item1 in parametertables:
            if item1!="characsetups":
    #            print("\n"+item1)
                tablenames=list(set(["batch","samples"]+[x.split('.')[0] for x in criteriaList+[item1]]))
    #            print(tablenames)
                wherelist=["samples.batch_id = batch.id AND "]
                for item in tablenames:
                    self.theCursor.execute("SELECT * FROM "+item)
                    headcol=[x[0] for x in self.theCursor.description]  
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
                self.theCursor.execute(SelectInstructions[:-4]+"ORDER BY samples.samplename ASC")
                data=list(set(self.theCursor.fetchall()))
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
        
        self.theCursor.close()
        self.db_conn.close()
        self.deiconify()
#        self.master.destroy()
#        print(len(data))
        messagebox.showinfo("#results", str(length)+" samples found")
#        self.backtomain()
        os.startfile(path)
        
################################################################################
################################################################################   

    def backtomain(self):
        global parameterList, criteriaList,tablesAndcolnames, criteriaexclusionlist, dropdowncriteria, fromtocriteria, timecriteria
        global criteriaListdetailled, criteriaListdetailled2, SetallcolnamesWOids

        try:
            self.selectionwindow.destroy()
        except: pass    
        try:
            self.criteriawindow.destroy()
        except: pass
        try:
            self.dropdownwindow.destroy()
        except: pass
        try:
            self.minmaxwindow.destroy()
        except: pass
    
        parameterList=[]
        tablesAndcolnames=[]
        SetallcolnamesWOids=[]
        criteriaList=[]
        criteriaListdetailled=[]
        criteriaListdetailled2=[]    
        
        self.theCursor.close()
        self.db_conn.close()
        self.deiconify()
    

###############################################################################        
if __name__ == '__main__':
    
    app = DBReadingapp()
    app.mainloop()



