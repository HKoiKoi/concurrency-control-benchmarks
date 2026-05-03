import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def save_latency_bar_chart(df, target_column, title, output_filepath, err_column=None):
    """
    지연 시간 지표(Mean, p95)를 기준으로 Vuser별 4개 락을 비교하는 막대 그래프를 생성합니다.
    """
    target_locks = ['Pessimistic Lock', 'Spin Lock', 'Pub/Sub Lock', 'ZooKeeper Lock']

    plot_df = df[df['Lock'].isin(target_locks)].copy()
    plot_df[target_column] = pd.to_numeric(plot_df[target_column])
    if err_column:
        plot_df[err_column] = pd.to_numeric(plot_df[err_column])

    pivot_df = plot_df.pivot(index='Vuser', columns='Lock', values=target_column)
    pivot_df = pivot_df[target_locks]

    semantic_colors = ['#34495e', '#e74c3c', '#3498db', '#27ae60']

    ax = pivot_df.plot(kind='bar', figsize=(14, 7), width=0.8, color=semantic_colors, zorder=2)

    if err_column:
        pivot_err = plot_df.pivot(index='Vuser', columns='Lock', values=err_column)[target_locks]

        for i, lock_name in enumerate(target_locks):
            container = ax.containers[i]
            means = pivot_df[lock_name].values
            errs = pivot_err[lock_name].values
            x_pos = [rect.get_x() + rect.get_width() / 2.0 for rect in container]
            ax.errorbar(x_pos, means, yerr=errs, fmt='none', ecolor='black', capsize=5, capthick=1.5, zorder=3)

    plt.title(title, fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Number of Virtual Users (Vusers)', fontsize=12, labelpad=10)
    plt.ylabel(f'{target_column} (ms)', fontsize=12, labelpad=10)
    plt.xticks(rotation=0)
    plt.legend(title='Lock Type', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(axis='y', linestyle='--', alpha=0.7, zorder=0)

    for i, lock_name in enumerate(target_locks):
        container = ax.containers[i]
        for j, p in enumerate(container):
            height = p.get_height()
            if height > 0:
                ax.annotate(f'{height:.2f}',
                            (p.get_x() + p.get_width() / 2., height),
                            ha='center', va='bottom',
                            xytext=(0, 4), textcoords='offset points',
                            fontsize=9, fontweight='bold', zorder=4,
                            bbox=dict(facecolor='white', edgecolor='none', alpha=0.8, pad=1.5))

    if err_column:
        max_y_value = (plot_df[target_column] + plot_df[err_column]).max()
    else:
        max_y_value = pivot_df.max().max()

    plt.ylim(0, max_y_value * 1.15)
    plt.tight_layout()

    os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
    plt.savefig(output_filepath, dpi=600, bbox_inches='tight')
    plt.close()
    print(f"그래프 저장 완료: {output_filepath}")


def plot_stability_mini_trends(df, output_filepath):
    """
    X축에 락 종류를 배치하고, Vuser 증가에 따른 지연 시간 변화를 선으로 이은 미니 추세선 그래프 (2-Sigma 적용)
    """
    target_locks = ['Pessimistic Lock', 'Spin Lock', 'Pub/Sub Lock', 'ZooKeeper Lock']
    vusers = [500, 800, 1000]
    semantic_colors = ['#34495e', '#e74c3c', '#3498db', '#27ae60']

    # 필요한 컬럼 숫자로 변환
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

        # CSV에 하/상한값이 없으므로 즉석에서 오차 막대 길이 계산 (음수 돌파 방지)
        yerr_lower = np.minimum(means, two_sigmas)
        yerr_upper = two_sigmas
        yerr = [yerr_lower, yerr_upper]

        # 최대 상한값 갱신 (Y축 스케일링용)
        max_upper_bound = max(max_upper_bound, np.nanmax(means + two_sigmas))

        x_base = i
        x_pos = [x_base + off for off in offsets]

        ax.errorbar(x_pos, means, yerr=yerr, fmt='-o', color=semantic_colors[i],
                    linewidth=3.0, markersize=8, capsize=6, capthick=2, elinewidth=2,
                    label=lock, alpha=0.85)

        for j, mean_val in enumerate(means):
            if not np.isnan(mean_val):
                bbox_props = dict(boxstyle="round,pad=0.2", facecolor='white', edgecolor='none', alpha=0.8)
                ax.annotate(f'{mean_val:.0f}\n(v{vusers[j]})',
                            (x_pos[j], mean_val), xytext=(0, 15), textcoords='offset points',
                            va='bottom', ha='center', fontsize=9, color=semantic_colors[i],
                            fontweight='bold', bbox=bbox_props)

    plt.title('Comparison of Latency Consistency with 2-Sigma Bounds', fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Lock Type', fontsize=12, labelpad=10)
    plt.ylabel('Latency (ms)', fontsize=12, labelpad=10)
    plt.xticks(np.arange(len(target_locks)), target_locks, fontsize=12, fontweight='bold')
    plt.xlim(-0.5, len(target_locks) - 0.5)
    plt.ylim(bottom=0, top=max_upper_bound * 1.15)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.legend(title='Lock Type', loc='upper left')

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
    plt.savefig(output_filepath, dpi=600, bbox_inches='tight')
    plt.close()
    print(f"그래프 저장 완료: {output_filepath}")


def run_latency_visual_analysis(input_path):
    if not os.path.exists(input_path):
        print(f"'{input_path}' 파일을 찾을 수 없습니다.")
        return

    print(f"데이터를 불러옵니다: {input_path}")
    df = pd.read_csv(input_path)

    # 1. Overall Mean Latency 비교 그래프 (표준편차 오차 막대 포함)
    save_latency_bar_chart(
        df,
        target_column='Overall Mean Latency',
        title='Comparison of Overall Mean Latency (ms)',
        output_filepath='../data/figures/latency_mean_comparison.png',
        err_column='Overall Std Dev'
    )

    # 2. Overall p95 Latency 비교 그래프 (오차 막대 없음)
    save_latency_bar_chart(
        df,
        target_column='Overall p95 Latency',
        title='Comparison of Overall p95 Latency (ms)',
        output_filepath='../data/figures/latency_p95_comparison.png'
    )

    # 3. Stability 추세선 그래프 (2-Sigma 적용)
    plot_stability_mini_trends(
        df,
        output_filepath='../data/figures/stability_comparison.png'
    )


if __name__ == '__main__':
    INPUT_FILEPATH = '../data/results/latency_ngrinder.csv'
    run_latency_visual_analysis(INPUT_FILEPATH)
