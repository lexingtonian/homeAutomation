# Code from best solution in page below:
# https://help.zoho.com/portal/community/topic/zoho-mail-servers-reject-python-smtp-module-communications

import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
import imaplib
import email

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
    emailPassword ="Not defined"
    emailIMAP ="Not defined"
    emailIMAPPort = 0
    emailSMTP ="Not defined"
    emailSMTPPort = 0
    emailRecipient ="Not defined"

    def __init__(self, emailAccount, emailPassword, emailIMAP, emailIMAPPort, emailSMTP, emailSMTPPort, emailRecipient):
        self.emailAccount=emailAccount
        self.emailPassword=emailPassword
        self.emailIMAP = emailIMAP
        self.emailIMAPPort=emailIMAPPort
        self.emailSMTP=emailSMTP
        self.emailSMTPPort=emailSMTPPort
        self.emailRecipient=emailRecipient


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
            print("Cannot send report!")

    def resetCommandQueue(self):
        self.command = "null"
        self.device = "null"
        sender = self.emailAccount
        sender_title = "Home Automation System"
        recipient = self.emailAccount

        # Create message
        msg = MIMEText("reset", 'plain', 'utf-8')
        #msg['Subject'] =  Header("reset", 'utf-8')
        msg['Subject'] =  Header("reset")
        msg['From'] = formataddr((str(Header(sender_title, 'utf-8')), sender))
        msg['To'] = recipient
        try:
            # Create server object with SSL option
            server = smtplib.SMTP_SSL(self.emailIMAP, self.emailSMTPPort)

            # Perform operations via server
            server.login(self.emailAccount, self.emailPassword)
            server.sendmail(sender, [recipient], msg.as_string())
            server.quit()
            self.emptyInbox()
        except:
            print("Cannot reset command queue!")

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
        server = smtplib.SMTP_SSL(self.emailIMAP, self.emailSMTPPort)

        # Perform operations via server
        server.login(self.emailAccount, self.emailPassword)
        server.sendmail(sender, [recipient], msg.as_string())
        server.quit()

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
                s = str(subject)
                print("Command received from email: ",s)

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
            return True

        except:
            print("Cannot read email and analyze commands x")
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
            return True
        except:
            print("Cannot empty inbox")
            return False



