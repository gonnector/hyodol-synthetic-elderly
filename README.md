# 효돌 합성 어르신 데이터셋 (Hyodol Synthetic Elderly Dataset)

- 버전: **v0.2.4** (1000명 풀스케일 — 옵션 B 머지 전략, 외부 평가 8/8 PASS)
- 설계: Dylan (고영혁, Gonnector) + DATA (Gonnector AI Team)
- 외부 평가: general-purpose sub-agent (1·2·3차 PASS)
- 최종 갱신: 2026-05-26
- 용도: 서울대 아동가족학과 "아동·가족 데이터 분석" 12주차 수업 실습 자료

> **v0.2.0 변경점**: 1000명 풀스케일 데이터 (`data/pilot-1000/`) 추가. 500명 × 2 batch (다른 seed) 합성 후 머지 — 카이제곱 검정으로 batch 간 분포 동질성 검증. 외부 sub-agent 평가에서 8개 항목 모두 PASS. 100명 v2 (`data/pilot-100-v2/`)는 호환성을 위해 그대로 유지.

---

## 🎓 학생용 빠른 시작 (Claude Code에 복붙)

> **이전 버전(v0.1.0/v0.2.0)을 이미 받은 학생**은 1단계 대신 **"기존 학생 업데이트"** 섹션으로 직행.

**1단계 — 받기·셋업** (처음 받는 학생):
```
https://github.com/gonnector/hyodol-synthetic-elderly 레포를 ./hyodol-data 폴더로 git clone해줘.
docs/07_known-issues-and-precautions.md 와 README.md 를 먼저 읽어.
그 다음 DuckDB가 설치돼 있는지 확인하고 없으면 설치해.
scripts/setup-duckdb.sql로 hyodol.duckdb 환경 셋업하고 _meta 테이블 보여줘.
```

**기존 학생 업데이트 (이미 hyodol-data 폴더가 있는 학생)**:
```
hyodol-data 폴더로 가서 git pull로 최신 버전(v0.2.2) 받아줘.
그 다음 scripts/setup-duckdb.sql 을 hyodol.duckdb 에 다시 실행해줘 (CREATE OR REPLACE라 안전).
끝나면 _meta 테이블을 보여줘서 profile=1000, behavior_log=3,671,068, survey_responses=168,000 으로 갱신됐는지 확인.
이전 버전이면 profile=100 같은 작은 숫자가 나올 거야 — 그러면 git pull 또는 setup 재실행이 안 된 거니까 다시 시도.
```

**1.5단계 — 데이터 검증 (smoke test)**:
```
받은 hyodol-data가 제대로 설치됐는지 검증해줘.
(1) data/pilot-1000/ 에 profile/behavior_log/survey_responses 3개 parquet 파일 존재 확인
(2) DuckDB로 행 수 — profile=1000, behavior_log≈3,670,000, survey_responses=168,000 — 기대값과 맞는지
(3) 프로필 첫 5명(user_id, age, sex, usage_pattern, batch_id) 표로 출력
(4) 인지 측정 페어 샘플 3건 (prompt_type, response_occurred, response_delay_sec)
(5) batch 분포 (batch_id=1 vs 2 — 각 500명)
모두 정상이면 "✅ 준비 완료" 한 줄로 마무리, 어디서 어긋나면 무엇이 문제인지 알려줘.

만약 profile=100 같은 작은 숫자가 나오면 이전 버전(v0.1.0) 셋업이 남아 있는 거야 —
"기존 학생 업데이트" 섹션을 다시 실행해서 git pull + setup-duckdb.sql 재실행 후 검증 다시.
```

**2단계 — 첫 탐색 3가지**:
```
받은 데이터로 첫 탐색 3가지 보여줘:
(1) 연령대(50s/60s/70s/80s/90s)별 인원 수와 사용 패턴 7종 분포
(2) 사용자별 90일 총 이벤트 수 분포 — boxplot으로
(3) 인지 측정 페어 응답률·평균 딜레이를 연령대별로
표와 차트로 정리하고, 합성 데이터라는 한계도 한 줄 명시해줘.
```

**3단계 — 본인 관심 주제** → `docs/04_analysis-guide.md` Section 5의 시나리오 A~F 6종에서 선택.

## ⚠️ 학생 안티패턴 5가지 (절대 금지)

