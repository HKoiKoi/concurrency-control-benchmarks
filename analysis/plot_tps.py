import os

import matplotlib.pyplot as plt
import pandas as pd


def save_tps_bar_chart(df, target_column, title, output_filepath):
    """
    공통 막대 그래프 생성 함수: 특정 컬럼(Mean 또는 Peak)을 기준으로 Vuser별 4개 락 비교
    """
    target_locks = ['Pessimistic Lock', 'Spin Lock', 'Pub/Sub Lock', 'ZooKeeper Lock']

    # 1. 4개 락 필터링 및 데이터 재구성
    plot_df = df[df['Lock'].isin(target_locks)].copy()
    pivot_df = plot_df.pivot(index='Vuser', columns='Lock', values=target_column)
    pivot_df = pivot_df[target_locks]  # 순서 고정

    # 2. 그래프 설정 (의미 기반 배색 적용)
    # Pessimistic(남색), Spin(빨강), Pub/Sub(파랑), ZooKeeper(초록)
    semantic_colors = ['#34495e', '#e74c3c', '#3498db', '#27ae60']

    ax = pivot_df.plot(kind='bar', figsize=(14, 7), width=0.8, color=semantic_colors)

    # 3. 스타일링
    plt.title(title, fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Vuser (Virtual Users)', fontsize=12, labelpad=10)
    plt.ylabel(f'{target_column} (req/s)', fontsize=12, labelpad=10)
    plt.xticks(rotation=0)
    plt.legend(title='Lock Type', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    # 4. 막대 위 수치 표시 (소수점 2자리)
    for p in ax.patches:
        height = p.get_height()
        if height > 0:
            ax.annotate(f'{height:.2f}',
                        (p.get_x() + p.get_width() / 2., height),
                        ha='center', va='center',
                        xytext=(0, 9),
                        textcoords='offset points',
                        fontsize=9, fontweight='bold')

    plt.ylim(0, pivot_df.max().max() * 1.15)
    plt.tight_layout()

    # 저장
    os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
    plt.savefig(output_filepath, dpi=600, bbox_inches='tight')
    plt.close()
    print(f"✅ 그래프 저장 완료: {output_filepath}")


def run_visual_analysis(input_path):
    if not os.path.exists(input_path):
        print(f"'{input_path}' 파일을 찾을 수 없습니다.")
        return

    df = pd.read_csv(input_path)

    # 1. Overall Mean TPS 비교 그래프 생성
    save_tps_bar_chart(
        df,
        target_column='Overall Mean TPS',
        title='Overall Mean TPS Comparison (req/s)',
        output_filepath='../data/figures/tps_mean_comparison.png'
    )

    # 2. Average Peak TPS 비교 그래프 생성 (신규 추가)
    save_tps_bar_chart(
        df,
        target_column='Average Peak TPS',
        title='Average Peak TPS Comparison (req/s)',
        output_filepath='../data/figures/tps_peak_comparison.png'
    )


if __name__ == "__main__":
    INPUT_FILEPATH = "../data/results/tps_ngrinder.csv"
    run_visual_analysis(INPUT_FILEPATH)
