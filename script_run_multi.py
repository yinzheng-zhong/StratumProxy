import subprocess
import time
import sys
import threading


def manage():
    arg = sys.argv[1]

    filename = 'main.py ' + arg
    while True:
        subprocess.Popen('python3 ' + filename, shell=True).wait()

        time.sleep(1)


threads = []
for i in range(int(sys.argv[2])):
    a = threading.Thread(target=manage)
    a.start()
    a.join()
