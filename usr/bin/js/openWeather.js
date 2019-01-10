var APIKey = "Example";               

//
// Has to be saved as yahooWeather.js for now, until someone figures out how to import in their runtime.
// Also you need to edit the weather.js to change getYahooWeather to   getOpenWeather
// And get an api key from : https://openweathermap.org/price (free one should be fine.)   
                                                                                
var APIFormat = "https://api.openweathermap.org/data/2.5/weather?";

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

            var weather = "";
            switch (jsonResult.weather[0].id){
                case (jsonResult.weather[0].id < 300):
                    weather='thunderstorm';
                    break;
                case (jsonResult.weather[0].id < 600):
                    weather='rain';
                    break;
                case (jsonResult.weather[0].id < 700):
                    weather='snow';
                    break;
                case (jsonResult.weather[0].id < 781):
                    weather='fog';
                    break;
                case (jsonResult.weather[0].id < 800):
                    weather='tornado';
                    break;
                default:
                    if(jsonResult.wind.speed>20){
                        weather='windy';
                    } else {
                        switch(jsonResult.weather[0].id){
                            case (jsonResult.weather[0].id===800):
                                weather='clear';
                                break;
                            case (jsonResult.weather[0].id<802):
                                weather='partlycloudy';
                                break;
                            default:
                                weather='cloudy';
                                break;
                        }
                    }
                    break;
            }

            var weatherObj = {
                'temperature': tempVal,
                'condition': weather,
                'wind': windSpeed
            }

            return weatherObj;
        }
        else {
                return null;
        }
}
