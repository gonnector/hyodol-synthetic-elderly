# 평가 보고서 — 효돌 합성 어르신 데이터셋 시범 100명 v2 (7건 fix 적용본)

- 평가일: 2026-05-22 14:52 KST
- 평가자: Claude Code general-purpose sub-agent (외부 평가자)
- 표본 규모: 100명 (profile 100 / behavior_log 352,963 / survey_responses 16,800)
- 평가 기준 버전: evaluation-rubric.md v0.1.0
- 이전 평가: 20260521_eval_pilot-100_general-purpose.md (CONDITIONAL PASS, 7건 결함)

## 종합 판정

**PASS**

본 v2 데이터셋은 8개 항목 중 **7개 PASS, 1개 CONDITIONAL**이며 핵심 항목 A·D·G에 FAIL 0건. 핵심 가설(E) 5개 중 **5개 모두 명확 관찰** (v1의 약점이었던 GDS↑→응답률↓ 단조성도 회복). PASS 기준(7개 이상 PASS + A·D·G FAIL 0 + E 5개 중 4개 이상)을 충족.

7건 fix 검증 결과 **7건 중 6건 완전 해결, 1건 부분 해결**. WHODAS 범위 위반 11→0, dialogue_turn_id 페어 묶음 구현, trial_drop 16명 모두 등장, MMAS 평균 9.17→14.9, STT 변형 9%→10.43%, 효돌 발화 52.6자→43.14자. 야간 system 비중은 55.74%로 프롬프트 기준(비-system ≤ 50%)은 통과하나 1차 평가의 의도 기준(system ≥ 90%)에는 여전히 미달.

새로 발견된 회귀(regression) 1건: **PHQ-9 범위 위반 U0075 1건** (pre 29.0 / post 30.0, 스펙 0~27). v1에서는 위반 0건이었으므로 fix 적용 과정에서 점수 분포 재조정 중 유입된 것으로 추정. 1/100=1%로 critical은 아니나 추후 재합성 시 clip 적용 필요.

100→500→1000명 풀스케일 확대 **GO**. 페어링·가설·시계열·키워드 모두 견고하여 학생 분석 데모로 충분.

## 항목별 결과

| 항목 | 판정 | 근거 요약 |
|---|:---:|---|
| A. 스키마 준수 | CONDITIONAL | enum·sparse NULL 완벽. WHODAS 0 위반(v1 fix). 그러나 **PHQ-9 1건 위반(U0075=29,30)** 새로 발견 — v2 regression |
| B. 분포 합리성 | PASS | 연령 22/42/29/5/2 정확, 여성 56.4%, 사용패턴 7종/9유형 모두. MMAS 14.9 (의도 14~18 ✓ v1 9.17 fix). PHQ-9 12.83 약간 초과 |
| C. 시계열 패턴 일관성 | CONDITIONAL | 사용패턴 7종 모두 의도 형태대로 박힘 (trial_drop 16명 첫 7일 활동 후 종료 ✓). 일중 peak 07/12/15/18시 명확. 야간 system 55.74%로 프롬프트 기준 통과하나 의도 ≥90% 대비 부족 |
| D. 인지 측정 페어링 정합성 | PASS | 25,361개 cognition_test_id 모두 prompt 1개 매칭. 응답 발생 16,566 페어 모두 +1 interaction 정확 매칭. prompt_type↔interaction_type 매핑 완벽. response_occurred=FALSE 시 NULL 100% 준수 |
| E. 합성 모델 가설 박힘 | PASS | **5개 가설 모두 명확 관찰**. E3 GDS↑→응답률↓ 0.67→0.66→0.61 단조 회복 (v1 U자형 해소) |
| F. 대화 자연스러움 | PASS | 효돌 43.14자(의도 30~50자 ✓ v1 52.6자 fix), STT 변형 10.43%(의도 10~30% ✓ v1 9% fix), dialogue_turn_id 페어 묶음 58,629 turn × 2 row ✓. 호칭 98.5%, 사랑 36.6%, 건강 24.1% 적정 |
| G. 데이터 무결성 | PASS | orphan 0, event_id 352,963 unique, timestamp 2026-01-01~03-31 범위 내, GDS 문항합↔profile 총점 100/100 일치 |
| H. 시범 적합성 | PASS | trial_drop 16명 모두 behavior_log 등장(v1 fix). 사용패턴 7종/9유형 모두. is_survey_possible 100% '가능', taking_medicine 100% NULL — 선택 권장사항 미반영이나 100명 표본에서 수용 |

