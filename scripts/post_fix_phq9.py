#!/usr/bin/env python3
"""
Fix 8 — Post-processing: PHQ-9 총점 재계산 (Q1~Q9만 합산).

기존 데이터의 phq9_total_pre/post가 Q1~Q10 합산이라 0~27 스펙 위반 가능.
survey_responses.parquet은 그대로 두고 profile.parquet만 갱신.

실행:
    python scripts/post_fix_phq9.py --target data/pilot-100-v2
    python scripts/post_fix_phq9.py --target data       # 500명 데이터
"""
import argparse, io, sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import duckdb
import pandas as pd

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--target', required=True, help='데이터 폴더 경로 (예: data/pilot-100-v2)')
    args = parser.parse_args()

    target = Path(args.target)
    profile_path = target / "profile.parquet"
    survey_path = target / "survey_responses.parquet"
    if not profile_path.exists() or not survey_path.exists():
        print(f"ERROR: parquet 파일 없음 — {profile_path} 또는 {survey_path}")
        sys.exit(1)

    print(f"[Fix 8] PHQ-9 post-fix: {target}")
    con = duckdb.connect()
    profile = con.execute(f"SELECT * FROM read_parquet('{profile_path.as_posix()}')").fetchdf()
    survey = con.execute(f"SELECT * FROM read_parquet('{survey_path.as_posix()}')").fetchdf()

    before_pre = profile['phq9_total_pre'].max()
    before_post = profile['phq9_total_post'].max()
    over27_before = ((profile['phq9_total_pre'] > 27) | (profile['phq9_total_post'] > 27)).sum()
    print(f"  before: max(pre)={before_pre}, max(post)={before_post}, >27 위반={over27_before}건")

    # Q1~Q9만 합산해서 다시 계산
    phq9 = survey[(survey['survey_type'] == 'phq9') & (survey['question_no'].between(1, 9))]
    pre_totals = phq9[phq9['wave'] == 'pre'].groupby('user_id')['answer_score'].sum()
    post_totals = phq9[phq9['wave'] == 'post'].groupby('user_id')['answer_score'].sum()

    profile['phq9_total_pre'] = profile['user_id'].map(pre_totals).astype('Int64')
    profile['phq9_total_post'] = profile['user_id'].map(post_totals).astype('Int64')

    after_pre = profile['phq9_total_pre'].max()
    after_post = profile['phq9_total_post'].max()
    over27_after = ((profile['phq9_total_pre'] > 27) | (profile['phq9_total_post'] > 27)).sum()
    print(f"  after:  max(pre)={after_pre}, max(post)={after_post}, >27 위반={over27_after}건")

    # CSV 경유 parquet 저장 (numpy dtype 문제 회피)
    tmp_csv = target / "_profile_fix8.csv"
    profile.to_csv(tmp_csv, index=False, encoding='utf-8')
    con.execute(f"""
        COPY (SELECT * FROM read_csv_auto('{tmp_csv.as_posix()}', header=true, sample_size=-1))
        TO '{profile_path.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
    """)
    tmp_csv.unlink()
    con.close()

    print(f"  ✅ {profile_path.name} 갱신 완료 ({len(profile)} rows)")

if __name__ == "__main__":
    main()
