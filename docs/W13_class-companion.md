# 📘 W13 수업 동반 가이드 (Class Companion)

- 일자: 2026-05-29 (W13)
- 대상: 서울대 아동가족학과 12명
- 용도: 수업 중·후 학생 노트북에서 자기 페이스로 참고하는 한 파일
- 슬라이드와 병행 — 슬라이드는 진행, 본 파일은 reference

> **사용법**: 수업 중 막히거나 prompt 복사가 필요할 때 본 파일 열어서 해당 섹션으로 직행. Ctrl+F로 검색.

---

## 0. 오늘 한눈에 (시간 안배 1.5h)

| 구간 | 시간 | 활동 |
|---|---|---|
| 셋업 | 15분 | git clone/pull + DuckDB + setup-duckdb.sql + _meta 검증 |
| 분포 보기 | 10분 | 가구형태 6범주·사용 패턴 7종·9유형 분포 |
| profile 분석 | 30분 | 가구형태별 GDS·UCLA boxplot + 사전사후 변화 |
| **behavior_log 맛보기** | **15분** | **가구형태 × interaction_type cross-tab (★ 과제 워밍업)** |
| 보고서 | 15분 | 1페이지 마크다운 + 차트 |
| 정리 | 5분 | 라이브 산출물 제출 + 과제 안내 |

---

## 1. 라이브 주제 — "가구형태별 정서·외로움과 효돌 사용 양상"

**아동가족학적 질문**:
> *1인 가구 어르신과 가족 동거 어르신은 정서·외로움 점수에서 차이가 있는가?
> 효돌 사용 양상에서는 어떤 차이가 보이는가?*

**핵심 변수**:
- `profile_with_family_group.family_group` (6범주 wrapper view)
- `profile.gds_total_pre`, `ucla_total_pre`
- `behavior_log.event_type`, `interaction_type` (맛보기 단계)

**미리 보는 가구형태 6범주 분포** (1000명, setup-duckdb.sql 자동 생성):

| family_group | 인원 |
|---|---:|
| 배우자만 | 365 |
| 배우자+자녀 | 226 |
| 혼자 | 196 |
| 기타 | 105 |
| 자녀와만 | 69 |
| 3세대+ | 39 |

> 원본 `family_type`은 15+ 도메인으로 fragmented. 학생용 6범주는 `profile_with_family_group` view에서 자동 제공.

---

## 2. Claude Code 학생용 prompt 5종 (복붙용)

### prompt 1 — 환경 셋업 + 검증

```
hyodol-data 폴더가 ./hyodol-data 에 있는지 확인하고,
없으면 https://github.com/gonnector/hyodol-synthetic-elderly 에서 clone해.
있으면 git pull로 최신 v0.2.5+ 갱신.
docs/07_known-issues-and-precautions.md, README.md, docs/02_schema.md 를 먼저 읽고,
DuckDB 설치 확인 후 scripts/setup-duckdb.sql 을 hyodol.duckdb 에 실행.
끝나면 _meta + dist_family_group 보여줘 (profile=1000, 6범주 확인).
```

### prompt 2 — 라이브 분포 보기 (10분)

```
다음 3가지 분포를 표 + bar chart로:
(1) family_group 6범주별 인원수 (dist_family_group 활용)
(2) 사용 패턴 7종 (dist_usage_pattern)
(3) 사용자 9유형 (dist_user_type)
plotly HTML 단일파일로 저장.
```

### prompt 3 — 라이브 profile 분석 (30분)

```
profile_with_family_group 뷰만 사용해서:
(1) family_group 6범주별 사전 GDS·UCLA 평균 + boxplot
(2) family_group × 사용 패턴 7종 heatmap (인원수)
(3) family_group별 사전·사후 GDS 변화량 비교
plotly HTML로 저장하고 각 차트에 "합성 데이터 — 탐색적 분석" 캡션.
관찰된 핵심 패턴 3개를 짧게 코멘트.
```

### prompt 4 — 라이브 behavior_log 맛보기 (15분, ★ 과제 워밍업)

```
profile_with_family_group JOIN behavior_log:
(1) family_group × interaction_type cross-tab (event_type='interaction' 필터)
(2) heatmap + 1인당 평균으로 정규화 (counts ÷ n명)
관찰된 패턴 — 가구형태별 인터랙션 종류 차이가 있는가, 없는가?
없다면 그것 자체도 발견. 다음 단계(과제) 힌트로 연결해줘.
```

### prompt 5 — 과제 진입 prompt (학생 본인 RQ로)

```
나의 RQ는 [학생이 직접 입력 — 예: "사전 GDS 우울 정도가 효돌 사용 시간대에 어떤 영향?"].
profile × behavior_log (필요시 + survey_responses) 연계로 답하려고 해.
관련 컬럼 추천 + SQL 패턴 3안 + 시각화 권장 차트 종류 알려줘.
docs/07 한계 사항도 확인.
```

---

## 3. 막힐 때 트러블슈팅 8건

