# -*- coding: utf-8 -*-
"""
Created on Fri Feb 26 07:07:31 2021

@author: serjw
"""

import serial
from serial.tools import list_ports
import time

#def ConnectToArduino(likelyport='COM1', baudrate=115200, timeout=.2,connected=0):
##    print([p.description for p in list_ports.comports()])
##    arduino_ports = [p.device for p in list_ports.comports() if 'Arduino' in p.description]
#    arduino=''
#    connected=0
#    try:
#        arduino = serial.Serial(likelyport,115200, timeout=.1)
#        print('arduino: ',arduino)
#        time.sleep(2)
#        datacomm=Arduino_write_read('comm',arduino)
#        print(datacomm)
#        print('here2')
#        if datacomm =='IcommwithU':
##            print('connected on '+likelyport)
#            connected=1
#        if datacomm == '':
#            print('not connected')
#            connected=0
#    except:
##        print('could not open port')
#        pass
#    if connected==0:
#        i=0
#        while(i<30):
#            print(i)
#            try:
#                arduino = serial.Serial('COM'+str(i),115200, timeout=.1)
#                time.sleep(2)
#                if Arduino_write_read('comm',arduino)=='IcommwithU':
#                    print('arduino connected on COM'+str(i))
#                    connected=1
#                    break
#                else:
#                    print(i)
#                    i+=1
#            except:
##                print(i)
#                i+=1
#        if i==30:
##            print('notconnected')
#            connected=0
#    
#        
#    return connected,arduino


def ConnectToArduino(likelyport='COM1', baudrate=115200, timeout=.1,connected=0):
    # print([p.description for p in list_ports.comports()])
    # arduino_ports = [p.device for p in list_ports.comports() if 'Arduino' in p.description]
    arduino=''
    connected=0
    try:
        arduino = serial.Serial(likelyport,115200, timeout=.1)
        print('arduino: ',arduino)
        time.sleep(2)
        datacomm=Arduino_write_read('comm',arduino)
        print(datacomm)
        print('here2')
        if datacomm =='IcommwithU':
            print('connected on '+likelyport)
            connected=1
        if datacomm == '':
            print('not connected')
            connected=0
    except:
        # print('could not open port')
        pass
    if connected==0:
        i=0
        while(i<30):
            try:
                arduino = serial.Serial('COM'+str(i),115200, timeout=.1)
                time.sleep(2)
                if Arduino_write_read('comm',arduino)=='IcommwithU':
 #                    print('arduino connected on COM'+str(i))
                    connected=1
                    break
                else:
                    print(i)
                    i+=1
            except:
                print(i)
                i+=1
        if i==30:
            print('notconnected')
            connected=0
    
    return connected,arduino

def Arduino_write_read(x,arduino):
    try:
        arduino.write(bytes(x, 'utf-8'))
        # time.sleep(0.5)
        # data = arduino.readline()
        i=0
        while(i<10):
            try:
                data = str(arduino.readline().strip().decode())
            except UnicodeDecodeError:#happens if try to communicate with a serial port that is not the proper arduino, like the keithley for example
                return ''
            # print('data: ',data)
            if data!='':
#                print('data: ',data)
                break
            else:
                time.sleep(0.1)
                i+=1
        return data
    except: #happens if arduino not connected
        return ''



    
if __name__ == "__main__":
    connected, arduino = ConnectToArduino('COM1', 115200, .1,0)
#    arduino = serial.Serial('COM1',115200, timeout=.1)
    
#    print([p for p in list_ports.comports()])
    
    