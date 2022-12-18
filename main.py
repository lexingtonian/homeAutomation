import time
from datetime import datetime
from dateTimeConversions import MyDateTime
from spotData import SpotData
from shellyControls import ShellyDevice, ShellyDevicePair
from mailManagement import haMail
import getpass
import threading

#CONFIGFILE = "/Users/jaaksi/Downloads/HomeAutomation/HA_Config.txt"
CONFIGFILE = "HA_Config.txt"
stopThreads = False

def printDeviceDayPlan(msd, d):
    print(d.name, ":")
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

    print(str)
    print(str2)


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
    print("Refreshing Spot -data")
    #mySpotData = SpotData(daytimeTax, nightimeTax)
    mySpotData.populateSpotData()
    mySpotData.addTax()
    mySpotData.printSpotDataArray()

#main program starts here ----------------------------------------------------------------------------------
#print("Starting ----------")
shellyDevices = []
shellyDevicePairs= []

#Get password for email
try:
    passwrd = getpass.getpass()
except Exception as error:
    print('ERROR in password assignment: ', error)

#read config file
if (True):
    try:
        f = open(CONFIGFILE, "r")
    except:
        print("Cannot open configuration file at ", CONFIGFILE)
        print("EXIT")
        exit(0)
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
                print("Creating device: ", deviceName)
                shellyDevices.append(ShellyDevice(deviceName, deviceType, ipAddress, nbrOfHours,highPrice,lowPrice))
            elif res[0]=="Email":
                emailAccount = res[1]
                emailPassword = passwrd  #note: not from file but a user prompt
                emailIMAP = res[2]
                emailIMAPPort = int(res[3])
                emailSMTP = res[4]
                emailSMTPPort = int(res[5])
                emailRecipient = res[6]
                print("Creating email connections: ", emailAccount)
                email = haMail(emailAccount, emailPassword, emailIMAP, emailIMAPPort, emailSMTP, emailSMTPPort,emailRecipient)
                email.emptyInbox()
            elif res[0]=="Common":
                updateInterval = int(res[1])
                daytimeTax = float(res[2])
                nightimeTax = float(res[3])
                print("Creating Spot Data with day tax at ", daytimeTax, " and night tax at ",nightimeTax )
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

print("Starting the loop:")
loop = 0
oldHour = -1

while True:
    #go through every device and do approppriate actions
    loop = loop +1
    print("In the loop #: ",loop, "at ", nowTime.getCurrentSystemTimeString())
    time.sleep(updateInterval)
    #read temperatures from each meter and update them for those objects
    #currently implemented in a separate thread and thus commented away here
    #for x in shellyDevices:
    #    if x.isMeter():
    #        x.getTemperature()

    #refresh spot data every hour AND
    #overide manually (email) spot driven settings
    now = nowTime.getCurrentSystemHour()
    if (now != oldHour and mySpotData.spotDataOK()):
        refreshSpotData(mySpotData)
        oldHour=now

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
                    print("Adjust ", switchToAdjust.name , "ON based on the reading from ", meterToRead.name)
                else:
                    switchToAdjust.turnOff()
                    print("Adjust ", switchToAdjust.name, "OFF based on the reading from ", meterToRead.name)

    #read the command queue from email
    if email.readMailQueuAndReturnCommands():
        device = email.device
        command = email.command
        #see, if command is for the system
        if (device == "system"):
            if command == "status":
                status = "Doing great! \n"
                for x in shellyDevices:
                    status = status + x.createSelfReport()
                email.sendMail("Home Automation System Status", status)
                email.resetCommandQueue()
            elif command == "reset":
                email.resetCommandQueue()

            elif command == "shutdown":
                print("System shutdown started:")
                print("...creating shutdown report")
                status = "I'm about to get shut down -- self destruction started -- nothing you can do about it! \n"
                for x in shellyDevices:
                    status = status + x.createSelfReport()

                print("...sending shutdown report")
                email.sendMail("Home Automation System Shutdown", status)
                print("...reseting command queue")
                email.resetCommandQueue()
                print("...killing threads")
                stopThreads = True
                readingMeters.join()
                print("...killing main ... BYE!")
                exit(0)

            elif command == "prices":
                prices = mySpotData.createSpotDataReport()
                email.sendMail("Home Automation System Report", prices)
                email.resetCommandQueue()

            elif command == "refresh":
                status = "I re-run startup routines \n"
                refreshSpotData(mySpotData)
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
