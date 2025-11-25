# %%
import time
import subprocess
import platform
import sys
from pathlib import Path

# ✅ 현재 OS 확인
current_os = platform.system()
python_cmd = "python3" if current_os != "Windows" else "python"

# ✅ 경로 설정
current_file = Path(__file__).resolve()          # batch_RTM_Down_GitUpload.py
src_dir = current_file.parent                    # src 디렉토리
func_dir = src_dir / "func"                       # src/func 디렉토리

# ✅ 실행할 스크립트 경로
script1 = func_dir / "RTM_Rawdata_Filtered_Download.py"
script2 = func_dir / "RTM_Visual_Upload_Git.py"


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
