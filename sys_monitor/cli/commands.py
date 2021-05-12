from ..monitors import *
from ..collector import *

import argparse

SYSTEMS = ['collector', 'monitor', 'process', 'docker']

def get_system(sys_type, args):
    if args.host and args.port:
        if sys_type == 'collector':
            return Collector(address=args.host, port=int(args.port))
        elif sys_type == 'monitor':
            return OSMonitor(address=args.host, port=int(args.port), interval=int(args.interval))
        elif sys_type == 'process':
            return ProcessMonitor(address=args.host, port=int(args.port), interval=int(args.interval))
        elif sys_type == 'docker':
            return DockerMonitor(address=args.host, port=int(args.port), interval=int(args.interval))
        elif sys_type == 'cli':
            return CollectorClient(address=args.host, port=int(args.port))
    elif not args.host:
        print("Missing --host/-H IP")

parser = argparse.ArgumentParser(description='sys-monitor commands')

parser.add_argument('-t', '--type', help='Functionality of sys-monitor. E.g. collector, monitor, merge...')
parser.add_argument('-H', '--host', default='0.0.0.0', help='Host that any of sys-monitor functions will be connecting', metavar='IP')
parser.add_argument('-p', '--port', default=9822, help='Port of the host')
parser.add_argument('-f', '--files', nargs=2, help='Files for merge', metavar=('FILE1', 'FILE2'))
parser.add_argument('-c', '--command', default="", nargs='*', help="Command for be executing on CollectorClient")
parser.add_argument('-i', '--interval', default=5, help="Data collection rate by monitors")

args = parser.parse_args()