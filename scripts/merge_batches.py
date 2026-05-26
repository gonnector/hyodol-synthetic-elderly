#!/usr/bin/env python3
"""
500명 × 2 batch 머지 → 1000명 단일 데이터셋.

독립성 보장 4 조건:
1. Random seed 다름 (batch1=20260521, batch2=20260526)
2. Nemotron 페르소나 uuid 중복 체크 (1M pool 기준 확률 ≈ 0)
3. 식별자 재할당 — batch2의 user_id +500, doll_id +500, serial_number 재해시
4. event_id 재할당 — batch2에 +(batch1 max event_id), response_event_id 같이 shift

추가:
- batch_id 컬럼 명시 (1 또는 2) — 학생 분석 시 batch 간 비교 가능

실행:
    python scripts/merge_batches.py \
        --batch1 data/pilot-500-v2 \
        --batch2 data/pilot-500-v2-batch2 \
        --out data/pilot-1000
"""
import argparse, hashlib, io, sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import duckdb
import pandas as pd

OFFSET = 500  # batch2 user_id/doll_id offset

def shift_user_id(uid: str, off: int) -> str:
    n = int(uid[1:]) + off
    return f"U{n:04d}"

def save_via_csv(df: pd.DataFrame, out_path: Path, con: duckdb.DuckDBPyConnection):
    tmp = out_path.parent / f"_{out_path.stem}.csv"
    df.to_csv(tmp, index=False, encoding='utf-8')
    con.execute(f"""
        COPY (SELECT * FROM read_csv_auto('{tmp.as_posix()}', header=true, sample_size=-1))
        TO '{out_path.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
    """)
    tmp.unlink()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--batch1', required=True, help='batch1 데이터 폴더 (U0001~U0500)')
    parser.add_argument('--batch2', required=True, help='batch2 데이터 폴더 (U0001~U0500, shift 전)')
    parser.add_argument('--out', required=True, help='출력 폴더 (1000명 머지 결과)')
    args = parser.parse_args()

    b1 = Path(args.batch1)
    b2 = Path(args.batch2)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    print(f"[Merge batches] batch1={b1} batch2={b2} out={out} offset=+{OFFSET}")
    con = duckdb.connect()

    # ============================
    # 1. Profile 머지
    # ============================
    p1 = con.execute(f"SELECT * FROM read_parquet('{(b1/'profile.parquet').as_posix()}')").fetchdf()
    p2 = con.execute(f"SELECT * FROM read_parquet('{(b2/'profile.parquet').as_posix()}')").fetchdf()
    print(f"\n[1/3] Profile — batch1 {len(p1)} rows, batch2 {len(p2)} rows")

    # batch_id 컬럼 추가
    p1['batch_id'] = 1
    p2['batch_id'] = 2

    # batch2 ID re-assignment
    p2['user_id'] = p2['user_id'].apply(lambda u: shift_user_id(u, OFFSET))
    p2['doll_id'] = (p2['doll_id'].astype(int) + OFFSET).astype(str)
    # serial_number 재해시 (새 user_id 기반, 머지 컨텍스트 prefix)
    p2['serial_number'] = p2['user_id'].apply(
        lambda u: f"S-{hashlib.sha256(f'doll_{u}_merge'.encode()).hexdigest()[:8].upper()}"
    )

    profile_merged = pd.concat([p1, p2], ignore_index=True)

    # user_id 중복 검증
    dup = profile_merged[profile_merged.duplicated('user_id', keep=False)]
    if len(dup) > 0:
        print(f"  ⚠️ user_id 중복 {len(dup)}건 — 머지 ID 충돌")
        sys.exit(1)
    print(f"  user_id 중복 0건, 총 {len(profile_merged)} 명")
    print(f"  doll_id 범위: {profile_merged['doll_id'].astype(int).min()}~{profile_merged['doll_id'].astype(int).max()}")

    # ============================
    # 2. Behavior_log 머지
    # ============================
    bl1 = con.execute(f"SELECT * FROM read_parquet('{(b1/'behavior_log.parquet').as_posix()}')").fetchdf()
    bl2 = con.execute(f"SELECT * FROM read_parquet('{(b2/'behavior_log.parquet').as_posix()}')").fetchdf()
    print(f"\n[2/3] Behavior_log — batch1 {len(bl1):,} rows, batch2 {len(bl2):,} rows")

    bl1['batch_id'] = 1
    bl2['batch_id'] = 2

    # batch2 user_id shift
    bl2['user_id'] = bl2['user_id'].apply(lambda u: shift_user_id(u, OFFSET))

    # event_id 재할당 — batch1 max 이후로 batch2 shift
    eid_offset = int(bl1['event_id'].max())
    bl2['event_id'] = bl2['event_id'] + eid_offset
    # response_event_id도 같이 shift (NULL이 아닌 경우만)
    mask = bl2['response_event_id'].notna()
    bl2.loc[mask, 'response_event_id'] = bl2.loc[mask, 'response_event_id'] + eid_offset

    behavior_merged = pd.concat([bl1, bl2], ignore_index=True)

    # event_id 중복 검증
    n_dup_eid = len(behavior_merged) - behavior_merged['event_id'].nunique()
    if n_dup_eid > 0:
        print(f"  ⚠️ event_id 중복 {n_dup_eid}건")
        sys.exit(1)
    print(f"  event_id 1~{int(behavior_merged['event_id'].max()):,}, 중복 0건")
    # cognition_test_id UUID 충돌 검증
    ct_dup = behavior_merged[behavior_merged['cognition_test_id'].notna()].groupby('cognition_test_id').size()
    overlap = ct_dup[ct_dup > 2]
    print(f"  cognition_test_id: 정상 페어(≤2 events/id) — 이상 페어링 {len(overlap)}건")

    # ============================
    # 3. Survey_responses 머지
    # ============================
    sr1 = con.execute(f"SELECT * FROM read_parquet('{(b1/'survey_responses.parquet').as_posix()}')").fetchdf()
    sr2 = con.execute(f"SELECT * FROM read_parquet('{(b2/'survey_responses.parquet').as_posix()}')").fetchdf()
    print(f"\n[3/3] Survey_responses — batch1 {len(sr1):,} rows, batch2 {len(sr2):,} rows")

    sr1['batch_id'] = 1
    sr2['batch_id'] = 2
    sr2['user_id'] = sr2['user_id'].apply(lambda u: shift_user_id(u, OFFSET))

    survey_merged = pd.concat([sr1, sr2], ignore_index=True)
    print(f"  총 {len(survey_merged):,} rows")

    # ============================
    # 4. 저장
    # ============================
    print(f"\n[Save] Parquet 저장 (CSV 경유 ZSTD)...")
    save_via_csv(profile_merged, out / "profile.parquet", con)
    save_via_csv(behavior_merged, out / "behavior_log.parquet", con)
    save_via_csv(survey_merged, out / "survey_responses.parquet", con)

    for fname in ['profile.parquet', 'behavior_log.parquet', 'survey_responses.parquet']:
        path = out / fname
        size_mb = path.stat().st_size / 1024 / 1024
        print(f"  ✅ {fname}: {size_mb:.2f} MB")

    # ============================
    # 5. 무결성 자체 검증
    # ============================
    print(f"\n[Self-check]")
    # FK 무결성
    user_ids_in_profile = set(profile_merged['user_id'])
    user_ids_in_behavior = set(behavior_merged['user_id'])
    user_ids_in_survey = set(survey_merged['user_id'])
    orphan_bl = user_ids_in_behavior - user_ids_in_profile
    orphan_sr = user_ids_in_survey - user_ids_in_profile
    print(f"  behavior_log orphan user_id: {len(orphan_bl)}")
    print(f"  survey_responses orphan user_id: {len(orphan_sr)}")
    # Nemotron uuid 중복 (있으면 표시)
    if 'uuid' in profile_merged.columns:
        n_dup_uuid = len(profile_merged) - profile_merged['uuid'].nunique()
        print(f"  Nemotron uuid 중복: {n_dup_uuid}건")
    # batch 분포
    print(f"  batch 분포: {profile_merged['batch_id'].value_counts().to_dict()}")
    # PHQ-9 위반 검사
    over27 = ((profile_merged['phq9_total_pre'] > 27) | (profile_merged['phq9_total_post'] > 27)).sum()
    print(f"  PHQ-9 > 27 위반: {over27}건 (기대 0건)")
    # WHODAS 위반
    over60 = ((profile_merged['whodas_total_pre'] > 60) | (profile_merged['whodas_total_post'] > 60)).sum()
    print(f"  WHODAS > 60 위반: {over60}건 (기대 0건)")
    # 분포
    print(f"  연령대 분포: {profile_merged['age_group'].value_counts().sort_index().to_dict()}")
    print(f"  사용 패턴 분포: {profile_merged['usage_pattern'].value_counts().to_dict()}")

    con.close()
    print(f"\n✅ 머지 완료: {out}")

if __name__ == "__main__":
    main()
