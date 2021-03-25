from sys_monitor.cli import *
from sys_monitor.merge import merge

if __name__ == "__main__":
    if args.type == 'merge':
        if not args.files:
            print("Merge type requires --file/-f")
        else:
            merge(*args.files)
    elif args.type in SYSTEMS:
        get_system(args.type, args).start()
    elif args.type == 'cli' and args.command:
        get_system(args.type, args).exec(args.command)
    else:
        print("Argument %s does not exist." % args.type)
