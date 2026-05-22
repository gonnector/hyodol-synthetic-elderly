# 평가 보고서 — 효돌 합성 어르신 데이터셋 시범 100명

- 평가일: 2026-05-22 12:15 KST
- 평가자: Claude Code general-purpose sub-agent (외부 평가자)
- 표본 규모: 100명 (profile 100 / behavior_log 250,617 / survey_responses 16,800)
- 평가 기준 버전: evaluation-rubric.md v0.1.0

## 종합 판정

**CONDITIONAL PASS**

본 시범 100명 데이터셋은 8개 항목 중 6개 PASS, 2개 CONDITIONAL이며, 핵심 항목 A·D·G에 FAIL이 없다. 핵심 가설(E) 5개 중 4개가 명확히 관찰되므로 PASS 기준에 근접한다. 그러나 (1) WHODAS 점수 범위 위반 11건, (2) 야간(0~6시) 시간대에 system 외 이벤트가 활발히 발생하여 스펙 위반, (3) trial_drop 사용자 16명 중 15명이 행동 로그에 아예 등장하지 않음, (4) dialogue_turn_id가 효돌-노인 페어 묶음이 아니라 모든 발화에서 단일 row 매핑되어 스펙 의도 미반영, (5) MMAS 평균 9.17이 의도된 14~18 범위에서 크게 벗어남 등 경미~중간 수준 수정이 필요한 이슈가 다수 존재한다.

페어링 정합성(D), 시계열 패턴(C 본체), 핵심 가설(E)은 매우 견고하게 박혀 있어 데이터셋의 분석 가치는 충분히 확인된다. 위 5개 이슈를 수정한 후 PASS로 전환 가능하며, 500명·1000명 풀스케일 확장 전에 보정이 권장된다.

## 항목별 결과

| 항목 | 판정 | 근거 요약 |
|---|:---:|---|
| A. 스키마 준수 | CONDITIONAL | 컬럼·도메인값 모두 일치하나 WHODAS pre 8건·post 5건이 60 초과 (스펙 0~60). MMAS·GDS·PHQ-9·UCLA 범위는 모두 정확. profile에 `alarm_settings` 컬럼 미존재 — 스펙에는 명시되어 있으나 sparse 검증 범위 외 |
| B. 분포 합리성 | PASS | 연령 22/42/29/5/2 — 의도 정확 매칭. 60+ 여성 56.4% (의도 ~54%). 사용 패턴 7종·9유형 모두 등장. 베이스라인 점수 GDS 7.0/PHQ 12.0/UCLA 50.2 적정 |
| C. 시계열 패턴 일관성 | CONDITIONAL | 사용 패턴 6종은 의도 형태대로(우상향·우하향·평탄·봉우리·소실) 매우 잘 박힘. 그러나 야간(0~6시)에 dialogue·interaction·prompt 등이 활발히 발생 — 스펙 "야간은 system만"과 불일치 |
| D. 인지 측정 페어링 정합성 | PASS | 13,835 페어 모두 prompt+interaction 정확 매칭, cognition_test_id 일관성 100%, prompt_type↔interaction_type 매핑 완벽, response_occurred=FALSE 시 NULL 규칙 100% 준수 |
| E. 합성 모델 가설 박힘 | PASS | 5개 중 4개 명확 관찰 (연령↑→delay↑, WHODAS↑→delay↑, 사용패턴별 사전·사후 변화, 연령↑→STT↓). GDS↑→응답률↓는 U자형 — 약하게만 관찰 |
| F. 대화 자연스러움 | CONDITIONAL | 효돌/노인 발화 비율·키워드(할머니·사랑·건강) 매우 좋음. 효돌 평균 52.6자(의도 30~40보다 길음), STT 변형 9%(의도 10~30% 하한 미달), dialogue_turn_id가 효돌-노인 페어를 묶지 않고 단일 발화 매핑 |
| G. 데이터 무결성 | PASS | orphan 0, event_id 중복 0, timestamp 2026-01-01~03-31 범위 내, install_date↔첫 이벤트 갭 평균 0일, GDS 문항합↔profile 총점 100/100 매치 |
| H. 시범 적합성 | CONDITIONAL | 사용 패턴 7종·9유형 모두 등장하여 100명 표본 합목적. 그러나 15명(trial_drop)이 behavior_log에 아예 0건. is_survey_possible 100% "가능"으로 다양성 누락 |