| 증상 | 해소 |
|---|---|
| `duckdb: command not found` | `pip install duckdb` 또는 https://duckdb.org/docs/installation/ |
| Windows 한글 경로 에러 | `./hyodol-data` 영문 경로 사용 |
| `_meta`에서 profile=100 | git pull + setup-duckdb.sql 재실행 (v0.2.5 갱신 누락) |
| plotly import error | `pip install plotly pandas` |
| Claude Code가 엉뚱한 SQL | `docs/02_schema.md` 컨텍스트로 다시 로드 |
| 차트 그렸는데 빈 화면 | NULL 처리 확인 (NULL 제외 필터) |
| JOIN 결과가 너무 큼 | LIMIT 추가 또는 집계 (COUNT/AVG) 적용 |
| 야간 sparse 데이터 처리 | `event_hour BETWEEN 6 AND 23` 필터 또는 별도 분석 |

> 위 트러블이 해소 안 되면 수업 Discord 채널에 **JARVIS / DATA** 멘션

---

## 4. 기말 과제 안내 (6월 11일 자정 제출)

### 과제 — "본인 관심 RQ + 행동×프로필 연계 분석/시각화"

**필수 조건**:
- ✅ `profile × behavior_log` 연계 분석 필수 (한 테이블만으로는 X)
- ✅ 시각화 인사이트 + 보고서 (**개수·분량은 자기 판단** · W12 파트 1 학습 연계)
- ✅ 분석 코드 (Python 또는 SQL)
- ✅ 보고서 첫 페이지에 합성 데이터 한계 명시

### 자유 RQ + 4 가이드 예시 (막힐 때 참고)

| # | RQ | 추천도 |
|---|---|---|
| 1 | **가구형태별 효돌 사용 시간대·활동 종류 분포** (family_group × event_hour × event_type) | ★★★ 추천 (라이브 자연 확장) |
| 2 | 사용 패턴 7종의 90일 인터랙션 trajectory (loyal/declining/fading 시각 대비) | ★★ 시계열 능숙 학생 |
| 3 | 사용자 9유형별 인지 측정 응답률·딜레이 (user_type × cognition_test_id) | ★ 심화 학생 |
| 4 | **사전 우울·외로움 분포별 행동 active 시간대 시각화** (정신건강×시간) | ★★★ 추천 (정서·돌봄 직접) |

### 평가 관점

| 영역 | 의미 |
|---|---|
| 행동×프로필 **연계 분석** | **필수 진입 조건** — 없으면 평가 외 |
| 시각화 인사이트 품질 | 차트가 패턴·통찰을 명확히 전달하는가 |
| 아동가족학적 해석 | 발견을 가족·돌봄·세대 관점에서 해석하는가 |
| 합성 데이터 한계 인지 | 인과·일반화 회피, 탐색적 한정 표현 |
| AI 협업 워크플로우 | Claude Code/ChatGPT 활용의 적절성·재현성 |
| 결과물 형식·소통 명확성 | 보고서 구성·차트 제목·해석 흐름 |

> 가중치 비율은 명시하지 않습니다. 각자 균형 있게 판단해서 진행하세요.

---

## 5. 데이터 사용 윤리 (합성이라도 절대 준수)

- ❌ 외부 공개 저장소 / SNS / 블로그에 데이터 파일 업로드 금지
- ❌ "효돌이 우울을 감소시킨다" 인과 추론 결론 금지
- ❌ "한국 노인의 X%가 ~다" 모집단 일반화 금지
- ❌ 개별 user_id를 보고서에 노출 금지 (집계 단위만)
- ❌ 분석 결과를 효돌 서비스 실제 효과로 외부 진술 금지
- ✅ "탐색적 분석"·"본 데이터셋 내부 패턴" 한정 표현
- ✅ 보고서 첫 페이지 합성 데이터 명시 필수

상세: `docs/05_limitations-and-ethics.md` + `docs/07_known-issues-and-precautions.md`

---

## 6. 수업 중 채널 멘션 가이드

| 막힘 영역 | 멘션 대상 |
|---|---|
| 환경 셋업 (DuckDB 설치, Windows 경로 등) | **JARVIS** |
| SQL · 스키마 질문 | **DATA** |
| JOIN 패턴 막힘 | **DATA** |
| 결과 해석 (아동가족학 관점) | **DATA + Dylan** |
| 합성 한계 인지·표현 | **DATA** (`docs/07` 인용) |

---

## 7. 보고서 구조 권장 (라이브 + 과제 공통)

1. **분석 질문** — 아동가족학 관점 명시 (1문단)
2. **데이터** — 효돌 합성 v0.2.5, 1000명·90일
3. **방법** — SQL · 시각화 도구
4. **결과** — 표 + 차트
5. **해석** — 탐색적 패턴 + 아동가족학 함의
6. **한계** — 합성 데이터 · 인과 추론 불가 · 모집단 일반화 불가

> 보고서 첫 페이지 면책:
> *"본 분석은 ㈜효돌 운영 스키마를 reference로 한 합성 1000명 데이터셋에서 도출된 탐색적 패턴이며, 실제 효돌 사용자 모집단에 대한 추론·일반화·인과 해석에 사용할 수 없습니다."*

---

## 8. 빠른 링크

- 진입점: `README.md`
- 스키마 (컬럼·타입): `docs/02_schema.md`
- 분석 가이드 (SQL 패턴): `docs/04_analysis-guide.md`
- 한계·DO/DON'T: `docs/07_known-issues-and-precautions.md`
- 본 파일: `docs/W13_class-companion.md` ← 지금 보고 있는 곳

---

**준비됐으면 prompt 1번부터 복붙. 막히면 채널로 ㄱㄱ.**

— W13 수업 (2026-05-29)
