#!/bin/bash
set -ex

echo 'NOTE: Make sure you are connected to the Oboo access point before running this script!'
echo "Also, this script requires curl and jq.  Make sure they're installed before executing."

# Factory root password for Oboo
# (can be ascertained from setup.getoboo.com, under webpack///.src/api/ubus.js in the debugger console under Sources)
factoryRootUser="root"
factoryRootPassword="uUhdKGPJw52c61gXDXfQQsRd"
#factoryRootPassword="onioneer"  # Onion Omega default root password
defaultIpAddress='192.168.3.1'

# Get the IP address from the user
read -erp "Enter the IP address of your Oboo clock (default $defaultIpAddress)" ipAddr
if [ -z $ipAddr ]; then
    ipAddr=$defaultIpAddress
fi

# Make a call to the API to verify the device is present
versionInfo=$(curl -X GET -H "Content-Type:application/json" "http://$ipAddr/cgi-bin/ver")
deviceName=$(echo "$versionInfo"|jq '.device_name')
if [ -z $deviceName ]; then
    echo "Oboo device did not respond to /cgi-bin/ver with expected response!  Make sure it's connected to wi-fi, and you can ping the IP address."
    exit
fi
echo "Found $deviceName!"

# Authenticate via ubus's JSON RPC endpoint
# https://www.jsonrpc.org/specification
# https://openwrt.org/docs/techref/ubus
token="00000000000000000000000000000000"
ubusUrl="http://$ipAddr/ubus"
get_token()
{
  cat <<EOF
{
    "jsonrpc": "2.0",
    "id": 0,
    "method": "call",
    "params": [
        "$token",
        "session",
        "login",
        {
            "username": "$factoryRootUser",
            "password": "$factoryRootPassword"
        }
    ]
}
EOF
}
sessionInfo=$(curl -X POST -H "Content-Type:application/json" -d "$(get_token)" "$ubusUrl")
newtoken=$(echo "$sessionInfo"|jq '.result[1].ubus_rpc_session')
if [ -z $newtoken ]; then
    echo "UBus session was not acquired!  This possibly means the root password is invalid."
    echo "Debugging output:"
    echo "$sessionInfo"
    exit
fi

# Now that we have an authenticated session, execute the command to enable SSH at boot
echo "Enabling SSH at boot time..."
enable_ssh()
{
  cat <<EOF
{
    "jsonrpc": "2.0",
    "id": 0,
    "method": "call",
    "params": [
        $newtoken,
        "file",
        "exec",
        {
            "command": "/etc/init.d/dropbear",
            "params": ["enable"]
        }
    ]
}
EOF
}
result=$(curl -X POST -H "Content-Type:application/json" -d "$(enable_ssh)" "$ubusUrl")
stdout=$(echo "$result"|jq '.result[1].stdout')
echo $result
if [ -z $stdout ]; then
    echo "Error executing: /etc/init.d/dropbear enable"
    exit
fi


# Who wants to wait for a reboot to access SSH?  Not me!  So, start up the SSH service!
echo "Starting SSH service..."
start_ssh()
{
  cat <<EOF
{
    "jsonrpc": "2.0",
    "id": 0,
    "method": "call",
    "params": [
        $newtoken,
        "file",
        "exec",
        {
            "command": "/etc/init.d/dropbear",
            "params": ["start"]
        }
    ]
}
EOF
}
result=$(curl -X POST -H "Content-Type:application/json" -d "$(start_ssh)" "$ubusUrl")
stdout=$(echo "$result"|jq '.result[1].stdout')
echo $result
if [ -z $stdout ]; then
    echo "Error executing: /etc/init.d/dropbear start"
    exit
fi

# We're done!  Output the default credentials to the console so the user can log in
echo "SSH has been enabled on the Oboo!  Use the following credentials for initial login:"
echo
echo "IP Address: $ipAddr"
echo "User: $factoryRootUser"
echo "Password: $factoryRootPassword"
echo
