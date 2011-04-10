import subprocess

process = subprocess.Popen('python runner.py',
            stdin = subprocess.PIPE,
            stdout = subprocess.PIPE,
            )
            
In = process.stdout
print In.readline()
