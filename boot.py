# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
#import webrepl
#webrepl.start()

import network
import utime
from w_credentials import ssid, password

red = network.WLAN(network.STA_IF)
red.active(True)

if not red.isconnected():
    red.connect(ssid, password)
    print('Conectando WiFi')

while not red.isconnected():
    print('.', end=' ')
    utime.sleep_ms(100)
    
print('WiFi conectado!')
print(red.ifconfig())