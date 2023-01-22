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
# This module contains the main program
#

import time
import sys
from dateTimeConversions import MyDateTime
from spotData import SpotData
from devices import ShellySwitch, ShellyMeter, DevicePair
from mailManagement import haMail
import getpass
import threading
from debugTools import *

CONFIGFILE = "HA_Config.txt"
stopThreads = False


# Only to show daily proces on screen
# A better way is to command system prices through email
def printDeviceDayPlan(msd, d):
    printOnTerminal(d.name+ ":")
    str = "Hour:   1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 16 17 18 19 20 21 22 23 24"
    str2 = "Status: "
    for x in range(24):
        rank = msd.spotItemArray[x].rank
        hour = msd.spotItemArray[x].hour
        price = msd.spotItemArray[x].price
        d.turnOnOff(rank, hour, price)
        if d.isOn == True:
            str2 = str2 + "+  "
        else:
            str2 = str2 + "-  "

    printOnTerminal(str)
    printOnTerminal(str2)


# Reading meters in a separate thread
# NOTE: we read meters, such as temp meters by polling in this separate thread
# e.g Shelly meters are on ONLY when temperature has recently changed
# if no change recently, they are in sleep and cannot be contacted
def readMeters(name):
    while True:
        time.sleep(1)
        for x in myDevices:
            if x.isMeter():
                x.getTemperature()
        global stopThreads
        if stopThreads:
            break


# Reading input from the terminal
# --always ready to accept input
def readTerminal(name):
    while True:
        time.sleep(1)
        i = input("Terminal on: ")
        print(i)
        global stopThreads
        if stopThreads:
            break


# Re-read price data, add approppriate tax
def refreshSpotData(mySpotData):
    printOnTerminal("Refreshing Spot -data")
    if mySpotData.populateSpotData():
        mySpotData.addTax()
        mySpotData.printSpotDataArray()
        return True
    else:
        printOnTerminal("Failed in refreshing Spot -data")
        return False


def readAndManageConfigurationFile(filename):
    global myDevicePairs
    global myDevices
    global email
    global mySpotData
    global updateInterval

    myDevices.clear()
    myDevicePairs.clear()

    try:
        f = open(filename, "r")
    except:
        printOnTerminal("Cannot open configuration file at "+ filename)
        printOnTerminal("EXIT")
        sys.exit("DONE")

    acList = []
    for x in f:
        if x[0]!="#" and x[0]!='\n':
            res = x.split()
            if res[0]=="Device":
                deviceName = res[1]
                deviceType = res[2]
                ipAddress = res[3]
                printOnTerminal("Creating device: " + deviceName)
                if deviceType == "switch":
                    myDevices.append(ShellySwitch(deviceName, ipAddress))
                elif deviceType == "meter":
                    myDevices.append(ShellyMeter(deviceName, ipAddress))
            elif res[0]=="Email":
                emailAccount = res[1]
                emailPassword = passwrd  #note: not from file but a user prompt
                emailIMAP = res[2]
                emailIMAPPort = int(res[3])
                emailSMTP = res[4]
                emailSMTPPort = int(res[5])
                emailRecipient = res[6]
                printOnTerminal("Creating account list")
                i=0
                #the main account is always firt marked as emailRecipient, and then the main mail account
                acList.append(emailRecipient)
                acList.append(emailAccount)
                #then add the rest, if any
                for ac in res:
                    if i>6:
                        printOnTerminal("Creating email connections: " + emailAccount)
                        printOnTerminal(ac)
                        acList.append(ac)
                    i=i+1
                email = haMail(emailAccount, emailPassword, emailIMAP, emailIMAPPort, emailSMTP, emailSMTPPort,emailRecipient, acList)
                emailPasswordOK = email.verifyEmail()
                email.emptyInbox()
            elif res[0]=="Common":
                updateInterval = int(res[1])
                daytimeTax = float(res[2])
                nightimeTax = float(res[3])
                printOnTerminal("Creating Spot Data with day tax at " + str(daytimeTax) + " and night tax at " + str(nightimeTax))
                mySpotData = SpotData(daytimeTax,nightimeTax)
                mySpotData.populateSpotData()
                mySpotData.addTax()
                mySpotData.printSpotDataArray()
            elif res[0]=="Pair":
                meterName = res[1]
                switchName = res[2]
                lo = float(res[3])
                hi = float(res[4])
                try:
                    hours = int(res[5])
                except:
                    hours = 0
                myDevicePairs.append(DevicePair(meterName, switchName, lo, hi, hours))
                printOnTerminal("Pair created between " + meterName + " and " +  switchName + " with values " + str(lo) + "-"+str(hi) + " and hour " + str(hours))

    return(emailPasswordOK)

