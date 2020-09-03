import psutil
import time
import sys
import csv

def monitor(interval=1):
    swap = psutil.swap_memory().total
    
    if swap == 0:
        print('Swap not enabled')
        time.sleep(.4)
    
    with open('data.csv', mode='w', newline='') as f:
        writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        
        writer.writerow([
            'cpu_usage', 'memory_usage', 
            'disk_read_bytes', 'disk_written_bytes',
            'net_sent_bytes', 'net_received_bytes',
            'net_sent_packets', 'net_received_packets',
            'swap', 'swap_enabled', 'thread_count'
        ])
        
        while True:
            p = psutil.Process()
            
            time.sleep(interval)
            
            mem = psutil.virtual_memory().percent
            cpu = psutil.cpu_percent()
            disk_io = psutil.disk_io_counters()
            net_io = psutil.net_io_counters()
            num_threads = p.num_threads()
            
            print(f'CPU usage: {cpu:.4f}% \t {"":7} Memory usage: {mem:.4f}%')
            print(f'Disk read bytes: {disk_io.read_bytes:.4f} \t Disk written bytes: {disk_io.write_bytes:.4f}')
            print(f'Net sent bytes: {net_io.bytes_sent:.4f} \t Net received bytes: {net_io.bytes_recv:.4f}')
            print(f'Net sent packets: {net_io.packets_sent:.4f} \t Net received packets: {net_io.packets_recv:.4f}')
            print(f'Number of threads: {num_threads}')
            
            writer.writerow([
                cpu, mem, disk_io.read_bytes,
                disk_io.write_bytes, net_io.bytes_sent,
                net_io.bytes_recv, net_io.packets_sent,
                net_io.packets_recv, swap, swap != 0,
                num_threads
            ])
            
            if swap != 0:
                print(f'Swap: {swap}')

def main():   
    try:
        interval = 0
        
        if sys.argv[1] and (sys.argv[1] == '--interval' or sys.argv[1] == '-i'):
            interval = float(sys.argv[2])
            monitor(interval)
        else:
            print('You have not selected any interval. Interval setted to 1 second.\n')
            monitor()
                
    except (IndexError, KeyboardInterrupt):
        pass
        
    
if __name__ == '__main__':
    main()