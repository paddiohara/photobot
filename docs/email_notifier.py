# An error logging object that sends updates via email.
# Credit to https://medium.freecodecamp.org/send-emails-using-code-4fcea9df63f for related tutorial
# Created by Gregory O'Hagan

import smtplib
from string import Template
from datetime import datetime
from time import sleep
import os

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import threading

class PhotobotEmailNotifier:
	address = ''    # photobot's email
	password = ''   # photobot's email password
	host = ''       # smpt host of photobot's email. These can be found online for each email provider
	port = ''       # port number of the smpt host above. Also available online
	targetAddresses = []    # email addresses of receivers
	location = ''       # the identification of the camera. Used in report emails
	
	hourTime = 0                    # the time as of the last update() call
	lastErrorMessageTime = 0    # the time of the last error message
	fileErrorThresh = 20        # number of file errors to throw an error
	cameraErrorThresh = 20      # number of camera errors to send an error email
	errorIntervalHours = 12     # minimum interval between error emails
	errorsSent = 0            # number of error emails sent.
	
	cycles = 0          # number of cycles (number of times update() is called)
	cameraErrors = 0    # number of camera errors reported
	fileErrors = 0      # number of file errors reported
	
	logName = "emailLog.txt"
	writing = False             # Writing is called on a thread - don't start writing until the previous is finished
	
	def __init__(self, targetAddresses, location = 'in-lab setup', address = 'nemesphotobot@gmail.com', password = 'CORALlab',
	             host = 'smtp.gmail.com', port = 587):
		self.address = address
		self.password = password
		self.host = host
		self.port = port
		if (type(targetAddresses) == type([])):
			self.targetAddresses = targetAddresses
		else:
			self.targetAddresses = [targetAddresses]
		self.location = location
		self.hourTime = self.get_hour_time()
		
		# Check for an existing log file
		try:
			f = open(self.logName, 'r')
			logTime = int(f.readline())
			if abs(self.hourTime - logTime) <= 1:
				self.lastErrorMessageTime = int(f.readline())
				self.errorsSent = int(f.readline())
				self.cycles = int(f.readline())
				self.cameraErrors = int(f.readline())
				self.fileErrors = int(f.readline())
		except:
			pass
		
	# Sets the required number of errors to send an email, as well as the minimum time between reports.
	# Note that for repeat errors, the formula for minimum errors is: (minimum interval) * (1 + numErrors)
	# Ex: If the first file error is at 20 file errors, the second will be at 40, the third will be at 60...
	# Note that even if an error doesn't send an email due to the minimum duration, it will still count in this formula
	def set_error_thresholds(self, fileErrorThresh = 20, cameraErrorThresh = 20, errorIntervalHours = 12):
		self.fileErrorThresh = fileErrorThresh
		self.cameraErrorThresh = cameraErrorThresh
		self.errorIntervalHours = errorIntervalHours
	
	
	# Writes down critical information to a log file. Allows the program to keep going over a hard reset
	def write_to_log(self):
		self.writing = True
		try:
			file = open(self.logName, 'w')
			file.write(str(self.hourTime) + "\n")
			file.write(str(self.lastErrorMessageTime) + "\n")
			file.write(str(self.errorsSent) + "\n")
			file.write(str(self.cycles) + "\n")
			file.write(str(self.cameraErrors) + "\n")
			file.write(str(self.fileErrors) + "\n")
			file.close()
		# If we can't write, don't worry about it. We're not going to crash the camera over a file IO mistake
		except:
			pass
		self.writing = False
	
	
	# Should be run every complete cycle. Increments the cycle counter, and sends a report if needed.
	# The error reporting function is started as a new thread to make sure the email sending doesn't block any other
	# functions, and any errors that occur there will not affect any other code.
	# The timing logic is controlled in the send_error_message function, and set in the set_error_thresholds function.
	def update(self):
		self.hourTime = self.get_hour_time()
		self.cycles += 1
		if self.cameraErrors >= self.cameraErrorThresh * (1 + self.errorsSent)\
					or self.fileErrors >= self.fileErrorThresh * (1 + self.errorsSent):
			threading.Thread(target=self.send_error_message).start()
		if not self.writing:
			threading.Thread(target=self.write_to_log).start()
	
	# Reports a camera error
	# Note that no error emails will be sent until the next update() call
	def report_camera_error(self):
		self.cameraErrors += 1
	
	# Reports a file error
	# Note that no error emails will be sent until the next update() call
	def report_file_error(self):
		self.fileErrors += 1
		
	# Creates and sends an error message
	def send_error_message(self):
		self.errorsSent += 1
		# Note that this is approximate over month roll-overs
		if (self.hourTime - self.lastErrorMessageTime < self.errorIntervalHours):
				return
		self.lastErrorMessageTime = self.hourTime
		# create and send the email to each target
		for target in self.targetAddresses:
			try:
				t = datetime.now()
				reportTemplate = Template("""
				Error report on ${YEAR}-${MONTH}-${DAY} at ${HOUR}:${MINUTE} from ${LOCATION}:
		
				Update cycles: ${CYCLECOUNT}
				Camera errors: ${CAMERAERRORS}
				File errors: ${FILEERRORS}
				""")
				
				msg = MIMEMultipart()
				
				message = reportTemplate.substitute(YEAR=t.year, MONTH=t.month, DAY=t.day,\
				                                    HOUR=t.hour, MINUTE=t.minute,\
				                                    LOCATION=self.location, CYCLECOUNT=self.cycles,\
				                                    CAMERAERRORS=self.cameraErrors, FILEERRORS = self.fileErrors)
				
				msg['From']=self.address
				msg['To']=target
				msg['Subject']="Photobot Error Report"
				
				msg.attach(MIMEText(message, 'plain'))
				
				# Log in to SMTP
				s = smtplib.SMTP(self.host, self.port)
				s.starttls()
				s.login(self.address, self.password)
				s.sendmail(self.address, target, msg.as_string())
				del msg
				s.quit()
			# There may be unexpected errors (such as if the internet is out)
			# If there are any, mark lastErrorMessageTime to false to override the minimum error interval
			except:
				print("error?")
				self.lastErrorMessageTime = 0
	
	
	# Returns the current time in hours as an int
	# Time is approximate over month changes, and errs on the side of skipping time over a month change
	def get_hour_time(self):
		t = datetime.now()
		return t.year * 8928 + t.month * 744 + t.day * 24 + t.hour


