# Copyright Ari Jaaksi
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# -------------------------------------------------------------------------
# This module implements Shelly devices
# This module can currently control only Shelly devices
# -------------------------------------------------------------------------

import ShellyPy
import json
from datetime import datetime
from debugTools import *


# -------------------------------------------------------------------------
# The parent class for any device controlled by this system
# to be inherited later
# -------------------------------------------------------------------------
class Device():
    name = "Not Specified"
    def __init__(self, name):
        self.name = name.lower()

    def setName(self, name):
        self.name = name.lower()

    def getName(self):
        return self.name


# -------------------------------------------------------------------------
# Any type of a shelly device
# not to be used directly but to be inherited to all kinds of shelly devices
# such as switch and meter
# -------------------------------------------------------------------------
class ShellyDevice(Device):
    address = "NotSpecified"
    alive = True
    isOn = False
    lastUpdated = 0
    lastConnectionSuccessful = False
    created = 0

    def __init__(self, name, address):
        super().__init__(name)
        self.address = address.lower()
        self.isOn = False
        self.created = datetime.now()
        self.lastUpdated = datetime.now()

        try:
            self.device = ShellyPy.Shelly(self.address)
            self.alive = True
            self.lastUpdated = datetime.now()
            self.lastConnectionSuccessful = True
            self.lastUpdated = datetime.now()
            printOnTerminal("A Shelly device " + name + " successfully contacted at the address " + address)
        except:
            printOnTerminal("A Shelly device " + name + " cannot be reached at the address " + address)
            self.lastConnectionSuccessful = False
            self.alive = False


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

    def testMe(self):
        printOnTerminal(str(self.device.status()))



# -------------------------------------------------------------------------
# A Shelly meter; to be used directly in code
#
# -------------------------------------------------------------------------
class ShellyMeter(ShellyDevice):

    temperature = -999.99
    humidity = -999.99
    battery = 0.0

    def __init__(self, name, address):
        super().__init__(name, address)
        self.temperature = -999.99
        self.humidity = -999.99
        self.battery = 0.0

        try:
            self.device = ShellyPy.Shelly(address)
            self.alive = True
            self.lastUpdated = datetime.now()
            self.lastConnectionSuccessful = True
            self.lastUpdated = datetime.now()
            printOnTerminal("A Shelly meter " + name + " successfully contacted at the address " + address)
        except:
            printOnTerminal("A Shelly meter " + name + " cannot be reached at the address " + address)
            self.lastConnectionSuccessful = False
            self.alive = False


    # get temperature and update humidity and battery status
    # this is done by polling; we have NOT implemented callbacks yet!
    def getTemperature(self):
        try:
            device = ShellyPy.Shelly(self.address)
            m_obj = device.status()
            m_str = json.dumps(m_obj)
            data = json.loads(m_str)
            self.temperature = float(data['tmp']['value'])
            self.humidity = float(data['hum']['value'])
            self.battery = float(data['bat']['value'])
            printOnTerminal("A Shelly meter " + self.name + " temperature at the address " + self.address + " is " + str(self.temperature) + " and  humidity is "+ str(self.humidity) + "%")
            self.lastUpdated = datetime.now()
            self.lastConnectionSuccessful=True
            return self.temperature
        except:
            self.lastConnectionSuccessful = False
            return self.temperature


    def createSelfReport(self):
        report = self.name + ": in address " + str(self.address) + "\n   -last connection was " + str(self.lastConnectionSuccessful) + "\n   -currently available " + str(self.pingDevice())
        report = report + "\n   -temperature reading " + str(self.getTemperature()) + "\n   -humidity reading " + str(self.humidity) + "\n   -battery precentage reading " + str(self.battery)+"%"


        lastDate = self.wasLastUpdated()
        lastDateString = lastDate.strftime("%H:%M:%S")

        report = report + "\n   -this data was last updated " + lastDateString + "\n"
        #lastDateString = lastDate.strftime("%H:%M:%S")
        return report


# -------------------------------------------------------------------------
# A Shelly switch; to be used directly in code
#
# -------------------------------------------------------------------------
class ShellySwitch(ShellyDevice):
    isOn = False
    heatingHoursRequired = 0
    minPrice = 0    #under which price always on
    maxPrice = 0    #over which price never on

    def __init__(self, name, address, heatingHoursRequired, max, min):
        super().__init__(name, address)
        self.isOn = False
        self.heatingHoursRequired = heatingHoursRequired
        self.minPrice = min
        self.maxPrice = max
        self.temperature = -999.99
        self.humidity = -999.99

        try:
            self.device = ShellyPy.Shelly(self.address)
            self.alive = True
            self.lastConnectionSuccessful = True
            self.lastUpdated = datetime.now()
            printOnTerminal("A Shelly switch " + name + " successfully contacted at the address " + address)
        except:
            printOnTerminal("A Shelly switch " + name + " cannot be reached at the address " + address)
            self.lastConnectionSuccessful = False
            self.alive = False

        self.turnOn()


    def turnOn(self):
        # if already on, do not turn on again
        if self.isOn:
            return ()
        try:
            device = ShellyPy.Shelly(self.address)
            device.relay(0, turn=True)
            self.lastConnectionSuccessful = True
            self.lastUpdated = datetime.now()
            self.isOn = True
            printOnTerminal("A Shelly switch " + self.name + " turned on at the address " + self.address)
        except:
            self.lastConnectionSuccessful = False
            printOnTerminal("A Shelly switch " + self.name + "cannot be turned on at the address " + self.address)

    def turnOff(self):
        #if already off, do not turn off again
        if self.isOn == False:
            return()
        try:
            device = ShellyPy.Shelly(self.address)
            device.relay(0, turn=False)
            self.lastConnectionSuccessful = True
            self.lastUpdated = datetime.now()
            self.isOn = False
            printOnTerminal("A Shelly switch " + self.name + " turned off at the address " + self.address)
        except:
            self.lastConnectionSuccessful = False
            printOnTerminal("A Shelly switch " + self.name + " cannot be turned off at the address " + self.address)

    def createSelfReport(self):
        report = self.name + ": in address " + str(self.address) + "\n   -last connection was " + str(self.lastConnectionSuccessful) + "\n   -currently available " + str(self.pingDevice())
        report = report + "\n   -is turned on " + str(self.isOn)

        lastDate = self.wasLastUpdated()
        lastDateString = lastDate.strftime("%H:%M:%S")

        report = report + "\n   -this data was last updated " + lastDateString + "\n"
        #lastDateString = lastDate.strftime("%H:%M:%S")
        return report


# -------------------------------------------------------------------------
# We create meter- switch pairs for Shelly devices where
# a meter can control the swicg so, that
# it is turned ON between temperatures lowTemp - highTemp
# -------------------------------------------------------------------------
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









