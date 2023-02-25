# Copyright Ari Jaaksi, 2023
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
# This module implements a watcdog to monitor,
# that the Home Automation is up and running
#
# -------------------------------------------------------------------------

import socket
import time
import threading
from datetime import datetime
from mailManagement import haMail

HOST = '0.0.0.0'  # Listen on all network interfaces
PORT = 12345  # Use a unique port number
PING_TRESHOLD_SEC = 30  #how manyt sec idle before HA system is considerd down
IDLE_TRESHOLD_SEC = 60 #how many seconds without ping before the wachdog is treminated
password = "null"
haRunning = False
emailCreated = False
stopThreads = False
killWatchdog = False

# get email credentials frm the Home Automation app
def createEmail(res, passwrd):
    global wdMail
    global emailCreated
    emailAccount = res[1]
    emailPassword = passwrd  # note: not from file but a user prompt
    emailIMAP = res[2]
    emailIMAPPort = int(res[3])
    emailSMTP = res[4]
    emailSMTPPort = int(res[5])
    emailRecipient = res[6]
    acList = []
    wdMail = haMail(emailAccount, emailPassword, emailIMAP, emailIMAPPort, emailSMTP, emailSMTPPort, emailRecipient, acList)
    print("Creating: ", emailAccount)
    if wdMail.verifyEmail():
        emailCreated = True
        print("Email creation successful")
    else:
        print("Email creation failed")


# This function runs in a separate thread independently
# it measures time since the last ping from the home atomation system
# If the time since last ping > PING_TRESHOLD_SEC a warning email is sent
def countTime(name):
    global pingTime
    global wdMail
    global haRunning
    global emailCreated
    global stopThreads
    global killWatchdog
    while True:
        time.sleep(1)
        nowTime = datetime.now()
        deltaTime = nowTime - pingTime
        deltaSec = deltaTime.total_seconds()
        print("DeltaSec: ", deltaSec)
        if deltaSec > PING_TRESHOLD_SEC and haRunning == True:
            #alert the user; home automation has been idle for more than treshold
            print("Home Automation System not running!")
            if emailCreated:
                wdMail.sendReport("Home Automation System not running! -- a message from the watchdog")
            else:
                print("Watchdog cannot send an email!")
            haRunning = False
        if deltaSec > IDLE_TRESHOLD_SEC and haRunning == False:
            # shut down this watchdog
            killWatchdog = True
            stopThreads = True
            if emailCreated:
                wdMail.sendReport("Home Automation System not running for " + str(deltaSec) + " seconds! Shutting down the watchdog")
            else:
                print("Home Automation System not running for ", str(deltaSec), " seconds! Shutting down the watchdog")
        if stopThreads:
            killWatchdog = True
            break




# ---- main program starts here --------------------------------------------
print("Starting the watchdog ...")
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen()

conn, addr = s.accept()
print('Home Automation found running at ', addr)

nowTime = datetime.now()
pingTime = datetime.now()
deltaTime  = nowTime - pingTime
deltaSec = deltaTime.total_seconds()

#We start a new function in a separate thread to calculate time
countingTimeTh = threading.Thread(target=countTime, args=(1,))
countingTimeTh.start()

mailCredentials = "not_defined"
print("Watchdog running, Home Automation running  ....")
while True:
    if killWatchdog:
        exit()
    conn, addr = s.accept()
    data = conn.recv(1024)
    if data:
        text = data.decode()
        split = text.split()
        haRunning = True
        # if data starts by "email", the we parse email credentials from it
        if split[0] == "password":
            password = split[1]
        elif split[0] == "email":
            mailCredentials = split
            createEmail(split, password)
            wdMail.sendReport("Home Automation watchdog running -- all is fine!")
        elif split[0] == "ping":
            pingTime = datetime.now()

        print('Received:', data.decode(), " ==> All systems up and running!")
        if emailCreated==False:
            print("Watchdog cannot connect to email. If you get this message often, please: ")
            print("resfresh Home Automation by sending 'system refresh' or restarting Home Automation")
            #trying to crate email
            print(mailCredentials)
            if mailCredentials != "not_defined":
                createEmail(mailCredentials, password)

        conn.sendall(data)


conn.close()
