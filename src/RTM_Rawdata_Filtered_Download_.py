import boto3
import os
from botocore.exceptions import NoCredentialsError
import pandas as pd
import datetime
import subprocess



try:
    subprocess.run(["aws", "sso", "login", "--profile", "tmap-sv"], check=True)
    print("AWS SSO 로그인 성공 ✅")
except subprocess.CalledProcessError as e:
    print(f"AWS SSO 로그인 실패 ❌: {e}")
# --------------------
# AWS & 시간 관련 설정
# --------------------
bucket_name = 's3-bmw-rtti-prd'
aws_profile = 'tmap-sv'

# 현재 날짜 및 시간 계산
day1 = datetime.datetime.now().strftime('%Y%m%d')  # 예: "20250223"
now = datetime.datetime.now()
start_time = (now - datetime.timedelta(minutes=30)).strftime('%H%M')  # 예: "0930"
end_time = now.strftime('%H%M')  # 예: "1000"

source_prefix = f'res_data/BMW/BACKUP/rtm/{day1}/'
# local_directory = f'/Users/pseongmin/Desktop/1.BMW/1.KPI_Report/03_RTM/histpy/{day1}/'
local_directory = f'/Users/pseongmin/Desktop/1.BMW/1.KPI_Report/03_RTM/rtm-map/Rawdata/{day1}'

# 최종 머지, CSV 등 경로
output_file_path = os.path.join(local_directory, "merged_output.txt")
csv_output_path = os.path.join(local_directory, "csv_output.csv")

# 필터링된 CSV 파일 경로
filtered_csv_path = os.path.join(local_directory, f"00_xy_filter_csv_output_{end_time}.csv")

# 좌표 조건
x_min = 126.8346
x_max = 127.16865
y_min = 37.45567
y_max = 37.61329

xy_filtered_csv_path = os.path.join(local_directory, filtered_csv_path)

# --------------------------
# 1. S3 다운로드 함수 (수정)
# --------------------------
def download_s3_directory_with_time_filter(bucket_name, source_prefix, local_directory, 
                                           day1, start_time, end_time, aws_profile=None):
    """
    지정된 S3 디렉토리에서 파일명에 포함된 날짜+시간을 추출하여,
    day1(YYYYMMDD)이면서 start_time(포함)~end_time(포함)에 해당하는
    파일만 다운로드한다.

    :param bucket_name: S3 버킷 이름
    :param source_prefix: S3 디렉토리 경로 (예: 'res_data/BMW/BACKUP/rtm/20250223/')
    :param local_directory: 로컬에 저장할 디렉토리 경로
    :param day1: 오늘 날짜(YYYYMMDD)
    :param start_time: 시작 시간 (HHMM)
    :param end_time: 종료 시간 (HHMM)
    :param aws_profile: AWS CLI 프로파일 이름
    """
    try:
        if aws_profile:
            boto3.setup_default_session(profile_name=aws_profile)
        s3 = boto3.client('s3')
        paginator = s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket_name, Prefix=source_prefix)

        for page in pages:
            if 'Contents' in page:
                for obj in page['Contents']:
                    file_key = obj['Key']
                    # 예: file_key = "res_data/BMW/BACKUP/rtm/20250223/RTM_202502230955.txt"
                    filename = os.path.basename(file_key)  
                    # filename = "RTM_202502230955.txt"
                    
                    # 파일명 예: "RTM_202502230955.txt"
                    if filename.startswith("RTM_") and filename.endswith(".txt"):
                        datetime_part = filename.split("_")[1].split(".")[0]  # "202502230955"
                        
                        # 날짜(YYYYMMDD)와 시간(HHMM) 분리
                        date_str = datetime_part[:8]  # "20250223"
                        time_str = datetime_part[8:]  # "0955"
                        
                        # 날짜와 시간 범위 확인
                        if date_str == day1 and start_time <= time_str <= end_time:
                            local_file_path = os.path.join(
                                local_directory, 
                                os.path.relpath(file_key, source_prefix)
                            )
                            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
                            print(f"Downloading {file_key} → {local_file_path}...")
                            s3.download_file(bucket_name, file_key, local_file_path)
        
        print("Filtered download complete!")
    
    except NoCredentialsError:
        print("AWS credentials not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


# --------------------------
# 2. TXT 파일 병합 함수
# --------------------------
def merge_txt_files(directory, output_filename):
    """
    주어진 디렉토리에서 모든 .txt 파일의 첫 줄(헤더)을 제외하고 병합.
    파일 간 공백 줄 없이 병합하며, 파일명 순서대로 처리.
    마지막 작업으로 지정된 내용을 첫 줄에 추가.
    """
    if os.path.exists(output_filename):
        os.remove(output_filename)
        
    # 맨 위 헤더
    first_line = (
        "BASE_DTTM|REG_DTTM|SUDN_ST_ID|SUDN_LAST_VER|SUDN_SERV_ST_DTTM|SUDN_ST_DTTM|"
        "SUDN_ED_DTTM|SUDN_ST_CD|SUDN_ST_TYPE_CD|SUDN_ST_CONT|SUDN_ST_ROAD_KIND|"
        "SUDN_LANE_NO|VEHICLE_KIND|OCCUR_LINK_ID|OCCUR_X_POS|OCCUR_Y_POS|SUDN_ST_ROAD|"
        "SUDN_ST_SECTION|SUB_LINK_CNT|MID|KS_SUB_LINK_ID\n"
    )
    
    merged_content = ""
    
    for filename in sorted(os.listdir(directory)):
        if filename.endswith(".txt"):
            file_path = os.path.join(directory, filename)
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()[1:]  # 첫 줄(헤더) 제외
                merged_content += "".join(lines)
    
    with open(output_filename, 'w', encoding='utf-8') as output_file:
        output_file.write(first_line)
        output_file.write(merged_content)
    
    print(f"모든 txt 파일이 {output_filename}에 성공적으로 병합되었습니다.")

# --------------------------
# 3. TXT → CSV 변환 함수
# --------------------------
def convert_txt_to_csv(input_file_path, csv_output_path):
    """
    텍스트 파일을 읽어서 CSV 파일로 변환하는 함수.
    """
    try:
        data = pd.read_csv(input_file_path, sep='|')
        data.to_csv(csv_output_path, index=False, encoding='utf-8-sig')
        print(f"CSV 파일이 성공적으로 저장되었습니다: {csv_output_path}")
    except Exception as e:
        print(f"파일 처리 중 오류가 발생했습니다: {e}")

# --------------------------
# 4. CSV 필터링 함수 (SUDN_ST_CD="B")
# --------------------------
def filter_and_save_csv(input_path, output_path):
    """
    주어진 조건에 따라 CSV 파일을 필터링하고 저장하는 함수.
    여기서는 SUDN_ST_CD == "B" 인 행만 필터링 예시.
    """
    df = pd.read_csv(input_path)
    condition3 = df["SUDN_ST_CD"] == "B"
    filtered_df = df[condition3]
    filtered_df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"필터링된 CSV 파일이 저장되었습니다: {output_path}")

