# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['Main20210921exe32bit_v3.py'],
             pathex=['C:\\Users\\serjw\\Documents\\nBox\\PythonScripts\\SolarSim\\SolarSimPklab-SERIS-20210921exe\\labCode\\32bit'],
             binaries=[],
             datas=[	('C:\\Users\\serjw\\Documents\\nBox\\PythonScripts\\SolarSim\\SolarSimPklab-SERIS-210921exe\\labCode\\32bit\\GUIfiles\\loadingsavingtemplate.py','.'),
			('C:\\Users\\serjw\\Documents\\nBox\\PythonScripts\\SolarSim\\SolarSimPklab-SERIS-210921exe\\labCode\\32bit\\KeithleyCode\\myKeithleyFunctions.py','.'),
			('C:\\Users\\serjw\\Documents\\nBox\\PythonScripts\\SolarSim\\SolarSimPklab-SERIS-210921exe\\labCode\\32bit\\KeithleyCode\\ArduinoComm.py','.'),
			('C:\\Users\\serjw\\Documents\\nBox\\PythonScripts\\SolarSim\\SolarSimPklab-SERIS-210921exe\\labCode\\32bit\\Otherfunctions\\database_Tables.py','.'),
			('C:\\Users\\serjw\\Documents\\nBox\\PythonScripts\\SolarSim\\SolarSimPklab-SERIS-210921exe\\labCode\\32bit\\Otherfunctions\\database_reading.py','.'),
			('C:\\Users\\serjw\\Documents\\nBox\\PythonScripts\\SolarSim\\SolarSimPklab-SERIS-210921exe\\labCode\\32bit\\Otherfunctions\\database_GeneralReading_pyqt.py','.'),
			('C:\\Users\\serjw\\Documents\\nBox\\PythonScripts\\SolarSim\\SolarSimPklab-SERIS-210921exe\\labCode\\32bit\\GUIfiles\\gui.py','.')],
             hiddenimports=['pyvisa','xlsxwriter','serial.tools','serial.tools.list_ports'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='PySoSim_20220319',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True )
