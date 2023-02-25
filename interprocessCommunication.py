# Copyright Ari Jaaksi 2023
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
# This module implements a class Computer that can be used as a watchdog
# to ensure, this process/application is ok and running
# It is then up to the other computer to implement actions
# The implementation for the other computer is XXX
# -------------------------------------------------------------------------

import socket
from debugTools import *

class Computer():
    host = '0.0.0.0'
    port = 0
    #HOST = '192.168.1.190'  # Replace with the remote hostname or IP address
    #PORT = 12345  # Use the same port number as the server

    def __init__(self, host, port):
        self.host = host
        self.port = port

    def setHostAndPort(self, host, port):
        self.host = host
        self.port = port
        printOnTerminal("Setting watchdog host and port to " + host + " and " + str(port))
    def sendMessage(self, message):
        printOnTerminal("Contacting a watchdog (in message)")
        if self.host == "0.0.0.0":
            printOnTerminal("Watchdog computer not defined")
            return
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.host, self.port))
            s.sendall(str.encode(message))
            s.close()
        except:
            printOnTerminal("Cannot send a watchdog message")

