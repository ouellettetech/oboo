# Oboo Smart Clock
The Oboo Smart Clock was a [Kickstarter](https://www.kickstarter.com/projects/onion/oboo-smart-clock-wifi-connected-and-gesture-contro) project by The Onion Corporation that promised a device that marries a large format clock with a smart display powered by the Onion Omega2 IoT platform. Upon delivery, it was discovered that a number of basic functionality was broken and missing entirely. This repository will serve as a resource to help users get their units functioning properly.

## Enabling SSH
The easiest way to interface with the Oboo and make changes is through shell access, but unfortuantely, SSH is disabled. To enable SSH access, dropbear must be enabled and this can be done in a few ways.

### Enable SSH via Powershell Script
This is mostly for Windows users. Click [here](https://github.com/ouellettetech/oboo/blob/master/external-tools/enable-ssh.ps1) to download the script by [jcouctch](https://github.com/jcoutch). Make sure you are connected to the Oboo access point before running the script.

It's possible to run Powershell on Linux/Mac as well.

### Enable SSH via Web Calls
Using a tool such as [Postman](https://www.getpostman.com/), make sure you are connected to the Oboot access point and execute a POST command to `http://192.168.3.1/ubus` with the following body:

```
{"jsonrpc":"2.0","id":0,"method":"call","params":["00000000000000000000000000000000","session","login",{"username":"root","password":"uUhdKGPJw52c61gXDXfQQsRd"}]}
```

Pay attention to what's returned. You are looking for SessionID (labeled: `ubus_rpc_session`). Copy this value and send a new POST to the same address, with this body:

```
{"jsonrpc":"2.0","id":0,"method":"call","params":["SessionID","file","exec",{"command":"/bin/ln","params":["-s","/etc/init.d/dropbear","/etc/rc.d/S21dropbear"]}]}
```

Reboot your Oboo and you should be able to connect to it via it's IP with the root/password login.

## Weather
The weather card is broken because the Oboo was using a public Yahoo Weather API that was decomissioned on January 3, 2019. Replace the yahooWeather.js file in `/usr/bin/js` with the contents of [this](https://github.com/ouellettetech/oboo/blob/master/usr/bin/js/openWeather.js) file. Then edit weather.js and change the call from `getYahooWeather` to `getOpenWeather`

## Fixing the Battery Indicator
Open `/usr/bin/js/mcu.js` and change:

```
var batteryVoltage = detectedVoltage * 1.25
```

to:
```
var batteryVoltage = detectedVoltage * 1.49
```

## Updating the AP wireless password
The default wireless password for the Oboo is `123456789`. This is unsecure but you can update it by editing `/etc/config/wireless`

## Enabling Bluetooth Audio
Bluetooth should already be enabled for Kickstarter backers but if it's not, just execute `gpioctl dirout-high 3`. If you see this setting is not persisting between reboots, please add `gpioctl dirout-high 3` to `/etc/rc.local`. See [more](https://getoboo.com/community/topic/enable-bluetooth-audio-on-oboo/).

## Reseting the System (In case you make a mistake)
/sbin/firstboot -y

## Miscellaneous Links
* [Gitter Chat](https://gitter.im/oboo-development/community)
* [Updating the firmware with SSH certificate bypass](https://getoboo.com/community/topic/update-issues-and-workarounds/)
* [Image converter to change PNG to BIN](https://getoboo.com/image-converter/)
* [Repository of firmware and files](https://getoboo.com/image-converter/)
* [External USB Root Filesystem (More space)](https://openwrt.org/docs/guide-user/additional-software/extroot_configuration)
* [Oboo Setting to enable ssh] (http://setup.getoboo.com/?dev=1#/welcome)
