import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def plot_stability_mini_trends(input_filepath, output_filepath):
    """
    X축에 락 종류를 배치하고, 해당 락 영역 안에서 Vuser(500, 800, 1000) 증가에 따른
    지연 시간 변화를 선으로 이은 '미니 추세선(Mini-Trend)' 그래프를 생성합니다.
    """
    if not os.path.exists(input_filepath):
        print(f"'{input_filepath}' 파일을 찾을 수 없습니다.")
        return

    print(f"데이터를 불러옵니다: {input_filepath}")
    df = pd.read_csv(input_filepath)

    # 문자열로 저장된 수치 데이터를 숫자형으로 변환
    target_cols = ['Overall Mean Latency', '2-Sigma Lower Bound', '2-Sigma Upper Bound']
    for col in target_cols:
        df[col] = pd.to_numeric(df[col])

    target_locks = ['Pessimistic Lock', 'Spin Lock', 'Pub/Sub Lock', 'ZooKeeper Lock']
    vusers = [500, 800, 1000]

    # 락별 고유 색상 (의미 기반 배색 유지)
    semantic_colors = ['#34495e', '#e74c3c', '#3498db', '#27ae60']

    plt.figure(figsize=(14, 8))
    ax = plt.gca()

    # 락 영역 내에서 Vuser 점들을 좌우로 벌려줄 간격 (Span: -0.2 ~ 0.2)
    offsets = [-0.2, 0, 0.2]

    # 1. 락 종류별로 순회하며 독립된 미니 추세선 그리기
    for i, lock in enumerate(target_locks):
        # 해당 락의 데이터만 추출 후 Vuser 순서 보장
        subset = df[df['Lock'] == lock]
        subset = subset.set_index('Vuser').reindex(vusers).reset_index()

        means = subset['Overall Mean Latency'].values
        lowers = subset['2-Sigma Lower Bound'].values
        uppers = subset['2-Sigma Upper Bound'].values

        # 오차 막대 길이 계산 (음수 방지)
        yerr_lower = np.maximum(0, means - lowers)
        yerr_upper = np.maximum(0, uppers - means)
        yerr = [yerr_lower, yerr_upper]

        # 현재 락이 위치할 기본 X좌표(i)를 중심으로 Vuser 점들 분산 배치
        x_base = i
        x_pos = [x_base + off for off in offsets]

        # 꺾은선 + 오차 막대 그리기
        ax.errorbar(x_pos, means, yerr=yerr,
                    fmt='-o',
                    color=semantic_colors[i],
                    linewidth=3.0,  # 추세를 명확히 보기 위해 선을 조금 두껍게
                    markersize=8,
                    capsize=6,
                    capthick=2,
                    elinewidth=2,
                    label=lock,  # 범례에는 락 이름만 표시
                    alpha=0.85)

        # 평균값 및 Vuser 안내 텍스트 표시
        for j, mean_val in enumerate(means):
            if not np.isnan(mean_val):
                # 텍스트가 오차 막대에 가려지지 않도록 반투명 흰색 배경 추가
                bbox_props = dict(boxstyle="round,pad=0.2", facecolor='white', edgecolor='none', alpha=0.8)

                # 수치와 어떤 Vuser인지(예: 310 \n (v500)) 함께 표시
                ax.annotate(f'{mean_val:.0f}\n(v{vusers[j]})',
                            (x_pos[j], mean_val),
                            xytext=(0, 15), textcoords='offset points',
                            va='bottom', ha='center',
                            fontsize=9, color=semantic_colors[i], fontweight='bold',
                            bbox=bbox_props)

    # 그래프 전체 스타일링
    plt.title('Latency Stability (2-Sigma) Comparison', fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Lock Type', fontsize=12, labelpad=10)
    plt.ylabel('Latency (ms)', fontsize=12, labelpad=10)

    # X축 눈금을 락 이름으로 매핑
    plt.xticks(np.arange(len(target_locks)), target_locks, fontsize=12, fontweight='bold')
    plt.xlim(-0.5, len(target_locks) - 0.5)

    # 텍스트와 오차막대가 잘리지 않도록 상단, 하단 여유 공간 확보
    plt.ylim(bottom=0, top=df['2-Sigma Upper Bound'].max() * 1.15)

    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.legend(title='Lock Type', loc='upper left')

    # 저장
    plt.tight_layout()
    os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
    plt.savefig(output_filepath, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"✅ 미니 추세선 시각화 완료! '{output_filepath}'에 저장되었습니다.")


if __name__ == "__main__":
    INPUT_FILEPATH = "../data/results/stability_ngrinder.csv"
    OUTPUT_FILEPATH = "../data/figures/stability_comparison.png"

    plot_stability_mini_trends(INPUT_FILEPATH, OUTPUT_FILEPATH)
