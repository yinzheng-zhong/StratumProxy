import subprocess

filename = 'main.py script'
while True:
    """However, you should be careful with the '.wait()'"""
    p = subprocess.Popen('python3 ' + filename, shell=True).wait()
