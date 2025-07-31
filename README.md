This is a simple script to send a push notification to my phone when my washer or dryer has finished it's cycle. It arms when it detects sustained high-power usage and then disarms and sends the notifications when the power is low for 3 minutes.

I may work on this more so it sets itself up more completely and other people can use it more easily, but for now, this version works for my setup. If you'd like to set this up for youself, the below information may be useful to you:

The script works with Tapo P110 and P110M smart plugs and uses Pushover to send the push notifications. It also requires the smart plugs to be given a reserved IP address. Some washers and dryers may sit idle during the cycle for long enough to trick the sensor into sending a false positive.

I have this installed on a Raspberry Pi Zero 2, running Debian Bookworm in a headless setup. It runs in a virtual environment due to constraints from Bookworm. The initial setup for this was quite frustrating as the imager does not correctly set up the network address. To set the network up, after imaging your sd card, you need to edit the firstrun.sh file to include your wifi network details. Then you'll be able to remotely connect to it using SSH.


You can set the script to run as a service on the Raspberry Pi using the below commands on that systemm replacing <path> with the appropriate path for your system. It should be home/username in most cases:

# Make the script executable. 
chmod +x <path>/laundry_script.py

#Create the service file
sudo nano /etc/systemd/system/laundry.service 

#Paste this script into it
[Unit]
Description=Laundry Monitor Script
After=network.target

[Service]
ExecStart=<path>/laundry-venv/bin/python <path>/laundry_script.py
WorkingDirectory=<path>
Restart=always
RestartSec=10
User=Username
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target

# Restart systemd
sudo systemctl daemon-reexec

# Reload the service files
sudo systemctl daemon-reload

# Instructs systemd to start the service on boot, and --now starts the service immediately as well
sudo systemctl enable --now laundry
