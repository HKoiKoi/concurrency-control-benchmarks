import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def save_adaptive_vs_best_latency_chart(df, target_column, title, output_filepath):
    """
    4개의 락 중 지연 시간이 가장 짧은(Best) 수치를 추출하여 Adaptive Lock과 1:1 비교하는 막대 그래프
    """
    competitor_locks = ['Pessimistic Lock', 'Spin Lock', 'Pub/Sub Lock', 'ZooKeeper Lock']

    # 데이터 수치화
    df[target_column] = pd.to_numeric(df[target_column])

    vusers = sorted(df['Vuser'].unique())

    best_vals = []
    best_names = []
    adapt_vals = []

    for v in vusers:
        # 1. 4개 락 중 1위 찾기 (💡 지연 시간은 가장 '낮은' 값이 1위이므로 idxmin 사용)
        v_comp = df[(df['Vuser'] == v) & (df['Lock'].isin(competitor_locks))]
        best_idx = v_comp[target_column].idxmin()

        best_vals.append(v_comp.loc[best_idx, target_column])
        best_names.append(v_comp.loc[best_idx, 'Lock'].replace(' Lock', ''))

        # 2. Adaptive Lock 데이터 가져오기
        v_adapt = df[(df['Vuser'] == v) & (df['Lock'] == 'Adaptive Lock')]
        if v_adapt.empty:
            print(f"[경고] Vuser {v}에 대한 Adaptive Lock 데이터가 없습니다. 0으로 대체합니다.")
            adapt_vals.append(0)
        else:
            adapt_vals.append(v_adapt[target_column].values[0])

    # 그래프 그리기 준비
    fig, ax = plt.subplots(figsize=(10, 7))
    x_base = np.arange(len(vusers))
    width = 0.35

    # 막대 색상: Best 경쟁자(진한 회색), Adaptive(보라색/강조색)
    color_best = '#7f8c8d'
    color_adapt = '#9b59b6'

    # 막대 생성
    rects1 = ax.bar(x_base - width / 2, best_vals, width, color=color_best, label='Best of Others (Lowest)')
    rects2 = ax.bar(x_base + width / 2, adapt_vals, width, color=color_adapt, label='Adaptive Lock')

    # 스타일링
    ax.set_title(title, fontsize=16, fontweight='bold', pad=25)
    ax.set_xlabel('Vuser (Virtual Users)', fontsize=12, labelpad=10)
    ax.set_ylabel(f'{target_column} (ms)', fontsize=12, labelpad=10)
    ax.set_xticks(x_base)
    ax.set_xticklabels([f'Vuser {v}' for v in vusers], fontsize=11, fontweight='bold')

    # 범례 및 격자
    ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1), title='Comparison Group')
    ax.grid(axis='y', linestyle='--', alpha=0.6)

    # 수치 및 이름 표시 함수
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
                        xytext=(0, 5),
                        textcoords="offset points",
                        ha='center', va='bottom',
                        fontsize=10, fontweight='bold',
                        color='black')

    autolabel(rects1, best_vals, best_names)
    autolabel(rects2, adapt_vals)

    # Y축 상단 여유 확보 (텍스트 겹침 방지)
    all_vals = [v for v in best_vals + adapt_vals if v > 0]
    y_max = max(all_vals) if all_vals else 1
    plt.ylim(0, y_max * 1.25)
    plt.tight_layout()

    # 저장
    os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
    plt.savefig(output_filepath, dpi=600, bbox_inches='tight')
    plt.close()
    print(f"✅ VS 비교 그래프 저장 완료: {output_filepath}")


def main():
    INPUT_FILEPATH = "../data/results/latency_ngrinder.csv"

    if not os.path.exists(INPUT_FILEPATH):
        print("데이터 파일이 없습니다.")
        return

    df = pd.read_csv(INPUT_FILEPATH)

    # 1. Overall Mean Latency 비교 그래프
    save_adaptive_vs_best_latency_chart(
        df,
        target_column='Overall Mean Latency',
        title='Adaptive Lock vs Best Baseline Lock (Overall Mean Latency)',
        output_filepath='../data/figures/latency_mean_adaptive_vs_best.png'
    )

    # 2. Overall p95 Latency 비교 그래프
    save_adaptive_vs_best_latency_chart(
        df,
        target_column='Overall p95 Latency',
        title='Adaptive Lock vs Best Baseline Lock (Overall p95 Latency)',
        output_filepath='../data/figures/latency_p95_adaptive_vs_best.png'
    )


if __name__ == "__main__":
    main()
