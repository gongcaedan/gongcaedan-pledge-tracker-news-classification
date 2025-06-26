import os
import psycopg2
from dotenv import load_dotenv

load_dotenv(override=True)

print("Loaded DB credentials:", 
      os.getenv("POSTGRES_USER"), 
      os.getenv("POSTGRES_PASSWORD"))

# db 연결
def get_pg_conn():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        port=os.getenv("POSTGRES_PORT", 5432)
    )

# 라벨링 되지 않은 뉴스 가져오기
def fetch_unlabeled_news(limit=500):
    """
    아직 Silver(또는 Gold) 테이블에 저장된 적 없는 최신 뉴스 가져오기
    """
    conn = get_pg_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, title, description
                FROM news
                WHERE id NOT IN (
                    SELECT news_id FROM news_silver
                )
                ORDER BY pub_date DESC
                LIMIT %s
    """, (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows