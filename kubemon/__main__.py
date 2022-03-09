from kubemon.log import create_logger
from kubemon.exceptions.platform_exception import NotLinuxException
from kubemon.cli import *
from kubemon.collector.commands import COMMAND_CLASSES

import kubemon.settings as settings

import sys

if __name__ == "__main__":

    if 'win' in sys.platform:
        raise NotLinuxException("Kubemon is only available for Linux-based Operating Systems. Sorry.")
        
    LOGGER = create_logger(__name__, level=settings.LOGGING_LEVEL)

    args = parser.parse_args()
    
    if not args.from_ctnr:
        settings.Volatile.set_procfs()
        LOGGER.info("PROCFS_PATH set to %s", '/proc')
    
    module = get_module(args.type, args.host, int(args.port))

    if module == None:
        LOGGER.info('Module %s does not exist', type(module))
        exit()

    if module != None and args.type == 'cli':
        module.run()

    if module != None and not args.type == 'cli':
        module.start()
  
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