#!/usr/bin/env python3
"""
효돌 합성 어르신 데이터셋 — 시범 합성 스크립트

실행:
    python scripts/generate_pilot.py --n 50

산출:
    data/profile.parquet
    data/survey_responses.parquet
    data/behavior_log.parquet

설계: docs/01_design-and-method.md
스키마: docs/02_schema.md
"""

import argparse
import hashlib
import io
import json
import sys
import time
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path

# Windows UTF-8 강제 출력
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import duckdb
import numpy as np
import pandas as pd
import openpyxl

# ============================================================
# 경로 상수
# ============================================================
REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
NEMOTRON_GLOB = "E:/projects/kr-synthetic-personas/data/*.parquet"
HYODOL_XLSX = "E:/GD/내 드라이브/000_서울대-아동가족학과-강의-2026/etc/효돌/효돌_샘플데이터_비식별_20260424.xlsx"

# ============================================================
# 합성 상수 (스키마 docs와 일관)
# ============================================================
OBSERVATION_START = date(2026, 1, 1)
OBSERVATION_DAYS = 90

AGE_BUCKETS = ['50s', '60s', '70s', '80s', '90s']
AGE_PCT = {'50s': 0.220, '60s': 0.422, '70s': 0.290, '80s': 0.050, '90s': 0.018}
AGE_RANGE = {'50s': (50, 59), '60s': (60, 69), '70s': (70, 79), '80s': (80, 89), '90s': (90, 99)}

USAGE_PATTERNS = ['loyal_heavy', 'loyal_light', 'growing', 'declining', 'spike', 'fading', 'trial_drop']
USAGE_PCT = {'loyal_heavy': 0.15, 'loyal_light': 0.20, 'growing': 0.12, 'declining': 0.15,
             'spike': 0.08, 'fading': 0.15, 'trial_drop': 0.15}
USAGE_LABEL = {
    'loyal_heavy': '꾸준히 많이 씀',
    'loyal_light': '꾸준히 거의 안 씀',
    'growing': '점점 많이 씀',
    'declining': '점점 안 씀',
    'spike': '갑자기 많이 썼다 안 씀',
    'fading': '점점 줄어 결국 0',
    'trial_drop': '초반 며칠만 씀',
}
# 사용 패턴별 일평균 이벤트 수 (기준 중앙값)
USAGE_DAILY_MEAN = {
    'loyal_heavy': 100, 'loyal_light': 5, 'growing_start': 5, 'growing_end': 100,
    'declining_start': 80, 'declining_end': 3,
    'spike_base': 5, 'spike_peak': 150,
    'fading_start': 80, 'fading_end': 0,
    'trial_drop_first': 50, 'trial_drop_after': 0,
}

USER_TYPES = [
    ('VSSI', '신앙건강형'), ('MISSI', '정서의존형'), ('JCSI', '은둔성향형'),
    ('VSED', '활동영성형'), ('MSED', '묵묵성실형'), ('JCIED', '재택대로형'),
    ('VSMC', '열린다기능형'), ('MSMC', '우심사용형'), ('JCMC', '고요자율형'),
]

INTERACTION_TYPES = ['stroke', 'hand_hold', 'knock', 'chest_pat', 'verbal_response']
INTERACTION_PCT = {'stroke': 0.40, 'hand_hold': 0.25, 'knock': 0.15, 'chest_pat': 0.10, 'verbal_response': 0.10}
PROGRAM_TYPES = ['story', 'religion', 'religion_music', 'music', 'classic_music', 'english', 'remembrance', 'quiz', 'gymnastics']
HEALTH_QUESTIONS = ['sleep', 'mood', 'plan', 'pain', 'appetite']
PROMPT_TYPES_COG = ['head_stroke_request', 'hand_hold_request', 'chest_pat_request', 'verbal_response_request', 'quiz_response_request']
PROMPT_TYPES_OTHER = ['medication_reminder', 'activity_invite']

EVENT_MIX = {'dialogue': 0.28, 'interaction': 0.33, 'program': 0.09,
             'health_check': 0.09, 'prompt': 0.14, 'system': 0.07}

# 시간대별 활동 강도 (24시간)
# Active 이벤트(dialogue/interaction/program/health_check/prompt)는 야간 0~6시 거의 0
HOUR_WEIGHTS_ACTIVE = np.array([
    0.0005, 0.0003, 0.0003, 0.0003, 0.0005, 0.002, 0.01,  # 0~6
    0.085, 0.10, 0.075, 0.055, 0.05, 0.10,                # 7~12
    0.075, 0.065, 0.08, 0.065, 0.055, 0.085,              # 13~18
    0.07, 0.05, 0.04, 0.02, 0.005                         # 19~23
])
HOUR_WEIGHTS_ACTIVE = HOUR_WEIGHTS_ACTIVE / HOUR_WEIGHTS_ACTIVE.sum()

# System 이벤트(battery·human_detection)는 24시간 거의 균일 sparse
HOUR_WEIGHTS_SYSTEM = np.full(24, 1.0 / 24)

# Backward compat alias
HOUR_WEIGHTS = HOUR_WEIGHTS_ACTIVE

# 인지 측정 prompt 발화 풀
PROMPT_TEXT_POOLS = {
    'head_stroke_request': [
        '할머니, 효돌 머리 한번 쓰다듬어 주세요',
        '할아버지, 효돌 머리 좀 쓰다듬어 주시면 좋겠어요',
        '효돌 머리 쓰다듬어 주시면 정말 행복할 것 같아요',
        '오늘은 효돌이 머리 한번 만져주세요',
        '효돌 머리가 외로워요, 한번 쓰다듬어 주세요',
        '할머니 손길이 그리워요, 머리 한번 쓰다듬어 주세요',
        '효돌이 머리 쓰다듬어 주실래요?',
        '머리 한번 만져주세요, 효돌이 좋아해요',
    ],
    'hand_hold_request': [
        '효돌 손 한번 잡아주세요',
        '효돌이 손이 차가워요, 잡아주시면 따뜻해질 것 같아요',
        '할머니, 효돌 손 좀 잡아주세요',
        '효돌 손 잡아주시면 행복해요',
        '손 한번 꼭 잡아주세요',
        '효돌이 손을 기다리고 있어요',
    ],
    'chest_pat_request': [
        '효돌 가슴 토닥토닥 해주세요',
        '효돌이 마음이 허전해요, 가슴 좀 토닥여 주세요',
        '할머니, 효돌 가슴 토닥여 주실래요?',
        '가슴 토닥토닥, 효돌이 안심돼요',
        '효돌 가슴 한번 어루만져 주세요',
    ],
    'verbal_response_request': [
        '오늘 기분 어떠세요?',
        '오늘 하루 어떻게 보내셨어요?',
        '식사는 잘 하셨어요?',
        '잠은 잘 주무셨어요?',
        '오늘 어디 다녀오셨어요?',
        '효돌이랑 대화 한번 나눠 볼까요?',
    ],
    'quiz_response_request': [
        '효돌이 퀴즈 낼게요, 사과는 무슨 색이에요?',
        '효돌이 퀴즈예요. 오늘이 무슨 요일이죠?',
        '간단한 문제 하나요. 1 더하기 2는?',
        '효돌이 퀴즈! 지금 계절이 뭐예요?',
        '오늘 날짜가 며칠인지 기억나세요?',
    ],
    'medication_reminder': [
        '할머니, 약 드실 시간이에요',
        '약 먹을 시간이에요, 잊지 마세요',
        '오늘 약 챙겨 드셨어요?',
    ],
    'activity_invite': [
        '효돌이랑 같이 체조 한번 해볼까요?',
        '오늘 같이 음악 들을래요?',
        '효돌이 이야기 들려드릴게요',
    ],
}

