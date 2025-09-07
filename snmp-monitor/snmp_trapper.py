#!/usr/bin/env python3

import subprocess
import re
from shared.db_handler import db_connection, insert_trap_data
from shared.config_loader import TRAPPER_LOG_FILE
from shared.logger_config import setup_logger


logger = setup_logger("SNMPTrapper", TRAPPER_LOG_FILE)

# Regex patterns
IF_DESCR_RE = re.compile(r'interfaces\.ifTable\.ifEntry\.ifDescr\.\d+="([^"]+)"')
IF_ADMIN_RE = re.compile(r'interfaces\.ifTable\.ifEntry\.ifAdminStatus\.\d+=(\d+)')

# Capture SNMP traps
with subprocess.Popen(
    ["sudo", "/usr/bin/tcpdump", "-i", "any", "port", "162", "-l"],
    stdout=subprocess.PIPE, text=True
) as proc:
    for line in proc.stdout:
        if "interfaces.ifTable.ifEntry.ifAdminStatus" in line:
            parts = line.split()
            timestamp = parts[0]
            host = parts[4].split('.')[0:4]
            host = ".".join(host)

            interface_match = IF_DESCR_RE.search(line)
            admin_match = IF_ADMIN_RE.search(line)
            if interface_match and admin_match:
                interface = interface_match.group(1)
                status = "UP" if admin_match.group(1) == "1" else "DOWN"

                insert_trap_data(db_connection, timestamp, host, interface, status)

                # Log based on status
                logger.info(f"Interface {interface} is {status} on host {host}")
