from ui_file import Ui_VisDAQ
import sys
from PyQt6.QtWidgets import QApplication, QWidget, QFileDialog, QMessageBox
from PyQt6 import QtCore, QtGui
from plotter_single import plotter_and_data_single
from mark10_force_reader import mark10_f_values, save_to_file, random_generator
from force_gauge_single import conditions_for_single_gauge
from os.path import expanduser
import time
# Assuming 'login', 'check_before_start', 'errors', 'colors' are available
# from login import Login
# from check_before_start import check_before_start

# --- Global Placeholder for Simplicity ---
# Note: Since the motor control is gone, we simulate the displacement input.
# For manual testing, the user must input the displacement value manually
# or the test must rely solely on time/force measurements.
# We will use the 'distance_to_be_covered' and 'speed_of_motor' fields 
# to calculate a theoretical displacement over time, but the physical movement is manual.

class AppWindow(QWidget):
	def __init__(self):
		super().__init__()
		self.ui = Ui_VisDAQ()
		self.ui.setupUi(self)
		# Load the logo if available, or just set the title
		try:
			self.setWindowIcon(QtGui.QIcon('images/logo.png'))
		except:
			pass
		self.show()

		# --- Application State Flags ---
		self.current_running_status = False # Indicates if a test is currently in progress
		self.recording_start_time = 0
		self.displacement_increment = 0.0 # Stores displacement manually entered by user during recording

		# --- UI Adjustments for Manual/Single Gauge Setup ---
		# Hide/Disable motor control elements (assuming their object names from ui_file.py)
		self.ui.select_motor_label.setVisible(False)
		self.ui.is_roller.setVisible(False)
		self.ui.is_axis.setVisible(False)
		self.ui.speed_label.setText("Recording Duration (s):") # Re-purpose for duration input
		self.ui.distance_label.setText("Displacement Increment (mm):") # Re-purpose for manual step input
		
		# Hide distal gauge elements
		self.ui.distal_force_gauge_groupbox.setVisible(False)
		self.ui.horizontalLayout_6.setVisible(False) # Hides all manual motor control buttons
		
		# --- Plotting Setup ---
		self.plotter = plotter_and_data_single(self.ui)
		self.ui.graphing_layout.addWidget(self.plotter.canvas)
		self.ui.graphing_layout.addWidget(self.plotter.toolbar)
		self.ui.graphing_layout.addWidget(self.plotter.canvas_all)
		self.ui.graphing_layout.addWidget(self.plotter.toolbar_all)

		self.button_clicks()

		# Initialize force gauge conditions (now only for the single Mark-10 gauge)
		self.gauge_handler = conditions_for_single_gauge(self.ui)
		self.data_file = None # Placeholder for the data file path

		# Automatically connect and start force gauge thread
		if self.gauge_handler.proximal_thread.connect_com():
			self.gauge_handler.proximal_connected = True
			self.gauge_handler.proximal_thread.start()
			self.ui.connect_proximal_force_gauge.setStyleSheet("background-color: rgb(99, 255, 138);")
			self.ui.connect_proximal_force_gauge.setText("Disconnect Force Gauge")
			self.ui.record_proximal_force_gauge.setChecked(True) # Force proximal recording
		else:
			self.ui.connect_proximal_force_gauge.setStyleSheet("background-color: rgb(255, 170, 0);")
			self.ui.connect_proximal_force_gauge.setText("Connect Force Gauge")
		
		self.ui.record_proximal_force_gauge.setEnabled(False)
		self.ui.record_distal_force_gauge.setVisible(False) # Should already be hidden, but disable just in case
		
		# --- GUI Update Timer ---
		# Timer for regular GUI updates (e.g., displaying force values, plotting)
		self.update_timer = QtCore.QTimer()
		self.update_timer.timeout.connect(self.update_gui)
		self.update_timer.start(50) # Update fast (50ms)

		# --- Data Reading Timer (for test recording) ---
		self.read_data_timer = QtCore.QTimer()
		self.read_data_timer.timeout.connect(self.record_manual_data)
		self.record_interval_ms = 100 # Default 10 times per second

	def record_manual_data(self):
		"""Reads force data and calculates displacement based on manual inputs."""
		
		current_time = time.time()
		ti = current_time - self.recording_start_time
		
		# Use the 'speed_of_motor' field as the recording duration limit
		try:
			duration_limit = float(self.ui.speed_of_motor.text())
		except ValueError:
			duration_limit = float('inf') # Record indefinitely if input is invalid

		# Use the 'distance_to_be_covered' field as the displacement increment for each step
		try:
			self.displacement_increment = float(self.ui.distance_to_be_covered.text())
		except ValueError:
			self.displacement_increment = 1.0 # Default displacement increment (1mm)

		if ti < duration_limit:
			force = round(self.gauge_handler.proximal_thread.present_reading, 3)
			
			# Calculate displacement based on time and the defined increment/interval
			# The displacement here is a virtual displacement for plotting, 
			# calculated based on the recording interval and the displacement increment.
			steps = len(self.plotter.temp_displacement) + 1
			displacement = round(self.displacement_increment * steps, 2)

			# Append current readings to temporary lists for plotting and saving
			self.plotter.temp_proximal_force.append(force)
			self.plotter.temp_time.append(round(ti, 2))
			self.plotter.temp_displacement.append(displacement)

			# Update real-time display of force and virtual displacement on video overlay
			self.gauge_handler.images_from_camera.displacement = displacement
			self.gauge_handler.images_from_camera.p_value = force

			self.ui.r_t.display(round(ti, 1)) # Update LCD with elapsed time
		else:
			# Test finished: stop timer, set status, save data, and update plot
			self.current_running_status = False
			self.read_data_timer.stop()
			
			# Ensure output directory exists and setup file name
			save_dir = self.ui.save_directory.text()
			test_name = self.ui.test_name.text()
			file_path = f"{save_dir}/{test_name}/data.csv"
			
			self.save_and_finish_test(file_path)

		pass

	def update_gui(self):
		"""Method to update the GUI elements regularly (real-time force value and camera feed)."""
		# Update displayed force value
		self.ui.proximal_force_value.setText(f"{self.gauge_handler.proximal_thread.present_reading:.3f} N")
		
		# Capture and display camera image
		self.gauge_handler.got_image()
		
		# If a test is running, update the plot
		if self.current_running_status:
			self.plotter.plot_now()
			
	def save_and_finish_test(self, file_path):
		"""Finalizes recording by stopping video, saving data, and updating UI results."""
		
		if self.ui.record_video.isChecked():
			self.gauge_handler.images_from_camera.should_record = False # Stop video recording

		# Use the same save_to_file structure, but only for proximal data
		self.gauge_handler.saver_thread.file_name = file_path
		self.gauge_handler.saver_thread.p_f_data = self.plotter.temp_proximal_force
		self.gauge_handler.saver_thread.t_data = self.plotter.temp_time
		self.gauge_handler.saver_thread.dis_data = self.plotter.temp_displacement
		self.gauge_handler.saver_thread.which_test = "proximal" # We reuse 'proximal' logic for saving
		self.gauge_handler.saver_thread.start() # Start saving data in a separate thread
		
		self.plotter.add_proximal_data() # Update plot with collected data (reusing proximal data function)
		
		# Reset the LCD display
		self.ui.r_t.display(0.0)
		self.current_running_status = False
		self.ui.start_test.setText("Start Recording")
		self.ui.start_test.setStyleSheet("background-color: rgb(170, 255, 127);")
		QMessageBox.information(self, "Test Finished", "Data recording and saving completed.")

	# Method to connect all UI button click signals to their respective slots
	def button_clicks(self):
		self.ui.browse_directory.clicked.connect(self.browse_now)
		self.ui.start_test.clicked.connect(self.start_recording_data)
		self.ui.set_proximal_zero.clicked.connect(self.gauge_handler.proximal_zero_clicked)
		self.ui.connect_proximal_force_gauge.clicked.connect(self.gauge_handler.connect_proximal)
		# Motor control buttons are now hidden, so no need to connect them.

	# Method to open a file dialog for selecting a save directory
	def browse_now(self):
		self.my_dir = QFileDialog.getExistingDirectory(
			self,
			"Open a folder",
			expanduser("~"),
			QFileDialog.ShowDirsOnly)
		if self.my_dir:
			self.ui.save_directory.setText(self.my_dir)

	def start_recording_data(self):
		"""Toggles the data recording process for manual operation."""
		
		if self.current_running_status:
			# STOP RECORDING
			self.read_data_timer.stop()
			self.current_running_status = False
			
			# Ensure output directory exists and setup file name
			save_dir = self.ui.save_directory.text()
			test_name = self.ui.test_name.text()
			file_path = f"{save_dir}/{test_name}/data.csv"
			
			# Save and finalize
			self.save_and_finish_test(file_path)
			
		else:
			# START RECORDING
			
			# Simple input validation
			try:
				# We reuse the speed and distance fields as Duration and Displacement Increment
				duration = float(self.ui.speed_of_motor.text()) 
				increment = float(self.ui.distance_to_be_covered.text())
				if duration <= 0 or increment <= 0:
					QMessageBox.warning(self, "Invalid Input", "Duration and Displacement Increment must be positive numbers.")
					return
			except ValueError:
				QMessageBox.warning(self, "Invalid Input", "Please enter valid numbers for Duration and Displacement Increment.")
				return
			
			if not self.gauge_handler.proximal_connected:
				QMessageBox.warning(self, "Connection Error", "Force Gauge is not connected. Cannot start recording.")
				return
			
			# Use a simplified check_before_start logic
			save_dir = self.ui.save_directory.text()
			test_name = self.ui.test_name.text()
			if not save_dir or not test_name:
				QMessageBox.warning(self, "Missing Info", "Please enter a Save Directory and a Test Name.")
				return

			# 1. Setup Data Folder
			os.makedirs(f"{save_dir}/{test_name}", exist_ok=True)
			
			# 2. Start Video Recording
			if self.ui.record_video.isChecked():
				video_file = f"{save_dir}/{test_name}/video.avi"
				self.gauge_handler.images_from_camera.start_recording(duration, video_file)
				self.gauge_handler.images_from_camera.record_time = duration
				self.gauge_handler.images_from_camera.video_file_name = video_file
				self.gauge_handler.images_from_camera.should_record = True
			
			# 3. Prepare Plotter and Start Timer
			self.gauge_handler.proximal_zero_clicked() # Zero the force gauge
			self.plotter.reset_temp_data()
			self.plotter.what_plot = "proximal"
			
			self.recording_start_time = time.time()
			self.current_running_status = True
			
			# Start the timer to sample data every 100ms
			self.read_data_timer.start(self.record_interval_ms) 
			
			self.ui.start_test.setText("Stop Recording")
			self.ui.start_test.setStyleSheet("background-color: rgb(255, 102, 102);")
			
	def closing_in(self):
		"""Handles cleanup when closing the application."""
		if self.current_running_status:
			self.read_data_timer.stop()
			if self.ui.record_video.isChecked():
				self.gauge_handler.images_from_camera.should_record = False # Stop video recording
		self.gauge_handler.proximal_thread.stop() # Stop the force gauge thread


# Function to handle application closing and motor stop
def close_it(app, ui):
	"""Executes the application and ensures cleanup on exit."""
	try:
		sys.exit(app.exec())
	finally:
		ui.closing_in()

# Main entry point for the application
if __name__ == "__main__":
	import os # Ensure os is imported here for safety
	# Simple placeholder for Login, assuming it's either handled or bypassed
	app = QApplication(sys.argv)
	# login = Login()
	# if login.exec_() == QtWidgets.QDialog.Accepted: 
	ui = AppWindow() 
	close_it(app, ui) # Use the unified close handler
