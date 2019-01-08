var APIKey = "Example";                                                                                                    
var APIFormat = "https://api.openweathermap.org/data/2.5/weather?";                                                                               
var currentZip = "98203";                                                                                                                             
                                                                                                                                                      
function buildUrl (location) {                                                                                                                        
        var url = APIFormat + "q=" + location + ",us&appid="+APIKey;                                                                              
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
                'condition': jsonResult.weather[0].main.toLowerCase(),                                                                                
                'wind': windSpeed                                                                                                                     
            }                                                                                                                                         
                                                                                                                                                      
            return weatherObj;                                                                                                                        
        }                                                                                                                                             
        else {                                                                                                                                        
                return null;                                                                                                                          
        }                                                                                                                                             
}