import subprocess
import time
import sys

arg = sys.argv[1]

filename = 'main.py ' + arg

clients = []

while len(clients) < 10:
    clients.append(subprocess.Popen('python3 ' + filename, shell=True))

while True:
    for proc in clients:
        if proc.poll() is None:
            proc = subprocess.Popen('python3 ' + filename, shell=True)

    time.sleep(1)
