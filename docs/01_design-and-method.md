# 01. 설계 의도와 합성 방법론

- 버전: v0.2.4
- 최종 갱신: 2026-05-26
- 설계: Dylan (고영혁, Gonnector) + DATA (Gonnector AI Team)

본 문서는 효돌 합성 어르신 데이터셋이 **왜** 만들어졌고 **어떻게** 만들어졌는지 설명한다. 데이터를 분석하는 학생·LLM이 데이터의 본질을 이해하고 결과를 올바르게 해석할 수 있도록 돕는다.

---

## 1. 왜 이 데이터셋이 필요한가

### 1-1. 효돌 원본 데이터의 3가지 한계

서울대 아동가족학과 8주차 수업에서 사용한 `효돌_샘플데이터_비식별_20260424.xlsx` (24명·단일 시점)는 학술 분석용으로 합리적 구조였지만, 다음 세 가지 분석을 **구조적으로 불가능하게** 만든다.

| # | 한계 | 영향 |
|---|---|---|
| 1 | **5분 주기·일일 단위 집계** (이벤트 단위 timestamp 없음) | 시간 패턴 분석 불가, prompt-response 딜레이 측정 불가 |
| 2 | **대화 로그에 user_id 연결 없음** (782건이 단일 풀) | 사용자별 대화 패턴·정서 변화 분석 불가 |
| 3 | **prompt-response 페어링 부재** | 효돌의 "머리 쓰다듬어 주세요"라는 trigger 발화 후 실제 행동이 발생했는지·얼마나 빨리 발생했는지 추적 불가 → **인지 능력 측정 자체가 데이터 구조상 불가능** |

추가로 24명·단일 기관·단일 시점이라는 표본 한계는 통계적 유의성 확보·생활주기적 패턴 추적·사용 패턴 다양성 관찰을 모두 차단한다.

### 1-2. 본 데이터셋이 해결하는 것

위 3가지 한계를 모두 풀고, 효돌 운영팀이 실제 서비스에서 수집 가능한 데이터의 **이상적 형태**를 보여주는 것이 목적이다.

- 이벤트 단위 timestamp → 시간대별/일별 패턴 분석, prompt-response 딜레이 측정 가능
- user_id로 통합된 대화 로그 → 개인별 대화 빈도·정서 톤 변화 추적
- `cognition_test_id` 페어링 키 → 인지 능력 측정 분석 (본 데이터셋의 핵심 신규 분석 축)
- 1000명·90일 → 사용 패턴 다양성·종단 변화 관찰

### 1-3. 부수 가치 — 효돌 측에 schema upgrade 청사진

본 데이터셋의 스키마는 효돌이 실제 운영 시스템에서 **이미 수집 가능한** 신호로 구성되어 있다 (LLM 발화 timestamp·인터랙션 센서 raw event 등). 즉 본 합성 데이터로 분석 가치를 입증한 다음 효돌 측에 **실제 운영 스키마 업그레이드를 역제안**할 수 있는 부가 가치도 갖는다.

---

## 2. 핵심 설계 원칙

### 원칙 1 — 효돌 원본과 100% 호환되는 필드명·도메인값

| 합성 데이터에서 | 효돌 원본에서 |
|---|---|
| `doll_id`, `doll_gender`, `serial_number` | 동일 (효돌 운영 키) |
| `stroke`, `hand_hold`, `knock`, `human_detection` | 동일 (인터랙션 센서) |
| `story`, `religion`, `religion_music`, `music`, `classic_music`, `english`, `remembrance`, `quiz`, `gymnastics` | 동일 (콘텐츠 9종) |
| 설문 7종 (MMAS/GDS/생활관리/WHODAS/PHQ-9/UCLA/사용성) | 동일 96문항 |
| `survey_sort`, `reg_date`, `agency_name` | 동일 |

→ 효돌 원본 분석 코드가 본 데이터셋에서도 거의 그대로 동작 (테이블 명만 변경).

### 원칙 2 — 신규 확장은 effect-size 분석이 가능한 영역에만

확장된 영역(가슴 쓰다듬기·verbal response·prompt 이벤트·cognition test 페어링·사용자 유형 9분류)은 모두 **명확한 분석 질문**과 연결되어 있다. "수집 가능하니까 일단 넣자"가 아니라 "이 분석을 가능하게 하려면 이 컬럼이 필요하다"라는 역설계.

### 원칙 3 — DuckDB columnar 분석 친화적 구조

