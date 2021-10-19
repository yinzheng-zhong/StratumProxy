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
            self.proc_list.append(subprocess.Popen('python3 ' + self.filename, shell=True).wait())

    def remove_dead_procs(self):
        self.proc_list = [proc for proc in self.proc_list if proc.poll()]

    def maintain(self):
        while True:
            self.add_procs()

            for proc in self.proc_list:
                proc.wait()


filename = 'main.py ' + sys.argv[1]
num_processes = int(sys.argv[2])
pm = ProcManager(filename, num_processes)


