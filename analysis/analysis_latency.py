import os

import numpy as np
import pandas as pd


def calculate_log_normal_p95(mean_val, variance_val):
    """
    평균과 분산을 바탕으로 로그 정규 분포의 p95 지점을 추정합니다.
    """
    if mean_val <= 0:
        return 0.0

    # 일반 통계를 Log-Normal 파라미터로 변환
    sigma_log = np.sqrt(np.log(1 + (variance_val / (mean_val ** 2))))
    mu_log = np.log(mean_val) - (sigma_log ** 2 / 2)

    # 최종 p95 계산 (Z-score 1.64485 활용)
    p95 = np.exp(mu_log + 1.64485 * sigma_log)
    return p95


def analyze_latency(input_filepath, output_filepath):
    """
    nGrinder 데이터를 바탕으로 가중 평균 및 p95 Latency를 분석하여 요약된 CSV를 생성합니다.
    """
    if not os.path.exists(input_filepath):
        print(f"'{input_filepath}' 파일을 찾을 수 없습니다.")
        return

    print(f"데이터를 불러옵니다: {input_filepath}")
    df = pd.read_csv(input_filepath)

    # 컬럼명 안전장치
    lock_col = 'Lock'
    if lock_col not in df.columns:
        print(f"[오류] '{lock_col}' 컬럼이 데이터에 없습니다. 현재 컬럼: {list(df.columns)}")
        return

    # 1. 각 테스트(Order)별로 가중 평균 및 p95 산출
    def get_test_metrics(group):
        n = group['Tests']
        mu = group['Mean_Test_Time_(ms)']
        sigma = group['Test_Time_Standard_Deviation_(ms)']

        total_n = n.sum()
        if total_n == 0:
            return pd.Series({'Mean_Latency': 0.0, 'p95_Latency': 0.0})

        # [Mean Latency] 전체 가중 평균 구하기
        weighted_mean = (n * mu).sum() / total_n

        # [p95 Latency] 전체 결합 분산(Pooled Variance) 구하기
        ex2 = (sigma ** 2) + (mu ** 2)  # 각 행의 제곱의 평균
        ex2_total = (n * ex2).sum() / total_n  # 전체 제곱의 평균 가중합
        var_total = ex2_total - (weighted_mean ** 2)  # 최종 전체 분산

        # 부동소수점 연산 오차로 인한 미세한 음수 방지
        var_total = max(0, var_total)

        # p95 로그 정규 분포 추정
        p95_estimated = calculate_log_normal_p95(weighted_mean, var_total)

        return pd.Series({'Mean_Latency': weighted_mean, 'p95_Latency': p95_estimated})

    # Order별 데이터 1차 집계
    test_runs = df.groupby([lock_col, 'Vuser', 'Order']).apply(get_test_metrics, include_groups=False).reset_index()

    # 2. Lock 종류 및 Vuser별 최종 요구 지표 산출
    latency_summary = test_runs.groupby([lock_col, 'Vuser']).agg(
        Worst_Mean_Latency=('Mean_Latency', 'max'),  # 가장 느린(최대) 평균 지연 시간
        Overall_Mean_Latency=('Mean_Latency', 'mean'),  # n번의 테스트 평균의 평균
        Best_Mean_Latency=('Mean_Latency', 'min'),  # 가장 빠른(최소) 평균 지연 시간
        Overall_p95_Latency=('p95_Latency', 'mean')  # p95의 평균
    ).reset_index()

    # 소수점 둘째 자리 반올림
    latency_summary = latency_summary.round(2)

    # 3. 지정된 순서대로 정렬 및 컬럼 이름 다듬기
    custom_lock_order = [
        'Pessimistic Lock',
        'Spin Lock',
        'Pub/Sub Lock',
        'ZooKeeper Lock',
        'Adaptive Lock'
    ]
    latency_summary[lock_col] = pd.Categorical(
        latency_summary[lock_col],
        categories=custom_lock_order,
        ordered=True
    )

    # 락 종류 -> Vuser 오름차순 다중 정렬
    latency_summary = latency_summary.sort_values(by=[lock_col, 'Vuser'], ascending=[True, True])

    # 언더바를 공백으로 변경 (출력/보고용 포맷)
    latency_summary = latency_summary.rename(columns={
        'Worst_Mean_Latency': 'Worst Mean Latency',
        'Overall_Mean_Latency': 'Overall Mean Latency',
        'Best_Mean_Latency': 'Best Mean Latency',
        'Overall_p95_Latency': 'Overall p95 Latency'
    })

    target_columns = ['Worst Mean Latency', 'Overall Mean Latency', 'Best Mean Latency', 'Overall p95 Latency']
    for col in target_columns:
        latency_summary[col] = latency_summary[col].apply(lambda x: f"{x:.2f}")

    # 결과물 저장
    os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
    latency_summary.to_csv(output_filepath, index=False)

    print(f"✅ Latency 분석 완료! '{output_filepath}'에 저장되었습니다.")
    print("\n[결과 데이터 상단 5행]")
    print(latency_summary.head(5).to_string(index=False))


if __name__ == "__main__":
    INPUT_FILEPATH = "../data/processed/ngrinder.csv"
    OUTPUT_FILEPATH = "../data/results/latency_ngrinder.csv"

    analyze_latency(INPUT_FILEPATH, OUTPUT_FILEPATH)
