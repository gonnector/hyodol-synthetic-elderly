# 효돌 합성 어르신 데이터셋 — 평가 Rubric (서브에이전트용 Prompt)

- 버전: v0.1.0
- 작성일: 2026-05-21
- 작성자: DATA (합성 데이터 설계자)
- 평가자: 별도 서브에이전트 (general-purpose) — 1차 (100명), 2차 (100명 v2), 3차 (1000명) 모두 완료

본 문서는 효돌 합성 어르신 데이터셋의 시범 합성 결과(50명 또는 100명)를 **공정한 별도 서브에이전트**가 평가할 때 사용하는 rubric이다. 평가자는 본 문서를 prompt의 일부로 받고, 합성된 데이터(`data/` 폴더)와 데이터셋 스펙(`docs/` 폴더)에 접근해 평가를 수행한다.

---

## 1. 평가자에게 보내는 지시 (Role)

당신은 합성 데이터셋의 **공정한 외부 평가자**다. 이 데이터셋의 합성 설계자(DATA 에이전트)와는 별개로, 데이터 자체와 데이터 명세 문서만을 근거로 평가한다.

평가 결과는 합성 설계자에게 전달되어 다음 결정에 사용된다:
- **PASS** → 표본 확대(100명 또는 1000명) 또는 다음 단계 진행
- **CONDITIONAL PASS** → 경미한 수정 후 진행
- **FAIL** → 합성 모델 보정 → 재생성 루프

따라서 객관성과 명확성이 중요하다. 합성 설계자에게 좋게 보이려는 동기도, 일부러 까다롭게 평가하려는 동기도 없어야 한다.

---

## 2. 평가자의 작업 흐름

1. **컨텍스트 로드**:
   - `docs/01_design-and-method.md` — 설계 의도와 방법론
   - `docs/02_schema.md` — 4 테이블 전체 스펙
   - `docs/05_limitations-and-ethics.md` — 합성 데이터의 본질적 한계 인지

2. **데이터 로드** (DuckDB 활용):
   - `data/profile.parquet`
   - `data/behavior_log.parquet`
   - `data/survey_responses.parquet`

3. **평가 항목 8가지 모두 수행** (Section 3)

4. **평가 보고서 작성**:
   - 위치: `eval/reports/<YYYYMMDD>_eval_pilot-<N>_<evaluator-name>.md`
   - 형식: Section 4의 템플릿

---

## 3. 평가 항목 8가지

각 항목은 PASS / CONDITIONAL / FAIL 중 하나로 판정. 관찰 근거(SQL 쿼리·수치·예시)를 보고서에 명시.

### A. 스키마 준수 (필수 — FAIL 시 전체 FAIL)

- 모든 컬럼이 `docs/02_schema.md`와 일치하는가?
- 데이터 타입이 정확한가? (INT / VARCHAR / TIMESTAMP / DATE / BOOLEAN 등)
- NULL 처리가 sparse column 규칙대로인가? (event_type별로 해당 sparse 컬럼만 값, 나머지 NULL)
- 도메인 값이 정의된 enum 범위 내인가?
  - `interaction_type` ∈ {stroke, hand_hold, knock, chest_pat, verbal_response}
  - `usage_pattern` ∈ {loyal_heavy, loyal_light, growing, declining, spike, fading, trial_drop}
  - `user_type_code` ∈ {VSSI, MISSI, JCSI, VSED, MSED, JCIED, VSMC, MSMC, JCMC}
  - `event_type` ∈ {dialogue, interaction, program, health_check, prompt, system}
  - `survey_type` ∈ {mmas, gds, life_mgmt, whodas, phq9, ucla, usability}
  - `wave` ∈ {pre, post}

### B. 분포 합리성

- **연령 분포** 의도된 비율과 일치하는가? (50명일 때 비례 적용):
  - 50대 22.0% / 60대 42.2% / 70대 29.0% / 80대 5.0% / 90대 1.8%
  - 50명 기준: 50대 11, 60대 21, 70대 14~15, 80대 2~3, 90대 1
- **성별 분포**: 60+ 어르신 중 여자 약 54% (효돌 원본은 여성 비중 더 높지만 본 합성은 Nemotron 분포 따름)
- **사용 패턴 7종 비중** 매칭:
  - loyal_heavy 15% / loyal_light 20% / growing 12% / declining 15% / spike 8% / fading 15% / trial_drop 15%
- **9유형 사용자 분류** 모두 등장 (50명에서 일부 누락 가능, 100명에서는 모두 등장 권장)
- **베이스라인 점수 분포** (사전 wave):
  - GDS 0~15 범위, 평균 5~9 부근 (효돌 원본 24명 reference)
  - PHQ-9 0~27 범위, 평균 5~10 부근
  - UCLA 20~80 범위, 평균 40~55 부근
  - MMAS 0~20 범위, 평균 14~18 부근
  - 비현실적 극단값(GDS 평균 0 또는 평균 14)은 FAIL

### C. 시계열 패턴 일관성

