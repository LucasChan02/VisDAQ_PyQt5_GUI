from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from PyQt6.QtWidgets import QCheckBox
import numpy as np

class plotter_and_data():
	def __init__(self, ui):
		self.figure = Figure()
		self.figure_all = Figure()
		self.canvas = FigureCanvas(self.figure)
		self.canvas_all = FigureCanvas(self.figure_all)
		self.toolbar = NavigationToolbar(self.canvas, None)
		self.toolbar_all = NavigationToolbar(self.canvas_all,None)
		self.ax = self.figure.add_subplot(111)                    # Axis on which graph will be plotted
		self.ax_all = self.figure_all.add_subplot(111)
		self.ax.set_xlabel("Displacement (mm)")
		self.ax.set_ylabel("Force (N)")
		self.ax_all.set_xlabel("Displacement(mm)")
		self.ax_all.set_ylabel("Force (N)")
		self.ui = ui
		self.what_plot = None
		#########################  Saved values ###################################################
		self.y_values = []             # Conssts all y values
		self.displacement_values = []  # consists all displacement values
		self.time_values = []          # consists all time values
		self.checkboxes = []           # all the checkboxes are added to this list
		self.name = []                 # all test names
		########### Temporary values ##############################################################
		self.temp_proximal_force = []  # temporary proximal force
		self.temp_distal_force = []    # temporary distal force values are stored in this list
		self.temp_push_values = []     # temporary push values are stored in this list
		self.temp_displacement = []    # temporary displacements are stored here
		self.temp_time = []            # temporary time values are stred here
		self.colors = ["#000000", "#FFFF00", "#1CE6FF", "#FF34FF", "#FF4A46", "#008941", "#006FA6", "#A30059",
		"#FFDBE5", "#7A4900", "#0000A6", "#63FFAC", "#B79762", "#004D43", "#8FB0FF", "#997D87",
		"#5A0007", "#809693", "#FEFFE6", "#1B4400", "#4FC601", "#3B5DFF", "#4A3B53", "#FF2F80",
		"#61615A", "#BA0900", "#6B7900", "#00C2A0", "#FFAA92", "#FF90C9", "#B903AA", "#D16100",
		"#DDEFFF", "#000035", "#7B4F4B", "#A1C299", "#300018", "#0AA6D8", "#013349", "#00846F",
		"#372101", "#FFB500", "#C2FFED", "#A079BF", "#CC0744", "#C0B9B2", "#C2FF99", "#001E09",
		"#00489C", "#6F0062", "#0CBD66", "#EEC3FF", "#456D75", "#B77B68", "#7A87A1", "#788D66",
		"#885578", "#FAD09F", "#FF8A9A", "#D157A0", "#BEC459", "#456648", "#0086ED", "#886F4C",
		"#34362D", "#B4A8BD", "#00A6AA", "#452C2C", "#636375", "#A3C8C9", "#FF913F", "#938A81",
		"#575329", "#00FECF", "#B05B6F", "#8CD0FF", "#3B9700", "#04F757", "#C8A1A1", "#1E6E00",
		"#7900D7", "#A77500", "#6367A9", "#A05837", "#6B002C", "#772600", "#D790FF", "#9B9700",
		"#549E79", "#FFF69F", "#201625", "#72418F", "#BC23FF", "#99ADC0", "#3A2465", "#922329",
		"#5B4534", "#FDE8DC", "#404E55", "#0089A3", "#CB7E98", "#A4E804", "#324E72", "#6A3A4C",
		"#83AB58", "#001C1E", "#D1F7CE", "#004B28", "#C8D0F6", "#A3A489", "#806C66", "#222800",
		"#BF5650", "#E83000", "#66796D", "#DA007C", "#FF1A59", "#8ADBB4", "#1E0200", "#5B4E51",
		"#C895C5", "#320033", "#FF6832", "#66E1D3", "#CFCDAC", "#D0AC94", "#7ED379", "#012C58",     
		"#7A7BFF", "#D68E01", "#353339", "#78AFA1", "#FEB2C6", "#75797C", "#837393", "#943A4D",
		"#B5F4FF", "#D2DCD5", "#9556BD", "#6A714A", "#001325", "#02525F", "#0AA3F7", "#E98176",
		"#DBD5DD", "#5EBCD1", "#3D4F44", "#7E6405", "#02684E", "#962B75", "#8D8546", "#9695C5",
		"#E773CE", "#D86A78", "#3E89BE", "#CA834E", "#518A87", "#5B113C", "#55813B", "#E704C4",
		"#00005F", "#A97399", "#4B8160", "#59738A", "#FF5DA7", "#F7C9BF", "#643127", "#513A01",
		"#6B94AA", "#51A058", "#A45B02", "#1D1702", "#E20027", "#E7AB63", "#4C6001", "#9C6966",
		"#64547B", "#97979E", "#006A66", "#391406", "#F4D749", "#0045D2", "#006C31", "#DDB6D0",
		"#7C6571", "#9FB2A4", "#00D891", "#15A08A", "#BC65E9", "#FFFFFE", "#C6DC99", "#203B3C",
		"#671190", "#6B3A64", "#F5E1FF", "#FFA0F2", "#CCAA35", "#374527", "#8BB400", "#797868",
		"#C6005A", "#3B000A", "#C86240", "#29607C", "#402334", "#7D5A44", "#CCB87C", "#B88183",
		"#AA5199", "#B5D6C3", "#A38469", "#9F94F0", "#A74571", "#B894A6", "#71BB8C", "#00B433",
		"#789EC9", "#6D80BA", "#953F00", "#5EFF03", "#E4FFFC", "#1BE177", "#BCB1E5", "#76912F",
		"#003109", "#0060CD", "#D20096", "#895563", "#29201D", "#5B3213", "#A76F42", "#89412E",
		"#1A3A2A", "#494B5A", "#A88C85", "#F4ABAA", "#A3F3AB", "#00C6C8", "#EA8B66", "#958A9F",
		"#BDC9D2", "#9FA064", "#BE4700", "#658188", "#83A485", "#453C23", "#47675D", "#3A3F00",
		"#061203", "#DFFB71", "#868E7E", "#98D058", "#6C8F7D", "#D7BFC2", "#3C3E6E", "#D83D66",       
		"#2F5D9B", "#6C5E46", "#D25B88", "#5B656C", "#00B57F", "#545C46", "#866097", "#365D25",
		"#252F99", "#00CCFF", "#674E60", "#FC009C", "#92896B"]

	def plot_now(self):
		self.ax.cla()
		if self.what_plot=="proximal":
			try:
				self.ax.set_xlabel("Displacement (mm)")
				self.ax.set_ylabel("Force (N)")
				self.ax.plot(self.temp_displacement, self.temp_proximal_force[:len(self.temp_displacement)])
			except:
				pass
		elif self.what_plot=="distal":
			try:
				self.ax.set_xlabel("Displacement (mm)")
				self.ax.set_ylabel("Force (N)")
				self.ax.plot(self.temp_displacement, self.temp_distal_force[:len(self.temp_displacement)])
			except:
				pass
		elif self.what_plot=="both":
			try:
				self.ax.set_xlabel("Displacement (mm)")
				self.ax.set_ylabel("Force (N)")
				self.ax.plot(self.temp_displacement, self.temp_proximal_force[:len(self.temp_displacement)])
				self.ax.plot(self.temp_displacement, self.temp_distal_force[:len(self.temp_displacement)])
				# self.ax.plot(self.temp_displacement, self.temp_push_values[:len(self.temp_displacement)])
			except:
				pass
		else:
			pass
		self.canvas.draw()
		pass

	def update_plots(self):
		self.ax_all.cla()
		for i in range(len(self.checkboxes)):
			if self.checkboxes[i].isChecked():
				self.ax_all.set_xlabel("Displacement(mm)")
				self.ax_all.set_ylabel("Force (N)")
				self.ax_all.plot(self.displacement_values[i], self.y_values[i], label = self.name[i], color=self.colors[i])
		self.canvas_all.draw()
		pass

	def remove_by_testname(self,testname):
		if testname in self.name:
			index = self.name.index(testname)
			self.y_values.remove(self.y_values[index])
			self.displacement_values.remove(self.displacement_values[index])
			self.time_values.remove(self.time_values[index])
			self.checkboxes[index].deleteLater()
			self.checkboxes.remove(self.checkboxes[index])
			self.name.remove(self.name[index])
		else:
			pass

	def add_checkbox(self):
		temp_checkbox = QCheckBox(self.ui.scrollAreaWidgetContents)
		temp_checkbox.setText(self.ui.test_name.text())
		temp_checkbox.setChecked(True)
		temp_checkbox.stateChanged.connect(self.update_plots)
		self.checkboxes.append(temp_checkbox)
		self.ui.verticalLayout_7.removeItem(self.ui.checkbox_spacer)
		self.ui.verticalLayout_7.addWidget(temp_checkbox)
		self.ui.verticalLayout_7.addItem(self.ui.checkbox_spacer)

	def add_proximal_data(self):
		self.name.append(self.ui.test_name.text())
		self.y_values.append(self.temp_proximal_force)
		self.time_values.append(self.temp_time)
		self.displacement_values.append(self.temp_displacement)
		
		self.ui.proximal_average_force.setText("Average force : "+str(round(np.array(self.temp_proximal_force).mean(),2))+" N")
		self.ui.proximal_maximum_force.setText(str(max(self.temp_proximal_force)))
		self.ui.proximal_maximum_force_position_value.setText(str(self.temp_displacement[self.temp_proximal_force.index(max(self.temp_proximal_force))]))
		
		self.temp_time = []
		self.temp_proximal_force = []
		self.temp_displacement = []
		self.add_checkbox()
		self.update_plots()
		
	def add_distal_data(self):
		self.name.append(self.ui.test_name.text())
		self.y_values.append(self.temp_distal_force)
		self.time_values.append(self.temp_time)
		self.displacement_values.append(self.temp_displacement)

		self.ui.distal_average_force.setText("Average force : "+str(round(np.array(self.temp_distal_force).mean(),2))+" N")
		self.ui.distal_maximum_force.setText(str(max(self.temp_distal_force)))
		self.ui.distal_maximum_force_position_value.setText(str(self.temp_displacement[self.temp_distal_force.index(max(self.temp_distal_force))]))
		
		self.temp_time = []
		self.temp_distal_force = []
		self.temp_displacement = []	
		self.add_checkbox()
		self.update_plots()

	def add_both_data(self):
		self.name.append(self.ui.test_name.text())
		self.y_values.append(self.temp_push_values)
		self.time_values.append(self.temp_time)
		self.displacement_values.append(self.temp_displacement)

		self.ui.proximal_average_force.setText("Average force : "+str(round(np.array(self.temp_proximal_force).mean(),2))+" N")
		self.ui.proximal_maximum_force.setText(str(max(self.temp_proximal_force)))
		self.ui.proximal_maximum_force_position_value.setText(str(self.temp_displacement[self.temp_proximal_force.index(max(self.temp_proximal_force))]))
		self.ui.distal_average_force.setText("Average force : "+str(round(np.array(self.temp_distal_force).mean(),2))+" N")
		self.ui.distal_maximum_force.setText(str(max(self.temp_distal_force)))
		self.ui.distal_maximum_force_position_value.setText(str(self.temp_displacement[self.temp_distal_force.index(max(self.temp_distal_force))]))
		
		self.temp_time = []
		self.temp_proximal_force = []
		self.temp_distal_force = []
		self.temp_push_values = []
		self.temp_displacement = []	
		self.add_checkbox()
		self.update_plots()