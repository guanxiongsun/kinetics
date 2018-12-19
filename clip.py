import subprocess


command = ['ffmpeg',
           '-i', '"CHR.mp4"',
           '-ss', 288,
           '-t', 10,
           '-c:v', 'libx264', '-c:a', 'copy',
           '-threads', '1',
           '-loglevel', 'panic',
           '"chr.mp4"']
command = ' '.join(command)
try:
    output = subprocess.check_output(command, shell=True,
                                     stderr=subprocess.STDOUT)
except subprocess.CalledProcessError as err:
    print(err.output)
