var cardInfo = {
    id: -1,
    responseTopic: '/weatherCard_' + getEpochMillis(),
    // bgColor: 0xc44569,
    bgColor: 0x0,
    params: {
        location: 'Toronto, On',
        tempUnit: 'fahrenheit',
        distanceUnit: 'imperial',
        prevCalendarDay: -1,
        prevUpdate: 0,
        updateInterval: 15*60*1000 // 15 min
    }
}

// definitions for the program
var elementId = {
    weatherUnitIndicator: 0,
    weatherTemperature: 1,
    weatherMainImage: 2,
    date: 3,
    weatherParameterName: 4,
    weatherParameterValue: 5,
    weatherParameterUnits: 6,
    separator: 7,
    cover: 8
};

var weatherImg = {
    degree: "degree",
    percipitationIcon: "percipitation",

    partlyCloudy: "cloudy-2",
    partlyCloudyNight: "cloudy-night",
    cloudy: "cloudy",
    cloudyNight: "cloudy",
    rain: "rain",
    rainNight: "rain-night",
    windy: "windy",
    windyNight: "windy",
    tornado: "tornado",
    tornadoNight: "tornado",
    snow: "snowy",
    snowNight: "snowy",
    clear: "sunny",
    clearNight: "clear-night",
    thunderstorm: "storm",
    thunderstormNight: "storm",
    fog: "fog",
    fogNight: "fog",


    separator: "line",
    cover: "card_border"
};


function getFormattedDate () {
    var weekdays = [ "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

    var monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "June",
        "July", "Aug", "Sept", "Oct", "Nov", "Dec"
    ];

    var date = new Date();

    return {
        weekday: weekdays[date.getDay()],
        month: monthNames[date.getMonth()],
        day: date.getDate()
    };
}


function createCard () {
    var dateObj = getFormattedDate();
    var cardObj = generateNewCardObj(cardInfo.bgColor, cardInfo.responseTopic);

    // background border
    cardObj.elements.push(generateImageElement(
                            elementId.cover,
                            generateImgPath(imgRootPath, weatherImg['cover']),
                            0, 0)
                        );

    // temperature unit indicator and value
    // TODO: implement fahrenheit handling
    cardObj.elements.push(generateImageElement(
                            elementId.weatherUnitIndicator,
                            generateImgPath(imgRootPath, weatherImg['degree']),
                            178, 91)
                        );
    cardObj.elements.push(generateTextElement(
                            elementId.weatherTemperature,
                            '25',
                            82,
                            0, 79, 'center')
                        );

    // main weather image
    cardObj.elements.push(generateImageElement(
                            elementId.weatherMainImage,
                            generateImgPath(imgRootPath, weatherImg['clear']),
                            5, 5)
                        );
    // date
    cardObj.elements.push(generateTextElement(
                            elementId.date,
                            dateObj.weekday + ', ' + dateObj.month + ' ' + dateObj.day,
                            23,
                            0, 170, 'center')
                        );
    // weather parameter
    cardObj.elements.push(generateTextElement(
                            elementId.weatherParameterName,
                            'Wind',
                            50,
                            30, 209, 'left')
                        );
    cardObj.elements.push(generateTextElement(
                            elementId.weatherParameterValue,
                            '50',
                            50,
                            -64, 209, 'right')
                        );
    cardObj.elements.push(generateTextElement(
                            elementId.weatherParameterUnits,
                            'km/h',
                            23,
                            180, 233, 'left')
                        );
    // line separator
    cardObj.elements.push(generateImageElement(
                            elementId.separator,
                            generateImgPath(imgRootPath, weatherImg['separator']),
                            21, 196)
                        );

    // init the card
    initCard(JSON.stringify(cardObj), true);
}

function getImageName(condition,isNighttime) {
    if(isNighttime){
        return weatherImg[condition+"Night"];
    }
    return weatherImg[condition];
}