# --------------------------
# 5. 좌표 필터링 함수
# --------------------------
def filter_by_coordinates(input_path, output_path, x_min, x_max, y_min, y_max):
    """
    좌표 조건에 따라 CSV 파일을 필터링하고 저장하는 함수.
    """
    try:
        df = pd.read_csv(input_path)
        condition_x = (df['OCCUR_X_POS'] > x_min) & (df['OCCUR_X_POS'] < x_max)
        condition_y = (df['OCCUR_Y_POS'] > y_min) & (df['OCCUR_Y_POS'] < y_max)
        filtered_df = df[condition_x & condition_y]
        filtered_df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"좌표 조건 필터링 후 CSV 파일이 저장되었습니다: {output_path}")
    except Exception as e:
        print(f"파일 처리 중 오류가 발생했습니다: {e}")

# ---------------------------------------------
# 실제 실행 흐름
# 1) 30분 전 ~ 현재 시각의 파일만 S3에서 다운로드
# 2) 다운로드된 .txt 파일들 병합 → merged_output.txt
# 3) 병합된 txt → CSV 변환
# 4) SUDN_ST_CD="B" 필터링
# 5) 좌표 조건 필터링
# ---------------------------------------------
def main():
    # 1) 다운로드
    download_s3_directory_with_time_filter(
        bucket_name=bucket_name,
        source_prefix=source_prefix,
        local_directory=local_directory,
        day1=day1,
        start_time=start_time,
        end_time=end_time,
        aws_profile=aws_profile
    )

    # 2) TXT 병합
    merge_txt_files(local_directory, output_file_path)

    # 3) CSV 변환
    convert_txt_to_csv(output_file_path, csv_output_path)

    # 4) SUDN_ST_CD="B" 필터링
    filter_and_save_csv(csv_output_path, filtered_csv_path)

    # 5) 좌표 필터링
    filter_by_coordinates(filtered_csv_path, xy_filtered_csv_path, x_min, x_max, y_min, y_max)

if __name__ == "__main__":
    main()
