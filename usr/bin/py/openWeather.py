import json
import urllib.request
from datetime import timezone
import datetime
import time
import urllib
import urllib.request, json 

def utc_to_local(utc_dt):
    return datetime.datetime.fromtimestamp(utc_dt / 1e3)
#
# get an API key from : https://openweathermap.org/price (free one should be fine.)   
# store the API key in either /etc/config.json as part of the weather card object.

APIFormat = "https://api.openweathermap.org/data/2.5/weather?"

# Set what you consider to be windy, in mps http://gyre.umeoce.maine.edu/data/gomoos/buoy/php/variable_description.php?variable=wind_2_speed
# 11 is considered a strong breeze.
windyConditions = 11 

def getApiKey():
    with open('/etc/config.json') as data_file:
        data = json.load(data_file)
        if (data != None):
            if(data['cards'] != None):
                if(data['cards']['0'] != None):
                    if( data['cards']['0']['apiKey']):
                        return data['cards']['0']['apiKey']
    return 'example'

def buildUrl(location, APIKey):
    params = { 'q' : location, 'appid' : APIKey}
    url = APIFormat + urllib.parse.urlencode(params)
    print('Getting Url:'+url)
    return url

def getOpenWeather (location, tempUnit, distanceUnit):
    print('getting openweathermap weather')
    with urllib.request.urlopen(buildUrl(location, getApiKey()))  as url:
        jsonResult = json.loads(url.read().decode())
        print(jsonResult)
        tempVal = jsonResult["main"]["temp"]
        # special case where there is a mismatch between temperature and distance units
        tempVal = jsonResult["main"]["temp"]
        if (tempUnit == 'fahrenheit' or tempUnit == 'imperial'):
            tempVal = int(round(1.8 * (tempVal - 273) + 32))
        else:
            tempVal = tempVal - 273.15
        windSpeed = jsonResult["wind"]["speed"]
        print('Current Wind Speed :'+ str(windSpeed))
        if (distanceUnit == 'metric'):
            #convert from meters per a second to kilometers per an hour
            windSpeed = int(round(windSpeed * 3.6))
        else:
            # convert metric wind speed to imperial
            windSpeed = int(round(windSpeed * 2.23694))
        
        weather = ""
        if (jsonResult["weather"][0]["id"] < 300):
            weather = 'thunderstorm'
        elif (jsonResult["weather"][0]["id"] < 600):
            weather = 'rain'
        elif (jsonResult["weather"][0]["id"] < 700):
            weather = 'snow'
        elif (jsonResult["weather"][0]["id"] < 781):
            weather = 'fog'
        elif (jsonResult["weather"][0]["id"] < 800):
            weather = 'tornado'
        elif (jsonResult["wind"]["speed"] > windyConditions):
            weather = 'windy'
        elif (jsonResult["weather"][0]["id"] == 800):
            weather = 'clear'
        elif (jsonResult["weather"][0]["id"] < 802):
            weather = 'partlycloudy'
        else:
            weather = 'cloudy'
        #Solve for nighttime by checking to see if current time is not between sunrise and sunset
        sunrise = utc_to_local(jsonResult["sys"]["sunrise"])
        sunset = utc_to_local(jsonResult["sys"]["sunset"])
        curTime = datetime.datetime.today()
        print(type(sunrise))
        print(type(curTime))
        isNight = (curTime < sunrise or curTime >= sunset)
        #Create the return weather object
        weatherObj = {
            'temperature': tempVal,
            'condition': weather,
            'wind': windSpeed,
            'isNight': isNight
        }
        return weatherObj
    return None
