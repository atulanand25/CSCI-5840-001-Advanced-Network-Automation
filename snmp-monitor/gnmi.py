from pygnmi.client import gNMIclient
import json

with gNMIclient(target=('192.168.200.8', 57400), username='admin', password='admin', insecure=True) as gc:
    result = gc.get(path=['/network-instances/network-instance[name=default]/protocols/protocol[name=BGP]/bgp/neighbors'], encoding='json')
    print(json.dumps(result, indent=2))