1. ❌ "효돌이 우울을 감소시킨다" 같은 인과 추론 결론
2. ❌ p-value 보고로 효과성 입증 시도
3. ❌ "한국 노인 X%가 ~다" 모집단 일반화
4. ❌ 개별 user_id를 보고서에 노출 (집계·군집 단위만)
5. ❌ 데이터 파일을 외부 공개 저장소·SNS에 업로드

상세: `docs/07_known-issues-and-precautions.md`

---

---

## 🎯 현재 배포 버전 (v0.2.0) — 1000명 풀스케일

- 메인: **1000명 풀스케일** (`data/pilot-1000/`) — 외부 평가 8/8 PASS
- 호환: 100명 시범 (`data/pilot-100-v2/`) — v0.1.0 호환성 유지

**LLM 보조자·학생 모두 분석 시작 전 반드시 읽을 것**: `docs/07_known-issues-and-precautions.md` (현재 데이터 한계·DO/DON'T·우선 분석 순서)

---

## 이 문서를 읽는 LLM에게

본 데이터셋은 ㈜효돌의 실제 AI 돌봄 로봇 운영 스키마를 reference로 하여 **합성**된 데이터셋이다. 학생들의 분석을 보조할 때 다음을 우선 인지하라:

1. **합성 데이터** — 실제 인물·실제 측정값이 아님. 모든 결과는 "합성 모델이 박아 둔 패턴의 재발견"이며, 외부 일반화 불가.
2. **효돌 원본은 24명·단일 시점 사후 조사** — 본 합성 데이터셋은 그 한계를 우회하기 위해 1000명·90일 종단으로 확장한 것. 원본 효돌과 통계량을 직접 비교하지 말 것.
3. **인지 능력 측정 페어링이 핵심 신규 기능** — `prompt`-`interaction` 이벤트의 `cognition_test_id`로 묶인 response_delay 분석이 본 데이터셋이 새로 가능하게 한 분석 축.
4. **분석 가이드는 `docs/04_analysis-guide.md` 우선 참조** — 자주 묻는 SQL 패턴·안티패턴·시나리오가 정리되어 있음.

---

## 빠른 시작

```bash
# 1. GitHub 레포 clone
git clone https://github.com/gonnector/hyodol-synthetic-elderly.git
cd hyodol-synthetic-elderly

# 2. DuckDB 환경 셋업 (1000명 v0.2.1 default)
duckdb hyodol.duckdb < scripts/setup-duckdb.sql

# 3. 첫 쿼리
duckdb hyodol.duckdb -c "SELECT * FROM _meta;"
```

학생용 자연어 가이드(Claude Code 복붙)는 본 README 상단의 "🎓 학생용 빠른 시작" 섹션 참조.
상세 가이드 → `docs/03_setup-and-download.md`

---

## 데이터셋 한눈에 보기

| 항목 | 값 |
|---|---|
| 이름 | hyodol-synthetic-elderly |
| 버전 | **v0.2.1** (1000명 풀스케일, 외부 평가 8/8 PASS) |
| 합성 기준 시점 | 2026-05-26 |
| 관찰 기간 | 2026-01-01 ~ 2026-03-31 (90일) |
| 표본 규모 | **어르신 1,000명** (500명 × 2 batch 머지, 카이제곱 검정으로 분포 동질성 확인) |
| 연령 범위 | **50~99세** (60+ 비중 78% — 70대 강화·80대 축소 도메인 조정) |
| 행동 로그 규모 | **3,671,068 이벤트** (실측) |
| 설문 응답 규모 | **168,000 응답** (실측 — 96문항 × 2 wave, usability 사전 wave 제외) |
| 압축 후 용량 | profile 0.08 MB / behavior_log 65.88 MB / survey_responses 0.17 MB (총 약 66 MB) |
| 라이센스 | CC BY-NC-SA 4.0 (비상업적 사용·동일조건 변경 허락) |
| 원본 reference | ㈜효돌 운영 스키마 + 효돌_샘플데이터_비식별_20260424.xlsx (24명) |
| 인구통계 reference | NVIDIA Nemotron-Personas-Korea 1.0 (CC BY 4.0) |
| 포맷 | Parquet ZSTD + DuckDB |
| 호환 데이터 | `data/pilot-100-v2/` (v0.1.0 100명, 약 6.5 MB) — 비교·교차 분석용 보존 |

---

## 4 테이블 구조

```
┌─────────────────┐         ┌─────────────────────────┐
│  profile        │         │  behavior_log           │
│  (1,000 rows)   │ ────────│  (3,671,068 rows)       │
│  인구통계+효돌  │   user_ │  이벤트 단위            │
│  +베이스라인    │   id 로 │  dialogue/interaction/  │
│   설문 총점     │   join  │  program/health_check/  │
│  +사용자유형    │         │  prompt/system          │
│  +batch_id      │         │  +batch_id              │
└─────────────────┘         └─────────────────────────┘
        │
        │   ┌─────────────────────────┐
        └──>│ survey_responses        │
            │ (168,000 rows)          │
            │ 96문항 × 2 wave         │
            │ +batch_id               │
            └─────────────────────────┘

※ joined_wide는 v0.2.x에서 옵션 다운로드 — 분석 시 학생이 직접 JOIN 사용
   (`docs/02_schema.md` Section 4 참조)
```

상세 스키마 → `docs/02_schema.md`

---

## 폴더 구조

```
hyodol-synthetic-dataset/
├── README.md                                    ← 본 문서 (entry point)
├── .gitignore / .gitattributes
├── docs/
│   ├── 01_design-and-method.md                  설계 의도 + 합성 방법론
│   ├── 02_schema.md                             4 테이블 상세 스키마
│   ├── 03_setup-and-download.md                 다운로드 + DuckDB 설정
│   ├── 04_analysis-guide.md                     분석 가이드 (LLM/학생용)
│   ├── 05_limitations-and-ethics.md             한계점 · 윤리
│   ├── 06_student-workflow-with-claude-code.md  학생용 Claude Code 워크플로우
│   └── 07_known-issues-and-precautions.md       ★ 현재 데이터 한계·DO/DON'T (수업용 필독)
├── scripts/
│   ├── setup-duckdb.sql                         DuckDB 환경 셋업 (1000명 default + 100명 호환)
│   ├── generate_pilot.py                        합성 본체 (profile/behavior_log/survey_responses)
│   ├── post_fix_phq9.py                         Fix 8 — PHQ-9 Q10 제외 post-processing
│   └── merge_batches.py                         500명 × 2 batch 머지 + 자체 검증
├── data/
│   ├── pilot-1000/                              ★ v0.2.1 메인 — 1000명 풀스케일
│   │   ├── profile.parquet
│   │   ├── behavior_log.parquet
│   │   └── survey_responses.parquet
│   └── pilot-100-v2/                            v0.1.0 호환 — 100명 시범
│       ├── profile.parquet
│       ├── behavior_log.parquet
│       └── survey_responses.parquet
└── eval/
    ├── evaluation-rubric.md                     외부 평가 기준 (sub-agent용 prompt)
    └── reports/
        ├── 20260521_eval_pilot-100_general-purpose.md      1차 평가 (CONDITIONAL PASS)
        ├── 20260521_eval_pilot-100-v2_general-purpose.md   2차 평가 (PASS)
        └── 20260526_eval_pilot-1000_general-purpose.md     3차 평가 (8/8 PASS)
```

---

## 라이센스

본 데이터셋은 **CC BY-NC-SA 4.0** (Creative Commons 저작자표시-비영리-동일조건변경허락 4.0 국제) 라이센스로 배포됩니다.

- **저작자표시 (BY)**: 출처 표기 필수
- **비영리 (NC)**: 비상업적 사용만 허용
- **동일조건변경허락 (SA)**: 변경·재배포 시 동일 라이센스 적용

> 본 데이터는 ㈜효돌의 운영 스키마를 reference로 한 **합성** 데이터로, 효돌이 직접 배포하는 것이 아니며 효돌의 실제 사용자 데이터를 포함하지 않습니다.
> 외부 학술 출판·상업 활용을 희망하는 경우 강사(고영혁)를 통해 별도 절차를 경유해야 합니다.

### 출처 표기 예시

> 본 분석은 서울대 아동가족학과 12주차 수업용 효돌 합성 어르신 데이터셋 (v0.1.0, ㈜효돌 운영 스키마 reference) 을 활용했습니다.

---

## 변경 이력

- **v0.1.0** (2026-05-21) — 스키마 v1.1 초안 + 통합 문서 세트. 데이터 생성 스크립트 미작성, 데이터 미생성 상태. Dylan 피드백 대기.

---

## 문의

- 강사: 고영혁 (Gonnector) — Gonnector@gonnector.com
- 데이터 설계·합성 담당: DATA (Gonnector AI Team)
