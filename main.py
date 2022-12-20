import time
from datetime import datetime
from dateTimeConversions import MyDateTime
from spotData import SpotData
from shellyControls import ShellyDevice, ShellyDevicePair
from mailManagement import haMail
import getpass
import threading
from debugTools import *

#CONFIGFILE = "/Users/jaaksi/Downloads/HomeAutomation/HA_Config.txt"
CONFIGFILE = "HA_Config.txt"
stopThreads = False

def printDeviceDayPlan(msd, d):
    printOnTerminal(d.name+ ":")
    str =  "Hour:   1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 16 17 18 19 20 21 22 23 24"
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


#Readining meters in a separate thread
def thread_function(name):
    while True:
        time.sleep(1)
        for x in shellyDevices:
            if x.isMeter():
                x.getTemperature()
        global stopThreads
        if stopThreads:
            break


def refreshSpotData(mySpotData):
    printOnTerminal("Refreshing Spot -data")
    #mySpotData = SpotData(daytimeTax, nightimeTax)
    if mySpotData.populateSpotData():
        mySpotData.addTax()
        mySpotData.printSpotDataArray()
        return True
    else:
        printOnTerminal("Failed in refreshing Spot -data")
        return False


def readAndManageConfigurationFile(filename):
    global shellyDevicePairs
    global shellyDevices
    global email
    global mySpotData

    shellyDevices.clear()
    shellyDevicePairs.clear()

    try:
        f = open(filename, "r")
    except:
        printOnTerminal("Cannot open configuration file at "+ filename)
        printOnTerminal("EXIT")
        exit(0)
    acList = []
    for x in f:
        if x[0]!="#" and x[0]!='\n':
            res = x.split()
            if res[0]=="Device":
                deviceName = res[1]
                deviceType = res[2]
                ipAddress = res[3]
                nbrOfHours = int(res[4])
                highPrice = float(res[5])
                lowPrice = float(res[6])
                printOnTerminal("Creating device: " + deviceName)
                shellyDevices.append(ShellyDevice(deviceName, deviceType, ipAddress, nbrOfHours,highPrice,lowPrice))
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
                lo = int(res[3])
                hi = int(res[4])
                shellyDevicePairs.append(ShellyDevicePair(meterName, switchName,lo, hi))


#main program starts here ----------------------------------------------------------------------------------
#print("Starting ----------")
shellyDevices = []
shellyDevicePairs = []
updateInterval = 5

#Get password for email
try:
    passwrd = getpass.getpass()
except Exception as error:
    printOnTerminal('ERROR in password assignment: '+  error)

readAndManageConfigurationFile(CONFIGFILE)

nowTime = MyDateTime()
nowTime.setNow()

#shellyDevices.index(ShellyDevice.name)

#Remove the following comment if you want to simulate savings
#mySpotData.testRunSavings(22000/3)

#Tests
#remove comments if you want testing
#shellyDevices[0].turnOn()
#time.sleep(2)
#shellyDevices[0].turnOff()

#reding meters in a separate thread to make sure we do it often enough
readingMeters = threading.Thread(target=thread_function, args=(1,))
readingMeters.start()

printOnTerminal("Starting the loop:")
loop = 0
oldHour = -1

