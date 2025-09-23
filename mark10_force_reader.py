from PyQt6 import QtCore
# import PySide6.QtCore
import time
import serial
import serial.tools.list_ports
import csv
import numpy as np 
import random

class mark10_f_values(QtCore.QThread):
	mark10_connection_fail_signal = QtCore.pyqtSignal()                               # Signal which indicates failing of mark10 fourge gauge
	mark10_not_found_signal = QtCore.pyqtSignal()
	mark10_connection_lost_signal = QtCore.pyqtSignal()

	def __init__(self):
		super(mark10_f_values, self).__init__()
		self.com = "COM3"
		self.should_read = False                                   ### Flag which will decide should stop or not
		self.zero_value = 0
		self.read_value = 0
		self.found = True
		self.present_reading = 0
		self.record_starting_time = 0
		self.record = False
		self.s = None
		self.record_time = 0
		self.time_record = []
		self.force_record = []
		self.click_zero = False

	def connect_com(self):                                        ### This function returns mark 10 object
		# self.find_com()
		if self.found:                                          # checking flag
			try:
				self.s = serial.Serial(self.com, 115200)
				time.sleep(0.1)
				self.s.write(b'N\r\n')
				time.sleep(0.1)
				self.s.write(b'CUR\r\n')
				print("Connected successfully")
				self.should_read = True
				return True                                       ### Set force unit to Newton
			except:
				self.mark10_connection_fail_signal.emit()
				return False
		else:
			self.mark10_not_found_signal.emit()
			print("Didn't found any mark10")
			return False

	def find_com(self):                             # This function finds the com port where mark 10 is connected  using manufacturer
		comlist = serial.tools.list_ports.comports()      # gives list of active COM ports
		connected = []
		for element in comlist:
			connected.append(element)
		for connection in connected:
			print(connection.manufacturer)
			if connection.manufacturer == 'Prolific':
				self.com = connection.device                     # COM port where mark 10 is connected
				self.found = True                                # Connection flag

	def run(self):
		# self.s = self.connect_com()                             ### Call for setup
		start = time.time()                                       ### Start time
		while self.should_read:                                   ### Loop will start for reading the data
			if self.click_zero:
				time.sleep(0.1)
				self.s.write(b'Z\r\n')
				self.click_zero = False
				time.sleep(0.1)
				pass
			try:
				self.s.write(b'?\r\n')                           ### Sending signal to force gauge to get current force value
				# time.sleep(0.01)                                  ### Wait for 10 ms
				available_bytes = self.s.in_waiting
				if available_bytes >= 8:
					try:
						self.read_value = float(self.s.readline()[:5])
						self.present_reading = round((self.read_value - self.zero_value),2)        ### Present value variable
					except:
						pass
			except:
				self.s.close()
				self.should_read = False
				print('getting out')
				self.mark10_connection_lost_signal.emit()
				break
		pass

	def start_recording(self, record_time):
		self.record_starting_time = time.time()
		self.record_time = record_time
		self.record = True

	def stop(self):
		self.should_read = False                                    ### This will toggle the flag and stop the force reading
		time.sleep(0.1)
		self.s.close()                                              ### break com connection and then leave the thread

	def set_zero(self):
		# self.zero_value = self.read_value                		    ### This will give a new zero value
		print("Came to set zero")
		self.click_zero = True

class save_to_file(QtCore.QThread):
	
	d_all_signal = QtCore.pyqtSignal(list, list)
	def __init__(self):
		super(save_to_file, self).__init__()
		self.set_all_none()

	def set_all_none(self):
		self.file_name = None
		self.p_f_data = []
		self.d_f_data = []
		self.t_data = []
		self.dis_data = []
		self.push_data = []
		self.which_test = None

	def run(self):
		if self.which_test == "proximal":
			self.write_proximal_data()
		elif self.which_test == "distal":
			self.write_distal_data()
		elif self.which_test == "both":
			self.write_both_data()
		else:
			print("Did not know which file to write")
		pass

	def write_proximal_data(self):
		with open(self.file_name, 'w', newline = '') as csvfile:
			csvwriter = csv.writer(csvfile)
			heads = ["Time","Displacement","Proximal Force(N)"]
			csvwriter.writerow(heads)
			for i in range(len(self.t_data)):	
				data_to_write = [self.t_data[i], self.dis_data[i], self.p_f_data[i]] 
				csvwriter.writerow(data_to_write)
		self.set_all_none()
		pass

	def write_distal_data(self):
		with open(self.file_name, 'w', newline = '') as csvfile:
			csvwriter = csv.writer(csvfile)
			heads = ["Time","Displacement","Distal Force(N)"]
			csvwriter.writerow(heads)
			for i in range(len(self.t_data)):	
				data_to_write = [self.t_data[i], self.dis_data[i], self.d_f_data[i]] 
				csvwriter.writerow(data_to_write)
		self.set_all_none()
		pass

	def write_both_data(self):
		with open(self.file_name, 'w', newline = '') as csvfile:
			csvwriter = csv.writer(csvfile)
			heads = ["Time","Displacement","Proximal Force(N)","Distal Force(N)","Pushability (%)"]
			csvwriter.writerow(heads)
			for i in range(len(self.t_data)):	
				data_to_write = [self.t_data[i], self.dis_data[i], self.p_f_data[i],
				self.d_f_data[i], self.push_data[i]] 
				csvwriter.writerow(data_to_write)
		self.set_all_none()
		pass

class random_generator(QtCore.QThread):
	sig = QtCore.pyqtSignal(list, list)
	def __init__(self, gg):
		super(random_generator, self).__init__()
		self.times = []
		self.val = []
		self.gg = gg
		self.emp = 1

	def run(self):
		self.times = []
		self.val = []
		i=0
		start = time.time()
		s_t = time.time()
		while True:
			self.emp = self.gg.present_reading
			temp = random.randint(1,100)
			self.times.append(time.time()-s_t)
			self.val.append(temp)
			i=i+1
			if (time.time()-start)>=0.1:	
				self.sig.emit(self.times, self.val)
				start = time.time()
			if (time.time()-s_t)>=10:
				break
			time.sleep(0.1)




