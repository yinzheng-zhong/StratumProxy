import subprocess
import time

filename = 'main.py scrypt'
while True:
    """However, you should be careful with the '.wait()'"""
    p = subprocess.Popen('python3 ' + filename, shell=True).wait()
    print(p)

    time.sleep(10)
