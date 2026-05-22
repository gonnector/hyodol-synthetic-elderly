# 04. 분석 가이드 (LLM/학생용)

- 버전: v0.1.0
- 최종 갱신: 2026-05-21
- 작성자: DATA
- 대상: 학생 분석을 보조하는 LLM(Claude Code 등) + 직접 분석하는 학생

본 문서는 효돌 합성 어르신 데이터셋으로 학생들이 수행할 수 있는 **자주 묻는 분석 패턴·SQL 템플릿·시각화 가이드**를 모은다. LLM이 학생 분석을 보조할 때 이 문서를 컨텍스트로 로드하면 답변 품질이 크게 올라간다.

---

## 0. LLM이 분석 보조 시 우선 인지

본 데이터셋은 **합성** 데이터다. 학생이 발견한 패턴은 합성 모델이 박아 둔 패턴의 재발견이며, 실제 효돌 사용자 모집단에 대한 추론에 사용하면 안 된다. 분석 결과 보고 시 다음 면책 문구를 항상 포함하라:

> 본 분석은 ㈜효돌 운영 스키마를 reference로 한 합성 데이터셋에서 도출된 탐색적 패턴이며, 실제 효돌 사용자 모집단에 대한 추론·일반화·인과 해석에 사용할 수 없습니다.

자세한 분석 안티패턴 → `docs/05_limitations-and-ethics.md`

---

## 1. 학생 수준별 시작점

### 1-1. 초급 (SQL 기초 학습)

목표: profile 테이블 한 개로 SELECT·WHERE·GROUP BY 익히기

```sql
-- 60대 여성 어르신 인원
SELECT COUNT(*) FROM profile WHERE age BETWEEN 60 AND 69 AND sex = '여자';

-- 연령대별 평균 GDS 점수 (사전)
SELECT age_group, AVG(gds_total_pre) AS avg_gds
FROM profile
GROUP BY age_group
ORDER BY age_group;

-- 사용 패턴별 분포
SELECT * FROM dist_usage_pattern;
```

### 1-2. 중급 (JOIN·집계)

목표: profile + behavior_log JOIN으로 행동-속성 연결 분석

```sql
-- 사용자별 90일 총 이벤트 수
SELECT
  p.user_id, p.age_group, p.usage_pattern,
  COUNT(*) AS total_events
FROM profile p
JOIN behavior_log b USING (user_id)
GROUP BY p.user_id, p.age_group, p.usage_pattern
ORDER BY total_events DESC
LIMIT 20;

-- 인터랙션 타입별 횟수 by 연령대
SELECT
  p.age_group, b.interaction_type,
  COUNT(*) AS n
FROM profile p
JOIN behavior_log b USING (user_id)
WHERE b.event_type = 'interaction'
GROUP BY p.age_group, b.interaction_type
ORDER BY p.age_group, n DESC;
```

### 1-3. 고급 (시계열·페어링·통계)

목표: 인지 측정·사전·사후 변화·복합 cross-tab

```sql
-- 인지 측정 응답률·딜레이 by 연령대·GDS 범주
SELECT
  p.age_group,
  p.gds_result_pre,
  COUNT(*) AS n_prompts,
  AVG(b.response_occurred::INT) AS response_rate,
  AVG(b.response_delay_sec) FILTER (WHERE b.response_occurred) AS avg_delay
FROM profile p
JOIN behavior_log b USING (user_id)
WHERE b.event_type = 'prompt' AND b.cognition_test_id IS NOT NULL
GROUP BY p.age_group, p.gds_result_pre
ORDER BY p.age_group, p.gds_result_pre;
```

---

## 2. 자주 쓰는 SQL 패턴 모음

### 2-1. 사용자 수준 분석