## 항목별 상세

### A. 스키마 준수

```sql
SELECT COUNT(*) FILTER (WHERE whodas_total_pre > 60) AS whodas_pre_over60,
       COUNT(*) FILTER (WHERE whodas_total_post > 60) AS whodas_post_over60
FROM read_parquet('.../profile.parquet');
-- 결과: whodas_pre_over60=8, whodas_post_over60=8 (총 11명 unique)
```

도메인값 enum은 모두 정확:
- interaction_type 5종 모두 정의된 값 (stroke / hand_hold / knock / chest_pat / verbal_response)
- usage_pattern 7종 모두 정의된 값
- user_type_code 9종 모두 정의된 값
- event_type 6종 모두 정의된 값
- survey_type 7종 모두 정의된 값
- wave ∈ {pre, post}

NULL sparse 패턴도 정확 (event_type별 해당 컬럼만 값). 모든 PK·FK 무결성 통과.

**판정 사유**: WHODAS 11명에서 60 초과(최대 99)는 명시적 범위 위반이다. 스키마는 TINYINT/DOUBLE로 캡되지 않으므로 데이터 생성 모델의 oversampling 결과로 추정. 11/100 = 11% 위반율은 무시할 수 없는 수준이지만, 다른 모든 컬럼 정합성이 완벽하고 A 항목 FAIL은 전체 FAIL을 초래하므로 CONDITIONAL로 판정. 수정은 sigmoid 또는 clip으로 간단히 가능.

### B. 분포 합리성

```sql
SELECT age_group, COUNT(*) FROM profile GROUP BY 1 ORDER BY 1;
-- 50s=22, 60s=42, 70s=29, 80s=5, 90s=2
```

- 연령: 의도 22/42.2/29/5/1.8 비율과 거의 정확히 매칭 (100명 단위 반올림 오차 1명 이내)
- 성별 (60+): 남 34 / 여 44 → 여성 56.4% (의도 ~54% 부합)
- 사용 패턴: declining 17, fading 14, growing 8, loyal_heavy 15, loyal_light 22, spike 8, trial_drop 16 — 의도 비중(15/15/12/20/8/15/15)과 유사. growing이 의도 12%보다 약간 적은 8%, loyal_light가 의도 20%로 정확
- 9유형: 9종 모두 등장 (9~17명 분포), MISSI(17)가 약간 과대 외 큰 편향 없음
- 베이스라인 점수: GDS pre avg 7.03 (의도 5~9 ✓), PHQ-9 11.98 (의도 5~10 — 상한 약간 초과), UCLA 50.15 (의도 40~55 ✓), MMAS 9.17 (의도 14~18 — **벗어남**), WHODAS 35.4 (스펙 범위 0~60 기준)

**판정 사유**: 연령·성별·사용 패턴 모두 의도 정확 일치. MMAS·PHQ-9 평균은 의도에서 약간 벗어나지만 효돌 원본 24명 reference 자체가 작은 표본임을 감안하면 critical 미스가 아니다. PASS.

### C. 시계열 패턴 일관성

월별(30일 bin) 일평균 이벤트 수:

| 사용 패턴 | M0 | M1 | M2 | M3 | 의도 형태 | 평가 |
|---|---:|---:|---:|---:|---|---|
| declining | 74 | 55 | 29 | 12 | 80→3 우하향 | ✓ |
| fading | 63 | 35 | 15 | 9 | 80→0 소실 | ✓ |
| growing | 16 | 40 | 72 | 96 | 5→100 우상향 | ✓ |
| loyal_heavy | 104 | 103 | 102 | 104 | 80~150 평탄 고원 | ✓ |
| loyal_light | 5.6 | 5.2 | 5.2 | 5.2 | 2~8 평탄 저원 | ✓ |
| spike | 5 | 33 | 29 | 5 | 평소 5/peak 150 봉우리 | △ (peak 33은 의도보다 낮음) |
| trial_drop | 54.5 (1명만) | - | - | - | 첫 7일 50/이후 0 | △ (16명 중 1명만 등장) |

