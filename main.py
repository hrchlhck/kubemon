from requests import exceptions
from sys_monitor.cli.commands import start_collector, start_monitor, start_spark_monitor
import sys

if __name__ == "__main__":
    """
    args[2] -> ip
    args[3] -> port
    """
    args = sys.argv

    if len(args) > 1:
        try:
            if args[1] == "collector":
                start_collector(args[2])
            elif args[1] == "monitor":
                start_monitor(args[2])
            elif args[1] == "spark_monitor":
                start_spark_monitor(args[2])
            else:
                print("Option doesn't exist")
        except KeyboardInterrupt:
            print("Exiting")
    else:
        print("No option selected")
