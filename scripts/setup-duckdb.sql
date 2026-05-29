-- ===============================================================
-- 효돌 합성 어르신 데이터셋 — DuckDB 환경 셋업 (v0.2.1)
--
-- 1000명 풀스케일 데이터 (data/pilot-1000/) 를 기본 분석 대상으로 등록한다.
-- 100명 호환 데이터 (data/pilot-100-v2/) 는 별도 뷰로도 참조 가능.
--
-- 실행:
--     cd <hyodol-synthetic-elderly>
--     duckdb hyodol.duckdb < scripts/setup-duckdb.sql
-- ===============================================================

-- 1. 메인 테이블/뷰 — pilot-1000 (v0.2.0+, 권장 default)
CREATE OR REPLACE VIEW profile          AS SELECT * FROM read_parquet('data/pilot-1000/profile.parquet');
CREATE OR REPLACE VIEW behavior_log     AS SELECT * FROM read_parquet('data/pilot-1000/behavior_log.parquet');
CREATE OR REPLACE VIEW survey_responses AS SELECT * FROM read_parquet('data/pilot-1000/survey_responses.parquet');

-- 2. 100명 호환 뷰 (v0.1.0 호환용 — 비교 분석 시)
CREATE OR REPLACE VIEW profile_100          AS SELECT * FROM read_parquet('data/pilot-100-v2/profile.parquet');
CREATE OR REPLACE VIEW behavior_log_100     AS SELECT * FROM read_parquet('data/pilot-100-v2/behavior_log.parquet');
CREATE OR REPLACE VIEW survey_responses_100 AS SELECT * FROM read_parquet('data/pilot-100-v2/survey_responses.parquet');

-- 3. 메타데이터
CREATE OR REPLACE TABLE _meta AS
    SELECT
        (SELECT COUNT(*) FROM profile)          AS profile_rows,
        (SELECT COUNT(*) FROM behavior_log)     AS behavior_log_rows,
        (SELECT COUNT(*) FROM survey_responses) AS survey_responses_rows,
        (SELECT COUNT(*) FROM profile_100)      AS profile_100_rows,
        CURRENT_TIMESTAMP                       AS setup_at;

-- 4. 자주 쓰는 분포 캐싱 (1000명 기준)
CREATE OR REPLACE TABLE dist_age_group AS
    SELECT age_group, COUNT(*) AS n FROM profile GROUP BY age_group ORDER BY age_group;

CREATE OR REPLACE TABLE dist_sex AS
    SELECT sex, COUNT(*) AS n FROM profile GROUP BY sex;

CREATE OR REPLACE TABLE dist_usage_pattern AS
    SELECT usage_pattern, usage_pattern_label, COUNT(*) AS n
    FROM profile GROUP BY usage_pattern, usage_pattern_label ORDER BY n DESC;

CREATE OR REPLACE TABLE dist_user_type AS
    SELECT user_type_code, user_type_name, COUNT(*) AS n
    FROM profile GROUP BY user_type_code, user_type_name ORDER BY n DESC;

CREATE OR REPLACE TABLE dist_province AS
    SELECT province, COUNT(*) AS n FROM profile GROUP BY province ORDER BY n DESC;

-- 5. batch 분포 (v0.2.0 — 500명 × 2 머지 결과 추적)
CREATE OR REPLACE TABLE dist_batch AS
    SELECT batch_id, COUNT(*) AS n FROM profile GROUP BY batch_id ORDER BY batch_id;

-- 5b. ★ 비전공 친화 family_group 6범주 wrapper (v0.2.5)
-- profile.family_type 원본은 15+ 도메인으로 fragmented — 학생용 6범주로 묶음
CREATE OR REPLACE VIEW profile_with_family_group AS
    SELECT *,
        CASE
            WHEN family_type LIKE '혼자%'                                                  THEN '혼자'
            WHEN family_type = '배우자와 거주'                                             THEN '배우자만'
            WHEN family_type LIKE '배우자·자녀%' OR family_type LIKE '배우자.자녀%'        THEN '배우자+자녀'
            WHEN family_type LIKE '자녀%'                                                  THEN '자녀와만'
            WHEN family_type LIKE '%3세대%'
              OR family_type LIKE '%부모와 거주%'
              OR family_type LIKE '%편부모%'                                               THEN '3세대+'
            ELSE '기타'
        END AS family_group
    FROM profile;

CREATE OR REPLACE TABLE dist_family_group AS
    SELECT family_group, COUNT(*) AS n
    FROM profile_with_family_group
    GROUP BY family_group ORDER BY n DESC;

-- 6. 이벤트 타입 분포
CREATE OR REPLACE TABLE dist_event_type AS
    SELECT event_type, COUNT(*) AS n
    FROM behavior_log GROUP BY event_type ORDER BY n DESC;

-- 7. interaction type 분포
CREATE OR REPLACE TABLE dist_interaction_type AS
    SELECT interaction_type, COUNT(*) AS n
    FROM behavior_log
    WHERE event_type = 'interaction'
    GROUP BY interaction_type ORDER BY n DESC;

-- 8. 일별 이벤트 카운트 (시계열)
CREATE OR REPLACE TABLE daily_event_count AS
    SELECT event_date, event_type, COUNT(*) AS n
    FROM behavior_log
    GROUP BY event_date, event_type
    ORDER BY event_date, event_type;

-- 9. 설문 사전·사후 변화 (사용자별 pivot)
CREATE OR REPLACE TABLE survey_pre_post_pivot AS
    SELECT
        user_id,
        gds_total_pre,  gds_total_post,  (gds_total_post  - gds_total_pre)  AS gds_delta,
        phq9_total_pre, phq9_total_post, (phq9_total_post - phq9_total_pre) AS phq9_delta,
        ucla_total_pre, ucla_total_post, (ucla_total_post - ucla_total_pre) AS ucla_delta,
        life_mgmt_total_pre, life_mgmt_total_post,
        (life_mgmt_total_post - life_mgmt_total_pre) AS life_mgmt_delta
    FROM profile;

-- 10. 인지 측정 페어 추출 (분석 자주 쓰는 view — 본 데이터셋 핵심 분석축)
CREATE OR REPLACE VIEW cognition_tests AS
    SELECT
        b.event_id           AS prompt_event_id,
        b.event_ts           AS prompt_ts,
        b.user_id,
        b.prompt_type,
        b.cognition_test_id,
        b.cognition_window_sec,
        b.response_occurred,
        b.response_delay_sec,
        b.response_event_id
    FROM behavior_log b
    WHERE b.event_type = 'prompt'
        AND b.cognition_test_id IS NOT NULL;

-- 11. 완료 확인
SELECT '✅ 셋업 완료 — v0.2.1' AS status, * FROM _meta;
