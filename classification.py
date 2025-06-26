import os
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from db_utils import get_pg_conn

# 학습된 파인튜닝 모델 로드
MODEL_PATH = "policy-impl-classifier"
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
model.eval()

def classify_text(text: str) -> dict:
    """
    문장 하나를 입력받아 {'label': str, 'confidence': float} 반환
    """
    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=512
    )
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        probs = torch.softmax(logits, dim=1).squeeze().tolist()
        pred_idx = int(torch.argmax(logits, dim=1).item())
    label = model.config.id2label[pred_idx]
    confidence = probs[pred_idx]
    return {"label": label, "confidence": confidence}


def save_classification(news_id: int, result: dict):
    """
    분류 결과를 news_classification 테이블에 저장
    """
    conn = get_pg_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO news_classification (news_id, label, confidence)
        VALUES (%s, %s, %s)
        """,
        (news_id, result["label"], result["confidence"])
    )
    conn.commit()
    cur.close()
    conn.close()
