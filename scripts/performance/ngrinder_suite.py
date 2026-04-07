import sys
import time
from datetime import datetime

import requests

# --- [설정 영역] ---
NGRINDER_URL = "http://localhost:8081"
AUTH = ('admin', 'admin')

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

# 테스트 스케줄 정의 (ID, 설명, 테스트 종료 후 대기 시간(분))
SCHEDULE = [
    (IDS["PESSIMISTIC WARM-UP"], "본 테스트 전 비관적 락 웜업", 5),
    (IDS["SPIN WARM-UP"], "본 테스트 전 스핀 락 웜업", 5),
    (IDS["PUB/SUB WARM-UP"], "본 테스트 전 펍섭 락 웜업", 5),
    (IDS["ZOOKEEPER WARM-UP"], "본 테스트 전 주키퍼 락 웜업", 5),

    (IDS["PESSIMISTIC WARM-UP"], "비관적 락 웜업", 3),
    (IDS["PESSIMISTIC 500"], "비관적 락 Vuser 500 웜업", 7),
    (IDS["PESSIMISTIC WARM-UP"], "비관적 락 웜업", 3),
    (IDS["PESSIMISTIC 800"], "비관적 락 Vuser 800 웜업", 7),
    (IDS["PESSIMISTIC WARM-UP"], "비관적 락 웜업", 3),
    (IDS["PESSIMISTIC 1000"], "비관적 락 Vuser 1000 웜업", 7),

    (IDS["SPIN WARM-UP"], "스핀 락 웜업", 3),
    (IDS["SPIN 500"], "스핀 락 Vuser 500 웜업", 7),
    (IDS["SPIN WARM-UP"], "스핀 락 웜업", 3),
    (IDS["SPIN 800"], "스핀 락 Vuser 800 웜업", 7),
    (IDS["SPIN WARM-UP"], "스핀 락 웜업", 3),
    (IDS["SPIN 1000"], "스핀 락 Vuser 1000 웜업", 7),

    (IDS["PUB/SUB WARM-UP"], "펍섭 락 웜업", 3),
    (IDS["PUB/SUB 500"], "펍섭 락 Vuser 500 웜업", 7),
    (IDS["PUB/SUB WARM-UP"], "펍섭 락 웜업", 3),
    (IDS["PUB/SUB 800"], "펍섭 락 Vuser 800 웜업", 7),
    (IDS["PUB/SUB WARM-UP"], "펍섭 락 웜업", 3),
    (IDS["PUB/SUB 1000"], "펍섭 락 Vuser 1000 웜업", 7),

    (IDS["ZOOKEEPER WARM-UP"], "주키퍼 락 웜업", 3),
    (IDS["ZOOKEEPER 500"], "주키퍼 락 Vuser 500 웜업", 7),
    (IDS["ZOOKEEPER WARM-UP"], "주키퍼 락 웜업", 3),
    (IDS["ZOOKEEPER 800"], "주키퍼 락 Vuser 800 웜업", 7),
    (IDS["ZOOKEEPER WARM-UP"], "주키퍼 락 웜업", 3),
    (IDS["ZOOKEEPER 1000"], "주키퍼 락 Vuser 1000 웜업", 7),

]


def run_test(test_id, description):
    now = datetime.now().strftime('%H:%M:%S')
    print(f"\n[{now}] {description} 실행 시도 (Origin ID: {test_id})")

    url = f"{NGRINDER_URL}/perftest/api/{test_id}/clone_and_start"

    headers = {'Content-Type': 'application/json'}
    payload = {}

    try:
        res = requests.post(url, auth=AUTH, headers=headers, json=payload)

        if res.status_code == 200:
            new_id = res.json().get("id")
            print(f"실행 성공! (새로운 실행 ID: {new_id})")

            return new_id
        else:
            print(f"실행 실패: {res.text}")
            return None
    except Exception as e:
        print(f"통신 에러: {e}")
        return None


def wait_until_finished(perf_id):
    if not perf_id: return

    print("테스트 완료 대기 중...", end="", flush=True)
    status_url = f"{NGRINDER_URL}/perftest/api/{perf_id}/status"

    while True:
        try:
            res = requests.get(status_url, auth=AUTH)
            status_data = res.json()

            if isinstance(status_data, list):
                status_data = status_data[0]

            status = status_data.get("status", {}).get("name")

            print(f"[{status}]", end="", flush=True)

            if status in ["FINISHED", "STOPPED", "ERROR", "CANCELED"]:
                print(f"\n최종 상태 확인됨: {status}")

                if status in ["ERROR", "CANCELED"]:
                    print("테스트가 비정상 종료되었습니다. 스케줄을 즉시 중단합니다.")
                    sys.exit(1)

                break
        except Exception as e:
            print(f"\n[상태 조회 에러: {e}", end="", flush=True)

        time.sleep(10)


if __name__ == "__main__":
    print(f"=== nGrinder 통합 성능 테스트 시작 ({datetime.now().strftime('%H:%M:%S')}) ===")

    total_start = time.time()

    for idx, (t_id, desc, wait_min) in enumerate(SCHEDULE):
        current_perf_id = run_test(t_id, desc)

        if current_perf_id is None:
            print("\n[치명적 오류] 실행 실패로 인해 전체 테스트를 중단합니다.")
            sys.exit(1)

        wait_until_finished(current_perf_id)

        if wait_min > 0:
            print(f"시나리오에 따라 {wait_min}분간 휴식합니다...")
            time.sleep(wait_min * 60)

    total_duration = (time.time() - total_start) / 60
    print(f"\n모든 시나리오 종료. 총 소요 시간: {total_duration:.1f}분")
