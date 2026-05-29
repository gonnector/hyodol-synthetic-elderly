# 02. 4 테이블 상세 스키마

- 버전: v0.1.0 (스키마 v1.1)
- 최종 갱신: 2026-05-21
- 작성자: DATA

본 문서는 효돌 합성 어르신 데이터셋의 4개 테이블 전체 컬럼 스펙을 담는다. 컬럼마다 `[유지]`(효돌 원본 그대로)·`[수정]`(원본 진화)·`[신규]`(완전 확장) 마킹이 일관 적용된다.

---

## 0. ER 다이어그램

```
profile (1,000)            survey_responses (192K)
 ┌────────────┐             ┌──────────────────┐
 │ user_id PK │◀────────────│ user_id          │
 │ ...        │             │ wave (pre/post)  │
 │ doll_id    │             │ survey_type      │
 └────────────┘             │ question_no      │
       │                    │ answer_text      │
       │                    │ answer_score     │
       │                    └──────────────────┘
       │
       │   behavior_log (~430만)
       │   ┌────────────────────────┐
       └──▶│ user_id FK             │
           │ event_id PK            │
           │ event_ts               │
           │ event_type             │
           │ (sparse columns by     │
           │  event_type)           │
           │ cognition_test_id      │── prompt-response 페어링
           └────────────────────────┘

joined_wide (~430만)  ← profile + behavior_log denormalized (벤치마크 전용)
```

---

## 1. `profile` 테이블 (1,000 rows)

### 1-1. 식별자

| 컬럼 | 타입 | 종류 | 설명 |
|---|---|:---:|---|
| `user_id` | VARCHAR PK | [유지] | U0001~U1000 (효돌 U001 패턴 자릿수 확장) |
| `doll_id` | VARCHAR | [유지] | 효돌 운영 키 (예: 8001~9999) |
| `serial_number` | VARCHAR | [유지] | 인형 일련번호 해시 (S-XXXXXXXX) |

### 1-2. 인구통계 (Nemotron-Personas-Korea 출처)

| 컬럼 | 타입 | 종류 | 설명 |
|---|---|:---:|---|
| `sex` | VARCHAR | [유지] | 남자/여자 |
| `age` | INT | [유지] | 50~99 |
| `age_group` | VARCHAR | [신규] | 50s / 60s / 70s / 80s / 90s (derived) |
| `marital_status` | VARCHAR | [유지] | 미혼/배우자있음/사별/이혼 |
| `family_type` | VARCHAR | [유지] | 부부+미혼자녀/배우자와 거주/혼자 거주 등 39종 |
| `housing_type` | VARCHAR | [유지] | 아파트/단독주택/다세대주택 등 6종 |
| `education_level` | VARCHAR | [유지] | 무학~대학원졸 7종 |
| `occupation` | VARCHAR | [유지] | 자유서술 (60+ 대부분 무직·은퇴) |
| `province` | VARCHAR | [유지] | 17개 시·도 |
| `district` | VARCHAR | [유지] | 252개 시·군·구 |

### 1-3. 효돌 설치·환경 정보

| 컬럼 | 타입 | 종류 | 설명 |
|---|---|:---:|---|
| `doll_gender` | VARCHAR | [유지] | 효돌 인형 성별 설정 (남성/여성) — 사용자 성별과 동일하게 설정하는 경향 |
| `doll_nickname` | VARCHAR | [신규] | 사용자가 부르는 효돌 호칭 ("효돌이"/"우리효도리"/"우리아기" 등) |
| `install_date` | TIMESTAMP | [수정] | 효돌 설치 일자 (효돌 원본 reg_date 진화) |
| `install_agency` | VARCHAR | [유지] | 합성 기관명 (8개 풀, 도시·농촌 mix) |
| `agency_type` | VARCHAR | [신규] | urban_welfare / rural_welfare / nursing_facility / home_visit |
| `is_survey_possible` | VARCHAR | [유지] | 가능/불가능 |

### 1-4. 생활·건강 컨텍스트 (효돌 원본 유지, 의도적 결측 포함)

