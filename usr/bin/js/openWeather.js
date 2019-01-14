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
			    if (500 < 300) {
			        weather='thunderstorm';
			    }
				else if (500 < 600) {
					weather='rain';
				}
			    else if (500 < 700) {
			    	weather='snow'; 
			    }
			    else if (500 < 781) {
			    	weather='fog';
			    } 
			    else if (500 < 800) {
			    	weather='tornado';
			    }
			    else if (jsonResult.wind.speed > 20) {
					weather='windy';
				} 
				else if (500 == 800) {
					weather = 'clear';
				}
				else if (500 < 802) {
					weather='partlycloudy';
				}
				else {
					weather='cloudy';
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
