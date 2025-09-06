"""
Handles all database interactions for the SNMP monitoring tools.

This module is responsible for creating a connection to the SQLite database
and setting up the necessary tables for storing CPU utilization and SNMP trap data.
Functions are designed to be imported and used by other scripts.
"""

import sqlite3
from sqlite3 import Error
import logging
from pathlib import Path
from .config_loader import DB_LOCATION

# Setup a logger for this module
logger = logging.getLogger(__name__)

# Define the name for the database file
DB_FILE = "snmp_monitor.db"
# Construct the full path to the database file using pathlib for cross-platform compatibility
DB_PATH = Path(DB_LOCATION) / DB_FILE


def create_connection():
    """
    Create a database connection to the SQLite database specified in the config.

    The database file is created at the path specified by DB_LOCATION if it
    does not already exist.

    Returns:
        sqlite3.Connection: Connection object or None if an error occurs.
    """
    conn = None
    try:
        # The directory is expected to exist.
        # sqlite3.connect() will create the database file if it doesn't exist at the given path.
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        logger.info(f"Successfully connected to SQLite database at {DB_PATH}")
        return conn
    except Error as e:
        logger.error(f"Error connecting to database at {DB_PATH}: {e}", exc_info=True)
    return conn

def setup_database(conn):
    """
    Create tables in the database if they don't already exist.

    Args:
        conn (sqlite3.Connection): The database connection object.
    """
    cpu_table_sql = """
    CREATE TABLE IF NOT EXISTS cpu_utilization (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        host TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        utilization REAL NOT NULL
    );
    """

    trap_table_sql = """
    CREATE TABLE IF NOT EXISTS snmp_traps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        host TEXT NOT NULL,
        interface TEXT,
        interface_status TEXT
    );
    """
    try:
        cursor = conn.cursor()
        cursor.execute(cpu_table_sql)
        cursor.execute(trap_table_sql)
        conn.commit()
        logger.info("Database tables 'cpu_utilization' and 'snmp_traps' are ready.")
    except Error as e:
        logger.error(f"Error creating database tables: {e}", exc_info=True)

def insert_cpu_data(conn, host, timestamp, utilization):
    """
    Inserts a new CPU utilization record into the database.

    Args:
        conn (sqlite3.Connection): The database connection object.
        host (str): The IP address or hostname of the device.
        timestamp (str): The timestamp of the data collection.
        utilization (float): The calculated CPU utilization.

    Returns:
        bool: True if insertion was successful, False otherwise.
    """
    sql = '''INSERT INTO cpu_utilization(host, timestamp, utilization)
             VALUES(?, ?, ?)'''
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (host, timestamp, utilization))
        conn.commit()
        logger.debug(f"Inserted CPU data for {host}: {utilization}%")
        return True
    except Error as e:
        logger.error(f"Failed to insert CPU data for {host}: {e}", exc_info=True)
        return False

def insert_trap_data(conn, timestamp, host, interface, status):
    """
    Inserts a new SNMP trap record into the database.

    Args:
        conn (sqlite3.Connection): The database connection object.
        timestamp (str): The timestamp of the trap.
        host (str): The IP address of the device sending the trap.
        interface (str): The name of the interface from the trap.
        status (str): The calculated status (UP/DOWN) of the interface.

    Returns:
        bool: True if insertion was successful, False otherwise.
    """
    sql = '''INSERT INTO snmp_traps(timestamp, host, interface, interface_status)
             VALUES(?, ?, ?, ?)'''
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (timestamp, host, interface, status))
        conn.commit()
        logger.info(f"Inserted trap data from {host} for interface {interface}: {status}")
        return True
    except Error as e:
        logger.error(f"Failed to insert trap data for {host}: {e}", exc_info=True)
        return False

# --- One-time Setup ---
# When this module is imported, it will automatically try to connect to the
# database and set up the necessary tables.
db_connection = create_connection()
if db_connection:
    setup_database(db_connection)