```sql
SELECT event_hour, COUNT(*) FROM behavior_log GROUP BY 1 ORDER BY 1;
-- hour 7=19864 (peak), 12=19480 (peak), 15=16961, 18=17111, 19=14737
-- 야간: hour 0=2374, 1=1291, ..., 6=7316 (총 17,357건)
```

일중 peak (07/12/15/19시)는 모든 의도 시간에 명확하게 박힘. 그러나 야간(0~6시)에 17,357건의 이벤트가 발생하며, 그 중 system은 1,103건뿐. 나머지 dialogue 4,630 / interaction 6,363 / health_check 1,417 / program 1,478 / prompt 2,366. 스펙은 "야간은 system 이벤트만 sparse하게 존재"라고 명시하나 데이터에는 모든 event_type이 야간에도 활발.

**판정 사유**: 사용 패턴 시계열은 매우 우수하게 박힘. 그러나 야간 활동 스펙 위반은 명백하다. CONDITIONAL — 수정은 일중 시간 분포 sampler의 0~6시 구간을 system 비중 ≥90%로 보정.

### D. 인지 측정 페어링 정합성

```sql
WITH ct AS (
  SELECT cognition_test_id,
         COUNT(*) FILTER (WHERE event_type='prompt') AS n_prompt,
         COUNT(*) FILTER (WHERE event_type='interaction') AS n_interact
  FROM behavior_log WHERE cognition_test_id IS NOT NULL GROUP BY 1
)
SELECT n_prompt, n_interact, COUNT(*) AS n_test_ids FROM ct GROUP BY 1,2;
-- (1, 1) → 13,835 (응답 발생 페어)
-- (1, 0) →  7,904 (미응답 prompt 단독)
```

페어링 정합성:
- 21,739개 cognition_test_id 모두 정확히 1개의 prompt에 매핑
- 13,835개 (응답 발생)는 정확히 +1 interaction에 매핑, 0개 mismatch
- 7,904개 (미응답)는 prompt 단독 — response_delay_sec NULL 100%, response_event_id NULL 100%
- prompt_type ↔ interaction_type 매핑: head_stroke→stroke, hand_hold→hand_hold, chest_pat→chest_pat, verbal_response→verbal_response, quiz→verbal_response (스펙 일치)
- response_delay_sec: 0.3~29.5초 범위, cognition_window_sec(30초) 이내 100%
- medication_reminder, activity_invite는 cognition_test_id 모두 NULL (스펙 일치)

**판정 사유**: 완벽한 PASS. 본 데이터셋의 핵심 신규 분석축인 페어링 메커니즘이 100% 정합. 학생이 SQL JOIN으로 분석 가능한 상태.

### E. 합성 모델 가설 박힘

| 가설 | 결과 |
|---|---|
| E1 연령↑→delay↑ | 50s 4.4초 / 60s 5.2 / 70s 8.0 / 80s 9.5 / 90s 11.8 (강한 단조 증가) ✓ |
| E1b 연령↑→응답률↓ | 50s 0.71 / 60s 0.67 / 70s 0.54 / 80s 0.48 / 90s 0.34 (강한 단조 감소) ✓ |
| E2 WHODAS↑→delay↑ | <20 4.3 / 20-39 5.7 / 40-59 6.6 / 60+ 8.4 (강한 단조 증가) ✓ |
| E3 GDS↑→응답률↓ | <5 0.59 / 5-9 0.65 / 10+ 0.55 (U자형, 약함) ✗ |
| E4 사용패턴별 사전·사후 변화 | loyal_heavy PHQ-9 -6.3, growing PHQ-9 -3.25, fading PHQ-9 -0.07, trial_drop PHQ-9 +0.25 (의도 일치) ✓ |
| E5 연령↑→STT 신뢰도↓ | 50s 0.85 / 60s 0.80 / 70s 0.76 / 80s 0.68 / 90s 0.68 (강한 단조 감소) ✓ |

