from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import (QApplication, QCheckBox, QColorDialog, QDialog,
		QErrorMessage, QFileDialog, QFontDialog, QFrame, QGridLayout,
		QInputDialog, QLabel, QLineEdit, QMessageBox, QPushButton)


class show_error(QDialog):
	def __init__(self, parent=None):
		super(show_error, self).__init__(parent)
		self.i_am_here = True
		self.motor_selection_message = "<p>Message boxes have a caption, a text, and up to three " \
			"buttons, each with standard or custom texts.</p>" \
			"<p>Click a button to close the message box. Pressing the Esc " \
			"button will activate the detected escape button (if any).</p>"
	
	def info_about_move(self):
		title = "Motor is not selected"
		error_message = "<p>No motor is selected for test.</p> Please select a motor to perform a test..."
		ms = QMessageBox.information(self,title, error_message)
		pass

	def info_about_recording(self):
		title = "None of the recording options is selected"
		error_message = "<p>No recording option is selected.<\p> Please select a recording option to perform a test..."
		self.reply = QMessageBox.information(self,title, error_message)

	def speed_not_specified(self):
		title = "Mototr speed not specified"
		error_message = "<p>You have not specified mototr speed.<\p> Please specify motor speed to perform a test..."
		self.reply = QMessageBox.information(self,title, error_message)

	def distance_not_specified(self):
		title = "Distance not specified"
		error_message = "<p>You have not specified how much distance has to be travelled in order to perform a test.<\p> Please specify..."
		self.reply = QMessageBox.information(self,title, error_message)

	def test_name_not_specified(self):
		reply = QMessageBox.critical(self, "Test name not specified",
					 "Test name is not specified. Please specify test name and try again.",      ##### error with test name
					 QMessageBox.StandardButtons(QMessageBox.StandardButton.Retry))
		return reply

	def directory_already_exist(self):
		reply = QMessageBox.critical(self, "Wrong Directory",              ### error message
					 "Directory does not exist ",
					 QMessageBox.StandardButtons(QMessageBox.StandardButton.Retry))
		return reply

	def test_done_before(self):
		msgBox = QMessageBox(QMessageBox.Icon.Warning, "QMessageBox.warning()",
				 "Already exist", QMessageBox.StandardButtons(QMessageBox.StandardButton.NoButton), self)
		msgBox.addButton("Overwrite", QMessageBox.ButtonRole.AcceptRole)
		msgBox.addButton("Change", QMessageBox.ButtonRole.RejectRole)
		return msgBox.exec()

	def filename_not_specified(self):
		title = "File name not specified"
		error_message = "You have to specify a filename in order to save your test results"
		self.reply = QMessageBox.information(self,title, error_message)

	def problem_with_mark10(self):
		title = "Problem with Mark10 force gauge"
		error_message = "Please check connection of force gauge"
		self.reply = QMessageBox.information(self,title, error_message)

	def proximal_connection_problem(self):
		_ = QMessageBox.information(self, "Unable to Connect Proximal Force Gauge",
									"Could not connect proximal force gauge. There could be problem with force gauge or its settings")
		pass

	def proximal_not_found(self):
		_ = QMessageBox.information(self, "Proximal Force Gauge Not Found",
									"System was unable to find proximal force gauge. Please connect the force gauge. If you have already connected it, then please check for the loose connection.")
		pass

	def distal_connection_problem(self):
		_ = QMessageBox.information(self, "Unable to Connect Distal Force Gauge",
									"Could not connect distal force gauge. There could be problem with force gauge or its settings")
		pass

	def distal_not_found(self):
		_ = QMessageBox.information(self, "Distal Force Gauge Not Found",
									"System was unable to find distal force gauge. Please connect the force gauge. If you have already connected it, then please check for the loose connection.")
		pass

	def controller_connection_problem(self):
		_ = QMessageBox.critical(self, "Problem with controller",              ### error message
				    "Unable to connect controller. You will not be able to perform any test if controller is not connected. Please connect properly and try again. ",
				    QMessageBox.StandardButtons(QMessageBox.StandardButton.Retry))
		pass

	def controller_not_found(self):
		_ = QMessageBox.critical(self, "Controller not found",              ### error message
				    "Unable to find controller. You will not be able to perform any test if controller is not connected. Please make sure it is connected properly and try again. ",
				    QMessageBox.StandardButtons(QMessageBox.StandardButton.Retry))
		pass

	def controller_not_connected(self):   ##### for not starting test
		_ = QMessageBox.critical(self, "Controller not connected",              ### error message
				    "Test cannot be performed, because controller is not connected. Please connect the controller and restart the software in order to perform test.",
				    QMessageBox.StandardButtons(QMessageBox.StandardButton.Retry))
		pass 

	def cannot_move_motor(self):
		_ = QMessageBox.critical(self, "Action cannot be performed",              ### error message
				    "Action cannot be performed, because controller is not connected. Please connect the controller and restart the software in order to perform test.",
				    QMessageBox.StandardButtons(QMessageBox.StandardButton.Retry))
		pass 

	def proximal_gauge_not_connected(self):
		title = "Proximal force sensor is not connected"
		error_message = "<p>Proximal sensor data should be recorded for your test but sensor is nopt connected.<\p> Please connect proximal force sensor to perform test."
		self.reply = QMessageBox.information(self,title, error_message)
		pass

	def distal_gauge_not_connected(self):
		title = "Distal force sensor is not connected"
		error_message = "<p>Distal sensor data should be recorded for your test but sensor is nopt connected.<\p> Please connect distal force sensor to perform test."
		self.reply = QMessageBox.information(self,title, error_message)
		pass