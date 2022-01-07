from ..monitors import *
from ..collector import *
from ..config import DEFAULT_CLI_PORT, DEFAULT_MONITOR_INTERVAL, DEFAULT_MONITOR_PORT
from ..monitors import Kubemond

import argparse

MODULES = ['collector', 'daemon']

parser = argparse.ArgumentParser(description='Kubemon commands')

parser.add_argument('-l', '--list', help="Lists all available modules", action='store_true')
parser.add_argument('-lc', '--list-commands', help='List all available commands for CollectorClient', action='store_true')
parser.add_argument('-t', '--type', help='Functionality of sys-monitor. E.g. collector, monitor, merge...')
parser.add_argument('-H', '--host', default='0.0.0.0', help='Host that any of sys-monitor functions will be connecting', metavar='IP')
parser.add_argument('-p', '--port', default=DEFAULT_MONITOR_PORT, help='Port of the host')
parser.add_argument('-f', '--files', nargs=2, help='Files for merge', metavar=('FILE1', 'FILE2'))
parser.add_argument('-c', '--command', default="", nargs='*', help="Command for be executing on CollectorClient")
parser.add_argument('-i', '--interval', default=DEFAULT_MONITOR_INTERVAL, help="Data collection rate by monitors")

args = parser.parse_args()

SYSTEMS = {
    'collector': Collector(address=args.host, port=int(args.port)),
    'daemon': Kubemond(address=args.host, port=int(args.port), interval=int(args.interval)),
    'cli': CollectorClient(address=args.host, port=DEFAULT_CLI_PORT)
}