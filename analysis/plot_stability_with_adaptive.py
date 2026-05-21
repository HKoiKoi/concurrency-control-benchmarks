import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def save_2sigma_3way_comparison_chart(df, target_column, title, output_filepath):
    """
    비관적 락, Pub/Sub 락, ADLF 3자 비교 막대 그래프 (안정성: 2-Sigma)
    """
    target_locks = ['Pessimistic Lock', 'Pub/Sub Lock', 'Adaptive Lock']
    df[target_column] = pd.to_numeric(df[target_column])
    vusers = sorted(df['Vuser'].unique())

    all_vals = []
    all_names = []

    for lock in target_locks:
        lock_vals = []
        lock_display_name = lock.replace(' Lock', '') if 'Adaptive' not in lock else 'ADLF'
        for v in vusers:
            val = df[(df['Vuser'] == v) & (df['Lock'] == lock)][target_column]
            lock_vals.append(float(val.values[0]) if not val.empty else 0.0)
        all_vals.append(lock_vals)
        all_names.append([lock_display_name] * len(vusers))

    num_groups = 3

    # 1. 캔버스 전체 가로 너비
    chart_width = 8 if len(vusers) == 1 else 12
    fig, ax = plt.subplots(figsize=(chart_width, 7))

    x_base = np.arange(len(vusers))

    # 2. 막대 두께와 막대 사이 간격 조절
    if len(vusers) == 1:
        width = 0.45
        gap = 0.12
        ax.set_xlim(-0.8, 0.8)
    else:
        width = 0.85 / num_groups
        gap = 0.0
    # 3. 색상 설정 (통일성 유지)
    color_map = {'Pessimistic': '#34495e', 'Pub/Sub': '#3498db', 'ADLF': '#9b59b6'}

    rects_list = []
    for i in range(num_groups):
        color = color_map.get(all_names[i][0], '#7f8c8d')
        # 간격(gap)을 포함하여 각 막대의 X 좌표(offset) 계산
        offset = (i - (num_groups - 1) / 2) * (width + gap)

        r = ax.bar(x_base + offset, all_vals[i], width, color=color, label=all_names[i][0], zorder=2)
        rects_list.append(r)

    # 스타일링
    ax.set_title(title, fontsize=16, fontweight='bold', pad=25)
    ax.set_xlabel('Number of Virtual Users (Vusers)', fontsize=12, labelpad=10)
    ax.set_ylabel(f'{target_column} (ms)', fontsize=12, labelpad=10)
    ax.set_xticks(x_base)
    ax.set_xticklabels([f'{v}' for v in vusers], fontsize=11)

    ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1), title='Comparison Group')
    ax.grid(axis='y', linestyle='--', alpha=0.6, zorder=0)

    # 4. 라벨링
    for i in range(num_groups):
        for j, rect in enumerate(rects_list[i]):
            height = rect.get_height()
            if height > 0:
                label_text = f"[{all_names[i][j]}]\n{all_vals[i][j]:.2f}"

                y_offset = 12

                if all_names[i][j] == 'Pessimistic' and vusers[j] == 500:
                    y_offset = 15
                elif all_names[i][j] == 'Pub/Sub' and vusers[j] == 800:
                    y_offset = 15
                elif all_names[i][j] == 'Pub/Sub' and vusers[j] == 1000:
                    y_offset = 25

                ax.annotate(label_text,
                            xy=(rect.get_x() + rect.get_width() / 2, height),
                            xytext=(0, y_offset), textcoords="offset points",
                            ha='center', va='bottom', multialignment='center',
                            fontsize=10, fontweight='bold', zorder=4)

    # Y축 상단 여유 확보
    ax.set_ylim(bottom=0)
    y_max = max([max(v) for v in all_vals])
    ax.set_ylim(top=y_max * 1.35)

    plt.tight_layout()

    # 저장
    os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
    plt.savefig(output_filepath, dpi=600, bbox_inches='tight')
    plt.close()
    print(f"✅ 그래프 저장 완료: {output_filepath}")


def main():
    INPUT_FILEPATH = "../data/results/latency_ngrinder.csv"

    if not os.path.exists(INPUT_FILEPATH):
        print(f"데이터 파일이 없습니다: {INPUT_FILEPATH}")
        return

    df = pd.read_csv(INPUT_FILEPATH)

    # 2-Sigma(안정성) 3자 비교 그래프 생성
    save_2sigma_3way_comparison_chart(
        df,
        target_column='2-Sigma',
        title='Comparison of 2-Sigma Range: Pessimistic vs Pub/Sub vs ADLF (ms)',
        output_filepath='../data/figures/stability_2sigma_3way_comparison.png'
    )


if __name__ == "__main__":
    main()
