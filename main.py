import atexit
import sqlite3
import time

import keyboard
import serial
import os
from pyfiglet import Figlet
from enum import Enum


class DataType(Enum):
    INFORMATION = 1
    DATA = 0

class App:
    def __init__(self):
        # ADMIN CONFIG, YOU SHOULDN'T NEED TO EDIT THESES VALUES /!\
        self.DEFAULT_COM_PORT = 'COM4'
        self.DEFAULT_DB_PATH = 'pool1.db'
        # IN-APP VARIABLES
        self.com_port = None
        self.serial_link = None
        self.db_conn = None

    def send_command(self, command):
        print(f"SENDING ${command} COMMAND")
        self.serial_link.write(command.encode())
        self.serial_link.flush()
        print("WAITING FOR ARDUINO BOARD TO RESPOND")
        time.sleep(2)

    def readDataIn(self):
        try:
            data = self.serial_link.readline().decode()
        except serial.SerialException as e:
            print("ERROR: NO NEW DATA FROM SERIAL PORT")
            print(e)
            exit()
        except TypeError as e:
            print("ERROR: PORT DISCONNECTED OR USB-UART OCCURRED")
            print(e)
            exit()
        else:
            if data[:11] == str('BEGIN_DATA:'):
                return DataType.DATA, data[11:len(data) - 11]
            else:
                return DataType.INFORMATION, data

    def exit_handler(self):
        print('Closing com port')
        self.serial_link.close()
        print('Closing database link')
        if self.db_conn:
            self.db_conn.close()

    def storeData(self, data):
        cursor = self.db_conn.cursor()
        print(data)
        cursor.execute("INSERT INTO data (TOC,isDataValid,sensor1) " +
                       "VALUES (datetime('now'), (?), (?));", (True, data,))
        self.db_conn.commit()

    def run(self):
        print(Figlet(font='slant').renderText('Proton'), end='')
        print("v1.7.0-A - 12/01/2023 - Proton MMS(Monitoring and Management System)")
        print("Please ensure that the arduino board is already plug-in")
        print("==================================================================")
        print("Press S at any time to stop the system")
        print("Press R at any time to restart the system")
        print("Press Q at any time to close Proton")
        print("DO NOT CLOSE BY ANY OTHER MEAN, DOING SO MIGHT RESULT IN DATA LOSSES /!\\")
        print("Press X to calibrate the system")
        print("DOING SO WHILE CAPTURING DATA WILL INVALIDATE ANY FURTHER DATA /!\\")
        print("==================================================================")
        print('\n')
        # SERIAL LINK SETUP
        self.com_port = str(input("Com port? (DEFAULT IS " + str(self.DEFAULT_COM_PORT) + ")"))
        if self.com_port == '':
            self.com_port = self.DEFAULT_COM_PORT
        try:
            self.serial_link = serial.Serial(port=self.com_port, baudrate=9600, timeout=1)
        except serial.SerialException as e:
            print(f"TRIED TO ACCESS PORT: ${self.com_port}")
            print("ERROR: COM PORT LOCKED/UNKNOWN, PROTON IS SHUTTING DOWN")
            print(e)
            exit()
        print("==================================================================")
        atexit.register(self.exit_handler)
        print("WAITING FOR ARDUINO BOARD TO RESTART")
        time.sleep(2)
        print("==================================================================")
        # DATABASE CONNECTION SETUP
        print(f"Initializing database connection..  (located at ~/${self.DEFAULT_DB_PATH}")
        self.db_conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), self.DEFAULT_DB_PATH))
        print("==================================================================")
        # STARTUP
        self.send_command('calibrate')
        self.send_command('run')
        print("NOW RECEIVING DATA")
        print("==================================================================")
        while True:
            if keyboard.is_pressed('s'):
                self.send_command('stop')
            if keyboard.is_pressed('r'):
                self.send_command('run')
            if keyboard.is_pressed('q'):
                exit()
            dataIn = self.readDataIn()
            # DEBUG ONLY: print(dataIn[0], dataIn[1])
            if dataIn[0] == DataType.DATA:
                self.storeData(dataIn[1])
            else:
                print(dataIn)
