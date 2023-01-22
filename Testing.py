#https://github.com/AbhinavOraon/Nodemcu-prog./blob/main/esp8266_with_python.ino
import os, sys
import httplib2

http = httplib2.Http()
url = "http://192.168.4.1/shutterbutton"

response, content = http.request(url,"GET")