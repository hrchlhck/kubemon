from kubemon.cli import *
from kubemon.merge import merge
from multiprocessing import Process

def start(instance):
    instance.start()

if __name__ == "__main__":
    if args.type == 'merge':
        if not args.files:
            print("Merge type requires --file/-f")
        else:
            merge(*args.files)

    if args.type in MODULES:
        get_system(args.type, args).start()

    if args.type == 'cli' and args.command:
        get_system(args.type, args).exec(args.command)

    if args.type == 'all':
        for s in MODULES[1:]:
            s = get_system(s, args)
            Process(target=start, args=(s,)).start()
    
    if args.list:
        print("Available modules:")
        for module in MODULES:
            print(f"\t- {module.capitalize()}")
