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
    p95 = np.exp(mu_log + 1.63385 * sigma_log)
    return p95


def analyze_latency_and_stability(input_filepath, output_filepath):
    """
    nGrinder 데이터를 바탕으로 통합 지연 시간 지표(Min/Max/Mean, p95, Sigma, 2-Sigma)를 산출합니다.
    """
    if not os.path.exists(input_filepath):
        print(f"'{input_filepath}' 파일을 찾을 수 없습니다.")
        return

    print(f"데이터를 불러옵니다: {input_filepath}")
    df = pd.read_csv(input_filepath)

    lock_col = 'Lock'
    if lock_col not in df.columns:
        print(f"[오류] '{lock_col}' 칼럼이 데이터에 없습니다.")
        return

    # ================================
    # 회차(Order)별 평균 및 p95 집계
    # ================================
    def get_test_metrics(group):
        n = group['Tests']
        mu = group['Mean_Test_Time_(ms)']
        sigma = group['Test_Time_Standard_Deviation_(ms)']

        total_n = n.sum()
        if total_n == 0:
            return pd.Series({'Mean_Latency': 0.0, 'p95_Latency': 0.0})

        weighted_mean = (n * mu).sum() / total_n
        ex2 = (sigma ** 2) + (mu ** 2)
        ex2_total = (n * ex2).sum() / total_n
        var_total = max(0, ex2_total - (weighted_mean ** 2))

        p95_estimated = calculate_log_normal_p95(weighted_mean, var_total)
        return pd.Series({'Mean_Latency': weighted_mean, 'p95_Latency': p95_estimated})

    # Order별 1차 집계 후 Vusers별 평균(Overall) 도출
    test_runs = df.groupby([lock_col, 'Vuser', 'Order']).apply(get_test_metrics, include_groups=False).reset_index()
    latency_summary = test_runs.groupby([lock_col, 'Vuser']).agg(
        Worst_Mean_Latency=('Mean_Latency', 'max'),
        Overall_Mean_Latency=('Mean_Latency', 'mean'),
        Best_Mean_Latency=('Mean_Latency', 'min'),
        Overall_p95_Latency=('p95_Latency', 'mean'),
    ).reset_index()

    # ================================
    # 회차(Order)별 평균 및 p95 집계
    # ================================
    def get_stability_metrics(group):
        n = group['Tests']
        mu = group['Mean_Test_Time_(ms)']
        sigma = group['Test_Time_Standard_Deviation_(ms)']

        total_n = n.sum()
        if total_n == 0:
            return pd.Series({'Overall_Std_Dev': 0.0, 'Two_Sigma': 0.0})

        mu_total = (n * mu).sum() / total_n

        if total_n <= 1:
            return pd.Series({'Overall_Std_Dev': 0.0, 'Two_Sigma': 0.0})

        ss_within = (np.maximum(0, n - 1) * (sigma ** 2)).sum()
        ss_between = (n * ((mu - mu_total) ** 2)).sum()
        sigma_total = np.sqrt(max(0, (ss_within + ss_between) / (total_n - 1)))

        return pd.Series({
            'Overall_Std_Dev': sigma_total,
            'Two_Sigma': 2 * sigma_total,
        })

    # 전체 데이터 기준 통합 표준편차 추출
    stability_summary = df.groupby([lock_col, 'Vuser']).apply(get_stability_metrics,
                                                              include_groups=False).reset_index()

    # ================================
    # 데이터 병합 및 포맷팅
    # ================================
    # 두 요약 데이터를 Lock과 Vuser를 기준으로 병합
    final_summary = pd.merge(latency_summary, stability_summary, on=[lock_col, 'Vuser'])

    # 정렬 및 카테고리화
    custom_lock_order = ['Pessimistic Lock', 'Spin Lock', 'Pub/Sub Lock', 'ZooKeeper Lock', 'Adaptive Lock']
    final_summary[lock_col] = pd.Categorical(final_summary[lock_col], categories=custom_lock_order, ordered=True)
    final_summary = final_summary.sort_values(by=[lock_col, 'Vuser'], ascending=[True, True])

    # 컬럼명 정리
    final_summary = final_summary.rename(columns={
        'Worst_Mean_Latency': 'Worst Mean Latency',
        'Overall_Mean_Latency': 'Overall Mean Latency',
        'Best_Mean_Latency': 'Best Mean Latency',
        'Overall_p95_Latency': 'Overall p95 Latency',
        'Overall_Std_Dev': 'Overall Std Dev',
        'Two_Sigma': '2-Sigma'
    })

    # 소수점 포맷팅
    target_columns = ['Worst Mean Latency', 'Overall Mean Latency', 'Best Mean Latency', 'Overall p95 Latency',
                      'Overall Std Dev', '2-Sigma']
    for col in target_columns:
        final_summary[col] = final_summary[col].apply(lambda x: f"{float(x):.2f}")

    # 결과물 저장
    os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
    final_summary.to_csv(output_filepath, index=False)

    print(f"통합 Latency 분석 완료! '{output_filepath}'에 저장되었습니다.")
    print("\n[결과 데이터 상단 3행]")
    print(final_summary.head(3).to_string(index=False))


if __name__ == '__main__':
    INPUT_FILEPATH = '../data/processed/ngrinder.csv'
    OUTPUT_FILEPATH = '../data/results/latency_ngrinder.csv'

    analyze_latency_and_stability(INPUT_FILEPATH, OUTPUT_FILEPATH)
