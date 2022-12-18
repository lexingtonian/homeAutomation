from datetime import datetime, date
import re


class MyDateTime:
    year = 0
    month = 0
    date = 0
    hour = 0
    minute = 0

    # set computer time now
    def setNow(self):
        now = datetime.now()
        self.year = now.year
        self.month = now.month
        self.date = now.day
        self.hour = now.hour
        self.minute = 0

    # set time read from price data 2022-11-19T18:00:00+02:00
    def setHour(self, string):
        s = re.findall(r'\d+', string)
        self.year = int(s[0])
        self.month = int(s[1])
        self.date = int(s[2])
        self.hour = int(s[3])

    def getCurrentSystemHour(self):
        now = datetime.now()
        return now.hour

    def getCurrentSystemTimeString(self):
        return (str(datetime.now()))