| 컬럼 | 타입 | 종류 | 설명 |
|---|---|:---:|---|
| `spouse` | VARCHAR | [유지] | 배우자 여부 (결측 다수 — 효돌 원본 패턴 재현) |
| `having_children` | VARCHAR | [유지] | 자녀 유무 |
| `son` | INT | [유지] | 아들 수 |
| `daughter` | INT | [유지] | 딸 수 |
| `housing_cleanliness` | VARCHAR | [유지] | 좋음/보통/나쁨 |
| `meal` | VARCHAR | [유지] | 식사 상태 |
| `public_visit_support` | VARCHAR | [유지] | 공공방문 지원 |
| `taking_medicine` | VARCHAR | [유지] | 복용약 명 (자유서술) |

### 1-5. 베이스라인 설문 총점·결과 (effizient cross-tab용)

> 문항별 응답은 `survey_responses` 테이블 참조. profile에는 총점·결과만 보관.

| 컬럼 | 타입 | 종류 | 범위 |
|---|---|:---:|---|
| `mmas_total_pre` | TINYINT | [유지] | 0~20 (복약 순응도) |
| `mmas_total_post` | TINYINT | [신규] | 사후 wave |
| `gds_total_pre` | TINYINT | [유지] | 0~15 |
| `gds_total_post` | TINYINT | [신규] | |
| `gds_result_pre` | VARCHAR | [유지] | 보통/우울/심한우울 |
| `gds_result_post` | VARCHAR | [신규] | |
| `phq9_total_pre` | TINYINT | [유지] | 0~27 |
| `phq9_total_post` | TINYINT | [신규] | |
| `phq9_q9_pre` | TINYINT | [유지] | 9번 자살사고 별도 노출 |
| `phq9_q9_post` | TINYINT | [신규] | |
| `ucla_total_pre` | TINYINT | [유지] | 20~80 |
| `ucla_total_post` | TINYINT | [신규] | |
| `whodas_total_pre` | TINYINT | [유지] | 0~60 |
| `whodas_total_post` | TINYINT | [신규] | |
| `life_mgmt_total_pre` | TINYINT | [유지] | 생활관리 |
| `life_mgmt_total_post` | TINYINT | [신규] | |
| `life_mgmt_result_pre` | VARCHAR | [유지] | 좋음/보통/나쁨 |
| `life_mgmt_result_post` | VARCHAR | [신규] | |
| `usability_total_post` | TINYINT | [유지] | 효돌 사용성 (사후만, 사전 의미 없음) |

### 1-6. 효돌 2.5세대 사용자 유형 분류

| 컬럼 | 타입 | 종류 | 설명 |
|---|---|:---:|---|
| `user_type_code` | VARCHAR | [신규] | 9유형 코드 |
| `user_type_name` | VARCHAR | [신규] | 9유형 한글명 |

9유형 (효돌 2.5세대 분류 엔진 SSoT):

| 코드 | 한글명 | 영역 |
|---|---|---|
| VSSI | 신앙건강형 | Sacred Interactors |
| MISSI | 정서의존형 | Sacred Interactors |
| JCSI | 은둔성향형 | Sacred Interactors |
| VSED | 활동영성형 | Energetic Diversions |
| MSED | 묵묵성실형 | Energetic Diversions |
| JCIED | 재택대로형 | Energetic Diversions |
| VSMC | 열린다기능형 | Melody Connectors |
| MSMC | 우심사용형 | Melody Connectors |
| JCMC | 고요자율형 | Melody Connectors |

### 1-7. 사용 패턴 (합성 데이터셋 신규)

| 컬럼 | 타입 | 종류 | 설명 |
|---|---|:---:|---|
| `usage_pattern` | VARCHAR | [신규] | loyal_heavy / loyal_light / growing / declining / spike / fading / trial_drop |
| `usage_pattern_label` | VARCHAR | [신규] | 한글 라벨 (꾸준히 많이 씀 등) |

### 1-8. 효돌 설정·hidden state

| 컬럼 | 타입 | 종류 | 설명 |
|---|---|:---:|---|
| `alarm_settings` | JSON | [신규] | { meal_morning, meal_lunch, meal_dinner, med_morning, ... } |
| `dialogue_stt_confidence` | FLOAT | [신규] | 0.0~1.0 사용자별 STT 인식 신뢰도 평균 |
| `cognition_baseline_score` | FLOAT | [신규] | 0.0~1.0 인지 능력 잠재 변수 (분석 시 참고만, hidden state) |

---

