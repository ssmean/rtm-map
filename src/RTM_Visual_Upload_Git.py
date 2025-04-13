import pandas as pd
import folium
from datetime import datetime
import shutil
import os
import subprocess

# 📅 오늘 날짜 문자열
today = datetime.today().strftime("%y%m%d")
file_name = f"{today}_RTM_Map_Visualization.html"

# 🔄 입력 CSV
csv_path = "/Users/pseongmin/Desktop/1.BMW/1.KPI_Report/03_RTM/rtm-map/RawData/20250408/00_xy_filter_csv_output_1159.csv"
score_csv = "/Users/pseongmin/Desktop/1.BMW/1.KPI_Report/03_RTM/rtm-map/src/2504_score.csv"



# 📍 데이터 로딩
df = pd.read_csv(csv_path)
score_df = pd.read_csv(score_csv)

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
    folium.Rectangle(
        bounds=bounds,
        color='blue',
        opacity=0.25,             # 🔹 테두리 선의 투명도 설정
        fill=True,
        fill_color='blue',
        fill_opacity=0.1,
        popup=f"🔵 점수 구간 {i + 1}"
    ).add_to(m)

# 🔴 마커 추가
for idx, row in df.iterrows():
    popup_text = f"""
    📌공사ID: {row['SUDN_ST_ID']}<br>
    📍도로명: {row['SUDN_ST_ROAD']}<br>
    📝내용: {row['SUDN_ST_CONT']}<br>
    🕒기간: {row['SUDN_ST_DTTM']} ~ {row['SUDN_ED_DTTM']}
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
repo_path = "/Users/pseongmin/Desktop/1.BMW/1.KPI_Report/03_RTM/rtm-map/Visualization_Data"
output_file_path = os.path.join(repo_path, file_name)

# 📝 지도 저장
m.save(output_file_path)
print(f"✅ 저장 완료 → {output_file_path}")

# 🔁 Git add → commit → push
try:
    subprocess.run(["git", "add", file_name], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", f"Add {file_name}"], cwd=repo_path, check=True)
    subprocess.run(["git", "push"], cwd=repo_path, check=True)
    print("🚀 GitHub 업로드 완료!")
except subprocess.CalledProcessError as e:
    print("❌ Git 오류 발생:", e)