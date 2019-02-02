import paho.mqtt.client as mqtt
import json
import time
import datetime
from datetime import date
from datetime import timedelta

def mqttcSetup(on_message=None, on_connect=None, on_publish=None, on_subscribe=None, on_log=None, createCard=None, setup=None, mainLoop=None):
    # If you want to use a specific client id, use
    # mqttc = mqtt.Client("client-id")
    # but note that the client id must be unique on the broker. Leaving the client
    # id parameter empty will generate a random id for you.
    mqttc = mqtt.Client()

    if(on_message != None):
        mqttc.on_message = on_message
    if(on_connect != None):
        mqttc.on_connect = on_connect
    if(on_publish != None):
        mqttc.on_publish = on_publish
    if(on_subscribe != None):
        mqttc.on_subscribe = on_subscribe
    if(on_log != None):
        mqttc.on_log = on_log
    mqttc.connect("localhost", 1883, 60)
    mqttc.subscribe("/cardResponse",0)
    mqttc.subscribe('/config/update',0)
    if(createCard != None):
        createCard(mqttc)
    if(setup != None):
        setup()

    while True:
        #global curCard
        #print("Current Card: " + curCard)
        mqttc.loop(.1) #blocks for 100ms
        #print('running mqttc loop')
        if(mainLoop != None):
            mainLoop(mqttc)