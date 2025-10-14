from mark10_force_reader import mark10_f_values, save_to_file, random_generator
import queue
import os
from PyQt6.QtWidgets import QMessageBox, QGraphicsPixmapItem
from PyQt6 import QtWidgets, QtGui
from errors import show_error
# from image_taker import image_taker
from forsentek_force_reader import forsentek_f_values
from errors import show_error
from colors import colors


class conditions_for_proximal():
	"""Manages force gauge connections, data handling, camera, and associated UI updates."""

	def __init__(self, ui):
		self.ui = ui

		# --- Data Queues ---
		# Queues for inter-thread communication and data buffering
		self.record_force_q = queue.Queue() # Queue for recorded force values
		self.record_time_q = queue.Queue()  # Queue for recorded time values
		self.image_queue = queue.Queue(1)   # Queue for camera images (buffer size 1)
		self.mark10_q = queue.Queue(1)      # Queue for Mark-10 specific data (buffer size 1)

		# --- Connection Status Flags ---
		self.proximal_connected = False
		self.distal_connected = False
		self.camera_connected = False

		# --- General Properties ---
		self.colors = colors() # Color utility instance
		self.proximal_force = 0 # Current reading from proximal force gauge
		self.distal_force = 0   # Current reading from distal force gauge

		self.temp_force_ = None # Temporary storage for force data (e.g., from signals)
		self.temp_time_ = None  # Temporary storage for time data (e.g., from signals)
		
		# --- Proximal Force Gauge (Mark-10) Setup -------
		self.proximal_thread = mark10_f_values() # QThread for Mark-10 force gauge communication
		
		# Connect Mark-10 thread signals to handler methods
		self.proximal_thread.mark10_connection_fail_signal.connect(self.proximal_connection_problem)
		self.proximal_thread.mark10_not_found_signal.connect(self.proximal_not_found)
		self.proximal_thread.mark10_connection_lost_signal.connect(self.proximal_connection_lost)

		# Connect UI buttons for proximal gauge control
		self.ui.connect_proximal_force_gauge.clicked.connect(self.connect_proximal)
		self.ui.set_proximal_zero.clicked.connect(self.proximal_zero_clicked)
		
		# --- Distal Force Gauge (Forsentek) Setup ---
		self.distal_thread = forsentek_f_values() # QThread for Forsentek force gauge communication
		
		# Connect Forsentek thread signals to handler methods
		self.distal_thread.forsentek_connection_fail_signal.connect(self.distal_connection_problem)
		self.distal_thread.forsentek_not_found_signal.connect(self.distal_not_found)
		self.distal_thread.forsentek_connection_lost_signal.connect(self.distal_connection_lost)

		# Connect UI buttons for distal gauge control
		self.ui.connect_distal_force_gauge.clicked.connect(self.connect_distal)
		self.ui.set_distal_zero.clicked.connect(self.distal_zero_clicked)

		# --- Camera and Graphics View Setup -------
		# self.scene = QtWidgets.QGraphicsScene() # Graphics scene for displaying camera feed
		# self.scene.setSceneRect(self.scene.itemsBoundingRect())
		# self.pixmap_item = QGraphicsPixmapItem() # Item to hold the camera image
		# self.scene.addItem(self.pixmap_item)
		# self.images_from_camera = image_taker(self.proximal_thread,self.distal_thread) # Camera handler instance
		# self.images_from_camera.image_signal.connect(self.got_image) # Connect camera signal if needed
		# self.ui.connect_camera.clicked.connect(self.connect_cam) # Connect camera UI button

		# --- Error Handling and Data Saving ---
		self.errors_ = show_error() # Error display utility
		self.saver_thread = save_to_file() # QThread for saving data to file

		# --- Data Storage for Plotting ---
		self.maximum_forces = []      # Stores maximum force values (unused in current context)
		self.maximum_force_x_val = [] # Stores x-values corresponding to maximum forces (unused)
		self.all_proximal_f_data = [] # List of all proximal force data sets for plotting
		self.all_proximal_t_data = [] # List of all proximal time data sets for plotting
		self.all_proximal_labels = [] # Labels for proximal data sets
		self.all_distal_f_data = []   # List of all distal force data sets for plotting
		self.all_distal_t_data = []   # List of all distal time data sets for plotting
		self.all_distal_labels = []   # Labels for distal data sets
		self.checkboxes = []          # List to hold dynamically created checkboxes for plot visibility

	def connect_cam(self):
		"""Connects or disconnects the camera and updates the UI accordingly."""
		if self.camera_connected:
			self.images_from_camera.stop() # Stop camera thread
			self.camera_connected = False
			self.ui.connect_camera.setStyleSheet("background-color: rgb(255, 170, 0);") # Set button color to orange (disconnected)
			self.ui.connect_camera.setText("Connect camera")
		else:
			self.images_from_camera.connect_cam() # Initialize camera connection
			self.images_from_camera.start()     # Start camera thread
			self.camera_connected = True
			self.ui.connect_camera.setStyleSheet("background-color: rgb(99, 255, 138);") # Set button color to green (connected)
			self.ui.connect_camera.setText("Disconnect camera")

	def got_image(self):
		"""Receives an image from the camera thread and displays it in the QGraphicsView."""
		if self.camera_connected:
			try:
				image = self.images_from_camera.final_image # Get the latest image from the camera
				# Convert OpenCV image (numpy array) to QImage and then to QPixmap for display
				self.ima = QtGui.QImage(image.data,image.shape[1],image.shape[0],QtGui.QImage.Format_RGB888)
				self.pixmap = QtGui.QPixmap.fromImage(self.ima)
				self.pixmap_item.setPixmap(self.pixmap) # Set the pixmap to the QGraphicsPixmapItem
			except Exception as e:
				print(f"Could not change video frame: {e}") # Log error if image conversion fails
		else:
			pass # Do nothing if camera is not connected

	def save_now(self, times, vals):
		"""Prepares and starts a thread to save force and time data to a CSV file."""
		self.saver_thread.file_name = self.ui.save_directory.text()+"/"+self.ui.test_name.text()+"/proximal.csv" # Set output file path
		self.saver_thread.all_time_data = times # Assign time data to saver thread
		self.saver_thread.all_force_data = vals # Assign force data to saver thread
		self.saver_thread.start() # Start the saving thread

		# Store data for 'all graphs' plotting feature
		self.all_proximal_labels.append(self.ui.test_name.text()+" proximal force")
		self.all_proximal_f_data.append(vals)
		self.all_proximal_t_data.append(times)
		self.add_checkboxes() # Add a new checkbox for the saved data set
		pass

	def add_checkboxes(self):
		"""Dynamically adds a QCheckBox to the UI for each saved data set, allowing plot visibility control."""
		temp_checkbox = QtWidgets.QCheckBox(self.ui.scrollAreaWidgetContents)
		temp_checkbox.setText(self.all_proximal_labels[-1]) # Set checkbox text to the latest data label
		temp_checkbox.setChecked(True) # Check the checkbox by default
		# temp_checkbox.stateChanged.connect(self.update_all_graphs) # Connect signal to update all graphs (currently commented out)
		self.checkboxes.append(temp_checkbox) # Add checkbox to the list

		# Insert the new checkbox into the vertical layout, maintaining spacer position
		self.ui.verticalLayout_7.removeItem(self.ui.checkbox_spacer)
		self.ui.verticalLayout_7.addWidget(temp_checkbox)
		self.ui.verticalLayout_7.addItem(self.ui.checkbox_spacer)
		# self.update_all_graphs() # Update all graphs after adding checkbox (currently commented out)

	# def update_all_graphs(self):
	# 	"""Updates the 'all graphs' plot based on which checkboxes are checked."""
	# 	checked = []
	# 	for i in range(len(self.checkboxes)):
	# 		if self.checkboxes[i].isChecked():
	# 			checked.append(i)
	# 	self.all_plotter.plot_all(self.all_proximal_t_data, self.all_proximal_f_data, checked, self.all_proximal_labels)

	# def plot__(self,times,vals):
	# 	"""Placeholder for plotting current data (e.g., from random generator)."""
	# 	self.current_plotter.plot_now(times,vals)

	def got_force_signal(self, f_vals):
		"""Receives force values from a signal and stores them temporarily."""
		self.temp_force_ = f_vals

	def got_time_signal(self, t_vals):
		"""Receives time values from a signal and stores them temporarily."""
		self.temp_time_ = t_vals

	def connect_proximal(self):
		"""Connects or disconnects the proximal (Mark-10) force gauge and updates the UI."""
		print(self.colors.colors[0]) # Debug print
		print("Clicked") # Debug print
		if self.proximal_connected:
			self.proximal_connected = False
			self.proximal_thread.stop() # Stop the force gauge reading thread
			self.ui.connect_proximal_force_gauge.setStyleSheet("background-color: rgb(255, 170, 0);") # Set button color to orange
			self.ui.connect_proximal_force_gauge.setText("Connect Proximal force gauge")
		else:
			if self.proximal_thread.connect_com(): # Attempt to connect to the COM port
				self.proximal_connected = True
				self.proximal_thread.start() # Start the force gauge reading thread
				self.ui.connect_proximal_force_gauge.setStyleSheet("background-color: rgb(99, 255, 138);") # Set button color to green
				self.ui.connect_proximal_force_gauge.setText("Disconnect Proximal force gauge")

	def connect_distal(self):
		"""Connects or disconnects the distal (Forsentek) force gauge and updates the UI."""
		print("Clicked") # Debug print
		if self.distal_connected:
			self.distal_connected = False
			self.distal_thread.stop() # Stop the force gauge reading thread
			self.ui.connect_distal_force_gauge.setStyleSheet("background-color: rgb(255, 170, 0);") # Set button color to orange
			self.ui.connect_distal_force_gauge.setText("Connect Distal force gauge")
		else:
			if self.distal_thread.connect_com(): # Attempt to connect to the COM port
				self.distal_connected = True
				self.distal_thread.start() # Start the force gauge reading thread
				self.ui.connect_distal_force_gauge.setStyleSheet("background-color: rgb(99, 255, 138);") # Set button color to green
				self.ui.connect_distal_force_gauge.setText("Disconnect Distal force gauge")

	def proximal_zero_clicked(self):
		"""Sends a command to the proximal force gauge thread to set its current reading to zero."""
		self.proximal_thread.set_zero()

	def proximal_not_found(self):
		"""Handles the signal when the proximal force gauge is not found, updating status and showing an error."""
		print("Proximal force gauge is not connected") # Debug print
		self.proximal_connected = False
		self.errors_.proximal_not_found() # Display error message to the user

	def proximal_connection_problem(self):
		"""Handles connection failure for the proximal force gauge, updating status and showing an error."""
		print("Got error from thread. Could not connect gauge") # Debug print
		self.proximal_connected = False
		self.errors_.proximal_connection_problem() # Display error message to the user

	def proximal_connection_lost(self):
		"""Handles the signal when connection to the proximal force gauge is lost, updating UI and status."""
		print("Connection to proximal force gauge has been lost") # Debug print
		self.ui.connect_proximal_force_gauge.setStyleSheet("background-color: rgb(255, 170, 0);") # Set button color to orange
		self.ui.connect_proximal_force_gauge.setText("Connect Proximal force gauge")
		self.errors_.proximal_connection_problem() # Display error message to the user
		self.proximal_connected = False

	def distal_zero_clicked(self):
		"""Sends a command to the distal force gauge thread to set its current reading to zero."""
		self.distal_thread.set_zero()

	def distal_not_found(self):
		"""Handles the signal when the distal force gauge is not found, updating status and showing an error."""
		print("Distal force gauge is not connected") # Debug print
		self.distal_connected = False
		self.errors_.distal_not_found() # Display error message to the user

	def distal_connection_problem(self):
		"""Handles connection failure for the distal force gauge, updating status and showing an error."""
		print("Got error from thread. Could not connect distal gauge") # Debug print
		self.distal_connected = False
		self.errors_.distal_connection_problem() # Display error message to the user

	def distal_connection_lost(self):
		"""Handles the signal when connection to the distal force gauge is lost, updating UI and status."""
		print("Connection to distal force gauge has been lost") # Debug print
		self.ui.connect_distal_force_gauge.setStyleSheet("background-color: rgb(255, 170, 0);") # Set button color to orange
		self.ui.connect_distal_force_gauge.setText("Connect Proximal force gauge") # Note: This text should probably be "Connect Distal force gauge"
		self.errors_.distal_connection_problem() # Display error message to the user
		self.distal_connected = False

	def got_proximal_force(self, val):
		"""Receives proximal force value and updates the UI display."""
		self.proximal_force = val
		self.ui.proximal_force_value.setText(str(val))

	def start_clicked(self):
		"""Placeholder method for actions to take when a 'start' button is clicked (currently unused)."""
		pass

	def start_recording(self):
		"""Placeholder method for initiating data recording (currently unused)."""
		pass




