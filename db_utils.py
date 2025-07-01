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
def fetch_unlabeled_news(batch_size: int):
    """
    news_silver 에 있는 step_id별로,
    아직 news_classification에 없는 기사  batch_size개를 가져옴
    반환 형식: List[(news_id, step_id, title, description)]
    """
    conn = get_pg_conn()
    cur = conn.cursor()
    cur.execute("""
    SELECT ns.news_id,
           ns.step_id,
           n.title,
           n.description
    FROM news_silver ns
    JOIN news n 
      ON ns.news_id = n.id
    LEFT JOIN news_classification nc
      ON ns.news_id = nc.news_id
     AND ns.step_id = nc.step_id
    WHERE nc.news_id IS NULL
    LIMIT %s;
    """, (batch_size,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows
