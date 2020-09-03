from sys_monitor.monitor import Monitor


def main():
    try:
        monitor = Monitor()
        monitor.start()
    except KeyboardInterrupt:
        print('\nExiting')


if __name__ == "__main__":
    main()