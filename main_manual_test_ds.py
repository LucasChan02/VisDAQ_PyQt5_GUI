from ui_file import Ui_VisDAQ
import sys
from PyQt6.QtWidgets import QDialog, QApplication, QMainWindow, QWidget, QFileDialog, QMessageBox
from PyQt6 import QtCore, QtGui, QtWidgets
from plotter import plotter_and_data
from mark10_force_reader import mark10_f_values, save_to_file
from force_gauges import conditions_for_proximal
from os.path import expanduser
import os
import time

class AppWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.ui = Ui_VisDAQ()
        self.ui.setupUi(self)
        self.setWindowIcon(QtGui.QIcon('images/logo.png'))
        self.show()

        # --- Application State Flags ---
        self.ready_for_test = True
        self.current_running_status = False
        
        # Hide motor control elements since we're manual now
        self.hide_motor_controls()

        # --- Plotting Setup ---
        self.plotter = plotter_and_data(self.ui)
        self.ui.graphing_layout.addWidget(self.plotter.canvas)
        self.ui.graphing_layout.addWidget(self.plotter.toolbar)
        self.ui.graphing_layout.addWidget(self.plotter.canvas_all)
        self.ui.graphing_layout.addWidget(self.plotter.toolbar_all)
        
        self.test_time = 0
        self.test_start_time = 0
        self.button_clicks()

        # Initialize force gauge conditions
        self.prox = conditions_for_proximal(self.ui)
        self.data_file = None

        # Automatically connect and start force gauge thread
        if self.prox.proximal_thread.connect_com():
            self.prox.proximal_connected = True
            self.prox.proximal_thread.start()
            self.ui.connect_proximal_force_gauge.setStyleSheet("background-color: rgb(99, 255, 138);")
            self.ui.connect_proximal_force_gauge.setText("Disconnect Proximal force gauge")
        else:
            self.ui.connect_proximal_force_gauge.setStyleSheet("background-color: rgb(255, 170, 0);")
            self.ui.connect_proximal_force_gauge.setText("Connect Proximal force gauge")

        # Disable distal force gauge since we only have one
        self.disable_distal_gauge()

        # --- GUI Update Timer ---
        self.update_timer = QtCore.QTimer()
        self.update_timer.timeout.connect(self.update_gui)
        self.update_timer.start(100)

        # --- Data Reading Timer ---
        self.read_force_timer = QtCore.QTimer()
        self.read_force_timer.timeout.connect(self.read_force_data)

    def hide_motor_controls(self):
        """Hide motor control related UI elements"""
        # Hide motor control buttons and labels
        self.ui.move_axis_left_end.setVisible(False)
        self.ui.move_axis_left_one.setVisible(False)
        self.ui.move_axis.setVisible(False)
        self.ui.move_axis_right_one.setVisible(False)
        self.ui.move_axis_right_end.setVisible(False)
        
        # Hide motor selection radio buttons
        self.ui.is_axis.setVisible(False)
        self.ui.is_roller.setVisible(False)
        
        # Hide motor parameters
        self.ui.speed_label.setVisible(False)
        self.ui.speed_of_motor.setVisible(False)
        self.ui.distance_label.setVisible(False)
        self.ui.distance_to_be_covered.setVisible(False)
        self.ui.select_motor_label.setVisible(False)

    def disable_distal_gauge(self):
        """Disable distal force gauge UI elements"""
        self.ui.connect_distal_force_gauge.setEnabled(False)
        self.ui.set_distal_zero.setEnabled(False)
        self.ui.record_distal_force_gauge.setEnabled(False)
        self.ui.record_distal_force_gauge.setChecked(False)
        
        # Gray out distal gauge section
        self.ui.distal_force_gauge_groupbox.setStyleSheet("QGroupBox { border: 1px solid gray; background-color: #f0f0f0; }")
        self.ui.distal_force_value.setText("Not Available")

    def read_force_data(self):
        """Read data from the single force gauge during manual test"""
        ti = time.time() - self.test_start_time
        
        # For manual operation, we'll record until user stops
        # or use the test_time if specified
        if self.test_time > 0 and ti >= self.test_time:
            self.stop_recording()
            return
            
        # Append current readings for plotting and saving
        current_force = round(self.prox.proximal_thread.present_reading, 2)
        self.plotter.temp_proximal_force.append(current_force)
        self.plotter.temp_time.append(round(ti, 2))
        
        # For manual operation, displacement might not be relevant
        # or could be entered manually. We'll keep it at 0 for now.
        self.plotter.temp_displacement.append(0)

    def stop_recording(self):
        """Stop the current recording and save data"""
        self.current_running_status = False
        self.read_force_timer.stop()
        
        # Save the recorded data
        if hasattr(self, 'before_start_checks') and self.before_start_checks.data_file:
            self.prox.saver_thread.file_name = self.before_start_checks.data_file
            self.prox.saver_thread.p_f_data = self.plotter.temp_proximal_force
            self.prox.saver_thread.t_data = self.plotter.temp_time
            self.prox.saver_thread.dis_data = self.plotter.temp_displacement
            self.prox.saver_thread.which_test = "proximal"
            self.prox.saver_thread.start()
        
        # Update plot with collected data
        self.plotter.add_proximal_data()
        
        # Reset recording state
        self.ui.start_test.setStyleSheet("background-color: rgb(170, 255, 127);")
        self.ui.start_test.setText("Start Recording")

    def update_gui(self):
        """Update the GUI elements regularly"""
        # Update displayed force values
        self.ui.proximal_force_value.setText(str(self.prox.proximal_thread.present_reading))
        
        # Update camera if connected
        self.prox.got_image()
        
        # If a test is running, update the plot
        if self.current_running_status:
            self.plotter.plot_now()

    def button_clicks(self):
        """Connect all UI button click signals"""
        self.ui.browse_directory.clicked.connect(self.browse_now)
        self.ui.start_test.clicked.connect(self.toggle_recording)
        self.ui.clear_all_button.clicked.connect(self.clear_data)

    def browse_now(self):
        """Open file dialog for selecting save directory"""
        self.my_dir = QFileDialog.getExistingDirectory(
            self,
            "Open a folder",
            expanduser("~"),
            QFileDialog.ShowDirsOnly)
        self.ui.save_directory.setText(self.my_dir)

    def toggle_recording(self):
        """Start or stop manual recording"""
        if not self.current_running_status:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        """Start manual data recording"""
        # Basic validation
        if not self.ui.save_directory.text() or not self.ui.test_name.text():
            QMessageBox.warning(self, "Missing Information", 
                              "Please specify both save directory and test name.")
            return

        # Create save directory if it doesn't exist
        save_path = os.path.join(self.ui.save_directory.text(), self.ui.test_name.text())
        try:
            os.makedirs(save_path, exist_ok=True)
        except Exception as e:
            QMessageBox.critical(self, "Directory Error", f"Cannot create directory: {str(e)}")
            return

        # Set up data file path
        self.data_file = os.path.join(save_path, "force_data.csv")
        
        # Reset plotter data
        self.plotter.temp_proximal_force = []
        self.plotter.temp_time = []
        self.plotter.temp_displacement = []
        self.plotter.what_plot = "proximal"

        # Zero the force gauge
        self.prox.proximal_zero_clicked()

        # Start recording
        self.current_running_status = True
        self.test_start_time = time.time()
        
        # Use test time if specified, otherwise manual stop
        if self.ui.distance_to_be_covered.text() and self.ui.speed_of_motor.text():
            try:
                distance = float(self.ui.distance_to_be_covered.text())
                speed = float(self.ui.speed_of_motor.text())
                self.test_time = abs(distance / speed) if speed != 0 else 0
            except ValueError:
                self.test_time = 0  # Manual stop only
        else:
            self.test_time = 0  # Manual stop

        # Start video recording if enabled
        if self.ui.record_video.isChecked():
            video_path = os.path.join(save_path, "video.avi")
            self.prox.images_from_camera.start_recording(self.test_time, video_path)
            self.prox.images_from_camera.should_record = True

        # Start force data reading
        self.read_force_timer.start(20)  # Read every 20ms
        
        # Update UI
        self.ui.start_test.setStyleSheet("background-color: rgb(255, 100, 100);")
        self.ui.start_test.setText("Stop Recording")

    def clear_data(self):
        """Clear all current data and reset plots"""
        self.plotter.clear_all_data()
        if hasattr(self.plotter, 'temp_proximal_force'):
            self.plotter.temp_proximal_force = []
            self.plotter.temp_time = []
            self.plotter.temp_displacement = []

    def closing_in(self):
        """Clean up when closing application"""
        if self.current_running_status:
            self.stop_recording()
        if self.prox.proximal_connected:
            self.prox.proximal_thread.stop()

def close_it(app, ui):
    """Handle application closing"""
    app.exec()
    try:
        ui.closing_in()
    except:
        pass

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    
    # Skip login for now, or implement simple login if needed
    ui = AppWindow()
    ui.show()
    sys.exit(close_it(app, ui))