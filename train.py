import os
from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments,
)
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
import torch

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = logits.argmax(axis=-1)
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, preds, average="weighted"
    )
    acc = accuracy_score(labels, preds)
    return {"accuracy": acc, "f1": f1, "precision": precision, "recall": recall}

def main():
    # 모델/토크나이저 선택
    MODEL_NAME = "klue/roberta-base"
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    # 데이터 로드
    data_files = {"train": "train.jsonl", "eval": "eval.jsonl"}
    raw_datasets = load_dataset("json", data_files=data_files)
    label_list = raw_datasets["train"].unique("label")
    label_list.sort()

    # 라벨을 정수로 매핑
    def label_to_int(example):
        example["labels"] = label_list.index(example["label"])
        return example
    datasets = raw_datasets.map(label_to_int)

    # 토크나이징
    def preprocess(examples):
        return tokenizer(
            examples["text"],
            truncation=True,
            padding="max_length",
            max_length=128
        )
    tokenized = datasets.map(preprocess, batched=True)

    # 포맷팅
    tokenized.set_format(
        type="torch",
        columns=["input_ids", "attention_mask", "labels"]
    )

    # 모델 로드
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        num_labels=len(label_list)
    )

    # TrainingArguments 설정 (legacy API)
    training_args = TrainingArguments(
        output_dir="ckpt",
        do_train=True,                 # 학습 수행
        do_eval=True,                  # 평가 수행
        eval_steps=200,                # 몇 스텝마다 평가할지
        save_steps=500,                # 몇 스텝마다 체크포인트 저장할지
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        num_train_epochs=3,
        save_total_limit=2,
        logging_steps=50,
        seed=42,
        fp16=torch.cuda.is_available(),  # GPU에서 fp16 사용 여부
    )

    # Trainer 준비
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized["train"],
        eval_dataset=tokenized["eval"],
        tokenizer=tokenizer,
        compute_metrics=compute_metrics,
    )

    # 학습 시작
    trainer.train()

    # 최종 모델 저장
    trainer.save_model("policy-impl-classifier")
    tokenizer.save_pretrained("policy-impl-classifier")

if __name__ == "__main__":
    main()
