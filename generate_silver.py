import json, random
from db_utils import fetch_unlabeled_news, get_pg_conn
from transformers import pipeline, XLMRobertaTokenizer

# 룰 기반 키워드
MUST_HAVE_KEYWORDS = [
    "추진", "시행", "착수", "착공", "집행", "승인", "확정", "발표",
    "증가", "감소", "개통", "개소", "개관", "보급", "지급", "지원", "도입",
    "법안", "의결", "통과", "공포", "고시", "협약", "MOU"
]

def rule_label(text):
    """키워드가 전혀 없으면 '관련 없음'"""
    return None if any(k in text for k in MUST_HAVE_KEYWORDS) else "관련 없음"

# 느린(slow) 토크나이저 직접 로드 (SentencePiece 필요)
tokenizer = XLMRobertaTokenizer.from_pretrained(
    "joeddav/xlm-roberta-large-xnli"
)
# Zero-shot 파이프라인에 slow 토크나이저 지정
zs = pipeline(
    "zero-shot-classification",
    model="joeddav/xlm-roberta-large-xnli",
    tokenizer=tokenizer,
    device=-1
)
CANDS = ["이행됨", "이행 중", "미이행"]

def save_silver(record):
    """DB 테이블에 news_id, label, confidence, source 만 저장"""
    conn = get_pg_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO news_silver(news_id, label, confidence, source)
        VALUES (%s, %s, %s, %s)
        """,
        (record["news_id"], record["label"], record.get("confidence"), record["source"])
    )
    conn.commit()
    cur.close()
    conn.close()


def main():
    # 미분류 뉴스 불러오기
    rows = fetch_unlabeled_news(500)
    silver = []

    for news_id, title, desc in rows:
        # 뉴스 전체 텍스트
        text = f"{title}\n{desc}"
        # 룰 기반 분류
        lbl = rule_label(text)
        if lbl:
            rec = {
                "news_id": news_id,
                "text": text,
                "label": lbl,
                "confidence": None,
                "source": "rule"
            }
        else:
            # Zero-shot 분류
            out = zs(text, CANDS)
            rec = {
                "news_id": news_id,
                "text": text,
                "label": out["labels"][0],
                "confidence": float(out["scores"][0]),
                "source": "zero-shot"
            }
        silver.append(rec)
        save_silver(rec)

    # 전체 Silver 파일로 저장
    with open("silver_full.jsonl", "w", encoding="utf-8") as f_full:
        for rec in silver:
            f_full.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"전체 Silver 데이터 {len(silver)}건 저장: silver_full.jsonl")

    # 검수용 샘플 100건 생성
    random.shuffle(silver)
    with open("silver_review.jsonl", "w", encoding="utf-8") as f:
        for rec in silver[:100]:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print("Silver 생성 및 DB 저장 완료, 검수용 샘플 100건 ➡ silver_review.jsonl")

if __name__ == "__main__":
    main()