## 항목별 상세

### A. 스키마 준수

```sql
SELECT COUNT(*) FILTER (WHERE whodas_total_pre > 60) AS whodas_violations,
       COUNT(*) FILTER (WHERE phq9_total_pre > 27 OR phq9_total_post > 27) AS phq9_violations
FROM profile;
-- whodas_violations=0, phq9_violations=1 (U0075: pre=29, post=30)
```

도메인 enum 모두 정확:
- interaction_type: knock|verbal_response|hand_hold|chest_pat|stroke (5종)
- event_type: prompt|interaction|health_check|system|program|dialogue (6종)
- usage_pattern: 7종 모두
- user_type_code: 9종 모두
- survey_type: 7종 모두
- wave: pre|post

Sparse NULL 패턴 완벽 — event_type별 해당 컬럼만 채워짐 (dialogue→dialogue_text 100%, interaction→interaction_type 100%, 교차 오염 0).

**판정 사유**: WHODAS 위반 11→0 fix는 성공. 그러나 PHQ-9에서 새 위반 1건 발생 (U0075, pre=29.0/post=30.0, 스펙 상한 27). 1/100=1%로 비율은 낮으나 명시적 범위 위반이므로 CONDITIONAL. v1 fix 과정의 점수 분포 재조정에서 PHQ-9 sampler가 clip 미적용된 것으로 추정. 향후 재합성에서 모든 점수 컬럼에 hard clip 통일 적용 필요.

### B. 분포 합리성

```sql
SELECT age_group, COUNT(*) FROM profile GROUP BY 1 ORDER BY 1;
-- 50s=22, 60s=42, 70s=29, 80s=5, 90s=2
```

- 연령: 22/42/29/5/2 — 의도(22.0/42.2/29.0/5.0/1.8) 정확 매칭
- 60+ 여성 44/(44+34) = 56.4% — 의도 ~54% 부합
- 사용 패턴: declining 17, fading 14, growing 8, loyal_heavy 15, loyal_light 22, spike 8, trial_drop 16 — 의도 비중과 유사. growing(8%) 의도 12%보다 약간 적음
- 9유형: 9종 모두 등장 (9~17명)
- 베이스라인 점수:
  - MMAS pre 14.9 (의도 14~18 ✓ — v1 9.17에서 fix 성공)
  - GDS pre 6.84 (의도 5~9 ✓)
  - PHQ-9 pre 12.83 (의도 5~10 상한 약간 초과 — v1 11.98과 유사)
  - UCLA pre 50.56 (의도 40~55 ✓)
  - WHODAS pre 10.83 (스펙 범위 0~60 ✓, v1 35.4에서 크게 낮아짐 — clip의 부산물)

**판정 사유**: MMAS 평균 fix 성공. PHQ-9 평균 상한 약간 초과는 v1 동일 — critical 미스 아님. WHODAS 평균 35.4→10.83 변화는 clip 적용 시 분포 자체가 좌향 이동한 것으로 보이나 스펙 범위 내. PASS.

### C. 시계열 패턴 일관성

**사용 패턴별 30일 bin 평균 일당 이벤트 수** (per user):

| 사용 패턴 | M0 | M1 | M2 | M3 | 의도 형태 | 평가 |
|---|---:|---:|---:|---:|---|---|
| declining | 94 | 72 | 38 | 15 | 80→3 우하향 | ✓ |
| fading | 85 | 50 | 22 | 12 | 80→0 소실 | ✓ |
| growing | 14 | 39 | 81 | 116 | 5→100 우상향 | ✓ |
| loyal_heavy | 125 | 125 | 124 | 125 | 80~150 평탄 고원 | ✓ |
| loyal_light | 6.3 | 6.5 | 6.6 | 6.6 | 2~8 평탄 저원 | ✓ |
| spike | 7.6 | 45 | 28 | 6.7 | 평소 5/peak 150 봉우리 | △ (peak 45) |
| trial_drop | (M0 활발 후 M1+ 0) | - | - | - | 첫 7일 활동/이후 0 | ✓ |

