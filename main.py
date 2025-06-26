from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

from classification import classify_text, save_classification
from db_utils import fetch_unlabeled_news

app = FastAPI()

class ClassifyResponse(BaseModel):
    news_id: int
    label: str
    confidence: float

@app.get("/")
def health_check():
    return {"status": "classification service up"}

@app.post("/classify-news", response_model=List[ClassifyResponse])
def classify_news(batch_size: int = 20):
    """
    1) DB에서 아직 분류되지 않은 뉴스(batch_size개) 가져오기
    2) 모델로 분류 → DB에 저장
    3) 결과 반환
    """
    rows = fetch_unlabeled_news(batch_size)
    results = []
    for news_id, title, desc in rows:
        text = f"{title}\n{desc}"
        res = classify_text(text)
        save_classification(news_id, res)
        results.append(ClassifyResponse(
            news_id=news_id,
            label=res["label"],
            confidence=res["confidence"]
        ))
    return results
