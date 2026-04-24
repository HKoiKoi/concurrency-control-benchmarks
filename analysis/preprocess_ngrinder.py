import os
from pathlib import Path

import pandas as pd


def preprocess_ngrinder_data(base_data_dir, output_filepath):
    """
    여러 디렉터리에 분산된 nGrinder 결과 CSV 파일을 하나로 병합합니다.
    파일명과 폴더명에서 메타데이터를 추출하여 데이터프레임의 새로운 칼럼으로 추가합니다.
    """
    # 탐색할 최상위 경로 객체 생성
    base_path = Path(base_data_dir)

    # '**/*result.csv' 패턴으로 하위의 모든 결과 파일 탐색
    all_csv_files = list(base_path.rglob('*result.csv'))

    if not all_csv_files:
        print(f"'{base_data_dir}' 경로에서 처리할 CSV 파일을 찾을 수 없습니다.")
        return

    print(f"총 {len(all_csv_files)}개의 CSV 파일을 발견했습니다. 병합을 시작합니다...")

    lock_name_mapping = {
        'pessimistic-lock': 'Pessimistic Lock',
        'spin-lock': 'Spin Lock',
        'pub-sub-lock': 'Pub/Sub Lock',
        'zookeeper-lock': 'ZooKeeper Lock',
        'adaptive-lock': 'Adaptive Lock',
    }

    df_list = []

    for file_path in all_csv_files:
        try:
            # 파일이 위치한 폴더명 추출 (e.g., '1st-test', '2nd-test', etc.)
            test_phase = file_path.parent.name

            # 파일명에서 정보 추출
            filename_stem = file_path.name.replace('-result.csv', '')
            parts = filename_stem.split('-')

            # 락 종류, Vuser, 테스트 수 추출
            # e.g., parts = ['pessimistic', 'lock', '500', '1']
            if len(parts) >= 3:
                vuser_count = int(parts[-2])
                order = int(parts[-1])
                lock_type_raw = '-'.join(parts[:-2])

                # 딕셔너리에 있으면 변환된 이름 사용, 없으면 원래 이름 사용
                lock_type = lock_name_mapping.get(lock_type_raw, lock_type_raw)
            else:
                lock_type = 'unknown'
                vuser_count = 0
                order = 0

            # CSV 파일 읽기
            df = pd.read_csv(file_path)

            # 추출한 메타데이터 추가
            df['Order'] = order
            df['Lock'] = lock_type
            df['Vuser'] = vuser_count

            df_list.append(df)

        except Exception as e:
            print(f"[오류] {file_path.name} 파일 처리 중 에러 발생: {e}")

    # 모든 데이터프레임 병합 및 저장
    if df_list:
        merged_df = pd.concat(df_list, ignore_index=True)

        if 'DateTime' in merged_df.columns:
            merged_df['DateTime'] = pd.to_datetime(merged_df['DateTime'])

        meta_cols = ['Order', 'Lock', 'Vuser']
        original_cols = [col for col in merged_df.columns if col not in meta_cols]
        merged_df = merged_df[meta_cols + original_cols]

        custom_lock_order = [
            'Pessimistic Lock',
            'Spin Lock',
            'Pub/Sub Lock',
            'ZooKeeper Lock',
            'Adaptive Lock',
        ]
        merged_df['Lock'] = pd.Categorical(
            merged_df['Lock'],
            categories=custom_lock_order,
            ordered=True
        )

        merged_df = merged_df.sort_values(
            by=['Order', 'Lock', 'Vuser'],
            ascending=[True, True, True],
        )

        os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
        merged_df.to_csv(output_filepath, index=False)

        print(f"데이터 병합 완료! 최종 데이터가 '{output_filepath}'에 저장되었습니다.")
        print(f"    - 총 행(Row) 수: {len(merged_df):,}")
        print(f"    - 총 열(Column) 수: {len(merged_df.columns)}")
    else:
        print("병합할 데이터가 없습니다.")


if __name__ == '__main__':
    BASE_DATA_DIR = '../data/raw/ngrinder'
    OUTPUT_FILEPATH = '../data/processed/ngrinder.csv'

    preprocess_ngrinder_data(BASE_DATA_DIR, OUTPUT_FILEPATH)