## 2. `behavior_log` 테이블 (약 350만~430만 rows)

핵심 설계: **단일 wide table + event_type별 sparse 컬럼**. DuckDB columnar가 sparse 저장에 강함.

### 2-1. 공통 컬럼 (모든 이벤트)

| 컬럼 | 타입 | 종류 | 설명 |
|---|---|:---:|---|
| `event_id` | BIGINT PK | [신규] | 1부터 순차 |
| `user_id` | VARCHAR FK | [수정] | profile.user_id (원본은 dialogue에 user 연결 없었음) |
| `event_ts` | TIMESTAMP | [수정] | 이벤트 발생 시각 (ms급 정밀) |
| `event_date` | DATE | [신규] | derived (대시보드 파티셔닝용) |
| `event_hour` | TINYINT | [신규] | 0~23 |
| `event_dow` | TINYINT | [신규] | 0=월~6=일 |
| `event_type` | VARCHAR | [신규] | dialogue / interaction / program / health_check / prompt / system |
| `event_subtype` | VARCHAR | [신규] | event_type별 세부 분류 |

### 2-2. Dialogue 전용 (event_type='dialogue')

| 컬럼 | 종류 | 설명 |
|---|:---:|---|
| `dialogue_turn_id` | [신규] | 같은 대화 세션의 효돌-노인 turn을 묶는 ID |
| `dialogue_speaker` | [수정] | 'hyodol' / 'senior' (원본은 컬럼 2개, 우리는 row 2개로 정규화) |
| `dialogue_text` | [유지] | 발화 텍스트 (효돌 원본 hyodol_utterance/senior_utterance 통합) |
| `dialogue_duration_sec` | [신규] | 발화 길이 (초) |
| `dialogue_stt_confidence` | [신규] | senior 발화의 STT 인식 신뢰도 (0~1). 낮을수록 효돌→효도리/효소리 등 인식 오류 변형 빈도↑. **변형 비율의 분모 정의는 `docs/07_known-issues-and-precautions.md` Section 1-3 항목 #9 참조** (전체 senior 발화 분모 기준 약 12.76%, 의도 10~30% 정상) |

### 2-3. Interaction 전용 (event_type='interaction')

| 컬럼 | 종류 | 설명 |
|---|:---:|---|
| `interaction_type` | [유지+신규] | stroke / hand_hold / knock (유지) + **chest_pat / verbal_response (신규)** |
| `interaction_duration_sec` | [신규] | 머리쓰다듬기·손잡기 지속 시간 |
| `interaction_intensity` | [신규] | 1~5 강도 (센서 데이터 합성) |

interaction_type 5종 상세:

| 타입 | 효돌 원본 | 설명 |
|---|:---:|---|
| `stroke` | ○ | 인형 머리 쓰다듬기 |
| `hand_hold` | ○ | 인형 손 버튼 누름·잡음 |
| `knock` | ○ | 인형 등 두드림 |
| `chest_pat` | × (신규) | 인형 가슴 토닥토닥 |
| `verbal_response` | × (신규) | 효돌 질문에 사용자가 음성으로 답변 (별도 dialogue 발화로도 기록되지만, response interaction으로 paired 가능) |

### 2-4. Program 전용 (event_type='program')

| 컬럼 | 종류 | 설명 |
|---|:---:|---|
| `program_type` | [유지] | story / religion / religion_music / music / classic_music / english / remembrance / quiz / gymnastics |
| `program_duration_sec` | [신규] | 프로그램 실제 수행 시간 |
| `program_completed` | [신규] | 완주 여부 (중도 이탈 검출) |
| `program_quiz_correct` | [신규] | 퀴즈 시 정답 수 |
| `program_quiz_total` | [신규] | 퀴즈 시 출제 수 |

### 2-5. Health Check 전용 (event_type='health_check')

| 컬럼 | 종류 | 설명 |
|---|:---:|---|
| `health_question` | [수정] | sleep / mood / plan / pain / appetite (효돌 운영 5종) |
| `health_answer` | [수정] | 사용자 답변 텍스트 |
| `health_answer_category` | [신규] | derived (mood: positive/neutral/negative 등) |

### 2-6. Prompt 전용 (event_type='prompt')

신규 이벤트 타입. 효돌이 사용자에게 던지는 발화 중 **사용자 행동 응답을 기대하는 것**만 prompt로 마킹.

