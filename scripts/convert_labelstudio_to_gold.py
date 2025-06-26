import json

# Label Studio에서 검수 후 Export한 JSONL 파일 경로
in_path = "silver_review.jsonl"
# 사람이 검수해서 덮어쓴 키-값 쌍이 정확히 'news_id', 'text', 'label' 로 남아 있다고 가정
# Label Studio 기본 형식이 다를 경우, rec 내용 구조에 맞춰 키를 조정
out_path = "gold.jsonl"

gold = []
with open(in_path, encoding="utf-8") as fin:
    for line in fin:
        rec = json.loads(line)
        # Label Studio Export JSON 구조 예시:
        # {"data": {"news_id": 123, "text": "..."},
        #  "annotations": [{"result": [{"value": {"choices": ["이행됨"]}}]}]}
        # 만약 이런 구조라면 아래 부분을 변경해야 함
        # 아래는 'in_path'가 단순히 {news_id, text, label}인 경우의 처리 예시:
        news_id = rec.get("news_id")
        text = rec.get("text")
        label = rec.get("label")
        
        gold.append({
            "news_id": news_id,
            "text": text,
            "label": label
        })

# 결과 JSONL로 저장
with open(out_path, "w", encoding="utf-8") as fout:
    for rec in gold:
        fout.write(json.dumps(rec, ensure_ascii=False) + "\n")

print(f"Gold 데이터 {len(gold)}건 생성: {out_path}")