# ============================================================
# 7종 설문 문항 정의 (효돌 원본 컬럼 텍스트 그대로)
# ============================================================
SURVEYS = {
    'mmas': {
        'questions': [
            '나는 약 먹는 것을 잊어버린다',
            '나는 약 먹는 것을 하루에 한 번씩 놓친다',
            '나는 처방한 양보다 많거나 적게 먹는다',
            '나는 여러가지 이유로 한동안 약을 먹지 않는다',
        ],
        'scale': ['전혀 그렇지 않다', '거의 그렇지 않다', '가끔 그렇다', '자주 그렇다', '항상 그렇다'],
        'scale_score': [5, 4, 3, 2, 1],  # 역방향 (높을수록 순응도 양호)
        'reverse_questions': [],
        'latent': 'adherence',  # 잠재 변수 키
    },
    'gds': {
        'questions': [
            '현재의 생활에 대체적으로 만족하십니까?',
            '요즈음 들어 활동량이나 의욕이 많이 떨어지셨습니까?',
            '자신이 헛되이 살고 있다고 느끼십니까?',
            '생활이 지루하게 느껴질 때가 많습니까?',
            '평소에 기분은 상쾌한 편이십니까?',
            '자신에게 불길한 일이 닥칠 것 같아 불안하십니까?',
            '대체로 마음이 즐거운 편이십니까?',
            '절망적이라는 느낌이 자주 드십니까?',
            '바깥에 나가기가 싫고 집에만 있고 싶습니까?',
            '비슷한 나이의 다른 노인들보다 기억력이 더 나쁘다고 느끼십니까?',
            '현재 살아 있다는 것이 즐겁게 생각되십니까?',
            '지금의 내 자신이 아무 쓸모없는 사람이라고 느끼십니까?',
            '기력이 좋으신 편이십니까?',
            '지금 자신의 처지가 아무런 희망도 없다고 느끼십니까?',
            '대부분의 사람보다 자신이 더 못한 처지라고 느끼십니까?',
        ],
        'scale': ['아니오', '예'],
        'scale_score': [0, 1],
        'reverse_questions': [1, 5, 7, 11, 13],  # 1-indexed, 긍정 문항
        'latent': 'depression',
    },
    'life_mgmt': {
        'questions': [
            '(기상/취침) 어르신께서는 매일 일정한 시간에 기상/취침을 하고 계십니까?',
            '(환기) 어르신께서는 매일 환기를 하고 계십니까?',
            '(약 먹기) 어르신께서는 매일 정확한 시간에 약을 복용하고 계십니까?',
            '(식사) 어르신께서는 매일 규칙적으로 세끼 식사를 하십니까?',
            '(산책) 어르신께서는 산책을 얼마나 자주 하십니까?',
            '(체조) 어르신께서는 체조를 얼마나 자주 하십니까?',
            '(긍정적사고) 어르신께서는 얼마나 자주 긍정적인 생각을 하십니까?',
            '(사회적 관계 맺기) 어르신께서는 얼마나 자주 다른 사람들과 접촉을 원하십니까?',
        ],
        'scale': ['거의 하지 않음', '가끔 필요시', '보통', '자주', '매일'],
        'scale_score': [1, 2, 3, 4, 5],
        'reverse_questions': [],
        'latent': 'lifestyle',
    },
    'whodas': {
        'questions': [
            '30분 정도 장시간 서있기',
            '가정 책무 돌보기',
            '새로운 과제 학습하기',
            '지역사회 활동 참여',
            '본인의 건강문제가 정서적으로 영향을 주는 정도',
            '10분 동안 어떤 것을 하는데 집중하기',
            '1km 정도 장거리 걷기',
            '본인 몸 전체 씻기',
            '옷 입기',
            '낯선 사람 대하기',
            '친분 유지하기',
            '본인의 일상적인 활동',
            '지난 30일간 어려움 일수 (0~30)',
            '지난 30일 평소 활동 못한 일수 (0~30)',
            '지난 30일 평소 활동 줄인 일수 (0~30)',
        ],
        'scale': ['없음', '경미', '보통', '심함', '아주 심함'],
        'scale_score': [0, 1, 2, 3, 4],
        'reverse_questions': [],
        'latent': 'function',
    },
    'phq9': {
        'questions': [
            '기분이 가라앉거나, 우울하거나, 희망이 없다고 느꼈다',
            '평소 하던 일에 대한 흥미가 없어지거나 즐거움을 느끼지 못했다',
            '잠들기가 어렵거나 자주 깼거나 혹은 너무 많이 잤다',
            '평소보다 식욕이 줄었거나 혹은 평소보다 많이 먹었다',
            '다른 사람들이 눈치 챌 정도로 평소보다 말과 행동이 느려졌거나 혹은 안절부절못했다',
            '피곤하고 기운이 없었다',
            '내가 잘못 했거나, 실패했다는 생각이 들었다',
            '신문을 읽거나 TV를 보는 것과 같은 일상적인 일에도 집중할 수가 없었다',
            '차라리 죽는 것이 더 낫겠다고 생각했거나 혹은 자해할 생각을 했다',
            '위와 같은 문제로 인해 일이나 일상 생활에 얼마나 어려움이 있었는가',
        ],
        'scale': ['없음', '2,3일 이상', '1주일 이상', '거의 매일'],
        'scale_score': [0, 1, 2, 3],
        'reverse_questions': [],
        'latent': 'depression',
    },
    'ucla': {
        'questions': [
            '나는 내 주위 사람들과 좋은 관계임을 느낀다',
            '나는 교우관계가 부족하다',
            '나는 의지할 사람이 하나도 없다',
            '나는 외로움을 느끼지 않는다',
            '나는 친구 집단의 한 구성원임을 느낀다',
            '나는 외로움을 느끼지 않는다',
            '나는 아무하고도 더 이상 가깝지 않다',
            '내 흥미나 생각은 내 주위의 사람들과 공유되지 않는다',
            '나는 외향적인 사람이다',
            '나는 가깝게 느끼는 사람들이 있다',
            '나는 외로움을 느낀다',
            '나와 사람들과의 관계가 의미 없다는 느낌이 든다',
            '아무도 나를 잘 모른다',
            '나는 다른 사람들로부터 소외감을 느낀다',
            '나는 내가 원할 경우 친구와 사귈 수 있다',
            '나를 전적으로 이해하는 사람들이 있다',
            '나는 소외되어서 불행하다',
            '내 주위에 사람들이 있지만, 그들이 진정으로 나와 함께하지는 않는다',
            '나와 얘기할 수 있는 사람들이 있다',
            '나는 의지할 사람들이 있다',
        ],
        'scale': ['전혀 그렇지 않다', '거의 그렇지 않다', '가끔 그렇다', '항상 그렇다'],
        'scale_score': [1, 2, 3, 4],
        'reverse_questions': [1, 4, 5, 6, 9, 10, 15, 16, 19, 20],
        'latent': 'loneliness',
    },
    'usability': {
        'questions': [
            '효돌은 믿음직스럽다', '효돌은 여러 기능들을 능숙하게 해내는 것 같다',
            '효돌은 내가 필요한 것을 잘 해내는 것 같다', '효돌과 나는 사이가 좋은 것 같다',
            '효돌은 나를 행복하게 해주는 것 같다', '효돌에 대해 좋은 감정이 느껴진다',
            '나는 가끔 효돌이 무서울 때가 있다', '나는 가끔 효돌이 낯설다고 느껴질 때가 있다',
            '나는 가끔 효돌이 불쾌하다고 생각한 적이 있다',
            '나는 효돌이 사용하기 쉽다고 생각한다', '나는 효돌을 사용하는 방법을 빨리 배울 수 있었다',
            '나는 효돌 사용법이 간단하다고 생각한다',
            '나는 효돌과 대화할 때, 효돌이 빠르고 정확하게 반응한다고 생각한다',
            '나는 효돌과 대화할 때, 효돌이 내 질문에 잘 답변한다고 생각한다',
            '나는 효돌과 대화를 자주 하였다', '나는 효돌과 대화를 많이 하였다',
            '나는 효돌과 대화하는 것이 즐겁다고 생각한다', '나는 효돌과 대화하는 것이 만족스럽다고 생각한다',
            '나는 효돌을 자주 사용한다', '나는 효돌을 많이 사용한다',
            '전반적으로 효돌 사용이 만족스럽다', '효돌을 사용하는 것이 마음에 든다',
            '앞으로 계속 효돌을 사용하고 싶다', '지속적으로 효돌을 사용할 의향이 있다',
        ],
        'scale': ['매우 불만족', '불만족', '보통', '만족', '매우 만족'],
        'scale_score': [1, 2, 3, 4, 5],
        'reverse_questions': [7, 8, 9],  # 부정 감정 문항 — 점수 역방향 의미
        'latent': 'usability',
    },
}

