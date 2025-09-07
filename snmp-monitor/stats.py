import time
import xml.etree.ElementTree as ET
from ncclient import manager
from ncclient.operations.rpc import RPCError

# Shared utilities
from shared.db_handler import db_connection, insert_interface_stats
from shared.config_loader import SNMP_HOSTS

def process_interface_details(xml_response: str, ip_address: str):
    """
    Parses NETCONF XML response, extracts interface stats,
    and inserts them into the database.
    """
    root = ET.fromstring(xml_response)

    ns = {
        'ocif': 'http://openconfig.net/yang/interfaces',
        'ocipv4': 'http://openconfig.net/yang/interfaces/ip',
        'ocvlan': 'http://openconfig.net/yang/vlan',
        'oceth': 'http://openconfig.net/yang/interfaces/ethernet',
    }

    for interface in root.findall('.//ocif:interface', ns):
        name_elem = interface.find('ocif:name', ns)
        name = name_elem.text if name_elem is not None else "No Name"

        mtu_ipv4 = "1500"
        incoming_packets = "N/A"
        outgoing_packets = "N/A"
        port_speed = "N/A"
        oper_status = "N/A"

        ipv4_elem = interface.find('.//ocipv4:ipv4', ns)
        if ipv4_elem is not None:
            mtu_elem_ipv4 = ipv4_elem.find('ocipv4:state/ocipv4:mtu', ns)
            mtu_ipv4 = mtu_elem_ipv4.text if mtu_elem_ipv4 is not None else "1500"

        counters_elem = interface.find('.//ocif:counters', ns)
        if counters_elem is not None:
            incoming_packets_elem = counters_elem.find('ocif:in-pkts', ns)
            outgoing_packets_elem = counters_elem.find('ocif:out-pkts', ns)
            incoming_packets = incoming_packets_elem.text if incoming_packets_elem is not None else "N/A"
            outgoing_packets = outgoing_packets_elem.text if outgoing_packets_elem is not None else "N/A"

        state_elem = interface.find('.//oceth:state', ns)
        if state_elem is not None:
            port_speed_elem = state_elem.find('oceth:port-speed', ns)
            port_speed = port_speed_elem.text.split('_')[1] if port_speed_elem is not None else "N/A"

        oper_status_elem = interface.find('.//ocif:oper-status', ns)
        if oper_status_elem is not None:
            oper_status = oper_status_elem.text if oper_status_elem is not None else "N/A"

        print(f"[{ip_address}] Interface: {name}, MTU: {mtu_ipv4}, In: {incoming_packets}, Out: {outgoing_packets}, Speed: {port_speed}, Status: {oper_status}")

        # Store interface stats
        insert_interface_stats(
            db_connection,
            ip_address=ip_address,
            interface_name=name,
            mtu=mtu_ipv4,
            incoming_packets=incoming_packets,
            outgoing_packets=outgoing_packets,
            speed=port_speed,
            interface_status=oper_status
        )

def poll_device_interfaces(ip_address: str):
    """
    Connects to a device via NETCONF, retrieves interface data,
    and processes the response.
    """
    try:
        with manager.connect(
            host=ip_address,
            port=830,
            username='admin',
            password='admin',
            hostkey_verify=False
        ) as m:

            netconf_filter = """
            <filter type="subtree">
                <interfaces xmlns="http://openconfig.net/yang/interfaces"/>
            </filter>
            """
            response = m.get(netconf_filter)
            print(f"\n--- Polling {ip_address} ---")
            process_interface_details(response.xml, ip_address)

    except RPCError as e:
        print(f"[RPC ERROR] {ip_address}: {e}")
    except Exception as e:
        print(f"[ERROR] {ip_address}: {e}")

def main():
    """
    Main loop to continuously poll all configured SNMP hosts using NETCONF.
    """
    if not SNMP_HOSTS:
        print("No SNMP hosts found in configuration.")
        return

    while True:
        for ip in SNMP_HOSTS:
            poll_device_interfaces(ip)

        time.sleep(1)

if __name__ == "__main__":
    main()
