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

y = ShellySwitch("svitsi","192.168.1.9")
y.turnOn()
y.turnOff()


#d = Device("Laite")
#print(d.getName())

from scapy.all import *

print(os.system('arp -n ' + str("192.168.1.168")))

from time import sleep

from pyroombaadapter import PyRoombaAdapter

PORT = "/dev/ttyUSB0"
adapter = PyRoombaAdapter(PORT)

adapter.send_song_cmd(0, 9,
                      [69, 69, 69, 65, 72, 69, 65, 72, 69],
                      [40, 40, 40, 30, 10, 40, 30, 10, 80])
adapter.send_play_cmd(0)
sleep(10.0)