#_______________________Everything below here is testing________________________________


# (This test doesn't terminate - please don't spam me with emails permanently...)
def log_test():
	#Lets us kill the ebot by having it go out of scope
	i = 0
	while True:
		ebot = PhotobotEmailNotifier("gregsohagan@gmail.com", "coral lab")
		ebot.set_error_thresholds(4, 4, 1)
		ebot.update()
		ebot.report_camera_error()
		ebot.report_file_error()
		ebot.update()
		i += 1
		print("updated " + str(i) + " times")
		sleep(10)


def test():
	targetEmails = "gregsohagan@gmail.com" #["gregoryrohagan@gmail.com", "gregsohagan@gmail.com"]
	ebot = PhotobotEmailNotifier(targetEmails, "coral lab")
	ebot.set_error_thresholds(4, 4, 0)
	for i in range(50):
		ebot.update()
	ebot.report_camera_error()
	ebot.report_file_error()
	ebot.update()
	ebot.report_file_error()
	ebot.update()
	ebot.report_file_error()
	ebot.update()
	ebot.report_file_error()
	ebot.update()
	sleep(1)
	ebot.report_file_error()
	ebot.update()
	ebot.report_file_error()
	ebot.update()
	sleep(1)
	print("The following email addresses should have gotten two emails. Did it work?")
	for address in ebot.targetAddresses:
		print(address)


if __name__ == "__main__":
	log_test()