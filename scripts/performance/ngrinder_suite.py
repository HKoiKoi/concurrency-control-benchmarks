import os
import subprocess
import sys
import time
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()

# --- [설정 영역] ---
NGRINDER_URL = "http://localhost:8081"
AUTH = ('admin', 'admin')
AGENT_CONTAINER_NAME = "ngrinder-agent"
CONTROLLER_CONTAINER_NAME = "ngrinder-controller"

# MySQL 설정 값
MYSQL_CONTAINER_NAME = "mysql"
MYSQL_USER = "root"
MYSQL_PASSWORD = os.getenv("MYSQL_ROOT_PASSWORD")
MYSQL_DB = os.getenv("MYSQL_DATABASE")

IDS = {
    "PESSIMISTIC WARM-UP": 1,
    "PESSIMISTIC 500": 2,
    "PESSIMISTIC 800": 3,
    "PESSIMISTIC 1000": 4,

    "SPIN WARM-UP": 5,
    "SPIN 500": 6,
    "SPIN 800": 7,
    "SPIN 1000": 8,

    "PUB/SUB WARM-UP": 9,
    "PUB/SUB 500": 10,
    "PUB/SUB 800": 11,
    "PUB/SUB 1000": 12,

    "ZOOKEEPER WARM-UP": 13,
    "ZOOKEEPER 500": 14,
    "ZOOKEEPER 800": 15,
    "ZOOKEEPER 1000": 16
}

# 테스트 스케줄 정의 (ID, 설명, 대기시간(분), 락전략(파일명용), Vuser(파일명용))
SCHEDULE = [
    # --- 비관적 락 ---
    # (IDS["PESSIMISTIC WARM-UP"], "비관적 락 웜업", 3, "pessimistic-lock", "warmup"),
    (IDS["PESSIMISTIC 500"], "비관적 락 Vuser 500 테스트", 1, "pessimistic-lock", 500),
    # (IDS["PESSIMISTIC 800"], "비관적 락 Vuser 800 테스트", 7, "pessimistic-lock", 800),
    # (IDS["PESSIMISTIC 1000"], "비관적 락 Vuser 1000 테스트", 7, "pessimistic-lock", 1000),

    # --- 스핀 락 ---
    # (IDS["SPIN WARM-UP"], "스핀 락 웜업", 3, "spin-lock", "warmup"),
    # (IDS["SPIN 500"], "스핀 락 Vuser 500 테스트", 7, "spin-lock", 500),
    # (IDS["SPIN 800"], "스핀 락 Vuser 800 테스트", 7, "spin-lock", 800),
    # (IDS["SPIN 1000"], "스핀 락 Vuser 1000 테스트", 7, "spin-lock", 1000),

    # --- 펍섭 락 ---
    # (IDS["PUB/SUB WARM-UP"], "펍섭 락 웜업", 3, "pubsub-lock", "warmup"),
    # (IDS["PUB/SUB 500"], "펍섭 락 Vuser 500 테스트", 7, "pubsub-lock", 500),
    # (IDS["PUB/SUB 800"], "펍섭 락 Vuser 800 테스트", 7, "pubsub-lock", 800),
    # (IDS["PUB/SUB 1000"], "펍섭 락 Vuser 1000 테스트", 7, "pubsub-lock", 1000),

    # --- 주키퍼 락 ---
    # (IDS["ZOOKEEPER WARM-UP"], "주키퍼 락 웜업", 3, "zookeeper-lock", "warmup"),
    # (IDS["ZOOKEEPER 500"], "주키퍼 락 Vuser 500 테스트", 7, "zookeeper-lock", 500),
    # (IDS["ZOOKEEPER 800"], "주키퍼 락 Vuser 800 테스트", 7, "zookeeper-lock", 800),
    # (IDS["ZOOKEEPER 1000"], "주키퍼 락 Vuser 1000 테스트", 7, "zookeeper-lock", 1000),
]


