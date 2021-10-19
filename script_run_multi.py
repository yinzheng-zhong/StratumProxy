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
        self.proc_list = [subprocess.Popen('python3 ' + self.filename, shell=True)] * int(self.num_procs)

    def remove_dead_procs(self):
        self.proc_list = [proc for proc in self.proc_list if proc.poll()]

    def maintain(self):
        while True:
            self.add_procs()
            self.remove_dead_procs()
            time.sleep(1)


filename = 'main.py ' + sys.argv[1]
num_processes = int(sys.argv[2])
pm = ProcManager(filename, num_processes)


