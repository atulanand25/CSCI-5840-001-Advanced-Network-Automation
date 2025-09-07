#!/usr/bin/env python3

import time
import datetime
from easysnmp import Session, EasySNMPError
from shared.logger_config import setup_logger
from shared.db_handler import db_connection, insert_cpu_data
from shared.config_loader import (
    SNMP_COMMUNITY, SNMP_HOSTS, POLLER_OID,
    POLLER_INTERVAL, POLLER_LOG_FILE
)

# Setup logger for this script
logger = setup_logger("SNMPPoller", POLLER_LOG_FILE)

def fetch_cpu_utilization(host, community, oid):
    """
    Fetches CPU utilization values from a single host using easysnmp walk.

    Args:
        host (str): The IP address or hostname of the device.
        community (str): The SNMP community string.
        oid (str): The OID to walk for CPU utilization.

    Returns:
        list[int] or None: A list of integer utilization values, or None on failure.
    """
    try:
        # Create an SNMP session with the remote host
        session = Session(hostname=host, community=community, version=2, timeout=5, retries=2)

        # Perform an SNMP walk on the OID
        response = session.walk(oid)

        # Extract the integer value from each returned SNMP variable
        utilizations = [int(item.value) for item in response]
        return utilizations

    except EasySNMPError as e:
        logger.error(f"[{host}] SNMP Error: {e}")
        return None
    except Exception as e:
        logger.error(f"[{host}] An unexpected error occurred: {e}", exc_info=True)
        return None

def main():
    """Main polling loop."""
    logger.info("Starting CPU Utilization Monitoring Service (using easysnmp).")

    if not db_connection:
        logger.critical("Database connection failed. Poller cannot start.")
        return

    while True:
        for host in SNMP_HOSTS:
            logger.info(f"Polling CPU utilization for {host}...")

            util_values = fetch_cpu_utilization(host, SNMP_COMMUNITY, POLLER_OID)

            if util_values is not None:
                if util_values:
                    average = sum(util_values) / len(util_values)
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    logger.info(f"[{host}] Average CPU Utilization: {average:.2f}%")

                    # Insert data into the database
                    insert_cpu_data(db_connection, host, timestamp, average)
                else:
                    logger.warning(f"[{host}] No CPU utilization data returned.")
            else:
                # Error is already logged by the fetch function
                logger.warning(f"Failed to retrieve data from {host}.")

        logger.info(f"Polling cycle complete. Waiting for {POLLER_INTERVAL} seconds.")
        time.sleep(POLLER_INTERVAL)

if __name__ == "__main__":
    main()

