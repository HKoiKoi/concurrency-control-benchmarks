import os

import pandas as pd


def analyze_tps(input_filepath, output_filepath):
    """
    통합된 nGrinder 결과를 바탕으로 TPS(Mean, Peak)를 분석하여 요약된 CSV를 생성합니다.
    """
    if not os.path.exists(input_filepath):
        print(f"'{input_filepath}' 파일을 찾을 수 없습니다. 경로를 확인해주세요.")
        return

    print(f"데이터를 불러옵니다: {input_filepath}")
    df = pd.read_csv(input_filepath)

    lock_col = 'Lock'
    if lock_col not in df.columns:
        print(f"[오류] '{lock_col}' 컬럼이 데이터에 없습니다. 현재 컬럼: {list(df.columns)}")
        return

    test_runs = df.groupby([lock_col, 'Vuser', 'Order']).agg(
        Mean_TPS=('TPS', 'mean'),
        Peak_TPS=('TPS', 'max')
    ).reset_index()

    tps_summary = test_runs.groupby([lock_col, 'Vuser']).agg(
        Worst_Mean_TPS=('Mean_TPS', 'min'),
        Overall_Mean_TPS=('Mean_TPS', 'mean'),
        Best_Mean_TPS=('Mean_TPS', 'max'),
        Average_Peak_TPS=('Peak_TPS', 'mean'),
    ).reset_index()
    tps_summary = tps_summary.round(2)

    custom_lock_order = [
        'Pessimistic Lock',
        'Spin Lock',
        'Pub/Sub Lock',
        'ZooKeeper Lock',
        'Adaptive Lock'
    ]
    tps_summary[lock_col] = pd.Categorical(
        tps_summary[lock_col],
        categories=custom_lock_order,
        ordered=True
    )

    tps_summary = tps_summary.sort_values(by=[lock_col, 'Vuser'], ascending=[True, True])
    tps_summary = tps_summary.rename(columns={
        'Worst_Mean_TPS': 'Worst Mean TPS',
        'Overall_Mean_TPS': 'Overall Mean TPS',
        'Best_Mean_TPS': 'Best Mean TPS',
        'Average_Peak_TPS': 'Average Peak TPS'
    })

    target_columns = ['Worst Mean TPS', 'Overall Mean TPS', 'Best Mean TPS', 'Average Peak TPS']
    for col in target_columns:
        tps_summary[col] = tps_summary[col].apply(lambda x: f"{x:.2f}")

    os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
    tps_summary.to_csv(output_filepath, index=False)

    print(f"TPS 분석 완료! '{output_filepath}'에 저장되었습니다.")
    print("\n[최종 생성되는 데이터 미리보기]")
    print(tps_summary.head(3).to_string(index=False))


if __name__ == "__main__":
    INPUT_FILEPATH = '../data/processed/ngrinder.csv'
    OUTPUT_FILEPATH = '../data/results/tps_ngrinder.csv'

    analyze_tps(INPUT_FILEPATH, OUTPUT_FILEPATH)
