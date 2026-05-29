# 03. 다운로드 + DuckDB 환경 설정

- 버전: v0.1.0
- 최종 갱신: 2026-05-21
- 작성자: DATA
- Reference: NVIDIA Nemotron-Personas-Korea 활용 가이드 (`E:/projects/kr-synthetic-personas/docs/usage.md`)

본 문서는 효돌 합성 어르신 데이터셋을 처음 받는 사람이 분석 가능한 상태까지 도달하는 단계별 가이드다. Claude Code 활용 학생용 워크플로우는 `docs/06_student-workflow-with-claude-code.md` 별도 참조.

---

## 0. 사전 준비

### 0-1. 환경 요구사항

| 항목 | 권장 |
|---|---|
| OS | Windows / macOS / Linux 무관 |
| 디스크 여유 | 핵심 3 테이블 기준 최소 500 MB / 전체 포함 최소 1.5 GB |
| Python | 3.9 이상 (다운로드 CLI용) |
| DuckDB | v1.0 이상 (분석용) |
| Claude Code (선택) | 자연어로 데이터 받고 분석할 학생용 |

### 0-2. 데이터 용량과 학생 접근법 분기

본 데이터셋의 Parquet ZSTD 압축 후 예상 용량:

| 테이블 | 행 수 | 압축 후 | 다운로드 분류 |
|---|---:|---:|---|
| `profile` | 1,000 | ~2 MB | 필수 |
| `behavior_log` | ~4,000,000 | ~80-120 MB | 필수 |
| `survey_responses` | 192,000 | ~5-8 MB | 필수 |
| `joined_wide` | ~4,000,000 | ~200-400 MB | 선택 (벤치마크 학습 시) |

용량에 따라 학생이 선택할 수 있는 접근법:

| 옵션 | 다운로드 | 적합 |
|---|---|---|
| **A. 핵심 3 테이블만 (권장 default)** | 약 90~130 MB | 모든 학생. 1~2분 다운로드 |
| **B. 전체** | 약 290~530 MB | DuckDB 성능 벤치마크 학습 |
| **C. HF Datasets streaming** | 0 | 디스크 부족 / 노트북 사양 낮은 학생 |
| **D. Motherduck (클라우드)** | 0 | 협업 분석 (강사가 선택적으로 제공) |

### 0-3. DuckDB 설치

DuckDB는 단일 바이너리로 설치되며, 별도 서버가 필요 없다.

**Windows**:
```bash
# Scoop 사용 시
scoop install duckdb

# 또는 https://duckdb.org/docs/installation/ 에서 단일 .exe 다운로드
```

**macOS**:
```bash
brew install duckdb
```

**Linux**:
```bash
curl -L https://github.com/duckdb/duckdb/releases/download/v1.0.0/duckdb_cli-linux-amd64.zip -o duckdb.zip
unzip duckdb.zip
sudo mv duckdb /usr/local/bin/
```

**설치 확인**:
```bash
duckdb --version
```

### 0-4. Python (선택, 분석 환경)

```bash
pip install duckdb
```

---

## 1. 효돌 합성 데이터셋 다운로드

> ⚠️ **현재 상태 (2026-05-21)**: 본 데이터셋은 합성 스크립트 작성 단계이며 아직 공식 배포되지 않았습니다. 다운로드 경로는 v0.2.0 (데이터 생성 완료) 시점에 확정 후 업데이트됩니다.

### 1-A. GitHub 퍼블릭 레포 (현재 공식 배포 채널)

```bash
# 전체 clone — 1000명 + 100명 호환 데이터 + 문서·스크립트·평가 보고서 (약 72 MB)
git clone https://github.com/gonnector/hyodol-synthetic-elderly.git
cd hyodol-synthetic-elderly
```

태그된 안정 버전을 받으려면:

```bash
git clone --branch v0.2.1 https://github.com/gonnector/hyodol-synthetic-elderly.git
```

### 1-B. Hugging Face Hub (옵션 — 향후 미러)

현재 GitHub가 공식 채널. HF 미러는 v0.3.x 이후 검토 예정.

### 1-C. 직접 빌드 (개발자용)

스크립트로 재생성하려면 (Nemotron-Personas-Korea 사전 다운로드 필요 — Section 2 참조):

