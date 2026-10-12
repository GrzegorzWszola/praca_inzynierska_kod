import os
os.environ["ACCELERATE_MIXED_PRECISION"] = "no"

from ml_engine.metrics import Metrics
from ml_engine.profiler import Profiler
import torch

from test_utils import read_cr4, save_raport_to_file, read_emo_bank
from datasets import Dataset
from transformers import AutoModelForSequenceClassification, AutoTokenizer, TrainingArguments, Trainer

TRAIN=True

DATASET_CR4 = "/home/grzeg/inz/app/ml-engine/tests/data/cr4_narr_dataset.csv"
DATASET_EMO_BANK = "/home/grzeg/inz/app/ml-engine/tests/data/main_dataset.csv"
model_name = "microsoft/deberta-v3-base"
# model_name = "microsoft/deberta-v3-large"
if not TRAIN:
    ready_model = AutoModelForSequenceClassification.from_pretrained(
        "/home/grzeg/inz/app/ml-engine/tests/saved_models/deberta/deberta_cr4-seed69",
        dtype=torch.float32,
    )

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(
    model_name,
    num_labels=3,
    problem_type="regression",
    dtype=torch.float32,
)

def prepare_df(df):
    df = df.copy()
    df["labels"] = df[["BERT_V", "A", "D"]].values.tolist()
    return df[["text", "labels"]]

def tokenize_fn(batch):
    return tokenizer(batch["text"], truncation=True, padding="max_length", max_length=256)

metrics_tracker = Metrics()

def compute_metrics_for_trainer(eval_pred):
    preds, labels = eval_pred
    mae = metrics_tracker.mae(labels, preds)
    ccc = metrics_tracker.ccc(labels, preds)
    return {
        "mae_V": float(mae[0]), "mae_A": float(mae[1]), "mae_D": float(mae[2]),
        "ccc_V": float(ccc[0]), "ccc_A": float(ccc[1]), "ccc_D": float(ccc[2]),
    }

train, dev, test = read_cr4(DATASET_CR4)
# train, dev, test = read_emo_bank(DATASET_EMO_BANK)

train = prepare_df(train)
dev = prepare_df(dev)
test = prepare_df(test)

train_dataset = Dataset.from_pandas(train, preserve_index=False)
dev_dataset = Dataset.from_pandas(dev, preserve_index=False)
test_dataset = Dataset.from_pandas(test, preserve_index=False)

train_dataset = train_dataset.map(tokenize_fn, batched=True)
dev_dataset = dev_dataset.map(tokenize_fn, batched=True)
test_dataset = test_dataset.map(tokenize_fn, batched=True)

training_args = TrainingArguments(
    output_dir="./deberta-vad-output",
    eval_strategy="epoch",
    save_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    num_train_epochs=3,
    weight_decay=0.01,
    load_best_model_at_end=True,
    metric_for_best_model="ccc_V",
    logging_steps=50,
    fp16=False,   # jawnie wyłącz
    bf16=False,   # jawnie wyłącz
)

profiler = Profiler()

if __name__ == "__main__":
    if TRAIN:
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=dev_dataset,
            compute_metrics=compute_metrics_for_trainer,
        )
        with profiler.measure("Training", "Deberta"):
            trainer.train()

        trainer.save_model("/home/grzeg/inz/app/ml-engine/tests/saved_models/deberta/deberta-vad-seed42")
        tokenizer.save_pretrained("/home/grzeg/inz/app/ml-engine/tests/saved_models/deberta/deberta-vad-seed42")
    else:
        trainer = Trainer(
            model=ready_model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=dev_dataset,
            compute_metrics=compute_metrics_for_trainer,
        )

    print(next(trainer.model.parameters()).device)

    with profiler.measure("Prediction", "Deberta"):
        results = trainer.predict(test_dataset)

    metrics_tracker.compute_metrics("DeBERTa-v3-base", results.label_ids, results.predictions)
    metrics_report = metrics_tracker.report()
    profiler_report = profiler.report()

    save_raport_to_file("/home/grzeg/inz/app/ml-engine/tests/reports", metrics_report=metrics_report, profiling_report=profiler_report)
    