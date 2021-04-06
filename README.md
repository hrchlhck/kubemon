# sys-monitor
A Python tool for monitoring SLA in container orchestration environments 

## Building and testing
For testing sys-monitor you must have installed `gnu-make`. Once it is installed, you must run this command:
```sh
$ make build_test && make test
```

For building, you can simply type
```sh
$ make 
```

## Dependencies
- [Python 3](https://www.python.org/)
- [psutil](https://github.com/giampaolo/psutil)
- [requests](https://github.com/psf/requests)
- [pyspark](https://github.com/apache/spark/tree/master/python)
- [pandas](https://github.com/pandas-dev/pandas)
- [Docker CE](https://github.com/docker/docker-ce)
- [Docker compose](https://github.com/docker/compose)
- [Kubernetes](https://github.com/kubernetes/kubernetes)

## Summary
`sys-monitor` currently is only supported **Linux** based Operating Systems. 

## References
- [Block layer statistics](https://www.kernel.org/doc/html/latest/block/stat.html)
- [/proc virtual file system](https://man7.org/linux/man-pages/man5/proc.5.html)
- [Evaluation of desktop operating systems under thrashing conditions](https://journal-bcs.springeropen.com/track/pdf/10.1007/s13173-012-0080-8.pdf)
- [cgroups](https://www.man7.org/linux/man-pages/man7/cgroups.7.html)
- [Docker runtime metrics](https://docs.docker.com/config/containers/runmetrics/)
