import subprocess
import time
import sys

arg = sys.argv[1]

filename = 'main.py ' + arg
while True:
    proc = subprocess.Popen('python3 ' + filename, shell=True).wait()

    time.sleep(1)
