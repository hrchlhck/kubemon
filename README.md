# kubemon
A tool for distributed container monitoring over Kubernetes.

## Translations
- [Português](./assets/README-pt-br.md)

## Table of contents
- [Environment Requirements](#environment-requirements)
- [Application Requirements](#application-requirements)
- [Illustrations](#illustrations)
- [Main Functionalities](#main-functionalities)
    - [Collected Metrics](#collected-metrics)
- [Installation](#installation)
- [Running](#running)
    - [Collector](#collector)
    - [Monitor](#monitor)
    - [CLI](#cli)
- [References](#references)

## Environment requirements
- Ubuntu 18.04
- Kubernetes v1.19
- Docker v.19.03.13
- Python 3.8
- make

## Application requirements
- [psutil](https://github.com/giampaolo/psutil)
- [requests](https://github.com/psf/requests)
- [addict](https://github.com/mewwts/addict)
- [docker-py](https://github.com/docker/docker-py)
- [sty](https://github.com/feluxe/sty)
- [virtualenv](https://github.com/pypa/virtualenv)

## Illustrations
Basic diagram
![Kubemon diagram](./assets/diagram-en.svg)

## Main functionalities
- Collects metrics from operating system, Docker containers and processes created by the container
- Send the collected metrics to the ```collector``` module, which saves the data in a CSV file
- Can be controlled remotely by a basic CLI

### Collected metrics
For more information about the collected metrics, please refer to:
- Operating System Metrics: These metrics are collected from linux ```/proc``` filesystem using both ```psutil``` Python API and ```/sys/block/<dev>/stat```.
    - CPU: [Miscellaneous kernel statistics in /proc/stat](https://www.kernel.org/doc/html/latest/filesystems/proc.html#miscellaneous-kernel-statistics-in-proc-stat)
    - Memory: [proc - process information pseudo-filesystem: /proc/vmstat](https://man7.org/linux/man-pages/man5/proc.5.html)
    - Disk : [Block layer statistics in /sys/block/\<dev\>/stat](https://www.kernel.org/doc/html/latest/block/stat.html#block-layer-statistics-in-sys-block-dev-stat)
    - Network: [proc - process information pseudo-filesystem: /proc/net/dev](https://man7.org/linux/man-pages/man5/proc.5.html)
- Docker: These metrics are collected from linux ```cgroups```.
    - CPU: [cgroups - Linux control groups: cpu,cpuacct](https://www.man7.org/linux/man-pages/man7/cgroups.7.html)
    - Memory: [cgroups - Linux control groups: memory](https://www.man7.org/linux/man-pages/man7/cgroups.7.html)
    - Disk: [cgroups - Linux control groups: blkio](https://www.man7.org/linux/man-pages/man7/cgroups.7.html)
    - Network: [proc - process information pseudo-filesystem: /proc/net/dev](https://man7.org/linux/man-pages/man5/proc.5.html)
- Docker Processes: These metrics are collected from linux ```/proc``` filesystem using ```psutil``` Python API.
    - CPU: [Miscellaneous kernel statistics in /proc/stat](https://www.kernel.org/doc/html/latest/filesystems/proc.html#miscellaneous-kernel-statistics-in-proc-stat)
    - Memory: [proc - process information pseudo-filesystem: /proc/vmstat](https://man7.org/linux/man-pages/man5/proc.5.html)
    - Disk: [Block layer statistics in /sys/block/\<dev\>/stat](https://www.kernel.org/doc/html/latest/block/stat.html#block-layer-statistics-in-sys-block-dev-stat)
    - Network: [proc - process information pseudo-filesystem: /proc/net/dev](https://man7.org/linux/man-pages/man5/proc.5.html)

#### **Operating System**
|  Type   |  Unit  | Metric |
| ------- | ------ | ------ |
| CPU     | Quantity <br> Quantity <br> Quantity <br> Quantity <br> Clock Ticks <br> Clock Ticks <br> Clock Ticks <br> Clock Ticks <br> Clock Ticks <br> Clock Ticks <br> Clock Ticks <br> Clock Ticks <br> Clock Ticks <br> | Context Switches <br> Interrupts <br> Soft Interrupts <br> Syscalls <br> Times User <br> Times System <br> Times Nice <br> Times Softirq <br> Times IRQ <br> Times IOWait <br> Times Guest <br> Times Guest Nice <br> Times Idle |
| Memory  | Quantity <br> Quantity <br> Quantity <br> Quantity <br> Quantity <br> KB <br> KB <br> Quantity <br> Quantity <br> Quantity <br> Quantity <br> | Active (Anon) <br> Inactive (Anon) <br> Inactive (file) <br> Active (file) <br> Mapped Pages <br> KB Paged In Since Boot (pgpgin) <br> KB Paged Out Since Boot (pgpgout) <br> Pages Free (pgfree) <br> Page Faults (pgfault) <br> Major Page Faults (pgmajfault) <br> Pages Reused (pgreuse) |
| Disk    | Requests <br> Requests <br> Sectors <br> Milliseconds <br> Requests <br> Requests <br> Sectors <br> Milliseconds <br> Requests <br> Milliseconds <br> Milliseconds <br> Requests <br> Requests <br> Sectors <br> Milliseconds <br> Requests <br> Milliseconds | Read I/O <br> Read I/O Merged with In-queue I/O <br> Read Sectors <br> Total Wait Time for Read Requests <br> Write I/O <br> Write I/O Merged with In-Queue I/O <br> Write Sectors <br> Total Wait Time for Write Requests <br> I/O in Flight <br> Total Time This Block Device Has Been Active <br> Total Wait Time for All Requests <br> Discard I/O Processed  <br> Discard I/O Processed with In-Queue I/O <br> Discard Sectors <br> Total Wait Time for Discard Requests <br> Flush I/O Processed <br> Total Wait Time for Flush Requests |
| Network | Bytes <br> Bytes <br> Packets <br> Packets | Sent <br> Received <br> Sent <br> Received |

#### **Docker Processes**
|  Type   |  Unit  | Metric |
| ------- | ------ | ------ |
| CPU     | Clock Ticks <br> Clock Ticks <br> Clock Ticks <br> Clock Ticks <br> Clock Ticks <br> | User Time <br> System Time <br> Children User <br> Children System <br> IOWait |
| Memory  | Pages <br> Pages <br> Pages <br> Pages <br> Pages <br> Pages <br> Pages <br> | Total Program Size (size) <br> Resident Set Size (resident) <br> Resident Shared Pages (shared) <br> Text (text) <br> ~~Library (lib)~~ <br> Data + Stack (data) <br> ~~Dirty Pages (dt)~~ |
| Disk    | Requests <br> Requests <br> Bytes <br> Bytes <br> Chars <br> Chars <br> | Read <br> Write <br> Read <br> Write <br> Read <br> Write <br> |
| Network | Bytes <br> Bytes <br> Packets <br> Packets | Sent <br> Received <br> Sent <br> Received |

#### **Docker**
|  Type   |  Unit  | Metric |
| ------- | ------ | ------ |
| CPU     | Clock Ticks <br> Clock Ticks <br> Quantity <br> Quantity <br> Clock Ticks <br> | User <br> System <br> Periods <br> Throttled <br> Throttled Time <br> |
| Memory  | Pages <br> Pages <br> Pages <br> Pages <br> Pages <br> Pages <br> Pages <br> Pages <br> Pages <br> Pages <br> Pages <br> Pages <br> | Resident Set Size (rss) <br> Chached <br> Mapped (mapped_file) <br> Paged In (pgpgin) <br> Paged Out (pgpgout) <br> Page Faults (pgfault) <br> Major Page Faults (pgmajfault) <br> Active (active_anon) <br> Inactive (inactive_anon) <br> Active File (active_file)<br> Inactive File (inactive_file) <br> Unevictable <br> |
| Disk    | Bytes <br> Bytes <br> Bytes <br> Bytes <br> Bytes <br> Bytes <br> | Read <br> Write <br> Sync <br> Async <br> Discard <br> Total <br> |
| Network | Bytes <br> Bytes <br> Packets <br> Packets | Sent <br> Received <br> Sent <br> Received |

## Installation
Before installing the tool, make sure Kubernetes and Docker are properly installed in the system. Besides, the tool must be downloaded and extracted in each Kubernetes node to properly monitor the metrics of the cluster.

1. Download the latest version here: [kubemon v2.0.0](https://github.com/hrchlhck/kubemon/archive/refs/tags/v2.0.0.zip) 

2. Extract the zip file and go on the extracted directory

3. Create a virtual environment and activate it
    ```sh
    $ python3 -m venv venv 
    $ source venv/bin/activate
    ```

4. Install packages
    ```sh 
    (venv) $ pip install .
    ```

## Running
The collected metrics will be saved in the ```client``` machine (See [Client](#Illustrations) in the diagram) by default in ```/tmp/data```. This setting can be changed in ```./kubemon/constants.py``` by changing ```ROOT_DIR``` variable value.

Example: 
```python
# Before
ROOT_DIR = "/tmp/data"

# After
ROOT_DIR = "/home/user/Documents/data"
```

In the further subsections will be teaching how to execute this tool.

A brief command list:
```sh
usage: kubemon [-h] [-l] [-t TYPE] [-H IP] [-p PORT] [-f FILE1 FILE2] [-c [COMMAND ...]] [-i INTERVAL]

Kubemon commands

optional arguments:
  -h, --help            show this help message and exit
  -l, --list            Lists all available modules
  -t TYPE, --type TYPE  Functionality of sys-monitor. E.g. collector, monitor, merge...
  -H IP, --host IP      Host that any of sys-monitor functions will be connecting
  -p PORT, --port PORT  Port of the host
  -f FILE1 FILE2, --files FILE1 FILE2
                        Files for merge
  -c [COMMAND ...], --command [COMMAND ...]
                        Command for be executing on CollectorClient
  -i INTERVAL, --interval INTERVAL
                        Data collection rate by monitors
```
### Collector
```sh
(venv) $ make collector
[ Collector ] Started collector CLI at 0.0.0.0:9880
[ Collector ] Started collector at 0.0.0.0:9822
```

### Monitor
Assuming that the collector IP is ```192.168.0.3```, let's connect the monitors to it.

There are three types of monitors:
1. OSMonitor - Collects Operating System metrics
2. DockerMonitor - Collects Docker metrics
3. ProcessMonitor - Collects container processes metrics

**The tool must be executed as ```sudo``` because some metrics (e.g. network, disk, ...) are available only for super users.**

### In this case, let's run all the monitors at once:
```sh
(venv) $ sudo python -m kubemon -t all -H 192.168.0.3
Connected OSMonitor_192_168_0_3_node_0 monitor to collector
...
```

### CLI
Assuming the same IP address for the collector in the section [Monitor](#monitor), the port to communicate with the ```collector``` via CLI is ```9880```.

There are two commands available so far:
1. ```/instances``` - Number of monitor instances connected to the ```collector``` object.
2. ```/start <output_dir>``` - Start the monitors and setting up the output directory to save the files

### Checking how many instances are connected
```sh
(venv) $ python -m kubemon -t cli -H 192.168.0.3 -c /instances
Connected instances: 5
```

### Starting monitors. In this case the CSV files will be saved at ```/tmp/data/test00/```
```sh
(venv) $ python -m kubemon -t cli -H 192.168.0.3 -c /start "test00"
Started 5 monitors
```

## References
- [Block layer statistics](https://www.kernel.org/doc/html/latest/block/stat.html)
- [/proc virtual file system](https://man7.org/linux/man-pages/man5/proc.5.html)
- [Evaluation of desktop operating systems under thrashing conditions](https://journal-bcs.springeropen.com/track/pdf/10.1007/s13173-012-0080-8.pdf)
- [cgroups](https://www.man7.org/linux/man-pages/man7/cgroups.7.html)
- [Docker runtime metrics](https://docs.docker.com/config/containers/runmetrics/)
