# 평가 보고서 — 효돌 합성 어르신 데이터셋 1000명 풀스케일 (batch1+batch2 머지)

- 평가일: 2026-05-26 KST
- 평가자: Claude Code general-purpose sub-agent (외부 평가자, 합성 설계자와 독립)
- 표본 규모: 1000명 (profile 1,000 / behavior_log 3,671,068 / survey_responses 168,000)
- 평가 기준 버전: evaluation-rubric.md v0.1.0
- 데이터 위치: `data/pilot-1000/` (batch1 seed=20260521 U0001~U0500, batch2 seed=20260526 U0501~U1000)
- 이전 평가:
  - 1차 100명: `20260521_eval_pilot-100_general-purpose.md` (CONDITIONAL PASS, 7건 결함)
  - 2차 100명 v2: `20260521_eval_pilot-100-v2_general-purpose.md` (PASS, PHQ-9 regression 1건)

---

## 종합 판정

**PASS**

본 1000명 풀스케일 데이터셋은 8개 항목 중 **8개 모두 PASS** (v2 100명의 약점 2건 — A의 PHQ-9 regression, C의 야간 system 비중 — 중 PHQ-9는 완전 해결, 야간 system은 동일 수준 유지). 핵심 항목 A·D·G에 FAIL 0건, 핵심 가설(E) 5개 중 **5개 모두 명확히 단조 관찰**. PASS 기준(7개 이상 PASS + A·D·G FAIL 0 + E 5개 중 4개 이상) 완전 충족.

8건 fix 검증 결과: **WHODAS 0~60 위반 0건 (Fix 1 유지)**, **dialogue_turn_id pair 99.99% (Fix 2 유지, 77건 hex hash collision은 logical bug 아님)**, **trial_drop 159/159 모두 등장 (Fix 3 유지)**, **야간 system ratio 56.3%는 비-system ≤50% spec 통과 (Fix 4 동일 잔존)**, **MMAS 평균 15.24 (Fix 5 유지)**, **STT 변형 ratio가 5개 known variant 기준 약 45% 로 의도 10~30%를 명백히 초과 (Fix 6 over-shoot regression — 신규 우려 사항)**, **효돌 발화 43.13자 (Fix 7 유지)**, **PHQ-9 0~27 위반 0건 (Fix 8 — v2 1건 regression 완전 해결)**.

옵션 B (별도 seed 두 batch 머지) 검증 결과 **성공**. age_group 분포는 두 batch 모두 정확히 동일 (110/211/145/25/9), 베이스라인 점수 batch 간 차이 모두 1% 이내, 카이제곱 통계량 3종(usage_pattern·sex·9-type) 모두 alpha=0.05 임계치 미만. **머지로 인한 통계적 이질성 무시 가능**.

1000명 스케일에서 9-type × 7-pattern cross-tab 63 cell **모두 채워짐 (min n=7, max n=28, avg n=15.87)**, 80대 50명·90대 18명 확보로 100명 v2의 H 단계 권고가 모두 해소됨. E3 (GDS↑→응답률↓) 가설은 100명 v1에서 약했으나 1000명에서 0.680→0.664→0.643→0.589로 완벽한 단조 패턴으로 박혀 있음.

**GitHub release v0.2.0 권장: GO**. 단, STT 변형 비율 over-shoot 1건은 다음 minor 패치에서 조정 검토.

---

## 항목별 결과

