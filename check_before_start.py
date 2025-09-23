import os 
from PyQt6.QtWidgets import QMessageBox
from errors import show_error

class check_before_start():
	def __init__(self,ui,plotter,prox):
		self.ui = ui
		self.plotter = plotter
		self.ready_for_test = True
		self.errors_ = show_error()
		self.data_file = None
		self.prox = prox
	
	def sensor_connection_tests(self):
		if self.ui.record_proximal_force_gauge.isChecked():
			if not self.prox.proximal_connected: 
				self.ready_for_test = False
				self.errors_.proximal_gauge_not_connected()

		if self.ui.record_distal_force_gauge.isChecked():
			if not self.prox.distal_connected:
				self.ready_for_test = False
				self.errors_.distal_gauge_not_connected()

	def checks(self):
		self.ready_for_test = True
		########################################################
		############### Sensor connectivity test ###############
		self.sensor_connection_tests()

		#####################################################################################
		###################### What is selected #############################################

		if not (self.ui.is_roller.isChecked() or self.ui.is_axis.isChecked()):
			self.ready_for_test = False
			self.errors_.info_about_move()

		#######################################################################################
		##### This will check if directory mentioned already exists or not ####################

		##### If directory does not exist ################################
		if not os.path.isdir(self.ui.save_directory.text()):
			self.ready_for_test = False
			reply = self.errors_.directory_already_exist()
			if reply == QMessageBox.Retry:
				self.ui.save_directory.setText("")

		######################################################################
		######## Check if test name is specified or not ???  #################
		if not self.ui.test_name.text():
			self.ready_for_test = False
			reply = self.errors_.test_name_not_specified()
			if reply == QMessageBox.Retry:
				self.ui.test_name.setText("")
		elif not os.path.isdir(self.ui.save_directory.text()+"/"+self.ui.test_name.text()):
			os.mkdir(self.ui.save_directory.text()+"/"+self.ui.test_name.text())

		###########################################################################################
		################## Check if test is done before or not ? ##################################

		self.data_file = self.ui.save_directory.text()+"/"+self.ui.test_name.text()+"/TestData.csv"

		if os.path.isfile(self.data_file):
			if  self.errors_.test_done_before() == QMessageBox.AcceptRole:
				os.remove(self.data_file)
				self.plotter.remove_by_testname(self.ui.test_name.text())
				pass
			else:
				self.ready_for_test = False
				self.ui.test_name.setText("")

		##############################################################################
		################## check speed of motor is specified or not ##################

		if not self.ui.speed_of_motor.text():
			self.ready_for_test = False
			self.errors_.speed_not_specified()

		################################################################################
		#################### Check distance is specified or not ########################

		if not self.ui.distance_to_be_covered.text():
			self.ready_for_test = False
			self.errors_.distance_not_specified()

