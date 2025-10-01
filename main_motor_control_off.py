from ui_file import Ui_VisDAQ
import sys
from PyQt6.QtWidgets import QDialog, QApplication, QMainWindow, QWidget, QFileDialog, QMessageBox
from PyQt6 import QtCore, QtGui, QtWidgets
from plotter import plotter_and_data
from mark10_force_reader import mark10_f_values, save_to_file, random_generator
from force_gauges import conditions_for_proximal
from os.path import expanduser
import os
# from controller import motor_controller
from check_before_start import check_before_start
# from test_data import all_test_data
global f_value_experiment
f_value_experiment = 0
import time
from login import Login

# Main application window class, inheriting from QWidget
class AppWindow(QWidget):
	def __init__(self):
		super().__init__()
		self.ui = Ui_VisDAQ()
		self.ui.setupUi(self)
		self.setWindowIcon(QtGui.QIcon('images/logo.png'))
		self.show()

		# --- Application State Flags ---
		self.ready_for_test = True        ##### Flag for starting test
		self.should_plot = False
		self.current_running_status = False # Indicates if a test is currently in progress

		# --- Plotting Setup ---
		self.plotter = plotter_and_data(self.ui)
		# Add Matplotlib canvases and toolbars to the GUI layout
		self.ui.graphing_layout.addWidget(self.plotter.canvas)
		self.ui.graphing_layout.addWidget(self.plotter.toolbar)
		self.ui.graphing_layout.addWidget(self.plotter.canvas_all)
		self.ui.graphing_layout.addWidget(self.plotter.toolbar_all)
		self.test_time = 10
		self.test_start_time = 0
		self.button_clicks()

		# Initialize force gauge conditions and camera
		self.prox = conditions_for_proximal(self.ui)
		self.data_file = None # Placeholder for the data file path

		# Automatically connect and start force gauge threads
		if self.prox.proximal_thread.connect_com():
			self.prox.proximal_connected = True
			self.prox.proximal_thread.start()
			self.ui.connect_proximal_force_gauge.setStyleSheet("background-color: rgb(99, 255, 138);")
			self.ui.connect_proximal_force_gauge.setText("Disconnect Proximal force gauge")
		else:
			self.ui.connect_proximal_force_gauge.setStyleSheet("background-color: rgb(255, 170, 0);")
			self.ui.connect_proximal_force_gauge.setText("Connect Proximal force gauge")

		if self.prox.distal_thread.connect_com():
			self.prox.distal_connected = True
			self.prox.distal_thread.start()
			self.ui.connect_distal_force_gauge.setStyleSheet("background-color: rgb(99, 255, 138);")
			self.ui.connect_distal_force_gauge.setText("Disconnect Distal force gauge")
		else:
			self.ui.connect_distal_force_gauge.setStyleSheet("background-color: rgb(255, 170, 0);")
			self.ui.connect_distal_force_gauge.setText("Connect Distal force gauge")

		# --- Random Data Generator (for testing/simulation) ---
		self.random_thread = random_generator(self.prox.proximal_thread)
		# self.random_thread.sig.connect(self.plot__) # Connect signal if needed for plotting random data
		self.ui.clear_all_button.clicked.connect(self.start_random) # Connect button to start random data generation

		# --- Motor Controller Setup ---
		# self.controller = motor_controller()
		# self.controller.connect_com() # Attempt to connect to the motor controller

		# --- Pre-test Checks ---
		self.before_start_checks = check_before_start(self.ui,self.plotter,self.prox)

		# --- GUI Update Timer ---
		# Timer for regular GUI updates (e.g., displaying force values, plotting)
		self.update_timer = QtCore.QTimer()
		self.update_timer.timeout.connect(self.update_gui)
		self.update_timer.start(100) # Update every 100 milliseconds

		# --- Data Reading Timers (for different test types) ---
		# Timer for reading proximal force gauge data during a test
		self.read_proximal_timer = QtCore.QTimer()
		self.read_proximal_timer.timeout.connect(self.read_proximal_data)
		# Timer for reading distal force gauge data during a test
		self.read_distal_timer = QtCore.QTimer()
		self.read_distal_timer.timeout.connect(self.read_distal_data)
		# Timer for reading both proximal and distal force gauge data during a test
		self.read_both_timer = QtCore.QTimer()
		self.read_both_timer.timeout.connect(self.read_both)

	def read_proximal_data(self):
		ti = time.time()-self.test_start_time
		if ti<self.test_time:
			# Append current readings to temporary lists for plotting and saving
			self.plotter.temp_proximal_force.append(round(self.prox.proximal_thread.present_reading,2))
			self.plotter.temp_time.append(round(ti,2))
			# Calculate and append displacement
			self.prox.images_from_camera.displacement = round(int(self.ui.speed_of_motor.text())*ti,2)
			self.plotter.temp_displacement.append(self.prox.images_from_camera.displacement)
		else:
			# Test finished: stop timer, set status, save data, and update plot
			self.current_running_status = False
			self.read_proximal_timer.stop()
			self.prox.saver_thread.file_name = self.before_start_checks.data_file
			self.prox.saver_thread.p_f_data = self.plotter.temp_proximal_force
			self.prox.saver_thread.t_data = self.plotter.temp_time
			self.prox.saver_thread.dis_data = self.plotter.temp_displacement
			self.prox.saver_thread.which_test = "proximal"
			self.prox.saver_thread.start() # Start saving data in a separate thread
			self.plotter.add_proximal_data() # Update plot with collected data
		pass

	# Method to read data from the distal force gauge during a test
	def read_distal_data(self):
		ti = time.time()-self.test_start_time
		if ti<self.test_time:
			# Append current readings to temporary lists for plotting and saving
			self.plotter.temp_distal_force.append(self.prox.distal_thread.reading)
			self.plotter.temp_time.append(round(ti,2))
			# Calculate and append displacement
			self.prox.images_from_camera.displacement = round(int(self.ui.speed_of_motor.text())*ti,2)
			self.plotter.temp_displacement.append(self.prox.images_from_camera.displacement)
		else:
			# Test finished: stop timer, set status, save data, and update plot
			self.read_distal_timer.stop()
			self.prox.saver_thread.file_name = self.before_start_checks.data_file
			self.prox.saver_thread.d_f_data = self.plotter.temp_distal_force
			self.prox.saver_thread.t_data = self.plotter.temp_time
			self.prox.saver_thread.dis_data = self.plotter.temp_displacement
			self.prox.saver_thread.which_test = "distal"
			self.prox.saver_thread.start() # Start saving data in a separate thread
			self.plotter.add_distal_data() # Update plot with collected data
			self.current_running_status = False
		pass

	# Method to read data from both proximal and distal force gauges during a test
	def read_both(self):
		ti = time.time()-self.test_start_time
		if ti<self.test_time:
			# Get readings from both force gauges
			p = self.prox.proximal_thread.present_reading
			d = self.prox.distal_thread.reading
			# Calculate and append push values (distal/proximal ratio)
			if p==0:
				self.plotter.temp_push_values.append(0)
			else:
				self.plotter.temp_push_values.append((d/p)*100)
			# Append force readings, displacement, and time
			self.plotter.temp_proximal_force.append(p)
			self.plotter.temp_distal_force.append(d)
			self.prox.images_from_camera.displacement = round(int(self.ui.speed_of_motor.text())*ti,2)
			self.plotter.temp_displacement.append(self.prox.images_from_camera.displacement)
			self.plotter.temp_time.append(ti)
		else:
			# Test finished: stop timer, set status, save data, and update plot
			self.read_both_timer.stop()
			self.prox.saver_thread.file_name = self.before_start_checks.data_file
			self.prox.saver_thread.p_f_data = self.plotter.temp_proximal_force
			self.prox.saver_thread.d_f_data = self.plotter.temp_distal_force
			self.prox.saver_thread.push_data = self.plotter.temp_push_values
			self.prox.saver_thread.t_data = self.plotter.temp_time
			self.prox.saver_thread.dis_data = self.plotter.temp_displacement
			self.prox.saver_thread.which_test = "both"
			self.prox.saver_thread.start() # Start saving data in a separate thread
			self.plotter.add_both_data() # Update plot with collected data
			self.current_running_status = False
		pass

	# Method to update the GUI elements regularly
	def update_gui(self):
		# Update displayed force values
		self.ui.proximal_force_value.setText(str(self.prox.proximal_thread.present_reading))
		self.ui.distal_force_value.setText(str(self.prox.distal_thread.reading))
		# Capture and display camera image
		self.prox.got_image()
		# If a test is running, update the plot
		if self.current_running_status:
			self.plotter.plot_now()
			
	# Placeholder method for reading data (currently unused)
	def read_data(self):
		self.prox.proximal_thread.present_reading

	# Method to start the random data generation thread
	def start_random(self):
		self.random_thread.start()

	# Method to connect all UI button click signals to their respective slots
	def button_clicks(self):
		self.ui.browse_directory.clicked.connect(self.browse_now)
		self.ui.start_test.clicked.connect(self.start_recording_data) # Connect to a new method for recording
		# self.ui.move_axis_right_one.clicked.connect(self.move_axis_right_one)
		# self.ui.move_axis_left_one.clicked.connect(self.move_axis_left_one)
		# self.ui.move_axis_right_end.clicked.connect(self.move_axis_right_end)
		# self.ui.move_axis_left_end.clicked.connect(self.move_axis_left_end)
		
	# Method to open a file dialog for selecting a save directory
	def browse_now(self):
		# options = QFileDialog.DontResolveSymlinks | QFileDialog.ShowDirsOnly
		self.my_dir = QFileDialog.getExistingDirectory(
			self,
			"Open a folder",
			expanduser("~"),
			QFileDialog.ShowDirsOnly)
		self.ui.save_directory.setText(self.my_dir) # Display selected directory in UI
		print(self.my_dir)
		print(self.controller.controller_connected)

	# Method to initiate a test sequence
	def start_testing(self):
		# This method will now only handle pre-test checks and setup, not actual recording initiation
		self.before_start_checks.checks() # Perform pre-test checks
		self.before_start_checks.ready_for_test = True # Always ready for test without controller

		"""
		#################### Check if controller is connected ##########################
		if not self.controller.controller_connected:
			self.before_start_checks.ready_for_test = False
			# Display critical error message if controller is not connected
			_ = QMessageBox.critical(self, "Controller not connected",              ### error message
									"Test cannot be performed, because controller is not connected. Please connect the controller and restart the software in order to perform test.",
									QMessageBox.Retry)
		"""

		###############################################################################
		#################  Start recording ############################################
		if self.before_start_checks.ready_for_test and not self.current_running_status:
			# Calculate test duration based on distance and speed
			self.test_time = abs(float(self.ui.distance_to_be_covered.text())/float(self.ui.speed_of_motor.text()))                       ##### Time for which it should be recorded
			self.current_running_status = True # Set test running status to true

			# If video recording is enabled, start camera recording
			if self.ui.record_video.isChecked():
				self.prox.images_from_camera.start_recording(self.test_time, self.ui.save_directory.text()+"/"+self.ui.test_name.text()+"/video.avi")                                                         

			# Start data acquisition based on selected force gauges
			if self.ui.record_proximal_force_gauge.isChecked() and not self.ui.record_distal_force_gauge.isChecked():	
				self.prox.proximal_zero_clicked() # Zero the proximal force gauge
				self.test_start_time = time.time() # Record test start time
				self.read_proximal_timer.start(20) # Start timer for reading proximal data
				self.plotter.what_plot = "proximal" # Set plotter mode

			if not self.ui.record_proximal_force_gauge.isChecked() and self.ui.record_distal_force_gauge.isChecked():	
				self.prox.distal_zero_clicked() # Zero the distal force gauge
				self.test_start_time = time.time() # Record test start time
				self.read_distal_timer.start(20) # Start timer for reading distal data
				self.plotter.what_plot = "distal" # Set plotter mode

			if self.ui.record_proximal_force_gauge.isChecked() and self.ui.record_distal_force_gauge.isChecked():	
				self.prox.proximal_thread.proximal_zero_clicked() # Zero both force gauges
				self.prox.distal_zero_clicked()
				self.test_start_time = time.time() # Record test start time
				self.read_both_timer.start(20) # Start timer for reading both data
				self.plotter.what_plot = "both" # Set plotter mode

			# If video recording is enabled, configure camera for recording
			if self.ui.record_video.isChecked():
				self.prox.images_from_camera.record_time = self.test_time
				self.prox.images_from_camera.video_file_name = self.ui.save_directory.text()+"/"+self.ui.test_name.text()+"/video.avi"
				self.prox.images_from_camera.should_record = True

			# Control motor movement based on axis or roller selection
			# if self.ui.is_axis.isChecked():
			# 	self.controller.rotate_axis_signal(int(self.ui.speed_of_motor.text()), int(self.ui.distance_to_be_covered.text()))     ##### Sending signal to controller for motor movement
			# else:
			# 	self.controller.rotate_roller_signal(int(self.ui.speed_of_motor.text()), int(self.ui.distance_to_be_covered.text()))
			
	def start_recording_data(self):
		"""Initiates the data recording process based on selected force gauges and video option."""
		if self.before_start_checks.ready_for_test and not self.current_running_status:
			self.test_time = abs(float(self.ui.distance_to_be_covered.text())/float(self.ui.speed_of_motor.text()))
			self.current_running_status = True

			if self.ui.record_video.isChecked():
				self.prox.images_from_camera.start_recording(self.test_time, self.ui.save_directory.text()+"/"+self.ui.test_name.text()+"/video.avi")
				self.prox.images_from_camera.record_time = self.test_time
				self.prox.images_from_camera.video_file_name = self.ui.save_directory.text()+"/"+self.ui.test_name.text()+"/video.avi"
				self.prox.images_from_camera.should_record = True
			
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

			# Since motor controller is disabled, no motor movement commands here
			# The test duration (self.test_time) will still be calculated but not used for motor control.

	# Method to stop the motor controller when closing the application
	def closing_in(self):
		# self.controller.stop()
		pass # No controller to stop

	# Methods for manual motor control (moving axis right/left)
	# def move_axis_right_one(self):
	# 	self.controller.rotate_axis_one_right()

	# def move_axis_left_one(self):
	# 	self.controller.rotate_axis_one_left()

	# def move_axis_right_end(self):
	# 	self.controller.rotate_axis_signal(1,50)

	# def move_axis_left_end(self):
	# 	self.controller.rotate_axis_signal(-1,50)

# Function to handle application closing and motor stop
def close_it(app, ui):
	app.exec()
	try:
		ui.closing_in() # Stop motor if UI is available
	except:
		pass

# Main entry point for the application
if __name__ == "__main__":
	import sys
	app = QApplication(sys.argv)
	login = Login() # Initialize login dialog
	# if login.exec_() == QtWidgets.QDialog.Accepted: # Check for successful login
	ui = AppWindow() # Create and show the main application window
	ui.show()
	sys.exit(close_it(app, ui)) # Exit application after closing

