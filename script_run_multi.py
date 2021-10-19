import subprocess
import time
import sys


filename = 'main.py ' + sys.argv[1]

clients = []

while len(clients) < int(sys.argv[2]):
    clients.append(subprocess.Popen('python3 ' + filename, shell=True))

while True:
    for proc in clients:
        if proc.poll() is not None:
            proc = subprocess.Popen('python3 ' + filename, shell=True)

    time.sleep(1)
