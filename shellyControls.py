#This moduel implements Shelly devices
#This module can currently control only Shelly devices

import ShellyPy
import json
from datetime import datetime
from debugTools import *

class ShellyDevice:
    address = "NotSpecified"
    device = "NotSpecified"
    alive = True
    name = "No Name"
    type = "No Type"
    isOn = False
    heatingHoursRequired = 0
    minPrice = 0    #under which price always on
    maxPrice = 0    #over which price never on
    lastUpdated = 0
    lastConnectionSuccessful = False
    temperature = -999.99
    humidity = -999.99
    battery = 0.0
    created = 0

    def __init__(self, name, dtype, address, heatingHoursRequired, max, min):
        self.name = name.lower()
        self.type = dtype.lower()
        self.address = address.lower()
        self.isOn = False
        self.heatingHoursRequired = heatingHoursRequired
        self.minPrice = min
        self.maxPrice = max
        self.temperature = -999.99
        self.humidity = -999.99
        self.battery = 0.0
        self.created = datetime.now()
        self.lastUpdated = datetime.now()

        try:
            self.device = ShellyPy.Shelly(address)
            self.alive = True
            self.lastUpdated = datetime.now()
            self.lastConnectionSuccessful = True
            self.lastUpdated = datetime.now()
            printOnTerminal("A Shelly device " + name + " successfully contacted at the address " + address)
        except:
            printOnTerminal("A Shelly device " + name + " cannot be reached at the address " + address)
            self.lastConnectionSuccessful = False
            self.alive = False

        self.turnOn()


    def turnOn(self):
        #Make a new connection:
        #if not a switch, cannot be turned on
        if self.isSwitch() == False:
            return()
        # if already on, do not turn on again
        if self.isOn:
            return ()
        try:
            device = ShellyPy.Shelly(self.address)
            device.relay(0, turn=True)
            self.lastConnectionSuccessful = True
            self.lastUpdated = datetime.now()
            self.isOn = True
            printOnTerminal("A Shelly device " + self.name + " turned on at the address " + self.address)
        except:
            self.lastConnectionSuccessful = False
            printOnTerminal("A Shelly device " + self.name + "cannot be turned on at the address " + self.address)

    def turnOff(self):
        # Make a new connection:
        #if not a switch, cannot be turned on
        if self.isSwitch() == False:
            return()
        #if already off, do not turn off again
        if self.isOn == False:
            return()
        try:
            device = ShellyPy.Shelly(self.address)
            device.relay(0, turn=False)
            self.lastConnectionSuccessful = True
            self.lastUpdated = datetime.now()
            self.isOn = False
            printOnTerminal("A Shelly device " + self.name + " turned off at the address " + self.address)
        except:
            self.lastConnectionSuccessful = False
            printOnTerminal("A Shelly device " + self.name + " cannot be turned off at the address " + self.address)

    #get temperature and update humidity and battery status
    def getTemperature(self):
        # Make a new connection:
        #if not a meter, cannot return temp
        if self.isMeter() != True:
            return()
        try:
            device = ShellyPy.Shelly(self.address)
            m_obj = device.status()
            m_str = json.dumps(m_obj)
            data = json.loads(m_str)
            self.temperature = float(data['tmp']['value'])
            self.humidity = float(data['hum']['value'])
            self.battery = float(data['bat']['value'])
            printOnTerminal("A Shelly device " + self.name + " temperature at the address " + self.address + " is " + str(self.temperature) + " and  humidity is "+ str(self.humidity) + "%")
            self.lastUpdated = datetime.now()
            self.lastConnectionSuccessful=True
            return self.temperature
        except:
            #print("A Shelly device ", self.name, "cannot return temperature at the address ", self.address)
            self.lastConnectionSuccessful = False
            return self.temperature

    def pingDevice(self):
        try:
            device = ShellyPy.Shelly(self.address)
            self.lastConnectionSuccessful = True
            return True
        except:
            self.lastConnectionSuccessful = False
            return False


    def wasLastConnectionSuccessful(self):
        return self.lastConnectionSuccessful


    def wasLastUpdated(self):
        return self.lastUpdated


    def createSelfReport(self):
        report = self.name + ": in address " + str(self.address) + "\n   -last connection was " + str(self.lastConnectionSuccessful) + "\n   -currently available " + str(self.pingDevice())
        if self.isMeter():
            report = report + "\n   -temperature reading " + str(self.getTemperature()) + "\n   -humidity reading " + str(self.humidity) + "\n   -battery precentage reading " + str(self.battery)+"%"
        if self.isSwitch():
            report = report + "\n   -is turned on " + str(self.isOn)

        lastDate = self.wasLastUpdated()
        lastDateString = lastDate.strftime("%H:%M:%S")

        report = report + "\n   -this data was last updated " + lastDateString + "\n"
        #lastDateString = lastDate.strftime("%H:%M:%S")
        return report


    def testMe(self):
        printOnTerminal(str(self.device.status()))


    def isSwitch(self):
        if self.type == "switch":
            return True
        else:
            return False


    def isMeter(self):
        if self.type == "meter":
            return True
        else:
            return False


class ShellyDevicePair:
    meterName = "Not Defined"
    switchName = "Not defined"
    lowTemp=0
    highTemp=0

    def __init__(self, meterName, switchName, lowTemp, highTemp):
        self.meterName = meterName.lower()
        self.switchName = switchName.lower()
        self.lowTemp = lowTemp
        self.highTemp = highTemp

    def createSelfReport(self):
        report = "Meter " + self.meterName + " controls switch " + self.switchName + " turning it on between " + str(self.lowTemp) + " and " + str(self.highTemp) + " centigrades.\n"
        return report









