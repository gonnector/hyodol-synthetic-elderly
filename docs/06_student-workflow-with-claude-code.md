# 06. 학생용 Claude Code 워크플로우

- 버전: v0.1.0
- 최종 갱신: 2026-05-21
- 작성자: DATA
- 대상: 서울대 아동가족학과 수강생 (Claude Code 사용 환경)

본 문서는 학생이 Claude Code를 사용해 효돌 합성 어르신 데이터셋을 **다운로드하고 분석하는 가장 빠른 경로**를 안내한다. Claude Code에게 자연어로 시키는 것이 직접 CLI 외우는 것보다 더 빠르고 안전하다.

---

## 0. 이 문서를 학생이 Claude Code에게 보여줄 때

학생이 Claude Code 세션에서 본 문서를 컨텍스트로 로드한 뒤 다음 한 줄만 입력해도 충분하다:

> "위 가이드를 따라서 효돌 합성 데이터셋을 받고 분석 환경을 셋업해줘."

Claude Code는 본 문서를 읽고 단계별로 알아서 실행한다. 학생은 결과만 검수.

---

## 1. 학생이 Claude Code에게 시키는 자연어 명령 예시

### 1-A. 데이터 다운로드

> "허깅페이스에서 `<org>/hyodol-synthetic-elderly` 데이터셋을 `./hyodol-data` 폴더로 받아줘. 핵심 3 테이블만 (profile, behavior_log, survey_responses) 받으면 돼."

Claude Code가 자동 수행:
1. `huggingface-cli` 설치 여부 확인 — 없으면 `pip install -U huggingface_hub[cli]`
2. 다음 명령 실행:
   ```bash
   huggingface-cli download <org>/hyodol-synthetic-elderly \
     --repo-type dataset \
     --local-dir ./hyodol-data \
     --include "data/profile.parquet" \
     --include "data/behavior_log.parquet" \
     --include "data/survey_responses.parquet" \
     --include "scripts/setup-duckdb.sql"
   ```
3. 다운로드 사이즈·파일 수 보고

### 1-B. NVIDIA Nemotron-Personas-Korea 함께 받기 (원본 페르소나 풀 탐색용)

> "추가로 NVIDIA Nemotron-Personas-Korea도 받아줘. `./nemotron-personas-korea` 폴더에. 받은 후 DuckDB로 행 수 확인까지."

Claude Code 자동 수행:
1. `huggingface-cli download nvidia/Nemotron-Personas-Korea --repo-type dataset --local-dir ./nemotron-personas-korea --max-workers 8`
2. `duckdb -c "SELECT COUNT(*) FROM read_parquet('./nemotron-personas-korea/data/*.parquet');"`
3. 결과 1,000,000과 비교 — 일치 시 무결성 OK

### 1-C. DuckDB 환경 셋업

> "내려받은 효돌 데이터로 DuckDB 환경 셋업해줘. scripts/setup-duckdb.sql 실행하고 _meta 테이블 확인해서 행 수가 맞는지 보고해줘."

Claude Code 자동 수행:
1. `cd ./hyodol-data && duckdb hyodol.duckdb < scripts/setup-duckdb.sql`
2. `duckdb hyodol.duckdb -c "SELECT * FROM _meta;"`
3. profile=1,000 / behavior_log=약 4M / survey_responses=192,000 매칭 확인 보고

### 1-D. 분석 시작

> "효돌 사용자 1,000명의 우울 점수 분포와 사용 패턴별 차이를 보여줘. DuckDB로 쿼리하고 결과를 표와 간단한 시각화로."

Claude Code 자동 수행:
1. `docs/04_analysis-guide.md` 참고하여 적절한 SQL 작성
2. DuckDB 쿼리 실행
3. pandas DataFrame → matplotlib/plotly 차트 생성
4. 결과 해석 (단, 합성 데이터임을 명시)

---

## 2. 학생이 알아야 할 Claude Code 활용 패턴

### 2-1. 데이터셋 문서 컨텍스트 로드

분석 시작 전 다음 문서들을 Claude Code 세션에 읽혀두면 분석 품질이 크게 올라간다:

```
@hyodol-data/README.md
@hyodol-data/docs/02_schema.md
@hyodol-data/docs/04_analysis-guide.md
@hyodol-data/docs/05_limitations-and-ethics.md
```

특히 `02_schema.md` 와 `05_limitations-and-ethics.md` 는 분석 결과 해석의 정확성을 좌우한다.

### 2-2. 분석 질문 던지는 좋은 패턴

❌ 나쁜 질문: "데이터 분석해줘"
✓ 좋은 질문: "60대와 80대 그룹 간 prompt 응답 딜레이 차이가 유의한지 분석해줘. 단, 합성 데이터라 통계적 검정은 탐색적 해석으로만."

✓ 좋은 질문: "사용자 유형 9분류별 GDS 우울 점수 분포를 boxplot으로 그려줘. profile 테이블만 쓰면 돼."

✓ 좋은 질문: "사용 패턴 `declining`과 `growing` 두 그룹의 90일 일별 이벤트 수 추이를 라인차트로 비교해줘."

### 2-3. 합성 데이터임을 항상 명시

Claude Code가 분석 결과를 보고할 때 다음을 항상 포함하도록 학생이 지시:
- "이 결과는 합성 데이터에서 도출된 패턴이며, 실제 효돌 사용자 모집단에 대한 추론은 불가능함"
- "통계적 검정 결과는 합성 모델이 박은 패턴의 재발견이며 새로운 발견이 아님"

### 2-4. SQL 결과를 차트로 자동 변환

```
"DuckDB로 일별 이벤트 수 시계열을 뽑은 다음, plotly로 인터랙티브 라인차트 만들어서 single HTML 파일로 저장해줘."
```

