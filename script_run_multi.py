import subprocess
import time
import sys


class ProcManager:
    def __init__(self, filename, num_procs):
        self.filename = filename
        self.num_procs = num_procs

        self.proc_list = []

        self.maintain()

    def add_procs(self):
        while len(self.proc_list) < self.num_procs:
            self.proc_list.append(subprocess.Popen('python3 ' + self.filename, shell=True))

    def remove_dead_procs(self):
        self.proc_list = [proc for proc in self.proc_list if proc.pid]
        print(len(self.proc_list))

    def maintain(self):
        while True:
            self.add_procs()
            print('*' * 100 + str(len(self.proc_list)) + '*' * 100)
            self.remove_dead_procs()
            time.sleep(1)


filename = 'main.py ' + sys.argv[1]
num_processes = int(sys.argv[2])
pm = ProcManager(filename, num_processes)


