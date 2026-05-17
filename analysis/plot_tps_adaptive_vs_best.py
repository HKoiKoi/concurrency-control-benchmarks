import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def save_adaptive_vs_best_chart(df, target_column, title, output_filepath, error_column=None):
    """
    4개의 락 중 가장 성능이 높은(Best) 수치를 추출하여 Adaptive Lock과 1:1 비교하는 막대 그래프
    (ADLF 라벨 추가 및 깔끔한 상단 여백 스타일 적용)
    """
    competitor_locks = ['Pessimistic Lock', 'Spin Lock', 'Pub/Sub Lock', 'ZooKeeper Lock']

    # 데이터 수치화
    df[target_column] = pd.to_numeric(df[target_column])

    vusers = sorted(df['Vuser'].unique())

    best_vals = []
    best_errs = []
    best_names = []

    adapt_vals = []
    adapt_errs = []
    adapt_names = []

    # 각 Vuser별로 Best 락과 Adaptive 락의 데이터 추출
    for v in vusers:
        # 1. 4개 락 중 1위(최고 수치) 찾기
        v_comp = df[(df['Vuser'] == v) & (df['Lock'].isin(competitor_locks))]
        best_idx = v_comp[target_column].idxmax()

        best_vals.append(v_comp.loc[best_idx, target_column])
        best_names.append(v_comp.loc[best_idx, 'Lock'].replace(' Lock', ''))

        if error_column and error_column in df.columns:
            best_errs.append(pd.to_numeric(v_comp.loc[best_idx, error_column]))
        else:
            best_errs.append(0)

        # 2. Adaptive Lock 데이터 가져오기
        v_adapt = df[(df['Vuser'] == v) & (df['Lock'] == 'Adaptive Lock')]
        adapt_names.append('ADLF')

        if v_adapt.empty:
            adapt_vals.append(0)
            adapt_errs.append(0)
        else:
            adapt_vals.append(v_adapt[target_column].values[0])
            if error_column and error_column in df.columns:
                adapt_errs.append(pd.to_numeric(v_adapt[error_column].values[0]))
            else:
                adapt_errs.append(0)

    # 그래프 그리기 준비
    fig, ax = plt.subplots(figsize=(10, 7))
    x_base = np.arange(len(vusers))
    width = 0.35

    color_best = '#7f8c8d'
    color_adapt = '#9b59b6'

    has_errors = any(e > 0 for e in best_errs + adapt_errs)

    # 막대 생성
    if has_errors:
        rects1 = ax.bar(x_base - width / 2, best_vals, width, color=color_best, label='Best of Others',
                        yerr=best_errs, capsize=5, ecolor='black', zorder=2)
        rects2 = ax.bar(x_base + width / 2, adapt_vals, width, color=color_adapt, label='ADLF',
                        yerr=adapt_errs, capsize=5, ecolor='black', zorder=2)
    else:
        rects1 = ax.bar(x_base - width / 2, best_vals, width, color=color_best, label='Best of Others', zorder=2)
        rects2 = ax.bar(x_base + width / 2, adapt_vals, width, color=color_adapt, label='ADLF', zorder=2)

    # 스타일링
    ax.set_title(title, fontsize=16, fontweight='bold', pad=25)
    ax.set_xlabel('Number of Virtual Users (Vusers)', fontsize=12, labelpad=10)
    ax.set_ylabel(f'{target_column} (req/s)', fontsize=12, labelpad=10)
    ax.set_xticks(x_base)
    ax.set_xticklabels([f'{v}' for v in vusers], fontsize=11)

    ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1), title='Comparison Group')
    ax.grid(axis='y', linestyle='--', alpha=0.6, zorder=0)

    # 수치 및 이름 표시 함수 (bbox 제거 및 여백 확대)
    def autolabel(rects, vals, names=None, errs=None):
        for i, rect in enumerate(rects):
            height = rect.get_height()
            err_val = errs[i] if errs else 0

            if height > 0:
                lines = []
                if names:
                    lines.append(f"[{names[i]}]")

                if err_val > 0:
                    lines.append(f"{vals[i]:.2f}\n(±{err_val:.2f})")
                else:
                    lines.append(f"{vals[i]:.2f}")

                label_text = "\n".join(lines)
                y_pos = height + err_val

                ax.annotate(label_text,
                            xy=(rect.get_x() + rect.get_width() / 2, y_pos),
                            xytext=(0, 12), textcoords="offset points",
                            ha='center', va='bottom', multialignment='center',
                            fontsize=10, fontweight='bold', zorder=4)

    autolabel(rects1, best_vals, names=best_names, errs=best_errs if has_errors else None)
    autolabel(rects2, adapt_vals, names=adapt_names, errs=adapt_errs if has_errors else None)

    # Y축 상단 여유 확보
    y_max_factor = 1.35 if has_errors else 1.25
    all_max_heights = [v + (e if has_errors else 0) for v, e in zip(best_vals + adapt_vals, best_errs + adapt_errs)]
    y_max = max(all_max_heights) if all_max_heights else 1
    plt.ylim(0, y_max * y_max_factor)
    plt.tight_layout()

    # 저장
    os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
    plt.savefig(output_filepath, dpi=600, bbox_inches='tight')
    plt.close()
    print(f"✅ VS 비교 그래프 저장 완료: {output_filepath}")


def main():
    INPUT_FILEPATH = "../data/results/tps_ngrinder.csv"

    if not os.path.exists(INPUT_FILEPATH):
        print(f"데이터 파일이 없습니다: {INPUT_FILEPATH}")
        return

    df = pd.read_csv(INPUT_FILEPATH)

    # 1. Mean TPS 비교 그래프
    save_adaptive_vs_best_chart(
        df,
        target_column='Overall Mean TPS',
        title='Comparison of Overall Mean TPS: ADLF vs Best Lock (req/s)',
        output_filepath='../data/figures/tps_mean_adaptive_vs_best.png',
        error_column='Std Dev TPS'
    )

    # 2. Peak TPS 비교 그래프
    save_adaptive_vs_best_chart(
        df,
        target_column='Mean Peak TPS',
        title='Comparison of Mean Peak TPS: ADLF vs Best Lock (req/s)',
        output_filepath='../data/figures/tps_peak_adaptive_vs_best.png'
    )


if __name__ == "__main__":
    main()