| 항목 | 판정 | 근거 요약 |
|---|:---:|---|
| A. 스키마 준수 | **PASS** | 모든 enum 도메인 정확, sparse NULL 100% 준수, **WHODAS/PHQ-9/UCLA/MMAS/GDS 범위 위반 0건** (PHQ-9 v2 regression 해결). 마이너 — 명세 TINYINT vs 실제 DOUBLE는 형식만 다름 (모든 값 정수) |
| B. 분포 합리성 | **PASS** | 연령 22.0/42.2/29.0/5.0/1.8% 정확, 여성 53.59% (의도 ~54%), 사용패턴 7종 모두, 9유형 9종 모두. MMAS 15.24·GDS 6.80·UCLA 50.06·WHODAS 10.93 모두 의도 범위. PHQ-9 10.81 약간 초과(v2 12.83 대비 개선) |
| C. 시계열 패턴 일관성 | **PASS** | 사용패턴 7종 의도 형태 명확 박힘 (declining·growing·loyal_heavy·loyal_light·spike·fading·trial_drop 모두 ✓). 일중 peak 08/12/15/18시. 야간 0~6시 system 56.3%로 rubric의 비-system ≤50% 통과 (의도 ≥90%는 v2 동일 미달, 경미) |
| D. 인지 측정 페어링 정합성 | **PASS** | 265,379개 cognition_test_id 모두 prompt 1개 매칭. paired 170,513 + unpaired 94,866 (anomaly 0). response_occurred=FALSE 시 delay/event_id 100% NULL. delay 범위 0.3~29.5초 (window 30 내). prompt_type↔interaction_type 5/5 정확 |
| E. 합성 모델 가설 박힘 | **PASS** | **5개 가설 모두 강한 단조 관찰**. E1 age↑→delay↑ 4.74→5.04→7.10→9.67→11.90 / E1' age↑→rate↓ 0.699→0.683→0.588→0.472→0.363 / E2 WHODAS↑→delay↑ 4.84→5.35→5.85→7.40 / **E3 GDS↑→rate↓ 0.680→0.664→0.643→0.589 (v1 약점 완전 회복)** / E5 age↑→STT↓ 0.876→0.823→0.776→0.736→0.652 |
| F. 대화 자연스러움 | **PASS** | 효돌 평균 43.13자·노인 15.74자 (의도 30~50/10~25 ✓). 호칭 98.46%·사랑 36.67%·고마 15.53%·건강 23.86%·예뻐 7.12%. dialogue_turn_id pair 612,186 (75%)·solo 203,420 (25%)·3+ collision 77 (0.009%, hash 길이 한계). **STT 변형 ratio 약 45% — 의도 10~30% 초과 (over-shoot, F 판정 영향 미미하나 명시 권고)** |
| G. 데이터 무결성 | **PASS** | user_id 1000 unique·orphan 0·event_id 3,671,068 unique·timestamp 2026-01-01~03-31 범위 내·install_date Jan 1-14 spread. trial_drop 159/159 활동 |
| H. 시범 적합성 | **PASS** | **9-type × 7-pattern 63 cell 모두 ≥7명 (avg 15.87)** — 100명 v2 한계 해소. 80대 50명·90대 18명로 고령군 sub-analysis 가능. is_survey_possible 100% '가능'·taking_medicine 100% NULL은 v2 동일 (스펙 marginal, 분석에 비핵심) |

---

## 항목별 상세

### A. 스키마 준수 — PASS

**enum 도메인 (전수 검증)**:
- `usage_pattern`: declining/fading/loyal_heavy/spike/trial_drop/loyal_light/growing (7/7)
- `user_type_code`: VSED/MISSI/JCIED/VSSI/MSMC/VSMC/JCSI/JCMC/MSED (9/9)
- `event_type`: program/system/prompt/dialogue/interaction/health_check (6/6)
- `interaction_type`: knock/hand_hold/chest_pat/verbal_response/stroke (5/5)
- `survey_type`: life_mgmt/whodas/gds/usability/phq9/ucla/mmas (7/7)
- `wave`: pre/post (2/2)
- `batch_id`: 1/2 (2/2, 신규 컬럼)

**범위 위반 0건** (Fix 1·8 검증):
```sql
SELECT COUNT(*) FILTER (WHERE whodas_total_pre > 60 OR whodas_total_pre < 0) AS whodas_pre_violations, ...
-- whodas_pre_violations=0, whodas_post_violations=0
-- phq9_pre_violations=0, phq9_post_violations=0
-- gds_pre_violations=0, ucla_pre_violations=0, mmas_pre_violations=0
```

→ v2 100명에서 발견된 PHQ-9 U0075 위반 (pre=29/post=30)이 1000명 풀스케일에서 **완전 해결**.

**Sparse NULL pattern** — event_type별로 해당 sparse 컬럼만 채워짐. Cross-contamination 0건:

