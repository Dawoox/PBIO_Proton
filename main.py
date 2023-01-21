import atexit
import random
import sqlite3
import time

import keyboard
import serial
import os
import logging
import coloredlogs
from pyfiglet import Figlet


def formatData(data):
    data = data.split(':')
    data.pop(0)
    return list(map(int, data))


class App:
    def __init__(self):
        # ADMIN CONFIG, YOU SHOULDN'T NEED TO EDIT THESES VALUES /!\
        self.DEFAULT_COM_PORT = 'COM4'
        self.DEFAULT_DB_PATH = 'pool1.db'
        self.EMULATE_ARDUINO_DATA = True
        self.EMULATE_MAX_DATA_JUMP = 5
        self.DEBUG_last_emulate_data = [0, 0, 0]
        self.DEBUG_ignore_precheck = True
        # IN-APP VARIABLES
        self.com_port = None
        self.serial_link = None
        self.db_conn = None
        self.data_validity = True
        self.zero_point = None

        # Config for the file logger
        # WIP: logging.basicConfig(filename='what_the_heck_just_happened.log', encoding='utf-8', level=logging.DEBUG)

        # Config for the console logger
        self.logger = logging.getLogger(__name__)
        coloredlogs.install(level='INFO', logger=self.logger, milliseconds=True)

    def send_command(self, command):
        if self.EMULATE_ARDUINO_DATA:
            self.logger.debug(f"EMULATING ARDUINO DATA set to True, {command} not sent")
        else:
            self.logger.info(f"SENDING ${command} COMMAND")
            self.serial_link.write(command.encode())
            self.serial_link.flush()
            self.logger.debug("WAITING FOR ARDUINO BOARD TO RESPOND")
            time.sleep(2)

    def readDataIn(self):
        if self.EMULATE_ARDUINO_DATA:
            data = []
            for i in range(3):
                data.append(random.randint(self.DEBUG_last_emulate_data[i] - self.EMULATE_MAX_DATA_JUMP,
                                           self.DEBUG_last_emulate_data[i] + self.EMULATE_MAX_DATA_JUMP))
            self.DEBUG_last_emulate_data = data
            return data
        else:
            try:
                data = self.serial_link.readline().decode()
            except serial.SerialException:
                self.logger.exception("NO NEW DATA FROM SERIAL PORT")
                exit()
            except TypeError:
                self.logger.exception("PORT DISCONNECTED OR USB-UART OCCURRED")
                exit()
            else:
                return data

    def exit_handler(self):
        if not self.EMULATE_ARDUINO_DATA:
            self.logger.info('Closing com port')
            self.serial_link.close()
        if self.db_conn:
            self.logger.info('Closing database link')
            self.db_conn.close()

    def storeData(self, data):
        cursor = self.db_conn.cursor()
        self.logger.debug(f"STORING DATA: {data}")
        cursor.execute("INSERT INTO data (time,sensor1,sensor2,sensor3) " +
                       "VALUES (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'), (?), (?), (?));",
                       (data[0], data[1], data[2]))
        self.db_conn.commit()

    def precheck(self):
        # Check if the zero point is already set
        if self.zero_point is None:
            self.logger.critical("ZERO POINT NOT SET")
            exit()
        # Check if the flag "EMULATE_ARDUINO_DATA" is set to True
        if self.EMULATE_ARDUINO_DATA:
            self.logger.critical("EMULATING ARDUINO DATA")
            self.logger.critical("DO NOT USE THIS MODE FOR PRODUCTION /!\\")
            exit()

    def connectToSerialPort(self):
        # SERIAL LINK SETUP
        self.com_port = str(input("Com port? (DEFAULT IS " + str(self.DEFAULT_COM_PORT) + ")"))
        if self.com_port == '':
            self.com_port = self.DEFAULT_COM_PORT
        self.logger.debug(f"TRIED TO ACCESS PORT: ${self.com_port}")
        try:
            self.serial_link = serial.Serial(port=self.com_port, baudrate=9600, timeout=1)
        except serial.SerialException:
            self.logger.exception("COM PORT LOCKED/UNKNOWN, PROTON IS SHUTTING DOWN")
            exit()
        self.logger.debug("WAITING FOR ARDUINO BOARD TO RESTART")

    def calibrate(self):
        self.DEBUG_last_emulate_data = self.readDataIn()
        pass

    def run(self):
        print(Figlet(font='slant').renderText('Proton'), end='')
        print("v1.9.1-RC2 - 19/01/2023 - Proton MMS(Monitoring and Management System)")
        print("Please ensure that the arduino board is already plug-in")
        self.logger.info("==================================================================")
        self.logger.info("Press Q at any time to close Proton")
        self.logger.info("Press X to calibrate the system")
        self.logger.info("DOING SO WHILE CAPTURING DATA WILL INVALIDATE ANY FURTHER DATA")
        self.logger.info("==================================================================")
        if self.DEBUG_ignore_precheck:
            self.logger.warning("/!\\ PRECHECK DISABLED /!\\")
        else:
            self.precheck()
        if not self.EMULATE_ARDUINO_DATA:
            print()
            self.connectToSerialPort()
            print()
        # Set exit handler
        atexit.register(self.exit_handler)
        time.sleep(2)
        # DATABASE CONNECTION SETUP
        self.logger.info(f"Initializing database connection..  (located at ~/${self.DEFAULT_DB_PATH})")
        self.db_conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), self.DEFAULT_DB_PATH))
        self.logger.info("==================================================================")
        # STARTUP
        self.send_command('run')
        self.logger.info("Now running...")
        while True:
            if keyboard.is_pressed('q'):
                self.logger.debug("Q PRESSED, EXITING")
                exit()
            if keyboard.is_pressed('x'):
                self.logger.debug("X PRESSED, CALIBRATING")
                self.calibrate()
            data_in = self.readDataIn()
            self.storeData(data_in)


if __name__ == '__main__':
    App().run()
