var APIKey = "example";

//
// Has to be saved as yahooWeather.js for now, until someone figures out how to import in their runtime.
// Also you need to edit the weather.js to change getYahooWeather to   getOpenWeather
// And get an api key from : https://openweathermap.org/price (free one should be fine.)

var APIFormat = "https://api.openweathermap.org/data/2.5/weather?";

// Set what you consider to be windy, in mph
var windyConditions = 20;

function buildUrl(location) {
    var url = APIFormat + "q=" + encodeURIComponent(location) + "&appid=" + APIKey;
    return url;
}

function getOpenWeather(location, tempUnit, distanceUnit) {
    print('getting openweathermap weather');

    var result = httpRequest({
        method: 'GET',
        url: buildUrl(location)
    });

    if (result) {
        var jsonResult;
        try {
            jsonResult = JSON.parse(result);
        } catch (e) {
            print(e); // error in the above string!
            print(result);
            return null;
        }

        // special case where there is a mismatch between temperature and distance units
        var tempVal = jsonResult.main.temp;
        if (tempUnit === 'fahrenheit' || tempUnit === 'imperial') {
            tempVal = Math.round((1.8 * (tempVal - 273)) + 32);
        } else {
            tempVal = tempVal - 273.15;

        }
        var windSpeed = jsonResult.wind.speed;
        print(windSpeed);
        if (distanceUnit === 'metric') {
            // convert from meters per a second to kilometers per an hour
            windSpeed = Math.round(windSpeed * 3.6);
        }
        else {
            // convert metric wind speed to imperial
            windSpeed = Math.round(windSpeed * 2.23694);
        }

        var weather = "";
        if (jsonResult.weather[0].id < 300) {
            weather = 'thunderstorm';
        }
        else if (jsonResult.weather[0].id < 600) {
            weather = 'rain';
        }
        else if (jsonResult.weather[0].id < 700) {
            weather = 'snow';
        }
        else if (jsonResult.weather[0].id < 781) {
            weather = 'fog';
        }
        else if (jsonResult.weather[0].id < 800) {
            weather = 'tornado';
        }
        else if (jsonResult.wind.speed > windyConditions) {
            weather = 'windy';
        }
        else if (jsonResult.weather[0].id == 800) {
            weather = 'clear';
        }
        else if (jsonResult.weather[0].id < 802) {
            weather = 'partlycloudy';
        }
        else {
            weather = 'cloudy';
        }
        //Solve for nighttime by checking to see if current time is not between sunrise and sunset
        var datenow = new Date();
        var timenow = Math.floor(datenow.getTime() / 1000);
        var isNight = (timenow < jsonResult.sys.sunrise || timenow > jsonResult.sys.sunset);
        //Create the return weather object
        var weatherObj = {
            'temperature': tempVal,
            'condition': weather,
            'wind': windSpeed,
            'isNight': isNight
        }
        return weatherObj;
    }
    else {
        return null;
    }
}