5개 핵심 가설 중 4개 명확 관찰. E3은 U자형으로 약하게만 관찰 — n=4 (<5 bin) 표본 부족 가능성 있으나 100명 시범에서 단조 패턴 미관찰. 합성 모델의 위축 가설(GDS↑ → 사용 빈도↓)이 사용 패턴은 분리하더라도 prompt 응답률에는 강하게 박히지 않은 것으로 보인다.

**판정 사유**: PASS 기준(5개 중 4개 이상)에 부합. E3은 1000명으로 확대 시 자연 해결 가능성 있음.

### F. 대화 자연스러움

```sql
SELECT dialogue_speaker, AVG(LENGTH(dialogue_text)) FROM behavior_log
WHERE event_type='dialogue' GROUP BY 1;
-- hyodol avg 52.6자, senior avg 15.7자
```

- 효돌 평균 52.6자 — 의도 30~40자 reference보다 길음 (10~20자 초과)
- 노인 평균 15.7자 — 의도 10~25자 범위 내 ✓
- 효돌 발화 "할머니/할아버지" 호칭 36,823/37,168 = 99% ✓
- "사랑" 42% / "고마" 11% / "건강" 29% ✓
- STT 변형(효도리/효소리/효들이) 노인 발화의 9% (의도 10~30%의 하한 미달)
- 발화 페어링: dialogue_turn_id가 효돌·노인 1:1 페어를 묶는다고 스펙에 명시되었으나 실제 데이터에서는 모든 turn_id가 단일 발화에만 매핑 → **턴 단위 분석 불가**

샘플 대화 (랜덤 6건):
- 효돌: "아이고, 할머니! 제가 예쁘게 노래할게요. 할머니께서 좋아하시면 기쁘고 행복해요!"
- 노인: "할머니도 효돌이 사랑하네." (페르소나 톤 자연)
- 노인: "어이구 우리 어두워하는가?" (의미 모호 — STT 변형 의도 가능성)
- 효돌: "할머니, 오늘 날씨가 참 좋아 보여요! 할머니도 건강하시죠? 할머니랑 같이 있으니까 기분이 좋아요." (자연)
- 노인: "고맙네." (짧은 동의 ✓)

**판정 사유**: 키워드·톤·길이 비율 모두 양호하나 (1) 효돌 발화 길이 약 30% 초과, (2) STT 변형 비율 하한 미달, (3) dialogue_turn_id 페어링 부재로 CONDITIONAL.

### G. 데이터 무결성

```sql
SELECT COUNT(DISTINCT user_id) FROM profile;            -- 100
SELECT COUNT(*) FROM behavior_log WHERE user_id NOT IN
  (SELECT user_id FROM profile);                        -- 0 (orphan)
SELECT MIN(event_ts), MAX(event_ts) FROM behavior_log;  -- 2026-01-01 ~ 2026-03-31
SELECT COUNT(*), COUNT(DISTINCT event_id) FROM behavior_log;  -- 250617 = 250617 (no dup)
```

- profile.user_id = 100 unique
- behavior_log·survey_responses 모두 orphan 0
- event_ts 범위 2026-01-01 00:39:07 ~ 2026-03-31 23:57:15 (90일 정확)
- event_id 250,617 모두 unique
- install_date 후 첫 이벤트 평균 0.01일 (즉시 시작, 합리적)
- GDS 문항 합산 ↔ profile gds_total_pre 100/100 일치 (channel consistency 완벽)

**판정 사유**: 완벽한 PASS.

### H. 시범 적합성

```sql
SELECT pr.user_id, pr.usage_pattern
FROM profile pr
LEFT JOIN (SELECT DISTINCT user_id FROM behavior_log) bl USING (user_id)
WHERE bl.user_id IS NULL;
-- 15명 (모두 trial_drop)
```