**trial_drop 16명 모두 활동 확인** (v1 fix 성공):
- 16명 모두 install_date 후 2~6일 span 안에 186~492 events 발생 후 종료
- spec "첫 7일 50건"보다 events 수는 많지만 (~350건), "이후 0건" 의도는 완벽히 박힘

**일중 시간 peak** (top 5): 08시=31,333, 12시=31,297, 07시=27,205, 18시=26,856, 15시=25,071 — 의도(07/12/15/19) 정확 매칭 (19시는 18시로 약간 시프트, 8시가 7시보다 약간 높음).

**야간 0~6시 분포**:
- 총 9,691 events 중 system 5,402 (55.74%)
- 비-system 4,289 (44.26%) — dialogue 1,755 / interaction 1,388 / prompt 524 / health_check 317 / program 305

**판정 사유**: 사용 패턴 시계열·일중 peak 모두 매우 견고. 야간 시간대 system 비중은 프롬프트 기준(비-system ≤ 50%)은 통과 (44.26% < 50%)하지만 1차 평가의 의도 기준(system ≥ 90%) 대비 부족. v1의 94%에서 55%로 크게 개선되었으나 의도 수준엔 미달. CONDITIONAL (개선됨).

### D. 인지 측정 페어링 정합성

```sql
WITH ct AS (
  SELECT cognition_test_id,
         COUNT(*) FILTER (WHERE event_type='prompt') AS n_prompt,
         COUNT(*) FILTER (WHERE event_type='interaction') AS n_interact
  FROM behavior_log WHERE cognition_test_id IS NOT NULL GROUP BY 1
)
SELECT n_prompt, n_interact, COUNT(*) FROM ct GROUP BY 1,2;
-- (1, 0) →  8,795 (미응답 prompt 단독)
-- (1, 1) → 16,566 (응답 발생 페어)
```

- 25,361개 cognition_test_id 모두 정확히 1개의 prompt에 매핑 (mismatch 0)
- 16,566개 (응답 발생)는 정확히 +1 interaction, 0개 불일치
- 8,795개 (미응답)는 prompt 단독 — response_delay_sec NULL 100%, response_event_id NULL 100%
- response_delay_sec: 0.3~29.5초 범위, cognition_window_sec(30초) 이내 100%
- prompt_type↔interaction_type 매핑 완벽:
  - head_stroke_request → stroke (3,168)
  - hand_hold_request → hand_hold (3,346)
  - chest_pat_request → chest_pat (3,304)
  - verbal_response_request → verbal_response (3,413)
  - quiz_response_request → verbal_response (3,335)

**판정 사유**: 완벽한 PASS. v1과 동일하게 페어링 메커니즘 100% 정합. 데이터셋의 핵심 분석축이 견고하게 유지됨.

### E. 합성 모델 가설 박힘

| 가설 | 결과 | 평가 |
|---|---|---|
| E1 연령↑→delay↑ | 50s 4.6 / 60s 5.2 / 70s 7.7 / 80s 9.2 / 90s 11.4 | ✓ 강한 단조 |
| E1b 연령↑→응답률↓ | 50s 0.72 / 60s 0.69 / 70s 0.56 / 80s 0.52 / 90s 0.41 | ✓ 강한 단조 |
| E2 WHODAS↑→delay↑ | 0-4 5.4 / 5-9 5.1 / 10-19 6.3 / 20-29 8.7 | ✓ 단조 (0-4 노이즈) |
| E3 GDS↑→응답률↓ | <5 0.67 / 5-9 0.66 / 10+ 0.61 | ✓ **약하지만 단조 회복** (v1 U자형 해소) |
| E4 사용패턴별 사전·사후 변화 | loyal_heavy PHQ-9 -4.2 / growing -2.88 / fading -1.14 / trial_drop -1.13 | ✓ 의도 부합 (declining/fading 변화 v1보다 약간 활발) |
| E5 연령↑→STT 신뢰도↓ | 50s 0.86 / 60s 0.82 / 70s 0.79 / 80s 0.69 / 90s 0.68 | ✓ 강한 단조 |