```bash
# 1000명 합성 = 500명 × 2 batch 머지 (옵션 B 전략, 약 220분)
python scripts/generate_pilot.py --n 500 --seed 20260521   # batch1 (약 110분)
# (data/ 백업 후)
python scripts/generate_pilot.py --n 500 --seed 20260526   # batch2 (약 110분)
# 머지 + 자체 검증
python scripts/merge_batches.py \
  --batch1 data/pilot-500-v2 \
  --batch2 data/pilot-500-v2-batch2 \
  --out    data/pilot-1000
# (선택) PHQ-9 0~27 clip post-fix
python scripts/post_fix_phq9.py --target data/pilot-1000
```

> v0.2.x에서는 `joined_wide`를 별도 parquet로 빌드하지 않고 학생 분석 시 SQL JOIN으로 생성한다. 벤치마크 시나리오 상세 → `docs/02_schema.md` Section 4.

---

## 2. 사전 의존 — NVIDIA Nemotron-Personas-Korea 다운로드

본 합성 데이터셋의 `profile` 테이블은 NVIDIA Nemotron-Personas-Korea 1.0의 인구통계 sub-sampling에서 출발한다. 직접 빌드(1-C) 또는 학생이 원본 페르소나 풀을 함께 탐색하고 싶은 경우 필요하다.

### 2-1. 다운로드 명령 (CLI)

```bash
# CLI 설치
pip install -U "huggingface_hub[cli]"

# 빠른 다운로드용 가속 (선택)
pip install hf_xet

# 다운로드
huggingface-cli download nvidia/Nemotron-Personas-Korea \
  --repo-type dataset \
  --local-dir ./nemotron-personas-korea \
  --max-workers 8
```

- 약 1.9 GB / 22 files / 100만 행 × 26 컬럼
- 라이센스: CC BY 4.0 (상업적 사용 가능, 출처 표기 필수)

### 2-2. Claude Code 학생용 한 줄 명령

학생들은 별도 CLI 외우지 않고 Claude Code에게 자연어로 시키면 된다.

> "허깅페이스에서 nvidia/Nemotron-Personas-Korea 데이터셋을 `./nemotron-personas-korea` 폴더로 받아줘. 받은 다음 DuckDB로 행 수 확인까지 해줘."

Claude Code가 자동으로 실행할 것:
1. `huggingface-cli` 설치 여부 확인 (없으면 `pip install`)
2. 위 `huggingface-cli download` 명령 실행
3. `duckdb -c "SELECT COUNT(*) FROM read_parquet('./nemotron-personas-korea/data/*.parquet');"` 으로 무결성 확인 (기대 1,000,000)

학생용 상세 워크플로우 → `docs/06_student-workflow-with-claude-code.md`

### 2-3. 다운로드 결과 폴더

```
./nemotron-personas-korea/
├── README.md                          (HF 원본 데이터셋 카드)
├── data/                              (1.9 GB)
│   ├── train-00000-of-00009.parquet   ~210 MB
│   ├── ...
│   └── train-00008-of-00009.parquet
└── images/                            (스키마·분포 시각화 PNG)
```

### 2-4. Nemotron 데이터셋 무결성 검증

```bash
# 행 개수
duckdb -c "SELECT COUNT(*) FROM read_parquet('./nemotron-personas-korea/data/*.parquet');"
# 기대값: 1,000,000

# 스키마 (26 컬럼)
duckdb -c "DESCRIBE SELECT * FROM read_parquet('./nemotron-personas-korea/data/*.parquet') LIMIT 1;"
```

---

## 3. 효돌 합성 데이터셋 무결성 검증

### 3-1. 행 개수 확인

```bash
duckdb -c "
SELECT
  (SELECT COUNT(*) FROM read_parquet('./hyodol-data/data/profile.parquet'))          AS profile,
  (SELECT COUNT(*) FROM read_parquet('./hyodol-data/data/behavior_log.parquet'))     AS behavior_log,
  (SELECT COUNT(*) FROM read_parquet('./hyodol-data/data/survey_responses.parquet')) AS survey_responses;
"
```

**기대값** (v0.2.0 배포 시점):

| 테이블 | 기대 행 수 |
|---|---:|
| profile | 1,000 |
| behavior_log | 약 3,500,000~4,300,000 |
| survey_responses | 192,000 |
| joined_wide (있을 경우) | behavior_log와 동일 |

### 3-2. 스키마 확인

```bash
duckdb -c "DESCRIBE SELECT * FROM read_parquet('./hyodol-data/data/profile.parquet') LIMIT 1;"
duckdb -c "DESCRIBE SELECT * FROM read_parquet('./hyodol-data/data/behavior_log.parquet') LIMIT 1;"
```

각 컬럼 명·타입이 `docs/02_schema.md` 와 일치하는지 확인.

---

