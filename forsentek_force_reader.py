from PyQt6 import QtCore
import time
import serial
import serial.tools.list_ports

class forsentek_f_values(QtCore.QThread):
    forsentek_connection_fail_signal = QtCore.pyqtSignal()        # Signal which indicates failing of mark10 fourge gauge
    forsentek_not_found_signal = QtCore.pyqtSignal()              # Signal which indicates with the given manufacturer, forsentek was not found
    forsentek_connection_lost_signal = QtCore.pyqtSignal()        # Signal for connection inturrption or lost

    def __init__(self):
        super(forsentek_f_values, self).__init__()
        self.com = "COM5"
        self.should_read = False                                   ### Flag which will decide should stop or not
        self.zero_value = 0
        self.found = True
        self.present_reading = 0
        self.record_starting_time = 0
        self.record = False
        self.s = None
        self.record_time = 0
        self.time_record = []
        self.force_record = []
        self.read_value = 0
        self.reading = 0

    def find_com(self):
        comlist = serial.tools.list_ports.comports()
        connected = []
        for element in comlist:
            connected.append(element)
        for connection in connected:
            if connection.manufacturer == 'Prolific':
                self.com = connection.device
                self.found = True

    def connect_com(self):                                        ### This function returns mark 10 object
        # self.find_com()
        if self.found:                                          # checking flag
            try:
                self.s = serial.Serial(self.com, 9600)
                print("Connected successfully")
                self.should_read = True
                return True                                       ### Set force unit to Newton
            except:
                self.forsentek_connection_fail_signal.emit()
                return False
        else:
            self.forsentek_not_found_signal.emit()
            print("Didn't found Forsentek load cell")
            return False

    def run(self):
        start = time.time()
        while self.should_read:
            try:
                if self.s.in_waiting >= 16:
                    if (time.time() - start) > 0.01:
                        _ = self.s.readline()
                        present_reading = self.s.readline()
                        if chr(present_reading[5]) == 'A' or chr(present_reading[5]) == '@':
                            self.read_value = '+' + str(round(int(present_reading[6:-2]) * 0.00001, 5))
                        else:
                            self.read_value = '-' + str(round(int(present_reading[6:-2]) * 0.00001, 5))
                        # self.s.flushInput()
                        self.reading_ = float(self.read_value)*9.81
                        self.reading = round((self.reading_ - self.zero_value),2)
                        start = time.time()
            except KeyboardInterrupt:
                self.s.close()
                print('getting out')
                break
        pass

    def stop(self):
        self.should_read = False                            ### This will toggle the flag and stop the force reading  
        time.sleep(10)
        self.s.flushInput()
        self.s.close()

    def set_zero(self):
        self.zero_value = self.reading_                      ### This will give a new zero value
