import json
from sklearn.model_selection import train_test_split

records = []
with open("final_dataset.jsonl", encoding="utf-8") as f:
    for line in f:
        records.append(json.loads(line))

train, eval_ = train_test_split(records, test_size=0.2, random_state=42)

def write_split(data, path):
    with open(path, "w", encoding="utf-8") as f:
        for rec in data:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

write_split(train, "train.jsonl")
write_split(eval_,  "eval.jsonl")
print(f"Split 완료: train={len(train)}, eval={len(eval_)}")
