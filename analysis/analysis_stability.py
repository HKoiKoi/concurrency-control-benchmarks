import os

import numpy as np
import pandas as pd


def analyze_stability(input_filepath, output_filepath):
    """
    nGrinder 통합 데이터를 바탕으로 통합 표준편차(sigma)와 2-Sigma 신뢰구간을 분석합니다.
    """
    if not os.path.exists(input_filepath):
        print(f"'{input_filepath}' 파일을 찾을 수 없습니다.")
        return

    print(f"데이터를 불러옵니다: {input_filepath}")
    df = pd.read_csv(input_filepath)

    # 컬럼명 유연성 확보
    lock_col = 'Lock'
    if lock_col not in df.columns:
        print(f"[오류] '{lock_col}' 컬럼이 데이터에 없습니다. 현재 컬럼: {list(df.columns)}")
        return

    # 핵심 분석 로직: Lock과 Vuser 단위로 묶어서 한 번에 모든 수식 처리
    def get_stability_metrics(group):
        n = group['Tests']
        mu = group['Mean_Test_Time_(ms)']
        sigma = group['Test_Time_Standard_Deviation_(ms)']

        N = n.sum()  # 전체 요청 건수 (Sigma n_i)

        # 데이터가 없을 경우 방어 코드
        if N == 0:
            return pd.Series({
                'Overall Mean Latency': 0.0, 'Overall Std Dev': 0.0, '2-Sigma': 0.0,
                '2-Sigma Lower Bound': 0.0, '2-Sigma Upper Bound': 0.0
            })

        # 1. mu_total (전체 가중 평균) 계산
        mu_total = (n * mu).sum() / N

        if N <= 1:  # 데이터가 1개뿐이라 분산 계산이 불가능한 경우
            return pd.Series({
                'Overall Mean Latency': mu_total, 'Overall Std Dev': 0.0, '2-Sigma': 0.0,
                '2-Sigma Lower Bound': mu_total, '2-Sigma Upper Bound': mu_total
            })

        # 2. SS_within (그룹 내 제곱합)
        # n_i - 1 이 음수가 되지 않도록 방어 (np.maximum)
        ss_within = (np.maximum(0, n - 1) * (sigma ** 2)).sum()

        # 3. SS_between (그룹 간 제곱합)
        ss_between = (n * ((mu - mu_total) ** 2)).sum()

        # 4. 최종 통합 표준편차 (sigma_total)
        # 부동소수점 오차로 인한 미세한 음수 방지 (max)
        sigma_total = np.sqrt(max(0, (ss_within + ss_between) / (N - 1)))

        two_sigma = 2 * sigma_total

        # 5. 2-Sigma 신뢰 구간 도출
        lower_bound = max(0, mu_total - two_sigma)
        upper_bound = mu_total + two_sigma

        return pd.Series({
            'Overall Mean Latency': mu_total,
            'Overall Std Dev': sigma_total,
            '2-Sigma': two_sigma,
            '2-Sigma Lower Bound': lower_bound,
            '2-Sigma Upper Bound': upper_bound
        })

    # 그룹화 및 수식 적용 (Pandas 경고 방지를 위한 include_groups=False 추가)
    stability_summary = df.groupby([lock_col, 'Vuser']).apply(get_stability_metrics, include_groups=False).reset_index()

    # 정렬을 위한 Categorical 설정
    custom_lock_order = [
        'Pessimistic Lock',
        'Spin Lock',
        'Pub/Sub Lock',
        'ZooKeeper Lock',
        'Adaptive Lock'
    ]
    stability_summary[lock_col] = pd.Categorical(
        stability_summary[lock_col],
        categories=custom_lock_order,
        ordered=True
    )

    # 락 종류 -> Vuser 다중 정렬
    stability_summary = stability_summary.sort_values(by=[lock_col, 'Vuser'], ascending=[True, True])

    # 출력할 칼럼 순서 재배치
    cols = [lock_col, 'Vuser', 'Overall Mean Latency', 'Overall Std Dev', '2-Sigma', '2-Sigma Lower Bound',
            '2-Sigma Upper Bound']
    stability_summary = stability_summary[cols]

    # 모든 숫자 데이터를 강제로 소수점 둘째 자리 문자열("0.00")로 포맷팅
    target_columns = ['Overall Mean Latency', 'Overall Std Dev', '2-Sigma', '2-Sigma Lower Bound',
                      '2-Sigma Upper Bound']
    for col in target_columns:
        stability_summary[col] = stability_summary[col].apply(lambda x: f"{x:.2f}")

    # 결과물 저장
    os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
    stability_summary.to_csv(output_filepath, index=False)

    print(f"✅ 안정성(2-Sigma) 분석 완료! '{output_filepath}'에 저장되었습니다.")
    print("\n[결과 데이터 상단 3행]")
    print(stability_summary.head(3).to_string(index=False))


if __name__ == "__main__":
    # 데이터 경로 설정
    INPUT_FILEPATH = "../data/processed/ngrinder.csv"
    OUTPUT_FILEPATH = "../data/results/stability_ngrinder.csv"

    analyze_stability(INPUT_FILEPATH, OUTPUT_FILEPATH)
