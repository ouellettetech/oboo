import paho.mqtt.client as mqtt
import json
import time
import datetime
from datetime import date
from datetime import timedelta
import calendar
import openWeather as weatherApi


class ComplexEncoder(json.JSONEncoder):
    def default(self, o): # pylint: disable=E0202
        if hasattr(o,'reprJSON'):
            return o.reprJSON()
        else:
            return json.JSONEncoder.default(self, o)


class WeatherElementIds:
  weatherUnitIndicator = 0
  weatherTemperature = 1
  weatherMainImage = 2
  date = 3
  weatherParameterName = 4
  weatherParameterValue = 5
  weatherParameterUnits = 6
  separator = 7
  cover = 8

imgRootPath = '/usr/bin/img/'

weatherImg = {
    'degree': "degree",
    'percipitationIcon': "percipitation",

    'partlyCloudy': "cloudy-2",
    'partlyCloudyNight': "cloudy-night",
    'cloudy': "cloudy",
    'cloudyNight': "cloudy",
    'rain': "rain",
    'rainNight': "rain-night",
    'windy': "windy",
    'windyNight': "windy",
    'tornado': "tornado",
    'tornadoNight': "tornado",
    'snow': "snowy",
    'snowNight': "snowy",
    'clear': "sunny",
    'clearNight': "clear-night",
    'thunderstorm': "storm",
    'thunderstormNight': "storm",
    'fog': "fog",
    'fogNight': "fog",


    'separator': "line",
    'cover': "card_border"
}

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

def readConfig():
    print ('Reading config file')
    global curCard
    with open('/etc/config.json') as data_file:
        data = json.load(data_file)
        print('printing datajson')
        print(data['cards']['0'])
        if (data != None):
            if(data['cards'] != None):
                if(data['cards']['0'] != None):
                    print(data['cards']['0']['location'])
                    # apply the settings from the config file
                    if( data['cards']['0']['location']):
                        curCard.location = data['cards']['0']['location']
                    if (data['cards']['0']['tempUnit']):
                        curCard.tempUnit = data['cards']['0']['tempUnit']
                    if (data['cards']['0']['distanceUnit']):
                        curCard.distanceUnit = data['cards']['0']['distanceUnit']
                    print('configuration: location = ' + curCard.location + '; temperature unit = ' + curCard.tempUnit + '; distance unit = ' + curCard.distanceUnit)

def resetPrevUpdate(): # force an update
    global curCard
    curCard.prevUpdate = datetime.datetime.now() - timedelta(days=0, seconds=0, microseconds=0, milliseconds=0, minutes=16, hours=0, weeks=0)
    print ('reseting to previous update')

class CardObj:
  def __init__(self, bgColor, responseTopic, command):
      self.bg_color = bgColor
      self.responseTopic = responseTopic
      self.elements = []
      self.command = command
      self.nightlight = 0
      self.id = -1
      self.updateInterval = timedelta(days=0, seconds=0, microseconds=0, milliseconds=0, minutes=15, hours=0, weeks=0) # 15 min
      self.prevUpdate = datetime.datetime.now() - self.updateInterval
      self.prevCalendarDay = -1
  def reprJSON(self):
      return dict(cmd=self.command, bg_color=self.bg_color, responseTopic=self.responseTopic, elements=self.elements) 

class UpdateCardObj:
  def __init__(self, cardId):
      self.command = 'update_card'
      self.id = cardId
      self.elements = []
  def reprJSON(self):
      return dict(cmd=self.command, id=self.id, elements=self.elements) 

curCard = None

def generateImgPath(path, image):
    return path + 'img_' + image + '.bin'

def getImageName(condition,isNighttime):
    if(isNighttime):
        return weatherImg[condition+"Night"]
    return weatherImg[condition]

def on_connect(mqttc, obj, flags, rc):
    print("rc: " + str(rc))


def on_message(mqttc, obj, msg):
    try:
        global curCard
        #"{\"cardId\":5,\"attention\":\"/myCard_1111114805188\",\"action\":\"create\",\"success\":true}"
        print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
        json.loads(msg.payload)
        
        topic=msg.topic
        decodedString=str(msg.payload.decode("utf-8","ignore"))
        print("data Received type",type(decodedString))
        print("data Received",decodedString)
        respObj = decodeResponse(decodedString)
        print("after decode")
        print("Topic: "+topic)
        if (topic == '/cardResponse'):
            print("topic matches")
            print(type(respObj))
            for key in respObj:
                print('Contains key: {0}, with value {1} '.format(key, respObj[key]))
            print("after prints")
            updateCardInfo(mqttc, curCard, respObj)
        else: 
            print('topic ['+topic+'] doent equal [/cardResponse]')
        if (topic == '/config/update'):
            readConfig()
            resetPrevUpdate() # force an update
    except Exception as e:
        print("Unexpected Execption"+e)
    except:
        print("Unexpected error:")
        raise

def on_publish(mqttc, obj, mid):
    print("mid: " + str(mid))


def on_subscribe(mqttc, obj, mid, granted_qos):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))

def on_log(mqttc, obj, level, string):
    print(string)

