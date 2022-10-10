#! python3


import sqlite3

"""
#list of tables:
batch
samples
cells
JVmeas
MPPmeas

#sqlite variable type: TEXT, NULL, INTEGER, REAL, BLOB
"""
def CreateAllTables(db_conn):
    
    theCursor = db_conn.cursor()

#%%    
    try: 
        theCursor.execute("""CREATE TABLE IF NOT EXISTS batch(
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                batchname TEXT NOT NULL,
                users_id INTEGER,
                FOREIGN KEY(users_id) REFERENCES users(id) ON DELETE CASCADE
                );""")
        db_conn.commit()
    except sqlite3.OperationalError:
        print("Table batch couldn't be created")
    try: 
        theCursor.execute("""CREATE TABLE IF NOT EXISTS users(
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                user TEXT NOT NULL UNIQUE
                );""")
        db_conn.commit()
    except sqlite3.OperationalError:
        print("Table users couldn't be created")
    try:
        theCursor.execute("""CREATE TABLE IF NOT EXISTS samples(
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                samplename TEXT NOT NULL,
                batch_id INTEGER,
                FOREIGN KEY(batch_id) REFERENCES batch(id) ON DELETE CASCADE
                );""")
        db_conn.commit()
    except sqlite3.OperationalError:
        print("Table samples couldn't be created")        
    try:
        theCursor.execute("""CREATE TABLE IF NOT EXISTS cells(
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                cellname TEXT,
                AllpixSeq TEXT,
                pixelarea_id REAL,
                samples_id INTEGER,
                batch_id INTEGER,
                FOREIGN KEY(pixelarea_id) REFERENCES pixelarea(id),
                FOREIGN KEY(batch_id) REFERENCES batch(id) ON DELETE CASCADE,
                FOREIGN KEY(samples_id) REFERENCES samples(id)
                );""")
        db_conn.commit()
    except sqlite3.OperationalError:
        print("Table cells couldn't be created")
    try:
        theCursor.execute("""CREATE TABLE IF NOT EXISTS pixelarea(
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                pixel_area REAL
                )""")
        db_conn.commit()
    except sqlite3.OperationalError:
        print("Table pixelarea couldn't be created")
    try:
        theCursor.execute("""CREATE TABLE IF NOT EXISTS JVmeas(
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                DateTimeJV TEXT,
                Eff REAL,
                Voc REAL,
                Jsc REAL,
                Isc REAL,
                FF REAL,
                Vmpp REAL,
                Jmpp REAL,
                Pmpp REAL,
                Roc REAL,
                Rsc REAL,
                ScanDirect TEXT,
                Delay REAL,
                DelayShutter REAL,
                IntegTime REAL,
                Vmin REAL,
                Vmax REAL,
                MeasType TEXT,
                MeasNowType TEXT,
                StepSize REAL,
                CurrentLimit REAL,
                LightDark TEXT,
                IlluminationIntensity REAL,
                commentJV TEXT,
                MeasurementLongName TEXT,
                SampleNamePix TEXT,
                linktorawdata TEXT UNIQUE,
                aftermpp INTEGER,
                samples_id INTEGER,
                batch_id INTEGER,
                cells_id INTEGER,
                Refdiode_id INTEGER,
                FOREIGN KEY(batch_id) REFERENCES batch(id) ON DELETE CASCADE,
                FOREIGN KEY(samples_id) REFERENCES samples(id),
                FOREIGN KEY(cells_id) REFERENCES cells(id),
                FOREIGN KEY(Refdiode_id) REFERENCES Refdiode(id)
                );""")
        db_conn.commit()
    except sqlite3.OperationalError:
        print("Table JVmeas couldn't be created")
    try:
        theCursor.execute("""CREATE TABLE IF NOT EXISTS Refdiode(
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                IsRefDiodeMeasured INTEGER,
                RefDiodeNomCurr REAL,
                RefDiodeMeasCurr REAL,
                temperature REAL
                );""")
        db_conn.commit()
    except sqlite3.OperationalError:
        print("Table JVmeas couldn't be created")
    try:
        theCursor.execute("""CREATE TABLE IF NOT EXISTS MPPmeas(
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                DateTimeMPP TEXT,
                TrackingAlgo TEXT,
                MeasType TEXT,
                MeasNowType TEXT,
                TrackingDuration REAL,
                Vstart REAL,
                Vstep REAL,
                Delay REAL,
                PowerEnd REAL,
                PowerAvg REAL,
                commentmpp TEXT,
                LightDark TEXT,
                IlluminationIntensity REAL,
                MeasurementLongName TEXT,
                SampleNamePix TEXT,
                linktorawdata TEXT UNIQUE,
                samples_id INTEGER,
                batch_id INTEGER,
                cells_id INTEGER,
                Refdiode_id INTEGER,
                FOREIGN KEY(batch_id) REFERENCES batch(id) ON DELETE CASCADE,
                FOREIGN KEY(samples_id) REFERENCES samples(id),
                FOREIGN KEY(cells_id) REFERENCES cells(id),
                FOREIGN KEY(Refdiode_id) REFERENCES Refdiode(id)
                );""")
        db_conn.commit()
    except sqlite3.OperationalError:
        print("Table MPPmeas couldn't be created")    
#%%


###############################################################################        
if __name__ == '__main__':
    
    db_conn=sqlite3.connect(':memory:')
    
    CreateAllTables(db_conn)  
    