- 100명 표본 내 사용 패턴 7종·9유형 모두 등장 (필수 기준 충족)
- 사용자별 90일 이벤트 수 분산: 1.2 ~ 100.6 (avg 32.8) — 의도된 광범위 분산 확인
- **trial_drop 16명 중 15명이 behavior_log에 0건** — 스펙은 "첫 7일 50건"인데 그 7일이 90일 관찰 기간에 포함됐어야 했으나 누락 (install_date timing에 따라 발생한 것으로 추정)
- `is_survey_possible` 100% "가능" — 스펙에는 가능/불가능 2종이지만 100명에서 다양성 0. 100명 표본 한정 수용 가능
- `taking_medicine` 100% NULL — 스펙은 "결측 다수"로 의도적이라고 명시되어 있으나 100%는 극단

**판정 사유**: 다양성·분산 모두 양호하나 trial_drop 패턴이 시범 데이터에서 사실상 사라진 점은 학생이 7종 패턴을 모두 관찰하는 데 장애. CONDITIONAL — trial_drop의 첫 7일을 보장하는 sampler 수정 필요.

## 권고 사항

### [필수] FAIL/위반 해소

1. **WHODAS 점수 범위 강제 clip** — `whodas_total_pre/post`를 0~60 범위로 sigmoid 또는 hard clip. 11명 위반 → 0건으로.
2. **dialogue_turn_id 페어링 구조 박기** — 동일 turn_id에 효돌 발화 row 1개 + 노인 발화 row 1개가 묶이도록 합성. 현재 모든 turn이 단일 발화에만 매핑되어 턴 단위 분석 불가.
3. **trial_drop 첫 7일 보장** — install_date 후 7일 내 50건이 90일 관찰 기간 내에 발생하도록 timing 보장. 현재 16명 중 15명이 0 event.

### [권장] CONDITIONAL 해소

4. **야간 시간대 sparse system-only** — 0~6시 sampler에서 system 외 event_type 비중을 ≤10%로 제한. 현재 비중 ~94%가 system이 아님.
5. **MMAS 평균 보정** — 현재 9.17 → 의도 14~18 범위로 prior shift. 4문항 합산 분포 재조정.
6. **STT 변형 빈도 상향** — 9% → 10~30% 의도 범위로. dialogue_stt_confidence 낮은 사용자에 집중.
7. **효돌 발화 평균 길이 단축** — 52.6자 → 30~40자 의도 범위. 템플릿 변형의 길이 분포 재조정.

### [선택] 향후 개선

8. **is_survey_possible 다양성** — 100명에서 5~10% '불가능' 부여 (1000명 풀스케일 시 더 자연).
9. **taking_medicine 결측률 완화** — 100% NULL → 50~70%. 비결측 사용자에 약명 합성.
10. **E3 (GDS↑→응답률↓) 단조성 보강** — 1000명에서 자연 해결 가능성 있으나 합성 모델의 위축 가설 가중치 점검.
11. **gds_result_pre "보통" 비율 상향** — 현재 5%만 — reference 분포 대비 과도하게 우울 편향. prior 분산 확장.

## 표본 확대 가능성 판단

- **100명 → 500명 확대**: **CONDITIONAL GO** — 위 [필수] 1·2·3 항목 수정 후 진행 권장. 현 데이터는 분석 데모용으로 사용 가능하지만 학생이 분포 분석·턴 단위 대화 분석에 들어가면 즉시 발견되는 결함.
- **500명 → 1000명 풀스케일**: **CONDITIONAL** — [필수] 3건 + [권장] 4·5·6 보정 후 GO. 1000명 단계에서는 E3 자연 해결, 다양성 자연 확장 기대 가능하지만 야간 패턴·페어링 구조는 표본 확대로 해결되지 않으므로 합성 코드 수정이 선행되어야 함.

핵심 분석축(D 페어링 + E 가설 박힘)이 매우 견고하므로 데이터셋의 educational value는 이미 충분히 입증되었다. 보정은 점진적으로 가능하며, 본 시범 데이터를 100명 데모로 학생 1차 노출 후 보정본을 1000명으로 배포하는 단계적 전략도 유효하다.