Claude Code 처리 흐름:
1. SQL 쿼리 작성·실행 (`daily_event_count` 테이블 활용)
2. pandas DataFrame 처리
3. plotly 차트 생성
4. `chart.html` 단일 파일 저장
5. 결과 파일 경로 안내

---

## 3. 학생용 분석 시나리오 5가지 (Claude Code에게 그대로 시킬 수 있는 프롬프트)

### 시나리오 1. 우울-고독 상관 + 사용 패턴별 차이

> "profile 테이블에서 GDS 사전 점수와 UCLA 사전 점수의 상관관계를 보고, 사용 패턴 7종별로 이 상관이 어떻게 다른지 분석해줘."

기대 산출: 전체 상관계수, 패턴별 7개 상관계수, 비교 시각화

### 시나리오 2. 인지 측정 페어 — 연령·우울에 따른 응답 딜레이

> "behavior_log의 cognition_tests를 활용해서 연령대(60s/70s/80s)와 GDS 범주(보통/우울/심한우울)별로 평균 응답 딜레이와 응답률을 cross-tab으로 만들어줘."

기대 산출: 3×3 매트릭스 (heatmap 가능), 패턴 해석

### 시나리오 3. 효돌 효과성 — 사전·사후 우울 점수 변화

> "사용 패턴별로 GDS 우울 점수의 사전·사후 변화량(delta)을 비교해줘. survey_pre_post_pivot 테이블 활용 가능. boxplot으로 시각화하고 어떤 사용 패턴이 효과가 큰지 결론."

기대 산출: 패턴별 delta 분포, 효과 큰 패턴 (`loyal_heavy`·`growing` 예상)

### 시나리오 4. 사용 강도 vs 사용성 평가

> "사용자별 90일 총 이벤트 수와 사용성 평가 총점의 관계를 산점도로 그리고, 어떤 사용자 유형(9분류)이 가장 만족도가 높은지 분석해줘."

기대 산출: 산점도 + 사용자유형별 평균 사용성

### 시나리오 5. 대화 패턴 분석

> "behavior_log에서 dialogue 이벤트만 필터링해서 효돌 발화와 노인 발화의 평균 길이(문자수), 일중 분포, STT 신뢰도 분포를 분석해줘. 사용 패턴별 대화량 차이도."

기대 산출: 발화 길이 통계, 시간대 차트, STT confidence 히스토그램

---

## 4. Claude Code가 모르는 도메인 지식 — 학생이 보충해야 할 것

| 항목 | Claude Code가 모르는 이유 | 학생 보충 |
|---|---|---|
| 효돌 도메인 (㈜효돌 서비스) | 학습 데이터에 없음 | `docs/01_design-and-method.md` 보여주기 |
| 9유형 사용자 분류 의미 | 효돌 자체 분류 | `docs/02_schema.md` Section 1-6 보여주기 |
| 합성 데이터 한계 | 일반 합성 모델 한계는 알지만 본 데이터셋 특수성은 모름 | `docs/05_limitations-and-ethics.md` 보여주기 |
| 효돌 원본 24명 데이터와의 차이 | 모름 | "이 데이터는 효돌 운영 스키마 reference로 합성한 1000명·90일 종단" 명시 |

---

## 5. 분석 결과 보고서 자동 생성

학생이 분석 결과를 과제로 제출할 때 Claude Code에게:

> "지금까지 분석한 내용을 마크다운 보고서로 정리해줘. 분석 질문, 방법, 결과, 해석, 한계 순서. 합성 데이터임을 명시하고 통계 결과는 탐색적 해석으로 한정해줘. 사용자 ID 개별 노출 금지."

기대 보고서 구조:
1. 분석 질문 (RQ)
2. 데이터 (효돌 합성 데이터셋 v0.1.0, n=1000, 90일)
3. 방법 (SQL·분석 도구)
4. 결과 (표·차트)
5. 해석 (탐색적 패턴)
6. **한계** (합성 데이터 / 인과 추론 불가 / 외부 일반화 불가)

---

## 6. 자주 발생하는 문제와 Claude Code에게 묻는 법

| 문제 | 학생이 Claude Code에게 묻기 |
|---|---|
| DuckDB 설치 실패 | "내 OS에 DuckDB 설치 안 돼. 에러 메시지: ... 해결책 알려줘" |
| 쿼리 결과가 이상 | "이 SQL 결과가 예상과 다른데, schema 확인하고 쿼리 디버깅해줘: `<쿼리>`" |
| 차트가 안 그려짐 | "plotly로 그렸는데 빈 차트야. 데이터 확인하고 원인 찾아줘" |
| 메모리 부족 | "DuckDB가 메모리 부족 에러. `SET memory_limit` 옵션 추가해서 다시 실행해줘" |

---

## 7. 보안·윤리 — 학생용 체크리스트

Claude Code가 자동 실행할 때 학생이 사전 점검해야 할 것:

- ✅ 합성 데이터 다운로드는 자유 (라이센스 CC BY-NC-SA 4.0)
- ✅ 분석 결과는 비상업 학술용
- ❌ 외부 SNS·블로그·공개 GitHub 리포에 데이터 자체 업로드 금지
- ❌ 분석 결과에 개별 user_id 노출 금지 — 집계·군집·분포 단위로만
- ❌ "효돌 실제 사용자가 이렇다"는 추론 금지 — 합성 패턴의 재발견일 뿐

상세 → `docs/05_limitations-and-ethics.md`

---

## 다음 문서

- 분석 패턴·SQL 템플릿: `docs/04_analysis-guide.md`
- 한계점·윤리: `docs/05_limitations-and-ethics.md`
- 스키마: `docs/02_schema.md`