# This function verifies that the device in question is pared with something else
def isPairedDevice(device, devicePairs):
    for pair in devicePairs:
        if device.getName() == pair.switchName:
            return True
        if device.getName() == pair.meterName:
            return True
    return False


# Turn every switch on
def turnEverySwitchOn(myDevices):
    for d in myDevices:
        if d.isSwitch():
            d.turnOff()
            d.turnOn()


# go through meter-switch pairs and set switches based on data from meters
def adjustSwitchesBasedOnConnectedMeters(myDevices, myDevicePairs, now):
    printOnTerminal("Adjusting pairs")
    for pair in myDevicePairs:
        # find devices in that pair
        #find the meter
        for meter in myDevices:
            if meter.isMeter() and meter.getName() == pair.meterName:
                # now meter is the meter that adjusts
                # find a switch
                for switch in myDevices:
                    if switch.isSwitch() and switch.getName() == pair.switchName:
                        #at this point meter and switch are pairs to be adjusted
                        #then adjust accoriding to the binding
                        printOnTerminal("Found a meter-switch pair to adjust")
                        lowTemp = pair.lowNbr
                        highTemp = pair.highNbr
                        tempNow = meter.getTemperature()
                        #Say, tempNow is 20 and min max are 0 22, then turn on
                        if tempNow>lowTemp and tempNow<highTemp:
                            switch.turnOn()
                            printOnTerminal("Adjust " + switch.name + " ON based on the reading from " + meter.name)
                        else:
                            switch.turnOff()
                            printOnTerminal("Adjust " + switch.name + " OFF based on the reading from "+  meter.name)

        # then, separately, look for switch - system clock pairs; systemclock is handled as a meter
        # in these cases a switch is turned on/of based on time
        if pair.meterName == "systemclock":
            printOnTerminal("Adjusting based on systemclock")
            for switch in myDevices:
                if switch.isSwitch() and switch.getName() == pair.switchName:
                    printOnTerminal("Found a systemclock-switch pair to adjust")
                    start = pair.lowNbr  # has actually nothing to do with themp, but just jusing the same variable name
                    end = pair.highNbr
                    if start<end: #i.e. happens during the same day; e.g. 8 16
                        if start <= now < end:
                            switch.turnOn()
                            printOnTerminal("Adjust " + switch.name + " ON  based on the reading from the systemclock: " + str(now))
                        else:
                            switch.turnOff()
                            printOnTerminal("Adjust " + switch.name + " OFF based on the reading from the systemclock: " + str(now))
                    else: #i.e. starts today, continues tomorrow; e.g. 16 8
                        if end <= now < start:
                            switch.turnOff()
                            printOnTerminal("Adjust " + switch.name + " OFF  based on the reading from the systemclock: " + str(now))
                        else:
                            switch.turnOn()
                            printOnTerminal("Adjust " + switch.name + " ON based on the reading from the systemclock: " + str(now))

        # then, separately, look for the European spot data - switch pairs; spot data is handled as a meter
        # in these cases a switch is turned on/of based on settings
        if pair.meterName == "spotdata":
            printOnTerminal("Adjusting based on spotdata")
            for switch in myDevices:
                if switch.isSwitch() and switch.getName() == pair.switchName:
                    printOnTerminal("Found a spotdata-switch pair to adjust")
                    lowPrice = pair.lowNbr
                    highPrice = pair.highNbr
                    hours = pair.hourNbr
                    shouldBeOn = False
                    if mySpotData.spotItemArray[now].rank > hours:
                        #switch.turnOff()
                        shouldBeOn=False
                    else:
                        #switch.turnOn()
                        shouldBeOn=True
                    # if price is LOWER than specified in the first value, turn it ALWAYS on
                    if mySpotData.spotItemArray[now].price <= lowPrice:
                        #switch.turnOn()
                        shouldBeOn = True
                    # if price is HIGHER than specified in the second value, always turn off
                    if mySpotData.spotItemArray[now].price >= highPrice:
                        #switch.turnOff()
                        shouldBeOn=False
                    #To avoid switching on/of
                    if shouldBeOn:
                        switch.turnOn()
                    else:
                        switch.turnOff()



