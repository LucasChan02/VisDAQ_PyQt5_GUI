from ui_file import Ui_Form
import sys
from PyQt6.QtWidgets import QDialog, QApplication, QMainWindow, QWidget, QFileDialog, QMessageBox
from PyQt6 import QtCore, QtGui, QtWidgets
from plotter import plotter_and_data
from mark10_force_reader import mark10_f_values, save_to_file, random_generator
from force_gauges import conditions_for_proximal
from os.path import expanduser
import os
from controller import motor_controller
from check_before_start import check_before_start
# from test_data import all_test_data
global f_value_experiment
f_value_experiment = 0
import time
from login import Login

class AppWindow(QWidget):
	def __init__(self):
		super().__init__()
		self.ui = Ui_Form()
		self.ui.setupUi(self)
		self.setWindowIcon(QtGui.QIcon('images/logo.png'))
		self.show()
		self.ready_for_test = True        ##### Flag for starting test
		self.should_plot = False
		self.current_running_status = False
		self.plotter = plotter_and_data(self.ui)
		self.ui.graphing_layout.addWidget(self.plotter.canvas)
		self.ui.graphing_layout.addWidget(self.plotter.toolbar)
		self.ui.graphing_layout.addWidget(self.plotter.canvas_all)
		self.ui.graphing_layout.addWidget(self.plotter.toolbar_all)
		self.test_time = 0
		self.test_start_time = 0
		self.button_clicks()
		self.prox = conditions_for_proximal(self.ui)
		self.data_file = None

		####
		self.random_thread = random_generator(self.prox.proximal_thread)
		# self.random_thread.sig.connect(self.plot__)
		####
		self.ui.clear_all_button.clicked.connect(self.start_random)
		####

		##### Controller define
		self.controller = motor_controller()
		self.controller.connect_com()
		self.before_start_checks = check_before_start(self.ui,self.plotter,self.prox)
		##### GUI updator
		self.update_timer = QtCore.QTimer()
		self.update_timer.timeout.connect(self.update_gui)
		self.update_timer.start(100)
		##### 
		self.read_proximal_timer = QtCore.QTimer()
		self.read_proximal_timer.timeout.connect(self.read_proximal_data)
		#####
		self.read_distal_timer = QtCore.QTimer()
		self.read_distal_timer.timeout.connect(self.read_distal_data)
		#####
		self.read_both_timer = QtCore.QTimer()
		self.read_both_timer.timeout.connect(self.read_both)

	def read_proximal_data(self):
		ti = time.time()-self.test_start_time
		if ti<self.test_time:
			self.plotter.temp_proximal_force.append(round(self.prox.proximal_thread.present_reading,2))
			self.plotter.temp_time.append(round(ti,2))
			self.prox.images_from_camera.displacement = round(int(self.ui.speed_of_motor.text())*ti,2)
			self.plotter.temp_displacement.append(self.prox.images_from_camera.displacement)
		else:
			self.current_running_status = False
			self.read_proximal_timer.stop()
			self.prox.saver_thread.file_name = self.before_start_checks.data_file
			self.prox.saver_thread.p_f_data = self.plotter.temp_proximal_force
			self.prox.saver_thread.t_data = self.plotter.temp_time
			self.prox.saver_thread.dis_data = self.plotter.temp_displacement
			self.prox.saver_thread.which_test = "proximal"
			self.prox.saver_thread.start()
			self.plotter.add_proximal_data()
		pass

	def read_distal_data(self):
		ti = time.time()-self.test_start_time
		if ti<self.test_time:
			self.plotter.temp_distal_force.append(self.prox.distal_thread.reading)
			self.plotter.temp_time.append(round(ti,2))
			self.prox.images_from_camera.displacement = round(int(self.ui.speed_of_motor.text())*ti,2)
			self.plotter.temp_displacement.append(self.prox.images_from_camera.displacement)
		else:
			self.read_distal_timer.stop()
			self.prox.saver_thread.file_name = self.before_start_checks.data_file
			self.prox.saver_thread.d_f_data = self.plotter.temp_distal_force
			self.prox.saver_thread.t_data = self.plotter.temp_time
			self.prox.saver_thread.dis_data = self.plotter.temp_displacement
			self.prox.saver_thread.which_test = "distal"
			self.prox.saver_thread.start()
			self.plotter.add_distal_data()
			self.current_running_status = False
		pass

	def read_both(self):
		ti = time.time()-self.test_start_time
		if ti<self.test_time:
			p = self.prox.proximal_thread.present_reading
			d = self.prox.distal_thread.reading
			if p==0:
				self.plotter.temp_push_values.append(0)
			else:
				self.plotter.temp_push_values.append((d/p)*100)
			self.plotter.temp_proximal_force.append(p)
			self.plotter.temp_distal_force.append(d)
			self.prox.images_from_camera.displacement = round(int(self.ui.speed_of_motor.text())*ti,2)
			self.plotter.temp_displacement.append(self.prox.images_from_camera.displacement)
			self.plotter.temp_time.append(ti)
		else:
			self.read_both_timer.stop()
			self.prox.saver_thread.file_name = self.before_start_checks.data_file
			self.prox.saver_thread.p_f_data = self.plotter.temp_proximal_force
			self.prox.saver_thread.d_f_data = self.plotter.temp_distal_force
			self.prox.saver_thread.push_data = self.plotter.temp_push_values
			self.prox.saver_thread.t_data = self.plotter.temp_time
			self.prox.saver_thread.dis_data = self.plotter.temp_displacement
			self.prox.saver_thread.which_test = "both"
			self.prox.saver_thread.start()
			self.plotter.add_both_data()
			self.current_running_status = False
		pass

	def update_gui(self):
		self.ui.proximal_force_value.setText(str(self.prox.proximal_thread.present_reading))
		self.ui.distal_force_value.setText(str(self.prox.distal_thread.reading))
		self.prox.got_image()
		if self.current_running_status:
			self.plotter.plot_now()
			
	def read_data(self):
		self.prox.proximal_thread.present_reading

	def start_random(self):
		self.random_thread.start()

	def button_clicks(self):
		self.ui.browse_directory.clicked.connect(self.browse_now)
		self.ui.start_test.clicked.connect(self.start_testing)
		self.ui.move_axis_right_one.clicked.connect(self.move_axis_right_one)
		self.ui.move_axis_left_one.clicked.connect(self.move_axis_left_one)
		self.ui.move_axis_right_end.clicked.connect(self.move_axis_right_end)
		self.ui.move_axis_left_end.clicked.connect(self.move_axis_left_end)
		
	def browse_now(self):
		# options = QFileDialog.DontResolveSymlinks | QFileDialog.ShowDirsOnly
		self.my_dir = QFileDialog.getExistingDirectory(
			self,
			"Open a folder",
			expanduser("~"),
			QFileDialog.ShowDirsOnly)
		self.ui.save_directory.setText(self.my_dir)
		print(self.my_dir)
		print(self.controller.controller_connected)

	def start_testing(self):
		self.before_start_checks.checks()

		#################### Check if controller is connected ##########################
		if not self.controller.controller_connected:
			self.before_start_checks.ready_for_test = False
			_ = QMessageBox.critical(self, "Controller not connected",              ### error message
									"Test cannot be performed, because controller is not connected. Please connect the controller and restart the software in order to perform test.",
									QMessageBox.Retry)

		###############################################################################
		#################  Start recording ############################################
		if self.before_start_checks.ready_for_test and not self.current_running_status:
			self.test_time = abs(float(self.ui.distance_to_be_covered.text())/float(self.ui.speed_of_motor.text()))                       ##### Time for which it should be recorded
			self.current_running_status = True

			if self.ui.record_video.isChecked():
				self.prox.images_from_camera.start_recording(self.test_time, self.ui.save_directory.text()+"/"+self.ui.test_name.text()+"/video.avi")                                                         
			
			if self.ui.record_proximal_force_gauge.isChecked() and not self.ui.record_distal_force_gauge.isChecked():	
				self.prox.proximal_zero_clicked()
				self.test_start_time = time.time()
				self.read_proximal_timer.start(20)
				self.plotter.what_plot = "proximal"

			if not self.ui.record_proximal_force_gauge.isChecked() and self.ui.record_distal_force_gauge.isChecked():	
				self.prox.distal_zero_clicked()
				self.test_start_time = time.time()
				self.read_distal_timer.start(20)
				self.plotter.what_plot = "distal"

			if self.ui.record_proximal_force_gauge.isChecked() and self.ui.record_distal_force_gauge.isChecked():	
				self.prox.proximal_thread.proximal_zero_clicked()
				self.prox.distal_zero_clicked()
				self.test_start_time = time.time()
				self.read_both_timer.start(20)
				self.plotter.what_plot = "both"

			if self.ui.record_video.isChecked():
				self.prox.images_from_camera.record_time = self.test_time
				self.prox.images_from_camera.video_file_name = self.ui.save_directory.text()+"/"+self.ui.test_name.text()+"/video.avi"
				self.prox.images_from_camera.should_record = True

			if self.ui.is_axis.isChecked():
				self.controller.rotate_axis_signal(int(self.ui.speed_of_motor.text()), int(self.ui.distance_to_be_covered.text()))     ##### Sending signal to controller for motor movement
			else:
				self.controller.rotate_roller_signal(int(self.ui.speed_of_motor.text()), int(self.ui.distance_to_be_covered.text()))
			
	def closing_in(self):
		self.controller.stop()

	def move_axis_right_one(self):
		self.controller.rotate_axis_one_right()

	def move_axis_left_one(self):
		self.controller.rotate_axis_one_left()

	def move_axis_right_end(self):
		self.controller.rotate_axis_signal(1,50)

	def move_axis_left_end(self):
		self.controller.rotate_axis_signal(-1,50)

def close_it(app, ui):
	app.exec()
	try:
		ui.closing_in()
	except:
		pass

if __name__ == "__main__":
	import sys
	app = QApplication(sys.argv)
	login = Login()
	# if login.exec_() == QtWidgets.QDialog.Accepted:
	ui = AppWindow()
	ui.show()
	sys.exit(close_it(app, ui))

