#!/usr/bin/env python
# -*- encoding: UTF-8 -*-

__author__ = 'Fabrimat'
__license__ = 'Apache License 2.0'
__version__ = '0.8.5'

NAO_IP = "127.0.0.1"
NAO_PORT = 9559

tetheringSSID = "Nao-WiFi"
tetheringPassword = "nao12345"
wifiCountry = "IT"

import sys
import time

from optparse import OptionParser

try:
	from naoqi import ALProxy
	from naoqi import ALBroker
	from naoqi import ALModule
	import qi
except:
	print("NAOqi Python SDK not found")
	sys.exit(1)

session = qi.Session()
CorMenu = None
pip = None
pport = None
memory = None

menuVal = 0

menu = ["init","disconnect","activateWiFi","deactivateWiFi","autonomousLifeToggle","changeOffsetFromFloor","changeVolume","status","close"]

class CorMenuModule(ALModule):
	def __init__(self, name):
		ALModule.__init__(self, name)
		self.changeOffset = False
		
		try:
			self.autoLife = ALProxy("ALAutonomousLife")
		except:
			self.logger.warn("ALAutonomousLife is not available")
			self.autoLife = None
		
		try:
			self.tts = ALProxy("ALTextToSpeech")
		except:
			self.logger.warn("ALTextToSpeech is not available")
			self.tts = None
			
		try:
			self.connectionManager = ALProxy("ALConnectionManager", NAO_IP, NAO_PORT)
		except:
			self.logger.warn("ALConnectionManager is not available, hotspot cannot be created")
			self.connectionManager = None
		
		global memory
		memory = ALProxy("ALMemory")
		memory.subscribeToEvent("ALChestButton/TripleClickOccurred",
			self.getName(),
			"onTripleChest")
	
	
	def disconnect(self):
		services = session.services()
		removed = False
		for s in services :
			strName = s["name"];
			try:
				serviceID = s["serviceId"];
			except:
				serviceID = s[1]
			if strName in ["ALChoregraphe", "ALChoregrapheRecorder"] :
				session.unregisterService( serviceID )
				if not removed:
					self.tts.say("Choregraphe connection removed successfully.")
				removed = True
		if not removed:
			self.tts.say("Choregraphe connection not found.")
		
	def onTripleChest(self, *_args):
		memory.unsubscribeToEvent("ALChestButton/TripleClickOccurred",
			self.getName())
		
		self.language = self.tts.getLanguage()
		self.tts.setLanguage("English")
		
		memory.subscribeToEvent("FrontTactilTouched",
			self.getName(),
			"onFrontHead")
		memory.subscribeToEvent("MiddleTactilTouched",
			self.getName(),
			"onMiddleHead")
		memory.subscribeToEvent("RearTactilTouched",
			self.getName(),
			"onRearHead")
	
	def onFrontOffset(self, *_args):
		memory.unsubscribeToEvent("FrontTactilTouched",
			self.getName())
		
		self.offset += 1
		
		memory.subscribeToEvent("FrontTactilTouched",
			self.getName(),
			"onFrontOffset")
		
	def onMiddleOffset(self, *_args):
		memory.unsubscribeToEvent("MiddleTactilTouched",
			self.getName())
		
		self.autoLife.setRobotOffsetFromFloor(self.offset)
		self.changeOffset = False
		self.tts.say("Offset set!")
		
		memory.subscribeToEvent("MiddleTactilTouched",
			self.getName(),
			"onMiddleOffset")
	
	def onRearOffset(self, *_args):
		memory.unsubscribeToEvent("RearTactilTouched",
			self.getName())
		
		if self.offset > 0:
			self.offset -= 1
		else:
			self.tts.say("Cannot do it")
			
		memory.subscribeToEvent("RearTactilTouched",
			self.getName(),
			"onRearOffset")
	
	def onFrontHead(self, *_args):
		memory.unsubscribeToEvent("MiddleTactilTouched",
			self.getName())
		memory.unsubscribeToEvent("FrontTactilTouched",
			self.getName())
		memory.unsubscribeToEvent("RearTactilTouched",
			self.getName())
			
		global menuVal
		global menu
		if menuVal >= 0 and menuVal < len(menu)-1:
			menuVal += 1
		elif menuVal == len(menu)-1:
			menuVal = 1
		else:
			self.tts.say("Unknown error.")
			return
		
		self.tts.say(menu[menuVal] + " selected!")
		memory.subscribeToEvent("FrontTactilTouched",
			self.getName(),
			"onFrontHead")
		memory.subscribeToEvent("MiddleTactilTouched",
			self.getName(),
			"onMiddleHead")
		memory.subscribeToEvent("RearTactilTouched",
			self.getName(),
			"onRearHead")
			
	def onMiddleHead(self, *_args):
		memory.unsubscribeToEvent("MiddleTactilTouched",
			self.getName())
		memory.unsubscribeToEvent("FrontTactilTouched",
			self.getName())
		memory.unsubscribeToEvent("RearTactilTouched",
			self.getName())
		
		flag_Return = False
		
		global menuVal
		global menu
		if menu[menuVal] == "init":
			self.tts.say("Nothing selected! Quitting.")
		elif menu[menuVal] == "disconnect":
			self.disconnect()
		elif menu[menuVal] == "activateWiFi":
			self.activateWiFi()
		elif menu[menuVal] == "deactivateWiFi":
			self.deactivateWiFi()
		elif menu[menuVal] == "status":
			self.status()
		elif menu[menuVal] == "autonomousLifeToggle":
			self.autonomousLifeToggle()
		elif menu[menuVal] == "changeOffsetFromFloor":
			self.changeOffset = True
			flag_Return = True
			self.offset = self.autoLife.getRobotOffsetFromFloor()
		else:
			self.tts.say("Unknown error.")
		
		if not flag_Return:
			self.tts.setLanguage(self.language)
			menuVal = 0
			
			memory.subscribeToEvent("ALChestButton/TripleClickOccurred",
				self.getName(),
				"onTripleChest")
		else:
			memory.subscribeToEvent("FrontTactilTouched",
				self.getName(),
				"onFrontOffset")
			memory.subscribeToEvent("MiddleTactilTouched",
				self.getName(),
				"onMiddleOffset")
			memory.subscribeToEvent("RearTactilTouched",
				self.getName(),
				"onRearOffset")
		
	def onRearHead(self, *_args):
		memory.unsubscribeToEvent("MiddleTactilTouched",
			self.getName())
		memory.unsubscribeToEvent("FrontTactilTouched",
			self.getName())
		memory.unsubscribeToEvent("RearTactilTouched",
			self.getName())
		
		global menuVal
		global menu
		if menuVal <= 1:
			menuVal = len(menu)-1
		else :
			menuVal = menuVal - 1
		
		self.tts.say(menu[menuVal] + " selected!")
		memory.subscribeToEvent("FrontTactilTouched",
			self.getName(),
			"onFrontHead")
		memory.subscribeToEvent("MiddleTactilTouched",
			self.getName(),
			"onMiddleHead")
		memory.subscribeToEvent("RearTactilTouched",
			self.getName(),
			"onRearHead")
			
	def activateWiFi(self):
		if self.connectionManager is None:
			self.tts.say("Error, ALConnectionManager is no longer avaiable")
			return
		if not self.connectionManager.getTetheringEnable("wifi"):
			self.connectionManager.setCountry(wifiCountry)
			self.connectionManager.enableTethering("wifi", tetheringSSID, tetheringPassword)
			self.tts.say("Wifi Tethering activated.")
		else:
			self.tts.say("Wifi Tethering is already active.")
			
	def deactivateWiFi(self):
		if self.connectionManager is None:
			self.tts.say("Error, ALConnectionManager is no longer avaiable")
			return
		if self.connectionManager.getTetheringEnable("wifi"):
			self.connectionManager.disableTethering("wifi")
			self.tts.say("Wifi Tethering deactivated.")
		else:
			self.tts.say("Wifi Tethering is already inactive.")
		
	def status(self):
	
		
		global memory
		realNotVirtual = False
		try:
			memory.getData( "DCM/Time" )
			if( memory.getData( "DCM/Simulation" ) != 1 ):
				realNotVirtual = True
			else:
				import os
				realNotVirtual = os.path.exists("/home/nao")
		except:
			pass 

		if realNotVirtual:
			import socket
			robotName = socket.gethostname()
			naoName = robotName
		else:
			naoName = "virtual-robot"
		
		self.tts.say("My name is %s" %(naoName))
		
		batteryCharge = memory.getData("Device/SubDeviceList/Battery/Charge/Sensor/Value")
		batteryCurrent = memory.getData("Device/SubDeviceList/Battery/Current/Sensor/Value")
		batteryTemp = memory.getData("Device/SubDeviceList/Battery/Temperature/Sensor/Value")
		self.tts.say("My battery is at %d percent with %d Ampere and the temperature is at %d percent" %(batteryCharge*100, batteryCurrent, batteryTemp))
		
		autoLifeStatus = self.autoLife.getState()
		self.tts.say("My autonomous life status is: %s" %(autoLifeStatus))
		
		if(self.connectionManager.getTetheringEnable("wifi")):
			self.tts.say("WiFi is active")
			
			self.tts.say("WiFi SSID is %s" &(ssid))
			self.tts.say("WiFi password is %s" &(password))
		else:
			self.tts.say("WiFi is not active")
		pass
		
	def autonomousLifeToggle(self):
		lifeState = self.autoLife.getState()
		if lifeState == "solitary" or lifeState == "interactive":
			self.autoLife.setState("disabled")
		elif lifeState == "safeguard":
			pass # Stand Up from Choregraphe
		else:
			self.autoLife.setState("solitary")
		
	def unload(self):
		self.tts.setLanguage(self.language)
def main():
	parser = OptionParser()
	parser.add_option("--pip",
		help="Robot address",
		dest="pip")
	parser.add_option("--pport",
		help="NAOqi port",
		dest="pport",
		type="int")
	parser.set_defaults(
		pip=NAO_IP,
		pport=NAO_PORT)

	(opts, args_) = parser.parse_args()
	pip   = opts.pip
	pport = opts.pport
	
	session.connect("tcp://" + str(pip) + ":" + str(pport))
	myBroker = ALBroker("myBroker",
	   "0.0.0.0",
	   0, 
	   pip,
	   pport)
	
	global CorMenu
	CorMenu = CorMenuModule("CorMenu")
	
	try:
		while True:
			time.sleep(1)
	except KeyboardInterrupt:
		print "Interrupted by user, shutting down"
		CorMenu.unload()
		myBroker.shutdown()
		sys.exit(0)

if __name__ == "__main__":
	main()