function updateWeather () {
    var updateObj = generateUpdateCardObj(cardInfo.id);
    var weather = getOpenWeather(cardInfo.params.location, cardInfo.params.tempUnit, cardInfo.params.distanceUnit);
    if (weather !== null) {
        updateObj.elements.push(generateElementUpdate(
                                    elementId.weatherTemperature,
                                    weather.temperature)
                                );
        updateObj.elements.push(generateElementUpdate(
                                    elementId.weatherParameterValue,
                                    weather.wind)
                                );
        updateObj.elements.push(generateElementUpdate(
                                    elementId.weatherParameterUnits,
                                    (cardInfo.params.distanceUnit === 'metric' ? 'km/h' : 'mph'))
                                );
        updateObj.elements.push(generateElementUpdate(
                                    elementId.weatherMainImage,
                                    generateImgPath(imgRootPath, getImageName(weather.condition,weather.isNight))
                                    )
                                )

        updateCard(JSON.stringify(updateObj));
        return true;
    }

    return false;
}

function updateDate () {
    var dateObj = getFormattedDate();

    // only update if the calendar day has changed
    if (cardInfo.params.prevCalendarDay !== dateObj.day) {
        var updateObj = generateUpdateCardObj(cardInfo.id);
        updateObj.elements.push(generateElementUpdate(
                                    elementId.date,
                                    dateObj.weekday + ', ' + dateObj.month + ' ' + dateObj.day)
                                );

        updateCard(JSON.stringify(updateObj));

        // update the prev day variable
        cardInfo.params.prevCalendarDay = dateObj.day;
    }
}

function readConfig() {
    readFile('/etc/config.json', '', function (err, data) {
        if (!err) {
            var config;
    	    try {
    	        config = JSON.parse(data);
    	    } catch(e) {
    	        print(e); // error in the above string!
    	        return null;
    	    }

    	    // apply the settings from the config file
    	    cardIdentifier  = 0;    // TODO: this is temporary
    	    cardInfo.params.location        = config.cards['0'].location || cardInfo.params.location;
    	    cardInfo.params.tempUnit        = config.cards['0'].tempUnit || cardInfo.params.tempUnit;
    	    cardInfo.params.distanceUnit    = config.cards['0'].distanceUnit || cardInfo.params.distanceUnit;
        }
        print('configuration: location = ' + cardInfo.params.location + '; temperature unit = ' + cardInfo.params.tempUnit + '; distance unit = ' + cardInfo.params.distanceUnit);
    });
}

function setup() {
    readConfig();

    connect('localhost', 1883, null, function () {
        subscribe('/cardResponse', function () {
            createCard();
        });
        subscribe('/config/update');
        // subscribe('/button');
        // subscribe('/gesture');
      },
      null,
      '/card',
      JSON.stringify({
        cmd: 'remove_card',
        cardName: cardInfo.responseTopic
      })
    );
}

function loop() {
    // return if card not initialized
    if (cardInfo.id < 0) return;

    // update weather in every  {{updateInterval}}
    if ((new Date - cardInfo.params.prevUpdate) > cardInfo.params.updateInterval) {
        if ( updateWeather() ){
            // reset time stamp if successful
            cardInfo.params.prevUpdate = new Date;
        } else {
            // check back in 1 minute
            cardInfo.params.prevUpdate = new Date - (cardInfo.params.updateInterval - 1 * 60 * 1000);
        }
    }

    // update date every loop
    updateDate();
}

function onInput(e) {
    if (typeof e.source !== 'undefined' && typeof e.payload !== 'undefined' ) {
        print('input! input source: ' + e.source + ', value: ' + e.payload);
    }
}

function onMessage(e) {
    if (typeof e.topic !== 'undefined' && typeof e.payload !== 'undefined' ) {
        print('message! topic: ' + e.topic + ', value: ' + e.payload);
        switch (e.topic) {
            case '/cardResponse':
                cardInfo = handleCardResponseMessage(cardInfo, e.payload);
                break;
            case '/config/update':
                readConfig();
                cardInfo.params.prevUpdate = 0; // force an update
                break;
            default:
                break;
        }
    }
}
