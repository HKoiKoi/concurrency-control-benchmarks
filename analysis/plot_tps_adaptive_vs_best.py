import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def save_adaptive_vs_best_chart(df, target_column, title, output_filepath):
    """
    4개의 락 중 가장 성능이 높은(Best) 수치를 추출하여 Adaptive Lock과 1:1 비교하는 막대 그래프
    """
    competitor_locks = ['Pessimistic Lock', 'Spin Lock', 'Pub/Sub Lock', 'ZooKeeper Lock']

    # 데이터 수치화
    df[target_column] = pd.to_numeric(df[target_column])

    vusers = sorted(df['Vuser'].unique())

    best_vals = []
    best_names = []
    adapt_vals = []

    # 각 Vuser별로 Best 락과 Adaptive 락의 데이터 추출
    for v in vusers:
        # 1. 4개 락 중 1위(최고 수치) 찾기
        v_comp = df[(df['Vuser'] == v) & (df['Lock'].isin(competitor_locks))]
        best_idx = v_comp[target_column].idxmax()  # 가장 높은 값의 인덱스

        best_vals.append(v_comp.loc[best_idx, target_column])
        # 락 이름에서 ' Lock' 글자를 빼고 짧게 저장 (예: Pub/Sub Lock -> Pub/Sub)
        best_names.append(v_comp.loc[best_idx, 'Lock'].replace(' Lock', ''))

        # 2. Adaptive Lock 데이터 가져오기
        v_adapt = df[(df['Vuser'] == v) & (df['Lock'] == 'Adaptive Lock')]
        adapt_vals.append(v_adapt[target_column].values[0] if not v_adapt.empty else 0)

    # 그래프 그리기 준비
    fig, ax = plt.subplots(figsize=(10, 7))
    x_base = np.arange(len(vusers))
    width = 0.35

    # 막대 색상: Best 경쟁자(진한 회색), Adaptive(보라색/강조색)
    color_best = '#7f8c8d'
    color_adapt = '#9b59b6'

    # 막대 생성
    rects1 = ax.bar(x_base - width / 2, best_vals, width, color=color_best, label='Best of Others')
    rects2 = ax.bar(x_base + width / 2, adapt_vals, width, color=color_adapt, label='Adaptive Lock')

    # 스타일링
    ax.set_title(title, fontsize=16, fontweight='bold', pad=25)
    ax.set_xlabel('Vuser (Virtual Users)', fontsize=12, labelpad=10)
    ax.set_ylabel(f'{target_column} (req/s)', fontsize=12, labelpad=10)
    ax.set_xticks(x_base)
    ax.set_xticklabels([f'Vuser {v}' for v in vusers], fontsize=11, fontweight='bold')

    # 범례 및 격자
    ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1), title='Comparison Group')
    ax.grid(axis='y', linestyle='--', alpha=0.6)

    # 수치 및 이름 표시 함수 (막대 상단)
    def autolabel(rects, vals, names=None):
        for i, rect in enumerate(rects):
            height = rect.get_height()

            # Best의 경우 어떤 락이 1위를 했는지 이름도 같이 표시
            if names:
                label_text = f"[{names[i]}]\n{vals[i]:.2f}"
            else:
                label_text = f"{vals[i]:.2f}"

            ax.annotate(label_text,
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 5),  # 5포인트 위로
                        textcoords="offset points",
                        ha='center', va='bottom',
                        fontsize=10, fontweight='bold',
                        color='black')

    autolabel(rects1, best_vals, best_names)  # Best 막대 위에는 락 이름 명시
    autolabel(rects2, adapt_vals)  # Adaptive 막대 위에는 수치만

    # Y축 상단 여유 20% 확보 (텍스트 겹침 방지)
    plt.ylim(0, max(max(best_vals), max(adapt_vals)) * 1.25)
    plt.tight_layout()

    # 저장
    os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
    plt.savefig(output_filepath, dpi=600, bbox_inches='tight')
    plt.close()
    print(f"✅ VS 비교 그래프 저장 완료: {output_filepath}")


def main():
    INPUT_FILEPATH = "../data/results/tps_ngrinder.csv"

    if not os.path.exists(INPUT_FILEPATH):
        print("데이터 파일이 없습니다.")
        return

    df = pd.read_csv(INPUT_FILEPATH)

    # 1. Mean TPS 비교 그래프
    save_adaptive_vs_best_chart(
        df,
        target_column='Overall Mean TPS',
        title='Adaptive Lock vs Best Baseline Lock (Overall Mean TPS)',
        output_filepath='../data/figures/tps_mean_adaptive_vs_best.png'
    )

    # 2. Peak TPS 비교 그래프
    save_adaptive_vs_best_chart(
        df,
        target_column='Average Peak TPS',
        title='Adaptive Lock vs Best Baseline Lock (Average Peak TPS)',
        output_filepath='../data/figures/tps_peak_adaptive_vs_best.png'
    )


if __name__ == "__main__":
    main()
