from requests import exceptions
from sys_monitor.cli.commands import *
import sys

if __name__ == "__main__":
    """
        args[2] -> ip
        args[3] -> port
    """
    args = sys.argv
    
    if len(args) > 1:
        if args[1] == 'collector':
            start_collector(args[2], args[3])
        elif args[1] == 'monitor':
            try:
                start_monitor(args[2], args[3])
            except exceptions.ConnectionError:
                print('Connection refused')
        else:
            print('Option doesn\'t exist')
    else:
        print('No option selected')
    