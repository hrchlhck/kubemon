from ..collector import *
from ..settings import MONITOR_PORT, COLLECT_INTERVAL
from ..monitors import Kubemond

import argparse

MODULES = ['collector', 'daemon']

__all__ = ['parser', 'get_modules']

parser = argparse.ArgumentParser(description='Kubemon commands')

parser.add_argument('-l', '--list', help="Lists all available modules", action='store_true')
parser.add_argument('-lc', '--list-commands', help='List all available commands for CollectorClient', action='store_true')
parser.add_argument('-t', '--type', help='Functionality of sys-monitor. E.g. collector, monitor, ...', required=True)
parser.add_argument('-H', '--host', help='Host that any of sys-monitor functions will be connecting', metavar='IP', required=True)
parser.add_argument('-p', '--port', default=MONITOR_PORT, help='Port of the host')
parser.add_argument('-c', '--command', default="", nargs='*', help="Command for be executing on CollectorClient")
parser.add_argument('-i', '--interval', default=COLLECT_INTERVAL, help="Data collection rate by monitors")
parser.add_argument(
    '-fc', '--from-container',
    dest='from_ctnr', action='store_false',
    default=True,
    help="Flag if the metrics are being collected from a container or from the host"
)
parser.add_argument('-n', '--num-daemons', default=1, help='Number of daemons that are expected to connect to the collector module.')

SYSTEMS = {
    'collector': Collector,
    'daemon': Kubemond,
    'cli': CollectorClient
}

def get_module(module: str, address: str, port: int) -> object:
    if module != 'daemon':
        return SYSTEMS.get(module)(address=address, port=port)
    return SYSTEMS.get(module)(port=port)