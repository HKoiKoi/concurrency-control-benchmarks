import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def save_latency_bar_chart(df, target_column, title, output_filepath):
    """
    지연 시간 지표를 기준으로 Vuser별 4개 락을 비교하는 막대 그래프
    """
    target_locks = ['Pessimistic Lock', 'Spin Lock', 'Pub/Sub Lock', 'ZooKeeper Lock']

    plot_df = df[df['Lock'].isin(target_locks)].copy()
    plot_df[target_column] = pd.to_numeric(plot_df[target_column])

    pivot_df = plot_df.pivot(index='Vuser', columns='Lock', values=target_column)
    pivot_df = pivot_df[target_locks]

    semantic_colors = ['#34495e', '#e74c3c', '#3498db', '#27ae60']

    # figsize를 가로로 넓게 설정하여 막대 간 간격을 확보
    fig, ax = plt.subplots(figsize=(16, 8))
    pivot_df.plot(kind='bar', ax=ax, width=0.85, color=semantic_colors, zorder=2)

    plt.title(title, fontsize=16, fontweight='bold', pad=25)
    plt.xlabel('Number of Virtual Users (Vusers)', fontsize=12, labelpad=10)
    plt.ylabel(f'{target_column} (ms)', fontsize=12, labelpad=10)
    plt.xticks(rotation=0)
    plt.legend(title='Lock Type', loc='best')
    plt.grid(axis='y', linestyle='--', alpha=0.6, zorder=0)

    for i, lock_name in enumerate(target_locks):
        container = ax.containers[i]

        for p in container:
            height = p.get_height()

            if height > 0:
                label_text = f"{height:.2f}"
                y_pos = height

                # 바 차트는 bbox 없이 텍스트 높이 조절로 가독성 확보
                ax.annotate(label_text,
                            (p.get_x() + p.get_width() / 2., y_pos),
                            ha='center', va='bottom', multialignment='center',
                            xytext=(0, 6), textcoords='offset points',
                            fontsize=9, fontweight='bold', color='black', zorder=4)

    max_y_value = pivot_df.max().max()
    plt.ylim(0, max_y_value * 1.15)

    plt.tight_layout()

    os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
    plt.savefig(output_filepath, dpi=600, bbox_inches='tight')
    plt.close()
    print(f"✅ 바 차트 저장 완료: {output_filepath}")


def plot_stability_mini_trends(df, output_filepath):
    """
    X축에 락 종류를 배치하고, Vuser 증가에 따른 지연 시간 변화를 선으로 이은 미니 추세선 그래프 (2-Sigma 적용)
    """
    target_locks = ['Pessimistic Lock', 'Spin Lock', 'Pub/Sub Lock', 'ZooKeeper Lock']
    vusers = [500, 800, 1000]
    semantic_colors = ['#34495e', '#e74c3c', '#3498db', '#27ae60']

    df['Overall Mean Latency'] = pd.to_numeric(df['Overall Mean Latency'])
    df['2-Sigma'] = pd.to_numeric(df['2-Sigma'])

    plt.figure(figsize=(14, 8))
    ax = plt.gca()
    offsets = [-0.2, 0, 0.2]
    max_upper_bound = 0

    for i, lock in enumerate(target_locks):
        subset = df[df['Lock'] == lock].set_index('Vuser').reindex(vusers).reset_index()

        means = subset['Overall Mean Latency'].values
        two_sigmas = subset['2-Sigma'].values

        yerr_lower = np.minimum(means, two_sigmas)
        yerr_upper = two_sigmas
        yerr = [yerr_lower, yerr_upper]

        max_upper_bound = max(max_upper_bound, np.nanmax(means + two_sigmas))

        x_base = i
        x_pos = [x_base + off for off in offsets]

        ax.errorbar(x_pos, means, yerr=yerr, fmt='-o', color=semantic_colors[i],
                    linewidth=3.0, markersize=8, capsize=6, capthick=2, elinewidth=2,
                    label=lock, alpha=0.85, zorder=2)

        for j, mean_val in enumerate(means):
            if not np.isnan(mean_val):
                two_sigma_val = two_sigmas[j]

                label_text = f'{mean_val:.2f}\n(±{two_sigma_val:.2f})\n(v{vusers[j]})'
                bbox_props = dict(boxstyle="round,pad=0.2", facecolor='white', edgecolor='none', alpha=0.8)

                # Vusers 1000 (j == 2) 데이터일 때만 y_offset을 40으로 크게 주어 겹침 방지
                y_offset = 40 if j == 2 else 12

                ax.annotate(label_text,
                            (x_pos[j], mean_val),
                            xytext=(0, y_offset), textcoords='offset points',
                            ha='center', va='bottom', multialignment='center',
                            fontsize=9, color=semantic_colors[i],
                            fontweight='bold', zorder=4, bbox=bbox_props)

    plt.title('Comparison of Latency Consistency with 2-Sigma Bounds', fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Lock Type', fontsize=12, labelpad=10)
    plt.ylabel('Latency (ms)', fontsize=12, labelpad=10)
    plt.xticks(np.arange(len(target_locks)), target_locks, fontsize=12, fontweight='bold')
    plt.xlim(-0.5, len(target_locks) - 0.5)

    # 텍스트가 더 위로 솟아오른 것을 감안하여 Y축 천장을 1.35배로 넉넉하게 확장
    plt.ylim(bottom=0, top=max_upper_bound * 1.35)
    plt.grid(axis='y', linestyle='--', alpha=0.6, zorder=0)
    plt.legend(title='Lock Type', loc='best')

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
    plt.savefig(output_filepath, dpi=600, bbox_inches='tight')
    plt.close()
    print(f"✅ 안정성 비교(추세선) 그래프 저장 완료: {output_filepath}")


def run_latency_visual_analysis(input_path):
    if not os.path.exists(input_path):
        print(f"'{input_path}' 파일을 찾을 수 없습니다.")
        return

    print(f"데이터를 불러옵니다: {input_path}")
    df = pd.read_csv(input_path)

    # 1. Overall p95 Latency 비교 그래프
    save_latency_bar_chart(
        df,
        target_column='Overall p95 Latency',
        title='Comparison of Overall p95 Latency (ms)',
        output_filepath='../data/figures/latency_p95_comparison.png'
    )

    # 2. Stability 추세선 그래프
    plot_stability_mini_trends(
        df,
        output_filepath='../data/figures/stability_comparison.png'
    )


if __name__ == '__main__':
    INPUT_FILEPATH = '../data/results/latency_ngrinder.csv'
    run_latency_visual_analysis(INPUT_FILEPATH)
