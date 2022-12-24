# a placeholder for random testing
# ignore

from devices import *

#class ShellySwitch(ShellyDevice):
#    pass

#class ShellyMeter(ShellyDevice):
#    def __init__(self, name, dtype, address, heatingHoursRequired, max, min, extra):
#        super().__init__(name, dtype, address, heatingHoursRequired, max, min)
#        self.extra = extra

#    def printExtra(self):
#        print(self.extra)


x = ShellyMeter("name", "address")
#y = ShellySwitch("name", "dtype", "address", 3, 3, 3)

print(isinstance(x, ShellyMeter))
print(x.getName())

y = ShellySwitch("svitsi","192.168.1.4",1,2,3)
y.turnOn()
y.turnOff()


#d = Device("Laite")
#print(d.getName())