```sql
-- (a) 사용자별 90일 통계 요약
WITH user_summary AS (
  SELECT
    user_id,
    COUNT(*) AS total_events,
    COUNT(DISTINCT event_date) AS active_days,
    SUM(CASE WHEN event_type='interaction' THEN 1 ELSE 0 END) AS interactions,
    SUM(CASE WHEN event_type='dialogue' THEN 1 ELSE 0 END) AS dialogues,
    SUM(CASE WHEN event_type='prompt' AND cognition_test_id IS NOT NULL THEN 1 ELSE 0 END) AS cognition_tests,
    AVG(CASE WHEN event_type='prompt' AND response_occurred THEN response_delay_sec END) AS avg_delay
  FROM behavior_log
  GROUP BY user_id
)
SELECT p.*, u.total_events, u.active_days, u.interactions,
       u.dialogues, u.cognition_tests, u.avg_delay
FROM profile p
JOIN user_summary u USING (user_id);
```

### 2-2. 시계열 분석

```sql
-- (b) 일별 사용량 시계열 by 사용 패턴
SELECT
  b.event_date, p.usage_pattern,
  COUNT(*) AS n,
  COUNT(DISTINCT b.user_id) AS active_users
FROM behavior_log b
JOIN profile p USING (user_id)
GROUP BY b.event_date, p.usage_pattern
ORDER BY b.event_date, p.usage_pattern;

-- (c) 일중 시간대별 분포
SELECT event_hour, event_type, COUNT(*) AS n
FROM behavior_log
GROUP BY event_hour, event_type
ORDER BY event_hour, event_type;

-- (d) 요일별 패턴
SELECT event_dow, event_type, COUNT(*) AS n
FROM behavior_log
GROUP BY event_dow, event_type
ORDER BY event_dow, event_type;
```

### 2-3. 인지 측정 분석 (핵심 신규)

```sql
-- (e) prompt_type 별 응답률
SELECT
  prompt_type,
  COUNT(*) AS n_prompts,
  AVG(response_occurred::INT) AS response_rate,
  AVG(response_delay_sec) FILTER (WHERE response_occurred) AS avg_delay_sec,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY response_delay_sec) AS median_delay
FROM cognition_tests
GROUP BY prompt_type
ORDER BY response_rate DESC;

-- (f) 응답 딜레이 분포 by WHODAS 범주
SELECT
  CASE
    WHEN p.whodas_total_pre < 10 THEN '0-9: 거의 없음'
    WHEN p.whodas_total_pre < 20 THEN '10-19: 경미'
    WHEN p.whodas_total_pre < 30 THEN '20-29: 보통'
    ELSE '30+: 심함'
  END AS whodas_band,
  COUNT(*) AS n,
  AVG(b.response_delay_sec) AS avg_delay,
  AVG(b.response_occurred::INT) AS response_rate
FROM profile p
JOIN behavior_log b USING (user_id)
WHERE b.event_type='prompt' AND b.cognition_test_id IS NOT NULL
GROUP BY whodas_band
ORDER BY whodas_band;
```

### 2-4. 설문 분석

```sql
-- (g) 사전·사후 우울 변화 by 사용 패턴
SELECT
  p.usage_pattern,
  p.usage_pattern_label,
  AVG(p.gds_total_pre) AS gds_pre_avg,
  AVG(p.gds_total_post) AS gds_post_avg,
  AVG(p.gds_total_post - p.gds_total_pre) AS gds_delta_avg,
  COUNT(*) AS n_users
FROM profile p
GROUP BY p.usage_pattern, p.usage_pattern_label
ORDER BY gds_delta_avg;

-- (h) 사용성 평가 영역별 점수 (24문항을 8영역으로 집계)
SELECT
  CASE
    WHEN question_no BETWEEN 1 AND 6 THEN '신뢰·유능성'
    WHEN question_no BETWEEN 7 AND 9 THEN '부정감정(역)'
    WHEN question_no BETWEEN 10 AND 12 THEN '용이성'
    WHEN question_no BETWEEN 13 AND 14 THEN '대화성능'
    WHEN question_no BETWEEN 15 AND 16 THEN '대화 빈도양'
    WHEN question_no BETWEEN 17 AND 18 THEN '대화 만족'
    WHEN question_no BETWEEN 19 AND 20 THEN '사용 빈도양'
    WHEN question_no BETWEEN 21 AND 24 THEN '전반·지속의향'
  END AS domain,
  AVG(answer_score) AS avg_score
FROM survey_responses
WHERE survey_type = 'usability' AND wave = 'post'
GROUP BY domain
ORDER BY avg_score DESC;
```

