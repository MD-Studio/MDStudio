import time
import re
import os

completed = False
lineCount = 0

if os.path.exists('/tmp/.INSTALLINGDONE'):
    exit()

while not completed:
    try:
        with open('/tmp/.INSTALLING') as log:
            logLines = log.readlines()

        for l in range(lineCount, len(logLines)):
            print(logLines[l][:-1])
            if re.match('<<<<COMPLETED>>>>', logLines[l]):
                completed = True

        lineCount = len(logLines)
    except Exception as e:
        raise e
        pass
    
    time.sleep(0.2)

open('/tmp/.INSTALLINGDONE', 'a').close()
os.remove('/tmp/.INSTALLING')
