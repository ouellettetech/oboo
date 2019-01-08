var APIKey = "Example";               
//
// Has to be saved as yahooWeather.js for now, until someone figures out how to import in their runtime.
// Also you need to edit the weather.js to change getYahooWeather to   getOpenWeather
// And get an api key from : https://openweathermap.org/price (free one should be fine.)   
                                                                                
var APIFormat = "https://api.openweathermap.org/data/2.5/weather?";
var weatherConditions =
{
    "Thunderstorm":'rain',
    "Drizzle":'rain',
    "Rain":'rain',
    "Snow":'snow',
    "Atmosphere":'partlyCloudy',
    "Clear":'sunny',
    "Clouds":'cloudy'
}
function buildUrl (location) {
        var url = APIFormat + "q=" + encodeURIComponent(location) + "&appid="+APIKey;
        return url;
}

function getOpenWeather (location, tempUnit, distanceUnit) {
    print('getting openweathermap weather');
    var result = httpRequest({
        method: 'GET',
        url: buildUrl(location)
    });

        if (result) {
            var jsonResult;
            try {
                jsonResult = JSON.parse(result);
            } catch(e) {
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
                if( distanceUnit !== 'metric') {
                        // convert metric wind speed to imperial
                        windSpeed = Math.round(windSpeed * (1/1.609344));
            }

            var weatherObj = {
                'temperature': tempVal,
                'condition': weatherConditions[jsonResult.weather[0].main],
                'wind': windSpeed
            }

            return weatherObj;
        }
        else {
                return null;
        }
}