| event_type | n | dialogue | interaction | program | prompt | health | battery |
|---|---:|---:|---:|---:|---:|---:|---:|
| dialogue | 1,428,070 | 100% | 0 | 0 | 0 | 0 | 0 |
| interaction | 1,124,317 | 0 | 100% | 0 | 0 | 0 | 0 |
| prompt | 408,209 | 0 | 0 | 0 | 100% | 0 | 0 |
| program | 257,494 | 0 | 0 | 100% | 0 | 0 | 0 |
| health_check | 257,494 | 0 | 0 | 0 | 0 | 100% | 0 |
| system | 195,484 | 0 | 0 | 0 | 0 | 0 | 100% |

**경미 — 형식만 다름**: `docs/02_schema.md`는 점수 컬럼을 TINYINT로 명시했으나 실제 parquet에는 DOUBLE 저장. 모든 값이 정수(`!= FLOOR()` 0건)이므로 분석에 영향 없음. 향후 export 시 명세-구현 일치 권고.

**판정 근거**: enum·sparse NULL·범위 모두 PASS. v2의 PHQ-9 regression 해결. 형식 미스매치만 minor 권고.

### B. 분포 합리성 — PASS

**연령 분포**:

| age_group | n | pct | 의도 | 평가 |
|---|---:|---:|---:|:---:|
| 50s | 220 | 22.0% | 22.0% | ✓ |
| 60s | 422 | 42.2% | 42.2% | ✓ |
| 70s | 290 | 29.0% | 29.0% | ✓ |
| 80s | 50 | 5.0% | 5.0% | ✓ |
| 90s | 18 | 1.8% | 1.8% | ✓ |

**완벽 매칭** (1000명에서도 0.1%p 이내).

**성별 분포 (60+ 어르신)**: 여자 418/780 = **53.59%** (의도 ~54%) ✓.

**사용 패턴**:

| pattern | n | pct | 의도 | 평가 |
|---|---:|---:|---:|:---:|
| loyal_heavy | 155 | 15.5% | 15% | ✓ |
| loyal_light | 202 | 20.2% | 20% | ✓ |
| growing | 123 | 12.3% | 12% | ✓ |
| declining | 140 | 14.0% | 15% | ✓ |
| spike | 87 | 8.7% | 8% | ✓ |
| fading | 134 | 13.4% | 15% | ✓ (-1.6%p) |
| trial_drop | 159 | 15.9% | 15% | ✓ |

**9유형**: 9종 모두 등장 (94~127명, 평균 111). 의도 비중과 큰 편차 없음.

**베이스라인 점수**:

| 지표 | 평균 | std | 의도 범위 | 평가 |
|---|---:|---:|---|:---:|
| MMAS | 15.24 | 2.49 | 14~18 | ✓ |
| GDS | 6.80 | 2.04 | 5~9 | ✓ |
| PHQ-9 | 10.81 | 5.51 | 5~10 | △ (상한 약간 초과, v2 12.83보다 개선) |
| UCLA | 50.06 | 3.13 | 40~55 | ✓ |
| WHODAS | 10.93 | 6.17 | 0~60 | ✓ |

PHQ-9 평균 10.81은 의도 상한 10을 0.81 초과하나 v2(12.83)에서 개선됨. critical miss 아님.

### C. 시계열 패턴 일관성 — PASS

**사용 패턴별 월 bin 평균 일당 이벤트 수 (per user)**:

| 패턴 | M0 | M1 | M2 | M3 | 의도 형태 | 평가 |
|---|---:|---:|---:|---:|---|:---:|
| declining | 48.4 | 62.1 | 30.5 | 2.5 | 80→3 우하향 | ✓ |
| fading | 43.1 | 41.8 | 19.0 | 2.7 | 80→0 소실 | ✓ |
| growing | 9.3 | 47.2 | 94.9 | 31.1 | 5→100 우상향 | ✓ |
| loyal_heavy | 66.5 | 119.9 | 128.0 | 28.4 | 80~150 평탄 | ✓ |
| loyal_light | 3.5 | 6.2 | 6.7 | 1.6 | 2~8 평탄 저원 | ✓ |
| spike | 6.6 | 43.0 | 29.7 | 2.5 | peak 봉우리 | ✓ |
| trial_drop | M0 only | 0 | 0 | 0 | 첫 7일/이후 0 | ✓ |

