import json
import time
import datetime
from datetime import date
from datetime import timedelta
import calendar
import openWeather as weatherApi
import mqttcCardSetup
import cardLib
import atexit

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

curCard = None
gmqttc = None

def getImageName(condition,isNighttime):
    if(isNighttime):
        return weatherImg[condition+"Night"]
    return weatherImg[condition]

def on_connect(mqttc, obj, flags, rc):
    print("rc: " + str(rc))


def on_message(mqttc, obj, msg):
    try:
        global curCard
        print('Starting on message')
        print(msg)
        #"{\"cardId\":5,\"attention\":\"/myCard_1111114805188\",\"action\":\"create\",\"success\":true}"
        print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
        json.loads(msg.payload)
        
        topic=msg.topic
        decodedString=str(msg.payload.decode("utf-8","ignore"))
        print("data Received type",type(decodedString))
        respObj = cardLib.decodeResponse(decodedString)
        print("after decode")
        print("data Received",respObj)
        print("Topic: "+topic)
        if (topic == '/cardResponse'):
            print("topic matches")
            print(type(respObj))
            for key in respObj:
                print('Contains key: {0}, with value {1} '.format(key, respObj[key]))
            print("after prints")
            cardLib.updateCardInfo(mqttc, curCard, respObj)
            global gmqttc
            gmqttc = mqttc
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
    f=open("/tmp/weatherError.txt", "a+")
    f.write('Error: {0}'.format(string))
    f.close()

def createCard(mqttc):
    global curCard
    curCard = cardLib.CardObj(0x0,'/weatherCard_' + str(int(round(time.time() * 1000))), 'new_card')

    curCard.updateInterval = timedelta(days=0, seconds=0, microseconds=0, milliseconds=0, minutes=15, hours=0, weeks=0) # 15 min
    curCard.prevUpdate = datetime.datetime.now() - curCard.updateInterval
    curCard.prevCalendarDay = -1

    # background border
    curCard.elements.append(cardLib.Element.generateImageElement(
        WeatherElementIds.cover, 
        cardLib.generateImgPath(cardLib.imgRootPath, weatherImg['cover']),
         0, 0 ))

    # temperature unit indicator and value
    curCard.elements.append(cardLib.Element.generateImageElement(
        WeatherElementIds.weatherUnitIndicator, 
        cardLib.generateImgPath(cardLib.imgRootPath, weatherImg['degree']),
        178, 91 ))

    # Weather Temperature
    curCard.elements.append(cardLib.Element.generateTextElement(
        WeatherElementIds.weatherTemperature, 
        '25',
        82, 0, 79, 'center' ))
        
    # main weather image
    curCard.elements.append(cardLib.Element.generateImageElement(
        WeatherElementIds.weatherMainImage,
        cardLib.generateImgPath(cardLib.imgRootPath, weatherImg['clear']),
        5, 5 ))
    
    # date
    curDate = date.today()
    weekDay = calendar.day_name[curDate.weekday()]
    month = calendar.month_abbr[curDate.month]
    curCard.elements.append(cardLib.Element.generateTextElement(
        WeatherElementIds.date,
        weekDay + ', ' + month + ' ' + str(curDate.day),
        23, 0, 170, 'center'))

    # weather parameter
    curCard.elements.append(cardLib.Element.generateTextElement(
        WeatherElementIds.weatherParameterName,
        'Wind',
        50, 30, 209, 'left'))
    
    # weather parameter Value
    curCard.elements.append(cardLib.Element.generateTextElement(
        WeatherElementIds.weatherParameterValue,
        '50',
        50, -64, 209, 'right'))
    
    # Parameter Units
    curCard.elements.append(cardLib.Element.generateTextElement(
        WeatherElementIds.weatherParameterUnits,
        'km/h',
        23, 180, 233, 'left'))
    
    # line separator
    curCard.elements.append(cardLib.Element.generateImageElement(
        WeatherElementIds.separator,
        cardLib.generateImgPath(cardLib.imgRootPath, weatherImg['separator']),
        21, 196))
    
    curCard.command = 'new_card'

    print("Full JSON")
    jsonVal = json.dumps(curCard.reprJSON(), cls=cardLib.ComplexEncoder)
    print(jsonVal)
    mqttc.publish("/card", jsonVal)


def updateWeather(mqttc):
    print('running updagte weather')
    global curCard
    print('Updating Card: {0}'.format(curCard.id))
    updateObj = cardLib.UpdateCardObj(curCard.id)
    weatherObj = weatherApi.getOpenWeather(curCard.location, curCard.tempUnit, curCard.distanceUnit)
    if (weatherObj != None and updateObj.id > 0):
        print('Using Update Obj: {0}'.format(updateObj.id))
        updateObj.elements.append(cardLib.Element.generateElementUpdate(
            WeatherElementIds.weatherTemperature,
            weatherObj["temperature"]))
        updateObj.elements.append(cardLib.Element.generateElementUpdate(
            WeatherElementIds.weatherParameterValue,
            weatherObj["wind"]))
        updateObj.elements.append(cardLib.Element.generateElementUpdate(
            WeatherElementIds.weatherParameterUnits,
            ('km/h' if (curCard.distanceUnit == 'metric') else 'mph')))
        updateObj.elements.append(cardLib.Element.generateElementUpdate(
            WeatherElementIds.weatherMainImage,
            cardLib.generateImgPath(cardLib.imgRootPath, getImageName(weatherObj["condition"], weatherObj["isNight"]))))
        cardLib.updateCard(mqttc, updateObj)
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
        updateObj = cardLib.UpdateCardObj(curCard.id)
        updateObj.elements.append(cardLib.Element.generateElementUpdate(
            WeatherElementIds.date,
            weekDay + ', ' + month + ' ' + str(curDate.day)))
        # update the prev day variable
        curCard.prevCalendarDay = curDate.day
        cardLib.updateCard(mqttc, updateObj)

def exit_handler():
    global curCard
    global gmqttc
    print('My application is ending!')
    cardLib.removeCard(gmqttc, curCard)
    #remove_card

atexit.register(exit_handler)

def mainLoop(mqttc):
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

mqttcCardSetup.mqttcSetup(on_message, on_connect, on_publish, on_subscribe, on_log, createCard, readConfig, mainLoop)