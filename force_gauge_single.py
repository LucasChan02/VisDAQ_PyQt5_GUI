from mark10_force_reader import mark10_f_values, save_to_file
import queue
from PyQt6.QtWidgets import QGraphicsPixmapItem
from PyQt6 import QtWidgets, QtGui
# Assuming 'errors', 'image_taker', 'colors' are available
# from errors import show_error
# from image_taker import image_taker
# from colors import colors

# Placeholder classes/imports needed but not provided in full context:
class show_error:
    def __init__(self): pass
    def proximal_not_found(self): print("Error: Proximal gauge not found")
    def proximal_connection_problem(self): print("Error: Proximal connection problem")
class colors:
    def __init__(self): self.colors = ["#000000"]
class image_taker:
    def __init__(self, proximal, distal):
        self.proximal = proximal
        self.distal = distal
        self.final_image = None
        self.displacement = 0
        self.p_value = 0.0 # Proximal force value for overlay
        self.d_value = 0.0 # Distal force value (always 0 in this version)
        self.should_record = False
        self.record_time = 0
        self.video_file_name = None
        self.width = 720
        self.height = 720
        self.font = None # Placeholder, actual initialization in the original class
    def connect_cam(self): pass
    def start(self): pass
    def stop(self): pass
    def start_recording(self, time_for_record, video_file_name): pass
    def changes_in_image(self, image): 
        # Simplified placeholder for the image overlay logic
        return image 
# End of Placeholder classes

class single_gauge_conditions():
	"""Manages the single Mark-10 force gauge connection, data handling."""

	def __init__(self, ui):
		self.ui = ui

		# --- Data Queues (mostly unused but kept for compatibility) ---
		self.record_force_q = queue.Queue() 
		self.record_time_q = queue.Queue()  
		
		# --- Connection Status Flags ---
		self.proximal_connected = False

		# --- General Properties ---
		# self.colors = colors() # Color utility instance - removed import reliance
		self.proximal_force = 0 
		
		# --- Proximal Force Gauge (Mark-10) Setup -------
		self.proximal_thread = mark10_f_values() # QThread for Mark-10 force gauge communication
		
		# Connect Mark-10 thread signals to handler methods
		self.errors_ = show_error() # Initialize error utility (assuming errors.py is available)
		self.proximal_thread.mark10_connection_fail_signal.connect(self.proximal_connection_problem)
		self.proximal_thread.mark10_not_found_signal.connect(self.proximal_not_found)
		self.proximal_thread.mark10_connection_lost_signal.connect(self.proximal_connection_lost)

		# --- Data Saving ---
		self.saver_thread = save_to_file() # QThread for saving data to file

		# Connect UI buttons for proximal gauge control are connected in main_manual.py

	"""		# --- Camera and Graphics View Setup -------
		self.scene = QtWidgets.QGraphicsScene() # Graphics scene for displaying camera feed
		# Initial setup of scene for layout
		self.ui.graphing_layout.addWidget(QtWidgets.QGraphicsView(self.scene)) 
		self.scene.setSceneRect(self.scene.itemsBoundingRect())
		self.pixmap_item = QGraphicsPixmapItem() # Item to hold the camera image
		self.scene.addItem(self.pixmap_item)

		# NOTE: We pass a mock 'distal' thread/object to image_taker if it strictly requires two,
		# but since we removed forsentek_f_values import, we'll use a simplified image_taker init
		# Assuming image_taker is modified or prox.distal_thread is accessed safely
		self.images_from_camera = image_taker(self.proximal_thread, self) # Pass self as 'distal' proxy
		
		# Initialize camera connection (optional, as main_manual doesn't explicitly connect/disconnect)
		# self.images_from_camera.connect_cam() 
		# self.images_from_camera.start()     
	"""

	def connect_proximal(self):
		#Connects or disconnects the single (Mark-10) force gauge and updates the UI.
		if self.proximal_connected:
			self.proximal_connected = False
			self.proximal_thread.stop() # Stop the force gauge reading thread
			self.ui.connect_proximal_force_gauge.setStyleSheet("background-color: rgb(255, 170, 0);") # Set button color to orange
			self.ui.connect_proximal_force_gauge.setText("Connect Force Gauge")
		else:
			if self.proximal_thread.connect_com(): # Attempt to connect to the COM port
				self.proximal_connected = True
				self.proximal_thread.start() # Start the force gauge reading thread
				self.ui.connect_proximal_force_gauge.setStyleSheet("background-color: rgb(99, 255, 138);") # Set button color to green
				self.ui.connect_proximal_force_gauge.setText("Disconnect Force Gauge")

	def proximal_zero_clicked(self):
		"""Sends a command to the proximal force gauge thread to set its current reading to zero."""
		if self.proximal_connected:
			self.proximal_thread.set_zero()

	def proximal_not_found(self):
		"""Handles the signal when the force gauge is not found."""
		self.proximal_connected = False
		self.ui.connect_proximal_force_gauge.setStyleSheet("background-color: rgb(255, 170, 0);")
		self.ui.connect_proximal_force_gauge.setText("Connect Force Gauge")
		self.errors_.proximal_not_found()

	def proximal_connection_problem(self):
		"""Handles connection failure for the force gauge."""
		self.proximal_connected = False
		self.ui.connect_proximal_force_gauge.setStyleSheet("background-color: rgb(255, 170, 0);")
		self.ui.connect_proximal_force_gauge.setText("Connect Force Gauge")
		self.errors_.proximal_connection_problem()

	def proximal_connection_lost(self):
		"""Handles the signal when connection to the force gauge is lost."""
		self.proximal_connected = False
		self.ui.connect_proximal_force_gauge.setStyleSheet("background-color: rgb(255, 170, 0);")
		self.ui.connect_proximal_force_gauge.setText("Connect Force Gauge")
		self.errors_.proximal_connection_problem()
