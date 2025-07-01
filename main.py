from typing import List
from pydantic import BaseModel
from fastapi import FastAPI

from classification import classify_text, save_classification
from db_utils import fetch_unlabeled_news

class ClassifyResponse(BaseModel):
    news_id:    int
    step_id:    int
    label:      str
    confidence: float

app = FastAPI()

@app.post("/classify-news", response_model=List[ClassifyResponse])
def classify_news(batch_size: int = 20):
    rows = fetch_unlabeled_news(batch_size)
    results = []
    for news_id, step_id, title, desc in rows:
        text = f"{title}\n{desc}"
        res = classify_text(text)  
        save_classification(
            news_id=news_id,
            step_id=step_id,
            label=res["label"],
            confidence=res["confidence"],
        )
        results.append(ClassifyResponse(
            news_id=news_id,
            step_id=step_id,
            label=res["label"],
            confidence=res["confidence"],
        ))
    return results
