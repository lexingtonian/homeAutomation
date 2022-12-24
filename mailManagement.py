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
# Code from best solution in page below:
# https://help.zoho.com/portal/community/topic/zoho-mail-servers-reject-python-smtp-module-communications

import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
import imaplib
import email
from debugTools import *

#Command structure
#devicename action
#actions: turnon, turnoff
#
#status -- system status
#reset -- system reset
#shutdown -- system shutdown
#electricity prices -- system prices

class haMail:
    # Define to/from
    # Command variables obtained from mail:
    device = "Not defined"
    command = "Not defined"
    emailAccount = "Not defined"
    emailPassword = "Not defined"
    emailIMAP = "Not defined"
    emailIMAPPort = 0
    emailSMTP = "Not defined"
    emailSMTPPort = 0
    emailRecipient = "Not defined"
    #this is the list of authorized email accounts allowed to command the system
    #specified in the config file HA_Config.txt
    emailAccountList = []

    def __init__(self, emailAccount, emailPassword, emailIMAP, emailIMAPPort, emailSMTP, emailSMTPPort, emailRecipient, emailAccountList):
        self.emailAccount=emailAccount
        self.emailPassword=emailPassword
        self.emailIMAP = emailIMAP
        self.emailIMAPPort=emailIMAPPort
        self.emailSMTP=emailSMTP
        self.emailSMTPPort=emailSMTPPort
        self.emailRecipient=emailRecipient
        self.emailAccountList = emailAccountList


    def verifyEmail(self):
        try:
            server = smtplib.SMTP_SSL(self.emailIMAP, self.emailSMTPPort)
            server.login(self.emailAccount, self.emailPassword)
            server.quit()
            return True
        except:
            return False

    def sendReport(self, report):
        sender = self.emailAccount
        sender_title = "Home Automation System"
        recipient = self.emailRecipient

        # Create message
        msg = MIMEText(report, 'plain', 'utf-8')
        msg['Subject'] =  Header(report, 'utf-8')
        msg['From'] = formataddr((str(Header(sender_title, 'utf-8')), sender))
        msg['To'] = recipient
        try:
            # Create server object with SSL option
            server = smtplib.SMTP_SSL(self.emailIMAP, self.emailSMTPPort)

            # Perform operations via server
            server.login(self.emailAccount, self.emailPassword)
            server.sendmail(sender, [recipient], msg.as_string())
            server.quit()
        except:
            printOnTerminal("Cannot send report!")

    def sendMail(self, title, body):
        sender = self.emailAccount
        sender_title = "Home Automation System"
        recipient = self.emailRecipient

        # Create message
        #msg = MIMEText(command, 'plain', 'utf-8')
        msg = MIMEText(body)
        msg['Subject'] =  Header(title, 'utf-8')
        msg['From'] = formataddr((str(Header(sender_title, 'utf-8')), sender))
        msg['To'] = recipient

        # Create server object with SSL option
        try:
            server = smtplib.SMTP_SSL(self.emailIMAP, self.emailSMTPPort)
            # Perform operations via server
            server.login(self.emailAccount, self.emailPassword)
            server.sendmail(sender, [recipient], msg.as_string())
            server.quit()
        except:
            printOnTerminal("Cannot send mail")

    def readMailQueuAndReturnCommands(self):
        try:
            mail = imaplib.IMAP4_SSL(self.emailIMAP)
            mail.login(self.emailAccount, self.emailPassword)
            mail.select(readonly=True)  # refresh inbox
            status, message_ids = mail.search(None, 'ALL')  # get all emails
            s = "empty"
            #run through messages and exit after the first
            for message_id in message_ids[0].split():  # returns all message ids


                # for every id get the actual email
                status, message_data = mail.fetch(message_id, '(RFC822)')
                actual_message = email.message_from_bytes(message_data[0][1])

                # extract the needed fields
                email_date = actual_message["Date"]
                subject = actual_message["Subject"]
                #make sure the email comes from an accepted account
                sender = actual_message["From"]
                #1. loop through the list of accepted acccounts
                #2. if the sender is not one of the accepted accounts abort!
                #3. but before hat send an email to the main account about the attempt
                abort = True
                for ac in self.emailAccountList:
                    if sender.find(ac)!=-1:
                        printOnTerminal("----Sender: " + sender)
                        abort = False
                if (abort):
                    printOnTerminal("Commanding email sent from an unathorized account " +sender + ". Ignoring .....")
                    r = "Commanding email sent from an unathorized account "+ sender + ". Ignoring ....."
                    self.sendReport(r)
                    self.resetCommandQueue()
                    return False
                s = str(subject)
                printOnTerminal("Command received from email: " + s)

            #Note indent= only one loop cycle"
            #Expecting devicename command
            #Extract command and device
            #
            #Split to words

            splits = s.split()
            if len(splits) == 2:
                self.device = splits[0]
                self.command = splits[1]
                self.device = self.device.lower()
                self.command = self.command.lower()
            else:
                self.device = "null"
                self.command = "null"
            return True

        except:
            printOnTerminal("Cannot read email and analyze commands x")
            return False

    def emptyInbox(self):
        try:
            box = imaplib.IMAP4_SSL(self.emailIMAP, self.emailIMAPPort)
            box.login(self.emailAccount, self.emailPassword)
            box.select('Inbox')
            typ, data = box.search(None, 'ALL')
            for num in data[0].split():
                box.store(num, '+FLAGS', '\\Deleted')
            box.expunge()
            box.close()
            box.logout()
            printOnTerminal("Email inbox emptied")
            return True
        except:
            printOnTerminal("Cannot empty inbox")
            return False



