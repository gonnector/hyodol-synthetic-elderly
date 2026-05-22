# 효돌 합성 어르신 데이터셋 (Hyodol Synthetic Elderly Dataset)

- 버전: v0.1.0 (스키마 확정 전 초안)
- 작성자: DATA (Gonnector AI Team — 데이터 사이언티스트)
- 최종 갱신: 2026-05-21
- 용도: 서울대 아동가족학과 "아동·가족 데이터 분석" 12주차 수업 실습 자료

---

## ⚠️ 현재 배포 버전 (v0.1.0) — 수업용 시범 데이터

본 버전은 **100명 시범 데이터**(`data/pilot-100-v2/`)다. 1000명 풀스케일·외부 평가 PASS 버전은 별도 배포 예정.

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
# 1. 데이터 다운로드 (TBD — Hugging Face 또는 공유 링크)
huggingface-cli download <repo>/hyodol-synthetic-elderly \
  --repo-type dataset \
  --local-dir ./hyodol-data

# 2. DuckDB 설정
duckdb hyodol.duckdb < scripts/setup-duckdb.sql

# 3. 첫 쿼리
duckdb hyodol.duckdb -c "SELECT * FROM _meta;"
```

상세 가이드 → `docs/03_setup-and-download.md`

---

## 데이터셋 한눈에 보기

| 항목 | 값 |
|---|---|
| 이름 | hyodol-synthetic-elderly |
| 버전 | v0.1.0 |
| 합성 기준 시점 | 2026-05-21 |
| 관찰 기간 | 2026-01-01 ~ 2026-03-31 (90일) |
| 표본 규모 | **어르신 1,000명** |
| 연령 범위 | **50~99세** (60+ 비중 78% — 70대 강화·80대 축소 조정) |
| 행동 로그 규모 | 약 350만~430만 이벤트 |
| 설문 응답 규모 | 약 192,000 응답 (1000명 × 96문항 × 2 wave) |
| 라이센스 | CC BY-NC-SA 4.0 (비상업적 사용·동일조건 변경 허락) |
| 원본 reference | ㈜효돌 운영 스키마 + 효돌_샘플데이터_비식별_20260424.xlsx (24명) |
| 인구통계 reference | NVIDIA Nemotron-Personas-Korea 1.0 (CC BY 4.0) |
| 포맷 | Parquet (압축) + DuckDB |

---

## 4 테이블 구조

```
┌─────────────────┐         ┌─────────────────────────┐
│  profile        │         │  behavior_log           │
│  (1,000 rows)   │ ──┐  ┌──│  (~430만 rows)          │
│  인구통계+효돌  │   │  │  │  이벤트 단위            │
│  +베이스라인    │   │  │  │  dialogue/interaction/  │
│   설문 총점     │   │  │  │  program/health_check/  │
│  +사용자유형    │   │  │  │  prompt/system          │
└─────────────────┘   │  │  └────────────┬────────────┘
                      │  │               │
┌─────────────────┐   │  │  ┌────────────▼────────────┐
│ survey_responses│ ──┘  │  │  joined_wide            │
│ (~192,000 rows) │      │  │  (~430만 rows)          │
│ 96문항×2 wave   │      └─►│  profile + behavior_log │
└─────────────────┘         │  denormalized           │
                            │  (벤치마크 전용)         │
                            └─────────────────────────┘
```

상세 스키마 → `docs/02_schema.md`

---

## 폴더 구조

```
hyodol-synthetic-dataset/
├── README.md                       ← 본 문서 (entry point)
├── docs/
│   ├── 01_design-and-method.md           설계 의도 + 합성 방법론
│   ├── 02_schema.md                      4 테이블 상세 스키마
│   ├── 03_setup-and-download.md          다운로드 + DuckDB 설정
│   ├── 04_analysis-guide.md              분석 가이드 (LLM/학생용)
│   ├── 05_limitations-and-ethics.md      한계점 · 윤리
│   ├── 06_student-workflow-with-claude-code.md  학생용 Claude Code 워크플로우
│   └── 07_known-issues-and-precautions.md ★ 현재 데이터(100명 v2) 한계·DO/DON'T (수업용 필독)
├── scripts/
│   ├── setup-duckdb.sql            DuckDB 환경 셋업
│   ├── generate_profile.py         (TBD) 프로필 1000명 합성
│   ├── generate_behavior_log.py    (TBD) 행동 로그 합성
│   ├── generate_dialogues.py       (TBD) 대화 스크립트 합성
│   ├── generate_surveys.py         (TBD) 설문 응답 합성
│   ├── build_joined_wide.py        (TBD) joined_wide 빌드
│   └── benchmark_queries.py        (TBD) DuckDB 성능 벤치마크
└── data/
    ├── profile.parquet
    ├── behavior_log.parquet
    ├── survey_responses.parquet
    └── joined_wide.parquet
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
