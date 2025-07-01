import os
from datetime import datetime, time
import psycopg2
from db_utils import get_pg_conn

# confidence 컷오프 등 비즈니스 룰 (상수로 사용)
CONF_THRESHOLD = 0.8

def get_today_window():
    """오늘 00:00:00 부터 지금까지의 타임스탬프 범위를 돌려줍니다."""
    now = datetime.now()
    start = datetime.combine(now.date(), time.min)
    return start, now

def aggregate_classifications(conn, start, end):
    """
    step_id별로 오늘자 분류 결과를 집계해서
    { step_id: (cnt_ok, cnt_in_progress) } 형태의 딕셔너리를 반환.
    """
    cur = conn.cursor()
    cur.execute("""
        SELECT
          step_id,
          SUM(CASE WHEN label = '이행됨' AND confidence >= %s THEN 1 ELSE 0 END) AS cnt_ok,
          SUM(CASE WHEN label = '이행 중' THEN 1 ELSE 0 END) AS cnt_in_progress
        FROM news_classification
        WHERE classified_at BETWEEN %s AND %s
        GROUP BY step_id
    """, (CONF_THRESHOLD, start, end))
    rows = cur.fetchall()
    cur.close()
    return { row[0]: (row[1], row[2]) for row in rows }

def fetch_all_milestones(conn):
    """모든 MILESTONE(id, status)를 딕셔너리로 읽어옵니다."""
    cur = conn.cursor()
    cur.execute("SELECT id, status FROM MILESTONE")
    rows = cur.fetchall()
    cur.close()
    return { row[0]: row[1] for row in rows }

def upsert_status(conn, step_id, new_status, prev_status):
    """
    MILESTONE 테이블의 status를 업데이트하고,
    변화가 있으면 MILESTONE_LOG에 남깁니다.
    """
    cur = conn.cursor()
    # MILESTONE.status 업데이트
    cur.execute("""
        UPDATE MILESTONE
        SET status     = %s,
            updated_at = NOW()
        WHERE id = %s
    """, (new_status, step_id))

    # 상태가 변경된 경우 로그 남기기
    if new_status != prev_status:
        cur.execute("""
            INSERT INTO MILESTONE_LOG (
              milestone_id,
              prev_status,
              new_status,
              reason,
              source_url,
              updated_by,
              updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, NOW())
        """, (
            step_id,
            prev_status,
            new_status,
            f"Daily agg: cnt_ok={counts[0]}, cnt_prog={counts[1]}",
            None,
            os.getenv("GITHUB_ACTOR", "system"),
        ))

    conn.commit()
    cur.close()

if __name__ == "__main__":
    # DB 커넥션
    conn = get_pg_conn()

    # 오늘자 집계
    start_ts, end_ts = get_today_window()
    counts_by_step = aggregate_classifications(conn, start_ts, end_ts)

    # 현재 마일스톤 상태 로드
    current_status = fetch_all_milestones(conn)

    # 각 step에 대해 새 상태 결정 & upsert
    for step_id, prev in current_status.items():
        counts = counts_by_step.get(step_id, (0, 0))
        cnt_ok, cnt_prog = counts

        if cnt_ok >= 1:
            new_status = "이행됨"
        elif cnt_prog >= 1:
            new_status = "이행 중"
        else:
            new_status = "미이행"

        upsert_status(conn, step_id, new_status, prev)

    conn.close()
    print("✔️ Aggregation & pledge status updated.")