### 2-5. 대화 분석

```sql
-- (i) 사용자별 대화 turn 수와 평균 발화 길이
SELECT
  user_id,
  COUNT(*) AS n_turns,
  AVG(LENGTH(dialogue_text)) AS avg_text_length,
  AVG(dialogue_stt_confidence) FILTER (WHERE dialogue_speaker='senior') AS avg_stt_conf
FROM behavior_log
WHERE event_type = 'dialogue'
GROUP BY user_id;

-- (j) STT 인식 오류 단어 빈도 (효돌→효도리·효소리 등)
SELECT
  dialogue_text,
  COUNT(*) AS n
FROM behavior_log
WHERE event_type='dialogue'
  AND dialogue_speaker='senior'
  AND (dialogue_text LIKE '%효도리%' OR dialogue_text LIKE '%효소리%' OR dialogue_text LIKE '%효들이%')
GROUP BY dialogue_text
ORDER BY n DESC
LIMIT 20;
```

---

## 3. 시각화 가이드

### 3-1. 권장 시각화 도구

| 도구 | 적합 |
|---|---|
| **plotly** (Python) | 인터랙티브 차트, 단일 HTML 저장 가능. 학생 보고서 적합 |
| **matplotlib + seaborn** | 정적 그래프, 학술 보고서·논문 적합 |
| **DuckDB built-in** | 빠른 텍스트 출력 (`SELECT histogram(age)`) |
| **Observable** | 웹 대시보드 (고급) |

### 3-2. 추천 차트 매핑

| 분석 질문 | 추천 차트 |
|---|---|
| 분포 확인 (단일 변수) | histogram / boxplot |
| 두 변수 관계 | scatter plot (회귀선 추가 가능) |
| 시계열 | line chart / area chart |
| Cross-tab | heatmap / stacked bar |
| 사전·사후 변화 | slope chart / paired boxplot |
| 그룹 비교 | violin plot / boxplot by group |

### 3-3. plotly 단일 HTML 보고서 패턴

```python
import duckdb, plotly.express as px
con = duckdb.connect('hyodol.duckdb', read_only=True)

df = con.execute("""
SELECT p.age_group, AVG(b.response_delay_sec) AS avg_delay
FROM profile p
JOIN behavior_log b USING (user_id)
WHERE b.event_type='prompt' AND b.cognition_test_id IS NOT NULL
GROUP BY p.age_group ORDER BY p.age_group
""").fetchdf()

fig = px.bar(df, x='age_group', y='avg_delay',
             title='연령대별 평균 인지 측정 응답 딜레이 (합성 데이터)')
fig.write_html('cognition_delay_by_age.html')
```

---

## 4. 분석 안티패턴 (LLM이 학생에게 안내해야 할 것)

| ❌ 안티패턴 | ✅ 올바른 접근 |
|---|---|
| "효돌이 우울을 개선한다고 입증됨" | "합성 데이터에서 사용 강도와 GDS 변화량 사이에 음의 상관이 관찰됨 (탐색적)" |
| t-test/ANOVA로 효과성 결론 | 통계 검정은 합성 노이즈 검출 수준. 효과 크기·시각화 중심 |
| user_id 개별 사례를 보고서에 노출 | 집계·군집·분포 단위 보고 |
| 외부 효돌 사용자 추론 | "본 데이터셋 내부 패턴 탐색에 한정" 명시 |
| 분석 결과 SNS·공개 GitHub 업로드 | 분석 코드만 공개, 데이터는 .gitignore |
| 사후 우울 점수 감소 = 효돌 효과 | 사용 패턴 group의 self-selection (사용 많이 하는 사람이 원래 개선 잘 됨) — 인과 추론 불가 |

---

## 5. 학생 시나리오별 추천 분석 6가지

본 데이터셋에서 가능한 대표 연구 시나리오. 학생 팀당 1개씩 선택해도 좋다.

### 시나리오 A. 고독감-우울의 이중 구조와 사회적 관계의 완충 (8주차 주제 1 확장)