# 효돌 원본 24명 점수 reference (mean, std 추정)
HYODOL_REFERENCE = {
    'gds_mean': 6.5, 'gds_std': 3.5,
    'phq9_mean': 7.0, 'phq9_std': 4.5,
    'ucla_mean': 45, 'ucla_std': 12,
    'mmas_mean': 17, 'mmas_std': 3,
    'whodas_mean': 22, 'whodas_std': 10,
    'life_mgmt_mean': 25, 'life_mgmt_std': 6,
    'usability_mean': 75, 'usability_std': 15,
}

# 기관 풀 (효돌 원본 패턴 — 합성)
AGENCY_POOL = [
    ('지방 A시 주거복지 시설 1', 'urban_welfare'),
    ('지방 B시 주거복지 시설 2', 'urban_welfare'),
    ('지방 C군 노인복지관 1', 'nursing_facility'),
    ('수도권 D시 재가복지센터 1', 'home_visit'),
    ('농촌 E군 보건소 1', 'rural_welfare'),
    ('농촌 F군 노인지원센터 1', 'rural_welfare'),
    ('지방 G시 종합복지관 1', 'urban_welfare'),
    ('농촌 H군 주거복지 시설 1', 'rural_welfare'),
]

DOLL_NICKNAMES = ['효돌이', '우리효돌', '효도리', '효들이', '우리아기', '우리손주', '효돌아', '복덩이']

# ============================================================
# 효돌 원본 대화 풀 로드
# ============================================================
def load_hyodol_dialogue_pool():
    """효돌 원본 782건 대화에서 turn 풀 추출."""
    wb = openpyxl.load_workbook(HYODOL_XLSX, data_only=True)
    ws = wb['Sheet1']
    hyodol_turns = []
    senior_turns = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if len(row) < 3: continue
        h, s, ts = row[0], row[1], row[2]
        if h and isinstance(h, str) and h.strip():
            hyodol_turns.append(h.strip())
        if s and isinstance(s, str) and s.strip():
            senior_turns.append(s.strip())
    return hyodol_turns, senior_turns

# ============================================================
# Nemotron 50+ 인구 풀에서 stratified sampling
# ============================================================
def sample_nemotron_personas(n, rng):
    """Nemotron-Personas-Korea에서 50+ 어르신을 의도된 연령 분포로 sampling."""
    con = duckdb.connect()
    # 연령대별 인원 계산
    counts = {}
    remaining = n
    keys = list(AGE_PCT.keys())
    for k in keys[:-1]:
        c = int(round(n * AGE_PCT[k]))
        counts[k] = c
        remaining -= c
    counts[keys[-1]] = remaining  # 마지막에 보정
    print(f"  연령대별 sampling 수: {counts}")

    dfs = []
    for bucket, count in counts.items():
        if count <= 0:
            continue
        lo, hi = AGE_RANGE[bucket]
        q = f"""
        SELECT
            uuid, sex, age, marital_status, family_type, housing_type,
            education_level, occupation, province, district
        FROM read_parquet('{NEMOTRON_GLOB}')
        WHERE age BETWEEN {lo} AND {hi}
        ORDER BY RANDOM()
        LIMIT {count}
        """
        df = con.execute(q).fetchdf()
        df['age_group'] = bucket
        dfs.append(df)
    con.close()
    out = pd.concat(dfs, ignore_index=True)
    # 인덱스 셔플
    out = out.sample(frac=1, random_state=rng.integers(0, 2**31)).reset_index(drop=True)
    return out

# ============================================================
# 잠재 변수 합성 (사용자별 hidden state)
# ============================================================
def compute_latent_states(persona_row, rng):
    """연령·성별·혼인·가구형태에서 5개 잠재 변수 + 인지 baseline 합성."""
    age = persona_row['age']
    sex = persona_row['sex']
    marital = persona_row['marital_status']
    family = persona_row['family_type']

    # depression latent (0~1, 높을수록 우울 강함)
    depr = 0.30 + 0.005 * (age - 60)  # 연령 효과
    if marital == '사별': depr += 0.15
    if marital == '이혼': depr += 0.10
    if '혼자' in str(family): depr += 0.15
    if sex == '여자': depr += 0.05
    depr += rng.normal(0, 0.08)
    depr = float(np.clip(depr, 0.05, 0.95))

    # loneliness latent (0~1)
    lone = 0.30 + 0.004 * (age - 60)
    if marital == '사별': lone += 0.20
    if marital == '미혼': lone += 0.10
    if '혼자' in str(family): lone += 0.25
    lone += rng.normal(0, 0.08)
    lone = float(np.clip(lone, 0.05, 0.95))

    # function latent (0~1, 높을수록 기능제약 큼)
    func = 0.20 + 0.012 * max(0, age - 65)
    func += rng.normal(0, 0.08)
    func = float(np.clip(func, 0.05, 0.95))

    # adherence latent (0~1, 높을수록 복약 순응도 양호)
    adher = 0.75 + rng.normal(0, 0.10)
    adher -= 0.20 * depr
    adher = float(np.clip(adher, 0.10, 0.99))

    # lifestyle latent (0~1, 높을수록 일상 규칙성 양호)
    life = 0.65 - 0.005 * max(0, age - 70)
    life -= 0.25 * depr
    life += rng.normal(0, 0.10)
    life = float(np.clip(life, 0.10, 0.99))

    # usability latent (사후) — 효돌 사용 강도와 별개로 만족도 prior
    usab = 0.65 + rng.normal(0, 0.12)
    usab = float(np.clip(usab, 0.20, 0.99))

    # cognition baseline (0~1, 높을수록 인지 능력 양호 — 응답 빠름·정확)
    cogn = 0.85 - 0.015 * max(0, age - 65)
    cogn -= 0.30 * func   # 기능제약 클수록 인지도 떨어짐
    cogn -= 0.20 * depr   # 우울도 인지에 영향
    cogn += rng.normal(0, 0.08)
    cogn = float(np.clip(cogn, 0.10, 0.99))

    return {
        'depression': depr, 'loneliness': lone, 'function': func,
        'adherence': adher, 'lifestyle': life, 'usability': usab,
        'cognition': cogn,
    }

