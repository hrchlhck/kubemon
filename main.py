from sys_monitor.cli.commands import *

if __name__ == "__main__":
    try:
        if args.type == 'merge':
            if not args.files:
                print("Merge type requires --file/-f")
            else:
                merge(*args.files)
        elif args.type == 'collector':
            get_system('collector', args).start(int(args.monitors))
        elif args.type == 'monitor':
            get_system('monitor', args).start()
    except KeyboardInterrupt:
        print("Exiting")
