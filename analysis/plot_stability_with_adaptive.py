import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def save_2sigma_comparison_chart(df, title, output_filepath):
    """
    Pessimistic Lock, Pub/Sub Lock, ADLF 세 가지 락의 2-Sigma(편차)를 고정적으로 비교 (Vusers 1,000 한정)
    """
    target_locks = ['Pessimistic Lock', 'Pub/Sub Lock', 'Adaptive Lock']
    df['2-Sigma'] = pd.to_numeric(df['2-Sigma'])

    # Vusers 1000 데이터만 필터링하여 단일 그룹 비교
    vusers = [1000]

    all_vals = []
    all_names = []

    for lock in target_locks:
        lock_vals = []
        lock_display_name = lock.replace(' Lock', '') if 'Adaptive' not in lock else 'ADLF'
        for v in vusers:
            val = df[(df['Vuser'] == v) & (df['Lock'] == lock)]['2-Sigma']
            lock_vals.append(float(val.values[0]) if not val.empty else 0.0)
        all_vals.append(lock_vals)
        all_names.append([lock_display_name] * len(vusers))

    # 오차 막대(errs_list)는 2-Sigma 자체를 그리는 차트이므로 None으로 전달
    _draw_bar_chart(vusers, all_vals, all_names, None, title, '2-Sigma Range', output_filepath, num_groups=3)


def _draw_bar_chart(vusers, vals_list, names_list, errs_list, title, ylabel, output_filepath, num_groups=2):
    """
    공통 바 차트 그리기 함수 (제공해주신 최적화 비율 그대로 적용)
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

    # 2-Sigma(오차 범위) 비교 그래프 생성 (Vusers 1000 한정)
    save_2sigma_comparison_chart(
        df,
        title='Comparison of 2-Sigma Range (1,000 Vusers): Pessimistic vs Pub/Sub vs ADLF',
        output_filepath='../data/figures/stability_comparison_with_adlf.png'
    )


if __name__ == "__main__":
    main()