## 4. DuckDB 영구 DB 셋업

매번 Parquet를 read_parquet으로 읽는 대신, 영구 `.duckdb` 파일에 뷰·사전계산 분포 테이블을 등록해두면 매번 빠르게 시작할 수 있다.

### 4-1. 셋업 스크립트 실행

```bash
cd ./hyodol-data
duckdb hyodol.duckdb < scripts/setup-duckdb.sql
```

### 4-2. 셋업 스크립트 내용 (`scripts/setup-duckdb.sql`)

```sql
-- =============================================================
-- 효돌 합성 어르신 데이터셋 — DuckDB 환경 셋업
--
-- 실행:
--   cd <hyodol-data>
--   duckdb hyodol.duckdb < scripts/setup-duckdb.sql
-- =============================================================

-- 1. 메인 테이블/뷰 (Parquet 직접 참조)
CREATE OR REPLACE VIEW profile          AS SELECT * FROM read_parquet('data/profile.parquet');
CREATE OR REPLACE VIEW behavior_log     AS SELECT * FROM read_parquet('data/behavior_log.parquet');
CREATE OR REPLACE VIEW survey_responses AS SELECT * FROM read_parquet('data/survey_responses.parquet');

-- joined_wide는 옵션 다운로드 — 존재 시에만
-- 학생이 받지 않은 경우 아래 줄은 무시 가능
CREATE OR REPLACE VIEW joined_wide      AS SELECT * FROM read_parquet('data/joined_wide.parquet');

-- 2. 메타데이터
CREATE OR REPLACE TABLE _meta AS
  SELECT
    (SELECT COUNT(*) FROM profile)          AS profile_rows,
    (SELECT COUNT(*) FROM behavior_log)     AS behavior_log_rows,
    (SELECT COUNT(*) FROM survey_responses) AS survey_responses_rows,
    CURRENT_TIMESTAMP                       AS setup_at;

-- 3. 자주 쓰는 분포 캐싱
CREATE OR REPLACE TABLE dist_age_group AS
  SELECT age_group, COUNT(*) AS n FROM profile GROUP BY age_group ORDER BY age_group;

CREATE OR REPLACE TABLE dist_sex AS
  SELECT sex, COUNT(*) AS n FROM profile GROUP BY sex;

CREATE OR REPLACE TABLE dist_usage_pattern AS
  SELECT usage_pattern, usage_pattern_label, COUNT(*) AS n
  FROM profile GROUP BY usage_pattern, usage_pattern_label ORDER BY n DESC;

CREATE OR REPLACE TABLE dist_user_type AS
  SELECT user_type_code, user_type_name, COUNT(*) AS n
  FROM profile GROUP BY user_type_code, user_type_name ORDER BY n DESC;

CREATE OR REPLACE TABLE dist_province AS
  SELECT province, COUNT(*) AS n FROM profile GROUP BY province ORDER BY n DESC;

-- 4. 이벤트 타입 분포
CREATE OR REPLACE TABLE dist_event_type AS
  SELECT event_type, COUNT(*) AS n
  FROM behavior_log GROUP BY event_type ORDER BY n DESC;

-- 5. interaction type 분포
CREATE OR REPLACE TABLE dist_interaction_type AS
  SELECT interaction_type, COUNT(*) AS n
  FROM behavior_log
  WHERE event_type = 'interaction'
  GROUP BY interaction_type ORDER BY n DESC;

-- 6. 일별 이벤트 카운트 (시계열)
CREATE OR REPLACE TABLE daily_event_count AS
  SELECT event_date, event_type, COUNT(*) AS n
  FROM behavior_log
  GROUP BY event_date, event_type
  ORDER BY event_date, event_type;

-- 7. 설문 사전·사후 변화 (사용자별)
CREATE OR REPLACE TABLE survey_pre_post_pivot AS
  SELECT
    user_id,
    gds_total_pre,  gds_total_post,  (gds_total_post  - gds_total_pre)  AS gds_delta,
    phq9_total_pre, phq9_total_post, (phq9_total_post - phq9_total_pre) AS phq9_delta,
    ucla_total_pre, ucla_total_post, (ucla_total_post - ucla_total_pre) AS ucla_delta,
    life_mgmt_total_pre, life_mgmt_total_post,
    (life_mgmt_total_post - life_mgmt_total_pre) AS life_mgmt_delta
  FROM profile;

-- 8. 인지 측정 페어 추출 (분석 자주 쓰는 view)
CREATE OR REPLACE VIEW cognition_tests AS
  SELECT
    b.event_id           AS prompt_event_id,
    b.event_ts           AS prompt_ts,
    b.user_id,
    b.prompt_type,
    b.cognition_test_id,
    b.cognition_window_sec,
    b.response_occurred,
    b.response_delay_sec,
    b.response_event_id
  FROM behavior_log b
  WHERE b.event_type = 'prompt'
    AND b.cognition_test_id IS NOT NULL;

-- 9. 완료 확인
SELECT '셋업 완료' AS status, * FROM _meta;
```

