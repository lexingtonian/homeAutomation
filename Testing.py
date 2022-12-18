import ShellyPy
import time

def UdateMe():
    print("Updated")

print("1")
device = ShellyPy.Shelly("192.168.1.4")
device.relay(0, turn=True)
print("2")

#meter = ShellyPy.Shelly("192.168.1.5", init="UpdateMe")
meter = ShellyPy.Shelly("192.168.1.5")
print("3")
meter.


while True:
    time.sleep(5)
    print(".")