#The main program loop starts here
while True:
    #go through every device and do approppriate actions
    loop = loop +1
    printOnTerminal("In the loop #" +str(loop) + " at "+ nowTime.getCurrentSystemTimeString())
    time.sleep(updateInterval)

    #refresh spot data every hour AND
    #overide manually (email) spot driven settings
    now = nowTime.getCurrentSystemHour()
    if (now != oldHour and mySpotData.spotDataOK()):
        if refreshSpotData(mySpotData):
            oldHour=now
        else:
            printOnTerminal("Cannot refresh Spod Data in the main loop. Trying again!")

        #go through the Spot Data  and turn on devices based on their settings
        for device in shellyDevices: #loop through devices tyo turn them on/of based on the spot data and settings
            if device.isSwitch():
                debugStr = "Device " + device.name + "heatingHoursRequired: " + str(device.heatingHoursRequired) + " maxPrice: "+  str(device.maxPrice)+  " minPrice: " + str(device.minPrice)
                #print(debugStr)
                debugStr = "Device " + device.name + " was turned "
                #if the current price is below the device min price, turn it always on
                if mySpotData.spotItemArray[now].price <= device.minPrice:
                    debugStr = debugStr + "ON because mySpotData.spotItemArray[hourNow].price <= device.minPrice:"
                    device.turnOn()

                #else, if the current price is above the device max price, turn it off
                elif mySpotData.spotItemArray[now].price >= device.maxPrice:
                    debugStr = debugStr + "OFF because mySpotData.spotItemArray[hourNow].price >= device.maxPrice:"
                    device.turnOff()

                #turn on if spot data rank < heatingHoursRequired
                elif mySpotData.spotItemArray[now].rank > device.heatingHoursRequired: #turn off the device based on the ranking
                    debugStr = debugStr + "OFF because mySpotData.spotItemArray[hourNow].rank > device.heatingHoursRequired:"
                    device.turnOff()
                else:
                    device.turnOn()
                    debugStr = debugStr + "ON because none of the config file terms was met"

                #print(debugStr)

        # go through meter-switch pairs and set switches
        #first find pairs
        for pair in shellyDevicePairs:
            #find meter
            #print("Going though meter - switch pairs")
            meterFound = False
            switchFound = False
            #then find devices in that pair
            for device in shellyDevices:
                if device.isMeter() and device.name == pair.meterName:
                    meterToRead=device
                    meterFound = True
                if device.isSwitch() and device.name == pair.switchName:
                    switchToAdjust = device
                    switchFound = True
                #print("X, ", device.name, meterFound, switchFound)
            #then adjust accoriding to the binding
            if meterFound and switchFound:
                #print("Found a meter-switch pair to adjust")
                lowTemp = pair.lowTemp
                highTemp = pair.highTemp
                tempNow = meterToRead.getTemperature()
                if tempNow>lowTemp and tempNow<highTemp:
                    switchToAdjust.turnOn()
                    printOnTerminal("Adjust " + switchToAdjust.name + "ON based on the reading from " + meterToRead.name)
                else:
                    switchToAdjust.turnOff()
                    printOnTerminal("Adjust " + switchToAdjust.name + "OFF based on the reading from "+  meterToRead.name)

    #read the command queue from email
    if email.readMailQueuAndReturnCommands():
        device = email.device
        command = email.command
        #see, if command is for the system
        if (device == "system"):
            if command == "status":
                status = "Devices in the system \n"
                for x in shellyDevices:
                    status = status + x.createSelfReport()
                status = status + "\n"
                status = status + "Device pairs in the system \n"
                for x in shellyDevicePairs:
                    status = status + x.createSelfReport()
                email.sendMail("Home Automation System Status", status)
                email.resetCommandQueue()

            elif command == "reset":
                email.resetCommandQueue()

            elif command == "shutdown":
                printOnTerminal("System shutdown started:")
                #Turn all devices on before shutting down!!
                printOnTerminal("Turning all devices ON before shutting the system down")
                for x in shellyDevices:
                    x.turnOn()

                printOnTerminal("...creating shutdown report")
                status = "I'm about to get shut down -- self destruction started -- nothing you can do about it! \n"
                for x in shellyDevices:
                    status = status + x.createSelfReport()

                printOnTerminal("...sending shutdown report")
                email.sendMail("Home Automation System Shutdown", status)
                printOnTerminal("...reseting command queue")
                email.resetCommandQueue()
                printOnTerminal("...killing threads")
                stopThreads = True
                readingMeters.join()
                printOnTerminal("...killing main ... BYE!")
                exit(0)

            elif command == "prices":
                prices = mySpotData.createSpotDataReport()
                email.sendMail("Home Automation System Report", prices)
                email.resetCommandQueue()

            elif command == "refresh":
                status = "I re-run startup routines \n"
                refreshSpotData(mySpotData)
                readAndManageConfigurationFile(CONFIGFILE)
                email.sendMail("Home Automation System Report", status)
                email.resetCommandQueue()

            elif command == "help":
                help = "These are the available commands:\n"
                help = help + "system status \n"
                #help = help + "            reset \n"
                help = help + "system shutdown \n"
                help = help + "system prices \n"
                help = help + "system refresh \n"
                help = help + "system help \n"
                help = help + "------------------------------------------------ \n"
                help = help + "devicename systemturnon \n"
                help = help + "devicename turnoff \n"
                email.sendMail("Home Automation System Help", help)
                email.resetCommandQueue()

        #go through all devices to find the one command is addressed to
        for x in shellyDevices:
            if x.name == device:
                #do an approppriate command for the device
                if command == "turnon":
                    x.turnOn()
                    #send a report after a succesful state change
                    status = "State changed, "+ x.name + " turned on\n"
                    for x in shellyDevices:
                        status = status + x.createSelfReport()
                    email.sendMail("Home Automation System State Change", status)
                    email.resetCommandQueue()
                elif command == "turnoff":
                    x.turnOff()
                    #send a report after a succesful state change
                    status = "State changed, "+ x.name + " turned off\n"
                    for x in shellyDevices:
                        status = status + x.createSelfReport()
                    email.sendMail("Home Automation System State Change", status)
                    email.resetCommandQueue()
                    
    #Force a smiley on terminal after a succesfull first loop
    if (loop==1):
        forceOnTerminal(":-)")