# coding=utf-8
import psutil
import socket


def check_linux_status():
    # host
    print 'hostname:' + str(socket.getfqdn())

    # 输出cpu利用率
    cpu_use_percent = psutil.cpu_percent()
    if cpu_use_percent > 80:
        print 'Warnning!cpu使用率异常:' + str(cpu_use_percent) + '%'
    else:
        print 'cpu使用率:' + str(cpu_use_percent) + '%'

    # 输出memory
    # memory
    memory_last = int(psutil.virtual_memory().available) / 1024 / 1024
    if memory_last < 1024:
        print 'Warnning!memory剩余异常:' + str(memory_last) + 'M'
    else:
        print 'memory剩余:' + str(memory_last) + 'M'
    socket.gethostname()
    # disk
    for i in psutil.disk_partitions():
        disk_data = psutil.disk_usage(i[1])
        disk_str = 'device=%s。挂载点=%s。使用率=%s %%' % (str(i[0]), str(i[1]), str(disk_data[3]))
        if disk_data[3] > 90:
            print 'Warnning!disk异常:' + disk_str
        else:
            print 'disk:' + disk_str

if __name__ == '__main__':
    check_linux_status()
