import os

import matplotlib.pyplot as plt
import pandas as pd


def save_tps_bar_chart(df, target_column, title, output_filepath):
    """
    공통 막대 그래프 생성 함수: 특정 칼럼(Mean 또는 Peak)을 기준으로 Vuser별 4개 락 비교
    """
    target_locks = ['Pessimistic Lock', 'Spin Lock', 'Pub/Sub Lock', 'ZooKeeper Lock']

    # 1. 4개 락 필터링 및 데이터 복사
    plot_df = df[df['Lock'].isin(target_locks)].copy()
    plot_df[target_column] = plot_df[target_column].astype(float)

    # 2. 피벗 테이블 생성
    pivot_df = plot_df.pivot(index='Vuser', columns='Lock', values=target_column)
    pivot_df = pivot_df[target_locks]

    # 색상 설정 (Pessimistic: 남색, Spin: 빨강, Pub/Sub: 파랑, ZooKeeper: 초록)
    semantic_colors = ['#34495e', '#e74c3c', '#3498db', '#27ae60']

    # 3. 기본 막대 그래프 생성
    ax = pivot_df.plot(kind='bar', figsize=(14, 7), width=0.8, color=semantic_colors, zorder=2)

    # 4. 스타일링
    plt.title(title, fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Number of Virtual Users (Vusers)', fontsize=12, labelpad=10)
    plt.ylabel(f'{target_column} (req/s)', fontsize=12, labelpad=10)
    plt.xticks(rotation=0)
    plt.legend(title='Lock Type', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(axis='y', linestyle='--', alpha=0.7, zorder=0)

    # 5. 막대 위 수치 표시 (표준편차 병기 및 오차선 위로 위치 이동)
    for i, lock_name in enumerate(target_locks):
        container = ax.containers[i]

        for p in container:
            height = p.get_height()

            if height > 0:
                # 텍스트 내용 구성 (오차 값이 있으면 병기)
                label_text = f"{height:.2f}"
                y_pos = height

                ax.annotate(label_text,
                            (p.get_x() + p.get_width() / 2., y_pos),
                            ha='center', va='bottom',
                            xytext=(0, 6), textcoords='offset points',
                            fontsize=9, fontweight='bold', zorder=4,
                            bbox=dict(facecolor='white', edgecolor='none', alpha=0.8, pad=1.5))

    # 7. Y축 한계 설정 (텍스트가 2줄로 늘어나고 높아졌으므로 여백 크게 확보)
    max_y_value = pivot_df.max().max()
    plt.ylim(0, max_y_value * 1.15)

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

    # 1. Overall Mean TPS 비교 그래프 생성 (표준편차 사용)
    save_tps_bar_chart(
        df,
        target_column='Overall Mean TPS',
        title='Comparison of Overall Mean TPS (req/s)',
        output_filepath='../data/figures/tps_mean_comparison.png'
    )

    # 2. Mean Peak TPS 비교 그래프 생성 (에러바 없음)
    save_tps_bar_chart(
        df,
        target_column='Mean Peak TPS',
        title='Comparison of Mean Peak TPS (req/s)',
        output_filepath='../data/figures/tps_peak_comparison.png'
    )


if __name__ == "__main__":
    INPUT_FILEPATH = '../data/results/tps_ngrinder.csv'
    run_visual_analysis(INPUT_FILEPATH)