- 단일 wide `behavior_log` 테이블 (이벤트 타입별 sparse 컬럼) — DuckDB는 sparse columnar에 매우 효율적
- 자주 쓰는 derived 컬럼은 미리 (`event_date`, `event_hour`, `age_group`) — 학생이 derived expression을 매번 안 써도 됨
- 두 가지 storage 전략(`joined_wide` materialize vs `profile` JOIN `behavior_log`)을 모두 제공 → 학생이 성능 비교 학습 가능

### 원칙 4 — 합성 패턴이 합리적·해석 가능

데이터에 박혀 있는 패턴은 모두 **실제 가설에서 끌어온 것**이며, 임의 노이즈가 아니다. 예:
- WHODAS 기능제약 높을수록 prompt 응답 딜레이 증가 (인지 부하 가설)
- 우울 점수 높을수록 사용 빈도 감소 (위축 가설)
- 사용 패턴 7종은 효돌 실사용 관찰에서 자주 보이는 유형 (Dylan 도메인 입력)

이는 학생이 발견한 패턴이 "합성 모델이 박은 패턴의 재발견"임을 명시하기 위함. 데이터에 없는 패턴을 발견할 수는 없지만, 데이터에 있는 패턴을 발견하는 연습은 가능.

---

## 3. 효돌 원본 vs 합성 — 변경 매핑 요약

| 영역 | 효돌 원본 | 합성 데이터셋 | 변경 종류 |
|---|---|---|:---:|
| 식별자 | doll_id, user_name (실명) | user_id (U0001~U1000), doll_id | [수정] 익명화 |
| 시간 단위 | 5분 집계·일일 집계 | event timestamp (ms급) | [수정] 정규화 |
| 인터랙션 종류 | stroke·hand_hold·knock | + chest_pat · verbal_response | [신규] |
| 효돌 발화 추적 | 대화 로그에 묻혀 있음 | dialogue + prompt 분리 | [수정] |
| prompt-response 페어링 | 없음 | cognition_test_id 키 | [신규] ★ |
| 사용자-대화 연결 | 없음 (782건 단일 풀) | user_id 연결 | [수정] |
| 콘텐츠 종류 9가지 | 일일 카운트 | 이벤트별 시작/종료/완주 여부 | [수정] |
| 건강 문진 | 자유 대화에 묻힘 | health_check 이벤트로 분리 | [수정] |
| 설문 7종 96문항 | 시트별 wide | survey_responses long table | [수정] |
| 설문 wave | 사후 단일 시점 | 사전 + 사후 2 wave | [신규] |
| 사용자 유형 분류 | 효돌 운영 DB만 존재 | 9유형 코드·명칭 | [신규] |
| 사용 패턴 | 미분류 | 7종 패턴 (loyal_heavy/declining/spike 등) | [신규] |
| 인지 능력 측정 | 불가능 | cognition_test_id + response_delay_sec | [신규] ★ |

상세 컬럼별 마킹은 `docs/02_schema.md` 참조.

---

## 4. 합성 방법론

### 4-1. 인구통계 합성 (profile 테이블)

**Base**: NVIDIA Nemotron-Personas-Korea 1.0 (1,000,000 한국인 합성 페르소나, CC BY 4.0)
- 한국 통계청(KOSIS)·대법원·NHIS·KREI 실측 분포 기반
- 17개 시도 · 252개 시군구 커버
- 우리는 그 중 **50세 이상 sub-pool**에서 stratified sampling

**샘플링 전략**:
1. 50대 풀에서 220명 무작위 추출
2. 60대 풀에서 422명
3. 70대 풀에서 **290명** (Dylan 도메인 조정 — 80대 사용 어려움 반영하여 70대 증원)
4. 80대 풀에서 **50명** (도메인 조정 — 80대 후반부터 효돌 사용 어려움)
5. 90대 풀에서 18명

> 도메인 조정 메모: 인구 통계상 80대는 33.04%-노인층의 14.4%이지만, 실제 효돌 사용자에서는 인지·시청각 능력 한계로 80대 비중이 더 낮은 것이 합리적. 줄어든 62명을 70대로 이전.

