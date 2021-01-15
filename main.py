from sys_monitor.cli import *
from sys_monitor.merge import merge

if __name__ == "__main__":
    if args.type == 'merge':
        if not args.files:
            print("Merge type requires --file/-f")
        else:
            merge(*args.files)
    elif args.type == 'collector':
        get_system('collector', args).start()
    elif args.type == 'monitor':
        get_system('monitor', args).start()