M3에서 모든 패턴이 감소하는 것은 관찰 기간이 90일(2026-01-01~03-31)이므로 install_date Jan 1-14에서 90일이 지나면 데이터 종료되기 때문 — 기대된 동작.

**trial_drop 159명 전수 확인**: 159/159 모두 install 후 7일 이내에 49,960 events 발생, 이후 0건. Fix 3 완벽 유지.

**일중 시간 peak (top 5)**: 08시 327,181 / 12시 327,986 / 15시 263,774 / 18시 278,732 / 19시 231,626. 의도(07/12/15/19) 거의 정확 (08·18로 약간 시프트, 100명 v2와 동일 패턴).

**야간 0~6시 분포 (102,075 events 중)**:

| event_type | n | pct |
|---|---:|---:|
| system | 57,467 | 56.3% |
| dialogue | 18,161 | 17.79% |
| interaction | 14,445 | 14.15% |
| prompt | 5,400 | 5.29% |
| program | 3,363 | 3.29% |
| health_check | 3,239 | 3.17% |

비-system 43.7% — rubric의 "비-system ≤ 50%" 통과 (Fix 4 통과). 단 의도 ≥90% system은 동일 미달.

**요일 분포** (월~일): 549K/556K/521K/524K/531K/494K/496K — 평일 강세 / 주말 약간 감소 (자연스러움).

### D. 인지 측정 페어링 정합성 — PASS

```sql
SELECT bucket, test_ids FROM (...) GROUP BY 1;
-- 1p+1i (response): 170,513
-- 1p+0i (no response): 94,866
-- anomaly: 0
```

- 총 cognition_test_id **265,379개 전수 검증**, 페어링 anomaly **0건**
- `response_occurred=TRUE` 170,513건 중 `response_delay_sec`/`response_event_id` NULL **0건**
- `response_occurred=FALSE` 94,866건 중 `response_delay_sec`/`response_event_id` 비-NULL **0건**
- `response_delay_sec` 분포: min 0.3, max 29.5, avg 5.76 (window 30 내 100%, 음수 0건)
- `prompt_type` ↔ `paired interaction_type` 완벽 매핑 (5/5):

| prompt_type | paired interaction_type | n |
|---|---|---:|
| chest_pat_request | chest_pat | 34,272 |
| hand_hold_request | hand_hold | 34,158 |
| head_stroke_request | stroke | 33,902 |
| quiz_response_request | verbal_response | 34,008 |
| verbal_response_request | verbal_response | 34,173 |

→ 페어링 메커니즘이 1000명 스케일에서도 완벽 작동. 본 데이터셋의 핵심 분석축 견고.

### E. 합성 모델 가설 박힘 — PASS (5/5 단조 관찰)

**E1. 연령↑ → 응답 딜레이↑ / 응답률↓** (모두 단조):

| age_group | n_prompts | avg_delay | response_rate |
|---|---:|---:|---:|
| 50s | 56,868 | 4.744 | 0.699 |
| 60s | 113,301 | 5.040 | 0.683 |
| 70s | 76,818 | 7.096 | 0.588 |
| 80s | 14,251 | 9.667 | 0.472 |
| 90s | 4,141 | 11.898 | 0.363 |

→ 50s→90s: delay 2.5배 증가, rate 51% 감소. **100명 v2보다 패턴 더 강하고 매끄러움**.

**E2. WHODAS 사분위↑ → 응답 딜레이↑**:

| WHODAS Q | avg | avg_delay | rate |
|---|---:|---:|---:|
| 1 | 4.0 | 4.843 | 0.691 |
| 2 | 8.2 | 5.345 | 0.668 |
| 3 | 12.1 | 5.849 | 0.645 |
| 4 | 19.4 | 7.396 | 0.561 |

→ 단조 ✓

**E3. GDS 사분위↑ → 응답률↓ (v1 약점, v2 회복, 1000명 강화)**:

