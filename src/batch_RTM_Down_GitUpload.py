# launcher.py
import time
import subprocess

while True:
    subprocess.run(["python3", "RTM_Rawdata_Filtered_Download.py"])
    subprocess.run(["python3", "RTM_Visual_Upload_Git.py"])
    time.sleep(600)  # 600초 = 10분