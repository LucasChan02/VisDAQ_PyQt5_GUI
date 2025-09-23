from PyQt6 import QtCore
import time

class update_gui(QtCore.QThread):
	gui_updator_signal = QtCore.pyqtSignal()

	def __init__(self):
		super(update_gui, self).__init__()
		self.not_stop = True 

	def run(self):
		self.start_time = time.time() 
		while self.not_stop:
			if (time.time() - self.start_time)>=0.1:
				self.gui_updator_signal.emit()
				self.start_time = time.time()
		pass
				
	def stop(self):
		self.not_stop = False