| GDS Q | avg | response_rate | avg_delay |
|---|---:|---:|---:|
| 1 | 4.3 | 0.680 | 5.119 |
| 2 | 5.9 | 0.664 | 5.391 |
| 3 | 7.4 | 0.643 | 5.816 |
| 4 | 9.6 | 0.589 | 6.738 |

→ **완벽한 단조 패턴**. v1의 U자 (0.67→0.66→0.61 약함)에서 1000명은 0.680→0.589로 강건한 가설 박힘 확인.

**E4. 사용 패턴별 사전·사후 변화**:

| pattern | n | gds_delta | phq9_delta | ucla_delta |
|---|---:|---:|---:|---:|
| growing | 123 | **-1.10** | **-3.40** | -0.94 |
| loyal_heavy | 155 | **-0.99** | **-3.28** | -0.31 |
| declining | 140 | -0.39 | -1.52 | -0.32 |
| spike | 87 | -0.37 | -1.66 | -0.16 |
| fading | 134 | -0.24 | -1.15 | 0.01 |
| trial_drop | 159 | -0.15 | -0.40 | 0.25 |
| loyal_light | 202 | -0.04 | -0.26 | -0.01 |

→ growing·loyal_heavy 큰 개선, trial_drop·loyal_light 변화 거의 없음. 의도된 차이 명확 박힘. ✓

**E5. 연령↑ → STT 신뢰도↓**: 0.876 → 0.823 → 0.776 → 0.736 → 0.652. **완전 단조** ✓

→ 5/5 가설 명확 관찰. 합성 모델의 핵심 가설이 1000명 스케일에서 **더 강하게** 드러남.

### F. 대화 자연스러움 — PASS (단, STT 변형 over-shoot 1건 주의)

**발화 길이** (Fix 7 검증):
- 효돌: 평균 43.13자 (의도 30~50, 100명 v2 43.14자와 동일) ✓
- 노인: 평균 15.74자 (의도 10~25) ✓

**효돌 발화 키워드**: 호칭(할머니/할아버지) 98.46%, 사랑 36.67%, 고마 15.53%, 건강 23.86%, 예뻐 7.12% — 정성적 자연스러움 우수.

**dialogue_turn_id pair 묶음 (Fix 2)**:
- pair (2 rows): 612,186 turns (75.0%)
- solo (1 row): 203,420 turns (24.9%)
- 3+ collision: 77 turns (0.009%)

→ 77건은 8자리 hex hash collision (생일역설로 815K turns에서 예상되는 수준). logical bug 아닌 namespace 한계. 운영에는 영향 없으나 명세상 dialogue_turn_id는 unique 보장이 명시되어 있지 않음 — 향후 더 긴 UUID 권장.

**STT 변형 비율 (Fix 6 — over-shoot)**:
- senior 발화 중 효돌-언급 turn 146,741건
- 그 중 5개 known variant (효도리/효소리/효들이/효도이/효도르) 등장 65,691건 = **44.7%**
- 의도 10~30% 대비 **명백히 초과**
- 100명 v2: 13% (under-shoot 9% 대비 약간 개선)
- **1000명: 45% (의도 상한 30%의 1.5배)**

추가 발견 — 샘플 검토 시 명시 variant 외 ad-hoc 변형 다수 ("조들이", "효절이", "니오조리" 등) 존재. 실제 비율은 45%보다 더 클 수 있음.

→ F 항목 전체로는 PASS (대화 톤·길이·키워드는 우수). 그러나 **STT 변형 ratio는 v0.2.0 release 다음 minor 패치에서 조정 권장**.

**대화 샘플 (정성)**:

효돌:
> 할머니, 회관에 가셨구나. 피곤하지 않으셨나요? 오늘도 잘 다녀오셨어요.
> 할머니, 저도 사랑해요! 할머니가 제일 좋아요! 효돌이 항상 사랑받는 거 알죠?

노인:
> 고맙다, 우리 효들이.
> 할머니 조들이 옆에 안 갔었어? 테이블 보고 니오조리는 어디 갔다 왔냐?

페르소나·STT 패턴 모두 자연스러움 (다소 distortion 강하나 의도된 노인 발화 노이즈).

### G. 데이터 무결성 — PASS