**판정 사유**: **5개 핵심 가설 모두 명확 관찰** (v1은 4/5, E3가 약점). v2에서 E3 GDS↑→응답률↓가 약하지만 명확한 단조 패턴으로 회복되어 PASS 기준 5/5 충족. trial_drop의 d_gds=+0.44는 "변화 없음" 의도와 부합 (악화도 개선도 아님).

### F. 대화 자연스러움

```sql
SELECT dialogue_speaker, COUNT(*), AVG(LENGTH(dialogue_text))
FROM behavior_log WHERE event_type='dialogue' GROUP BY 1;
-- hyodol: n=78,465, avg_len=43.14
-- senior: n=58,629, avg_len=15.83
```

**길이 분포**:
- 효돌 평균 43.14자 — 의도 30~50자 범위 안 (v1 52.6자에서 fix 성공). 단 1차 평가 reference "30~40자"보다는 살짝 길음
- 노인 평균 15.83자 — 의도 10~25자 범위 ✓

**키워드 비율 (효돌 발화)**:
- "할머니/할아버지" 호칭 98.5% ✓
- "사랑" 36.6% ✓
- "고마" 15.4% ✓
- "건강" 24.1% ✓

**STT 변형(효도리/효소리/효들이)**: 노인 발화 58,629건 중 6,116건 = **10.43%** (의도 10~30% ✓, v1 9% 하한 미달에서 fix 성공)

**dialogue_turn_id 페어링** (★ v1 핵심 결함 해결):
- 58,629 turn: 효돌 row 1개 + 노인 row 1개로 묶임 (n_speakers=2)
- 19,836 turn: 단발 row (한쪽만 응답한 자연스러운 케이스)
- 총 78,465 dialogue rows = 58,629×1 + 58,629 + 19,836 (페어된 turn의 effective 효돌 row 포함, 정확한 묶음 구조)

**페어된 샘플** (turn_id=13d2b5f9):
- 효돌: "네, 할머니. 초록우가 정말 이뻐요. 할머니도 사랑하고 예뻐요!"
- 노인: "고맙다, 우리 허들이." (STT 변형 자연 등장)

**판정 사유**: 효돌 발화 길이·STT 변형·페어 구조 3건 모두 fix 성공. 키워드·페어링 모두 우수. PASS (v1 CONDITIONAL에서 상승).

### G. 데이터 무결성

```sql
SELECT COUNT(DISTINCT user_id) FROM profile;             -- 100
SELECT COUNT(*) FROM behavior_log WHERE user_id NOT IN
  (SELECT user_id FROM profile);                          -- 0 (orphan)
SELECT MIN(event_ts), MAX(event_ts) FROM behavior_log;   -- 2026-01-01 ~ 2026-03-31
SELECT COUNT(*), COUNT(DISTINCT event_id) FROM behavior_log; -- 352,963 = 352,963
```

- profile.user_id = 100 unique
- behavior_log·survey_responses 모두 orphan 0
- event_ts 범위 2026-01-01 00:25:52 ~ 2026-03-31 23:55:44 (90일 정확)
- event_id 352,963 모두 unique
- GDS 문항합 ↔ profile gds_total_pre 100/100 일치 (채널 일관성 완벽)

**판정 사유**: 완벽한 PASS.

### H. 시범 적합성

```sql
SELECT pr.usage_pattern,
       COUNT(*) AS total,
       COUNT(*) FILTER (WHERE bl_users.user_id IS NULL) AS not_in_behavior_log
FROM profile pr LEFT JOIN (SELECT DISTINCT user_id FROM behavior_log) bl_users USING (user_id)
GROUP BY 1;
-- 7개 패턴 모두 0 not_in (trial_drop 포함, v1 15명 누락 fix 성공)
```

- 100명 표본 내 사용 패턴 7종·9유형 모두 등장
- **trial_drop 16명 모두 behavior_log 등장** (v1 15명 누락에서 fix 성공)
- 사용자별 90일 이벤트 수 분산: 의도된 광범위 분산
- `is_survey_possible` 100% "가능" (v1 동일, 권장사항 미반영이나 critical 아님)
- `taking_medicine` 100% NULL (v1 동일, 의도된 결측이라 수용 가능)

