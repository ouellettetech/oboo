# This script is written in PowerShell (for Windows users), but I tried to document it as best
# as I could so someone with shell script experience can create one that uses curl

$ErrorActionPreference = 'Stop'

Write-Host -ForegroundColor Yellow 'NOTE: Make sure you are connected to the Oboo access point before running this script!'

# Factory root password for Oboo
# (can be ascertained from setup.getoboo.com, under webpack///.src/api/ubus.js in the debugger console under Sources)
$factoryRootUser = 'root'
$factoryRootPassword = 'uUhdKGPJw52c61gXDXfQQsRd'
#$factoryRootPassword = 'onioneer'  # Onion Omega default root password
$defaultIpAddress = '192.168.3.1'

# Get the IP address from the user
$ipAddr = Read-Host -Prompt "Enter the IP address of your Oboo clock (default $defaultIpAddress)"
if ([string]::IsNullOrWhiteSpace($ipAddr)) {
    $ipAddr = $defaultIpAddress
}

# Make a call to the API to verify the device is present
$versionInfo = Invoke-RestMethod "http://$ipaddr/cgi-bin/ver" -ErrorAction Continue
if (-not $versionInfo.device_name) {
    Write-Error "Oboo device did not respond to /cgi-bin/ver with expected response!  Make sure it's connected to wi-fi, and you can ping the IP address."
    return
}
Write-Host -ForegroundColor Green "Found ${$versionInfo.device_name}!"

# Authenticate via ubus's JSON RPC endpoint
# I'm using PowerShell's built-in JSON serialization in case the password has characters that need to be encoded
# https://www.jsonrpc.org/specification
# https://openwrt.org/docs/techref/ubus
$token = '00000000000000000000000000000000'
$ubusUrl = "http://$ipAddr/ubus"
$payload = @{
    jsonrpc = '2.0';
    id = 0;
    method = 'call';
    params = @(
        $token,
        'session',
        'login',
        @{
            username = $factoryRootUser
            password = $factoryRootPassword
        }
    );
} | ConvertTo-Json
$sessionInfo = Invoke-RestMethod $ubusUrl -Method Post -Body $payload -ContentType 'application/json' -ErrorAction Continue

if (-not $sessionInfo.result.ubus_rpc_session) {
    Write-Error "UBus session was not acquired!  This possibly means the root password is invalid."
    Write-Host "Debugging output:"
    $sessionInfo
    return
}
$token = $sessionInfo.result.ubus_rpc_session


# Now that we have an authenticated session, execute the command to enable SSH at boot
Write-Host "Enabling SSH at boot time..."
$payload = @"
{
    'jsonrpc': '2.0',
    'id': 0,
    'method': 'call',
    'params': [
        '$token',
        'file',
        'exec',
        {
            'command': '/etc/init.d/dropbear',
            'params': ['enable']
        }
    ]
}
"@
$result = Invoke-RestMethod $ubusUrl -Method Post -Body $payload -ContentType 'application/json'
Write-Host ($result | ConvertTo-Json -Compress)
if ($result.result.stdout) {
    Write-Error "Error executing: /etc/init.d/dropbear enable"
    return
}


# Who wants to wait for a reboot to access SSH?  Not me!  So, start up the SSH service!
Write-Host "Starting SSH service..."
$payload = @"
{
    'jsonrpc': '2.0',
    'id': 0,
    'method': 'call',
    'params': [
        '$token',
        'file',
        'exec',
        {
            'command': '/etc/init.d/dropbear',
            'params': ['start']
        }
    ]
}
"@
$result = Invoke-RestMethod $ubusUrl -Method Post -Body $payload -ContentType 'application/json'
Write-Host ($result | ConvertTo-Json -Compress)
if ($result.result.stdout) {
    Write-Error "Error executing: /etc/init.d/dropbear start"
    return
}


# We're done!  Output the default credentials to the console so the user can log in
Write-Host -ForegroundColor Green "SSH has been enabled on the Oboo!  Use the following credentials for initial login:"
Write-Host
Write-Host "IP Address: $ipAddr"
Write-Host "User: $factoryRootUser"
Write-Host "Password: $factoryRootPassword"
Write-Host