import time
import subprocess
import platform
import sys
from pathlib import Path

# ✅ 현재 운영체제 확인 (Windows, Darwin(macOS), Linux)
current_os = platform.system()

# ✅ python 실행 명령어 결정
python_cmd = "python3" if current_os != "Windows" else "python"

# ✅ 실행 경로 기준 스크립트 위치 설정 (상대경로 사용 가능)
project_root = Path(__file__).resolve().parent
script1 = project_root / "RTM_Rawdata_Filtered_Download.py"
script2 = project_root / "RTM_Visual_Upload_Git.py"

# ✅ AWS SSO 로그인
try:
    subprocess.run(["aws", "sso", "login", "--profile", "tmap-sv"], check=True)
    print("✅ AWS SSO 로그인 성공")
except subprocess.CalledProcessError as e:
    print(f"❌ AWS SSO 로그인 실패: {e}")
    sys.exit(1)

# ✅ 루프 실행 (10분마다)
while True:
    for script in [script1, script2]:
        result = subprocess.run(
            [python_cmd, str(script)],
            capture_output=True,
            text=True,
            encoding="utf-8"  # 대부분 OS에서 호환됨
        )
        print(f"📝 [{script.name}] STDOUT:\n{result.stdout}")
        print(f"⚠️  [{script.name}] STDERR:\n{result.stderr}")
    time.sleep(600)
