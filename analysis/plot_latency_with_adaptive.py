import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def save_adaptive_vs_best_latency_chart(df, target_column, title, output_filepath, error_column=None):
    """
    [기존 로직] 4개의 락 중 지연 시간이 가장 짧은(Best) 수치를 추출하여 Adaptive Lock과 1:1 비교
    (Overall Mean Latency에 사용)
    """
    competitor_locks = ['Pessimistic Lock', 'Spin Lock', 'Pub/Sub Lock', 'ZooKeeper Lock']
    df[target_column] = pd.to_numeric(df[target_column])
    vusers = sorted(df['Vuser'].unique())

    best_vals, best_names, best_errs = [], [], []
    adapt_vals, adapt_names, adapt_errs = [], [], []

    for v in vusers:
        v_comp = df[(df['Vuser'] == v) & (df['Lock'].isin(competitor_locks))]
        best_idx = v_comp[target_column].idxmin()
        best_vals.append(float(v_comp.loc[best_idx, target_column]))
        best_names.append(v_comp.loc[best_idx, 'Lock'].replace(' Lock', ''))
        best_errs.append(float(v_comp.loc[best_idx, error_column]) if error_column else 0.0)

        v_adapt = df[(df['Vuser'] == v) & (df['Lock'] == 'Adaptive Lock')]
        adapt_names.append('ADLF')
        if v_adapt.empty:
            adapt_vals.append(0.0);
            adapt_errs.append(0.0)
        else:
            adapt_vals.append(float(v_adapt[target_column].values[0]))
            adapt_errs.append(float(v_adapt[error_column].values[0]) if error_column else 0.0)

    _draw_bar_chart(vusers, [best_vals, adapt_vals], [best_names, adapt_names],
                    [best_errs, adapt_errs] if error_column else None,
                    title, target_column, output_filepath, num_groups=2)


def save_p95_comparison_chart(df, title, output_filepath):
    """
    [신규 로직] Pessimistic Lock, Pub/Sub Lock, ADLF 세 가지를 고정적으로 비교 (Vusers 1,000 한정)
    """
    target_locks = ['Pessimistic Lock', 'Pub/Sub Lock', 'Adaptive Lock']
    df['Overall p95 Latency'] = pd.to_numeric(df['Overall p95 Latency'])

    # Vusers 1000 데이터만 필터링하여 단일 그룹 비교
    vusers = [1000]

    all_vals = []
    all_names = []

    for lock in target_locks:
        lock_vals = []
        lock_display_name = lock.replace(' Lock', '') if 'Adaptive' not in lock else 'ADLF'
        for v in vusers:
            val = df[(df['Vuser'] == v) & (df['Lock'] == lock)]['Overall p95 Latency']
            lock_vals.append(float(val.values[0]) if not val.empty else 0.0)
        all_vals.append(lock_vals)
        all_names.append([lock_display_name] * len(vusers))

    _draw_bar_chart(vusers, all_vals, all_names, None, title, 'Overall p95 Latency', output_filepath, num_groups=3)


def _draw_bar_chart(vusers, vals_list, names_list, errs_list, title, ylabel, output_filepath, num_groups=2):
    """
    공통 바 차트 그리기 함수
    """
    # 1. 캔버스 전체 가로 너비
    chart_width = 8 if len(vusers) == 1 else 12
    fig, ax = plt.subplots(figsize=(chart_width, 7))

    x_base = np.arange(len(vusers))

    # 2. 막대 두께와 막대 사이 간격 조절 로직
    if len(vusers) == 1:
        width = 0.35  # 막대의 실제 두께
        gap = 0.12  # 막대와 막대 사이의 빈 공간(간격)
        ax.set_xlim(-0.8, 0.8)  # 3. 그래프 양옆 여백
    else:
        width = 0.8 / num_groups
        gap = 0.0  # 여러 Vuser 그룹이 있을 때는 서로 붙어있는 것이 정석이므로 간격 0

    # 색상 설정
    color_map = {'Pessimistic': '#34495e', 'Pub/Sub': '#3498db', 'ADLF': '#9b59b6', 'Spin': '#e74c3c',
                 'ZooKeeper': '#27ae60'}

    rects_list = []
    for i in range(num_groups):
        color = color_map.get(names_list[i][0], '#7f8c8d')

        # 간격(gap)을 포함하여 각 막대의 X 좌표(offset) 계산
        offset = (i - (num_groups - 1) / 2) * (width + gap)

        yerr = None
        if errs_list:
            lower_err = [min(v, e) for v, e in zip(vals_list[i], errs_list[i])]
            yerr = np.vstack([lower_err, errs_list[i]])

        r = ax.bar(x_base + offset, vals_list[i], width, color=color, label=names_list[i][0], yerr=yerr, capsize=5,
                   zorder=2)
        rects_list.append(r)

    ax.set_title(title, fontsize=16, fontweight='bold', pad=25)
    ax.set_xlabel('Number of Virtual Users (Vusers)', fontsize=12, labelpad=10)
    ax.set_ylabel(f'{ylabel} (ms)', fontsize=12, labelpad=10)
    ax.set_xticks(x_base)
    ax.set_xticklabels([f'{v}' for v in vusers], fontsize=11)

    ax.legend(loc='upper left', bbox_to_anchor=(1.05, 1), title='Comparison Group')
    ax.grid(axis='y', linestyle='--', alpha=0.6, zorder=0)

    # 라벨링
    for i in range(num_groups):
        for j, rect in enumerate(rects_list[i]):
            height = rect.get_height()
            err_val = errs_list[i][j] if errs_list else 0
            if height > 0:
                label_text = f"[{names_list[i][j]}]\n{vals_list[i][j]:.2f}"
                if err_val > 0:
                    label_text += f"\n(±{err_val:.2f})"

                ax.annotate(label_text,
                            xy=(rect.get_x() + rect.get_width() / 2, height + err_val),
                            xytext=(0, 12), textcoords="offset points",
                            ha='center', va='bottom', multialignment='center',
                            fontsize=10, fontweight='bold', zorder=4)

    ax.set_ylim(bottom=0)
    y_max = max([max(v) + (max(e) if errs_list else 0) for v, e in
                 zip(vals_list, errs_list if errs_list else [[0] * len(vusers)] * num_groups)])
    ax.set_ylim(top=y_max * 1.35)

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
    plt.savefig(output_filepath, dpi=600, bbox_inches='tight')
    plt.close()
    print(f"✅ 그래프 저장 완료: {output_filepath}")


def main():
    INPUT_FILEPATH = "../data/results/latency_ngrinder.csv"
    if not os.path.exists(INPUT_FILEPATH):
        print("데이터 파일이 없습니다.")
        return
    df = pd.read_csv(INPUT_FILEPATH)

    save_adaptive_vs_best_latency_chart(
        df,
        target_column='Overall Mean Latency',
        title='Comparison of Overall Mean Latency: ADLF vs Best Lock (ms)',
        output_filepath='../data/figures/latency_mean_adaptive_vs_best.png',
        error_column='Overall Std Dev'
    )

    save_p95_comparison_chart(
        df,
        title='Comparison of p95 Latency (1,000 Vusers): Pessimistic vs Pub/Sub vs ADLF',
        output_filepath='../data/figures/latency_p95_comparison_with_adlf.png'
    )


if __name__ == "__main__":
    main()
