import subprocess

filename = 'main.py scrypt'
while True:
    """However, you should be careful with the '.wait()'"""
    p = subprocess.Popen('python3 ' + filename, shell=True).wait()
