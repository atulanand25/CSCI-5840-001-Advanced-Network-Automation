# SNMP Monitoring Tools
This project contains two Python scripts for network monitoring via SNMP, designed to be run as system daemons.
# Overview
SNMP Poller (snmp_poller.py): Periodically queries a list of hosts for CPU utilization, calculates the average, and logs the data to a file and a central SQLite database.
SNMP Trapper (snmp_trapper.py): Listens for SNMP traps (specifically for interface status changes) and records the events to a file and the database.
Both scripts use a shared library for database and logging operations to ensure consistency and avoid code duplication.
# Project Structure
snmp_monitor/
├── snmp_poller.py          # Main script for polling CPU
├── snmp_trapper.py         # Main script for listening for traps
├── README.md               # This file
└── shared/
    ├── __init__.py         # Makes 'shared' a Python package
    ├── db_handler.py       # Handles all SQLite database interactions
    └── logger_config.py    # Provides standardized logging configuration


# Prerequisites
Python 3
The pysnmp library (pip install pysnmp)
sqlite3 command-line tool (usually installed by default on Linux)
SNMP enabled on your target network devices.
Setup and Installation
Directory and Permissions:
Create the necessary log directory. The user running the scripts will need write access to it.
sudo mkdir -p /var/log/netman
sudo chown your_user:your_group /var/log/netman


Install Python Library:
pip install pysnmp


Configuration:
Open snmp_poller.py and edit the HOSTS list and COMMUNITY_STRING.
Open snmp_trapper.py and edit SNMP_COMMUNITY if it differs from the poller.
Running the Scripts:
You can run them directly for testing:
python3 snmp_monitor/snmp_poller.py
python3 snmp_monitor/snmp_trapper.py

However, for production, it is highly recommended to run them as systemd services.
Running as systemd Services
Create the following two files in /etc/systemd/system/.
Poller Service (snmp-poller.service)
[Unit]
Description=SNMP CPU Polling Service
After=network.target

[Service]
ExecStart=/usr/bin/python3 /path/to/your/snmp_monitor/snmp_poller.py
WorkingDirectory=/path/to/your/snmp_monitor
User=your_user      # Run as a non-root user
Group=your_group
Restart=on-failure
RestartSec=10s

[Install]
WantedBy=multi-user.target


Trapper Service (snmp-trapper.service)
Note: To bind to port 162 as a non-root user, you need to grant the capability to the Python executable.
sudo setcap 'cap_net_bind_service=+ep' $(which python3)
[Unit]
Description=SNMP Trap Listening Service
After=network.target

[Service]
ExecStart=/usr/bin/python3 /path/to/your/snmp_monitor/snmp_trapper.py
WorkingDirectory=/path/to/your/snmp_monitor
User=your_user      # Run as a non-root user
Group=your_group
Restart=on-failure
RestartSec=10s

[Install]
Wantedby=multi-user.target


Managing the Services
After creating the files, run these commands:
# Reload systemd to recognize the new services
sudo systemctl daemon-reload

# Enable the services to start on boot
sudo systemctl enable snmp-poller.service
sudo systemctl enable snmp-trapper.service

# Start the services now
sudo systemctl start snmp-poller.service
sudo systemctl start snmp-trapper.service

# Check their status
sudo systemctl status snmp-poller.service
sudo systemctl status snmp-trapper.service


