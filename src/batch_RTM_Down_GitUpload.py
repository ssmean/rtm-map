# launcher.py
import time
import subprocess

try:
    subprocess.run(["aws", "sso", "login", "--profile", "tmap-sv"], check=True)
    print("AWS SSO 로그인 성공 ✅")
except subprocess.CalledProcessError as e:
    print(f"AWS SSO 로그인 실패 ❌: {e}")

while True:
    subprocess.run(["python3", "RTM_Rawdata_Filtered_Download.py"])
    subprocess.run(["python3", "RTM_Visual_Upload_Git.py"])
    time.sleep(600)  # 600초 = 10분