- 사용 패턴별 일별 이벤트 수 시계열이 의도된 형태대로:
  - `loyal_heavy`: 평탄 고원 (80~150)
  - `loyal_light`: 평탄 저원 (2~8)
  - `growing`: 우상향 (5 → 100)
  - `declining`: 우하향 (80 → 3)
  - `spike`: 봉우리 (평소 5, peak 150)
  - `fading`: 소실 (80 → 0)
  - `trial_drop`: 첫 7일만 (50) 이후 0
- 일중 시간대 패턴: 오전·점심·오후·저녁 peak (07/12/15/19시 부근)
- 야간(0~6시): system 이벤트만 sparse하게 존재
- 요일 효과 존재 여부 (주말이 평일과 유사한 수준이거나 약간 다름)

### D. 인지 측정 페어링 정합성 (★ 핵심)

- 모든 `cognition_test_id`가 정확히 두 개 이벤트(prompt + interaction)에 매칭되거나, prompt 단독(미응답)인가?
- `response_occurred=TRUE`인 prompt에 대해:
  - `response_delay_sec` ≥ 0 이고 `cognition_window_sec` 이하
  - `response_event_id`가 실제 behavior_log.event_id에 존재
  - 매칭된 interaction의 cognition_test_id가 prompt와 동일
- `response_occurred=FALSE`인 prompt에 대해:
  - `response_delay_sec` = NULL
  - `response_event_id` = NULL
- prompt_type ↔ 기대 interaction_type 매칭 (head_stroke_request ↔ stroke 등)

### E. 합성 모델 가설 박힘 확인 (★ 핵심)

다음 가설이 데이터에 박혀 있는가? 단순 상관 확인 + 시각화 권장.

- **연령↑ → 응답 딜레이↑**: 80대가 60대보다 평균 응답 딜레이가 길어야 함
- **WHODAS↑ → 응답 딜레이↑**: 기능제약 큰 사용자가 평균 딜레이 김
- **GDS↑ → 응답률↓**: 우울 점수 높은 사용자가 응답률 낮음
- **사용 패턴 → 사전·사후 변화 차이**:
  - `loyal_heavy`·`growing`: GDS·PHQ-9·UCLA 개선 (점수 감소)
  - `declining`·`fading`: 변화 미미
  - `trial_drop`: 거의 변화 없음
- **연령↑ → STT 신뢰도↓**: 80대 평균 STT confidence가 60대보다 낮음

각 가설이 데이터에서 **명확히 관찰되는가? 노이즈에 묻혀 안 보이는가? 반대 방향으로 박혀 있는가?**

### F. 대화 자연스러움

- 효돌 발화와 노인 발화의 평균 길이:
  - 효돌 평균 약 30~40자, 노인 평균 약 10~25자 (원본 reference)
- 발화 내용:
  - 효돌 발화에 "할머니/할아버지" 호칭 자주 등장
  - 노인 발화에 짧은 동의·과거 회상·가족 언급 등장
  - 효돌 발화에 "사랑해", "고마워", "예뻐", "건강" 등 키워드 등장
- STT 오류 패턴:
  - "효돌" → "효도리/효소리/효들이" 변형이 일부 turn에 등장 (10~30%)
  - `dialogue_stt_confidence` 낮은 사용자에서 더 빈번
- 페르소나·우울 점수에 따른 톤 변화 (정성적 — 샘플 10건 읽기)

### G. 데이터 무결성

- `user_id` 1~50 (또는 1~N) 모두 존재
- `behavior_log.user_id`가 모두 `profile.user_id`에 존재 (referential)
- `survey_responses.user_id`가 모두 `profile.user_id`에 존재
- 모든 timestamp가 관찰 기간(2026-01-01 ~ 2026-03-31) 내
- 중복 event_id 없음
- 사용자별 설치일 이후 첫 이벤트가 합리적 (설치 1~2일 적응 기간 후)

### H. 시범 적합성 (50명·100명 등 소규모 표본 한정)

- 50명·100명에서도 의미 있는 분석이 가능한가?
- 누락된 카테고리 (예: 모든 사용 패턴에 최소 1명 / 모든 9유형에 최소 1명):
  - 50명 → 일부 카테고리 0명 가능 (수용)
  - 100명 → 모든 사용 패턴에 최소 1명 (필수), 9유형은 일부 누락 가능
- 사용자별 90일 이벤트 수 분포가 의도된 분산(2~500/일)을 보이는가
- 시범 데이터를 본 학생이 1000명 풀 데이터셋의 모습을 합리적으로 추측 가능한가

---

## 4. 평가 보고서 템플릿

평가자는 다음 템플릿을 채워 `eval/reports/<YYYYMMDD>_eval_pilot-<N>_<evaluator>.md` 에 저장한다.

