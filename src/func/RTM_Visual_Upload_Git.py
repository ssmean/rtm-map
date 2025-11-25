import pandas as pd
import folium
import shutil
import os
from datetime import datetime

import subprocess
import glob 
from pathlib import Path


# 📅 오늘 날짜 문자열
today = datetime.today().strftime("%y%m%d")
file_name = f"{today}_RTM_Map_Visualization.html"


# 경로 설정 
current_dir = Path(__file__).resolve().parent #src 위치 
project_root = current_dir.parent #프로젝트 루트 디렉(src의 상위)
# day1 = datetime.datetime.now().strftime('%Y%m%d')  # 예: "20250223"
day1 = datetime.now().strftime('%Y%m%d')


# 🔍 RawData 디렉토리
raw_dir = project_root / 'Rawdata' / day1
pattern = os.path.join(raw_dir, "00_xy_filter_csv_output_*.csv")

# 최신 CSV 파일 찾기
csv_candidates = glob.glob(pattern)
if not csv_candidates:
    raise FileNotFoundError("❌ 해당 경로에 일치하는 CSV 파일이 없습니다!")

# 수정시간 기준으로 가장 최신 파일 선택
latest_csv = max(csv_candidates, key=os.path.getmtime)

# ✅ 자동으로 최신 파일 경로 설정
csv_path = latest_csv
print(f"🆕 최신 CSV 파일 사용: {csv_path}")

# 🔄 입력 CSV
score_csv = project_root.parent / 'Rawdata' / 'score.csv'
# 📍 데이터 로딩
df = pd.read_csv(csv_path)
score_df = pd.read_csv(score_csv, sep="\t")  # ✅ 탭 구분자로 읽기

# ✨ CHECK_CORRECT_H == 1 필터링
if "CHECK_CORRECT_H" not in score_df.columns:
    raise ValueError("❌ score.csv 파일에 'CHECK_CORRECT_H' 컬럼이 없습니다!")

score_df = score_df[score_df["CHECK_CORRECT_H"] == 1].reset_index(drop=True)
# ✅ CATE 열에서 '차단' 또는 '사고' 단어가 포함된 행 제거
score_df = score_df[~(score_df["CATE"].str.contains("차단|사고", na=False))].reset_index(drop=True)

print(f"🆕 필터링된 점수 데이터 로딩 완료 (행 개수: {len(score_df)})")

# 📍 지도 초기 중심점
center_lat = df["OCCUR_Y_POS"].mean()
center_lon = df["OCCUR_X_POS"].mean()

# 🗺 지도 생성
m = folium.Map(location=[center_lat, center_lon], zoom_start=13)

# 🔴 마커 추가
from folium.features import CustomIcon

# 아이콘 URL (예: 공사 표지판 아이콘)
icon_url = "https://cdn-icons-png.flaticon.com/512/12704/12704854.png"

# 🔷 score.csv 기준 파란색 박스 추가
# 📍 버퍼(m) → 위도/경도 환산 (대략 1도 ≈ 111,000m)
buffer_m = 200
buffer_deg = buffer_m / 111000  # 약 0.0045도

for i, row in score_df.iterrows():
    lat = row["Y"]
    lon = row["X"]
    bounds = [
        [lat - buffer_deg, lon - buffer_deg],
        [lat + buffer_deg, lon + buffer_deg]
    ]
    popup_text = f"""
    🔵 점수 구간 {i + 1}<br>
    🕒 TIME_STMP: {row['TIME_STMP']}<br>
    📋 CATE: {row['CATE']}<br>
    ✅ CHECK_CORRECT_H: {row['CHECK_CORRECT_H']}
    """
    folium.Rectangle(
        bounds=bounds,
        color='blue',
        opacity=0.25,
        fill=True,
        fill_color='blue',
        fill_opacity=0.1,
        popup=folium.Popup(popup_text, max_width=300)
    ).add_to(m)

# 🔴 마커 추가
for idx, row in df.iterrows():
    popup_text = f"""
    📌공사ID: {row['SUDN_ST_ID']}<br>
    📍도로명: {row['SUDN_ST_ROAD']}<br>
    📝내용: {row['SUDN_ST_CONT']}<br>
    🕒기간: {row['SUDN_ST_DTTM']} ~ {row['SUDN_ED_DTTM']}<br>
    🕒Datatime: {row['BASE_DTTM']}
    """

    # 커스텀 아이콘 정의
    custom_icon = CustomIcon(
        icon_image=icon_url,
        icon_size=(21, 21)  # 아이콘 크기 조절
    )

    # 마커 추가
    folium.Marker(
        location=[row["OCCUR_Y_POS"], row["OCCUR_X_POS"]],
        popup=folium.Popup(popup_text, max_width=300),
        tooltip=row["SUDN_ST_ROAD"],
        icon=custom_icon
    ).add_to(m)


# 🔷 회사에 이모티콘 표시
company_icon = CustomIcon(
    icon_image='https://cdn-icons-png.flaticon.com/512/5193/5193766.png',  # 회사/건물 아이콘 URL
    icon_size=(75, 75) 
)

folium.Marker(
    location=[37.4777493, 127.0378260],
    popup="📍회사 위치",
    tooltip="회사",
    icon=company_icon
).add_to(m)


# 📂 GitHub repo 로컬 경로
repo_path = project_root.parent / 'Visualization_Data'
output_file_path = repo_path / file_name   # ✅ Path 객체끼리 조합!
# 📝 지도 저장
m.save(output_file_path)
print(f"✅ 저장 완료 → {output_file_path}")
print("---------------------------")

# 🔁 Git add → commit → push
try:
    subprocess.run(["git", "add", str(output_file_path)], cwd=project_root, check=True)
    subprocess.run(["git", "commit", "-m", f"Add {file_name}"], cwd=project_root, check=True)
    subprocess.run(["git", "push"], cwd=project_root, check=True)
    print("🚀 GitHub 업로드 완료!")
    print("---------------------------")
except subprocess.CalledProcessError as e:
    print("❌ Git 오류 발생:", e)