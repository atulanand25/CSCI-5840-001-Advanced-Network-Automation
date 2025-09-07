"""
Handles loading configuration from the config.ini file.

This module uses Python's configparser to read the application settings
and make them available to other modules.
"""
import configparser
from pathlib import Path

# Create a parser and read the config file
config = configparser.ConfigParser()
config_path = Path(__file__).parent.parent / 'config.ini'
POLLER_LOG_FILE = Path(__file__).parent.parent.parent / 'log' / 'poll.log'
TRAPPER_LOG_FILE = Path(__file__).parent.parent.parent/ 'log' / 'trap.log'
STATS_LOG_FILE = Path(__file__).parent.parent.parent / 'log' / 'stats.log'
DB_LOCATION = Path(__file__).parent.parent

config.read(config_path)

# --- Common SNMP Settings ---
SNMP_COMMUNITY = config.get('snmp', 'community', fallback='public')
_hosts_str = config.get('snmp', 'hosts', fallback='')
# Converts the comma-separated string of hosts into a Python list
SNMP_HOSTS = [host.strip() for host in _hosts_str.split(',') if host.strip()]

# --- Poller-specific Settings ---
# Reads values from the [poller] section.
POLLER_OID = config.get('poller', 'oid', fallback='1.3.6.1.2.1.25.3.3.1.2')
# getint() automatically converts the string value to an integer.
POLLER_INTERVAL = config.getint('poller', 'interval', fallback=300)

