from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from PyQt6.QtWidgets import QCheckBox
import numpy as np

class plotter_and_data_single():
	def __init__(self, ui):
		self.figure = Figure()
		self.figure_all = Figure()
		# NOTE: Matplotlib backends now use qt6agg for PyQt6
		self.canvas = FigureCanvas(self.figure)
		self.canvas_all = FigureCanvas(self.figure_all)
		self.toolbar = NavigationToolbar(self.canvas, None)
		self.toolbar_all = NavigationToolbar(self.canvas_all,None)
		self.ax = self.figure.add_subplot(111)                    
		self.ax_all = self.figure_all.add_subplot(111)
		self.ax.set_xlabel("Displacement (mm)")
		self.ax.set_ylabel("Force (N)")
		self.ax_all.set_xlabel("Displacement (mm)")
		self.ax_all.set_ylabel("Force (N)")
		self.ui = ui
		self.what_plot = "proximal" # Always plots the single gauge data
		
		#########################  Saved values ###########################################
		self.y_values = []             # Stores all saved force values
		self.displacement_values = []  # Stores all saved displacement values
		self.time_values = []          # Stores all saved time values
		self.checkboxes = []           
		self.name = []                 # all test names
		
		########### Temporary values ######################################################
		self.temp_proximal_force = []  # only one force list needed
		self.temp_displacement = []    
		self.temp_time = []            
		
		# Color list for distinguishing saved plots
		self.colors = ["#000000", "#FF34FF", "#008941", "#006FA6", "#A30059",
		"#7A4900", "#63FFAC", "#B79762", "#8FB0FF", "#997D87",
		"#FFB500", "#C2FFED", "#A079BF", "#CC0744", "#C0B9B2", "#C2FF99",
		"#00489C", "#6F0062", "#0CBD66", "#EEC3FF"] # Shorter, cleaner color list

	def reset_temp_data(self):
		"""Clears temporary data lists before a new recording starts."""
		self.temp_time = []
		self.temp_proximal_force = []
		self.temp_displacement = []

	def plot_now(self):
		"""Real-time plotting of the current test data."""
		self.ax.cla()
		if self.what_plot == "proximal":
			try:
				# Only plot the single force data
				self.ax.set_xlabel("Displacement (mm)")
				self.ax.set_ylabel("Force (N)")
				# Ensure lengths match before plotting
				min_len = min(len(self.temp_displacement), len(self.temp_proximal_force))
				self.ax.plot(self.temp_displacement[:min_len], self.temp_proximal_force[:min_len], color="#1CE6FF")
			except Exception as e:
				# print(f"Plotting error: {e}")
				pass
		self.canvas.draw()
		pass

	def update_plots(self):
		"""Updates the 'all tests' plot based on selected checkboxes."""
		self.ax_all.cla()
		self.ax_all.set_xlabel("Displacement (mm)")
		self.ax_all.set_ylabel("Force (N)")
		
		for i in range(len(self.checkboxes)):
			if self.checkboxes[i].isChecked():
				self.ax_all.plot(self.displacement_values[i], 
								 self.y_values[i], 
								 label = self.name[i], 
								 color=self.colors[i % len(self.colors)]) # Cycle colors safely
		
		if len(self.checkboxes) > 0 and self.ax_all.has_data():
			self.ax_all.legend(loc='best')
		
		self.canvas_all.draw()
		pass

	def remove_by_testname(self, testname):
		"""Removes a saved test data set and its associated checkbox."""
		if testname in self.name:
			try:
				index = self.name.index(testname)
				self.y_values.pop(index)
				self.displacement_values.pop(index)
				self.time_values.pop(index)
				self.checkboxes[index].deleteLater()
				self.checkboxes.pop(index)
				self.name.pop(index)
				self.update_plots()
			except Exception as e:
				print(f"Error removing test: {e}")
		else:
			pass

	def add_checkbox(self):
		"""Adds a new checkbox for the completed test."""
		temp_checkbox = QCheckBox(self.ui.scrollAreaWidgetContents)
		temp_checkbox.setText(self.ui.test_name.text())
		temp_checkbox.setChecked(True)
		temp_checkbox.stateChanged.connect(self.update_plots)
		self.checkboxes.append(temp_checkbox)
		
		# Assuming checkbox_spacer is the last item in verticalLayout_7
		try:
			self.ui.verticalLayout_7.removeItem(self.ui.checkbox_spacer)
			self.ui.verticalLayout_7.addWidget(temp_checkbox)
			self.ui.verticalLayout_7.addItem(self.ui.checkbox_spacer)
		except Exception as e:
			# Fallback if spacer is missing (for compatibility)
			self.ui.verticalLayout_7.addWidget(temp_checkbox)


	def add_proximal_data(self):
		"""Aggregates the finished test data (renamed from add_proximal_data to be the main aggregator)."""
		# Only save if there is data
		if not self.temp_proximal_force:
			return

		self.name.append(self.ui.test_name.text())
		self.y_values.append(list(self.temp_proximal_force))
		self.time_values.append(list(self.temp_time))
		self.displacement_values.append(list(self.temp_displacement))
		
		force_array = np.array(self.temp_proximal_force)
		max_force = max(self.temp_proximal_force)
		max_index = self.temp_proximal_force.index(max_force)
		max_position = self.temp_displacement[max_index]

		# Update statistics display in the UI (reusing proximal fields)
		self.ui.proximal_average_force.setText("Average force : "+str(round(force_array.mean(), 3))+" N")
		self.ui.proximal_maximum_force.setText(str(round(max_force, 3)))
		self.ui.proximal_maximum_force_position_value.setText(str(round(max_position, 3)))
		
		# Clear temporary data in place
		self.reset_temp_data()
		
		self.add_checkbox()
		self.update_plots()
		
	# Removed add_distal_data and add_both_data as they are no longer needed
