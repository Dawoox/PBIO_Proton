import atexit
import sqlite3
import time

import keyboard
import serial
import os
from pyfiglet import Figlet
from enum import Enum

# ADMIN CONFIG, STANDARD USER SHOULD NOT INTERFERE WITH THESES SETTINGS /!\
DEFAULT_DB_PATH = 'pool1.db'
DEFAULT_COM_PORT = 'COM4'

# GLOBAL VARIABLES, DO NOT EDIT
conn = None
data_validity = True


def exit_handler():
    print('Closing com port')
    ser.close()
    print('Closing database link')
    if conn:
        conn.close()


def send_start_command():
    print("SENDING RUN COMMAND")
    ser.write('run'.encode())
    ser.flush()
    print("WAITING FOR ARDUINO BOARD TO RESPOND")
    time.sleep(2)


def send_calibrate_command(doesDataRemaindValid):
    if not doesDataRemaindValid:
        data_validity = False
    print("SENDING CALIBRATE COMMAND")
    ser.write('calibrate'.encode())
    ser.flush()
    print("WAITING FOR ARDUINO BOARD TO RESPOND")
    time.sleep(2)


def send_stop_command():
    print("SENDING STOP COMMAND")
    ser.write('stop'.encode())
    ser.flush()
    print("WAITING FOR ARDUINO BOARD TO RESPOND")
    time.sleep(2)


class DATA_TYPE(Enum):
    INFORMATION = 1
    DATA = 0


def decode_input_string(input_str):
    if input_str[:11] == str('BEGIN_DATA:'):
        return DATA_TYPE.DATA, input_str[11:len(input_str) - 11]
    else:
        return DATA_TYPE.INFORMATION, input_str


def store_data(db_conn, data):
    cursor = db_conn.cursor()
    print(data_validity, data)
    cursor.execute("INSERT INTO data (TOC,isDataValid,sensor1) "
                   "VALUES (datetime('now'), (?), (?));", (data_validity, data,))
    db_conn.commit()


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
com_port = str(input("Com port? (DEFAULT IS " + str(DEFAULT_COM_PORT) + ")"))
if com_port == '':
    com_port = DEFAULT_COM_PORT
ser = None
try:
    ser = serial.Serial(port=com_port, baudrate=9600, timeout=1)
except:
    print("TRIED TO ACCESS PORT: " + com_port)
    print("ERROR: COM PORT LOCKED/UNKNOWN, PROTON IS SHUTTING DOWN")
    exit()
print("==================================================================")
atexit.register(exit_handler)
print("WAITING FOR ARDUINO BOARD TO RESTART")
time.sleep(2)
print("==================================================================")
print("Initializing database connection..  (located at ~/" + str(DEFAULT_DB_PATH))
conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), DEFAULT_DB_PATH))
print("==================================================================")
send_calibrate_command(True)
send_start_command()
print("NOW RECEIVING DATA")
print("==================================================================")

while True:
    if keyboard.is_pressed('s'):
        send_stop_command()
    if keyboard.is_pressed('r'):
        send_start_command()
    if keyboard.is_pressed('q'):
        exit()
    decoded_str = decode_input_string(ser.readline().decode())
    # DEBUG ONLY print(decoded_str[1], decoded_str[0])
    if decoded_str[0] == DATA_TYPE.DATA:
        store_data(conn, decoded_str)
    else:
        print(decoded_str)