def createCard(mqttc):
    global curCard
    curCard = CardObj(0x0,'/weatherCard_' + str(int(round(time.time() * 1000))), 'new_card')

    # background border
    curCard.elements.append(Element.generateImageElement(
        WeatherElementIds.cover, 
        generateImgPath(imgRootPath, weatherImg['cover']),
         0, 0 ))

    # temperature unit indicator and value
    curCard.elements.append(Element.generateImageElement(
        WeatherElementIds.weatherUnitIndicator, 
        generateImgPath(imgRootPath, weatherImg['degree']),
        178, 91 ))

    # Weather Temperature
    curCard.elements.append(Element.generateTextElement(
        WeatherElementIds.weatherTemperature, 
        '25',
        82, 0, 79, 'center' ))
        
    # main weather image
    curCard.elements.append(Element.generateImageElement(
        WeatherElementIds.weatherMainImage,
        generateImgPath(imgRootPath, weatherImg['clear']),
        5, 5 ))
    
    # date
    curDate = date.today()
    weekDay = calendar.day_name[curDate.weekday()]
    month = calendar.month_abbr[curDate.month]
    curCard.elements.append(Element.generateTextElement(
        WeatherElementIds.date,
        weekDay + ', ' + month + ' ' + str(curDate.day),
        23, 0, 170, 'center'))

    # weather parameter
    curCard.elements.append(Element.generateTextElement(
        WeatherElementIds.weatherParameterName,
        'Wind',
        50, 30, 209, 'left'))
    
    # weather parameter Value
    curCard.elements.append(Element.generateTextElement(
        WeatherElementIds.weatherParameterValue,
        '50',
        50, -64, 209, 'right'))
    
    # Parameter Units
    curCard.elements.append(Element.generateTextElement(
        WeatherElementIds.weatherParameterUnits,
        'km/h',
        23, 180, 233, 'left'))
    
    # line separator
    curCard.elements.append(Element.generateImageElement(
        WeatherElementIds.separator,
        generateImgPath(imgRootPath, weatherImg['separator']),
        21, 196))
    
    curCard.command = 'new_card'

    print("Full JSON")
    jsonVal = json.dumps(curCard.reprJSON(), cls=ComplexEncoder)
    print(jsonVal)
    mqttc.publish("/card", jsonVal)


def updateCard(mqttc, cardJson):
    print('updateing Card')
    mqttc.publish("/card", cardJson)

def updateWeather(mqttc):
    print('running updagte weather')
    global curCard
    print('Updating Card: {0}'.format(curCard.id))
    updateObj = UpdateCardObj(curCard.id)
    weatherObj = weatherApi.getOpenWeather(curCard.location, curCard.tempUnit, curCard.distanceUnit)
    if (weatherObj != None and updateObj.id > 0):
        print('Using Update Obj: {0}'.format(updateObj.id))
        updateObj.elements.append(Element.generateElementUpdate(
            WeatherElementIds.weatherTemperature,
            weatherObj["temperature"]))
        updateObj.elements.append(Element.generateElementUpdate(
            WeatherElementIds.weatherParameterValue,
            weatherObj["wind"]))
        updateObj.elements.append(Element.generateElementUpdate(
            WeatherElementIds.weatherParameterUnits,
            ('km/h' if (curCard.distanceUnit == 'metric') else 'mph')))
        updateObj.elements.append(Element.generateElementUpdate(
            WeatherElementIds.weatherMainImage,
            generateImgPath(imgRootPath, getImageName(weatherObj["condition"], weatherObj["isNight"]))))
        jsonVal = json.dumps(updateObj.reprJSON(), cls=ComplexEncoder)
        print(jsonVal)
        updateCard(mqttc, jsonVal)
        return True
    print('Update Not ready will retry in 1 min...')
    return False
    
def updateDate(mqttc):
    global curCard
    curDate = date.today()
    weekDay = calendar.day_name[curDate.weekday()]
    month = calendar.month_abbr[curDate.month]
    if (curCard.prevCalendarDay != curDate.day and curCard.id > 0):
        print('Updating Card: {0}'.format(curCard.id))
        updateObj = UpdateCardObj(curCard.id)
        updateObj.elements.append(Element.generateElementUpdate(
            WeatherElementIds.date,
            weekDay + ', ' + month + ' ' + str(curDate.day)))
        # update the prev day variable
        curCard.prevCalendarDay = curDate.day
        jsonVal = json.dumps(updateObj.reprJSON(), cls=ComplexEncoder)
        print(jsonVal)
        updateCard(mqttc, jsonVal)

# If you want to use a specific client id, use
# mqttc = mqtt.Client("client-id")
# but note that the client id must be unique on the broker. Leaving the client
# id parameter empty will generate a random id for you.
mqttc = mqtt.Client()
mqttc.on_message = on_message
mqttc.on_connect = on_connect
mqttc.on_publish = on_publish
mqttc.on_subscribe = on_subscribe
# Uncomment to enable debug messages
mqttc.on_log = on_log
mqttc.connect("localhost", 1883, 60)
mqttc.subscribe("/cardResponse",0)
mqttc.subscribe('/config/update',0)
createCard(mqttc)
readConfig()

while True:
    #global curCard
    #print("Current Card: " + curCard)
    mqttc.loop(.1) #blocks for 100ms
    #print('running mqttc loop')
    # Only run if card info is setup.
    if (curCard != None and curCard.id > 0):
        # update weather in every  {{updateInterval}}
        if ((datetime.datetime.now() - curCard.prevUpdate) > curCard.updateInterval):
            print("updating weather")
            if (updateWeather(mqttc)):
                # reset time stamp if successful
                curCard.prevUpdate = datetime.datetime.now()
            else:
                # check back in 1 minute
                curCard.prevUpdate = datetime.datetime.now() - (curCard.updateInterval + timedelta(days=0, seconds=0, microseconds=0, milliseconds=0, minutes=60, hours=0, weeks=0) )
    # update date every loop
    updateDate(mqttc)
