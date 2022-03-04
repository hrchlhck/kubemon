from kubemon.monitors.daemon import APP
from kubemon.settings import MONITOR_PORT
from kubemon.utils.networking import get_host_ip

if __name__ == '__main__':
    APP.run(host=get_host_ip(), port=MONITOR_PORT)
