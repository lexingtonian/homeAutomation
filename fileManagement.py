CONFIGFILE = "/Users/jaaksi/Downloads/HomeAutomation/HA_Config.txt"

class ConfigFile:
    def OtapoisreadAndCreateDevices(self):
        f = open("/Users/jaaksi/Downloads/HomeAutomation/HA_Config.txt", "r")
        for x in f:
            if x[0]=="#":  #read comment
                print(x)
            else:
                res = x.split()
                if res[0]=="Device":
                    deviceName = res[1]
                    ipAddress = res[2]
                    nbrOfHours = int(res[3])
                    highPrice = int(res[4])
                    lowPrice = int(res[5])

#file = ConfigFile()
#file.readAndCreateDevices()

