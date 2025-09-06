"""
SNMP Trap Listener.

This script listens for SNMP traps on port 162. When a specific trap related
to interface status is received, it parses the trap data, determines the new
status, and logs the information to a file and a central SQLite database.

NOTE: This version is updated to use 'asyncio' instead of the removed
'asyncore' module, making it compatible with Python 3.12+.
"""
import datetime
import asyncio
from pysnmp.carrier.asyncio.dgram import udp
from pysnmp.entity import engine, config
from pysnmp.entity.rfc3413 import ntfrcv
from shared.logger_config import setup_logger
from shared.db_handler import db_connection, insert_trap_data

# --- Configuration ---
SNMP_COMMUNITY = "lab"
LOG_FILE = "/var/log/netman/snmp_traps.log"

# Setup logger for this script
logger = setup_logger("SNMPTrapper", LOG_FILE)

# OIDs we are interested in
IF_ADMIN_STATUS_OID = "1.3.6.1.2.1.2.2.1.7"
IF_DESCR_OID = "1.3.6.1.2.1.2.2.1.2"

# This callback function is synchronous and does not need to be changed.
def trap_callback(snmpEngine, stateReference, contextEngineId, contextName,
                  varBinds, cbCtx):
    """
    Callback function executed for each received trap.
    """
    transportDomain, transportAddress = snmpEngine.msgAndPduDsp.getTransportInfo(stateReference)
    host = transportAddress[0]
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    logger.info(f"Trap received from {host} at {timestamp}")

    trap_data = {
        'host': host,
        'timestamp': timestamp,
        'interface': 'N/A',
        'status': 'UNKNOWN'
    }

    # Iterate through the variable bindings in the trap
    for oid, val in varBinds:
        oid_str = str(oid)
        val_str = str(val.prettyPrint())

        if IF_DESCR_OID in oid_str:
            trap_data['interface'] = val_str
            logger.debug(f"[{host}] Parsed Interface: {val_str}")

        elif IF_ADMIN_STATUS_OID in oid_str:
            if val_str == "1":
                trap_data['status'] = "UP"
            else:
                trap_data['status'] = "DOWN"
            logger.debug(f"[{host}] Parsed Status: {trap_data['status']} (Raw value: {val_str})")

    # If we have meaningful data, log it to the database
    if trap_data['interface'] != 'N/A' and trap_data['status'] != 'UNKNOWN':
        if db_connection:
            insert_trap_data(
                db_connection,
                trap_data['timestamp'],
                trap_data['host'],
                trap_data['interface'],
                trap_data['status']
            )
        else:
            logger.error(f"[{host}] Cannot log trap to DB: Database connection is not available.")

# The main function is now an 'async' function
async def main():
    """Main listening function."""
    if not db_connection:
        logger.critical("Database connection failed. Trapper cannot start.")
        return

    snmpEngine = engine.SnmpEngine()

    # Transport setup: listening on UDP port 162
    config.addTransport(
        snmpEngine,
        udp.domainName,
        udp.UdpTransport().openServerMode(('0.0.0.0', 162))
    )

    config.addV1System(snmpEngine, 'my-area', SNMP_COMMUNITY)

    ntfrcv.NotificationReceiver(snmpEngine, trap_callback)

    logger.info("SNMP Trap Listener started on port 162.")
    logger.info("Waiting for traps...")

    try:
        # This will run the dispatcher indefinitely
        snmpEngine.transportDispatcher.jobStarted(1)
        # Create a future that never completes, keeping the script running
        await asyncio.Future()
    except Exception as e:
        logger.error(f"An error occurred in the trap listener: {e}", exc_info=True)
    finally:
        snmpEngine.transportDispatcher.closeDispatcher()
        logger.info("SNMP Trap Listener stopped.")

if __name__ == "__main__":
    try:
        # Use asyncio.run() to start the asynchronous main function
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down listener.")