| 컬럼 | 종류 | 설명 |
|---|:---:|---|
| `prompt_type` | [신규] | head_stroke_request / hand_hold_request / chest_pat_request / verbal_response_request / quiz_response_request / medication_reminder / activity_invite |
| `prompt_text` | [신규] | 효돌의 실제 발화 |
| `cognition_test_id` | [신규] | prompt-response 페어링 키 (UUID) — NULL이면 인지 측정 대상 아님 |
| `cognition_window_sec` | [신규] | 응답 대기 window (기본 30초) |
| `response_occurred` | [신규] | window 내 매칭 인터랙션 발생 여부 |
| `response_delay_sec` | [신규] | prompt_ts ↔ matched interaction_ts 차이 (NULL이면 미응답) |
| `response_event_id` | [신규] | 페어링된 interaction의 event_id |

prompt_type ↔ 기대 response interaction_type:

| prompt_type | 기대 응답 | 측정 의도 |
|---|---|---|
| `head_stroke_request` | stroke | 청각→운동 응답 |
| `hand_hold_request` | hand_hold | 동일 |
| `chest_pat_request` | chest_pat | 신규 인터랙션 측정 |
| `verbal_response_request` | verbal_response (dialogue 'senior' 발화) | 언어 처리 능력 |
| `quiz_response_request` | dialogue 'senior' 발화 (정답 판정) | 작업 기억·인지 부하 |
| `medication_reminder` | — | (인지 측정 대상 아님) |
| `activity_invite` | — | (인지 측정 대상 아님) |

### 2-7. System (event_type='system')

| 컬럼 | 종류 | 설명 |
|---|:---:|---|
| `battery_pct` | [유지] | 효돌 원본 battery |
| `human_detected` | [유지] | 효돌 원본 human_detection |
| `last_action_gap_sec` | [수정] | 효돌 last_none_action_time을 gap 초로 변환 |

---

## 3. `survey_responses` 테이블 (약 192,000 rows)

96문항 × 1000명 × 2 wave = 192,000 행.

| 컬럼 | 타입 | 종류 | 설명 |
|---|---|:---:|---|
| `response_id` | BIGINT PK | [신규] | 1부터 순차 |
| `user_id` | VARCHAR FK | [유지] | profile.user_id |
| `wave` | VARCHAR | [신규] | 'pre' (설치 직전) / 'post' (90일 후) |
| `survey_type` | VARCHAR | [신규] | mmas / gds / life_mgmt / whodas / phq9 / ucla / usability |
| `question_no` | TINYINT | [유지] | 1~24 (설문별 다름) |
| `question_text` | VARCHAR | [유지] | 효돌 원본 문항 텍스트 그대로 |
| `answer_text` | VARCHAR | [유지] | 응답 텍스트 ("전혀 그렇지 않다" 등) |
| `answer_score` | TINYINT | [수정] | 정수 점수 (역문항 reverse-coding 완료 상태) |
| `is_reverse_coded` | BOOLEAN | [신규] | 원래 역문항이었는지 마킹 |
| `reg_date` | TIMESTAMP | [유지] | 응답 일자 |

7종 설문별 문항 구성 (효돌 원본 그대로):

| survey_type | 문항 수 | 응답 척도 | 총점 범위 | 부가 |
|---|---:|---|---|---|
| `mmas` | 4 | 5점 리커트 | 0~20 | — |
| `gds` | 15 | 예/아니오 (이분) | 0~15 | result 범주 |
| `life_mgmt` | 8 | 빈도 5단계 | — | result 범주 |
| `whodas` | 15 (12+3) | 5점 + 일수 3개 | 0~60 | — |
| `phq9` | 10 (9+기능손상) | 4점 + 어려움 | 0~27 | 9번 자살사고 별도 |
| `ucla` | 20 | 4점 (역문항 10개) | 20~80 | — |
| `usability` | 24 | 5점 | 24~120 | 8개 하위영역 |

usability 8개 하위영역 (사용성 평가):

| 영역 | 문항 번호 | 설명 |
|---|---|---|
| 신뢰·유능성 | 1~6 | |
| 부정 감정 (역문항) | 7~9 | |
| 사용 용이성 | 10~12 | |
| 대화 성능 | 13~14 | |
| 대화 빈도·양 | 15~16 | |
| 대화 만족 | 17~18 | |
| 사용 빈도·양 | 19~20 | |
| 전반 만족·지속의향 | 21~24 | |