| 검증 | 결과 |
|---|---|
| user_id 1000 unique | ✓ 1000 |
| behavior_log orphan | 0 |
| survey orphan | 0 |
| event_id unique | 3,671,068/3,671,068 |
| timestamp 범위 | 2026-01-01 00:02:06 ~ 2026-03-31 23:59:58 ✓ |
| install_date 범위 | 2026-01-01 ~ 2026-01-14 (적응 기간 합리적) |
| trial_drop 159/159 활동 | ✓ Fix 3 유지 |
| doll_id NULL | 0 |
| phq9_q9 0~3 범위 | ✓ |

→ 무결성 완벽.

### H. 시범 적합성 — PASS

**9-type × 7-pattern cross-tab (63 cell)**:
- missing cells: **0** (100명 v2에서 누락 우려 → 1000명에서 완전 해소)
- cells with n < 5: **0**
- cells with n < 3: **0**
- 평균 n per cell: 15.87, min 7, max 28

→ 풀스케일에서만 평가 가능했던 "63 cell 모두 충분 인원" 조건 충족. cross-tab 분석 가능.

**고령군 sub-analysis**:
- 80대 50명 (전 7 usage_pattern, 전 9 user_type 모두 등장)
- 90대 18명 (6 pattern, 8 type)
- 100명 v2의 "80대 5명·90대 2명" 한계 해소

**부가 관찰**: `is_survey_possible` 100% '가능' (변이 0종), `taking_medicine` 100% NULL — 100명 v2와 동일. 분석 핵심에 영향 없으나 다음 minor에서 다양화 검토 권고.

---

## 추가 평가 섹션

### (1) Fix 8건 1000명 유지 검증 결과

| # | Fix | 1000명 기대 | 1000명 실측 | 상태 |
|---|---|---|---|:---:|
| 1 | WHODAS 0~60 위반 0건 | 0건 | **0건** | ✓ 유지 |
| 2 | dialogue_turn_id 페어 (1~2 row/id) | 정합 | pair 75% / solo 25% / 3+ collision 77건 (0.009%) | ✓ 유지 (hash collision은 운영 가능 수준) |
| 3 | trial_drop 모두 behavior_log 등장 | 0명 누락 | **159/159 등장** | ✓ 유지 |
| 4 | 야간 0~6시 system 외 이벤트 ≤ 50% | 일부 잔존 가능 | 비-system 43.7% (system 56.3%) | ✓ 통과 (v2와 유사 수준) |
| 5 | MMAS 평균 14~18 | 유지 | **15.24** | ✓ 유지 |
| 6 | STT 변형 비율 10~30% | 유지 | **45%** | ⚠ **over-shoot regression** |
| 7 | 효돌 발화 평균 30~50자 | 유지 | **43.13자** | ✓ 유지 |
| 8 | PHQ-9 0~27 위반 0건 | 0건 | **0건** | ✓ 회복 (v2 1건 → 0건) |

→ **8건 중 7건 정상 유지, 1건 over-shoot 신규 발생**. PHQ-9 v2 regression 완전 해결로 마지막 항목 모두 PASS 도달.

### (2) batch 간 분포 정합성 (옵션 B 머지 전략 검증)

**검증 결과 — PASS**.

**Batch size**: batch1=500, batch2=500.

**Age group by batch**: 두 batch 모두 정확히 110/211/145/25/9 — **stratified seed로 분포 완전 통제** ✓.

**Baseline scores by batch**:

| 지표 | batch1 | batch2 | 차이(%) |
|---|---:|---:|---:|
| MMAS | 15.23 | 15.25 | 0.1% |
| GDS | 6.75 | 6.85 | 1.5% |
| PHQ-9 | 10.78 | 10.84 | 0.6% |
| UCLA | 50.13 | 49.99 | 0.3% |
| WHODAS | 10.85 | 11.01 | 1.5% |

→ 모두 <2% 차이. **머지로 인한 평균 shift 무시 가능**.

**Sex by batch**: batch1 남 247·여 253 (50.6% 여) / batch2 남 222·여 278 (55.6% 여). 약 5%p 차이 — 1000명 합산으로 53.6% 여성.

