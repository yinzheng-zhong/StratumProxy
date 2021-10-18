import subprocess
import time


filename = 'main.py scrypt'
while True:
    proc = subprocess.Popen('python3 ' + filename, shell=True).wait()

    time.sleep(10)
