import json

# load gold IDs
gold_ids = set()
with open("gold.jsonl", encoding="utf-8") as f:
    for line in f:
        rec = json.loads(line)
        gold_ids.add(rec["news_id"])

# write final_dataset.jsonl
with open("silver_full.jsonl", encoding="utf-8") as f_in, \
     open("final_dataset.jsonl", "w", encoding="utf-8") as f_out:
    # 먼저 Gold(사람 검수) 데이터 쓰기
    with open("gold.jsonl", encoding="utf-8") as fg:
        for line in fg:
            f_out.write(line)
    # 그다음 Silver 중 나머지(노이즈) 쓰기
    for line in f_in:
        rec = json.loads(line)
        if rec["news_id"] not in gold_ids:
            f_out.write(json.dumps({
                "news_id": rec["news_id"],
                "text":  rec["text"],
                "label": rec["label"]  # Silver 라벨 (noisy)
            }, ensure_ascii=False) + "\n")

print("최종 학습용 데이터셋 생성: final_dataset.jsonl")
