import os
import pymysql      
import psycopg2      
from dotenv import load_dotenv
load_dotenv(override=True)

# MySQL 연결
def get_mysql_conn():
    return pymysql.connect(
        host     = os.getenv("MYSQL_HOST"),
        user     = os.getenv("MYSQL_USER"),
        password = os.getenv("MYSQL_PASSWORD"),
        database = os.getenv("MYSQL_DB"),
        port     = int(os.getenv("MYSQL_PORT", 3306)),
        cursorclass=pymysql.cursors.DictCursor
    )

# Postgres 연결
def get_pg_conn():
    return psycopg2.connect(
        host     = os.getenv("POSTGRES_HOST"),
        port     = os.getenv("POSTGRES_PORT", 5432),
        dbname   = os.getenv("POSTGRES_DB"),
        user     = os.getenv("POSTGRES_USER"),
        password = os.getenv("POSTGRES_PASSWORD"),
    )

def sync_milestones():
    # MySQL에서 MILESTONE 전부 읽어오기
    m_conn = get_mysql_conn()
    with m_conn.cursor() as m_cur:
        m_cur.execute("""
            SELECT id, pledge_id, sequence, title, description
            FROM milestone;
        """)
        rows = m_cur.fetchall()
    m_conn.close()

    # postgres에 upsert
    pg = get_pg_conn()
    cur = pg.cursor()
    for r in rows:
        cur.execute("""
            INSERT INTO pledge_steps (id, pledge_id, sequence, title, description)
            VALUES (%(id)s, %(pledge_id)s, %(sequence)s, %(title)s, %(description)s)
            ON CONFLICT (id) DO UPDATE
              SET pledge_id   = EXCLUDED.pledge_id,
                  sequence    = EXCLUDED.sequence,
                  title       = EXCLUDED.title,
                  description = EXCLUDED.description;
        """, r)
    pg.commit()
    cur.close()
    pg.close()
    print(f"Synced {len(rows)} milestone(s) from MySQL → Postgres.")

if __name__ == "__main__":
    sync_milestones()