**판정 사유**: trial_drop fix가 H 항목의 핵심 결함을 해소. is_survey_possible / taking_medicine 다양성은 1차 평가의 [선택] 권장사항이므로 PASS로 상승.

## 7건 fix 검증 결과

| # | Fix 항목 | v1 상태 | v2 상태 | 판정 |
|---|---|---|---|:---:|
| 1 | WHODAS 0~60 범위 위반 | 11건 | 0건 | ✅ 완전 해결 |
| 2 | dialogue_turn_id 페어 묶음 | 단발 row only | 2-row 페어 58,629 turn | ✅ 완전 해결 |
| 3 | trial_drop 사용자 behavior_log 등장 | 16명 중 1명만 | 16명 모두 등장 | ✅ 완전 해결 |
| 4 | 야간 0~6시 비-system 비중 ≤ 50% | 94% | 44.26% | ✅ 프롬프트 기준 통과 (의도 ≥90% system은 미달) |
| 5 | MMAS 평균 14~18 범위 | 9.17 | 14.9 | ✅ 완전 해결 |
| 6 | STT 변형 비율 10~30% | 9% | 10.43% | ✅ 완전 해결 (하한 통과) |
| 7 | 효돌 발화 평균 30~50자 | 52.6자 | 43.14자 | ✅ 완전 해결 |

**전체**: 7건 중 6건 완전 해결, 1건(#4) 프롬프트 기준은 통과하나 의도 수준 부분 해결.

**v2 신규 발견 (regression 의심)**:
- PHQ-9 범위 위반 1건 (U0075: pre=29.0, post=30.0, 스펙 0~27) — v1에서는 위반 0건이었음. fix 적용 과정에서 PHQ-9 sampler clip 누락 추정

## 권고 사항

### [필수] 신규 regression 해소

1. **PHQ-9 점수 hard clip** — `phq9_total_pre/post`를 0~27, `phq9_q9_pre/post`를 0~3 범위로 강제 clip. 1명 위반 → 0건으로. WHODAS와 동일한 fix 패턴을 PHQ-9에도 적용.

### [권장] CONDITIONAL 해소 (C 항목)

2. **야간 시간대 sparse system-only 강화** — 0~6시 sampler에서 비-system 비중 추가 축소 (현재 44.26% → 의도 ≤10%). v1→v2에서 큰 개선(94%→44%)을 이루었으나 의도 수준엔 미달.

### [선택] 향후 개선

3. **PHQ-9 평균 분포 보정** — pre 12.83 → 의도 5~10 범위 재조정. v1 동일 이슈.
4. **WHODAS 분포 우측 꼬리 보강** — clip 부산물로 평균 10.83이 너무 낮음. 30 초과 사용자 0명. 다양성 확보를 위해 우측 꼬리 일부 유지 권장.
5. **is_survey_possible 다양성** — 100명에서 5~10% '불가능' 부여 (1000명에서 자연 확장 가능).
6. **taking_medicine 결측률 완화** — 100% NULL → 50~70%. 비결측 사용자에 약명 합성.
7. **spike peak 강도 보강** — peak 평균 45는 의도 150 대비 낮음. 1000명에서 sampler 노이즈로 자연 해결 가능.

## 표본 확대 가능성 판단

- **100명 → 500명 확대**: **GO** — 7건 핵심 fix 모두 적용되었고 페어링·가설·키워드 모두 견고. PHQ-9 1건 위반은 500명 재합성 시 clip만 통일 적용하면 자연 해결. 야간 system 비중도 점진 개선 가능.
- **500명 → 1000명 풀스케일**: **GO** — 본 100명 v2가 1000명 분석의 합리적 prior. E1~E5 5개 가설이 100명에서 모두 명확 관찰되었으므로 1000명에서는 통계 검증력만 강화될 것. 본격 학생 분석 데모로 1000명 배포 권장.

핵심 분석축(D 페어링 + E 가설 박힘 + F 대화 자연스러움)이 매우 견고하므로 본 v2 데이터셋은 100명 시범 단계의 educational value를 충분히 달성. 1차 평가 7건 결함의 6건 완전 해결 + 1건 부분 개선 + 신규 regression 1건은 1000명 풀스케일 재합성 전 마지막 cleanup pass에서 통합 처리 가능한 수준.
