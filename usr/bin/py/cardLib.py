import json
import time
import datetime
from datetime import date
from datetime import timedelta


class ComplexEncoder(json.JSONEncoder):
    def default(self, o): # pylint: disable=E0202
        if hasattr(o,'reprJSON'):
            return o.reprJSON()
        else:
            return json.JSONEncoder.default(self, o)

imgRootPath = '/usr/bin/img/'

def decodeResponse(inputStr):
    new_Str = inputStr
    print("decoding :"+new_Str)
    if(inputStr[0] == '"'):
        new_Str = inputStr[1:]
        new_Str = new_Str[:-1]
        new_Str = new_Str.replace('\\"', '"')
    print(new_Str)
    jsval = json.loads(new_Str)
    print("decoded jsval")
    print(jsval)
    return jsval

class Position:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.align = None
    def reprJSON(self):
        if self.align:
            return dict(x=self.x, y=self.y, align=self.align)
        else:
            return dict(x=self.x, y=self.y)

class Element:
    def __init__(self, id, elementType, value, position): 
        self.id = id
        self.type = elementType
        self.value = value
        self.position = position
        self.size = None

    @classmethod
    def generateTextElement(self, id, value, size, x, y, alignment):
        pos = Position(x,y)
        pos.align = alignment
        basic = self(id, "text", value, pos)
        basic.size = size
        return basic
    @classmethod
    def generateImageElement(self, id, imagePath, x, y):
        pos = Position(x,y)
        basic = self(id, "image", imagePath, pos)
        return basic
    @classmethod
    def generateElementUpdate(self, id, value):
        basic = self(id,None,value, None)
        return basic
    def reprJSON(self):
        if self.type:
            if self.size:
                return dict(id=self.id, type=self.type, value=self.value, position=self.position, size=self.size)
            else:
                return dict(id=self.id, type=self.type, value=self.value, position=self.position)
        else:
            return dict(id=self.id, value=self.value)


def setCardNightlightColors(mqttc, color=0):
    print ('setting night light')
    if(isinstance(color, list) and len(color) == 4):
        payload = {
            'cmd': 'buttons',
            'value': color
        }
    else :
        payload = {
            'cmd': 'buttons',
            'value': [0,0,0,0]
        }
    print("Full JSON")
    jsonVal = json.dumps(payload)
    print(jsonVal)
    mqttc.publish("/set", jsonVal)


def updateCardInfo(mqttc, curCardValue, newMessage ):
    print('Running card Info Update function')
    if 'cardId' in newMessage:
        print('contains a cardid value')
        if(newMessage['action'] == 'create'):
            print("Create response")
            if (curCardValue.id < 0) and (newMessage["attention"] == curCardValue.responseTopic):
                print('assigning card id')
                curCardValue.id = newMessage["cardId"]
                print('Assigning card its id: ' + str(curCardValue.id))
                setCardNightlightColors(mqttc, curCardValue.nightlight)
        elif(newMessage['action'] == 'select'):
            print("Select response")
            print('selected card {0} Expected {1}'.format(newMessage["cardId"], curCardValue.id))
            if (curCardValue.id == newMessage["cardId"]):
                # this has become the active card
                print('Card has become active: ' + str(curCardValue.id))
                curCardValue.active = True
                setCardNightlightColors(mqttc, curCardValue.nightlight)
            else:
                #another card has become the active card
                curCardValue.active = False
                print('A different card has become active')
        else:
            print('Action is not a known one: ' + newMessage['action'])
    else:
        print('No card ID in message')
    return curCardValue

class CardObj:
  def __init__(self, bgColor, responseTopic, command):
      self.bg_color = bgColor
      self.responseTopic = responseTopic
      self.elements = []
      self.command = command
      self.nightlight = 0
      self.id = -1
  def reprJSON(self):
      return dict(cmd=self.command, bg_color=self.bg_color, responseTopic=self.responseTopic, elements=self.elements) 

class UpdateCardObj:
  def __init__(self, cardId):
      self.command = 'update_card'
      self.id = cardId
      self.elements = []
  def reprJSON(self):
      return dict(cmd=self.command, id=self.id, elements=self.elements) 

def generateImgPath(path, image):
    return path + 'img_' + image + '.bin'

def updateCard(mqttc, updateObj):
    print('updateing Card')
    jsonVal = json.dumps(updateObj.reprJSON(), cls=ComplexEncoder)
    print(jsonVal)
    mqttc.publish("/card", jsonVal)

def removeCard(mqttc, cardToRemove):
    if(cardToRemove.id):
        print('removing Card')
        jsonVal = json.dumps(dict(cmd="remove_card", id=cardToRemove.id))
        print(jsonVal)
        mqttc.publish("/card", jsonVal)