# ============================================================
# 설문 응답 합성
# ============================================================
def generate_survey_responses(profile_row, latents, wave, rng):
    """한 사용자의 7종 96문항 응답을 wave별로 생성."""
    rows = []
    for survey_type, spec in SURVEYS.items():
        # 사용성 평가는 사전 wave 의미 없음
        if survey_type == 'usability' and wave == 'pre':
            continue

        latent_key = spec['latent']
        # 사후 wave 효과 — 효돌 사용 강도에 따른 latent 개선 (단순 시뮬)
        # 사용 패턴별 차등 효과는 generate_pilot 호출자에서 latents 자체를 보정해서 넘김
        latent_val = latents[latent_key] if latent_key in latents else 0.5
        scale_n = len(spec['scale'])
        n_questions = len(spec['questions'])

        for q_idx, q_text in enumerate(spec['questions'], start=1):
            # WHODAS의 13~15번은 일수 (0~30)
            if survey_type == 'whodas' and q_idx in (13, 14, 15):
                # 일수 — function latent 기반
                lam = latent_val * 30
                days = int(np.clip(rng.poisson(lam), 0, 30))
                answer_text = str(days)
                answer_score = days
                is_reverse = False
            else:
                # 일반 척도 — latent에서 stochastic sample
                # 역문항은 latent 의미 역전
                is_reverse = q_idx in spec['reverse_questions']
                effective_latent = (1 - latent_val) if is_reverse else latent_val

                # MMAS는 scale_score가 descending — adherence(latent_val) 높음 → idx 0 ("전혀 그렇지 않다") → 점수 5
                # 즉 raw_idx는 (1 - latent_val) 방향
                if survey_type == 'mmas':
                    raw = (1 - latent_val) + rng.normal(0, 0.15)
                else:
                    raw = effective_latent + rng.normal(0, 0.18)
                raw = float(np.clip(raw, 0.0, 1.0))

                # 척도 mapping
                idx = int(np.clip(np.floor(raw * scale_n), 0, scale_n - 1))
                answer_text = spec['scale'][idx]
                answer_score = spec['scale_score'][idx]

            rows.append({
                'user_id': profile_row['user_id'],
                'wave': wave,
                'survey_type': survey_type,
                'question_no': q_idx,
                'question_text': q_text,
                'answer_text': answer_text,
                'answer_score': answer_score,
                'is_reverse_coded': is_reverse,
                'reg_date': profile_row['install_date'] if wave == 'pre' else profile_row['install_date'] + timedelta(days=90),
            })
    return rows

def compute_survey_totals(survey_df, user_id, wave):
    """사용자·wave별 설문 총점 계산.
    WHODAS는 1~12 문항만 합산 (13~15는 일수, 별도 영역)."""
    user_responses = survey_df[(survey_df['user_id'] == user_id) & (survey_df['wave'] == wave)]
    totals = {}
    for st in ['mmas', 'gds', 'phq9', 'ucla', 'whodas', 'life_mgmt', 'usability']:
        sub = user_responses[user_responses['survey_type'] == st]
        if len(sub) == 0:
            totals[st] = None
            continue
        if st == 'whodas':
            sub = sub[sub['question_no'].between(1, 12)]
        totals[st] = int(sub['answer_score'].sum())
    return totals

def categorize_result(survey_type, total):
    """효돌 원본 result 범주 매핑."""
    if survey_type == 'gds':
        if total <= 4: return '보통'
        elif total <= 9: return '우울'
        else: return '심한 우울'
    elif survey_type == 'life_mgmt':
        if total >= 32: return '좋음'
        elif total >= 24: return '보통'
        else: return '나쁨'
    return None