**RQ**: UCLA 고독감과 GDS·PHQ-9 우울이 어떻게 얽혀 있으며, "사회적 관계 맺기" 점수가 이 얽힘을 완화하는가?

**데이터**: profile (사전 점수), survey_responses (life_mgmt q8: 사회적 관계 맺기)

**방법**: Spearman 상관 + 군집 비교 + 산점도 색상 코딩

**효돌 24명 한계 극복**: 1000명·사용 패턴 7종으로 다양한 하위군 비교 가능

### 시나리오 B. 일상 루틴과 정신건강 (8주차 주제 2 확장)

**RQ**: 복약 순응도·생활관리 점수가 우울·기능제약과 어떻게 연관되는가? 효돌 사용 강도가 매개 변수인가?

**데이터**: profile + behavior_log(program: 체조·복약 알람 응답률)

**방법**: 매개 분석 / k-means 클러스터링 / 패스 분석 탐색

### 시나리오 C. 대화 담론 분석 (8주차 주제 3 확장)

**RQ**: 노인이 효돌에게 가장 많이 꺼내는 주제는? STT 인식 오류율은 사용자 특성과 어떻게 관계되는가?

**데이터**: behavior_log (dialogue 이벤트)

**방법**: 형태소 분석 → 빈도·토픽 모델링. STT confidence 분포 분석

**효돌 24명 한계 극복**: 사용자-대화 연결 가능 (원본은 user_id 없었음)

### 시나리오 D. AI 수용성 (8주차 주제 4 확장)

**RQ**: 사용성 평가 8개 하위영역과 정신건강·기능제약은 어떻게 연관되는가?

**데이터**: survey_responses (usability), profile (베이스라인)

**방법**: 하위영역 점수 산출 → 상관 행렬 → 요인 구조 탐색

### 시나리오 E. ★ 인지 능력 측정 — 본 데이터셋만 가능한 신규 분석

**RQ**: 인지 측정 응답률·딜레이가 연령·우울·기능제약과 어떻게 관계되는가? 일중·요일별 변동이 있는가?

**데이터**: behavior_log (cognition_tests), profile (베이스라인)

**방법**: prompt-response 페어 분석 + 시계열 + 다변량 회귀 탐색

**왜 본 데이터셋만 가능?**: 효돌 원본은 prompt-response 페어링 자체가 없음

### 시나리오 F. ★ 사용 패턴 7종 분석 — 본 데이터셋만 가능

**RQ**: 7종 사용 패턴은 어떤 사용자 속성과 연관되는가? 어떤 패턴이 효돌 효과(사전→사후 우울 개선)와 가장 강하게 연관되는가?

**데이터**: profile, behavior_log, survey_responses 모두

**방법**: 군집 검증 + 패턴별 cross-tab + 효과 크기 비교

**왜 본 데이터셋만 가능?**: 효돌 원본은 단일 시점·24명·패턴 분류 없음

---

## 6. LLM이 학생 보조 시 추천 응답 템플릿

학생: "60대와 80대 사이 우울 점수 차이 보여줘"

LLM 권장 응답:
> 합성 데이터셋의 profile 테이블로 분석하겠습니다. **단, 결과는 합성 모델에 박힌 패턴의 재발견이며 실제 모집단 추론은 불가**합니다.
>
> ```sql
> SELECT age_group, AVG(gds_total_pre) AS gds_avg, COUNT(*) AS n
> FROM profile WHERE age_group IN ('60s', '80s')
> GROUP BY age_group;
> ```
>
> 결과: [표]
>
> 패턴: 80s가 60s보다 GDS 평균 X.X점 높음. 이는 합성 모델의 우울 prior가 연령에 conditional하기 때문 (`docs/01_design-and-method.md` Section 4-2 참조). 실제 효돌 사용자 분포에서도 유사할 수 있으나 본 데이터로 입증할 수는 없음.

---

## 다음 문서

- 한계점·윤리: `docs/05_limitations-and-ethics.md`
- 스키마 상세: `docs/02_schema.md`
- 학생 Claude Code 워크플로우: `docs/06_student-workflow-with-claude-code.md`
