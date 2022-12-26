# homeAutomation
This is a simple home automation system intended to control electrical outlets to save electricity.

It has the following functionality:

-it reads hourly energy prices for Finland

-it reads a predefined configuration HA_Config.txt file that defines various things, such as rules for electro consumption and the topology of the device network

-it can be controlled through email where commands are send on the subject field with two terms (target, action)

-it runs until it is shut down through email

It is intended to be run on Raspberry Pi or similar. It is implemented in Python

——

-It’s currently only for Shelly devices

-It’s been tested with the https://mail.zoho.eu/ email service as it provides machine access; however, it can be controlled from any email

——

The current Python module structure is as follows:

*homeAutomation.py — the main program

*spotData.py — classes and functions to manage Finnish energy prices

*mailManagement.py — to read and write emails to the controlling email account

*devices.py — home devices under management

*dateTimeConversions.py — a few simple conversion tools

*HA_Config.txt — configuration file

As it's main idea, there are the following kinds of actors

-Devices, currently just switches and meters. Switches can be on/of, meters provide data, such as temperature, humidity or prices

-Device pairs, where a meter is paired to control a switch. Note, that in addition to a physical meter, such as a thermometer, a systemclock and spotdata collected from the European prices are also just meters!

All this is controlled in the configuration file where you can create the following kinds of pairs

Pair LaundryRoomThermometer LaundryRoomHeater -10 20

==> that would follow LaundryRoomThermometer and turn on LaundryRoomHeater if the temperature is between -10 and 20 degrees and turn it off outside that bracket

Pair SpotData WaterBoiler 0.05 0.75 4

==> that would follow the SpotData European prices and turn on WaterBoiler for the four cheaoest hours of the day; however taking into account that if the price is below 0.05€ then leave it on all anyway, and if it is ove 0.75€, turn it off regardless of required hours

Pair Systemclock PorchLight 18 6

==> that would turn on PorchLights between 18 and 6; i.e. for the night