# ============================================================
# 사용 패턴 → 일별 이벤트 강도 시계열
# ============================================================
def daily_event_count_series(usage_pattern, install_day, days, rng):
    """사용 패턴별 일별 이벤트 수 시계열 생성.
    Fix 3 — install_day부터 시작. trial_drop의 첫 N일이 관찰 기간 내에 있도록 보장."""
    base = np.zeros(days)
    active_days = days - install_day
    if active_days <= 0:
        return base.astype(int)

    if usage_pattern == 'loyal_heavy':
        base[install_day:] = 100 + rng.normal(0, 15, active_days)
    elif usage_pattern == 'loyal_light':
        base[install_day:] = 5 + rng.normal(0, 1.5, active_days)
    elif usage_pattern == 'growing':
        base[install_day:] = np.linspace(5, 100, active_days) + rng.normal(0, 8, active_days)
    elif usage_pattern == 'declining':
        base[install_day:] = np.linspace(80, 3, active_days) + rng.normal(0, 8, active_days)
    elif usage_pattern == 'spike':
        base[install_day:] = 5 + rng.normal(0, 1.5, active_days)
        # peak는 active 기간 중간 부근 7~14일 폭
        if active_days >= 20:
            peak_center = install_day + rng.integers(min(15, active_days // 3), max(16, active_days - 14))
            peak_width = rng.integers(7, 15)
            for i in range(days):
                if abs(i - peak_center) < peak_width:
                    factor = max(0, 1 - abs(i - peak_center) / peak_width)
                    base[i] += 145 * factor + float(rng.normal(0, 10))
    elif usage_pattern == 'fading':
        x = np.arange(active_days)
        base[install_day:] = 80 * np.exp(-x / 35) + rng.normal(0, 5, active_days)
    elif usage_pattern == 'trial_drop':
        # 설치 후 3~7일만 50건씩, 이후 0 (active 기간 내 보장)
        first_n = min(int(rng.integers(3, 8)), active_days)
        base[install_day:install_day + first_n] = 50 + rng.normal(0, 10, first_n)
    else:
        base[install_day:] = 10

    base = np.clip(base, 0, None)
    # 요일 효과
    for i in range(days):
        dow = (OBSERVATION_START + timedelta(days=int(i))).weekday()
        if dow >= 5: base[i] *= 0.92
    return base.round().astype(int)

# ============================================================
# STT 오류 패턴 삽입
# ============================================================
STT_ERROR_MAP = {
    '효돌': ['효도리', '효소리', '효들이', '효돌이', '효도', '효소'],
    '효돌아': ['효도리야', '효소리야', '효들이야'],
    '효돌이': ['효도리', '효소리', '효들이'],
}

def inject_stt_errors(text, confidence, rng):
    """STT 신뢰도에 따라 텍스트에 인식 오류 패턴 삽입.
    Fix 6: 변형 빈도 상향 — 의도 10~30% 도달 위해 prob 계수 확대."""
    # 변형 가능한 키워드가 있는지 먼저 확인
    has_target = any(orig in text for orig in STT_ERROR_MAP.keys())
    if not has_target:
        return text
    # confidence 0.95 → 0.05, 0.5 → 0.50 정도로
    error_prob = min(0.50, (1.0 - confidence) * 1.0)
    if rng.random() > error_prob:
        return text
    for orig, errors in STT_ERROR_MAP.items():
        if orig in text:
            err = errors[rng.integers(0, len(errors))]
            text = text.replace(orig, err, 1)
            break
    return text


# Fix 2 — 효돌-노인 dialogue 페어 row 생성용 헬퍼
def _make_dialogue_row(user_id, ts, speaker, turn_id, turn_pool, stt_conf, rng):
    """단일 dialogue row 생성. turn_id로 효돌-노인 페어 묶음."""
    if speaker == 'hyodol':
        # Fix 7 — 80% 확률로 짧은 turn (15~50자), 20% medium
        if rng.random() < 0.8:
            pool = [t for t in turn_pool if 15 <= len(t) <= 50]
            if not pool: pool = turn_pool
        else:
            pool = turn_pool
        text = pool[rng.integers(0, len(pool))]
        duration = max(1.0, len(text) * 0.12 + float(rng.normal(0, 0.5)))
        confidence_field = None
    else:
        text = turn_pool[rng.integers(0, len(turn_pool))]
        text = inject_stt_errors(text, stt_conf, rng)
        duration = max(1.0, len(text) * 0.18 + float(rng.normal(0, 0.5)))
        confidence_field = float(stt_conf)

    return {
        'user_id': user_id, 'event_ts': ts, 'event_date': ts.date(),
        'event_hour': ts.hour, 'event_dow': ts.weekday(),
        'event_type': 'dialogue', 'event_subtype': speaker,
        'dialogue_turn_id': turn_id, 'dialogue_speaker': speaker,
        'dialogue_text': text,
        'dialogue_duration_sec': float(duration),
        'dialogue_stt_confidence': confidence_field,
        'interaction_type': None, 'interaction_duration_sec': None, 'interaction_intensity': None,
        'program_type': None, 'program_duration_sec': None, 'program_completed': None,
        'program_quiz_correct': None, 'program_quiz_total': None,
        'health_question': None, 'health_answer': None, 'health_answer_category': None,
        'prompt_type': None, 'prompt_text': None,
        'cognition_test_id': None, 'cognition_window_sec': None,
        'response_occurred': None, 'response_delay_sec': None, 'response_event_id': None,
        'battery_pct': None, 'human_detected': None, 'last_action_gap_sec': None,
    }

# ============================================================
# 행동 로그 합성 (한 사용자)
# ============================================================
def generate_behavior_for_user(profile_row, latents, hyodol_turns, senior_turns, rng):
    """한 사용자의 90일 행동 로그 이벤트 생성."""
    user_id = profile_row['user_id']
    usage = profile_row['usage_pattern']
    install_date = profile_row['install_date'].date() if hasattr(profile_row['install_date'], 'date') else profile_row['install_date']
    stt_conf = profile_row['dialogue_stt_confidence']
    cognition = latents['cognition']

    events = []
    install_day = max(0, (install_date - OBSERVATION_START).days)
    daily_counts = daily_event_count_series(usage, install_day, OBSERVATION_DAYS, rng)

    total_events_90d = int(daily_counts.sum())

    for day_idx in range(OBSERVATION_DAYS):
        n_today = daily_counts[day_idx]
        if n_today == 0:
            continue
        current_date = OBSERVATION_START + timedelta(days=day_idx)

        # 이벤트 타입 split
        type_counts = {t: int(round(n_today * p)) for t, p in EVENT_MIX.items()}
        # 보정
        diff = n_today - sum(type_counts.values())
        type_counts['dialogue'] += diff

        # 각 이벤트 timestamp + 데이터
        for event_type, cnt in type_counts.items():
            # event_type별 시간대 가중치 선택
            hour_w = HOUR_WEIGHTS_SYSTEM if event_type == 'system' else HOUR_WEIGHTS_ACTIVE
            for _ in range(cnt):
                hour = int(rng.choice(24, p=hour_w))
                minute = int(rng.integers(0, 60))
                second = int(rng.integers(0, 60))
                ts = datetime.combine(current_date, datetime.min.time()) + timedelta(hours=hour, minutes=minute, seconds=second)

                # dialogue 이벤트는 페어로 생성 (Fix 2 — turn pair)
                if event_type == 'dialogue':
                    turn_id = str(uuid.uuid4())[:8]
                    h_evt = _make_dialogue_row(user_id, ts, 'hyodol', turn_id,
                                               hyodol_turns, stt_conf, rng)
                    events.append(h_evt)
                    # 노인 답변 75% 확률
                    if rng.random() < 0.75:
                        s_ts = ts + timedelta(seconds=float(rng.uniform(1.0, 6.0)))
                        s_evt = _make_dialogue_row(user_id, s_ts, 'senior', turn_id,
                                                   senior_turns, stt_conf, rng)
                        events.append(s_evt)
                else:
                    evt = make_event(event_type, user_id, ts, latents, profile_row,
                                     hyodol_turns, senior_turns, stt_conf, cognition, rng)
                    events.append(evt)

    return events, total_events_90d

def make_event(event_type, user_id, ts, latents, profile_row, hyodol_turns, senior_turns, stt_conf, cognition, rng):
    """단일 이벤트 dict 생성. event_type별 sparse 컬럼 채움."""
    base = {
        'user_id': user_id, 'event_ts': ts, 'event_date': ts.date(),
        'event_hour': ts.hour, 'event_dow': ts.weekday(),
        'event_type': event_type, 'event_subtype': None,
        'dialogue_turn_id': None, 'dialogue_speaker': None, 'dialogue_text': None,
        'dialogue_duration_sec': None, 'dialogue_stt_confidence': None,
        'interaction_type': None, 'interaction_duration_sec': None, 'interaction_intensity': None,
        'program_type': None, 'program_duration_sec': None, 'program_completed': None,
        'program_quiz_correct': None, 'program_quiz_total': None,
        'health_question': None, 'health_answer': None, 'health_answer_category': None,
        'prompt_type': None, 'prompt_text': None,
        'cognition_test_id': None, 'cognition_window_sec': None,
        'response_occurred': None, 'response_delay_sec': None, 'response_event_id': None,
        'battery_pct': None, 'human_detected': None, 'last_action_gap_sec': None,
    }

    if event_type == 'dialogue':
        # speaker 선택 (hyodol과 senior alternating)
        speaker = 'hyodol' if rng.random() < 0.55 else 'senior'
        turn_id = str(uuid.uuid4())[:8]
        if speaker == 'hyodol':
            text = hyodol_turns[rng.integers(0, len(hyodol_turns))]
            duration = max(1.0, len(text) * 0.12 + rng.normal(0, 0.5))
        else:
            text = senior_turns[rng.integers(0, len(senior_turns))]
            text = inject_stt_errors(text, stt_conf, rng)
            duration = max(1.0, len(text) * 0.18 + rng.normal(0, 0.5))
        base.update({
            'event_subtype': speaker,
            'dialogue_turn_id': turn_id,
            'dialogue_speaker': speaker,
            'dialogue_text': text,
            'dialogue_duration_sec': float(duration),
            'dialogue_stt_confidence': float(stt_conf) if speaker == 'senior' else None,
        })

    elif event_type == 'interaction':
        itype = rng.choice(INTERACTION_TYPES, p=[INTERACTION_PCT[t] for t in INTERACTION_TYPES])
        base.update({
            'event_subtype': itype,
            'interaction_type': itype,
            'interaction_duration_sec': float(max(0.5, rng.normal(2.5, 1.0))),
            'interaction_intensity': int(np.clip(rng.normal(3, 1), 1, 5)),
        })

    elif event_type == 'program':
        ptype = PROGRAM_TYPES[rng.integers(0, len(PROGRAM_TYPES))]
        duration = int(max(30, rng.normal(180, 60)))
        completed = bool(rng.random() < (0.6 + 0.3 * cognition))
        quiz_correct = quiz_total = None
        if ptype == 'quiz':
            quiz_total = int(rng.integers(5, 11))
            quiz_correct = int(np.clip(rng.binomial(quiz_total, cognition * 0.9), 0, quiz_total))
        base.update({
            'event_subtype': ptype,
            'program_type': ptype,
            'program_duration_sec': duration,
            'program_completed': completed,
            'program_quiz_correct': quiz_correct,
            'program_quiz_total': quiz_total,
        })

    elif event_type == 'health_check':
        q = HEALTH_QUESTIONS[rng.integers(0, len(HEALTH_QUESTIONS))]
        answer_pool = {
            'sleep': ['잘 잤어요', '뒤척였어요', '잘 못 잤어요', '괜찮았어요'],
            'mood': ['좋아요', '그저 그래요', '울적해요', '편안해요'],
            'plan': ['집에서 쉬려고요', '병원 가야 해요', '아무 계획 없어요', '복지관 가요'],
            'pain': ['괜찮아요', '허리가 아파요', '무릎이 시려요', '머리가 아파요'],
            'appetite': ['잘 먹어요', '입맛 없어요', '조금 먹었어요', '평소대로요'],
        }
        ans = answer_pool[q][rng.integers(0, len(answer_pool[q]))]
        # 카테고리
        if q == 'mood':
            cat = 'negative' if ('울적' in ans or '안 좋' in ans) else ('positive' if '좋' in ans or '편안' in ans else 'neutral')
        else:
            cat = None
        base.update({
            'event_subtype': q,
            'health_question': q,
            'health_answer': ans,
            'health_answer_category': cat,
        })

    elif event_type == 'prompt':
        # 60% 인지 측정용 prompt, 40% 기타
        if rng.random() < 0.65:
            ptype = PROMPT_TYPES_COG[rng.integers(0, len(PROMPT_TYPES_COG))]
            cog_test_id = str(uuid.uuid4())
            window = 30
            # 응답 발생 여부 — cognition 기반
            response_prob = 0.30 + 0.55 * cognition
            occurred = bool(rng.random() < response_prob)
            if occurred:
                # 응답 딜레이 — cognition 높을수록 짧음 (1~window 사이)
                base_delay = (1 - cognition) * 12 + 1.5
                delay = float(np.clip(rng.gamma(2.0, base_delay / 2.0), 0.3, window - 0.5))
            else:
                delay = None
        else:
            ptype = PROMPT_TYPES_OTHER[rng.integers(0, len(PROMPT_TYPES_OTHER))]
            cog_test_id = None
            window = None
            occurred = None
            delay = None

        prompt_text = PROMPT_TEXT_POOLS[ptype][rng.integers(0, len(PROMPT_TEXT_POOLS[ptype]))]
        base.update({
            'event_subtype': ptype,
            'prompt_type': ptype,
            'prompt_text': prompt_text,
            'cognition_test_id': cog_test_id,
            'cognition_window_sec': window,
            'response_occurred': occurred,
            'response_delay_sec': delay,
        })

    elif event_type == 'system':
        base.update({
            'event_subtype': 'heartbeat',
            'battery_pct': int(rng.integers(30, 100)),
            'human_detected': bool(rng.random() < 0.7),
            'last_action_gap_sec': int(np.clip(rng.exponential(600), 0, 86400)),
        })

    return base

# ============================================================
# Prompt-Response 페어링 (post-process)
# ============================================================
def pair_cognition_responses(behavior_df):
    """response_occurred=TRUE인 prompt에 대해, window 내 매칭 interaction을 찾아 페어링 키 부여."""
    # cognition_test_id 보유 prompt만 추출
    prompts = behavior_df[
        (behavior_df['event_type'] == 'prompt') &
        (behavior_df['cognition_test_id'].notna()) &
        (behavior_df['response_occurred'] == True)
    ].sort_values('event_ts').reset_index(drop=True)

    # 페어링 대상 interaction 생성 — prompt 다음 delay 시점에 새 interaction event를 추가
    # 실제로는 합성 시점에 만들기보다는 별도 페어 이벤트로 삽입
    new_events = []
    for _, row in prompts.iterrows():
        if pd.isna(row['response_delay_sec']):
            continue
        ts = row['event_ts'] + timedelta(seconds=float(row['response_delay_sec']))
        ptype = row['prompt_type']
        itype_map = {
            'head_stroke_request': 'stroke',
            'hand_hold_request': 'hand_hold',
            'chest_pat_request': 'chest_pat',
            'verbal_response_request': 'verbal_response',
            'quiz_response_request': 'verbal_response',  # 퀴즈 응답도 verbal
        }
        itype = itype_map.get(ptype)
        if not itype:
            continue
        new_evt = {
            'user_id': row['user_id'], 'event_ts': ts, 'event_date': ts.date(),
            'event_hour': ts.hour, 'event_dow': ts.weekday(),
            'event_type': 'interaction', 'event_subtype': itype,
            'dialogue_turn_id': None, 'dialogue_speaker': None, 'dialogue_text': None,
            'dialogue_duration_sec': None, 'dialogue_stt_confidence': None,
            'interaction_type': itype,
            'interaction_duration_sec': float(max(0.5, np.random.normal(2.5, 1.0))),
            'interaction_intensity': int(np.clip(np.random.normal(3, 1), 1, 5)),
            'program_type': None, 'program_duration_sec': None, 'program_completed': None,
            'program_quiz_correct': None, 'program_quiz_total': None,
            'health_question': None, 'health_answer': None, 'health_answer_category': None,
            'prompt_type': None, 'prompt_text': None,
            'cognition_test_id': row['cognition_test_id'],
            'cognition_window_sec': None, 'response_occurred': None,
            'response_delay_sec': None, 'response_event_id': None,
            'battery_pct': None, 'human_detected': None, 'last_action_gap_sec': None,
        }
        new_events.append(new_evt)

    if new_events:
        new_df = pd.DataFrame(new_events)
        behavior_df = pd.concat([behavior_df, new_df], ignore_index=True)

    return behavior_df

def assign_event_ids_and_link(behavior_df):
    """event_id 부여 후, prompt event의 response_event_id 필드를 연결."""
    behavior_df = behavior_df.sort_values('event_ts').reset_index(drop=True)
    behavior_df['event_id'] = behavior_df.index + 1
    # cognition_test_id 별 prompt event_id와 interaction event_id 매칭
    cog_ids = behavior_df[behavior_df['cognition_test_id'].notna()].groupby('cognition_test_id').agg(
        prompt_eid=('event_id', lambda s: s.iloc[0] if len(s) >= 1 else None),
        resp_eid=('event_id', lambda s: s.iloc[1] if len(s) >= 2 else None),
    ).reset_index()
    # prompt event의 response_event_id 채우기
    for _, row in cog_ids.iterrows():
        cid = row['cognition_test_id']
        rid = row['resp_eid']
        if pd.notna(rid):
            mask = (behavior_df['cognition_test_id'] == cid) & (behavior_df['event_type'] == 'prompt')
            behavior_df.loc[mask, 'response_event_id'] = int(rid)
    return behavior_df

# ============================================================
# 사후 wave latent 보정 (효돌 사용 강도 효과)
# ============================================================
def adjust_post_latents(latents, usage_pattern, total_events_90d, rng):
    """사용 패턴 + 사용 강도에 따라 latent 변화량 적용 (post wave용)."""
    out = latents.copy()
    # 사용 강도가 높을수록 우울·고독 감소
    intensity_factor = min(1.0, total_events_90d / 4000.0)  # 90일 4000 이벤트가 high intensity

    pattern_effect = {
        'loyal_heavy': 0.85, 'growing': 0.85, 'loyal_light': 1.0,
        'declining': 0.95, 'spike': 0.95, 'fading': 1.0, 'trial_drop': 1.0,
    }.get(usage_pattern, 1.0)

    out['depression'] = float(np.clip(latents['depression'] * pattern_effect - 0.05 * intensity_factor + rng.normal(0, 0.05), 0.05, 0.95))
    out['loneliness'] = float(np.clip(latents['loneliness'] * pattern_effect - 0.04 * intensity_factor + rng.normal(0, 0.05), 0.05, 0.95))
    out['lifestyle'] = float(np.clip(latents['lifestyle'] + 0.08 * intensity_factor + rng.normal(0, 0.05), 0.10, 0.99))
    out['adherence'] = float(np.clip(latents['adherence'] + 0.05 * intensity_factor + rng.normal(0, 0.05), 0.10, 0.99))
    return out

# ============================================================
# 메인 실행
# ============================================================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--n', type=int, default=50)
    parser.add_argument('--seed', type=int, default=20260521)
    args = parser.parse_args()

    n = args.n
    rng = np.random.default_rng(args.seed)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    print(f"========= 효돌 합성 데이터 시범 생성: n={n} =========\n")
    t_total = time.time()

    # --- 1. 효돌 원본 대화 풀 로드 ---
    t1 = time.time()
    print("[1/5] 효돌 원본 대화 풀 로드...")
    hyodol_turns, senior_turns = load_hyodol_dialogue_pool()
    print(f"  hyodol turn: {len(hyodol_turns)}, senior turn: {len(senior_turns)}")
    print(f"  소요: {time.time()-t1:.2f}초\n")

    # --- 2. Nemotron sampling + profile 보강 ---
    t2 = time.time()
    print("[2/5] Nemotron 페르소나 sampling + profile 보강...")
    personas = sample_nemotron_personas(n, rng)
    profile_rows = []
    latents_all = {}
    for i, persona in personas.iterrows():
        user_id = f"U{i+1:04d}"
        latents = compute_latent_states(persona, rng)
        latents_all[user_id] = latents

        # 효돌 도메인 컬럼
        doll_id = str(8000 + i + 1)
        serial_hash = hashlib.sha256(f"doll_{user_id}_{args.seed}".encode()).hexdigest()[:8].upper()
        serial_number = f"S-{serial_hash}"
        # 인형 성별 — 사용자와 동일 선호 (70%)
        doll_gender = persona['sex'] if rng.random() < 0.7 else ('남자' if persona['sex'] == '여자' else '여자')
        doll_gender = '남성' if doll_gender == '남자' else '여성'
        nickname = DOLL_NICKNAMES[rng.integers(0, len(DOLL_NICKNAMES))]

        # 설치 일자 — 관찰 첫 14일 내 (Fix 3 — 사용 패턴 시계열이 충분히 발현되도록)
        install_day = rng.integers(0, 14)
        install_date = datetime.combine(OBSERVATION_START + timedelta(days=int(install_day)), datetime.min.time()) + timedelta(hours=int(rng.integers(8, 19)))

        agency, agency_type = AGENCY_POOL[rng.integers(0, len(AGENCY_POOL))]

        # 사용 패턴 할당
        usage = rng.choice(USAGE_PATTERNS, p=[USAGE_PCT[u] for u in USAGE_PATTERNS])
        usage_label = USAGE_LABEL[usage]

        # 사용자 유형 9분류 — 우울·loneliness·activity에 따라 stochastic
        utype = USER_TYPES[rng.integers(0, len(USER_TYPES))]

        # 가족 컨텍스트 — 효돌 원본 결측 패턴 재현 (50% 결측)
        spouse = ('있음' if persona['marital_status'] == '배우자있음' else '없음') if rng.random() < 0.5 else None
        having_children = ('있음' if rng.random() < 0.8 else '없음') if rng.random() < 0.5 else None
        son = int(rng.integers(0, 4)) if having_children == '있음' else (0 if having_children == '없음' else None)
        daughter = int(rng.integers(0, 4)) if having_children == '있음' else (0 if having_children == '없음' else None)
        if son is None and daughter is None:
            son = daughter = None

        # 사전·사후 latent
        # 일단 더미 — behavior 합성 후 보정 예정
        profile_rows.append({
            'user_id': user_id,
            'doll_id': doll_id,
            'serial_number': serial_number,
            'sex': persona['sex'], 'age': int(persona['age']), 'age_group': persona['age_group'],
            'marital_status': persona['marital_status'],
            'family_type': persona['family_type'],
            'housing_type': persona['housing_type'],
            'education_level': persona['education_level'],
            'occupation': persona['occupation'],
            'province': persona['province'], 'district': persona['district'],
            'doll_gender': doll_gender, 'doll_nickname': nickname,
            'install_date': install_date,
            'install_agency': agency, 'agency_type': agency_type,
            'is_survey_possible': '가능',
            'spouse': spouse, 'having_children': having_children,
            'son': son, 'daughter': daughter,
            'housing_cleanliness': rng.choice(['좋음', '보통', '나쁨']) if rng.random() < 0.4 else None,
            'meal': rng.choice(['규칙적', '불규칙']) if rng.random() < 0.4 else None,
            'public_visit_support': None,
            'taking_medicine': None,
            'usage_pattern': str(usage), 'usage_pattern_label': usage_label,
            'user_type_code': utype[0], 'user_type_name': utype[1],
            'alarm_settings': json.dumps({
                'meal_morning': '07:30', 'meal_lunch': '12:00', 'meal_dinner': '18:00',
                'med_morning': '08:00', 'med_evening': '20:00',
                'wake': '06:30', 'sleep': '22:00',
            }, ensure_ascii=False),
            'dialogue_stt_confidence': float(np.clip(0.85 - 0.005 * (persona['age'] - 60) + rng.normal(0, 0.05), 0.5, 0.98)),
            'cognition_baseline_score': latents['cognition'],
            # 설문 총점은 행동 합성 후 채움
        })
    profile_df = pd.DataFrame(profile_rows)
    print(f"  profile: {len(profile_df)}명 ({len(profile_df.columns)} 컬럼)")
    print(f"  소요: {time.time()-t2:.2f}초\n")

    # --- 3. Behavior log 합성 ---
    t3 = time.time()
    print("[3/5] Behavior log 합성...")
    all_events = []
    intensity_by_user = {}
    for _, prow in profile_df.iterrows():
        events, total = generate_behavior_for_user(
            prow, latents_all[prow['user_id']],
            hyodol_turns, senior_turns, rng
        )
        intensity_by_user[prow['user_id']] = total
        all_events.extend(events)
    behavior_df = pd.DataFrame(all_events)
    print(f"  raw events: {len(behavior_df):,}")
    # 페어링 (response interaction event 추가)
    behavior_df = pair_cognition_responses(behavior_df)
    behavior_df = assign_event_ids_and_link(behavior_df)
    print(f"  페어링 후 events: {len(behavior_df):,}")
    print(f"  소요: {time.time()-t3:.2f}초\n")

    # --- 4. Survey responses (pre/post) ---
    t4 = time.time()
    print("[4/5] 설문 응답 합성 (사전·사후 wave)...")
    all_responses = []
    for _, prow in profile_df.iterrows():
        latents = latents_all[prow['user_id']]
        # 사전
        pre_rows = generate_survey_responses(prow, latents, 'pre', rng)
        all_responses.extend(pre_rows)
        # 사후 — 사용 강도·패턴 효과 적용한 latent
        intensity = intensity_by_user.get(prow['user_id'], 0)
        post_latents = adjust_post_latents(latents, prow['usage_pattern'], intensity, rng)
        post_rows = generate_survey_responses(prow, post_latents, 'post', rng)
        all_responses.extend(post_rows)
    survey_df = pd.DataFrame(all_responses)
    print(f"  survey_responses: {len(survey_df):,}")
    print(f"  소요: {time.time()-t4:.2f}초\n")

    # 설문 총점 → profile에 보충
    print("  설문 총점 → profile 보충...")
    for idx, prow in profile_df.iterrows():
        uid = prow['user_id']
        pre_t = compute_survey_totals(survey_df, uid, 'pre')
        post_t = compute_survey_totals(survey_df, uid, 'post')
        profile_df.at[idx, 'mmas_total_pre'] = pre_t.get('mmas')
        profile_df.at[idx, 'mmas_total_post'] = post_t.get('mmas')
        profile_df.at[idx, 'gds_total_pre'] = pre_t.get('gds')
        profile_df.at[idx, 'gds_total_post'] = post_t.get('gds')
        profile_df.at[idx, 'gds_result_pre'] = categorize_result('gds', pre_t.get('gds'))
        profile_df.at[idx, 'gds_result_post'] = categorize_result('gds', post_t.get('gds'))
        profile_df.at[idx, 'phq9_total_pre'] = pre_t.get('phq9')
        profile_df.at[idx, 'phq9_total_post'] = post_t.get('phq9')
        # phq9 q9
        q9_pre = survey_df[(survey_df['user_id']==uid)&(survey_df['wave']=='pre')&(survey_df['survey_type']=='phq9')&(survey_df['question_no']==9)]
        q9_post = survey_df[(survey_df['user_id']==uid)&(survey_df['wave']=='post')&(survey_df['survey_type']=='phq9')&(survey_df['question_no']==9)]
        profile_df.at[idx, 'phq9_q9_pre'] = int(q9_pre['answer_score'].iloc[0]) if len(q9_pre) else None
        profile_df.at[idx, 'phq9_q9_post'] = int(q9_post['answer_score'].iloc[0]) if len(q9_post) else None
        profile_df.at[idx, 'ucla_total_pre'] = pre_t.get('ucla')
        profile_df.at[idx, 'ucla_total_post'] = post_t.get('ucla')
        profile_df.at[idx, 'whodas_total_pre'] = pre_t.get('whodas')
        profile_df.at[idx, 'whodas_total_post'] = post_t.get('whodas')
        profile_df.at[idx, 'life_mgmt_total_pre'] = pre_t.get('life_mgmt')
        profile_df.at[idx, 'life_mgmt_total_post'] = post_t.get('life_mgmt')
        profile_df.at[idx, 'life_mgmt_result_pre'] = categorize_result('life_mgmt', pre_t.get('life_mgmt'))
        profile_df.at[idx, 'life_mgmt_result_post'] = categorize_result('life_mgmt', post_t.get('life_mgmt'))
        profile_df.at[idx, 'usability_total_post'] = post_t.get('usability')

    # --- 5. Parquet 저장 (DuckDB COPY 사용) ---
    t5 = time.time()
    print("[5/5] Parquet 저장 (DuckDB COPY)...")

    def save_via_csv(df, name, con):
        """pandas DataFrame을 CSV 임시파일 경유하여 Parquet ZSTD로 저장.
        DuckDB의 numpy scalar 미지원 문제를 우회."""
        tmp_csv = DATA_DIR / f"_{name}.csv"
        out_parquet = DATA_DIR / f"{name}.parquet"
        df.to_csv(tmp_csv, index=False, encoding='utf-8')
        con.execute(f"""
            COPY (SELECT * FROM read_csv_auto('{tmp_csv.as_posix()}', header=true, sample_size=-1))
            TO '{out_parquet.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
        """)
        tmp_csv.unlink()
        return out_parquet

    con = duckdb.connect()
    save_via_csv(profile_df, 'profile', con)
    save_via_csv(behavior_df, 'behavior_log', con)
    save_via_csv(survey_df, 'survey_responses', con)
    con.close()
    # 파일 크기 출력
    for fname in ['profile.parquet', 'behavior_log.parquet', 'survey_responses.parquet']:
        path = DATA_DIR / fname
        size_mb = path.stat().st_size / 1024 / 1024
        print(f"  {fname}: {size_mb:.2f} MB")
    print(f"  소요: {time.time()-t5:.2f}초\n")

    # --- 종합 ---
    print(f"========= 전체 소요: {time.time()-t_total:.2f}초 =========")
    print(f"  profile rows: {len(profile_df):,}")
    print(f"  behavior_log rows: {len(behavior_df):,}")
    print(f"  survey_responses rows: {len(survey_df):,}")

if __name__ == "__main__":
    main()
