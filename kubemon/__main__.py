from kubemon.cli.commands import SYSTEMS
from kubemon.log import create_logger
from kubemon.config import LOGGING_LEVEL

from .exceptions.platform_exception import NotLinuxException
from .cli import *
from .merge import merge
from .collector.commands import COMMAND_CLASSES

import sys

if __name__ == "__main__":

    if 'win' in sys.platform:
        raise NotLinuxException("Kubemon is only available for Linux-based Operating Systems. Sorry.")
        
    LOGGER = create_logger(__name__, level=LOGGING_LEVEL)

    if args.type == 'merge':
        if not args.files:
            print("Merge type requires --file/-f")
        else:
            merge(*args.files)

    if args.type in MODULES:
        LOGGER.debug(f"Starting application {args.type}")
        SYSTEMS[args.type].start()

    if args.type == 'cli' and args.command:
        LOGGER.debug("Executed CLI")
        SYSTEMS[args.type].exec(args.command)
    elif args.type == 'cli' and not args.command:
        LOGGER.debug("Executed CLI")
        SYSTEMS[args.type].run()
   
    if args.list:
        print("Available modules:")
        LOGGER.debug("Listing modules")
        for module in MODULES:
            print(f"\t- {module.capitalize()}")
    
    if args.list_commands:
        print("Available commands:")
        LOGGER.debug("Listing commands")
        cmd = COMMAND_CLASSES.get('help')(COMMAND_CLASSES)
        print(cmd.execute())