### 4-3. 셋업 검증

```bash
duckdb hyodol.duckdb -c "SELECT * FROM _meta;"
```

기대값:

| profile_rows | behavior_log_rows | survey_responses_rows |
|---:|---:|---:|
| 1,000 | ~4,000,000 | 192,000 |

---

## 5. 빠른 시작 — 첫 쿼리

### 5-1. 인터랙티브 셸 진입

```bash
duckdb hyodol.duckdb
```

### 5-2. 기본 분포 확인

```sql
-- 연령대 분포
SELECT * FROM dist_age_group;

-- 사용 패턴 분포
SELECT * FROM dist_usage_pattern;

-- 이벤트 타입 분포
SELECT * FROM dist_event_type;

-- 인터랙션 타입 분포
SELECT * FROM dist_interaction_type;
```

### 5-3. 프로필 샘플

```sql
SELECT
  user_id, age, sex, province,
  usage_pattern, user_type_name,
  gds_total_pre, ucla_total_pre
FROM profile
LIMIT 10;
```

### 5-4. 인지 측정 페어 샘플

```sql
SELECT
  ct.user_id,
  p.age,
  p.gds_total_pre,
  ct.prompt_type,
  ct.response_occurred,
  ct.response_delay_sec
FROM cognition_tests ct
JOIN profile p USING (user_id)
ORDER BY RANDOM()
LIMIT 20;
```

### 5-5. 자동 기술통계

```sql
SUMMARIZE SELECT * FROM profile;
SUMMARIZE SELECT * FROM behavior_log LIMIT 100000;  -- 큰 테이블은 sample
```

---

## 6. Python에서 사용

```python
import duckdb

con = duckdb.connect('hyodol.duckdb', read_only=True)

# 1. 분포 확인
df = con.execute("SELECT * FROM dist_age_group").fetchdf()
print(df)

# 2. 인지 측정 페어 분석
df = con.execute("""
SELECT
  p.age,
  p.gds_total_pre,
  AVG(b.response_delay_sec) AS avg_delay,
  AVG(b.response_occurred::INT) AS response_rate
FROM profile p
JOIN behavior_log b USING (user_id)
WHERE b.event_type = 'prompt' AND b.cognition_test_id IS NOT NULL
GROUP BY p.age, p.gds_total_pre
""").fetchdf()
```

---

## 7. HF Datasets streaming (옵션 C — 디스크 절약)

다운로드 없이 streaming으로 분석하고 싶은 학생용. 단, 전체 스캔이 매번 네트워크 호출이라 cross-tab·반복 쿼리는 느림.

```python
from datasets import load_dataset

ds = load_dataset("<org>/hyodol-synthetic-elderly",
                  split="train",
                  streaming=True)

# iterator로 한 번씩 순회 — DuckDB 같은 SQL 분석은 불가
for sample in ds.take(5):
    print(sample)
```

DuckDB로 분석하려면 streaming → Parquet 임시 저장 권장.

---

## 8. 문제 해결

| 증상 | 원인·해결 |
|---|---|
| `duckdb: command not found` | DuckDB 설치 확인. PATH 추가 |
| `read_parquet ... 파일 없음` | 경로 확인. setup-duckdb.sql 실행 시 cwd가 데이터 폴더인지 |
| 메모리 부족 | DuckDB는 자동 스트리밍하지만 큰 join 시 `SET memory_limit='4GB';` |
| `huggingface-cli` 다운로드 매우 느림 | `--max-workers 8` 증가 / `hf_xet` 설치 |
| Windows 한글 경로 문제 | `--local-dir` 영문 경로로 변경 (예: `./hyodol-data`) |
| joined_wide.parquet 없음 | 옵션 다운로드 — 옵션 A 선택 시 생략. 옵션 B 다운로드로 추가 가능 |

---

## 다음 문서

- 학생용 Claude Code 워크플로우: `docs/06_student-workflow-with-claude-code.md`
- 분석 가이드 (LLM/학생용): `docs/04_analysis-guide.md`
- 한계점·윤리: `docs/05_limitations-and-ethics.md`