---

## 4. `joined_wide` 테이블 (약 350만~430만 rows)

`profile`의 모든 컬럼을 `behavior_log`의 모든 행에 broadcast한 denormalized 표.

```sql
CREATE TABLE joined_wide AS
SELECT b.*, p.*
FROM behavior_log b
JOIN profile p USING (user_id);
```

**용도**: 단일 wide 스캔 vs profile JOIN behavior_log 두 가지 storage 전략 성능 비교. 운영 분석에는 사용하지 말고 벤치마크 전용.

벤치마크 쿼리 4종 (`docs/04_analysis-guide.md` 참조):
- Q1: 일별 stroke 카운트 by age_group
- Q2: user별 prompt 응답률
- Q3: region × user_type 매트릭스
- Q4: 인지 측정 delay 분포 by GDS 범주

---

## 5. 인지 능력 측정 페어링 메커니즘 (핵심 신규)

### 5-1. 데이터 흐름

```
T0: prompt event 발생
    event_id = 100,001
    event_type = 'prompt'
    prompt_type = 'head_stroke_request'
    prompt_text = "할머니, 효돌 머리 한번 쓰다듬어 주세요"
    cognition_test_id = 'CT-7a3b91f2-...'
    cognition_window_sec = 30

    ↓ (사용자가 듣고 행동까지 인지·실행)

T1: interaction event 발생 (T0 + 4.2초)
    event_id = 100,005
    event_type = 'interaction'
    interaction_type = 'stroke'
    cognition_test_id = 'CT-7a3b91f2-...'  ← 같은 키로 페어링

    ↓ (post-processing — 합성 시점)

prompt event (event_id=100,001) 업데이트:
    response_occurred = TRUE
    response_delay_sec = 4.2
    response_event_id = 100,005
```

### 5-2. SQL 분석 예시 — 사용자별 인지 측정 평균 딜레이

```sql
SELECT
  p.user_id,
  p.age,
  p.gds_total_pre,
  AVG(b.response_delay_sec)   AS avg_delay_sec,
  AVG(b.response_occurred::INT) AS response_rate
FROM profile p
JOIN behavior_log b USING (user_id)
WHERE b.event_type = 'prompt'
  AND b.cognition_test_id IS NOT NULL
GROUP BY p.user_id, p.age, p.gds_total_pre
ORDER BY avg_delay_sec DESC;
```

### 5-3. 핵심 분석 가설 (합성 모델이 박은 패턴)

- 연령 ↑ → response_delay ↑, response_rate ↓
- WHODAS 기능제약 ↑ → response_delay ↑
- GDS·PHQ-9 우울 ↑ → response_rate ↓ (위축 가설)
- 오전 응답 > 오후 응답 > 저녁 응답 (일중 변동)

학생이 위 가설을 데이터에서 발견하면 "패턴 재발견 연습 성공". 가설에 없는 패턴은 데이터에 없으므로 새로 발견될 수 없음 (합성 데이터의 한계 — `docs/05_limitations-and-ethics.md` 참조).

---

## 6. 데이터 볼륨 — v0.2.1 실측 (1000명 풀스케일)

| 테이블 | 행 수 | 컬럼 수 | Parquet ZSTD 실측 |
|---|---:|---:|---:|
| `profile` | 1,000 | 55 | **0.08 MB** |
| `behavior_log` | 3,671,068 | 30 (sparse) | **65.88 MB** |
| `survey_responses` | 168,000 | 10 | **0.17 MB** |
| **합계** | | | **약 66 MB** |

> `joined_wide`는 v0.2.x에서 학생 분석 시 SQL JOIN으로 생성. 별도 parquet 파일로 미배포.

> v0.1.0 호환 데이터(`data/pilot-100-v2/`)도 추가로 약 6.5 MB 포함.

---

## 다음 문서

- 데이터 다운로드·DuckDB 설정: `docs/03_setup-and-download.md`
- 분석 가이드 (LLM/학생용): `docs/04_analysis-guide.md`
- 한계점·윤리: `docs/05_limitations-and-ethics.md`
