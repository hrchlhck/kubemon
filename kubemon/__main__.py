from kubemon.log import create_logger
from .exceptions.platform_exception import NotLinuxException
from .cli import *
from .merge import merge
from .collector.commands import COMMANDS
from multiprocessing import Process

import sys
import logging

def start(instance):
    instance.start()

if __name__ == "__main__":

    if 'win' in sys.platform:
        raise NotLinuxException("Kubemon is only available for Linux-based Operating Systems. Sorry.")
        
    LOGGER = create_logger(__name__, level=logging.DEBUG)

    if args.type == 'merge':
        if not args.files:
            print("Merge type requires --file/-f")
        else:
            merge(*args.files)

    if args.type in MODULES:
        LOGGER.debug(f"Starting application {args.type}")
        get_system(args.type, args).start()

    if args.type == 'cli' and args.command:
        LOGGER.debug("Executed CLI")
        get_system(args.type, args).exec(args.command)

    if args.type == 'all':
        LOGGER.debug("Starting application with all monitors")
        for s in MODULES[1:]:
            s = get_system(s, args)
            Process(target=start, args=(s,)).start()
    
    if args.list:
        print("Available modules:")
        LOGGER.debug("Listing modules")
        for module in MODULES:
            print(f"\t- {module.capitalize()}")
    
    if args.list_commands:
        print("Available commands:")
        LOGGER.debug("Listing commands")
        for cmd in COMMANDS:
            print(f"- {COMMANDS[cmd]}")
