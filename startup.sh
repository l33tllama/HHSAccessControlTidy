#!/bin/sh
# Runs from /etc/rc.local
runuser -l pi -c 'cd /home/pi/HHSAccessControlTidy; screen -dmS doorman python /home/pi/HHSAccessControl/main.py'