```markdown
# 평가 보고서 — 효돌 합성 어르신 데이터셋 시범 N명

- 평가일: YYYY-MM-DD HH:MM KST
- 평가자: <에이전트 ID 또는 sub-agent>
- 표본 규모: N명
- 평가 기준 버전: evaluation-rubric.md v0.1.0

## 종합 판정

**PASS** / **CONDITIONAL PASS** / **FAIL**

종합 코멘트 1~3 문단.

## 항목별 결과

| 항목 | 판정 | 근거 요약 |
|---|:---:|---|
| A. 스키마 준수 | PASS/CONDITIONAL/FAIL | ... |
| B. 분포 합리성 | | |
| C. 시계열 패턴 일관성 | | |
| D. 인지 측정 페어링 정합성 | | |
| E. 합성 모델 가설 박힘 | | |
| F. 대화 자연스러움 | | |
| G. 데이터 무결성 | | |
| H. 시범 적합성 | | |

## 항목별 상세 (각 항목별 1~3 문단)

### A. 스키마 준수
- SQL 쿼리·결과 발췌
- 발견 사항
- 판정 근거

(B~H 동일)

## 권고 사항

합성 설계자에게 전달할 수정·개선 권고:
1. [필수] ... (FAIL 항목 해소용)
2. [권장] ... (CONDITIONAL 해소용)
3. [선택] ... (향후 개선)

## 표본 확대 가능성 판단

- 50명 → 100명 확대: GO / NO-GO / CONDITIONAL
- 100명 → 1000명 풀스케일: GO / NO-GO / CONDITIONAL (50명 단계에서는 보류)
```

---

## 5. PASS / CONDITIONAL PASS / FAIL 기준

### PASS
- 8개 항목 중 7개 이상 PASS
- A·D·G 중 FAIL 0개
- 핵심 가설(E) 5개 중 4개 이상 명확히 관찰

### CONDITIONAL PASS
- 8개 항목 중 5~6개 PASS
- A·D·G 중 FAIL 0개
- 경미한 수정으로 PASS 도달 가능

### FAIL
- A·D·G 중 어느 하나라도 FAIL
- 또는 8개 항목 중 4개 이하 PASS
- 또는 핵심 가설(E) 5개 중 3개 이상이 데이터에서 관찰 안 됨

---

## 6. 평가자가 사용할 SQL 패턴 모음

### A. 스키마 확인
```sql
DESCRIBE SELECT * FROM read_parquet('data/profile.parquet') LIMIT 1;
DESCRIBE SELECT * FROM read_parquet('data/behavior_log.parquet') LIMIT 1;
```

### B. 분포 확인
```sql
SELECT age_group, COUNT(*) FROM read_parquet('data/profile.parquet') GROUP BY 1;
SELECT usage_pattern, COUNT(*) FROM read_parquet('data/profile.parquet') GROUP BY 1;
SELECT AVG(gds_total_pre), AVG(phq9_total_pre), AVG(ucla_total_pre)
FROM read_parquet('data/profile.parquet');
```

### C. 시계열 확인
```sql
WITH bl AS (SELECT * FROM read_parquet('data/behavior_log.parquet')),
     pr AS (SELECT * FROM read_parquet('data/profile.parquet'))
SELECT pr.usage_pattern, bl.event_date, COUNT(*)
FROM bl JOIN pr USING (user_id)
GROUP BY 1, 2 ORDER BY 1, 2;
```

### D. 인지 측정 페어링 확인
```sql
SELECT prompt_type, response_occurred,
       AVG(response_delay_sec) FILTER (WHERE response_occurred),
       COUNT(*) AS n
FROM read_parquet('data/behavior_log.parquet')
WHERE event_type='prompt' AND cognition_test_id IS NOT NULL
GROUP BY 1, 2;
```

### E. 가설 박힘 확인
```sql
WITH bl AS (SELECT * FROM read_parquet('data/behavior_log.parquet')),
     pr AS (SELECT * FROM read_parquet('data/profile.parquet'))
SELECT pr.age_group,
       AVG(bl.response_delay_sec) FILTER (WHERE bl.response_occurred) AS avg_delay,
       AVG(bl.response_occurred::INT) AS response_rate
FROM bl JOIN pr USING (user_id)
WHERE bl.event_type='prompt' AND bl.cognition_test_id IS NOT NULL
GROUP BY 1 ORDER BY 1;
```

### G. 무결성 확인
```sql
SELECT COUNT(DISTINCT user_id) FROM read_parquet('data/profile.parquet');
SELECT COUNT(*) FROM read_parquet('data/behavior_log.parquet')
WHERE user_id NOT IN (SELECT user_id FROM read_parquet('data/profile.parquet'));
```

---

## 7. 평가 결과의 활용

- **PASS** → 합성 설계자가 다음 표본 규모로 확대 (50 → 100 → 1000)
- **CONDITIONAL** → 평가자의 권고 반영 후 재생성 (소규모 수정)
- **FAIL** → 합성 모델 보정 + 재생성 루프. 평가자는 무엇이 잘못 박혔는지 진단 보고

평가 결과는 합성 설계자와 Dylan(최종 의사결정자)에게 동시에 보고된다.