# --- [도우미 함수 영역] ---
def get_ordinal(n):
    if 11 <= (n % 100) <= 13: return f"{n}th"
    return f"{n}" + {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")


def run_mysql_query(query, description="DB 쿼리 실행", output_file=None):
    """MySQL 쿼리를 실행하고 결과를 화면 출력 및 파일에 기록합니다."""
    print(f"\n[{description}]")

    cmd = [
        "docker", "exec", "-i", MYSQL_CONTAINER_NAME,
        "mysql", f"-u{MYSQL_USER}", f"-p{MYSQL_PASSWORD}", MYSQL_DB,
        "-e", query
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        output = result.stdout.strip()

        if output:
            print(f"✅ 결과:\n{output}")
        else:
            print("✅ 실행 완료 (반환된 결과 없음)")

        if output_file:
            with open(output_file, "a", encoding="utf-8") as f:
                now_str = datetime.now().strftime('%H:%M:%S')
                f.write(f"[{now_str}] {description}\n")
                f.write(f"Query: {query}\n")
                f.write(f"{output if output else 'Success (No output)'}\n")
                f.write("-" * 60 + "\n")
        return output
    except subprocess.CalledProcessError as e:
        print(f"❌ 쿼리 실행 실패: {e.stderr}")
        return None


def prepare_agent_container(round_num):
    print("\n=== [준비] 에이전트 환경 세팅 ===")
    try:
        subprocess.run(["docker", "exec", AGENT_CONTAINER_NAME, "mkdir", "-p", "/tmp/result"], check=True)
        subprocess.run(
            ["docker", "exec", AGENT_CONTAINER_NAME, "sh", "-c", f"echo {round_num} > /tmp/result/round.txt"],
            check=True)
        print(f"✅ 에이전트 컨테이너 내 /tmp/result 및 round.txt({round_num}) 준비 완료")
    except Exception as e:
        print(f"❌ 초기화 실패: {e}")
        sys.exit(1)


def extract_output_csv(perf_id, target_dir, strategy, vuser, round_num):
    """컨트롤러에서 output.csv를 추출하고 이름을 변경하여 저장합니다."""
    print(f"\n=== [추출] nGrinder 공식 CSV 리포트 수집 (ID: {perf_id}) ===")

    bucket_folder = f"{(perf_id // 1000) * 1000}_{((perf_id // 1000) * 1000) + 999}"
    container_source = f"/opt/ngrinder-controller/perftest/{bucket_folder}/{perf_id}/report/output.csv"

    # 새로운 파일명: 예) pessimistic-500-1-result.csv
    new_filename = f"{strategy}-{vuser}-{round_num}-result.csv"
    temp_dest = os.path.join(target_dir, "temp_output.csv")
    final_dest = os.path.join(target_dir, new_filename)

    try:
        # 1. 파일 복사
        subprocess.run(["docker", "cp", f"{CONTROLLER_CONTAINER_NAME}:{container_source}", temp_dest], check=True)
        # 2. 이름 변경
        os.rename(temp_dest, final_dest)
        print(f"✅ CSV 저장 완료: {new_filename}")
    except Exception as e:
        print(f"❌ CSV 추출 실패: {e}")


def run_test(test_id, description):
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] {description} 시작 (ID: {test_id})")
    url = f"{NGRINDER_URL}/perftest/api/{test_id}/clone_and_start"
    try:
        res = requests.post(url, auth=AUTH, headers={'Content-Type': 'application/json'}, json={})
        if res.status_code == 200:
            new_id = res.json().get("id")
            print(f"🚀 테스트 실행 중... (ID: {new_id})")
            return new_id
    except Exception as e:
        print(f"❌ 통신 에러: {e}")
    return None


def wait_until_finished(perf_id):
    if not perf_id: return
    status_url = f"{NGRINDER_URL}/perftest/api/{perf_id}/status"
    while True:
        try:
            res = requests.get(status_url, auth=AUTH).json()
            status = (res[0] if isinstance(res, list) else res).get("status", {}).get("name")
            print(f"[{status}]", end="", flush=True)
            if status in ["FINISHED", "STOPPED", "ERROR", "CANCELED"]:
                print(f"\n테스트 종료 상태: {status}")
                break
        except:
            pass
        time.sleep(10)


def extract_and_cleanup_results(target_dir):
    print(f"\n=== [추출] 유입량(Arrivals) 데이터 수집 ===")
    try:
        subprocess.run(["docker", "cp", f"{AGENT_CONTAINER_NAME}:/tmp/result/.", target_dir], check=True)
        subprocess.run(["docker", "exec", AGENT_CONTAINER_NAME, "sh", "-c", "rm -rf /tmp/result/*"], check=True)
        print(f"✅ 유입량 파일 추출 및 에이전트 초기화 완료")
    except Exception as e:
        print(f"❌ 데이터 추출 중 오류: {e}")


# --- [메인 실행부] ---
if __name__ == "__main__":
    print("======================================================")
    print("       nGrinder 통합 성능 테스트 자동화 스크립트      ")
    print("======================================================")

    while True:
        try:
            round_num = int(input("진행할 테스트 회차를 숫자로 입력하세요: ").strip())
            break
        except:
            print("숫자만 입력하세요.")

    folder_name = f"{get_ordinal(round_num)}-test"

    # 경로 설정
    arrivals_dir = os.path.join(os.getcwd(), "data", "results", "arrivals", folder_name)
    consistency_dir = os.path.join(os.getcwd(), "data", "results", "consistency", folder_name)
    raw_csv_dir = os.path.join(os.getcwd(), "data", "raw", "ngrinder", folder_name)

    # 폴더 생성
    for d in [arrivals_dir, consistency_dir, raw_csv_dir]: os.makedirs(d, exist_ok=True)

    prepare_agent_container(round_num)
    total_start = time.time()

    # 2. 스케줄에 따른 개별 테스트 실행 및 정합성 체크
    for t_id, desc, wait_min, strategy, vuser in SCHEDULE:
        # [동적 파일명 생성] consistency-락전략-Vuser-회차.txt
        db_log_file = os.path.join(consistency_dir, f"consistency-{strategy}-{vuser}-{round_num}.txt")

        # 실제 테스트 실행 및 대기
        p_id = run_test(t_id, desc)
        wait_until_finished(p_id)

        # [After Test] DB 최종 상태 기록
        print(f"\n=== [Step 2] {desc} 종료 후 DB 체크 ===")
        run_mysql_query("SELECT COUNT(*) FROM enrollment;", "신청 완료 데이터(enrollment) 최종 건수 조회", db_log_file)
        run_mysql_query("SELECT enrolled_count FROM course WHERE course_id = 1;", "과목별 현재 수강 인원(counter) 최종 상태 조회",
                        db_log_file)

        # 컨트롤러에서 CSV 추출
        if p_id:
            extract_output_csv(p_id, raw_csv_dir, strategy, vuser, round_num)

        # 쿨다운 대기
        if wait_min > 0:
            print(f"다음 시나리오 전 {wait_min}분 대기...")
            time.sleep(wait_min * 60)

    # 3. 유입량 결과 파일 추출
    extract_and_cleanup_results(arrivals_dir)

    round_txt_path = os.path.join(arrivals_dir, "round.txt")
    if os.path.exists(round_txt_path):
        os.remove(round_txt_path)
        print("🧹 호스트 arrivals 폴더 내 round.txt 삭제 완료")

    total_duration = (time.time() - total_start) / 60

    print(f"\n🎉 모든 프로세스 완료. 총 소요 시간: {total_duration:.1f}분")
    print(f"결과는 data/results 하위의 'arrivals'와 'consistency' 폴더에서 확인하세요.")