**효돌 도메인 보강**:
- `doll_id`, `doll_gender`, `doll_nickname`, `install_date`, `install_agency` — 효돌 원본 필드 채우기
- `spouse`, `having_children`, `son`, `daughter`, `housing_cleanliness`, `meal`, `taking_medicine` — 효돌 원본 컬럼, 일부 의도적 결측 포함 (효돌 원본의 결측 패턴 재현)
- `user_type_code/name` — 효돌 2.5세대 9유형 (VSSI/MISSI/JCSI/VSED/MSED/JCIED/VSMC/MSMC/JCMC) 분류 (우울지표·선호 인터랙션 기반 stochastic 할당)

**Hidden state (외부 노출 안 함)**:
- `cognition_baseline_score` (0~1) — 인지 능력 잠재 변수. 행동 응답 생성 시 사용.

### 4-2. 베이스라인 설문 합성 (survey_responses 테이블 — wave='pre')

각 사용자의 **연령·성별·우울·고독·기능제약 잠재 변수**에서 7종 96문항 응답을 stochastic하게 생성.

**합성 모델**:
1. 각 사용자에 대해 5개 잠재 변수 (`latent_depression`, `latent_loneliness`, `latent_function`, `latent_adherence`, `latent_lifestyle`) 를 prior 분포에서 sample
   - prior는 연령·성별·혼인상태·가구형태에 conditional (예: 사별·1인가구 → loneliness prior 높음)
2. 각 문항에 대해 잠재 변수 + 문항별 loading + 측정 오차로 응답 생성
3. 역문항(GDS 1·5·7·11·13, UCLA 1·4·5·6·9·10·15·16·19·20, 사용성 7·8·9)은 reverse-coding 적용
4. 총점·result(보통/우울/심한우울 등)는 효돌 원본 채점 룰 그대로 계산

**효돌 원본과의 통계적 정합성**:
- 효돌 원본 24명의 점수 분포를 mean·std reference로 사용 (단, 표본 작아 정밀한 fitting은 안 함)
- 우리 1000명은 효돌 24명보다 분산이 더 넓을 가능성 (다양성 강조)

### 4-3. 행동 로그 합성 (behavior_log 테이블)

가장 복잡한 부분. **사용자별 사용 패턴 7종**을 먼저 할당하고, 각 패턴이 90일 시계열로 일평균 이벤트 수를 결정.

**Step 1 — 사용 패턴 할당** (분배 비율 default, Dylan 피드백 가능)

| 패턴 코드 | 패턴 명 | 시계열 형태 | 비중 | 일평균 이벤트 |
|---|---|---|---:|---:|
| `loyal_heavy` | 꾸준히 많이 씀 | 평탄 고원 | 15% | 80~150 |
| `loyal_light` | 꾸준히 거의 안 씀 | 평탄 저원 | 20% | 2~8 |
| `growing` | 점점 많이 씀 | 우상향 | 12% | 5→100 |
| `declining` | 점점 안 씀 | 우하향 | 15% | 80→3 |
| `spike` | 안 쓰다 갑자기 많이 → 다시 안 씀 | 봉우리 | 8% | 평소 5, peak 150 |
| `fading` | 점점 줄어 결국 0 | 소실 | 15% | 80→0 |
| `trial_drop` | 초반 며칠 써보고 안 씀 | 체험 후 이탈 | 15% | 첫 7일 50, 이후 0 |

**Step 2 — 일별 이벤트 수 결정**: 사용 패턴 × 사용자별 잠재 활성도 × 요일 효과 × 일별 노이즈

**Step 3 — 이벤트 mix**: 결정된 일별 이벤트 수를 다음 비율로 split
- dialogue (turn) 28%
- interaction 33%
- program 9%
- health_check 9% (효돌은 하루 2회 문진 → 5종 × 2 = 일 4회 base)
- prompt 14% (그 중 9%는 cognition_test_id 보유)
- system 7%

**Step 4 — 이벤트별 timestamp 분포**:
- 효돌 사용 시간대: 오전 7시·점심 12시·오후 3시·저녁 7시 peak (실측 보고서 참조)
- 야간 시간은 system 이벤트(human_detection·battery)만 남음

**Step 5 — 인지 측정 페어링**:
- prompt event 생성 시 30~50% 확률로 `cognition_test_id` 부여
- 해당 prompt 다음 0~window_sec 사이에 매칭 interaction event 생성 여부를 `cognition_baseline_score`에서 sample
- 매칭되면 response_delay_sec = (T_interaction - T_prompt)의 stochastic 변형 (인지 능력↓일수록 delay 분포 right-skew)

### 4-4. 대화 스크립트 합성

**Reference**: 효돌_샘플데이터_비식별_20260424.xlsx Sheet1 (782건 원본 대화)