# read the command queue from email
# initiate action based on thos read commands
def checkEmailForNewCommands(email, myDevices, myDevicePairs, mySpotData):
    global stopThreads
    #read the command queue from email
    if email.readMailQueueAndReturnCommands():
        device = email.device
        command = email.command
        forceOnTerminal("Command received over email: " + device + " " + command)
        #see, if command is for the system
        if (device == "system"):
            if command == "status":
                status = "Devices in the system \n"
                for x in myDevices:
                    status = status + x.createSelfReport()
                status = status + "\n"
                status = status + "Device pairs in the system \n"
                for x in myDevicePairs:
                    status = status + x.createSelfReport()
                email.sendMail("Home Automation System Status", status)

            elif command == "reset":
                email.emptyInbox()

            elif command == "shutdown":
                forceOnTerminal("System shutdown started:")
                # Turn all devices on before shutting down!!
                forceOnTerminal("Turning all devices ON before shutting the system down")
                turnEverySwitchOn(myDevices)

                forceOnTerminal("...creating shutdown report")
                status = "I'm about to get shut down -- self destruction started -- nothing you can do about it! \n"
                #for x in myDevices:
                #    status = status + x.createSelfReport()

                forceOnTerminal("...sending shutdown report")
                email.sendMail("Home Automation System Shutdown", status)
                forceOnTerminal("...reseting command queue")
                forceOnTerminal("...killing threads")
                stopThreads = True
                readingMeters.join()
                forceOnTerminal("...killing main ... BYE!")
                exit(0)

            elif command == "prices":
                prices = mySpotData.createSpotDataReport()
                email.sendMail("Home Automation System Report", prices)

            elif command == "refresh":
                status = "I re-run startup routines \n"
                refreshSpotData(mySpotData)
                readAndManageConfigurationFile(CONFIGFILE)
                turnEverySwitchOn(myDevices)
                email.sendMail("Home Automation System Report", status)

            elif command == "help":
                help = "These are the available commands:\n"
                help = help + "system status \n"
                #help = help + "            reset \n"
                help = help + "system shutdown \n"
                help = help + "system prices \n"
                help = help + "system refresh \n"
                help = help + "system help \n"
                help = help + "------------------------------------------------ \n"
                help = help + "devicename turnon \n"
                help = help + "devicename turnoff \n"
                email.sendMail("Home Automation System Help", help)

        #go through all devices to find the one command is addressed to
        for x in myDevices:
            if x.name == device:
                #do an approppriate command for the device
                if command == "turnon":
                    x.turnOn()
                    #send a report after a succesful state change
                    status = "State changed, "+ x.name + " turned on\n"
                    for x in myDevices:
                        status = status + x.createSelfReport()
                    email.sendMail("Home Automation System State Change", status)


                elif command == "turnoff":
                    x.turnOff()
                    #send a report after a succesful state change
                    status = "State changed, "+ x.name + " turned off\n"
                    for x in myDevices:
                        status = status + x.createSelfReport()
                    email.sendMail("Home Automation System State Change", status)


# main program starts here ----------------------------------------------------------------------------------
# main program starts here ----------------------------------------------------------------------------------
# main program starts here ----------------------------------------------------------------------------------
ECHO = False
myDevices = []
myDevicePairs = []
updateInterval = 5
mySpotData = []

# Get password for email from the command line
try:
    passwrd = getpass.getpass()
except:
    printOnTerminal("ERROR in password assignment")


forceOnTerminal("Rev'n up the motor scooters! v.0.11. Wait ....")
email = 0
passwordOk = readAndManageConfigurationFile(CONFIGFILE)
if passwordOk == False:
    forceOnTerminal("Wrong password or mail address")
    forceOnTerminal("....exiting")
    exit(0)

nowTime = MyDateTime()
nowTime.setNow()

# Remove the following comment if you want to simulate savings
# mySpotData.testRunSavings(22000/3)

# reading meters in a separate thread to make sure we do it often enough
readingMeters = threading.Thread(target=readMeters, args=(1,))
readingMeters.start()

#readingTerminal = threading.Thread(target=readTerminal, args=(1,))
#readingTerminal.start()




printOnTerminal("Starting the loop:")
loop = 0
oldHour = -1

# The main program loop starts here
# ---------------------------------
while True:
    #go through every device and do approppriate actions
    loop = loop +1
    forceOnTerminal("In the loop #" +str(loop) + " at "+ nowTime.getCurrentSystemTimeString())
    time.sleep(updateInterval)

    # refresh spot data every hour AND
    now = nowTime.getCurrentSystemHour()
    if (now != oldHour and mySpotData.spotDataOK()):
        if refreshSpotData(mySpotData):
            oldHour=now
        else:
            printOnTerminal("Cannot refresh Spot Data in the main loop. Trying again!")

    # ------------------------------------------------------------------------------------
    # These three lines + the readMeters thread above is the everlasting main loop!
    adjustSwitchesBasedOnConnectedMeters(myDevices, myDevicePairs, now)
    checkEmailForNewCommands(email, myDevices, myDevicePairs, mySpotData)
    # ------------------------------------------------------------------------------------

    #Force a smiley on terminal after a succesfull first loop
    if (loop==1):
        forceOnTerminal(":-) Josie is home! Now we'll just loop on ....")
        forceOnTerminal(("For help, send system help on subject field to ") + email.emailAccount)
        forceOnTerminal(" ")