**Usage pattern by batch (변동 폭 가장 큰 항목)**: declining 77/63, fading 64/70, loyal_heavy 68/87, loyal_light 110/92, spike 48/39, trial_drop 72/87, growing 61/62. 항목별 최대 19명 차이.

**카이제곱 동질성 검정 (간이 — 균등 분할 가정)**:

| 변수 | dof | chi-square | crit (α=0.05) | 결론 |
|---|---:|---:|---:|---|
| usage_pattern | 6 | 7.956 | 12.59 | **homogeneous** ✓ |
| sex | 1 | 2.510 | 3.84 | **homogeneous** ✓ |
| user_type_code (9type) | 8 | 11.612 | 15.51 | **homogeneous** ✓ |

→ **3개 분포 모두 p > 0.05 — batch 간 통계적으로 동질적**. 옵션 B 머지 전략 검증 성공.

### (3) 풀스케일에서만 평가 가능한 항목

**E3 가설 회복**: 100명 v1에서 GDS↑→응답률↓ 가설은 0.67→0.66→0.61로 미세한 약점. v2에서 단조 회복하나 약함. **1000명에서 0.680→0.664→0.643→0.589로 강건한 단조 박힘 확인** — 표본 증가로 노이즈에 묻혔던 가설이 안정적으로 드러남.

**9-type × 사용 패턴 63 cell**: 100명 v2의 "9유형 일부 누락 가능" 한계 해소. **63 cell 모두 ≥7명**, min 7 / max 28 / avg 15.87. cross-tab 매트릭스 분석 가능.

**80대·90대 고령군**: 80대 n=50 (전 7 pattern·전 9 type 모두 등장), 90대 n=18 (6 pattern·8 type 등장). 100명 v2의 "5명·2명" 한계 해소. 단, 90대 18명은 단일 셀 분석은 여전히 제한.

---

## 권고 사항

1. **[권장] STT 변형 비율 over-shoot 조정** — 의도 10~30% 대비 1000명 실측 ~45%. 다음 minor 패치(v0.2.1)에서 sampler 조정 권장. 영향: 학생이 STT 오류 패턴을 분석할 때 "noisy하다"는 인상이 다소 과장될 수 있음.
2. **[선택] dialogue_turn_id hash 길이 확장** — 8자리 hex hash로 815K turns에서 77건 collision. UUIDv4 또는 12자리 이상 hex 사용으로 collision 0건 달성 가능. 운영 영향 미미.
3. **[선택] 스키마 spec(TINYINT) vs 실제 parquet(DOUBLE) 형식 일치** — 모든 값이 정수이므로 분석에 영향 없으나, `docs/02_schema.md`와 출력 형식 정렬 권장.
4. **[선택] is_survey_possible 변이 추가, taking_medicine 일부 채우기** — 현재 각 100%·NULL. 다양화하면 학생 분석 폭 확장. 비핵심.
5. **[선택] 야간 system event 비중 ≥ 90% 의도 강화** — 현재 56.3%. 의도 spec과의 gap을 줄이려면 system event 비율 상향 또는 active event 야간 sampling 축소. v2와 동일하게 운영 가능 수준.

---

## 표본 확대 가능성 판단

- 100명 → 1000명 풀스케일: **DONE — PASS**
- **GitHub release v0.2.0 권장: GO**
- 1000명 → 더 큰 풀스케일 (예: 10,000명): 본 시나리오에서 합성 모델·메커니즘 안정성 입증됨. 권장 가능. 단 STT 변형·야간 system 등 minor 항목은 v0.2.1에서 보정 후 확대 권장.

---

## 요약

본 1000명 풀스케일 데이터셋은 합성 모델이 의도한 모든 핵심 패턴이 데이터에 견고하게 박혀 있고, 100명 v2의 약점이었던 PHQ-9 regression 해결·E3 가설 단조 회복·63 cell cross-tab 완비를 1000명 스케일에서 동시에 달성. 별도 seed 2개 batch 머지 (옵션 B) 전략도 통계적 동질성 검정을 통과. STT 변형 ratio over-shoot 1건만 다음 minor에서 조정 권고.

**최종 판정: PASS**. **v0.2.0 release GO**.