**방법**:
1. 원본 782건을 분석하여 다음 패턴 추출
   - 효돌 발화 종류: 인사·일과 알림·건강 문진·정서 표현·콘텐츠 도입 등
   - 노인 발화 종류: 짧은 동의·과거 회상·가족 언급·신체 호소·종교 표현 등
   - turn 길이 분포 (효돌 평균 약 35자, 노인 평균 약 15자)
   - STT 인식 오류 패턴 (효돌 → 효도리·효소리·효들이 등)
2. 사용자별 페르소나·우울/고독 점수·사용 패턴에 맞춰 대화 톤·주제 조정
3. 50명은 **풀 LLM 합성** (Claude/GPT 기반, 자연스러운 다양성), 나머지 950명은 **템플릿 stochastic 변형 + 일부 LLM mix**로 비용 효율 확보
4. STT 인식 오류는 사용자별 `dialogue_stt_confidence`에 따라 0~30% 확률로 삽입 (실제 효돌은 사투리·고령 발음에서 인식률 낮음)

**인지 측정 prompt 발화 풀**:
- 머리 쓰다듬기 요청: "할머니, 효돌 머리 한번 쓰다듬어 주세요" 등 12종 변형
- 손잡기 요청: "효돌 손 한번 잡아주세요" 등 8종
- 가슴 쓰다듬기 요청: "효돌 가슴 토닥토닥 해주세요" 등 6종
- verbal 응답 요청: "오늘 기분 어떠세요?" 등 효돌 문진 5종

### 4-5. 사후 설문 합성 (survey_responses — wave='post')

사전(pre) wave에서 90일 후 효돌 사용 영향을 받은 사후(post) wave 응답.

**합성 모델**:
1. 사용자별 효돌 사용 강도 (90일 평균 일이벤트 수)와 사용 패턴이 사전→사후 변화 폭을 결정
   - `loyal_heavy`·`growing` 사용자: 우울·고독 점수 개선, 생활관리·복약 점수 향상
   - `declining`·`fading` 사용자: 변화 미미 또는 일부 악화
   - `trial_drop` 사용자: 거의 변화 없음
2. 변화 폭은 효돌 브로셔 페이지 8의 사전·사후 변화 차트를 reference로 보정
   - 우울증 검사 평균: 10.3 → 7.4 (-2.9)
   - 스트레스 검사: 23.4 → 18.8 (-4.6)
   - 우울증 위험 낮음 비율: 81.0% → 85.7% (+4.7%p)
   - 생활관리 점수: 거의 모든 항목에서 평균 0.1~0.3 향상

---

## 5. 결과 — 최종 데이터셋 사양 (v0.2.1 실측)

| 항목 | 값 |
|---|---|
| 표본 수 | 어르신 1,000명 (500명 × 2 batch 머지) |
| 연령 범위 | 50~99세 (60+ 비중 78% — 70대 강화·80대 축소 도메인 조정) |
| 관찰 기간 | 90일 (2026-01-01 ~ 2026-03-31) |
| 행동 로그 이벤트 수 | **3,671,068** (실측) |
| 일평균 이벤트 (가중 평균) | 약 41건 |
| 사용 패턴 종류 | 7종 (loyal_heavy 155 / loyal_light 202 / growing 123 / declining 140 / spike 87 / fading 134 / trial_drop 159) |
| 인지 측정 페어 수 | **265,379 cognition_test_id** (1000명 평가 보고서 실측) |
| 설문 응답 수 | **168,000** (사전 72,000 + 사후 96,000 — usability 사전 wave 없음) |
| 대화 turn 수 | 약 815K (효돌 + 노인 페어링 포함) |
| 테이블 수 | 3 (profile / behavior_log / survey_responses) — joined_wide는 v0.2.x에서 분석 시 학생이 직접 JOIN |
| Parquet ZSTD 압축 후 | **약 66 MB** 실측 (profile 0.08 + behavior_log 65.88 + survey_responses 0.17) |
| 외부 평가 | 3차 sub-agent 평가에서 8/8 PASS (A·D·G FAIL 0, 핵심 가설 E 5/5 강한 단조) |

---

## 다음 문서

- 4 테이블 상세 스키마: `docs/02_schema.md`
- 다운로드·DuckDB 설정: `docs/03_setup-and-download.md`
- 분석 가이드: `docs/04_analysis-guide.md`
- 한계점·윤리: `docs/05_limitations-and-ethics.md`
