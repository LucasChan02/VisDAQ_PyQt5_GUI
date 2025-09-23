import cv2
from PyQt6 import QtCore
import numpy as np
import multiprocessing
import time

class image_process(multiprocessing.Process):
	def __init__(self,q,a):
		multiprocessing.Process.__init__(self)
		# super(image_process).__init__(self)
		self.q=q
		self.read = a
		print("Initiated")

	def run(self):  
		print("came to run")  
		self.cap = cv2.VideoCapture(0)
		self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,720)
		self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT,720)
		self.read.value = 1
		fourcc = cv2.VideoWriter_fourcc(*'XVID')
		out = cv2.VideoWriter('output.avi',fourcc, 30.0, (720,720))
		while self.read.value:
			ret,frame = self.cap.read()
			print(ret)
			if ret:
				frame=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
				print(frame.shape)
				# time.sleep(0.1)
				# print('Signal emitted')
				frame = cv2.flip(frame,1)
				out.write(frame)
				frame = cv2.resize(frame,(480,480))
				self.q.put(frame)
				# image_signal.emit(frame)
		self.cap.release()
		out.release()
		
	def stop(self):
		self.read.value = 0
		
class image_taker(QtCore.QThread):
	image_signal = QtCore.pyqtSignal(np.ndarray)
	camera_connection_error = QtCore.pyqtSignal()

	def __init__(self, proximal, distal):
		super(image_taker, self).__init__()
		self.is_run = True
		self.record_time = 0
		self.should_record = False
		self.video_file_name = None
		self.width = 720
		self.height = 720
		self.aa = np.zeros([60,self.width,3])
		self.font = cv2.FONT_HERSHEY_SIMPLEX
		self.adder = cv2.putText(self.aa ,'Distal force    :      N',(10,20), self.font, 0.8,(255,255,255),2,cv2.LINE_AA)
		self.adder = cv2.putText(self.adder,'Proximal force :      N',(10,45), self.font, 0.8,(255,255,255),2,cv2.LINE_AA)
		self.adder = cv2.putText(self.adder,'Displacement :      mm',(380,45), self.font, 0.8,(255,255,255),2,cv2.LINE_AA) 
		self.proximal = proximal
		self.distal = distal
		self.final_image = None
		self.displacement = 0
		self.p_value = 0.7
		self.d_value = 0

	def connect_cam(self):
		try:
			self.cap = cv2.VideoCapture(0)
			self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,720)
			self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT,720)
			self.is_run = True
			print("Found")
		except:
			print("Could not connect camera")
			self.camera_connection_error.emit()
			self.is_run = False

	def run(self):
		while self.is_run:
			ret,frame = self.cap.read()
			if ret:
				ima = self.changes_in_image(frame)
				self.final_image = cv2.resize(ima,(480,480))
			if self.should_record:
				fourcc = cv2.VideoWriter_fourcc(*'XVID')
				out = cv2.VideoWriter(self.video_file_name,fourcc, 15.0, (self.width,self.height))
				record_strating_time = time.time()
				print("Staring video recording")
				i = 0
				while self.should_record:
					ret,frame = self.cap.read()
					if ret:
						print(i)
						im = self.changes_in_image(frame)
						self.final_image = cv2.resize(im,(480,480))
						out.write(im)
						i+=1
					if (time.time()-record_strating_time)>=self.record_time:
						self.should_record = False
						print("Video recording stopped")
						out.release()
		pass

	def changes_in_image(self, image, ):
		image = cv2.flip(image,1)
		image = cv2.cvtColor(image,cv2.COLOR_BGR2RGB)
		aa = np.zeros([60,self.width,3])
		adder = cv2.putText(aa ,'Distal force    :        N',(10,20), self.font, 0.8,(255,255,255),2,cv2.LINE_AA)
		adder = cv2.putText(adder,'Proximal force :        N',(10,45), self.font, 0.8,(255,255,255),2,cv2.LINE_AA)
		adder = cv2.putText(adder,'Displacement :       mm',(380,45), self.font, 0.8,(255,255,255),2,cv2.LINE_AA) 
		adde = cv2.putText(adder,str(self.proximal.present_reading),(230,22), self.font, 0.8,(255,255,255),2,cv2.LINE_AA)
		adde = cv2.putText(adde,str(self.distal.reading),(230,47), self.font, 0.8,(255,255,255),2,cv2.LINE_AA)
		adde = cv2.putText(adde,str(self.displacement),(570,47), self.font, 0.8,(255,255,255),2,cv2.LINE_AA)
		image[-60:,:,:] = adde
		return image

	def changes_in_image_while_recording(self, image, ):
		image = cv2.flip(image,1)
		image = cv2.cvtColor(image,cv2.COLOR_BGR2RGB)
		aa = np.zeros([60,self.width,3])
		adder = cv2.putText(aa ,'Distal force    :        N',(10,20), self.font, 0.8,(255,255,255),2,cv2.LINE_AA)
		adder = cv2.putText(adder,'Proximal force :        N',(10,45), self.font, 0.8,(255,255,255),2,cv2.LINE_AA)
		adder = cv2.putText(adder,'Displacement :       mm',(380,45), self.font, 0.8,(255,255,255),2,cv2.LINE_AA) 
		adde = cv2.putText(adder,str(self.proximal.present_reading),(230,22), self.font, 0.8,(255,255,255),2,cv2.LINE_AA)
		adde = cv2.putText(adde,str(self.distal.reading),(230,47), self.font, 0.8,(255,255,255),2,cv2.LINE_AA)
		adde = cv2.putText(adde,str(self.displacement),(570,47), self.font, 0.8,(255,255,255),2,cv2.LINE_AA)
		image[-60:,:,:] = adde
		return image

	def flip(self,image):
		image = cv2.flip(image,1)
		return image

	def stop(self):
		print('Closing')
		self.is_run = False
		self.cap.release()
		
	def start_recording(self, time_for_record, video_file_name):
		self.record_time = time_for_record
		self.video_file_name = video_file_name
		self.should_record = True